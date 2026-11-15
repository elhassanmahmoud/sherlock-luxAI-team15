# Der Midpoint gewinnt alle 32 Solution-Spiele der Vorauswahl

Der Midpoint mit **einer Kartenansicht** gewann auf 16 Entwicklungskarten (7170230–7170245, beide Sitze) 32 von 32 Spielen gegen Solution und 24 von 32 direkt gegen V14. Gegen Kaggle gewann keiner der drei Agenten ein Spiel. Für diesen Midpoint wurden die Gewichte der beiden R8-Nachtrainingsläufe einmal gleichgewichtet gemittelt. Im Spiel bewertet ein einzelnes Beratungsnetz jede Stellung einmal. Die spätere [Prüfung mit zwei Ansichten](../r8_midpoint_diagonal_20261115/PLAN.md) hat eine eigene Auswertung.

| Siege in ganzen Spielen | V14 | R3 mit einer Ansicht | Midpoint mit einer Ansicht |
|---|---:|---:|---:|
| Gegen Solution | 29/32 | 31/32 | **32/32** |
| Gegen Kaggle | 0/32 | 0/32 | 0/32 |
| Beide externen Gegner zusammen | 29/64 | 31/64 | **32/64** |

Die drei zusätzlichen Solution-Siege gegenüber V14 entfallen auf **zwei Karten**. Auf Karte 7170238 gewann der Midpoint in beiden Sitzen zusätzlich, auf 7170239 als Spieler 1. Gegenüber R3 kam auf 7170236 als Spieler 0 ein Sieg hinzu. In beiden Vergleichen ging auf diesem Kartensatz kein zuvor gewonnenes Spiel verloren. Gegen Kaggle verlor der Midpoint sämtliche 96 einzelnen Matches, während V14 und R3 je zwei Matches gewannen.

| Gepaarte Auswertung | Beobachtung | 95-%-Intervall |
|---|---:|---:|
| Externe Siegquotendifferenz gegenüber V14 | +4,69 Prozentpunkte | 0 bis +12,50 Prozentpunkte |
| Externe Siegquotendifferenz gegenüber R3 | +1,56 Prozentpunkte | 0 bis +4,69 Prozentpunkte |
| Direkte Siegquote gegen V14 | 75,0 % (24/32) | 50,0 bis 93,75 % |

Das Bootstrap-Verfahren zieht 10.000-mal ganze Karten mit Zurücklegen (PCG64, Seed 2711). Beide Sitze bleiben zusammen und bei der externen Gesamtauswertung auch beide Gegner. Alle fünf Kriterien der [vorab festgelegten Vorauswahl](PLAN.md) sind erfüllt. Damit qualifiziert sich der Kandidat für die unabhängige Bestätigung auf neuen Karten. Auf diesen 16 Karten schließen die externen Intervalle einen Unterschied von null ein. Die 32 Solution-Siege belegen noch keine allgemeine 100-%-Siegquote.

**Prüfnachweis.** Alle 224 Rohzeilen wurden anhand von Arm, Gegner, Karte und Sitz eindeutig zugeordnet. Jede enthält 303 Schritte, drei abgeschlossene Matches und einen dazu passenden Spielausgang. Manifest- und Datenprüfsummen, vier Abschlusssummen, die Bewegungseingriffe, alle gepaarten Differenzen, Intervalle und Auswahlbedingungen wurden anhand der Rohdaten nachgerechnet. Das [Laufprotokoll](games/protocol.json) bindet Softwarestand und Modell. Die [Auswertung](games/screen/assessment.json) verweist über Prüfsummen auf die Rohdaten der Arme [Midpoint extern](games/screen/midpoint/games.jsonl), [V14 extern](games/screen/v14/games.jsonl), [R3 extern](games/screen/r3/games.jsonl) und [Midpoint direkt gegen V14](games/screen/direct/games.jsonl).
