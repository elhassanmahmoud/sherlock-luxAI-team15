"""Feature-Engineering: ein Vektor pro Einheit, alles im kanonischen Raum.

`make_context()` berechnet einmal pro Step alle gemeinsamen Groessen
(Karten, Zielzuweisung, Gegnerinfos). `build_features()` liest daraus pro Unit
den Vektor. Das haelt die Kosten bei 16 Units pro Step klein.

FEATURE_NAMES dokumentiert das Layout exakt -> fuer die Praesentation einfach
`python -m scripts.show_features` (bzw. den Namen ausgeben) nutzen.
"""
from __future__ import annotations

import numpy as np

from . import geometry as geo
from .belief import TILE_ASTEROID, _dilate

MAX_UNIT_ENERGY = 400.0   # feste Engine-Konstante (nicht randomisiert)
MAX_TILE_ENERGY = 20.0
N_MATCHES = 3

_DIR_NAMES = ["c", "u", "r", "d", "l"]


def _names() -> list[str]:
    n = [
        # --- eigene Lage + bekannte Spielparameter (10)
        "self_x", "self_y", "self_energy", "self_low_energy",
        "match_step_frac", "match_idx_frac",
        "cfg_move_cost", "cfg_sap_cost", "cfg_sap_range", "cfg_sensor_range",
        # --- Punktestand (4)
        "own_points", "point_diff", "own_wins", "opp_wins",
    ]
    # --- naechstes Ziel je Klasse (5 x 4 = 20)
    for cls in ["point", "cand", "relic", "unexp", "assigned"]:
        n += [f"{cls}_dx", f"{cls}_dy", f"{cls}_dist", f"{cls}_exists"]
    # --- aktuelles Tile (5)
    n += ["on_point", "on_cand", "on_nebula", "allies_here", "redundant_here"]
    # --- lokale Umgebung: 5 Richtungen x 6 Kanaele (30)
    for d in _DIR_NAMES:
        n += [f"{d}_passable", f"{d}_energy", f"{d}_point", f"{d}_cand",
              f"{d}_unexp", f"{d}_allies"]
    # --- Gegner (6)
    n += ["enemy_dx", "enemy_dy", "enemy_dist", "enemy_energy_rel",
          "enemies_in_sap", "enemies_visible"]
    # --- globale Zaehler (4)
    n += ["own_units", "known_points", "explored_frac", "cand_frac"]
    return n


FEATURE_NAMES = _names()
FEATURE_DIM = len(FEATURE_NAMES)

# --- Gefahr-Merkmale (Schalter cfg.threat_feats, 21.10.2026), an die 79 angehaengt:
# je Tile (stehen + 4 Zuege) sapfaehige sichtbare Gegner in Manhattan-Reichweite (so
# zielt Solution_92) und im Sap-Quadrat (Engine), Gegnerenergie auf dem Tile
# (Kollision) und daneben (Void); dazu bester Sap-Treffer und besetzte Punkte-Tiles.
THREAT_NAMES = [f"{d}_{k}" for d in _DIR_NAMES
                for k in ("threat_man", "threat_sq", "enemy_here", "enemy_adj")]
THREAT_NAMES += ["best_sap_hits", "enemy_on_points"]
THREAT_DIM = len(THREAT_NAMES)


def _nearest(coords: np.ndarray, x: int, y: int, W: int, H: int):
    """(dx/W, dy/H, dist/(W+H), exists) zum naechsten Punkt in `coords`."""
    if coords is None or len(coords) == 0:
        return 0.0, 0.0, 1.0, 0.0
    d = np.abs(coords[:, 0] - x) + np.abs(coords[:, 1] - y)
    k = int(np.argmin(d))
    return (
        float(coords[k, 0] - x) / W,
        float(coords[k, 1] - y) / H,
        float(d[k]) / (W + H),
        1.0,
    )


def grid_targets(coords: np.ndarray, block: int) -> np.ndarray:
    """Pro block x block-Feld das unerkundete Tile, das der Blockmitte am naechsten liegt."""
    if len(coords) == 0:
        return coords
    keys = (coords[:, 0] // block) * 1000 + coords[:, 1] // block
    centre = (coords // block) * block + (block - 1) / 2.0
    d = np.abs(coords - centre).sum(axis=1)
    order = np.lexsort((d, keys))
    first = np.ones(len(order), dtype=bool)
    first[1:] = keys[order][1:] != keys[order][:-1]
    return coords[order[first]]


def bfs_maps(passable: np.ndarray, starts: np.ndarray) -> np.ndarray:
    """BFS-Schrittzahl von jeder Startposition zu jedem Tile (n x W x H, -1 unerreichbar),
    alle Starts gleichzeitig als Wellenfront (4er-Nachbarschaft, nur passierbare Tiles)."""
    starts = np.asarray(starts, dtype=np.int64).reshape(-1, 2)
    n = len(starts)
    W, H = passable.shape
    dist = np.full((n, W, H), -1, dtype=np.int16)
    if n == 0:
        return dist
    idx = np.arange(n)
    ok = (starts[:, 0] >= 0) & (starts[:, 0] < W) & (starts[:, 1] >= 0) & (starts[:, 1] < H)
    front = np.zeros((n, W, H), dtype=bool)
    front[idx[ok], starts[ok, 0], starts[ok, 1]] = True
    dist[front] = 0
    seen = front.copy()
    free = np.asarray(passable, dtype=bool)[None]
    d = 0
    while front.any():
        d += 1
        nb = np.zeros_like(front)
        nb[:, 1:, :] |= front[:, :-1, :]
        nb[:, :-1, :] |= front[:, 1:, :]
        nb[:, :, 1:] |= front[:, :, :-1]
        nb[:, :, :-1] |= front[:, :, 1:]
        nb &= free & ~seen
        dist[nb] = d
        seen |= nb
        front = nb
    return dist


def assign_targets(belief, unit_ids, unit_pos, W, H,
                   enemy_half_penalty: float = 0.0,
                   seen_before_penalty: float = 0.0,
                   grid: int = 0, stale: int = 0,
                   cand_quota: int = 0, far_opp: int = 0,
                   prev: dict | None = None, sticky: float = 0.0,
                   far_cand: bool = False, cand_boost: float = 0.0,
                   explore_quota: int = 0, explore_until: int = 75,
                   energy_pref: float = 0.0, reach: bool = False,
                   home_reserve: bool = False, relic_scout: int = 0, scout_until: int = 60,
                   scout_stale: int = 20) -> dict[int, tuple[int, int]]:
    """Greedy-Zuweisung: jede Unit bekommt ein EIGENES Ziel.

    Prioritaet: bewiesene Punkte-Tiles < Kandidaten-Tiles < unerkundete Tiles.
    Eindeutige Ziele verhindern, dass alle Units auf dasselbe Tile laufen
    (ein Tile bringt maximal einen Punkt, Slide 38) und liefern gleichzeitig
    das Potential fuer das Reward-Shaping (siehe reward.py).

    enemy_half_penalty > 0: Ziele in der gegnerischen Kartenhaelfte werden
    teurer (cfg.home_first). Mit Symmetrie kennt der Belief auch die Punkte-
    Tiles beim Gegner; ohne Malus laufen Units dorthin und sterben (Analyse
    11.10.: 7,2 statt 5,8 Tote pro Match).

    seen_before_penalty > 0 (cfg.explore_memory): unerkundete Tiles, die schon in
    einem frueheren Match gesehen wurden, sind als Erkundungsziel teurer. Sonst
    laeuft der Agent jedes Match wieder in dieselbe (falsche) Ecke, weil
    `explored` pro Match zurueckgesetzt wird (Analyse 11.10.: auf manchen Karten
    in allen 3 Matches kein Relic gefunden).

    grid > 0 (cfg.explore_grid): Erkundungsziele nur je ein Tile pro grid x grid-
    Block, alle Bloecke statt nur die naechsten am Schwerpunkt -> die Units
    verteilen sich ueber die Karte statt als Klumpen zu wandern.
    stale > 0 (cfg.explore_stale): siehe Belief.explore_coords.

    cand_quota > 0 (cfg.cand_quota, 19.10.2026): die `cand_quota` Kandidaten-Tiles
    der eigenen Haelfte, die am naechsten an bekannten Punkte-Tiles liegen,
    rangieren direkt hinter den eigenen Punkte-Tiles und vor denen der
    Gegnerhaelfte. Sonst bekommt in spaeten Matches keine Unit mehr ein
    Kandidaten-Ziel (es gibt mehr bekannte Punkte-Tiles beider Haelften als
    Units), und die letzten Punkte-Tiles der eigenen Haelfte bleiben unentdeckt.

    far_opp > 0 (cfg.far_opp, 20.10.2026): Punkte-Tiles der Gegnerhaelfte, die
    weiter als far_opp Felder von der Unit entfernt sind, rangieren hinter den
    Kandidaten-Tiles. Diagnose Match 3: 5,7 Units liefen im Mittel 18 Felder weit
    zu (meist besetzten) Gegner-Tiles, waehrend eigene Kandidaten offen blieben.

    home_reserve (cfg.home_reserve, 29.10.2026): Units mit Ziel auf einem Punkte-Tile der Gegnerhaelfte
    weiter als far_opp bekommen stattdessen ein Reservetile nahe den eigenen Punkte-Tiles (reserve_tiles).

    relic_scout > 0 (cfg.relic_scout, 29.10.2026): In Match 2/3 bis scout_until, solange ein Relic-Paar
    fehlen kann, suchen hoechstens relic_scout dieser ueberzaehligen Units (Ziel weit in der Gegnerhaelfte)
    die eigene Haelfte nach dem neuen Paar ab (_relic_scout). Nie Units mit eigenem Ziel.

    reach (cfg.reach_assign, 22.10.2026): Weglaenge (BFS ueber die Gedaechtniskarte) statt
    Luftlinie; nach Gedaechtnis unerreichbare Ziele (z. B. Punkte-Tiles unter einem Asteroiden)
    nur noch als letzte Wahl. Diagnose 360051: Units warteten neben Zielen unter Asteroiden.
    """
    if len(unit_ids) == 0:
        return {}
    pools = [belief.point_coords(), belief.candidate_coords()]
    targets = []
    prios = []
    for prio, pool in enumerate(pools):
        if len(pool):
            targets.append(pool)
            prios.append(np.full(len(pool), prio, dtype=np.int32))
    n_hard = int(sum(len(t) for t in targets))
    if n_hard < len(unit_ids):
        unexp = belief.explore_coords(stale) if stale else belief.unexplored_coords()
        if grid:
            unexp = grid_targets(unexp, grid)
        if len(unexp) == 0:
            unexp = belief.relic_coords()
        if len(unexp):
            # nur die naechsten Kandidaten betrachten, damit die Matrix klein bleibt
            centre = unit_pos.mean(axis=0)
            d = np.abs(unexp[:, 0] - centre[0]) + np.abs(unexp[:, 1] - centre[1])
            seen = np.zeros(len(unexp))
            if seen_before_penalty:
                seen = belief.explored_ever[unexp[:, 0], unexp[:, 1]] * float(seen_before_penalty)
            order = np.argsort(d + seen, kind="stable") if seen_before_penalty else np.argsort(d)
            keep = order if grid else order[: max(len(unit_ids) * 4, 16)]
            targets.append(unexp[keep])
            prios.append(np.full(len(keep), 2, dtype=np.int32))
            extra_seen = seen[keep]
    if not targets:
        return {}
    tgt = np.concatenate(targets, axis=0)
    prio = np.concatenate(prios, axis=0)
    extra = np.zeros(len(tgt))
    if seen_before_penalty and prio[-1] == 2:
        extra[len(tgt) - len(extra_seen):] = extra_seen
    own_origin = belief.canonical or belief.team_id == 0
    s_sum = tgt[:, 0] + tgt[:, 1]
    in_enemy = s_sum > W - 1 if own_origin else s_sum < W - 1
    if cand_quota > 0:
        cand_idx = np.where((prio == 1) & ~in_enemy)[0]
        pts = belief.point_coords()
        if len(cand_idx) and len(pts):
            c = tgt[cand_idx]
            d = (np.abs(c[:, None, 0] - pts[None, :, 0]) + np.abs(c[:, None, 1] - pts[None, :, 1])).min(1)
            pick = cand_idx[np.argsort(d, kind="stable")[:cand_quota]]
            prio = prio.copy()
            prio[pick] = 0
            extra[pick] += 100.0
            # Gegner-Punkte-Tiles hinter die Quote-Kandidaten
            extra[(prio == 0) & in_enemy] += 200.0

    # Kostenmatrix (Units x Ziele); Prioritaet dominiert die Distanz
    if reach:
        paths = bfs_maps(belief.passable, unit_pos)[:, tgt[:, 0], tgt[:, 1]].astype(np.float64)
        dist_ut = np.where(paths >= 0, paths, 5000.0)
    else:
        dist_ut = (np.abs(unit_pos[:, None, 0] - tgt[None, :, 0])
                   + np.abs(unit_pos[:, None, 1] - tgt[None, :, 1])).astype(np.float64)
    cost = dist_ut + prio[None, :] * 1000 + extra[None, :]
    if enemy_half_penalty:
        # eigener Spawn: kanonisch immer (0, 0); ohne Spiegelung fuer Team 1 (W-1, H-1)
        cost += in_enemy[None, :] * float(enemy_half_penalty)
    if far_opp > 0:
        dist = (np.abs(unit_pos[:, None, 0] - tgt[None, :, 0])
                + np.abs(unit_pos[:, None, 1] - tgt[None, :, 1]))
        if reach:
            dist = np.minimum(dist_ut, 999.0)
        # 1500: hinter Kandidaten (1000 + Distanz), vor Erkundung (2000 + Distanz)
        cost += ((dist > far_opp) & ((prio == 0) & in_enemy)[None, :]) * 1500.0
        if far_cand:
            # ebenso entfernte Kandidaten der Gegnerhaelfte hinter die eigenen Kandidaten
            cost += ((dist > far_opp) & ((prio == 1) & in_enemy)[None, :]) * 500.0
    if cand_boost > 0:
        # 20.10.2026: eigene Kandidaten zaehlen wie Punkte-Tiles mit cand_boost Feldern
        # Umweg (vor Punkte-Tiles der Gegnerhaelfte). Diagnose: in Match 3 bleiben bis
        # Step 90 im Mittel 0,8 eigene Punkte-Tiles ungetestete Kandidaten.
        own_cand = (prio == 1) & ~in_enemy
        cost[:, own_cand] -= 1000.0 - float(cand_boost)
        cost[:, (prio == 0) & in_enemy] += float(cand_boost)
    if energy_pref > 0:
        # 20.10.2026: Punkte-Tiles mit mehr Feldenergie bevorzugen (energy_pref Felder je 10 Energie)
        e = np.asarray(belief.energy_map, dtype=np.float64)[tgt[:, 0], tgt[:, 1]]
        cost[:, prio == 0] -= (np.clip(e, -20.0, 20.0) / 10.0 * float(energy_pref))[prio == 0]
    if sticky and prev:
        # bisheriges Ziel behalten, solange kein um mehr als `sticky` Felder besseres frei ist
        index = {}
        for ti, (tx, ty) in enumerate(tgt.tolist()):
            index.setdefault((tx, ty), ti)
        for ui, uid in enumerate(unit_ids):
            ti = index.get(prev.get(int(uid)))
            if ti is not None:
                cost[ui, ti] -= float(sticky)

    out: dict[int, tuple[int, int]] = {}
    n_assign = min(len(unit_ids), len(tgt))
    for _ in range(n_assign):
        flat = int(np.argmin(cost))
        ui, ti = divmod(flat, cost.shape[1])
        if not np.isfinite(cost[ui, ti]):
            break
        out[int(unit_ids[ui])] = (int(tgt[ti, 0]), int(tgt[ti, 1]))
        cost[ui, :] = np.inf
        cost[:, ti] = np.inf
    if (home_reserve or relic_scout > 0) and far_opp > 0:
        col = {(int(x), int(y)): j for j, (x, y) in enumerate(tgt.tolist())}
        far = [i for i, uid in enumerate(unit_ids)
               if (t := out.get(int(uid))) is not None and belief.point_tiles[t] and in_enemy[col[t]]
               and dist_ut[i, col[t]] > far_opp]
        if (far and relic_scout > 0 and belief.match_idx >= 1 and belief.match_step <= scout_until
                and belief.known_pairs() < belief.match_idx + 1):
            out, far = _relic_scout(belief, unit_ids, unit_pos, out, far, W, H, own_origin,
                                    relic_scout, scout_stale)
        if far and home_reserve:
            out = _home_reserve(belief, unit_ids, unit_pos, out, far, W, H, own_origin)
    if (explore_quota > 0 and belief.match_idx >= 1 and belief.match_step < explore_until
            and belief.known_pairs() < belief.match_idx + 1):
        out = _explore_quota(belief, unit_ids, unit_pos, out, W, H, explore_quota,
                             grid or 4, own_origin)
    return out


def reserve_tiles(belief, W: int, H: int, own_origin: bool = True) -> np.ndarray:
    """Reservetiles (cfg.home_reserve): eigene Haelfte, Chebyshev-Abstand genau 2 zum naechsten
    eigenen Punkte-Tile (ausserhalb des Streuschadens eines Saps auf den Halter), begehbar, kein
    Nebel, kein Punkte- oder Kandidaten-Tile."""
    xs, ys = np.indices((W, H))
    own = (xs + ys <= W - 1) if own_origin else (xs + ys >= W - 1)
    pts = belief.point_tiles & own
    if not pts.any():
        return np.zeros((W, H), dtype=bool)
    ring = _dilate(pts, 2) & ~_dilate(pts, 1)
    return ring & own & belief.passable & ~belief.nebula & ~belief.point_tiles & ~belief.candidate


def _relic_scout(belief, unit_ids, unit_pos, out: dict, far: list, W: int, H: int, own_origin: bool,
                 n: int, stale: int) -> tuple[dict, list]:
    """Bis zu n Units aus `far` (Indizes) auf eigene Tiles schicken, die ein neues Relic verbergen
    koennen: begehbar, in diesem Match nicht in den letzten `stale` Steps und nicht ab Step 49
    gesehen (wie Belief.explore_coords), je 4x4-Block eins. Liefert (Zuweisung, restliche far)."""
    xs, ys = np.indices((W, H))
    own = (xs + ys <= W - 1) if own_origin else (xs + ys >= W - 1)
    ls = belief.last_seen
    fresh = (ls >= belief.match_step - stale) | (ls >= 49)
    goals = np.argwhere(own & belief.passable & ~fresh)
    if len(goals) == 0:
        return out, far
    goals = grid_targets(goals.astype(np.int32), 4)
    out, rest = dict(out), list(far)
    taken: set = set(out.values())
    pos = np.asarray(unit_pos)
    for _ in range(n):
        best = None
        for i in rest:
            d = np.abs(goals[:, 0] - pos[i][0]) + np.abs(goals[:, 1] - pos[i][1])
            for k in np.argsort(d, kind="stable"):
                g = (int(goals[k, 0]), int(goals[k, 1]))
                if g not in taken:
                    if best is None or (int(d[k]), int(unit_ids[i])) < best[:2]:
                        best = (int(d[k]), int(unit_ids[i]), i, g)
                    break
        if best is None:
            break
        _, uid, i, g = best
        out[uid] = g
        taken.add(g)
        rest.remove(i)
    return out, rest


def _home_reserve(belief, unit_ids, unit_pos, out: dict, far: list, W: int, H: int,
                  own_origin: bool) -> dict:
    """Units mit fernem Gegnerziel (Indizes `far`) auf freie Reservetiles verteilen: naechstes
    Tile nach Luftlinie, je 10 Feldenergie ein Feld Umweg; ohne Reservetiles bleibt das Ziel."""
    tiles = np.argwhere(reserve_tiles(belief, W, H, own_origin))
    if len(tiles) == 0:
        return out
    energy = np.clip(np.asarray(belief.energy_map, dtype=np.float64)[tiles[:, 0], tiles[:, 1]], -20, 20)
    out = dict(out)
    taken: set = set(out.values())
    pos = np.asarray(unit_pos)
    order = sorted(far, key=lambda i: int(unit_ids[i]))
    for i in order:
        d = np.abs(tiles[:, 0] - pos[i][0]) + np.abs(tiles[:, 1] - pos[i][1]) - energy / 10.0
        for k in np.argsort(d, kind="stable"):
            t = (int(tiles[k, 0]), int(tiles[k, 1]))
            if t not in taken:
                out[int(unit_ids[i])] = t
                taken.add(t)
                break
    return out


def _explore_quota(belief, unit_ids, unit_pos, out: dict, W: int, H: int, quota: int,
                   block: int, own_origin: bool, stale: int = 20) -> dict:
    """20.10.2026 (cfg.explore_quota): Solange das Relic-Paar dieses Matches noch fehlen
    kann, suchen `quota` Units gezielt danach. Diagnose: In Match 2/3 gibt es mehr bekannte
    Ziele als Units, dann erkundet niemand; in 13 von 57 verlorenen Matches fehlte ein Relic.
    Wegen der Spiegelsymmetrie genuegt die eigene Haelfte; Ziel sind Tiles, die seit `stale`
    Steps nicht gesehen wurden (je ein Tile pro block x block). Abgezogen werden Units, die
    nicht auf einem Punkte-Tile stehen, zuerst ohne Ziel / mit Ziel in der Gegnerhaelfte,
    dann Kandidaten, zuletzt eigene Punkte-Tiles."""
    xs, ys = np.indices((W, H))
    own = (xs + ys <= W - 1) if own_origin else (xs + ys >= W - 1)
    open_ = own & belief.passable & (belief.last_seen < belief.match_step - stale)
    goals = np.argwhere(open_).astype(np.int32)
    if len(goals) == 0:
        return out
    goals = grid_targets(goals, block)
    out = dict(out)
    ranked = []
    for i, uid in enumerate(unit_ids):
        uid = int(uid)
        x, y = int(unit_pos[i][0]), int(unit_pos[i][1])
        if belief.point_tiles[x, y]:
            continue  # wer punktet, bleibt
        t = out.get(uid)
        if t is None or not (belief.point_tiles[t] or belief.candidate[t]):
            r = 0
        elif belief.point_tiles[t] and ((t[0] + t[1] > W - 1) if own_origin else (t[0] + t[1] < W - 1)):
            r = 1
        elif belief.candidate[t]:
            r = 2
        else:
            r = 3
        d = int((np.abs(goals[:, 0] - x) + np.abs(goals[:, 1] - y)).min())
        ranked.append((r, d, i, uid))
    taken: set = set()
    for _, _, i, uid in sorted(ranked)[:quota]:
        x, y = int(unit_pos[i][0]), int(unit_pos[i][1])
        d = np.abs(goals[:, 0] - x) + np.abs(goals[:, 1] - y)
        for gi in np.argsort(d, kind="stable"):
            g = (int(goals[gi, 0]), int(goals[gi, 1]))
            if g not in taken:
                out[uid] = g
                taken.add(g)
                break
    return out


def relic_search(agent, belief, unit_ids, unit_pos, unit_ene, assigned: dict, W: int, H: int) -> dict:
    """cfg.relic_search (22.10.2026): in Match 2/3 sucht genau EIN fester Sucher das neue
    Relic-Paar, solange es fehlen kann (bekannte Paare < Matchindex + 1, bis relic_search_until).
    Solution_92 durchsucht seine Haelfte in jedem Match erneut; bei uns hat in spaeten Matches
    jede Unit ein bekanntes Ziel, niemand sucht. Anders als explore_quota (Auswahl jeden Step neu,
    -8 pp) bleiben Sucher und Ziel fest, bis das Ziel gesehen wurde. Ziel: naechstes Tile der
    eigenen Haelfte, das seit relic_search_stale Steps nicht gesehen wurde (je 4x4-Block eins);
    Spiegelung deckt die andere Haelfte mit ab. Nie eine Unit auf einem Punkte-Tile oder mit
    eigenem Punkte-Tile als Ziel."""
    cfg = agent.cfg
    m, ms = belief.match_idx, belief.match_step
    state = getattr(agent, "_searcher", None)
    if state is not None and state[0] != m:
        state = None
    if m < 1 or ms > cfg.relic_search_until or belief.known_pairs() >= m + 1:
        agent._searcher = None
        return assigned
    pos = {int(u): (int(p[0]), int(p[1])) for u, p in zip(unit_ids, unit_pos)}
    own = lambda t: t[0] + t[1] <= W - 1  # noqa: E731
    uid, goal = (state[1], state[2]) if state is not None else (None, None)
    if uid is not None and (uid not in pos or belief.point_tiles[pos[uid]] or unit_ene[uid] < 0):
        uid, goal = None, None
    if uid is None:
        best = None
        for u, p in pos.items():
            if belief.point_tiles[p] or unit_ene[u] < 0:
                continue
            t = assigned.get(u)
            if t is not None and belief.point_tiles[t] and own(t):
                continue
            rank = 0 if t is None or not (belief.point_tiles[t] or belief.candidate[t]) else (
                1 if belief.point_tiles[t] else 2)
            key = (rank, -float(unit_ene[u]), u)
            if best is None or key < best[0]:
                best = (key, u)
        if best is None:
            agent._searcher = None
            return assigned
        uid = best[1]
    xs, ys = np.indices((W, H))
    stale = belief.last_seen < ms - cfg.relic_search_stale
    if goal is None or not stale[goal]:
        goals = np.argwhere((xs + ys <= W - 1) & belief.passable & stale)
        if len(goals) == 0:
            agent._searcher = None
            return assigned
        goals = grid_targets(goals.astype(np.int32), 4)
        x, y = pos[uid]
        k = int(np.argmin(np.abs(goals[:, 0] - x) + np.abs(goals[:, 1] - y)))
        goal = (int(goals[k, 0]), int(goals[k, 1]))
    agent._searcher = (m, uid, goal)
    out = dict(assigned)
    out[uid] = goal
    return out


def _home_penalty(cfg, match_idx: int) -> float:
    """Kosten fuer Ziele in der Gegnerhaelfte (home_first/home_penalty/home_last_only)."""
    if cfg.home_last_only and match_idx < N_MATCHES - 1:
        return 0.0
    return cfg.home_penalty or (600.0 if cfg.home_first else 0.0)


def make_context(agent, obs, belief=None) -> dict:
    """Alle pro Step einmalig benoetigten Groessen (kanonischer Raum).

    `belief` ueberschreibt agent.belief (Ablation no_belief: Features aus einer
    gedaechtnislosen Sicht, Reward weiter aus dem vollen Belief).
    """
    belief = belief if belief is not None else agent.belief
    W, H = belief.W, belief.H
    cfg = agent.env_cfg or {}
    team, opp = belief.team_id, belief.opp_team_id

    ally_mask = np.asarray(obs["units_mask"], dtype=bool)[team]
    enemy_mask = np.asarray(obs["units_mask"], dtype=bool)[opp]
    pos_all = np.asarray(obs["units"]["position"], dtype=np.int32)
    ene_all = np.asarray(obs["units"]["energy"], dtype=np.float32)
    if ene_all.ndim == 3 and ene_all.shape[-1] == 1:
        ene_all = ene_all[..., 0]
    ally_pos, enemy_pos = pos_all[team], pos_all[opp]
    ally_ene, enemy_ene = ene_all[team], ene_all[opp]
    if belief.mirrored:
        ally_pos = geo.mirror_positions(ally_pos, W, H)
        enemy_pos = geo.mirror_positions(enemy_pos, W, H)

    ally_ids = np.where(ally_mask)[0]
    enemy_ids = np.where(enemy_mask)[0]

    # Belegungskarte eigener Units (fuer Stacking-Features)
    ally_count = np.zeros((W, H), dtype=np.float32)
    first_on_tile: dict[tuple[int, int], int] = {}
    for uid in ally_ids:
        x, y = int(ally_pos[uid][0]), int(ally_pos[uid][1])
        if 0 <= x < W and 0 <= y < H:
            ally_count[x, y] += 1.0
            first_on_tile.setdefault((x, y), int(uid))

    enemy_coords = np.array(
        [[int(enemy_pos[i][0]), int(enemy_pos[i][1])] for i in enemy_ids
         if enemy_pos[i][0] >= 0], dtype=np.int32
    ).reshape(-1, 2)
    enemy_vis_ids = np.array([int(i) for i in enemy_ids if enemy_pos[i][0] >= 0], dtype=np.int32)
    enemy_energies = np.array(
        [float(enemy_ene[i]) for i in enemy_ids if enemy_pos[i][0] >= 0],
        dtype=np.float32,
    )

    points = np.asarray(obs["team_points"], dtype=np.float32)
    wins = np.asarray(obs["team_wins"], dtype=np.float32)
    match_step = int(np.asarray(obs["match_steps"]))
    max_match_steps = float(cfg.get("max_steps_in_match", 100))

    sticky = float(agent.cfg.sticky)
    prev = getattr(agent, "_sticky_prev", None)
    prev = prev[1] if sticky and prev is not None and prev[0] == belief.match_idx else None
    # Negative-energy units disappear before the next action; zero energy survives.
    target_ids = ally_ids
    if agent.cfg.active_targets:
        target_ids = ally_ids[ally_ene[ally_ids] >= 0]
    assigned = assign_targets(
        belief, target_ids,
        ally_pos[target_ids] if len(target_ids) else np.zeros((0, 2), np.int32),
        W, H, enemy_half_penalty=_home_penalty(agent.cfg, belief.match_idx),
        seen_before_penalty=300.0 if agent.cfg.explore_memory else 0.0,
        grid=4 if agent.cfg.explore_grid else 0, stale=int(agent.cfg.explore_stale),
        cand_quota=int(agent.cfg.cand_quota), far_opp=int(agent.cfg.far_opp),
        prev=prev, sticky=sticky, far_cand=bool(agent.cfg.far_cand),
        cand_boost=float(agent.cfg.cand_boost),
        explore_quota=int(agent.cfg.explore_quota), explore_until=int(agent.cfg.explore_until),
        energy_pref=float(agent.cfg.energy_pref),
        reach=bool(agent.cfg.reach_assign) and (not agent.training or agent.cfg.rules_in_training),
        home_reserve=bool(agent.cfg.home_reserve) and (not agent.training or agent.cfg.rules_in_training),
        relic_scout=(int(agent.cfg.relic_scout)
                     if agent.cfg.relic_scout and (not agent.training or agent.cfg.rules_in_training) else 0),
        scout_until=int(agent.cfg.scout_until), scout_stale=int(agent.cfg.scout_stale),
    )
    if sticky and belief is agent.belief:
        agent._sticky_prev = (belief.match_idx, dict(assigned))
    if agent.cfg.relic_search and not agent.training and belief is agent.belief:
        assigned = relic_search(agent, belief, target_ids,
                                ally_pos[target_ids] if len(target_ids) else np.zeros((0, 2), np.int32),
                                ally_ene, assigned, W, H)

    return dict(
        belief=belief, W=W, H=H,
        ally_ids=ally_ids, ally_pos=ally_pos, ally_ene=ally_ene,
        enemy_coords=enemy_coords, enemy_energies=enemy_energies, enemy_vis_ids=enemy_vis_ids,
        ally_count=ally_count, first_on_tile=first_on_tile,
        point_coords=belief.point_coords(),
        cand_coords=belief.candidate_coords(),
        relic_coords=belief.relic_coords(),
        unexp_coords=belief.unexplored_coords(),
        assigned=assigned,
        passable=belief.passable, nebula=belief.nebula,
        energy_map=belief.energy_map,
        point_tiles=belief.point_tiles, candidate=belief.candidate,
        explored=belief.explored,
        own_points=float(points[team]), opp_points=float(points[opp]),
        own_wins=float(wins[team]), opp_wins=float(wins[opp]),
        step=int(np.asarray(obs["steps"])),
        match_step=match_step, max_match_steps=max_match_steps,
        match_idx=belief.match_idx,
        move_cost=float(cfg.get("unit_move_cost", 3)),
        sap_cost=float(cfg.get("unit_sap_cost", 40)),
        sap_range=int(cfg.get("unit_sap_range", 5)),
        sensor_range=float(cfg.get("unit_sensor_range", 2)),
        max_units=int(cfg.get("max_units", 16)),
    )


def build_features(ctx: dict, uid: int) -> np.ndarray:
    """Feature-Vektor fuer eine Unit (Nullvektor, falls Unit nicht existiert)."""
    f = np.zeros(FEATURE_DIM, dtype=np.float32)
    W, H = ctx["W"], ctx["H"]
    if uid not in set(ctx["ally_ids"].tolist()):
        return f
    x = int(ctx["ally_pos"][uid][0])
    y = int(ctx["ally_pos"][uid][1])
    if not (0 <= x < W and 0 <= y < H):
        return f
    e = float(ctx["ally_ene"][uid])
    WH = float(W + H)
    i = 0

    # --- eigene Lage + Parameter
    f[i] = x / W; i += 1
    f[i] = y / H; i += 1
    f[i] = min(max(e, 0.0) / MAX_UNIT_ENERGY, 1.0); i += 1
    f[i] = 1.0 if e < ctx["move_cost"] else 0.0; i += 1
    f[i] = ctx["match_step"] / max(1.0, ctx["max_match_steps"]); i += 1
    f[i] = ctx["match_idx"] / N_MATCHES; i += 1
    f[i] = ctx["move_cost"] / 5.0; i += 1
    f[i] = ctx["sap_cost"] / 50.0; i += 1
    f[i] = ctx["sap_range"] / 7.0; i += 1
    f[i] = ctx["sensor_range"] / 4.0; i += 1

    # --- Punktestand
    f[i] = min(ctx["own_points"] / 200.0, 1.0); i += 1
    f[i] = float(np.tanh((ctx["own_points"] - ctx["opp_points"]) / 20.0)); i += 1
    f[i] = ctx["own_wins"] / N_MATCHES; i += 1
    f[i] = ctx["opp_wins"] / N_MATCHES; i += 1

    # --- naechste Ziele je Klasse
    for coords in (ctx["point_coords"], ctx["cand_coords"],
                   ctx["relic_coords"], ctx["unexp_coords"]):
        dx, dy, dist, ex = _nearest(coords, x, y, W, H)
        f[i] = dx; f[i + 1] = dy; f[i + 2] = dist; f[i + 3] = ex
        i += 4
    tgt = ctx["assigned"].get(int(uid))
    if tgt is None:
        f[i] = 0.0; f[i + 1] = 0.0; f[i + 2] = 1.0; f[i + 3] = 0.0
    else:
        f[i] = (tgt[0] - x) / W
        f[i + 1] = (tgt[1] - y) / H
        f[i + 2] = (abs(tgt[0] - x) + abs(tgt[1] - y)) / WH
        f[i + 3] = 1.0
    i += 4

    # --- aktuelles Tile
    f[i] = float(ctx["point_tiles"][x, y]); i += 1
    f[i] = float(ctx["candidate"][x, y]); i += 1
    f[i] = float(ctx["nebula"][x, y]); i += 1
    f[i] = min(ctx["ally_count"][x, y] / 4.0, 1.0); i += 1
    owner = ctx["first_on_tile"].get((x, y), int(uid))
    f[i] = 1.0 if owner != int(uid) else 0.0; i += 1

    # --- lokale Umgebung in 5 Richtungen
    for d in range(5):
        tx, ty = x + int(geo.DIR_DX[d]), y + int(geo.DIR_DY[d])
        if 0 <= tx < W and 0 <= ty < H:
            f[i] = float(ctx["passable"][tx, ty])
            f[i + 1] = float(np.clip(ctx["energy_map"][tx, ty] / MAX_TILE_ENERGY, -1, 1))
            f[i + 2] = float(ctx["point_tiles"][tx, ty])
            f[i + 3] = float(ctx["candidate"][tx, ty])
            f[i + 4] = float(not ctx["explored"][tx, ty])
            f[i + 5] = min(ctx["ally_count"][tx, ty] / 4.0, 1.0)
        # ausserhalb der Karte -> alles 0 (inkl. passable=0)
        i += 6

    # --- Gegner
    ec = ctx["enemy_coords"]
    if len(ec):
        d = np.abs(ec[:, 0] - x) + np.abs(ec[:, 1] - y)
        k = int(np.argmin(d))
        f[i] = (ec[k, 0] - x) / W
        f[i + 1] = (ec[k, 1] - y) / H
        f[i + 2] = float(d[k]) / WH
        f[i + 3] = float(np.tanh((e - ctx["enemy_energies"][k]) / 100.0))
        R = ctx["sap_range"]
        in_range = (np.abs(ec[:, 0] - x) <= R) & (np.abs(ec[:, 1] - y) <= R)
        f[i + 4] = min(float(in_range.sum()) / 4.0, 1.0)
        f[i + 5] = min(len(ec) / float(ctx["max_units"]), 1.0)
    else:
        f[i + 2] = 1.0
    i += 6

    # --- globale Zaehler
    f[i] = len(ctx["ally_ids"]) / float(ctx["max_units"]); i += 1
    f[i] = min(len(ctx["point_coords"]) / 20.0, 1.0); i += 1
    f[i] = float(ctx["explored"].mean()); i += 1
    f[i] = min(len(ctx["cand_coords"]) / 50.0, 1.0); i += 1

    assert i == FEATURE_DIM, f"Feature-Layout inkonsistent: {i} != {FEATURE_DIM}"
    return f


def threat_features(ctx: dict, uid: int) -> np.ndarray:
    """Gefahr-Merkmale (THREAT_NAMES) einer Unit; Nullvektor ohne Unit/Gegner."""
    f = np.zeros(THREAT_DIM, dtype=np.float32)
    W, H = ctx["W"], ctx["H"]
    ec = ctx["enemy_coords"]
    if uid not in set(ctx["ally_ids"].tolist()) or len(ec) == 0:
        return f
    x = int(ctx["ally_pos"][uid][0])
    y = int(ctx["ally_pos"][uid][1])
    if not (0 <= x < W and 0 <= y < H):
        return f
    ee = np.maximum(ctx["enemy_energies"].astype(np.float32), 0.0)
    R = ctx["sap_range"]
    armed = ctx["enemy_energies"] >= ctx["sap_cost"]
    i = 0
    for d in range(5):
        tx, ty = x + int(geo.DIR_DX[d]), y + int(geo.DIR_DY[d])
        if 0 <= tx < W and 0 <= ty < H:
            ddx, ddy = np.abs(ec[:, 0] - tx), np.abs(ec[:, 1] - ty)
            man = ddx + ddy
            f[i] = min(float((armed & (man <= R)).sum()) / 4.0, 1.0)
            f[i + 1] = min(float((armed & (np.maximum(ddx, ddy) <= R)).sum()) / 4.0, 1.0)
            f[i + 2] = min(float(ee[man == 0].sum()) / MAX_UNIT_ENERGY, 1.0)
            f[i + 3] = min(float(ee[man == 1].sum()) / MAX_UNIT_ENERGY, 1.0)
        i += 4
    cheb = np.maximum(np.abs(ec[:, 0] - x), np.abs(ec[:, 1] - y))
    best = 0
    for k in np.where(cheb <= R)[0]:
        near = np.maximum(np.abs(ec[:, 0] - ec[k, 0]), np.abs(ec[:, 1] - ec[k, 1])) <= 1
        best = max(best, int(near.sum()))
    f[i] = min(best / 4.0, 1.0); i += 1
    occupied = {(int(a), int(b)) for a, b in ec if ctx["point_tiles"][a, b]}
    f[i] = min(len(occupied) / 8.0, 1.0); i += 1
    assert i == THREAT_DIM
    return f
