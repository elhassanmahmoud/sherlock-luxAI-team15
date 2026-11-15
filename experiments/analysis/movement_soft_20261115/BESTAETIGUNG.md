# R3 gewinnt 88 von 120 direkten Duellen gegen V14

Der R3-Schüler darf bei hoher Sicherheit einen gültigen Bewegungsbefehl von V14 ändern. Energieangriffe (SAP) und ihre Ziele übernimmt der Kandidat von V14. Nach der [Vorauswahl](AUSWAHL.md) spielten beide Agenten gegen zwei externe Gegner auf 60 neuen Karten mit beiden Startpositionen. Für das direkte Duell kamen weitere 60 Karten mit beiden Positionen zum Einsatz. Insgesamt wurden 600 Spiele mit je drei Matches vollständig ausgeführt.

| Gegner | R3, gewonnene Spiele | V14, gewonnene Spiele | Gewonnene Einzelmatches R3 / V14 |
|---|---:|---:|---:|
| Solution_92 | 119/120 (99,17 %) | 115/120 (95,83 %) | 347/360 gegenüber 323/360 |
| Nativer Kaggle-Drittplatzierter | 0/120 | 0/120 | 4/360 gegenüber 10/360 |
| R3 gegen V14 | 88/120 (73,33 %) | 32/120 | 264/360 gegenüber 96/360 |

Die Unsicherheit wurde aus 10.000 Ziehungen ganzer Karten berechnet. Beide Seiten und bei den externen Vergleichen beide Gegner jeder Karte bleiben zusammen. Direkt reicht das 95-%-Intervall für R3s Siegquote von 61,67 bis 83,33 %. Gegen Solution gewann R3 fünf vorher verlorene Spiele und verlor eines, das V14 gewonnen hatte. Der Unterschied beträgt +3,33 Prozentpunkte mit einem Intervall von 0 bis +7,50. Über beide externe Gegner beträgt er +1,67 Prozentpunkte mit einem Intervall von 0 bis +3,75. Die vorab festgelegte Untergrenze für den externen Vorteil muss über null liegen. Drei der vier Bedingungen sind erfüllt. V14 bleibt die Turnierversion.

Das einzige verlorene Solution-Spiel von R3 war Karte 7273148 auf Spielerposition 0. R3 verlor zwei von drei Matches trotz 887 zu 660 Punkten insgesamt. V14 gewann dort zwei Matches und erzielte 762 zu 751 Punkte. Eine über das ganze Spiel aufsummierte Punktedifferenz kann die Niederlage deshalb verdecken. Nachträgliche Untersuchungen dieses Falls zählen als Entwicklung.

Die externen Karten sind 7273100–7273159, die Direktkarten 7273200–7273259. Die Spielschlüssel aller drei Gruppen sind je Gruppe eindeutig. Aus den Rohzeilen wurden sämtliche Summen unabhängig nachgezählt und deren SHA-256-Prüfsummen mit der Auswertung abgeglichen. [Auswertung und Prüfsummen](confirmation/assessment.json) · [R3 gegen externe Gegner](confirmation/r3/games.jsonl) · [V14 gegen externe Gegner](confirmation/v14/games.jsonl) · [Direkte Duelle](confirmation/direct/games.jsonl).
