# Compact ensemble comparison requested08.11.2026

## Authority and design

User asks fewer games comparable to earlier versions. Root stopped the just-started7800gamephase before inspecting any outcomes. Controllerstate stopped, no ownedprocesses and no resultCSV persisted. Unknown actualparties executed; exclude original1400000–1400099 and1401000–1401099 from newstudy. Preserveall oldlaunch/state/logs. No automaticrestart or reuse.

Same auditedV14/A39/B39/ALL42/REPLACE36models, identicalinferencecfg, no newtraining. Same local6panel plusdefault, same score/strict-win gates andranking. REPLACE36remainsdiagnostic. Atmostonequalifiednominee, onefixedconfirmation. No extensionuntilsignificance; inconclusive countsasnotqualified.

Selection:20freshmaps1700000–1700019, bothsides,5roles×7opponents=1400games;4candidatesdirectV14 on1701000–1701019,bothsides=160.39jobs,1560total.
Confirmation:100freshmaps1800000–1800099, bothsides, V14+nominee×7opponents=2800games; nominee directV14 on1900000–1900199,bothsides=400.15jobs,3200total. Totalmaximum4760, comparable topreviousnetworkbreadthstudy4760performancegames; allocationdiffers deliberately. Keepalloriginalsevenconfirmationgates plus3additionalchecks unchanged; lowerprecision acknowledged. Defaultstrict99%means40/40selection and198/200confirmation. Statisticalmethodsunchanged:pairedwholemapbootstrap5000PCG64seed0,95%unadjusted; selectionexploratory.

## Implementation requirements

Extend existing compare/eval_supervisor with explicit immutable profile: defaultoriginalfull20261107 preservesalloldplan/tests and validatorexpectations. Newprofilecompact20261108 usesfixedcounts/seedsabove, NOT arbitrarybudgets. Add --profile option controller, persistinstate+launch; analysis readsplan.profile withlegacydefault. Mapprofile tofixedanalysisbase experiments/analysis/ensemble_diversity_20261108_compact andprotocolpaththisdocument; full retainsoriginalbase/protocol. No globalmutablemonkeypatches.

Profilemustpropagate through validate_plan, completeframechecks, selection/confirmationchecks,analyze,controllerbuild_state,selection_evidence,CLI. Confirmation must recompute entirematchingprofileselection and exactnominee beforeopeningconfirmseedfiles; fixed39jobs1560games vsfull39/7800. Same rolepaths,opponenthashes,receipts,source/provenance,power,processlimit,quota100userauthorization. Newprofileownselection_launch/confirmation_launch, originalreservationsuntouched. Jobseedpaths confinedtoprofilebase. Originalfunctionsdefaultlegacyprofiletoavoidbreakingoldrecords/tests.

Task1 filesonly scripts/ensemble_diversity_compare.py, scripts/ensemble_diversity_eval_supervisor.py, tests/test_ensemble_diversity_compare.py, tests/test_ensemble_diversity_eval_supervisor.py. TDD newprofilecomplete1560/3200syntheticfixtures andgatebehavior, malformedcounts/seeds/mixedprofiles/nomineetampering, defaultoldprofilepasses. Fullrelevanttests beforeanymodelrun. No games/modelweightchanges. Implementer no subagents, commitownfiles/report. Rootownsdocs/newjobgeneration/prelaunchseed-audit.

Rootpreflight: userapprovedremainingquota,noagentreset; atmosttwo computeprocesses,AC100%, frozenHEAD throughselection/confirmation; freshquota. Clear sharedSTOP onlyafterverifyingoldownprocessesabsent, archiveSTOPasuser-directedtermination first. Verifycandidatehashes, local seedhistory, independentreview, commit/pushbeforelaunch. No outcomepeekfromoldincompletephase, neverclaimzero actualgames merelybecauseCSVabsent.
