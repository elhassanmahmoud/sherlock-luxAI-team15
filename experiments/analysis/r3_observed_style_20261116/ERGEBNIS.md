# Gegnerbeobachtungen in Match 1 erkennen V14 häufig, lösen bei Solution zu oft aus

In echten R3-Partien erkannte der vorab festgelegte Auslöser **42 von 48 V14-Sitzen**. Auf Kaggle löste er nie aus. Auf Solution löste er dreimal aus; zulässig war höchstens ein Sitz. Damit endet der Versuch nach der Archivprüfung. Es wurden keine Spiele mit einem Umschalter gestartet. [Vorabplan](PLAN.md) · [Endprüfung mit allen 144 Sitzen](pruefung.json)

| Tatsächlicher Gegner | Auslösungen / R3-Sitze | Spieler 0 / Spieler 1 | Betroffene Karten | 95-%-Kartenintervall für den Sitzanteil |
|---|---:|---:|---:|---:|
| V14 | **42/48** (87,5 %) | 21/24 · 21/24 | 21/24 | 75,0–100 % |
| Kaggle | **0/48** | 0/24 · 0/24 | 0/24 | 0–0 % |
| Solution_92 | **3/48** (6,25 %) | 2/24 · 1/24 | 2/24 | 0–16,7 % |

Auf den ersten 48 R3-Karten waren es 28/32 V14-, 0/32 Kaggle- und 2/32 Solution-Auslösungen. Auf den weiteren 24 Karten waren es 14/16, 0/16 und 1/16. Die drei Solution-Fälle betrafen Karte **7287018 auf beiden Sitzen** und **7287114 auf Spieler 0**. Bei V14 reagierten jeweils beide Sitze derselben 21 Karten. Die Intervalle ziehen deshalb ganze Karten. Für Kaggle können bei null beobachteten Auslösungen alle Bootstrap-Stichproben ebenfalls nur null enthalten; weitere Karten können trotzdem Fehlalarme ergeben. [Einzelne Sitzschlüssel und Blockauswertung](pruefung.json)

## Was wurde gemessen?

Der Fit verwendete ausschließlich die 240 früheren R1-Sitze aus der DAgger-Sammlung für R2. Die getrennte Kalibrierung auf 48 weiteren R1-Sitzen lieferte die feste Schwelle **0,722729530667352**. Oberhalb davon lagen 12/16 V14-Sitze und keiner der jeweils 16 Kaggle- und Solution-Sitze. Die Schwelle liegt definitionsgemäß mindestens so hoch wie der höchste Wert für die beiden anderen Gegner in der Kalibrierung. Die R3-Archive wurden erst nach Speicherung dieser Regel geöffnet. Sie sind gegenüber Fit und Kalibrierung kartendisjunkt. [Regel, Koeffizienten, Kalibrierung und Quellhashes](regel.json)

**Korrektur zur Bedeutung der Sichtfläche im Vorabplan.** Ebene 12 zählt Felder, die Sherlock zum aktuellen Zug als erkundet markiert hat. Bei den verwendeten V14-Grundgewichten ist `use_symmetry` aktiv: Das umfasst das aktuelle Sensorfeld **und sein Spiegelbild**. Die Gegnerbelegungs- und Energieebenen 10/11 enthalten dagegen tatsächlich beobachtete gegnerische Schiffe. In den Merkmalen 1, 3 und 9 steht Ebene 12 somit für die durch Symmetrie erweiterte Abdeckung. Verminderte Belegungsübereinstimmung kann auch durch Sichtverlust entstehen. Diese Quellenprüfung erfolgte vor der Merkmalsauswertung. Alle 18 numerischen Merkmaldefinitionen und die Schwelle folgten der registrierten Vorschrift. [Erzeugung der Kartenebenen](../../../agents/sherlock/cnn_model.py) · [Aktualisierung der Sichtabdeckung](../../../agents/sherlock/belief.py)

Die Daten umfassen genau einen rotierenden Gegner je Karte. Jede einzelne Karte kann deshalb auch charakteristische Sicht- und Kontaktgelegenheiten beisteuern. Die Quote beschreibt die Erkennbarkeit in den aufgezeichneten Partien. Ob ein Wechsel zu V15 eine dieser Partien gewinnen oder verlieren würde, wurde nicht gemessen.

## Nachvollziehen

Aus dem Projektverzeichnis mit Python, NumPy, SciPy und beiden ursprünglichen Archivverzeichnissen. `DATA` zeigt auf die lokale Kopie von `experiments/imitation`.

```sh
STUDIE=experiments/analysis/r3_observed_style_20261116
AUSGABE="$(mktemp -d)"
python -B "$STUDIE/archivversuch.py" fit --data "$DATA" --out "$AUSGABE"
python -B "$STUDIE/archivversuch.py" assess --data "$DATA" --out "$AUSGABE"
```

432 vollständige Datei-SHAs wurden mit den früher veröffentlichten Einzelregistern verglichen. Alle 432 Sitze hatten Aufnahmen für sämtliche 100 berücksichtigten M1-Züge. Der Regelhash vor der Endprüfung war `21b26606a15f4f70dc1a5cd786c5fd7dbaf1f816cc1cb0ce66b7d5eaab5bbc06`. Eine zweite, schrittweise Rechnung reproduzierte alle 144 veröffentlichten R3-Scores auf eine absolute Abweichung unter 10⁻¹² sowie sämtliche Auslösungen und Kartenzähler. Die Auswertung nutzte einen Thread, NumPy und SciPy. Während des Versuchs wurden weder Torch noch ein Spielagent geladen. [Auswerter](archivversuch.py)
