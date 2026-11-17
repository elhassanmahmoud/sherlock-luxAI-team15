# Ergebnis Dev F: Schalter für den reinen Schüler v9 (17.11.2026)

**Kurz:** **Schwächere Strafe fürs Stehenbleiben (1,0 statt 1,5) zusammen mit der Halter-Regel `imit_hold_points`**
ist besser als der bestätigte reine Schüler v9. Diese Variante besteht als einzige die vorab festgelegte Regel:
Punkteanteil gegen Kaggle +1,15 [+0,02; +2,34] Prozentpunkte über dem Basis-Schüler und +4,57 [+3,37; +5,73] über R3,
396/400 gegen Solution (wie R3) und 20/400 gegen Kaggle (R3 6/400). Sie geht in eine eigene frische Bestätigung auf
7261000–7261399. **Das neue Besetzen freier Punktefelder (`imit_fill_points`) schadet** und wird nicht weiterverfolgt.

## Was gelaufen ist

Vorab festgelegt im [Plan](PLAN.md) (Commit `26640d1` um 11:26, Nachtrag mit den Besetzen-Varianten `1616dd1`, beide vor
dem Ende von Dev E). Basis PB ist nach der Regel der reine Schüler v9 (höherer Punkteanteil auf Dev E als v8). Karten
7259000–7259199, beide Seiten, gegen Solution und Kaggle, je Agent 800 Spiele, zusammen 5.600. Eingefrorene Quelle
`ab34c54`, 10 Prozesse, streng nacheinander von 13:12 bis 14:13 ([Skript](run_devf.sh), [Protokoll](run_devf.log)). Alle
Spiele liefen über 303 Schritte ohne abgefangenen Fehler.

## Ergebnisse

| Agent | Solution | Kaggle | Matches gegen Kaggle | Punkteanteil gegen Kaggle | Stehen gegen Kaggle |
|---|---:|---:|---:|---:|---:|
| R3 | 396/400 | 6/400 | 41/1.200 | 33,1 % | 31,8 % |
| PB: reiner Schüler v9 (Stay-Bias 1,5) | 396/400 | 12/400 | 93/1.200 | 37,3 % | 33,2 % |
| PB_H: + Halter-Regel | 397/400 | 24/400 | 121/1.200 | 38,1 % | 34,5 % |
| PB_S10: Stay-Bias 1,0 | 394/400 | 12/400 | 109/1.200 | 38,2 % | 34,7 % |
| **PB_S10_H: Stay-Bias 1,0 + Halter-Regel** | **396/400** | **20/400** | **103/1.200** | **38,8 %** | 35,8 % |
| PB_HF: + Halter-Regel + Besetzen | 395/400 | 6/400 | 67/1.200 | 36,1 % | 33,1 % |
| PB_S10_HF: Stay-Bias 1,0 + Halter + Besetzen | 388/400 | 10/400 | 71/1.200 | 36,6 % | 34,1 % |

**Gepaart** (Prozentpunkte, 95-%-Kartenintervall, 10.000 Ziehungen, Seed 2711, [Auswertung](analyze_devf.py)):

| Variante | gegen PB: Punkteanteil Kaggle | gegen PB: Spiele Solution | gegen R3: Punkteanteil Kaggle | gegen R3: Spiele Solution | besteht |
|---|---:|---:|---:|---:|---|
| PB_H | +0,48 [−0,45; +1,38] | +0,25 [−0,75; +1,50] | +3,90 [+2,65; +5,10] | +0,25 | nein |
| PB_S10 | +0,81 [−0,30; +1,98] | −0,50 [−1,25; 0,00] | +4,23 [+3,02; +5,40] | −0,50 | nein |
| **PB_S10_H** | **+1,15 [+0,02; +2,34]** | 0,00 [−1,50; +1,00] | **+4,57 [+3,37; +5,73]** | 0,00 | **ja** |
| PB_HF | −0,96 [−1,96; +0,01] | −0,25 [−1,75; +1,25] | +2,46 [+1,39; +3,41] | −0,25 | nein |
| PB_S10_HF | −0,05 [−1,19; +1,13] | −2,00 [−4,00; −0,25] | +3,37 [+2,33; +4,37] | −2,00 | nein |

## Einordnung

- **Weniger Druck zum Laufen hilft.** Mit Stay-Bias 1,0 und Halter-Regel steht der Schüler in 35,8 % der Schritte
  (Basis 33,2 %, Lehrer 41 %) und holt mehr Punkte. Beide Änderungen wirken einzeln etwas, zusammen am meisten.
- **Halter-Regel allein** verdoppelt die gewonnenen Spiele gegen Kaggle (24 statt 12 von 400), erreicht beim
  Punkteanteil aber nicht die verlangten +1,0 gegenüber der Basis.
- **Freie Punktefelder besetzen schadet.** Obwohl auf der eigenen Hälfte oft bekannte Felder leer sind
  ([Messung](../deve_20261117/PUNKTEFELDER.md)), verlieren beide Besetzen-Varianten Punkte, mit Stay-Bias 1,0 auch
  8 Solution-Spiele. Wahrscheinlich zieht die Regel Units aus Kämpfen ab und schickt sie auf umkämpfte Felder. Der
  Schalter bleibt im Code (Standard aus), wird aber nicht weiterverfolgt.
- Die Unterschiede zwischen den Schalter-Varianten sind klein und liegen teils im Zufall. Deshalb folgt für PB_S10_H eine
  eigene frische Bestätigung; der bereits bestätigte reine Schüler v9 spielt dort zum Vergleich mit.
