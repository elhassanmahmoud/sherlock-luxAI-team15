# Actual network-breadth protocol review — 4 November 2026

Reviewed actual `/Users/moayedshawesh/Desktop/KI/sherlock-november-followup/docs/superpowers/plans/2026-11-04-network-breadth.md` and `/tmp/sherlock-breadth-20261104-inventory.md`, plus the relevant runtime/statistical/source files. This replaces the earlier feasibility proposal in this temporary report; the actual chosen protocol is the one assessed below. No models, games, training, tests or repository edits were performed.

**Decision: PASS for the selected sample allocation, arithmetic, statistical gates and source lifecycle.** One factual rationale correction is needed; see below. Implementation and actual readiness are not yet accepted by this protocol review.

## Fixed study assessed

Exactly SOLO28 (V14 member28, zero-based `[q,*ensemble]`) and FO42 (all36 V14 members plus `all24fo.pth` members18–23), same V14 inference configuration. The inventory supplies a defensible bounded rationale and identifies42 distinct tensors; actual new artifact construction/reload still needs acceptance. The historical16/16 SOLO validation is selection evidence only, not a fresh superiority claim. The user explicitly authorized this new study after the previous study closed; old FT18 results, failed gates and prohibition on old-study nominee replacement remain intact.

| Phase | Arithmetic | Executions |
|---|---|---:|
| Screen panel/default | 3 roles ×20 maps ×2 sides ×7 opponents | 840 |
| Screen direct | 2 candidates ×20 maps ×2 sides | 80 |
| Confirmation panel/default | 2 roles ×120 maps ×2 sides ×7 opponents | 3,360 |
| Extra Solution confirmation | 2 roles ×280 maps ×2 sides | 1,120 |
| Confirmation direct | 160 maps ×2 sides | 320 |
| Total performance | 920 screen +4,800 confirmation | **5,720** |

Separate prescribed technical pilot: 3 roles ×2 consumed maps ×2 sides ×3 opponents =36, plus2 candidate roles ×2 maps ×2 sides direct =8, total44. These are additional executions, not fresh strength evidence.

Confirmation has400 distinct Solution maps/800games PER ARM,120 complete robustness/default maps,160 separate direct maps. Proposed blocks861000–861019,862000–862119,862120–862399,863000–863159 are mutually disjoint as specified; this review does not certify historical freshness. The coordinator's all-worktree/CSV/manifest audit must do so before freeze. The extra Solution rows cannot alter panel weighting, replace the first120maps or be counted twice.

## Runtime and cutoff arithmetic

Total timing classes:5,320 combined-panel games and400 direct games. Conservative two-worker throughput floors2.6 and3.5 wall seconds/game are already parallelized. Exact reservation:

`1.2 × (5320 ×2.6 +400 ×3.5) +1200 =19478.4 seconds =5h24m38.4s`.

The stated18,278.4 protected game seconds plus20-minute transition reserve is correct. Hard game end13:30UTC =14:30Berlin; final deadline15:00UTC =16:00Berlin leaves90minutes QC/closure. At unchanged floor rates, full screen's latest admissible start is08:05:21.6UTC =09:05:21.6Berlin. Pilot/setup precedes that admission and must be counted in actual elapsed time. Any pilot or completed-block slowdown can only raise the remaining forecast; no sample/count/gate reductions after outcomes.

The prior archived confirmation consumed6h53m20.307s for12,000games, so the selected bounded allocation is a rational adjustment made before new results. It does not pretend to retain the prior panel/direct precision. Small pilot startup cost may make its rates pessimistic; that is a feasibility constraint, not grounds to lower them after seeing outcomes.

## Statistical and lifecycle acceptance

The seven unchanged confirmation gates are correctly restated: panel delta≥+1pp and lower95%bound>0; Solution delta≥0 and lowerbound>−1pp; default≥99% and delta≥−1pp; direct lowerbound>50%. Whole-map paired bootstrap5000 draws,PCG64seed0 and linear2.5/97.5percentiles match the documented estimand. Panel uses6 equally weighted opponents on120complete maps; Solution uses400; default120; direct160. Smaller panel/direct samples have lower precision, explicitly acknowledged. No old/screen pooling, interim nomination, fallback nominee or team waiver is allowed. This is coherent even though it may fail to establish a modest improvement.

The different sources/candidates answer a new question; this is not a second FT18 confirmation. New branch/output directories/STOP/reservations and source freeze after the previous run's closure preserve the scientific boundary. Old source7c906e1 remains available via Git/archive; no active old run may be altered. Full current source/interpreter/engine/protocol/model/statistic identities must be bound from screen through confirmation, and remote merges confined to the other checkout until closure. Quota receipt age≤15minutes, no new phase at65%,30% reserve and fixed power/STOP/process ownership conditions are adequate protocol requirements; implementation still must enforce them.

Focused tests and independent review are proportionate to the selected changes when runtime agent/scoring code is unchanged. The historical1,075test pass is correctly labelled historical. A new package remains conditional on complete confirmation, independent data/technical acceptance, exact tensor equivalence and reversible protected-file transaction; failed/incomplete work leavesV14.

## One factual correction

The actual plan currently describes FO6 as six runs whose "Trainingsgegner weiter entfernte gegnerische Units berücksichtigten". This misstates `far_opp=10`. `agents/sherlock/config.py:90–97` and `features.py:267–270,359–368` show a change to the learner's target assignment: enemy-half point tiles farther than10cells from a unit receive lower priority. It is not a training-opponent change or distant enemy-unit observation mechanism.

Suggested replacement: **"FO42 ergänzt sechs Netze aus FO-Starts30–35, die mit far_opp=10 trainiert wurden: entfernte Punkteziele der Gegnerhälfte wurden nachrangig zugeteilt; ein Vorteil unter V14-Inferenzkonfiguration ist offen."** No additional experiment is needed to correct this source-backed wording.

## Implementation review checkpoints already communicated

- Historical fixed driver unchanged; imported launch functions must not accidentally retain old module deadlines/STOP/freeze via global bindings.
- Multi-file per-role summary must concatenate disjoint panel and extraSolution blocks, then verify exact120/400/120/160map counts. The old `frames[role]=frame` overwrite pattern is unsafe here.
- Use explicit local six-panel and the seven new-study gates; legacy `league_gates battle` CLI has different panel/Solution thresholds.
- Unique finite shape-compatible1/42ordered tensor states, exactV14config, no hidden second singleton member and no copied optimizer/replay; verify actual output reload.
- Synthetic complete/missing/duplicate/additional-key, summaryweighting, gateboundary, deterministicnominee, reservation, sourceidentity, quota/power/STOP/runtime/processtree tests before freeze. Actual pilot and all-artifact/freshness review remain root's task.

Available for subsequent actual implementation diff review. No implementation has been reviewed or accepted by this note.
