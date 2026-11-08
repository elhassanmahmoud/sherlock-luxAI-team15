# Task 2 implementation report — 2026-11-08

Status: implemented; **40 focused synthetic tests passed**. No real model games, no commits/pushes, no changes to production or historical study files. Root owns integration verification, source freeze, seed audit and public project documentation.

## Files

- `scripts/fog_reward_study.py`: bounded four-arm study, preparation, scoped `finetune` hooks, final-provenance reward/replay audit, full simulator/policy/replay hashes, immutable prefill bundles, independent bundle validation, final receipt validation.
- `scripts/fog_reward_supervisor.py`: single-use pair-first supervisor, at most two registered workers; independent prefill comparison before either learner proceeds; fresh usage strictly below100%, AC, source/HEAD/plans/input/submission/STOP/foreign-process guards, owned shutdown and wake process records.
- `tests/test_fog_reward_study.py`: synthetic tests only.
- This report.

## Fixed experiment

V14 exact SHA `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; component18; four identical fresh Q/target starts, no optimizer/replay serialized at preparation. Actual loaded learner must prove fresh Adam, empty replay, lr5e-5, counters60000/0, epsilon0.05. CONTROL/NEUTRAL differ only in `fog_unknown_reward_neutral`, starts41/42. Existing training rules including rescue enabled. SAP weight0.3, interval2, mixture60/20/10/10.

Each arm:40 prefill +400 train +16 initial/16 final known diagnostic executions, exactly60000 updates and193320 env_steps. Maps7410000–7410199/7420000–7420199, prefill7415000–7415019/7425000–7425019, diagnostic7600000–7600003. Initial diagnostics occur after no-gradient prefill as in existing finetune; model parameters remain identical. End state only is accepted; intermediate save calls are suppressed, inherited weights_best removed. No automatic promotion or claims of strength.

Preparation CLI:

```
python -B -m scripts.fog_reward_study prepare --out NEW_PREPARED
python -B -m scripts.fog_reward_supervisor start --prepared NEW_PREPARED --out NEW_OPERATIONS --python ABSOLUTE_PYTHON --expected-head FULL_HEAD --usage-file FRESH_USAGE_JSON
```

Supervisor chooses fixed fresh run names `20261108_fog_reward_control41`, `neutral41`, `control42`, `neutral42` under `experiments/runs`; no restart/resume/alternate attempt prefix. Default STOP `/tmp/sherlock-fog-reward-20261108/STOP`. No CLI smoke option: root's separate known complete reference traces supply mechanism proof. Internal inherited short-smoke schedule support cannot receive a production supervisor launch/receipt.

## Audit and lifecycle details

- Real final `_sap_unknown` is mandatory. Marked UIDs must exist in the reward transition and final SAP action dictionary, with unchanged numeric hit estimate0. No inference of Fog origin from legacy zero-hit counters.
- On every actual reward call, both formulas are evaluated on identical inputs; delta must be precisely +w_sap_hit for marked final SAPs with shaping, else0. Actual rewards must equal the configured formula. False retains the historic five-argument call. Numeric hits, estimated misses/positive hits, unknown counts, reward mass and actual reward totals remain recorded.
- Actual replay insertion reward values are checked against the audited reward values in the actual UID insertion order. Final action-to-replay mapping reuses `final_rescue_train.action_audit`.
- `holder_rollout.exact_digest` hashes every full simulator state/reset/step result and both-side actions, plus policy observations/features/actions/masks/explicit provenance and replay insertions without reward. Complete logical replay metadata/content hash excludes only reward.
- A frozen prefill bundle contains all40 raw rows plus initial/prefill learner identities, entry and replay hash. Bundle/rows/audit/progress are persisted before the prefill proof readiness marker. Supervisor independently recomputes chronology/summary and compares paired trajectory, replay and both counterfactual reward hashes, unknown counts/mass and unchanged Q/target/Adam. Neither arm starts diagnostics or gradients until matched proof exists. A mismatch records STOP, retains partial files, stops only registered children and prevents seed42 starts.
- Shared extraction/learner checks, isolated V14 validation, atomic output/protected-path checks, source identity, process locks/spawn/shutdown and quota parser are reused from existing scripts. No old constants or files are patched. Only finetune module hooks/constants, the new variant, process argv, reward callable, local environment/agent wrappers and signal handlers are scoped to the worker and restored in finally.
- Validation uses normalized original V14 cfg (new flagFalse), existing RNG restoration and learning identity checks. Per-game worker guards and supervisor10-second polling check fresh resources and frozen inputs. SIGINT/SIGHUP/SIGTERM are observed at completed-game boundaries. Wake PID/PGID/owner/command and each child PID/PGID/owner/command are saved. Partial checkpoint is separately named and never gets an eligible receipt.
- Final receipt checks bind config/inputs to preparation, all raw fixed schedules, reward/replay counters, training CSV chronology and finite loss, expected60000 updates, changed finite Q/target/Adam, saved checkpoint hash and actual reload proof. Pair effect remains descriptive.

## Actual checks

TDD: initial test invocation with generic `python` could not run because this shell has no `python` command. Using project interpreter then failed collection as expected because the new study module did not exist. Subsequent focused checks:32 passed,38 passed; final run:

```
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest tests/test_fog_reward_study.py -q --disable-warnings --maxfail=1
40 passed in 1.86s
```

Tests cover fixed schedules/config-only flag differences, bad arms, enabled/disabled/zero-weight/no-shaping arithmetic, explicit provenance violations, fail-closed arithmetic/restoration, actual replay reward corruption, replay-without-reward hashes, pair proof errors, fresh quota/100% rejection, foreign process filtering, frozen input changes, AC, partial receipt rejection, exclusive identical four-arm preparation/tampering, worker guard while finetune argv is installed, synthetic trajectory wrappers/restoration, frozen raw prefill chronology tampering, and pair failure/no-next-start shutdown.

## Open integration concerns / limits

No environment or actual model game was constructed by this task. Root should exercise the new reward/trajectory wrappers in its authorized known complete traces before study launch; real Lux state/reset/step serialization and real303-step reward/replay counters remain runtime verification. Root's final independent review/integration checks are pending. The actual60000-update/finiteness/reload and per-pair trajectory identity gates cannot be claimed before real training finishes. Quota receipt freshness follows the existing strict parser's1200-second limit; an external actual-usage observer must refresh it. No source edits/tests while training/evaluation is running.
