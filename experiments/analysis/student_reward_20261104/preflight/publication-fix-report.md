# Final publication-readiness fix

Completed/frozen 2026-11-04 14:39 Europe/Berlin after root explicitly lifted the source freeze following the independent94/94 RL audit. Only the two authorized files changed. No production games, models, original artifacts/receipts, reward/config/step/epoch settings, subagents or commits were changed/launched.

## Cause and minimal correction

A worker exposed `final_receipt.json` while disk `status.json` still said running. Another worker could see the marker immediately and reject that valid arm during `compare_prefill`. Unique staging filenames did not establish readiness across the receipt and status files.

The correction moves the existing final `persist()` before the final receipt's atomic `_write`. The visible receipt is now the readiness commit point: all completed learning evidence and done-status already exist. The preceding persisted audit and its receipt digest are unchanged; persistence writes the same audit object. Existing exception handling still removes the receipt and marks an arm incomplete if publication or later verification fails. No training/evaluation behavior changed.

## Deterministic regression

Enhanced the existing real-finetune orchestration test, with synthetic episodes, using an orchestrated `_write` hook. Immediately after the real atomic final-receipt write returns, and before the publisher can execute another statement, the hook calls the real peer `validate_receipt` against that run. It does this for both arms and asserts both observations are done. This tests the actual publication/readiness boundary, including exact evidence hashes and full proof validation; it uses no sleep or polling.

Observed red result before the fix: `ValueError: Incomplete arm` from peer validation because status was still running. **1failed4.48s**, `/tmp/student-reward-publication-red.log`.

Covering green command, existing primary venv, one CPU thread:

```
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest tests/test_student_reward_train.py -q
```

**21 passed in7.95s**, exit0. Log `/tmp/student-reward-publication-tests.log`. Both synthetic arms completed the full fixed orchestration, final peer observations passed, paired proof passed, and existing incomplete/failure/atomic-writer tests remained green. These synthetic episodes do not constitute a rerun of production arms or fresh games.

## Changed files and frozen SHA256

- `scripts/student_reward_train.py`: `011dd1b5612755fc5117ec9d3fbb8e32de86365624d4f948e57174c3d013e5f5`
- `tests/test_student_reward_train.py`: `a7445354cb3f43fd03d0d09e591871f1ea8d002b0be014e3b49daa2d1baa72b6`

Diff is14insertions/1deletion: source publication reorder plus explanation; test peer-observation hook and assertions. No processes remain running.

## Limits and historical artifacts

The original completed RL arms remain bound to their recorded source hashes and their accepted independent audit. Their receipts were neither rewritten nor revalidated against altered source pins. This correction applies to subsequent wrapper use; root owns final review, commit and next phase admission. Atomic publication establishes reader readiness, not a new crash-durability/fsync guarantee.
