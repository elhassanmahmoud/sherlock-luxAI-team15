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
from .imitation_net import ImitationNet
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
        if net is None and agent_path:
            ckpt = torch.load(agent_path, map_location="cpu", weights_only=False)
            arch = ckpt.get("arch") or {}
            if arch.get("sap_head"):
                net = ImitationNet(**arch)
                net.load_state_dict(ckpt["policy"])
        super().__init__(player, agent_path=agent_path, name=name, net=net, **kw)
        self.sample = False
        self.has_sap_head = isinstance(self.net, ImitationNet)

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
        sapmap = None
        with torch.no_grad():
            inputs = (torch.as_tensor(planes[None]), torch.zeros(len(ids), dtype=torch.long),
                      torch.as_tensor(pos), torch.as_tensor(feats))
            m = torch.as_tensor(masks)
            if self.has_sap_head:
                logits, _, smap = self.net.forward_all(*inputs)
                sapmap = smap[0].numpy()
            else:
                logits = self.net(*inputs)[0]
            logp = torch.log_softmax(logits.masked_fill(~m, -1e9), dim=1)
            for extra in self.extra_nets:
                logp = logp + torch.log_softmax(extra(*inputs)[0].masked_fill(~m, -1e9), dim=1)
            acts = logp.argmax(dim=1).numpy()
        R = int(ctx["sap_range"])
        W, H = ctx["W"], ctx["H"]
        for k, uid in enumerate(ids):
            a = int(acts[k])
            self._prev_actions[uid] = a
            target = None
            if a == geo.SAP and sapmap is not None:
                x, y = int(pos[k][0]), int(pos[k][1])
                x0, x1, y0, y1 = max(0, x - R), min(W, x + R + 1), max(0, y - R), min(H, y + R + 1)
                win = sapmap[x0:x1, y0:y1].copy()
                if x0 <= x < x1 and y0 <= y < y1:
                    win[x - x0, y - y0] = -np.inf  # nie auf das eigene Feld
                tx, ty = np.unravel_index(int(np.argmax(win)), win.shape)
                target = (int(tx) + x0 - x, int(ty) + y0 - y, 0)
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
