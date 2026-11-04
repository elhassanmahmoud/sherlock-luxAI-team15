# Local seed freshness audit

Verdict: **NO_OBSERVED_CONSUMPTION_OR_JSON_OVERLAP_WITH_REPORTED_SCHEMA_LIMITS**.

Scanned all 7 registered worktrees under experiments/logs/replays; SHA-256 deduplicated exact stored file bytes.

Ranges (inclusive): screen 861000–861019; confirmation 862000–862399; direct 863000–863159.

- 1494 unique CSV/CSV.gz files, 1,601,974 numeric seed values.
- 51 unique JSONL/JSONL.gz files, 16,200 records, 10,811 numeric seed values.
- 716 unique JSON/JSON.gz files, 599 interval candidates examined.
- Actual CSV/JSONL overlaps: 0; JSON numeric/seed mentions: 0; JSON interval overlaps: 0; JSON string mentions: 5, all explicitly classified in the report.
- Missing numeric seed information: 262 unique CSV files, 21 unique JSONL files, 6,065 JSONL records. Full paths/schema are in seed_freshness.json.
- Invalid nonblank seed values: 0; read/parse errors: 0; mutations: 0.

Local evidence only. Undocumented trials, other machines, and seedless records remain unknown. No repository writes, model loading, tests, or games were performed.

Reviewed JSON metadata: 361 unique manifest/state/plan/freeze/reservation files; zero matching named JSON files outside experiments/logs/replays. The five text matches are four hash substrings and one timestamp fraction. No NEW-study seed declarations were present in this JSON snapshot, and no new-study exception was used. All old-run statuses are retained in the full report.

The 262 seedless CSVs are aggregate validation/training summaries (254 validation and 8 training). The 21 seedless JSONL files comprise 20 step-trace files and one watcher-event file; their filenames were not treated as proof of non-use.
