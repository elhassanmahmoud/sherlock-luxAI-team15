# Default guard and confirmation admission review

**Approved: no blocking error in the completed default guard or admission to the fixed confirmation. No confirmed improvement or promotion is established.**

Read-only independent audit, 22 October 2026 at 13:01 UTC. No model/engine imports, tests, games, frozen-repository edits, or confirmation-outcome inspection.

- Both default CSVs contain exactly 400 unique games: seeds 610100–610299 × player_0/player_1 × default. Every numeric field is finite; all rows have coherent match results/point results, valid counts/fractions, 303 steps and point-counting version 2.
- Both baseline and recovery won **400/400**, no draws. Each has 800 half-result units; Δ=0/800. The whole-map bootstrap independently reproduces [0,0]. Both committed selection safeguards pass: recovery ≥792/800 units (99%) and Δ≥−8 units (−1 pp). The degenerate empirical interval is not proof of equivalence or universal 100% performance.
- Every field and input CSV hash in `selection_default_summary.json` matches independent recomputation. The two recorded jobs completed successfully and their output hashes agree.
- The admission file is named **`confirmation_admission.json`**, not `admission.json`. It correctly hashes both selection summaries, `confirmation_jobs.json` and `source_freeze.json`, and nominates recovery. Chronology is correct: completed guard → summary → admission → confirmation launch. Its recorded quota snapshot is 42% used (58% remaining), above the plan's admission reserve; no separate account-query audit was performed.
- Confirmation commands correctly bind exactly baseline/recovery to the frozen V10 checkpoint, false/false versus true/false flags, `--first 111000` (=611000), `--n 800`, both `default,solution92`, and `--workers 2`. The expected total is 6,400 games. The running phase state hashes and embeds that same command manifest.
- HEAD remains `de2e95d451a22643a3f7351636d3348f7770a1aa`; all 128 frozen source/plan/engine/environment files, the interpreter and four protected/reference checkpoint files still match the freeze.

## Review of the pure-data validator

`/tmp/sherlock-v10-fixes-20261022/audit_pair.py` correctly enforces exact schema and expected unique keys, finite/integer values, course duration, result/point coherence, and two sides per planned map. Its map-level difference arrays and 5,000 `default_rng(0)` resamples correctly preserve paired sides. Default thresholds use exact integer inequalities; confirmation Solution uses Δ≥2 pp plus a strictly positive lower bootstrap endpoint. The defaults' all-zero paired difference produces [0,0] as expected.

Nonblocking limitation: the helper validates recorded output paths/hashes, but does not by itself assert the complete weights/flags/command/source binding or hash each CSV before and after parsing. Therefore retain the external immutable job-manifest/admission/source-freeze checks; those checks passed in this review. Run without Python `-O`, which disables its assertions. `all_phase_gates_passed` covers only this helper's opponent phase, not the still-required direct duel and stronger-opponent guard.

Audited helper SHA-256: `d81d3cf93c23cac2c88015fdde01ae5e5687c39847d888079f04fc4d6e743819`.

Admission SHA-256: `1a2fb2c54808c9cb7ab6bef16f2aa4c257e95b3169dc1fe2585ce92f34b2e6c5`.

Independent machine-readable checks and data hashes: `/tmp/sherlock-v10-fixes-20261022/default-admission-review.json`.
