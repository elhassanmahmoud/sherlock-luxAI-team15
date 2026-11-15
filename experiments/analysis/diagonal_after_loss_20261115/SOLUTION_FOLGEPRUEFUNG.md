# Auf 16 weiteren Karten gewinnt der Diagonalagent gegen Solution jedes erste Match

Alle drei Spielweisen gewannen gegen **Solution 32 von 32 Partien**. Der Kandidat sollte nach einem verlorenen ersten Match für den Rest der Partie zu V14 wechseln. Auf den 16 vorab festgelegten Karten 7170960–7170975 gewann er auf beiden Startseiten jedes Auftaktmatch. Die Rückschaltung wurde **keinmal** ausgelöst. Damit verfehlt er das für diesen getrennten Versuch geforderte Siegplus gegenüber dem Diagonalagenten. [Versuchsplan](PLAN.md) · [Auswertung](run/solution/assessment.json)

| Spielweise | Spielsiege Spieler 0 | Spielsiege Spieler 1 | Gewonnene Matches M1 / M2 / M3 (je 32) | Matchsiege gesamt |
|---|---:|---:|---:|---:|
| Diagonal mit Rückschaltung | 16/16 | 16/16 | 32 / 31 / 31 | 94/96 |
| Diagonal durchgehend | 16/16 | 16/16 | 32 / 31 / 31 | 94/96 |
| V14 durchgehend | 16/16 | 16/16 | 31 / 29 / 29 | 89/96 |

In allen 32 Paaren von Kandidat und Diagonalagent stimmten die aufgezeichneten Hashes der Befehle beider Spieler für alle 303 Züge überein. Die beiden verlorenen Einzelmatches waren M2 auf 7170965 als Spieler 1 und M3 auf 7170969 als Spieler 0. Beide Partien endeten 2:1. Die fünf zusätzlichen Matchsiege gegenüber V14 kamen damit vollständig aus der durchgehend gespielten Diagonalpolitik. Im Vergleich beider beratenen Varianten wechselte auf keiner Karte der Spielsieger. Diese Stichprobe liefert keine neue Beobachtung des Verhaltens nach einer Rückschaltung. [Kandidat](run/solution/after_loss/games.jsonl) · [Diagonalagent](run/solution/diagonal/games.jsonl) · [V14](run/solution/v14/games.jsonl)

Für alle 96 Partien wurden die registrierten Karten, Sitze und Gegner, 303 Schritte, die offiziellen Matchsieger und ihre Punktestände sowie die Summen beider Spieler aus den Einzelzeilen geprüft. Die Rohdaten und Manifeste stimmen mit den gespeicherten Prüfsummen überein. Die frühere Rettung auf 7286137/P0 bleibt ein Ergebnis der gezielten Diagnose. Im ersten frischen Vergleich und in dieser Folgeprüfung kam es gegen Solution zusammen auf 32 verschiedenen Karten und 64 Sitzen zu keiner Rückschaltung. [Gezielte Diagnose](BEKANNTE_KARTEN.md) · [Erster frischer Vergleich](FRISCHE_KARTEN.md)
