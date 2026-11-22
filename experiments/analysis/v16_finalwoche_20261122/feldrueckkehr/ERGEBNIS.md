# Feldrückkehr im ganzen Spiel

**V16 bleibt die Abgabe.** Der Rückkehrbefehl verbesserte in vier Diagnosekarten die nächsten acht Züge. Auf 20 weiteren Karten brachte er gegen Kaggle keinen zusätzlichen Match- oder Spielgewinn. Im direkten Vergleich gewann der Kandidat 18 von 40 Spielen. Damit endet der Versuch nach dem vorab festgelegten Auswahltest. Eine große Bestätigung war an mindestens zwei zusätzliche Kaggle-Matchsiege und mindestens 21 direkte Siege gebunden. [Versuchsplan](PLAN.md) · [Vergleich derselben Ausgangslage mit und ohne Eingriff](DIAGNOSE.md).

Beide Varianten spielten als P0 und P1 gegen dieselben externen Gegner auf den Karten 160347100–160347119. Dazu kamen die direkten Duelle mit getauschten Sitzen. Die 200 Partien erreichten jeweils alle 303 Schritte und drei Matchentscheidungen.

| Gegner | V16, ganze Siege | Kandidat, ganze Siege | Matchsiege V16 / Kandidat | Spiele mit Eingriff | Geänderte Aktionen |
|---|---:|---:|---:|---:|---:|
| Solution_92 | 38/40 | 38/40 | 116 / 116 von je 120 | 14 von 40 | 17 |
| Kaggle-Dritter | 0/40 | 0/40 | 4 / 4 von je 120 | 8 von 40 | 12 |
| V16 im direkten Duell | 22/40 | 18/40 | 65 / 55 von 120 | 13 von 40 | 20 |

Gegen Solution und Kaggle blieb auf jeder einzelnen Karte und jedem Sitz sogar die Anzahl gewonnener Matches gleich. In den 58 externen Vergleichspaaren ohne geänderten Befehl stimmten zusätzlich beide Punktesummen exakt überein. Gegen V16 gewann der Kandidat sieben seiner 20 Spiele als P0 und elf als P1. Auf 18 Karten gewann jeder Agent je einen Sitz, auf zwei Karten gewann V16 beide Sitze.

**Warum mehr eigene Punkte in einigen Situationen nicht genügten.** Gegen Kaggle wurde auf vier der 20 Karten eingegriffen. Auf beiden Sitzen war jeweils dieselbe Veränderung des Punkteabstands zu beobachten.

| Karte | Geänderte Befehle je Partie | Änderung eigener Punkte | Änderung gegnerischer Punkte | Änderung des Punkteabstands |
|---|---:|---:|---:|---:|
| 160347108 | 1 | +76 | +31 | +45 |
| 160347112 | 2 | −107 | +17 | −124 |
| 160347115 | 2 | +3 | −6 | +9 |
| 160347118 | 1 | +7 | 0 | +7 |

Auf drei Karten nahm der Punkteabstand zu. Auf Karte 160347112 sank er stärker, als die anderen drei Zugewinne zusammen ausgleichen konnten. Die beiden veränderten Befehle dieser Karte und ihre Folgewirkungen sind hier gemeinsam gemessen. Der einzelne verantwortliche Zug lässt sich aus diesen Endständen allein nicht bestimmen.

Im Mittel aller 20 Karten veränderte sich der Punkteanteil des Kandidaten gegen Kaggle um **−0,192 Prozentpunkte** mit einem 95-%-Kartenbootstrapintervall von **−0,868 bis +0,255**. Gegen Solution lag die Änderung bei **+0,058 Prozentpunkten** mit Intervall **−0,002 bis +0,158**. Dafür wurde je Spiel der Anteil eigener Punkte an beiden Punktesummen berechnet und pro Karte der Mittelwert der beiden Sitzdifferenzen gebildet. Die Intervalle sind bei diesem kleinen Kartenpanel beschreibend. [200 vollständige Spieldatensätze](auswahl_partien.jsonl.gz) · [Auswertung und Prüfgrenzen](auswahl_ergebnis.json) · [Nachrechnung](REPRODUKTION.md).
