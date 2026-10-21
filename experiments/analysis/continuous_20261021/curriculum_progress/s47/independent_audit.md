# s47 completed-pair independent data audit

Complete: True. 2026-10-21T11:34:58.080190+00:00

Single known-start diagnostic on already used development maps. Not a method conclusion, no generalization over new training starts, and no release authority. Fixed starts 47/48/49 and all six final evaluations remain required; no optional stopping or gate alteration based on s47.

Both arms have 3,000 training rows, 160 intermediate validation rows, ten reproduced aggregates and 240 final evaluation rows. Schemas, complete unique keys, finite measurements (only initial loss before learning may be NaN), 303-step games, point version 2 and result consistency passed.

Initial identities, all 32 validation-zero games and the first 100 training games agree in every non-time field. Both schedules contain 1,426 Default and 1,574 Solution_92 games; exactly 200 positions differ as planned and schedules are identical from index 894.

Frozen source inventory, HEAD, plans, interpreter, protected weights, output hashes, phase success and final checkpoint metadata/hash bindings passed. Protocol remains fixed.

| Opponent | Control W/D/L | Early W/D/L | Early − control | Paired 95% card CI |
|---|---:|---:|---:|---:|
| default | 120/0/0 | 119/0/1 | -0.833 pp | [-2.500, +0.000] pp |
| solution92 | 86/0/34 | 62/0/58 | -20.000 pp | [-32.500, -7.500] pp |

Bootstrap: 5,000 whole-card draws, NumPy default_rng seed 0; two sides and paired arms kept together.

No tensor loading or independent tensor finiteness re-audit; verified saved finite-tensor metadata, completed audit return codes, and checkpoint byte-hash binding only. No training, evaluation, test jobs, repository edits, commits or pushes.

Machine-readable evidence: /tmp/sherlock-curriculum-s47-audit-20261021.json
