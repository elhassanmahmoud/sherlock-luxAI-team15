"""Team-Agent fuer Lux AI S3 - Einstiegspunkt fuer lux/runner.py (Klasse Agent_x).

Algorithmus: Double DQN mit Replay Buffer, Target Network, Dueling-Head,
Action Masking und per-Unit Reward Shaping.

Besonderheit: alle Features werden im KANONISCHEN Raum gebaut (geometry.py), in
dem der eigene Spawn immer auf (0, 0) liegt. Dadurch gilt ein Gewichtssatz fuer
beide Seiten und jedes Spiel liefert Erfahrung fuer player_0 UND player_1.

Pseudocode (fuer die Praesentation):

    fuer jedes Spiel:
        belief <- leer
        fuer jeden Step t:
            belief.observe(obs_t)                       # Relics, Karte, Punkte-Tiles
            ctx   <- make_context(obs_t, belief)        # Zielzuweisung, Gegner, Karten
            fuer jede lebende Unit u:
                s_u      <- build_features(ctx, u)
                mask_u   <- legale Aktionen (Asteroid/Rand/Energie/Sap-Ziel)
                a_u      <- eps-greedy( argmax_a Q(s_u, a) ueber mask_u )
            env.step(actions)
            belief.observe(obs_{t+1}); ctx' <- make_context(obs_{t+1})
            r_u <- shaped_reward(ctx, ctx')          # Matchsieg aus Delta team_wins
            Buffer <- (s_u, a_u, r_u, s'_u, done_u, mask'_u)   fuer alle u
            alle train_every Steps:
                Batch ziehen
                y = r + gamma * (1-done) * Q_target(s', argmax_a Q_online(s', a))
                Minimiere Huber(Q_online(s,a), y);  Target alle N Schritte syncen
"""
from __future__ import annotations

import os
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from . import geometry as geo
from . import rules
from .belief import Belief, MemorylessBelief
from .config import AgentConfig
from .features import FEATURE_DIM, THREAT_DIM, build_features, make_context, threat_features
from .model import N_ACTIONS, QNet, checkpoint_ensemble_dims
from .replay_buffer import ReplayBuffer
from .reward import surviving, unit_rewards

SAP_DROPOFF_ASSUMED = 0.5  # unit_sap_dropoff_factor ist nicht beobachtbar


class Agent_x:
    """DQN-Agent mit Gedaechtnis, Reward Shaping und Action Masking."""

    def __init__(
        self,
        player: str,
        agent_path: Optional[str] = None,
        name: str = "Sherlock Agent_X",
        cfg: Optional[AgentConfig] = None,
        train: bool = True,
        seed: Optional[int] = None,
    ) -> None:
        self.name = name
        self.agent_path = agent_path
        # Ohne explizite Config die des Checkpoints uebernehmen - so laedt der
        # Runner jede Ablations-Variante mit passender Architektur.
        self.cfg = cfg or self._cfg_from_checkpoint(agent_path) or AgentConfig()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.env_cfg: Optional[dict] = None

        self.n_actions = N_ACTIONS if self.cfg.use_sap else 5
        # 21.10.2026: cfg.threat_feats haengt THREAT_DIM Gefahr-Merkmale an (neue Netze)
        self.feat_dim = FEATURE_DIM + (THREAT_DIM if self.cfg.threat_feats else 0)
        self.q = QNet(self.feat_dim, self.n_actions, self.cfg.hidden, self.cfg.dueling).to(self.device)
        self.target_q = QNet(self.feat_dim, self.n_actions, self.cfg.hidden, self.cfg.dueling).to(self.device)
        self.opt = optim.Adam(self.q.parameters(), lr=self.cfg.lr)
        # Ensemble: weitere eingefrorene Netze (gleiche Architektur), deren
        # Q-Werte beim Handeln mit q gemittelt werden. Glaettet das Springen
        # einzelner DQN-Checkpoints. Nur zum Spielen, nicht zum Lernen.
        self.extra_q: list[QNet] = []
        self.cnn_policy = None  # optionale CNN-Policy zum Abstimmen (set_cnn_policy)
        self.cnn_weight, self.cnn_temp = 1.0, 0.2
        self.buffer = ReplayBuffer(self.cfg.buffer_capacity, self.feat_dim)
        self.rng = np.random.default_rng(seed)
        self._paths = rules.PathCache()

        self.training = bool(train)
        self.learn_enabled = True  # False: nur Transitions sammeln (Buffer auffuellen)
        self.autosave_on_terminate = True
        self.env_steps = 0
        self.learn_steps = 0
        self.recent_losses: list[float] = []

        self.belief = Belief(0, canonical=self.cfg.canonical, symmetry=self.cfg.use_symmetry,
                             early_inference=self.cfg.early_inference,
                             relic_filter=self.cfg.relic_filter,
                             subset_infer=self.cfg.subset_infer,
                             keep_dead=self.cfg.keep_dead,
                             keep_dead_fast=self.cfg.keep_dead_fast,
                             opp_infer=self.cfg.opp_infer,
                             stale_all=self.cfg.stale_all)
        # Sicht fuer die Features: voller Belief oder (Ablation) ohne Gedaechtnis
        self.feat_belief = (self.belief if self.cfg.use_belief
                            else MemorylessBelief(0, canonical=self.cfg.canonical,
                                             symmetry=self.cfg.use_symmetry))
        self._set_player(player)
        self._reset_episode_state()

        self.target_q.load_state_dict(self.q.state_dict())
        if agent_path:
            self.load_agent(agent_path)  # laedt auch target_q (nicht danach ueberschreiben)

    # ------------------------------------------------------------- identitaet
    def _set_player(self, player: str) -> None:
        self.player = player
        self.opp_player = "player_1" if player == "player_0" else "player_0"
        self.team_id = 0 if player == "player_0" else 1
        self.opp_team_id = 1 - self.team_id
        self.belief.set_team(self.team_id)
        self.feat_belief.set_team(self.team_id)

    def new_game(self, player: Optional[str] = None) -> None:
        """Vor jedem Spiel aufrufen (Netz/Buffer/Epsilon bleiben erhalten)."""
        if player is not None and player != self.player:
            self._set_player(player)
        for b in {id(self.belief): self.belief, id(self.feat_belief): self.feat_belief}.values():
            b.reset_game()
            b.set_team(self.team_id)
        self._reset_episode_state()

    @staticmethod
    def _cfg_from_checkpoint(path: Optional[str]) -> Optional[AgentConfig]:
        if not path or not os.path.isfile(path):
            return None
        try:
            ckpt = torch.load(path, map_location="cpu", weights_only=False)
        except Exception:
            return None
        if isinstance(ckpt, dict) and isinstance(ckpt.get("cfg"), dict):
            return AgentConfig.from_dict(ckpt["cfg"])
        return None

    def _reset_episode_state(self) -> None:
        self._prev_feats: dict[int, np.ndarray] = {}
        self._prev_actions: dict[int, int] = {}
        self._prev_masks: dict[int, np.ndarray] = {}
        self._prev_ctx: Optional[dict] = None
        self._sap_hits: dict[int, int] = {}
        self._enemy_prev: dict[int, tuple[int, int]] = {}
        self._cache: Optional[tuple] = None
        self._sticky_prev: Optional[tuple] = None  # (match_idx, {uid: Ziel}) fuer cfg.sticky
        # Diagnose pro Spiel (experiments: masked_frac, sap_attempts, ...)
        self.ep_stats = {"unit_steps": 0, "greedy_masked": 0, "explore_steps": 0,
                         "sap_attempts": 0, "sap_hits_est": 0}

    def episode_stats(self) -> dict:
        """Agent-spezifische Kennzahlen des laufenden/letzten Spiels."""
        st = dict(self.ep_stats)
        n = max(1, st["unit_steps"])
        st["greedy_masked_frac"] = st["greedy_masked"] / n
        st["relics_found"] = len(self.belief.relic_positions)
        st["known_point_tiles"] = int(self.belief.point_tiles.sum())
        st["belief_contradictions"] = int(self.belief.contradictions)
        return st

    # ------------------------------------------------------------ runner API
    def set_env_cfg(self, env_cfg) -> None:
        self.env_cfg = env_cfg
        W = int(env_cfg.get("map_width", 24))
        H = int(env_cfg.get("map_height", 24))
        for b in (self.belief, self.feat_belief):
            if (W, H) != (b.W, b.H):
                b.W, b.H = W, H
                b.reset_game()

    def set_to_eval_mode(self) -> None:
        self.training = False
        self.q.eval()

    def set_to_train_mode(self) -> None:
        self.training = True
        self.q.train()

    @property
    def epsilon(self) -> float:
        c = self.cfg
        if not self.training:
            return 0.0
        frac = min(1.0, self.env_steps / max(1, c.eps_decay_steps))
        return c.eps_start + frac * (c.eps_end - c.eps_start)

    # ------------------------------------------------------------- aktionen
    def _decide(self, obs) -> tuple:
        """Context, Features, Masken und Sap-Ziele fuer einen Step - mit Cache.

        act(obs_t+1) und update(..., next_obs=obs_t+1) brauchen genau dieselben
        Groessen; der Cache halbiert damit die Rechenzeit pro Step.
        """
        sid = int(np.asarray(obs["steps"]))
        if self._cache is not None and self._cache[0] == sid:
            return self._cache[1:]
        ctx = make_context(self, obs)
        if self.feat_belief is self.belief:
            fctx = ctx
        else:
            self.feat_belief.observe(obs)
            fctx = make_context(self, obs, belief=self.feat_belief)
        ids = [int(u) for u in ctx["ally_ids"].tolist()]
        saps = {u: self._best_sap_target(ctx, u) for u in ids}
        feats = {u: build_features(fctx, u) for u in ids}
        if self.cfg.threat_feats:
            feats = {u: np.concatenate([feats[u], threat_features(fctx, u)]) for u in ids}
        masks = {u: self._action_mask(ctx, u, saps[u]) for u in ids}
        self._cache = (sid, ctx, ids, feats, masks, saps)
        return self._cache[1:]

    def act(self, step: int, obs) -> np.ndarray:
        self.belief.observe(obs)
        max_units = int((self.env_cfg or {}).get("max_units", 16))
        actions = np.zeros((max_units, 3), dtype=int)

        self._prev_feats, self._prev_actions, self._prev_masks = {}, {}, {}
        self._sap_hits = {}
        # Match-Start (match_step 0): die sichtbaren Units sind Reste des alten
        # Matches, die Engine setzt sie im naechsten Step zurueck -> No-op und
        # kein Lern-Uebergang (sonst falsche Tod-Strafe fuer alle Units).
        if int(np.asarray(obs["match_steps"])) == 0:
            self._prev_ctx = None
            return actions

        ctx, ids, feat_map, mask_map, sap_targets = self._decide(obs)
        self._prev_ctx = ctx
        if not ids:
            return actions

        feats = np.stack([feat_map[u] for u in ids])
        masks = np.stack([mask_map[u] for u in ids])

        with torch.no_grad():
            t = torch.as_tensor(feats, dtype=torch.float32, device=self.device)
            qt = self.q(t)
            if self.extra_q and not self.training:
                # gemischtes Ensemble: Netze mit weniger Eingaben sehen die ersten Merkmale
                qt = torch.stack([qt] + [m(t[:, :m.feat_dim]) for m in self.extra_q]).mean(dim=0)
            q = qt.cpu().numpy()
        if self.cnn_policy is not None and not self.training:
            q = self._mix_cnn(ctx, ids, feats, masks, q)
        raw_greedy = q.argmax(axis=1)
        q[~masks] = -np.inf
        greedy = q.argmax(axis=1)
        st = self.ep_stats
        st["unit_steps"] += len(ids)
        st["greedy_masked"] += int((~masks[np.arange(len(ids)), raw_greedy]).sum())

        planned = np.zeros(len(ctx["enemy_coords"]))
        planned_fog = np.zeros((ctx["W"], ctx["H"]), dtype=bool)
        rammed: set = set()
        siege = None  # rules.SiegePlan, bei Bedarf einmal pro Step
        stationary = self._enemy_stationary(ctx)
        eps = self.epsilon
        for k, uid in enumerate(ids):
            legal = np.nonzero(masks[k])[0]
            if self.training and len(legal) > 0 and self.rng.random() < eps:
                st["explore_steps"] += 1
                if self.rng.random() < self.cfg.guided_prob:
                    a = self._guided_action(ctx, uid, masks[k], legal)
                else:
                    a = int(self.rng.choice(legal))
            else:
                a = int(greedy[k])
                if self.cfg.scripted_explore and a != geo.SAP:
                    a = self._explore_action(ctx, uid, masks[k], a)
                a = self._rule_override(ctx, uid, masks[k], a)
            self._prev_feats[uid] = feats[k]
            self._prev_actions[uid] = a
            self._prev_masks[uid] = masks[k]

            sap = sap_targets[uid]
            if self.cfg.ram:
                d = rules.ram_move(ctx, uid, masks[k], self.belief.point_tiles, rammed,
                                   self.cfg.ram_margin)
                if d is not None:
                    a = d
                    self._prev_actions[uid] = a
            if self.cfg.fog_sap and a == geo.STAY:
                sap = self._fog_sap(ctx, uid, planned_fog) or sap
                if sap is not sap_targets[uid]:
                    a = geo.SAP
                    self._prev_actions[uid] = a
            if self.cfg.contest_sap and a != geo.SAP and masks[k][geo.SAP]:
                # 20.10.2026: auf dem Ziel-Tile steht ein Gegner, den wir per Kollision nicht
                # schlagen -> aus der Entfernung auf genau dieses Tile sappen
                c_sap = self._contest_sap(ctx, uid)
                if c_sap is not None:
                    sap, a = c_sap, geo.SAP
                    self._prev_actions[uid] = a
            if self.cfg.pt_sap and a == geo.STAY and sap is not None and masks[k][geo.SAP]:
                # 20.10.2026: auf eigenem Punkte-Tile stehen bleiben UND sappen (Tile bleibt
                # besetzt). Diagnose: mit Sap-Gelegenheit sappte das Netz dort nur 9-12 %.
                x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
                on_tile = (self.belief.point_tiles[x, y] and ctx["first_on_tile"].get((x, y)) == uid)
                if self.cfg.pt_sap_zone:  # auch gestapelt oder auf Kandidaten-Tiles
                    on_tile = bool(self.belief.point_tiles[x, y] or self.belief.candidate[x, y])
                if on_tile and float(ctx["ally_ene"][uid]) >= ctx["sap_cost"] + self.cfg.pt_sap_reserve:
                    a = geo.SAP
                    self._prev_actions[uid] = a
            if (self.cfg.art_sap and a != geo.SAP and sap is not None and masks[k][geo.SAP]
                    and self._artillery_ok(ctx, uid, sap)):
                a = geo.SAP  # 21.10.2026: aus sicherer Position in einen Gegnerhaufen sappen
                self._prev_actions[uid] = a
            if (self.cfg.idle_sap and a == geo.STAY and sap is not None and masks[k][geo.SAP]
                    and float(ctx["ally_ene"][uid]) >= ctx["sap_cost"] + self.cfg.idle_sap_reserve):
                a = geo.SAP  # 20.10.2026: jede stehende Unit mit Ziel in Reichweite sappt
                self._prev_actions[uid] = a
            if self.cfg.siege and not self.training and float(ctx["ally_ene"][uid]) >= 0:
                x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
                holder = (self.belief.point_tiles[x, y]
                          and ctx["first_on_tile"].get((x, y)) == uid)
                if siege is None:
                    siege = rules.SiegePlan(ctx, self.belief, self.cfg.siege_prob,
                                            SAP_DROPOFF_ASSUMED)
                if not holder and siege.target_in_fortress(ctx["assigned"].get(int(uid))):
                    res = rules.siege_action(siege, ctx, uid, masks[k], self._paths,
                                             self.cfg.siege_min_score, self.cfg.siege_reserve)
                    if res is not None:
                        kind, val = res
                        a = geo.SAP if kind == "sap" else (val if kind == "move" else geo.STAY)
                        sap = val if kind == "sap" else sap
                        self._prev_actions[uid] = a
                        st["siege_steps"] = st.get("siege_steps", 0) + 1
            if a == geo.SAP and sap is not None and self.cfg.smart_sap:
                sap = rules.plan_sap(ctx, uid, planned, stationary, self.belief.point_tiles)
                if sap is None:
                    a = geo.STAY
                    self._prev_actions[uid] = a
            if a == geo.SAP and sap is not None:
                dx, dy, hits = sap
                if self.belief.mirrored:
                    dx, dy = geo.mirror_delta(dx, dy)
                actions[uid] = [geo.SAP, dx, dy]
                self._sap_hits[uid] = hits
                st["sap_attempts"] += 1
                st["sap_hits_est"] += int(hits > 0)
            else:
                d = a if a < 5 else geo.STAY
                if self.belief.mirrored:
                    d = geo.mirror_dir(d)
                actions[uid] = [d, 0, 0]
        return actions

    def set_cnn_policy(self, net, weight: float = 1.0, temp: float = 0.2) -> None:
        """CNN-Policy (cnn_model.PolicyNet) zum Abstimmen mit den Q-Netzen."""
        self.cnn_policy = net.eval() if net is not None else None
        self.cnn_weight, self.cnn_temp = float(weight), float(temp)

    def _mix_cnn(self, ctx, ids, feats, masks, q: np.ndarray) -> np.ndarray:
        """Abstimmung: log softmax(Q / T) + w * log pi_CNN, jeweils ueber erlaubte Aktionen."""
        from .cnn_model import map_planes
        pos = np.array([[int(ctx["ally_pos"][u][0]), int(ctx["ally_pos"][u][1])] for u in ids])
        m = torch.as_tensor(masks)
        with torch.no_grad():
            logits, _ = self.cnn_policy(torch.as_tensor(map_planes(ctx)[None]),
                                        torch.zeros(len(ids), dtype=torch.long),
                                        torch.as_tensor(pos, dtype=torch.long),
                                        torch.as_tensor(feats))
            lp = torch.log_softmax(logits.masked_fill(~m, -1e9), dim=1)
            lq = torch.log_softmax(torch.as_tensor(q).masked_fill(~m, -1e9) / self.cnn_temp, dim=1)
            return (lq + self.cnn_weight * lp).numpy()

    def _guided_action(self, ctx: dict, uid: int, mask: np.ndarray, legal: np.ndarray) -> int:
        """Heuristischer Explorationszug: Schritt Richtung zugewiesenes Ziel.

        Das ist nur die VERHALTENS-Policy waehrend der Exploration (behaviour
        policy). Gelernt wird weiterhin off-policy auf Q - Double DQN ist
        off-policy, deshalb ist ein informierter Explorationsprior erlaubt und
        beschleunigt das Auffinden der Punkte-Tiles massiv.
        """
        tgt = ctx["assigned"].get(int(uid))
        a = self._step_toward(ctx, uid, mask, tgt) if tgt is not None else None
        return int(self.rng.choice(legal)) if a is None else a

    def _explore_action(self, ctx: dict, uid: int, mask: np.ndarray, greedy: int) -> int:
        """cfg.scripted_explore: Units mit reinem Erkundungsziel (kein Punkte-/
        Kandidaten-Tile) laufen direkt zum Ziel. Analyse 12.10.: in den ersten 40
        Steps von Match 0 waehlt das Netz fast zur Haelfte "stehen" (wartet auf
        Energiefeldern nahe dem Spawn) und findet das Relic spaeter als Solution_92."""
        tgt = ctx["assigned"].get(int(uid))
        b = self.belief
        if tgt is None or b.point_tiles[tgt] or b.candidate[tgt]:
            return greedy
        a = self._step_toward(ctx, uid, mask, tgt)
        return greedy if a is None else a

    def _fog_sap(self, ctx: dict, uid: int, planned_fog: np.ndarray):
        """Sap in den Nebel fuer Units, die stehen wuerden, auf einem bewiesenen
        Punkte-Tile stehen (oder jede Unit mit cfg.fog_any) und Energie fuer
        Sap + Reserve haben."""
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        if not self.cfg.fog_any and not self.belief.point_tiles[x, y]:
            return None
        if float(ctx["ally_ene"][uid]) < ctx["sap_cost"] + self.cfg.fog_reserve:
            return None
        t = rules.fog_sap(ctx, uid, self.belief, planned_fog)
        if t is None:
            return None
        return t[0], t[1], 0

    def _contest_sap(self, ctx: dict, uid: int):
        """(dx, dy, Treffer) auf das zugewiesene Ziel-Tile, wenn dort ein sichtbarer
        Gegner steht, der mindestens so viel Energie hat wie wir nach einem Zug, und
        das Tile in Sap-Reichweite liegt; sonst None (cfg.contest_sap)."""
        tgt = ctx["assigned"].get(int(uid))
        ec = ctx["enemy_coords"]
        if tgt is None or len(ec) == 0:
            return None
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        if (x, y) == tuple(tgt) or max(abs(tgt[0] - x), abs(tgt[1] - y)) > int(ctx["sap_range"]):
            return None
        here = (ec[:, 0] == tgt[0]) & (ec[:, 1] == tgt[1])
        e = float(ctx["ally_ene"][uid])
        if not here.any() or float(ctx["enemy_energies"][here].sum()) < e - ctx["move_cost"]:
            return None
        if e < ctx["sap_cost"]:
            return None
        cheb = np.maximum(np.abs(ec[:, 0] - tgt[0]), np.abs(ec[:, 1] - tgt[1]))
        return int(tgt[0]) - x, int(tgt[1]) - y, int((cheb <= 1).sum())

    def _artillery_ok(self, ctx: dict, uid: int, sap) -> bool:
        """cfg.art_sap: lohnender Sap (>= art_min_hits Gegner) einer Unit, die nicht als
        Erste auf einem Punkte-Tile steht (dafuer gilt pt_sap), mit Energiereserve und
        (art_safe) ausserhalb der Manhattan-Reichweite aller sichtbaren sapfaehigen Gegner."""
        c = self.cfg
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        if self.belief.point_tiles[x, y] and ctx["first_on_tile"].get((x, y)) == uid:
            return False
        if int(sap[2]) < c.art_min_hits:
            return False
        if float(ctx["ally_ene"][uid]) < ctx["sap_cost"] + c.art_reserve:
            return False
        if c.art_safe and len(ctx["enemy_coords"]):
            ec = ctx["enemy_coords"]
            armed = ctx["enemy_energies"] >= ctx["sap_cost"]
            d = np.abs(ec[:, 0] - x) + np.abs(ec[:, 1] - y)
            if (armed & (d <= ctx["sap_range"])).any():
                return False
        return True

    def _enemy_stationary(self, ctx: dict) -> np.ndarray:
        """Je sichtbarem Gegner: stand er im letzten Step auf demselben Tile?"""
        ids = ctx["enemy_vis_ids"]
        ec = ctx["enemy_coords"]
        prev = self._enemy_prev
        out = np.array([prev.get(int(i)) == (int(c[0]), int(c[1])) for i, c in zip(ids, ec)],
                       dtype=bool)
        self._enemy_prev = {int(i): (int(c[0]), int(c[1])) for i, c in zip(ids, ec)}
        return out

    def _rule_override(self, ctx: dict, uid: int, mask: np.ndarray, a: int) -> int:
        """Regel-Schalter aus rules.py auf die Netz-Aktion anwenden (Sap bleibt)."""
        c = self.cfg
        if a == geo.SAP or not (c.pt_walk or c.pt_hold):
            return a
        b = self.belief
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        if c.pt_hold and b.point_tiles[x, y] and ctx["first_on_tile"].get((x, y)) == int(uid):
            return geo.STAY
        tgt = ctx["assigned"].get(int(uid))
        own_ok = not c.pt_walk_own or tgt is None or tgt[0] + tgt[1] < ctx["W"] - 1
        late_ok = b.match_idx >= c.pt_walk_from_match
        if (c.pt_walk and own_ok and late_ok and tgt is not None and b.point_tiles[tgt]
                and (x, y) != tuple(tgt)):
            dist = self._paths.get(ctx["step"], ctx["passable"], tgt)
            step = rules.first_step(dist, (x, y), mask, ctx["energy_map"])
            if step is not None:
                return step
        return a

    @staticmethod
    def _step_toward(ctx: dict, uid: int, mask: np.ndarray, tgt) -> Optional[int]:
        """Erlaubter Schritt Richtung tgt (laengere Achse zuerst), sonst None."""
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        dx, dy = tgt[0] - x, tgt[1] - y
        prefs = []
        if abs(dx) >= abs(dy):
            prefs = [geo.RIGHT if dx > 0 else geo.LEFT, geo.DOWN if dy > 0 else geo.UP]
        else:
            prefs = [geo.DOWN if dy > 0 else geo.UP, geo.RIGHT if dx > 0 else geo.LEFT]
        if dx == 0:
            prefs = [p for p in prefs if p not in (geo.LEFT, geo.RIGHT)]
        if dy == 0:
            prefs = [p for p in prefs if p not in (geo.UP, geo.DOWN)]
        for p in prefs:
            if mask[p]:
                return int(p)
        return None

    def _action_mask(self, ctx: dict, uid: int, sap_target) -> np.ndarray:
        mask = np.ones(self.n_actions, dtype=bool)
        if not self.cfg.mask_actions:
            if self.n_actions > 5:
                mask[geo.SAP] = sap_target is not None
            return mask

        W, H = ctx["W"], ctx["H"]
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        e = float(ctx["ally_ene"][uid])
        can_move = e >= ctx["move_cost"]
        for d in range(1, 5):
            tx, ty = x + int(geo.DIR_DX[d]), y + int(geo.DIR_DY[d])
            ok = can_move and 0 <= tx < W and 0 <= ty < H and bool(ctx["passable"][tx, ty])
            mask[d] = ok
        if self.cfg.safe_moves and len(ctx["enemy_coords"]):
            # 20.10.2026: nicht auf ein Tile mit sichtbarem, mindestens gleich starkem Gegner
            ec, ee = ctx["enemy_coords"], ctx["enemy_energies"]
            for d in range(1, 5):
                if mask[d]:
                    tx, ty = x + int(geo.DIR_DX[d]), y + int(geo.DIR_DY[d])
                    here = (ec[:, 0] == tx) & (ec[:, 1] == ty)
                    if here.any() and float(ee[here].sum()) >= e - ctx["move_cost"]:
                        mask[d] = False
        if self.n_actions > 5:
            mask[geo.SAP] = sap_target is not None and e >= ctx["sap_cost"]
        mask[geo.STAY] = True  # Stay ist immer legal
        return mask

    def _best_sap_target(self, ctx: dict, uid: int):
        """Bestes Sap-Ziel heuristisch waehlen: (dx, dy, geschaetzte Treffer).

        Das Netz entscheidet nur OB gesapt wird; das Zieltile waehlt die
        Heuristik (maximale getroffene Gegnerenergie inkl. 3x3-Streuung).
        """
        if self.n_actions <= 5:
            return None
        ec = ctx["enemy_coords"]
        if len(ec) == 0:
            return None
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        R = int(ctx["sap_range"])
        in_range = (np.abs(ec[:, 0] - x) <= R) & (np.abs(ec[:, 1] - y) <= R)
        if not in_range.any():
            return None
        energies = ctx["enemy_energies"]
        best, best_score, best_hits = None, -1.0, 0
        for i in np.where(in_range)[0]:
            tx, ty = int(ec[i, 0]), int(ec[i, 1])
            cheb = np.maximum(np.abs(ec[:, 0] - tx), np.abs(ec[:, 1] - ty))
            direct = cheb == 0
            splash = cheb == 1
            score = float(energies[direct].sum() + SAP_DROPOFF_ASSUMED * energies[splash].sum())
            if self.cfg.sap_pt_first and self.belief.point_tiles[tx, ty]:
                score += 1000.0  # 20.10.2026: Gegner auf Punkte-Tiles zuerst (sie punkten)
            if self.cfg.sap_kill_first and float(energies[direct].sum()) < float(ctx["sap_cost"]):
                score += 2000.0  # 20.10.2026: Treffer zerstoert die Unit -> Tile wird frei
            hits = int(direct.sum() + splash.sum())
            if score > best_score:
                best, best_score, best_hits = (tx - x, ty - y), score, hits
        if best is None:
            return None
        target = (best[0], best[1], best_hits)
        if self.cfg.sap_geometry:
            target = rules.better_sap_geometry(
                ctx, uid, target, best_score, SAP_DROPOFF_ASSUMED,
            )
        return target

    # ------------------------------------------------------------- lernen
    def update(self, step: int, obs, reward, action, terminated: bool, next_obs) -> None:
        self.env_steps += 1
        prev_ctx = self._prev_ctx
        self.belief.observe(next_obs)  # Belief weiterdrehen (act() ist idempotent)
        if prev_ctx is None or not self.training:
            if terminated and self.training and self.autosave_on_terminate:
                self.save_agent()
            return

        next_ctx, next_ids, next_feats, next_masks, _ = self._decide(next_obs)
        # Matchende (next match_step 0): fuer die Units endet hier ihre Episode.
        match_over = next_ctx["match_step"] == 0
        rewards = unit_rewards(self.cfg, prev_ctx, next_ctx,
                               self._prev_actions, self._sap_hits)

        alive_next = surviving(self.cfg, prev_ctx, next_ctx)
        zero = np.zeros(self.feat_dim, dtype=np.float32)
        dead_mask = np.zeros(self.n_actions, dtype=bool)
        dead_mask[geo.STAY] = True

        for uid, s in self._prev_feats.items():
            a = self._prev_actions[uid]
            if uid in alive_next:
                ns = next_feats[uid]
                nmask = next_masks[uid]
                done = bool(terminated) or match_over
            else:
                ns, nmask, done = zero, dead_mask, True
            self.buffer.push(s, a, rewards.get(uid, 0.0), ns, done, nmask)

        if (self.learn_enabled and len(self.buffer) >= self.cfg.learn_start
                and self.env_steps % self.cfg.train_every == 0):
            self._learn()

        if terminated and self.autosave_on_terminate:
            self.save_agent()

    def _learn(self) -> None:
        c = self.cfg
        s, a, r, ns, done, nmask = self.buffer.sample(c.batch_size, self.rng)
        dev = self.device
        s = torch.as_tensor(s, device=dev)
        ns = torch.as_tensor(ns, device=dev)
        a = torch.as_tensor(a, device=dev).unsqueeze(1)
        r = torch.as_tensor(r, device=dev).unsqueeze(1)
        done = torch.as_tensor(done, device=dev).unsqueeze(1)
        nmask = torch.as_tensor(nmask, device=dev)

        q = self.q(s).gather(1, a)
        with torch.no_grad():
            next_online = self.q(ns)
            next_online = next_online.masked_fill(~nmask, -float("inf"))
            if c.double_dqn:
                best = next_online.argmax(dim=1, keepdim=True)
                next_q = self.target_q(ns).gather(1, best)
            else:
                next_q = self.target_q(ns).masked_fill(~nmask, -float("inf")).max(
                    dim=1, keepdim=True).values
            next_q = torch.nan_to_num(next_q, neginf=0.0)
            y = r + (1.0 - done) * c.gamma * next_q

        loss = nn.functional.smooth_l1_loss(q, y)
        self.opt.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(self.q.parameters(), c.grad_clip)
        self.opt.step()

        self.learn_steps += 1
        self.recent_losses.append(float(loss.item()))
        if len(self.recent_losses) > 2000:
            self.recent_losses = self.recent_losses[-2000:]
        if self.learn_steps % c.target_update_every == 0:
            self.target_q.load_state_dict(self.q.state_dict())

    def pop_mean_loss(self) -> float:
        if not self.recent_losses:
            return float("nan")
        m = float(np.mean(self.recent_losses))
        self.recent_losses = []
        return m

    # ------------------------------------------------------- persistenz
    def save_agent(self, path: Optional[str] = None) -> None:
        path = path or self.agent_path
        if not path:
            return
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        torch.save(
            {
                "q": self.q.state_dict(),
                "target_q": self.target_q.state_dict(),
                "opt": self.opt.state_dict(),
                "env_steps": self.env_steps,
                "learn_steps": self.learn_steps,
                "cfg": self.cfg.to_dict(),
                "feature_dim": self.feat_dim,
                "n_actions": self.n_actions,
                "ensemble": [m.state_dict() for m in self.extra_q],
                "ensemble_dims": [m.feat_dim for m in self.extra_q],
            },
            path,
        )

    def save_buffer(self, path: str) -> None:
        """Replay Buffer separat speichern (gross, nur am Trainingsende)."""
        self.buffer.save(path)

    def load_buffer(self, path: str) -> int:
        return self.buffer.load(path)

    def load_agent(self, load_path: str) -> None:
        if not os.path.isfile(load_path):
            print(f"[{self.name}] {load_path} nicht gefunden - starte untrainiert.")
            return
        ckpt = torch.load(load_path, map_location=self.device, weights_only=False)
        if not isinstance(ckpt, dict) or "q" not in ckpt:
            self.q.load_state_dict(ckpt)  # reines state_dict (altes Format)
            return
        dims = checkpoint_ensemble_dims(ckpt, ckpt.get("feature_dim", FEATURE_DIM))
        if ckpt.get("feature_dim", FEATURE_DIM) != self.feat_dim or \
                ckpt.get("n_actions", self.n_actions) != self.n_actions:
            print(f"[{self.name}] Checkpoint passt nicht zur aktuellen Architektur "
                  f"(feature_dim/n_actions) - starte untrainiert.")
            return
        self.q.load_state_dict(ckpt["q"])
        self.target_q.load_state_dict(ckpt.get("target_q", ckpt["q"]))
        if "opt" in ckpt:
            try:
                self.opt.load_state_dict(ckpt["opt"])
            except (ValueError, KeyError):
                pass
        self.extra_q = []
        for sd, dim in zip(ckpt.get("ensemble", []), dims):
            # 21.10.2026: Eingabegroesse je Netz (V3-Netze 79 neben Gefahr-Netzen 101)
            m = QNet(int(dim), self.n_actions, self.cfg.hidden, self.cfg.dueling).to(self.device)
            m.load_state_dict(sd)
            m.eval()
            self.extra_q.append(m)
        if isinstance(ckpt.get("cnn_policy"), dict):
            from .cnn_model import PolicyNet
            cp = ckpt["cnn_policy"]
            net = PolicyNet(**cp["arch"])
            net.load_state_dict(cp["state"])
            self.set_cnn_policy(net, cp.get("weight", 1.0), cp.get("temp", 0.2))
        self.env_steps = int(ckpt.get("env_steps", 0))
        self.learn_steps = int(ckpt.get("learn_steps", 0))
        print(f"[{self.name}] geladen: {load_path} "
              f"(env_steps={self.env_steps}, eps={self.epsilon:.3f}, "
              f"Ensemble={1 + len(self.extra_q)} Netze)")
