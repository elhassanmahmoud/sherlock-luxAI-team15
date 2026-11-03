# Rescue alignment implementation report

Owned repository files: agents/sherlock/config.py, agents/sherlock/main.py, scripts/final_rescue_train.py, tests/test_final_rescue_training.py. No commit, actual environment game, real checkpoint extraction or actual training was performed. Historical wrappers/checkouts unchanged.

Default-off rescue_in_training permits only active rescue computation and its downstream obey/neb-candidate moves in training. Ordinary standalone eval-only rules remain gated. Existing eval behavior ignores this flag. Synthetic observations prove both stay-to-candidate and away-to-candidate correction, final actions written to actual replay, delay/known-point/enemy guards, antidiagonal player1 mapping and ring-buffer wrap.

New wrapper follows the fixed 120-prefill/1200-training/96-validation plan, common seed29/mapoffset3000, component18, independent fresh Adam/replay, 60000 initial env steps, epsilon0.05. Source is pinned to V14 hash. Shared identity/prefill/end/reload proofs are imported from the reviewed historical targeting_adapt module; that module is not modified. No forced P validation flags. The actual act/update boundary checks every canonical emitted action and resulting replay write and creates bounded transcript hashes. Every actual training episode must add150 updates; final counters must equal180000/459960. Treatment must exhibit rescue action changes during actual train-phase rows, not merely prefill. Control must exhibit none.

Outputs: prepared/run_records/<name>.json; run directory train.csv, val.csv, rollouts.jsonl, validation_games.jsonl, rescue_training_audit.json, weights/agent.pth and buffer; final_receipt.json only on successful full verification. validate_final_receipt(path, arm='control18'|'adapt18') rejects role swaps, hashes/inputs/pins mismatch, incomplete chronology, wrong checkpoint tensors/counters, missing reload proof and absent/mismatched interventions. Outputs never overwrite existing run directories. Frozen input/source/pins must be established before prepare; concurrent edits after prepare will reject execution.

Actual verification:
- Red: synthetic rescue tests failed at [STAY,STAY]/[LEFT,LEFT] instead of moving RIGHT; missing default flag and wrapper also failed.
- Green initial functionality and wrapper contracts.
- Focused regression command: /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest -q tests/test_final_rescue_training.py tests/test_targeting_adapt.py tests/test_rules_2110.py tests/test_finetune.py =>145 passed in41.87s (before two final additional tests).
- Additional red/green: a synthetic treatment with rescue only during prefill was initially accepted, then correctly rejected by requiring changes in train-phase rows.
- Final new test file: same interpreter -m pytest -q tests/test_final_rescue_training.py =>50 passed in13.17s. Full simulated finetune control flow tests cover both arms, fixed counts, receipt validation, changed checkpoint, incomplete updates, zero/only-prefill rescue, validation failure and hook restoration. Those tests explicitly replace environment episodes and action-audit boundary; they do not claim games or gradients. Separate observation tests use the real action audit and replay.
- git diff --check passed before final small additions; root integration should rerun.

Remaining: independent review; whole suite and actual small technical game smoke under root scheduling (initial task prohibited actual games); prepare only after final source freeze; actual run/data acceptance remains separate. Worktree has no .venv; use the absolute primary interpreter above.

Seed note from root ruling: prefill495000–495003 were historically used scratchpad training maps. Their reuse is accepted as training-only; remaining prefill495004–495059 follows fixed plan. Do not claim every prefill map fresh. Holdouts remain separately reserved/audited by root.

## Independent-review correction

Reviewer P2: receipt reader originally checked end hashes/reload but accepted a manually fabricated receipt missing full initial/prefill/validation evidence and empty savedAdam. Producer live checks were stronger than reader. Added independent persisted-proof validation: freshAdam hash/empty replay/initialidentity, unchangedprefill, beforetrain1/600/1200, three validation before==after proofs, all1320rollout counters/config/schema,150updatesper303-steptraininggame, savedAdam moments perparameter withstep180000, full rawGAME_FIELDS and303/v2, exactTRAIN_FIELDS and CSVcounters, final identity againsthistory. Added negatives with refreshedhashes for missinginitial/prefill/validations/beforetrain, emptyAdam, wrongrolloutcounters,302-stepvalidation and game-onlyCSV. Finaltrainerfile58tests passed27.78s. Independent bounded rereview PASS from final_protocol_review; report /tmp/sherlock-final-20261103/training_candidates_review.md. Root owns updatedcandidatefixture and integration/full-suite run.
