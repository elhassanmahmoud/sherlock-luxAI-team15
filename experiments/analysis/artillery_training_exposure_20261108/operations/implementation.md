# Artillery training exposure — implementation, 08.11.2026

Final scope is **offline only**, following root's updated instruction and `/tmp/sherlock-artillery-training-gap-review.md`. The initial two-game wrapper was replaced before any execution. No games, model construction/forwards, training, weight changes, actual archived-helper diagnosis, commits or pushes.

Only new files: `scripts/artillery_training_exposure.py` and `tests/test_artillery_training_exposure.py`.

CLI:

```
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B -m scripts.artillery_training_exposure --expected-head FULL_CURRENT_HEAD --usage-file ACTUAL_FRESH_USAGE_JSON
```

Fixed inputs: `experiments/analysis/continuation_20261102/targeting/manifest.json` and only `831006_player_1.jsonl.gz` / `831043_player_0.jsonl.gz`. New exclusive output: `experiments/analysis/artillery_training_exposure_20261108/run_v1`; no resume/overwrite. Canonical system-temp STOP is `/private/tmp/sherlock-artillery-training-exposure-20261108/STOP` on this Mac.

The adapter verifies trace hashes against the completed V14 manifest, the archived main.py Git blob against its recorded SHA, and exact `_artillery_ok` AST equality with current source. Full-agent byte identity is reported separately and is not invented. Each saved public configuration must normalize exactly to the corresponding historical observed-game configuration, with all helper config fields present.

For each recorded artillery event it reconstructs only the saved helper context, checks event-time position/energy/target against public fields, requires a genuine archived boolean return and unchanged archived arguments, then calls the **training helper only** on a SimpleNamespace. The archived eval boolean is never recomputed. An unavailable-estimator sentinel raises if any posterior read is attempted. Training=True is temporary; finally restores False and checks hashes of config, estimator sentinel, belief, context and SAP arguments. Countercall exceptions propagate/fail closed. The returned answer is always the archived eval boolean on successful callbacks; no result is fed into actions.

Per-call JSONL includes step/UID/event order/estimated hits, archived eval and recomputed training booleans, configured training min hits, training dropoff0, explicit unavailable eval dropoff, before/after hashes. Per-trace reports distinguish helper-call counts from unique(step,UID), differing calls/unique pairs, and four eval/training combinations `false_false`, `false_true`, `true_false`, `true_true`. Full records/actions are fingerprinted before/after processing. Only completeness of303stored rows/300decision rows is checked; there is no game replay, frame reproduction or hidden-engine-state claim.

Existing `resource_lock`, `probe.Guard`, source/HEAD/full input/protected V14/ZIP hashes, AC, actual fresh allowed quota strictly<100, STOP/signals and foreign model/test checks are reused. PID/PGID/command recorded; one process, no child worker. Outcomes remain descriptive helper exposure on these selected archived contexts, with no final-action, quality, learning, strength or promotion claim.

Tests:

```
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest tests/test_artillery_training_exposure.py -q --disable-warnings --maxfail=1
2 passed in 2.38s
```

Initial TDD collection failed as expected before the new module existed. The two final synthetic tests verify archived-answer preservation with training-only invocation and unchanged state, plus exception propagation/training restoration/context integrity. The four requested combination sums were added afterward as direct sums over existing rows; root explicitly requested no new test wave for that aggregation. No test process is active. Actual source/archive compatibility and the public-context/event-time premise remain for root's independent review and authorized offline execution. Implementation is in writing rest.
