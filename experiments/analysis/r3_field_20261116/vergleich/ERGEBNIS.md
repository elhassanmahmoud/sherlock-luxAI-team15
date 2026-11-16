# Frühe Besetzung auf den fünf bekannten Sitzen

Wir haben V15 und den neuen Kandidaten je fünfmal gegen die originale Solution gespielt. Alle Siege, Matchstände, Endpunkte beider Teams und Schrittzahlen stimmen mit den separat erfassten Ergebnissen überein. Beim Kandidaten stimmen auf allen fünf Sitzen im ersten Match sowohl Sherlocks als auch Solutions Befehle vollständig mit den Original-R3-Wiederholungen überein (je 505 von 505 Befehlsmatrizen, einschließlich der Startschritte). Auch Sherlocks sichtbare eigene Einheiten, die bestätigten Felder und sämtliche Punktestände waren in jedem dieser Schritte identisch.

## Wann besetzen die Agenten ihr erstes bekanntes Feld?

Jede Zelle enthält den ersten Zug mit mindestens einem besetzten, als Punktefeld bestätigten Feld in Match zwei und drei. Die Position stammt aus der Beobachtung **vor** Ausführung dieses Zuges. Bereits Zug eins enthielt in jedem dieser Matches mindestens ein bestätigtes Feld, bei allen vier Agenten. Der Startschritt null ist ausgeschlossen, weil dort noch Einheiten aus dem vorigen Match sichtbar sein können.

| Karte / Sitz | R3 | Bisherige Mischung | V15 | Neuer Kandidat |
|---|---:|---:|---:|---:|
| 7151043 / P0 | 4 / 2 | 4 / 2 | 4 / 2 | 4 / 2 |
| 7151059 / P1 | 27 / 16 | 27 / 15 | 24 / 15 | 24 / 15 |
| 7151068 / P0 | 5 / 2 | 6 / 2 | 5 / 2 | 5 / 2 |
| 7151073 / P0 | 7 / 12 | 7 / 11 | 7 / 11 | 7 / 11 |
| 7151094 / P1 | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 |

## Wo frühe Besetzung hilft

**7151073 / P0.** R3 verlor diese Partie. Im ersten Match erreichte V15 ein bestätigtes Punktefeld in Zug 12, R3 in Zug 14. Trotzdem verbuchte R3 den ersten Punkt schon nach Zug 9, V15 nach Zug 11, und beide gewannen Match eins. Ein tatsächlich punktendes Feld kann der Agent erst später als solches erkennen. In Match zwei besetzten alle vier Agenten erstmals in Zug 7 ein bestätigtes Feld. Bis Zug 25 kommen bei R3 34 besetzte Feld-Züge zusammen, bei den drei anderen Agenten jeweils 48. Dafür wird in jedem Zug jedes verschiedene bekannte, von einer lebenden Einheit besetzte Feld einmal gezählt. Der Zwischenstand beträgt bei R3 38 eigene Punkte, bei den anderen jeweils 54. R3 verliert das Match mit 565 zu 567, der neue Kandidat gewinnt mit 644 zu 544.

**7151059 / P1.** Hier verlor R3 die zweite bekannte Partie. In Match eins verbuchten R3 und die frühere Mischung den ersten Punkt nach Zug 29, V15 nach Zug 32. Die frühere Mischung gewann die Partie trotzdem 3 zu 0. In Match zwei erreicht der Kandidat das erste bestätigte Feld drei Züge früher als R3 und zur selben Zeit wie V15. Dennoch verliert er das Match 330 zu 361, während V15 mit 309 zu 264 gewinnt. Die spätere Mischung aus Feldkontrolle, gegnerischen Punkten und Kämpfen bleibt für diesen Sitz zu erklären. Allein die drei Züge früherer Besetzung liefern dafür keine Erklärung.

Die fünf Sitze wurden anhand divergierender früherer R3-/Mischungsergebnisse ausgewählt. Der reine V15 gewinnt vier dieser fünf Partien (Niederlage auf 7151043/P0), ebenso der neue Kandidat (Niederlage auf 7151059/P1). Die gepaarten Ergebnisse auf weiteren Karten stehen im übergeordneten Studienbericht.

Die zehn zusätzlichen [Zugfolgen und Kennzahlen](daten/) ergänzen die [Originalaufzeichnungen](../diagnose/roh/). Für eine Wiederholung den gemeinsamen nativen Laufzeitordner anhand der Vorgängerstudie wiederherstellen und `wiederholung.py --runtime LAUFZEIT --originals ../diagnose/roh --out NEUER_ORDNER` aus diesem Verzeichnis mit dem Projekt-Python ausführen.
