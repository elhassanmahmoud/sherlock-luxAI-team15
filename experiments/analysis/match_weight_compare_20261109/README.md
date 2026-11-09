# Fester Vergleich nach Matchgewicht-Training

V14 (36 Netze), CONTROL38 und MATCH38 (je ursprüngliche 36 plus beide vollständigen Endnetze). [Vorab festgelegter Umfang und Gates](../../../docs/superpowers/plans/2026-11-09-match-weight-training.md), [akzeptierte tatsächliche Trainingsabschlüsse](../match_weight_20261109/TRAININGSERGEBNIS.md).

**Aktuell abgeschlossen:** alle 200 festen Spiele unabhängig geprüft, MATCH38 nach allen vier vorab festen Gates nominiert. V14 bleibt bis zur getrennten Bestätigung unverändert. [Ergebnis mit Unsicherheit](ERGEBNIS.md).

Die folgende Aufnahmebeschreibung dokumentiert das vorab festgelegte Vorgehen: Zuerst prüft eine eigene Aufnahme die tatsächliche Montage und den unveränderten Agentenloader ohne Spiele. Erst nach tatsächlicher Root-Abnahme werden separat 200 feste Spiele aufgenommen: drei Solution-Reihen zu je 40 und zwei direkte Reihen zu je 40. Maximal zwei Worker, keine Wiederholung oder Verlängerung und keine automatische Gewichtsübernahme.

Die reservierten Karten werden aus dem bereits geprüften Trainingsplan übernommen. Der zusätzliche Nachweis unter preparation/delta-check.json prüft alle 1.998 intervenierenden eigenen Ausführungen, einschließlich der unterbrochenen Runde; keine Überschneidung mit den 60 Leistungskarten. Grenzen des ursprünglichen lokalen Scans bleiben erhalten.

Unterschiedliche Rewardziele können unterschiedliche Q-Skalen erzeugen. Deshalb ist das gemeinsame arithmetische Mittel eine empirisch zu prüfende Entscheidung. Gleiche Inferenzregeln und Originalmitglieder, keine Trainingskonfiguration in die Auswertung kopieren. Ein technischer Erfolg ist kein Stärkenachweis; 40/40 auf 20 Karten wäre keine allgemeine 100-Prozent-Garantie.

## Werkzeugprüfung

93 gezielte synthetische Tests bestanden in 4,33 Sekunden; unabhängiger finaler Code-/Methodenreview und Root-Abgleich bestanden. Testbeleg und Review unter operations. Diese synthetischen Tests selbst luden keine Produktionsgewichte und starteten keine Spiele; die späteren tatsächlichen Phasen sind im Ergebnis dokumentiert.
