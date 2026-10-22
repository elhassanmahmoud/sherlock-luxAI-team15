# Independent final confirmation audit

**Decision: valid completed confirmation, no qualifying improvement. Keep installed V10 unchanged. No data or provenance errors found.**

Audit completed **22 October 2026, 15:34:03 UTC**, while the worktree still had frozen HEAD `de2e95d451a22643a3f7351636d3348f7770a1aa`. Read-only repository operations and independent standard-library/NumPy calculations only; no model/engine imports, tests, games, or frozen-repository edits.

## Results independently reproduced

| Opponent | V10 W/D/L | Recovery W/D/L | V10 score | Recovery score | Paired Δ | 95% map-bootstrap interval |
|---|---|---|---:|---:|---:|---|
| Solution_92 | 1448/0/152 | 1437/0/163 | 90.5000% | 89.8125% | −0.6875 pp | [−1.5000; +0.1250] pp |
| default | 1599/0/1 | 1599/0/1 | 99.9375% | 99.9375% | 0 pp | [0; 0] pp |

Every value in `confirmation_summary.json` matches the independent calculation exactly.

**Solution fails both mandatory confirmation conditions:** the observed difference is below +2 pp, and its lower 95% endpoint is not above zero. The exact difference is −22 half-result units out of 3,200; the minimum required difference was +64. The interval includes zero, so this is not a claim that recovery is demonstrably worse. It is a clear failure to establish the required improvement.

**Default passes both safeguards:** 3,198/3,200 half-result units exceed the minimum 3,168, and Δ=0 exceeds the permitted lower bound of −32 units. Identical empirical results do not prove general equivalence or universal performance.

## Data and statistics checks

- Each CSV contains exactly 3,200 unique games: seeds **611000–611799 × both sides × default/Solution_92**. Together they contain all **6,400** planned rows, without missing, duplicate, or extra keys.
- Exact 24-field schema, finite values, nonnegative integer counters, valid fractions, three-match/303-step duration, point-counting version 2, match-result/game-win coherence and point-result coherence all passed.
- CSV hashes were checked before and after reading and agree with the phase journal and root summary.
- Independent bootstrap did not import the repository analysis helper. It grouped both sides into integer half-result totals per map, paired candidate-minus-reference within each map, resampled 800 whole maps 5,000 times using `default_rng(0)`, and took percentiles 2.5/97.5. Gates used exact integer counts and unrounded interval endpoints.

## Commands, chronology and frozen identity

- `confirmation_jobs.json`, embedded phase specification, recorded commands, output paths, both zero exit codes and hashes all agree. Both commands used the same frozen V10 checkpoint, offset 111000/count 800, both opponents and two workers. Baseline flags were false/false; recovery flags were true/false. This remained the originally nominated energy-recovery-only arm.
- Admission hashes for both selection summaries, command manifest and source freeze still match. Admission preceded confirmation start. Baseline completed before recovery began; recovery completed at **15:32:05.821407 UTC** and the phase completed at **15:32:05.944470 UTC**, before summary generation.
- Current HEAD, interpreter/resolved executable/hash, **all 128 frozen source/plan/engine/environment files**, complete source-file inventory and **all four protected/reference weights** match the original freeze. The predeclaration also equals its committed contents.
- All four checkpoints retain V10 SHA-256 `03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67`.

## Closing scope and unrun work

`closing_scope_20261022.json` records the user's instruction to finish the admitted confirmation, start no further direct/robustness phases, and make no promotion. Its recorded time, **14:24:29.572224 UTC**, precedes the final recovery CSV write at **15:32:04.565017 UTC** and the recorded completion. The file explicitly records candidate results as unseen then. The timestamps substantiate that this closing decision preceded final candidate output; this audit cannot independently establish a person's knowledge beyond the recorded evidence.

**Direct and stronger-opponent phases were not run; they did not fail.** No corresponding later-phase artifacts were present. Their reserved blocks remain unconsumed by this program. The closing instruction independently prohibits promotion regardless of results; additionally, the completed Solution confirmation already fails the improvement gates.

The frozen-input audit is now complete. Subsequent documentation/integration can proceed while preserving these historical source/command/data hashes. Do not reinterpret a new HEAD as the code used for these games.

## Evidence

| File | SHA-256 |
|---|---|
| confirmation_baseline.csv | `3f88403e9a99536a643e06798af09d0575cf74a59e32192299ad49d0088df595` |
| confirmation_recovery.csv | `68f8ab32a46d5726914a25c6bbe0ddd75ad930f4e70bcb95c6b85894812aa5fd` |
| confirmation_summary.json | `ad1952cb12b3a194c427e340e93ec673a13e9759545843cf6d2c80b855fae2be` |
| closing_scope_20261022.json | `40d0db0d7a6c8eca17a09c59e0e8ab71a07d08821360dc247c712c4fdcb47118` |

Machine-readable independent results: `/tmp/sherlock-v10-fixes-20261022/confirmation-data-review.json`.

Reproducer: `/tmp/sherlock-v10-fixes-20261022/confirmation_data_audit.py`.
