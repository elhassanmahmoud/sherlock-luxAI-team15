# Exploration replication — all three starts

All three completed pair audits and all six 240-game evaluation CSVs verified. Python source sets/hashes, interpreter, configs and versions agree across pairs. HEAD differences were restricted to documentation/data paths.

## Seed 47

| Opponent | Control | Slow | Slow − control | 95% map interval |
|---|---:|---:|---:|---:|
| default | 100.00% | 93.33% | -6.67 pp | [-13.33, -1.67] pp |
| solution92 | 71.67% | 47.50% | -24.17 pp | [-35.00, -13.33] pp |

## Seed 48

| Opponent | Control | Slow | Slow − control | 95% map interval |
|---|---:|---:|---:|---:|
| default | 98.33% | 93.33% | -5.00 pp | [-11.67, +0.83] pp |
| solution92 | 56.67% | 49.17% | -7.50 pp | [-16.67, +0.83] pp |

## Seed 49

| Opponent | Control | Slow | Slow − control | 95% map interval |
|---|---:|---:|---:|---:|
| default | 95.00% | 95.00% | +0.00 pp | [-6.67, +5.83] pp |
| solution92 | 55.00% | 47.50% | -7.50 pp | [-19.17, +4.17] pp |

## Equal-weight mean of three fixed starts

| Opponent | Control | Slow | Slow − control | 95% map interval |
|---|---:|---:|---:|---:|
| default | 97.78% | 93.89% | -3.89 pp | [-8.89, +0.00] pp |
| solution92 | 61.11% | 48.06% | -13.06 pp | [-19.17, -6.94] pp |

Prespecified method gate: not passed.
Positive Solution92 starts: 0/3.

Gate: mean Solution92 delta at least +3 pp, at least two positive starts, mean default delta at least −2 pp. Checks: {"mean_solution92_at_least_3pp": false, "at_least_two_positive_starts": false, "mean_default_loss_at_most_2pp": false}

The mean bootstrap averages the three starts within each map before drawing 60 whole maps (both sides together), 5,000 times with seed 0. These conditional intervals do not quantify training-start uncertainty. No best seed, job or promotion is selected.

All six final single-network CSVs included, no seed selection. Three fixed initializations do not establish general method superiority. Map bootstrap conditions on these starts and reused development maps. No ensemble is built or selected by this report; the separate ensemble pipeline remains out of scope.
