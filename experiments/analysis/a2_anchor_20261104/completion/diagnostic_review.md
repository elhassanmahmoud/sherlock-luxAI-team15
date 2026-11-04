# Exploratory A2 teacher-anchor diagnostic

Integrity: all 920 planned games complete and unique (720 panel + 200 direct), finite, 303 steps, scoring v2; recorded outcomes agree with win counts.

Scores count draws as half. Intervals are unadjusted 95% whole-card percentile bootstrap intervals, 5,000 draws, seed 0. Both sides and all panel opponents stay grouped.

| Role | Panel W–D–L | Panel score | Difference vs V14 | 95% interval | Solution W–D–L |
|---|---:|---:|---:|---:|---:|
| V14 | 101–0–19 | 84.17% | +0.00 pp | [+0.00, +0.00] pp | 40–0–0 |
| A2 | 95–0–25 | 79.17% | -5.00 pp | [-13.33, +3.33] pp | 39–0–1 |
| CONTROL25 | 81–0–39 | 67.50% | -16.67 pp | [-25.83, -7.50] pp | 34–0–6 |
| CONTROL26 | 75–0–45 | 62.50% | -21.67 pp | [-29.17, -13.33] pp | 31–0–9 |
| ANCHOR25 | 96–0–24 | 80.00% | -4.17 pp | [-12.50, +3.33] pp | 36–0–4 |
| ANCHOR26 | 88–0–32 | 73.33% | -10.83 pp | [-19.17, -2.50] pp | 36–0–4 |

| Paired comparison | Panel difference | 95% interval | Solution difference | 95% interval |
|---|---:|---:|---:|---:|
| ANCHOR25 minus CONTROL25 | +12.50 pp | [+2.50, +23.33] pp | +5.00 pp | [-7.50, +20.00] pp |
| ANCHOR26 minus CONTROL26 | +10.83 pp | [+0.83, +20.83] pp | +12.50 pp | [-5.00, +27.50] pp |
| A2 minus V14 | -5.00 pp | [-13.33, +3.33] pp | -2.50 pp | [-7.50, +0.00] pp |
| ANCHOR25 minus A2 | +0.83 pp | [-8.33, +10.00] pp | -7.50 pp | [-15.00, +0.00] pp |
| ANCHOR26 minus A2 | -5.83 pp | [-15.83, +4.17] pp | -7.50 pp | [-20.00, +0.00] pp |

| Candidate vs V14 | W–D–L | Candidate wins (95% interval) | Draw-half score (95% interval) | V14 wins (95% interval) |
|---|---:|---:|---:|---:|
| A2 | 16–0–24 | 40.00% [20.00, 60.00] | 40.00% [20.00, 60.00] | 60.00% [40.00, 80.00] |
| CONTROL25 | 12–0–28 | 30.00% [10.00, 50.00] | 30.00% [10.00, 50.00] | 70.00% [50.00, 90.00] |
| CONTROL26 | 6–0–34 | 15.00% [0.00, 30.00] | 15.00% [0.00, 30.00] | 85.00% [70.00, 100.00] |
| ANCHOR25 | 14–0–26 | 35.00% [15.00, 55.00] | 35.00% [15.00, 55.00] | 65.00% [45.00, 85.00] |
| ANCHOR26 | 12–0–28 | 30.00% [10.00, 50.00] | 30.00% [10.00, 50.00] | 70.00% [50.00, 90.00] |

| Later-confirmation candidate | Panel ≥ A2 | Solution ≥ A2 | Panel > control | Direct ≥24 wins | Eligible |
|---|---:|---:|---:|---:|---:|
| ANCHOR25 | yes | no | yes | no | no |
| ANCHOR26 | no | no | yes | no | no |

First candidate for later confirmation: **none**. Ordering: panel score, Solution score, smaller training seed.
This diagnosis does not qualify any submission. The full confirmation/course/package/backup path remains necessary; no fallback after failed confirmation.

Per-opponent comparisons, side summaries, per-card estimates and source hashes are in the JSON.

Interpretation limits:

- Exploratory diagnostic on 20 locally reserved cards; not a strength confirmation or submission decision.
- Only two training seeds, reported separately; card bootstrap quantifies card variation conditional on these checkpoints, not precise training-seed uncertainty.
- Multiple role/opponent comparisons; percentile intervals are unadjusted and do not control simultaneous error.
- Whole cards are paired across roles and resampled with both sides together; pooled panels additionally keep all three opponents together.
- A score of 1 on these games describes this sample only and does not imply a population guarantee.
- CSV consistency cannot independently reconstruct engine scoring; v2 is required and outcome/win/point fields are cross-checked.
