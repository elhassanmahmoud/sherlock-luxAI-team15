"""PPO-Agent mit CNN-Policy (cnn_model.PolicyNet).

Nutzt dieselben Leitplanken wie der DQN-Agent (Belief, Zielzuweisung,
Aktionsmaske, heuristisches Sap-Ziel, Reward Shaping pro Unit und Step), nur die
Aktionswahl kommt aus einer stochastischen Policy pi(a | Karte, Unit).

Recorder sammelt Uebergaenge pro Unit-Trajektorie (Tod, wiederverwendete ID oder
Matchende beenden sie) und berechnet GAE-Vorteile. Derselbe Recorder zeichnet
auch die Zuege eines Lehrer-Agenten (DQN-Ensemble) fuer das Vortraining
(Behaviour Cloning) auf.
"""
from __future__ import annotations

import os
from typing import Optional

import numpy as np
import torch

from . import geometry as geo
from .cnn_model import PolicyNet, map_planes
from .features import FEATURE_DIM
from .main import Agent_x
from .reward import surviving, unit_rewards

PLANE_SCALE = 127.0


class Recorder:
    """Rollout-Speicher eines Spiels (eine Seite)."""

    def __init__(self) -> None:
        self.planes: list[np.ndarray] = []
        self.rows: list[list] = []      # step, x, y, uid, act, logp, val
        self.feats: list[np.ndarray] = []
        self.masks: list[np.ndarray] = []
        self.rew: list[float] = []
        self.done: list[bool] = []
        self._open: dict[int, int] = {}  # uid -> Index der letzten Probe

    def on_act(self, ctx: dict, ids, feats, masks, actions, logps=None, values=None) -> None:
        si = len(self.planes)
        self.planes.append(np.round(map_planes(ctx) * PLANE_SCALE).astype(np.int8))
        self._open = {}
        for k, uid in enumerate(ids):
            x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
            self._open[int(uid)] = len(self.rows)
            self.rows.append([si, x, y, int(uid), int(actions[k]),
                              0.0 if logps is None else float(logps[k]),
                              0.0 if values is None else float(values[k])])
            self.feats.append(feats[k])
            self.masks.append(masks[k])
            self.rew.append(0.0)
            self.done.append(True)

    def on_next(self, agent: Agent_x, next_obs, terminated: bool) -> None:
        prev_ctx = agent._prev_ctx
        if prev_ctx is None or not self._open:
            return
        agent.belief.observe(next_obs)
        next_ctx = agent._decide(next_obs)[0]
        rewards = unit_rewards(agent.cfg, prev_ctx, next_ctx, agent._prev_actions, agent._sap_hits)
        alive = surviving(agent.cfg, prev_ctx, next_ctx)
        over = bool(terminated) or next_ctx["match_step"] == 0
        for uid, i in self._open.items():
            self.rew[i] = float(rewards.get(uid, 0.0))
            self.done[i] = over or uid not in alive
        self._open = {}

    def finish(self, gamma: float, lam: float) -> dict:
        n = len(self.rows)
        rows = np.array(self.rows, dtype=np.float64).reshape(n, 7)
        val = rows[:, 6].astype(np.float32)
        rew = np.array(self.rew, dtype=np.float32)
        done = np.array(self.done, dtype=bool)
        uid = rows[:, 3].astype(np.int32)
        adv = np.zeros(n, dtype=np.float32)
        # GAE rueckwaerts je Unit: naechste Probe derselben ID folgt im naechsten Step
        nxt_adv: dict[int, float] = {}
        nxt_val: dict[int, float] = {}
        for i in range(n - 1, -1, -1):
            u = int(uid[i])
            if done[i] or u not in nxt_val:
                a = rew[i] - val[i]
            else:
                delta = rew[i] + gamma * nxt_val[u] - val[i]
                a = delta + gamma * lam * nxt_adv[u]
            adv[i] = a
            nxt_adv[u], nxt_val[u] = a, float(val[i])
            if done[i]:
                pass
        return dict(
            planes=np.stack(self.planes) if self.planes else np.zeros((0,), np.int8),
            step=rows[:, 0].astype(np.int32), pos=rows[:, 1:3].astype(np.int64),
            feats=np.array(self.feats, dtype=np.float32).reshape(n, FEATURE_DIM),
            mask=np.array(self.masks, dtype=bool).reshape(n, -1),
            act=rows[:, 4].astype(np.int64), logp=rows[:, 5].astype(np.float32),
            val=val, adv=adv, ret=adv + val, rew=rew, done=done,
        )


class PPOAgent(Agent_x):
    """Agent_x-Schnittstelle (Runner/Kurs) mit CNN-Policy statt Q-Netz."""

    def __init__(self, player: str, agent_path: Optional[str] = None,
                 name: str = "Sherlock PPO", cfg=None, train: bool = False,
                 seed: Optional[int] = None, net: Optional[PolicyNet] = None) -> None:
        ckpt = None
        if agent_path and os.path.isfile(agent_path):
            ckpt = torch.load(agent_path, map_location="cpu", weights_only=False)
        if cfg is None and ckpt is not None and isinstance(ckpt.get("cfg"), dict):
            from .config import AgentConfig
            cfg = AgentConfig.from_dict(ckpt["cfg"])
        if cfg is not None:
            from dataclasses import replace
            cfg = replace(cfg, buffer_capacity=1)  # kein Replay Buffer noetig
        super().__init__(player, agent_path=None, name=name, cfg=cfg, train=train, seed=seed)
        self.agent_path = agent_path
        self.autosave_on_terminate = False
        if net is None:
            arch = (ckpt or {}).get("arch") or dict(feat_dim=FEATURE_DIM, n_actions=self.n_actions)
            net = PolicyNet(**arch)
            if ckpt is not None:
                net.load_state_dict(ckpt["policy"])
        self.net = net.eval()
        self.recorder: Optional[Recorder] = None
        self.sample = bool(train)

    def load_agent(self, load_path: str) -> None:  # Gewichte laedt __init__
        return

    def save_agent(self, path: Optional[str] = None) -> None:
        return  # Speichern nur ueber scripts.ppo_train (Schutz der Abgabe-Dateien)

    def update(self, *args, **kwargs) -> None:
        return  # gelernt wird ausserhalb (PPO-Learner)

    def act(self, step: int, obs) -> np.ndarray:
        self.belief.observe(obs)
        max_units = int((self.env_cfg or {}).get("max_units", 16))
        actions = np.zeros((max_units, 3), dtype=int)
        self._prev_feats, self._prev_actions, self._prev_masks = {}, {}, {}
        self._sap_hits = {}
        if int(np.asarray(obs["match_steps"])) == 0:
            self._prev_ctx = None
            return actions
        ctx, ids, feat_map, mask_map, sap_targets = self._decide(obs)
        self._prev_ctx = ctx
        if not ids:
            return actions
        feats = np.stack([feat_map[u] for u in ids])
        masks = np.stack([mask_map[u] for u in ids])
        planes = map_planes(ctx)
        pos = np.array([[int(ctx["ally_pos"][u][0]), int(ctx["ally_pos"][u][1])] for u in ids])
        with torch.no_grad():
            logits, values = self.net(
                torch.as_tensor(planes[None]), torch.zeros(len(ids), dtype=torch.long),
                torch.as_tensor(pos, dtype=torch.long), torch.as_tensor(feats))
            logits = logits.masked_fill(~torch.as_tensor(masks), -1e9)
            if self.sample:
                dist = torch.distributions.Categorical(logits=logits)
                a_t = dist.sample()
                logp = dist.log_prob(a_t).numpy()
            else:
                a_t = logits.argmax(dim=1)
                logp = None
        acts = a_t.numpy()
        if self.recorder is not None:
            self.recorder.on_act(ctx, ids, feats, masks, acts, logp, values.numpy())
        for k, uid in enumerate(ids):
            a = int(acts[k])
            self._prev_feats[uid] = feats[k]
            self._prev_actions[uid] = a
            self._prev_masks[uid] = masks[k]
            if a == geo.SAP and sap_targets[uid] is not None:
                dx, dy, hits = sap_targets[uid]
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


def save_policy(path: str, net: PolicyNet, cfg, extra: Optional[dict] = None) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    torch.save({"kind": "ppo", "policy": net.state_dict(), "arch": net.arch,
                "cfg": cfg.to_dict(), "feature_dim": FEATURE_DIM, **(extra or {})}, path)
