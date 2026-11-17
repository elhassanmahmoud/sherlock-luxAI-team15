# Test der Taktikschicht über R3 (17.11.2026)

**Kurz:** Die von Mahmoud gewünschten Taktiken (Granaten, gezieltes Schießen, Nebel-Schüsse, Erobern, Ausweichen, Sparen,
Halterwechsel, Tanken) sind als Schicht über R3 eingebaut und einzeln getestet. **Einzeln bringen sie wenig**: gegen
Kaggle +0,0 bis +0,8 Prozentpunkte Punkteanteil, keine Variante erfüllt die Regel. **Der Durchbruch kommt vom
Imitations-Schüler auf R3** (Units im Kampf und ohne Punktefeld-Aufgabe spielen den Schüler, der von Kaggle gelernt
hat): Auf Dev D +3,71 [+2,09; +5,39] Prozentpunkte Punkteanteil gegen Kaggle und 199/200 gegen Solution (R3 193/200),
auf 200 frischen Karten der zweiten Prüfung +3,98 [+3,04; +4,96] bei gleicher Solution-Bilanz (391/400). Ganze Spiele
gegen Kaggle gewinnt er weiter selten (6/400 statt 4/400). Er ist der Kandidat für die frische Bestätigung auf
7159000–7159399 ([Plan](BESTAETIGUNG_PLAN.md)). Bis zu ihrem Ergebnis und der Entscheidung von Mahmoud und Moayed
bleibt R3 die Abgabe.

## Was gelaufen ist

Karten Dev D 7256100–7256199, beide Seiten, gegen Solution und Kaggle, je Variante 400 Spiele. Jede Variante wurde
vor ihrem ersten Spiel im [Plan](PLAN.md) angemeldet, mit derselben Leseregel. Jeder Durchgang lief aus einer
eingefrorenen Kopie des jeweiligen Plan-Commits, 10 Prozesse, streng nacheinander (Durchgang 1 `013c9ba`
[Skript](run_screen.sh), Durchgang 2 `4f8fd36` [Skript](run_screen2.sh), Durchgang 3 `3a34f5a`
[Skript](run_screen3.sh)). Ohne Schalter spielt die Schicht exakt wie R3 (12 Spiele, alle Spalten gleich). Ein
daraus gebautes Kurspaket spielt exakt wie die entsprechende Variante (4 Spiele, `scripts/build_r3t_package.py`).

**Leseregel:** vielversprechend, wenn gegen Solution und Kaggle zusammen mindestens +2 Prozentpunkte gewonnene
Spiele über R3 **oder** mindestens +3 Prozentpunkte Punkteanteil gegen Kaggle, und gegen Solution nicht mehr als
1 Prozentpunkt unter R3 (gepaart nach Karte, 10.000 Ziehungen, Seed 2711, [Auswertung](analyze.py)).

## Ergebnisse (gewonnene Spiele von 200)

| Variante | Solution | Kaggle | Matches gegen Kaggle (von 600) | Punkteanteil gegen Kaggle |
|---|---:|---:|---:|---:|
| R3 (Abgabe) | 193 | 4 | 20 | 33,4 % |
| GRANATE | 196 | 2 | 18 | 33,9 % |
| SOG | 193 | 1 | 21 | 33,4 % |
| TANKEN | 193 | 6 | 24 | 33,1 % |
| ALLE (Granate, Sog, Tanken) | 196 | 6 | 29 | 34,2 % |
| NEBEL (Granate + Nebel) | 196 | 2 | 19 | 33,9 % |
| EROBERN | 193 | 4 | 20 | 33,4 % |
| SPAREN | 194 | 6 | 26 | 33,4 % |
| WECHSEL | 194 | 4 | 20 | 33,7 % |
| **SCHUELER** (R3 + Schüler) | **199** | 2 | 30 | **37,7 %** |
| SCHUELER_ALLE (+ Granate, Sog, Tanken) | 197 | 3 | 28 | 37,7 % |
| HYB_ENS8 (V14 + Schüler, Vergleich) | 198 | 0 | 24 | 37,1 % |

**Gepaart gegen R3** (Prozentpunkte, 95-%-Kartenintervall):

| Variante | Spiele Solution + Kaggle | Spiele Solution | Spiele Kaggle | Punkteanteil Kaggle | vielversprechend |
|---|---:|---:|---:|---:|---|
| GRANATE | +0,25 [−1,5; +2,0] | +1,5 [−1,0; +4,5] | −1,0 [−3,0; 0,0] | +0,45 [−0,09; +1,00] | nein |
| SOG | −0,75 [−2,25; +0,5] | 0,0 [−1,5; +1,5] | −1,5 [−4,0; 0,0] | +0,15 [−0,35; +0,65] | nein |
| TANKEN | +0,5 [−0,5; +2,0] | 0,0 [−1,5; +1,5] | +1,0 [0,0; +3,0] | −0,04 [−0,34; +0,27] | nein |
| ALLE | +1,25 [−0,75; +3,25] | +1,5 [−2,0; +5,0] | +1,0 [0,0; +3,0] | +0,82 [+0,13; +1,55] | nein |
| NEBEL | +0,25 [−1,75; +2,25] | +1,5 [−0,5; +4,0] | −1,0 [−4,0; +2,0] | +0,58 [−0,03; +1,18] | nein |
| EROBERN | 0,0 [0,0; 0,0] | 0,0 [0,0; 0,0] | 0,0 [0,0; 0,0] | +0,05 [−0,01; +0,15] | nein |
| SPAREN | +0,75 [−0,5; +2,25] | +0,5 [−1,5; +3,0] | +1,0 [0,0; +3,0] | +0,36 [−0,14; +0,87] | nein |
| WECHSEL | +0,25 [0,0; +0,75] | +0,5 [0,0; +1,5] | 0,0 [0,0; 0,0] | +0,40 [+0,04; +0,77] | nein |
| **SCHUELER** | +1,0 [−1,5; +3,5] | +3,0 [0,0; +6,5] | −1,0 [−5,0; +2,0] | **+3,71 [+2,09; +5,39]** | **ja** |
| SCHUELER_ALLE | +0,75 [−2,0; +3,25] | +2,0 [−1,0; +5,5] | −0,5 [−4,0; +3,0] | +3,50 [+2,20; +4,81] | ja |
| HYB_ENS8 | +0,25 [−2,0; +2,75] | +2,5 [−1,0; +6,5] | −2,0 [−5,0; 0,0] | +3,03 [+1,60; +4,40] | ja |

## Was die Taktiken im Spiel bewirken (Analysekarten 7256000–7256029 gegen Kaggle, Mittel je Match)

| Variante | Eingriffe je Spiel | eigene Punkte | Kaggle-Punkte | eigene Tode (davon Schuss / Sog / Zusammenstoß) | Kaggle-Tode | eigene Schüsse |
|---|---|---:|---:|---:|---:|---:|
| R3 | – | 195 | 377 | 24,2 (11,0 / 8,3 / 4,9) | 2,8 | 18,4 |
| GRANATE | 7 neu gezielt, 11 zusätzlich | 200 | 375 | 24,0 (11,3 / 8,0 / 4,7) | 3,8 | 22,6 |
| SOG | 28 Ausweichzüge | 196 | 381 | 23,1 (11,2 / 7,1 / 4,8) | 2,8 | 17,8 |
| TANKEN | 3 | 194 | 377 | 24,3 (11,4 / 8,2 / 4,7) | 2,8 | 18,2 |
| ALLE | 6 + 9 Granaten, 29 Ausweichzüge, 3 Tanken | 194 | 371 | 23,5 (11,2 / 7,3 / 5,1) | 3,4 | 20,5 |
| NEBEL | 9 neu gezielt, 16 zusätzlich | 196 | 377 | 24,2 (11,3 / 8,3 / 4,7) | 3,7 | 23,8 |
| EROBERN | 0,3 | 195 | 378 | 24,2 (11,1 / 8,2 / 4,9) | 2,8 | 18,5 |
| SPAREN | 26 gesparte Schüsse | 201 | 382 | 23,8 (10,6 / 8,4 / 4,8) | 2,7 | 15,0 |
| WECHSEL | 4 | 197 | 377 | 24,2 (11,4 / 8,2 / 4,6) | 2,9 | 19,2 |
| SCHUELER | Schüler steuert 2.097 von rund 3.200 Unit-Schritten je Spiel | 203 | 334 | 19,0 (11,5 / 5,1 / 2,4) | 6,7 | 47,8 |
| SCHUELER_ALLE | wie SCHUELER, dazu 28 + 5 Granaten, 10 Ausweichzüge | 197 | 330 | 19,0 (11,9 / 4,7 / 2,4) | 7,0 | 50,1 |

Die R3-Zeile dieser Tabelle stammt aus dem ersten Analyselauf. Ein zweiter R3-Lauf mit dem neueren Analysewerkzeug
(Quelle `3a34f5a`, [Daten](diag_r3_v2/)) ergab dieselben Werte und zusätzlich: Kaggle-Units ohne Punktefeld stehen auf
Feldern mit 5,4 Energie je Schritt, R3-Units nur auf 3,4 (mit Schüler 4,4). Auf den Punktefeldern selbst liegen beide
bei etwa 2,6–2,7.



## Zweite Prüfung auf 200 frischen Karten (7256200–7256399, je Variante 800 Spiele)

Vorab festgelegt im [Plan](PLAN.md#zweite-prüfung-festgelegt-am-17112026-0832-vor-dem-ersten-spiel-auf-diesen-karten),
eingefrorene Quelle `9d42692` ([Skript](run_check2.sh)).

| Variante | Solution | Kaggle | Matches gegen Kaggle (von 1.200) | Punkteanteil gegen Kaggle |
|---|---:|---:|---:|---:|
| R3 (Abgabe) | 391/400 | 4/400 | 37 | 33,7 % |
| **SCHUELER** | 391/400 | 6/400 | 65 | **37,8 %** |
| SCHUELER_ALLE | 394/400 | 4/400 | 49 | 37,2 % |
| HYB_ENS8 | 394/400 | 6/400 | 67 | 37,5 % |

| Variante | Spiele Solution + Kaggle | Spiele Solution | Spiele Kaggle | Punkteanteil Kaggle | besteht |
|---|---:|---:|---:|---:|---|
| **SCHUELER** | +0,25 [−1,62; +2,0] | 0,0 [−2,25; +2,25] | +0,5 [−1,5; +3,0] | **+3,98 [+3,04; +4,96]** | ja |
| SCHUELER_ALLE | +0,38 [−1,38; +2,25] | +0,75 [−1,5; +3,0] | 0,0 [−2,0; +2,0] | +3,49 [+2,52; +4,52] | ja |
| HYB_ENS8 | +0,62 [−1,12; +2,38] | +0,75 [−1,5; +3,0] | +0,5 [−1,5; +3,0] | +3,87 [+2,93; +4,83] | ja |

Nach der vorab festgelegten Auswahlregel tritt SCHUELER zur Bestätigung an.

## Einordnung

- **Taktik-Regeln allein reichen gegen Kaggle nicht.** Granaten erhöhen Kaggles Verluste (2,8 → 3,8 Units je Match),
  Ausweichen senkt unsere Sog-Tode (8,3 → 7,1), Sparen unsere Schuss-Tode (11,0 → 10,6). Das sind kleine Schritte. Die
  Ursache bleibt die Energie: Kaggle-Units ohne Punktefeld stehen auf Feldern mit 5,4 Energie je Schritt, unsere auf 3,4.
- **Der Schüler spielt den Energiekampf wie Kaggle:** weniger eigene Tode (24 → 19 je Match), fast so viele Schüsse
  wie Kaggle (48 statt 18), mehr als doppelt so viele Kaggle-Tode (2,8 → 6,7), Kaggle 43 Punkte weniger je Match.
  R3 behält dabei die Halter auf den Punktefeldern, solange kein Gegner in der Nähe ist.
- Der Vorteil zeigt sich vor allem im **Punkteanteil** (sicher über null auf beiden Kartensätzen) und bei den
  **gewonnenen Matches** gegen Kaggle (65 statt 37 von 1.200). Ganze Spiele gegen Kaggle bleiben selten.
- R3 + Schüler und der bisherige Hybrid V14 + Schüler liegen etwa gleichauf. Der Unterschied zu R3 kommt vom Schüler.
- Auf Dev D wurden 11 Varianten verglichen. Deshalb zählt erst die zweite Prüfung auf frischen Karten und danach die
  Bestätigung.
