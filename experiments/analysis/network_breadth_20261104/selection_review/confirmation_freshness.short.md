# Confirmation freshness delta

**PASS for local held-out freshness, with the original schema limits retained.**

Confirmation 862000–862399 and direct 863000–863159 have zero observed consumption. All seven worktrees were re-inventoried and all 10,377 current data/JSON files were rehashed. The 10,332 baseline files are byte-unchanged; 45 paths are new, with no missing baseline files or changed baseline bytes.

After exact-byte deduplication, the delta contains 10 CSV files with 964 numeric seed records: 920 completed-screen records on 861000–861019 and 44 pilot records. No JSONL files changed. Eighteen distinct new JSON contents were checked, including one byte-verified compressed archive of the pinned original audit; seven are manifest/state/plan/freeze/reservation records.

The current study plan reserves the held-out ranges. These reservations and the archived audit are metadata, not consumption. No unknown new metadata, new schema gaps, invalid seed values, read/parse errors, file mutations, or confirmation state/results were found.

The original audit and scanner remain untouched. Original limitations still apply: 262 seedless CSV summaries, 21 seedless JSONL files (6,065 records), undocumented trials, and other-machine use cannot be ruled out. No models, tests, games, or repository writes were performed.
