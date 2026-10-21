# Independent final CNN3 audit

Audit completed 2026-10-21T18:12:54.879134+00:00. **The completed candidate fails the fixed development gate. No direct, fresh, course or promotion branch is justified; retain V3.** The independent computation reproduces every reported count, paired interval and gate in `results.json`.

## Outcomes and fixed decision

| Agent | Solution_92 wins / 120 | Draws | Default wins / 120 |
|---|---:|---:|---:|
| Final CNN3 candidate | 89 | 0 | 120 |
| Original PPO60 | 96 | 0 | 120 |
| Unchanged V3 | 102 | 0 | 120 |

Candidate minus PPO60 is −5.83 percentage points on Solution_92, paired 95% map interval [−15.83; +3.33]. Candidate minus V3 is −10.83 points, interval [−20.00; −2.50]. Both default differences and intervals are exactly zero. Each interval resamples 60 whole maps, keeping both sides and the agent pair together, with 5,000 draws, NumPy generator seed 0 and 2.5/97.5 percentiles. I implemented the resampling separately using integer map indices; no project analysis function was imported.

The candidate meets 120/120 default but fails both Solution requirements: at least 108 wins and strictly more wins than PPO60. The known development maps are reused selection data, not an independent confirmation set. The negative result does not establish a general limitation of CNN/PPO, isolate the opponent mix causally, or justify an extended/intermediate-checkpoint search.

## Data and training integrity

Each full evaluation CSV has the exact 24-column schema and all 240 unique opponent/map/side keys: default and Solution_92, maps 500720–500779, both sides. All measurements are finite and in the checked legal ranges; count fields are integral, invalid-action fractions are zero, all games have 303 steps and point-counting version 2. Result, game-win and point-win fields agree with their underlying match wins and point totals. No subset, duplicate or missing key is accepted.

The four current V3 controls have exactly the expected keys on 500720–500721 and reproduce every one of 23 non-time fields against the frozen V3 reference. Control/reference/checkpoint hashes and successful job outputs agree. This is reproduction of saved summary fields, not a claim of independently inspected full trajectories.

Training completed ten ordered iterations of 24 games, with 837,246 recorded unit steps, finite required losses/statistics, and expected `wr_teacher=nan`. Its log records iterations 1–10, and the CSV hash matches the completed technical verification. Elapsed process time was 2330.797 seconds (38.85 minutes), inside 90 minutes and the 03:15 UTC internal deadline. The exact registered schedule was independently recreated: 120 maps on both sides, 211 Solution_92 and 29 default assignments. Training result means are not used as evaluation strength evidence.

There were **724 new games**: 240 PPO60 evaluations, four V3 controls, 240 training games and 240 candidate evaluations. The historical V3 reference adds no new games. The CNN execution state contains only these four successful jobs; their registered process IDs are no longer present. No direct/fresh/course qualification or promotion job is recorded for this failed candidate.

## Identity, storage and scope

Frozen HEAD remains `47388d4c7196d3ef90714e23045164f9c80348bf`. All 66 source entries, eight inputs (including the final checkpoint), and eight protected weights match their recorded SHA-256 values. All four current V3 copies remain `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`; all four old-release copies remain `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.

Final checkpoint SHA-256 is `d044fced91a887842cdb39f4540246038796b63fdc41c87bce8f270db4298e28`. It matches the technical-check JSON, frozen input and candidate job's checkpoint path. Root's technical report records 32 finite policy tensors, 30 changed tensors, unchanged architecture/effective configuration, latest/final policy equality and exact deterministic evaluation loading. **Those tensor, loader and architecture checks are root-generated evidence, not independently rerun by this audit.** The existing buffer-capacity normalization and newly defaulted false fields, including `joint_moves`, are accounted for; no historical optimizer-state restoration is claimed.

The last two helper-review requirements are closed: full control schema and protected V3 hash are asserted. Both helper archives match their executed-source copies. `*.csv -text` applies to the experiment CSVs, and Git's filtered and raw blob IDs match for candidate, baseline, controls, schedule and training CSVs, preserving their recorded bytes when added. This checks current attributes and content; publication/commit verification remains root's responsibility.

Only `final_audit.md` and `independent_results.json` were written for this final review. Computation used standard-library modules and NumPy, with no Torch/engine/project import, model test, game, training, source edit, HEAD change or Git mutation. Separate art-sap planning is outside this CNN audit. Full machine-readable checks and independent values are in `independent_results.json`.
