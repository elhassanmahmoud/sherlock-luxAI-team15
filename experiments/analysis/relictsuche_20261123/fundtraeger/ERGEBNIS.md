# Wer sah das erste Relikt auf den 96 Wiederholungskarten?

**Bei 18 der 57 früheren Funde sah ausschließlich das umgelenkte Schiff ein aktives Relikt (31,6 %). Bei den anderen 39 reichte die Sicht der übrigen Flotte aus, während das umgelenkte Schiff selbst keinen Knoten sah (68,4 %).** Auf Sitz 0 verteilten sich die früheren Funde auf neun durch den Kundschafter und 18 durch die übrige Flotte. Auf Sitz 1 waren es neun und 21. Der Vergleich umfasst den eingefrorenen Orts- und Flottenkundschafter gegen Solution, jeweils mit Original-V16 auf derselben Karte und demselben Sitz. [Wiederholungsserie](../sicht1_wiederholung/ERGEBNIS.md) · [Alle 192 Sitzbefunde](sitze.jsonl.gz)

| Erstsicht gegenüber Original-V16 | Sitze | Nur Kundschafter | Nur übrige Flotte | Vor der ersten Befehlsänderung | Kein Fund bis Zug 100 |
|---|---:|---:|---:|---:|---:|
| Früher | 57 | 18 | 39 | 0 | 0 |
| Gleich | 98 | 3 | 63 | 31 | 1 |
| Später | 37 | 3 | 32 | 0 | 2 |
| **Alle** | **192** | **24** | **134** | **31** | **3** |

Bei allen 39 früheren Funden durch die Restflotte konnte genau ein anderes Schiff den sichtbaren Knoten aus eigener Kraft erkennen. Über alle 134 Restflottenfunde stand in 125 Fällen genau ein solches Schiff in Reichweite, in neun Fällen jeweils zwei. Von den 189 Sitzen mit Erstsicht hatten 158 zu diesem Zeitpunkt bereits einen geänderten Befehl. Dort zeigte sich kein Fall, in dem Kundschafter und Restflotte jeweils für sich einen Knoten sahen. Ebenso trat kein Fall auf, in dem erst ihre kombinierte Sensorleistung den ersten Fund ermöglichte. Die drei fundlosen Starts werden gesondert geführt. Auf zwei davon hatte V16 einen Fund, auf einem blieben beide Varianten ohne Fund. [Gruppensummen](ergebnis.json)

Auf Karte 165300038, Sitz 0, fand allein das umgelenkte Schiff 2 den Knoten auf (19,2) in Zug 30. V16 sah sein erstes Relikt in Zug 60. Auf 165300321, Sitz 0, sah die Restflotte ohne das umgelenkte Schiff 1 den Knoten auf (4,8) in Zug 50, V16 erst in Zug 97. Die Trennung bezeichnet den physischen Sensor am Fundzug. Eine frühe Kursänderung kann auch die späteren Bewegungen anderer Schiffe beeinflussen.

Für die Auswertung liefen ausschließlich die archivierten Weltbefehle beider Spieler bis zur ersten Sicht oder zum Ende des ersten Matches. Die erste Abweichung gegen die gepaarte V16-Aufzeichnung identifiziert das eine geänderte Schiff. Beim Fund berechnete die originale Kursumgebung die Sicht mit allen Schiffen, ohne den Kundschafter und mit ihm allein. Dabei wurde der tatsächliche Geländestand vor der Nebelverschiebung verwendet. Die volle Maske stimmte mit der öffentlichen Beobachtung überein. Eine zweite Rechnung aus Weltpositionen, Sichtweite und tatsächlicher Nebeldämpfung reproduzierte die einzelnen Sensorbeiträge. Ein separater Archivabgleich prüfte alle Fundzeiten und die abweichenden Schiff-IDs. [Sensornachlauf](nachspielen.py) · [Gegenprüfung](gegenpruefung.json)
