# Wo verliert R3 gegen Kaggle? Energie- und Todesanalyse (17.11.2026)

**Kurz:** R3 verliert gegen den Kaggle-Dritten über die Energie. Je Match sterben etwa **24 R3-Units, aber nur 3
Kaggle-Units**. Unsere Units haben vor dem Tod im Median nur rund 20 Energie. Halter auf Punktefeldern werden aus
der Ferne abgeschossen, schwache Units sterben am Energie-Sog neben Kaggle-Units mit rund 240 Energie oder beim
Zusammenstoß mit ihnen. Kaggle tankt pro Unit und Schritt etwa 50 % mehr Energie aus den Feldern, schießt mehr als
doppelt so oft und trifft mit dem Streuschaden meist mehrere Units auf einmal.

## Was gemessen wurde

Das unveränderte R3-Paket (SHA-256 `8aabdc73…a64d`) spielte auf 30 frischen Karten 7256000–7256029, beide Seiten,
gegen den Kaggle-Dritten (60 Spiele, 180 Matches je Team). Das [Skript](diagnose.py) rechnet jeden Schritt mit den
Regeln der Engine nach: erst Bewegung, dann Saps auf die neuen Positionen, dann Zusammenstöße und Energie-Sog, zuletzt
das Energiefeld. Die Zusammenstöße stimmten in allen Schritten mit dem echten Folgezustand überein (0 Abweichungen).
Rohdaten: [Matches](diag_30/matches.csv), [Tode](diag_30/deaths.csv).

## Ergebnisse (Mittel je Match und Team)

| | R3 Match 1 | R3 Match 2 | R3 Match 3 | Kaggle Match 1 | Kaggle Match 2 | Kaggle Match 3 |
|---|---:|---:|---:|---:|---:|---:|
| Punkte | 107 | 206 | 272 | 233 | 416 | 483 |
| Matches gewonnen (Anteil) | 0,1 | 0,0 | 0,0 | 0,9 | 1,0 | 1,0 |
| tote Units: Schuss / Sog / Zusammenstoß | 9,2 / 9,3 / 5,9 | 12,6 / 8,3 / 4,6 | 11,4 / 7,4 / 4,1 | 1,9 / 0,6 / 0,5 | 1,8 / 0,7 / 0,1 | 2,4 / 0,2 / 0,2 |
| Energie aus Feldern (netto) | 3.030 | 2.609 | 2.495 | 5.664 | 5.157 | 4.903 |
| Energieverlust durch gegnerische Schüsse (direkt + Streu) | 1.829 | 2.186 | 1.919 | 673 | 511 | 694 |
| Energieverlust durch Sog | 1.491 | 1.138 | 897 | 588 | 422 | 307 |
| Energie für Bewegung | 2.070 | 1.848 | 1.691 | 1.790 | 1.568 | 1.495 |
| eigene Schüsse | 17,0 | 16,2 | 21,9 | 38,8 | 41,9 | 36,3 |
| davon Treffer direkt / Streu (Units) | 7,4 / 17,5 | 6,0 / 14,0 | 6,8 / 21,4 | 25,1 / 46,1 | 26,8 / 62,0 | 24,3 / 54,8 |
| Unit-Schritte (lebend) / davon auf Punktefeldern | 966 / 154 | 937 / 265 | 947 / 334 | 1.233 / 267 | 1.229 / 444 | 1.230 / 504 |
| Energie aller Units am Matchende | 575 | 519 | 748 | 3.156 | 3.026 | 3.020 |

**Die Tode der R3-Units** (Mediane):

| Ursache | eigene Energie davor | stärkster Gegner in 2 Feldern | auf Punktefeld |
|---|---:|---:|---|
| Schuss | 22 | kein Gegner in der Nähe | ja (Schuss aus der Ferne) |
| Sog | 19 | 241 Energie | nein |
| Zusammenstoß | 35 | 227 Energie | nein |

## Was daraus folgt

1. **Energie entscheidet.** Wer mehr Energie hat, gewinnt Zusammenstöße und saugt Nachbarn aus. Der Sog ist der
   Sog-Faktor (0,0625 bis 0,375) mal der Energie der gegnerischen Nachbarn: Ein Kaggle-Halter mit 240 Energie
   nimmt einer Unit daneben je Schritt 15 bis 90 Energie.
2. **Schwache Units sterben.** Fast alle Tode treffen Units mit weniger Energie als ein Schuss kostet (30–50).
3. **Kaggle nutzt den Streuschaden.** Je Schuss trifft Kaggle im Mittel 0,65 Units direkt und 1,4 Units mit der
   Streuung. Unsere Halter stehen dicht nebeneinander auf den Punktefeldern.
4. **Kaggle tankt mehr:** 4,6 Energie je Unit und Schritt aus den Feldern, R3 3,1.

Diese Befunde sind die Grundlage für die Taktikschicht in `agents/sherlock_r3t/` (Granaten, Schutz vor Sog und
Zusammenstoß, Tanken). Deren Test steht in [../r3t_20261117/](../r3t_20261117/).
