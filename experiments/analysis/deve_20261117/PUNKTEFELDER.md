# Punktefelder gegen Kaggle: kennen, besetzen, liegen lassen (17.11.2026, nur Messung)

Je 20 Spiele gegen den Kaggle-Dritten auf den Analysekarten 7256000–7256009 (beide Seiten). In jedem Schritt wurden
die echten Punktefelder der Engine mit dem Gedächtnis des Agenten und mit der Besetzung beider Teams verglichen
([Skript](punktefelder.py), Rohdaten in `punktefelder/`). Auf diesen Karten gibt es im Mittel 16,6 Punktefelder, davon
8,1 auf unserer Kartenhälfte. Werte je Schritt:

| Agent | Abschnitt | bekannt | von uns besetzt | von Kaggle besetzt | bekannt und leer | davon auf unserer Hälfte | eigene Units ohne Aufgabe* | Kaggle auf unserer Hälfte |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| R3 | Match 2, Schritt 31–70 | 67 % | 2,7 | 3,8 | 5,3 | – | – | – |
| R3 | Match 3, Schritt 31–70 | 84 % | 3,8 | 4,4 | 6,1 | – | – | – |
| R3 | Match 3, Schritt 91–100 | 89 % | 2,1 | **10,3** | 3,5 | – | – | – |
| R3 + Schüler v8 | Match 2, Schritt 31–70 | 62 % | 2,8 | 3,3 | 5,1 | 2,4 | 8,5 | 0,3 |
| R3 + Schüler v8 | Match 3, Schritt 31–70 | 89 % | 3,6 | 4,1 | 7,1 | **3,5** | 8,0 | 0,2 |
| R3 + Schüler v8 | Match 3, Schritt 91–100 | 93 % | 2,1 | **9,7** | 4,2 | 2,8 | 5,1 | 3,0 |
| reiner Schüler v8 | Match 2, Schritt 31–70 | 68 % | 2,1 | 2,9 | 6,6 | 3,4 | 9,2 | 0,2 |
| reiner Schüler v8 | Match 3, Schritt 31–70 | 93 % | 3,0 | 3,4 | 9,1 | **4,6** | 9,5 | 0,2 |
| reiner Schüler v8 | Match 3, Schritt 91–100 | 97 % | 3,3 | **7,9** | 5,2 | 3,2 | 6,6 | 1,8 |

\* weder auf einem Punktefeld noch ein Gegner im Umkreis von 3 Feldern (Chebyshev).

## Was man daraus lernt

1. **Wissen ist nicht das Problem.** Ab dem zweiten Match kennt unser Gedächtnis zwei Drittel, im dritten Match fast
   alle Punktefelder; falsche Einträge gibt es praktisch nicht.
2. **Wir lassen bekannte Punktefelder auf der eigenen Hälfte leer.** Mitten im dritten Match sind dort 3,5–4,6
   bekannte Felder frei, Kaggle steht dort fast nie (0,2), und 8–10 eigene Units haben gerade keine Aufgabe. Jedes
   besetzte Feld bringt einen Punkt je Schritt.
3. **Kaggle drängt am Matchende.** In den letzten 10 Schritten besetzt Kaggle 8–10 Felder, davon 2–3 auf unserer
   Hälfte, und unsere Besetzung fällt. Die meisten eigenen Tode fallen in die Schritte 61–100
   ([Diagnose](DIAGNOSE.md)).

## Was daraus gebaut wurde

- `imit_fill_points` (agents/sherlock/imitation_agent.py): freie bekannte Punktefelder bekommen die nächste eigene Unit
  ohne Schuss und ohne eigenes Punktefeld.
- `imit_hold_points`: der erste Halter eines bekannten Punktefelds wird nicht fürs Stehenbleiben bestraft.
- Getestet im vorab festgelegten [Dev-F-Vergleich](../devf_20261117/PLAN.md).

Mit beiden Schaltern aus spielt der Schüler unverändert: Die Messung des reinen Schülers ergab vor und nach dem Einbau
dieselben 600 Zeilen.
