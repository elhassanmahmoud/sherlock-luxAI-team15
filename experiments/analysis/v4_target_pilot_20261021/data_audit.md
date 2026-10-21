# Independent Stage 1 data audit — 2026-10-21

**Ready within reviewed scope: the completed run fails the preregistered influence gate and the pilot must stop.** No discrepancy was found in the saved results, recorded trajectory comparisons, scheduling, or checked hashes.

The decisive limitation is **zero eligible target choices at all 32 scheduled states**. There were **zero alternative-target calls**. The observed 0/32 gate result therefore does **not** show that V3 ignores target features or that a changed target cannot affect its action. This run tested baseline shadow reproduction, but did not exercise a target intervention. The individual eligibility filters causing the empty selections cannot be recovered from these saved records, and were not investigated or retuned in this audit.

## Independently checked evidence

A standalone Python standard-library check read `execution_state.json`, `run_01/manifest.json`, `run_01/result.json`, and all eight game JSON files without importing project modules, Torch, NumPy, or the engine. No games, training, or tests were run.

- Exactly four registered `(seed, side)` pairs, each with one control and one shadow game: **eight complete games**, each **303 steps**, **2,424 game steps** in total.
- All two-player trace lists are complete and contiguous from step 0 through 302. Across eight games there are **4,848 recorded player-action entries**, each containing a complete 16×3 action array and observation/action digests.
- Each control/shadow pair has exactly equal saved trace objects, including both players' complete actions and observation/action digests. All summary fields except elapsed `secs` match. Legal observations are retained as digests, so this audit compares those saved digests rather than independently reconstructing observation bytes.
- Each shadow game has exactly eight unique registered slots: match indices 1/2 × match steps 25/45/65/85. Each slot's recorded baseline action equals its corresponding live trace action. All **32** records have empty `available_choices`, null selected unit/target, empty `alternatives`, and zero distinct changed arrays. Control games have no scheduled-shadow records.
- Recomputed gate: **0 action-changing states / 32 scheduled states**, threshold **8**, `passed=false`, `next_step=stop_pilot`. Missing/empty choices remain in the denominator. Baseline-only shadow replay at all 32 slots is supported by the reviewed runner path completing successfully; no alternative action was evaluated.

| Map | V3 side | Match wins, V3:opponent | Total points, V3:opponent | Scheduled states |
| --- | --- | --- | --- | --- |
| 524000 | player_0 | 3:0 | 300:55 | 8 |
| 524000 | player_1 | 3:0 | 262:57 | 8 |
| 524001 | player_0 | 1:2 | 821:856 | 8 |
| 524001 | player_1 | 2:1 | 914:645 | 8 |

Each row applies identically to its control and shadow game. These repeated trajectories are an isolation check, not eight independent strength samples; all point summaries carry counting version 2.

## Execution and protection checks

- Manifest, execution state, and inspected checkout agree on frozen commit `1255f005255521d8d4a981147fb80064df3e0de4`.
- Rehashed all **65** source/runtime files listed in the execution state: all match. Rehashed all **eight** protected current/old checkpoint files: all match the execution-state hashes, manifest's before hashes, and result's after hashes. Candidate hash matches protected V3 `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`; old checkpoints retain `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.
- One completed job, return code **0**, `active=null`, and `verified_inputs_after=true`. Runner elapsed **15.0595 seconds**; launcher process elapsed **18.5832 seconds**. Completion precedes both registered deadlines and is within the 1,800-second collection limit. Execution-state fields `status=stage1_influence` and `remaining_games=8` are retained launch metadata; completion is established by the job and result records.
- `run_01` contains exactly the eight game files plus manifest and result, with no failure file: **6,621,523 bytes**, below **134,217,728 bytes**. Only seeds 524000/524001 occur; no held-out map run is present.

## Disposition

Stop this target pilot under its unchanged gate. Do not fit the conditional learner, consume the held-out maps for this pilot, or expand the target set based on this result. The data establish that this fixed selection procedure supplied no eligible interventions in these sampled windows; they do not establish target-feature insensitivity or a general limitation of learned target choice. A separate CNN proposal is outside this audit.
