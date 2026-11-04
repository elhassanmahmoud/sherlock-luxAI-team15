# A2 Teacher-Anchor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Diagnose A2 failures and test whether a fixed supervised anchor preserves useful decisions during RL.
**Architecture:** Separate read-only diagnostics and a training-only adapter reuse the verified collector/data loader/TD pipeline. Agent runtime and V14 submission remain unchanged.
**Tech Stack:** Existing Python environment, PyTorch CPU, NumPy, pytest, Lux course runner.
**Spec:** `docs/superpowers/specs/2026-11-04-a2-teacher-anchor.md`.

## Global Constraints

- Two heavy workers maximum, one CPU thread each; root coordinates actual game launches.
- No production agent, reward, config, protected weight or ZIP edits. Root alone commits/pushes and integrates.
- Use final checkpoints; immutable historic datasets, excluded map split, fresh test cards and whole-card uncertainty.
- New study output `experiments/analysis/a2_anchor_20261104/`, checkpoints/runs in new experiment directories. Preserve old untracked runs.
- Stop admissions at 65 % account usage / battery below 35 %; reserve 30 %, no reset. No new training after 22:15 Berlin; model jobs end by 23:00.

## Review Focus

- Data leakage: train indices only in anchor, diagnostic rows never sampled; tests verify sampled identities.
- Hidden behavior changes: observation must preserve full action digest/results, weight zero exact ordinary TD equivalence.
- Mask semantics: invalid actions zero contribution, single legal action zero anchor; raw Q copies precede in-place masks.
- State isolation: own anchor RNG, restore hooks and global adapters after errors, fail closed on source/input mismatch.
- Evidence: actual updates/logged loss, complete expected games and final model hashes; no partial run promoted.

### Task 1: Retention diagnostics

**Files:** Create `scripts/student_retention.py`, `tests/test_student_retention.py`.
**Interfaces:** CLI accepts `--datasets` (one or more collector dirs), repeated `--model NAME=PATH`, `--out` (new dir). Loads validated existing packages and checkpoint `q` with QNet inferred/checked config. Returns JSON per-role diagnostic metrics and provenance; one report can be used before and after training.
- [ ] Tests: malformed/mismatched masks fail; synthetic exact teacher has agreement 1/regret 0; excluded split only contributes; protected/occupied output rejected; finite independent model inference.
- [ ] Implement batched no-grad inference and metrics, model/data/source hashes. No model mutation.
- [ ] Run targeted tests, independent review and root verification; commit.
- [ ] Run five existing models once; report evidence/limits with no causal overclaim.

### Task 2: Loss traces

**Files:** Create `scripts/student_failure_trace.py`, `tests/test_student_failure_trace.py`.
**Interfaces:** CLI accepts `--model`, `--opponent` (solution92 or self), optional `--opponent-path`, `--seed`, `--side`, `--out`, `--deadline-utc`. One normal and one instrumented game per invocation; compare every action and final metrics, retain observation-only JSONL and summary. Agent may be A2 single or V14 ensemble. Hook inputs/raw outputs exactly once; compare teacher Q only on copied features, outside act if needed.
- [ ] Tests cover canonical mirroring, hook restoration on failure, no reset ghost rows, ensemble mean raw Q, no second act/context, per-match counter reset.
- [ ] Implement wrapper around normal play path, not a divergent replacement simulator. Capture actual state available to agent and final outputs; no hidden-state assistance.
- [ ] Run tests/review, then prescribed known-case paired replays (24 executions total), one CPU slot. Root analyzes earliest consequential divergence and missing evidence.

### Task 3: Anchored training adapter

**Files:** Create `scripts/student_anchor_train.py`, `tests/test_student_anchor_train.py`; avoid modifying existing trainer if a restored wrapper suffices.
**Interfaces:** `prepare --student PATH --datasets DIR... --out DIR --run-seed {25,26}` creates CONTROL/ANCHOR paired manifests. `run --prepared DIR --arm {control,anchor} --deadline-utc ISO` runs original fixed 40/160/32 pipeline with training-only combined loss. `validate --prepared DIR --arm NAME` validates completion and sidecar provenance. Document actual implemented invocation in help.
- [ ] Write failing tests: lambda 0 exact TD parameters/optimizer/RNG; positive anchor supplies gradients only through student legal centered preferences; single-action zero; own RNG doesn't consume replay RNG; no excluded rows; cleanup after exception; output/source/input guards.
- [ ] Implement existing TD update plus weight 0.1 action_loss on 256 training rows, one shared backward/clip/step; same targets and counter schedule. Keep value shifts unanchored. Do not alter production Agent_x source.
- [ ] Record source/data/model pins and separate actual TD/anchor/total metrics, updates, sample split/count. Reuse existing training audit and verify paired prefill (same configs/rewards).
- [ ] Run tests and independent review; root baseline/full relevant checks and commit before trials.

### Task 4: Controlled execution and fixed comparison

**Files:** New study manifests, original result CSVs, audits, candidate model copies under `experiments/candidates/a2_anchor_20261104/`.
- [ ] Inventory seeds/protected inputs/other processes and record runtime admission. Commit sources; freeze throughout each study phase.
- [ ] Run paired seeds25/26 (four arms, 928 games), validate actual learning and outputs. Run retention tool on all final checkpoints.
- [ ] Freeze six roles and 920-game comparison before reading any new result. Run two workers, validate completeness/version2/303steps and hashes.
- [ ] Independently calculate whole-card comparisons and direct intervals. Apply predeclared selection; complete full confirmation only if qualified and time permits, otherwise leave experimental.

### Task 5: Documentation and integration

**Files:** `docs/A2_LEHRERANKER_20261104.md`, `docs/ARBEITSSTAND.md`, `docs/EXPERIMENT_PROTOKOLL.md`; README/CLAUDE only relevant state updates; archive manifest.
- [ ] Record executed games/training counts, findings, uncertainty, status of hypothesis and next steps; include decision-flow trace useful for presentation later.
- [ ] Independent whole-branch review, verify protected hashes and data integrity; meaningful commits, safe remote check and push to authorized main, update primary checkout without touching foreign untracked files.
- [ ] End own processes and record closure. No active model/monitor jobs left implicitly running.
