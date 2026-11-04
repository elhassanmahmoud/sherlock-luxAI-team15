# Independent confirmation review — 4 November 2026

**Data/statistics integrity: PASS. Promotion qualification: FAIL.** FO42 fails three of the seven fixed gates; V14 remains the qualified incumbent. A higher Solution point estimate does not override the failed gates.

The unchanged pre-results auditor completed successfully at 2026-11-04T10:14:07+00:00. All five jobs and all **3,840** confirmation games were complete before outcome access. Every expected seed/side/opponent key, 303-step record, scoring version 2, result consistency, win/draw/loss count, confidence interval, and official-summary field matched. No missing, duplicate, extra, or excluded games were accepted.

| Measure | FO42 | V14 | Difference or direct rate, with 95% interval |
|---|---:|---:|---|
| Six-opponent panel, 80 cards × 12 games | 773/960 wins | 772/960 wins | Δ +0.104167 pp [-3.645833, +3.750000] |
| Solution, 400 cards × 2 sides | 771/800 wins | 762/800 wins | Δ +1.125 pp [-0.375, +2.750] |
| Default, 80 cards × 2 sides | 160/160 wins | 160/160 wins | Δ 0.000 pp |
| Direct versus V14, 160 cards × 2 sides | 180/320 wins | 140/320 wins | 56.25% [48.75%, 63.75%] |

| Fixed promotion gate | Observed | Result |
|---|---:|---|
| Panel Δ ≥ +1 pp | +0.104167 pp | FAIL |
| Panel lower bound > 0 | -3.645833 pp | FAIL |
| Solution Δ ≥ 0 | +1.125 pp | PASS |
| Solution lower bound > −1 pp | -0.375 pp | PASS |
| Default ≥ 99% | 100.00% | PASS |
| Default Δ ≥ −1 pp | 0.000 pp | PASS |
| Direct lower bound > 50% | 48.75% | FAIL |

Solution combines disjoint blocks **862000–862079** (80 cards) and **862080–862399** (320 cards), exactly once: 800 games per model. The extra block does not enter the panel; the six panel opponents retain equal weights on the first 80 cards. Direct cards are the separate range **863000–863159**. Intervals use 5,000 whole-card bootstrap samples, PCG64 seed 0, and linear 2.5/97.5 percentiles; both sides and all panel opponents remain clustered together.

The auditor recursively rechecked the closed 920-game selection, the same immutable freeze, and FO42's exact-count nomination. Original and confirmation prelaunch source/freeze/plan pins match; confirmation proof hashes also match. Actual source HEAD, complete source/protocol/interpreter inventory, all frozen model file hashes, and V14 protected raw inputs passed. The current `Gruppe15.zip` also matches the prelaunch protected ZIP SHA256 `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`. No models were loaded, games launched, or repository files changed during this review.

- Source HEAD: `bed06df3335caa4d7a79c928132143a9c7e0a8fc`
- Freeze SHA256: `c01a9f059fb165767e216683db95dc82a29c814ad7073a37585e98579c632e13`
- Auditor SHA256: `0722ff67da35b9b50ba71cd3f49340fe1024cba14965f27ed5dd29410eb7c530`
- Review JSON SHA256: `8ac4b9e2c16b64749843685b4f7cc8a74c8ef8a0e15853b549a9e63f6651570b`
- Full evidence: [confirmation_independent_review.json](/tmp/sherlock-breadth-20261104/confirmation_independent_review.json)
