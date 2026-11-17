# Vergleich auf Dev E: mehr Schüler gegen Kaggle (festgelegt am 17.11.2026, 11:15, vor dem ersten Spiel)

**Freigabe:** Mahmoud hat am 17.11. den ganzen Tag für neue Lösungen gegen Kaggle freigegeben („hast von mir alle
Go's“, „wir brauchen Fortschritt“). R3 bleibt die Abgabe, bis Mahmoud und Moayed gemeinsam anders entscheiden.

## Warum dieser Vergleich

- Die frische Bestätigung von R3 + Schüler (Ensemble v8 + v8L) verfehlte die Regel um ein Spiel. Der Punkteanteil
  gegen Kaggle stieg aber um 3,5 Prozentpunkte, und die gewonnenen Matches gegen Kaggle stiegen von 84 auf 124 von
  2.400 ([Ergebnis](../r3t_20261117/BESTAETIGUNG_ERGEBNIS.md)). Dieser Kandidat (S8) bekommt keine zweite
  Bestätigung.
- Die [Diagnose](DIAGNOSE.md) auf 30 Analysekarten zeigt: Der reine Schüler (alle Units) gewinnt gegen Kaggle die
  meisten Matches und drückt Kaggles Punkte am stärksten. Punktefelder hält er dagegen schlechter als R3.
- Seit 11:04 gibt es das Ensemble v9 + v8L nach DAgger-Runde 6 ([Ergebnis](../umbau_20261115/v9/ERGEBNIS.md)).

## Wer antritt

| Name | Spieler | Rolle |
|---|---|---|
| R3 | unverändertes R3-Paket (`r3zip:`, SHA-256 `8aabdc73…a64d`) | Referenz |
| S8 | `r3t:schueler=ens8` | nur Vergleich (Bestätigung verbraucht) |
| S9 | `r3t:schueler=ens9` | Kandidat |
| S9H | `r3t:schueler=ens9,schueler_halter` (Halter und Units auf dem Weg zum Punktefeld spielen immer R3) | Kandidat |
| P8 | reines Ensemble v8 + v8L (`--set imit_stay_bias=1.5 --set imit_unstack=true`) | Kandidat |
| P9 | reines Ensemble v9 + v8L (gleiche Schalter) | Kandidat |

## Was gespielt wird

- **Dev E: 7258000–7258199** (200 Karten, bisher von niemandem benutzt), beide Seiten, gegen Solution und Kaggle:
  je Agent 800 Spiele, zusammen 4.800.
- Nur zur Information: jeder Kandidat und S8 direkt gegen R3 auf 7258000–7258049 (je 100 Spiele).
- Eingefrorene Quelle per `git archive`, 10 Prozesse, streng nacheinander, keine Trainings parallel
  ([Skript](run_deve.sh)).

## Vorab festgelegte Auswahlregel

Gepaart nach Karte gegen R3 (beide Seiten zusammen, 10.000 Ziehungen, Seed 2711, [Auswertung](analyze_deve.py)).
Ein Kandidat (S9, S9H, P8, P9) **besteht**, wenn alle drei Bedingungen gelten:

1. **Punkteanteil gegen Kaggle:** Mittel mindestens +2,0 Prozentpunkte und untere 95-%-Grenze über 0.
2. **Gewonnene Spiele gegen Solution:** Mittel nicht unter −1,0 Prozentpunkt.
3. **Technik:** kein abgefangener Fehler, alle Spiele über 303 Schritte.

Von den bestehenden Kandidaten geht der mit dem höchsten Punkteanteil gegen Kaggle in eine frische Bestätigung. Liegen
zwei höchstens 0,5 Prozentpunkte auseinander, entscheidet die Zahl der gewonnenen Matches gegen Kaggle. Besteht kein
Kandidat, gibt es keine Bestätigung, und R3 bleibt die Abgabe. Die Regel der Bestätigung wird vor dem Ende dieses
Vergleichs getrennt festgelegt. Dev E wird danach für keine Auswahl mehr benutzt.
