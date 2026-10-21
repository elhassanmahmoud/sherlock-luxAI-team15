### Spec Compliance

- ❌ One consistency gap against the frozen-input requirement: generated checkpoint/candidate dependencies are checked at evaluation boundaries but omitted from the active-job periodic checks (`scripts/early_curriculum_study.py:790`, `:799`; see Important issue below). The other Task 4 requirements examined are implemented.
- ✅ The Task 3 caller obligations are satisfied: six paths come from audited final-arm state, development and fresh comparisons receive precisely the prescribed map ranges, and direct results are bound to their CSV hash and exact frozen-V3 self label (`scripts/early_curriculum_study.py:653`, `:822`, `:833`, `:843`, `:848`, `:852`).
- ⚠️ Final remote/reservation/source freeze, actual study start/results, and later technical release checks remain Root-owned. The diff correctly keeps these pending and cannot establish real model strength or release readiness (`docs/superpowers/plans/2026-10-21-early-opponent-curriculum.md:81`, `:83`, `:84`, `:103`).

### Strengths

- The fixed build uses protected V3 first and every final early checkpoint in seed order. It verifies finite, distinct, compatible q states, preserves the full base config and its effective interpretation, and permits legitimate historical training-config differences (`scripts/early_curriculum_study.py:672`). The unchanged builder appends all inputs, and unchanged inference averages q values equally (`scripts/build_ensemble.py:28`, `agents/sherlock/main.py:240`).
- Reports authenticate their full dependency coverage, owner/source and state audit, and recompute statistical decisions on reuse. Completed evaluation commands and CSV provenance are also checked before reuse (`scripts/early_curriculum_study.py:620`, `:637`, `:745`, `:779`).
- Negative method results cannot build a candidate. Development, fresh and direct stages are sequential and explicitly gated; only the prescribed candidate/reference pair is evaluated. Statistical completion sets technical-review readiness while release readiness stays false (`scripts/early_curriculum_study.py:818`).
- All remaining planned games remain in the admission budget until completed or excluded by an authenticated negative decision (`scripts/early_curriculum_study.py:195`). The main entry retains the shared resource lock through confirmation, and synthetic tests exercise negative decisions, exact offsets, report tampering, wrong self labels, no-repeat resume, real owned-child candidate construction and lightweight supervision (`tests/test_early_curriculum_study.py:453`, `:630`, `:648`, `:655`, `:721`, `:757`, `:793`).

### Issues

#### Critical (Must Fix)

- None found.

#### Important (Should Fix)

- **[P2] Include generated evaluation dependencies in periodic input verification — `scripts/early_curriculum_study.py:790–799`.** The caller freezes `candidate_phase['outputs']` and prerequisite outputs into `before`, but does not pass that binding to `run_process`. The existing 30-second active-job check calls only `check_inputs(state)` (`:503–505`), which verifies source and `state['protected']` (`:113–120`). The generated candidate and final training checkpoints are absent from that set. A generated input can therefore remain changed throughout multiple active-job checks without stopping the job; if restored before the completion audit, the accepted CSV is still attributed to the original hash even if workers loaded the changed candidate. This is a consistency gap relative to the plan's frozen source/weights requirement (`docs/superpowers/plans/2026-10-21-early-opponent-curriculum.md:22`, `:77`) and the review's explicit before/during/after input-binding constraint. Add per-job immutable input hashes to the existing periodic checks, retaining the before/after checks; a focused simulated-clock regression should change a generated dependency across one periodic check and confirm rejection before completion. This recommendation does not promise detection of adversarial replacements entirely between checks; existing source checks also cannot promise that.

#### Minor (Nice to Have)

- None found.

### Evidence and Limits

- Read the complete `review-a5ce6d8..9c5c06d.diff` once in three contiguous slices, plus the task brief, implementer report and Task 3 review. No changed function required a second read due to truncated context. Line references were derived from diff hunk positions.
- Named integration risk: builder and live inference might interpret network order/config/weighting differently. Checked only `scripts/build_ensemble.py`, `scripts/par_eval.py`, `Agent_x._cfg_from_checkpoint`, its ensemble loading/averaging sections and `AgentConfig.from_dict/to_dict`; fixed ordering, offset semantics, two-worker requests, config interpretation and equal weighting match.
- Named integration risk: report reuse, exclusivity, source protection or active-child execution could undermine the new caller. Checked unchanged `layout`, `check_inputs`, `new_output`, `reserve_study`, `resume_study`, `audit_pair`, `run_process` and `run_phase`. These establish the surrounding checks and expose the generated-input omission above.
- Read the existing conditional-release map. It separates later load/legality/runtime/reproduction/package evidence and current-V3 backup from this statistical pipeline. No later release checks were executed or independently certified here.
- Read the actual final evidence files: `/tmp/task4-final-four-groups.log` reports **174 passed in 43.92s**; `/tmp/task4-final-full-suite.log` reports **406 passed, 14 subtests passed in 74.72s**. Both logs are clean. These are implementer runs, not reruns by this reviewer.
- No additional tests were run: the sole issue is visible in the caller-to-periodic-check data flow, and repeating an existing suite would not resolve it. No model imports/loads, games, repository edits, Git mutations or subagents were used. Only this review report was written outside the checkout.

### Assessment

**Task quality:** Needs fixes.

**Reasoning:** The fixed candidate and gated confirmation pipeline is coherent, well covered by focused synthetic cases, and closes the prior analysis caller obligations. Extend the existing active-job integrity check to the newly bound generated dependencies before approving the long study run.
