# Task 1 independent review — 2026-11-04

**Spec compliance: PASS. Code quality: APPROVE. No blocking findings.**

Reviewed the task brief, implementation report, supplied Task 1 diff, current collector/tests, action-student design, producer/consumer contract, and relevant unchanged runtime helpers. This review made no implementation edits and started no tests, training or Lux games. The previously reported 56 passing tests were inspected as evidence, not rerun or independently claimed here.

## Spec compliance

- `ExactCollector` intercepts one normal instance-local `act`. Its `q` forward hook immediately copies both input and raw output using `.numpy().copy()`. This precedes the actual runtime's `q[~masks] = -np.inf` mutation of the CPU tensor view. Neither belief/context nor policy is evaluated a second time.
- In the actual `Agent_x._act`, network rows follow `ids`; `_prev_feats` and `_prev_masks` are inserted in the same loop/order. The collector verifies the captured feature matrix against that exact insertion order and copies masks after the normal action returns. Reset/no-unit paths clear saved fields before returning, so earlier rows cannot leak into later decisions. Unexpected forwards, misalignment, empty masks and nonfinite rows fail the run.
- Final action comes from the returned action array, after all runtime rule processing, rather than `_prev_actions`. World actions are independently copied. `geo.MIRROR_DIR` is the same involution the runtime uses for movement; applying it to movement/stay recovers canonical actions. SAP remains action 5 while its original world offsets are retained. A late final action outside the saved network mask is retained and counted.
- `play_game(..., train=False)` calls `new_game(our_side)` before each game; the actual runtime updates team identity, resets both beliefs and episode state, and preserves model state. The wrapper remains attached to the same agent across those resets. Eval mode, disabled learning/autosave, no `update` calls, and model/target/optimizer/counter/replay-length/loss digests prevent unintended learning in the reviewed path.
- The fixed opponent schedule and both sides per seed match the spec. Production maps 865100–865129 assign the final five whole maps to diagnosis; no within-map split occurs. Technical plans retain both nonempty partitions.
- Teacher labels use the existing hash-validated 36-member V14 loader and identical raw-Q arithmetic mean, in batches on the captured student features. The manifest explicitly limits this to teacher Q values on those rows and makes no final-teacher-policy claim.
- Collector publication matches the strict current `student_action_distill.load_datasets` contract: schema 1, completed manifest/status, pinned teacher hash/member count, student hash, exact file hashes, contiguous integer game plan with both sides and consistent whole-seed split, and the specified array names/shapes/dtypes. The consumer accepts final actions outside the network mask, as required.
- The collector requires complete 303-step games, checks deadlines before acts and phases, labels only complete data, verifies serialized arrays, and rechecks pinned inputs/sources/protected artifacts before publication. Exceptions remove both pending/final NPZ and write failed receipts, so an incomplete collection is not exported as a completed dataset.
- Source/input/dependency/protected hashes, occupied/protected/aliased-output guards, actual strict 512-wide single-net checkpoint load and equality checks meet the task's bounded collection requirements.

## Code quality and evidence

The implementation is focused in the two assigned files, reuses established environment/opponent/teacher/output helpers, and restores the hook and original instance/class `act` arrangement through context cleanup on exceptions. The tests target the concrete CPU aliasing failure, stale state, real checkpoint compatibility, final-action authority, whole-map partition, bad rows and failed publication rather than merely mirroring the implementation.

Independently checked during this review:

- Both current protected raw weights have SHA256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`.
- `git diff --name-only -- agents lux/runner.py main.py` is empty; runtime agent and course runner have no tracked modifications.
- `git diff --check` completes with no output.

## Remaining integration verification

The root agent owns the actual-game observer equivalence check. This static review confirms the hook/state alignment against the real runtime source but does not claim gameplay equivalence from synthetic tests alone. Root also owns final cross-workspace protected-artifact receipts and the central Arbeitsstand update. No production games or training should be inferred from this review.
