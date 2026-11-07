# Vorab festgelegter Vergleich neuer Ensemble-Mitglieder

Festgelegt vor Trainings- und Leistungsergebnissen der [Studie](../specs/2026-11-07-ensemble-diversity.md). Kein Startauftrag für unvollständige Modelle. Hauptziel ist allgemeine Spielstärke mit besonderem Augenmerk auf Solution_92; kein Overfitting auf dessen bekannte Karten.

## Unveränderliche Kandidaten

- Baseline: V14, 36 Netze, SHA256 98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8.
- A39: V14 + neue A0/A1/A2.
- B39: V14 + neue B0/B1/B2.
- ALL42: V14 + alle sechs neuen Mitglieder.
- REPLACE36: V14 ohne Mitglieder [0,6,12,18,24,30] + alle sechs. Nur Diagnose, nicht nominierbar.

Nur die überprüften Endstände nach jeweils 3000 Lernspielen. Keine Zwischenstands- oder Einzelmitglied-Nachauswahl. V14-Konfiguration in allen Auswertungen exakt unverändert. Neue Mitglieder müssen endliche, unterschiedliche Tensoren, korrekte Dimensionen und vollständige Lernnachweise haben. Anfangsduplikate der jeweiligen A/B-Familie sind nach Training keine beabsichtigte Mehrfachgewichtung.

## Gegner und Karten

Lokales Sechserpanel wie in den letzten Codex-Studien: solution92, sol92_sq, V3 (20261022_all18_v3), V7 (20261022_v7_Bsnpd), V10 (20261022_v10_baseline), V13 (20261101_v13_neb). Die nicht lokal verfügbaren league_nets6/threat6 werden nicht stillschweigend als vorhanden behauptet. Daher keine Gleichsetzung dieses Panels mit Mahmouds historischem Battle-Sechserpanel. Alle eigenen Gegner ausschließlich aus experiments/releases und vor Start per Hash festhalten. default separat. Direktgegner ist V14 (20261101_v14_baseline).

Auswahl: 1400000–1400099 für alle fünf Rollen gegen sieben Gegner, beide Seiten: 7000 Spiele. Separat 1401000–1401099 für vier Kandidaten gegen V14, beide Seiten: 800. Insgesamt 7800 Auswahlspiele. Alle vollständig, keine frühe statistische Erfolgserklärung oder Kandidatenverwerfung anhand unvollständiger Teilmengen.

Unter den drei nominierbaren Kandidaten muss gelten: Sechserpanelgewinn mindestens +0,5 Prozentpunkte; Solution-Siegquote mindestens Baseline; default mindestens 99 %; direkt mindestens 50 %. Rangfolge unter bestandenen: größter Panelgewinn, dann größter Solution-Gewinn, dann weniger Netze, dann alphabetischer Name. Höchstens ein Kandidat wird bestätigt. Auswahl ist explorativ, kein Stärkenachweis.

Einzige Bestätigung: Baseline + nominierter Kandidat auf 1500000–1500799 gegen dieselben sieben Gegner, beide Seiten (22400 Spiele). Direkt auf 1600000–1600399, beide Seiten (800). Insgesamt 23200 neue Spiele. Kein Zugriff vor Nominierung; keine Vermischung mit Auswahl oder historischen Spielen. Kein Nachrücken/zweiter Versuch bei Misserfolg. Ohne ausreichende Ressourcen für den festen Block bleibt er ungestartet; keine nach Ergebnissen verkleinerte Bestätigung.

## Auswertung und Übernahme

Gepaarter Bootstrap über ganze Karten mit beiden Seiten und Panelgegnern gemeinsam: 5000 Ziehungen, PCG64-Seed0, unadjustierte 95-%-Perzentilintervalle. Auswahl-Mehrfachvergleiche ausdrücklich explorativ; unabhängige Bestätigung nur für einen vorab fixierten Kandidaten.

Sieben etablierte Gates, unverändert aus league_gates.confirm_checks mit lokalem Sechserpanel/min_delta=0.01:

1. Panelgewinn mindestens +1 Prozentpunkt.
2. Untere Panel-Intervallgrenze > 0.
3. Solution-Differenz mindestens −0,5 Prozentpunkte.
4. Untere Solution-Differenzgrenze > −2,5 Prozentpunkte.
5. default-Siegquote mindestens 99 %.
6. default-Differenz mindestens −1 Prozentpunkt.
7. Untere Direktduell-Intervallgrenze > 50 %.

Zusätzliche Voraussetzung für diesen Solution-orientierten Auftrag: gemessene Solution-Differenz >= 0. Keine eigenständige Behauptung eines gesicherten Solution-Vorteils ohne positives Differenzintervall. Alle Tests und Datenvollständigkeit unabhängig prüfen. Vor einer Freigabe Kurs-Runner/Replay/Laufzeitverträglichkeit messen, alte Referenz sichern; kein Gewichtswechsel allein aufgrund eines Panelwerts. Kein tatsächlicher Moodle-Upload.

## Diagnosen ohne Nachoptimierung

- Maskierte Aktionsunterschiede und Q-Skalen gegenüber Eltern/V14 auf einer festen bekannten Zustandsbank, ohne die frischen Bestätigungskarten zu sehen.
- Kandidat gewinnt/Referenz verliert versus umgekehrt, pro Gegner und Karte.
- Vergleich ALL42 mit REPLACE36; Anzahl und Zusammensetzung sind dabei nicht kausal isoliert.
- Modellgröße, Laufzeit und Speicher. Die mathematische Zahl der Netze allein sagt nichts über bessere Entscheidungen.

Nach einer fehlgeschlagenen Bestätigung endet diese Welle. Weitere Ideen benötigen neue Hypothese, separate Dokumentation und neue Karten, keine blinde Wiederholung.
