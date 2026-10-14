# Statistikprüfung vom 14.10.2026

Neuberechnung vorhandener Ergebnisdateien mit dem korrigierten `scripts.compare_report`. Keine neuen Spiele, kein Training, keine Änderung der Gewichte oder historischen Rohdaten. [Maschinenlesbare Ergebnisse und Prüfsummen](../experiments/analysis/paired_bootstrap_20261014.json).

## Methode und Lesart

- Kandidat und Referenz nach Gegner, Karten-Seed und Spielseite paaren; die beiden Seitendifferenzen je Karte mitteln. Ganze Karten mit Zurücklegen ziehen: 5000 Wiederholungen, Zufallsseed 0, 2,5-/97,5-Perzentile für die mittlere Differenz.
- Nur gemeinsame vollständige Karten vergleichen. Beide WR, Differenz und Stichprobengröße verwenden dieselbe Kartenmenge. Nicht gemeinsame Karten werden ausdrücklich als ausgeschlossen ausgewiesen; hier wurde keine ausgeschlossen.
- Fehlende Seiten, doppelte Spielschlüssel, ungültige Ergebnisse oder keine gemeinsamen Karten führen zum Fehler. Bei nur einer gemeinsamen Karte wird die Differenz gezeigt, aber kein Unsicherheitsintervall geschätzt.
- WR bedeutet Mittelwert von `result`, ein Remis zählt 0,5. Die Tabelle zeigt Differenzen und Intervalle in **Prozentpunkten**; das Kommando gibt Anteile aus (0,01 = 1 Prozentpunkt).

## Neu berechnete Ergebnisse

| Vergleich | Gegner | Karten / Spiele | Kandidat / Referenz WR | Differenz | 95-%-KI der Differenz |
|---|---|---|---|---|---|
| Abgabe old3_sym3 vs full_s0 | default | 30 / 60 | 100.00 % / 85.00 % | +15.00 pp | [+3.33; +28.33] pp |
| Abgabe old3_sym3 vs full_s0 | solution92 | 30 / 60 | 46.67 % / 20.00 % | +26.67 pp | [+13.33; +41.67] pp |
| m1_early vs old3_sym3 – Runde 1 | default | 60 / 120 | 100.00 % / 99.17 % | +0.83 pp | [+0.00; +2.50] pp |
| m1_early vs old3_sym3 – Runde 1 | solution92 | 60 / 120 | 42.50 % / 33.33 % | +9.17 pp | [+0.00; +18.33] pp |
| m1_early vs old3_sym3 – Runde 2 | default | 120 / 240 | 96.67 % / 93.75 % | +2.92 pp | [+0.42; +5.83] pp |
| m1_early vs old3_sym3 – Runde 2 | solution92 | 120 / 240 | 42.08 % / 34.17 % | +7.92 pp | [+2.50; +13.75] pp |

**Für die Präsentation:** `m1_early` gegen Solution_92 in Runde 1: jetzt [0,00; +18,33] pp statt des historisch dokumentierten [+0,8; +17,5]. Null liegt im neuen Intervall: diese Runde allein nicht als klar belegten Vorteil darstellen. Runde 2 bleibt bei +7,92 pp mit [+2,50; +13,75] pp. Dies ist keine Freigabe zum Austausch des aktuellen Abgabe-Agenten.

**Grenzen:** Die Intervalle beschreiben Kartenstreuung für feste Agenten, nicht Streuung über neue Trainingsstarts. Keine Korrektur für Mehrfachvergleiche oder Modellauswahl. Wiederholt benutzte Benchmarkkarten werden durch die neue Berechnung nicht zu einem unberührten Abschlusstestsatz. Besonders die Abgabe-vs-Einzelnetz-Zeilen sind daher ein historischer Vergleich, kein unabhängiger Wirksamkeitsnachweis. Kleine Stichproben und seltene Ereignisse können vom Perzentil-Bootstrap unzureichend erfasst werden; auch ein Nullintervall beweist keine allgemeine Gleichheit.

Andere historische Vergleiche wurden hier nicht pauschal neu berechnet. Alte Berichtsausgaben und Tabellen bleiben historische Artefakte. Die separate Zwei-Ebenen-Auswertung `scripts/report.py` wurde nicht verändert.

## Wiederholen

Aus dem Repository-Ordner mit der eingerichteten Python-Umgebung:

```bash
python -m scripts.compare_report --ref experiments/compare/TEST_full_s0.csv experiments/compare/TEST_old3_sym3_points_v2.csv
```

```bash
python -m scripts.compare_report --ref experiments/compare/m1/old3_sym3.csv experiments/compare/m1/m1_early.csv
```

```bash
python -m scripts.compare_report --ref experiments/compare/m1b/old3_sym3.csv experiments/compare/m1b/m1_early.csv
```

Das Skript verwendet ausschließlich `result`; ältere CSVs ohne Punktezählungs-Version sind für diesen Siegvergleich weiterhin verwendbar. Ihre Punktzahlen werden dadurch nicht korrigiert. Den früheren pauschalen Glob über alle CSVs vermeiden: Test- und Validierungskarten können disjunkt sein; Referenz und Kandidaten bewusst auswählen.
