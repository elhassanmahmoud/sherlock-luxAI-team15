# Unabhängig 396 von 400 gegen Solution

Der signalgesteuerte Kundschafter gewann auf 200 neuen Karten **396/400 Spiele (99,0 %)** gegen Solution. Original-V16 gewann **393/400 (98,25 %)**. Der Kandidat holte drei zusätzliche Siege und verlor keinen bisherigen Sieg. Die drei gewonnenen Sitze verteilen sich auf nur **zwei verschiedene Karten**. Das nach ganzen Karten berechnete 95-%-Intervall für den Unterschied von +0,75 Prozentpunkten reicht von **0,00 bis +2,00 Prozentpunkten**. Die [vorab festgelegte Freigabe](BESTAETIGUNG.md) verlangt eine strikt positive Untergrenze. Die separate Kaggle-Stufe wurde deshalb geschlossen. V16 bleibt die geprüfte Abgabe.

| Echter Ganzspielvergleich | V16 | Signal-Kundschafter |
|---|---:|---:|
| Solution, 200 Startseiten P0 | 198/200 | **200/200** |
| Solution, 200 Startseiten P1 | 195/200 | **196/200** |
| Gewonnene Einzelmatches gegen Solution | 1.154/1.200 | **1.163/1.200** |
| Direkt gegen V16, 50 Karten auf beiden Seiten | 50/100 | 50/100 |

**Welche Befehle halfen?** Gegen Solution änderten sich 63 Befehle in 16 von 400 Sitzen auf neun Karten. In zwölf Sitzen fand das Team das nächste Reliktpaar früher und in einem später. Der Punktesaldo des Kandidaten lag über alle 400 Sitze um 1.869 Punkte höher. Auf 160344002/P0 genügten fünf geänderte Bewegungen und auf der anderen Seite derselben Karte zwei, um aus zwei ursprünglichen 1:2-Niederlagen ein 2:1 und ein 3:0 zu machen. Gegen Solution auf 160344183/P0 drehte ein weiterer Satz von fünf geänderten Bewegungen den Ausgang von 1:2 auf 3:0. In allen drei Verläufen kannte das Team zu Beginn von Match 3 mehr bestätigte Punktefelder als V16.

**Direktduell.** 99 der 100 Kandidatensitze gaben exakt die V16-Aktionen aus. Der einzige veränderte Sitz war 160344002/P0. Im unveränderten Gegensitz derselben deterministischen Karte verlor P0 alle drei Matches. Mit dem Scout verlor P0 ebenfalls alle drei. Auf den übrigen 49 Karten ohne Eingriff wurden die identischen globalen Matchsieger auf beiden Sitzen bestätigt. Der Kandidat belegte hier keine bessere direkte Spielstärke.

**War der Hinweis zuverlässig?** Der Kartenprüfer reproduzierte alle zuvor im Spiel gemessenen Aktivierungszeitpunkte auf den 48 Entwicklungskarten und bestimmte anschließend die tatsächlichen Spawnzeiten aller 200 Prüfkarten aus der Original-Engine. V16 hatte in 44 von 400 Sitzen eine nachträglich nachweisbare Suchgelegenheit. Der öffentliche Hinweis kam in 16 dieser Sitze mindestens fünf Züge früh, auf neun Karten, mit 5–49 Zügen Vorlauf. Zwei weitere Warnungen kamen später. Es gab **keinen Fehlalarm auf 71 echten Ein-Paar-Karten**. V16 verlor drei der 16 rechtzeitig gewarnten Partien; alle drei drehte die Suchvariante zum Sieg. Die vier verbleibenden Niederlagen lagen auf P1 und hatten keine Warnung. Auf 160344054 war ein zweites Paar seit Zug 14 aktiv und blieb verborgen. Auf 160344153 existierte in Match 2 kein zweites Paar. Auf 160344000 und 160344179 kannte das Team das zweite Paar in Zug 61 bzw. 28. Eine Regel, die ausschließlich einen zusätzlichen Suchauftrag ausgibt, kann diese vier Fälle nicht gleich begründen.

Die 900 neuen Spiele umfassen je 400 Partien beider Programme gegen Solution und 100 direkte Duelle. Hinzu kamen in der Entwicklung 96 Originalpartien und 192 Kandidatenpartien auf separaten 48 Karten sowie 16 exakt wiederholte Sichtkontrollen. Der Entwicklungsgewinn von 95 statt 94 Sitzen wird getrennt ausgewiesen. [Entwicklungsvergleich](ENTWICKLUNGSERGEBNIS.md) · [Bestätigungszahlen und umgeschlagene Sitze](haupt/ergebnis.json) · [900 gespeicherte Spielausführungen, Teil A](haupt/worker_0.jsonl) · [Teil B](haupt/worker_1.jsonl) · [Externe Prüfung des öffentlichen Hinweises](haupt/signalwahrheit.json)

Vom Projektordner mit der Kurs-Python-Umgebung:

```sh
d=experiments/analysis/v16_finalwoche_20261122/signalstudie
python "$d/publikumspruefung.py" haupt
python "$d/wahrheitskontrolle.py" haupt
```
