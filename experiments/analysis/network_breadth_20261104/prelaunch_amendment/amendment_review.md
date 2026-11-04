# Narrow pre-results allocation amendment review — 4 November 2026

**PASS. No substantive correction required in the reviewed amendment.**

Reviewed the actual Git diff of the study driver, its focused tests and the protocol, plus the matching independent-auditor diff, original admission rejection and existing pilot metadata/key sets. No games, models, training, tests or repository edits were performed. CSV inspection read counts and seed keys only; performance result values were not used.

## Exact amendment and arithmetic

Screen remains 920 games on 20 maps with the same two candidates and selection rules. Confirmation changes only panel/default exposure from 120 to 80 maps and extra Solution exposure from 280 to 320 maps:

- Panel/default: two roles × 80 maps × two sides × seven opponents = 2,240 games, seeds 862000–862079.
- Extra Solution: two roles × 320 maps × two sides = 1,280 games, seeds 862080–862399.
- Direct: unchanged 160 maps × two sides = 320 games, seeds 863000–863159.
- Confirmation totals 3,840; complete possible performance chain totals 4,760.

Solution still has exactly 400 maps / 800 games per role, the two blocks remain disjoint and exhaustive, panel weighting excludes the extra Solution block, and direct exposure remains unchanged. Default now has 160 games per role. Reduced panel/default precision is explicitly disclosed.

The actual driver diff changes only the two confirmation block definitions, confirmation total, future confirmation timing-class count and required panel/default map count. The seven gate thresholds, bootstrap implementation, exact half-win nomination ordering, candidates, configuration, timing floors, slowdown rule, reserves, deadline and quota boundaries are unchanged. Focused tests update those exact counts and verify 80+320 concatenation. The independent auditor makes corresponding allocation/shape/count changes and adds exact timing-class/range assertions; its statistical and decision rules are unchanged.

Actual pilot-derived rates are retained, not reduced:

- Panel: 3.3477221296883988 wall seconds/game.
- Direct: 4.506549020734383 wall seconds/game.
- Common slowdown: 1.287585434495538.

For 4,360 panel-class and 400 direct games, the protected game forecast is 19,678.425712482207 seconds. Including the unchanged 1,200-second transition reserve gives 20,878.425712482207 seconds = **5h 47m 58.426s**. The 13:30 UTC game cutoff implies a latest start of **07:42:01.574 UTC / 08:42:01.574 Berlin**, before any later measured slowdown. The protocol's rounded “about 5h48m” is accurate.

## Timing-only basis and preserved evidence

`original_admission.json` records rejection at 07:17:46.859541 UTC: the original 5,720-game chain projected completion at 14:10:01.861139 UTC against the unchanged 13:30 UTC cutoff. It explicitly records `fresh_performance_games_started=false`.

The original pilot remains complete with 44 games, five exit-zero jobs, source HEAD `3598bb8ee7011ac02914475fe9e7f9b68a3ab378`, and equal before/after source and weight identities. Independently recomputed hashes of all five pilot CSVs match their original receipt. Their only seed keys are the already-consumed 500720 and 500721. The study directory contained pilot/preflight evidence and no fresh-performance CSV, selection/confirmation state or freeze at this review snapshot. The amendment is therefore documented before any available fresh performance outcome, not a response to fresh win rates. This review does not claim knowledge of undocumented runs outside the inspected evidence.

The old plan/code and rejected admission remain preserved, pilot timing is not repeated or adjusted downward, and only orchestration/sample-allocation code changes after the pilot. The actual agent/model runtime is unchanged. A new reviewed source/freeze must bind this amended protocol before the first fresh game. All subsequent counts and decision rules remain fixed; an incomplete or failed confirmation cannot qualify a candidate.

## Verified identities and validation limits

- Study driver: `ddbe007a5486ec02e838c344dc59559ea5da9b9ef60c390ff4c8f9ae88e3900f`.
- Focused study tests: `79fa479b85b9afc62d4bfb4c2c3f1ade026edfe6f242a4520534a48e963f6630`.
- Independent auditor: `0722ff67da35b9b50ba71cd3f49340fe1024cba14965f27ed5dd29410eb7c530`.

The worker reports 31 focused tests passing in 4.13 seconds. The inspected independent synthetic receipt reports 59 checks passing, explicitly with no real results read and no model/repository-statistics imports. Neither test set was rerun by this reviewer.
