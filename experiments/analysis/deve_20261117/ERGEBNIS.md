# Ergebnis Dev E: mehr Schüler gegen Kaggle (17.11.2026)

**Kurz: Der reine Schüler v9 (Ensemble v9 + v8L) ist auf den 200 unbenutzten Dev-E-Karten der stärkste Agent.** Er
gewann 394/400 Spiele gegen Solution (R3 387/400), **22/400 gegen Kaggle** (R3 2/400) und 140 statt 54 von 1.200
Matches gegen Kaggle. Gepaart gegen R3: Punkteanteil gegen Kaggle **+4,97 [+3,92; +6,03]** Prozentpunkte, gewonnene
Spiele gegen Solution und Kaggle zusammen **+3,38 [+1,50; +5,50]**. Nach der vorab festgelegten Regel geht er in die
frische Bestätigung auf 7260000–7260399 ([Regel](BESTAETIGUNG_PLAN.md)). R3 bleibt bis dahin die Abgabe.

## Was gelaufen ist

Vorab festgelegt im [Plan](PLAN.md) (Commit `929d050`, 11:15). Karten 7258000–7258199, beide Seiten, gegen Solution
und Kaggle, je Agent 800 Spiele, zusammen 4.800. Eingefrorene Quelle `929d050`, 10 Prozesse, streng nacheinander von
11:15 bis 12:28 ([Skript](run_deve.sh), [Protokoll](run_deve.log)). Alle Spiele liefen über 303 Schritte ohne
abgefangenen Fehler.

## Ergebnisse

| Agent | Solution | Kaggle | Matches gegen Kaggle | Punkteanteil gegen Kaggle |
|---|---:|---:|---:|---:|
| R3 (Abgabe) | 387/400 | 2/400 | 54/1.200 | 33,3 % |
| S8: R3 + Schüler v8 (nur Vergleich) | 396/400 | 12/400 | 94/1.200 | 38,3 % |
| S9: R3 + Schüler v9 | 390/400 | 6/400 | 86/1.200 | 37,9 % |
| S9H: wie S9, Halter immer R3 | 394/400 | 2/400 | 60/1.200 | 35,9 % |
| P8: reiner Schüler v8 | 387/400 | 10/400 | 102/1.200 | 38,1 % |
| **P9: reiner Schüler v9** | **394/400** | **22/400** | **140/1.200** | **39,0 %** |

**Gepaart gegen R3** (Prozentpunkte bzw. Matches je Spiel, 95-%-Kartenintervall, 10.000 Ziehungen, Seed 2711,
[Auswertung](analyze_deve.py)):

| Agent | Punkteanteil Kaggle | Spiele Solution | Spiele Kaggle | Spiele zusammen | Matches je Spiel gegen Kaggle | besteht |
|---|---:|---:|---:|---:|---:|---|
| S8 | +4,55 [+3,57; +5,59] | +2,25 [−0,25; +5,00] | +2,50 [0,00; +5,01] | +2,38 [+0,50; +4,38] | +0,100 [+0,030; +0,175] | – |
| S9 | +4,28 [+3,44; +5,12] | +0,75 [−1,75; +3,25] | +1,00 [−1,00; +3,00] | +0,88 [−0,75; +2,62] | +0,080 [+0,015; +0,145] | ja |
| S9H | +2,89 [+2,10; +3,71] | +1,75 [−0,25; +4,00] | 0,00 [−1,50; +1,50] | +0,88 [−0,38; +2,25] | +0,015 [−0,035; +0,070] | ja |
| P8 | +4,29 [+3,25; +5,35] | 0,00 [−3,00; +3,00] | +2,00 [0,00; +4,50] | +1,00 [−0,88; +3,00] | +0,120 [+0,045; +0,200] | ja |
| **P9** | **+4,97 [+3,92; +6,03]** | +1,75 [−0,75; +4,50] | **+5,00 [+2,00; +8,50]** | **+3,38 [+1,50; +5,50]** | **+0,215 [+0,135; +0,300]** | **ja** |

**Auswahl nach der Regel:** P9, S9, S9H und P8 bestehen. P9 hat den höchsten Punkteanteil, 0,68 Prozentpunkte vor P8,
und tritt in der Bestätigung an. Für Dev F ist P9 die Basis PB, weil P9 unter den reinen Schülern den höheren
Punkteanteil hatte ([Dev-F-Plan](../devf_20261117/PLAN.md)).

## Einordnung

- **Mehr Schüler ist gegen Kaggle besser.** Halter, die immer R3 spielen (S9H), kosten 1,4 Prozentpunkte Punkteanteil
  gegenüber S9. Der reine Schüler v9 liegt vorn, besonders bei gewonnenen Matches und Spielen gegen Kaggle.
- **v9 hilft dem reinen Schüler**, im R3-Mix ist kein Unterschied zu v8 sichtbar. Die Unterschiede zwischen den
  Schülern liegen teils im Zufall; die Bestätigung prüft P9 allein gegen R3.
- **Gegen Solution** verliert kein Kandidat gegenüber R3. R3 gewann auf Dev E nur 387/400, weniger als auf früheren
  Kartensätzen.
- **Direkt gegen R3** (7258000–7258049, je 100 Spiele, nur Information; Matches in Klammern): S8 96/100 (282/300),
  S9 96/100 (274/300), S9H 90/100 (242/300), P8 96/100 (286/300), **P9 98/100 (286/300)**. Ein direkter Sieg beweist
  keine Stärke gegen andere Gegner, passt aber zum Bild.
