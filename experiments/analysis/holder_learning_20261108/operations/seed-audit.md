# Local seed freshness audit

Verdict: **NO_OBSERVED_CONSUMPTION_OR_JSON_OVERLAP_WITH_REPORTED_SCHEMA_LIMITS**.

Scanned all 8 registered worktrees under experiments/logs/replays; SHA-256 deduplicated exact stored file bytes.

Ranges (inclusive): hold-learning training 6500000–6500023; validation 6501000–6501007.

- 1636 unique CSV/CSV.gz files, 1,638,144 numeric seed values.
- 177 unique JSONL/JSONL.gz files, 255,084 records, 38,813 numeric seed values.
- 1213 unique JSON/JSON.gz files, 675 interval candidates examined.
- Actual CSV/JSONL overlaps: 0; JSON numeric/seed mentions: 0; JSON interval overlaps: 0; JSON string mentions: 0, all explicitly classified in the report.
- Missing numeric seed information: 282 unique CSV files, 83 unique JSONL files, 217,515 JSONL records. Full paths/schema are in seed-audit.json.gz.
- Invalid nonblank seed values: 598; read/parse errors: 0; mutations: 0.

Local evidence only. Undocumented trials, other machines, and seedless records remain unknown. No repository writes, model loading, tests, or games were performed.
