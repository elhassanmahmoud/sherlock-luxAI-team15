# Wann verliert V16 den Anschluss auf Punktefeldern?

Das veröffentlichte V16 spielte gegen den Kaggle-Dritten auf den **ersten acht Karten** der archivierten dritten Bestätigung (7261000–7261007, als Player 0). In Match 2 erreichten beide Seiten bis Zug 70 durchschnittlich **6,50 verschiedene Punktefelder**. Ob diese einmal erreichten Felder auch in den letzten 20 Zügen noch Punkte lieferten, unterschied die Spieler deutlich. V16 nutzte dann 36,1 % der möglichen Feldzüge auf diesen Feldern, Kaggle 71,6 %.

| Größe pro Match, über alle drei Matches gemittelt | V16 | Kaggle |
|---|---:|---:|
| Bis einschließlich Zug 70 mindestens einmal bepunktete Felder | 6,46 | 6,83 |
| Bis Matchende mindestens einmal bepunktete Felder | 7,54 | 9,58 |
| Spät genutzte Feldzüge auf den bis Zug 70 erreichten Feldern | 1.180 / 3.100 (38,1 %) | 2.138 / 3.280 (65,2 %) |
| Punkte pro spätem Zug von bis Zug 70 erreichten Feldern | 2,46 | 4,45 |
| Punkte pro spätem Zug von erst nach Zug 70 erreichten Feldern | 0,39 | 1,09 |
| Alle Punkte pro spätem Zug | 2,85 | 5,55 |

Jeweils **auf allen acht Karten** fiel der Anteil der spät genutzten Feldzüge bei V16 geringer aus. Vom späten Rückstand von insgesamt 2,70 Punkten pro Zug entfallen 2,00 auf die früher erreichten und 0,70 auf die später erreichten Felder. Die ersten beiden Differenzen sind aus ungerundeten Werten berechnet. Die Feldgruppen sind teambezogen. Ein Feld kann bei einem Team früh und beim anderen spät zählen.

## Was das für den Versuch bedeutet

Die acht Karten sprechen dafür, den Zeitraum **nach der ersten erfolgreichen Besetzung** genauer anzusehen. Aus diesen Werten allein lässt sich nicht ablesen, ob ein Halter umgekommen ist, sich freiwillig bewegt hat oder ob ein Gegner die Rückkehr verhinderte. Auch eine durch andere Figuren wiederholte Besetzung zählt. Kaggle gewinnt alle acht ausgewählten Spiele, V16 zwei der 24 Matches; die Gesamtquote stammt aus der größeren Bestätigung.

**Nächste Lernhypothese.** Nach Verlust eines vormals gehaltenen, laut eigenem Gedächtnis sicheren Punktefeldes könnte eine freie, überlebensfähige Nachbareinheit dessen Wiederbesetzung besser timen. Zuerst auf getrennten Entwicklungskarten die tatsächlich verfügbaren Fälle zählen und mit dem Kaggle-Lehrer vergleichen: Kennt V16 das Feld, ist es gerade sichtbar und frei, könnte eine eigene Einheit es ohne Aufgabe eines anderen Punktefelds erreichen, und bewegt sich der Lehrer im selben öffentlich beobachtbaren Zustand dorthin? Nur bei ausreichend vielen abweichenden Lehrerentscheidungen lohnt sich gezieltes Nachtrainieren. Schon geprüfte pauschale Feldzuweisungen haben das Problem im Spiel nicht gelöst. Schon besetzte Felder, Kampf unter Beschuss und fehlende Ersatzfiguren getrennt zählen. Zur Erfolgskontrolle zählen ganze Spiele, mit Seitentausch und frischen Karten gegen Solution, Kaggle und V16.

## Prüfung und Reproduktion

[Feldverlauf je Karte und Match](feldverlauf.json) · [Messskript](feldverlauf.py) · [Archiv der unabhängigen Endstände](../devf_20261117/bestaetigung3_kandidat.csv) · [Frühere Messung der Besetzung pro Zeitblock](../deve_20261117/PUNKTEFELDER.md)

Die Daten stammen aus acht vollständigen, nachgespielten Partien des [freigegebenen V16](../../releases/20261117_sherlock_v16/README.md), SHA-256 `0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099`. Für beide Spieler stimmten in allen 2.424 Zügen die gezählten Felder mit dem Punktezuwachs der Engine überein. Alle acht Endstände nach Matchsiegen und Gesamtpunkten waren mit dem Archiv identisch. Das Messskript liest den vollständigen Zustand ausschließlich **nach** den Aktionen für die Auswertung. Der Agent entscheidet aus seinen normalen Beobachtungen. Die Identität der von einem Team tatsächlich bepunkteten Felder wird rückblickend aus der Engine bestimmt. Ob der Agent selbst jedes dieser Felder bereits sicher erkannt hat, wurde hier nicht erhoben.

Matchzüge sind im Skript wie Agentenentscheidungen mit 0–100 nummeriert, das späte Fenster umfasst Zug 81–100. Ein Feldzug bedeutet eine Runde, in der ein Team auf einem bestimmten Feld punkten kann. Der Nenner der Auslastung beträgt 20 mal die Anzahl verschiedener früh erreichter Felder. Für die Zählung pro Match beginnt die Menge der erreichten Felder leer. Gleiche Karten wie in der früheren Bestätigung, nur ein Startplatz. Das ist eine Diagnose bereits gespielter Partien, kein neuer Leistungstest.

In der Projektumgebung aus dem Repo-Stamm ausführbar:

```sh
python experiments/analysis/v16_finalwoche_20261122/feldverlauf.py
```
