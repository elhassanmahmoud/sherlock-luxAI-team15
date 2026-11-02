# Task 2 independent review — 950cb17

**Verdict: CHANGES REQUESTED — one P2 provenance/fail-closed issue.** No agent-behavior/passivity defect found in the inspected observer paths. Review includes spec compliance and code quality against the current binding schema, including Root's productive-holder and read-only caller-action clarifications. No implementation edits, commits, existing test reruns, model jobs or new games.

## Required finding

### [P2] Recheck all pinned input identities before reporting a complete run

**Location:** `scripts/targeting_probe.py:636–638` (pinning at `598–603`).

`run_probe` records `keys_sha256`, the original baseline CSV SHA and Git HEAD, but its final integrity gate rechecks only weights and its selected source-file list. The key document, baseline CSV and HEAD can therefore differ from their recorded identities while the manifest is still marked `complete`. That breaks the fixed-input/provenance contract even when the game action/output comparisons themselves pass: baseline rows were loaded into memory before play, so later on-disk drift is invisible to those comparisons.

**Concrete pure counterexample:** I executed the unchanged production `_sha`, `_baseline` and `run_probe` functions with a disposable baseline/key file and a replacement game boundary that performs no games. During the observed-call boundary it changed both disposable key and baseline files. All metadata/passivity/reproduction comparisons stayed true and the actual production function returned `status="complete"` despite both SHA mismatches. No Torch/Lux import, model construction, forward, environment reset or real game occurred. Evidence: `/tmp/sherlock-continue-20261102/task2-provenance-counterexample.json`.

**Required correction:** Include key-file SHA, baseline CSV SHA and Git HEAD in the integrity check before success; preferably check the same frozen input set before each pair as well, so drift stops further replays. Add a small temporary-file regression around the existing no-game boundary for key/CSV mutation and changed HEAD. A mismatch must leave `failed`, never `complete`. Root's planned outer guard is valuable for full runtime/engine coverage, but does not remove this standalone CLI defect.

## Spec/code-quality findings without a blocker

- Commit scope is exactly the new observer and focused tests; no agent, runner, weights or historical-data change. `classify_frame` builds its results from copied public values, and optional truth enters only the separate posthoc object.
- Q hooks detach/clone existing outputs before the agent's in-place mask. Recalculated ensemble aggregation uses the same Torch stack/mean order and float32; no extra forward, act, observe, RNG or `_enemy_stationary` call was found. Selected context/argument copying avoids full agent/Belief copies.
- All eight wrappers call the captured original once; mutable arguments are copied before/after. Caller action is read only from this agent's exact `_act` code frame with matching unit, and frames are released. Hook/wrapper cleanup also covers exceptions; unobserved inline transitions stay unresolved.
- Productive holder uses the lowest nonnegative-energy ID, with legacy `first_on_tile`, masked/living stack size and living stackers distinguished. BFS/allowed-progress, negative energy, player-1 directions/sap deltas, real-sensor energy freshness and match-reset free durations match the requested distinctions. Two-owner swaps keep the selected own-point target set, require all four reachable/allowed paths, reject incompatible costs and cap pair checks at 120.
- `_play` uses fresh Solution state through the existing opponent factory, public policy observations, native action-byte digests for both teams and v2 endpoint accounting. Truth is read only after both actions were chosen and written separately after transition. Missing/cache/Q failures cannot pass the current completeness gate.

## Evidence/admission boundary

The provided 34-focused/728+14-full-suite evidence was not rerun. The two real integration games precede the last pure living-stacker refinement, as the implementation report correctly states; they are not final-source acceptance of all keys. After the provenance fix, Root still needs its pinned V14/36-network preflight, independent review of the corrected diff and the exact 12 plain/traced pairs (24 games), all actions/results/303-step/v2/frame keys checked. No new policy or strength admission follows from this code review.
