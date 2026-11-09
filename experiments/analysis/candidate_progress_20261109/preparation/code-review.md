# Independent candidate-progress code review — PASS

Read the final implementation and focused tests against the fixed plan and `/tmp/progress-rescue-review.md`. No blocking findings. This is code/method acceptance only: four real technical games and the later120-game screen have not been performed by this reviewer. No tests, models or games were executed here; no repository edits.

## Core and timer

- Default `cand_stall_rescue=False` leaves the action path unchanged: `_act` skips timer observation/reset calls, the added per-UID hook is skipped, and tracker construction/reset uses no random sources. Original global `_rescue` calculation and its immediate `True` branch remain unchanged; original zone fallback remains after the new branch. Existing tensor/features/target/mask construction is unmodified.
- First eligible observation initializes age0. Only same-side/same-match consecutive global steps with both observation windows eligible can add one; the12thcomplete no-progress transition enables readiness. Duplicate observations do not advance age or clear per-step UID accounting. New game resets the object; match reset, reverse/gap/side/history discontinuity, empty-unit windows and training/disabled modes reset conservatively. Timer update is before the no-unit return.
- Candidate, point and dead masks are copied. Occupancy uses current nonnegative-energy own units against the previous copied candidate mask; continued occupancy is intentionally progress. Own score increase, added relics or new point/dead classifications reset age. Knowledge loss/retraction, score decrease and leaving the eligible match0/no-known-point/relic/candidate window reset. Candidate-mask churn alone is not incorrectly treated as classification gain.
- The early branch requires current step/side/match and an in-bounds currently valid candidate target for that UID. It does not restrict old global rescue. Counters deduplicate actual early hook queries by UID/step and do not count old global rescue. Existing target/nebula helpers and downstream rules retain their behavior; early rescue remains the predefined rule bundle, with its documented energy risks.

## Runner, owner and measurement validity

- OFF/ON eval copies preserve all36original member tensor bytes/order plus target; only normalized default configuration, `frozen=False` and the specified flag differ. Historical configuration normalization accommodates absent default fields while still comparing all explicit settings. Loader validation and post-game tensor identity checks reject fallback or mutation.
- Technical execution is exactly OFF/ON×(9946007/player_0,831006/player_1), one reused environment, no gradients. Actual combined native-action hashes, per-match v2 points/results and303/3reset/300decision counters bind OFF to archived passive V14 summaries. ON acceptance requires actual early-unit query exposure and native action-sequence divergence in the same fixed key. These remain live measurement assertions until the real runs; no real acceptance is inferred from fixtures.
- Performance admission separately binds Root's technical receipt approval, source, eval copies, two fixed cohorts and bounded card freshness. Three40-game jobs execute in2+1waves, each `par_eval --workers1`; owned-group exit is awaited before the next wave. No retry/resume or automatic technical-to-performance transition.
- CSV validation enforces40unique expected opponent/card/side keys,303steps, point-counting v2, finite integer outcomes, match-win/result/game-win and point-score consistency. Gates use actual ON wins≥OFF and direct actual wins≥24; draw half-points apply only to descriptive score intervals. Existing paired whole-card5000PCG64seed0statistics are used.
- The new `par_eval.require_no_agent_errors(agent,opp)` is called immediately after every `play_game` and before row collection. A nonzero caught-error counter on either own or self-play opponent raises; the worker result/whole-job CSV is not published as successful. Baselines without the counter remain compatible. This is the requested narrow measurement-validity fix and does not change policy decisions.

## Supplied verification inspected

Core final log:23synthetic tests passed in2.53s; runner/measurement final log:26passed in2.77s. Read the matching test source, including11/12boundary, mutable-mask copy, information resets, side/match/gap/training/OFF/new-game/current-target cases, actual synthetic `_act` final-action and bookkeeping contrast, fixed cohort/gate negatives and real `_worker` error propagation with fake environment/agents. No released archives or real engine games are needed by these suites. Tests were not rerun here.

## Final reviewed byte hashes

| File | SHA-256 |
|---|---|
|agents/sherlock/config.py|b2c48435bb4d39c178769d3e2f3a09a039a1a241da9af5c6675d912a901a2793|
|agents/sherlock/main.py|9946a7194a0757963db10195335d3dbd692b6ba95175f5c7debac9e198358f45|
|agents/sherlock/candidate_progress.py|3d6069aa3f27b81544230a4928e17feab141cf9c09cea8ed8a13c95b6b8c5a03|
|tests/test_candidate_progress_rescue.py|367c3037b94a47d850643ead3bce7e9029d734553e6ecac4087e76e5afd78440|
|scripts/candidate_progress_eval.py|de13aa221a2e951689bd65a61461bb343a987efe8cb5a01215aa2962bd42c7b3|
|scripts/candidate_progress_owner.py|0027cd4d7859fc542e4a276eb3b5e752ac90628378ada096e3be411dc5ba8d3d|
|scripts/par_eval.py|93f6f98d2cf042c379f7d560b85934e4931cf6751997e021ae9364726a4e1cdd|
|tests/test_candidate_progress_screen.py|0240bf66a767086fdd785908c3edeb6747ba8ac9b5eecc151945c44ff52235de|
|/tmp/candidate-progress-impl/green-final.log|f3f4b387f12f52497eb89105ceb5be5194f1401c17da4feef0abb4faefbe7fd3|
|/tmp/candidate-progress-implementation/green-2.log|fe9130aac4572fd64bfe12fc669d9c2b573d031c1cb4b6b9f575970acba85dd6|

No claim of real OFF reproduction, ON exposure, screen nomination or improved strength is made. Root must bind these exact bytes before actual phases and retain the separate real-result acceptance gates.
