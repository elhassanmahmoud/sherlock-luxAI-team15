# A2 teacher-anchor data audit preparation

Ready for the explicit data-ready signal. No real result CSVs read, no games/training started, no repository source files written.

Auditor: `/tmp/sherlock-a2-anchor-20261104/audit_results.py`

SHA-256: `0ef14611b23bb8c14eb86ea7bfa44aae3cd2dc10e27e98c1f96826d1030a2d04`

Completed verification: 73 synthetic cases passed; CLI without `--data-ready` refuses to read results (exit 2). Existing project environment, NumPy 2.5.4; no Torch or repository imports.

The auditor requires exactly eleven CSVs: six roles V14/A2/CONTROL25/CONTROL26/ANCHOR25/ANCHOR26 under `panel/`, five non-V14 roles under `direct/`. Exact card/opponent/side key sets give 720 panel plus 200 direct games. Every field must be present and finite, games must have 303 steps and point-counting version 2; outcome, strict-win and point-outcome fields are cross-checked. Source hashes are checked during each read and after the audit. Invalid/incomplete inputs produce no outcome report.

Whole-card bootstrap: NumPy PCG64 seed 0, 5,000 samples of 20 whole cards, percentile 95% intervals with linear quantiles. Both sides and all three panel opponents stay together. Comparisons include ANCHOR minus paired CONTROL separately for seeds 25/26, all roles against A2/V14, all opponent strata; direct strict wins and draw-half scores have separate intervals and V14 complements.

The later-confirmation screen uses panel/Solution draw-half scores >= A2, strictly positive paired-control panel difference, and at least 24/40 strict direct wins. Only ANCHOR roles enter; ties rank panel, Solution, smaller training seed. Diagnosis cannot qualify a release; there is no fallback after failed confirmation.

Synthetic checks include all 14 paired comparisons × four strata against a separate whole-block enumerator, direct draws and all four direct intervals, distinction from incorrect sidewise bootstrap, selection boundaries/ranking/failure gates, missing/duplicate keys, wrong role/card/side/opponent, malformed schema/cells, nonfinite/invalid/negative values, inconsistent outcomes, steps/scoring, and changed-source hash rejection.

Run after root confirms completeness:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B \
/tmp/sherlock-a2-anchor-20261104/audit_results.py --data-ready \
--directory /Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/a2_anchor_20261104/diagnostic \
--out-prefix /tmp/sherlock-a2-anchor-20261104/diagnostic_review
```

The output prefix must be unused; outputs are JSON and Markdown. Findings about actual results, training integrity, source/model freeze and seed freshness remain pending and require their corresponding evidence.
