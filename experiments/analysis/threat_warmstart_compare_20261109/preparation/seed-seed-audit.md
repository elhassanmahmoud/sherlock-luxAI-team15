# SAP-leading targeted seed check

Verdict: **REVIEW_REQUIRED**.

Scanned 8 registered local worktrees, 14714 structured artifact paths and 9376 text paths. Full inventory, hashes, overlaps, gaps and errors are in seed-audit.json.

- Parsed unique CSV/JSONL/JSON: 1695/0/1613.
- Numeric CSV/JSONL seed values: 1643224/0.
- CSV/JSONL consumption overlaps: 0; JSON numeric mentions: 0; JSON interval overlaps: 0; JSON string mentions: 0.
- Text reservation mentions: 3; repository reservation allowlist is empty.
- Seedless unique CSV/JSONL files: 286/0; JSONL records without numeric seed: 0.
- Invalid nonblank seed values: 1997; structured errors: 0; text errors: 0; text decoding gaps: 0; mutations: 24.

Raw JSONL traces, rollouts and provenance were deliberately excluded; this is a metadata/CSV check without a stable-window claim.

Local evidence only. External/undocumented runs, opaque formats, computed formulas and seedless records remain unknown. No models, games or tests ran.
