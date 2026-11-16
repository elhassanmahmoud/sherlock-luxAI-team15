# Welche gegnerischen Punkte verhinderte der V15-Schuss unmittelbar?

**Über 49 getrennt berechnete Ein-Zug-Gegenproben erzielte Solution 163 Punkte mit den tatsächlichen V15-Befehlen und 205 mit den alternativen Befehlen.** V15 verhinderte damit auf seinen eigenen Spielverläufen in der Summe 42 gegnerische Feldpunkte. Bei 38 davon hatte Solution bereits vor dem Zug auf dem betreffenden Feld gepunktet (Nettozählung). Sherlocks eigene Punktgutschrift war in jedem der 49 Vergleiche identisch.

| V15 gegen Solution | Züge mit Übergabe | Getauschte Einheitsbefehle | Züge mit weniger gegnerischen Punkten | Direkt verhinderte gegnerische Punkte |
|---|---:|---:|---:|---:|
| 7158016 / P0 | 1 | 1 | 0 | 0 |
| 7158020 / P0 | 10 | 14 | 5 | 7 |
| 7158020 / P1 | 15 | 17 | 7 | 13 |
| 7158030 / P1 | 23 | 29 | 13 | 22 |
| Gesamt | 49 | 61 | 25 | 42 |

In keiner Gegenprobe bekam Solution mit den tatsächlichen V15-Befehlen mehr Punkte. Auf 7158020/P1, Match eins, Zug 42, schlug R3 für Einheit 5 Stehenbleiben vor. V15 schoss mit Zielversatz (−5,−3). Beim identischen Solution-Zug erhielten die Teams mit V15s Schuss 3 und 4 neue Punkte. Beim Stehenbleiben waren es 3 und 6. Solution verlor durch diesen einen Schuss die Gutschriften der Felder (9,6) und (10,6).

## Ablauf und Reichweite

Wir spielten die archivierten Befehle beider Teams auf den vier ursprünglichen V15-Verläufen ohne Modellaufruf erneut ab. Für alle 1.212 Schritte mussten beide offiziellen Punktstände und sämtliche tatsächlich gewerteten Weltfelder mit dem Archiv übereinstimmen. Bei den 61 bereits durch den öffentlichen Filter bestimmten Schüssen ersetzten wir ausschließlich die Befehle der beteiligten Einheiten durch deren aufgezeichnete R3-Vorschläge auf derselben Stellung. Alle anderen V15- und Solution-Befehle sowie Enginezustand und Zufallsschlüssel blieben für den Vergleich identisch. Ein zusätzlicher Zweig mit unveränderten Befehlen musste denselben gesamten Folgezustand und Zufallsschlüssel erzeugen wie die normale Ausführung. Anschließend setzten wir die Aufnahme vom regulären V15-Verlauf fort. Schüsse desselben Zugs wurden gemeinsam zurückgenommen.

Die zuvor beobachtete Änderung von 93 auf 54 Punkten beschreibt zwei aufeinanderfolgende Zustände in der vereinigten Schussumgebung. Die hier gemessenen 205 und 163 betreffen alle Punkte des Gegners im selben Spielschritt bei alternativen Befehlen. Die Einzelschrittsumme erlaubt keine Umrechnung in Matchsiege. Für den Transfer auf R3 gelten dessen separat gespielte Kandidatenpartien.

[Aufzeichnung aller alternativen Befehle, Punktedifferenzen und Felder](ergebnis.json). Aus diesem Ordner lässt sich der Vergleich mit dem historischen Laufzeitordner und dem Projektinterpreter wiederholen:

```sh
"$PY" -B gegenzuege.py --runtime "$LAUFZEIT" --out "$NEUE_DATEI"
```
