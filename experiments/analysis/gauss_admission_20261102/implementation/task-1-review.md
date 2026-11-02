# Independent Gauss admission review

Reviewed commit range `307b1ed..e58fa63`, the two new files, the implementation brief/report, and the binding plan including the four sequential subprocess-batch amendment. Existing agent, belief, import, opponent, scoring-driver and truth interfaces were read to verify compatibility.

**Spec verdict: changes required. Code-quality verdict: changes required.** Two Important findings; no Critical findings. Do not dispatch C/S until the startup blocker is corrected and independently checked.

## Important 1 — Normal package imports are excluded from the pinned runtime inventory

Location: `experiments/analysis/gauss_admission_20261102/admission.py:36`, `:389–391`, `:530–536`, `:606`.

`RUNTIME_PATHS` includes `agents/__init__.py`, Sherlock and Solution92, but excludes `agents/DQN` and `agents/default`. The existing `agents/__init__.py:5–6` unconditionally walks and imports all agent subpackages. Thus the child’s ordinary `from scripts.experiment import limit_threads` / Sherlock imports also load at least `agents.DQN` and `agents.default`, even though this study does not instantiate them. `check_imports()` examines every loaded `agents*` module and rejects those files because they are absent from `selected['files']`. The first C child therefore fails before its first `play_game()` call; the intended eight-game compatibility stage cannot run.

This was verified without importing agent/model code: a narrow pure counterexample populated a module-path double for the real tracked `agents/DQN/__init__.py` and used the actual inventory construction. Result:

```text
unpinned runtime import: agents.DQN: /Users/moayedshawesh/Desktop/KI/sherlock-november-followup/agents/DQN/__init__.py
```

Include and basis-verify all runtime modules imported by the existing package initializer, or provide an explicitly verified import strategy that avoids that discovery while preserving the selected source root. Do not simply weaken the import guard. Add a pure regression covering the real package-discovery/inventory relationship; the current foreign-import fixture does not exercise this necessary same-root import.

## Important 2 — Already measured dead-fact leads are retroactively marked censored

Location: `experiments/analysis/gauss_admission_20261102/admission.py:226–230`, `:244–246`, `:271–280`.

The truth-regime-change, match-reset and knowledge-loss branches add `censored_reason` to every affected dead-fact lead, including leads whose V and A catch-up delays have already been observed. For example, G acquires a valid dead fact at step 1, V and A both catch up at step 2, and an unrelated point appears at step 3. The completed one-step lead then changes from an observed result to a record marked censored. Match resets similarly affect all earlier dead leads, so completed leads from earlier matches will commonly carry the wrong censor status. This violates the plan’s requirement to censor when catch-up has not occurred and makes the reported lead distribution ambiguous/misleading.

A narrow pure raw-frame counterexample produced:

```text
Before regime change: step=1, V=1, A=1
After regime change:  step=1, V=1, A=1, censored_reason=truth_regime_change
```

Preserve completed comparator delays. Apply censoring only to unresolved comparators, with separate V/A censor state when one catches up before the other. Cover a fully resolved lead followed by a regime change/reset, and a partially resolved lead whose other comparator remains pending. The existing test covers only an entirely unresolved lead.

## Review coverage and limits

The four-batch sequencing, isolated selected roots, actual prototype HEAD recording, fixed baseline comparisons, V14 digest/tensor-verification logic, independent reset-time V/A/G copies, pre-V novelty formula, downstream truth access, native action-byte capture, fixed S timing gates, phase seals, and owned-child timeout handling were inspected. The reviewed code maintains the technical-shadow-only outcome boundary.

No focused test suite was rerun, no fullsuite was run, no real games were run, and no checkpoint/model/engine was loaded. One short stdlib-only counterexample invocation checked the two concrete findings above; it confirmed no `torch`, `agents.*` or `luxai_s3` modules remained imported. The reported 22 passing tests are implementation handoff evidence, not a new reviewer test result. No implementation edits or commits were made; only this review report was added. Runtime integration remains pending after corrections.
