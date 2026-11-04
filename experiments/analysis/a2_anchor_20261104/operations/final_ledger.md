# SDD ledger — plan: docs/superpowers/plans/2026-11-04-a2-teacher-anchor.md

Start: 2026-11-04 20:10 Berlin. Base bb21f4c. Branch improvement/a2-teacher-anchor-20261104; current isolated worktree reused. Remote identical. No running study jobs. Account 25% used, battery 100% (not AC). User explicitly approved implementation and Subagents; prior publish authorization retained.

## Preflight
| Task/interface | Check | Ruling |
|---|---|---|
| 1 | No-grad, excluded rows, output guards internally consistent | proceed |
| 2 | Observation-only hooks, plain replay equivalence, per-match resets | proceed |
| 3 | Training-only adapter, original TD equivalence at zero, fixed positive loss | proceed |
| 4 | Consumes completed/pinned models, separate fresh seeds, no optional mixtures | proceed |
| 5 | Documents actual evidence, protected V14/ZIP, safe publication | proceed |
| 1→3 | Same collector loader and split; diagnostic vs training indices disjoint | loader shared read-only, no shared writes |
| 2→4 | Old cases used for diagnosis, new seeds for strength | never mix observations with fresh win-rate |
| 3→4 | Final-only model/receipt contract required | root blocks games until independent review |
| 4→5 | Full raw rows/counts/uncertainty before strength claim | independent audit required |

Ruling: New explicit implementation request renews work after prior 18:00 deadline. Reserve today's submission preparation: no new training after22:15, own games end23:00, report/push target23:20. Missing time for release confirmation leaves V14 unchanged.
Ruling: Source/runtime isolation can be implemented with restored experimental adapter, not edits to production agent. If wrapper cannot preserve required invariants, report before integration.

## Tasks
- [x] 1 Retention diagnostic
- [x] 2 Loss traces
- [x] 3 Anchored training adapter
- [x] 4 Actual controlled trials/comparison
- [x] 5 Evidence/documentation/publication

## Progress 20:22 Berlin
- Spec/plan commit98df2d5; approved scope implemented without new permission loop.
- Baseline109 tests passed42.11s (collect/actiondistill/rewardtrain/finetune); no model jobs active. Seed inventory8worktrees/13241paths: no observed867000/867100 consumption/overlap, with explicit seedless/schema limitations. Guard cleanup7cases passed.
- Task1 implementation24tests; review oneP2 nested output inside dataset boundary. Fixround1 sent to original implementer; no actualcorpus yet.
- Task2 implementation10tests; accidental wider point-counting integration run: five completed known-seed900011 episodes +15 counterfactual terminal steps, sixth episode interrupted. This is technical verification, not any newstrength sample. Exact partialsteps unknown. Explicitly record, do not conceal or foldinto planned24.
- Task3 original engine left untouched: two internal prepared dirs per outerstudy, each runs originalcontrol only; unused sap0 init excluded. Allows manifest/audit semantics to stay honest.
- Own awakePID76404 pinned at /tmp/sherlock-a2-anchor-20261104/awake.json; stop at closure. Old foreignfiles and protectedweights/ZIP initial hashes stored in initial_state.json.

## Progress20:28 Berlin
- Task1 P2 fixed/re-reviewed;26testsrootpassed2.69s. Commit9e384a8. Actualretentionbefore complete4s on68687excludedrows, independently467checks full5models. A2agreement.867035 vsCONTROL27 .767438/28 .810328 andSAP027 .766462/28 .799205. Preference drift observed, causalforgettingunproven.
- Task2reviewaccepted10tests;commit1206e63. Prescribed12plain/observedpairs completed24executions, all303steps/3matches, everyactionandhistoricalresultidentical. Trace interpretation delegatedanchor_retention_audit. SourceHEAD1206e63 preservedthroughtraces.
- Task3implementation27tests, reviewP1: finetune CSVroundsmean_loss5decimals butnewvalidator comparesunroundedtoo tightly; originalimplementerwillfix aftercurrentfullsuite. No realstudytrainingadmitted.
- Task3testincident:13completedtemporarysyntheticstudentprefillgames455000–455006, zeroactualupdates, no validation/receipt;14thpartialunknown. Original5evidencefiles preserved SDD/task3_test_incident/. Separatetechnicalexecutions, notstudy928. Regressions now usefail-fastengineboundary.
- Fullprojectpytest running guard /tmp/sherlock-a2-anchor-20261104/full_tests_guard.json session41126 (deadline19:40UTC); no modeltraininglive. Traceguard session21911 completedexit0.
- Independent920gameauditor preparation delegatedanchor_data_audit, writeonly/tmp/audit_results.py.

## Progress20:35Berlin
- Traceaudit48218checks/52pins accepted. ConcreteA2pointdeparture866000p1env35 UID2 LEFT; teacher-on-same-featurealsoLEFT (noimitationgap). Firstactualdifferenceenv27UID3 A2STAY/teacherLEFT smallregret. Holding/energy/matchconversionissues; no isolatedcausalclaim. Reports /tmp/study/trace_analysis.*,teacher_on_trace_rows.*.
- Fullsuite beforefix:1303passed,126subtests,2failed historicalSTOPcleanup tests becausehardcoded studyGAME_END nowpast. Reproducedisolatedtwofailure; fixedONLYtestlocalfutureGAME_END;43affectedfiletestspassed. Ruling: repaircalendar-dependenttestswithout changingproductionhistoricaldeadlines; otherwiseSTOPcleanupwouldneverbecoveredafterstudyend.
- Task3reviewP1 fixedproducer-rounding;29tests includingouterreceiptpublication/wrongmeanrejectionpassed. Independentreviewapproved. No actualnewstudytrainingyet.
- Secondfullsuitewithallfixesrunning session71570/guard full_tests_fixed_guard.json deadline19:50UTC. Do notcommituntilitends (HEADcurrently1206e63).
- Account28%used; battery98%; remoteat19:32:38UTCstillbb21f4c, noforeigncommits. All5protected+5foreign+87originalsourcefiles byteidentical.

## Progress 20:43 Berlin
- Final full suite: 1307 passed, 126 subtests passed,235.96s. Guard full_tests_fixed_guard.json completed exit0. Test clock fixes committed8ad8708; anchor adapter/review fix09c6934.
- Tasks1/2 complete (9e384a8,1206e63), task3 implementation complete09c6934, independent scoped reviews accepted. All actual preflight evidence archived90 files, compressed traces preserve decompressed hashes.
- Seed25 control+anchor admitted and launched19:38:41UTC, guard sessions86319/94343. HEAD09c6934 pinned. Both prefill40 complete; independent startup33checks passed (learning_startup_audit.json). Actual learning now underway; full completion/activity audit pending. Seed26 prepared, not started.
- Account30%used; battery91%. New helper preparation delegatedanchor_diagnostic_prepare (tmp only, no heavy processes). No sources/HEAD changes during trials.

## Progress 20:52 Berlin
- Seed25 both complete exit0 (control19:50:57UTC,anchor19:51:14UTC). Outer receipts and paired actual prefill accepted;232games/24000updates each. Independent all-four learning audit pending.
- Fresh origin fetch stillbb21f4c, account31%used,battery86%. Source/protected hashes verified. Seed26 admitted from actual12.55min slower pair runtime padded25%+90s, plus60min evaluation/audit reserve; estimated all-model finish22:08Berlin before23limit.
- Seed26 launched19:51:52UTC; guard sessions71014control/81085anchor. Same fixed HEAD09c6934, no mutations.
- Independent completion auditor and fixed920 diagnostic preparation helper ready; root crosscheck prepared. Final-only selection, no ensembles.

## Progress 21:08 Berlin
- All four arms complete:928 actual games/96000updates. Independent completion audit accepted, all public validators passed once. Each anchor24000positive gradients/6144000train-onlysampledraws,zeroexcluded. Actualpairedprefillidentical. FirstauditfailedonlybecauseprivateNumPyreaderremoved; preservedfailedscript/report, publicreaderfixaccepted.
- Retentionafter both roottool and independent467checks: A2 .867035; controls25 .731987/26 .773684; anchors25 .787733/26 .809425. Activeanchorretainsmoreteacherguidancebutstillsome drift; no game-strengthclaim.
- Fixed920comparison admitted21:06Berlin, expectedend21:45Berlin, source09c6934, independent roles/protected pinsverified. Controller session37002 active, twoevalworkers, all11jobsfixed. Account32%used,battery79%,originmainstillbb21f4c.
- Ruling: use controller's own deadline and tested child-group cleanup directly, without an additional15s outerkillguard; otherwise outerguardcouldkillcontrollerbeforeits25s childcleanup finishes. Allindividualevalworkersstilluseowneddeadlineguards; rootmonitorscontrollerstate. Ifwrong, rootmustterminateidentifiedownedchildrenmanually.

## Progress 21:39 Berlin
- Fixed diagnostic complete at20:36:31UTC:11/11jobs,920games,303steps/v2, no missing/duplicate rows or caught exceptions. Independent dataaudit passed; root236numeric equalities and266source/153inputpins passed. Original5protected+5foreign+87sources byteequal.
- V14Solution40/40,panel101/120; A239/40,95/120,direct16/40. Controls25/26Solution34/31,panel81/75,direct12/6. Anchors25/26Solution36/36,panel96/88,direct14/12. Anchor-controlpanel+12.50pp[2.50,23.33],+10.83pp[.83,20.83]; exploratory20cards/two starts.
- Bothanchorcandidatesfail predeclaredscreen; no confirmation or further experiments, no release. V14 unchanged. Retentionbenefit and betterthanregularRL areobserved, no new stronger-than-A2/V14claim. OriginalV14 40/40onthissample doesnotmeanuniversal100%.
- Task4 complete:928training+24trace+920diagnostic=1872studyexecutions; technicalintegrationtests trackedseparately. Documentation/archive/publication now; finalwholebranchreviewpending.

## Final review and closure 21:46 Berlin
- Whole-branch review PASS through7ba7380: no unresolved findings. Read-only reviewer rechecked231archiveentries, model/receipt/CSVpins and allprotectedfiles. Finalreviewand300committed-filebytecheck archivedunderoperations.
- All19ownedjobgroupsandcontrollerabsent; owncaffeinate76404verifiedthenstopped. AutomationsremainPAUSED. Account35%used, noreset. Worktreepreservedbecauseunique replaybuffers.
- Integration follows existing explicitmain/pushauthorization; no newapprovalmenu. Onlydata/docs changedafterthe1307test+126subtestfullsuite; unchangedtestedcodeverifiedratherthanrerunninggames. Publicationproofwillberecordedafteractualpush.
