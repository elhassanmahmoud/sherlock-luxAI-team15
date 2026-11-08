# Fog comparison implementation — 08.11.2026

Status: implemented; final focused synthetic run **45passed in10.86s**. No real candidate assembly, no model games, no commits/pushes and no existing source/profile/agent/weight changes by this task. Root owns final independent review, actual assembly/admission, freshness audit, publication and bounded execution.

## New files

- `scripts/fog_reward_compare.py`: anchored historical admission, exact exclusive38-network assembly/reload, candidate revalidation, immutable plans, integer half-win screen gates/rank and existing LOCAL_SIX7+3 confirmation gates.
- `scripts/fog_reward_eval.py`: narrow exact state/plan adapter around existing `ensemble_diversity_eval_supervisor.run_queue`, execution receipts and ownership helpers; complete receipt/state/input validation before any statistics, one accepted nominee, canonical STOP, AC and strict fresh quota100.
- `tests/test_fog_reward_compare.py`: synthetic artifacts/results only.

## Fixed paths / contracts

Historical trust anchor: `experiments/analysis/fog_reward_20261108/operations/historical_training_acceptance.json`, SHA256 `8cfea7a7e28cdd010de1ef9693334f028ce8e3b52716805c5d91b6b0ec528e7b`. Training head retained as historical `a3111c3d0aa0aa974298daabe300bba7be157da1`; no invocation or weakening of the active-head training receipt validator.

Every accepted artifact in `files`, every per-arm receipt/raw-file/checkpoint binding and every protected binding is checked. Paths under accepted old root rebase to current root; historical primary protected duplicates rebase to corresponding current protected files. Historical external interpreter/source inventory remains historical metadata; no requirement that the old runtime or HEAD is current. New phase source/runtime freeze is separate.

Exact candidates exclusively in `experiments/candidates/fog_reward_20261108/CONTROL38.pth` and `NEUTRAL38.pth`, plus `admission.json`. Uniform mean of original36 in original order, then final41/final42 of the corresponding arm. Original normalized V14 inference config, flagFalse,79features/6actions. Build checks finite tensors and strict network reload/order/config. Admission independently reloads actual candidate checkpoints and recomputes expected ordered hashes from anchored V14/final arm inputs, rejecting coordinated candidate+admission changes. Build rechecks inputs/source before publishing admission; partial output cannot resume or be overwritten. Admission records build_root and supports rebased accepted input bindings.

Comparison root: `experiments/analysis/fog_comparison_20261108`.

- `plans/selection_panel.json`:7700000–7700019.
- `plans/selection_direct.json`:7700100–7700119.
- `plans/confirmation_panel.json`:7701000–7701039.
- `plans/confirmation_direct.json`:7701100–7701139.
- `plans/selection_jobs.json`:exact11jobs/440games. Confirmation plan is generated only after accepted nomination, exact15jobs/1200games.
- Single-use `selection_launch.json` / `confirmation_launch.json`; no partial adoption, restart, retry or alternate output prefix.
- Canonical default STOP: `Path('/tmp').resolve() / 'sherlock-fog-comparison-20261108' / 'STOP'`. Only system temp is resolved at definition; child symlinks remain rejected. CLI custom STOP also passes strict safe_path.

Both candidates eligible using identical integer half-win gates: panel gain>=4half-win units over80, Solution score/strict wins nonnegative,40/40strict default wins, directhalf-wins>=40. Rank panelhalf-wins, Solutionstrictwins, directhalf-wins, then CONTROL38. N–C paired two-opponent panel bootstrap is descriptive. Confirmation keeps unmodified existing seven gates with explicit LOCAL_SIX, plus existing three safeguards. Whole-map paired bootstrap5000PCG64seed0; no phase pooling.

Selection and optional confirmation deliberately keep **one shared comparison HEAD/source freeze**. Do not commit/change source/HEAD/bound plans/models during either stage or between stages before confirmation admission. Result JSON/Markdown may be written outside bound inputs; any independent audit Python must live outside the repository. There is no added historical selection layer.

## CLI sequence (not executed on real artifacts)

Use project absolute Python `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python` in place of `PY` below.

```
PY -B -m scripts.fog_reward_compare build
PY -B -m scripts.fog_reward_compare prepare-plans
PY -B -m scripts.fog_reward_eval start --jobs experiments/analysis/fog_comparison_20261108/plans/selection_jobs.json --admission experiments/candidates/fog_reward_20261108/admission.json --out experiments/analysis/fog_comparison_20261108/selection --python ABSOLUTE_PYTHON --expected-head FULL_COMPARISON_HEAD --usage-file ACTUAL_FRESH_USAGE_JSON
PY -B -m scripts.fog_reward_eval analyze --jobs experiments/analysis/fog_comparison_20261108/plans/selection_jobs.json --results experiments/analysis/fog_comparison_20261108/selection --out experiments/analysis/fog_comparison_20261108/selection/summary.json
```

If no nominee, stop. Otherwise root's independent selection audit creates a new JSON with at least:

```
{"status":"PASS","profile":"fog_reward_20261108","nominee":"CONTROL38 or NEUTRAL38","summary_sha256":"EXACT_HASH_OF_SELECTION_SUMMARY"}
```

The nominee string above is illustrative: supply exactly one of the two role names. No placeholders in actual audit. Save acceptance outside frozen source inputs; no fixed acceptance filename required.

```
PY -B -m scripts.fog_reward_eval prepare-confirmation --selection-acceptance ACCEPTANCE_JSON
PY -B -m scripts.fog_reward_eval start --phase confirmation --nominee EXACT_NOMINEE --selection-acceptance ACCEPTANCE_JSON --jobs experiments/analysis/fog_comparison_20261108/plans/confirmation_jobs.json --admission experiments/candidates/fog_reward_20261108/admission.json --out experiments/analysis/fog_comparison_20261108/confirmation --python ABSOLUTE_PYTHON --expected-head SAME_FULL_COMPARISON_HEAD --usage-file ACTUAL_FRESH_USAGE_JSON
PY -B -m scripts.fog_reward_eval analyze --phase confirmation --nominee EXACT_NOMINEE --jobs experiments/analysis/fog_comparison_20261108/plans/confirmation_jobs.json --results experiments/analysis/fog_comparison_20261108/confirmation --out experiments/analysis/fog_comparison_20261108/confirmation/summary.json
PY -B -m scripts.fog_reward_eval stop
```

Confirmation build_state stores the accepted selection path, recomputes complete selection and binds its summary/state/provenance/plan/all CSVs/receipts/audit. Confirmation analysis repeats these checks and requires all selection evidence still present in frozen inputs. A forged/incomplete summary, wrong nominee, missing audit, removed binding or attempted second plan/launch fails closed. No automatic promotion.

## Resource/process handling

Existing two-worker queue, job_command (`par_eval --workers1`), source/input guard, CSV validator, quota parser, launch reservations, owned PID/PGID records, graceful group shutdown, signals and wake process handling are reused. Only shared `S.guard` is replaced in-process for run_supervisor and restored finally; no old module constants/profiles are mutated. Wrapper demands AC and adds the newer Fog foreign-process predicate (including probes and tests) with explicit owned group exemptions. Actual usage must remain allowed, finite and strictly<100%,timestamp age0–1200s. STOP and all phase source/input/protected hashes checked by shared queue polling and before launches. No foreign processes are killed.

## Actual tests

TDD first failed import because new compare/eval modules did not yet exist. Initial focused implementation passed10tests. Expanded run reached29passed and a test-only exception mismatch: repeated exclusive confirmation plan correctly raised FileExistsError, while test expected ValueError. Test corrected to accept the explicit exclusive-file failure. Subsequent43tests passed10.84s. Added only the requested third-owned-worker rejection and end-of-assembly archived-source rehash regressions. Final command:

```
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest tests/test_fog_reward_compare.py -q --disable-warnings --maxfail=1
45 passed in 10.86s
```

Coverage: half-win boundary/rank/tie/no nominee, completeness/strict-win consistency, original profile immutability, exact440/1200 roles/seeds/counts (including boolean worker rejection), finite strict synthetic38-network build/reload/order/config, accepted hash/raw/receipt/checkpoint/inventory corruption, checkout rebasing without old runtime, coordinated actual checkpoint+admission tampering, full synthetic CSV/execution-receipt matrices and complete nomination-to-confirmation, missing/extra/duplicate/tampered rows/files/source/plan/receipt/commands/state, no eligible confirmation/no second plan, original7+3gates/80strict default wins, frozen selection binding deletion, STOP/AC/quota, foreign probe exemption and no third owned child spawn, source mutation before admission. No actual game environment created.

## Honest limits / remaining work

Root final test run, real artifact-only build/admission and independent final review remain pending. Freshness audit of all four fixed lists remains a root launch prerequisite; this adapter checks exact list content, it does not claim to scan every worktree or unlogged external games. Independent selection audit is externally supplied root authority, hash-bound to its exact complete recomputed summary; the tool does not independently invent an auditor. Actual process/power/quota behavior and all440/optional1200real outcomes cannot be claimed from synthetic fixtures. Training mechanics and historical acceptance remain technically valid evidence, not strength evidence. No automatic release, fallback nominee, extra maps or second confirmation is implemented.
