# DAgger-Runde 6 mit R3 + Schüler als Spieler, Schüler v9 und Ensemble v9 + v8L (17.11.2026)

**Kurz:** Zum ersten Mal spielte in einer DAgger-Runde nicht der reine Schüler, sondern R3 mit eingebautem Schüler,
also der Kandidat der Bestätigung. Der Kaggle-Lehrer beschriftete die Lagen. Der daraus weitertrainierte Schüler v9 und
das Ensemble v9 + v8L ahmen den Lehrer auf den frischen Prüfspielen **0,1 bis 0,4 Prozentpunkte genauer** nach als v8
und v8 + v8L. Der Fortschritt ist klein, wie bei den letzten Runden. Im Spiel ist v9 noch nicht getestet. R3 bleibt
die Abgabe.

## Was gelaufen ist

Alles lief auf Mahmouds M5 aus der eingefrorenen Quelle `c2461cc`, streng nach der Bestätigung, von 10:05 bis 11:04
([Skript](run_dagger6.sh), [Protokoll](run_dagger6.log)).

1. **DAgger-Runde 6:** Spieler `r3t:schueler=ens8` (R3; Units im Kampf und ohne Punktefeld-Aufgabe spielen das
   Ensemble v8 + v8L mit Stay-Bias 1,5 und Entstapeln). Aufgezeichnet werden die Lagen des eingebauten Schülers mit
   der Antwort des Lehrers. 600 Spiele auf 7257000–7257599, Gegner Kaggle/V14/Solution zu 60/20/20 %, 1.999.472
   Entscheidungen in 16 Minuten. Der Spieler gewann dabei 114/116 gegen Solution, 3/367 gegen Kaggle und 110/117
   gegen V14. Das sind andere Karten und nicht gepaart, also nur ein Hinweis.
2. **v9:** Fortsetzung von v8 mit allen Daten (b1–b3, DAgger 1–6; 19,0 Mio. Entscheidungen, davon 18,7 Mio. im Spiel
   ausführbar), 2 Epochen zu je 17,5 Minuten, Lernrate 0,001, Seed 11, Eingabe „letzte eigene Bewegung“
   ([Trainingsprotokoll](training_v9.log)). Validierung im Training 83,5 % gleiche Aktion. Wie bei v8 ist diese Zahl
   nicht mit früheren vergleichbar.
3. **Ensemble v9 + v8L** (`imitate ensemble`, Log-Wahrscheinlichkeiten addiert). v8L blieb unverändert.

Prüfsummen (SHA-256): `v9_from_v8.pth` `1ca5ba0db5495ff0dbc2cbd4eae9946688a87bb82b0592ddc7e3308f0579c949`,
`ens_v9_v8L.pth` `a9f551f8a3b866e42199faf9342eb9cd0c901b493cb7818992d395a9c3b6e7ea` (beide lokal unter
`experiments/imitation/students/`).

## Nachahmung auf frischen Prüfspielen

Dieselben Prüfsätze wie in Runde 5, die kein Schüler im Training gesehen hat
([Werkzeug](../tools/offline_eval.py), [Lehrerspiele](nachahmung/teacher.md),
[Schülerspiele](nachahmung/dagger_v5.md)). Anteil gleicher Aktion mit dem Lehrer:

| Schüler | Lehrerspiele 7254000–7254059 | Schüler-v5-Spiele 7254100–7254159 | Schuss richtig (Lehrer / v5) |
|---|---:|---:|---:|
| v8 | 86,85 % | 81,49 % | 51,6 / 36,3 |
| Ensemble v8 + v8L | 87,18 % | 81,88 % | 49,5 / 35,1 |
| **v9** | 86,90 % | 81,89 % | 52,6 / 38,1 |
| **Ensemble v9 + v8L** | **87,28 %** | **82,09 %** | 50,4 / 36,0 |

- v9 gegenüber v8: +0,05 und +0,40 Prozentpunkte. Ensemble v9 + v8L gegenüber v8 + v8L: +0,10 und +0,21.
- Die Kontrolle v8 ergab genau die Werte aus Runde 5. Die Messung ist also vergleichbar.
- Die neuen Daten stammen aus Lagen, in denen R3 die Halter steuert. Die Prüfsätze enthalten solche Lagen nicht. Ein
  Gewinn genau dort wäre mit diesen Prüfsätzen nicht sichtbar.

## Einordnung

- Weitere Runden derselben Art bringen pro Runde nur noch Zehntelprozentpunkte bei der Nachahmung.
- Ob v9 im Spiel besser ist, zeigt erst ein Test auf neuen Karten. Das Ensemble v9 + v8L ist dafür als Schüler
  `ens9` in `agents/sherlock_r3t/agent.py` eingetragen.
- Daten: `experiments/imitation/k3_dagger6_r3t/` (lokal, 600 Spieldateien, `collect.json`).
