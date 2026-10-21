### Spec Compliance

- ✅ Spec compliant for Task 3 at `e3f8b2b..a5ce6d8`. The six-file method interface fixes starts 47/48/49, control/early, 60 declared maps, both sides and both opponents; strict full-schema/key validation precedes aggregation (`scripts/early_curriculum_analysis.py:48`, `:119`).
- ✅ Method gates use integer half-win totals and cross-multiplication for mean Sol ≥3 pp, at least two positive pairs, and mean Default ≥−2 pp. No confidence-interval condition is added to the method decision (`scripts/early_curriculum_analysis.py:143`; regression evidence in `tests/test_early_curriculum_analysis.py:209`).
- ✅ Candidate gates require positive exact Sol difference and strictly positive lower interval, plus the exact Default tolerance; direct comparison uses absolute results from the prescribed 200 maps/400 games and lower interval strictly above 0.5 (`scripts/early_curriculum_analysis.py:159`, `:180`).
- ⚠️ Cannot verify from this diff: Task 4 must build the six input paths from audited final-arm state, bind development/fresh candidate/reference identities and prescribed map ranges, and pass `expected_opponent` equal to the exact frozen V3 self-label to `direct_gate`. The generic comparison helper intentionally accepts caller-declared map sets; `candidate_gate` consumes a summary rather than authenticating original CSV provenance; `direct_gate` permits an omitted expected label (`scripts/early_curriculum_analysis.py:119`, `:146`, `:159`, `:180`). These are explicit cross-task integration obligations, not defects in the scoped implementation.
- ⚠️ Cannot verify from this diff: the eventual Task 4 caller must bind raw direct rows to the audited input CSV hash, and ensure diagnostics/intermediates cannot enter candidate selection. The analysis interface rejects extra method arms but cannot establish the caller's checkpoint provenance (`scripts/early_curriculum_analysis.py:119`, `:180`).

### Strengths

- Whole-card bootstrap aggregates the two sides before drawing and adds the three fixed-start card totals before computing method intervals. Units are consistently fractions; denominators are 4 half-win units per map/start, with 5,000 seed-0 draws and 2.5/97.5 percentiles (`scripts/early_curriculum_analysis.py:91`, `:99`, `:106`, `:139`). Complementary-start and opposed-side counterexamples directly test the correlations that would be lost by row or start resampling (`tests/test_early_curriculum_analysis.py:136`, `:162`, `:192`).
- Missing rows, duplicate keys, unexpected maps/opponents, invalid result consistency and nonfinite numeric values fail before any aggregation. Six distinct resolved physical files are required, and hashes bracket CSV parsing (`scripts/early_curriculum_analysis.py:48`, `:82`, `:119`; tests at `tests/test_early_curriculum_analysis.py:71`, `:119`).
- The uncertainty text explicitly limits interpretation to map uncertainty for three known fixed starts. Hashes, per-start estimates, equal-weight mean estimates, intervals and exact totals are returned in serializable reports (`scripts/early_curriculum_analysis.py:34`, `:106`, `:119`).

### Issues

#### Critical (Must Fix)

- None found.

#### Important (Should Fix)

- None found.

#### Minor (Nice to Have)

- None found.

### Checks and Scope

- Read the packaged diff once; the first tool result elided part of `validate_keys`, so retrieved only that omitted package section. Used package symbol positions for line references; did not reread changed source files or regenerate Git diffs.
- Named external risk: imported CSV/schema helpers might accept duplicate headers, malformed row widths, or nonfinite data before binding hashes. Checked only `GAME_FIELDS`, `require`, `digest`, and `read_rows` in `scripts/early_curriculum_study.py:37`, `:50`, `:55`, `:221`; they supply the expected schema, byte hashing, and strict CSV shape checks.
- Read the brief-named `scripts/compare_report.py:59`. Its common-key merge can silently exclude cards, but this implementation uses complete validated integer map arrays instead, so that failure mode is absent. The custom integer comparison preserves the stated statistic while enabling exact gate units.
- Inspected the implementer report's final focused evidence: 54 tests passed in 0.54s, with a clean staged whitespace check. The initial RED evidence is accurately described as missing-module/setup failures. No suite rerun or focused counterexample was needed because no unresolved behavioral risk remained after inspection.
- No model jobs, repository edits, Git mutations or subagents were used.

### Assessment

**Task quality:** Approved.

**Reasoning:** Exact arithmetic, complete-key validation and whole-card resampling implement the statistical contract coherently, with targeted synthetic counterexamples. Root should carry the explicit provenance, map-range and frozen-opponent bindings into Task 4 and resolve those integration checks before declaring the full workflow complete.
