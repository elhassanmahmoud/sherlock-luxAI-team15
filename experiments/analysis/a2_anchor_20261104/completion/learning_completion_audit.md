# Independent learning completion audit

Status: **passed**. All four final arms were checked after DATA_READY, at frozen source `09c69349afc020a7b2418c249657a5698c472964`. No new games, training, or model inference were performed. Four public validators each ran once and exited successfully.

| Arm | Actual games | Updates | Teacher samples | Positive anchor gradients | Mean TD | Mean anchor | Mean total |
|---|---:|---:|---:|---:|---:|---:|---:|
| CONTROL25 | 232 | 24000 | 0 | 0 | 0.82400066 | 0.00000000 | 0.82400066 |
| ANCHOR25 | 232 | 24000 | 6,144,000 | 24,000 | 0.83093059 | 0.05813438 | 0.83674403 |
| CONTROL26 | 232 | 24000 | 0 | 0 | 0.86360432 | 0.00000000 | 0.86360432 |
| ANCHOR26 | 232 | 24000 | 6,144,000 | 24,000 | 0.91213323 | 0.06430966 | 0.91856420 |

Each arm has exactly 40 prefill, 160 training and 32 isolated known-validation games: 928 actual games and 96,000 updates overall. Every train game accounts for 150 actual updates. Both seed pairs have identical actual initial weights/optimizer/RNG evidence and all 40 prefill action, reward, replay-content and RNG projections.

All 12,288,000 teacher draws were independently recreated from seed `20261104 + run_seed`, with 256 draws with replacement per ANCHOR update. Every index belongs to the fixed 356,415 training rows; none belongs to the 68,687 excluded rows. Train-only scale independently recomputed as 1.4293522257922757. Every ANCHOR update has a positive finite output-gradient norm and finite `TD + 0.1 × anchor` loss; one optimizer step per update. CONTROL has no anchor draws/gradient/loss and uses the pinned original zero-weight update branch.

All final Q/target/config/counters and Adam moments match the saved runtime evidence; each parameter has Adam step 24,000. Final Q changed from A2, replay chronology grew from empty, persisted replay arrays are finite and correctly shaped, and both public checkpoint receipts and their evidence hashes match. Unused nested SAP0 roles were never run. Pinned source, dataset, initial/protected files and HEAD were checked again after validation.

The first verifier attempt stopped because NumPy 2.5.4 does not expose the private `_read_array_header` function. The original failed report and script are preserved as `learning_completion_audit.failed_attempt1.json` and `learning_completion_auditor.failed_attempt1.py`. Only the temporary auditor changed to supported public NPY header readers; frozen sources and experimental data were unchanged.

Limits: prefill arrays are represented by their actual runtime content digest, not a separately saved prefill array snapshot. Gradient activity is the persisted hook norm from the actual shared backward. This audit accepts learning evidence; it does not assess playing strength.

Machine-readable evidence: `learning_completion_audit.json`. Auditor SHA256: `8731231b56a514f882736b06040188703e0887d717f181b86a446bb0a9f2acbc`. Completed UTC: 2026-11-04T20:05:53.455864+00:00.
