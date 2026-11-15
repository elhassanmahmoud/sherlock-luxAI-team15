"""Ein gelernter Imitationsschueler beraet V14 selektiv nach dessen vollstaendiger Aktionswahl."""
from collections import Counter

import numpy as np
import torch

from agents.sherlock import geometry as geo
from agents.sherlock import own_command
from agents.sherlock.cnn_model import map_planes
from agents.sherlock.imitation_agent import sap_legal
from agents.sherlock.imitation_net import ImitationNet, masked_sap_logits
from agents.sherlock.main import Agent_x
from scripts.combat_teacher_counterfactual import substitute
from scripts.imitate import PLANE_SCALE


HISTORY_KIND = "selective_movement_previous_enemy_v1"


def is_next_frame(step, match_step, last_step, last_match_step):
    """Scalar or vector; the two clocks must both advance on the same map and seat."""
    return (step == last_step + 1) & (match_step == last_match_step + 1)


def live_history_board(current, step, match_step, prior):
    """One board in canonical playing coordinates; remember just its quantized occupancy."""
    previous = np.zeros_like(current[10])
    if prior is not None:
        last_step, last_match_step, saved = prior
        if is_next_frame(step, match_step, last_step, last_match_step):
            previous = saved
    saved = np.rint(current[10] * PLANE_SCALE) / PLANE_SCALE
    return np.concatenate((current, previous[None]), axis=0), (step, match_step, saved)


def load_heads(path):
    """Eigene Checkpoints aus scripts.imitate train/ensemble. Die Beratungsnetze laufen auf der CPU."""
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    if checkpoint.get("kind") not in ("imitation", HISTORY_KIND, own_command.KIND):
        raise ValueError("Fuer advice_path wird ein Checkpoint vom Typ imitation benoetigt")
    members = []
    for entry in [checkpoint, *checkpoint.get("imitation_ensemble", [])]:
        expected_channels = 17 if checkpoint["kind"] == HISTORY_KIND else 16
        if entry["arch"].get("in_ch", 16) != expected_channels:
            raise ValueError("Unerwartete Anzahl Kartenebenen fuer diesen Beratertyp")
        width = 85 if checkpoint["kind"] == own_command.KIND else 79
        if entry["arch"]["feat_dim"] != width:
            raise ValueError("Movement adviser feature count disagrees with its checkpoint type")
        if not entry["arch"].get("sap_head"):
            raise ValueError("Ein gelernter Schusszielkopf wird fuer selektive Beratung benoetigt")
        model = ImitationNet(**entry["arch"])
        model.load_state_dict(entry["policy"])
        members.append(model.eval())
    return members, bool(checkpoint.get("sap_own_tile", False))


class SelectiveAdviceAgent(Agent_x):
    previous_enemy = False
    own_command_input = False

    def __init__(self, player, agent_path, name="Sherlock mit selektiver Imitation", cfg=None,
                 train=False, seed=None, *, advice_path, mode):
        if mode not in ("movement", "combat"):
            raise ValueError("mode muss movement oder combat sein")
        super().__init__(player, agent_path=agent_path, name=name, cfg=cfg, train=train, seed=seed)
        if len(self.extra_q) != 35:
            raise ValueError("Als Basis wird V14 mit seinen 36 Netzen benoetigt")
        self.mode = mode
        self.members, self.sap_own_tile = load_heads(advice_path)
        self.previous_enemy = self.members[0].arch["in_ch"] == 17
        if self.previous_enemy and mode != "movement":
            raise ValueError("Der historisierte Berater wurde nur fuer Bewegung festgelegt")
        self.own_command_input = self.members[0].arch["feat_dim"] == 85
        if self.own_command_input and (mode != "movement" or len(self.members) != 1):
            raise ValueError("Own-command study requires a single movement adviser")
        self.autosave_on_terminate = False

    def _reset_episode_state(self):
        super()._reset_episode_state()
        self.selective_counts = Counter()
        self.played_commands = own_command.PlayedCommands()
        self._previous_frame = None

    def _input_board(self, current, step, match_step):
        if not self.previous_enemy:
            return current
        board, self._previous_frame = live_history_board(current, step, match_step, self._previous_frame)
        return board

    def _act(self, step, obs):
        # _act_est protokolliert die hier zurueckgegebenen Befehle im Parameterschaetzer.
        base = super()._act(step, obs)
        played = self._advise(step, obs, base)
        if self.own_command_input:
            ctx = self._prev_ctx
            if ctx is None:
                self.played_commands = own_command.PlayedCommands()
            else:
                ids = [int(u) for u in ctx["ally_ids"] if ctx["ally_ene"][u] >= 0]
                self.played_commands.record(int(obs["steps"]), int(obs["match_steps"]), ids,
                                            np.asarray(ctx["ally_pos"])[ids], played, self.belief.mirrored)
        return played

    def _advise(self, step, obs, base):
        if self.training or int(obs["match_steps"]) == 0:
            self._previous_frame = None
            return base
        ctx, cached_ids, feats, mask_map, _ = self._decide(obs)
        ids = [u for u in cached_ids if ctx["ally_ene"][u] >= 0]
        if not ids:
            self._previous_frame = None  # The collector does not store these boards.
            return base

        board = self._input_board(map_planes(ctx), int(obs["steps"]), int(obs["match_steps"]))
        planes = torch.from_numpy(board[None])
        step_idx = torch.zeros(len(ids), dtype=torch.long)
        pos = torch.as_tensor(np.asarray(ctx["ally_pos"])[ids], dtype=torch.long)
        features = np.stack([feats[u] for u in ids])
        if self.own_command_input:
            extra = self.played_commands.features(int(obs["steps"]), int(obs["match_steps"]), ids, pos.numpy())
            features = np.column_stack((features, extra))
        features = torch.from_numpy(features)
        masks = np.stack([mask_map[u] for u in ids])
        masks = sap_legal(masks, np.asarray(ctx["ally_ene"])[ids], ctx["sap_cost"])
        advice = base.copy()
        with torch.inference_mode():
            outputs = [net.forward_all(planes, step_idx, pos, features) for net in self.members]
            # Mittel statt Summe: Die Sicherheitsschwellen behalten bei identischen Kopien dieselbe Bedeutung.
            logits = torch.stack([out[0] for out in outputs]).mean(0)
            prob, choice = logits.masked_fill(~torch.from_numpy(masks), -torch.inf).softmax(1).max(1)
            accepted = prob >= 0.70
            moves = torch.where(accepted & (choice != geo.SAP))[0]
            for row in moves.tolist():
                direction = int(choice[row])
                if self.belief.mirrored:
                    direction = geo.mirror_dir(direction)
                advice[ids[row]] = [direction, 0, 0]
            if self.mode == "combat":
                shots = torch.where(accepted & (choice == geo.SAP))[0]
                if len(shots):
                    target_map = torch.stack([out[2] for out in outputs]).mean(0)
                    positions = pos[shots]
                    radii = torch.full_like(shots, int(ctx["sap_range"]))
                    scores = masked_sap_logits(target_map, step_idx[shots], positions, radii)
                    height = target_map.shape[-1]
                    if not self.sap_own_tile:
                        own = positions[:, 0] * height + positions[:, 1]
                        scores[torch.arange(len(shots)), own] = -torch.inf
                    confidence, cells = scores.softmax(1).max(1)
                    for k in torch.where(confidence >= 0.50)[0].tolist():
                        tx, ty = divmod(int(cells[k]), height)
                        x, y = positions[k].tolist()
                        delta = (tx - x, ty - y)
                        if self.belief.mirrored:
                            delta = geo.mirror_delta(*delta)
                        advice[ids[int(shots[k])]] = [geo.SAP, *delta]
        # Dieselben Modusgrenzen, Legalitaetspruefungen und Folgezustaende wie in der Lehrer-Gegenprobe.
        return substitute(self, obs, base, advice, self.mode, self.selective_counts)
