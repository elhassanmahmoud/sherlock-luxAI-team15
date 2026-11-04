# Exploratory action-student diagnostic

Integrity: all 1,400 planned games complete and unique (1,080 panel + 320 direct), finite, 303 steps, scoring v2; recorded outcomes agree with win counts.

Scores count draws as half. Intervals are unadjusted 95% whole-card percentile bootstrap intervals, 5,000 draws, seed 0. Both sides and all panel opponents stay grouped.

| Role | Panel W–D–L | Panel score | Difference vs V14 | 95% interval | Solution W–D–L |
|---|---:|---:|---:|---:|---:|
| V14 | 98–0–22 | 81.67% | +0.00 pp | [+0.00, +0.00] pp | 38–0–2 |
| S30 | 58–0–62 | 48.33% | -33.33 pp | [-40.00, -25.83] pp | 16–0–24 |
| A2 | 94–0–26 | 78.33% | -3.33 pp | [-10.83, +4.17] pp | 38–0–2 |
| CONTROL27 | 82–0–38 | 68.33% | -13.33 pp | [-20.00, -5.83] pp | 34–0–6 |
| CONTROL28 | 90–0–30 | 75.00% | -6.67 pp | [-16.67, +3.33] pp | 32–0–8 |
| SAP027 | 79–0–41 | 65.83% | -15.83 pp | [-22.50, -9.17] pp | 35–0–5 |
| SAP028 | 88–0–32 | 73.33% | -8.33 pp | [-15.83, +0.00] pp | 36–0–4 |
| CONTROL2 | 92–0–28 | 76.67% | -5.00 pp | [-11.67, +2.50] pp | 36–0–4 |
| SAP02 | 93–0–27 | 77.50% | -4.17 pp | [-12.50, +4.17] pp | 37–0–3 |

| Paired comparison | Panel difference | 95% interval |
|---|---:|---:|
| SAP027 minus CONTROL27 | -2.50 pp | [-11.67, +6.67] pp |
| SAP028 minus CONTROL28 | -1.67 pp | [-12.50, +10.83] pp |
| A2 minus S30 | +30.00 pp | [+19.15, +40.83] pp |
| CONTROL2 minus CONTROL27 | +8.33 pp | [+2.50, +15.00] pp |
| CONTROL2 minus CONTROL28 | +1.67 pp | [-10.00, +13.33] pp |
| SAP02 minus SAP027 | +11.67 pp | [+2.50, +20.83] pp |
| SAP02 minus SAP028 | +4.17 pp | [-3.33, +11.69] pp |

| Candidate vs V14 | W–D–L | Candidate wins (95% interval) | Draw-half score (95% interval) | V14 wins (95% interval) |
|---|---:|---:|---:|---:|
| S30 | 2–0–38 | 5.00% [0.00, 15.00] | 5.00% [0.00, 15.00] | 95.00% [85.00, 100.00] |
| A2 | 14–0–26 | 35.00% [15.00, 55.00] | 35.00% [15.00, 55.00] | 65.00% [45.00, 85.00] |
| CONTROL27 | 4–0–36 | 10.00% [0.00, 25.00] | 10.00% [0.00, 25.00] | 90.00% [75.00, 100.00] |
| CONTROL28 | 12–0–28 | 30.00% [10.00, 50.00] | 30.00% [10.00, 50.00] | 70.00% [50.00, 90.00] |
| SAP027 | 4–0–36 | 10.00% [0.00, 25.00] | 10.00% [0.00, 25.00] | 90.00% [75.00, 100.00] |
| SAP028 | 10–0–30 | 25.00% [10.00, 45.00] | 25.00% [10.00, 45.00] | 75.00% [55.00, 90.00] |
| CONTROL2 | 8–0–32 | 20.00% [5.00, 40.00] | 20.00% [5.00, 40.00] | 80.00% [60.00, 95.00] |
| SAP02 | 12–0–28 | 30.00% [10.00, 50.00] | 30.00% [10.00, 50.00] | 70.00% [50.00, 90.00] |

Per-opponent comparisons, side summaries, per-card estimates and source hashes are in the JSON.

Interpretation limits:

- Exploratory diagnostic on 20 locally reserved cards; not a strength confirmation or submission decision.
- Only two training seeds, reported separately; card bootstrap quantifies card variation conditional on these checkpoints, not precise training-seed uncertainty.
- Multiple role/opponent comparisons; percentile intervals are unadjusted and do not control simultaneous error.
- Whole cards are paired across roles and resampled with both sides together; pooled panels additionally keep all three opponents together.
- A score of 1 on these games describes this sample only and does not imply a population guarantee.
- CSV consistency cannot independently reconstruct engine scoring; v2 is required and outcome/win/point fields are cross-checked.
