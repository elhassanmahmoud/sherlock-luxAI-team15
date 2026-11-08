# Local seed freshness audit

Verdict: **NO_OBSERVED_CONSUMPTION_OR_JSON_OVERLAP_WITH_REPORTED_SCHEMA_LIMITS**.

Scanned all 8 registered worktrees under experiments/logs/replays; SHA-256 deduplicated exact stored file bytes.

Fog ranges (inclusive): fog_train41 7410000–7410199; fog_prefill41 7415000–7415019; fog_train42 7420000–7420199; fog_prefill42 7425000–7425019; fog_diagnostic 7600000–7600003.

- 1636 unique CSV/CSV.gz files, 1,638,144 numeric seed values.
- 358 unique JSONL/JSONL.gz files, 295,460 records, 39,003 numeric seed values.
- 1228 unique JSON/JSON.gz files, 677 interval candidates examined.
- Actual CSV/JSONL overlaps: 0; JSON numeric/seed mentions: 0; JSON interval overlaps: 0; JSON string mentions: 0, all explicitly classified in the report.
- Missing numeric seed information: 282 unique CSV files, 215 unique JSONL files, 257,701 JSONL records. Full paths/schema are in seed_freshness.json.
- Invalid nonblank seed values: 778; read/parse errors: 0; mutations: 0.

Local evidence only. Undocumented trials, other machines, and seedless records remain unknown. No repository writes, model loading, tests, or games were performed.
