# DAgger-Runde 5, Schüler v8 und v8L, Ensemble v8 + v8L (17.11.2026)

**Kurz:** DAgger-Runde 5 macht den Schüler noch etwas besser, aber nicht entscheidend. Das reine Ensemble aus v8 und
v8L gewinnt auf Dev A **198/200 direkt gegen R3**, so oft wie kein Schüler zuvor. Der Hybrid daraus liegt gegen
Solution und Kaggle zusammen auf Dev A +2,25 Prozentpunkte über R3, auf den vorher angemeldeten Dev-C-Karten +1,75.
Die vorab festgelegte Regel verlangt dort mindestens +2. **Keine Bestätigung, R3 bleibt die Abgabe.** Auf frischen
Prüfspielen ahmt das neue Ensemble den Lehrer 0,3 bis 0,5 Prozentpunkte genauer nach als das Ensemble aus Runde 4.
Gegen Kaggle gewinnen alle Schüler weiter nur wenige Spiele.

## Was gelaufen ist

Alles lief auf Mahmouds M5 aus der eingefrorenen Quelle `8324845`, streng nacheinander von 04:16 bis 05:57
([Skript](run_f.sh), [Protokoll](run_f.log)).

1. **DAgger-Runde 5:** Diesmal spielt das Ensemble v7 + v7L (Stay-Bias 1,5, Entstapeln), der Kaggle-Lehrer
   beschriftet jede Lage. 600 Spiele auf den Karten 7255000–7255599, Gegner Kaggle/V14/Solution zu 60/20/20 %,
   2.058.567 Entscheidungen in 13 Minuten. Das Ensemble gewann dabei 13/339 gegen Kaggle, 120/122 gegen V14 und
   134/139 gegen Solution. In Runde 4 hatte v6 4/361, 120/127 und 106/112 gewonnen. Das sind andere Karten und nicht
   gepaart, also nur ein Hinweis.
2. **v8:** Fortsetzung von v7 mit allen Daten (b1–b3, DAgger 1–5; 17,2 Mio. Entscheidungen, davon 16,9 Mio. im Spiel
   ausführbar), 2 Epochen zu je 16 Minuten, Lernrate 0,001, Seed 9 ([Trainingsprotokoll](training_v8.log)).
3. **v8L:** Fortsetzung des großen Netzes v7L mit denselben Daten, 1 Epoche (38 Minuten), Lernrate 0,001, Seed 10
   ([Trainingsprotokoll](training_v8L.log)).
4. **Ensemble v8 + v8L** (`imitate ensemble`, Log-Wahrscheinlichkeiten addiert) und daraus der gepackte Hybrid
   (V14 auf den Punktefeldern, Schüler im Kampf bis Radius 5, gleiche Schalter).
5. **Tests auf Dev A** (7150000–7150099, beide Seiten): reines Ensemble und Hybrid gegen Solution, Kaggle und das
   R3-Paket. R3 und das Ensemble v7 + v7L stammen aus früheren Läufen auf denselben Karten.

Validierung im Training: v8 84,1 % gleiche Aktion, v8L 82,4 %. Beide Zahlen sind zu günstig und nicht mit früheren
vergleichbar. Jeder Lauf zieht seine Validierungsspiele mit eigenem Seed, und beide Netze bauen auf Vorgängern auf,
die einen Teil dieser Spiele schon im Training gesehen haben. Den fairen Vergleich liefern die frischen Prüfspiele
weiter unten.

## Spiele auf Dev A (gewonnene Spiele von 200, in Klammern Matches von 600)

| Agent | Solution | Kaggle | direkt gegen R3 | Punkteanteil gegen Kaggle |
|---|---:|---:|---:|---:|
| R3 (Abgabe) | 195 (570) | 4 (30) | – | 33,0 % |
| Hybrid Ensemble v7 + v7L | 200 (580) | 2 (36) | 174 (480) | 36,5 % |
| **Hybrid Ensemble v8 + v8L** | 198 (576) | 10 (50) | 174 (470) | 36,6 % |
| reines Ensemble v7 + v7L | 197 (572) | 8 (52) | 196 (546) | 37,2 % |
| **reines Ensemble v8 + v8L** | 196 (572) | 6 (78) | **198** (564) | 38,3 % |

**Gepaart gegen R3** (Prozentpunkte ganze Spiele, 95-%-Kartenintervall, 10.000 Ziehungen, Seed 2711;
[Werkzeug](../tools/compare_dev.py)):

| Agent | Solution | Kaggle | beide zusammen |
|---|---:|---:|---:|
| **Hybrid Ensemble v8 + v8L** | +1,5 [−1,0; +4,5] | +3,0 [−2,0; +8,0] | **+2,25 [−0,75; +5,25]** |
| reines Ensemble v8 + v8L | +0,5 [−3,0; +4,0] | +1,0 [−3,0; +6,0] | +0,75 [−2,0; +3,75] |
| zum Vergleich: Hybrid v7L | +0,5 [−3,0; +4,0] | +3,0 [0,0; +7,0] | +1,75 [−0,5; +4,25] |
| zum Vergleich: Hybrid Ensemble v7 + v7L | +2,5 [+0,5; +5,5] | −1,0 [−3,0; 0,0] | +0,75 [−0,76; +2,5] |

Gegenüber Runde 4 auf denselben Sitzen:

- Hybrid Ensemble v8 gegen Hybrid Ensemble v7: Solution −1,0 [−2,5; 0,0], Kaggle +4,0 [0,0; +9,0] (10 Spiele
  gewonnen, 2 verloren), zusammen +1,5 [−1,0; +4,0]. Direkt gegen R3 beide 174/200 (0,0 [−6,0; +6,0]).
- reines Ensemble v8 gegen reines Ensemble v7: zusammen −0,75 [−3,5; +2,0], direkt gegen R3 +1,0 [−2,0; +5,0].

Das reine Ensemble v8 + v8L gewinnt gegen Kaggle 78 von 600 Matches, mehr als jeder andere Agent (R3 30). Ganze
Spiele gewinnt es trotzdem nur 6 von 200, weil es selten zwei von drei Matches holt.

## Gegenprobe des Hybrids auf Dev C

Vor seinem ersten Dev-C-Spiel wurde der Hybrid im [Dev-C-Plan](../devC/PLAN.md) angemeldet (Nachtrag 2, Commit
`7d9aa60`). Es gilt dieselbe Leseregel wie für alle Kandidaten: mindestens +2 Prozentpunkte über R3 gegen Solution und
Kaggle zusammen, und gegen Solution nicht unter R3. Gespielt wurde von 05:58 bis 06:08 auf 7164000–7164099, beide
Seiten ([Skript](../devC/run_e3.sh), [Protokoll](../devC/run_e3.log)).

| Agent | Solution | Kaggle | direkt gegen R3 | Punkteanteil gegen Kaggle | gegen R3, Solution + Kaggle |
|---|---:|---:|---:|---:|---:|
| R3 (Abgabe) | 197 (573) | 4 (20) | – | 30,8 % | – |
| Hybrid v7L (zum Vergleich) | 198 (567) | 10 (32) | 162 (456) | 33,1 % | +1,75 [−0,75; +4,5] |
| **Hybrid Ensemble v8 + v8L** | 200 (579) | 8 (38) | 170 (482) | 33,5 % | **+1,75 [−0,75; +4,5]** |

Getrennt nach Gegner: Solution +1,5 [0,0; +4,0], Kaggle +2,0 [−3,0; +7,0] (8 Spiele gewonnen, 4 verloren gegenüber
R3). Die zweite Bedingung ist erfüllt, die erste mit +1,75 knapp verfehlt. Über Dev A und Dev C zusammen (200 Karten)
sind es +2,0 [+0,12; +4,0]. Das ist nur eine Einordnung, weil der Dev-A-Teil durch die Auswahl eher zu hoch liegt.
Alle Kandidaten auf Dev C: [Dev-C-Auswertung](../devC/ERGEBNIS.md).

## Frische Prüfspiele: Nachahmung

Gleiche Prüfsätze und gleiches Werkzeug wie in Runde 4 (60 Lehrerspiele auf 7254000–7254059, 60 Spiele von v5 mit
Lehrerbeschriftung auf 7254100–7254159, nie trainiert; [Vorgehen](../v7/ERGEBNIS.md), [Skript](run_g.sh),
[Protokoll](run_g.log)). Zur Kontrolle lief v7 noch einmal mit und ergab genau die alten Werte 86,67 % und 81,06 %.
Die Zeilen v7L und Ensemble v7 + v7L stammen aus dem Lauf von Runde 4.

| Schüler | gleiche Aktion, Lehrerspiele | gleiche Aktion, Schülerspiele | Schuss erkannt, Schülerspiele | richtig, wenn der Lehrer wechselt | wiederholt selbst |
|---|---:|---:|---:|---:|---:|
| v7 | 86,7 % | 81,1 % | 34,5 % | 63,5 % | 62,6 % |
| v7L | 85,9 % | 80,2 % | 32,0 % | 61,8 % | 62,9 % |
| Ensemble v7 + v7L | 86,9 % | 81,4 % | 33,5 % | 63,5 % | 63,1 % |
| **v8** | 86,9 % | 81,5 % | 36,3 % | 64,6 % | 62,1 % |
| **v8L** | 86,3 % | 80,8 % | 33,6 % | 63,2 % | 62,5 % |
| **Ensemble v8 + v8L** | **87,2 %** | **81,9 %** | 35,1 % | 64,7 % | 62,7 % |

Die letzten beiden Spalten gelten für die Schülerspiele. Der Lehrer wiederholt dort in 57,6 % der Fälle die letzte
Bewegung der Einheit ([alle Zahlen](nachahmung/)).

- Runde 5 hebt die Nachahmung um 0,2 bis 0,6 Prozentpunkte. Von v6 zu v7 (Runde 4) waren es noch 0,5 bis 0,7. Der
  Zuwachs wird kleiner.
- Bei Richtungswechseln des Lehrers wird v8 besser (64,6 statt 63,5 %). Die Neigung, die letzte Bewegung zu
  wiederholen, bleibt etwa gleich.
- Das große Netz liegt auch nach Runde 5 unter dem kleinen (v8L 80,8 %, v8 81,5 %).
- Schüsse erkennt der Schüler auf seinen eigenen Lagen weiter nur in gut einem Drittel der Fälle. Das ist die größte
  Lücke zum Lehrer.

## Einordnung

- Fünf DAgger-Runden haben den Schüler stetig verbessert, mit immer kleineren Schritten. Gegen Solution liegen reine
  Schüler und Hybride inzwischen bei 196 bis 200 von 200, also auf dem Niveau von R3.
- Gegen Kaggle bleibt die Lücke: 6 bis 10 von 200 Spielen, gut ein Drittel der Punkte. Das reine Ensemble v8 gewinnt
  zwar 78 von 600 Matches gegen Kaggle, holt aber selten zwei Matches im selben Spiel.
- Die Stärke im direkten Duell gegen R3 wächst weiter (198/200), überträgt sich aber nicht auf die externen Gegner.
- Zwei verschiedene Hybride (v7L und Ensemble v8 + v8L) liegen auf Dev C bei je +1,75. Ein kleiner echter Vorteil
  gegenüber R3 ist möglich, aber nicht nachgewiesen. Die vorab festgelegte Regel ist nicht erfüllt.
- Weitere DAgger-Runden derselben Art bringen kaum noch etwas. Für die Kaggle-Lücke braucht es eine gezielte Idee,
  zum Beispiel aus der Kampfdiagnose im [Codex-Auftrag](../../../../docs/AUFTRAG_CODEX_20261116.md) (Aufgabe 4).

## Dateien

- v8: `experiments/imitation/students/v8_from_v7.pth`, SHA-256
  `3bae46183378f4a87b15234f377b9baba8c6966bccef18b981540934fd148476`.
- v8L: `experiments/imitation/students/v8L_from_v7L.pth`, SHA-256
  `b5348816ae8dfc69e40a4c87d17b639d91a5960519688d9e9be5db00ad9cb0f6`.
- Ensemble v8 + v8L: `experiments/imitation/students/ens_v8_v8L.pth`, SHA-256
  `1a68ad1466814a07196d39f9cff222562a972945c1defc44c356d0e47b5e7ad0`; gepackter Hybrid (lokal,
  `experiments/imitation/releases/ens_v8_v8L_mixed/weights/agent.pth`)
  `f021f63d3268afe423daaf53a83e10399cbb508824c1d00dcc9921e94bc1ffd7`.
- Rohdaten: `hyb_ens_v8_v8L_mixed_devA.csv`, `student_ens_v8_v8L_devA.csv` (je Spiel eine Zeile),
  `../devC/hyb_ens_v8_v8L_mixed_devC.csv`; Nachahmung je Prüfsatz als Tabelle und JSON mit allen Zählern in
  `nachahmung/`.
- Die DAgger-Daten der Runde 5 liegen lokal unter `experiments/imitation/k3_dagger5` (nicht im Repo).
