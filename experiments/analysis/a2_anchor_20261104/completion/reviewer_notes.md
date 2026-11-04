# Independent completed-diagnostic review

Completed-data audit PASS; no data-integrity or selection defect found. Read-only review of the fixed 920-game A2 teacher-anchor diagnostic at frozen HEAD `09c69349afc020a7b2418c249657a5698c472964`. No game, training, model inference, repository/source edit, HEAD update, commit, or subagent was performed. Outputs are confined to this temporary review directory.

## Actual execution and integrity

The first attempted audit command used `.venv/bin/python` from the study worktree and failed before data read with exit 127: `zsh:1: no such file or directory: .venv/bin/python`. The successful rerun used `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python`, with OMP, OpenBLAS, MKL, VECLIB and NumExpr thread environment variables all set to 1. `audit_results.py --data-ready --directory <diagnostic> --out-prefix /tmp/sherlock-a2-anchor-20261104/diagnostic_review` exited 0. The earlier 73 fabricated selfchecks were not repeated.

- Exactly 720 panel and 200 direct records across 11 CSV files; complete, unique prescribed card/side/opponent keys. Panel cards 867000–867019 and separate direct cards 867100–867119. All 920 records finite, 303 steps and point-counting version 2; result, strict win, match-win counts and point-win fields consistent. No draws in this completed sample.
- Reviewed full JSON results, opponent/side summaries, per-card contrasts, direct win/score complements and screen values. Every CSV digest agrees with the controller completion state and the independent audit output.
- Independently rehashed **266 source pins and 153 input pins**, all equal to the admitted protocol. This includes four active V14 files across both working copies, the primary submission ZIP, candidate weights, engine files, archived admission files, executable/interpreter pins, helper scripts and seed lists. Counts are recorded-file counts, not a count of distinct physical bytes.
- HEAD remains the frozen commit. Protocol/controller/auditor hashes agree with their state/archive records. All **11 controller jobs and 11 guard records completed with returncode 0**; state has no running jobs and `pins_after_equal=true`. Controller ended 2026-11-04T20:36:31.197925+00:00. Scanned 22 guard/controller log files: no traceback/error/exception/action-failure patterns. This is a log scan, not a proof that every conceivable unlogged fault is absent.

## Exact observed strict wins

| Role | Solution /40 | Panel /120 | Direct vs V14 /40 |
|---|---:|---:|---:|
| V14 | 40 | 101 | — |
| A2 | 39 | 95 | 16 |
| CONTROL25 | 34 | 81 | 12 |
| CONTROL26 | 31 | 75 | 6 |
| ANCHOR25 | 36 | 96 | 14 |
| ANCHOR26 | 36 | 88 | 12 |

## Paired method contrast

| Training seed | ANCHOR minus CONTROL panel | Exploratory 95% whole-card CI |
|---|---:|---:|
| 25 | +12.500000 pp | [+2.500000, +23.333333] pp |
| 26 | +10.833333 pp | [+0.833333, +20.833333] pp |

The panel bootstrap uses 20 whole cards, preserving both sides and all three opponents together; 5,000 resamples, NumPy default_rng seed 0, percentile 95% with linear quantiles. ANCHOR25 minus A2 panel is +0.833333 pp [−8.333333, +10.000000], ANCHOR26 minus A2 is −5.833333 pp [−15.833333, +4.166667]. Both anchors score 36/40 against Solution versus A2 39/40. Gains relative to their controls do not establish improvement relative to the starting A2 or V14.

## Prespecified selection

**Selected for later confirmation: none.** Only ANCHOR candidates are eligible. ANCHOR25 passes panel >= A2 and panel > paired control, but fails Solution >= A2 and the >=24 strict direct wins threshold (14/40). ANCHOR26 passes only panel > paired control; it fails panel >= A2, Solution >= A2 and direct wins (12/40). No ranking tie-break is reached. Panel and Solution use draw-half scores; direct threshold uses strict wins. With zero draws this distinction does not change the observed decision. No control, A2, post-hoc ensemble or fallback is nominated. This diagnosis provides no release qualification; V14 remains the protected submission.

## Interpretation limits

The positive method contrasts are conditional on these two trained checkpoints and the 20 local panel cards; they do not precisely estimate variability over training starts. All intervals are exploratory and unadjusted for multiple comparisons. Seed freshness was admitted from a local inventory; undocumented/external trials remain unknown. CSV consistency cannot independently reconstruct engine scoring. V14's observed 40/40 against Solution is a sample result, not a population guarantee. The fixed 0.1 anchor improved the observed panel relative to control in both starts, but this alone neither proves the proposed forgetting mechanism nor qualifies a stronger agent. A failure of this fixed-weight intervention is not a rejection of all stabilization methods.

Raw result JSON: `diagnostic_review.json`; rendered review: `diagnostic_review.md`. No new confirmation or replacement is authorized by these outcomes.
