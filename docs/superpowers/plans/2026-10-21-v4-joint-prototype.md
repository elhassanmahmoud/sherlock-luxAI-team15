# V4 joint-action prototype: implementation and fixed first experiment

Spec: [approved V4 strategy](../../V4_STRATEGIE_20261021.md). User authorizes autonomous implementation, subagents, tests and sensible commits/pushes until **22 October 2026 06:00 Europe/Berlin (04:00 UTC)**; finish sooner if the bounded program is complete. Current release V3 is protected until independent qualification. No new parameter search after outcomes.

## Global constraints and rulings

- Worktree `/Users/moayedshawesh/Desktop/KI/sherlock-v4-joint`, branch `improvement/v4-joint-20261021`, base `a88d005`. Native app worktree creation returned `Not a git repository` because its context is parent KI; normal Git linked-worktree fallback used. Other existing experiment checkouts remain untouched.
- Python `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python`. One training OR at most two evaluation workers. No packages or engine/course-runner changes.
- Both released weights SHA-256 `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`; old6 backup `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`. Only experimental copies may gain a config flag; all 18 Q tensor sets must remain exactly identical.
- One boolean `joint_moves=False`. Evaluation-only intervention after all current action overrides. Disabled/training paths retain existing behavior. No Sap target/class changes, feature/reward/training changes or Q model changes.
- Root owns docs/results/integration; implementer owns config, main, new joint_actions module and focused tests. Reviewer read-only. Remote watcher fetches refs and reports changes but never merges.

## Task 1: bounded pair decoder and integration

Files: create `agents/sherlock/joint_actions.py`, `tests/test_joint_actions.py`; modify `agents/sherlock/config.py` and `agents/sherlock/main.py` only as needed.

Interface: `coordinate_moves(ctx, ids, q, masks, base_actions) -> dict[int, int]`. `ids` is the row order for q/masks; `base_actions` maps those UIDs to final canonical action classes AFTER existing rules. Return changed UID->canonical movement class only. Do not mutate any input. Use only legal observation/Belief fields from ctx, never engine truth, seed IDs, future states or opponent actions.

Fixed algorithm for candidate `v4_joint_pairs_v1`:

1. Eligible units have a legal finite baseline movement/STAY (0..4), valid position and finite nonnegative energy. Final SAP, negative-energy, illegal or nonfinite baseline units remain fixed. All fixed units count at their final destination when nonnegative; SAP stays at its current tile.
2. Candidate options are the baseline plus the TWO highest-Q legal finite movement/STAY classes (stable tie by action ID). No option whose Q is more than 15% of that unit's finite legal all-action Q span below its baseline Q; use `max(span, 1e-6)`. Include baseline even if a rule made it lower-Q. No absolute Q-unit thresholds or parameter sweep.
3. Iterate pairs deterministically by sorted UID, only initial Manhattan distance <=2 and whose option destination sets share at least one known point tile. Each UID may participate in at most one ACCEPTED pair update per step; rejected pairs do not reserve a unit. At most 120 pairs and 9 combinations per pair for 16 units.
4. For every nonbaseline option considered for a unit, require BOTH its current and destination tiles to have Chebyshev distance >1 from every visible nonnegative-energy enemy. This conservative guard preserves immediate collision/void stacking decisions; it is not a claim of safety from Sap or hidden enemies. The unchanged baseline remains allowed even when near an enemy.
5. Evaluate total DISTINCT known point tiles occupied by the entire team's resulting destinations (fixed and earlier accepted moves included). Count only units with finite nonnegative energy and for movement enough energy to pay the known move cost. This is NOMINAL productive occupancy, not a full prediction of field energy/Sap/void/collision effects. Do not award additional points for stacking, but do not penalize it or change it absent a strict occupancy gain.
6. Pick combination maximizing occupancy; among equal occupancy minimize SUM of nonnegative Q regret relative to each unit's baseline, normalized by each unit's span above; then prefer fewer changes, then action-ID tuple. Accept ONLY strict occupancy increase relative to current plan, never merely a Q improvement or stack reduction. Baseline is always fallback. Invalid numeric inputs must not create actions; no broad exception swallowing.
7. Integrate at the end of `Agent_x.act`, only `cfg.joint_moves and not self.training`. Convert final world action classes to canonical before helper and changed classes back with existing mirror functions. Preserve all SAP rows byte-for-byte and update `_prev_actions` for changed UIDs. Add small counters to ep_stats only if they can be done without changing existing CSV schema: calls and changed units. Do not modify `scripts/par_eval.py` or GAME_FIELDS for telemetry.

TDD: first failing tests of real helper/integration behavior, then minimal implementation. Cover: true occupancy gain with two units competing; gains counted globally with fixed outsider; no change if no strict gain; useful stack near enemy preserved; SAP/nonfinite/negative-energy fixed; masks/Q regret bound; legal action order ties; input arrays unchanged; valid role of baseline after rule override; mirrored player equivalence; disabled/training paths identical; no points/empty IDs; accepted unit not changed twice. Avoid tests that only repeat the loop.

Run focused tests while editing; run existing full pytest suite once after implementation. Do not start games/training. Self-review and commit code/tests only, report RED/GREEN commands and outcomes plus commit. Root dispatches independent review; implementer must not spawn a reviewer.

## Task 2: review and checkpoint/runner verification

Independent reviewer checks algorithm/spec and main integration, canonical/world mapping, legal/numeric fallback and no hidden information. Run a focused test only for a concrete unanswered doubt; do not rerun the whole suite. Root resolves findings, reruns only affected checks.

Root creates a NEW experimental checkpoint `experiments/candidates/v4_joint_pairs_v1_20261021.pth`, copying V3 with only cfg.joint_moves=true. Verify tensor/metadata identity, load both sides, run existing candidate-runner short check. V3-disabled deterministic smoke on four known cards, both sides/both opponents (16 games) must reproduce corresponding existing reference fields except elapsed time; otherwise reference reuse is disallowed and discrepancy investigated before results. Candidate action overhead: timed helper and representative real act; technical stop if p95 total act >50ms or max >250ms after warm-up on this Mac. These are our conservative prototype budget, not official course limits.

## Task 3: complete development and requested V3 comparison

Freeze source commit/hash list, Python/engine, candidate and protected input hashes before games; use existing evaluators and own short bounded launcher, not a general experiment framework. Verify no duplicate active jobs, no output overwrite. Hard cutoff 22Oct04:00UTC, reserve last45min for closing. Admission before each job uses measured conservative game duration × remaining count ×1.25 plus closing reserve; decline a job that cannot fit.

- Development cards **500720–500779**, both sides: candidate120 vsSolution_92 plus120 vsDefault. Baseline can reuse verified matching `experiments/analysis/enemy_tie_energy_20261021/development_v3.csv` (Sol102/120, Default120/120), with disabled smoke and source binding above.
- Also **120 candidate-vs-V3 development games**, those same60knowncards, regardless of opponent development gate so the user's requested direct test is delivered. This is descriptive, not fresh confirmation. Use unchanged V3 checkpoint as `self:` opponent.
- Continue to fresh confirmation only if candidate Sol >=108/120, Default120/120, direct development mean result >=0.5 and technical checks pass. No optional sample extension/parameter tweaking. Solution/Default gates and their intervals use actual win indicators (result==1); direct comparison uses result0/0.5/1. Report wins/draws/losses and exact shared-card bootstrap uncertainty; 5,000 card-pair resamples, NumPy default_rng(0), percentiles2.5/97.5.
- If negative, report complete failure of THIS fixed prototype. Inspect bounded activation/decision evidence before choosing a genuinely separate follow-up from the approved strategy. Do not repeatedly loosen thresholds to rescue v1.

## Task 4: fresh qualification, only if development qualifies

Proposed fresh blocks **523000–523199** opponents, **523200–523399** direct. Check all local/remote recorded seeds and reserve before use; any conflict is resolved before games, not after outcomes. Opponent confirmation:200cards×bothsides×2opponents for candidate AND baseline =1600games. Direct400games. Same paired-card bootstrap as above.

Require Sol delta >=5percentagepoints and95%lower>0; Default>=99% and delta>=−1pp; direct mean result lower95%bound>0.5. Only one preselected candidate, no merging historical and fresh rows. Fresh failures end this release attempt. No automatic promotion from development results.

Before any promotion, back up CURRENT V3 plus metadata/hashes (old6 backup also retained), run course/package checks, verify frozen results/candidate bytes and update shared docs. An accepted candidate may become V4. Final100%audit520000–520999 stays untouched unless candidate qualified AND sufficient deadline reserve remains. Otherwise honestly list as not run. No100%claim without2,000wins in that frozen audit.

## Task 5: handoff and deadline

Record implementation and results as sensible separate commits, push checked work and preserve foreign untracked files. Integrate into main only reviewed code with flagFalse by default; promoted weights only after all gates. Morning report `docs/MORGENBERICHT_20261022.md`: exact games, cards, opponents, results/uncertainty, weight state/backup, commits, missing work. Finish by06Berlin; own PID/command-verified jobs and watcher/wakefulness ended. Disable appropriate automations. Status messages must describe actual processes/results, never equate a quiet repo monitor with active development.
