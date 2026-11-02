# Independent statistics review — 02.11.2026

**Final verdict: PASS after the integrity fix. No open Important or Critical
finding in the reviewed statistics scope.**

Reviewed `/tmp/sherlock-continue-20261102/targeting_stats.py` against
`targeting-performance-protocol.md`, the current external evaluation-driver
interface, and the reused `compare_report` / `league_gates` numerical helpers.
Final reviewed statistics SHA256:
`a02eb0a84a56ef326bff1b404aed9c0a1f7f4c2f8ea95d12d9180081568932b4`.

## Important finding, resolved

Before the fix, `source_before == source_after` did not bind either to the frozen
identity. The summarizer also did not revalidate fixed jobs against the freeze's
role models/flags, or require a valid shared freeze/plan schema. A pure synthetic
counterexample with 4600 table rows, nonexistent model paths, P flags both false,
and an equal-but-wrong source pair was accepted as `status=complete`.

Root added `driver.check_plan(plan_path)`, exact equality of its returned
plan/freeze to the already read artifacts, and
`state.source_before == state.source_after == frozen.identity`.
The same counterexample now aborts before writing any summary (missing required
schema_version is rejected by the newly invoked plan guard). Code inspection
confirms the guard also checks the current full source/weight/driver identity,
fixed job construction, role weights/flags and confirmation selection receipts.

Preserved evidence:
- RED: `targeting_stats_review_counterexample.json` (old SHA
  `f2f8528be4aa7e1f6d2d4ed242072925b035e41b10fde370c86f2901329729e5`).
- GREEN: `targeting_stats_review_counterexample_after_fix.json`.
Both explicitly record zero environment games and no Torch import.

## Checks and remaining limits

- Whole-map bootstrap is correct: paired key merge, then mean over both sides
  and all six panel opponents per map, then 5000 RNG0 draws of those map means.
  Solution uses paired two-side map differences; direct uses candidate-side
  two-side map scores. Percentiles are 2.5/97.5. The helpers' numerical functions
  are reused with explicit PANEL/DIRECT arguments; their old gates/pick are not.
- Selection/confirmation thresholds and strict versus inclusive inequalities
  match the protocol with 1e-9 tolerance. Nomination considers passing candidates
  only, choosing P before PT for ties within 1e-9, independent of dictionary order.
- Driver `validate_output(target,job)` now exists and direct labels match the
  required relative V14 label. Full schema, exact seed/side/opponent sets,
  duplicates, finite/range/outcome checks, 303/v2, per-job hashes and counts are
  checked. Statistics additionally requires exactly one panel/default job per
  role and one direct job per candidate, with total 4600/9000.
- Confirmation is now revalidated through the driver's full plan guard, which
  binds completed selection state, selected candidate, exact selection plan and
  freeze, summary hash and every unchanged selection CSV. No runner-up selection
  or new nomination occurs during confirmation.
- Minor reporting gap: panel/default have wins/draws/losses; direct currently
  reports its score/interval without those pure outcome counts. Add direct counts
  to meet the protocol's reporting wording; gate correctness is unaffected.
- Read the author's 13 stdlib gate-test receipt; did not rerun that suite. The
  only execution was the narrow synthetic red/green counterexample. No actual
  full valid phase, model, tensor, training or game was loaded/run. A real phase
  still requires complete independent raw-data audit and promotion checks.

No repository edits or source fixes were made by this reviewer. Root applied the
statistics fix; the active training freeze was untouched.
