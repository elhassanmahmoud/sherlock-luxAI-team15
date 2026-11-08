# Independent compact selection audit

**PASS — complete and internally consistent; nominee is `null`.**

Frozen source: `2146494ee12ce288b48ae69bde119198cf8316b9`. Independently checked all 39 jobs / 1560 rows against the complete predeclared role × opponent × seed × side matrix. No missing, duplicate, extra or excluded rows. Every game uses point-counting v2 and 303 steps. All 316 source hashes, Python executable, model/opponent/protected hashes, commands, plan/seed inputs, receipts, state and summary bindings agree. No new games, model loads or test suites were run.

Independent recomputation uses standard-library CSV parsing and fresh NumPy PCG64(0) integer-index resampling (5000 replicates), taking whole maps with both sides and all six panel opponents together. Results and all reported W/D/L, per-opponent counts, scores, deltas, intervals, checks and ranking agree with the production summary to 1e-12. All 1560 results have zero draws.

| Role | Panel W/L (240) | Panel Δ pp [95% CI] | Solution W/L (40) | Solution Δ pp [95% CI] | Direct W/L (40) | Direct score % [95% CI] | Selection |
|---|---:|---:|---:|---:|---:|---:|---|
| V14 | 185/55 | reference | 38/2 | reference | — | — | baseline |
| A39 | 202/38 | +7.083 [-1.250; +15.833] | 39/1 | +2.500 [+0.000; +7.500] | 18/22 | 45.0 [25.0; 65.0] | fails direct ≥50% |
| B39 | 193/47 | +3.333 [-3.333; +10.000] | 39/1 | +2.500 [+0.000; +7.500] | 14/26 | 35.0 [15.0; 55.0] | fails direct ≥50% |
| ALL42 | 205/35 | +8.333 [+1.250; +14.583] | 40/0 | +5.000 [+0.000; +15.000] | 18/22 | 45.0 [25.0; 65.1] | fails direct ≥50% |
| REPLACE36 | 202/38 | +7.083 [+0.833; +13.333] | 39/1 | +2.500 [+0.000; +7.500] | 28/12 | 70.0 [50.0; 90.0] | passed, diagnostic only |

Default: every role 40 wins / 0 draws / 0 losses; difference to V14 exactly zero. A39, B39 and ALL42 fail the predeclared direct-score selection gate (45%, 35%, 45%). REPLACE36 passes all six exploratory checks but was explicitly non-nominable before results; it cannot replace a failed candidate. Thus no nominee and no confirmation are authorized by these data. Seven confirmation score gates plus three safeguards remain unchanged and were not applied as a substitute selection procedure.

Caveats:
- Selection is exploratory: four candidate comparisons and unadjusted 95% intervals do not establish general strength or control selection multiplicity.
- Only 20 independent maps per panel/direct block; sides and opponents remain grouped within maps. Interval precision is low and near-boundary estimates are fragile.
- Observed 40/40 on Solution_92 for ALL42 and default 40/40 for every role are finite samples, not universal 100% win guarantees.
- REPLACE36 was predeclared diagnostic/non-nominable; passing its exploratory checks cannot authorize confirmation or promotion.
- No confirmation games were requested or executed by this audit; no candidate substitution, source changes, model loads, games or test suites.
- Receipt and file identities validate recorded execution bindings; no engine replay was newly run, so point totals are checked for numeric and result consistency rather than regenerated.

Detailed per-opponent W/D/L, full verified input hashes, job receipt/CSV digests and numeric calculations: `independent_audit.json`.
