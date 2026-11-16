# R3 in Match eins, V15 bei der Wiederbesetzung

**Der frische Solution-Satz belegt keinen Vorteil des Kandidaten gegenüber R3. R3 bleibt die Abgabe.**

## Gegen Solution auf neuen Karten

Jeder Agent spielte dieselben 40 vorab festgelegten Karten auf beiden Startseiten gegen Original-Solution_92. Ein ganzes Spiel umfasst drei Matches. Zwei gewonnene Matches entscheiden das Spiel.

| Agent | Gewonnene Spiele |
|---|---:|
| Gezielte Übergabe | 79/80 |
| Original-R3 | 79/80 |
| Bisherige Mischung | 79/80 |

Gegenüber R3 beträgt der Unterschied +0,00 Prozentpunkte (95-%-Kartenintervall -3,75 bis +3,75), einen Sieg hinzugewonnen und einen abgegeben. Gegenüber der bisherigen Mischung sind es +0,00 Prozentpunkte (95-%-Kartenintervall -3,75 bis +3,75), einen Sieg hinzugewonnen und einen abgegeben. Die gepaarten Intervalle beruhen auf 10.000 Ziehungen ganzer Karten mit beiden Sitzen. Bei wenigen Niederlagen bleiben Gewinne auf anderen Karten unsicher. R3s früheres Ergebnis von 788/800 gehört zu einem anderen Kartensatz.

Die drei Agenten verloren jeweils auf einem anderen Sitz. Der Kandidat gewann R3s Verlust auf 7426126/P1 und den der bisherigen Mischung auf 7426132/P0. Dafür verlor er 7426119/P0, wo beide Referenzen siegten.

## Direkt gegen die Eltern

Auf den 16 historischen Duellkarten wurde jede Startseite gespielt. Die vorab festgelegten direkten Originalvergleiche wurden nach Kartennummer und Startseite zugeordnet.

| Gegner | Gezielte Übergabe | Bisherige Mischung | Zusätzliche / abgegebene Siege | Differenz in Prozentpunkten, 95-%-Kartenintervall |
|---|---:|---:|---:|---:|
| R3 | 20/32 | 30/32 | 2 / 12 | -53,12 bis -6,25 |
| V15 | 14/32 | 18/32 | 6 / 10 | -43,75 bis +18,75 |

Original-R3 gewann auf denselben Sitzen 6/32 gegen V15. Die Intervalle des direkten Vergleichs sind wegen der 16 verschiedenen Karten breit.

## Fünf Fälle aus der Diagnose

Jede Zelle enthält gewonnene und verlorene Matches innerhalb einer Partie. Diese fünf Sitze wurden wegen unterschiedlicher Ergebnisse ausgewählt und sind getrennt vom neuen Solution-Vergleich ausgewiesen.

| Karte und Startseite | R3 | Bisherige Mischung | Gezielte Übergabe |
|---|---:|---:|---:|
| 7151043 / P0 | 2:1 | 1:2 | 2:1 |
| 7151059 / P1 | 1:2 | 3:0 | 1:2 |
| 7151068 / P0 | 2:1 | 1:2 | 2:1 |
| 7151073 / P0 | 1:2 | 3:0 | 3:0 |
| 7151094 / P1 | 2:1 | 1:2 | 3:0 |

Auf 7151068/P0 führte ein unterschiedlicher Zug ohne bestätigtes Feld zu zwei verschiedenen Spielverläufen. Die erste Punktgutschrift erfolgte bei R3 in Zug 39 und bei der bisherigen Mischung in Zug 71. Auf 7151073/P0 zog die bisherige Mischung in Match zwei in Zug 23 eine Einheit direkt auf das freie bestätigte Feld (4,7). Die beiden Beispiele begründen die Entscheidung, die frühe Erkundung bei R3 zu belassen und V15 bei der Wiederbesetzung einzusetzen. Die Wirkung eines einzelnen Zuges auf das Endergebnis wurde nicht isoliert gemessen. [Fünf Spielverläufe mit Zugbeispielen](diagnose/ERGEBNIS.md).

### Was die vollständigen Befehle zeigen

Beim neuen Kandidaten waren auf allen fünf Sitzen im ersten Match alle 505 Befehlsmatrizen von Sherlock und alle 505 von Solution identisch zu den Original-R3-Spielen. In Match zwei auf 7151073/P0 besetzten alle vier Varianten erstmals in Zug 7 ein bestätigtes Feld. Bis Zug 25 kam der Kandidat auf 48 besetzte Feld-Züge, R3 auf 34. R3 verlor das Match 565 zu 567, der Kandidat gewann 644 zu 544. Auf 7151059/P1 erreichten Kandidat und V15 das erste bestätigte Feld schon in Zug 24, R3 erst in Zug 27. V15 gewann das Match 309 zu 264, der Kandidat verlor 330 zu 361. [Direkter Vergleich aller vier Agenten](vergleich/ERGEBNIS.md).

Auch den einzigen neu verlorenen Sitz haben wir anschließend zur Diagnose wiederholt. Auf 7426119/P0 erreichte eine Einheit in Match zwei das bestätigte Feld (5,16) vor Zug 22 und zog sofort nach links weiter. Die bisherige Mischung hielt auf ihrem eigenen Spielverlauf das erste Feld und besetzte zusätzlich ein zweites. In den ersten 25 Zügen des dritten Matches kam der Kandidat auf 4 besetzte Feld-Züge, beide Referenzen auf 21. Diese drei nachträglichen Wiederholungen zählen nicht erneut zu den 80 Sitzen. [Nachschau mit Punkteständen und allen Befehlen](vergleich/frisch/ERGEBNIS.md).

## Welche Befehle änderten sich?

In den 80 neuen Solution-Partien behielt der Kandidat im ersten Match bei 15.149 abweichenden Kontaktbefehlen den Vorschlag von R3. In späteren Matches übernahm er 3.734 abweichende Befehle von V15 während der frühen Wiederbesetzung außerhalb des Kontakts und 24.111 im Kontakt. Die Bedingung „mindestens ein bestätigtes Feld“ änderte auf den 80 Sitzen keinen einzigen abweichenden Befehl. Der tatsächlich wirksame Unterschied zur bisherigen Mischung lag auf diesen Karten im ersten Match. Ein Befehl zählt jeweils für eine Einheit und einen Zug. Diese Zahlen messen die Nutzung der Regel. [Regel](REGEL.md) · [Vollständige gepaarte Auswertung](auswertung.json).

## Reproduktion

Aus dem Projektverzeichnis prüft der Projektinterpreter die gespeicherten Daten mit `python -B experiments/analysis/r3_field_20261116/auswertung.py`. Er prüft SHA-256 und Umfang aller verwendeten Spielreihen, drei Matchentscheidungen pro Spiel und die vollständigen Kartenpaare. Für neue Spielreihen lässt sich die [ursprüngliche Laufzeit](../r3_v15_blend_20261116/REPRODUKTION.md) wiederherstellen. Danach `versuch.py` für die Phasen `parents`, `cases` und `candidate` jeweils mit `--runtime` und einem neuen `--out` ausführen. Das Archiv der freigegebenen Version hat SHA-256 `8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d`.
