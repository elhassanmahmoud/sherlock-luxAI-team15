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
    """Env-Seed fuer Trainingsspiel `game` (zwei Spiele = ein Seed, beide Seiten).

    Starts ab 50 (22.10.2026): Block run_seed - 50 ab Kartenindex 5000. Bisher nutzten Trainings
    nur die Indizes < 2000 jedes Blocks; so bleiben neue Starts unter VAL_SEED_BASE und frisch."""
    if run_seed >= 50:
        assert game // 2 < 5000, "zu viele Trainingsspiele fuer einen Block"
        s = TRAIN_SEED_BASE + (run_seed - 50) * TRAIN_SEED_STRIDE + 5000 + game // 2
    else:
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


# 26.10.2026: Gegner-Liga nach der Aufwaermphase (Robustheit gegen andere Spielweisen, Plan
# docs/superpowers/plans/2026-10-26-league.md). Anteile je Spielpaar; "pool" = eigene alte Abgaben.
LEAGUE_MIX = (("solution92", 0.40), ("sol92_sq", 0.20), ("pool", 0.20), ("rush", 0.05),
              ("default", 0.15))


def league_opponent(game: int, total_games: int) -> str:
    """Wie train_opponent, aber nach der Aufwaermphase nach LEAGUE_MIX verteilt."""
    if game < int(CURRICULUM_WARMUP_FRAC * total_games):
        return "default"
    u = ((game // 2) * 0.6180339887) % 1.0
    acc = 0.0
    for name, frac in LEAGUE_MIX:
        acc += frac
        if u < acc:
            return name
    return LEAGUE_MIX[-1][0]


def opponent_schedule(total_games: int, sol92_frac: float | None,
                      pool_frac: float, mode: str) -> list[str]:
    """Materialize the original schedule or the fixed order-only study treatment."""
    if mode not in ("standard", "early_sol100", "league"):
        raise ValueError(f"Unknown opponent plan: {mode}")
    if mode == "league":
        if sol92_frac is not None or pool_frac:
            raise ValueError("league sets its own opponent shares (no sol92_frac/pool_frac)")
        return [league_opponent(g, total_games) for g in range(total_games)]
    if mode == "early_sol100" and (total_games, sol92_frac, pool_frac) != (3000, .7, 0.):
        raise ValueError("early_sol100 requires 3000 games, sol92_frac=0.7, pool_frac=0")
    labels = [train_opponent(g, total_games, sol92_frac, pool_frac)
              for g in range(total_games)]
    if mode == "early_sol100":
        # Select from the original sequence, before changing any positions.
        late_pairs = [g for g in range(750, total_games, 2)
                      if labels[g] == "solution92"][:50]
        labels[100:200] = ["solution92"] * 100
        for g in late_pairs:
            labels[g:g + 2] = ["default", "default"]
    return labels


def val_seeds(n: int = N_VAL) -> list[int]:
    return [VAL_SEED_BASE + i for i in range(n)]


def test_seeds(n: int = N_TEST) -> list[int]:
    return [TEST_SEED_BASE + i for i in range(n)]
