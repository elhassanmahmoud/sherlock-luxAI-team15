# Independent diagnostic auditor prepared

Standalone `/tmp/sherlock-student-20261104/audit_diagnostic.py` uses only stdlib and NumPy; no repository/game/model imports or repository edits. Execution against actual data is gated by `--data-ready`. No actual diagnostic CSVs were read; awaiting the root's explicit data-ready signal.

Reviewed current `scripts/experiment.py::GAME_FIELDS`, `scripts/par_eval.py`, `scripts/common.py::play_game`, `scripts/scoring.py` and amended five-role study spec. Exact current 24-column schema is required, with no missing/duplicate/unexpected columns or empty cells. The auditor validates five ×120 exact role-qualified keys, covering all20 reserved cards864000–864019, both sides, and exactly Solution/default/V13. Duplicate, unexpected or missing outcomes abort before statistics. Every numeric cell must be finite; counts must be integral/nonnegative; all games must have303steps and v2. Result0/.5/1 is cross-checked against both recorded match-win counts; game_win and point_win are cross-checked too. Impossible >3 total match wins are rejected. CSV hashes are checked before/after reading and after statistics.

Outputs include W–D–L, draw-half score and average point totals per role/opponent and pooled panel. Every role is compared with V14 (V14 self-reference is zero). The primary reward comparison is SAP0_30 minus CONTROL30. Each unadjusted95% percentile interval uses5000 NumPy PCG64 resamples with seed0, resampling20whole cards with replacement. Both sides are kept together; pooled cards also keep all three opponents together. The identical resample matrix is reused across comparisons. Per-card deltas are retained in JSON for inspection. No ranking, promotion, performance-pass or statistical-significance flag is produced.

Synthetic validation:23cases passed in a fabricated temporary directory, including independent literal whole-card bootstrap enumeration, pooled opponent correlation, per-opponent side pairing, deterministic seed, WDL/half-draw arithmetic, self-reference, missing/duplicate keys, wrong card/side/opponent, contradictory outcomes, malformed schema, nonfinite/empty metrics, incomplete steps and old scoring. Evidence: `/tmp/sherlock-student-20261104/diagnostic_auditor_selftest.json`. No games/models were run. The script refuses actual-data execution without the explicit gate and refuses occupied report outputs.

Once the root declares all five final CSVs ready, run:

```sh
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B \
  /tmp/sherlock-student-20261104/audit_diagnostic.py --data-ready
```

Default outputs: `/tmp/sherlock-student-20261104/diagnostic_review.{json,md}`. Invalid/incomplete input exits2 with an integrity error and no outcome report. The document labels the20-card, one-training-seed result exploratory, reports multiple unadjusted comparisons, and explicitly separates card uncertainty from training-seed uncertainty. CSV checks cannot reconstruct engine scoring independently; this limit is stated. Any perfect observed score remains a sample description, not a population guarantee.
