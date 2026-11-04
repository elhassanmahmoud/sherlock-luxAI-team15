# Task 3: Independent reward-training starts

Implemented only `scripts/student_reward_train.py` and its test file. No commits,
training jobs, production games, historical-data rewrites, or subagents.

## Approved adjustment

The original 31/32 and integer 0..1000 proposal conflicts with the unchanged
`finetune.main` admission assertion: its prefill formula must remain below
validation map 500000. Root explicitly revised the study to starts **27/28** and
strict integer **0..29**, default 29. Neither bools nor floats are accepted.
Out-of-range seeds fail before an output directory is created. Core finetune
source and the 40 prefill / 160 training / 32 validation budget, offset 3000,
24000 updates and 120600 final environment steps remain unchanged.

## Change and acceptance

- `prepare(..., run_seed=29)` and `prepare --run-seed` record one top-level
  manifest seed, replicated and strictly checked in both arm/local init entries.
- Rollout map seeds and opponent RNG schedules derive from that manifest seed;
  each control/SAP0 pair has identical plans and initial network tensors, with
  exactly the original `w_sap_hit` config difference. Starts 27 and 28 have
  disjoint maps and different opponent schedules.
- `run_arm` closes over the checked manifest seed, admits only that seed in its
  learner-loading hook, forwards it to the real Learners constructor, and passes
  it in finetune's `--seed`. No global seed constant is mutated.
- The existing `prove_initial` checks remain intact: exact source q/target,
  canonical single learner, fresh Adam state, empty replay, original counters,
  expected config, disabled autosave and epsilon .05. Tests additionally verify
  the actual initial agent RNG hashes against NumPy seeds 2700/2800/2900 and
  prove identical initial RNG hashes within each pair.
- Audit and final receipt include the run seed. Receipt verification checks the
  seed type/value and reconstructs the expected complete rollout schedule from
  the prepared manifest, while retaining every previous learning/action proof.
- Seedless legacy prepared manifests are rejected with an explicit message to
  prepare a new directory. They are never rewritten.

## Actual verification

Interpreter: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python`.
One CPU thread via OMP/OPENBLAS/MKL variables and existing PyTorch test setup.

1. New API/seed cases first failed against original code (22 expected failures).
2. Additional strict local-init/audit checks first reproduced four failures,
   including Python's `27.0 == 27` equality accepting a malformed local seed.
3. Final command: `python -m pytest tests/test_student_reward_train.py -q`:
   **48 passed in 19.93 seconds**, retaining all 21 original cases.
4. Coverage includes actual CLI preparation, boundaries, bool/float/string/null
   and range rejection, top-level/arm/local tampering, legacy immutability,
   seed-consistent audit/receipt rejection even with rehashed audit evidence,
   and real finetune orchestration for 29/27/28 with synthetic episode boundaries.
   The latter executes both arms and final receipt/prefill verification; it
   makes no real-game or gradient-learning performance claim.
5. `git diff --check`: clean. Full repository suite intentionally not run under
   Root's explicit instruction; Root handles combined focused integration checks.

## Limits / handoff

- Accepted starts are deliberately 0..29, not the original 0..1000. Any future
  expansion needs a separate reviewed map-range policy in finetune.
- Starts 27/28 need not be historically fresh training maps; this change does
  not claim map freshness or a performance benefit. Fresh final diagnosis is
  a separate study requirement.
- Old serialized prepared manifests/receipts should be validated using their
  historic source rather than migrated in place.
- Root owns the shared Arbeitsstand/plan update and integration; no shared
  documentation was edited by this subtask.
