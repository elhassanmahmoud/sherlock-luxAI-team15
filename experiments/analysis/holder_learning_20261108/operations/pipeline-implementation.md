# Task B implementation report

Implemented only the assigned collector/policy files plus `tests/test_holder_learning_study.py`. No games, model evaluation/training, production edits, protected assets, documentation edits, or commits performed by this task.

## Interfaces

- `DiagnosticAgent(..., head=None)` preserves the original no-head path. Supplied heads pass Task A `validate_head`. The inference hook remains directly in `_rule_override`, with its original `Agent_x._act` caller/row check. The recorded and scored candidate share exactly the same construction. A first eligible UID consumes one of eight opportunities and starts the twelve-step cooldown immediately, including rejection. `new_game` alone resets those counters. The ordinary rules still process an accepted STAY. Forced intervention plus a head is rejected.
- `holder_rollout_probe.run_collection(...)` contains the previous audited collector loop. `run_probe` still validates exactly the original twelve keys and selects the same two smoke keys/one pair for its historical smoke option. Original default result and feasibility fields remain unchanged. Existing Guard, usage/AC/STOP/source freeze, protected-input binding, resource lock and full-game passivity checks remain active.
- `holder_learning_study.validate_plan(path, split)` accepts exactly the prepared schema and train6500000..6500023/validation6501000..6501007, both ordered sides, fixed protocols/cadence/baseline.
- `read_collection(manifest, plan, split)` keeps every complete pair, including identical-action zero labels. It verifies bound input/artifact hashes, all fixed keys and complete game counts, 303 stored frames per execution, frame/action/trajectory hashes and chains, reference/collector whole-trajectory identity and recomputed passivity, live baseline frames and receipts, branch point sums/labels, first-pair repeat proof, cadence/budget, and actual counters.
- `fit(...)` passes Task A `fit_head` the complete training rows and provenance containing baseline_sha256/source_identity/training_manifest_sha256/training_artifacts/plan_sha256. It writes exclusive `head.json`, `fit_report.json`, and `receipt.json`; insufficient data leaves a failed-gate receipt and propagates the stop.
- `read_fit_receipt(...)` checks complete fit, same exact source/HEAD, head/report hashes, current training manifest/artifacts and head provenance. `validate(...)` checks this before opening validation labels, requires the validation manifest's receipt/head/training bindings, calls only `validation_report`, and writes one exclusive report.
- `neutral_proof(...)` prepares the exact known831006/player_1 and831043/player_0 pairs (four actual executions when Root runs it). `max_pairs=0` disables all diagnostic branching. A validated zero head uses the real inference hook. Exact full trajectories must equal original V14, and each neutral execution must score at least one opportunity so this proof cannot pass vacuously. Operational opportunity counts appear only on the instrumented result; every original reference field remains part of passivity equality.

## Exact CLI sequence for Root

All commands below use the same Python path, same actual frozen HEAD, same source files, same bound plan, and exclusive new output paths. Replace HEAD with the final reviewed commit hash; usage evidence and STOP paths must be valid at each collection. These are prepared commands, not executed game runs.

```sh
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m scripts.holder_learning_study neutral-proof --plan experiments/analysis/holder_learning_20261108/plan.json --out experiments/analysis/holder_learning_20261108/neutral_v1 --expected-head HEAD --usage-file experiments/analysis/holder_learning_20261108/operations/usage.json --stop-file experiments/analysis/holder_learning_20261108/operations/STOP
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m scripts.holder_learning_study collect --split train --plan experiments/analysis/holder_learning_20261108/plan.json --out experiments/analysis/holder_learning_20261108/train_v1 --expected-head HEAD --usage-file experiments/analysis/holder_learning_20261108/operations/usage.json --stop-file experiments/analysis/holder_learning_20261108/operations/STOP
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m scripts.holder_learning_study fit --plan experiments/analysis/holder_learning_20261108/plan.json --train-manifest experiments/analysis/holder_learning_20261108/train_v1/manifest.json --out experiments/analysis/holder_learning_20261108/fit_v1 --expected-head HEAD
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m scripts.holder_learning_study collect --split validation --plan experiments/analysis/holder_learning_20261108/plan.json --fit-receipt experiments/analysis/holder_learning_20261108/fit_v1/receipt.json --out experiments/analysis/holder_learning_20261108/validation_v1 --expected-head HEAD --usage-file experiments/analysis/holder_learning_20261108/operations/usage.json --stop-file experiments/analysis/holder_learning_20261108/operations/STOP
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m scripts.holder_learning_study validate --plan experiments/analysis/holder_learning_20261108/plan.json --validation-manifest experiments/analysis/holder_learning_20261108/validation_v1/manifest.json --fit-receipt experiments/analysis/holder_learning_20261108/fit_v1/receipt.json --out experiments/analysis/holder_learning_20261108/report_v1 --expected-head HEAD
```

The historical `python -m scripts.holder_rollout_probe` CLI and its required arguments remain supported. No arbitrary seeds, free feature sets, thresholds, hyperparameters, validation refit, or promotion command was added.

## Actual focused verification

- TDD red run observed missing cadence/caller/plan/receipt features; later red run caught missing neutral provenance baseline; later red run demonstrated that an unexercised neutral hook was previously accepted.
- Final targeted command: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest -q tests/test_holder_learning_study.py tests/test_holder_rollout.py`: **42 passed in2.13s** (16 new study/policy tests plus26 preserved probe tests).
- Earlier combined integration check with Task A:100 passed in2.14s (before the final two additional B receipt/nonvacuity tests). Root owns the final combined run.
- `git diff --check`: no output, successful. `python -m scripts.holder_learning_study --help`: successful with exactly collect/fit/validate/neutral-proof subcommands.
- No full suite per task instruction. No actual data/labels opened, no actual fit, no games/model runs. Freshness audit, independent review, final combined checks, frozen commit and actual neutral/collection runs remain Root's work.
