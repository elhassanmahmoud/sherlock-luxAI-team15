# Wie stark beeinflussen die neuen Netze das Ensemble?

**Die neuen Einzelnetze liefern andere Bewertungen, aber daraus folgt keine belegte bessere Spielentscheidung.** Auf den vorhandenen Trainingszuständen ändern die beiden 38er-Kandidaten den legalen Netzvorschlag in rund 1,4 % der Zeilen gegenüber V14. Die Diagnose liefert keinen Grund für eine blinde Umgewichtung oder einen Abgabeaustausch.

## Tatsächlich geprüft

10.000 gespeicherte Folgezustände, je 2.500 aus den vier finalen Replay-Puffern. Verwendet wurden ausschließlich nichtterminale `ns`-Zeilen zusammen mit ihrer tatsächlich gespeicherten nächsten Aktionsmaske. Fester PCG64-Start0, keine Auswahl anhand der Vorhersagen. 9.996 unterschiedliche Feature-/Maskenpaare; keine unabhängige Stichprobe, weil die Zustände aus den eigenen Trainingsverläufen stammen.

Alle 40 beteiligten Einzelnetze wurden auf derselben Bank ausgewertet: die ursprünglichen 36 und die vier neuen Kontroll-/Neutral-Netze. Die getrennt geladenen 38er-Kandidaten reproduzierten die zusammengesetzten Mittelwerte exakt (maximale Abweichung0). Keine Spiele, keine Gradienten, keine neuen Modellgewichte.

| Vergleich | Geänderte legale Netzvorschläge | Anteil |
|---|---:|---:|
| CONTROL38 gegenüber V14 |143/10.000|1,43 %|
| NEUTRAL38 gegenüber V14 |139/10.000|1,39 %|
| control41 gegenüber ursprünglicher Komponente18 |2.055/10.000|20,55 %|
| control42 gegenüber ursprünglicher Komponente18 |1.889/10.000|18,89 %|
| neutral41 gegenüber ursprünglicher Komponente18 |1.962/10.000|19,62 %|
| neutral42 gegenüber ursprünglicher Komponente18 |1.895/10.000|18,95 %|

CONTROL38 wechselte dabei in drei Zeilen zu SAP und in fünf davon weg; NEUTRAL38 in jeweils vier Zeilen. Das sagt nicht, ob diese Wechsel hilfreich sind. Nachfolgende Regeln und vollständige Spielzustände sind in diesen Merkmalszeilen nicht enthalten.

## Warum die Prozentzahlen nicht direkt eine Ursache beweisen

Die Einzelnetzvergleiche beziehen sich auf Komponente18, die Ensemblevergleiche auf den Mittelwert aller36 ursprünglichen Netze. Unterschiedliche Referenzen! Daraus darf nicht abgeleitet werden, dass das Ensemble hilfreiches Lernen unterdrückt.

Ein **zusätzlicher nachträglicher, rein rechnerischer Interpretationscheck** verwendet INIT38: ursprüngliche36 plus zwei unveränderte Kopien von Komponente18. Dafür wurde kein Agent gespeichert, trainiert oder in einem Spiel getestet. INIT38 unterscheidet sich von V14 auf142 Zeilen; CONTROL38 und NEUTRAL38 unterscheiden sich von INIT38 auf117 beziehungsweise116 Zeilen. Diese ähnlich großen Anzahlen beschreiben nicht notwendigerweise dieselben Fälle. Insbesondere bedeutet142 gegenüber143 nicht, dass142 der143 Änderungen erklärt wären.

Dieser Check trennt den Vergleich mit zusätzlich gewichteter Elternkomponente von dem Vergleich mit dem ursprünglichen Ensemble. Er bewertet keine Aktionsqualität und dient nicht zur Auswahl eines neuen Kandidaten. Alle ursprünglichen Vergleichsregeln und Ergebnisse bleiben unverändert.

## Prüfung und Grenzen

Root11 synthetische Tests bestanden (2,42s); unabhängiger Code-/Methodenreview PASS. Reale Diagnose unter Quellenstand `f6f8b8ad2feecb680a3cd06a0eab2669d5d7b4d7`. Unabhängiger Daten-/Matheaudit PASS: alle vier Originalpuffer, Auswahlindizes, Zustände, Masken und Prüfsummen bestätigt;1906 Statistik-/Strukturprüfungen bestanden. NumPy-Gegenrechnung der Mittelwerte innerhalb der vorab festgelegten relativen/absoluten Toleranzen. Der tatsächliche Agent maskiert mit−∞; für sämtliche angenommenen endlichen Ausgaben ergab die Diagnose mit−1e9 denselben legalen Gewinner.

V14 und die ZIP bleiben bytegleich. Der Diagnoseprozess ist beendet. Bank,40er-Netzausgaben, Zusammenfassung und unabhängiger Audit sind archiviert; große Original-Replay-Puffer bleiben lokal. Keine inferenziellen Konfidenzintervalle über korrelierte Zeilen. Keine Aussage über versteckte Fog-Treffer, final ausgeführte Regelaktionen oder allgemeine Spielstärke.

## Nächster sachlicher Prüfpunkt

Der bestehende Code weist einen konkreten Unterschied zwischen Training und Spielen auf: `_artillery_ok` aktiviert die Streuschaden-Anpassung von `art_splash` nur bei `not self.training`, auch mit `rules_in_training_all=True` (`agents/sherlock/main.py`, Zeilen752–755). Der Unterschied ist bereits in `docs/RESCUE_NACHTRAINING_DIAGNOSE_20261103.md` dokumentiert. Er ist kein neu bewiesener Fehler und erklärt nicht automatisch die bisherigen Niederlagen.

Vor weiterem großem Training sollte zuerst eine kleine rein diagnostische Prüfung klären, wie häufig dieser Unterschied auf bekannten Spielsituationen tatsächlich andere Artillerieentscheidungen erzeugt. Erst bei messbarer Exposition wäre ein eng begrenzter Trainingsvergleich mit angeglichener Regel sinnvoll. Keine Regel- oder Gewichtsänderung dafür bisher umgesetzt.

Nachweise: `run_v1/summary.json`, `bank.npz`, `outputs.npz`, `operations/independent-data-audit.json` und `.md`, `operations/historical_acceptance.json`.
