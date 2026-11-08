# Kleinen HOLD-Korrekturkopf lernen

Spec: [feste Lerndefinition](../specs/2026-11-08-holder-learning.md). Dieser Plan erklärt die dortigen Vorschläge vor neuen Labels für verbindlich. Neuer kleiner Versuch nach unabhängiger erfolgreicher Einflussprobe. Keine Gewichtspromotion aus Offline-Labels. Nutzer autorisiert fortlaufende Arbeit, sinnvolle Commits/main und sichere lokale Synchronisation.

## Globale Grenzen

Originalagent/V14/ZIP bleiben unverändert. Rein experimenteller Kopf und DiagnosticAgent, kein Produktionsumbau. Quelle einfrieren während Spielblöcken; maximal zwei Modellprozesse, hier sequenziell, keine parallelen Tests. Keine neuen Hyperparameter, Kartenverlängerung oder Refit bei negativem Gate. Frühere Studien geschlossen. 16öffentliche Merkmale, genau ein Ridgefit, Schwelle>1Punkt, acht GESCORTE Gelegenheiten/Spiel,12Schritte Abstand auch nach Ablehnung, reset ausschließlich new_game.

Trainingskarten6500000–6500023; Validierung6501000–6501007, beide Seiten gegenSolution92. Frischeprüfung vor Start. Je Schlüssel Referenz+Sammler, insgesamt128vollständige Ausführungen und maximal512Paare (12288primäre und höchstens1536Wiederholungs-Schritte), tatsächlich weniger bei seltener Eligibility. Alte55Diagnosepaare nicht fürTraining/Normierung/Validierung verwenden. Beide Splitlisten vorab binden. Training erfassen→einmal fitten/Kopfhash festhalten→erst dann Validierungslabels erzeugen/lesen. Kopfdatei gehört während Validierung zu eingefrorenen Inputs.

## TaskA – pure Lernarithmetik (unabhängiger Schreibbereich)

Dateien `scripts/holder_learning.py`, `tests/test_holder_learning.py`.

Öffentliche Schnittstellen:
- `FEATURE_NAMES` fester16erTuple, `feature_vector(candidate)`→float64[16], keine Objekt-/Umweltzugriffe.
- `fit_head(rows, *, provenance)`→(head_dict, report_dict), `InsufficientTrainingData` bei vorab fehlender Menge; rows sind vollständige {seed,side,candidate,label}-Paare. Originalbaselinehash/Datensatz-/Quellhashes in provenance. AlleLabels einschließlichNull undnegative.
- `validate_head(head)`→validierte Kopie, nonfinite/falscheSchema-/Feature-/Baseline-/Cadence-/Thresholdwerte ablehnen.
- `predict_gain(head,candidate)`→float. `validation_report(head, rows, validation_seeds)`→vollständiger Bericht inklusive festenGates/Bootstrap/MSE; kein Refitting.

ExakteFormeln/Gates/FeatureOrder ausSpec. JSONSchema v1 mitfeatureversion,eligibleversion,cadence,H12,mean,scale,coefficients,intercept,ridge_alpha0.1,threshold1.0,baseline_sha256 undprovenance. FixedbaselineSHA98a07350…d3d8. Kopfklein/inspectable, keineTorchabhängigkeit. Tests erst, insbesondereTrain-onlyNormierung,ChangingValLabelsCannotAlterFit,Mapgewichtung,NullHeadneutral,MalformedHead,Schema/Boundary undGatearithmetik. KeineSpielausführung, keineanderenDateien, keineCommits.

## TaskB – Erfassung und experimentelle Policy (getrennter Schreibbereich)

Dateien `scripts/holder_rollout.py`, `scripts/holder_rollout_probe.py`, neu`scripts/holder_learning_study.py`, `tests/test_holder_learning_study.py`. TaskA-APIs exakt verwenden, nicht ändern. Vorhandene historischeProbeCLI bewahren.

- Factor audited collectorloop into reusable internal collector accepting prevalidated fixedkeys/extra frozeninputs/protocolpaths. HistorischeCLI prüft weiter exaktalte12Keys/Smoke2. KeineDuplizierung derBranchengine/Pointhelper. Neues collectCLI nurvalidierteStudienpläne mit genau24train/8val, beideSeiten,fixedSeedRanges; keinefreie nachträglicheAuswahl. Prophase exklusivesOutput+vollständige manifests/provenance/Guards/Counters/Passivität. KleineQuellenrefaktorisierung darf alteSemantiknichtändern.
- DiagnosticAgent optional validierter `head` nurEvaluation; fehlenderKopf alterPfad. Eingriff anidentischer `_rule_override`-Stelle, keineClosure/liveLeaks. SechzehnFeatures anhanddesgleichen aufgezeichnetenCandidates. ProeligibleerstenUID Opportunitysofortverbrauchen/12CooldownauchbeiAblehnung; max8completegame, nichtproMatch. `new_game` resets; keineanderenResets. Interventionprobe und gelernterKopf nichtkombinieren. Q-ZugriffamOriginalcallerbeibehalten; Headneutral mussganzeAktionenidentischlassen.
- Datenerfassung immerhead=None. CLI `collect --split train|validation --plan ... --out NEW --expected-head ... --usage-file ... --stop-file ...`; validation benötigt vorabgültigenfit/head-Receipt und bindetKopfdatei+Trainingmanifesthash. Optionalfit/validateSubcommandswrappenTaskAAPI, Lesen nurcomplete/liveverifiedPaare,ArtifactHashes/keys/recomputedPassivitynachweisen. `fit` ausschließlichtrainmanifest, exklusiv head+report; `validate` validiertesfrozenhead+validationmanifest, report keinePromotion.
- NeutralerEndtoEnd-Test vorbereitet alsCLI oderklarerRootcall: bekannteSmokeKeys beideSeiten jeOriginalreferenz+neutralerKopf, insgesamt4kompletteAusführungen; fehlenderKopf durchTrainingreference/collectorpassivitygeprüft. Kein actualgamewährendImplementierung. Rootführt erstnachunabhängigemReviewaus. SynthetischeTests eligibility/cadence accepted/rejected/UIDorder/cooldown/reset/schema/guards, bestehende26ProbeTests nichtabschalten.

## TaskC – Integration, Modelllauf und Entscheidung

Root prüftA+B gemeinsam mit unabhängigerReview; passendeTests einmal, dann Commit/Remoteabgleich. VierneutraleTechnikausführungen, beiPassivität festeTrainingsdaten erfassen. Datenaudit+exactfit, Kopffreeze, dannfesteValidierung. Quellstanddarf zwischenSammlungundFitnuramklarenPhasenübergangnachBegründungwechseln; standardmäßiggleicherStand. Alle tatsächlichenAusführungen/Rohpaare/Herkünfte dokumentieren.

Nur beiOfflinegatePASS separatenkleinenFullgame-Vergleich gegendiesesV14/Solution/Kontrollen vor neuenLeistungsdaten definieren. Wirdabgelehnt, Kopf nichtnachtrainieren/tunen oderValidationinsTrainingverschieben; nächsterbegründeterAnsatz ausEnergie-/FogRewarddiagnose. KeineEndlosschleifeaufgleichengedaten. V14erstnachgesichertemStärke-/Portabilitäts-/AbgabecheckundBackupersetzen.
