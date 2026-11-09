# Ensemble-behavior seed conflict check

Ranges inclusive: solution 9990000–9990019 (20 cards); direct_v14 9990100–9990119 (20 cards); direct_control 9990200–9990219 (20 cards); 60 targeted card IDs. Historical 9960xxx training blocks are excluded without a freshness claim.

Verdict: **NO_OBSERVED_OTHER_CONSUMPTION_OR_RESERVATION_WITH_REPORTED_LIMITS**.

Scanned 8 registered local worktrees, 15117 structured artifact paths and 9767 text paths. Full inventory, hashes, overlaps, gaps and errors are in seed-audit.json.

- Parsed unique CSV/JSONL/JSON: 1713/0/1779.
- Numeric CSV/JSONL seed values: 1644184/0.
- CSV/JSONL consumption overlaps: 0; JSON numeric mentions: 0; JSON interval overlaps: 0; JSON string mentions: 0.
- Text reservation mentions: 1; only the exact current ensemble-behavior plan and spec paths are allowlisted as reservation mentions.
- Seedless unique CSV/JSONL files: 288/0; JSONL records without numeric seed: 0.
- Invalid nonblank seed values: 2543; structured errors: 0; text errors: 0; text decoding gaps: 0; mutations: 0.

Raw JSONL traces, rollouts and provenance were deliberately excluded; this is a metadata/CSV check without a stable-window claim.

Local evidence only. External/undocumented runs, opaque formats, computed formulas and seedless records remain unknown. No models, games or tests ran.
