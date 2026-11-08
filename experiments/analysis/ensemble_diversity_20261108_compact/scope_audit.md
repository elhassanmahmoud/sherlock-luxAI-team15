# Independent compact scope audit — 08 November 2026

The fixed compact design has **1,560 selection games + at most 3,200 confirmation games = at most 4,760 new performance games**. Confirmation only follows a qualified, fixed nominee. These are planned limits, not played-game counts. The stopped selection may have executed games without a persisted CSV; its actual count is unknown. Both complete old blocks (1400000–1400099 and 1401000–1401099) remain excluded.

| Phase | Arithmetic | Jobs | Games |
|---|---|---:|---:|
| Selection panel/default | 5 roles × 7 opponents × 20 maps × 2 sides | 35 | 1,400 |
| Selection direct | 4 candidates × 20 maps × 2 sides | 4 | 160 |
| Confirmation panel/default | 2 roles × 7 opponents × 100 maps × 2 sides | 14 | 2,800 |
| Confirmation direct | 1 nominee × 200 maps × 2 sides | 1 | 400 |

Selection nominates only A39/B39/ALL42. REPLACE36 remains diagnostic. Same V14 configuration, opponents, score/ranking and supplementary strict-win conditions; all complete roles required. Selection keeps panel score Δ≥0.5 pp, Solution score Δ≥0, default score≥99%, direct score≥50%, strict Solution win rate≥baseline and strict default win rate≥99%. Ranking: panel Δ, Solution Δ, fewer networks, name. No old/new pooling, candidate succession, second confirmation or extension until significance.

Confirmation retains the **original ensemble comparison** seven score gates: panel Δ≥1 pp; panel lower bound>0; Solution Δ≥−0.5 pp; Solution lower bound>−2.5 pp; default score≥99%; default score Δ≥−1 pp; direct lower bound>50%. Its three additional conditions remain Solution score Δ≥0, strict Solution win rate≥baseline, strict default win rate≥99%. At this sample size strict default requires 40/40 selection wins and ≥198/200 confirmation wins. Whole-map paired bootstrap remains 5,000 draws, PCG64 seed 0, unadjusted 95% intervals; selection is exploratory. Smaller samples reduce precision; inconclusive means unqualified.

The earlier network_breadth_20261104 study used **920 selection + 3,840 confirmation = 4,760 performance games, plus 44 technical games**. Its allocation was 20 selection maps; confirmation 80 panel/default maps, 400 Solution maps per model (800 games), and 160 direct maps (320 games). Compact uses 100 panel/default/Solution maps per model (200 games), 200 direct maps (400 games), more selection roles, and no additional Solution block. Thus equal maximum performance-game totals do not imply equal precision or identical designs. The historical study also used the stricter Solution interval condition >−1 pp; preserving original ensemble gates is not a claim of identical historical network_breadth gates.

Operational design requirements remain maximum two compute processes, unchanged frozen source/model/provenance checks, all tests before games, user-authorized quota cap 100 with fresh/known/allowed usage strictly below cap, existing power/STOP checks, and no agent quota reset. Technical/course/runtime/replay/backup acceptance remains necessary before any replacement; no Moodle upload is authorized by this audit. Existing historical files remain preserved.

Read-only evidence: `docs/superpowers/plans/2026-11-08-ensemble-compact.md`; `docs/superpowers/plans/2026-11-07-ensemble-comparison.md`; `docs/superpowers/plans/2026-11-04-network-breadth.md`; `experiments/analysis/network_breadth_20261104/confirmation/README.md`; current CLAUDE, latest Arbeitsstand entry and experiment protocol. Seed collision evidence, file counts, paths, ranges, exclusions and limitations are in `seed_audit.json`.

This is a **design/history/seed audit**, not an implementation or launch approval. No tests, fresh games, model loads, outcome analysis of the stopped selection, source changes, HEAD changes or commits were performed. Root must verify the implementation, generated fixed-profile plans, nominee binding, candidate hashes, process state, power and fresh quota before launch. No independent strength or freshness guarantee beyond recorded local seeds is claimed.
