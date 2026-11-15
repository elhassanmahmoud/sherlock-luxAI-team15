"""Experimenteller Schusskopf hinter der finalen V14-Aktion. Alle Netzeingaben sind kanonisch."""
from __future__ import annotations

import math

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from agents.sherlock import geometry as geo
from agents.sherlock.cnn_model import N_PLANES, ResBlock, map_planes
from agents.sherlock.features import FEATURE_DIM
from agents.sherlock.main import Agent_x


CHECKPOINT_KIND = "sherlock_combat_advice_v1"
BOARD_SIZE = 24


class CombatBoardHistory:
    """Letzte beobachtete Gegnerebenen einer Seite; bei Spielstart und ausgelassenen Frames zuruecksetzen."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._stamp = None
        self._last = None

    def build(self, planes16, step, match_step, match_idx):
        current = np.asarray(planes16, dtype=np.float32)
        if current.shape != (N_PLANES, BOARD_SIZE, BOARD_SIZE):
            raise ValueError("Erwartet 16 kanonische Kartenebenen auf 24 x 24 Feldern")
        recent = current[10:13]
        previous = np.zeros_like(recent)
        if match_step == 0:
            self.reset()
        else:
            if self._stamp == (step - 1, match_step - 1, match_idx):
                previous = self._last
            self._stamp = (step, match_step, match_idx)
            self._last = recent.copy()
        return np.concatenate((current, previous), axis=0)


class CombatAdviceNet(nn.Module):
    """Liefert Schusslogits [N] und reichweitenmaskierte Ziellogits [N,24,24], indiziert als [x,y]."""

    def __init__(self):
        super().__init__()
        channels, query_size = 24, 16
        self.board = nn.Sequential(nn.Conv2d(19, channels, 3, padding=1), nn.ReLU(),
                                   ResBlock(channels), ResBlock(channels))
        self.shooter = nn.Sequential(nn.Linear(channels + FEATURE_DIM + 6, 64), nn.ReLU())
        self.fire = nn.Linear(64, 1)
        self.query = nn.Linear(64, query_size)
        self.keys = nn.Conv2d(channels, query_size, 1)
        self.offset_x = nn.Embedding(2 * BOARD_SIZE - 1, query_size)
        self.offset_y = nn.Embedding(2 * BOARD_SIZE - 1, query_size)

    def forward(self, boards, step_idx, pos, feats, base_actions, sap_range):
        board = self.board(boards)
        local = board[step_idx, :, pos[:, 0], pos[:, 1]]
        base = F.one_hot(base_actions, num_classes=6).to(feats.dtype)
        unit = self.shooter(torch.cat((local, feats, base), dim=1))
        query = self.query(unit)
        keys = self.keys(board)[step_idx]
        scores = torch.einsum("nq,nqxy->nxy", query, keys)

        # Ein Schuetze kann Ziele nach Entfernung UND Richtung anders einstufen.
        # Nur zwei kleine Offset-Tabellen auswerten, statt sie fuer jedes Feld zu kopieren.
        axis = torch.arange(BOARD_SIZE, device=pos.device)
        dx = axis[None, :] - pos[:, 0, None]
        dy = axis[None, :] - pos[:, 1, None]
        x_score = (query @ self.offset_x.weight.T).gather(1, dx + BOARD_SIZE - 1)
        y_score = (query @ self.offset_y.weight.T).gather(1, dy + BOARD_SIZE - 1)
        scores = (scores + x_score[:, :, None] + y_score[:, None, :]) / math.sqrt(query.shape[1])
        reach = sap_range[:, None, None]
        legal = (dx.abs()[:, :, None] <= reach) & (dy.abs()[:, None, :] <= reach)
        return self.fire(unit).squeeze(1), scores.masked_fill(~legal, -torch.inf)


def advice_decision(base, fire_probability, target_probability, affordable, protected_move, mode):
    """True, wenn ein Schuetze das vorgeschlagene Ziel verwenden darf (gleiche Regel fuer Spiel und Diagnose)."""
    if mode not in ("aim", "fire"):
        raise ValueError("mode muss aim oder fire sein")
    if not (affordable and target_probability >= 0.5):
        return False
    if base == geo.SAP:
        return True
    return bool(mode == "fire" and not protected_move and fire_probability >= 0.90)


class CombatAdviceAgent(Agent_x):
    def __init__(self, player, agent_path=None, name="Sherlock V14 mit Schusskopf", cfg=None,
                 train=False, seed=None, *, advice_path, mode):
        if mode not in ("aim", "fire"):
            raise ValueError("mode muss aim oder fire sein")
        self.mode = mode
        self.history = CombatBoardHistory()
        super().__init__(player, agent_path=agent_path, name=name, cfg=cfg, train=train, seed=seed)
        checkpoint = torch.load(advice_path, map_location="cpu", weights_only=True)
        if checkpoint.get("kind") != CHECKPOINT_KIND:
            raise ValueError(f"Schusskopf vom Typ {CHECKPOINT_KIND} erwartet")
        self.advice = CombatAdviceNet()
        self.advice.load_state_dict(checkpoint["state_dict"])
        self.advice.eval()
        self.autosave_on_terminate = False

    def _reset_episode_state(self):
        super()._reset_episode_state()
        self.history.reset()

    def _act(self, step, obs):
        # Der umgebende Originalpfad _act_est merkt nach der Rueckkehr die tatsaechlichen Weltaktionen.
        actions = super()._act(step, obs)
        if self.training or int(obs["match_steps"]) == 0:
            self.history.reset()
            return actions
        ctx, ids, feats, _, _ = self._decide(obs)  # Cache des gerade abgeschlossenen V14-Zuges
        ids = [uid for uid in ids if ctx["ally_ene"][uid] >= 0]
        if not ids:
            self.history.reset()
            return actions
        boards = self.history.build(map_planes(ctx), int(obs["steps"]), int(obs["match_steps"]), ctx["match_idx"])
        base = actions[ids, 0].copy()
        if self.mode == "aim" and not np.any(base == geo.SAP):
            return actions
        if self.belief.mirrored:
            move = base < geo.SAP
            base[move] = geo.MIRROR_DIR[base[move]]
        pos = np.asarray(ctx["ally_pos"])[ids]
        with torch.inference_mode():
            fire_logits, target_logits = self.advice(
                torch.from_numpy(boards[None]), torch.zeros(len(ids), dtype=torch.long),
                torch.as_tensor(pos, dtype=torch.long), torch.from_numpy(np.stack([feats[u] for u in ids])),
                torch.as_tensor(base, dtype=torch.long), torch.full((len(ids),), int(ctx["sap_range"])))
            fire = fire_logits.sigmoid().numpy()
            confidence, cells = target_logits.flatten(1).softmax(1).max(1)
        for row, uid in enumerate(ids):
            a = int(base[row])
            x, y = map(int, pos[row])
            protected = False
            if 1 <= a <= 4:
                tx, ty = x + geo.DIR_DX[a], y + geo.DIR_DY[a]
                if 0 <= tx < BOARD_SIZE and 0 <= ty < BOARD_SIZE:
                    protected = self.belief.point_tiles[tx, ty] and ctx["ally_count"][tx, ty] == 0
            affordable = ctx["ally_ene"][uid] >= ctx["sap_cost"]
            if not advice_decision(a, fire[row], float(confidence[row]), affordable, protected, self.mode):
                continue
            tx, ty = divmod(int(cells[row]), BOARD_SIZE)
            delta = (tx - x, ty - y)
            if self.belief.mirrored:
                delta = geo.mirror_delta(*delta)
            if a == geo.SAP and tuple(actions[uid, 1:]) == delta:
                continue
            actions[uid] = [geo.SAP, *delta]
            self._record_advised_shot(ctx, uid, a, (tx, ty))
        return actions

    def _record_advised_shot(self, ctx, uid, base, target):
        enemies = ctx["enemy_coords"]
        hits = int((np.max(np.abs(enemies - target), axis=1) <= 1).sum()) if len(enemies) else 0
        old_hits = self._sap_hits.get(uid, 0)
        self._sap_hits[uid] = hits
        self._sap_unknown.discard(uid)  # Der neue Vorschlag stammt nicht aus V14s Fog-SAP-Regel.
        self._prev_actions[uid] = geo.SAP
        self.ep_stats["sap_hits_est"] += int(hits > 0) - int(old_hits > 0)
        if base != geo.SAP:
            self.ep_stats["sap_attempts"] += 1
            # Vorhandene Energieprognosen muessen im naechsten Schritt die echten Schusskosten abziehen.
            self._pred_pending = [(u, x, y, e, shot or u == uid) for u, x, y, e, shot in self._pred_pending]
            self._shape_pending = [(u, x, y, e, shot or u == uid, shape)
                                   for u, x, y, e, shot, shape in self._shape_pending]
        key = "advice_retargeted" if base == geo.SAP else "advice_new_saps"
        self.ep_stats[key] = self.ep_stats.get(key, 0) + 1
