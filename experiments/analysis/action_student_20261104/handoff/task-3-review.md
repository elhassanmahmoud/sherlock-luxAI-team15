# Task 3 independent review

Spec compliance: **PASS**.
Code quality: **APPROVED**. No actionable findings.

Reviewed the full supplied two-file diff, task brief, implementer report and the
current functions that consume the seed. Read the relevant unchanged finetune,
Learners and initial-learning proof implementations to trace seed propagation.

- API and prepare CLI default to 29. The strict validator accepts Python integer
  seeds 0..29 and excludes booleans/floats, before preparation writes begin.
- The prepared top-level seed is cross-checked against both arm entries and
  both init manifests, including strict type checks that avoid 27.0 == 27.
  The runtime closes over the checked manifest seed and passes it to Learners
  and finetune; opponent and map schedules use that same seed. No remaining
  runtime use of RUN_SEED overrides a selected start.
- Starts 27/28 preserve identical control/SAP0 schedules within each pair and
  distinct map/opponent schedules between starts. Only the intended SAP config
  difference remains; default-29 map/opponent formulas retain prior behavior.
- Fixed 40/160/32 counts, offset 3000, 24000 updates, 120600 environment steps,
  checkpoint contract, fresh optimizer/replay checks, validation isolation,
  final-only selection and existing receipt/action/learning proofs are intact.
  Receipt and audit seeds are additionally checked against the manifest.
- Seedless legacy preparation is explicitly rejected before mutation. No
  migration or historical rewrite was introduced. The supplied diff contains
  no runtime-agent, default-config or submission-weight change.
- Added tests address the actual seed admission and propagation paths, malformed
  and inconsistent seeds, immutable legacy refusal, default parity, and
  synthetic real-finetune orchestration for all three relevant starts. Test
  comments correctly avoid claiming real game or gradient results.

Actual reviewer verification: static inspection above and
`git diff --check -- scripts/student_reward_train.py tests/test_student_reward_train.py`
passed. I did not repeat the implementer-reported 48 tests or run any full suite,
training job, production game or historical-data mutation. No concrete coverage
gap requiring another test was identified. Shared documentation remains Root's
integration responsibility.
