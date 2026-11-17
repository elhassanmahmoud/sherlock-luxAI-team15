# DAgger-Runde 4, Schüler v7 und größeres Netz v7L (17.11.2026)

**Kurz:** Die vierte DAgger-Runde und ein fast dreimal so großes Netz bringen auf Dev A **keinen klaren
Fortschritt**. Alle Hybride liegen gegen Solution und Kaggle zusammen 1 bis 2 Prozentpunkte über R3. Alle
Intervalle enthalten null, und Dev A ist durch frühere Auswahlen nach oben verzerrt. Das große Netz v7L lernt von
Grund auf in zwei Epochen etwa so viel wie die lange Kette v4 → v5 → v6 → v7. **Keine Bestätigung, R3 bleibt die
Abgabe.**

## Was gelaufen ist

Alles lief auf Mahmouds M5 aus der eingefrorenen Quelle `8324845`, streng nacheinander ([Skript](run_c.sh),
[Protokoll](run_c.log)).

1. **DAgger-Runde 4:** Schüler v6 (mit letzter Bewegung, Stay-Bias 1,5, Entstapeln) spielt, der Kaggle-Lehrer
   beschriftet jede Lage. 600 Spiele auf den Karten 7253000–7253599, Gegner Kaggle/V14/Solution zu 60/20/20 %,
   2.034.812 Entscheidungen, 10 Minuten. Der Schüler gewann dabei 4/361 gegen Kaggle, 120/127 gegen V14 und 106/112
   gegen Solution. Vorher lief ein Probelauf mit 2 Spielen fehlerfrei.
2. **v7:** Fortsetzung von v6 mit allen Daten (b1–b3, DAgger 1–4; 15,1 Mio. Entscheidungen), 2 Epochen, Lernrate
   0,001, Seed 7 ([Trainingsprotokoll](training_v7.log)).
3. **v7L:** größeres Netz (96 statt 64 Kanäle, 8 statt 6 Blöcke, 384 statt 256 versteckte Einheiten; 1.809.193 statt
   699.721 Parameter), von Grund auf, gleiche Daten und Eingaben, 2 Epochen zu je 34 Minuten, Lernrate 0,002,
   Seed 8 ([Trainingsprotokoll](training_v7L.log)).
4. **Tests auf Dev A** (7150000–7150099, beide Seiten): gepackter Hybrid und reiner Schüler, jeweils gegen
   Solution, Kaggle und das R3-Paket. R3, v5 und v6 stammen aus den Läufen vom 16./17.11. auf denselben Karten.

Validierung im Training: v7 83,3 % gleiche Aktion, v7L 82,2 %. Die Zahlen sind nicht direkt vergleichbar. v7 baut
auf v6 auf, und v6 hat einen Teil der v7-Validierungsspiele schon im Training gesehen. v7L hat seine
Validierungsspiele nie gesehen. Den fairen Vergleich aller Schüler auf frischen Spielen liefert der nächste Schritt.

## Spiele (gewonnene Spiele von 200, in Klammern Matches von 600)

| Agent | Solution | Kaggle | direkt gegen R3 | Punkteanteil gegen Kaggle |
|---|---:|---:|---:|---:|
| R3 (Abgabe) | 195 (570) | 4 (30) | – | 33,0 % |
| Hybrid v6 | 195 (572) | 8 (48) | 164 (438) | 35,9 % |
| **Hybrid v7** | 198 (572) | 6 (42) | 162 (442) | 35,9 % |
| **Hybrid v7L** | 196 (569) | 10 (54) | 164 (440) | 35,7 % |
| reiner v6 | 192 (558) | 4 (38) | 178 (496) | 34,3 % |
| **reiner v7** | 196 (563) | 2 (40) | 176 (518) | 35,2 % |
| **reiner v7L** | 194 (551) | 6 (36) | 166 (472) | 32,7 % |

**Gepaart gegen R3** (Prozentpunkte ganze Spiele, 95-%-Kartenintervall, 10.000 Ziehungen, Seed 2711;
[Werkzeug](../tools/compare_dev.py)):

| Agent | Solution | Kaggle | beide zusammen |
|---|---:|---:|---:|
| Hybrid v6 | 0,0 [−4,0; +3,5] | +2,0 [−3,0; +7,0] | +1,0 [−2,25; +4,25] |
| Hybrid v7 | +1,5 [−2,0; +4,5] | +1,0 [−3,0; +6,0] | +1,25 [−1,75; +4,5] |
| Hybrid v7L | +0,5 [−3,0; +4,0] | +3,0 [0,0; +7,0] | +1,75 [−0,5; +4,25] |
| reiner v7 | +0,5 [−3,0; +4,0] | −1,0 [−5,0; +2,0] | −0,25 [−2,75; +2,25] |
| reiner v7L | −0,5 [−4,5; +3,5] | +1,0 [−2,0; +5,0] | +0,25 [−2,5; +2,75] |

Gegenüber Hybrid v6 liegen Hybrid v7 bei +0,25 [−2,25; +2,75] und Hybrid v7L bei +0,75 [−1,75; +3,5] (beide
Gegner zusammen).

## Einordnung

- Vier DAgger-Runden haben den Schüler gegen Solution und im direkten Duell stärker gemacht (reiner Schüler gegen
  Solution: v4 185, v5 190, v7 196 von 200). Gegen Kaggle bleibt es bei 2–10 von 200 Spielen und etwa einem Drittel
  der Punkte.
- Das größere Netz holt in zwei Epochen von Grund auf so viel wie die lange Kette. Ein klarer Gewinn durch mehr
  Größe ist auf Dev A nicht zu sehen.
- Der beste Hybrid gegen Kaggle ist v7L mit 10/200, so viel wie V15. Das sind sechs gewonnene und null verlorene
  Spiele gegenüber R3 auf denselben Sitzen. Bei so wenigen Siegen ist das kein belastbarer Vorteil.

## Dateien

- v7: `experiments/imitation/students/v7_from_best.pth`, SHA-256
  `a63d66c0938bb4983ebe89478acaaeead53c3b63e7b9fbf4ef14cd0592d56ec5`.
- v7L: `experiments/imitation/students/v7L_scratch.pth`, SHA-256
  `e6f1d5344a35b799181f0e4462a8b9424e33047f969f4eaeeef8ae2f94bd216c`.
- Gepackte Hybride (lokal): v7 `d5dc152cff0889b74d1241e0fb0bf217b1c69dde1ad2080c2c4a8020be331082`,
  v7L `1b17f0fea626fb01bc9957d13f5fd0b91da7f8d8ce9f9363abada574d9e6a269`.
- Rohdaten: `hyb_v7_mixed_devA.csv`, `hyb_v7L_mixed_devA.csv`, `student_v7_devA.csv`, `student_v7L_devA.csv`.
