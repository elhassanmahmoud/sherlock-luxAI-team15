# Independent Task 3 critical review — 2026-11-04

Verdict: **changes required before real training admission**. One blocking finding; no additional consequential issue found in the inspected adapter interfaces.

## P1 — Account for the original CSV's five-decimal rounding

Location: `scripts/student_anchor_train.py:423–425` (`_validate_completed`).

The adapter averages the 150 full-precision update losses per game and compares that raw mean to `train.csv` with `rel_tol=1e-7, abs_tol=1e-8`. The unchanged original producer explicitly writes `round(agent.pop_mean_loss(), 5)` at `scripts/finetune.py:228`. Normal serialization error can therefore be up to 0.000005, which exceeds this guard for ordinary losses. Both CONTROL and ANCHOR can finish their entire 40/160/32 pipeline and then be declared incomplete solely because their valid CSV was rounded. The outer receipt is removed and the occupied output cannot be rerun, wasting the full run budget.

Read-only arithmetic reproduction: raw mean `0.123456789`, producer output `0.12346`; the current `math.isclose` returns `False`. No model/game execution was needed.

Required narrow correction: compare to the same five-decimal rounded independently reconstructed mean (or an explicitly justified quantization bound). Add a regression that exercises the outer completion validation with realistic rounded means, and still rejects a materially wrong CSV mean. A mocked engine/evidence boundary can exercise publication and read-only validation without running games. Do not change the original trainer or relax unrelated proof checks.

## Inspected and consistent with the fixed contract

- Positive-weight adapter reproduces the original replay draw, TD target expressions, DQN branches, Huber loss, optimizer clearing, one backward/clip/step, loss counter and target refresh schedule. Only `0.1 * action_loss` is added.
- Weight zero directly calls the saved original `_learn`, with no extra network evaluation, replay/sample draw or loss arithmetic before the existing step. Its audit work uses a separate generator and pure hashing.
- Existing action loss detaches the teacher, centers over legal actions, normalizes by the fixed scale, and excludes illegal coordinates; additive value shifts and single-action rows are unanchored.
- Sampling copies only training rows, uses an independent generator seeded by `20261104 + run_seed`, and records global indices. Exact dataset hashes, row counts, scale, source/model pins and train-index hash are checked. The sidecar validator recreates each draw and verifies counts, split, losses, summaries and nonzero anchor gradient evidence.
- Public arms use distinct nested original preparations and execute only each nested `control`; configs, rewards, original engine audits, final-only checkpoint semantics and 24,000-update budget are retained.
- Constructor, `_learn` and replay `push` adapters are restored through exception-safe contexts. The original isolated-validation guards save/restore these instance bindings, so they do not discard the anchor or prefill hook.
- Prefill content is captured before the first training-phase push; pair comparison includes actual replay content, action/reward/feature transcripts and learner/global RNG identities. Learner identities contain no process addresses or output paths in this comparison.
- Outer completion pins the original receipt and evidence, checks restored bindings and full update sidecars, and removes its marker on exceptions. Source/input/output protections are present. The success-path rounding issue above remains an admission blocker.

## Scope and evidence limits

Read the provided review diff, Task 3 brief, implementation handoff, approved specification, repository rules/current handoff, and concrete original trainer/action-loss/identity/validation interfaces. Ran only a scalar arithmetic reproduction. No games, training, focused tests or full suite were run by this reviewer; no source, index, HEAD or production file was changed. Root owns suite execution. The reported 27 focused tests and accidental 13 known-map synthetic prefill games are implementation handoff evidence, not independent review runs. No successful full outer completion path or strength claim is established here.

Root should include this review and the eventual correction/actual checks in the shared Arbeitsstand after integration; this delegated review owns only this review file.

## Scoped fix review — accepted

The P1 finding above is **resolved** in the current adapter: `_validate_completed` now compares the CSV number to `round(actual, 5)`, exactly matching the unchanged producer. It preserves exact acceptance at the producer's documented precision rather than broadly widening an audit tolerance.

Inspected both parametrized cases of the new outer-completion regression. Explicitly mocked preparation/original-engine/update-sidecar boundaries prevent game execution; the real outer validator reconstructs 160 means from 24,000 supplied records, accepts valid five-decimal CSV output, verifies restoration at receipt publication and read-only subsequent validation, and rejects a 0.001 discrepancy before publication with incomplete status. The scope is appropriate for this integration error. The implementation handoff reports 29 focused tests passed; this reviewer did not rerun them.

Also inspected the adjacent tracked test-only diff: precisely two added lines in each of `tests/test_final_battle_study.py` and `tests/test_network_breadth_study.py` import `time` and locally monkeypatch `GAME_END = time.time() + 60` in the existing STOP cleanup test. This lets the intended owned-child STOP cleanup branch remain reachable after the historical deadline. Child-command replacement and cleanup assertions remain intact, and no production deadline was changed. Root reports 43 focused tests passed; these are not independent reviewer executions. The named `reportdeadline_test_fix.md` was not present at the supplied handoff path during review; the actual four-line diff was directly inspected.

Current verdict: **no remaining blocking findings in the reviewed scope**. This is source/test review acceptance, not evidence of a completed real training run or performance improvement. No additional tests, games, training, source edits, index changes or commits were performed in this scoped fix review; only this review record was appended.
