# Task 1 implementation

Three new files only. No old source edited, no commit, no real checkpoint/model/archive or simulator/game execution. Synthetic tensors and temporary synthetic replay fixtures were used. No production profile monkeypatching.

## Verified

`source-config-green.log`: 87 passed in 4.29 s (latest run); previous `final-targeted.log`: 87 passed in 5.18 s (34 new contracts, existing BehaviorEnsemble contracts and four parameterized historical-binding test groups). Original Python interpreter, -B. Red/green stages are retained in red-1..4.log and green-1..6.log; intermediate green-3/4 logs contain reported failures while the next planned contract was incomplete and one synthetic play-one double missed the new keyword. Final tests pass. `git diff --check` clean. Exact current hashes in stable-hashes.json. Independent static review completed with no open findings: /private/tmp/frozen-v14-exposure-review/static-review.json. The reviewer read the 34/87-PASS logs and ran no tests/models. Root actual admission remains separate.

## Admission

Base original behavior fields: schema_version=1, profile=frozen_v14_exposure_20261109, stage=technical|training, starts=[48,49], start_authorized=true, allow_battery=true, historical_runtime_gap_acknowledged=true, root/out/python/plans/source/runtime/protected/inputs/stop_file/config/initial/rollout_plans/v14_source. Each rollout_plan is the original match_weight 440-key sequence unchanged.

Additional: reference_admission/reference_receipt/reference_acceptance/reference_state name the accepted original match_weight_compare V14 assembly. training_completion names the accepted ON training closure, SHA fca3a077e57f079605db362f9dc68facadf787b0a3e819d1aca85050a84b23ce. opponent_model is the accepted v14.pth (817e565f...). opponent_config_source names match_weight source-config.json, directly pinned by SOURCE_CONFIG_SHA=a094376eca24e5054b0a14228f5861b9bccb832199954fd7957f1431af5ab69f; use its source_config object normalized by original inference_config. Root actual metadata preflight showed that the wrapper is absent from both historical admission input sets. The prior synthetic assumption of that historical membership was removed, and the actual normal stock model config remains checked against the pinned metadata. source_members is the ordered original 36 tensor-hash list. These fields are required in both stages.

Technical omits technical_receipt/technical_acceptance; training includes them. Technical receipt is technical_v1/technical/receipt.json. Root technical acceptance requires status=PASS, profile, exact current source, technical_receipt_sha256 and original_processes_ended=true. All receipt.files are bound inputs. No historical admission is re-run against new HEAD; sealed original metadata validators are reused.

## Worker artifacts and manual release

Technical: one role technical, exactly two historical ON/Solution cases followed by two fresh-start ON/frozen-V14 cases on fixed seeds/sides. Separate fresh start49 setup without play. Original play_game, TraceEnv and reward/action audits. Source BehaviorEnsemble reused unchanged.

Training: roles e48/e49; internal learner.role stays control. Each role saves ensemble-initial.json, games.jsonl, prefill.pth, prefill-replay.npz, prefill-reward-audit.npz, prefill.json, waiting.json. Both original workers wait after exactly40 games. approve-prefill validates both actual saved prefills and a Root review pinning current source/admission/prefill hashes, then atomically creates release.json. No automatic release/resume/retry.

Checkpoints retain q/target_q/opt/cfg/feature_dim/n_actions/empty ensemble fields/env_steps/learn_steps; `exposure` metadata has profile,status,role,start,source,completed_games,component_index=18,opponent_sha256. End files final.pth/final-replay.npz/receipt.json only after440 games and60000 updates. Failure produces ineligible incomplete artifacts. Owner requires original process groups ended before final actual artifact validators, shares original guard/lock/spawn/stop/cleanup helpers.

Every row retains the original key. `exposure` records original_opponent, actual_opponent, actual class/side, action-call count and action hash. Frozen participation additionally records fixed hash/seed/config, fresh-instance status, global+learner setup RNG proof and actual before/after member/target/optimizer/private-RNG/counter/buffer identities. A fresh ordinary stock Agent_x is loaded per V14 game, global and learner RNG restored even on load failure. All q/target/extras have gradients disabled. update/_update/_learn/save_agent/save_buffer fail immediately. Original new_game/env_cfg/act calls are only observed; no behavior hook or rules are added to the opponent. Before/after identities must match after all303 actual calls.

## Limits / next work

No empirical learning or strength result. Root controls actual technical admission, independent actual-data audit, manual joint prefill release, model phase and closure. No broad full suite was run because the task explicitly excludes real archives/simulators and asks for focused synthetic checks. Later comparison is a separate task after training acceptance.

## Root metadata preflight correction

The originally assumed source-config membership in reference_admission.inputs was false for actual historical metadata. On explicit Root ruling, only the new study/test were changed: fixed wrapper SHA, original V14 SHA and existing normalized inference/training configuration equalities. The synthetic historical fixture now deliberately has reference.inputs={} and verifies that a repinned-but-changed wrapper fails. Actual Red: source-config-red.log, one failure at the obsolete membership condition. Green: source-config-green.log, 87 passed in4.29s. Owner unchanged. No models, archives or games run. Independent follow-up review PASS: reviewer confirmed the actual wrapper digest and its absence from both historical admission input sets, plus the preserved configuration checks and Red/Green logs. Root notified.
