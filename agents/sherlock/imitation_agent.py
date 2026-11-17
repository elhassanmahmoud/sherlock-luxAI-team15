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
from .prev_move import MoveTracker


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
        prev_move = bool(kw.pop("prev_move_input", False))
        members = []
        own_tile = True
        if net is None and agent_path:
            ckpt = torch.load(agent_path, map_location="cpu", weights_only=False)
            # Aeltere Schueler (vor dem 15.11., 15:40) lernten den Zielkopf ohne das eigene Feld; dessen Bewertung ist
            # dort untrainiert. Fuer sie bleibt das eigene Feld als Ziel gesperrt.
            own_tile = bool(ckpt.get("sap_own_tile", False))
            # 16.11.2026 (v6): letzte eigene Bewegung je Unit als 5 Zusatzmerkmale (prev_move.py)
            prev_move = bool(ckpt.get("prev_move_input", False))
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
        self.prev_move_input = prev_move
        self.move_tracker = MoveTracker()
        if members:
            if prev_move and any(m.arch["feat_dim"] != self.net.arch["feat_dim"] for m in members):
                raise ValueError("Ensemble-Mitglieder brauchen dieselben Eingaben (letzte Bewegung)")
            self.extra_nets = members

    def _reset_episode_state(self) -> None:
        super()._reset_episode_state()
        tracker = getattr(self, "move_tracker", None)
        if tracker is not None:
            tracker.reset()
        tactics = getattr(self, "_tactics", None)
        if tactics is not None:
            tactics.reset()

    def prev_move_features(self, ctx, ids, pos) -> np.ndarray:
        """Fuenf Zusatzmerkmale je Unit (prev_move.py) und die Positionen dieses Zugs fuer den naechsten merken."""
        ms = int(ctx["match_step"])
        extra = self.move_tracker.features(ms, ids, pos)
        live = [float(ctx["ally_ene"][u]) >= 0 for u in ids]
        self.move_tracker.record(ms, ids, pos, live)
        return extra

    def _point_holder_rows(self, ctx, ids, pos) -> list[int]:
        """Zeilen der Units, die als erste auf einem bekannten Punktefeld stehen (cfg.imit_hold_points)."""
        points = np.asarray(self.belief.point_tiles, dtype=bool)
        first = ctx["first_on_tile"]
        rows = []
        for k in range(len(ids)):
            tile = (int(pos[k][0]), int(pos[k][1]))
            if points[tile] and first.get(tile) == int(ids[k]):
                rows.append(k)
        return rows

    def _fill_points(self, ctx, ids, pos, logp: np.ndarray, acts: np.ndarray, max_dist: int) -> np.ndarray:
        """cfg.imit_fill_points > 0 (17.11.2026): Jedes bekannte Punktefeld, auf dem keine eigene Unit steht und auf das
        in diesem Zug keine eigene Unit zieht, bekommt die nächste eigene Unit (Manhattan-Abstand höchstens max_dist),
        die weder schießt noch ein Punktefeld hält. Sie nimmt unter den erlaubten Bewegungen, die den
        Abstand verkleinern, die vom Netz am höchsten bewertete. Gegen Kaggle blieben im dritten Match 3,5-5 bekannte
        Punktefelder leer, während der Schüler nur 2-3 besetzte."""
        points = np.asarray(self.belief.point_tiles, dtype=bool)
        here = [(int(p[0]), int(p[1])) for p in pos]
        taken = set(here)
        for k, (x, y) in enumerate(here):
            a = int(acts[k])
            if 1 <= a <= 4:
                taken.add((x + int(geo.DIR_DX[a]), y + int(geo.DIR_DY[a])))
        free = [(int(tx), int(ty)) for tx, ty in zip(*np.nonzero(points)) if (int(tx), int(ty)) not in taken]
        if not free:
            return acts
        first = ctx.get("first_on_tile", {})
        pairs = []
        for k, (x, y) in enumerate(here):
            if int(acts[k]) == geo.SAP or (points[x, y] and first.get((x, y), int(ids[k])) == int(ids[k])):
                continue  # Schützen und Halter bleiben; zusätzlich gestapelte Units auf Punktefeldern dürfen weiter
            for t in free:
                d = abs(x - t[0]) + abs(y - t[1])
                if d <= max_dist:
                    pairs.append((d, k, t))
        pairs.sort()
        acts = acts.copy()
        used_k, used_t = set(), set()
        for d, k, t in pairs:
            if k in used_k or t in used_t:
                continue
            x, y = here[k]
            best, best_lp = None, -np.inf
            for a in range(1, 5):
                nx, ny = x + int(geo.DIR_DX[a]), y + int(geo.DIR_DY[a])
                if np.isfinite(logp[k, a]) and abs(nx - t[0]) + abs(ny - t[1]) < d and logp[k, a] > best_lp:
                    best, best_lp = a, float(logp[k, a])
            if best is None:
                continue
            used_k.add(k)
            used_t.add(t)
            if int(acts[k]) != best:
                acts[k] = best
                self.ep_stats["fill_moves"] = self.ep_stats.get("fill_moves", 0) + 1
        return acts

    def _end_fill(self, ctx, ids, pos, logp: np.ndarray, acts: np.ndarray, n: int) -> np.ndarray:
        """cfg.imit_end_fill > 0 (17.11.2026, "Matchende-Sturm"): In den letzten n punktenden Schritten eines Matches
        zählt nur noch, wie viele Punktefelder besetzt sind; die Engine entfernt am Matchende alle Units. Halter (erste
        eigene Unit auf einem bekannten Punktefeld) bleiben stehen, ein Schuss bleibt erlaubt (er bewegt die Unit
        nicht). Jedes bekannte Punktefeld ohne eigene Unit, ohne eigenen Zug darauf und ohne sichtbaren Gegner bekommt
        die nächste eigene Unit ohne Punktefeld, ohne Schuss und ohne Zug auf ein Punktefeld, die es vor dem Matchende
        erreicht (Manhattan-Abstand höchstens die verbleibenden Schritte). Sie nimmt unter den erlaubten Bewegungen,
        die den Abstand verkleinern, die vom Netz am höchsten bewertete.

        Die Aktion bei match_steps m wirkt im Schritt m und punktet noch, wenn m <= max_match_steps (luxai_s3/env.py:
        Punkte vor der Prüfung match_steps >= max_steps_in_match). Ab dieser Aktion punkten also
        max_match_steps - m + 1 Schritte."""
        left = int(ctx["max_match_steps"]) - int(ctx["match_step"]) + 1
        if not 0 < left <= n:
            return acts
        points = np.asarray(self.belief.point_tiles, dtype=bool)
        first = ctx.get("first_on_tile", {})
        here = [(int(p[0]), int(p[1])) for p in pos]
        acts = acts.copy()
        holders = set()
        for k, tile in enumerate(here):
            if points[tile] and first.get(tile) == int(ids[k]):
                holders.add(k)
                if 1 <= int(acts[k]) <= 4:
                    acts[k] = geo.STAY
                    self.ep_stats["end_hold"] = self.ep_stats.get("end_hold", 0) + 1
        taken, filling = set(), set()
        for k, (x, y) in enumerate(here):
            a = int(acts[k])
            if 1 <= a <= 4:
                dest = (x + int(geo.DIR_DX[a]), y + int(geo.DIR_DY[a]))
                taken.add(dest)
                if 0 <= dest[0] < points.shape[0] and 0 <= dest[1] < points.shape[1] and points[dest]:
                    filling.add(k)
            else:
                taken.add((x, y))
        ec = np.asarray(ctx.get("enemy_coords", np.zeros((0, 2), dtype=int))).reshape(-1, 2)
        enemy = {(int(x), int(y)) for x, y in ec}
        free = [(int(tx), int(ty)) for tx, ty in zip(*np.nonzero(points))
                if (int(tx), int(ty)) not in taken and (int(tx), int(ty)) not in enemy]
        if not free:
            return acts
        pairs = []
        for k, (x, y) in enumerate(here):
            if k in holders or k in filling or int(acts[k]) == geo.SAP:
                continue
            for t in free:
                d = abs(x - t[0]) + abs(y - t[1])
                if 0 < d <= left:
                    pairs.append((d, k, t))
        pairs.sort()
        used_k, used_t = set(), set()
        for d, k, t in pairs:
            if k in used_k or t in used_t:
                continue
            x, y = here[k]
            best, best_lp = None, -np.inf
            for a in range(1, 5):
                nx, ny = x + int(geo.DIR_DX[a]), y + int(geo.DIR_DY[a])
                if np.isfinite(logp[k, a]) and abs(nx - t[0]) + abs(ny - t[1]) < d and logp[k, a] > best_lp:
                    best, best_lp = a, float(logp[k, a])
            if best is None:
                continue
            used_k.add(k)
            used_t.add(t)
            if int(acts[k]) != best:
                acts[k] = best
                self.ep_stats["end_fill_moves"] = self.ep_stats.get("end_fill_moves", 0) + 1
        return acts

    def _world_maps(self):
        """Punktefelder, Energiefeld und Nebel aus dem Gedächtnis in Weltkoordinaten (für die Taktikschicht)."""
        b = self.belief
        maps = [np.asarray(b.point_tiles, dtype=bool), np.asarray(b.energy_map, dtype=float),
                np.asarray(b.nebula, dtype=bool)]
        if b.mirrored:
            maps = [geo.mirror_map(m) for m in maps]
        return maps

    def _apply_tactics(self, spec: str, obs, actions: np.ndarray) -> np.ndarray:
        """cfg.imit_tactics (17.11.2026): Taktikschicht (tactics_layer.py) hinter der Policy, wie R3T hinter R3. Die
        Parameterschätzung (Streufaktor, Nebelabzug) sieht dabei die tatsächlich gespielten Befehle."""
        from .tactics_layer import Tactics, TacticsCfg

        if getattr(self, "_tactics", None) is None or self._tactics_spec != spec:
            self._tactics = Tactics(TacticsCfg.parse(spec))
            self._tactics_spec = spec
        est = self.param_est
        env_cfg = self.env_cfg or {}
        est.observe(obs, self.team_id, None, env_cfg)
        points, energy, nebula = self._world_maps()
        W, H = points.shape
        assigned = {}
        ctx = getattr(self, "_prev_ctx", None) or {}
        for uid, t in (ctx.get("assigned") or {}).items():
            if t is not None:
                t = (int(t[0]), int(t[1]))
                assigned[int(uid)] = geo.mirror_xy(*t, W, H) if self.belief.mirrored else t
        out = self._tactics.apply(actions, obs, self.team_id, env_cfg, point_tiles=points, energy_map=energy,
                                  nebula_map=nebula, nebula_drain=est.nebula(default=None),
                                  dropoff=est.dropoff(default=0.5), assigned=assigned)
        est.remember(obs, self.team_id, out)
        changed = int(np.any(out != actions, axis=1).sum())
        if changed:
            self.ep_stats["tactics_units"] = self.ep_stats.get("tactics_units", 0) + changed
        return out

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

    def _cover_moves(self, ctx, ids, pos, logp: np.ndarray, acts: np.ndarray, margin: float) -> np.ndarray:
        """cfg.imit_cover ("Tarnung"): Bewegungen auf vom Gegner gesehene Felder durch fast gleich gute Bewegungen auf
        verborgene Felder ersetzen. Gesehen = Chebyshev-Abstand zu einem sichtbaren Gegner hoechstens seine Sichtweite,
        Nebelfelder gelten als Deckung. Stehenbleiben ist keine Alternative (keine zusaetzliche Passivitaet)."""
        ec = np.asarray(ctx.get("enemy_coords", np.zeros((0, 2), dtype=int))).reshape(-1, 2)
        if len(ec) == 0:
            return acts
        W, H = int(ctx["W"]), int(ctx["H"])
        rng = int(ctx.get("sensor_range") or 2)
        seen = np.zeros((W, H), dtype=bool)
        for ex, ey in ec:
            seen[max(0, int(ex) - rng):int(ex) + rng + 1, max(0, int(ey) - rng):int(ey) + rng + 1] = True
        seen &= ~np.asarray(ctx["nebula"], dtype=bool)
        acts = acts.copy()
        for k in range(len(ids)):
            a = int(acts[k])
            if not 1 <= a <= 4:
                continue
            x, y = int(pos[k][0]), int(pos[k][1])
            tx, ty = x + int(geo.DIR_DX[a]), y + int(geo.DIR_DY[a])
            if not (0 <= tx < W and 0 <= ty < H) or not seen[tx, ty]:
                continue
            best, best_lp = None, -np.inf
            for d in range(1, 5):
                if d == a or not np.isfinite(logp[k, d]):
                    continue
                nx, ny = x + int(geo.DIR_DX[d]), y + int(geo.DIR_DY[d])
                if 0 <= nx < W and 0 <= ny < H and not seen[nx, ny] and logp[k, d] > best_lp:
                    best, best_lp = d, float(logp[k, d])
            if best is not None and best_lp >= float(logp[k, a]) - margin:
                acts[k] = best
                self.ep_stats["cover_moves"] = self.ep_stats.get("cover_moves", 0) + 1
        return acts

    def act(self, step: int, obs) -> np.ndarray:
        actions = self._policy_act(step, obs)
        spec = str(getattr(self.cfg, "imit_tactics", "") or "")
        if spec:
            actions = self._apply_tactics(spec, obs, actions)
        return actions

    def _policy_act(self, step: int, obs) -> np.ndarray:
        max_units = int((self.env_cfg or {}).get("max_units", 16))
        actions = np.zeros((max_units, 3), dtype=int)
        self._prev_feats, self._prev_actions, self._prev_masks = {}, {}, {}
        self._sap_hits = {}
        fz = featurize(self, obs)
        self.last_fz = fz  # DAgger: Eingaben dieses Schritts fuer die Lehrer-Labels
        if fz is None:
            return actions
        ctx, ids, feats, masks, sap_targets, planes, pos = fz
        if getattr(self, "prev_move_input", False):  # last_fz (DAgger-Archiv) behaelt 79 Merkmale; 5 aus Positionen
            feats = np.concatenate([feats, self.prev_move_features(ctx, ids, pos)], axis=1).astype(np.float32)
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
                bias = torch.full((len(ids),), stay_bias, dtype=logp.dtype)
                if getattr(self.cfg, "imit_hold_points", False):
                    for k in self._point_holder_rows(ctx, ids, pos):
                        bias[k] = 0.0
                        self.ep_stats["hold_points"] = self.ep_stats.get("hold_points", 0) + 1
                logp[:, geo.STAY] -= bias
            sap_bias = float(getattr(self.cfg, "imit_sap_bias", 0.0) or 0.0)
            if sap_bias:
                logp[:, geo.SAP] += sap_bias  # gesperrte Schuesse bleiben -inf
            acts = logp.argmax(dim=1).numpy()
            if getattr(self.cfg, "imit_unstack", False):
                acts = self._unstack_actions(ctx, ids, pos, logp.numpy(), acts)
            cover = float(getattr(self.cfg, "imit_cover", 0.0) or 0.0)
            if cover > 0:
                acts = self._cover_moves(ctx, ids, pos, logp.numpy(), acts, cover)
            fill = int(getattr(self.cfg, "imit_fill_points", 0) or 0)
            if fill > 0:
                acts = self._fill_points(ctx, ids, pos, logp.numpy(), acts, fill)
            end_fill = int(getattr(self.cfg, "imit_end_fill", 0) or 0)
            if end_fill > 0:
                acts = self._end_fill(ctx, ids, pos, logp.numpy(), acts, end_fill)
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
