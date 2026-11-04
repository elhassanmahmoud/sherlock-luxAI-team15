# Task 2 fix 1 scoped review

Verdict: **ADDRESSED**. No new breakage found in the scoped correction. Task 2 is approved against the earlier review, with the parent-owned production provenance/completeness checks unchanged.

The local `reserve_output` wrapper (`scripts/student_action_distill.py:43-52`) now checks packaged submission paths `agents/Gruppe15` in the current, primary and historical checkouts before any directory creation. `checked_output` rejects descendants and filesystem aliases; the explicit ancestor check also refuses an output that would contain the protected tree. Delegation to `_reserve_output` retains existing occupied-path, raw-weight, root-level package and input-source protection. The producer implementation is not imported or changed.

The fix diff changes only the helper import/alias, adds the wrapper and adds four focused regression cases (three checkout roots plus a repository symlink alias). Existing training call sites resolve the new local wrapper. Training, objective, calibration, dataset loading, export and deadline logic are unchanged. The imported stable output helper remains included in source pins.

Evidence reviewed: `/tmp/sherlock-action-student-20261104/task2-fix1.diff`, the appended implementation report, current helper source and added regressions. The implementer records three regression failures before the fix and 32 passing Task 2 tests after it. This reviewer did not repeat tests, launch jobs/games, or edit source; only this review report was written.
