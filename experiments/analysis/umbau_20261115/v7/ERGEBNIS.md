# DAgger-Runde 4, Schüler v7, größeres Netz v7L und Ensemble (17.11.2026)

**Kurz:** Die vierte DAgger-Runde und ein fast dreimal so großes Netz bringen auf Dev A **keinen klaren
Fortschritt** gegen Solution und Kaggle. Alle Hybride liegen dort zusammen 1 bis 2 Prozentpunkte über R3. Alle
Intervalle enthalten null, und Dev A ist durch frühere Auswahlen nach oben verzerrt. Das **Ensemble aus v7 und v7L**
ist der bisher stärkste Schüler im direkten Duell: Rein gespielt gewinnt es **196/200 gegen R3** (v7 allein 176/200),
als Hybrid 200/200 gegen Solution. Auf frischen, nie trainierten Spielen ahmen die Schüler mit letzter Bewegung den
Lehrer messbar besser nach, wiederholen ihre letzte Bewegung aber öfter als der Lehrer. **Keine Bestätigung, R3
bleibt die Abgabe.** Die Gegenprobe auf den unbenutzten Karten Dev C läuft ([Plan](../devC/PLAN.md)).

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

## Frische Prüfspiele: Wie gut ahmen die Schüler den Lehrer nach?

Die Validierung im Training ist für den Vergleich ungeeignet (siehe oben). Deshalb wurden zwei neue Sätze gespielt,
die kein Schüler je gesehen hat ([Skript](run_d.sh), [Protokoll](run_d.log), [Werkzeug](../tools/offline_eval.py)):

- **Lehrerspiele:** Der Kaggle-Lehrer spielt selbst, 60 Spiele auf 7254000–7254059 (88 Lehrerseiten,
  306.446 Entscheidungen; Gegner Kaggle/V14/Solution 50/25/25 %).
- **Schülerspiele:** Schüler v5 spielt (Stay-Bias 1,5, Entstapeln), der Lehrer sagt für jede Lage, was er getan
  hätte. 60 Spiele auf 7254100–7254159, 195.548 Entscheidungen. v5 ist der gemeinsame Vorgänger aller anderen
  Schüler, die Lagen bevorzugen also keinen von ihnen.

Gewertet werden nur ausführbare Lehrerbefehle. Die Validierung im Training zählt die nicht ausführbaren (etwa 1,7 %)
zusätzlich als Fehler. Zur Kontrolle lief das Werkzeug auf den 331 Validierungsspielen von v6 und v5c. Nach dieser
Umrechnung ergibt es genau die Trainingswerte 82,2 % und 80,2 % ([Kontrolle](nachahmung/kontrolle_validierung_v6.md)).

| Schüler | gleiche Aktion, Lehrerspiele | gleiche Aktion, Schülerspiele | Schuss erkannt, Schülerspiele |
|---|---:|---:|---:|
| v5 | 83,0 % | 78,2 % | 29,9 % |
| v5c (Kontrolle ohne letzte Bewegung) | 83,7 % | 79,2 % | 33,6 % |
| v6 (letzte Bewegung) | 86,2 % | 80,4 % | 32,0 % |
| v7 (+ DAgger 4) | 86,7 % | 81,1 % | 34,5 % |
| v7L (großes Netz, von Grund auf) | 85,9 % | 80,2 % | 32,0 % |
| **Ensemble v7 + v7L** | **86,9 %** | **81,4 %** | 33,5 % |

**Wiederholt der Schüler nur seine letzte Bewegung?** Gezählt sind Einheiten mit bekannter letzter Bewegung in den
Schülerspielen. Der Lehrer wiederholt dort in 57,6 % der Fälle die letzte Bewegung der Einheit.

| Schüler | wiederholt selbst | richtig, wenn der Lehrer wiederholt | richtig, wenn der Lehrer wechselt |
|---|---:|---:|---:|
| v5c | 59,8 % | 90,6 % | 63,0 % |
| v6 | 63,1 % | 93,6 % | 61,7 % |
| v7 | 62,6 % | 93,5 % | 63,5 % |
| v7L | 62,9 % | 93,3 % | 61,8 % |
| Ensemble | 63,1 % | 94,1 % | 63,5 % |

In den Lehrerspielen ist es genauso: Der Lehrer wiederholt 67,2 %, v5c 65,6 %, v6 69,9 %. Wenn der Lehrer wechselt,
liegt v6 dort mit 68,1 % unter v5c mit 69,0 % ([alle Zahlen](nachahmung/)).

- Die neue Eingabe hilft auch auf frischen Spielen: v6 liegt 2,5 Prozentpunkte (Lehrerspiele) und 1,2 Prozentpunkte
  (Schülerspiele) über der gleich lang trainierten Kontrolle v5c.
- Der Gewinn stammt ganz aus den Fällen, in denen der Lehrer seine Bewegung wiederholt. Wechselt der Lehrer, ist v6
  etwas schlechter als v5c. Die Schüler mit letzter Bewegung wiederholen öfter als der Lehrer. Das ist die erwartete
  Neigung „weiter wie eben“ in milder Form. Nach DAgger-Runde 4 erreicht v7 bei Wechseln wieder den Wert von v5c.
- Das große Netz v7L liegt knapp unter v7. Mehr Parameter helfen in zwei Epochen nicht. Die Kette v4 → v7 hat
  insgesamt viel länger trainiert.
- Auf ihren eigenen Lagen (Schülerspiele) sind alle Schüler etwa 5 Prozentpunkte schlechter als auf Lehrerlagen.
  Diese Lücke soll DAgger schließen.

## Ensemble v7 + v7L auf Dev A

Beide Netze bewerten jede Lage, ihre Log-Wahrscheinlichkeiten werden addiert (`imitate ensemble`). Gleiche Schalter
wie oben, Hybrid wieder mit V14 auf den Punktefeldern.

| Agent | Solution | Kaggle | direkt gegen R3 | Punkteanteil gegen Kaggle |
|---|---:|---:|---:|---:|
| **reines Ensemble** | 197 (572) | 8 (52) | **196** (546) | 37,2 % |
| **Hybrid Ensemble** | **200** (580) | 2 (36) | 174 (480) | 36,5 % |

Gepaart gegen R3: reines Ensemble Solution +1,0 [−2,0; +4,5], Kaggle +2,0 [−3,0; +7,0], zusammen +1,5 [−1,5; +4,5].
Hybrid Ensemble Solution +2,5 [+0,5; +5,5], Kaggle −1,0 [−3,0; 0,0], zusammen +0,75 [−0,76; +2,5].
Direkt gegen R3 gewinnt das reine Ensemble 10 Prozentpunkte öfter als der reine v7 [+4,0; +16,0], der Hybrid
Ensemble 6 Prozentpunkte öfter als der Hybrid v7 [−2,0; +14,0].

## Einordnung

- Vier DAgger-Runden haben den Schüler gegen Solution und im direkten Duell stärker gemacht (reiner Schüler gegen
  Solution: v4 185, v5 190, v7 196 von 200). Gegen Kaggle bleibt es bei 2–10 von 200 Spielen und etwa einem Drittel
  der Punkte.
- Das Ensemble ahmt nur 0,3 Prozentpunkte genauer nach als v7, spielt im direkten Duell aber deutlich stärker.
  Gegen die externen Gegner ist kein Vorteil gesichert.
- Der beste Hybrid gegen Kaggle ist v7L mit 10/200, so viel wie V15. Das sind sechs gewonnene und null verlorene
  Spiele gegenüber R3 auf denselben Sitzen. Bei so wenigen Siegen ist das kein belastbarer Vorteil.
- Auf Dev A wurden inzwischen viele Varianten verglichen. Einzelne gute Werte können deshalb Zufall sein. Darum gibt
  es die vorab festgelegte Gegenprobe auf Dev C.

## Dateien

- v7: `experiments/imitation/students/v7_from_best.pth`, SHA-256
  `a63d66c0938bb4983ebe89478acaaeead53c3b63e7b9fbf4ef14cd0592d56ec5`.
- v7L: `experiments/imitation/students/v7L_scratch.pth`, SHA-256
  `e6f1d5344a35b799181f0e4462a8b9424e33047f969f4eaeeef8ae2f94bd216c`.
- Gepackte Hybride (lokal): v7 `d5dc152cff0889b74d1241e0fb0bf217b1c69dde1ad2080c2c4a8020be331082`,
  v7L `1b17f0fea626fb01bc9957d13f5fd0b91da7f8d8ce9f9363abada574d9e6a269`.
- Ensemble v7 + v7L: `experiments/imitation/students/ens_v7_v7L.pth`, SHA-256
  `dca29436b560c71e7fff3d8b71af7f14afb783718c092d474c0a6b19ff2c1047`; gepackter Hybrid (lokal)
  `dbdbfe98debe376841a072a4c2c860ff094cd0cdfb5d91a8fced62e7a005b9d6`.
- Rohdaten: `hyb_v7_mixed_devA.csv`, `hyb_v7L_mixed_devA.csv`, `student_v7_devA.csv`, `student_v7L_devA.csv`,
  `hyb_ens_v7_v7L_mixed_devA.csv`, `student_ens_v7_v7L_devA.csv`; Nachahmung je Prüfsatz als Tabelle und JSON mit
  allen Zählern in `nachahmung/`. Die Prüfspiele selbst liegen lokal unter `experiments/imitation/k3_holdout_teacher`
  und `experiments/imitation/k3_holdout_dagger_v5`.
