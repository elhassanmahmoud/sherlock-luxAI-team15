# Mahmouds gemischter Hybrid auf 400 Bestätigungskarten

Mahmoud hat den vorher festgelegten V15-Kandidaten (v4 mixed) auf den Karten 7158000–7158399 von beiden Startpositionen geprüft. Die 5.600 Spielausgänge aus seinem Commit `d0c4576` wurden unabhängig aus den Rohdateien nachgezählt. Für jeden Gegner und Sitz ist jede Karte genau einmal vertreten. Alle Spiele haben 303 Schritte und drei abgeschlossene Matches.

| Gegner | V15 | V14 | Was sich ändert |
|---|---:|---:|---|
| Solution_92 | 764/800 | 767/800 | 30 bisherige Niederlagen gewonnen, 33 bisherige Siege verloren |
| Kaggle-Dritter | 12/800 | 12/800 | acht Siege hinzugewonnen, acht verloren |
| Default | 800/800 | 800/800 | beide gewinnen auf beiden Sitzen alle Spiele |
| Direkt gegen V14 | 730/800 | 70/800 | V15 gewinnt auf jeder Startposition 365 von 400 |

Im direkten Duell liegt V15 bei 91,25 % mit einem 95-%-Kartenintervall von 88,49 bis 94,00 %. Gegen Solution steigt die Zahl seiner gewonnenen Einzelmatches auf 2.204 von 2.400 (V14 2.144). Für einen Spielsieg müssen zwei der drei Matches **im selben Spiel** gewonnen werden. Über alle Spiele resultieren drei Siege weniger. Beim Kaggle-Gegner beträgt das Intervall für den Unterschied der Spielsiege −1,50 bis +1,50 Prozentpunkte. Die vorab festgelegte Bedingung für einen Kaggle-Vorteil ist verfehlt.

Die beiden CSV-Dateien belegen die Leistung des von Mahmoud eingesetzten Kandidaten. Dieser Commit veröffentlicht die Messergebnisse. Für eine lokale Weiterverwendung des identischen Hybrids fehlt hier das gepackte Gewicht mit der Prüfsumme `28933a3b…`. Im anschließend veröffentlichten Kursprotokoll bestehen acht Spiele auf beiden Seiten. Mahmoud berichtet zusätzlich eine bestandene ZIP-Prüfung und null Aktionsabweichungen beim isolierten Nachspielen. Die technische Prüfung ist damit auf seinem Rechner dokumentiert. Als offizieller Stand gilt weiterhin V14. [Kursprotokoll](runner_v15.json) · [Entscheidungsvorlage](../V15_ENTSCHEIDUNG.md).

[Auswertung mit Kartenziehungen](gepaarte_pruefung.json) · [V15-Rohdatei](v15_candidate.csv) · [V14-Rohdatei](v14_ref.csv) · [Auswertungsprogramm](../tools/gates.py)
