# Task 3 implementation handoff — 04 November 2026

Implemented `scripts/student_anchor_train.py` and `tests/test_student_anchor_train.py`. No production agent or existing trainer was changed; no commits made.

## Architecture and fixed contract

Each public CONTROL/ANCHOR arm owns a separate original `student_reward_train.prepare` directory under `engine/ARM`. Each executes only the original engine **control** arm and original CONTROL config. Both unused engine SAP0 initializations are explicitly excluded. Original 40/160/32 orchestration, action/reward/isolation/initial/prefill/end/reload audits, CSVs, and final-only weight selection remain intact.

A restored `finetune.Learners` wrapper attaches an instance `_learn` adapter to the shared learner. Weight zero directly calls the original bound method without any extra forward, sample, RNG use or loss arithmetic. Weight .1 reproduces the original TD expressions and adds existing `student_action_distill.action_loss` before one backward, original clipping, one Adam step, and the original loss/counter/target-update schedule. The detached teacher targets are fixed tensors; only copied training rows are reachable by the sampler. The existing centered legal MSE/scale² plus teacher→student KL leaves additive value shifts unanchored.

Outer manifests pin A2 SHA, both exact dataset SHA values and all package files, source dependencies/protected files/interpreter, full effective configs, plans, seeds 25/26, weight, batch 256 and update budget 24000. Actual collection load independently confirmed 356415 training rows, 68687 excluded rows and scale 1.4293522257922757.

Per-update sidecars persist actual TD/anchor/total losses, one-step count, observed anchor-output backward-gradient norm, split and sample hashes. All 256 global row indices/update are stored as little-endian uint32 (`samples.u32`, 24576000 bytes for a full ANCHOR arm). Validation recreates every RNG draw from 20261104+seed, checks train-only sampling and loss identities/summaries, and matches 150 actual total losses per game against the original CSV. Prefill replay content is hashed before the first learning-phase replay push; matched-pair checks include this hash plus original configs, rewards, actions and learner/replay/global RNG evidence.

The new-study readiness marker is only `audits/ARM/anchor_receipt.json`. The inner original receipt always means original-engine completion only. New completion validates all evidence and hook restoration **before** atomic publication. Deadline, mutation, malformed audit, occupied/protected/escaped output, failed cleanup or inactive anchor all prevent a new-study success receipt. `validate` is read-only.

## Actual checks

- 27 focused tests pass, using one CPU thread and the specified project Python. They cover exact lambda-zero network/target/Adam/loss/replay-RNG equality across three updates and both DQN branches; actual one-step anchoring and independent sampling; legal centered/teacher-detached gradients; single-action zero; exception restoration; fixed public-arm preparation; input/source/config/init mutation; protected/occupied/input-contained/aliased output guards; real update sidecar reconstruction and corruption rejection; read-only incomplete validation.
-CLI help invoked successfully; `git diff --check` succeeded.
-No full training success or strength claim. The complete new outer success path has not been exercised with a full engine run. Root owns independent review/full relevant checks and admission before the actual four runs.

## Test incident, preserved accurately

While developing the missing audit-alias guard, one regression test was initially missing its fail-fast engine boundary and entered the real engine using a temporary **synthetic** student and tiny temporary dataset fixtures. Interrupted immediately after discovery. Original evidence records 13 completed known-map prefill games: 455000–455005 both sides and 455006 player 0; the next game was interrupted. All 13 recorded learning counters are 0, validation games 0, status incomplete, no completion receipt. Evidence is preserved under `task3_test_incident/` in this handoff directory. No actual A2 model run was launched. The regression now replaces both engine and finetune entrypoints with fail-fast boundaries, and the missing output/input alias guards are implemented. This incident must not be presented as zero game executions; it supplied no learning or study performance evidence.

## Invocation after root admission

```sh
PY=/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python
OMP_NUM_THREADS=1 "$PY" -m scripts.student_anchor_train prepare \
  --student experiments/candidates/action_student_20261104/A2.pth \
  --datasets experiments/analysis/action_student_20261104/collection/r1 experiments/analysis/action_student_20261104/collection/r2 \
  --out experiments/runs/NEW_ANCHOR_SEED25 --run-seed 25
OMP_NUM_THREADS=1 "$PY" -m scripts.student_anchor_train run \
  --prepared experiments/runs/NEW_ANCHOR_SEED25 --arm control --deadline-utc 2026-11-04T21:00:00Z
OMP_NUM_THREADS=1 "$PY" -m scripts.student_anchor_train run \
  --prepared experiments/runs/NEW_ANCHOR_SEED25 --arm anchor --deadline-utc 2026-11-04T21:00:00Z
OMP_NUM_THREADS=1 "$PY" -m scripts.student_anchor_train validate \
  --prepared experiments/runs/NEW_ANCHOR_SEED25 --arm anchor
```

Use a new directory and `--run-seed 26` for the second pair. Deadline above is only an example and must follow root admission/runtime reserve. Root should update shared Arbeitsstand and experiment documentation after integration; this delegated task owns only the two new files and this handoff evidence.

## Fix round 1 — independent review P1

Confirmed the unchanged `finetune.py` producer serializes `round(agent.pop_mean_loss(), 5)`. The outer audit now compares the CSV value to the same five-decimal quantization of the independently reconstructed 150-update mean. Exact equality after that producer quantization rejects material differences without widening unrelated tolerances.

Added a regression exercising the real outer completion validator, status transition, receipt publication and immediate peer validation using explicitly mocked original-engine/preparation/update-evidence boundaries. It supplies 160 realistic rounded means from 24,000 synthetic loss records, verifies restored adapters/constructor before publication, and verifies subsequent validation performs no writes. A second case changes one CSV mean by 0.001 and verifies rejection before any receipt publication and an incomplete status. Both engine entrypoints are replaced; zero games and zero gradient updates are performed by these new cases.

Observed the valid rounded-CSV case fail on the old comparison while the wrong-CSV case rejected as intended. After the narrow fix, all 29 tests in `tests/test_student_anchor_train.py` pass; scoped whitespace validation also passes. No full suite, actual training or additional game execution was run in this fix round. No commits or other source files changed. Root retains ownership of integration and full-run admission.
