# Independent REPLACE36 validation audit

**Data/statistics audit PASS. REPLACE36 fails 6 of 10 adoption gates; V14 remains.**

All 15 jobs / 3200 actual game rows are complete, with exact predeclared maps, both sides and opponents, no duplicates, exclusions or draws. Panel/default: 100 maps (2000000–2000099), two roles × seven opponents × two sides = 2800 games. Direct: 200 separate maps (2100000–2100199) × two sides = 400 games. Every game has 303 steps, point-counting v2 and consistent numeric outcomes.

Frozen HEAD `f9e1195bb65b6587206685971b3ce11e604666db`, 317 source hashes, Python executable, 129 bound inputs, all model/opponent/protected hashes, commands, receipts and CSV digests verified. All 85 archived discovery files remain byte-identical, including the closed compact selection with `nominee:null` and diagnostic REPLACE36 non-nominable. All recorded owned PIDs are absent; wake cleanup is recorded. V14 weights and ZIP remain unchanged. No models, games, tests or replays were run by this audit.

Independent standard-library CSV parsing and NumPy PCG64(0) integer-index resampling reproduce all 262 compared values, including W/D/L, scores, deltas, intervals and all ten gates, within 1e-12 of `summary.json`. Each of 5000 replicates samples whole maps; paired roles, both sides and all six panel opponents stay together. Intervals are unadjusted 95% percentile intervals. Production statistics were not imported or invoked.

| Comparison | REPLACE36 W/D/L | V14 W/D/L | Difference pp [95% interval] |
|---|---:|---:|---:|
| Six-opponent panel | 930/0/270 | 962/0/238 | −2.667 [−6.252; +0.917] |
| Solution_92 | 193/0/7 | 194/0/6 | −0.500 [−3.500; +3.000] |
| sol92_sq | 169/0/31 | 171/0/29 | −1.000 [−5.500; +3.000] |
| V3 | 166/0/34 | 190/0/10 | −12.000 [−21.000; −3.000] |
| V7 | 168/0/32 | 156/0/44 | +6.000 [−4.000; +16.000] |
| V10 | 154/0/46 | 150/0/50 | +2.000 [−9.000; +13.000] |
| V13 | 80/0/120 | 101/0/99 | −10.500 [−19.500; −1.000] |
| default | 200/0/0 | 200/0/0 | 0.000 [0.000; 0.000] |

Direct REPLACE36 versus V14: **206/0/194**, score **51.5% [44.5%; 58.5%]**.

| Predeclared gate | Observed | Outcome |
|---|---:|---|
| Panel difference ≥ +1 pp | −2.667 pp | FAIL |
| Panel interval lower bound > 0 | −6.252 pp | FAIL |
| Solution difference ≥ −0.5 pp | −0.5 pp | PASS |
| Solution interval lower bound > −2.5 pp | −3.5 pp | FAIL |
| default score ≥ 99% | 100% | PASS |
| default difference ≥ −1 pp | 0 pp | PASS |
| Direct interval lower bound > 50% | 44.5% | FAIL |
| Solution score ≥ V14 | 96.5% < 97% | FAIL |
| Strict Solution wins ≥ V14 | 193 < 194 | FAIL |
| Strict default wins ≥ 198/200 | 200/200 | PASS |

This is the separate prospective, outcome-motivated validation of one exact 36-member artifact; it does not retroactively nominate the earlier diagnostic role. Only fresh data enter these estimates. There is no confirmed overall strength gain, and the panel interval also does not establish a general deterioration. The predeclared acceptance conditions fail, so no promotion, successor, top-up or automatic further study is supported.

Limits: 100 independent panel maps and 200 direct maps on a fixed local opponent panel provide limited precision. Unadjusted intervals do not control project-wide repeated exploration or multiple comparisons. Negative per-opponent intervals are descriptive, not multiplicity-adjusted general claims. Exact member replacement does not isolate a causal curriculum or ensemble-size effect. Observed default 200/200 is not a universal 100% guarantee. CSV rows carry no source-commit column; source association comes from each recorded CSV hash and execution receipt, and outcomes were not independently replayed.

Portability: raw-CSV statistics can be independently reproduced on another host with Python/NumPy. Full lifecycle and file-identity validation is bound to this original checkout, frozen HEAD, absolute receipt paths, Python executable and original process identities. Preserve archived provenance instead of rewriting it to match another host; later documentation commits do not change the recorded run. The audit implementation is `/tmp/replacement_independent_audit.py` (root may archive it separately); exact invocation and its SHA-256 are recorded in `independent_audit.json`. It creates the JSON exclusively, so this completed audit must not be overwritten by a rerun.

Detailed calculations, hashes and evidence: `independent_audit.json`.
