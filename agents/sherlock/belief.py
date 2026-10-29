"""Gedaechtnis ueber das ganze Spiel (3 Matches): Relics, Punkte-Tiles, Karte.

Alles wird im KANONISCHEN Raum gespeichert (siehe geometry.py), d. h. aus Sicht
eines Spielers, der auf (0, 0) spawnt. Damit sind Belief und Features
seitenunabhaengig und ein Gewichtssatz gilt fuer beide Seiten.

Kernidee "Punkte-Tiles finden":
Die punktebringenden Tiles um einen Relic-Node sind unsichtbar (5x5-Maske,
Slide 38) und muessen durch Probieren erschlossen werden. Pro Step gilt
  gain      = team_points[t] - team_points[t-1]
  besetzt   = eindeutige Tiles mit mindestens einer eigenen Unit mit energy >= 0
              (die Engine zaehlt Units mit negativer Energie nicht mit,
               env.py: exclude_negative_energy_units=True)
  bekannt   = Anzahl besetzter, bereits bewiesener Punkte-Tiles
  U         = besetzt - bewiesene Punkte-Tiles - bewiesene Null-Tiles
  rest      = gain - bekannt   = Anzahl punktender Tiles in U
Daraus:
  rest == 0         -> alle Tiles in U bringen KEINE Punkte
  rest == |U|       -> alle Tiles in U SIND Punkte-Tiles
  sonst             -> unentschieden: als Constraint merken und spaeter erneut
                       aufloesen (Constraint-Propagation).
Die Constraints laufen bewusst ueber ALLE besetzten Tiles, nicht nur ueber die
Kandidaten in Relic-Naehe. Dadurch ist der Schluss auch dann korrekt, wenn ein
Relic noch nicht entdeckt wurde (sonst waere `rest` zu gross und es entstuenden
falsche Punkte-Tiles).

WICHTIG - wann darf ueberhaupt gefolgert werden:
Die Punkte-Schwelle der Engine haengt davon ab, wie viele Relic-Paare schon
gespawnt sind, und ein Paar spawnt in Match j bei match_step 0..49. In dieser
Phase kann dasselbe Tile erst punktlos und dann punktend sein - jeder Schluss
daraus ist potenziell falsch (im Experiment: 27 falsche Punkte-Tiles von 108).
Deshalb werden Constraints erst ab match_step >= 50 gesammelt.

WICHTIG - "dead" ist nicht dauerhaft gueltig:
Die Engine vergibt Punkte nur fuer Tiles, deren Relic schon gespawnt ist
(luxai_s3/env.py):

    scores = (unit_counts > 0) & (relic_nodes_map_weights <= relic_nodes_mask.sum()//2)
             & (relic_nodes_map_weights > 0)

Relic-Paare spawnen erst im Laufe der ersten k Matches. Ein Tile kann also in
Match 0 punktlos sein und ab Match 1 punkten (z. B. wenn sich die 5x5-Masken
zweier Relics ueberlappen und das Tile zum spaeteren Relic gehoert). Deshalb:
  * bewiesene Punkte-Tiles sind FUER IMMER gueltig (die Schwelle waechst nur),
  * "dead"-Tiles und die Constraint-Historie werden bei jedem Matchwechsel und
    bei jedem Widerspruch verworfen (_reopen_dead).
Ohne diese Korrektur entstehen falsche Punkte-Tiles (im Experiment 3 von 44).

SYMMETRIE (11.10.2026, Schalter `symmetry`): Relics spawnen paarweise
spiegelsymmetrisch zur Antidiagonale M(x, y) = (W-1-y, H-1-x), und die
punktebringenden Tiles sind zu JEDEM Zeitpunkt symmetrisch (geprueft ueber
1818 Steps auf 6 Seeds, 0 Verstoesse). Deshalb gilt jeder Schluss auch fuer das
Spiegeltile: gesehenes Relic -> Spiegel-Relic bekannt, bewiesenes Punkte-/
Null-Tile -> Spiegeltile ebenso, erkundetes Gebiet -> Spiegelgebiet erkundet.
Die Analyse vom 11.10. (scripts/analyze_losses.py) zeigte: wir kennen am
Matchende nur ~5 Punkte-Tiles, Solution_92 besetzt ~6.

Implementierungsdetail: die Propagation laeuft auf flachen int-Indizes und
Python-Sets, nicht auf numpy-Skalarindizierung - das ist ca. 50x schneller und
war im Profiling der Flaschenhals.
"""
from __future__ import annotations

import numpy as np

# tile_type-Werte der Engine
TILE_UNKNOWN = -1
TILE_EMPTY = 0
TILE_NEBULA = 1
TILE_ASTEROID = 2

RELIC_REWARD_RANGE = 2  # 5x5-Maske = Chebyshev-Radius 2 um den Relic-Node
MAX_RECORDS = 400       # Obergrenze fuer die Constraint-Historie
MAX_MATCH_STEPS = 100

# Relic-Paare spawnen laut luxai_s3/state.py:348
#   schedule_j = randint(0, max_steps_in_match // 2) + j * (max_steps_in_match + 1)
# also in Match j bei match_step in [0, 49] - und beide Kartenhaelften gleichzeitig.
# Ab diesem match_step aendert sich die Punkte-Schwelle innerhalb des Matches
# nicht mehr, nur dann sind Schluesse ueber Punkte-Tiles verlaesslich.
STABLE_FROM_MATCH_STEP = 50
NEVER_SEEN = -1000


def _dilate(mask: np.ndarray, r: int) -> np.ndarray:
    """Chebyshev-Dilatation um r (5x5 bei r=2), ohne scipy."""
    W, H = mask.shape
    pad = np.pad(mask, r)
    out = np.zeros_like(mask)
    for dx in range(2 * r + 1):
        for dy in range(2 * r + 1):
            out |= pad[dx:dx + W, dy:dy + H]
    return out


class Belief:
    """Persistentes Weltmodell eines Agenten fuer ein komplettes Spiel."""

    def __init__(self, team_id: int, W: int = 24, H: int = 24, canonical: bool = True,
                 symmetry: bool = False, early_inference: bool = False,
                 relic_filter: bool = False, subset_infer: bool = False,
                 keep_dead: bool = False, keep_dead_fast: bool = False,
                 opp_infer: bool = False, stale_all: bool = False,
                 nebula_infer_drift_safe: bool = False):
        self.W, self.H = W, H
        self.canonical = bool(canonical)
        self.symmetry = bool(symmetry)
        self.early_inference = bool(early_inference)
        self.relic_filter = bool(relic_filter)
        self.subset_infer = bool(subset_infer)
        self.keep_dead = bool(keep_dead)
        self.keep_dead_fast = bool(keep_dead_fast)
        self.opp_infer = bool(opp_infer)
        self.stale_all = bool(stale_all)
        # 22.10.2026 (Schalter nebula_infer): Tiles in unserer Sensorreichweite, die trotzdem
        # unsichtbar sind, muessen Nebel sein; sensor_range setzt der Agent aus env_cfg
        self.nebula_infer = False
        self.nebula_infer_drift_safe = bool(nebula_infer_drift_safe)
        self.sensor_range: int | None = None
        # 22.10.2026 (Schalter drift_track): Asteroiden/Nebel driften global um (s, -s) mit
        # Umlauf (luxai_s3/env.py, jnp.roll) -> bei erkannter Drift ganze Gedaechtniskarte mitrollen
        self.drift_track = False
        # 22.10.2026 (Schalter sym_map): Karte und Energiefeld sind exakt spiegelsymmetrisch
        # (x, y) <-> (W-1-y, H-1-x), auch nach Drift -> jedes sichtbare Tile verraet sein Spiegeltile
        self.sym_map = False
        # 22.10.2026 (Schalter window_infer): Punkte-Inferenz auch im Relic-Spawnfenster, wenn um
        # jede eigene Unit das 5x5-Feld sichtbar ist (kein ungesehenes Relic kann den Gewinn erklaeren)
        self.window_infer = False
        # 22.10.2026 (Schalter window_infer_all): im Spawnfenster immer schliessen; Tiles, deren 5x5
        # nicht ganz sichtbar ist (ungesehenes neues Relic moeglich), gehen als offene Unbekannte ein
        self.window_infer_all = False
        # 29.10.2026 (Schalter opp_point_infer): Gleichungen auch aus dem Punktgewinn des Gegners, wenn
        # jedes Tile, das ueberhaupt punkten kann, gerade wirklich sichtbar ist (_infer_points_from_enemy)
        self.opp_point_infer = False
        self.opp_point_records = 0
        self._vis_now = None
        self._sensor_now = None
        self.set_team(team_id)
        self.reset_game()

    # ------------------------------------------------------------------ setup
    def set_team(self, team_id: int) -> None:
        self.team_id = int(team_id)
        self.opp_team_id = 1 - self.team_id
        # player_1 sieht die Welt gespiegelt -> in kanonischen Raum drehen
        # (Ablation no_canonical: nie spiegeln, dafuer getrennte Netze je Seite)
        self.mirrored = self.canonical and self.team_id == 1

    def reset_game(self) -> None:
        W, H = self.W, self.H
        self.relic_positions: set[tuple[int, int]] = set()
        self.relic_zone = np.zeros((W, H), dtype=bool)   # 5x5 um bekannte Relics
        self.candidate = np.zeros((W, H), dtype=bool)    # relic_zone, noch unbekannt
        self.point_tiles = np.zeros((W, H), dtype=bool)  # bewiesen: bringt Punkte
        self.dead_tiles = np.zeros((W, H), dtype=bool)   # bewiesen: bringt nichts
        self.explored = np.zeros((W, H), dtype=bool)
        # wie explored, aber NICHT pro Match zurueckgesetzt (Zielwahl explore_memory)
        self.explored_ever = np.zeros((W, H), dtype=bool)
        # match_step, an dem ein Tile (oder sein Spiegeltile) zuletzt gesehen wurde
        self.last_seen = np.full((W, H), NEVER_SEEN, dtype=np.int16)
        self.match_step = 0
        self.tile_type = np.full((W, H), TILE_UNKNOWN, dtype=np.int8)
        self.energy_map = np.zeros((W, H), dtype=np.float32)
        self.drift_events = 0
        self.drift_votes = {1: 0, -1: 0}

        # schnelle Spiegelbilder der Statusmengen (flache Indizes x*H + y)
        self._point: set[int] = set()
        self._dead: set[int] = set()
        self._cand_dirty = True

        self.records: list[tuple[tuple[int, ...], int]] = []
        self._dead_hist: set[int] = set()       # Null-Tiles frueherer Matches
        self.relic_match: dict[tuple[int, int], int] = {}  # Relic -> Match des Fundes
        self.last_points = 0
        self.last_opp_points = 0
        self.opp_gain = 0
        self.match_idx = 0
        self.newly_proven = 0        # in diesem Step neu bewiesene Punkte-Tiles
        self.newly_explored = 0      # in diesem Step neu gesehene Tiles
        self.contradictions = 0      # erkannte Widersprueche (Diagnose)
        self._last_step = -1
        self._coords_dirty = True
        self._cache: dict[str, np.ndarray] = {}

    def reset_match(self) -> None:
        """Matchwechsel: Punktestand faellt auf 0, Relics koennen neu erscheinen."""
        self.last_points = 0
        self.last_opp_points = 0
        # Relics erscheinen in den ersten k Matches noch nachtraeglich (Slide 38)
        # -> Erkundungswissen pro Match zuruecksetzen, Relic-/Punktewissen behalten.
        self.explored[:] = False
        self.last_seen[:] = NEVER_SEEN
        self._coords_dirty = True
        # Neues Match => moeglicherweise neues Relic-Paar => Punkte-Regel aendert sich
        if self.keep_dead:
            self._dead_hist |= self._dead
        if self.keep_dead_fast:
            # wie Solution_92: Null-Tiles bleiben, nur die Gleichungen verfallen;
            # Tiles neben neu gefundenen Relics oeffnet _add_relic wieder
            self.records.clear()
        else:
            self._reopen_dead()

    # ------------------------------------------------------------ observation
    def observe(self, obs) -> None:
        """Beobachtung einarbeiten. Idempotent pro Step - act() und update()
        duerfen beide aufrufen."""
        step = int(np.asarray(obs["steps"]))
        if step == self._last_step:
            return
        self._last_step = step
        self.newly_proven = 0
        self.newly_explored = 0
        self.match_idx = step // (MAX_MATCH_STEPS + 1)

        match_step = int(np.asarray(obs["match_steps"]))
        self.match_step = match_step
        if match_step == 0:
            self.reset_match()
            return  # zu Matchbeginn existieren noch keine Units

        from . import geometry as geo  # lokal: vermeidet Zyklus

        sensor = np.asarray(obs["sensor_mask"], dtype=bool)
        tile_type = np.asarray(obs["map_features"]["tile_type"], dtype=np.int32)
        energy = np.asarray(obs["map_features"]["energy"], dtype=np.float32)
        relic_pos = np.asarray(obs["relic_nodes"], dtype=np.int32)
        relic_mask = np.asarray(obs["relic_nodes_mask"], dtype=bool)
        ally_pos = np.asarray(obs["units"]["position"], dtype=np.int32)[self.team_id]
        ally_mask = np.asarray(obs["units_mask"], dtype=bool)[self.team_id]
        ally_energy = np.asarray(obs["units"]["energy"], dtype=np.int32)[self.team_id]
        if ally_energy.ndim == 2 and ally_energy.shape[-1] == 1:
            ally_energy = ally_energy[:, 0]

        if self.mirrored:
            sensor = geo.mirror_map(sensor)
            tile_type = geo.mirror_map(tile_type)
            energy = geo.mirror_map(energy)
            relic_pos = geo.mirror_positions(relic_pos, self.W, self.H)
            ally_pos = geo.mirror_positions(ally_pos, self.W, self.H)

        self._sensor_now = sensor  # wirklich sichtbar (kanonisch), ohne Spiegelbild
        self._vis_now = (sensor | geo.mirror_map(sensor)) if self.symmetry else sensor
        if self.sym_map:
            msensor = geo.mirror_map(sensor)
            tile_type = np.where(sensor, tile_type, geo.mirror_map(tile_type))
            energy = np.where(sensor, energy, geo.mirror_map(energy))
            sensor = sensor | msensor
        drift_events_before = self.drift_events
        if self.drift_track:
            self._detect_drift(sensor, tile_type)
        self._update_map(sensor, tile_type, energy)
        # Die Engine berechnet den Sensor VOR der Terrain-Drift und zeigt damit
        # die Karte NACH der Drift. Hidden-in-range belegt auf solchen Steps nur
        # alten Nebel, nicht den aktuellen Tile-Typ. Unerkannte Drift bleibt offen.
        skip_nebula = self.nebula_infer_drift_safe and self.drift_events != drift_events_before
        if self.nebula_infer and self.sensor_range is not None and not skip_nebula:
            self._infer_nebula(sensor, ally_pos, ally_mask & (ally_energy >= 0))
        self._update_relics(relic_pos, relic_mask)
        if self.keep_dead and self._dead_hist:
            self._restore_dead()

        points = int(np.asarray(obs["team_points"])[self.team_id])
        gain = points - self.last_points
        self.last_points = points
        opp_points = int(np.asarray(obs["team_points"])[self.opp_team_id])
        self.opp_gain = max(0, opp_points - self.last_opp_points)  # Gegner-Punkte dieses Steps
        self.last_opp_points = opp_points
        self._infer_point_tiles(ally_pos, ally_energy, ally_mask, gain, match_step)
        if self.opp_infer:
            self._infer_from_enemy(obs, match_step)
        if self.opp_point_infer:
            self._infer_points_from_enemy(obs, match_step)
        self._refresh_candidates()

    def _enemy_tiles(self, obs) -> set:
        """Flache Indizes (kanonisch) der Tiles sichtbarer Gegner mit Energie >= 0."""
        from . import geometry as geo
        pos = np.asarray(obs["units"]["position"], dtype=np.int32)[self.opp_team_id]
        mask = np.asarray(obs["units_mask"], dtype=bool)[self.opp_team_id]
        ene = np.asarray(obs["units"]["energy"], dtype=np.int32)[self.opp_team_id]
        if ene.ndim == 2 and ene.shape[-1] == 1:
            ene = ene[:, 0]
        if self.mirrored:
            pos = geo.mirror_positions(pos, self.W, self.H)
        occ = set()
        for i in np.nonzero(mask)[0]:
            x, y = int(pos[i][0]), int(pos[i][1])
            if 0 <= x < self.W and 0 <= y < self.H and ene[i] >= 0:
                occ.add(x * self.H + y)
        return occ

    def _infer_points_from_enemy(self, obs, match_step: int) -> None:
        """Schalter `opp_point_infer` (29.10.2026): Gleichung aus dem Punktgewinn des Gegners.

        Der Gegner punktet mit genau den Punkte-Tiles, auf denen eine seiner Units (Energie >= 0)
        steht; die Punkte-Tiles sind fuer beide Teams dieselben. Ist JEDES Tile, das ueberhaupt
        punkten kann (_possible_point_zone), in diesem Step wirklich sichtbar, steht kein punktender
        Gegner unsichtbar -> opp_gain = Summe punkt(t) ueber die sichtbar besetzten Tiles. Das ist
        dieselbe Gleichung, die wir aus eigenen Units bilden. Sonst erklaert jedes unsichtbare, nicht
        tote Zonen-Tile hoechstens einen Punkt: Reicht der Rest danach noch fuer alle sichtbar besetzten
        offenen Tiles, sind sie alle Punkte-Tiles (typisch fuer eine Gegnerfestung). Diagnose Dev A (800051): Solution_92
        besetzt einen gemeinsamen Haufen zuerst, wir kennen dort das ganze Match kein Punkte-Tile;
        mit wahren Punkte-Tiles (Orakel) gewinnt V10 auf Dev A +4 bis +6 pp.
        """
        if not self._stable(match_step) or self._sensor_now is None:
            return
        zone = self._possible_point_zone()
        if zone is None:
            return
        occ = {f for f in self._enemy_tiles(obs) if zone[divmod(f, self.H)]}
        known = len(occ & self._point)
        unknown = occ - self._point - self._dead
        rest = self.opp_gain - known
        if not unknown or rest < 0:
            return
        # Unsichtbare moegliche Punkte-Tiles (nicht als tot bekannt): jedes kann hoechstens einen
        # Punkt eines unsichtbaren Gegners erklaeren -> rest - hidden ist eine untere Schranke
        hidden = int((zone & ~self._sensor_now & ~self.dead_tiles).sum())
        if hidden == 0 and rest <= len(unknown):
            new = (tuple(sorted(unknown)), rest)            # Gleichung
        elif rest - hidden >= len(unknown):
            new = (tuple(sorted(unknown)), len(unknown))    # alle sichtbar besetzten sind Punkte-Tiles
        else:
            return  # keine sichere Aussage
        if new in self.records:
            return
        if self.subset_infer:
            self._add_differences(new)
        self.records.append(new)
        if len(self.records) > MAX_RECORDS:
            del self.records[: len(self.records) - MAX_RECORDS]
        self.opp_point_records += 1
        self._propagate()

    def _infer_from_enemy(self, obs, match_step: int) -> None:
        """Schalter `opp_infer`: Null-Tiles aus dem Punktgewinn des Gegners.

        Der Gegner punktet mit genau den Punkte-Tiles, auf denen eine seiner
        Units (Energie >= 0) steht - dieselben Tiles wie fuer uns. Erklaeren die
        sichtbaren Gegner auf bekannten Punkte-Tiles schon den ganzen Gewinn,
        bringt kein anderes Tile unter einer (sichtbaren) gegnerischen Unit
        Punkte -> diese Tiles sind Null-Tiles (unsichtbare Gegner aendern daran
        nichts, sie koennten den Gewinn nur erhoehen).
        """
        if not self._stable(match_step):
            return
        from . import geometry as geo
        pos = np.asarray(obs["units"]["position"], dtype=np.int32)[self.opp_team_id]
        mask = np.asarray(obs["units_mask"], dtype=bool)[self.opp_team_id]
        ene = np.asarray(obs["units"]["energy"], dtype=np.int32)[self.opp_team_id]
        if ene.ndim == 2 and ene.shape[-1] == 1:
            ene = ene[:, 0]
        if self.mirrored:
            pos = geo.mirror_positions(pos, self.W, self.H)
        occ = set()
        for i in np.nonzero(mask)[0]:
            x, y = int(pos[i][0]), int(pos[i][1])
            if 0 <= x < self.W and 0 <= y < self.H and ene[i] >= 0:
                occ.add(x * self.H + y)
        if not occ:
            return
        known = len(occ & self._point)
        if self.opp_gain != known:
            return
        for f in occ - self._point - self._dead:
            self._mark_dead(f)

    def _update_map(self, sensor, tile_type, energy) -> None:
        explored_now = sensor
        if self.symmetry:
            from . import geometry as geo
            explored_now = sensor | geo.mirror_map(sensor)  # nur fuer "erkundet"
        new = int(np.count_nonzero(explored_now & ~self.explored))
        self.newly_explored = new
        if new:
            self.explored |= explored_now
            self._coords_dirty = True
        self.explored_ever |= explored_now
        self.last_seen[explored_now] = self.match_step
        # Asteroiden/Nebel driften (Slides 30/31) -> sichtbare Tiles ueberschreiben
        np.copyto(self.tile_type, tile_type.astype(np.int8), where=sensor)
        np.copyto(self.energy_map, energy, where=sensor)

    def _detect_drift(self, sensor, tile_type) -> None:
        """Passt die sichtbare Karte zur um (s, -s) gerollten Erinnerung deutlich besser als zur
        ungerollten, ist eine Drift passiert: ganze Karte rollen (auch unsichtbare Teile). Die
        Richtung ist pro Spiel fest; nach zwei gleichen Funden nur noch diese pruefen."""
        bt = self.tile_type
        seen = sensor & (bt != TILE_UNKNOWN)
        m0 = int(np.count_nonzero(seen & (tile_type != bt)))
        if m0 < 2:
            return
        dirs = [s for s in (1, -1) if self.drift_votes[-s] < 2 or self.drift_votes[s] >= 2]
        best = None
        for s in dirs:
            rolled = np.roll(bt, (s, -s), axis=(0, 1))
            seen_r = sensor & (rolled != TILE_UNKNOWN)
            if np.count_nonzero(seen_r) < 4:
                continue
            ms = int(np.count_nonzero(seen_r & (tile_type != rolled)))
            if ms * 4 <= m0 and (best is None or ms < best[1]):
                best = (s, ms, rolled)
        if best is not None:
            self.tile_type = best[2].astype(np.int8)
            self.drift_votes[best[0]] += 1
            self.drift_events += 1

    def _infer_nebula(self, sensor, ally_pos, alive) -> None:
        """Engine: jede Unit gibt Sichtkraft >= 1 auf alle Tiles in Chebyshev-Abstand <= sensor_range,
        nur Nebel zieht Sichtkraft ab. Unsichtbar trotz Reichweite => Nebel (auch wo das Gedaechtnis
        noch einen laengst weggedrifteten Asteroiden fuehrt)."""
        r = int(self.sensor_range)
        in_range = np.zeros((self.W, self.H), dtype=bool)
        for i in np.nonzero(alive)[0]:
            x, y = int(ally_pos[i][0]), int(ally_pos[i][1])
            if 0 <= x < self.W and 0 <= y < self.H:
                in_range[max(0, x - r):x + r + 1, max(0, y - r):y + r + 1] = True
        hidden = in_range & ~sensor
        if hidden.any():
            if self.sym_map:
                from . import geometry as geo
                hidden = hidden | geo.mirror_map(hidden)
            self.tile_type[hidden] = TILE_NEBULA

    def _update_relics(self, relic_pos, relic_mask) -> None:
        for i in np.nonzero(relic_mask)[0]:
            x, y = int(relic_pos[i][0]), int(relic_pos[i][1])
            if x < 0 or y < 0:
                continue
            self._add_relic(x, y)
            if self.symmetry:
                self._add_relic(self.W - 1 - y, self.H - 1 - x)

    def _add_relic(self, x: int, y: int) -> None:
        if (x, y) in self.relic_positions:
            return
        self.relic_positions.add((x, y))
        self.relic_match[(x, y)] = self.match_idx
        if self.keep_dead_fast and self._dead:
            r = RELIC_REWARD_RANGE
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    tx, ty = x + dx, y + dy
                    if 0 <= tx < self.W and 0 <= ty < self.H:
                        f = tx * self.H + ty
                        if f in self._dead:
                            self._dead.discard(f)
                            self.dead_tiles[tx, ty] = False
        r = RELIC_REWARD_RANGE
        self.relic_zone[max(0, x - r):x + r + 1, max(0, y - r):y + r + 1] = True
        self._cand_dirty = True
        self._coords_dirty = True

    def _refresh_candidates(self) -> None:
        """candidate ist abgeleitet: Relic-Umfeld, das noch nicht entschieden ist."""
        if not self._cand_dirty:
            return
        np.logical_and(self.relic_zone, ~(self.point_tiles | self.dead_tiles),
                       out=self.candidate)
        self._cand_dirty = False

    # ----------------------------------------------------- punkte-tile-logik
    def known_pairs(self) -> int:
        """Anzahl bekannter Relic-Paare (Relic und Spiegelrelic spawnen gemeinsam)."""
        return len({min((x, y), (self.W - 1 - y, self.H - 1 - x))
                    for x, y in self.relic_positions})

    def pair_spawned(self) -> bool:
        """Ist das Relic-Paar des aktuellen Matches sicher schon gespawnt?

        Paar j spawnt in Match j (falls j < k) bei match_step 0..49, hoechstens
        eines pro Match. Kennen wir j+1 Paare, sind 0..j alle da. In Match 0 gibt
        es vor dem ersten Paar gar keine Relics: jeder Punkt (auch des Gegners)
        beweist den Spawn.
        """
        if self.known_pairs() >= self.match_idx + 1:
            return True
        return self.match_idx == 0 and (self.last_points > 0 or self.last_opp_points > 0)

    def _stable(self, match_step: int) -> bool:
        """Darf aus dem Punktgewinn geschlossen werden? Nach dem (einzigen) Spawn
        des Matches aendert sich die Punkte-Schwelle bis Matchende nicht mehr."""
        if match_step >= STABLE_FROM_MATCH_STEP:
            return True
        return self.early_inference and self.pair_spawned()

    def _infer_point_tiles(self, ally_pos, ally_energy, ally_mask, gain: int,
                           match_step: int) -> None:
        window = False
        open_tiles: set = set()
        if not self._stable(match_step):
            if self.window_infer and self._window_ok(ally_pos, ally_energy, ally_mask):
                window = True
            elif self.window_infer_all and self._vis_now is not None:
                window = True
                open_tiles = self._open_tiles(ally_pos, ally_energy, ally_mask)
            else:
                return  # Relic-Spawn-Fenster: Punkte-Schwelle noch instabil
        H = self.H
        occupied = set()
        for i in np.nonzero(ally_mask)[0]:
            x, y = int(ally_pos[i][0]), int(ally_pos[i][1])
            # Units mit negativer Energie zaehlen fuer die Punkte nicht mit
            if x >= 0 and y >= 0 and ally_energy[i] >= 0:
                occupied.add(x * H + y)
        if not occupied:
            return

        if self.relic_filter:
            zone = self.relic_zone if window else self._possible_point_zone()
            if zone is not None:
                # Units ausserhalb jeder moeglichen Relic-Reichweite punkten nie
                occupied = {f for f in occupied if zone[divmod(f, H)] or f in open_tiles}
                if not occupied:
                    return

        known = len(occupied & self._point)
        unknown = (occupied - self._point - self._dead) | ((occupied & open_tiles) - self._point)
        rest = gain - known
        if rest < 0 or rest > len(unknown):
            # Widerspruch: der Punktgewinn ist mit dem aktuellen Wissen nicht
            # erklaerbar -> ein weiteres Relic-Paar ist aktiv geworden.
            # Null-Wissen und Constraints verwerfen, Punkte-Tiles behalten.
            self.contradictions += 1
            self._reopen_dead()
            known = len(occupied & self._point)
            unknown = occupied - self._point - self._dead
            rest = gain - known
            if rest < 0 or rest > len(unknown):
                return
        if not unknown:
            return  # keine neue Information
        new = (tuple(sorted(unknown)), rest)
        if self.subset_infer:
            if new in self.records:
                return  # dieselbe Gleichung schon bekannt
            self._add_differences(new)
        self.records.append(new)
        if len(self.records) > MAX_RECORDS:
            del self.records[: len(self.records) - MAX_RECORDS]
        self._propagate()

    def _add_differences(self, new: tuple[tuple[int, ...], int]) -> None:
        """Schalter `subset_infer`: Differenzen von Teilmengen-Gleichungen.

        Jede Beobachtung ist eine Gleichung  Summe_{t in U} punkt(t) = rest.
        Ist U_alt eine echte Teilmenge von U_neu, gilt fuer U_neu \\ U_alt die
        Differenz der beiden rest-Werte (und umgekehrt). Typischer Fall: eine
        Unit betritt ein neues Kandidaten-Tile, der Punktgewinn steigt um 1 ->
        genau dieses Tile ist ein Punkte-Tile, auch wenn die uebrigen Tiles noch
        offen sind. Die reine Alles-oder-nichts-Regel kann das nicht schliessen.
        """
        tiles_n, rest_n = set(new[0]), new[1]
        derived = []
        for tiles_o, rest_o in self.records:
            if len(tiles_o) == len(tiles_n):
                continue
            so = set(tiles_o)
            if so < tiles_n:
                d = (tuple(sorted(tiles_n - so)), rest_n - rest_o)
            elif tiles_n < so:
                d = (tuple(sorted(so - tiles_n)), rest_o - rest_n)
            else:
                continue
            if 0 <= d[1] <= len(d[0]) and d not in derived:
                derived.append(d)
        for d in derived:
            if d not in self.records:
                self.records.append(d)

    def _window_ok(self, ally_pos, ally_energy, ally_mask) -> bool:
        """Im Spawnfenster nur schliessen, wenn das 5x5-Feld um jede punktende eigene Unit jetzt
        sichtbar ist (inkl. Spiegelbild bei Symmetrie): ein Relic, das eines dieser Tiles zum
        Punkte-Tile macht, waere dann bekannt; ungesehene neue Relics koennen den Gewinn nicht erklaeren."""
        vis = self._vis_now
        if vis is None:
            return False
        r = RELIC_REWARD_RANGE
        any_unit = False
        for i in np.nonzero(ally_mask)[0]:
            x, y = int(ally_pos[i][0]), int(ally_pos[i][1])
            if x < 0 or y < 0 or ally_energy[i] < 0:
                continue
            any_unit = True
            if not vis[max(0, x - r):x + r + 1, max(0, y - r):y + r + 1].all():
                return False
        return any_unit

    def _open_tiles(self, ally_pos, ally_energy, ally_mask) -> set:
        """Flache Indizes eigener Unit-Tiles, deren 5x5-Feld jetzt nicht ganz sichtbar ist."""
        vis = self._vis_now
        r = RELIC_REWARD_RANGE
        out = set()
        for i in np.nonzero(ally_mask)[0]:
            x, y = int(ally_pos[i][0]), int(ally_pos[i][1])
            if x < 0 or y < 0 or ally_energy[i] < 0:
                continue
            if not vis[max(0, x - r):x + r + 1, max(0, y - r):y + r + 1].all():
                out.add(x * self.H + y)
        return out

    def _restore_dead(self) -> None:
        """Schalter `keep_dead`: Null-Tiles frueherer Matches wiederherstellen.

        Ein Tile, das in einem frueheren Match keine Punkte brachte, kann spaeter
        nur punkten, wenn es im 5x5-Feld eines NEU gespawnten Relics liegt (die
        Schwelle aktiviert nur die Masken neuer Relic-Paare). Sobald feststeht,
        wo neue Relics dieses Matches liegen koennen, gelten alle alten
        Null-Tiles ausserhalb dieser Zonen wieder als Null-Tiles. Ohne das testen
        die Units jedes Match dieselben leeren Felder um alte Relics erneut.
        """
        new_relics = np.zeros((self.W, self.H), dtype=bool)
        for (x, y), m in self.relic_match.items():
            if m == self.match_idx:
                new_relics[x, y] = True
        if self.known_pairs() >= self.match_idx + 1:
            possible = new_relics
        elif self.match_step >= STABLE_FROM_MATCH_STEP:
            possible = new_relics | (self.last_seen < STABLE_FROM_MATCH_STEP)
        else:
            return
        zone = _dilate(possible, RELIC_REWARD_RANGE)
        restore = [f for f in self._dead_hist if not zone[divmod(f, self.H)] and f not in self._point]
        for f in restore:
            self._dead_hist.discard(f)
            self._mark_dead(f)

    def _possible_point_zone(self):
        """Tiles, die ueberhaupt Punkte bringen koennen (5x5 um moegliche Relics).

        Schalter `relic_filter` (19.10.2026, Idee aus Solution_92): Ein Tile kann
        nur punkten, wenn ein Relic hoechstens 2 Felder entfernt ist. Moegliche
        Relic-Orte:
          * alle Paare dieses Matches bekannt (known_pairs >= match_idx + 1;
            hoechstens ein Paar pro Match) -> nur die bekannten Relics,
          * sonst ab match_step 50 (Spawnfenster vorbei): bekannte Relics und
            jedes Tile, das in diesem Match nicht ab Step 50 gesehen wurde,
          * sonst keine Einschraenkung (None).
        Ohne den Filter landen alle Units weit weg von Relics als "unbekannt"
        in den Constraints; die Alles-oder-nichts-Schluesse greifen dann kaum
        (Analyse 19.10.: Match 1, Step 50 kennt Solution_92 2,6 Punkte-Tiles, wir 0,2).
        """
        if self.known_pairs() >= self.match_idx + 1:
            return self.relic_zone
        if self.match_step < STABLE_FROM_MATCH_STEP:
            return None
        possible = self.last_seen < STABLE_FROM_MATCH_STEP
        for x, y in self.relic_positions:
            possible[x, y] = True
        return _dilate(possible, RELIC_REWARD_RANGE)

    def _reopen_dead(self) -> None:
        """Alle "bringt keine Punkte"-Schluesse verwerfen (siehe Modulkopf).

        Bewiesene Punkte-Tiles bleiben erhalten: die Engine-Schwelle
        relic_nodes_mask.sum()//2 waechst monoton, ein Tile das einmal punktet
        punktet immer weiter.
        """
        if not self._dead and not self.records:
            return
        self._dead.clear()
        self.records.clear()
        self.dead_tiles[:] = False
        self._cand_dirty = True
        self._coords_dirty = True

    def _propagate(self) -> None:
        """Constraint-Propagation ueber alle gesammelten Beobachtungen."""
        point, dead = self._point, self._dead
        changed = True
        while changed:
            changed = False
            still_open: list[tuple[tuple[int, ...], int]] = []
            for tiles, rest in self.records:
                open_tiles = [t for t in tiles if t not in point and t not in dead]
                if not open_tiles:
                    continue  # vollstaendig aufgeloest
                rest_now = rest - sum(1 for t in tiles if t in point)
                if rest_now <= 0:
                    for t in open_tiles:
                        self._mark_dead(t)
                    changed = True
                elif rest_now >= len(open_tiles):
                    for t in open_tiles:
                        self._mark_point(t)
                    changed = True
                else:
                    still_open.append((tuple(open_tiles), rest_now))
            self.records = still_open

    def _mirror_idx(self, f: int) -> int:
        x, y = divmod(f, self.H)
        return (self.W - 1 - y) * self.H + (self.H - 1 - x)

    def _mark_point(self, f: int) -> None:
        self._dead.discard(f)
        if f in self._point:
            return
        if self.symmetry:
            m = self._mirror_idx(f)
            if m != f:
                self._point.add(f)          # Rekursionsschutz
                self._mark_point(m)
                self._point.discard(f)
        self._point.add(f)
        x, y = divmod(f, self.H)
        self.point_tiles[x, y] = True
        self.dead_tiles[x, y] = False
        self.newly_proven += 1
        self._cand_dirty = True
        self._coords_dirty = True

    def _mark_dead(self, f: int) -> None:
        if f in self._dead or f in self._point:
            return
        self._dead.add(f)
        if self.symmetry:
            self._mark_dead(self._mirror_idx(f))
        x, y = divmod(f, self.H)
        self.dead_tiles[x, y] = True
        self._cand_dirty = True
        self._coords_dirty = True

    # ----------------------------------------------------------- abfragen
    @property
    def passable(self) -> np.ndarray:
        """True, wo (nach letztem Wissen) kein Asteroid liegt."""
        return self.tile_type != TILE_ASTEROID

    @property
    def nebula(self) -> np.ndarray:
        return self.tile_type == TILE_NEBULA

    def _coords(self, key: str, mask: np.ndarray) -> np.ndarray:
        if self._coords_dirty:
            self._cache.clear()
            self._coords_dirty = False
        hit = self._cache.get(key)
        if hit is None:
            hit = np.argwhere(mask).astype(np.int32)
            self._cache[key] = hit
        return hit

    def point_coords(self) -> np.ndarray:
        return self._coords("point", self.point_tiles)

    def candidate_coords(self) -> np.ndarray:
        self._refresh_candidates()
        return self._coords("cand", self.candidate)

    def unexplored_coords(self) -> np.ndarray:
        return self._coords("unexp", ~self.explored)

    def explore_coords(self, stale: int = 0) -> np.ndarray:
        """Erkundungsziele. stale > 0: in Match 0, solange kein Relic bekannt ist,
        zaehlen nur Tiles als erkundet, die in den letzten `stale` Steps oder ab
        match_step 49 gesehen wurden (vorher gesehene koennen ein spaeter
        gespawntes Relic verbergen)."""
        if stale <= 0:
            return self.unexplored_coords()
        if self.stale_all:
            # jedes Match: solange ein Relic-Paar dieses Matches fehlen kann
            if self.known_pairs() >= self.match_idx + 1:
                return self.unexplored_coords()
        elif self.match_idx != 0 or self.known_pairs() > 0:
            return self.unexplored_coords()
        ls = self.last_seen
        fresh = (ls >= self.match_step - stale) | (ls >= STABLE_FROM_MATCH_STEP - 1)
        return np.argwhere(~fresh).astype(np.int32)

    def relic_coords(self) -> np.ndarray:
        if not self.relic_positions:
            return np.zeros((0, 2), dtype=np.int32)
        key = "relic"
        if self._coords_dirty:
            self._cache.clear()
            self._coords_dirty = False
        hit = self._cache.get(key)
        if hit is None or len(hit) != len(self.relic_positions):
            hit = np.array(sorted(self.relic_positions), dtype=np.int32)
            self._cache[key] = hit
        return hit


class MemorylessBelief(Belief):
    """Ablation `no_belief`: dieselbe Schnittstelle, aber ohne Gedaechtnis.

    Vor jeder Beobachtung wird alles verworfen, d. h. Relics, Karte und
    "erkundet" spiegeln nur das aktuell Sichtbare wider. Punkte-Tiles koennen
    ohne Gedaechtnis (Punktverlauf ueber Steps) nicht abgeleitet werden und
    bleiben leer.
    """

    def observe(self, obs) -> None:
        step = int(np.asarray(obs["steps"]))
        if step == self._last_step:
            return
        self.reset_game()
        super().observe(obs)

    def _infer_point_tiles(self, *args, **kwargs) -> None:
        return
