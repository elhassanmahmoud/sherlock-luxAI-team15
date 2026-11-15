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

Die 184/200 direkten Siege gegen V14 gehören zum reinen v4-Schüler. Für den points-Hybrid liegen 166/200 direkte Siege vor. Die direkten Messungen für den gemischten Hybrid folgten später und stehen im nächsten Abschnitt. [Reiner v4 direkt](../kaggle3_20261115/duel_v4_b15u.csv) · [v4 points direkt](../kaggle3_20261115/duel_hyb_v4_points.csv) · [points-Rohdaten](../kaggle3_20261115/student_hyb_v4_points.csv) · [mixed-Rohdaten](../kaggle3_20261115/student_hyb_v4_mixed.csv) · [Zuweisung im Agenten](../../../agents/sherlock/hybrid_agent.py).

## Zweiter Kartensatz und direktes Duell

Der inzwischen veröffentlichte gemischte Hybrid gewinnt auf Dev A direkt gegen V14 180 von 200 Spielen (504/600 Einzelmatches). Auf den 100 weiteren Dev-B-Karten, je beide Sitze, sehen die vollständigen Ergebnisse so aus.

| Gegner | V14 | v4 allein | v4 gemischt |
|---|---:|---:|---:|
| Solution | 185/200 | 185/200 | **190/200** |
| Kaggle-Drittplatzierter | 0/200 | 4/200 | **4/200** |
| Direkt gegen V14 | – | 172/200 | **178/200** |

Gegen Solution gewinnt der gemischte Hybrid elf zuvor verlorene Sitze und verliert sechs frühere Siege. Der Unterschied beträgt +2,5 Prozentpunkte mit einem gepaarten 95-%-Intervall von −2 bis +7,5. Gegen Kaggle gewinnt er vier Spiele hinzu, Intervall 0 bis +5 Prozentpunkte. Die Intervalle verwenden je 10.000 Ziehungen ganzer Karten mit beiden Sitzen, Startwert 2711. Bei allen vier Quelldateien wurden Karten, Seiten, Matchzahlen, Endschritte und Siegerkennzeichen geprüft. Die Auswahl für die endgültige Bestätigung fiel auf den gemischten v4-Hybrid. Dazu ist die gepackte Datei mit SHA-256 `28933a3b7810037b0af37b9ccfbf261c7c9b2b1353c8e0e8ef3b25e2c77cae45` festgelegt. Die 400 Karten der Bestätigung waren an dieser Auswahl unbeteiligt. [Registrierung](../../../docs/superpowers/plans/2026-11-15-umbau-imitation.md) · [Dev B, gemischt](../kaggle3_20261115/devB_hyb_v4_mixed.csv) · [Dev B, Schüler](../kaggle3_20261115/devB_student_v4.csv) · [Dev B, V14](../kaggle3_20261115/devB_v14.csv) · [Dev A, Direktduell](../kaggle3_20261115/duel_hyb_v4_mixed.csv).
