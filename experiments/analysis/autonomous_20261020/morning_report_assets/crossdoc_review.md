# Abschließender dokumentübergreifender Review

Nur lesend geprüft: `docs/MORGENBERICHT_20261021.md`, `README.md`, `CLAUDE.md`, `docs/superpowers/plans/2026-10-20-autonomous-improvement.md` und sämtliche fünf Dateien in `experiments/analysis/autonomous_20261020/morning_report_assets/`. Keine Modelle, Spiele, Git- oder Repositoryänderungen; keine Wiederholung bereits geprüfter Ergebnisrechnungen.

## Konkrete Korrekturen

1. **Defekter relativer Link:** Plan, Zeile 119, Übernahmebericht: `../../../../experiments/analysis/autonomous_20261020/RELEASE.md` geht eine Ebene zu weit nach oben. Richtig ist `../../../experiments/analysis/autonomous_20261020/RELEASE.md`. Alle anderen geprüften relativen Dateilinks lösen auf vorhandene Dateien auf.
2. **Veraltete nächste Schritte:** README, Zeile 284 unter „Grenzen und nächste Schritte“, nennt aktive Zielvergabe, Sap-Ziele und Rewardvergleich weiterhin als nächste Versuche. Diese Studien sind nach Morgenbericht und aktuellem Plan bereits abgeschlossen. Absatz auf abgeschlossene negative/unklare Ergebnisse und den noch ungestarteten Curriculum-Entwurf aktualisieren; Stand dort von 20. auf 21.10. setzen. Die übrigen fachlichen Grenzen können bestehen bleiben.

## Historische 18.000: Korrektur meines vorigen Reviews

Die Teilmengenbehauptung in meinem ersten Review war nicht belegt und wird zurückgenommen. Die Identitäten lassen sich nun anhand der vorhandenen Manifeste unterscheiden:

- Historischer Präsentationsstand: `20261010_full_s0..s2` (Variante `full`) und `20261011_full_sym_s0..s2` (Variante `full_sym`), je 3.000 Spiele. Das Experimentprotokoll, Zeile 156, beschreibt daraus `old3_sym3`.
- Heutige V3-Gruppe `rules6`: `20261019_full_rules_s0..s5` (Variante `full_rules`), je 3.000 Spiele; diese sechs anderen Läufe stehen in `experiments/candidates_20261020.json`, Zeilen 8–13, zusätzlich zu zwölf 4.000er-Läufen.

Die alten 18.000 dürfen daher nicht einfach als Teil der heutigen dokumentierten 66.000 Quelllaufspiele bezeichnet werden. Der Morgenbericht trennt diese Mengen korrekt. Die ablehnende Erläuterung im Assets-README ist richtig; der unveränderte erste Review ist ein historischer Textbeleg und keine verbindliche Herkunftsquelle. Empfehlenswert ist, diese eindeutige Rücknahme mit dem Archiv zu verlinken.

## Konsistenz und Grenzen

- V3 bleibt Abgabe, V4 ohne Übernahme, 18.800 neue Trainingsspiele, 66.000 historische V3-Quelllaufspiele und passive Aktionsbefunde sind zwischen Bericht, README-Einstieg und CLAUDE konsistent. Die zwei vorher empfohlenen sprachlichen Präzisierungen zu PPO und 5,2 Stunden sind korrekt umgesetzt.
- Plan kennzeichnet die früheren Fristen/Laufzustände als historische Einträge; der aktuelle Abschlussstand untersagt neue Modellversuche und lässt den Prozess-/Automationsabschluss sichtbar offen. Keine aktuelle Anweisung zum Neustarten alter Versuche ableitbar.
- Kleine optionale Klarstellung: CLAUDE Zeile 13 heißt noch „Aktueller Präsentationsstand vom 15.10.“ und endet mit einer historischen Änderungsbeschränkung. „Historischer Präsentationsstand vom 15.10.; damalige Beschränkung“ würde die schon später erklärte zeitliche Einordnung auch direkt dort sichtbar machen. Aktuelle explizite Team-Anweisungen haben laut Zeile 6 ohnehin Vorrang.
- Alle im Assets-Manifest aufgeführten Hashes einschließlich PNG stimmen. Historischer Renderer ist ausdrücklich Textsnapshot mit dokumentierten Ausgabepfaden; keine implizite Trainingsanleitung. Grafik und Werte waren bereits im vorherigen Review geprüft und wurden nicht neu berechnet.
- Abschließender Git-/Prozess-/Automationsnachweis bleibt absichtlich ausstehend; dieser Review bestätigt ihn nicht. Keine weitere wichtige inhaltliche Abweichung gefunden.
