# Independent ensemble-dimensions review — 21 October 2026

Reviewed commit `0867de4e75ebd99be6f5673b174e7eeff00e164b` against `baef7a8` in `/Users/moayedshawesh/Desktop/KI/sherlock-ensemble-validation`.

**Verdict: ready for root integration and the planned combined-source suite. No blocking or important defect found in this scoped fix.** This is a code/format compatibility review, not evidence of playing-strength improvement or authorization to replace V3.

## Requirements and implementation

- The builder now unconditionally replaces `ensemble_dims` with the complete ordered list. Its order is the existing base extras followed by each appended source's main net and extras, matching the constructed `ensemble` list exactly (`scripts/build_ensemble.py:40–62`). This closes the stale homogeneous-list truncation bug.
- A single shared validator checks positive integral `feature_dim`, explicit dimension container/type, exact extra-net count, non-bool positive integer entries no larger than the main input, and the actual `body.0.weight` input width for the main and every extra net (`agents/sherlock/model.py:19–47`). There is no coercion of floats, strings, or booleans into accepted dimensions.
- The loader validates before loading checkpoint weights and before the `zip`, so malformed dimensions cannot produce the old successful load with silently omitted members (`agents/sherlock/main.py:688–707`).
- Every builder source is validated before directory creation or saving. Dimension errors in either the base or appended source use the existing CLI failure style. Inspection also confirms an existing output is untouched on these validation failures, although the new regression directly asserts only the missing-output case.
- Missing, `None`, and empty-list metadata retain homogeneous fallback, with widths checked afterward. Empty ensembles and the loader's old raw-state-dict branch remain supported. Tuples are also accepted as explicit sequences; this does not weaken entry/count checks.
- Valid 101/79 flattening preserves all tensors and action inference. The `--mixed` requirement for adding a smaller-input source remains in place. The existing actual-feature mixed-network test also checks sliced-input numerical averaging; its author-reported pass is part of the 32-test run, not independently rerun here.

## Quality and evidence

The change is narrow: six requested files, 316 additions and six deletions, with one shared validation function rather than divergent loader/builder rules. The regressions exercise real save/build/load/rebuild operations, exact per-tensor identity, observable actions, legacy metadata, malformed dimensions, and invalid tensor widths. The German note distinguishes technical validation from strength evidence and correctly leaves the combined suite/review to root. No false compatibility claim was found for the format described.

Independent checks actually performed:

```text
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest -q tests/test_ensemble_dimensions.py
28 passed in 3.24s

git diff --check baef7a8 0867de4e75ebd99be6f5673b174e7eeff00e164b
passed (no output)

git status --short
clean (no output)
```

The focused run was announced to root and the compute slot was released immediately afterward. No full suite, engine games, checkpoint installation, source edits, commits, pushes, or subagents were used by this reviewer.

Both protected files still hash to the documented V3 SHA-256:

```text
aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935  agents/sherlock/weights/agent_p0.pth
aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935  agents/sherlock/weights/agent_p1.pth
```

## Findings

- Critical: none.
- Important: none.
- Minor: no production correction requested. An existing-output sentinel assertion could strengthen the builder rejection test, but control-flow inspection already shows no write before all validations complete; this is optional coverage, not a merge condition.

## Considered but outside this narrow review

- General checkpoint-schema validation (e.g. `ensemble=None`, absent required builder keys), hidden/output layer compatibility, target/optimizer corruption, and finite-value validation: existing broader format responsibilities; this change promises input-dimension validation for DQN main/extra networks.
- Generic overwrite/symlink protection and atomic output replacement: pre-existing builder behavior; no output was written to a protected path during this review.
- Standalone `python scripts/build_ensemble.py` invocation: the documented and repository pipeline invocation is `python -m scripts.build_ensemble`; direct-script support is not claimed.
- CNN/PPO behavior and game-strength comparison: unrelated code paths and explicitly outside the assigned execution scope. Root owns the combined integration suite and any later reproduction.

No source modification is required from this review before integration. V3 must remain installed until the separately required proof supports a replacement.

## Follow-up fixture review — commit `3dcf090`

**Verdict: approved for integration; no blocker or weakened assertion found.** Read-only review of `0867de4..3dcf090b380918175c5d1d01262ddbd7a717d18f`, plus the one-line working-tree change in `/Users/moayedshawesh/Desktop/KI/sherlock-v4-joint/tests/test_v4_target_influence.py`.

- `test_checkpoint_load_and_probe_fail_closed` still verifies a valid loaded checkpoint first, then independently checks changed tensor weights, changed effective configuration, and incompatible architecture. The config/architecture checks use the untouched original agent, so the preceding weight corruption cannot mask their failures. It additionally asserts the real loader's early input-width exception, correctly replacing the obsolete expectation that this malformed checkpoint returns an untrained agent.
- The curriculum fixture adds only a finite `(1, 79)` input-weight tensor to each inert network. Its distinct `w` markers remain 0–20, preserving count/order/uniqueness checks. Existing provenance hashes are recomputed from the completed fixture exactly as before; source binding, protected paths, positive/negative gates, duplicate/nonfinite/shape/config/dimension rejection, and real owned-child build assertions are unchanged. Production validator, builder, audit, and gate logic are untouched.
- `AssignedDxPolicy` gains only `self.feat_dim = FEATURE_DIM`, matching the 79-feature fixture and the production extra-network slicing contract. The affected aliasing test actually places a copy of this policy in `extra_q`; forward behavior, RNG consumption, shared-module identity, dynamic-state isolation, and all assertions remain unchanged.

`git diff --check` passed for both reviewed diffs. Commit `3dcf090` changes only the two test files and two documentation files; the separate V4 diff is exactly one added fixture attribute. No model imports, tests, games, production edits, or weight writes were performed during this follow-up review. The reported **2 RED failures / 98 GREEN passes** are implementer evidence, not independently rerun here; root owns the combined-source suite. Unrelated untracked artillery preparation files were left untouched and are outside this review.
