### Task 1: Retention diagnostics

**Files:** Create `scripts/student_retention.py`, `tests/test_student_retention.py`.
**Interfaces:** CLI accepts `--datasets` (one or more collector dirs), repeated `--model NAME=PATH`, `--out` (new dir). Loads validated existing packages and checkpoint `q` with QNet inferred/checked config. Returns JSON per-role diagnostic metrics and provenance; one report can be used before and after training.
- [ ] Tests: malformed/mismatched masks fail; synthetic exact teacher has agreement 1/regret 0; excluded split only contributes; protected/occupied output rejected; finite independent model inference.
- [ ] Implement batched no-grad inference and metrics, model/data/source hashes. No model mutation.
- [ ] Run targeted tests, independent review and root verification; commit.
- [ ] Run five existing models once; report evidence/limits with no causal overclaim.

