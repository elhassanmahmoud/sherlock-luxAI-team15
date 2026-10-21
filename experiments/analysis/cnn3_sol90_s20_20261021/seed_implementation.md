# PPO Torch seeding — implementation report

Status: DONE (implementation and focused tests; coordinator owns independent review and final integration).

Worktree: `/Users/moayedshawesh/Desktop/KI/sherlock-v4-joint`
Branch: `improvement/v4-joint-20261021`
Starting HEAD: `1255f005255521d8d4a981147fb80064df3e0de4`
Commits created: none, as requested.

## Change and reason

`play_recorded` previously reset Python and NumPy random state, but stochastic
Torch action selection inherited the worker's previous Torch state. It now calls
`torch.manual_seed(2 * int(seed) + (0 if side == "player_0" else 1))` in the same
per-game seeding block, before environment reset and action selection. Python
and NumPy retain their existing seeds, including NumPy's modulo conversion.

`cmd_ppo` now calls `torch.manual_seed(args.seed)` before loading/constructing the
PPO agent. This also precedes optional fresh detached-critic construction and
the learner's minibatch permutations. No new arguments or return values.

Architecture, reward, opponent selection, training schedule, checkpoint format,
and release weights are unchanged. This seeds the existing generators; it is
not a claim of bitwise equality across devices or library versions.

Side handling inspected: `play_recorded`, its callers, and
`Agent_x._set_player/new_game` use `player_0` versus the other side. There is no
existing explicit side validation. Production game generation emits only
`player_0` and `player_1`; this narrow fix preserves that interface rather than
introducing a separate validation change.

## Test coverage

`tests/test_ppo_seeding.py` contains eight parametrized cases:

- Three cases exercise real `torch.distributions.Categorical` samples over 16
  units and four synthetic steps. The literal seed mappings 112/P0 → 224,
  112/P1 → 225, and 113/P0 → 226 produce the expected samples despite different
  incoming Torch states.
- One case checks that paired sides and the adjacent game do not share the
  same Torch action stream.
- Two cases preserve historical Python/NumPy streams on both sides, including
  a seed above 2**32, for both PPO and teacher recording modes.
- Two cases execute `cmd_ppo` with and without a fresh detached critic. Tiny
  modules use real Torch parameter initialization and state loading. Synthetic
  rollout data and a stub update boundary avoid games and optimizer steps;
  the boundary uses real `torch.randperm`. Loaded parameters, saved parameter
  snapshots, and two advancing permutations repeat under the same run seed
  despite different ambient states and differ under another run seed.

The rollout fixture uses a four-step fake environment and a sampling agent.
Recorder finalization is stubbed because the fixture captures actions at the
environment boundary and has no recorded unit trajectories. Recorder creation,
per-step notification, result calculation, side dispatch, and recorder cleanup
still execute through the production function. Tests preserve the incoming
Python, NumPy, and CPU Torch random states.

## TDD evidence

Command before implementation:

```text
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest -q tests/test_ppo_seeding.py
```

Observed RED output:

```text
FFFF..FF                                                                 [100%]
6 failed, 2 passed in 3.38s
```

The three expected-stream cases failed with action-array mismatches; paired
sides/adjacent games returned the same action stream under the same incoming
state; both learner cases failed because loaded parameters differed between
incoming Torch seeds 1 and 2. The two Python/NumPy compatibility cases passed
before the fix. No setup errors or unexpected failures.

Same command after the four added production lines:

```text
........                                                                 [100%]
8 passed in 3.81s
```

Exit code 0, no warnings. `git diff --check` also exited 0.

## Self-review and limits

- Only the two requested production seed sites were changed.
- Tests use real stochastic samples and real parameter initialization, not
  assertions that a mocked `manual_seed` was called.
- Removing either seed, ignoring `args.seed`, moving learner seeding after
  construction, omitting the side offset, or using a colliding seed-plus-side
  mapping is caught by the focused tests.
- No simulator games, training runs, optimizer steps, dependency changes,
  checkpoints, or protected weights were written. Only one test process ran at
  a time, using the shared venv.
- The full project suite was not run here: the dispatch explicitly assigns
  final integration to the coordinator and prohibits games/training for this
  worker. No full-suite result is claimed.
- Unrelated existing experiment artifacts and concurrent coordinator edits
  were left untouched. Shared project handoff documentation remains the
  coordinator's write scope.

## Files written

1. `scripts/ppo_train.py`
2. `tests/test_ppo_seeding.py`
3. `.superpowers/sdd/2026-10-21-ppo-seeding/implementation.md`

Open correctness concerns: none found in self-review. Independent review and
coordinator integration verification remain pending.
