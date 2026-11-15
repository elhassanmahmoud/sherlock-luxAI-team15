# R3 und v4 verlieren auf unterschiedlichen Startpositionen

Auf Mahmouds Dev-A-Karten haben wir R3 direkt mit den drei veröffentlichten Solution-Tabellen verglichen. Für alle acht Kontrollpartien auf vier Karten reproduzierte unser Kurslauf jedes Match- und Punkteergebnis von V14. Der eigentliche Vergleich umfasst dieselben 100 Karten und beide Startseiten für alle vier Strategien.

| Agent gegen Solution | Gewonnene Spiele | Gewonnene Einzelmatches | R3 gewinnt zusätzlich / verliert zuvor gewonnen |
|---|---:|---:|---:|
| V14 | 188/200 | 522/600 | 10 / 3 |
| Mahmouds v3 points | 194/200 | 548/600 | 4 / 3 |
| Mahmouds v4 mixed | 194/200 | 557/600 | 6 / 5 |
| R3-Bewegungsberater | **195/200** | **570/600** | – |

Der gepaarte Unterschied R3 gegenüber V14 beträgt +3,5 Prozentpunkte, 95-%-Intervall +0,5 bis +7,5. Gegen v4 mixed sind es +0,5 Prozentpunkte mit Intervall −3 bis +4, gegen v3 points −2 bis +3 für denselben Punktschätzer. Für jedes Intervall wurden 10.000-mal 100 Karten mit beiden Sitzpositionen gezogen. Dieser Kartensatz diente der Entwicklung. Die Ergebnisse zur Kaggle-Spielstärke unterscheiden sich zwischen den Varianten und werden separat verglichen.

Auf **jeder** der 200 Startpositionen gewann mindestens einer von R3 und v4 mixed. R3 verlor 7150011 auf beiden Sitzen sowie 7150035/P0, 7150079/P1 und 7150096/P0. Mahmouds v4 gewann alle fünf, verlor aber sechs andere Spiele, die R3 gewann. 200/200 ist damit die rechnerische Obergrenze einer nachträglichen Auswahl anhand der bekannten Sieger. Für eine tatsächlich spielbare Kombination muss eine Entscheidung aus den öffentlich sichtbaren Beobachtungen getroffen und auf neuen Karten geprüft werden.

Der R3-Checkpoint und die Spielquelle entsprechen bytegenau dem unabhängigen Vergleich. Die drei externen Vergleichstabellen sind über ihre Dateiprüfsummen gebunden. Die Auswertung einschließlich aller umgedrehten Sitzschlüssel wurde zweimal aus den Spielzeilen berechnet. [Vollständiger Vergleich](assessment.json) · [200 R3-Partien](r3/games.jsonl) · [Acht reproduzierte V14-Partien](reproduction/games.jsonl) · [Plan und Tabellen](../DEV_A_PLAN.md).
