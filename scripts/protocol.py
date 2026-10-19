"""Evaluationsprotokoll als Code (Details und Begruendung: docs/EXPERIMENT_PROTOKOLL.md).

Die drei Seed-Mengen sind disjunkt:

  Training    [0, 100_000)        Start k nutzt k * 10_000 + Spielpaar-Index
  Validierung [500_000, 500_000 + N_VAL)   Lernkurven, Tuning
  Test        [900_000, 900_000 + N_TEST)  NUR finale Auswertung

Jeder Seed wird von beiden Seiten gespielt (player_0 und player_1).
"""
from __future__ import annotations

TRAIN_SEED_BASE = 0
TRAIN_SEED_STRIDE = 10_000   # Abstand der Env-Seeds zwischen Trainingsstarts
VAL_SEED_BASE = 500_000
TEST_SEED_BASE = 900_000

N_VAL = 8
N_TEST = 30

SIDES = ("player_0", "player_1")
EVAL_OPPONENTS = ("default", "solution92")

# Curriculum: erst nur default, danach abwechselnd default / Solution_92
CURRICULUM_WARMUP_FRAC = 0.25


def train_seed(run_seed: int, game: int) -> int:
    """Env-Seed fuer Trainingsspiel `game` (zwei Spiele = ein Seed, beide Seiten)."""
    s = TRAIN_SEED_BASE + run_seed * TRAIN_SEED_STRIDE + game // 2
    assert s < VAL_SEED_BASE, "Trainings-Seeds wuerden in die Validierung laufen"
    return s


def train_side(game: int) -> str:
    return SIDES[game % 2]


def train_opponent(game: int, total_games: int, sol92_frac: float | None = None,
                   pool_frac: float = 0.0) -> str:
    """Curriculum. sol92_frac (19.10.2026): Anteil Solution_92 nach der
    Aufwaermphase; None = urspruengliches Protokoll (abwechselnd, 50 %).
    Beide Seiten desselben Seeds bekommen denselben Gegner."""
    if game < int(CURRICULUM_WARMUP_FRAC * total_games):
        return "default"
    if sol92_frac is None:
        return "default" if (game // 2) % 2 == 0 else "solution92"
    pair = game // 2
    u = (pair * 0.6180339887) % 1.0
    if u < sol92_frac:
        return "solution92"
    return "pool" if u < sol92_frac + pool_frac else "default"


def val_seeds(n: int = N_VAL) -> list[int]:
    return [VAL_SEED_BASE + i for i in range(n)]


def test_seeds(n: int = N_TEST) -> list[int]:
    return [TEST_SEED_BASE + i for i in range(n)]
