# Independent performance-protocol review — 02.11.2026

**Verdict: methodologically suitable within the stated local-panel scope; ready
only after the explicit freezes/admission checks below. No Critical issue. Two
Important implementation/resource risks must be resolved before fresh outcomes.**

Read-only review of Root's proposed P/PT protocol, continuation design,
adaptation plan/Root amendment, existing league/compare helpers and historical
runtime memo. Observed training HEAD `8e4720ca224f3cdf61693d5e5c4b4ef422ac6d8d`.
No repository edits, implementation, model loads, games or training. Only this
/tmp note and a pure arithmetic calculation were produced.

## Methodology

- Counts independently reconcile: selection = 3×7×2×100 + 2×2×100 = **4600**;
  confirmation = 2×7×2×300 + 2×300 = **9000**. Confirmation has only V14 and the
  single nominee; the rejected candidate is not tested there.
- Fresh selection of at most one fixed candidate followed by a separate, fixed
  confirmation is appropriate. All confirmation conditions are jointly required;
  no runner-up, extension, altered gate or changed candidate after outcomes.
  Selection estimates are optimistic/descriptive, not confirmation evidence.
- Specify the metric as mean `result` (win=1, draw=.5, loss=0), equal weight for
  the six panel opponents and both sides. Default is separate. Pair candidate
  and V14 by opponent/map/side; bootstrap the map-level mean difference, keeping
  all six opponents and both sides together. Solution uses its paired two-side
  map difference; direct uses nominee-perspective two-side map mean. 5000 draws,
  RNG0 and 2.5/97.5 percentiles are consistent with existing methodology.
- Explicitly pin selection direct games to **841000–841099**, both sides for
  each candidate. Do not spend 842/843 confirmation keys during selection.
  Pin sorted seed order and percentile interpolation for reproducibility.
- Freeze exact source/artifact/config/opponent hashes and expected keys before
  the first 841 result. P preserves all 36 V14 tensors; PT replaces both 18/19
  with the predeclared adapted final Qs only after all four arms pass audit.
  Controls remain diagnostics. Test-loaded inference must have both flags on,
  epsilon zero, no learning and uniform 1/36 ensemble weighting. Historical
  opponents must be exact artifacts with their intended configs, not aliases
  silently resolving to another release.
- Whole expected grids must pass independent validation before any gate. Reject
  missing/duplicate/extra keys, nonfinite or invalid results, wrong sides,
  incomplete 303-step episodes, non-v2 points, caught inference errors or changed
  source/config/weight hashes. Do not let an inner join silently drop maps.
  Predeclare infrastructure retry/abort handling; never discard inconvenient
  completed outcomes. No outcome-based checkpoint/candidate/job selection.
- Interpret a passing PT as evidence for that fixed artifact versus V14 on this
  panel. It does not establish that adaptation beats P, that the learning method
  generalizes across training starts, or superiority against unknown opponents.
  No extra candidate is needed to preserve this limited claim.

## Important risks

1. **Existing gate helpers implement a different study.**
   `scripts/league_gates.py` has a different default panel, selection +1.5pp /
   Solution -1pp, confirmation +2pp / Solution -.5pp / lower >-2.5pp, and `pick`
   breaks ties using direct score. They cannot be reused unchanged for this
   protocol. The runner must enforce the exact proposed inequalities, including
   Solution confirmation lower **>= -1pp**, panel/direct lower strictly **>**, and
   equal-panel ties favoring **P**. Use exact score totals or a declared tiny
   numerical tolerance for equality; test gate boundaries and tie handling on
   synthetic summaries before freeze. No change to the proposed policy needed.

2. **The 22:30 confirmation start in the older runtime memo spends the reserve.**
   `/tmp/sherlock-continue-20261102/training_design.md:113` explicitly defines
   2.22 as **wall seconds per completed game at two workers** (process means
   4.35/4.19s); never divide it by two again. Independent arithmetic:

   | Phase | Base minutes | With 20% reserve |
   |---|---:|---:|
   | Selection, 4600 | 170.20 | 204.24 |
   | Confirmation, 9000 | 333.00 | 399.60 |
   | Both plus 60-min closure | 563.20 | **663.84** |

   The binding adaptation plan reserves 60 minutes **before 05:30**, with final
   reporting to 06:00. Thus latest selection start is **18:26:09 Berlin** and
   latest confirmation start **21:50:24**. At Root's 15:46 anchor only **160.16
   minutes** remain for unfinished training, audit, assembly, runner review,
   runtime/source freeze, freshness audit and transitions before selection.
   A pure 06:00 deadline would instead yield 18:56 / 22:20, but that silently
   loses the existing 05:30 boundary unless explicitly amended before results.
   Starting confirmation 22:30 at the reserved rate ends 05:09:36, leaving only
   20.4 minutes to 05:30, or 50.4 to 06:00.

   Rates are historical, not a guarantee for P/PT or direct ensemble duels.
   A 10% slowdown adds **60.38 minutes** to the reserved full study; 20% adds
   **120.77 minutes**. Two active workers are an assumption, not an extra speedup.
   Use the slower measured representative rate and account for both-worker
   capacity, memory pressure, battery/charging and quota. The 35/25% battery rules
   remain unless the actual user explicitly supersedes them; permission to run
   on battery alone does not waive thresholds. Include all review/assembly/audit
   work outside the game-time estimate and preserve >=30% quota if still binding.

## Admission recommendation

Publish the exact performance amendment before fresh outcomes, incorporating
metric/key definitions and the corrected deadlines. Independently verify actual
runtime/source pins and central/remote seed provenance immediately before start.
If the complete required path no longer fits, decide **before 841 games** whether
to omit PT entirely under the existing contingency or label the study research
only with no current promotion. Once outcomes exist, retain sample sizes, gates,
nominee rule and source freeze; an interrupted confirmation is incomplete and
cannot promote. No fresh-data execution was authorized or performed by this review.
