# Derselbe v4-Schüler mit zwei Aufgabenteilungen

Auf Dev A spielten Mahmouds v4-Schüler und V14 im points- und im mixed-Hybrid zusammen. Bei points behält V14 Schiffe mit bestätigtem Punkteauftrag. Bei mixed übernimmt der Schüler solche Schiffe zusätzlich, wenn Gegner in seiner Nähe sichtbar sind. Dadurch lässt sich der Wechsel der Aufgabenteilung bei derselben Schülerversion untersuchen.

| 100 Karten, je beide Seiten | v4 points | v4 mixed | Durch mixed gewonnene / verlorene Spiele |
|---|---:|---:|---:|
| Solution | 194/200 | 194/200 | 5 / 5 |
| Kaggle-Drittplatzierter | 8/200 | 10/200 | 6 / 4 |

Der Wechsel verbessert auf diesem Satz die Kaggle-Siegquote um einen Prozentpunkt. Das gepaarte 95-%-Intervall über ganze Karten reicht von −3 bis +6 Prozentpunkten. Gegen Solution beträgt der Unterschied null (rund −2,5 bis +3 Prozentpunkte). Über beide Gegner liegt er bei +0,5 Prozentpunkten mit einem Intervall von −2 bis +3. Für die Intervalle wurden 10.000-mal alle hundert Karten mit Zurücklegen gezogen. Beide Sitze und beim Gesamtwert beide Gegner blieben zusammen.

Auf diesen sechs Schlüsselpositionen verlor der gemischte v4-Hybrid gegen Solution. Die Zahlen geben gewonnene Einzelmatches von drei an.

| Karte | Sitz | V14 | v4 points | v4 mixed |
|---|---:|---:|---:|---:|
| 7150003 | 1 | 1 | 2 | 1 |
| 7150026 | 0 | 2 | 3 | 1 |
| 7150039 | 0 | 3 | 2 | 1 |
| 7150068 | 1 | 2 | 2 | 0 |
| 7150074 | 0 | 2 | 1 | 1 |
| 7150083 | 1 | 2 | 3 | 1 |

Bei fünf der sechs Niederlagen gewann v4 points. Umgekehrt verlor v4 points an fünf anderen Stellen, an denen mixed gewann. Für Mahmoud ist deshalb der Moment aufschlussreich, an dem ein Schiff mit Punkteauftrag erstmals wegen eines sichtbaren Gegners an den Schüler übergeht. Ein Nachspielen auf dem eigenen v4-Checkpoint kann zeigen, ob die neue Aktion ein Feld preisgibt oder ein Schiff im Kampf rettet. Die Endstandtabellen allein enthalten diese einzelnen Befehle nicht.

Die 184/200 direkten Siege gegen V14 gehören zum reinen v4-Schüler. Für den points-Hybrid liegen 166/200 direkte Siege vor. Die veröffentlichten direkten Zahlen beziehen sich auf andere Strategien als den mixed-Hybrid. [Reiner v4 direkt](../kaggle3_20261115/duel_v4_b15u.csv) · [v4 points direkt](../kaggle3_20261115/duel_hyb_v4_points.csv) · [points-Rohdaten](../kaggle3_20261115/student_hyb_v4_points.csv) · [mixed-Rohdaten](../kaggle3_20261115/student_hyb_v4_mixed.csv) · [Zuweisung im Agenten](../../../agents/sherlock/hybrid_agent.py).
