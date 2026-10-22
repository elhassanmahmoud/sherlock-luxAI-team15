"""Hyperparameter an einer Stelle (gut fuer die Folie "Training configuration")."""
from __future__ import annotations

from dataclasses import dataclass, asdict, fields


@dataclass
class AgentConfig:
    # --- Netz
    hidden: int = 256
    dueling: bool = True

    # --- DQN
    gamma: float = 0.99
    lr: float = 3e-4
    batch_size: int = 256
    buffer_capacity: int = 300_000
    learn_start: int = 5_000          # Env-Steps, bevor gelernt wird
    train_every: int = 2              # Lernschritt alle n Env-Steps
    target_update_every: int = 500    # harte Target-Sync alle n Lernschritte
    grad_clip: float = 5.0
    double_dqn: bool = True

    # --- Exploration (lineares Epsilon-Decay ueber Env-Steps)
    eps_start: float = 1.0
    eps_end: float = 0.05
    eps_decay_steps: int = 60_000
    guided_prob: float = 0.7
    """Anteil der Explorationsschritte, die NICHT uniform zufaellig sind, sondern
    heuristisch Richtung zugewiesenes Ziel laufen. Ohne diesen Prior erreichen die
    Units aus der Spawn-Ecke die Relic-Zonen praktisch nie und der w_point-Reward
    wird nie gesehen (im Experiment: Recall der Punkte-Tiles ~5%)."""

    # --- Ablations-Schalter (docs/EXPERIMENT_PROTOKOLL.md). Jede Ablation
    # schaltet genau EINEN davon gegenueber "full" um.
    use_belief: bool = True
    """False: das Netz sieht nur die aktuelle Beobachtung (MemorylessBelief).
    Reward, Maske und gefuehrte Exploration nutzen weiter den vollen Belief."""
    use_symmetry: bool = False
    """True: Belief nutzt die Spiegelsymmetrie der Karte (Relics, Punkte-/Null-Tiles,
    Erkundung, siehe belief.py). Default False, damit alte Checkpoints und
    Experimente unveraendert reproduzierbar bleiben (from_dict fuellt fehlende
    Schluessel mit dem Default)."""
    home_first: bool = False
    """True: Zielzuweisung bestraft Ziele in der gegnerischen Haelfte (+600, d. h.
    eigene Punkte-Tiles < gegnerische Punkte-Tiles < eigene Kandidaten < ...)."""
    home_penalty: float = 0.0
    """> 0: ueberschreibt die Kosten fuer Ziele in der gegnerischen Haelfte
    (home_first nutzt 600). 1500 ordnet: eigene Punkte-Tiles < eigene Kandidaten
    < gegnerische Punkte-Tiles < Erkundung (Prioritaetsstufen kosten je 1000)."""
    home_last_only: bool = False
    """True: home_first/home_penalty nur im letzten Match (Analyse 19.10.: in
    Match 3 laufen ~4,7 Units zu Punkte-Tiles der Gegnerhaelfte, 0,4 besetzt)."""
    explore_memory: bool = False
    """True: Erkundung bevorzugt Tiles, die in KEINEM bisherigen Match gesehen
    wurden (+300 Kosten fuer frueher gesehene, siehe features.assign_targets)."""
    # --- Match-1-Schalter (12.10.2026, Analyse scripts/analyze_timing.py: wir sehen
    # das erste Relic im Median 10 Steps nach Solution_92, in 12/80 Matches nie).
    explore_grid: bool = False
    """True: Erkundungsziele = je ein unerkundetes Tile pro 4x4-Block statt der
    unerkundeten Tiles am naechsten zum Schwerpunkt -> Units verteilen sich."""
    scripted_explore: bool = False
    """True: Hat eine Unit nur ein Erkundungsziel (kein Punkte-/Kandidaten-Tile),
    laeuft sie heuristisch dorthin statt der Netz-Aktion (ausser Sap). Das Netz
    hat gelernt, am Matchanfang auf Energiefeldern nahe dem Spawn zu warten."""
    explore_stale: int = 0
    """> 0: In Match 0, solange kein Relic bekannt ist, gilt ein Tile nur als
    erkundet, wenn es in den letzten `explore_stale` Steps oder ab match_step 49
    gesehen wurde - das Relic-Paar spawnt erst bei match_step 0..49, Gebiete von
    vorher koennen es verbergen. 0 = aus."""
    early_inference: bool = False
    """True: Punkte-Tile-Schluesse schon vor match_step 50, sobald das Relic-Paar
    des aktuellen Matches sicher gespawnt ist (siehe Belief._stable)."""
    relic_filter: bool = False
    """True: Punkte-Schluesse ignorieren Units ausserhalb jeder moeglichen
    Relic-Reichweite (Belief._possible_point_zone, Idee aus Solution_92)."""
    subset_infer: bool = False
    """True: zusaetzlich Differenzen von Teilmengen-Beobachtungen auswerten
    (Belief._add_differences) und doppelte Gleichungen nicht speichern."""
    cand_quota: int = 0
    """> 0: so viele eigene Kandidaten-Tiles rangieren vor den Punkte-Tiles der
    Gegnerhaelfte (features.assign_targets)."""
    sticky: float = 0.0
    """> 0: Kostenabzug (in Feldern), wenn eine Unit ihr Ziel aus dem vorigen
    Step behaelt (20.10.2026). Diagnose: 15-24 % aller Unit-Schritte wechselten
    das Ziel, obwohl das alte noch gueltig war (features.assign_targets)."""
    far_opp: int = 0
    """> 0: Punkte-Tiles der Gegnerhaelfte, die weiter als far_opp Felder von der
    Unit entfernt sind, rangieren hinter den Kandidaten-Tiles (20.10.2026,
    features.assign_targets)."""
    far_cand: bool = False
    """True (mit far_opp): auch Kandidaten der Gegnerhaelfte, die weiter als far_opp
    entfernt sind, rangieren hinter den eigenen Kandidaten (20.10.2026)."""
    cand_boost: float = 0.0
    """> 0: eigene Kandidaten-Tiles rangieren wie Punkte-Tiles mit cand_boost Feldern
    Zusatzweg, Punkte-Tiles der Gegnerhaelfte bekommen denselben Zuschlag."""
    contest_sap: bool = False
    """True: steht auf dem Ziel-Tile ein Gegner, den die Unit per Kollision nicht schlaegt,
    sappt sie dieses Tile aus der Entfernung (main._contest_sap)."""
    energy_pref: float = 0.0
    """> 0: Punkte-Tiles mit hoher Feldenergie bevorzugen (energy_pref Felder Umweg je 10 Energie)."""
    explore_quota: int = 0
    """> 0: so viele Units suchen in Match 2/3 gezielt das Relic-Paar, solange es fehlen
    kann (bis explore_until), Ziel: lange nicht gesehene Tiles der eigenen Haelfte."""
    explore_until: int = 75
    pt_sap: bool = False
    """True: Unit auf eigenem Punkte-Tile, deren Netz-Aktion 'stehen' ist, sappt
    stattdessen ein sichtbares Ziel in Reichweite (bleibt dabei auf dem Tile)."""
    pt_sap_reserve: int = 0
    """Energie, die nach dem Sap mindestens uebrig bleiben muss (pt_sap)."""
    pt_sap_zone: bool = False
    """True (mit pt_sap): auch gestapelte Units und Units auf Kandidaten-Tiles sappen."""
    safe_moves: bool = False
    """True: Aktionsmaske verbietet Zuege auf ein Tile mit sichtbarem Gegner, dessen
    Energie mindestens so gross ist wie die eigene nach dem Zug (Kollision verloren)."""
    idle_sap: bool = False
    """True: jede Unit, deren Netz-Aktion 'stehen' ist, sappt ein Ziel in Reichweite,
    wenn danach noch idle_sap_reserve Energie bleibt (auch abseits der Punkte-Tiles)."""
    idle_sap_reserve: int = 30
    art_sap: bool = False
    """True (21.10.2026): Unit, die nicht als Erste auf einem Punkte-Tile steht, sappt
    statt ihrer Netz-Aktion, wenn das Ziel mindestens art_min_hits Gegner trifft,
    danach art_reserve Energie bleibt und (art_safe) kein sichtbarer Gegner mit
    Energie >= Sap-Kosten sie in Manhattan-Reichweite hat. Solution_92 prueft die
    Sap-Reichweite nach Manhattan, die Engine erlaubt das ganze Quadrat (Chebyshev)."""
    art_min_hits: int = 2
    art_reserve: int = 0
    art_safe: bool = True
    art_surplus: bool = False
    """True (22.10.2026): art_sap nicht fuer Units, deren Ziel ein Punkte-Tile der eigenen Haelfte ist."""
    threat_feats: bool = False
    """True (21.10.2026): Netz-Eingabe um features.THREAT_NAMES erweitert (Gefahr je Tile,
    bester Sap). Andere Eingabegroesse -> nur fuer neu trainierte Netze."""
    dodge: bool = False
    """True (21.10.2026, nur Auswertung): Units, die stehen/sappen wuerden und laut
    opp_model von Solution_92 direkt beschossen werden, weichen einen Schritt aus."""
    dodge_mode: str = "lethal"
    dodge_verify: bool = False
    """True (22.10.2026, nur Auswertung): dodge/dodge_auto erst, wenn sich die Vorhersage des
    Solution_92-Modells in diesem Spiel bestaetigt (>= 3 Faelle, >= 60 % direkte Treffer bei
    stehen gebliebenen vorhergesagten Zielen). Gegen anders zielende Gegner bleibt es aus."""
    obey_target: bool = False
    """True (22.10.2026): ohne nahen Gegner kein Zug weg vom zugewiesenen Punkte-/Kandidaten-Tile
    (BFS-Distanz waechst) -> erster Schritt des kuerzesten Wegs."""
    mobile_seen: bool = False
    """True (22.10.2026): collision_guard/holder_guard zaehlen Gegner, die im letzten Step am selben
    Ort standen, nicht als beweglich (nicht nur Gegner auf bekannten Punkte-Tiles)."""
    holder_guard: bool = False
    """True (22.10.2026): stehende Unit weicht aus, wenn ein beweglicher, mindestens gleich starker
    sichtbarer Gegner kardinal daneben steht (er zieht sonst oft auf unser Tile)."""
    collision_guard: bool = False
    """True (22.10.2026): Zuege sperren, wenn ein beweglicher, mindestens gleich starker sichtbarer
    Gegner im selben Step auf dasselbe Tile ziehen kann (Kollisionstod)."""
    window_infer: bool = False
    """True (22.10.2026): Punkte-Tile-Inferenz auch in den ersten 50 Steps von Match 2/3 (Spawnfenster
    neuer Relics), wenn um jede eigene Unit das 5x5-Feld sichtbar ist. Diagnose V8-Verlustspiele: in
    Match 2/3 bleiben ~2 echte eigene Punkte-Tiles pro Step ungetestete Kandidaten bekannter Relics."""
    window_infer_all: bool = False
    """True (22.10.2026): im Spawnfenster immer schliessen; Unit-Tiles ohne ganz sichtbares 5x5-Feld
    zaehlen als offene Unbekannte (ein ungesehenes neues Relic koennte sie punkten lassen)."""
    sap_still_all: bool = False
    """True (22.10.2026): wie sap_still, aber fuer jedes Sap (Netz, Artillerie, Halter): nur wenn ein
    stehender Gegner direkt oder mindestens zwei stehende im 3x3-Bereich getroffen werden."""
    sap_still: bool = False
    """True (22.10.2026): pt_sap nur auf stehende Gegner (unbewegt im letzten Step oder auf bekanntem
    Punkte-Tile); ziehende Ziele weichen dem direkten Treffer aus."""
    sap_relevant: bool = False
    """True (22.10.2026): pt_sap nur auf Gegner auf/neben bekannten Punkte-Tiles, nicht auf
    durchziehende Erkunder (Energie der Halter schonen)."""
    sap_no_overkill: bool = False
    """True (22.10.2026): kein Sap auf Gegner, die durch schon geplante Saps desselben Steps sicher
    sterben (ohne weiteren lebenden Gegner daneben) -> Energie behalten statt Mehrfach-Treffer."""
    sym_map: bool = False
    """True (22.10.2026): sichtbare Tiles fuellen auch ihr Spiegeltile (Typ und Feldenergie). Die
    Karte ist in allen geprueften Zustaenden exakt symmetrisch (auch nach Drift); Solution_92 nutzt das."""
    sap_reserve_k: float = 0.0
    """22.10.2026: Regel-Saps (pt_sap, art_sap) nur mit Energie >= Sap-Kosten * (1 + k) (+ alte
    absolute Reserven). Diagnose V7-Verlustspiele: Halter haben 60-84 statt 82-115 Energie, wir
    sappen 2-3x so oft wie Solution_92; 74 % der Toten hatten weniger Energie als ein Sap kostet."""
    unstack: bool = False
    """True (22.10.2026): gestapelte Unit (Punkte-Tile gehoert schon einer anderen eigenen Unit)
    wartet nicht, sondern geht per BFS-Schritt zu ihrem zugewiesenen Ziel."""
    reach_assign: bool = False
    """True (22.10.2026): Zielzuweisung nach BFS-Weglaenge ueber die Gedaechtniskarte statt
    Luftlinie; unerreichbare Ziele (z. B. Punkte-Tiles unter Asteroiden) nur als letzte Wahl."""
    drift_track: bool = False
    """True (22.10.2026): Drift von Asteroiden/Nebel erkennen (sichtbare Tiles passen zur um
    (s, -s) gerollten Erinnerung) und die ganze Gedaechtniskarte mitrollen."""
    path_fix: bool = False
    """True (22.10.2026): Zug, der nach Luftlinie naeher ans Ziel fuehrt, auf dem BFS-Weg aber
    nicht (Sackgasse an Asteroidenwand), durch den ersten Schritt des kuerzesten Wegs ersetzen.
    Diagnose 360581: Units pendeln zwischen Wand und Sackgasse und verlieren alle Energie."""
    nebula_infer: bool = False
    """True (22.10.2026): Tiles in Sensorreichweite eigener Units, die unsichtbar sind, sind Nebel.
    Behebt veraltete Asteroiden im Gedaechtnis (Drift), die bei kleiner Sicht Wege sperren
    (z. B. Units eingesperrt am Spawn, 360014)."""
    dodge_bait: bool = False
    """True (22.10.2026): beim Ausweichen in Manhattan-Reichweite der Schuetzen bleiben (Koeder:
    Solution_92 zielt auf unsere hoechste ID in Reichweite) und nicht neben eigene Units ziehen."""
    dodge_auto: bool = False
    dodge_auto_max: float = 0.5
    """Hoechster geschaetzter Streufaktor, bei dem dodge_auto ausweicht. 22.10.2026: Gewinn fast
    nur bei 0,25 (schwere Karten +2,7 pp), bei 0,5 leichte Karten −1,7 pp."""
    """True (22.10.2026, nur Auswertung): dodge (mit dodge_mode) nur, solange der geschaetzte
    Sap-Streufaktor (param_est, sonst 0,5) <= 0,5 ist. Entwicklung 500720-500779: dodge always
    bei Streufaktor 0,25 / 0,5 / 1,0: +5,9 / +2,5 / −2,2 pp."""
    """'lethal': nur ausweichen, wenn Stehenbleiben vermutlich toetet; 'always': immer."""
    tactics_when_behind: bool = False
    """True (21.10.2026): dodge und art_sap greifen nur, wenn wir im laufenden Match nach Punkten
    hinten liegen. Entwicklung: beide helfen auf schweren Karten (+10 bis +14 pp), kosten aber
    auf leichten Karten 2-3 pp."""
    nebula_avoid: bool = False
    """True (21.10.2026, nur Auswertung): geschaetzter Nebel-Energieabzug (param_est) >=
    nebula_avoid_min -> keine Zuege in Nebel ohne Punkte-Tile; bei >= 25 verlassen Units den Nebel.
    Analyse 2000 Karten: V3 gegen Solution_92 bei Nebelabzug 25 nur 65,5 % statt ~78 %."""
    nebula_avoid_min: int = 25
    nebula_avoid_mode: str = "mask"
    """'mask' (Zuege in Nebel gesperrt, V5-B) oder 'soft' (Umweg/Wartezeit statt Sperre)."""
    """Ab diesem geschaetzten Abzug greift nebula_avoid. 22.10.2026: bei 5 auf 60 Karten mit
    Nebelabzug 5 −16,7 pp (Units erreichen ihre Ziele nicht mehr), bei 25 auf 100 Karten +5,0 pp."""
    sap_dropoff_est: bool = False
    """True (22.10.2026, nur Auswertung): Sap-Zielwertung mit dem geschaetzten Streufaktor
    (param_est) statt der festen Annahme 0,5."""
    stack_guard: bool = False
    """True (22.10.2026, nur Auswertung): keine Zuege auf ein Punkte-Tile, auf dem schon eine
    eigene Unit steht (Stapeln bringt keinen Punkt und verdoppelt Sap-Schaden)."""
    relic_search: bool = False
    """True (22.10.2026, nur Auswertung): ein fester Sucher sucht in Match 2/3 das neue Relic-Paar
    (features.relic_search), solange es fehlen kann."""
    relic_search_until: int = 75
    relic_search_stale: int = 25
    siege: bool = False
    """True (21.10.2026, nur Auswertung): Units, deren Ziel ein vom Gegner (sichtbar oder
    wahrscheinlich im Nebel) besetztes Punkte-Tile ist, laufen nicht hinein, sondern zur
    naechsten Schussposition ausserhalb seiner Manhattan-Reichweite und sappen von dort
    (rules.SiegePlan). Fehlt Energie, warten sie dort."""
    siege_min_score: float = 1.5
    """Mindestens erwartete getroffene Gegner (direkt 1, daneben 0,5) fuer einen Schuss."""
    siege_reserve: float = 0.0
    siege_prob: float = 0.5
    """Ab dieser Besetzungswahrscheinlichkeit zaehlt ein Nebel-Punkte-Tile zur Festung."""
    sap_kill_first: bool = False
    """True: Sap-Ziel bevorzugt Gegner, die der direkte Treffer zerstoert (Energie < Sap-Kosten)."""
    sap_kill_safe: bool = False
    """True (22.10.2026): Sap-Ziel bevorzugt lebende Gegner, die der direkte Treffer sicher toetet
    (Energie + Feldgewinn < Sap-Kosten). Korrigiert sap_kill_first, das auch schon tote Gegner
    (Energie < 0, verschwinden vor dem Sap) bevorzugte."""
    sap_pt_first: bool = False
    """True: Sap-Ziel bevorzugt Gegner auf bekannten Punkte-Tiles (_best_sap_target)."""
    sap_geometry: bool = False
    """True: bei bereits vorhandenem Sap-Ziel weitere legale Zentren pruefen;
    nur strikt hoeherer bisheriger Energiescore ersetzt das Ziel. Keine neue Sap-Maske."""
    keep_dead: bool = False
    """True: Null-Tiles frueherer Matches gelten wieder, sobald feststeht, dass
    sie nicht neben einem neuen Relic liegen (Belief._restore_dead)."""
    keep_dead_fast: bool = False
    """True: wie Solution_92 - Null-Tiles bleiben ueber Matchgrenzen gueltig, nur
    Tiles neben NEU gefundenen Relics werden wieder offen (Risiko: ein noch
    ungesehenes neues Relic; Widersprueche oeffnen dann alles)."""
    stale_all: bool = False
    """True: explore_stale gilt in JEDEM Match, solange das Relic-Paar dieses
    Matches noch unbekannt ist (neue Paare spawnen auch in frueher gesehenen
    Gebieten)."""
    opp_infer: bool = False
    """True: Null-Tiles auch aus dem Punktgewinn des Gegners (Belief._infer_from_enemy)."""
    # --- Regel-Schalter (19.10.2026, rules.py). Default aus.
    pt_walk: bool = False
    """True: Units, deren Ziel ein bewiesenes Punkte-Tile ist, laufen auf dem
    kuerzesten Weg (BFS) dorthin statt der Netz-Aktion (ausser Sap)."""
    pt_walk_own: bool = False
    """pt_walk nur fuer Punkte-Tiles der eigenen Haelfte."""
    pt_walk_from_match: int = 0
    """pt_walk erst ab diesem Match (0 = immer)."""
    pt_hold: bool = False
    """True: eine Unit, die als Erste auf einem bewiesenen Punkte-Tile steht,
    verlaesst es nicht (Netz darf nur stehen oder sappen)."""
    ram: bool = False
    """True: Units fahren auf Nachbar-Tiles mit schwaecheren Gegnern und
    zerstoeren sie per Kollision (rules.ram_move)."""
    ram_margin: float = 10.0
    fog_sap: bool = False
    """True: Units auf bewiesenen Punkte-Tiles, die stehen wuerden, sappen auf
    unsichtbare Gegner-Punkte-Tiles, wenn der Gegner-Punktgewinn versteckte
    Besetzer verraet (rules.fog_sap)."""
    fog_any: bool = False
    """True: Nebel-Sap fuer jede stehende Unit, nicht nur auf Punkte-Tiles."""
    fog_reserve: float = 30.0
    fog_sap_max_sensor: int = 4
    """fog_sap nur bei Sensorreichweite <= diesem Wert (22.10.2026: Schwachstelle Sicht 1-2)."""
    """Energie, die nach einem Nebel-Sap mindestens uebrig bleiben soll."""
    reward_fix: bool = False
    """True: drei Reward-Korrekturen (Pruefung 14.10.): wiederverwendete Unit-IDs
    nach Tod gelten als Tod, kein Punkte-Reward bei negativer Energie, phi = 0
    im terminalen Matchende-Zustand. Default aus = alte Trainings reproduzierbar."""
    terminal_death_potential: bool = False
    """True: auch beim bereits erkannten Unit-Tod den terminalen Potentialterm
    -w_shape * phi(s) addieren. Keine neue Done-Regel; fuer den geplanten Pilot
    zusammen mit reward_fix=True. Default False erhaelt bisherige Rewards."""
    active_targets: bool = False
    """True: nur Units mit Energie >= 0 erhalten Ziele; sonstige Features bleiben
    unveraendert. Default False erhaelt das Verhalten alter Checkpoints."""
    smart_sap: bool = False
    """True: Sap-Ziel mit Teamabstimmung (rules.plan_sap): kein Overkill,
    stehende Gegner/Gegner auf Punkte-Tiles bevorzugt, Abschuss-Bonus; lohnt
    sich kein Sap mehr, bleibt die Unit stehen."""
    use_shaping: bool = True
    """False: Reward = w_point (auf bewiesenem Punkte-Tile) + w_match * Env-Reward.
    Ohne Potential-, Explore-, Discovery-, Stack-, Energie-, Tod- und Sap-Terme."""
    canonical: bool = True
    """False: keine Spiegelung; je Seite ein eigenes Netz (agent_p0/agent_p1)."""

    # --- Aktionen
    use_sap: bool = True              # 6. Aktion: Sap auf heuristisch bestes Ziel
    mask_actions: bool = True         # Asteroiden/Kartenrand/Sap ohne Ziel maskieren

    # --- Reward Shaping (siehe reward.py)
    w_point: float = 1.0
    w_shape: float = 0.5
    w_explore: float = 0.3
    w_energy: float = 0.1
    w_stack: float = 0.3
    w_death: float = 0.5
    w_match: float = 2.0
    w_discovery: float = 0.5
    w_sap_hit: float = 0.3
    w_opp_points: float = 0.0
    """> 0: Strafe je Gegner-Punkt in diesem Step, auf das Team verteilt (19.10.)."""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "AgentConfig":
        """Unbekannte Schluessel ignorieren (aeltere/neuere Checkpoints)."""
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in (d or {}).items() if k in known})
