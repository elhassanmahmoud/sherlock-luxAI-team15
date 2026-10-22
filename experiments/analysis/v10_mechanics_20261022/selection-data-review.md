# Independent V10 selection-data review

**Verdict: approved for the already nominated recovery-only default guard. No blocking errors found. This is not confirmation of improved strength or approval to promote.**

Read-only audit completed 22 October 2026, 12:46 UTC, worktree HEAD `de2e95d451a22643a3f7351636d3348f7770a1aa`. Used only standard-library data/file operations and NumPy; no repository edits, model/engine imports, tests, or games.

## Independent results

Each of the four Solution CSVs contains exactly 400 unique games: seeds 610100–610299 × both sides × `solution92`, with no missing or extra keys. All 1,600 rows have the expected 24-field schema, finite values, 303 steps, point-counting version 2, valid fractions and coherent match outcomes, game results, game-win flags and point-win flags. No draws occurred.

| Variant | W/D/L | Score | Exact Δ half-result units / 800 | Δ | Paired 95% interval |
|---|---|---:|---:|---:|---|
| baseline | 363/0/37 | 90.75% | — | — | — |
| recovery | 367/0/33 | 91.75% | +8/800 | +1.00 pp | [−0.75; +3.00] pp |
| drift | 359/0/41 | 89.75% | −8/800 | −1.00 pp | [−2.50; +0.25] pp |
| combined | 362/0/38 | 90.50% | −2/800 | −0.25 pp | [−2.50; +2.00] pp |

Bootstrap was recomputed independently, without importing the repository analysis code: sum both sides' half-result units within each map, form paired map differences, draw 200 whole maps with replacement 5,000 times using `default_rng(0)`, take percentiles 2.5/97.5. All reported totals, intervals, map counts, exclusions and CSV hashes match `selection_summary.json` exactly.

The committed predeclaration requires at least +1 pp and maximal Solution improvement, with ties combined > recovery > drift. Recovery is the unique eligible nominee. Its exact +8/800 meets the inclusive threshold; floating subtraction of displayed percentages must not turn this boundary pass into a failure. The interval includes zero, as permitted at this selection stage.

## Binding and freeze checks

- `selection_jobs.json`, `selection_state.json`, recorded commands, all four zero exit codes and all four output hashes agree. The selection phase is recorded complete before the default phase began.
- `selection_default_jobs.json` and its state bind exactly **baseline then recovery**, `--first 110100`, `--n 200`, `--workers 2`, `--opponents default`, and separate new output files. Both use the same absolute frozen V10 checkpoint path.
- Baseline flags are false/false. Recovery flags are `sap_overkill_recovery=true`, `nebula_infer_drift_safe=false`. Thus the selected arm is energy recovery only, not combined.
- `source_freeze.json` matches current HEAD, interpreter path/resolved executable/SHA, **all 128 frozen source/plan/engine/environment files**, and the independently reconstructed source-file inventory. No file was added to or removed from that inventory.
- All four frozen/protected checkpoint files match the required V10 SHA `03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67`.
- The current predeclaration equals its committed contents and was committed before selection started. The frozen engine source still specifies three matches of 100 steps; each complete CSV row records 303 steps.

Evidence identities:

| Artifact | SHA-256 |
|---|---|
| source_freeze.json | `482b1908cde0f5d2969e54d960c33b832f8ead4836efa14ff1ccb5e70a356907` |
| selection_summary.json | `ec1f1c29357469b2556fd0eecdc3a11385ee8d1e0f2707cbff523eb87224c991` |
| selection_default_jobs.json | `fd2579e44ba4b8a6422aa18897591ef3264dae35d5d9062e086e410052a4815a` |

## Remaining decision boundary

The default guard was running during this audit; its outcomes were not examined. Under the **committed** plan, recovery must reach default score ≥99% **and** Δ≥−1 pp. At 400 games, these are respectively at least 792/800 half-result units and a candidate-minus-baseline difference of at least −8 units. If either condition fails, stop with no fallback nomination. Passing that guard only permits the frozen 800-map confirmation; all later gates and stronger-opponent guard remain outstanding.

Machine-readable independent calculations and full CSV hashes: `/tmp/sherlock-v10-fixes-20261022/selection-data-review.json`. Reproducer: `/tmp/sherlock-v10-fixes-20261022/selection_data_audit.py`.
