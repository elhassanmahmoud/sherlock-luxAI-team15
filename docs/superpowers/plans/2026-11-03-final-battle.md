# Finaler Battle-Durchlauf bis 04.11.2026, 16:00 Berlin

> **For agentic workers:** Use superpowers:subagent-driven-development. User explicitly authorizes autonomous execution, subagents, meaningful commits/pushes and conditional replacement. No additional design approval needed.

**Goal:** Einen nachweislich stärkeren, technisch geprüften Sherlock auswählen und rechtzeitig eine reproduzierbare Battle-Abgabe bereitstellen.
**Architecture:** Vorhandenes V14, kompakte Teilensembles, separate zonenweise Rettung und ein kontrolliertes Rettungs-Nachtraining. Ein vorher festgelegter Screen nominiert höchstens einen Kandidaten; eine frische Bestätigung entscheidet. Die 36 bisherigen Netze und ZIP werden gesichert erhalten.
**Tech Stack:** Bestehendes Python3.13/Torch, LuxAI-Kursengine mit drei Matches; zusätzliche Python3.10-Paketprüfung.
**Spec:** Nutzerauftrag vom03.11. und Moodle-Screenshot: Upload04.11.23:59, Gruppe15.zip, Klasse Gruppe15.main.Agent_x, Gewicht Gruppe15/agent.pth; zehn Minuten Vortrag über Agent, Training und letzte Entwicklungen. Spiel-/DQN-Grundlagen als bekannt voraussetzen. Prof-Feedback: Zielwahl, Netzinput/-output, Masken, Regelreihenfolge mit Flowchart/Pseudocode erklären.

## Globale Bedingungen

- Ausgang main06a6b84, V14 SHA25698a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8, ZIP88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6. Alte Sicherungen erhalten; historische Performancekopie03e nicht ändern.
- Arbeit in vorhandenem sauberen Worktree sherlock-november-followup, Branch improvement/final-battle-20261103. Eigenen README-Prüfeintrag in primary erhalten und bei Integration zusammenführen.
- Maximal zwei rechenintensive Prozesse insgesamt, je ein Torch/BLAS-Thread. Keine gleichzeitige Testsuite und Modellläufe. Code/Interpreter/Engine/Gewichte pro Studie einfrieren; neue Remote-Commits nur beim sicheren Phasenübergang integrieren.
- Mindestreserve30% Codex-Kontingent; ab65% Verbrauch keine neue Phase, geprüften Stand sichern, ab70% keine Entwicklung. Keine Resets. Quota regelmäßig tatsächlich lesen.
- Akku: unter35% keine neue lange Phase, bei25% kontrolliert sichern/beenden; Netzbetrieb vor jeder Phase prüfen. Nutzer schließt an/lässt Deckel offen. Wachhalter verhindert keinen Deckelschlaf.
- Vor jeder Trainings-/Screenphase die gesamte verbleibende Kette bis zur Bestätigung reservieren: 2,22 Kalendersekunden je Panelspiel und3,0 je Direktspiel sind bereits Durchsatz mit zwei Workern, nicht nochmals durch zwei teilen. Je Kostenklasse mindestens historische Rate oder langsamste tatsächlich gemessene Rate, gemeinsamer Verlangsamungsfaktor, zusätzlich20% Reserve. Vor Training mindestens90 Minuten dafür reservieren; zusätzlich60 Minuten für technische Übergänge vor13:30. Reicht die Zeit nicht, keine Phase starten.
- Kein neues langes Training nach04.11.03:00 Berlin; Bestätigung muss nach konservativer Laufzeitrechnung bis13:30 fertig werden. Ab13:30 nur Abschluss/Paket/Dokumentation, spätestens16:00 eigene Jobs beenden. Unvollständige Messungen qualifizieren nicht.
- Keine Wiederaufnahme des verworfenen P/PT2-Programms. Kein Server/Tunnel; bekannte Ressourcenfehler bleiben separat. Keine Moodle-Abgabe ohne konkrete Uploadfreigabe.

## Fester Kandidatenkatalog

V14-Mitglieder sind `[q,*ensemble]`, nullbasiert; keine Tensor-Mittelung. V14-Konfiguration für alle außer Z36 unverändert in der Inferenz. Pair-Auswahl basiert ausschließlich auf historischen ft3-val.csv-Endständen nach2000 Spielen, Lösungssiegquote absteigend, default absteigend, Seed aufsteigend; pro Familie drei/vier Original-Nachtrainingspaare. Diese kleinen Validierungen sind keine Stärkenbelege.

- PAIR18: [0,1,3,6,8,10,13,15,16,18,19,21,24,26,28,31,33,34].
- PAIR24: [0,1,3,5,6,7,8,10,13,15,16,17,18,19,21,23,24,25,26,28,31,33,34,35].
- FT18: Indizes18 bis35.
- Z36: alle36 Originalnetze, nur zone_rescue=True. Konfigurationsversuch, kein Training.
- R36: alle36, nur Index18 durch festen Endstand des Rettungsarms ersetzt; V14-Inferenzkonfiguration. Keine erhöhte Gewichtung.
- C36: analoge Ersetzung durch Kontrollarm, ausschließlich methodische Kontrolle, nicht zur Übernahme nominierbar.

## Training

- Zwei Arme C/R ab demselben V14-Netz18, frischer Adam/Replay, q=target, env_steps60000, learn_steps0, lr1e-4, bestehende V14-Belohnung, epsilon0.05. rules_in_training/rules_in_training_all=True, Pflags=False, zone_rescue=False, cand_rescue=True/rescue_after30.
- Neuer Schalter rescue_in_training standardmäßigFalse. Nur R aktiviert bestehende Rettungsberechnung und tatsächlich zugehörige obey_target/neb_cand-Aktionen im Training. Keine pauschale Aktivierung anderer eval-only-Regeln.
- Je120 Prefill +1200 Lernspiele +96 bekannte Validierungen (0/600/1200,500000–500007,default/Solution,beide Seiten), Endstand statt best checkpoint. Mix .6Solution/.2square/.1default/.1rush. Seed29, map-offset3000: Training493000–493599, Prefill495000–495059; gemeinsame Gegner-/Seitenfolge.
- Auditentscheidung vor Start: Prefill495000–495003 wurde historisch in vier Scratchpad-Trainingsspielen benutzt. Die feste Prefillfolge bleibt erhalten; diese vier Karten sind ausdrücklich wiederverwendete Trainingsdaten, keine frischen Testkarten. Leistungsblöcke851/852/853 müssen weiterhin unbenutzt bleiben.
- Vor Start tatsächliche Quellen-/Seedkonfliktprüfung einschließlich Worktrees/Manifeste. Neuer Wrapper mit eigenen Pfaden, keine Wiederverwendung alter Laufverzeichnisse. Echte Initial-, Prefill-, Update-, End-/Reload-Belege aus bestehendem targeting_adapt ableiten. Erwartet180000 Updates, env_steps459960; Abweichungen untersuchen statt als Erfolg markieren. Rescue-Eingriffe und gespeicherte Endaktionen belegen.

## Leistung und Übernahme

- Lokales Panel: solution92,sol92_sq,V3(20261022_all18_v3),V7(20261022_v7_Bsnpd),V10(20261022_v10_baseline),V13(20261101_v13_neb). default separat. Fehlende historische league_nets6/threat6 nicht ersetzen oder zufällig initialisieren.
- Screen und Bestätigung bilden EINE unveränderliche Leistungsstudie: gleicher HEAD, Quellen/Interpreter/Engine, geordnete Kandidatentensoren und Configs, Gegnerdateien, Statistikimplementation und Manifeste. Auch zwischen Screen und Bestätigung keine Remoteintegration. Eine notwendige Verhaltenskorrektur macht diese Studie für eine Übernahme ungültig; alte Daten nicht unter neuem Code fortsetzen.
- Vor dem ersten Screenspiel ein gehashtes Zulassungsmanifest mit allen Rollen erstellen. C36 ist nie nominierbar. Wenn einer der Trainingsarme technisch unvollständig/ungeprüft ist, entfallen C36 UND R36 vor allen Screenresultaten; reduzierter Screen6240 Spiele. Kein Nachstart/Ersetzen innerhalb eines begonnenen Screens.
- Screen:80 Karten851000–851079, beide Seiten, Baseline+alle sechs Kandidaten gegen sieben Gegner; dazu je Kandidat160 Direktspiele auf denselben Screenkarten gegen V14. Insgesamt8800 Spiele. Gesamten Screen abschließen vor Ergebniswahl. Bei unvollständigem Training entfallen vor Screenbeginn C36/R36 mit dokumentiertem technischem Grund; kein nachträgliches Entfernen anhand der Leistung.
- Screenzulassung: PanelΔ>=+0.5pp, SolutionΔ>=0,default>=99%,direkt>=50%. R36 zusätzlich Panel und Solution nicht schlechter als C36. Höchstens ein Nominierter: höchstes PanelΔ, dann SolutionΔ, dann weniger Netze, dann Name. Kein Nachrücken nach gescheiterter Bestätigung.
- Bestätigung:400 neue Karten852000–852399, beide Seiten, V14 und ein Kandidat gegen sieben Gegner;800 getrennte Direktspiele853000–853399. Insgesamt12000 Spiele. Vorher Reservierung gegen alle lokalen Datensätze prüfen. Keine Auswahl anhand laufender Bestätigungsquoten.
- Statistikdefinition: Ergebniswert Sieg1,Remis0.5,Niederlage0; Panel gleicher Mittelwert über genau sechs Nicht-default-Gegner. Differenzen Kandidat minus V14 je Karte. Direktduell misst absolute Kandidatenquote auf separatem853-Block. Bootstrap-Perzentile linear2.5/97.5, Vergleichs- und Direktkarten separat, nur vollständige erwartete Schlüssel, keine Schnittmengen/Teilgruppen.
- Sieben feste Bedingungen: PanelΔ>=+1pp; gepaarte untere95%-Grenze>0; SolutionΔ>=0; Solution-Untergrenze>−1pp; default>=99%;defaultΔ>=−1pp; Direktduell-Untergrenze>50%. 5000 Bootstrap-Ziehungen,PCG64Seed0,ganze Karten mit beiden Seiten/Panelgegnern zusammen. Vollständige CSV-Schlüssel/303Schritte/Punktezählungv2 prüfen. Alle Bedingungen erforderlich, keine Team-Ausnahme unterstellen.
- Nach Datenreview: unabhängige technische Prüfung (Suite, Kursrunner, neue ZIP an beiden Ablageorten, frozen/trainTrue, Python3.10-Replay, Zeit/Mem, Tensor-/Quellenidentität), Sicherung alter Dateien/ZIP mit Hashes, erst dann kontrollierter Austausch. Keine automatische Übernahme durch unreviewten Studienrunner.

## Aufgaben / Prüfungen

- [ ] Bereits reproduzierten Testisolationsfehler korrigieren; README-Befunde mit aktuellem Programmstatus beheben, unabhängiger Review.
- [ ] Default-aus-Rettungsgate und eigenes Trainingswerkzeug implementieren; Red/Green, unveränderte Standardentscheidungen, echte Rettung im Lernmodus, Endaktion im Replay, Reviewerabnahme.
- [ ] Reproduzierbaren Teilensemble-/Ersetzungsbauer implementieren; Indizes, Anzahl, Identität, Ausgabeschutz, Quellenmanifest testen/reviewen.
- [ ] Supervisor mit Phasenjournal, Quelle-/Hashschutz, Ressourcen-/Akku-/Deadlinebedingungen, Prozessgruppenbereinigung und Fortsetzungsvermeidung prüfen. Training ausführen und Daten prüfen.
- [ ] Kandidaten vor Screen festschreiben; Screen vollständig ausführen/auswerten, ggf.einmalige Bestätigung. Unabhängiger Review vor Übernahme.
- [ ] README/Arbeitsstand/Experimentprotokoll und Ergebnissicherung sinnvoll committen/pushen; Remoteabgleich erhalten. Finale ZIP und verständlicher Abschlussbericht; anschließende Folienvorbereitung auf bestätigter Version.

## Review-Fokus

- Mehrfachlauf/Resume darf keine Ergebnisse überschreiben oder doppelt zählen.
- Trainingseingriffe müssen tatsächlich aktiviert sein; Flags allein sind kein Nachweis.
- Teilensemble behält Tensorreihenfolge und richtige V14-Konfiguration; alte Target-/Optimizerdaten werden nicht als trainierte Teilensemblehistorie ausgegeben.
- Gleiche Karten beider Seiten zusammen resampeln; keine gepoolte Unabhängigkeitsannahme oder nachträgliche Auswahl von Teilmengen.
- Ende/Schlaf/Akkufehler darf keine Teilmessung zur Freigabe machen. Bestehende Abgabe bleibt verfügbar.
