# Student and reward pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Train a genuine single-network student and, if time permits, a matched training-only SAP-reward ablation, without changing the submission.
**Architecture:** New standalone experiment scripts reuse QNet and the reviewed training/evaluation interfaces. No runtime-agent or default-config changes. Separate diagnostic outputs and final-only checkpoints.
**Tech Stack:** Existing Python 3.13 venv, PyTorch, NumPy, pytest; standard-library provenance and subprocess coordination.
**Spec:** `docs/superpowers/plans/2026-11-04-student-reward-spec.md`.

**Amendment before new study game results (04.11.,14:15):** the spec now additionally fixes S30 (same student,30epochs), keeps S3, starts both RL arms from S30, and expands the one diagnostic to five roles/600games. The original task text below is retained for provenance; the dated spec amendment governs these changed counts.

## Global Constraints

Finish by 2026-11-04 16:00 Europe/Berlin; model jobs stop by 15:35. Maximum two CPU workers, one thread each. V14 and ZIP remain byte-identical. No promotion, no fresh-test tuning, no optimizer/replay reuse across reward treatments. Use `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python`. Writes only in experiment paths checked against submission roots. Reject existing output directories, source mutation and nonfinite input/output. Preserve foreign files. Root owns Git commits, runtime jobs, documentation and integration; implementers do not launch production experiments or commit.

## Review Focus

- Student checkpoint must load in Agent_x as exactly one 79-input/6-output 512-wide network.
- Teacher input and all 36 members remain unchanged; no RNG or gradients affect teacher.
- Historical row diagnostics cannot claim unseen-map generalization; current action masks are absent.
- RL role configs differ only by the SAP reward weight, with empty fresh buffers and equal initial tensors.
- Deadline/failure paths leave truthful incomplete status and never a success receipt or promoted weights.

### Task 1: Single-network distillation

**Files:** Create `scripts/student_distill.py`, `tests/test_student_distill.py`.
**Interface:** CLI `python -m scripts.student_distill --teacher PATH --buffers PATH PATH --out PATH --deadline-utc ISO`. Output `out/weights/agent.pth`, `out/manifest.json`, `out/metrics.json`, progress/status JSON. Defaults exactly match spec (seed 20261104, hidden512, epochs3, batch1024, lr1e-4); optional CLI row cap only for technical tests, never silently applied to production.

- [x] Write and run failing tests for teacher arithmetic mean, analytic MSE decomposition, independent per-file80/20 split, wrong shapes/nonfinite inputs, empty ensemble export and protected/occupied output refusal.
- [x] Implement guarded teacher load (`weights_only=True`), actual36-member/hash/config validation, full finite float32 79-column data load and input hashes; label in bounded batches, fit one student deterministically. Teacher `.eval()`/no_grad; student training mode only during fitting.
- [x] Report per-buffer before/after row diagnostics and exact train/diagnostic feature-row overlap. Hash entire source files/checkpoints before and after. Record code, teacher, buffer hashes, actual row counts, epoch/update counts and wall time. Deadline checks between batches; status incomplete on timeout, successful checkpoint only after full3epochs and finite tensors. Save single q with target_q clone, empty ensemble/dims, configteacher+hidden512, feature_dim79/n_actions6/env_steps60000/learn_steps0, no optimizer/replay. Distillation updates recorded separately, not misrepresented as zero training.
- [x] Verify on tiny synthetic fixture (smaller data but real QNet), exact checkpoint reload predictions and teacher nonmutation. Run focused tests once after changes, write report to the supplied scratch path. Do not modify any other files or commit.

### Task 2: Matched reward fine-tuning and diagnostics

**Files:** Create `scripts/student_reward_train.py`, `tests/test_student_reward_train.py`.
**Interface:** CLI `prepare --student PATH --out PATH`, then `runarm --prepared PATH --arm control|sap0 --deadline-utc ISO`; separate init/run paths under supplied output root. Both scripts can be implemented independently; consume only the checkpoint contract from Task1, not its internals.

- [x] Write failing tests for exact one-field treatment difference, no copied replay/optimizer, protected output refusal, signed SAP reward counterfactual identity, and incomplete-run refusal.
- [x] Reuse `scripts.finetune`, temporary VARIANTS registration and reviewed final-action audit / isolated validation helpers where appropriate. Do not reuse old fixed1200-game receipts. Both arms get fresh optimizer/replay, exact same student q/target and common training config, seed29/offset3000,40prefill/160learn, lr1e-4, epsilon.05, mix solution92=.6/sol92_sq=.2/default=.1/rush=.1, final-only saving, initial/final known4-card validation. Training configs preserve full teacher gameplay config; set frozen=False and rules_in_training/rules_in_training_all=True in both, no new rescue treatment.
- [x] Log actual game plan/counts, before/after tensor hashes, finite updates, unchanged input/protected hashes, successful reload, final-action replay agreement, validation learning-state isolation. Instrument reward in a temporary context: same transition rewards with original vszero SAP weight; aggregate removed signed/absolute contribution, SAP counts and positive-to-nonpositive flips. Restore bindings on every exit; actual treatment alone changes rewards.
- [x] Check identical prefill action transcript between arms from receipts; different stored rewards are expected. Deadline stop yields incomplete status, no success receipt. Never admit a partial arm as completed. Run focused tests and report; no production jobs/commits.

### Task 3: Root-run experiments, independent review and delivery

**Files:** New `experiments/analysis/student_reward_20261104/` artifacts and shared documentation; no runtime defaults.

- [x] Independent code review, targeted baseline/modified tests, source/input freeze and protected hashes; measured runtime admission. Commit approved tools before production jobs.
- [x] Train student; independently verify counts, actual weight changes, finite output, source hashes and exact Agent_x reload. Admit both RL arms together only if fixed extent fits. Run no more than two workers.
- [x] Audit local seed inventory before any diagnostic games, freeze model/opponent hashes, execute fixed480games only if all four checkpoints qualify technically and remaining time fits. Otherwise explicitly omit that phase. Report uncertainty and exploratory scope, not a release decision.
- [x] Independently verify raw outcomes; document for Mahmoud, safe fetch/integration, meaningful commits/push. Stop own watcher/wake processes, keep other jobs/files and old artifacts, archive managed worktree only after outputs are preserved and it is no longer needed.

## Abschluss

Alle festgelegten Modell-/Messphasen einschließlich der transparent geänderten S30-/600-Spiele-Phase vollständig ausgeführt und unabhängig geprüft; Werkzeuge, Daten, Kandidaten und Übergabe bis `a4addad` auf `main` veröffentlicht und gegen die primäre lokale Arbeitskopie verifiziert. Eigene Prozesse beendet, beide Automationen pausiert. Studienarbeitskopie wegen einzigartiger lokaler Replay-Puffer bewusst erhalten; keine weitere automatische Arbeit. Kein stärkerer Kandidat, keine Übernahme. [Ergebnisbericht](../../SCHUELERNETZ_REWARD_20261104.md). Historischer Aufgabentext mit drei Epochen/vier Rollen bleibt über die datierte Spezifikationsänderung nachvollziehbar.
