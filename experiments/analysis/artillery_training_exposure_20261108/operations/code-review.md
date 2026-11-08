# Independent artillery offline code/method review

2026-11-08. **PASS — no blocking findings in the reviewed implementation.** Scope is only the two fixed archived targeting traces and helper exposure, not games, full policy reproduction or training effectiveness.

Exact reviewed files:

- `scripts/artillery_training_exposure.py`: `e82533145e3cd85a2633082b2db468ed2030760e497f886f425267387e1ccd1b`.
- `tests/test_artillery_training_exposure.py`: `a852fa1a64b20836dabe4818e922f70eefeb72f5a4a84ff3334b52ff571bb49e`.

Read the plan, `/tmp/sherlock-artillery-offline-premises.md`, both files, the current `_artillery_ok` implementation and relevant trace-observer/guard code. No tests, model imports/loads, helper-data execution or games were run by this reviewer; only this review artifact was written. The two synthetic test assertions were inspected, not claimed as independently executed.

The method correctly uses the historical event boolean as evaluation baseline. Only the actual current helper is called in training mode on an isolated SimpleNamespace, with an estimator sentinel that raises if queried. The current helper's `training=True` short-circuit avoids the unrecorded posterior. No evaluation replay, estimated posterior, model/Agent construction or engine call is introduced.

The historical main blob must match the manifest source SHA; its helper AST must equal current helper AST. Manifest completeness/V14 hash, each trace SHA and historical normalized config are checked. Reconstruction includes the helper's actual required position, energy, assignment, first-on-tile, point-map and safety inputs. Event position/energy/target and unchanged SAP arguments are cross-checked against the same-frame public context. The separate premises review supports the post-act point-map/assignment stability assumption; the new script does not claim to independently reproduce hidden historical state.

The callback records pre/post config, estimator sentinel, belief, context and SAP hashes, restores `training=False` in `finally`, rejects nonboolean returns and mutations, and leaves the recorded eval verdict untouched. Exceptions abort rather than inventing answers. Whole-record hashes additionally detect mutations to archived public data or native actions. The synthetic checks cover ordinary return/restoration and callback failure/restoration.

The fixed two files are each required to contain 303 rows and 300 decisions with sequential keys. Every observed helper event is retained; per-trace counts include unique step/UID pairs, all four archived-eval/reconstructed-training verdict combinations and differences. Calls are not silently interpreted as unique final actions. JSONL evidence is hash-bound, outputs use a fresh exclusive directory, and incomplete work is marked failed. Shared source/input/protected-hash, AC, fresh-quota, STOP/signal and process-lock/foreign-job guards are retained. The code does not write protected weights or modify production logic.

Interpretation detail: reconstruction preserves the archived `rules_in_training_all=False` value. `_artillery_ok` never reads that flag, so its training-mode result is numerically identical if the flag were set True for recipe fidelity. This is acceptable for the explicitly helper-only question; it does not establish caller eligibility or final policy behavior under the full training recipe. Historical selection, correlation, absent estimator posterior and absence of action-quality/strength implications are correctly explicit.

Real offline artifact completion and any subsequent independent count audit remain runtime work. No additional traces, games, model loading, rule changes or training comparison are approved by this code review.
