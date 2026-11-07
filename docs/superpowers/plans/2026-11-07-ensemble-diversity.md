# Ensemble Diversity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Autonomous execution is explicitly authorized by Moayed.

**Goal:** Train six genuinely new complementary members and measure fixed ensembles against protected V14.

**Architecture:** A process-local wrapper reuses finetune, isolated validation and action/replay auditing. New experiment artifacts contain preparation identities, actual rollout logs and verified final receipts. Production agent code and old experiment wrappers stay unchanged.

**Tech Stack:** Existing Python environment, PyTorch, NumPy, LuxAI engine, pytest.

**Spec:** ../specs/2026-11-07-ensemble-diversity.md

## Global Constraints

- At most two model processes; stop new work at 65 % account usage, retain at least 30 %.
- Protected V14 SHA256: 98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8.
- Never rewrite historical evidence, active weights, or submitted ZIP.
- Separate six training arms, fresh seed reservations, immutable source during runs.
- No automatic candidate promotion; selection/confirmation plan fixed before outcomes.

## Review Focus

- Warm start must have one net, fresh optimizer/replay, intended cfg, and online/target identity.
- Validation must not train, advance learning state, or perturb training RNG.
- Saved replay actions must equal actual issued actions, including mirrored side and rescue.
- Partial/smoke runs must never receive a complete eligible receipt.
- Seed or source changes, duplicate outputs and protected destinations must fail closed.

### Task 1: New training wrapper and checks

Files: scripts/ensemble_diversity_train.py; tests/test_ensemble_diversity_train.py; scripts/ensemble_diversity_supervisor.py; tests/test_ensemble_diversity_supervisor.py.

- [x] Add failing tests for arm mapping, isolated seed ranges, source/config identity, safe outputs and smoke/incomplete eligibility.
- [x] Implement prepare/run CLI using existing training machinery; persist incremental progress and final evidence, restore process-local hooks.
- [x] Run focused pytest tests and actual separate smoke games; independently review source and receipts.
- [x] Commit reviewed tool, tests, spec and plan before source-freeze.

### Task 2: First six-member training wave

- [x] Complete seed-collision audit; snapshot reference/source/interpreter hashes.
- [ ] Prepare six arms and record operational ownership; run A0/B0 first, then A1/B1 and A2/B2 with at most two workers.
- [ ] Check real loss, optimizer updates, replay/action consistency, finite changed weights, validation isolation and final checkpoint reload. Stop on technical defects; do not nominate partial outputs.
- [ ] Record resource/battery/account budget and safe GitHub comparisons; finish or stop cleanly on resource limits.

### Task 3: Fixed ensemble comparisons

- [ ] Write exact selection/confirmation jobs and thresholds before first fresh result; independent review.
- [ ] Build the four specified candidates with identical V14 inference config and verified distinct members.
- [ ] Run paired selection, choose at most one by fixed ranking, then one independent confirmation if qualified.
- [ ] Independently verify complete raw data and all gates; keep V14 absent proof of improvement. Document results and push meaningful verified commits; safely update primary checkout.

## Execution Ledger

- 07.11.: Remote at a9b5202, no active model processes; existing worktree reused on improvement/ensemble-diversity-20261107. Two read-only audits dispatched. Account 44 % used; battery 62 %, user will connect AC. Existing unittest discovery found no tests; corrected to pytest (repository uses pytest functions), no test failure claimed.

- Baseline: 88 pytest tests passed in 50.47 s (finetune, ensemble dimensions, final rescue training). Local seed audit passed; external or seedless runs remain outside scope. REPLACE36 is diagnostic-only and removes the three selected parents plus their verified ancestors [0,6,12,18,24,30]. A/B retain separate maps as specified; no isolated curriculum-effect claim.

- Vor Betriebsstart unveränderte abgegebene ZIP vom primären Checkout in den ignorierten Studienworktree kopiert (SHA256 88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6); kein Neubau. Betreuer prüft dieselben Bytes zusätzlich zu beiden Rohgewichten.

- Root verification: 142 targeted pytest tests passed in 50.74 s, including both new tools and shared finetune/ensemble/rescue/supervisor tests. Independent review found validation SIGTERM waited a full block; fixed with two initially failing regression tests, root inspected per-game check and verified green suite. Real smoke remains next; no performance results.

- Task 1 complete: tool/spec commit cda52d9; Root real A0/B0 smoke at that commit: each 2 prefill + 2 learning + 8 validation executions, 300 actual optimizer updates, changed finite weights and successful reload, validation identities unchanged. Both receipts explicitly smoke/ineligible, total24 technical executions. Protected baseline hashes unchanged. Production not yet started.
