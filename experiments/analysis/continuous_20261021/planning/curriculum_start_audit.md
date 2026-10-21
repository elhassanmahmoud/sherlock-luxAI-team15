# Read-only early-contact startup audit — 21 October 2026

Observed at 2026-10-21T09:47:04.874521+00:00. Healthy startup in the bounded artifact snapshot; no strength inference.

- Frozen HEAD and state/manifest source: `a5d2e61b0e8654bad64e31c29447ada1e439174d`. Study ID `20261021_early_contact_v1`; owner sidecar matches state, seed 47, control arm.
- Supervisor/child registration: 63520 / 63533, child PGID 63533. Start 2026-10-21T09:44:34.547488+00:00, deadline 2026-10-21T21:44:34.547488+00:00 (exactly 12 hours).
- Actual CLI matches manifest: full_rules_v3, seed47, 3000 games, sol92_frac0.7/pool_frac0, standard opponent plan, validation every750 on8 maps beginning500720, isolate-validation and no-test. Full 3000-label standard schedule and its SHA match independently computed values; counts1426 Default/1574 Solution_92.
- Initial identity: schema1, one CPU learner shared across both sides; q/target hashes equal; zero initial env/learn counters, empty replay and losses, no autosave; all recorded tensor/optimizer/agent/global RNG identities are well-formed SHA-256. Replay capacity300000, feature dimension79. Full initial config equals manifest; eps_decay_steps60000 and terminal_death_potential/active_targets/sap_geometry false.
- Snapshot contains 225 complete training rows, indices0–224, expected map/side/opponent keys and env_steps=(game+1)*303; learning has begun and latest recorded loss is finite. 1 initial NaN-loss row(s), only with learn_steps0. These are running partial data, not a final phase audit.
- Validation at after_games0 contains exactly32 raw keys (500720–500727, both opponents/sides), plus two16-game aggregate rows. Production schemas match; aggregates reproduce from raw rows. All observed training/validation games have303 steps and point_counting_version2; inspected numeric fields and results are consistent.
- Isolation is configured and initial/validation/training artifact sequence is plausible. This read-only audit does not independently remeasure in-memory RNG/tensor preservation; it relies on the already-reviewed implementation for that runtime guarantee.
- Job log has normal progress and no Traceback in this snapshot. No gate or performance conclusion was drawn.

## Process snapshot
```text
63520     1 63520 Ss   02:30 /Library/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python -B -m scripts.early_curriculum_study --run-id 20261021_early_contact_v1 --start
63533 63520 63533 Rs   02:30 /Library/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python -B -m scripts.experiment --variant full_rules_v3 --run-seed 47 --games 3000 --sol92-frac 0.7 --pool-frac 0 --val-every 750 --val-seeds 8 --val-seed-start 500720 --isolate-validation --no-test --tag 20261021_early_contact_v1 --opponent-plan standard --out /Users/moayedshawesh/Desktop/KI/sherlock-counterplay/experiments/runs/20261021_early_contact_v1_early_curriculum_s47_control
```

## Read snapshot SHA-256
Hashes below identify bytes actually read; train/state/log snapshots continue changing normally.
- `/Users/moayedshawesh/Desktop/KI/sherlock-counterplay/experiments/analysis/early_curriculum_20261021_early_contact_v1/state.json`: `e6002c5fdfd0420d6880394880a9a63b59e438280e4fdfae97530e01ae9ec847`
- `/Users/moayedshawesh/Desktop/KI/sherlock-counterplay/experiments/runs/20261021_early_contact_v1_early_curriculum_s47_control/initial_identity.json`: `f809fd270609ed48edf77b4f85f857a753f99b584b9ad8b8c8944093e617155c`
- `/Users/moayedshawesh/Desktop/KI/sherlock-counterplay/experiments/runs/20261021_early_contact_v1_early_curriculum_s47_control/manifest.json`: `47071738e59b6878269c70290a2cdc0f961bc54c20bc73444d5d0f3400b14db0`
- `/Users/moayedshawesh/Desktop/KI/sherlock-counterplay/experiments/runs/20261021_early_contact_v1_early_curriculum_s47_control/study.json`: `52caf6b3c9739ec1e55024e447b75f0c3886ac2b235e0fd80a50c9bb827b2ab2`
- `/Users/moayedshawesh/Desktop/KI/sherlock-counterplay/experiments/runs/20261021_early_contact_v1_early_curriculum_s47_control/train.csv`: `3d170e546965757cdd5f627e3619b23eb42c0476ce7bd9868af223c936b02274`
- `/Users/moayedshawesh/Desktop/KI/sherlock-counterplay/experiments/runs/20261021_early_contact_v1_early_curriculum_s47_control/val.csv`: `56af0675e750bd758e6deb6b6b82ee6910f73859e852166eb3b4b9223d579d89`
- `/Users/moayedshawesh/Desktop/KI/sherlock-counterplay/experiments/runs/20261021_early_contact_v1_early_curriculum_s47_control/val_games.csv`: `1fd7d95afb84f42b027d17ceec1ac94a0a1e4681970cc5e673f86217b838fc56`
- `/Users/moayedshawesh/Desktop/KI/sherlock-counterplay/experiments/analysis/early_curriculum_20261021_early_contact_v1/job_0_0.log`: `52acfaf2412ad582f4451955e2c3248b914061a5bc8d9ad43ae18f59c10825a9`

Scope: standard-library reads/parsing only, no Torch/model imports or loads, no tests, no new model jobs, no checkout changes. Only this requested report was written outside the checkout. An initial attempt to use /usr/bin/python3 was rejected by the local Xcode-license stub; the configured existing virtualenv interpreter was then used for standard-library inspection. This is unrelated to the running study.
