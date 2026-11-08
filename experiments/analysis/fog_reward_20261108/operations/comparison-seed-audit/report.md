# Fog comparison seed usage audit

**Independent read-only result:** no earlier consumption or reservation overlap was observed in the scanned result data for any of the four planned evaluation ranges. The ranges are reserved by the published comparison spec at commit `8094c38`; that is the intended reservation for this study, not a prior foreign use or collision.

## Planned evaluation ranges (inclusive)

- `fog_selection`: 7700000–7700019
- `fog_direct_selection`: 7700100–7700119
- `fog_confirmation`: 7701000–7701039
- `fog_direct_confirmation`: 7701100–7701139

The spec sets these for 440-game selection (7700000–7700019 and 7700100–7700119) and, only if nominated, a max 1,200-game confirmation (7701000–7701039 and 7701100–7701139).

## Findings

- All 8 registered worktrees; 15,003 evidence paths inventoried. Unique parsed data: 1643 CSV, 370 JSONL, 1266 JSON; 686 range candidates.
- Matches in actual CSV/JSONL seed fields: **0**. JSON seed/numeric mentions: **0**. Candidate intervals/reservations overlapping target ranges: **0**. Target-like numeric strings: **0**.
- The only known reservation is the comparison spec published in commit `8094c38`, which reserves these four ranges for this study. It is intentionally distinguished from prior result-data use; the scanned artifacts contain no evidence of earlier use or a competing reservation.

## Protocol commit and planned reservation

`8094c38` is exclusively the Git commit identifier for the published comparison protocol/spec that reserves the four listed seed ranges. There is no separate reservation named `8094`. The spec reservation is the intended reservation for this study, not an earlier competing reservation. Bare `8094` matches in old run logs can be update indices or decimal values (for example `0.8094`), not game seeds; they were not counted as range collisions.

## Scan limits

- The ongoing training changed 17 files during the scan (8 changed during/after read, 9 detected changed at final inventory), including progress, rollout, audit, run-record, and quota-usage files. These are active training artifacts using seeds in the 741/742/760 ranges, outside the planned 770xxxx evaluation ranges, so the observed mutation does not indicate an overlap. The scan is still a local snapshot; those active artifacts can continue changing. The scanner recorded zero errors, and HEAD did not change.
- Explicit metadata gaps: 285 CSV files without a seed column; 219 JSONL files and 258,913 JSONL records without numeric seed metadata; 893 invalid nonblank seed-field values. Full paths and values are enumerated in scanner evidence.
- Scope is eight registered local worktrees and experiments/logs/replays trees; undocumented/external runs are unknown. Scanner supports JSON/JSONL/CSV and gzip variants, skips `.git`, environments, `node_modules`, and `__pycache__`, and does not follow directory symlinks. Other formats/locations are out of scope.

## Evidence

- `report.json`: concise findings, range definitions, reservation distinction, scan limits, and mutation list.
- `seed_freshness.json`: full scanner inventory, hashes, fields, gaps, errors, and mutations.
- `scan.py`: adapted copy of the established read-only scanner. All outputs are under `/tmp/sherlock-fog-comparison-seed-audit`; no repository files were changed or tests/models/games run.
