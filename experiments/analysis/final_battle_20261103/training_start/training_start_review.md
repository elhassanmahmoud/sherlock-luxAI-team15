# Actual training-start acceptance — 2026-11-03

**Verdict: PASS for the observed actual start and available early prefill evidence.** Training remains running and incomplete; this is neither final training acceptance nor performance/release qualification. No code, HEAD, plans, interpreter or weights were edited; no tests, replay, models, games or benchmarks were executed by this reviewer.

## Actual launch and immutable inputs

- Supervisor owner55001, child55028 control18 and55033 adapt18, distinct owned PGIDs55028/55033, with the exact once-only runarm arguments and fixed new run names. Actual process snapshot found these two heavy children and their lightweight coordinator, with no foreign model/evaluation/training process. An existing `caffeinate -i` is active.
- HEAD, prepared pins and state source agree on **7c906e16943ff7217afe1eae392834439cc76634**. Independently rehashed **238 source/interpreter-config/engine/protocol files**, the interpreter executable, **7 prepared inputs**, all **6 wrapper dependency pins**, **2 state-protected active weights**, and **5 cross-checkout active-weight/ZIP records**: zero mismatches. V14 remains98a07350…d3d8; primary ZIP remains88dfbe32…9dff9d6.
- Both prepared arms bind V14 member18 tensor3c79c583…ddb309, runseed29, identical1320-row opponent/map/side chronology. Independently checked seed arithmetic, alternating sides and120-prefill/1200-train boundary. Configs differ only in rescue_in_training=false/true. Known four reused prefill cards remain training-only as documented.

## Actual learner and early prefill evidence

- Real initial audit records show q=target equal to the prepared source component; both arms have identical q/target/Adam/agent-RNG/global-RNG hashes, with config difference confined to the treatment flag. Initial env_steps60000, learn_steps0, empty replay pos/size0/maskdim1, shared canonical side ownership, learning enabled, autosave disabled and no recent losses match the fixed start. The previously reviewed runtime prove_initial checks the live Adam class/empty state and actual parameter ownership; this reviewer inspected those emitted records without opening checkpoints or constructing learners.
- At the independent row snapshot, control had **38 complete prefill games** and treatment **37**. Every available row matched its prepared opponent/map/side/phase chronology,303 steps and point-countingv2. All remained at0 updates with unchanged q/target/optimizer, expected env-step progression, learning disabled, and303 actual act/update calls plus positive checked replay transitions and SHA transcripts.
- Control recorded0 rescue-unit steps/0 changes. Treatment already recorded **176 rescue-unit steps and41 rescue-helper action changes** in prefill, demonstrating actual opt-in activation. Totals of actual checked final-action/replay transitions were137464 control /133783 treatment. These are intermediate helper changes; later safety/SAP rules may still alter final actions, while the separate audit establishes final emitted/replay consistency.
- Complete120-game prefill proof, learned train-phase interventions, validation restoration, all180000 updates, final checkpoint/reload and final receipts were **not yet available** at this snapshot and remain required. Prefill changes alone cannot admit R36.

## Compute, quota, power and time

- Actual child environments have OMP_NUM_THREADS,OPENBLAS_NUM_THREADS,MKL_NUM_THREADS,VECLIB_MAXIMUM_THREADS,NUMEXPR_NUM_THREADS andPYTHONDONTWRITEBYTECODE all1. The invoked finetune path also calls the reviewed Torch single-thread limiter. This establishes configured limits; no additional model introspection was run.
- Actual power was58% Battery Power at the first snapshot, later57%; AC is false. Supervisor state reports this honestly. >=35% start and >25% continuation thresholds apply, checked every10 seconds; owned-group cleanup and the external STOP path remain in force. This is not an AC claim or guarantee of unattended completion.
- Root supplied its actual quota reading **33% used at15:57UTC**; that leaves67% available and respects the30% reserve/65% phase threshold. Quota API was not independently queried by this reviewer; supervisor correctly delegates quota checks to root/STOP rather than inventing a reading.
- Recomputed full-chain projection uses aggregate two-worker rates2.22 panel/3.0 direct,20% margin: remaining evaluation57058.56s plus remaining90-minute training allowance and3600s transitions. Snapshot required65946.3s against73828.6s available, leaving **7882.3s (2h11m22s)** slack through04 Nov13:30Berlin. Guard age was about10s. Actual learning-phase speed remains to be observed; two-hour training cap and full-chain guards must continue, and no incomplete data may qualify.

## Preceding technical smoke

Read both the disposable smoke script and its actual successful log. The log timestamp precedes official supervisor launch. It reports exactly two real303-step games on already-consumed seed500720, control player0/treatment player1,0 optimizer updates, q/target/optimizer unchanged and protected files unchanged. Final-action audit checked303 act/update calls each and3608/3585 real replay transitions, including canonical-to-world mapping through the actual boundary. The script forbids official run records/launch before smoke and never saves checkpoints/buffers/CSV/run records. Both smoke games recorded0 rescue changes, so the smoke supports mechanics/no-learning only; it does not itself establish rescue activation or strength. Actual early treatment prefill now provides intervention evidence separately.

No material start defect found. Keep the current source freeze and finish actual-run acceptance before any candidate admission.
