# Confirmation freshness — actual local recheck

**PASS. No actual seed-field consumption found for 852000–852399 or 853000–853399 before confirmation start.**

Checked at 2026-11-03T22:35:01.671479+00:00; scan duration 21.05 seconds. This is a local seed-provenance check, not an outcome or strength analysis. No models, games, source/HEAD/plan/weight edits or fetches were performed. Only this report and its JSON were written outside the repository.

All seven currently registered Git worktrees match the original audit's registry. The historical baseline is `/tmp/sherlock-final-20261103/seed_audit.json`, audited at 2026-11-03T15:30:28.910313+00:00, SHA-256 `1faf40b601bb2550e06b5941136861eaa989f1d619344d5d65ce56e4be257bc3`. Every current CSV/CSV.gz and JSONL/JSONL.gz file was inventoried and scanned, deduplicating identical stored-file hashes. New or changed JSON files were selected by modification **or** change time since that original audit, including copied archives/manifests/receipts and both phase reservations.

| Current inventory / inspection | Count |
|---|---:|
| CSV / CSV.gz files | 6,936 / 9 |
| Unique CSV contents inspected | 1,492 |
| Actual CSV seed fields inspected | 1,589,974 |
| JSONL / JSONL.gz files | 20 / 205 |
| Unique JSONL contents inspected | 51 |
| JSONL lines / actual seed fields | 16,200 / 10,235 |
| Current JSON inventory / new-or-changed unique JSON inspected | 3,090 / 35 |
| New-or-changed unique manifests/state/plan/freeze records | 15 |
| Target-range actual consumption matches | **0** |
| Scan errors or data/HEAD changes during scan | **0** |

CSV fields were parsed as exact `seed` columns. JSONL entries with actual `seed` keys were parsed structurally; new JSON game records and manifest seed declarations were inspected separately. 263 unique CSV files have no seed column; they were not treated as direct seed-consumption evidence. Numeric fragments inside hashes, ordinary text and plans were not interpreted as games. Seed-field counts include multiple formats of the same execution and are not independent-game counts.

The added actual records are consistent with the completed 8,800-game 851000–851079 selection and the paired 493000–493599 learning / 495000–495059 prefill data. Repeated learning/rollout representations do not consume new confirmation cards. The older prefill reuse documented by the original audit remains historical training reuse, outside these confirmation blocks.

The only new target declarations found are the three planned jobs in the current confirmation plan: baseline and FT18 each declare first_seed852000,n_maps400; the direct job declares first_seed853000,n_maps400. Its SHA-256 is `918d0ea0e354dda69639002cde92aab8cd99f6c43e3d6b6f1298810b5b0d8749`, matching root's checked plan. At the audit snapshot, `performance/confirmation/` contained **only plan.json**, with no CSV,state or log files. The sibling `freeze.confirmation.reservation.json` reserves a future phase; it is not consumption evidence.

Worktree HEADs were stable throughout; followup remained7c906e1 and primary remained24f9d76. All inspected files retained their size/modification identity across the scan. The JSON retains the exact seven paths/HEADs, original-audit hash, counts, all15 manifest hashes, the three classified plan declarations, empty consumption-overlap/error lists and snapshot time.

Machine-readable evidence: `/tmp/sherlock-final-20261103/confirmation_freshness.json`. Confirmation freshness is accepted for the predeclared blocks; ordinary root source/resource/power/quota/time admission remains separate.
