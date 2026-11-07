# Neue Ensemble-Mitglieder nach der Battle-Präsentation

## Auftrag und Ausgangslage

Moayed hat am 07.11. die Präsentationsphase beendet und autonome weitere Trainings ohne feste Uhrzeit beauftragt, mit Schwerpunkt größere Ensembles. Das hebt den alten Experimentstopp auf. Die frühere Kontingentreserve bleibt bestehen: ab 65 % Verbrauch keine neuen Aufgaben, spätestens 70 % keine Entwicklung; kein Reset. V14 bleibt Referenz, bis ein Ersatz alle festgelegten Prüfungen besteht. Die erfolgte Moodle-Abgabe wird nicht verändert.

V14 enthält 36 unterschiedliche Gewichtsstände. FO42 (sechs ältere zusätzliche Netze) und FT18 haben ihre Bestätigung nicht bestanden. Diese abgeschlossenen Studien werden nicht erneut gestartet. Mehr Netze allein ist keine Verbesserungshypothese; neue Mitglieder sollen unterschiedliche Fehler machen und den bestehenden Verbund ergänzen.

## Entscheidung und Alternativen

Erste neue Welle: sechs nachtrainierte Einzelnetze aus drei V14-Mitgliedern, mit zwei unterschiedlichen Gegnermischungen. Die Auswahl von Ausgangsnetzen und Mischungen ist Codex' Umsetzungsvorschlag innerhalb des autonomen Auftrags, keine vom Nutzer vorgegebene Parameterauswahl. Ein erneuter unveränderter FO42-Test wird verworfen. Vollständige neue Zufallsstarts bleiben eine spätere Alternative; sie benötigen mehr Lernspiele. Schülerdestillation bleibt ein anderes Experiment und wird hier nicht wiederholt.

Je zwei Arme stammen aus den Mitgliedern 18, 24 und 30 (nullbasiert): A0/B0, A1/B1, A2/B2. Trainingsstarts 0–5, gleiche Architektur 79→256→256/Dueling. Jeder Arm beginnt mit frischem Optimierer, leerem Replay, identischem Online-/Target-Startnetz und env_steps=60000. Danach 120 Vorlaufspiele ohne Updates und 3000 Lernspiele; Lernrate 0,00005, finaler Checkpoint allein. Rewards unverändert. Vorhandene Schalter rules_in_training, rules_in_training_all und rescue_in_training aktivieren; das bedeutet ausdrücklich nicht vollständige Gleichheit aller Trainings- und Inferenzregeln (art_splash bleibt während Training inaktiv).

- Mischung A: Solution_92 70 %, sol92_sq 20 %, default 10 %.
- Mischung B: Solution_92 40 %, sol92_weak 20 %, rush 20 %, default 20 %.
- Pro Arm eigene Karten und RNG; daher kein isolierter kausaler A/B-Nachweis des Curriculums.
- Training ab 1100000 + Start×10000, 1500 Karten je Arm; Vorlauf ab derselben Basis +5000, 60 Karten.
- Zwischenvalidierung auf 1300000–1300007, beide Seiten gegen default und Solution_92, bei 0/1000/2000/3000 Lernspielen. Diese bekannten Zwischenprüfungen wählen keine Checkpoints aus.
- Smoke-Läufe separat mit 2 Vorlauf-/2 Lernspielen: Karten ab 1190000 + Start×10000 (Vorlauf +5000), Validierungskarte 1390000; nie als Leistungstest oder vollständiges Training ausgeben.

## Kandidaten und Bewertung

Nach erfolgreicher technischer Prüfung aller sechs Endstände feste Varianten bauen: V14+A0/A1/A2 (39), V14+B0/B1/B2 (39), V14+alle sechs (42), sowie ein 36er-Vergleich, der V14-Mitglieder 0/6/12/18/24/30 durch alle sechs ersetzt. Alle Kandidaten spielen mit exakt V14s Inferenzkonfiguration. Keine mehrfach identischen Netze, keine Umgewichtung anhand späterer Bestätigungsdaten. Nur A39, B39 und ALL42 sind nominierbar. Der 36er-Vergleich bleibt rein diagnostisch und prüft eine Alternative ohne Wachstum; er isoliert die Netzanzahl nicht kausal, weil sich auch Mitglieder ändern.

Auswahl und Bestätigung erhalten vor den ersten Leistungsspielen einen eigenen vollständigen Ausführungsplan mit festen Karten, Gegnern und Hürden. Reserviert: Auswahl 1400000–1400099 und direkt 1401000–1401099; Bestätigung 1500000–1500799 und direkt 1600000–1600399. Kollisionsprüfung am 07.11. abgeschlossen: acht lokale Worktrees, 8.612 CSV (7.157 mit Seeds), 4.622 JSON und 82 JSONL; keine Überschneidung der aufgezeichneten Seeds/Seedintervalle. Nicht aufgezeichnete oder externe Läufe sind nicht erfasst. Frühere 900000–900029 sind verbrauchte historische Testkarten.

Höchstens ein Kandidat bekommt eine unabhängige Bestätigung, kein Nachrücken nach Misserfolg. Ganze Karten mit beiden Seiten gemeinsam auswerten. Übernahme braucht abgesicherten Panelgewinn, Solution-Nichtverschlechterung, default-Schutz, Direktduellvorteil und technische Laufzeit-/Kursprüfung; vorhandene sieben Battle-Gates sind die Untergrenze. 100 % auf einer Stichprobe wären keine Garantie auf beliebigen Karten.

## Betrieb und Abschluss

Vorbereitung und Reviews in bestehendem isoliertem Worktree; Agentenquellen, Referenzgewichte und ZIP unverändert. Neue Modelle ausschließlich in Experimentverzeichnissen. Maximal zwei Rechenprozesse auf M3/8 GB; keine parallel laufenden Volltests. Laufende Quellen/HEAD unverändert lassen. GitHub vor Start, spätestens nach drei Stunden und an sicheren Phasenübergängen abrufen; Änderungen während Training nur vergleichen, nicht einmischen. Eigene PID/Kommandos und Fortschritt protokollieren. Akku: keine neue lange Welle unter 35 %, kontrolliert sichern/stoppen spätestens bei 25 % ohne Netzstrom. Kein bezahlter externer Rechner ohne Auftrag.

Nach jeder Welle tatsächliche Spielzahlen, Updates, Gewichtsänderungen, Fehler und Vergleiche dokumentieren. Keine automatische Übernahme anhand Trainingssiegquoten. Bestehende Sicherungen erhalten. Bei fehlendem Vorteil Ursachen prüfen, bevor eine neue Welle festgelegt wird.
