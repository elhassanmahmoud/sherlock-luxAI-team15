# Ein zusätzlicher Sieg gegen Solution auf 120 neuen Karten

**V16 bleibt der Abgabeagent.** Mitte2 gewann gegen Solution_92 238 von 240 Spielen, V16 gewann 237. Der Unterschied von **+0,42 Prozentpunkten** hat ein gepaartes 95-%-Kartenintervall von **0,00 bis +1,25 Prozentpunkten**. Für eine Freigabe war eine strikt positive Untergrenze gefordert. Im direkten Duell gewann Mitte2 **38/80** statt der geforderten mindestens 40. Gegen den Kaggle-Dritten erreichten beide acht Siege. Damit ist eine von drei Freigabebedingungen erfüllt. Diese Linie ist ohne Paketänderung oder weiteren Wiederholungsblock abgeschlossen. [Vorab festgelegter Plan](PLAN.md) · [Vollständige Auswertung](ergebnis.json).

Auf allen 120 ungefilterten Karten 160384000–160384119 spielten beide Agenten von beiden Startseiten gegen beide externen Gegner. Auf den ersten 40 Karten kamen direkte Duelle mit Sitzwechsel hinzu. Alle 1.040 Partien wurden tatsächlich bis zur dritten Matchentscheidung gespielt.

| Gegner | Ganze Siege V16 | Ganze Siege Mitte2 | Matchsiege V16 / Mitte2 | Spiele mit geändertem Befehl |
|---|---:|---:|---:|---:|
| Solution_92 | 237/240 (98,75 %) | 238/240 (99,17 %) | 692 / 697 von je 720 | 174 auf 98 Karten |
| Kaggle-Dritter | 8/240 | 8/240 | 100 / 100 von je 720 | 36 auf 18 Karten |
| V16 direkt | 42/80 | 38/80 | 125 / 115 von 240 | 23 auf 23 Karten |

**Die eine gerettete Partie.** Auf Karte 160384039, P0, änderte der Berater in Zug 49 des zweiten Matches einen Bewegungsbefehl. Nur dieser von V16 verlorene Solution-Sitz wurde zu einem ganzen Sieg. Keiner der 237 bisherigen Gewinne ging verloren. Die übrigen beiden Niederlagen betrafen P1: auf 160384017 griff die Regel nie ein, auf 160384119 griff sie in Zug 37 ein. Beide Partien endeten weiterhin 1:2. Ein einzelner Unterschied auf 120 unabhängigen Karten ist mit der verlangten Sicherheit vereinbar mit einer Siegquotenänderung von null.

Gegen Kaggle wechselten zwei Karten ihren Ausgang in entgegengesetzte Richtungen. Auf 160384093 kostete die Änderung in Zug 41 auf beiden Sitzen einen Sieg. Auf 160384096 gewann sie mit dem Eingriff in Zug 26 beide Sitze hinzu. Das 95-%-Kartenintervall der Differenz der Spielsiegquoten reicht von −2,50 bis +2,50 Prozentpunkten. Der Punkteanteil stieg zwar um 0,18 Prozentpunkte (Intervall +0,02 bis +0,37), die Siegsumme blieb gleich. Im direkten Vergleich mit V16 gewann Mitte2 20/40 als P0 und 18/40 als P1. Auf 32 Karten gewann jeder Agent einen Sitz, auf drei gewann Mitte2 beide, auf fünf V16.

**Einordnung des früheren Ergebnisses.** In der [archivierten Wirkungsprüfung](../mitte2/ERGEBNIS.md) rettete derselbe einzelne Eingriff sieben gezielt ausgewählte frühere Niederlagen. Die dort geforderte mittlere Verbesserung nach 15 Zügen verfehlte er. Der neue, vorher gebundene Versuch maß stattdessen direkt komplette Spiele auf ungefilterten neuen Karten. Weder die alten sieben Siege noch die alten 54 Sitze wurden hier mitgezählt. Die 240 neuen Solution-Spiele sind ein eigenes Panel und sollten entsprechend neben anderen, historisch getrennten Benchmarks berichtet werden.

**Nachrechnung.** Die 1.040 eindeutigen Aufträge wurden gegen die feste Liste aus Karte, Sitz, Gegner und Agent abgeglichen. Jede Partie hatte 303 Schritte und drei Matchsiege in Summe. In allen 270 externen Vergleichspaaren ohne geänderten Befehl waren beide Punktesummen sowie Match- und Spielausgänge identisch. Eine zweite Rechnung aus den komprimierten Einzeldaten bestätigte alle veränderten Siege, beide Kartenintervalle und die Verteilung der direkten Kartensiege. Die Datei ist 27.399 Bytes groß, SHA-256 `885cd55dac1cd7d586301e6d0046f15272f0cbd8a8770d1110421c581edeb520`. [1.040 vollständige Spieldatensätze](partien.jsonl.gz) · [Quellen und Paketbindung](herkunft.json).

Aus dem Repository-Stamm lässt sich der Endstand mit der eingerichteten Kursumgebung ohne erneute Spiele auswerten:

```sh
d=experiments/analysis/v16_finalwoche_20261122/mitte2_spielquote
python "$d/auswerten.py" "$d/partien.jsonl.gz"
```
