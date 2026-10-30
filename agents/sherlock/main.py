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
from .features import FEATURE_DIM, THREAT_DIM, MAX_TILE_ENERGY, build_features, make_context, threat_features
from .model import N_ACTIONS, QNet, checkpoint_ensemble_dims
from .replay_buffer import ReplayBuffer
from .reward import surviving, unit_rewards

SAP_DROPOFF_ASSUMED = 0.5  # unit_sap_dropoff_factor ist nicht beobachtbar


def resolve_weights(path: Optional[str]) -> Optional[str]:
    """Gewichte neben main.py finden, wenn der Pfad vom Arbeitsverzeichnis aus fehlt.

    Abgabe 06.11.2026: Der Prof legt unseren Ordner an eine Stelle, die wir nicht
    kennen (agents/ oder Projektwurzel), und uebergibt z. B. 'Gruppe15/agent.pth'.
    Ohne diesen Rueckfall spielte der Agent still untrainiert und mit Standard-Config.
    Im Repo liegen keine .pth direkt neben main.py, dort aendert sich also nichts.
    """
    if not path or os.path.isfile(path):
        return path
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.basename(path))
    if os.path.isfile(local):
        print(f"[Sherlock] {path} nicht gefunden - nutze {local}")
        return local
    return path


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
        agent_path = resolve_weights(agent_path)
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

        self.training = bool(train) and not self.cfg.frozen
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
                             stale_all=self.cfg.stale_all,
                             nebula_infer_drift_safe=self.cfg.nebula_infer_drift_safe)
        self.belief.nebula_infer = bool(self.cfg.nebula_infer)
        self.belief.drift_track = bool(self.cfg.drift_track)
        self.belief.sym_map = bool(self.cfg.sym_map)
        self.belief.window_infer = bool(self.cfg.window_infer)
        self.belief.window_infer_all = bool(self.cfg.window_infer_all)
        self.belief.opp_point_infer = bool(self.cfg.opp_point_infer)
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
        self._searcher: Optional[tuple] = None  # (match_idx, uid, Ziel) fuer cfg.relic_search
        self._pred_pending: list = []  # cfg.dodge_verify: vorhergesagte, stehen gebliebene Ziele
        self._pred_n, self._pred_hit = 0, 0
        self._shape_pending: list = []  # cfg.dodge_shape: Ziele nur einer Form, stehen geblieben
        self._shape_ev = {"man": 0, "cheb": 0}
        from .param_est import ParamEstimator
        self.param_est = ParamEstimator()  # 21.10.2026: versteckte Parameter (Nebel, Streuschaden)
        self._first_relic_step = None  # 22.10.2026: fuer cand_rescue/rescue_after
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
            b.sensor_range = int(env_cfg["unit_sensor_range"]) if "unit_sensor_range" in env_cfg else None

    def set_to_eval_mode(self) -> None:
        self.training = False
        self.q.eval()

    def set_to_train_mode(self) -> None:
        if self.cfg.frozen:  # Battle-Abgabe bleibt im Spielmodus
            return
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
        use_est = ((self.cfg.nebula_avoid or self.cfg.dodge_auto or self.cfg.sap_dropoff_est or self.cfg.art_splash
                    or self.cfg.sap_still_splash) and (not self.training or self.cfg.rules_in_training_all))
        if use_est:
            self.param_est.observe(obs, self.team_id, None, self.env_cfg or {})
        actions = self._act(step, obs)
        if use_est:
            self.param_est.remember(obs, self.team_id, actions)
        return actions

    def _act(self, step: int, obs) -> np.ndarray:
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
            self._shape_pending = []  # Units verschwinden beim Match-Reset, das ist kein Treffer
            self._pred_pending = []
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
        planned_dmg = np.zeros(len(ctx["enemy_coords"]))  # sap_no_overkill: geplanter Schaden je Gegner
        planned_fog = np.zeros((ctx["W"], ctx["H"]), dtype=bool)
        rammed: set = set()
        siege = None  # rules.SiegePlan, bei Bedarf einmal pro Step
        reserve = None  # cfg.reserve_sap: Reservetiles, bei Bedarf einmal pro Step
        stationary = self._enemy_stationary(ctx)
        # 21.10.2026: vorhergesagte Solution_92-Treffer je eigener Unit (opp_model)
        # 21.10.2026: cfg.tactics_when_behind -> Kampftaktiken (dodge, art_sap) nur bei Rueckstand
        fight = not self.cfg.tactics_when_behind or ctx["opp_points"] > ctx["own_points"]
        dodge_on = self.cfg.dodge or (self.cfg.dodge_auto and self._dropoff() <= self.cfg.dodge_auto_max)
        if self.cfg.dodge_shape and not self.training:
            self._check_shapes(ctx)  # 30.10.2026: Treffer des letzten Steps -> Sap-Form des Gegners
        trusted = True
        if (self.cfg.dodge_verify or self.cfg.dodge_distrust > 0) and not self.training:
            self._check_predictions(ctx)
            predicted = self._predicted_hits(ctx, stationary)
            if self.cfg.dodge_distrust > 0:
                # 30.10.2026: Modell gilt, bis es sich in diesem Spiel als falsch erweist
                trusted = not (self._pred_n >= 6 and self._pred_hit < self.cfg.dodge_distrust * self._pred_n)
            else:
                trusted = self._pred_n >= 3 and self._pred_hit >= 0.6 * self._pred_n
            incoming = predicted if dodge_on and fight and trusted else {}
        else:
            predicted = {}
            incoming = (self._predicted_hits(ctx, stationary)
                        if dodge_on and not self.training and fight else {})
        # 30.10.2026: cfg.splash_dodge -> Nachbarn vorhergesagter Ziele bei sicherem Streufaktor >= 0,5
        splash_drop = self.param_est.dropoff(default=0.0) if self.cfg.splash_dodge and not self.training else 0.0
        splash_hits = ((incoming or predicted or self._predicted_hits(ctx, stationary))
                       if splash_drop >= 0.5 and fight and trusted else {})
        stage_info = self._stage_prepare(ctx) if self.cfg.stage_attack and not self.training else None
        eps = self.epsilon
        # 22.10.2026 (cfg.cand_rescue): Notfall, wenn trotz bekannter Relics kein Punkte-Tile bekannt ist
        # (z. B. 361050: Haufen im Nebel; 361255: Units laufen von Kandidaten weg) -> Kandidaten gezielt
        # testen (obey_target, neb_cand, idle_approach nur in diesem Fall aktiv)
        if self.belief.relic_positions and getattr(self, "_first_relic_step", None) is None:
            self._first_relic_step = int(ctx["step"])
        self._rescue = bool(self.cfg.cand_rescue and not self.training and self.belief.relic_positions
                            and not self.belief.point_tiles.any() and self.belief.match_step >= 10
                            and int(ctx["step"]) - self._first_relic_step >= self.cfg.rescue_after)
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
                if self.cfg.path_fix and (not self.training or self.cfg.rules_in_training) and 1 <= a <= 4:
                    a = self._path_fix(ctx, uid, masks[k], a)
                if self.cfg.stage_attack and not self.training and 1 <= a <= 4:
                    a = self._stage(ctx, uid, a, stage_info)
                if (self.cfg.obey_target or self._rescue) and not self.training and 1 <= a <= 4:
                    a = self._obey_target(ctx, uid, masks[k], a)
                if self.cfg.unstack and not self.training and a == geo.STAY:
                    a = self._unstack(ctx, uid, masks[k], a)
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
            if (self.cfg.fog_sap and a == geo.STAY
                    and ctx["sensor_range"] <= self.cfg.fog_sap_max_sensor):
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
                if self.cfg.reserve_sap and not on_tile and ctx["assigned"].get(int(uid)) == (x, y):
                    if reserve is None:  # 29.10.2026: Reserve auf ihrem Tile verteidigt wie ein Halter
                        from .features import reserve_tiles
                        reserve = reserve_tiles(self.belief, ctx["W"], ctx["H"])
                    on_tile = bool(reserve[x, y])
                if (on_tile and float(ctx["ally_ene"][uid]) >= ctx["sap_cost"] * (1 + self.cfg.sap_reserve_k) + self.cfg.pt_sap_reserve
                        and (not self.cfg.sap_relevant or self.training or self._sap_relevant(ctx, uid, sap))
                        and (not self.cfg.sap_still or (self.training and not self.cfg.rules_in_training_all)
                             or self._sap_still(ctx, uid, sap, stationary))):
                    a = geo.SAP
                    self._prev_actions[uid] = a
            if (self.cfg.art_sap and fight and a != geo.SAP and sap is not None and masks[k][geo.SAP]
                    and self._artillery_ok(ctx, uid, sap)
                    and (not self.cfg.art_still or self.training or self._sap_on_still(ctx, uid, sap, stationary))):
                a = geo.SAP  # 21.10.2026: aus sicherer Position in einen Gegnerhaufen sappen
                self._prev_actions[uid] = a
            if (self.cfg.idle_sap and a == geo.STAY and sap is not None and masks[k][geo.SAP]
                    and float(ctx["ally_ene"][uid]) >= ctx["sap_cost"] + self.cfg.idle_sap_reserve):
                a = geo.SAP  # 20.10.2026: jede stehende Unit mit Ziel in Reichweite sappt
                self._prev_actions[uid] = a
            if (self.cfg.nebula_avoid_mode == "soft" and 1 <= a <= 4
                    and self._harmful_nebula() >= self.cfg.nebula_avoid_min):
                a2 = self._soft_nebula(ctx, uid, masks[k], a)
                if a2 != a:
                    a = a2
                    self._prev_actions[uid] = a
                    st["nebula_detours"] = st.get("nebula_detours", 0) + 1
            if ((self.cfg.neb_cand or self._rescue) and not self.training and a == geo.STAY
                    and (self.cfg.idle_approach or self._rescue
                         or self._harmful_nebula() >= self.cfg.nebula_avoid_min)):
                d = self._neb_cand_step(ctx, uid, masks[k])
                if d is not None:
                    a = d
                    self._prev_actions[uid] = a
                    st["neb_cand_steps"] = st.get("neb_cand_steps", 0) + 1
            if a == geo.STAY and self._harmful_nebula() >= 25:
                x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
                if (ctx["nebula"][x, y] and not self.belief.point_tiles[x, y]
                        and not ((self.cfg.neb_cand or self._rescue) and self.belief.candidate[x, y])):
                    d = self._leave_nebula(ctx, uid, masks[k])
                    if d is not None:
                        a = d
                        self._prev_actions[uid] = a
                        st["nebula_exits"] = st.get("nebula_exits", 0) + 1
            if incoming.get(int(uid)) and a in (geo.STAY, geo.SAP):
                a2 = self._dodge(ctx, uid, masks[k], a, sap, incoming)
                if a2 != a:
                    a = a2
                    self._prev_actions[uid] = a
                    st["dodges"] = st.get("dodges", 0) + 1
            if splash_hits and 0 <= a <= 4 and not splash_hits.get(int(uid)):
                a2 = self._splash_dodge(ctx, uid, masks[k], a, splash_hits, splash_drop)
                if a2 != a:
                    a = a2
                    self._prev_actions[uid] = a
                    st["splash_dodges"] = st.get("splash_dodges", 0) + 1
            if predicted.get(int(uid), 0.0) >= 0.5 and a in (geo.STAY, geo.SAP):
                x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
                self._pred_pending.append((int(uid), x, y, float(ctx["ally_ene"][uid]), a == geo.SAP))
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
            if (a == geo.SAP and sap is not None and self.cfg.sap_still_all and not self.training
                    and not self._sap_on_still(ctx, uid, sap, stationary)):
                a = geo.STAY  # 22.10.2026: jedes Sap nur auf stehende Ziele (auch Netz/Artillerie)
                self._prev_actions[uid] = a
                st["moving_target_skips"] = st.get("moving_target_skips", 0) + 1
            if (a == geo.SAP and sap is not None and self.cfg.sap_no_overkill
                    and (not self.training or self.cfg.rules_in_training)):
                if self._overkill(ctx, uid, sap, planned_dmg):
                    a = geo.STAY  # 22.10.2026: Ziel ist durch geplante Saps schon tot -> Energie behalten
                    self._prev_actions[uid] = a
                    st["overkill_skips"] = st.get("overkill_skips", 0) + 1
            if self.cfg.holder_guard and not self.training and a in (geo.STAY, geo.SAP):
                d = self._holder_guard(ctx, uid, masks[k])
                if d is not None:
                    a = d  # 22.10.2026: staerkerer beweglicher Gegner neben dem Halter -> ausweichen
                    self._prev_actions[uid] = a
                    st["holder_guards"] = st.get("holder_guards", 0) + 1
            if a == geo.SAP and sap is not None and self.cfg.smart_sap:
                sap = rules.plan_sap(ctx, uid, planned, stationary, self.belief.point_tiles)
                if sap is None:
                    a = geo.STAY
                    self._prev_actions[uid] = a
            if (a == geo.SAP and sap is not None and self.cfg.sap_no_overkill
                    and (not self.training or self.cfg.rules_in_training)):
                self._plan_damage(ctx, uid, sap, planned_dmg)
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
        if self.cfg.dodge_shape and not self.training:
            self._record_shapes(ctx)
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
        if c.art_surplus:
            # 22.10.2026: Units auf dem Weg zu einem eigenen Punkte-Tile nicht aufhalten
            tgt = ctx["assigned"].get(int(uid))
            if tgt is not None and self.belief.point_tiles[tgt] and tgt[0] + tgt[1] <= ctx["W"] - 1:
                return False
        min_hits, safe = c.art_min_hits, c.art_safe
        drop_est = self.param_est.dropoff(default=0.0) if c.art_splash and not self.training else 0.0
        if c.art_splash and not self.training and drop_est >= c.splash_min_drop:
            # 30.10.2026: voller Streuschaden; unter splash_safe_below bleibt die Sicherheitspruefung
            min_hits, safe = c.art_splash_hits, safe and drop_est < c.splash_safe_below
        if int(sap[2]) < min_hits:
            return False
        if float(ctx["ally_ene"][uid]) < ctx["sap_cost"] * (1 + c.sap_reserve_k) + c.art_reserve:
            return False
        if safe and len(ctx["enemy_coords"]):
            ec = ctx["enemy_coords"]
            armed = ctx["enemy_energies"] >= ctx["sap_cost"]
            if c.art_safe_cheb:  # 22.10.2026: Engine erlaubt Saps im ganzen Quadrat
                d = np.maximum(np.abs(ec[:, 0] - x), np.abs(ec[:, 1] - y))
            else:
                d = np.abs(ec[:, 0] - x) + np.abs(ec[:, 1] - y)
            if (armed & (d <= ctx["sap_range"])).any():
                return False
        return True

    def _dropoff(self) -> float:
        """Sap-Streufaktor: Schaetzung aus param_est (22.10.2026), sonst die alte Annahme 0,5."""
        if (self.cfg.dodge_auto or self.cfg.sap_dropoff_est) and not self.training:
            return self.param_est.dropoff(default=SAP_DROPOFF_ASSUMED)
        return SAP_DROPOFF_ASSUMED

    def _check_predictions(self, ctx: dict) -> None:
        """cfg.dodge_verify: Haben die im letzten Step vorhergesagten, stehen gebliebenen Ziele
        wirklich einen direkten Treffer bekommen (Energieverlust >= 0,7 Sap-Kosten oder tot)?
        Nur dann verhaelt sich der Gegner wie das Solution_92-Modell (opp_model)."""
        pending, self._pred_pending = self._pred_pending, []
        if not pending:
            return
        alive = {int(u) for u in ctx["ally_ids"].tolist()}
        cost = float(ctx["sap_cost"])
        for uid, x, y, e, sapped in pending:
            self._pred_n += 1
            if uid not in alive:
                self._pred_hit += 1
                continue
            px, py = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
            if (px, py) != (x, y):
                self._pred_n -= 1  # anderer Slot/Respawn: keine Aussage
                continue
            loss = e - (cost if sapped else 0.0) - float(ctx["ally_ene"][uid])
            self._pred_hit += int(loss >= 0.7 * cost)

    def _sap_shape(self) -> str:
        """cfg.dodge_shape: Sap-Form des Gegners, Quadrat erst bei mehr Belegen als fuer die Raute."""
        return "cheb" if self._shape_ev["cheb"] > self._shape_ev["man"] else "man"

    def _record_shapes(self, ctx: dict) -> None:
        """cfg.dodge_shape: eigene Units merken, die nur die Raute oder nur das Quadrat als Ziel
        vorhersagt und die in diesem Step stehen bleiben (stehen oder sappen)."""
        from .opp_model import predict_sol92_saps
        man = {u for _, u in predict_sol92_saps(ctx, self.belief, shape="man")}
        cheb = {u for _, u in predict_sol92_saps(ctx, self.belief, shape="cheb")}
        for uid, form in [(u, "man") for u in man - cheb] + [(u, "cheb") for u in cheb - man]:
            a = self._prev_actions.get(uid)
            if a in (geo.STAY, geo.SAP):
                x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
                self._shape_pending.append((uid, x, y, float(ctx["ally_ene"][uid]), a == geo.SAP, form))

    def _check_shapes(self, ctx: dict) -> None:
        """cfg.dodge_shape: Hat eine gemerkte Unit einen direkten Treffer bekommen (Energieverlust
        >= 0,7 Sap-Kosten oder tot), zaehlt das fuer ihre Form. Bei sicherem Streufaktor 1,0 sieht
        der Streuschaden wie ein direkter Treffer aus, dann keine Aussage."""
        pending, self._shape_pending = self._shape_pending, []
        if not pending or self.param_est.dropoff(default=0.5) >= 1.0:
            return
        alive = {int(u) for u in ctx["ally_ids"].tolist()}
        cost = float(ctx["sap_cost"])
        for uid, x, y, e, sapped, form in pending:
            if uid not in alive:
                self._shape_ev[form] += 1
                continue
            if (int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])) != (x, y):
                continue  # anderer Slot/Respawn: keine Aussage
            loss = e - (cost if sapped else 0.0) - float(ctx["ally_ene"][uid])
            self._shape_ev[form] += int(loss >= 0.7 * cost)

    def _harmful_nebula(self) -> float:
        """cfg.nebula_avoid: geschaetzter Nebelabzug, falls >= nebula_avoid_min, sonst 0."""
        if not self.cfg.nebula_avoid or (self.training and not self.cfg.rules_in_training_all):
            return 0.0
        neb = self.param_est.nebula(default=None)
        return float(neb) if neb is not None and neb >= self.cfg.nebula_avoid_min else 0.0

    def _soft_nebula(self, ctx: dict, uid: int, mask: np.ndarray, a: int) -> int:
        """nebula_avoid_mode 'soft': Zug in schaedlichen Nebel (kein Punkte-Tile) durch einen
        gleich guten Zug ohne Nebel ersetzen (gleiche BFS-Verkuerzung zum Ziel); ohne Alternative
        nur mit genug Energie (>= 2x Nebelabzug) hinein, sonst warten. Keine Maske: Wege durch
        Nebel bleiben moeglich (22.10.2026: die Maske kostete auf leichten Karten Spiele)."""
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        tx, ty = x + int(geo.DIR_DX[a]), y + int(geo.DIR_DY[a])
        if not ctx["nebula"][tx, ty] or self.belief.point_tiles[tx, ty]:
            return a
        if (self.cfg.neb_cand or getattr(self, "_rescue", False)) and self.belief.candidate[tx, ty]:
            return a  # 22.10.2026: Kandidaten im Nebel testen (sonst nie Punkte-Tiles, 361050)
        tgt = ctx["assigned"].get(int(uid))
        if tgt is not None:
            dist = self._paths.get(ctx["step"], ctx["passable"], tgt)
            here = dist[x, y]
            want = dist[tx, ty]
            for d in range(1, 5):
                if d == a or not mask[d]:
                    continue
                nx, ny = x + int(geo.DIR_DX[d]), y + int(geo.DIR_DY[d])
                if ctx["nebula"][nx, ny] or dist[nx, ny] < 0:
                    continue
                if dist[nx, ny] <= want or (here >= 0 and dist[nx, ny] < here):
                    return d
        if float(ctx["ally_ene"][uid]) >= 2 * self._harmful_nebula():
            return a
        return geo.STAY if not ctx["nebula"][x, y] else a

    def _neb_cand_step(self, ctx: dict, uid: int, mask: np.ndarray) -> Optional[int]:
        """cfg.neb_cand: wartende Unit (nicht auf Punkte-Tile), deren Ziel ein Kandidat im schaedlichen
        Nebel ist und hoechstens 3 BFS-Schritte entfernt liegt, geht hin (Energie faellt nur auf 0,
        Solution_92 sitzt dort ebenso). Diagnose 361050: Relic-Haufen ganz im Nebel 25, 0 Punkte."""
        tgt = ctx["assigned"].get(int(uid))
        b = self.belief
        if tgt is None or not b.candidate[tgt]:
            return None
        approach = self.cfg.idle_approach or getattr(self, "_rescue", False)
        if not approach and not ctx["nebula"][tgt]:
            return None
        ec = ctx["enemy_coords"]
        x0, y0 = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        if approach and len(ec) and (np.maximum(np.abs(ec[:, 0] - x0), np.abs(ec[:, 1] - y0)) <= 2).any():
            return None
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        if b.point_tiles[x, y] or (x, y) == tuple(tgt):
            return None
        dist = self._paths.get(ctx["step"], ctx["passable"], tgt)
        if not 0 < int(dist[x, y]) <= 3:
            return None
        return rules.first_step(dist, (x, y), mask, ctx["energy_map"])

    def _leave_nebula(self, ctx: dict, uid: int, mask: np.ndarray) -> Optional[int]:
        """Unit steht in schaedlichem Nebel (kein Punkte-Tile): Zug auf ein Nicht-Nebel-Tile,
        bevorzugt Richtung Ziel, sonst mit mehr Feldenergie. None, wenn keiner moeglich ist."""
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        tgt = ctx["assigned"].get(int(uid))
        best, best_s = None, -np.inf
        for d in range(1, 5):
            if not mask[d]:
                continue
            tx, ty = x + int(geo.DIR_DX[d]), y + int(geo.DIR_DY[d])
            if ctx["nebula"][tx, ty]:
                continue
            s = float(np.clip(ctx["energy_map"][tx, ty], -20, 20)) / 20.0
            if tgt is not None and abs(tgt[0] - tx) + abs(tgt[1] - ty) < abs(tgt[0] - x) + abs(tgt[1] - y):
                s += 2.0
            if s > best_s:
                best, best_s = d, s
        return best

    def _predicted_hits(self, ctx: dict, stationary: np.ndarray) -> dict[int, float]:
        """cfg.dodge: erwartete direkte Solution_92-Saps je eigener Unit-ID (opp_model).
        Gewicht 0,85 fuer Schuetzen, die schon im letzten Step dort standen, sonst 0,5
        (gemessen am 21.10. auf 500720-500729: Trefferquote der Vorhersage je Fall)."""
        from .opp_model import predict_sol92_saps
        out: dict[int, float] = {}
        self._shooters: dict[int, list] = {}
        shape = self._sap_shape() if self.cfg.dodge_shape else "man"
        for k, uid in predict_sol92_saps(ctx, self.belief, shape=shape):
            p = 0.85 if (k < len(stationary) and stationary[k]) else 0.5
            out[uid] = out.get(uid, 0.0) + p
            self._shooters.setdefault(uid, []).append(
                (int(ctx["enemy_coords"][k][0]), int(ctx["enemy_coords"][k][1])))
        return out

    def _splash_dodge(self, ctx: dict, uid: int, mask: np.ndarray, a: int, hits: dict, drop: float) -> int:
        """cfg.splash_dodge (30.10.2026): Unit, die selbst kein vorhergesagtes Ziel ist, aber am Ende dieses
        Steps (stehend oder nach ihrem Zug) neben oder auf dem Tile vorhergesagter Ziele stuende, bekaeme bei
        sicher geschaetztem Streufaktor >= 0,5 mindestens splash_dodge_min ihrer Energie als Streuschaden ->
        stattdessen Stehen oder der Zug mit dem geringsten vorhergesagten Schaden (bevorzugt freie Punkte-Tiles,
        Richtung Ziel). Auch das Zurueckgehen in die Streuzone wird so verhindert, solange die Gefahr besteht.
        Diagnose V11 gegen sol92_sq (Dev A, verlorene Matches 2/3): Streuschaden auf uns 2.016 bei Streufaktor
        1,0 und 1.190 bei 0,5, direkter Schaden nur 651 bzw. 688."""
        cost = float(ctx["sap_cost"])
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        e = float(ctx["ally_ene"][uid])
        shots = [(int(ctx["ally_pos"][v][0]), int(ctx["ally_pos"][v][1]), h)
                 for v, h in hits.items() if v != int(uid)]

        def damage(tx, ty):
            d = 0.0
            for ox, oy, h in shots:
                cheb = max(abs(ox - tx), abs(oy - ty))
                d += h * cost * (1.0 if cheb == 0 else drop if cheb == 1 else 0.0)
            return d

        dest = (x, y) if a == geo.STAY else (x + int(geo.DIR_DX[a]), y + int(geo.DIR_DY[a]))
        planned = damage(*dest)
        if planned < self.cfg.splash_dodge_min * max(e, 1.0):
            return a
        occupied = {(int(ctx["ally_pos"][v][0]), int(ctx["ally_pos"][v][1]))
                    for v in ctx["ally_ids"].tolist() if int(v) != int(uid)}
        tgt = ctx["assigned"].get(int(uid))
        best, best_s = a, -np.inf
        for d in range(0, 5):
            if d != geo.STAY and not mask[d]:
                continue
            tx, ty = (x, y) if d == geo.STAY else (x + int(geo.DIR_DX[d]), y + int(geo.DIR_DY[d]))
            dmg = damage(tx, ty)
            if dmg >= planned or e - (0 if d == geo.STAY else ctx["move_cost"]) - dmg < 0:
                continue
            s = -dmg / cost
            if self.belief.point_tiles[tx, ty] and (tx, ty) not in occupied:
                s += 2.0
            if tgt is not None and abs(tgt[0] - tx) + abs(tgt[1] - ty) < abs(tgt[0] - x) + abs(tgt[1] - y):
                s += 1.0
            s += float(np.clip(ctx["energy_map"][tx, ty], -20, 20)) / 20.0
            if s > best_s:
                best, best_s = d, s
        return best

    def _dodge(self, ctx: dict, uid: int, mask: np.ndarray, a: int, sap, hits: dict) -> int:
        """cfg.dodge: Unit, die stehen oder sappen wuerde und vorhergesagt direkt getroffen
        wird, weicht einen Schritt aus (Solution_92 zielt auf die aktuelle Position, beim
        Ausweichen trifft nur der Streuschaden). Bevorzugt ein freies bekanntes Punkte-Tile.
        dodge_mode 'lethal': nur wenn Stehenbleiben die Unit vermutlich toetet; ist der Tod
        auch beim Ausweichen sicher, wird stattdessen noch gesappt (falls moeglich)."""
        c = self.cfg
        cost, drop = float(ctx["sap_cost"]), self._dropoff()
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        e = float(ctx["ally_ene"][uid])
        n = hits[int(uid)]
        others = [(int(ctx["ally_pos"][v][0]), int(ctx["ally_pos"][v][1]), h)
                  for v, h in hits.items() if v != int(uid)]

        def damage(tx, ty, moved):
            d = n * cost * (drop if moved else 1.0)
            for ox, oy, h in others:
                cheb = max(abs(ox - tx), abs(oy - ty))
                d += h * cost * (1.0 if cheb == 0 else drop if cheb == 1 else 0.0)
            return d

        stay_left = e - damage(x, y, False) - (cost if a == geo.SAP else 0.0)
        if c.dodge_mode == "lethal" and stay_left >= 0:
            return a
        occupied = {(int(ctx["ally_pos"][v][0]), int(ctx["ally_pos"][v][1]))
                    for v in ctx["ally_ids"].tolist() if int(v) != int(uid)}
        tgt = ctx["assigned"].get(int(uid))
        best, best_s = None, -np.inf
        for d in range(1, 5):
            if not mask[d]:
                continue
            tx, ty = x + int(geo.DIR_DX[d]), y + int(geo.DIR_DY[d])
            if e - ctx["move_cost"] - damage(tx, ty, True) < 0:
                continue  # stirbt auch nach dem Ausweichen
            s = 0.0
            if self.belief.point_tiles[tx, ty] and (tx, ty) not in occupied:
                s += 2.0
            if tgt is not None and abs(tgt[0] - tx) + abs(tgt[1] - ty) < abs(tgt[0] - x) + abs(tgt[1] - y):
                s += 1.0
            s += float(np.clip(ctx["energy_map"][tx, ty], -20, 20)) / 20.0
            if c.dodge_bait:
                # 22.10.2026: Koeder - in Reichweite der eigenen Schuetzen bleiben, solange dort andere
                # eigene Units stehen (sie haben niedrigere IDs und bleiben so unbeschossen); nicht
                # neben eigene Units ziehen (Streuschaden)
                R = int(ctx["sap_range"])
                shooters = getattr(self, "_shooters", {}).get(int(uid), [])
                cheb = c.dodge_shape and self._sap_shape() == "cheb"  # 30.10.2026: Reichweite wie das Modell

                def reach(sx, sy, ox, oy):
                    return (max(abs(sx - ox), abs(sy - oy)) if cheb else abs(sx - ox) + abs(sy - oy)) <= R

                guarded = any(reach(sx, sy, ox, oy) for sx, sy in shooters for ox, oy in occupied)
                if guarded and all(reach(sx, sy, tx, ty) for sx, sy in shooters):
                    s += 3.5
                if any(max(abs(ox - tx), abs(oy - ty)) <= 1 for ox, oy in occupied):
                    s -= 2.0
            if s > best_s:
                best, best_s = d, s
        if best is not None:
            return best
        if stay_left < 0 and a != geo.SAP and sap is not None and mask[geo.SAP]:
            return geo.SAP  # Tod nicht zu vermeiden: vorher noch schiessen
        return a

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

    def _sap_cover(self, ctx: dict, uid: int, sap) -> tuple[np.ndarray, np.ndarray]:
        """Je sichtbarem Gegner: direkt getroffen / daneben getroffen (Chebyshev 0 / 1 vom Zieltile)."""
        ec = ctx["enemy_coords"]
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        tx, ty = x + int(sap[0]), y + int(sap[1])
        cheb = np.maximum(np.abs(ec[:, 0] - tx), np.abs(ec[:, 1] - ty)) if len(ec) else np.zeros(0)
        return cheb == 0, cheb == 1

    def _sap_still(self, ctx: dict, uid: int, sap, stationary: np.ndarray) -> bool:
        """cfg.sap_still (22.10.2026): Halter-Saps (pt_sap) nur, wenn ein direkt getroffener Gegner
        steht (letzter Step unbewegt oder auf bekanntem Punkte-Tile). Ziehende Erkunder weichen dem
        direkten Treffer aus; Diagnose: unser direkter Treffer je Sap ~30 % der Kosten, Solution_92 ~43 %."""
        direct, _ = self._sap_cover(ctx, uid, sap)
        if not direct.any():
            return False
        if self.cfg.sap_still_splash and self.param_est.dropoff(default=0.0) >= self.cfg.splash_min_drop:
            return True  # 30.10.2026: voller Streuschaden trifft auch nach einem Schritt
        ec = ctx["enemy_coords"]
        on_pt = self.belief.point_tiles[ec[:, 0], ec[:, 1]]
        still = (stationary[: len(ec)] if len(stationary) >= len(ec) else np.zeros(len(ec), dtype=bool)) | on_pt
        return bool((direct & still).any())

    def _enemy_mobile(self, ctx: dict) -> np.ndarray:
        """Je sichtbarem Gegner: kann er sich im naechsten Step bewegen? Nicht beweglich, wer auf
        einem bekannten Punkte-Tile steht oder (cfg.mobile_seen) im letzten Step am selben Ort stand
        (Solution_92-Sammler sitzen fest). 22.10.2026: ohne bekannte Punkte-Tiles galt sonst jeder
        Sammler als beweglich und collision_guard sperrte die Zuege rund um die Relics (361255)."""
        ec = ctx["enemy_coords"]
        mobile = ~self.belief.point_tiles[ec[:, 0], ec[:, 1]]
        if self.cfg.mobile_seen:
            prev = self._enemy_prev
            same = np.array([prev.get(int(i)) == (int(c[0]), int(c[1]))
                             for i, c in zip(ctx["enemy_vis_ids"], ec)], dtype=bool)
            if len(same) == len(mobile):
                mobile &= ~same
        return mobile

    def _holder_guard(self, ctx: dict, uid: int, mask: np.ndarray) -> Optional[int]:
        """cfg.holder_guard (22.10.2026): Steht neben unserer stehenden Unit (kardinal) ein
        beweglicher, sichtbarer Gegner mit mindestens unserer Energie, zieht er im naechsten Step oft
        auf unser Tile (Kollision: wir sterben). Diagnose: haeufigste Kollisionsart (5,5 Tote je
        Verlustspiel). Ausweichen auf ein freies Nachbartile, das an keinen solchen Gegner grenzt;
        bevorzugt Punkte-Tiles, dann mehr Feldenergie. None, wenn keine Gefahr oder kein Ausweg."""
        ec, ee = ctx["enemy_coords"], ctx["enemy_energies"]
        if not len(ec):
            return None
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        e = float(ctx["ally_ene"][uid])
        mobile = self._enemy_mobile(ctx)
        strong = mobile & (ee - ctx["move_cost"] >= e)
        man = np.abs(ec[:, 0] - x) + np.abs(ec[:, 1] - y)
        if not (strong & (man == 1)).any():
            return None
        best, best_s = None, -np.inf
        for d in range(1, 5):
            if not mask[d]:
                continue
            tx, ty = x + int(geo.DIR_DX[d]), y + int(geo.DIR_DY[d])
            dt = np.abs(ec[:, 0] - tx) + np.abs(ec[:, 1] - ty)
            if ((dt == 0) | (strong & (dt <= 1))).any():
                continue
            sc = (5.0 if self.belief.point_tiles[tx, ty] else 0.0) + float(np.clip(ctx["energy_map"][tx, ty], -20, 20)) / 20.0
            if sc > best_s:
                best, best_s = d, sc
        return best

    def _sap_on_still(self, ctx: dict, uid: int, sap, stationary: np.ndarray) -> bool:
        """cfg.sap_still_all: Sap lohnt, wenn ein stehender Gegner direkt oder mindestens zwei
        stehende Gegner im 3x3-Bereich getroffen werden (stehend = unbewegt oder auf Punkte-Tile)."""
        direct, near = self._sap_cover(ctx, uid, sap)
        ec = ctx["enemy_coords"]
        if not len(ec):
            return False
        on_pt = self.belief.point_tiles[ec[:, 0], ec[:, 1]]
        still = (stationary[: len(ec)] if len(stationary) >= len(ec) else np.zeros(len(ec), dtype=bool)) | on_pt
        return bool((direct & still).any() or int((near & still).sum()) >= 2)

    def _sap_relevant(self, ctx: dict, uid: int, sap) -> bool:
        """cfg.sap_relevant (22.10.2026): Halter-Saps (pt_sap) nur auf Gegner auf oder direkt neben
        bekannten Punkte-Tiles (sie punkten oder greifen gleich an). Durchziehende Erkunder kosten den
        Halter sonst die Energie, die er gegen Kollision und Void braucht (Diagnose 360019)."""
        direct, near = self._sap_cover(ctx, uid, sap)
        ec = ctx["enemy_coords"]
        pt = self.belief.point_tiles
        W, H = ctx["W"], ctx["H"]
        for k in np.nonzero(direct | near)[0]:
            ex, ey = int(ec[k][0]), int(ec[k][1])
            if pt[max(0, ex - 1):min(W, ex + 2), max(0, ey - 1):min(H, ey + 2)].any():
                return True
        return False

    def _overkill(self, ctx: dict, uid: int, sap, planned_dmg: np.ndarray) -> bool:
        """cfg.sap_no_overkill (22.10.2026): Sap ist verschwendet, wenn alle direkt getroffenen
        Gegner laut geplanter Treffer sterben und daneben kein noch lebender Gegner steht.
        Trefferplanung setzt unveraenderte Zielpositionen voraus; mit sap_overkill_recovery
        wird auch die maximal moegliche Feld-Erholung nach den Saps beruecksichtigt."""
        direct, near = self._sap_cover(ctx, uid, sap)
        if not direct.any():
            return False
        rest = ctx["enemy_energies"].astype(np.float64) - planned_dmg
        if self.cfg.sap_overkill_recovery:
            # Beobachtete Feldenergie ist kein sicherer Wert fuer den naechsten Step:
            # Energieknoten koennen inzwischen gedriftet sein. Oeffentliche Obergrenze
            # nutzen (Engine-Default 20), ohne versteckte Parameter/Zustaende zu lesen.
            # Nebel/Void reduzieren Energie nur; nichtpositive Felder beleben negative
            # Energie nicht wieder. Genau null bleibt am Leben (Engine clippt bei 0).
            max_gain = max(0.0, float((self.env_cfg or {}).get("max_energy_per_tile", MAX_TILE_ENERGY)))
            rest += max_gain
        alive_direct = direct & (rest >= 0)
        alive_near = near & (rest >= 0)
        return not alive_direct.any() and not alive_near.any()

    def _plan_damage(self, ctx: dict, uid: int, sap, planned_dmg: np.ndarray) -> None:
        direct, near = self._sap_cover(ctx, uid, sap)
        cost = float(ctx["sap_cost"])
        drop = self._dropoff() if self.cfg.sap_dropoff_est else SAP_DROPOFF_ASSUMED
        planned_dmg += np.where(direct, cost, 0.0) + np.where(near, int(cost * min(drop, 0.25)), 0.0)

    def _stage_prepare(self, ctx: dict):
        """cfg.stage_attack (22.10.2026): Gefahrenzone = Tiles in Manhattan-Reichweite sichtbarer,
        sapfaehiger Gegner auf bekannten Punkte-Tiles (Solution_92-Schuetzen). Zaehlt eigene Units, die
        mit Ziel in der Zone schon nahe davor stehen (Gruppe)."""
        ec, ee = ctx["enemy_coords"], ctx["enemy_energies"]
        if not len(ec):
            return None
        pt = self.belief.point_tiles
        shooters = [(int(x), int(y)) for (x, y), e in zip(ec.tolist(), ee.tolist())
                    if e >= ctx["sap_cost"] and pt[int(x), int(y)]]
        if not shooters:
            return None
        R = int(ctx["sap_range"])
        W, H = ctx["W"], ctx["H"]
        xs, ys = np.indices((W, H))
        zone = np.zeros((W, H), dtype=bool)
        for sx, sy in shooters:
            zone |= (np.abs(xs - sx) + np.abs(ys - sy)) <= R
        near = 0
        for u in ctx["ally_ids"].tolist():
            tgt = ctx["assigned"].get(int(u))
            if tgt is None or not zone[tgt]:
                continue
            x, y = int(ctx["ally_pos"][u][0]), int(ctx["ally_pos"][u][1])
            d = min(abs(x - sx) + abs(y - sy) for sx, sy in shooters)
            if d <= R + 3:
                near += 1
        return zone, near

    def _stage(self, ctx: dict, uid: int, a: int, info) -> int:
        """Vor dem Betreten der Gefahrenzone warten, bis mindestens cfg.stage_min eigene Units mit Ziel
        in der Zone davor stehen (sonst laufen sie einzeln hinein und werden einzeln abgeschossen,
        Diagnose 361038). Ausnahmen: viel Energie (>= 3 Saps) oder spaet im Match (>= stage_until)."""
        if info is None:
            return a
        zone, near = info
        tgt = ctx["assigned"].get(int(uid))
        if tgt is None or not zone[tgt]:
            return a
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        tx, ty = x + int(geo.DIR_DX[a]), y + int(geo.DIR_DY[a])
        if zone[x, y] or not zone[tx, ty]:
            return a
        if near >= self.cfg.stage_min or self.belief.match_step >= self.cfg.stage_until:
            return a
        if float(ctx["ally_ene"][uid]) >= 3 * float(ctx["sap_cost"]):
            return a
        self.ep_stats["stage_waits"] = self.ep_stats.get("stage_waits", 0) + 1
        return geo.STAY

    def _obey_target(self, ctx: dict, uid: int, mask: np.ndarray, a: int) -> int:
        """cfg.obey_target (22.10.2026): Zug, der die BFS-Distanz zum zugewiesenen Punkte- oder
        Kandidaten-Tile vergroessert, ohne dass ein sichtbarer Gegner nahe ist (Chebyshev <= 2), durch
        den ersten Schritt des kuerzesten Wegs ersetzen. Diagnose 361255: sechs Units liefen in Match 1
        von ihren Kandidaten weg, kein Punkte-Tile wurde bis Match 3 gelernt."""
        tgt = ctx["assigned"].get(int(uid))
        b = self.belief
        if tgt is None or not (b.point_tiles[tgt] or b.candidate[tgt]):
            return a
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        if b.point_tiles[x, y]:
            return a
        ec = ctx["enemy_coords"]
        if len(ec) and (np.maximum(np.abs(ec[:, 0] - x), np.abs(ec[:, 1] - y)) <= 2).any():
            return a
        dist = self._paths.get(ctx["step"], ctx["passable"], tgt)
        here = int(dist[x, y])
        if here <= 0:
            return a
        tx, ty = x + int(geo.DIR_DX[a]), y + int(geo.DIR_DY[a])
        nd = int(dist[tx, ty])
        if nd >= 0 and nd <= here:
            return a
        step = rules.first_step(dist, (x, y), mask, ctx["energy_map"])
        if step is None:
            return a
        self.ep_stats["obey_fixes"] = self.ep_stats.get("obey_fixes", 0) + 1
        return int(step)

    def _path_fix(self, ctx: dict, uid: int, mask: np.ndarray, a: int) -> int:
        """cfg.path_fix (22.10.2026): Greedy-Falle an Asteroidenwaenden beheben. Netz und
        scripted_explore ziehen nach Luftlinie (dx/dy-Merkmale); fuehrt der Zug nach Luftlinie
        naeher ans zugewiesene Ziel, auf dem BFS-Weg aber nicht (Sackgasse), stattdessen den
        ersten Schritt des kuerzesten Wegs nehmen. Seitliche/abgewandte Zuege bleiben (Absicht)."""
        tgt = ctx["assigned"].get(int(uid))
        if tgt is None:
            return a
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        tx, ty = x + int(geo.DIR_DX[a]), y + int(geo.DIR_DY[a])
        dist = self._paths.get(ctx["step"], ctx["passable"], tgt)
        here = int(dist[x, y])
        if here <= 0:
            return a  # Ziel erreicht oder (nach Gedaechtnis) unerreichbar
        nd = int(dist[tx, ty])
        if 0 <= nd < here:
            return a
        gx, gy = int(tgt[0]), int(tgt[1])
        if abs(gx - tx) + abs(gy - ty) >= abs(gx - x) + abs(gy - y):
            return a
        step = rules.first_step(dist, (x, y), mask, ctx["energy_map"])
        if step is None:
            return a
        self.ep_stats["path_fixes"] = self.ep_stats.get("path_fixes", 0) + 1
        return int(step)

    def _unstack(self, ctx: dict, uid: int, mask: np.ndarray, a: int) -> int:
        """cfg.unstack (22.10.2026): Unit steht gestapelt auf einem Punkte-Tile, das schon eine
        andere eigene Unit haelt (bringt keinen Punkt) -> BFS-Schritt zum eigenen Ziel statt warten.
        Diagnose (Verlustspiele V7): 0,5 gestapelte Units pro Step, waehrend eigene Punkte-Tiles frei sind."""
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        if not self.belief.point_tiles[x, y] or ctx["first_on_tile"].get((x, y), int(uid)) == int(uid):
            return a
        tgt = ctx["assigned"].get(int(uid))
        if tgt is None or tuple(tgt) == (x, y):
            return a
        dist = self._paths.get(ctx["step"], ctx["passable"], tgt)
        step = rules.first_step(dist, (x, y), mask, ctx["energy_map"])
        if step is None:
            return a
        self.ep_stats["unstacks"] = self.ep_stats.get("unstacks", 0) + 1
        return int(step)

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
        if self.cfg.collision_guard and (not self.training or self.cfg.rules_in_training) and len(ctx["enemy_coords"]):
            # 22.10.2026: kein Zug auf ein Tile, auf das ein beweglicher (nicht auf bekanntem
            # Punkte-Tile stehender), mindestens gleich starker sichtbarer Gegner im selben Step
            # ziehen kann. Diagnose: 1/3 der Kollisionstode entstehen, wenn beide auf dasselbe Tile ziehen.
            ec, ee = ctx["enemy_coords"], ctx["enemy_energies"]
            mobile = self._enemy_mobile(ctx)
            e_after = e - ctx["move_cost"]
            for d in range(1, 5):
                if mask[d]:
                    tx, ty = x + int(geo.DIR_DX[d]), y + int(geo.DIR_DY[d])
                    adj = (np.abs(ec[:, 0] - tx) + np.abs(ec[:, 1] - ty) == 1) & mobile & (ee >= e_after)
                    if adj.any():
                        mask[d] = False
        if self.cfg.stack_guard and not self.training:
            for d in range(1, 5):
                tx, ty = x + int(geo.DIR_DX[d]), y + int(geo.DIR_DY[d])
                if mask[d] and self.belief.point_tiles[tx, ty] and ctx["ally_count"][tx, ty] > 0:
                    mask[d] = False  # 22.10.2026: nicht auf ein schon eigenes Punkte-Tile stapeln
        neb = self._harmful_nebula()
        if neb and self.cfg.nebula_avoid_mode == "mask":
            for d in range(1, 5):
                tx, ty = x + int(geo.DIR_DX[d]), y + int(geo.DIR_DY[d])
                if mask[d] and ctx["nebula"][tx, ty] and not self.belief.point_tiles[tx, ty]:
                    mask[d] = False  # 21.10.2026: geschaetzter Nebelabzug >= nebula_avoid_min
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
        # 22.10.2026: cfg.sap_dropoff_est -> geschaetzter Streufaktor statt fester Annahme 0,5
        drop = self._dropoff() if self.cfg.sap_dropoff_est else SAP_DROPOFF_ASSUMED
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
            score = float(energies[direct].sum() + drop * energies[splash].sum())
            if self.cfg.sap_pt_first and self.belief.point_tiles[tx, ty]:
                score += 1000.0  # 20.10.2026: Gegner auf Punkte-Tiles zuerst (sie punkten)
            if self.cfg.sap_kill_first and float(energies[direct].sum()) < float(ctx["sap_cost"]):
                score += 2000.0  # 20.10.2026: Treffer zerstoert die Unit -> Tile wird frei
            if self.cfg.sap_kill_safe:
                # 22.10.2026: wie sap_kill_first, aber nur lebende Gegner (negative sind schon tot
                # und verschwinden vor dem Sap) und inklusive Feldenergie ihres Tiles
                gain = max(float(ctx["energy_map"][tx, ty]), 0.0)
                e_dir = energies[direct]
                if len(e_dir) and e_dir.min() >= 0 and float(e_dir.max()) + gain < float(ctx["sap_cost"]):
                    score += 2000.0
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
        if self.cfg.frozen and not path:  # Runner-Aufruf: Battle-Abgabe nicht ueberschreiben
            return
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


# Beispiel des Profs fuer die Battle-Abgabe lautet 'Gruppe21.main.Agent'; beide Namen gehen.
Agent = Agent_x
