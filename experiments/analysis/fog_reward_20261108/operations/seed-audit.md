# Fog seed freshness audit

**Verdict:** NO_OBSERVED_CONSUMPTION_OR_JSON_OVERLAP_WITH_REPORTED_SCHEMA_LIMITS. No observed target-range consumption, JSON numeric/seed mentions, range overlaps, or target-like numeric strings in the scanned local evidence.

## Requested ranges (inclusive)

- `fog_train41`: 7410000–7410199
- `fog_prefill41`: 7415000–7415019
- `fog_train42`: 7420000–7420199
- `fog_prefill42`: 7425000–7425019
- `fog_diagnostic`: 7600000–7600003

## Scan coverage

- All 8 registered Git worktrees; 14,925 discovered log/artifact paths, with stored-byte exact duplicates deduplicated for parsing.
- Unique parsed: 1636 CSV, 358 JSONL, 1228 JSON files; 1,638,144 CSV and 39,003 JSONL numeric seed values; 677 JSON interval candidates.
- Target overlaps: CSV/JSONL consumption 0; JSON seed/numeric mentions 0; interval/reservation candidates 0; target-like JSON strings 0.
- Errors 0; scan-time file/HEAD mutations 0. Invalid nonblank seed-field values: 778; retained individually in JSON evidence.

## Gaps and limits

- 282 unique CSV files have no seed column; 215 JSONL files have no numeric seed field. 257,701 JSONL records lack numeric seed metadata.
- These are explicit unknowns, not proof of freshness. The scanner covers registered local worktrees and experiments/logs/replays trees only; unregistered/external or undocumented runs remain unknown. It skips `.git`, virtual environments, `node_modules`, and `__pycache__`, does not follow directory symlinks, and cannot establish seed use from seedless records.
- No matching planned reservation/range mention was found. All discovered JSON files and 677 numeric interval candidates were examined; no candidate overlapped requested ranges. No hidden exclusions from the scanner's recorded inventory/gap/error lists.

## Evidence files

- Full file/range/schema evidence: `seed_freshness.json` (14925 inventory entries; full paths, hashes, and metadata).
- Machine-generated overview: `short.md`.
- No repository files were changed; no models loaded, games played, or tests run.
