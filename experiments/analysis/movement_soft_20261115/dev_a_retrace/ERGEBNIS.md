# Wo R3 auf fünf bekannten Solution-Sitzen verliert

Alle fünf R3-Niederlagen auf Dev A endeten 1:2. Jede Partie wurde mit R3 und V14 samt beiden Punktesummen exakt reproduziert. Dazu kamen drei positive Kontrollen, in denen R3 eine Niederlage von V14 in einen Sieg umgewandelt hatte. Insgesamt liegen 16 vollständige Partien und 48 Matchverläufe vor.

| Neue Spielniederlage gegenüber V14 | Match, das von Sieg zu Niederlage kippt | Punkte R3 : Solution | Beobachtung |
|---|---:|---:|---|
| 7150011, Spieler 1 | 3 | 821 : 837 | R3 liegt ab Schritt 8 dauerhaft zurück. Fünf Abgänge eines alleinigen Halters lassen das Feld am nächsten Zugende leer. |
| 7150035, Spieler 0 | 2 | 335 : 449 | Dauerhafter Rückstand ab Schritt 31. In diesem Match gibt es keinen R3-Eingriff, der einen alleinigen Halter wegzieht. |
| 7150096, Spieler 0 | 2 | 474 : 515 | Dauerhafter Rückstand ab Schritt 61. Acht unmittelbare Lücken nach Haltereingriffen. |

Die beiden weiteren R3-Niederlagen (7150011/P0 und 7150079/P1) verlor auch V14. Auf 7150079/P1 und 7150096/P0 erzielt R3 über alle Matches zusammen mehr Punkte als Solution und verliert dennoch das Spiel. Für den Ausgang zählt die Mehrheit der Einzelmatches.

In den drei gegenüber V14 verlorenen Einzelmatches führten 18 beobachtete R3-Eingriffe an alleinigen Haltern zu 13 sofort leeren Feldern. In den **fünf gegenüber V14 zusätzlich gewonnenen Einzelmatches** der Kontrollgruppe waren es sogar 29 Lücken nach 52 solchen Eingriffen. Ein pauschaler Haltebefehl würde also auch Züge in erfolgreichen Verläufen verändern. Die Vergleichsagenten erlebten nach ihren ersten verschiedenen Befehlen unterschiedliche Spielverläufe. Ein einzelner Halterwechsel lässt sich daraus nicht als Ursache eines Siegs oder einer Niederlage ableiten.

7150035 eignet sich als Gegenprobe für einen neuen Ansatz. Auf Spieler 0 fällt R3 im zweiten Match von einem V14-Sieg auf eine Niederlage. Auf Spieler 1 gewinnt R3 das erste Match 221:119, das V14 111:234 verlor. Beide Sitze verwenden dieselben Spielparameter. Der direkt nutzbare nächste Vergleich ist, ob ein kampfstärkerer Schüler in öffentlich sichtbaren Gegnerkontakten hilft, während R3 die Bewegungen abseits des Kampfes wählt.

[Alle 48 Matchverläufe mit Punkteständen und Zeitabschnitten](run1/comparison.json) · [R3-Zugverläufe](run1/r3) · [V14-Zugverläufe](run1/v14) · [Fallauswahl](PLAN.md)
