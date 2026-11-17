# Vergleich auf Dev F: Strafe fürs Stehenbleiben und Halter-Schalter beim reinen Schüler (festgelegt am 17.11.2026, 11:26, vor dem Ende von Dev E und vor dem ersten Dev-F-Spiel)

**Freigabe:** wie Dev E (Mahmoud, 17.11.: „hast von mir alle Go's“). R3 bleibt die Abgabe, bis Mahmoud und Moayed
gemeinsam anders entscheiden.

## Warum

Aus der [Diagnose](../deve_20261117/DIAGNOSE.md) und den Dev-A-Spielen des reinen Schülers v8 + v8L gegen Kaggle:

- Er hält Punktefelder schlechter als R3 (203–211 statt 251 Unit-Schritte je Match).
- Er steht in 34 % der Unit-Schritte (R3 31 %), der Kaggle-Lehrer in seinen Daten in 41 %.
- Am Matchende hat er nur gut halb so viel Energie wie Kaggle (1.130 statt 1.900). Er zahlt mehr für Bewegungen
  (1.964 statt 1.768 je Match) und verliert mehr im Nebel (417 statt 295).
- Die Strafe fürs Stehenbleiben (`imit_stay_bias` 1,5) wurde am 15.11. für den viel schwächeren Schüler v2 gewählt,
  der damals in 58–67 % der Schritte stand. Sie trifft auch Halter auf Punktefeldern.

Neu ist der Schalter `imit_hold_points`: Der erste Halter auf einem bekannten Punktefeld bekommt keine Strafe fürs
Stehenbleiben. Ohne den Schalter spielt der Schüler wie bisher.

## Wer antritt

**Basis PB** ist der reine Schüler aus Dev E (P8 oder P9), der dort gepaart gegen R3 den höheren Punkteanteil gegen
Kaggle hatte.

| Name | Spieler |
|---|---|
| R3 | unverändertes R3-Paket (`r3zip:`), Referenz |
| PB | Basis: Stay-Bias 1,5, Entstapeln |
| PB_H | wie PB, dazu `imit_hold_points` |
| PB_S10 | Stay-Bias 1,0, Entstapeln |
| PB_S10_H | Stay-Bias 1,0, Entstapeln, `imit_hold_points` |

## Was gespielt wird

- **Dev F: 7259000–7259199** (200 Karten, bisher von niemandem benutzt), beide Seiten, gegen Solution und Kaggle:
  je Agent 800 Spiele, zusammen 4.000.
- Eingefrorene Quelle, 10 Prozesse, streng nacheinander, keine Trainings parallel. Startet erst nach Dev E und nach
  der Bestätigung auf 7260000–7260399.

## Vorab festgelegte Regel

Gepaart nach Karte (beide Seiten zusammen, 10.000 Ziehungen, Seed 2711). Eine Variante (PB_H, PB_S10, PB_S10_H)
**besteht**, wenn alle Bedingungen gelten:

1. gegenüber PB: Punkteanteil gegen Kaggle im Mittel mindestens +1,0 Prozentpunkte, untere 95-%-Grenze über 0,
2. gegenüber PB: gewonnene Spiele gegen Solution im Mittel nicht unter −1,0 Prozentpunkt,
3. gegenüber R3: Punkteanteil gegen Kaggle im Mittel mindestens +2,0, untere Grenze über 0, und gewonnene Spiele gegen
   Solution im Mittel nicht unter −1,0 (wie auf Dev E),
4. kein abgefangener Fehler, alle Spiele über 303 Schritte.

Von den bestehenden Varianten wird die mit dem höchsten Punkteanteil gegen Kaggle (gegenüber R3) gewählt. Liegen zwei
höchstens 0,5 Prozentpunkte auseinander, entscheiden die gewonnenen Matches gegen Kaggle.

**Danach:** Besteht eine Variante, folgt eine frische Bestätigung auf **7261000–7261399** nach genau der Regel aus
[BESTAETIGUNG_PLAN.md](../deve_20261117/BESTAETIGUNG_PLAN.md), gegen R3. Wurde der Dev-E-Sieger auf 7260000–7260399
bestätigt, spielt er dort zur Information mit, damit beide Kandidaten auf denselben Karten verglichen werden. Besteht
keine Variante, gibt es keine weitere Bestätigung. Dev F wird danach für keine Auswahl mehr benutzt.
