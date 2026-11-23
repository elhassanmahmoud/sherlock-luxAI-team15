# Flottenblick qualifiziert sich für die unabhängige Bestätigung

Auf 40 frischen Karten mit Sensorreichweite eins fand Flottenblick das erste Relikt gegen Solution im Mittel 1,76 Züge früher als Original-V16. Die erste Gutschrift blieb im Mittel gleich. Flottenblick gewann 77 von 80 ganzen Spielen gegen Solution, V16 gewann 76. Im direkten Duell mit V16 gewann Flottenblick 40 von 80. Damit erfüllt er alle sieben vorab festgelegten Auswahlbedingungen. Das Kartenintervall für den Sichtgewinn reicht von 1,06 Zügen später bis 5,13 Zügen früher. Die Nominierung erfordert eine getrennte Bestätigung.

## Gegen dieselbe Original-Solution

Je 80 vollständige Partien pro Vergleichsarm, beide Sitze der 40 Karten mit Seeds zwischen 161620000 und 161620134. Bei Sicht und Gutschrift bedeutet eine positive Differenz eine frühere Beobachtung. Die Intervalle stammen aus 20.000 gepaarten Ziehungen ganzer Karten.

| Maß | Original-V16 | Flottenblick | Gewinn [95-%-Kartenintervall] | Besser / gleich / schlechter |
|---|---:|---:|---:|---:|
| Erste Sicht, Zug | 44,09 | 42,33 | +1,76 [−1,06; +5,13] | 19 / 47 / 14 |
| Erste Gutschrift, Zug | 38,60 | 38,60 | 0,00 [−1,89; +1,59] | 16 / 51 / 13 |
| Eigene Punkte nach Zug 70 | 78,49 | 79,53 | +1,04 [−3,41; +5,80] | 24 / 28 / 28 |
| Gegnerische Punkte nach Zug 70 | 81,25 | 80,45 | 0,80 weniger [−2,31; +3,78] | 30 / 28 / 22 |
| Punktedifferenz nach Zug 70 | −2,76 | −0,93 | +1,84 [−3,74; +7,64] | 28 / 25 / 27 |
| Punktedifferenz nach Match 1 | +156,29 | +152,11 | −4,18 [−22,29; +13,45] | 27 / 23 / 30 |
| Siege in Match 1 | 70/80 | 70/80 | 0,00 Prozentpunkte [−7,50; +7,50] | 3 / 74 / 3 |
| Ganze Siege | 76/80 | 77/80 | +1,25 Prozentpunkte [0,00; +3,75] | 1 / 79 / 0 |

Alle 80 Flottenblick-Sitze sahen ein Relikt in Match 1, Original-V16 auf 78 Sitzen. Alle Sitze erreichten bei beiden Agenten eine Gutschrift. Die drei einzelnen Matchsiegzahlen lauten 70, 78, 71 bei Original-V16 und 70, 78, 70 bei Flottenblick. Die Stände nach Zug 70 und nach Match 1 können mit der anschließenden Spielentwicklung unterschiedliche Richtungen haben.

## Sitze und Gegenbeispiele

| Vergleich gegen Solution | P0 | P1 |
|---|---:|---:|
| Sichtgewinn, Züge | +2,475 | +1,050 |
| Gutschriftgewinn, Züge | +0,850 | −0,850 |
| Gewinn Punktedifferenz Zug 70 | +6,675 | −3,000 |
| Ganze Siege V16 → Flottenblick | 39 → 39 | 37 → 38 |

Der zusätzliche Gesamtsieg kam auf 161620106 P1. Auf 161620068 P0 und P1 sowie 161620111 P1 verloren beide Agenten. Im ersten Match gingen Siege auf 161620043 P0 und P1 sowie 161620044 P0 verloren. Hinzu kamen 161620063 P1 sowie 161620106 P0 und P1. Auf 161620044 P0 sah der Kandidat das erste Relikt 27 Züge später (96 gegenüber 69). Auf 161620043 P1 kam die erste Gutschrift 48 Züge später (85 gegenüber 37), und die Match-1-Punktedifferenz fiel von +80 auf −227. Der größte Sichtgewinn war auf 161620106 P0 mit 52 Zügen (49 gegenüber dem Ersatzwert 101).

Flottenblick änderte gegen Solution 164 Bewegungen auf 58 Sitzen und 29 Karten. Spiele ohne Eingriff stimmten vollständig mit der jeweiligen Referenz überein. Im direkten Vergleich gab es 136 Änderungen auf 56 Sitzen und 28 Karten. Die direkte Siegquote von 50,0 Prozent hat ein 95-Prozent-Kartenintervall von 37,5 bis 62,5 Prozent. Von diesen direkten Spielen gewann Flottenblick 17/40 auf P0 und 23/40 auf P1. Die direkten Matchsiegzahlen waren 44, 38 und 42.

## Nachrechnung

Die unabhängige Nachrechnung erfasste alle 240 vollständigen Partien, 80 gepaarte Sitze, die sechs eingefrorenen Laufzeitdateien, die sieben Hauptkennzahlen mit Intervallen und sämtliche Auswahlbedingungen. Die Kursüberwachung prüfte in jeder Partie sämtliche Befehle beider Seiten über 303 Schritte. Alle Fehlerzähler standen auf null. Wo der Kandidat eingriff, bewegte er ausschließlich die vorgesehene UID im vorgeschriebenen Zeitfenster vor der ersten Sicht.

Die Einzelwerte stehen in `gepaarte_sitze.csv`. Das vollständige Spielprotokoll `partien.jsonl.gz` hat den SHA-256-Wert `21133ddc7d6c6b225a61a1bfd609ec35f9fbe4b60e5e1e5902bd1923c2d0a51a`, die CSV `5d2a39afbac3e5954e7b3914f53897871935858f050d23cfc1685f454996476e`. Quellen, Karten, Ergebnis und Nachrechnung stehen in `serie.json`, `ergebnis.json` und `nachpruefung.json`.
