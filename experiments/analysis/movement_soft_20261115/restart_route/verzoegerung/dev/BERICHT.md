# Verzögerte R3-Rückkehr zum bestätigten Ziel gegen Solution

14 neue Sitzpartien auf sieben vorab benannten historischen Karten. Die vorher unabhängig kalibrierte Grenze lag bei 12,5. Eine Rückkehr zum V14-Befehl war damit frühestens im laufenden Matchschritt 13 möglich. Der Vergleich umfasst 28 überprüfte historische Referenzpartien mit denselben Karten, Sitzen, Gewichten und Spielregeln.

| Arm | Ganze Spiele gewonnen | Matches gewonnen |
|---|---:|---:|
| R3 | 13/14 | 39/42 |
| Sofortroute | 13/14 | 33/42 |
| Verzögerte Route | 12/14 | 34/42 |

| Verzögert gegenüber | Gerettet | Neu verloren |
|---|---|---|
| R3 | 7273148/P0 | 7273105/P0, 7273105/P1 |
| Sofortroute | 0 | 7273105/P1 |

**Die erhoffte Reparatur blieb aus.** Die verzögerte Route erhielt den Sieg auf 7273148/P0 und verlor weiterhin 7273105/P0. Hinzu kam eine Niederlage auf dessen Gegensitz. Der Entwicklungstest rechtfertigt den bedingt vorgesehenen Folgeversuch auf 7285000–7285059 nicht.

## Die zwei vorab benannten Fragen

| Karte und Sitz | Match | R3 Punkte und erster öffentlicher Schritt | Sofortroute | Verzögerte Route |
|---|---:|---|---|---|
| 7273105/P0 | 2 | 798–725, Schritt 15 (Sieg) | 776–792, Schritt 12 (Verlust) | 767–789, Schritt 15 (Verlust) |
| 7273105/P0 | 3 | 907–815, Schritt 12 (Sieg) | 765–814, Schritt 12 (Verlust) | 797–815, Schritt 12 (Verlust) |
| 7273148/P0 | 2 | 229–245, Schritt 41 (Verlust) | 334–204, Schritt 21 (Sieg) | 334–204, Schritt 21 (Sieg) |
| 7273148/P0 | 3 | 343–398, Schritt 14 (Verlust) | 362–394, Schritt 14 (Verlust) | 373–328, Schritt 17 (Sieg) |

- 7273105/P0 gegenüber R3. Erste Abweichung im Match 2, Befehl 13 (global 114).
- 7273105/P0 gegenüber Sofortroute. Erste Abweichung im Match 2, Befehl 4 (global 105).

- 7273148/P0 gegenüber R3. Erste Abweichung im Match 2, Befehl 17 (global 118).
- 7273148/P0 gegenüber Sofortroute. Erste Abweichung im Match 3, Befehl 10 (global 212).

Auf dem neu verlorenen Schutzsitz 7273105/P1 wich erstmals bei M2-Schritt 13 UID 3 von R3 ab. Den ersten öffentlichen Punkt erreichten beide in Schritt 15. R3 gewann dieses Match 833–793, die verzögerte Route verlor 774–794. Der Zeitpunkt ihres ersten Punktes unterschied die späteren Gewinner in diesem Paar nicht.

Von den fünf früheren R3-Rettungen gegenüber V14 gewann die verzögerte Variante 5, auf den zugehörigen sieben Gegensitzen 6 von sieben. Diese Karten wurden wegen bekannter Verläufe ausgewählt. Das Ergebnis beschreibt den ausgewählten Diagnoseblock.

Über die erreichten Stellungen gab es 107 tatsächlich angewandte Einheitenbefehle ab Schritt 13 und 43 davor zurückgehaltene mögliche Eingriffe. Die Zähler entlang der erreichten Stellungen erklären für sich keine späteren Matchausgänge.

Alle 14 neuen Befehlsströme enthalten 303 vollständige Schritte mit beiden Teams. Der unabhängige Prüfer glich jedes protokollierte Ereignis gegen tatsächliche UID, Weltbefehl, Matchuhr und Wegedistanz ab. Für zwölf Sitze verglich er außerdem jede frühe Abweichung mit den gespeicherten vollständigen Befehlsarrays beider früheren Versionen. Für 7273105/P0 und P1 enthalten die alten Reproduktionen Hashes statt Roharrays. Dort wurden je Sitz das komplette erste Match, der gemeinsame 105-Schritt-Präfix und die protokollierten Befehle der ersten abweichenden UIDs geprüft. Matchsiege stammen aus dem offiziellen Siegerstand. Der erste öffentliche Punkt erscheint einen Entscheidungsschritt nach dem erstmals bepunkteten Befehl.

[Alle 126 Matchzeilen](matches.csv) · [Unabhängiger Rohdatenabgleich](raw_audit.json) · [Versuchsergebnis und Einzeldateihashes](summary.json) · [Gebundene Quellen und historische Referenzen](manifest.json)
