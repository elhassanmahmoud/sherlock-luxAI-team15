"""Sherlock mit nachgeahmter Policy (15.11.2026, "Umbau").

Ein CNN (cnn_model.PolicyNet) sieht die ganze Karte (16 Ebenen aus Sherlocks Gedaechtnis) und je Unit
die 79 Merkmale. Es wurde per Imitation Learning auf die Zuege eines starken Lehrers trainiert
(scripts/imitate.py; Lehrer: Kaggle-Platz-3-Agent, nur als Lehrer und Testgegner, nie Teil der Abgabe).

Wichtig: `featurize` ist die EINZIGE Vorverarbeitung, sowohl beim Sammeln der Lehrer-Daten (Schatten-Agent
auf der Seite des Lehrers) als auch beim Spielen. So sieht das Netz im Spiel genau die Eingaben wie im Training.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import torch

from . import geometry as geo
from .cnn_model import map_planes
from .imitation_net import ImitationNet, masked_sap_logits
from .ppo_agent import PPOAgent


def featurize(agent, obs):
    """Gedaechtnis aktualisieren und Netzeingaben bauen (kanonischer Raum).

    Rueckgabe (ctx, ids, feats [N,79], masks [N,6], sap_targets, planes [16,W,H], pos [N,2]) oder None
    am Matchstart (Units sind Reste des alten Matches) bzw. ohne eigene Units."""
    agent.belief.observe(obs)
    if int(np.asarray(obs["match_steps"])) == 0:
        agent._prev_ctx = None
        return None
    ctx, ids, feat_map, mask_map, sap_targets = agent._decide(obs)
    agent._prev_ctx = ctx
    if not ids:
        return None
    feats = np.stack([feat_map[u] for u in ids]).astype(np.float32)
    masks = np.stack([mask_map[u] for u in ids]).astype(bool)
    planes = map_planes(ctx)
    pos = np.array([[int(ctx["ally_pos"][u][0]), int(ctx["ally_pos"][u][1])] for u in ids], dtype=np.int64)
    return ctx, ids, feats, masks, sap_targets, planes, pos


def canonical_action(row, mirrored: bool) -> tuple[int, int, int]:
    """Echte Aktion [a, dx, dy] eines Spielers in den kanonischen Raum uebersetzen."""
    a, dx, dy = int(row[0]), int(row[1]), int(row[2])
    if a == geo.SAP:
        if mirrored:
            dx, dy = geo.mirror_delta(dx, dy)
        return a, dx, dy
    if not 0 <= a <= 4:
        a = geo.STAY
    if mirrored:
        a = geo.mirror_dir(a)
    return a, 0, 0


def sap_legal(masks: np.ndarray, energy: np.ndarray, sap_cost: float) -> np.ndarray:
    """Mit Zielkopf darf jede Unit schiessen, die die Sap-Kosten bezahlen kann (Ziel waehlt das Netz, auch in
    den Nebel); die uebrigen Aktionen behalten Sherlocks Maske."""
    m = masks.copy()
    m[:, geo.SAP] = energy >= sap_cost
    return m


class ImitationAgent(PPOAgent):
    """Agent_x-Schnittstelle mit der nachgeahmten Policy. Gespielt wird gierig (argmax), illegale
    Aktionen sind maskiert. Mit Zielkopf (ImitationNet) waehlt das Netz das Sap-Ziel in Reichweite,
    sonst Sherlocks Zielheuristik."""

    def __init__(self, player: str, agent_path: Optional[str] = None, name: str = "Sherlock Imitation", **kw):
        net = kw.pop("net", None)
        members = []
        own_tile = True
        if net is None and agent_path:
            ckpt = torch.load(agent_path, map_location="cpu", weights_only=False)
            # Aeltere Schueler (vor dem 15.11., 15:40) lernten den Zielkopf ohne das eigene Feld; dessen Bewertung ist
            # dort untrainiert. Fuer sie bleibt das eigene Feld als Ziel gesperrt.
            own_tile = bool(ckpt.get("sap_own_tile", False))
            arch = ckpt.get("arch") or {}
            if arch.get("sap_head"):
                net = ImitationNet(**arch)
                net.load_state_dict(ckpt["policy"])
            # Ensemble mehrerer Schueler (scripts/imitate.py ensemble): gemittelte Aktions- und Zielbewertung
            for m in ckpt.get("imitation_ensemble", []):
                extra = ImitationNet(**m["arch"])
                extra.load_state_dict(m["policy"])
                members.append(extra.eval())
        super().__init__(player, agent_path=agent_path, name=name, net=net, **kw)
        self.sample = False
        self.has_sap_head = isinstance(self.net, ImitationNet)
        self.sap_own_tile = own_tile
        if members:
            self.extra_nets = members

    def _unstack_actions(self, ctx, ids, pos, logp: np.ndarray, acts: np.ndarray) -> np.ndarray:
        """cfg.imit_unstack: je Feld bleibt hoechstens eine Unit stehen; die anderen nehmen ihre beste erlaubte
        Bewegung (nach der Netzbewertung). Schuesse bleiben erhalten (Schuetzen stehen ebenfalls)."""
        acts = acts.copy()
        by_tile: dict[tuple[int, int], list[int]] = {}
        for k in range(len(ids)):
            if acts[k] == geo.STAY:
                by_tile.setdefault((int(pos[k][0]), int(pos[k][1])), []).append(k)
        for tile, rows in by_tile.items():
            if len(rows) < 2:
                continue
            holder = ctx["first_on_tile"].get(tile)
            keep = next((k for k in rows if int(ids[k]) == holder), max(rows, key=lambda k: logp[k, geo.STAY]))
            for k in rows:
                if k == keep:
                    continue
                moves = logp[k, 1:5]
                if np.isfinite(moves).any():
                    acts[k] = 1 + int(np.argmax(moves))
                    self.ep_stats["unstack_moves"] = self.ep_stats.get("unstack_moves", 0) + 1
        return acts

    def act(self, step: int, obs) -> np.ndarray:
        max_units = int((self.env_cfg or {}).get("max_units", 16))
        actions = np.zeros((max_units, 3), dtype=int)
        self._prev_feats, self._prev_actions, self._prev_masks = {}, {}, {}
        self._sap_hits = {}
        fz = featurize(self, obs)
        self.last_fz = fz  # DAgger: Eingaben dieses Schritts fuer die Lehrer-Labels
        if fz is None:
            return actions
        ctx, ids, feats, masks, sap_targets, planes, pos = fz
        energy = np.array([float(ctx["ally_ene"][u]) for u in ids])
        if self.has_sap_head:
            masks = sap_legal(masks, energy, float(ctx["sap_cost"]))
        targets = {}
        with torch.no_grad():
            inputs = (torch.as_tensor(planes[None]), torch.zeros(len(ids), dtype=torch.long),
                      torch.as_tensor(pos), torch.as_tensor(feats))
            m = torch.as_tensor(masks)
            if self.has_sap_head:
                logits, _, smap = self.net.forward_all(*inputs)
                smap = torch.log_softmax(smap[0].flatten(), 0)
            else:
                logits = self.net(*inputs)[0]
            logp = torch.log_softmax(logits.masked_fill(~m, -torch.inf), dim=1)
            for extra in self.extra_nets:
                if self.has_sap_head and isinstance(extra, ImitationNet):
                    lg, _, sm = extra.forward_all(*inputs)
                    smap = smap + torch.log_softmax(sm[0].flatten(), 0)
                else:
                    lg = extra(*inputs)[0]
                logp = logp + torch.log_softmax(lg.masked_fill(~m, -torch.inf), dim=1)
            stay_bias = float(getattr(self.cfg, "imit_stay_bias", 0.0) or 0.0)
            if stay_bias:
                logp[:, geo.STAY] -= stay_bias
            sap_bias = float(getattr(self.cfg, "imit_sap_bias", 0.0) or 0.0)
            if sap_bias:
                logp[:, geo.SAP] += sap_bias  # gesperrte Schuesse bleiben -inf
            acts = logp.argmax(dim=1).numpy()
            if getattr(self.cfg, "imit_unstack", False):
                acts = self._unstack_actions(ctx, ids, pos, logp.numpy(), acts)
            # 15.11.2026 (cfg.end_sap > 0): in den letzten end_sap Schritten eines Matches verfaellt die Energie
            # ohnehin; stehende Units mit genug Energie schiessen dann (der Lehrer tut das kaum: rund 3 %).
            end_sap = int(getattr(self.cfg, "end_sap", 0) or 0)
            end_phase = end_sap > 0 and int(ctx["match_step"]) >= int(ctx["max_match_steps"]) - end_sap
            end_rows = set()
            if end_phase:
                for k, uid in enumerate(ids):
                    if (acts[k] == geo.STAY and energy[k] >= float(ctx["sap_cost"])
                            and (self.has_sap_head or sap_targets[uid] is not None)):
                        acts[k] = geo.SAP
                        end_rows.add(k)
                self.ep_stats["end_saps"] = self.ep_stats.get("end_saps", 0) + len(end_rows)
            if self.has_sap_head:
                shots = torch.from_numpy(np.flatnonzero(acts == geo.SAP))
                if shots.numel():
                    positions = inputs[2][shots]
                    radii = torch.full_like(shots, int(ctx["sap_range"]))
                    scores = masked_sap_logits(smap.reshape(1, *planes.shape[1:]), inputs[1][shots], positions, radii)
                    if not getattr(self, "sap_own_tile", True):
                        own = positions[:, 0] * int(ctx["H"]) + positions[:, 1]
                        scores[torch.arange(len(own)), own] = -torch.inf
                    for row, flat in zip(shots.tolist(), scores.argmax(1).tolist()):
                        tx, ty = divmod(flat, ctx["H"])
                        targets[row] = (tx - int(pos[row, 0]), ty - int(pos[row, 1]), 0)
        focus = {}
        if getattr(self.cfg, "focus_sap", False):
            # 15.11.2026: sichere gemeinsame Abschuesse stehender Gegner (wie V14-Schalter focus_sap)
            from . import combat
            stationary = self._enemy_stationary(ctx)
            focus = combat.focus_plan(ctx, [int(u) for u in ids], self.belief.point_tiles, stationary,
                                      self._holders(ctx, ids), dropoff=self.cfg.focus_dropoff,
                                      reserve=self.cfg.focus_reserve)
        for k, uid in enumerate(ids):
            a = int(acts[k])
            if int(uid) in focus:
                a = geo.SAP
            self._prev_actions[uid] = a
            target = None
            if int(uid) in focus:
                target = focus[int(uid)]
            elif k in end_rows and sap_targets[uid] is not None and sap_targets[uid][2] > 0:
                target = sap_targets[uid]  # Restenergie: sichtbare Gegner zuerst
            elif a == geo.SAP and self.has_sap_head:
                target = targets[k]
            elif a == geo.SAP:
                target = sap_targets[uid]
            if a == geo.SAP and target is not None:
                dx, dy, hits = target
                if self.belief.mirrored:
                    dx, dy = geo.mirror_delta(dx, dy)
                actions[uid] = [geo.SAP, dx, dy]
                self._sap_hits[uid] = hits
            else:
                d = a if a < 5 else geo.STAY
                if self.belief.mirrored:
                    d = geo.mirror_dir(d)
                actions[uid] = [d, 0, 0]
        return actions
