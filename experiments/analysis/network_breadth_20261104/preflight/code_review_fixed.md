# Scoped fix and pilot-controller readiness review — 4 November

No source edits, models, games or tests executed. Reviewed only the ranking correction/new regression and the separately new external44gamecontroller. Worker reports the full-CSV regression failed before the fix and31focused tests passed4.19s after; those runs are not my executions.

## Study implementation: PASS, original P2 addressed

Actual hashes match the supplied fix:

- `scripts/network_breadth_study.py`: `007cf1347f27c37435654cea33a3c0a60caa03deed92b7377a0a53ad8fe5d683`
- `tests/test_network_breadth_study.py`: `35cd17c8a2d4452eb9c4ee99d8e125cce0a04863d464cb9c82fbcfe47d15eec5`

`nominee` now ranks exact integer half-win deltas (`2*wins + draws`, candidate minusbaseline), first overthe sixpanelopponents, thenSolution, thennetworkcount/name. Equal validated screen denominators make this equivalent to mathematical score ordering without per-map float noise. The new regression constructs completeCSVresults with fiveequalwins placed differently acrossmaps, asserts the actual two differentfloatestimates and expectsSOLO28. Gates/statisticalestimates remain unchanged. No new breakage found within this scoped correction; the sole earlier studyfinding is closed.

## External pilot controller: correction required before launch

Reviewed `/tmp/sherlock-breadth-20261104/run_pilot.py` SHA256 `ad1488eb8b17e51650ae9795276b9bd9a010bef7daf9e1ed3aa6733866c0cac9`.

**P2, lines64–67: child process registration is interruptible.** SIGINT/SIGTERM/SIGHUP are unblocked while`subprocess.Popen`creates the new session, before the returnedchild is assigned to`current` and itsPGID saved. A signal afterchildcreation butbeforeassignment raises into the outerhandler while`current` is stillNone; itscleanup cannot find orstop the newly launchedpar_evalgroup and itsworkers. A stoppedpilot can thereforeleave compute running withoutownership/deadlinecontrol.

Use the already-reviewed study.run_job protectedregistration pattern: block those signals acrossPopen+ownership/receiptregistration, use the smallstdlib exec-launcher torestore the childmask, thenrestore the parentmask onlyaftercurrent/PGID areknown. Mask cleanup aswell so a secondtermination signal cannotinterrupt ownedgroup shutdown/receiptfinalization. This is a narrow controllerfix; no newgameexperiment or broadtestrequest is needed.

Other bounded checks passed: commands use theintendedPython andfollowupcwd; absolute500720–500721seeds correctly map throughjob_command to--first720;three12gamepaneljobs plus two4gamedirectjobs equal44; correctSolution/V13/defaultandV14opponents;eachcommandexplicitly uses2workers withtheone-threadenvironment;exclusive resource lock andone-shot outputdirectory; completeCSVvalidation andhash/exitcodechecks; before/aftersource+weightidentity; monotonicwallreceipts inexactpilot_rates shape; no outcomes usedforselection. FOsource/opponentpaths exist; actualcandidate artifacts are correctlystill absent pending theapprovedbuild.

Finallaunchreadiness remains conditional on fixing this solecontrollerownershipissue and actualcandidate/buildacceptance. The newstudycode itself is accepted bythisreview.
