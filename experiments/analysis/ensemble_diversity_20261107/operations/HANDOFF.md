# Fortsetzung 08.11.2026 – neue Nutzerfreigabe

Die bisherige30%-Reserve ist ausdrücklich aufgehoben. Nutzer erlaubt restlichesKontingent und übernimmt etwaigeResets selbst. Quellen-/Gewichts-/Datenintegrität undmaximalzweiWorker geltenweiter. Alle6Trainingsarme fertig, vierKandidaten geprüft. NochkeinAuswahlstart zumZeitpunktdieserNotiz. Controllermittels explizitemmax-used-percent100 vorbereiten, Tests/Reviewabschließen, dann39Jobs/7800Spiele. KeineTrainingswiederholung. AktuellerArbeitsstand hatVorrang; darunterhistorischerAbschluss.

---

# Aktuelle Übergabe – Trainingswelle abgeschlossen

r1 vollständig, sechs Receipts, keine aktiven Prozesse. Unabhängiger Audit bestanden. Vier feste Kandidaten gebaut; Leistungsdaten noch nicht begonnen. Kontingent zuletzt64%, mindestens30%Reserve bleibt bis ausdrücklicher Änderung. Keine neue große Phase; nicht erneut trainieren. Remote-Abgleich pausiert. Details und nächsten Ablauf in docs/ENSEMBLE_TRAINING_20261107.md und jüngstem docs/ARBEITSSTAND.md. Quellstand des Trainings6ad3452; Arbeitskopie nach Ende sicher auf73119c7 aktualisiert. V14 undZIP unverändert. Die folgenden Betriebsnotizen sind historisch.

---

# Active ensemble study — fresh attempt r1, 7 November 2026

User authorizes autonomous training toward stronger Sherlock, favors more networks, no time deadline. Preserve30% account reserve: no new work at65% used, controlled stop before70%, no reset. Last root quota57% used at14:31UTC. AC recognized,99%.

## Active jobs — do not duplicate or modify frozen sources

Study worktree: /Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15
Primary checkout: /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15
Frozen studyHEAD:6ad34527673e29f0e50e2dacc917e5ded59f0343; primary main also at6ad3452 when r1 started.

SupervisorPID27750, exec session84149; initial A0PID27767/B0PID27773. Owned caffeinatePID27756. Verify commands before signaling. Max two model processes; fixed queueA0/B0/A1/B1/A2/B2. Live state experiments/analysis/ensemble_diversity_20261107/training_run_r1/state.json. Controller log supervisor_r1.log. Per-arm progress experiments/runs/20261107_diversity_r1_<ARM>/progress.json. Prepared inputs experiments/runs/20261107_diversity_r1_prepared.

NO TESTS OR PYTEST ANYWHERE while training/evaluation runs. No Python-source, pinned-plan or HEAD changes in the study checkout. Read-only stdlib progress/log checks and document-only operations files are okay. New model jobs requireAC or>=35%battery; stop<=25%withoutAC. STOP is /tmp/sherlock-diversity-20261107/STOP. Watcher writes STOP at65%quota or unknownbudget. No auto-restart.

Interpreter /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python. Each fullarm:120prefill+3000learning+128validation,450000updates. Sixarm total19488 executions. No new strength claim.

## Original attempt — retained, ineligible, not running

Original state training_run/state.json is FAILED and historical. At14:14UTC root incorrectly allowed lightweightpytest inPRIMARY; global guard intentionally blocked it and stopped A0/B0 after1906/2178learninggames. Both checkpoints saved, all oldPIDs6274/6291/6297/6280 gone. Total4484executions =4084learning+240prefill+160validation,612600updates. No complete receipts. Preserve all original dirs/reservations. Replay/RNGnotfullysaved, so no exactresume claim. Newr1 is an explicit operational retry with identical initial tensors/configs/seeds/opponent plans; proof operations/retry_initial_equality.json. No intermediate-performance choice. Record original overhead separately.

## Verified implementation and publications

Main commits:cda52d9 tools/design; b683bc7 real24game smoke;4925a3c initialstartdocs;2020c6b first1000audit/strictwinclarification;4ff93d9 explicitfreshattemptnaming/cleanupfix;6ad3452 fixedcomparison tools. All pushed. Root287tests+16subtests before review fixes, then138targeted+16subtests after. Independent review and narrow re-review accepted both corrected findings. Old24game smoke is technical only, not strength evidence. No realselection/confirmationgames yet.

Candidate builder scripts/ensemble_diversity_candidates.py: --source experiments/releases/20261101_v14_baseline/agent_p0.pth --training-state <r1state> --out experiments/candidates/ensemble_diversity_20261107. Requiresall6 complete and independently audited; createsA39/B39/ALL42/REPLACE36 plus manifest.json(statusadmitted, rolesincludingV14). Do not runwhiletraining.

Comparison controller scripts/ensemble_diversity_eval_supervisor.py start --jobs <jobs.json> --admission <candidate_manifest> --out <fresh analysisdir> --python <venv> --expected-head <full currentHEAD> --usage-file operations/usage.json --phase selection; optional confirmation --nominee. Uses fixed39jobs/7800games from selection_plan/jobs.json. SameSTOP, max2jobs, quota receipt must be<20minutes old. Noauto restart/resume. Source/HEAD must remain frozen through selection AND confirmation; confirmation re-analyzes complete selection evidence before reading its own seeds.

Analysis scripts/ensemble_diversity_compare.py analyze --jobs <jobs> --results <dir> --provenance <dir>/provenance.json --phase selection --out <dir>/summary.json. RequirescompleteCSV+receipts and source/model hashes. Default fullabsolute/relative paths work as CLI documents. Keep summary.json for binding optional confirmation. Confirmation15jobs/23200games manifest still to prepare ONLY after a qualifying nominee. No data or seed files opened before nomination. Exact plan docs/superpowers/plans/2026-11-07-ensemble-comparison.md.

## Fixed study decisions

A39=V14+A0/A1/A2;B39=V14+B0/B1/B2;ALL42=V14+all6. REPLACE36=remove[0,6,12,18,24,30]+all6; diagnosticonly. No intermediate checkpoint/member selection. V14rawconfigurationunchanged. CurriculaA/B differ plus differentmap/RNG, so no isolated causal curriculumclaim. Trainingart_splash remainsinference-only, disclosed.

Selection maps1400000..1400099; direct1401000..1401099. Localpanel Solution,sol92_sq,V3,V7,V10,V13;defaultseparate. Historicalleague/threat filesmissing, do notclaimsamepanelasMahmoud. Candidate nomineegates panel>=+.5pp,Solution>=baseline,default>=99%,direct>=50%; rankpanel thenSolution thenfewernets thenalphabetical. OnlyA39/B39/ALL42 eligible. Full7800mustfinish.

Onlyoneoptionalconfirmation:800maps1500000..1500799,400directmaps1600000..1600399,total23200. Sevenexisting scoregates plusSolution>=0; also STRICT Solutionwins>=baseline andstrictdefault>=99% in bothphases. Reportscore=(W+.5D)/N andW/D/L separately. Wholecardpairedbootstrap5000PCG64seed0,95%unadjusted. Onefailedconfirmationendswave,no replacementnominee. Course/runtime/reproduction plusbackup required before anypromotion.

Protected weights bothcheckouts98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8. ZIP88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6. No ZIP rebuild/upload.

## Coordination

remote_watch_20261107 checksremote/quota every10min, currently extended until18:08UTC/19:08Berlin; extend before expiry. Writes operations/usage.json {timestamp,usedPercent,ordinaryUsageAllowed}. Keepexisting3hourremote-sync automation; pausewhenstudyends/stops. No new jobwatch automation. Preserve foreign primary config2/reward2/.DS_Store/oldawake files and five historical student/A2 run dirs.

Next: monitor r1 without tests; independently audit6complete receipts/rawchronology/tensors afteralltrainingends; buildfixedcandidates; runfixedselection; optionalconfirmation onlyifqualifiesandresourcesallow. Documentverifiedresults, meaningfulcommits/push, no unproven replacement.


## Monitoring handoff at 18:08 UTC

The original remote_watch_20261107 ended cleanly at 18:08 UTC. New read-only watcher ensemble_watch_budget (small model for mechanical polling) owns monitoring until 21:08 UTC. Quota checks and progress snapshots every 10 minutes, remote fetch every 30 minutes. Same STOP at65% or unknown/disallowed usage. Root should renew before expiry if still authorized. Latest snapshot: A0/B0 complete, A1=998 and B1=677 learning games, A2/B2 queued; AC100%, usage62%. Primary/origin main73119c7; study remains frozen6ad3452. No tests or model imports during the active wave.
