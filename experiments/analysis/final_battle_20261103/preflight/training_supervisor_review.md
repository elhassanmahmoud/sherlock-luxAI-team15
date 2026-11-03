# Independent training supervisor review — 03 November 2026

**Verdict: PASS. No remaining P2-or-higher finding in the final reviewed version.**

Read-only scope: `scripts/final_training_supervisor.py`, `tests/test_final_training_supervisor.py`, and the current final Battle plan. No repository edits, test reruns, models, games, training, full suite or server execution by this reviewer. The author reported 17 focused tests passing in 0.93s, including real lightweight child-process lifecycle tests; that result was not independently rerun here while root coordinates its checks.

## Timing and whole-chain reservation

Lines63–74 reserve the full-roster performance chain: screen7,840 panel games plus960 direct games; confirmation11,200 panel games plus800 direct games. Thus19,040 panel games at2.22 wallseconds/game plus1,760 direct games at3.0, with20% margin, at least90 minutes initial training allowance and60 minutes internal transition allowance. The initial required budget is66,058.56 seconds. These historical rates already reflect two-worker throughput; there is no second division by two.

The fixed cutoff is04 November12:30UTC /13:30Berlin. New training starts are refused at/after02:00UTC /03:00Berlin. Continued training has a two-hour cap. `elapsed()` uses the maximum of monotonic and wall elapsed time, so a sleeping machine does not silently preserve the training budget. Admission is checked before children, throughout polling, and after receipt validation. No performance runs are launched by this supervisor.

The supervisor starts before any new evaluation observations exist, so its evaluation floors are fixed historical values. The performance supervisor separately owns observed-rate/slowdown admission once evaluation jobs run.

## Resources, input freeze and external controls

The common repository resource lock is held across admission, both training children and final receipt validation (lines358–371). Exactly two named arms and fixed run names are generated; `spawn_owned` rejects duplicate/excess owned arms, and thread environment limits are passed explicitly. Foreign Python model/test processes are checked before launch and in guards; owned groups are exempted by their registered PGIDs.

The prepared manifest is bound to the prescribed V14 source hash, both arm roles, component18, seed29 and the role-specific rescue flag. Prepared initialization files are hashed, extra weight/replay files are refused, active V14 files must retain their prescribed hash, and the source/HEAD/plan/interpreter/engine identity is rechecked by guards. Fixed run directories, run records and existing output directories cannot be adopted as resume inputs.

The STOP file is checked in the0.2-second loop and each full guard. Power is read and validated with fail-closed parsing; a new start on battery requires35%, continuation requires>25%, AC is permitted. Full guards are scheduled every10 seconds, with bounded power/process-snapshot commands. Actual Codex quota is intentionally delegated to the root/heartbeat, as required; the state explicitly records the external-admission obligation rather than inventing an API or bypass.

## Ownership, failures and no duplicate start

Child launch blocks HUP/INT/TERM until a new process session/group, Popen object, owner PID and PGID are registered and journaled (lines237–256). The child restores its prior signal mask before exec. Cleanup only signals a child with matching current owner PID and registered Popen PID/PGID, escalates TERM to KILL and waits for both process and group disappearance. Child failure, STOP, guard failure, receipt failure or parent signal enters cleanup. Cleanup errors leave the state failed and retain unresolved child identifiers in `active`, rather than claiming every child stopped.

The initial review raised an early-import duplicate-start window: if children were killed before creating their run directories/records, a different supervisor output directory could otherwise permit relaunch. The author corrected this before the final review. The final version creates `prepared/supervisor_launch.json` exclusively with fsync **before any Popen**, includes its hash in guarded inputs, and rejects any prior marker. This closes the window even if children never reach their own initialization records. The focused test suite contains an exclusive-reservation test.

Completion requires both zero exits, no leftover groups, both validated final receipts, and a final successful guard. Failure cannot become complete; no model promotion or installation is implemented.

## Tests inspected

The test file covers fixed arm commands/thread settings; power parsing and35/25 boundaries; full-chain arithmetic/deadline/two-hour rejection; foreign-process exclusion of owned groups; atomic receipts/output exclusivity; exclusive pre-child launch reservation; real lightweight new-process-group registration and termination; rejection of an unowned group; paired fake-child success, nonzero exit, guard failure, bad receipt and STOP; saved failure/cleanup state; and full-guard input/foreign/STOP calls.

No new test execution was performed by the reviewer. Live initial/prefill/update/end/reload and strength acceptance remain the separate real-data audits described by the main plan.

## Nonblocking operational caveat (P3)

`safe_path` rejects any symlink ancestor before its final resolve (lines112–116). On macOS, `/tmp` and `/var` are system symlink aliases, so an invocation using literal `/tmp/...` or `/var/...` for prepared/output paths will fail closed. Root should use canonical `/private/tmp/...` / `/private/var/...` or resolve those arguments before invoking. This is a usability caveat, not a resource/data integrity failure. STOP uses its fixed `/tmp/...` location directly and is unaffected.

The Python-command snapshot filter can conservatively reject a Python inline command containing model-module text; this also fails closed. It is not a reason to relax the resource lock or run tests concurrently with training.

Reviewed SHA-256 identities:

- Supervisor: `1b35745c175f5adca714e9762768c9ca81224a5ee456abad1dea64132e9fdb76`.
- Tests: `927c9f2f87211577b7b7c391f168929d54a01e3204e151e74eb4896ab2736194`.
- Plan: `c0f723a83cca3a0689a9334b49e6e39d0873f37737f9ef88b9b7277e0512b22a`.
