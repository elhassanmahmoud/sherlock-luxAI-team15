# Vergleich auf Dev G: Schüler v10 nach DAgger-Runde 7 (festgelegt am 17.11.2026, 14:19, bevor v10 existiert)

**Freigabe:** wie Dev E und Dev F (Mahmoud, 17.11.). R3 bleibt die Abgabe, bis Mahmoud und Moayed gemeinsam anders
entscheiden.

## Warum

DAgger-Runde 7 lässt den Dev-F-Sieger (reiner Schüler v9 mit Stay-Bias 1,0 und Halter-Regel) spielen; der
Kaggle-Lehrer beschriftet die Lagen. Daraus entsteht v10 (Fortsetzung von v9) und das Ensemble v10 + v8L
([Skript](../umbau_20261115/v10/run_dagger7.sh)). Frage: Spielt der neue Schüler besser als der zuletzt bestätigte?

## Wer antritt

**Schalter S** sind die Schalter des zuletzt bestätigten Kandidaten: Stay-Bias 1,0, Entstapeln und Halter-Regel, wenn
die dritte Bestätigung (7261000–7261399) besteht, sonst Stay-Bias 1,5 und Entstapeln (P9).

| Name | Spieler |
|---|---|
| R3 | unverändertes R3-Paket (`r3zip:`), Referenz |
| PS | Ensemble v9 + v8L mit Schaltern S (zuletzt bestätigt) |
| E10 | Ensemble v10 + v8L mit Schaltern S |
| E3 | Ensemble v10 + v9 + v8L mit Schaltern S |

## Was gespielt wird

- **Dev G: 7264000–7264199** (200 Karten, bisher unbenutzt), beide Seiten, gegen Solution und Kaggle: je Agent
  800 Spiele, zusammen 3.200. Startet nach DAgger-Runde 7 und v10, eingefrorene Quelle, 10 Prozesse.

## Vorab festgelegte Regel

Gepaart nach Karte (beide Seiten zusammen, 10.000 Ziehungen, Seed 2711). Eine Variante (E10, E3) **besteht**, wenn
1. gegenüber PS: Punkteanteil gegen Kaggle im Mittel mindestens +1,0 Prozentpunkte, untere 95-%-Grenze über 0,
2. gegenüber PS: gewonnene Spiele gegen Solution im Mittel nicht unter −1,0 Prozentpunkt,
3. gegenüber R3: Punkteanteil gegen Kaggle im Mittel mindestens +2,0 mit unterer Grenze über 0, Spiele gegen Solution
   nicht unter −1,0,
4. kein abgefangener Fehler, alle Spiele über 303 Schritte.

Von den bestehenden Varianten die mit dem höchsten Punkteanteil gegen Kaggle (gegenüber R3); bei höchstens 0,5 Abstand
entscheiden die gewonnenen Matches gegen Kaggle. **Danach:** frische Bestätigung auf **7265000–7265399** nach der Regel
aus [BESTAETIGUNG_PLAN.md](../deve_20261117/BESTAETIGUNG_PLAN.md) gegen R3; der zuletzt bestätigte Kandidat spielt zur
Information mit. Besteht keine Variante, bleibt es beim zuletzt bestätigten Kandidaten. Dev G wird danach für keine
Auswahl mehr benutzt.
