# Independent actual selection-start verification — 4 November 2026

**PASS for the observed start, frozen identities, schedule and configured resource limits.** This is a bounded start verification, not a result review. No fresh performance CSV or outcome log was opened; no model was loaded, game/test started, source edited or job duplicated. Only process/state metadata, pinned evidence, source bytes and model-file hashes were inspected. No ongoing polling is requested or performed by this review.

## Actual running process and resources

Selection state is `running`, started 07:22:38.897977 UTC / 08:22:38.897977 Berlin. The observed owner is PID91519. Its actual child PID/PGID91541 executes the intended Python3.13 framework interpreter with `-B -m scripts.par_eval`, baselineV14, `--first361000 --n20`, the exact local six opponents plusdefault, `--workers2`, and the expected new baseline-panel CSV path. The index translates to absolute seeds861000–861019.

The child has exactly two observed multiprocessing model workers, PIDs91546/91547, both in owned PGID91541; PID91545 is the multiprocessing resource tracker. A bounded Python-command snapshot found no additional training/evaluation supervisor or par_eval process outside this owned tree. The owner and par_eval parent are orchestration processes, not extra model workers.

Actual inherited settings on the par_eval parent and both workers are OMP_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1, MKL_NUM_THREADS=1, VECLIB_MAXIMUM_THREADS=1 and NUMEXPR_NUM_THREADS=1. The unchanged worker path calls `limit_threads()`, which sets Torch intra-op threads to1 before game execution. This verifies configured compute limits; it is not a claim of one OS thread per process. The engine/runtime creates background threads (58 thread rows per worker were visible), so raw OS-thread count is explicitly distinguished from the configured Torch/BLAS limit. No model attachment or runtime injection was used.

## Exact source, freeze and plan

Actual HEAD equals the externally pinned `bed06df3335caa4d7a79c928132143a9c7e0a8fc`.

- Freeze SHA-256: `c01a9f059fb165767e216683db95dc82a29c814ad7073a37585e98579c632e13`.
- Selection-plan SHA-256: `ece414c4d1247753881b4910206fb1233bc4498be156d587673fbc78b2d9cd0a`.
- Independent-auditor SHA-256: `0722ff67da35b9b50ba71cd3f49340fe1024cba14965f27ed5dd29410eb7c530`.

All match `/tmp/sherlock-breadth-20261104/prelaunch_pins.json` and the actual state. Read-only `check_plan`/freeze verification succeeded against the live filesystem:254 pinned source/evidence files,10 frozen weight files, exact interpreter/executable/engine identity and exclusive study/phase reservations. The state source-before identity equals the live freeze. This verification imported no Torch, JAX or Lux model stack.

The actual five-job selection schedule totals920games. Reconstructing the fixed optional confirmation schedule without preparing or launching it gives3,840games:80panel/default maps,320extraSolution maps,160separate direct maps. The full400Solution maps and exact half-win nomination, unchanged seven gates, bootstrap and extraSolution exclusion from panel weighting remain frozen. The current candidate paths are the separately builtSOLO28 andFO42 artifacts, not oldFT18 nominees.

## Evidence and original pilot preservation

The freeze binds the protocol, candidate manifest, actual candidate review, original pilot receipt and its CSV hashes, seed-freshness archive, weights mapping, amendment review and independent auditor. The actual candidate review reports PASS, ordered tensor equality and exact rawV14config for1and42members. Frozen hashes match the current bytes; this start verification does not independently reload those models.

The original pilot's entire relevant runtime source is unchanged: direct byte-hash comparison passed for24 current files comprising par_eval/common/experiment/scoring, Sherlock agent modules and course runtime modules against the pilot source-before receipt. The source change since the pilot is therefore the already reviewed orchestration/sample allocation amendment, not a changed agent/game runtime.

The pinned freshness evidence covers all seven registered local worktrees, proposed screen861000–861019, completeSolution862000–862399 and direct863000–863159 ranges. It reports no observed consumed-seed or prior JSON-interval overlap, no invalid seed values, errors or source mutations. Explicit limits remain: seedless records cannot prove absence, and undocumented external-machine experiments are unknown. The amendment remains recorded before fresh measurement, with original rejected admission and44-game pilot preserved.

## Admission and limits

The actual start quota receipt is59% used /41% remaining, sourced from the usage tool at07:20:00.271 UTC, less than15minutes before launch and below the65% new-phase threshold. Actual admission reserves the entire4,760-game chain:4,360panel-class and400direct games, using the upward-adjusted pilot rates3.3477221296883988 and4.506549020734383 seconds/game, multiplied by1.2, plus1,200transition seconds. The recorded projection is19,678.425712482207 protected game seconds. Hard game cutoff remains13:30UTC /14:30Berlin, with90minutes for final QC/closure before16:00Berlin.

This PASS establishes that the observed launch matches the accepted protocol and evidence. It does not establish any candidate's performance, completed screen, confirmation eligibility or release qualification.
