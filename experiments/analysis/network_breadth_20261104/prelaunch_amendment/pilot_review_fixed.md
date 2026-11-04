# Scoped pilot ownership re-review — 4 November 2026

**PASS. The original blocking ownership race is resolved. No remaining blocker was found in this scoped review.**

Reviewed `/tmp/sherlock-breadth-20261104/run_pilot.py`; actual SHA-256 matches the submitted identity:

`e705300aace7875e9c54d57041e5cc1107ac09a285067c3785db646d2dfdfee6`

SIGINT, SIGTERM and SIGHUP are now blocked across child creation, assignment to `current`, `early.CURRENT` registration, PID/PGID recording and receipt persistence. The small exec launcher restores the original signal mask in the child. The parent unmasks only after ownership is known, so an immediately delivered pending signal reaches cleanup with a registered child. Both normal and exceptional group cleanup are protected against a second signal; exceptional receipt finalization is also protected. Original handlers and the parent mask are restored on exit.

The prescribed pilot remains unchanged: consumed seeds 500720–500721, both sides; V14, SOLO28 and FO42 against Solution/V13/default produce 36 games, and the two candidates directly against V14 produce eight more. Total remains exactly 44 games in five sequential jobs, each with two one-thread workers. Commands, output paths, opponent definitions and receipt validation are unchanged by this fix.

The supplied stdlib regression was inspected. It injects a signal before `Popen` returns, checks a second signal during cleanup, and asserts that the owned group is gone, the receipt is incomplete, ownership was recorded, and child/parent masks and handlers are correct. The worker reports both cases passed; I did not rerun them.

No actual models, games, training, tests or repository changes were performed in this re-review. This closes the controller ownership finding; actual artifact/build acceptance remains the coordinator's separate launch prerequisite.
