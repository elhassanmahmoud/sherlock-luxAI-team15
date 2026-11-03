# Actual final training acceptance — 2026-11-03

**PASS. Both actual completed training arms are technically accepted for fixed candidate construction. This is not a strength result or release approval.**

Both real final receipts passed the reviewed validator. Independent checks covered raw schedules/counts,303-step/v2 rows, exact counters, intervention/action-replay evidence, source/input/protected hashes, initial pair identity, finite saved tensors/Adam and live/saved/reloaded end evidence. Only checkpoint reads and validator-only architecture/optimizer construction ran after status=complete. No games, tests, model forwards, gradients, code/HEAD/plan/weight writes or commits.

Frozen HEAD: 7c906e16943ff7217afe1eae392834439cc76634. Independently rehashed 238 source/engine/protocol files, interpreter executable, 7 prepared inputs and 5 active-weight/ZIP records before and after audit: zero changes. Supervisor reports both children exited0 and no active owned jobs.

| Arm | Prefill | Learning | Known validation | Updates | Env steps | Train rescue units | Train rescue helper changes | Replay transitions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| control18 | 120 | 1200 | 96 | 180000 | 459960 | 0 | 0 | 4736222 |
| adapt18 | 120 | 1200 | 96 | 180000 | 459960 | 15737 | 2001 | 4730182 |

Each arm proves1320 complete raw rollouts,96 complete known validation games,1200 exact-schema train records and399960 actual act/update calls. Every train game adds150 updates and303 env steps. Final-action audits bind emitted canonical/world actions to actual replay writes. Treatment has interventions during learning; control has none. Helper-change totals describe intermediate rescue corrections, while the separate boundary audit verifies final emitted actions were stored.

Initial q/target/Adam/agent-RNG/global-RNG and empty replay agree across the paired start; only rescue_in_training differs. Prefill preserves tensors/optimizer with zero learning. Three fixed validations preserve complete learning/RNG identities. Final q tensors are finite, changed from source and distinct between arms. Saved configs/counters, Adam parameter moments at180000 updates and live/saved/reload hashes match.

These2832 game executions are not2832 independent tests. Known500000–500007 validations are repeated diagnostics;495000–495003 are explicitly reused training-only prefill cards. One paired start supports technical control/treatment comparison, not general causal superiority or a win-rate guarantee. C36 remains nonnominatable. Candidate construction must preserve V14 inference config and replace only member18; independent performance screen/confirmation and technical release checks remain required.

Machine-readable evidence: [training_final_audit.json](training_final_audit.json)
