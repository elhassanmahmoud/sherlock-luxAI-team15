# Runtime admission review — conditional, with a tight whole-chain window

Read-only review; no new games, fitting, or repository edits. The amendment fixes S30 from the same initialization, then two matched 40-prefill + 160-learn + 32-validation arms, then V14/S3/S30/CONTROL30/SAP0_30 on 20 reserved maps × both sides × three opponents = 600 fresh diagnostic games. S3 remains unchanged. Its 17.897-second distillation timing does not measure game throughput.

At the root's stated 14:17 Berlin planning point, 78 minutes remain until the 15:35 model stop. Existing timings support a provisional schedule, but do not establish a measured upper bound for the new 512-wide learner plus added signed-reward/transcript instrumentation. Reserve at least five minutes before 15:35. Check battery/quota and code/input freeze separately before every admission.

## Existing evidence

All paths below are under `/Users/moayedshawesh/Desktop/KI/sherlock-november-followup/experiments/`.

| Actual prior workload | Evidence | Observed wall time |
|---|---|---:|
| Nov 3 control18/adapt18, same finetune family, exact 60/20/10/10 mix, action/replay audit, paired simultaneous runs; hidden 256 | `runs/20261103_rescue_{control18,adapt18}/log.txt` and `manifest.json` | 46 clean adjacent 25-game intervals per arm: mean 3.2661 / 3.2965 s per learning game; worst interval 4.44 s/game in either arm |
| Same runs, 120 prefill games each | First two log timestamps | 326 / 328 seconds = 2.7167 / 2.7333 s/game |
| Same runs, 32 games per validation event (8 maps × 2 opponents × 2 sides) | Initial/final validation timestamps | 70–81 seconds = 2.1875–2.53125 s/game |
| Nov 4 V14, SOLO28, FO42 on Solution/V13/default, two workers, two already-known maps 500720–500721 | `analysis/network_breadth_20261104/pilot/receipt.json`, jobs `baseline_panel`, `SOLO28_panel`, `FO42_panel` | 29.0595 / 25.8339 / 30.3244 seconds for 12 games = **2.42162 / 2.15283 / 2.52703 aggregate wall s/game** |
| Nov 4 long V14/FO42 panels, seven opponents including the required three, two workers | `analysis/network_breadth_20261104/confirmation/state.json` | 2261.1796 / 2354.7097 seconds for 1120 games = 2.01891 / 2.10242 aggregate wall s/game |

The old RL arms each completed 120 prefill + 1200 learning + 96 validation games in 4449.6 / 4481.6 seconds. Their similar start timestamps and interleaved completion establish the relevant two-concurrent-arm cost regime. Training inference ignores extras in training mode; these were genuine single-256 learners. Current student arms are single-512, use 150 optimizer updates per learning game, and add three reward computations, feature/action transcript hashes and deadline checks. The historical action/replay audit and identity checks already existed. Consequently, their historical 3.3 s/game cannot simply be promised for the new arms.

`par_eval` calls `limit_threads()` inside each worker. Use one evaluation coordinator with `--workers 2`, and run roles sequentially; do not run two two-worker coordinators simultaneously. Its wall seconds/game already includes the two-worker speedup: **do not divide that figure by two again**. For training, one `runarm` process per arm means the two arm budgets overlap in wall time; do not sum both budgets when launched together.

## Conservative planning allowances

These are deliberately padded estimates, not newly measured current-run rates:

| Phase | Allowance and arithmetic | Wall budget |
|---|---|---:|
| Full S30 plus fixed-label/diagnostic/export work | 120 s, versus 17.897 s for S3; repeated label/diagnostic fixed costs mean 10× S3 is itself pessimistic, but retain 120 s only as a provisional allowance and enforce a deadline | 2:00 |
| Each arm's prefill | 40 × 5 s (1.83× prior prefill) | 3:20 |
| Each arm's learning | 160 × 8 s (2.43× prior mean, 1.80× worst historical block) | 21:20 |
| Each arm's validation | 32 × 5 s (1.98× slowest historical event) | 2:40 |
| Each arm's setup/export/full hashing/receipt proof | 120 s | 2:00 |
| **Two arms concurrently** | max of the identical per-arm budgets | **29:20** |
| Five-role fresh diagnosis | 600 × 3.8 aggregate wall s/game, i.e. 1.50× slowest matched three-opponent pilot, plus 120 s role startup/export/verification | **40:00** |
| **S30 → paired RL → fresh diagnosis** | 120 + 1760 + 2400 s | **71:20** |

At 14:17 this projects S30 complete by 14:19, paired arms complete by 14:48:20, diagnosis complete by 15:28:20, leaving 6:40 before the hard stop. A five-minute reserve gives the following latest starts: entire chain including S30 **14:18:40**; paired arms after an already completed/accepted S30 **14:20:40**; full 600-game diagnosis **14:50:00**. Existing setup/review time consumes this window. These times must move earlier if S30, startup or code review takes longer. A phase must still be admitted on its own fresh clock/resource evidence; no candidate-quality result can relax the budget. Start no new longer training block at/after 15:00. A partial arm is incomplete and cannot stand in for its fixed full budget.

**Admission conclusion:** the whole amended chain is plausible but tight at 14:17; these prior timings justify only a provisional, padded projection. For a stronger current-machine admission, measure the known-card technical panel below after S30 is final and before consuming reserved maps. If its rate exceeds the 3.8 aggregate wall s/game allowance, recompute the entire remaining budget and omit a phase that no longer fits. Do not silently shrink the 600-game diagnosis or compare selected complete subsets as the planned full result. Added RL instrumentation remains the principal unmeasured uncertainty; reject a blanket claim that this note proves the entire chain will finish.

## Precise optional technical timing command (not executed here)

Run from the student worktree, with no other heavy process. This plays 12 read-only evaluation games on **known validation maps 500000–500001**, never the reserved 864000–864019 range. It creates only a new temporary CSV. Replace the weights argument with the final accepted S30 path if its directory name differs; do not use a pending checkpoint. The existing S3 path below is real and already audited, and has the same inference architecture/config as S30.

```sh
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  /usr/bin/time -p /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B -m scripts.par_eval \
  --weights experiments/runs/20261104_student512/weights/agent.pth \
  --first 0 --n 2 \
  --opponents solution92,self:experiments/releases/20261101_v13_neb/agent_p0.pth,default \
  --workers 2 \
  --out /tmp/sherlock-student-20261104/known_card_timing_student512.csv
```

`par_eval` prints elapsed time; external `real` additionally includes interpreter startup. Divide external `real` by 12 for aggregate wall seconds/game. This is a technical timing fixture, not a fresh performance sample, and it does **not** time learning or the reward-audit wrapper. Refuse an occupied output path rather than overwrite/repeat it. The 12 known-card games add to operational work but are not part of the fixed 600 reserved-map games or either arm's learning/validation budget. A role with V14's 36 networks remains more expensive than single512 against some opponents; the prior exact V14/FO42 panel evidence is retained in the 3.8 s/game allowance for that reason.
