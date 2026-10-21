# Stage-one implementation handoff

Scope: only the pre-registered influence probe in `docs/superpowers/plans/2026-10-21-v4-target-pilot.md`. No production agent changes, training, learner, environment continuation branches, new games, or policy replacement were performed by the implementer.

## Changes

- `experiments/analysis/v4_target_pilot_20261021/influence.py`: legal fixed-window target selection, bounded BFS with UP/RIGHT/DOWN/LEFT route ties, fresh dynamic agent clones, rebuilt assigned-target features and actual final `act` calls, unchanged live baseline return, exact complete-action and legal-observation traces, global Python/NumPy/Torch CPU RNG restoration in `finally`, and live dynamic-state/input digests on success and error paths.
- Shared objects are limited to the Q/target/ensemble networks, optimizer and unused empty buffer. All networks must already be in evaluation mode. The remaining agent graph is copied together, retaining belief/feature/cache/context aliases while separating caches, paths and the local Generator.
- `run_influence.py`: exactly two maps (524000/524001), both sides, control plus passive-shadow game: eight full games when Root elects to run it. Thirty-minute real-time alarm; fresh output directory; pre-write 128MiB cap; all protected V3 and old-release files in both primary and worktree checked before/after, including exceptions. Input checkpoint must exactly match the protected V3 hash.
- The comparison rejects every difference in complete action arrays, action dtype/shape hashes, legal incoming-observation hashes for both players, or summary fields other than `secs`. Eight scheduled states must be present in each of four shadow games. At least eight of 32 states must permit a changed complete array. Alternative arrays are deduplicated exactly. Other-unit changes are explicitly listed in each record; sequential shared SAP/fog/ram processing in ordinary `act` can propagate a real selected-unit change.
- Module docstrings document the invocation and explain that no learner or simulator forks belong in this stage. No separate README was created because Root owns experiment documentation.

## Actual RED / GREEN evidence

Shared interpreter: `../sherlock-luxAI-team15/.venv/bin/python` from the worktree root.

- Wrote the focused tests first. The corrected RED run produced **16 failed** because the new helper module did not exist (3.47s). The initial test pass exposed a nonexistent fixture cache-invalidation method; this fixture typo was corrected before the recorded RED run.
- After the helper implementation, two fixture expectations were corrected using existing geometry/data: Lux's antidiagonal reflection maps LEFT to DOWN for player_1, and the failure policy must inspect the selected first unit rather than the unrelated second unit. Both-side ordinary-act/state/RNG checks then passed.
- Wrote runner bounds/deadline/output tests before its implementation: **3 failed, 17 passed** (3.16s), all three failures due to the missing runner module.
- Final focused run: **24 passed in 3.32s**. Includes occupied zero-energy slots, assigned/blocked/unreachable targets, six-step boundary and route/UID ties, true cache/graph aliases and shared ensemble members, rebuilt-feature action changes on both sides, actual `pt_walk` and late `contest_sap` overrides, distinct complete-array counting, RNG/live/observation cleanup after a deliberately failing final network forward, fixed scheduling, full trace/non-time-summary comparisons, protected-file mutation rejection, fresh-output refusal, data cap, and real signal deadline cleanup.
- CLI `--help` exited 0; `git diff --check` exited 0. No eight-game probe or other games were executed. The full suite was not run, per Root's explicit resource/scope allocation. No reviewers were spawned.

## Root invocation after review

```bash
../sherlock-luxAI-team15/.venv/bin/python -m experiments.analysis.v4_target_pilot_20261021.run_influence \
  --weights agents/sherlock/weights/agent_p0.pth \
  --out experiments/analysis/v4_target_pilot_20261021/run_01
```

The destination must not exist. Output contains the initial protected hashes, each complete control/shadow trace and scheduled-state choices/actions, final gate, final protected hashes, and failure information if collection stops. Source freezing and the independent review are Root-owned. A passing influence result only permits the separate isolation stage; this code does not implement or authorize learning, rollout labels, or playing strength claims.

## Limits / remaining verification

The focused tests run real Sherlock `act`, belief, context, features, masks and rules with small deterministic test policies, without an engine game. Real protected 18-network checkpoint and eight-game control reproduction remain for Root's reviewed run. The legal target path uses the existing belief's passable raster; no hidden environment state or future opponent actions enter selection/shadow helpers. The helper deliberately rejects no-belief/CNN/joint/training/nonempty-buffer configurations. Global JAX state is outside this stage because no shadow calls an environment. Shadows never call update, save, opponents, or reset/render.
