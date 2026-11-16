# Neue Eingabe „letzte eigene Bewegung“ (v6) gegen gleich lange Kontrolle (v5c), 17.11.2026

**Kurz:** Mit der neuen Eingabe ahmt der Schüler den Kaggle-Lehrer besser nach: **82,2 % statt 80,2 %** gleiche
Aktion auf denselben Validierungsspielen. Die Kontrolle hatte genauso viele Trainingsschritte. In Spielen gegen
Solution und Kaggle zeigt sich **kein Unterschied** (gepaart 0,0 Prozentpunkte). Direkt gegen R3 gewinnt v6 etwas
öfter als die Kontrolle (Hybrid 164 statt 152 von 200, rein 178 statt 170), aber die Intervalle enthalten null.
**Keine Bestätigung, R3 bleibt die Abgabe.** v6 ist der Startpunkt für DAgger-Runde 4 ([../v7](../v7/)).

## Was gelaufen ist

Alles lief auf Mahmouds M5 aus der eingefrorenen Quelle `8324845`, streng nacheinander ([Skript](run_v6.sh),
[Protokoll](run_v6.log)).

1. **Zwei Fortsetzungen von v5** auf denselben Daten (b1–b3, DAgger 1–3, 13,2 Mio. Einheitsentscheidungen),
   je 2 Epochen, Lernrate 0,001, Seed 6, Sparmodus:
   - **v6** bekommt fünf zusätzliche Eingaben je Einheit: ihre letzte Bewegung (stehen, hoch, rechts, runter,
     links; in gespiegelten Koordinaten wie alle Merkmale). Die neuen Gewichte starten bei null. Am Start sind die
     Ausgaben deshalb genau gleich wie bei v5 (geprüft, größte Abweichung 0,0).
   - **v5c** ist dieselbe Fortsetzung ohne neue Eingabe. So misst der Vergleich nur die Eingabe und nicht die
     längere Trainingszeit.
2. **Tests auf Dev A** (7150000–7150099, beide Seiten): gepackter Hybrid (V14 hält Punktefelder, der Schüler
   kämpft; wie V15) und reiner Schüler, jeweils gegen Solution, Kaggle und das R3-Paket, Hybrid zusätzlich gegen V14.
   Der reine v6 lief außerdem ohne Stay-Bias. R3, Hybrid v5 und reiner v5 stammen aus dem Lauf vom 16.11. auf
   denselben Karten ([v5](../v5/ERGEBNIS.md)).

## Nachahmung (Validierung, 331 Spiele, 1,14 Mio. Entscheidungen)

| Schüler | gleiche Aktion | ganzer Befehl | stehen | hoch | rechts | runter | links | Schuss | Schussziel exakt |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v5c (Kontrolle) | 80,2 % | 79,9 % | 93 | 46 | 80 | 79 | 46 | 39 | 78 % |
| **v6** (letzte Bewegung) | **82,2 %** | **81,9 %** | 94 | 53 | 81 | 81 | 54 | 40 | 78 % |

Den größten Gewinn gibt es bei den seltenen Richtungen hoch und links (je etwa 4 % der Daten).
Grenze: Die Validierungsspiele wurden mit Seed 6 gezogen, v5 selbst wurde mit Seed 5 trainiert. Das Startnetz kannte
also einen Teil dieser Spiele. Belastbar ist deshalb nur der Unterschied v6 gegen v5c (gleicher Start, gleiche
Daten, gleiche Schritte), nicht der Vergleich mit den 80,5 % aus dem v5-Training
([Protokoll v6](training_v6.log), [Protokoll v5c](training_v5c.log)).

## Spiele (gewonnene Spiele von 200, in Klammern Matches von 600)

| Agent | Solution | Kaggle | direkt gegen R3 | direkt gegen V14 |
|---|---:|---:|---:|---:|
| R3 (Abgabe) | 195 (570) | 4 (30) | – | – |
| Hybrid v5 | 193 (565) | 0 (36) | 158 (428) | 182 |
| Hybrid v5c | 197 (575) | 6 (36) | 152 (434) | 194 |
| **Hybrid v6** | 195 (572) | 8 (48) | **164** (438) | 192 |
| reiner v5 | 190 (551) | 4 (34) | 180 (506) | – |
| reiner v5c | 194 (565) | 2 (28) | 170 (490) | – |
| **reiner v6** | 192 (558) | 4 (38) | 178 (496) | – |
| reiner v6 ohne Stay-Bias | 192 (552) | 4 (50) | – | – |

Punkteanteil gegen Kaggle: R3 33,0 %, Hybrid v5c 35,3 %, Hybrid v6 35,9 %, reiner v5c 34,7 %, reiner v6 34,3 %,
reiner v6 ohne Stay-Bias 37,1 %.

**Gepaarte Differenzen** (Prozentpunkte ganze Spiele, 95-%-Kartenintervall, 10.000 Ziehungen, Seed 2711;
[Werkzeug](../tools/compare_dev.py)):

| Vergleich | Solution + Kaggle | direkt gegen R3 |
|---|---:|---:|
| reiner v6 − reiner v5c | 0,0 [−1,75; +1,75] | +4,0 [−3,0; +11,0] |
| Hybrid v6 − Hybrid v5c | 0,0 [−2,75; +3,0] | +6,0 [−4,0; +16,0] |
| Hybrid v6 − R3 | +1,0 [−2,25; +4,25] | – |
| Hybrid v5c − R3 | +1,0 [−1,75; +3,75] | – |

Getrennt nach Gegner liegt Hybrid v6 gegen R3 bei Solution 0,0 [−4,0; +3,5] und bei Kaggle +2,0 [−3,0; +7,0].

**Stay-Bias beim reinen v6** (ohne minus mit, je Spiel): gewonnene Spiele gleich (192 und 4). Gegen Kaggle steigt
der Punkteanteil ohne Stay-Bias um +2,6 Prozentpunkte [+0,8; +4,2], gegen Solution sinkt er um −4,8 [−6,2; −3,5].
Das ist ein nachträglicher Nebenbefund auf einem oft benutzten Kartensatz, keine geprüfte Aussage.

## Einordnung

- Der Gewinn bei der Nachahmung ist fair gemessen: gleicher Start, gleiche Daten, gleich viele Schritte. Die letzte
  Bewegung hilft dem Netz vorherzusagen, was der Lehrer tut.
- Im Spiel sieht man das auf 100 Karten nicht. Ein möglicher Grund ist bekannt: Mit der eigenen letzten Aktion als
  Eingabe lernt ein Netz leicht „weiter wie eben“. In den Lehrerspielen ist das fast immer richtig. Im eigenen Spiel
  wiederholt der Schüler damit aber auch seine Fehler. Das ist eine Vermutung und noch nicht geprüft.
- Dev A wurde schon oft für Auswahlen benutzt; alle Werte sind nach oben verzerrt.
- Nächster Schritt (läuft seit 00:54): DAgger-Runde 4 mit v6, danach v7 (Fortsetzung von v6) und v7L (größeres
  Netz mit 96 Kanälen und 8 Blöcken, von Grund auf), Ergebnisse in [../v7](../v7/).

## Dateien

- Schüler v6: `experiments/imitation/students/v6_pm_from_v5.pth`, SHA-256
  `7b4eec696b4d1afbe1aee53d5e00b76574dbd6376fa9eedc0b330e38ad546b6d` (699.721 Parameter). Eine Kopie liegt unter
  `experiments/candidates/umbau_20261116/student_v6.pth`.
- Kontrolle v5c: `experiments/imitation/students/v5c_from_v5.pth` (lokal), SHA-256
  `0f559954a214ca11c2c734e429377e5c5c4a9f1161b7f1843db2a22611767e57`.
- Gepackte Hybride (lokal): v6 `ae84d563c1acd3e183ef71ca15ea07071aad3e4ec34c547c3a85c86cc2e6a1ec`,
  v5c `0f1469d4512bdff55dad9309c95b043d604f07af2d67757cdd314018d220bc2d`.
- Rohdaten: `hyb_v6_mixed_devA.csv`, `hyb_v5c_mixed_devA.csv`, `student_v6_devA.csv`, `student_v5c_devA.csv`,
  `student_v6_sb0_devA.csv` (je Spiel eine Zeile, alle 303 Schritte).
