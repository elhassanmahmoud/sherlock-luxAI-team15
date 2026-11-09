# Frozen-V14 exposure comparison implementation

The three new comparison files were integrated only after Root accepted the actual exposure training closure and released its source freeze. The earlier external draft was prepared while training ran under the explicit Root workflow exception recorded in `experiments/analysis/frozen_v14_exposure_20261109/operations/external-draft-ruling.json`. That draft was only text-read, never imported or executed during training; this is not presented as a strict test-before-draft workflow.

Actual closure metadata read before integration:
`experiments/analysis/frozen_v14_exposure_20261109/operations/training-completion.json`, SHA256 `1b3a4ea33661420c6ee1be9dcd691109e6cd829d2b9b5f5d6c17c25fda230236`, original source `6839ebd3bd3f2a939aeb07c15bb470a73bfc74c4`. It contains the two final identities, both preserved prefill proofs, manual release/Root review and complete owner record. No actual model or archive was decoded by this implementation task.

## Scope and identity

- `scripts/frozen_v14_exposure_compare.py`: `af4668708c31a1b2f02153eb1f7a2c0130c00c0409c80078b630ce5ce673ffc3`
- `scripts/frozen_v14_exposure_compare_owner.py`: `484326f9fac2fe2efa231ec19a50d2ecfdeeafb10f016a0d4fa060f7a48a534a`
- `tests/test_frozen_v14_exposure_compare.py`: `7408582158a2a9613ac3b49812e4aa6861f4e5750fbbe3a387f4452bf8bffdaf`

Only these three new repository files were written by the implementer. No existing source, project documentation, model, ZIP, commit or remote branch was changed. Root owns the parallel publication of actual completed training artifacts and documentation.

The adapter reuses unchanged `match_weight_compare.mount`, `inference_config`, `validate_and_load`; the prior comparison's historical binding and accepted-reference/training/assembly helpers; existing strict result/statistics helpers; and the original owner/process/guard utilities. No module-global profile monkeypatching, production behavior change or new framework.

Fixed models are original V14, unchanged accepted BEHAVIOR38, and original 36 plus e48 final.q followed by e49 final.q. Exact existing reference files are reloaded but never reserialized. Only the new exposure assembly is saved. The original normalized inference config and target are preserved. The actual stock loader checks batches 1, 8 and 16 during a separately admitted future zero-game phase.

The five fixed jobs total 200 games, both sides on the original three 20-card ranges. The four original gates count actual wins: Solution at least both references; both direct comparisons at least 24/40. Descriptive whole-card bootstrap statistics remain unchanged. Nomination only, no automatic confirmation or promotion. The owner has independent technical/performance invocations, at most two workers in waves 2+2+1, exclusive outputs, STOP/quota checks and owned-group cleanup.

## Actual verification

Interpreter: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python`.

1. `python -B -m pytest -q -p no:cacheprovider tests/test_frozen_v14_exposure_compare.py -k 'closed_both_starts or exact_five_jobs'` against a temporary legacy-only adapter: **2 expected failures**, 67 deselected. The old ON closure contract and old role/job composition fail the new exposure contract. Log: `red.log`.
2. Integrated the authorized external implementation draft and current headers. First complete new-file run: **66 passed, 3 failed**. All three failures were the new test fixture attempting to overwrite its synthetic corrupt-input JSON through the existing exclusive publication helper. Log: `green-first.log`. Fixed only those fixture writes, preserving production exclusive publication.
3. `python -B -m pytest -q -p no:cacheprovider tests/test_frozen_v14_exposure_compare.py tests/test_ensemble_behavior_compare.py tests/test_match_weight_compare.py`: **178 passed in 7.19s**, exit 0. Log: `green.log`. This includes 69 new cases and 109 existing directly reused comparison-helper cases.

Tests cover real synthetic closure/hash chains, changed/missing final and prefill evidence, preserved old source/profile identities, exact assembly order and current metadata, in-memory stock loading, unchanged reference serialization, card overlap/missing rows, strict complete CSV validation, 23 wins plus draws failing the 24-win gates, whole-map statistics, separate phase admission, STOP/quota/failure cleanup and no resume/automatic transition. Test guards prohibit actual archive loading, simulator construction, games and subprocesses. No full repository suite was run: Root authorized focused synthetic checks and prohibited actual archive/model/game work.

Independent final code/contract review passed with no open findings. The reviewer verified the three stable hashes, the complete 178-pass log, and the actual closure's required metadata/files/pins. Review: `/private/tmp/frozen-v14-exposure-review/compare-integrated-review.json`. These checks do not claim an actual assembly or performance result.

## Admission and receipt contract

Both stages use `schema_version:1`, `profile:frozen_v14_exposure_compare_20261109`, `stage:technical|performance`, `start_authorized:true`, `allow_battery:true`, and existing `root/python/plans/source/protected/inputs/stop_file/out` fields. Output is exactly `experiments/analysis/<profile>/{stage}_v1`; use distinct `technical.STOP` and `performance.STOP`. The plan list must preserve all historical source-bound plan paths plus the original frozen-exposure spec and plan. Every consumed path and historical input remains hash-bound in `inputs`.

Common new fields:
- `training_completion`: actual exposure closure above; `training_completion_sha256`: its actual accepted hash.
- `reference_performance_admission`: original accepted `ensemble_behavior_compare_20261109` performance admission. Existing helpers consume its original schema/source/profile and a new superset of bound inputs; never call an old admission against new HEAD.
- `v14_source`: original protected V14 model.
- `cohorts`: `solution/direct_v14/direct_behavior` paths under the existing exposure preparation directory.
- `seed_acceptance`: existing exposure preparation `seed-acceptance.json`. The historical limitations remain; only the intervening 884 receipt rows are additionally checked for overlap.

Technical admission omits `models` and new `technical_*` fields. Performance adds `technical_admission`, `technical_receipt`, `technical_state`, `technical_acceptance`, and exact `models` keys `v14`, `behavior`, `exposure`. The first two paths are unchanged historical eval copies; the last is new `technical_v1/exposure.pth`. No new top-level training config, initial state, runtime or rollout plan fields are needed.

Technical receipt: `status:complete`, comparison `profile`, `source`, `admission_sha256`, `training_completion_sha256`, `reference_performance_admission_sha256`, `command`, `games:0`, `no_strength_claim:true`, and models records with `path/sha256/members/member_sha256/loader_pass:true/batches:[1,8,16]`. Counts are 36/38/38, first 36 in original order, final two exposure member hashes match e48 then e49.

Required new Root assembly acceptance: comparison `profile`, `status:PASS`, `source`, `admission_sha256`, `technical_receipt_sha256`, `owner_state_sha256`, `actual_assembly_and_stock_loader_pass:true`, `original_processes_ended:true`. It must bind the complete zero-game owner, exact current source and both unchanged common provenance paths. Performance never starts automatically.
