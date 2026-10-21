# Independent PPO seed and bounded-launcher review

Review date: 21 October 2026. Reviewer inspected the working tree at
`/Users/moayedshawesh/Desktop/KI/sherlock-v4-joint`. Scope: `scripts/ppo_train.py`,
`tests/test_ppo_seeding.py`, their direct callers, and
`.superpowers/sdd/2026-10-21-cnn3-continuation/job_launcher.py`. No model imports,
pytest, simulator games, training, commits, or source edits were performed.
Only this review document was written. AGENTS, CLAUDE, the latest handoff, and
the bounded continuation plan were read.

## Seed change: approved

The production diff is limited to the requested Torch seeding:

- `cmd_ppo` seeds with `args.seed` before `PPOAgent` construction, optional
  detached critic construction, and update permutations. No intervening code
  reseeds Torch. Inspection of the installed Torch implementation confirms
  `manual_seed` seeds CPU and MPS, including the device used by `ppo_update`.
- `play_recorded` seeds with `2 * int(seed) + side_id` after per-game resets and
  before environment reset/action selection. The two legal sides and adjacent
  positive game seeds have distinct mappings. Python and NumPy seed expressions
  are unchanged.
- The learner uses a spawned process pool; rollout reseeding therefore does
  not reset the learner's advancing Torch stream. Existing default/Solution
  opponents do not introduce competing Torch draws. The teacher uses frozen
  inference. No architecture, reward, checkpoint, opponent schedule, protected
  weight, or public interface change was found.

The eight tests exercise actual Categorical draws, actual initialized module
parameters, state loading for the new critic path, and actual permutations at
the update boundary. Different incoming RNG states, same/different run seeds,
both sides, adjacent game seeds, both teacher modes, and NumPy's large-seed
modulo behavior are covered. These tests are meaningful for the narrow seed
placement contract even though the simulator and full optimizer update are
stubbed. The implementer's recorded RED 6-fail/2-pass and GREEN 8-pass results
were read but not independently executed; root owns the integration suite.

Nonblocking note: the test fixture explicitly restores only CPU Torch RNG
(`fork_rng(devices=[])`). `manual_seed` also changes MPS RNG on this machine, so
the fixture does not restore every device's RNG. The implementation report
accurately limits its restoration claim to CPU. Preserving the available
accelerator state would improve test isolation; no production conflict follows
from this test-only limitation.

## Launcher: corrections verified, static approval

Two findings were sent to root and corrected before this final review:

1. **Deadline polling (resolved)** — the initial version waited a fixed 30 seconds. A job
   can continue past its 90-minute/absolute limit until the next poll. Cap the
   wait by the remaining minimum of the job and absolute deadline and recheck
   time after potentially slow hash/memory checks. The 300-second admission
   reserve protects the external deadline but does not itself enforce the
   stated per-job limit.
   The revised code defines `stop_at` with three seconds for cleanup, bounds
   every wait by the remaining interval, bounds the memory-pressure command's
   timeout, and rechecks time after input and training checks.
2. **Cleanup disappearance race (resolved)** — the initial version probed the group
   and then send SIGTERM without catching `ProcessLookupError` at the actual
   send. If the last member exits between these calls, cleanup aborts before
   clearing `active` and writing the final state. Catch disappearance when
   sending SIGTERM; ensure final state persistence occurs even if cleanup
   raises. The revised code catches disappearance at the actual SIGTERM call
   and puts final state persistence in an outer `finally`. Root's planned
   fake-child smoke covers success, failure, deadline termination, and group
   cleanup including a ready-confirmed descendant that ignores SIGTERM.

Otherwise the launcher binds HEAD, source hashes, protected weights, and input
hashes before launch and periodically/after return; starts its child in a new
session; targets only that owned process group; records commands/PIDs/errors;
refuses duplicate labels and work after an errored job; applies one-thread
limits; checks first-iteration projection with a 20% margin; checks logged
finite losses; and stops on sustained <=5% reported free-memory pressure.

The execution state did not yet exist during this review, so actual hash-map
coverage and configured limits cannot yet be certified. Root must freeze all
runtime/source/input/protected files and set training to 5,400 seconds and the
predeclared absolute deadline before launch.

## Boundaries explicitly left to root

- Final completeness/tensor validation is outside this launcher's technical
  stop-guard scope. Root explicitly confirmed a mandatory verifier before
  candidate evaluation: iterations 1–10, 24 games each, finite losses,
  preregistered realized opponent mix, iteration-10 finite/changed tensors,
  preserved architecture/config, current/final checkpoint identity, and
  unchanged input/release hashes.
- Statistical gates, seed reservation, strength claims, and experiment
  methodology are assigned to another independent reviewer.
- The full test suite and helper runtime smoke are root-owned to avoid
  concurrent model workloads. Results below are attributed to root; this
  reviewer did not rerun them.

Root subsequently reported the single integration run: **489 passed plus 14
subtests in 82.30 seconds**. This is root-owned execution evidence, not a test
run performed by this reviewer. This reviewer also reran `git diff --check`
for the seed code/tests with exit status zero and reread the entire revised
launcher.

## Final helper recheck after smoke

Read-only inspection of the final helper confirms two additional amendments:

- Projection is frozen on first observed completed iteration(s), includes
  elapsed startup/completed work, and adds first-iteration time times remaining
  iterations with a 20% margin. It is still checked against the fixed job and
  absolute budgets.
- Cleanup calls `process.poll()` before probing the group, reaping the leader.
  If macOS returns EPERM for the probe, a bounded `ps` query checks the actual
  group states. Only an absent group or exclusively zombie members counts as
  no live work; any live member retains the error. Final state persistence
  remains in the outer `finally`.

Read the final saved `launcher_smoke.json`: success has launcher/child exit 0
and verified inputs; failure preserves child exit 3 and removes the process
group in 2.187 seconds; the four-second-budget deadline case records child
exit -15 and a gone group after 1.086 seconds. All are final root-owned smoke
results. The earlier transient null-returncode/zombie failure is superseded
by these final verified records. Root also confirms `active=None` in the
smoke states and a readiness handshake before the TERM-ignoring descendant
failure test.

Read `original_checkpoint_check.json`: PPO60 SHA-256 matches the planned
original, all 32 loaded policy tensors are exact and finite, architecture has
`detach_value=true`, and MPS is available. These are root-produced checks;
this reviewer did not load the checkpoint.

Final verdict: **seed patch and final launcher approved; no remaining code
blocker**. The helper smoke prerequisite is satisfied by the saved evidence.
Actual frozen-state/hash coverage remains a prerequisite before real jobs.
V3 and its backup remain outside all write scope. No additional tests or model
jobs were run during this final review.
