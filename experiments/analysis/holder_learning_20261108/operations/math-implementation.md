# Task A report — completed implementation, root integration review pending

Scope: only `scripts/holder_learning.py`, `tests/test_holder_learning.py`, and this report. No commits, subagents, model/checkpoint loads, historical labels/results, actual games, or experiment runs. Synthetic fixtures were fitted only in focused unit tests. Root owns shared documentation, protocol, integration, and broader verification.

## Delivered API

- `FEATURE_NAMES`: sixteen ordered, descriptive names from the exact fixed spec.
- `feature_vector(candidate)`: float64 length16, only candidate public/uid/proposal/q/mask inputs. Public arrays may be live NumPy arrays or recorded JSON lists. Empty visible-enemy sets supported. Illegal q entries must be None, legal entries finite, both STAY and move legal. Candidate's 79-vector and every diagnostic/hidden field are ignored.
- `fit_head(rows, *, provenance)`: returns `(head, training_report)`; raises `InsufficientTrainingData` on the fixed96/12/12/6 minima. Rows retain all zero/negative labels. Equal represented-map weights include both sides, training-only weighted population normalization, scale1 below1e-6, standardized clipping[-5,5], exactly ridge0.1 and unpenalized intercept.
- `validate_head(head)`: detached JSON-safe validated copy; exact schema keys, features, fixed policy constants, positive scales, finite scalar/vector values, baseline and exact JSON provenance required.
- `predict_gain(head, candidate)`: float points gain, caller chooses HOLD only strictly>1.0.
- `validation_report(head, rows, validation_seeds)`: frozen head, exactly eight map identities, full recorded pairs, fixed opportunity/map/selection/positive-proxy/bootstrap gates. No mutation/refit. NumPy default_rng(0),5000 whole-map samples, lower2.5th percentile. All eight gains present, including zero-pair maps.

JSON schema keys: `schema_version=1`, `feature_version='holder_public_v1'`, `feature_names`, `eligibility_version='holder_eligibility_v1'`, `cadence={'version':'scored_opportunities_v1','max_opportunities':8,'min_step_gap':12,'reset':'new_game'}`, `horizon=12`, `mean`, `scale`, `coefficients`, `intercept`, `ridge_alpha=0.1`, `threshold=1.0`, `baseline_sha256`, `provenance`.

Provenance requires `baseline_sha256` equal to the known full V14 SHA; all supplied exact JSON keys/values retained without renaming. Caller binds and verifies `source_identity`, `training_manifest_sha256`, `training_artifacts` and any further exact artifact/source hashes. Numeric dictionary keys and non-JSON objects are rejected rather than silently converted.

Report fields communicated to TaskB/root: `pairs`, `represented_maps`, `selected`, `selected_maps`, `selected_positive`, `selected_zero`, `selected_negative`, `total_selected_gain`, `selected_mean_gain` (None if none), `map_gains=[{seed,gain}]`, `mean_map_gain`, `bootstrap_lower_025`, `weighted_mse`, `unweighted_mse`, `gates`, `passed`. Validation weighted MSE balances represented maps, while all eight maps always enter gain/bootstrap; empty validation has None MSE, eight zero gains and failed gates.

## Actually executed verification

- Test-first: missing module import observed, then empty module yielded40 expected missing-API failures before implementation.
- Initial implementation39/40 passed; corrected one invalid test fixture that unintentionally had positive labels in only one map, as the production gate correctly rejected it. All40 then passed.
- Added strict malformed-head/provenance checks: observed two expected failures (float cadence integer accepted; numeric provenance keys silently converted); implemented strict checks; all57 passed.
- Added exact positive gate-boundary and small population-std coverage. Final focused command `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest tests/test_holder_learning.py -q`: **60 passed in0.36s**.
- `git diff --check -- scripts/holder_learning.py tests/test_holder_learning.py`: no output; these new files remain untracked until root stages them.

Tests cover exact hand-derived sixteen-feature values; allowed clipping only; zero-q span; empty/negative/unarmed/diagonal/adjacent enemies; canonical side/UID independence and hidden fields; legal-q None; map density weighting; ridge analytic solution/intercept; training-only normalization and zero/negative retention; insufficient-data and exact boundary gates; zero head; standardized clipping; malformed schema/nonfinite/boolean/cadence/baseline/JSON provenance; threshold equality; all-eight-map zero gains; selected sign counts; represented-map versus row MSE; each validation gate and no head mutation.

## Limits / outstanding

Root must integrate and independently review with TaskB. No full repository suite run here, per root's focused-tests-only scope; no runtime game, strength, portability or live-candidate identity claim. Cadence enforcement, source/artifact authenticity, complete-pair verification, split binding and frozen-head receipt belong to TaskB/caller. These pure APIs intentionally do not read files or enforce study seed ranges (the collector/CLI does). No thresholds, model variants, data subsets, or post-validation tuning added.
