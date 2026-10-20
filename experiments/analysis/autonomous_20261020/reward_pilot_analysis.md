# Paired reward pilot — seed 46

Technical audit passed: 400 training games and 240 evaluation games per arm; source/protected-weight identity, equal fresh initialization, final checkpoint records and finite learned q/target tensors verified.

| Opponent | Control result | Fix result | Fix − control | 95% paired-map interval |
|---|---:|---:|---:|---:|
| default | 100.00% | 88.33% | -11.67 pp | [-19.17, -5.00] pp |
| solution92 | 35.83% | 12.50% | -23.33 pp | [-34.17, -13.33] pp |

`result` counts a draw as 0.5. Each opponent has 60 maps × both sides. Intervals resample whole maps 5,000 times, RNG seed 0.

**Continuation gate: stop_and_investigate.**
Reasons: solution92_delta_at_most_minus_5pp_and_upper95_below_zero, default_observed_delta_below_minus_2pp

Eligibility authorizes no automatic job and proves no benefit. This is exactly one paired initialization (seed 46), not evidence of average reward-method performance across initializations. Maps are reused development maps. Card intervals do not measure training-seed variability.

Diagnostic differences (fix minus control; excluded from the continuation gate):

| Opponent | Match-win margin/game | Point margin/game |
|---|---:|---:|
| default | -0.917 | -228.150 |
| solution92 | -1.267 | -350.458 |

The 400-game curriculum has 100 default-only games; fresh 3,000-game runs have 750. Pilot performance therefore need not predict the longer curriculum. Training loss is a numerical diagnostic, not a strength measure.

Prespecified continuation plan SHA-256: `77b70d41e6a56df688a7478fad2fb7b24c9315c77c605749437ffaf01f2eb369`.
Source HEAD: `3aa0e8ef37e01ff9f3ccf410c7169a6c5e72f36c`.
Exact source/input/checkpoint hashes and diagnostic intervals are in the JSON report.
