# Warum verliert R3 diese fünf Spiele?

Auf den 100 bekannten Dev-A-Karten gegen Solution gewann R3 195 von 200 Partien. Untersucht werden alle fünf Niederlagen und als Gegenprobe die drei ersten **verschiedenen** Karten nach aufsteigender Seednummer, auf denen R3 ein V14-Verlustspiel gewann. Je Karte zählt der erste gerettete Sitz. Der eingefrorene R3 und der damalige V14 spielen jeden ausgewählten Sitz einmal. Das sind 16 Reproduktionen von acht bekannten Startpositionen auf sechs Karten. Jeder Lauf prüft den Endstand gegen die ursprüngliche Zeile. Der V14- und der R3-Spielpfad verwenden dieselben bereits veröffentlichten Gewichte und dieselben Gegnerquellen wie der Dev-A-Vergleich.

| Bekannte R3-Niederlagen | Gerettete V14-Verlustspiele als Kontrolle |
| --- | --- |
| 7150011/P0 und P1, 7150035/P0, 7150079/P1, 7150096/P0 | 7150003/P0, 7150035/P1, 7150037/P1 |

Die Auswahl umfasst drei zuvor von V14 gewonnene und zwei von V14 ebenfalls verlorene Sitze. Auf 7150035 sind beide Wirkungsrichtungen vertreten. Alle fünf R3-Niederlagen endeten 1:2. Auf 7150079/P1 und 7150096/P0 lag R3 bei der Punktegesamtsumme sogar vorne. Darum zählt das Ergebnis **jedes einzelnen Matches**. Die ursprünglichen [R3-Partien](../dev_a_solution/r3/games.jsonl) und [V14-Zeilen](../../kaggle3_20261115/v14_ref_devA.csv) bleiben die Referenz.

## Was die Rekonstruktion misst

Für jeden Arm getrennt erscheinen die drei Matchsiege bzw. -niederlagen mit Punkten beider Teams und Entscheidungskriterium. Der Bericht zeigt erstes bestätigtes Feld, erste eigene bestätigte Belegung, Beginn des Punktens beider Teams, größten Vor- und Rückstand sowie den Beginn des Rückstands, der bis zum Ende bestand. Für die Phasen 0, 1–33, 34–66 und 67–100 nennt er Punktgewinne, Endstand, Zahl der Schritte im Rückstand, Belegung bestätigter Felder, aktive Schiffe und beobachtbare Einheitsabgänge. Null ist ein beobachteter Nullwert, `null` eine fehlende Gelegenheit. Der volle Spielbericht enthält zusätzlich alle 101 Punktestände jedes Matches in zeitlicher Reihenfolge. Der Beobachter kontrolliert den tatsächlichen Punktezuwachs pro Schritt separat anhand der Engine. Diese Kontrolle erfolgt nach dem Zug außerhalb beider Agenten.

Bei tatsächlichen R3-Eingriffen lässt sich zusätzlich feststellen, ob das Schiff vor dem Zug allein ein bestätigtes Feld hielt, V14s konkrete Anweisung auf derselben R3-Stellung es dort belassen hätte und das Feld nach dem ausgeführten Zug tatsächlich leer war. Die Dauer zählt folgende leere Schrittenden bis zur ersten beobachteten Wiederbesetzung oder zum Matchende. Endet das Match vorher, ist der Zeitraum rechtszensiert. Der Nenner sind einzelne passende Eingriffe. Die zusammengefasste Dauer mehrerer Eingriffe ist keine Zahl verlorener Punkte. Energie-, Positions- und Feldstatistiken zweier kompletter Arme beschreiben deren jeweils eigene Spielgeschichte. Eine einzelne Ursache lässt sich aus solchen Differenzen nicht identifizieren.

Nach der Reproduktion zuerst die Verlustmatches lesen, danach denselben Befund in den geretteten Kontrollspielen prüfen. Einen nächsten Mechanismustest nur vorschlagen, wenn sich eine zeitlich erkennbare öffentliche Situation mit konkreten Ereignissen auf mehreren Verlustkarten belegen lässt und die Kontrollen zeigen, wann derselbe Eingriff nützlich sein kann. Aus dieser gezielten Auswahl entsteht keine neue Aussage zur Siegrate.

## Erneut ausführen

In einer leeren Kopie der Ordner `agents`, `scripts` und `lux` aus `0105658188b2ec5eaf5c3a4b0ef477be9a1412f8` die beiden Dateien `scripts/r3_solution_observation.py` und `scripts/r3_solution_retrace.py` aus `3bd955b531513e8634e04cb638789cf92450f08d` ergänzen. Das [Diagnoseprogramm](../../../../scripts/r3_deva_retrace.py) aus diesem Plan hinzufügen. Aus dieser Kopie starten. `ANALYSIS` bezeichnet den absoluten Pfad zum vorhandenen Ordner `experiments/analysis`, `R3` den publizierten `r3_soft.pth`, `PYTHON` die Projektumgebung, `OUT` ein neues gemeinsames Ergebnisverzeichnis. Jeder der ersten beiden Aufrufe belegt einen Worker.

```sh
"$PYTHON" -m scripts.r3_deva_retrace v14 --analysis "$ANALYSIS" --out "$OUT"
"$PYTHON" -m scripts.r3_deva_retrace r3 --analysis "$ANALYSIS" --r3 "$R3" --out "$OUT"
"$PYTHON" -m scripts.r3_deva_retrace compare --analysis "$ANALYSIS" --out "$OUT"
```

Ein Arm vergleicht alle acht Ursprungszeilen vor seinem Vollständigkeitsbeleg, R3 einschließlich der historischen Eingriffszähler. Die Auswertung akzeptiert nur beide kompletten Arme samt den SHA-256-Werten aller 16 Einzelberichte. Eine Abweichung bleibt als Fehler sichtbar. Kein Modell wird durch die Diagnose trainiert.
