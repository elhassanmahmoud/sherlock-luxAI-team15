# Independent final training audit

**PASS — technical qualification only.** Six r1 arms have complete, internally consistent final evidence. No material issue found.

Frozen HEAD `6ad34527673e29f0e50e2dacc917e5ded59f0343`. Independently inspected all raw chronological rows and saved tensors; the receipt validator and plan generators were not used.

| Arm | Parent | Prefill / learning / validation | Updates | Q tensors changed |
|---|---:|---:|---:|---:|
| A0 | 18 | 120 / 3000 / 128 | 450,000 | 12/12 |
| B0 | 18 | 120 / 3000 / 128 | 450,000 | 12/12 |
| A1 | 24 | 120 / 3000 / 128 | 450,000 | 12/12 |
| B1 | 24 | 120 / 3000 / 128 | 450,000 | 12/12 |
| A2 | 30 | 120 / 3000 / 128 | 450,000 | 12/12 |
| B2 | 30 | 120 / 3000 / 128 | 450,000 | 12/12 |

Totals: **19,488 executions** (720 prefill, 18,000 learning, 768 validation), **2,700,000 optimizer updates**. Interrupted r0 and smoke runs remain separate.

Independently verified: exact parent Q/target starts; fresh Adam identity; intended training config; regenerated ordered RNG/opponent, seed and side plans; every 303-step rollout and every 150-update learning increment; CSV/raw-row consistency and validation aggregates; finite positive recorded losses; finite changed Q/target/Adam with all Adam steps at 450,000; strict Q/target and optimizer load; six distinct new final Q states; all receipt/artifact/source/interpreter/input hashes and supervisor completion. All 24 recorded validation before/after identities match exactly, with V14 validation config and expected counters.

Both protected V14 files remain `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; ZIP hash also matches the supervisor baseline.

Limits: Validation equality is independently checked against recorded pre/post identities, including model/optimizer hashes, counters, config, replay metadata and RNG hashes. Full historical replay/RNG bytes were not retained and were not reconstructed. Action/replay consistency counters and transcript digest format were checked; raw action transcripts were not retained, so historical per-action correspondence was not independently replayed. Saved Q/target and Adam were deserialized, finite-checked and loaded with strict shape/optimizer checks. No new inference, game, training or pytest was run. Known validation maps do not establish fresh generalization or ensemble strength. Interrupted r0 and smoke runs are excluded from these totals. Outside the validation boundary, B1 milestones 0/2000 and B2 milestone 0 have only a changed global RNG digest before the next training call. Each next opponent is default; its constructor resets NumPy RNG (agents/default/default.py:17), and finetune constructs it before the rollout hook. Validation pre/post identities themselves are unchanged.

No sources, historical artifacts, weights or commits changed. Full hashes, counts and checks: `final_training_audit.json`.

## Independent candidate check

**PASS** — A39/B39/ALL42/REPLACE36 contain exactly 39/39/42/36 distinct members in the fixed order. Every saved tensor was compared directly with the protected original 36 and the six independently audited final Q states; all 42 combined members are distinct. Raw V14 configuration is exactly preserved, every input dimension is 79 (six actions), all tensors are finite and strict model loading succeeds. Candidate/checkpoint/receipt/input/builder hashes match; target Q and inference-only counters are correct. REPLACE36 remains non-nominable. No performance games, inference, tests or source changes. Detailed separate candidate checks and manifest hash are in the JSON.
