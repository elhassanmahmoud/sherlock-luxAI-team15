# Drei Sherlock-Versionen auf denselben 400 Karten

Mit einer Kartenansicht gewann der ursprüngliche R3 gegen Solution **788/800 (98,50 %)**. V14 gewann 767/800, V15 764/800. Gegenüber V14 beträgt der Unterschied in ganzen Solution-Spielsiegen +2,62 Prozentpunkte (95 % +1,00 bis +4,38).

| Gegner und Kennzahl | V14 | R3 mit einer Ansicht | V15 |
|---|---:|---:|---:|
| Original-Solution, ganze Spiele | 767/800 | 788/800 | 764/800 |
| Original-Solution, einzelne Matches | 2144/2.400 | 2286/2.400 | 2204/2.400 |
| Kaggle-Dritter, ganze Spiele | 12/800 | 12/800 | 12/800 |
| Kaggle-Dritter, einzelne Matches | 86/2.400 | 80/2.400 | 102/2.400 |

R3 gewann gegen Solution 30 Sitze, die V14 verloren hatte, und verlor 9 frühere V14-Siege. Gegen Kaggle waren es 8 hinzugewonnene und 8 verlorene Sitze. Über beide Gegner mit gleichem Gewicht beträgt die Differenz +1,31 Prozentpunkte (95 % +0,25 bis +2,44). Für die zuvor festgelegte Überlegenheit muss die Untergrenze über null liegen und die Solution-Siegzahl mindestens V14 entsprechen. Beide Kriterien sind erfüllt.

Die getrennte Direktprüfung gewann R3 mit 88/120 gegen V14. Das 95-%-Kartenintervall für seine Siegquote reicht von 61,67 bis 83,33 %. Das historische und das aktuelle V14 erzeugten auf der registrierten Kursaufnahme 4242 dieselben 606 Befehlsmatrizen für beide Startseiten. [V14-Quellenvergleich](../../v14_course_trace_20261116/README.md) · [R3-Kurspaket und 606 Vergleiche gegen den Forschungsagenten](../candidate_package/README.md)

## Wie weit reicht eine Wahl zwischen den drei Agenten?

Auf jedem der zwölf von R3 verlorenen Solution-Sitze gewann V14 oder V15. Hätte man für jeden Sitz den Sieger im Nachhinein auswählen dürfen, wären höchstens 800/800 Siege möglich gewesen. Eine einzige Wahl für beide Sitze derselben Karte hätte höchstens 799/800 erreicht. Das sind rechnerische Obergrenzen für diese drei vorhandenen Versionen. Ein Agent müsste vor seiner Entscheidung aus öffentlich sichtbaren Spieldaten erkennen, welches Verhalten hilft. [Gemeinsame Niederlagen mit den Endständen aller Versionen](sitzvergleich/coverage.json) · [Einzelvergleich nach Gegner, Karte und Sitz](sitzvergleich/joined.csv)

## Karten und Nachprüfung

Beide Startseiten und beide Gegner wurden auf 7158000–7158399 ausgewertet. Die V14- und V15-Ergebnisse waren zuvor veröffentlicht. Eine technische Aufnahme reproduzierte alle 16 vorgesehenen V14-Spiele einschließlich der beiden Punktestände. Erst danach wurden genau 1.600 R3-Partien gespielt. Alle 303 Züge und drei Matches je Partie sind in den geprüften Spielabschlüssen vertreten. Die Unsicherheitsintervalle ziehen 10.000-mal ganze Karten, einschließlich beider Sitze und gemeinsam für die beiden Gegner. Der separate Diagonaltest auf dem ersten Viertel addiert keine weiteren Karten zu diesem Vergleich. [Plan](PLAN.md) · [Gepaarte Intervalle und Prüfsummen](measured/assessment.json) · [R3-Rohdaten](measured/r3/games.jsonl) · [Diagonaler Vergleich auf 100 dieser Karten](../../movement_reflection_20261115/solution_quarter/ERGEBNIS.md)
