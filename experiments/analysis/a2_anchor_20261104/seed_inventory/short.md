# Local seed freshness audit

Verdict: **NO_OBSERVED_CONSUMPTION_OR_JSON_OVERLAP_WITH_REPORTED_SCHEMA_LIMITS**.

Scanned all 8 registered worktrees under experiments/logs/replays; SHA-256 deduplicated exact stored file bytes.

Range (inclusive): anchor diagnostic867000–867019; direct867100–867119.

- 1543 unique CSV/CSV.gz files, 1,609,738 numeric seed values.
- 66 unique JSONL/JSONL.gz files, 17,712 records, 12,635 numeric seed values.
- 908 unique JSON/JSON.gz files, 639 interval candidates examined.
- Actual CSV/JSONL overlaps: 0; JSON numeric/seed mentions: 0; JSON interval overlaps: 0; JSON string mentions: 0, all explicitly classified in the report.
- Missing numeric seed information: 268 unique CSV files, 22 unique JSONL files, 6,065 JSONL records. Full paths/schema are in seed_freshness.json.
- Invalid nonblank seed values: 287; read/parse errors: 0; mutations: 0.

Local evidence only. Undocumented trials, other machines, and seedless records remain unknown. No repository writes, model loading, tests, or games were performed.
