# Bedingte zweite Forschungsroute: PT2

Vor Root-Lektüre vollständiger frischer P-Ergebnisse festgelegt,02.11.2026.
Keine Erweiterung des laufenden P-only-Masters, keine aktuelle Startfreigabe.
Die P-Messreihe bleibt auf Source03e54e267242ff642c126313fe5f512ed9d959ac eingefroren.

## Ausschließliche Eintrittsbedingungen

Nur nach vollständiger3.000-Spiele-P-Auswahl, vollständiger unabhängigerACCEPTED-Abnahme
und `nominee=null`. Nach begonnener P-Bestätigung (auch Fehler/Abbruch) ist PT2 verboten.
Ebenso kein Einstieg nach unvollständiger/technisch verworfener P-Auswahl. Genau eine
unabhängige Bestätigung darf im gesamten adaptiven Nachtpfad tatsächlich begonnen werden.
Aktuelle P-Studie zunächst mit unveränderten Quellen/HEAD/Modellen schließen und belegen.

Vor Start AC, aktuelle Codex-Grenzen (mindestens30%Rest, ab65%Verbrauch Abschluss),
freie Ressourcen und Freshness der unbenutzten842/843/844-Blöcke erneut prüfen.
Zwei schwere Worker insgesamt; kein Training parallel zur laufenden P-Auswahl.
Nur wenn die ganze Folge samt20minSetup-/Auditbudget und60minAbschluss bis03.11.05:30Berlin
passt. Alle tatsächlich beobachteten Klassenraten aus der P-Auswahl übernehmen;
keine Rücksetzung auf optimistischere Werte. Langsamerer Durchsatz kann PT2 vor frischen
Daten ganz ausschließen. Keinerlei Lockerung numerischer Gates oder Stichprobe nach Outcomes.

## Neue Trainingskohorte, keine Umdeutung der alten Teilwelle

Zwei neue, gleichzeitig trainierte Einzelnetze aus V14-Komponenten18/19 in `[q,*ensemble]`.
Die vorherige Zweier-Teilwelle wird NICHT wiederverwendet und der alte Vierarmpilot bleibt
unvollständig. Neue Starts30/31 statt28/29; keine Kontrollen und keine Behauptung eines
kausal nachgewiesenen Anpassungseffekts. Die Forschung prüft ausschließlich den fertigen
kombinierten Agenten gegen V14 auf unabhängigen Karten.

| Arm | Komponente | Runseed | Training (600Spiele, beideSeiten) | Prefill (120Spiele) |
|---|---:|---:|---|---|
| adapt18 |18|30|504200–504499|505000–505059|
| adapt19 |19|31|514200–514499|515000–515059|

Lernkarten dürfen bekannt sein, werden nicht als frische Tests bezeichnet. Validation
weiter bekannte500000–500007, nach0/300/600 je32Spiele=96proArm, eigenerEval-RNG,
strikte vorher/nachher Lern-/eigen-/Global-RNG-Isolation. Nur End600, kein weights_best.
QuelleV14-SHA98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8.
Initialisierung/volleConfig/Adam/Replay/Kanonisierung/epsilon.05/rules_in_training/all
und Reward exakt wie targeting_adapt.py, beide P-Flags im Rollout und in der Val aktiv.
MIX solution92=.6,sol92_sq=.2,default=.1,rush=.1, Rolle-RNG Runseed+4200. JeArm120+600+96=816,
beide1.632 tatsächlicheSimulationen, davon1.200Lernspiele. Neue Verzeichnisse; unveränderter
Source/HEAD/Interpreter/Engine/Quell-/Initgewichte über beide Arme. Maximal70minTrainingsfenster,
vorher Gesamtzeit zulassen; bisherigeWelle40min, konservativ50minTrainingsprovision.

Neuer Wrapper scripts/targeting_adapt_backup.py ist eine offen benannte Kopie des geprüften
Wrappers; ausschließlichProtokoll/Variantenname/ARMS ändern. ARMS genau adapt18=(18,30,true)
und adapt19=(19,31,true). Funktionskörper und übrigeTrainingsparameter unverändert,
AST-/Schedule-/Configtests und unabhängigerReview vor tatsächlichemLoad. KeinTorch-/Modeltest
während der zwei aktuellen P-Evaluationsworker. Die tatsächlicheInit-/Enddatenabnahme folgt
im eigenen Ressourcenfenster. Beide vollständigen Arme oder kein PT2; Counterabweichungen
konkret klären, tatsächliche positiveUpdates/finiteZustände/Endreload belegen.

PT2 hält exakt36Netze: nur18/19 durch neue adaptierte End-q ersetzt; andere34 und
Reihenfolge exakt V14, Gewichte1/36. Inferenzconfig V14+point_pair_swap+art_move_guard,
keine anderen Änderungen. Actual-Load/Tensor-/Configabnahme vor frischen Daten.

## Getrennte Leistungsstudie mit einziger gemeinsamer Bestätigungsreserve

NeueAuswahl50Karten844000–844049 (bisher ungenutzteTechnikreserve), je beideSeiten:
V14/PT2 jeweils700Spiele gegen dasselbeSechserpanel+default, PT2zusätzlich100direkt=1500.
Nur PT2 ist nominierbar. Unveränderte Auswahlgates: PanelΔ>=+.5pp,SolΔ>=0,
default>=99%,direkt>=50%. Keine Kandidaten-/Checkpoint-/Seed-/Mischungsnachwahl.

Falls qualifiziert, genau eine Bestätigung:842000–842299 je300Karten/beideSeiten/7Gegner
für V14/PT2=8400Spiele, direkt843000–843299=600,gesamt9000. DieseBlöcke sind nur dann
verwendbar,wenn die P-Bestätigung nie begonnen wurde und kein anderer bekannter Lauf
sie benutzt hat. Gleiche vorab fixierteÜbernahmegates: PanelΔ>=1pp undlower95>0;
SolΔ>=0/lower>=−1pp; default>=99%/Δ>=−1pp; direktlower95>50%.
Whole-map paired bootstrap5000/RNG0/2.5–97.5,alleSeiten+6Panelgegner gemeinsam.
Identischer neuer Master/Source/HEAD/Modelle über PT2-Auswahl und PT2-Bestätigung;
keine Integration dazwischen. Eine persistente Confirmation-Reservierung verhindert
jedes zweiteStarten, auch nach Fehler oder0persistiertenSpielen.

Neue, getrennte Werkzeugkopien unter experiments/analysis/backup_adaptation_20261102/:
study_driver.py undstudy_stats.py, ausschließlich wire-RollePT2 stattP/PPT, feste50/300/
Seedblöcke und eigenerStudienname. Vorhandene source_identity,par_eval,CSV-/Gates-/Bootstrap-
Implementierung wiederverwenden, aktuelleP-Werkzeuge nicht verändern. Parent-P-ACCEPTED-
Summary/State/Master/CSV/Audit/Freezeabschluss als unveränderliche historischeKette binden:
wegen späterem legalemHEAD-Wechsel nicht fälschlichParent-LiveHEAD03e fordern, sondern
ursprüngliche Abschlussbelege und sämtlicheDateihashes prüfen. Parentconfirmation muss fehlen.
Kandidatenabnahme und neueTrainingsdaten vollständig binden, keineLegacy4Arm-Abnahme vortäuschen.

Initiale Zeitprovision: Training50min+Auswahl68.16min+Bestätigung408.96min+Setup/Audit20min+
Abschluss60min=607.12min (10h07), ab19:15 Ende05:22, nur8minZusatzpuffer bis05:30.
Die Zeitprüfung verwendet jeweils aktuellelangsamereRaten. Ohne vollständigen Zeitfit
keine weitere langePhase, ungetestete Endstände bleiben Forschung, V14 bleibt Abgabe.
Keine zweite unabhängigeBestätigung, kein Nachrücken nach verfehlter Bestätigung.
