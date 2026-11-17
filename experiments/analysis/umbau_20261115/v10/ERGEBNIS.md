# DAgger-Runde 7 mit dem bestätigten Schüler als Spieler, Schüler v10 und Ensemble v10 + v8L (17.11.2026)

**Kurz:** In DAgger-Runde 7 spielte der in der dritten Bestätigung bestandene reine Schüler v9 (Stay-Bias 1,0,
Entstapeln, Halter-Regel); der Kaggle-Lehrer beschriftete jede Lage. Der daraus weitertrainierte v10 und das Ensemble
v10 + v8L ahmen den Lehrer auf den frischen Prüfspielen **praktisch gleich gut** nach wie v9 + v8L (+0,03 und
+0,10 Prozentpunkte). Ob v10 im Spiel besser ist, prüft der vorab festgelegte [Dev-G-Vergleich](../../devg_20261117/PLAN.md).

## Was gelaufen ist

Eingefrorene Quelle `ab34c54`, streng nach der dritten Bestätigung, 15:10 bis 16:08 ([Skript](run_dagger7.sh),
[Protokoll](run_dagger7.log)).

1. **DAgger-Runde 7:** Spieler Ensemble v9 + v8L mit `imit_stay_bias=1.0`, `imit_unstack=true`,
   `imit_hold_points=true`. 600 Spiele auf 7262000–7262599, Gegner Kaggle/V14/Solution zu 60/20/20 %, 2.054.348
   Entscheidungen in 12,6 Minuten. Der Spieler gewann dabei 18/357 gegen Kaggle, 120/123 gegen V14 und 120/120 gegen
   Solution. In Runde 6 (R3 + Schüler als Spieler) waren es 3/367, 110/117 und 114/116. Andere Karten, nicht gepaart,
   also nur ein Hinweis.
2. **v10:** Fortsetzung von v9 mit allen Daten (b1–b3, DAgger 1–7; rund 21 Mio. Entscheidungen), 2 Epochen zu je
   19 Minuten, Lernrate 0,001, Seed 12, Eingabe „letzte eigene Bewegung“ ([Trainingsprotokoll](training_v10.log)).
   Validierung im Training 82,9 % (nicht mit früheren Läufen vergleichbar).
3. **Ensemble v10 + v8L** und für Dev G zusätzlich das Dreier-Ensemble v10 + v9 + v8L.

Prüfsummen (SHA-256, Dateien lokal unter `experiments/imitation/students/`): `v10_from_v9.pth`
`7590f07366b8d7696ca266c2684149783529cd4eb763b0900f8a23ff435ce521`, `ens_v10_v8L.pth`
`cc22c1de177f6eab5fe5404865404eaa8c3bfe47b011f8fb0b0f3f5ca924dd2d`, `ens_v10_v9_v8L.pth`
`355cc427dc841a973c5715f407bae552757baa2830c973c8568af4bd1561114d`.

## Nachahmung auf frischen Prüfspielen

([Werkzeug](../tools/offline_eval.py), [Lehrerspiele](nachahmung/teacher.md), [Schülerspiele](nachahmung/dagger_v5.md))

| Schüler | Lehrerspiele 7254000–7254059 | Schüler-v5-Spiele 7254100–7254159 | Schuss richtig (Lehrer / v5) |
|---|---:|---:|---:|
| Ensemble v9 + v8L (Kontrolle) | 87,28 % | 82,09 % | 50,4 / 36,0 |
| v10 | 87,01 % | 82,07 % | 53,4 / 38,9 |
| **Ensemble v10 + v8L** | **87,31 %** | **82,19 %** | 50,5 / 36,5 |

Die Kontrolle ergab genau die Werte aus Runde 6. Der Zuwachs je DAgger-Runde liegt jetzt bei wenigen Hundertstel- bis
Zehntelprozentpunkten.
