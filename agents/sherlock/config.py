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
    """Energie, die nach einem Nebel-Sap mindestens uebrig bleiben soll."""
    reward_fix: bool = False
    """True: drei Reward-Korrekturen (Pruefung 14.10.): wiederverwendete Unit-IDs
    nach Tod gelten als Tod, kein Punkte-Reward bei negativer Energie, phi = 0
    im terminalen Matchende-Zustand. Default aus = alte Trainings reproduzierbar."""
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
