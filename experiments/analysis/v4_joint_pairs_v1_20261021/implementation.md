# Task 1 implementation report

Status: DONE. Commit `b73523f` — `Add default-off pair coordination for productive movement`.
Branch: `improvement/v4-joint-20261021`. No push.

## Implemented

- Added `coordinate_moves(ctx, ids, q, masks, base_actions)` as a 121-line, observation-only canonical movement helper. Baseline plus the two highest legal finite movement proposals, 15% normalized all-action span bound, deterministic sorted pairs/ties, at most one accepted pair per unit, conservative current/destination enemy guard, and strict global distinct nominal point occupancy improvement.
- Fixed SAP/nonfinite/negative-energy/illegal-baseline units stay outside the search but contribute productive final destinations when valid. Existing SAP rows remain untouched; movement occupancy requires enough known move energy.
- Added `joint_moves=False`, with evaluation-only integration after all existing action overrides. Final world action classes become canonical for the helper; changes return through existing mirror functions and update `_prev_actions`.
- Added only `joint_calls` and `joint_changed_units` episode counters. Existing CSV field lists and evaluation code are unchanged.
- Root's explicit numeric ruling: malformed/nonfinite visible enemy positions or energies return unchanged fallback `{}`; finite negative-energy enemies are ignored. Narrow failing regressions preceded this fallback implementation. No broad exception handling.

Files changed and committed:

- `agents/sherlock/joint_actions.py`
- `agents/sherlock/config.py`
- `agents/sherlock/main.py`
- `tests/test_joint_actions.py`

This report is intentionally outside the code commit for root-owned integration/reporting.

## TDD evidence

All commands used `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python` from this worktree, with `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`.

Initial RED:

```text
python -m pytest -q tests/test_joint_actions.py -k 'competing_units or act_applies'
3 failed, 22 deselected in 3.83s
```

The helper did not yet exist (`ModuleNotFoundError`). Both real `Agent_x.act` tests failed on behavior: player 0 produced RIGHT instead of STAY; mirrored player 1 produced UP instead of STAY. Expected canonical joint action was STAY in both cases. These demonstrated the intended behavior was missing before implementation.

Initial GREEN after helper/config/integration:

```text
python -m pytest -q tests/test_joint_actions.py
25 passed in 2.98s
```

Numeric boundary RED before conservative malformed-threat fallback:

```text
python -m pytest -q tests/test_joint_actions.py
2 failed, 35 passed in 2.87s
```

NaN/Inf enemy energy wrongly allowed `{0: 0}` instead of unchanged `{}`.

```text
python -m pytest -q tests/test_joint_actions.py -k 'invalid_visible_enemy_position'
3 failed, 43 deselected in 2.26s
```

NaN, Inf and out-of-bounds visible enemy coordinates likewise wrongly allowed a new movement. Root agreed the conservative unchanged fallback before it was added.

Focused GREEN after fallback:

```text
python -m pytest -q tests/test_joint_actions.py tests/test_mask_and_act.py tests/test_rules_1910.py
82 passed in 2.68s
```

Final focused GREEN (two final global/normalized-regret cases added):

```text
python -m pytest -q tests/test_joint_actions.py
48 passed in 2.90s
```

Covered real occupancy gain and simultaneous handoff, global fixed outsider and earlier accepted destinations, no strict gain, useful combat stacking, both threat guard endpoints, SAP/nonfinite/negative-energy fixed units, masks/top-two proposal restriction, legal all-action spans, normalized regret/scale invariance, rule-overridden baseline inclusion, stable action ties/fewer changes, nonmutation/UID row order, empty/no-points cases, accepted/rejected pair reservation, mirrored world actions, SAP row preservation, final rule overrides and disabled/training behavior.

## Full verification

Exactly one full suite after implementation, adding `VECLIB_MAXIMUM_THREADS=1`:

```text
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest -q
457 passed, 14 subtests passed in 77.68s (0:01:17)
```

Exit 0, no warnings/failures. The only later edit removed a misleading test comment; no executable statements changed. `git diff --check` passed before commit.

Synthetic timing sanity only: 16 units clustered around shared point destinations, 20 warmups then 500 helper calls. Median **1.8365 ms**, p95 **1.9107 ms**, max **2.2096 ms**. This ran concurrently with the full test suite and is not the representative real-act admission measurement required in task 2.

## Self-review and concerns

Read the complete helper and staged integration/config diff against every task-1 rule. No outstanding correctness concern found. The helper objective remains deliberately nominal; it cannot predict enemy/future actions, Sap, field energy, hidden enemies, void or collision resolution. No learned tensor, feature, reward, training path, engine/course runner, weights, CSV schema, historical data or evaluation game changed. No training or evaluation games were started; only the authorized tests and a synthetic helper timing script ran.

Independent review, representative act timing, checkpoint identity checks and games remain root's later tasks.
