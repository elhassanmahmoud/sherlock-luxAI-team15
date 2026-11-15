# Wo der gemischte Hybrid gegen Solution Punkte liegen lässt

Auf den 400 Bestätigungskarten erzielte Solution gegen den v4-Mixed-Hybrid im Mittel **134 Punkte weniger je Spiel** als gegen V14 (gepaartes 95-%-Intervall −150 bis −118). Sherlock selbst erzielte **31 Punkte weniger** (−51 bis −10). Die gemessene Zahl eigener Einheitenzüge stieg um **108** (+98 bis +118). Das Muster passt zu einem Agenten, der den Gegner stärker unter Druck setzt und aus den eigenen verfügbaren Einheiten noch mehr Punkte holen könnte.

| Gepaarte Spiele gegen Solution | Mittlere Änderung eigener Punkte | Mittlere Änderung gegnerischer Punkte | Neu verlorene Spiele mit weniger eigenen Punkten | Davon mit mehr eigenen Einheitenzügen | Neu gewonnene Spiele mit weniger gegnerischen Punkten |
|---|---:|---:|---:|---:|---:|
| Dev A, 100 Karten / 200 Spiele je Agent | −6 | −151 | 5/5 | 5/5 | 11/11 |
| Dev B, 100 Karten / 200 Spiele je Agent | −52 | −130 | 6/6 | 6/6 | 10/11 |
| Bestätigung, 400 Karten / 800 Spiele je Agent | −31 | −134 | 33/33 | 31/33 | 30/30 |

Ein neu verlorenes Spiel ist ein identischer Seed und Sitz, den V14 gewann und der Hybrid verlor. Diese nachträgliche Gruppierung isoliert keinen ursächlichen Effekt. Auf der Bestätigung verteilen sich die 33 neuen Niederlagen auf 25 Karten, mit 17 auf Spieler 0 und 16 auf Spieler 1. Die 30 neuen Siege verteilen sich auf 26 Karten, mit 15 je Sitz. Der Median der 33 neuen Niederlagen beträgt −293 eigene Punkte bei +60 eigenen Einheitenzügen. Als Einheitenzug zählt der Tracker eine von `units_mask` gemeldete eigene Einheit je Schritt. Die Metrik misst weder bestätigte Überlebenszeit noch besetzte Punktefelder. Die CSV enthalten die Anzahl gewonnener Matches und die korrigierte Punktesumme über alle drei Matches. Welches Match zuerst gewonnen wurde und wann ein Punktefeld frei wurde, lässt sich daraus nicht ablesen.

## Zwei Seiten derselben Karte

Auf Dev A entscheidet bei beiden Varianten exakt derselbe v4-Schüler. In `points` übernimmt V14 die Halter bestätigter Punktefelder und Einheiten auf dem Weg dorthin. In `mixed` darf in sichtbarer Gegnernähe auch auf diesen Schiffen der Schüler entscheiden. Auf Karte **7150068** kippt der Sieger in den beiden Richtungen.

| Gewonnene Matches von drei | V14 | v4 points | v4 mixed |
|---|---:|---:|---:|
| Spieler 0 | 3 | 1 | 2 |
| Spieler 1 | 2 | 2 | 0 |

Ein Schalter pro Karte würde hier mindestens einen Sitz verlieren. Im gesamten Dev A rettet `points` vier der fünf von `mixed` gegenüber V14 neu verlorenen Spiele. Die elf neu gewonnenen Spiele hält `points` alle. Zugleich verliert `points` fünf von 183 Sitzen, die `mixed` und V14 beide gewinnen. Für Dev B und die Bestätigung gibt es in dieser Veröffentlichung keine vergleichbare `points`-Messung.

## Eine prüfbare Änderung

Zuerst beide Sitze auf 7150068 unter `points` und `mixed` mit demselben Gewicht nachspielen und die Matchstände erneut treffen. An jeder Entscheidung öffentlich festhalten, ob ein **alleiniger Halter** von einem bewiesenen Punktefeld abzieht, obwohl V14 dort geblieben wäre und kein anderer eigener Endbefehl das Feld übernimmt. Für die Diagnose im Folgezustand messen, ob das Feld tatsächlich leer wird, wie viele Züge es so bleibt und wie sich das Punktekonto im selben Match verändert. Die Folgebeobachtung ist ausschließlich ein Messwert.

Wenn diese Ereignisse bei Spieler 1 Punkte kosten, lohnt sich eine einzelne Gegenprobe. Nur in genau dieser Situation behält V14 den Befehl des Halters. Wenn V14 von dort schießen will, bleibt auch das Schussziel erhalten. Den Gewinn des gemischten Hybrids auf Spieler 0 als Schutzkontrolle mitprüfen. Die vorhandenen Tabellen beweisen weder diesen Mechanismus noch, dass der engere Schutz auf neuen Karten mehr Spiele gewinnen wird.

Alle Unterschiede verwenden beide Sitze derselben Karte zusammen. Die Mittelwertintervalle ziehen 10.000-mal komplette Karten mit Zurücklegen (PCG64, Seed 2711). Die zwei Entwicklungssätze dienten der Auswahl, die Bestätigungsanalyse dieser konkreten Mechanismusfrage entstand nach Betrachtung der Ergebnisse. Datenstand `d0c4576`. Reproduktion vom Repository-Stamm mit `python experiments/analysis/umbau_20261115/tools/solution_points.py experiments/analysis`. [Rohsummen, Gruppen, Intervalle und sieben Eingabeprüfsummen](confirm_solution_points.json) · [Regel für die beteiligten Rollen](../../../agents/sherlock/hybrid_agent.py) · [Definition der Einheitenzüge](../../../scripts/metrics.py)
