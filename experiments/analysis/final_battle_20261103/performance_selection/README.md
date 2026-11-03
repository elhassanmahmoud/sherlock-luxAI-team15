# Finale Auswahl vom 03.11.2026: FT18 nominiert

**8.800 Spiele vollständig und unabhängig akzeptiert. FT18 wird als einziger Kandidat
auf neuen Karten bestätigt. V14 bleibt bis dahin unverändert die Abgabe.**

80 Karten **851000–851079**, beide Seiten, sieben Rollen. Pro Rolle 1.120 Spiele gegen
Solution_92, sol92_sq, V3, V7, V10, V13 und default; zusätzlich je Kandidat 160 direkte
Spiele gegen V14. Das Panel mittelt die sechs Nicht-default-Gegner gleichgewichtet.
Alle 13 Aufgaben Exit 0, je Spiel 303 Schritte und Punktezählung v2. Laufzeit rund 5 h 11 min.

| Kandidat | Netze | Panelquote | Änderung zu V14 | Solution-Siege | Direkt gegen V14 | Auswahl |
|---|---:|---:|---:|---:|---:|---|
| V14 | 36 | 80,73 % | Referenz | 150/160 | – | Referenz |
| PAIR18 | 18 | 75,63 % | −5,10 pp | 147/160 | 52/160 | abgelehnt |
| PAIR24 | 24 | 80,00 % | −0,73 pp | 154/160 | 84/160 | abgelehnt |
| **FT18** | **18** | **81,67 %** | **+0,94 pp** | **152/160** | **98/160** | **nominiert** |
| Z36 | 36 | 81,56 % | +0,83 pp | 152/160 | 80/160 | zugelassen, nicht nominiert |
| C36 | 36 | 80,63 % | −0,10 pp | 152/160 | 76/160 | nur Kontrolle, nicht nominierbar |
| R36 | 36 | 78,02 % | −2,71 pp | 143/160 | 85/160 | abgelehnt |

Alle Rollen gewannen 160/160 gegen default. Es gab in diesen Daten keine Remis;
die feste Wertung berücksichtigt ansonsten Remis mit 0,5. Prozentpunkte sind
Differenzen auf **denselben Karten**, keine Vergleiche mit früheren Testblöcken.

FT18 enthält ausschließlich die **bereits zuvor nachtrainierte zweite Hälfte der
36 V14-Netze**, Indizes 18–35. Es enthält keines der beiden heute neu trainierten
Netze. Konfiguration und Tensoren der übernommenen Mitglieder bleiben unverändert.
Die Rangfolge war vorab festgelegt: größter Panelgewinn unter den zugelassenen
Kandidaten. Deshalb FT18 vor Z36; das ist kein gesicherter direkter Vergleich beider Methoden.

Die gepaarte FT18-Paneldifferenz hat ein 95%-Intervall von **−3,23 bis +4,90 pp**;
Solution **+1,25 pp [−3,13; +5,63]**, direkt **61,25 % [51,25; 71,25]**.
Die Auswahl ist kein bestätigter Stärkenachweis. Das neue Rettungsnachtraining R36
war in dieser Auswahl schwächer als V14 und Kontrolle. Aus einem einzigen gepaarten
Trainingsstart folgt keine allgemeine Aussage über alle möglichen Nachtrainingsverfahren.

## Daten und Prüfung

- [Offizielle vollständige Auswertung](selection_summary.json)
- [Unabhängiger tatsächlicher Review](review/selection_actual_review.md)
- [Unabhängige Zahlenprüfung](review/actual_review_v2.json)
- Originale CSVs, Logs, Plan und abgeschlossener State unter `selection/`
- `archive_manifest.json`: Herkunft, Größe und SHA-256 aller bytegleich kopierten Nachweise

Die externe Prüfung musste zunächst einen eigenen fehlenden Gegnernamen im
Ausgabeformat ergänzen. Ursprünglicher Fehlerbericht, alte Prüferfassung und die
vollständig bestandene erneute Abnahme sind erhalten. Keine Statistik, Grenzen,
Kandidatenauswahl oder eingefrorene Implementierung wurde dafür verändert.

Die ursprünglichen Ausführungspfade bleiben in den Belegen erhalten. Auswerter sind
als `.py.txt` archiviert, damit eine Archivierung keine Quellen des laufenden Versuchs
verändert. Die aktive Studienkopie bleibt auf Commit `7c906e1` eingefroren.

## Einzige nächste Leistungsphase

FT18 gegen V14: 400 neue Karten **852000–852399**, beide Seiten, sieben Gegner;
zusätzlich 800 direkte Spiele auf **853000–853399**. Insgesamt **12.000 Spiele**.
Gleiche Quelle, Gewichte, Konfigurationen und Auswertung; alle sieben festgelegten
Bestätigungskriterien müssen erfüllt sein. Keine Auswahlkarten dazupoolen und bei
Fehlschlag keinen zweiten Kandidaten nachrücken lassen. Die spätere Bestätigung
und technische Paketabnahme bestimmen die Abgabeentscheidung.

[Fester Plan](../../../../docs/superpowers/plans/2026-11-03-final-battle.md)
· [Training und neue Endnetze](../completed_training/README.md)
