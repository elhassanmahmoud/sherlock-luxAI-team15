# Die sechs offenen Solution-Partien des v3-Hybrids

Auf Dev A gewann der Hybrid v3 im Modus `points` 194 von 200 Spielen. Die Tabelle enthält seine sechs Niederlagen und die gewonnenen Matches der drei bereits ausgewerteten Strategien auf denselben Spielschlüsseln. Zwei Matchsiege entscheiden eine Partie.

| Karte | Hybridseite | V14 | Hybrid v2 combat | Hybrid v3 points | Punktedifferenz v3 über das ganze Spiel |
|---:|---:|---:|---:|---:|---:|
| 7150003 | 0 | 1 | 2 | 0 | −247 |
| 7150009 | 0 | 3 | 3 | 1 | +111 |
| 7150010 | 0 | 3 | 2 | 1 | +36 |
| 7150011 | 0 | 1 | 2 | 1 | −1 |
| 7150011 | 1 | 2 | 2 | 1 | +20 |
| 7150068 | 1 | 2 | 1 | 1 | −86 |

Der Kampfhybrid v2 gewann fünf dieser sechs Partien. V14 gewann die verbleibende Partie auf 7150068. Umgekehrt verlor v2 an anderen Stellen und kommt ebenfalls auf 194/200. Eine nachträgliche Wahl anhand der Endergebnisse könnte alle 200 Sitzpartien abdecken. Wenn auf jeder Karte die gleiche Strategie für beide Seiten gelten muss, liegt diese theoretische Obergrenze bei 199/200. Für die Wahl vor dem Spiel steht der Endstand natürlich nicht zur Verfügung.

Gegenüber V14 rettete v3 zehn Niederlagen und verlor vier frühere Siege. Bei gemeinsamer Stichprobenziehung beider Sitze pro Karte beträgt die Differenz der Spielsiegraten +3 Prozentpunkte mit 95-%-Intervall [−1, +7] (10.000 Ziehungen, Seed 2711). Die drei positiven Gesamtpunktdifferenzen in der Tabelle zeigen, warum wir die einzelnen Matchenden betrachten müssen.

Für eine Diagnose eignen sich besonders beide Seiten von 7150011 und die einzige auch von v2 verlorene Partie auf 7150068. Für den Vergleich der Architekturen fehlt noch eine Messung, in der derselbe v3-Schüler wahlweise mit der `combat`- oder der `points`-Auswahl spielt. Im bisherigen Vergleich wechseln Schülergewichte und Auswahlregel gemeinsam. Die veröffentlichten Rohdaten reichen für die Tabelle. Zur lokalen Ausführung auf einem zweiten Rechner wird der tatsächlich gemessene v3-Schülercheckpoint benötigt. Mahmouds laufendes weiteres Nachtraining ist ein separates Experiment.

[V14](../kaggle3_20261115/v14_ref_devA.csv) · [Hybrid v2 combat](../kaggle3_20261115/student_hyb_v2_combat.csv) · [Hybrid v3 points](../kaggle3_20261115/student_hyb_v3_points.csv) · [Trainingsstand](README.md)
