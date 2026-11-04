# Reward wrapper integration fix round 2

Completed and frozen 2026-11-04, 14:21 Europe/Berlin. Only `scripts/student_reward_train.py` and `tests/test_student_reward_train.py` changed. No other source/artifact files, commits, subagents or RL games.

## Root cause and correction

The actual S30 export has 72 serialized configuration keys. Current `AgentConfig` has 167 effective keys; omitted legacy keys are valid defaults. The producer intentionally preserves the sparse teacher configuration. `_student` incorrectly required equality between that sparse serialization and the complete normalized configuration, rejecting valid inputs before preparation.

Minimal correction: `_student` validates required contract values against `AgentConfig(**cp['cfg']).to_dict()` and returns a shallow checkpoint mapping with that normalized effective config. It never writes the source. Existing explicit nondefault fields win over defaults. All other checkpoint/provenance, architecture, finite-state and no-optimizer/replay restrictions remain. `prepare`, `check_prepared`, saved role configs and live learners now consistently consume the same complete effective configuration.

## Portable regression and tests

Added a test using the actual tiny distillation producer with sparse legacy teacher configuration and explicit nondefault `w_opp_points=1.25`, `w_sap_hit=.45`, `cand_rescue=True`, `frozen=True`. It checks defaults are completed, true overrides preserved, only the assigned SAP weight differs, both prepared init checkpoints pass checks and actual fresh `Learners`/`prove_initial` agree with full configs, and the student bytes/config remain unchanged.

The test failed before the correction with `ValueError: Student config violates fixed learner contract` (1failed3.14s; `/tmp/student-reward-fix2-red.log`). Afterward the full covering file passed:

```
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest tests/test_student_reward_train.py -q
```

**21 passed in8.28s**, exit0, one CPU thread. Log: `/tmp/student-reward-fix2-tests.log`.

## Actual S30 read-only admission check

Used actual immutable `experiments/runs/20261104_student512_e30/weights/agent.pth` with `_student`, then prepared under `TemporaryDirectory` and checked both arms. No games ran. Complete evidence: `/tmp/sherlock-student-20261104/reward_fix2_actual_check.json`.

- Raw config72keys normalized to167effective keys; all72explicit fields preserved.
- Both init checkpoints have identical q/target tensor SHA `4b94c376e8e290e151d32397f4024a6c47aceab59d7e7751d8d6322af13b9a7e`.
- Both lack optimizer/replay. Full configs differ only in `w_sap_hit`: control0.3, sap0=0.
- S3 hash before/after unchanged: `0b465006b5eb6ec3dc9e2bdff19aec29eae44f557573e76e07e3af1e35a52a9b`.
- S30 hash before/after unchanged: `3104596d5527d644d0c3f2cfc98189ec166e6e8e4a1f0ae9a4166f27a934b11b`.

## Frozen source SHA256

- `scripts/student_reward_train.py`: `b91a1149422273800c01cf7d65750d933c36dc8d7809e91ac8e264d3071c0213`
- `tests/test_student_reward_train.py`: `d2112d19fcb2e4b504db37c9de5fec1676226818445be2c4d7f7f7c361f25ada`

No test or admission-check processes remain running. Root retains source-freeze/commit, runtime/resource admission and production-launch ownership.
