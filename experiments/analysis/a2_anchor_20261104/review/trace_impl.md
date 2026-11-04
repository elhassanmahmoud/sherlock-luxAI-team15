# Task 2 — observation-only loss traces

Implemented only `scripts/student_failure_trace.py` and `tests/test_student_failure_trace.py`; no commits, production-agent edits, weights, historical artifacts, or planned trace games. Parent owns final integration/workstand.

## Behavior

- CLI: `--model PATH --opponent solution92|self [--opponent-path PATH] --seed N --side player_0|player_1 --out NEW_DIRECTORY --deadline-utc ISO_WITH_OFFSET`.
- Exactly two fresh executions per successful invocation: ordinary, then instrumented. Both delegate to existing `scripts.common.play_game`; evaluated Agent_x has seed 0 as in historical par_eval, eval, frozen false, no autosave/no learning. Existing self-opponent constructor/RNG convention retained.
- Instance-local hooks clone inputs and every member's raw output before in-place CPU numpy masks. Aggregate uses the same ordered `torch.stack(...).mean(0)` as Agent_x. No extra act, belief.observe, `_decide`, context building, feature building, or forward is called by tracing.
- Decision JSONL retains pre-act world observation, exact current canonical context (excluding live belief object), features, masks, raw aggregate Q, masked network preference, actual complete world/canonical output, targets, known relic/point coordinates, first discovery times, and per-match counters. Reset/no-unit steps retain no ghost unit/context rows. Rule identity is deliberately not inferred from a preference/action discrepancy.
- Environment wrapper delegates reset/step unmodified and records both players' complete action arrays. Terminal match points use existing version-2 scorer after step; external-only terminal points are explicitly labeled and never passed to act. Three match endpoints and first-positive-score timestamps retained separately.
- Success requires literal equality of every action component, per-step digests, full ordered game digest, every final play_game metric except runtime, and all match metrics. Requires303 observed original acts and303 steps/3 matches. NaN metrics normalized to JSON null before equality. Checkpoint/source/protected hashes and model/optimizer/replay learning-state digest must stay unchanged. Failure preserves evidence with failed status, removes all hooks/restores instance act, and closes env.
- Outputs: `plain.jsonl`, `observed.jsonl`, per-run summaries, and `summary.json` with hashes/equality checks. Output paths use existing guarded reservation and must be new.

## Verification actually performed

Interpreter: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python`; OMP/MKL threads1 and torch threads1.

1. Seven tests written first; initial red run: **7 failed**, missing tracer assertion. Implemented and green: **7 passed**.
2. Added paired failure/seed regression; red exposed evaluated seed866000 instead of historical seed0. Corrected. Added actual Agent_x synthetic-observation checks on both sides, using real belief/context/features/networks and no environment.
3. Final bounded verification:

   `python -m pytest -q tests/test_student_failure_trace.py tests/test_student_collect.py tests/test_mask_and_act.py tests/test_point_counting.py -k 'not match_end_points_against_engine'`

   **56 passed, 6 deselected in 2.39s**, exit0. Includes all10 trace tests. Trace tests cover mirrored movement/SAP, ensemble copies/mean, no second belief/context, reset ghosts/match reset, hook restoration, deadlines, full opponent-action digest, unequal-action pair rejection.
4. CLI `--help` exit0; `git diff --check` exit0. Full project suite was not run because scope calls for bounded checks and explicitly withholds live game approval.

## Unintended engine regression run — separately account, not study data

I mistakenly included `tests/test_point_counting.py` before inspecting its engine fixture. Once recognized, stopped pytest PID76747 with SIGINT. This was contrary to the task's no-live-games-before-review instruction. No planned known-case trace invocation or fresh seed was started. The tests use V14/default, known seed900011, one process/thread. They do not write model files or experiment results.

Preserved exact command:

`OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest -q tests/test_student_failure_trace.py tests/test_student_collect.py tests/test_point_counting.py tests/test_mask_and_act.py`

Preserved terminal output:

```text
..........................................
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! KeyboardInterrupt !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/lib/python3.13/site-packages/numpy/_core/_methods.py:55: KeyboardInterrupt
(to show a full traceback on KeyboardInterrupt use --full-trace)
42 passed in 26.08s
```

37 preceding passes were10 trace +27 collector tests; collection order confirmed read-only afterward. Five completed engine test nodes:

- `tests/test_point_counting.py::test_match_end_points_against_engine[game-player_0]`
- `tests/test_point_counting.py::test_match_end_points_against_engine[game-player_1]`
- `tests/test_point_counting.py::test_match_end_points_against_engine[losses-player_0]`
- `tests/test_point_counting.py::test_match_end_points_against_engine[losses-player_1]`
- `tests/test_point_counting.py::test_match_end_points_against_engine[timing-player_0]`

Interrupted node: `tests/test_point_counting.py::test_match_end_points_against_engine[timing-player_1]`. Its partial step count was not logged and is unknown; it is not a completed game.

From fixture/consumer code: each passed node completes one three-match episode (303 ordinary engine steps), and its audited_step performs three additional counterfactual `jax_env.step` terminal probes with extended match length. Thus **five complete episodes =1515 ordinary steps +15 independent terminal probes**, plus an uncounted partial sixth episode/probes. These are technical regressions only; do not add them to the planned24 traced/plain executions or920 diagnostic games. Parent notified immediately.

## Remaining

Parent review, prescribed known-case24 executions, actual equality acceptance, and trace interpretation remain pending. No performance or causal conclusion is asserted by this implementation report.
