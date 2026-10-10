"""Hyperparameter an einer Stelle (gut fuer die Folie "Training configuration")."""
from __future__ import annotations

from dataclasses import dataclass, asdict


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

    def to_dict(self) -> dict:
        return asdict(self)
