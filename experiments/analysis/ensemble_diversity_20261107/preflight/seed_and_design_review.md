# Seed and design review — 07 November 2026

Read-only review preceded any new production games. The current explicit user
authorization replaces the old presentation-only stop. No historical experiment
was restarted and no model was trained during this review.

## Recorded-data collision audit

Scanned `experiments/` in all eight paths returned by `git worktree list --porcelain`:

- `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15`
- `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15`
- `/Users/moayedshawesh/Desktop/KI/sherlock-counterplay`
- `/Users/moayedshawesh/Desktop/KI/sherlock-enemy-tie`
- `/Users/moayedshawesh/Desktop/KI/sherlock-ensemble-validation`
- `/Users/moayedshawesh/Desktop/KI/sherlock-november-followup`
- `/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics`
- `/Users/moayedshawesh/Desktop/KI/sherlock-v4-joint`

Production scan: **8,612 CSV files, 7,157 with seed columns, 4,622 JSON files and
82 JSONL files**. CSV integer values in columns containing `seed` were checked.
JSON/JSONL integer values under keys containing `seed` or `map`, including nested
lists/objects, were checked; ascending two-integer seed/map arrays were also
checked as inclusive ranges. Duplicate evidence copied across worktrees remains
in these file counts; these are not unique games. No consumed exact seeds or
overlapping recorded two-endpoint ranges were found in the following blocks:

| Purpose | Inclusive ranges |
|---|---|
| Training, starts 0–5 | 1100000–1101499; 1110000–1111499; 1120000–1121499; 1130000–1131499; 1140000–1141499; 1150000–1151499 |
| Prefill, starts 0–5 | 1105000–1105059; 1115000–1115059; 1125000–1125059; 1135000–1135059; 1145000–1145059; 1155000–1155059 |
| Known validation | 1300000–1300007 |
| Selection panel | 1400000–1400099 |
| Selection direct | 1401000–1401099 |
| Confirmation panel | 1500000–1500799 |
| Confirmation direct | 1600000–1600399 |

The current worktree's Markdown/Python/shell files under `docs/` and `scripts/`
had no matching numeric reservations at scan time, before the new study spec was
written. These blocks were reserved but not played by this reviewer.

The subsequently requested **smoke extension** scanned the same eight worktrees
and formats: **8,612 CSV, 7,157 seed-bearing CSV, 4,623 JSON, 82 JSONL**, with zero
parse/read errors. The broad inclusive interval **1190000–1245059** and validation
seed **1390000** had no exact-seed or recorded-range collisions. This broad scan
covers all six smoke train bases `1190000 + start*10000` and their `+5000` prefill
bases. Smoke remains technically separate from production and strength tests.

An earlier scan of 900000–920000 found only **900000–900029**, already consumed in
37 historical seed-bearing CSV paths per worktree. Those historical test cards
must not be described as fresh. Unrecorded/external runs, string-encoded JSON
seeds, arbitrary implicit formulas and seedless logs are outside these scans.
No freshness guarantee beyond the inspected local records is claimed.

## Design findings accepted by the coordinator

- Three lineages, two descendants each: V14 parent 18 traces to original member 0;
  24 to original 6; 30 to original 12. Provenance was verified against
  `docs/presentation/source/ENSEMBLE_BATTLE_0611_20261104.json`. These are six newly
  trained descendants, not six independent random initializations.
- Nominable candidates are fixed **A39, B39, ALL42**. Diagnostic REPLACE36 removes
  **[0,6,12,18,24,30]** and adds all six descendants. It cannot be nominated and
  does not isolate a universal causal effect of network count.
- A/B keep the distinct training maps specified by the coordinator. Therefore
  curriculum comparisons are descriptive, not isolated causal A/B estimates.
  Final checkpoints alone enter the fixed combinations; no member picking from
  intermediate validation outcomes.
- Training flags have explicit coverage limits: `rules_in_training`,
  `rules_in_training_all`, `rescue_in_training` do not imply full training/play
  equivalence. Production candidates retain exact V14 inference configuration.
- Prior FO42 confirmation: panel +0.104 pp [−3.646,+3.750], direct 56.25%
  [48.75,63.75]. FT18: panel −0.917 pp [−2.813,+0.958]. Neither justifies a repeat
  confirmation or an assumption that more members improve strength.

Before fresh performance outcomes, fix all job keys, opponent files, source
hashes, sample sizes, gates and ranking. Recommended selection gates retain panel
Δ≥0.5 pp, Solution Δ≥0, default≥99%, direct≥50%; at most one nominee. Confirmation
retains all seven historical release gates, whole-card paired bootstrap with
both sides/all panel opponents together, 5,000 draws, PCG64 seed 0. Historical and
selection rows stay outside confirmation; no candidate replacement after failure.
Eight hundred panel cards against seven opponents for two models plus 400 direct
cards means 23,200 confirmation games; resource admission must cover completion.

Minimal complementarity diagnostics: legal-action disagreement and centered
Q-scale on a fixed known feature/mask bank; paired fresh-card discordant outcomes
by opponent; ALL42 versus A39/B39 and fixed-count REPLACE36; inference time/model
size. Distinct hashes or disagreement alone cannot establish useful diversity.

## Supervisor verification

New supervisor tests first failed because its module did not exist. After
implementation, **20 mock-only tests passed (0.09 s)**; `git diff --check` passed.
No real supervisor, model process or game was launched by this reviewer. Queue
order, two-worker ceiling, power hold/stop thresholds, STOP inhibition, ownership,
180-second graceful shutdown, hashes/receipts, atomic ledger and shared/external
resource locking are covered. The controller performs lightweight receipt/hash
checks only; full tensor/learning audits remain the coordinator's post-training
step. Account usage is externally monitored by the coordinator through STOP;
the supervisor does not claim access to an automatic quota API.
