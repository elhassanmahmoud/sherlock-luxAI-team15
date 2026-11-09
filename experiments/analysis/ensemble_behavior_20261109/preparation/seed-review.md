# Ensemble-behavior seed conflict check

**Raw verdict: `NO_OBSERVED_OTHER_CONSUMPTION_OR_RESERVATION_WITH_REPORTED_LIMITS`.** One bounded scan covered only 60 new card IDs:

| Block | Inclusive card IDs | Count |
|---|---:|---:|
| Solution reference | 9990000–9990019 | 20 |
| Direct vs V14 | 9990100–9990119 | 20 |
| Direct vs CONTROL38 | 9990200–9990219 | 20 |

Historical 9960xxx training cards are intentional controls and were outside this scan; no freshness claim is made for them. Scan window: 2026-11-09T18:18:11.779460+00:00 through 2026-11-09T18:18:37.700192+00:00 UTC; 25.97s; exit 0.

## Method and result

Reused the existing scanner source `experiments/analysis/match_weight_20261109/preparation/seed-audit.py.txt` (SHA-256 `ecfaf1e859394b0e2e6ee84edb4cdc91c680c9f6470d01ecbc1ec36d727e2c12`), via prior external adaptation `0a05c8c68d5d1b3092760d77b513d413958333959e7f7f36d4a69e8670d3f8dc`. Search logic was unchanged; only target ranges, the exact two current plan/spec paths, and profile/summary wording changed. Those paths exist only in the study worktree. No additional allowlist exceptions.

Eight registered worktrees were scanned: 15,117 structured CSV/JSON/`.gz` paths and 9,767 text paths. Results: **0 CSV seed hits**, **0 JSON numeric/interval/string overlaps**. There was **one text hit**, the current spec's line 32 stating the three reserved ranges; it is classified as `allowed_current_spec_or_plan`. The plan is an exact allowlisted path but does not contain target card literals. No other matching hit is suppressed.

The scan recorded no parser/text errors and no file/HEAD mutations. All eight HEADs match before and after; study HEAD was `e1b8f8e35399109de9cfa8431ed6cc46f97aad6c`. Plan/spec scan hashes match post-scan reads.

## Limits

The existing method does not parse 2,020 raw JSONL paths, and 288 unique CSV files (5,061 rows) lack a seed column. It found 2,543 heuristic nonnumeric JSON seed-field values; these are schema gaps, not consumption hits. External/unregistered worktrees, undocumented or seedless records, computed seed formulas, opaque binary archives, and exclusively JSONL-backed histories remain unknown. This is local evidence, not an absolute freshness guarantee.

## Hashes

| Evidence | SHA-256 |
|---|---|
| Original scanner source | `ecfaf1e859394b0e2e6ee84edb4cdc91c680c9f6470d01ecbc1ec36d727e2c12` |
| Prior adapted scanner base | `0a05c8c68d5d1b3092760d77b513d413958333959e7f7f36d4a69e8670d3f8dc` |
| New adapted external scanner | `a03e8d991eaaab2cd7790f02506e2e8f636545ce6d8f283705eb34fa0b48b634` |
| Scanner diff | `aacd26389ef3d4fc7c6ee4538520c1c426c569ff5f8e12016dc98d3f6dddefc9` |
| Raw scan report | `93aab0b5e88d8463fa3699200bc339ab5abb3d0bcae15cec81f47c3711d83d6f` |
| New plan | `d2b706abc9701f01498edae84f042d874188381a08ae23cd703625c5d9dd4b9b` |
| New spec | `3fbad1bb1f283e9719463e94d438600270e0878809d3d995ce05382ab8a1a7fb` |
| Preserved previous audit archive input | `d7cd3b599394ddee754e641572ca77a873516aa41e4ce6ca5ba720aa738231f2` |

Full file inventory, hashes, text hits, schema gaps, excluded paths and eight HEADs are in `seed-audit.json`; lineage/scope are in `method.json`. All new files are under `/private/tmp/ensemble-behavior-seeds/`.
