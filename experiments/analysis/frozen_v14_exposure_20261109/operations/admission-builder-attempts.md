# Frozen-V14-exposure admission builder: check-only attempts

No admission was written by any attempt; no model bytes were loaded or rehashed by the successful check-only builder.

1. Root's first check-only invocation failed at the historical ON technical acceptance guard (`Accepted ON technical evidence differs`). The old accepted ON technical acceptance schema records `own_processes_ended` as `[owner_pid, worker_pid]`, not `original_processes_ended: true`. The builder now compares that PID list with its bound owner state, requiring complete/inactive state and worker return code 0. No old evidence was edited.
2. My next check-only invocation then failed (`V14 source-config is not bound by historical montage admission`). Inspection showed that the match-weight-comparison admission does not include that preparation wrapper in its `inputs`; the earlier match-weight technical admission does. Root directed that the already accepted wrapper be pinned directly by SHA-256 `a094376eca24e5054b0a14228f5861b9bccb832199954fd7957f1431af5ab69f`, checking its V14 source hash, metadata-source hash, normalized config fields and frozen=False setting. The false reference-input assertion was removed.
3. Final check-only invocation passed: profile `frozen_v14_exposure_20261109`, stage `technical`, expected HEAD `a87a2c14d2a3675fd567c22d43b9d328d5deb0f8`, 113 bound inputs, 427 source files, `admission_written=false`, `started=false`. Output path `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/frozen_v14_exposure_20261109/technical-v1-admission.json`. The phase output directory and admission file remain absent.

Final external builder SHA-256: `6baef3e53ec7e80ff2e513c62ca2a7e4f5f810b41d9e46fe12dbe3509d2adb28`.
