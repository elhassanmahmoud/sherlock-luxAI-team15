# DAgger-Runde 3 und Schüler v5 (16.11.2026)

**Kurz:** Die dritte DAgger-Runde macht den Schüler stärker gegen Solution und im direkten Duell. Der reine
Schüler v5 gewinnt auf Dev A **180/200 direkt gegen die Abgabe R3**. Gegen den Kaggle-Agenten ändert sich nichts:
Alle Varianten holen dort 33–36 % der Punkte und nur wenige Spiele. Gegen Solution liegt v5 unter R3. Deshalb gibt
es **keine Bestätigung und keine Übernahme**. R3 bleibt die Abgabe.

## Was gelaufen ist

Alles lief auf Mahmouds M5 aus der eingefrorenen Quelle `1c148c3`, streng nacheinander ([Skript](run_v5.sh),
[Protokoll](run_v5.log)).

1. **DAgger-Runde 3:** Schüler v4 spielt mit Stay-Bias 1,5 und Entstapeln, der Kaggle-Lehrer beschriftet jede Lage.
   600 Spiele auf den Karten 7252000–7252599, Gegner Kaggle/V14/Solution zu 60/20/20 %, 2.013.415 Entscheidungen,
   11 Minuten. Der Schüler gewann dabei 3/371 gegen Kaggle, 109/121 gegen V14 und 105/108 gegen Solution. Die
   Teildaten vom 15.11. wurden nicht verwendet.
2. **Schüler v5:** gleiches Rezept wie v4 (CNN 64 Kanäle, 6 Blöcke, 2 Epochen, Sparmodus), Daten b1–b3 und DAgger
   1–3. Validierung 80,5 % gleiche Aktion, Schussziel exakt 75 %, genauso wie v4 ([Trainingsprotokoll](training_v5.log)).
3. **Tests auf Dev A** (7150000–7150099, beide Seiten): Hybrid v5 mixed (V14 hält Punktefelder, v5 kämpft; wie
   V15), reiner v5 und als Referenz das unveränderte R3-Paket (`r3zip:`). V15, V14 und reiner v4 stammen aus den
   Dev-A-Läufen vom 15.11. auf denselben Karten. Dort spielen V14 und V15 nachweislich Zug für Zug gleich wie heute.

## Ergebnisse (gewonnene Spiele, in Klammern Matches)

| Agent | Solution | Kaggle | direkt gegen R3 | direkt gegen V14 |
|---|---:|---:|---:|---:|
| R3 (Abgabe) | 195/200 (570/600) | 4/200 (30/600) | – | – |
| V14 | 188/200 (522/600) | 8/200 (30/600) | – | – |
| V15 = Hybrid v4 | 194/200 (557/600) | 10/200 (56/600) | 136/200 (394/600) | 180/200 |
| **Hybrid v5** | 193/200 (565/600) | 0/200 (36/600) | **158/200** (428/600) | 182/200 |
| reiner v4 | 185/200 (536/600) | 6/200 (40/600) | – | 184/200 |
| **reiner v5** | 190/200 (551/600) | 4/200 (34/600) | **180/200** (506/600) | – |

Punkteanteil gegen Kaggle: R3 33,0 %, V15 34,8 %, Hybrid v5 35,6 %, reiner v5 33,6 %.

**Gepaart gegen R3** (Prozentpunkte ganze Spiele, 95-%-Kartenintervall, 10.000 Ziehungen, Seed 2711;
[Werkzeug](../tools/compare_dev.py)):

- Hybrid v5: Solution −1,0 [−5,0; +2,5], Kaggle −2,0 [−5,0; 0,0], beide zusammen −1,5 [−4,0; +0,75].
- reiner v5: Solution −2,5 [−7,0; +1,5], Kaggle 0,0 [−4,0; +4,0], beide zusammen −1,25 [−4,0; +1,5].
- V15: Solution −0,5 [−4,0; +3,0], Kaggle +3,0 [0,0; +7,0], beide zusammen +1,25 [−0,75; +3,5].

## Einordnung

- Dev A ist ein Entwicklungssatz; V15 wurde dort ausgewählt, seine Werte sind nach oben verzerrt. Auf den
  400 Bestätigungskarten gewannen V14, V15 und R3 gegen Kaggle jeweils nur 12/800.
- Der Fortschritt durch DAgger zeigt sich gegen Solution (rein: v4 185 → v5 190) und im direkten Duell
  (Hybrid gegen R3: 136 → 158). Gegen Kaggle bleibt die Lücke: Der Schüler stimmt zu 80 % mit dem Lehrer überein,
  verliert aber fast jedes Spiel gegen ihn.
- Nächster Versuch (läuft): neue Eingabe „letzte eigene Bewegung“ (v6) gegen eine gleich lange trainierte
  Kontrolle (v5c), [Ergebnisse in ../v6](../v6/).

## Dateien

- Schüler v5: `experiments/imitation/students/v5_b123d123.pth`, SHA-256
  `af01b28114deda63e2ce36858b3551cc75f3eff81d780c4918df0acf046768c1`. Eine Kopie liegt für Codex unter
  `experiments/candidates/umbau_20261116/student_v5.pth`.
- Gepackter Hybrid v5: `experiments/imitation/releases/v5_mixed/weights/agent.pth` (lokal), SHA-256
  `791a42c393f2660c75bc58d79f763f2fb2c35da36ed98980496cb293e880ec01`.
- Rohdaten: `hyb_v5_mixed_devA.csv`, `student_v5_devA.csv`, `r3_devA.csv`, `v15_vs_r3_devA.csv` (je Spiel eine
  Zeile, alle 303 Schritte).
