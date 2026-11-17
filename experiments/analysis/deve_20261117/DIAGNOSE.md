# Diagnose: Was der Schüler gegen Kaggle verändert (17.11.2026, nur Messung)

Dieselben 30 Analysekarten 7256000–7256029 wie in der [ersten Analyse](../r3_kaggle_20261117/ERGEBNIS.md), beide
Seiten, je 60 Spiele gegen den Kaggle-Dritten. Jeder Schritt wurde mit den Regeln der Engine nachgerechnet
([Skript](../r3_kaggle_20261117/diagnose.py), neu mit `--agent student:NAME`; in allen Läufen 0 Abweichungen vom
echten Folgezustand). Werte je Match (180 Matches je Agent):

| | R3 | R3 + Schüler v8 (S8) | reiner Schüler v8 (P8) | reiner Schüler v9 (P9) |
|---|---:|---:|---:|---:|
| gewonnene Matches | 6 | 14 | **22** | 10 |
| eigene Punkte / Kaggle-Punkte | 195 / 377 | 203 / 334 | 187 / **289** | 180 / 301 |
| Punkteanteil | 34,1 % | 37,9 % | **39,3 %** | 37,4 % |
| eigene Tode / Kaggle-Tode | 24,2 / 2,8 | 19,0 / 6,7 | 17,3 / 8,8 | 16,8 / 8,5 |
| davon durch Schüsse / Sog / Zusammenstoß | 11,0 / 8,3 / 4,9 | 11,5 / 5,1 / 2,4 | 11,0 / 4,0 / 2,3 | 10,8 / 4,0 / 2,0 |
| Tode auf Punktefeldern (eigene / Kaggle) | 9,4 / 0,8 | 7,6 / 2,5 | 5,9 / 3,6 | 5,8 / 3,3 |
| Energie aus dem Feld je Unit und Schritt (Kaggle etwa 4,3) | 2,85 | 3,69 | 4,03 | 4,09 |
| Schüsse (eigene / Kaggle) | 18 / 39 | 48 / 47 | 53 / 51 | 52 / 51 |
| direkte Treffer (eigene / Kaggle) | 6,7 / 25,4 | 20,5 / 26,3 | 22,8 / 26,3 | 23,2 / 27,4 |
| Unit-Schritte auf Punktefeldern (eigene / Kaggle) | 251 / 405 | 252 / 362 | **211** / 320 | **203** / 333 |
| Units am Matchende (eigene / Kaggle) | 7,4 / 15,9 | 10,9 / 15,7 | 11,8 / 15,3 | 12,3 / 15,1 |

## Was man daraus lernt

- **Der Schüler hat den Energiekrieg zum großen Teil übernommen:** Er schießt so oft wie Kaggle, trifft dreimal so oft
  direkt wie R3, tankt fast so viel Energie und verliert weniger Units durch Sog und Zusammenstöße.
- **Der reine Schüler kämpft am stärksten**, hält Kaggle bei den Punkten am meisten zurück und verliert die wenigsten
  Units auf Punktefeldern.
- **Punktefelder hält er schlechter als R3:** 203–211 statt 251 Unit-Schritte je Match, obwohl sein Gedächtnis im
  Mittel sogar etwas mehr Punktefelder kennt (Dev A: 15,4 statt 14,1). Wahrscheinlicher Grund: Kaggle entscheidet nach
  seinem eigenen Wissen über Punktefelder, das der Schüler nicht sieht. Gängige Wege zu Punktefeldern lernt er deshalb
  nur unscharf.
- Schüsse auf eigene Units bleiben bei allen Varianten die häufigste Todesursache (etwa 11 je Match, Kaggle 2–6).
- 30 Karten sind wenig. Der Unterschied zwischen P8 und P9 (22 gegen 10 Matches) liegt im Zufall. Die Entscheidung
  fällt erst auf Dev E ([Plan](PLAN.md)).

Rohdaten: `../r3t_20261117/diag_r3_v2`, `diag_schueler_ens8`, `diag_student_ens8`, `diag_student_ens9`
(`matches.csv`, `deaths.csv`, `games.csv`).

## Nachtrag 17.11.2026, 17:05: der empfohlene Kandidat auf denselben Karten

Dieselbe Diagnose für den reinen Schüler v9 mit Stay-Bias 1,0 und Halter-Regel (`--agent
"student:ens9:imit_stay_bias=1.0,imit_hold_points=true"`), verglichen mit P9 (Stay-Bias 1,5) und R3, je 180 Matches:

| | R3 | P9 | Kandidat |
|---|---:|---:|---:|
| gewonnene Matches | 6 | 10 | 12 |
| eigene Punkte / Kaggle-Punkte je Match | 195 / 377 | 180 / 301 | **190 / 303** |
| eigene Tode / Kaggle-Tode | 24,2 / 2,8 | 16,8 / 8,5 | 17,2 / 8,4 |
| Unit-Schritte auf Punktefeldern (eigene / Kaggle) | 251 / 405 | 203 / 333 | 214 / 334 |
| Energie für Bewegungen je Match | 1.870 | 1.991 | 1.912 |

Die schwächere Stehstrafe und die Halter-Regel bringen etwas mehr Punkte und mehr Zeit auf Punktefeldern bei
weniger Bewegungskosten. Die große Lücke bleibt: Kaggle holt weiter rund 300 Punkte je Match gegen unsere 190 und
besetzt in den letzten 10 Schritten jedes Matches 8 Felder gegen unsere 3
([Punktefelder](PUNKTEFELDER.md), Rohdaten `punktefelder/student_ens9_s10h.csv`, `../r3t_20261117/diag_student_ens9_s10h/`).
