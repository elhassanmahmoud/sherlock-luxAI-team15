# Auftrag für Codex (ab 17.11.2026, mittags)

Geschrieben von Claude Code auf Mahmouds Wunsch („du kannst ihm immer neue Aufgaben geben“). **Starten nur durch
Moayed.** Ergänzt den Auftrag vom 16.11.; offene Punkte von dort gelten weiter.

## Ausgangslage (17.11., mittags)

- **Abgabe bleibt R3** (`experiments/releases/20261116_r3_finale/agent.zip`, SHA-256 `8aabdc73…a64d`).
- Mahmoud hat den Freeze heute früh aufgehoben und den Tag für Lösungen gegen Kaggle freigegeben.
- **R3 + Imitations-Schüler** (Units im Kampf und ohne Punktefeld-Aufgabe spielen den Schüler) hob den Punkteanteil
  gegen Kaggle in der frischen Bestätigung auf 7159000–7159399 um +3,5 Prozentpunkte und die gewonnenen Matches gegen
  Kaggle von 84 auf 124 von 2.400. Bei den gewonnenen Spielen fehlte genau eins (803 statt 804 von 1.600), deshalb
  nach Regel nicht bestanden ([Ergebnis](../experiments/analysis/r3t_20261117/BESTAETIGUNG_ERGEBNIS.md)).
- Der **reine Schüler** gewinnt gegen Kaggle die meisten Matches. Er lässt aber auf der eigenen Hälfte 3–4,5
  bekannte Punktefelder leer ([Diagnose](../experiments/analysis/deve_20261117/DIAGNOSE.md),
  [Punktefelder](../experiments/analysis/deve_20261117/PUNKTEFELDER.md)). Neue Schalter `imit_hold_points` und
  `imit_fill_points`.
- **Dev E (vorab festgelegt, 7258000–7258199):** Der reine Schüler v9 (Ensemble v9 + v8L) war am stärksten:
  Solution 394/400 (R3 387/400), **Kaggle 22/400** (R3 2/400), Matches gegen Kaggle 140 statt 54 von 1.200, direkt
  98/100 gegen R3 ([Ergebnis](../experiments/analysis/deve_20261117/ERGEBNIS.md)).
- **Frische Bestätigung auf 7260000–7260399 bestanden** (13:12): Solution 789/800 (R3 787/800), Kaggle 28/800
  (R3 16/800), Matches gegen Kaggle 236 statt 90 von 2.400, Punkteanteil gegen Kaggle +4,02 [+3,10; +4,92], direkt
  192/200 ([Ergebnis](../experiments/analysis/deve_20261117/BESTAETIGUNG_ERGEBNIS.md)). Kurspaket im Repo:
  `experiments/candidates/deve_20261117/agent_p9_reiner_schueler.zip` (SHA-256 `1579eb83…253f`, 9,5 MB, Format
  wie R3, Ladeprüfung bestanden). Danach laufen Dev F ([Plan](../experiments/analysis/devf_20261117/PLAN.md)) und
  die Robustheit gegen sechs weitere Spielweisen.

## Rahmen

- **Nicht ändern:** `agents/sherlock/weights/*`, `experiments/releases/20261116_r3_finale/*`, `dist/agent.zip`,
  `Gruppe15.zip`. Keine neue Abgabe ohne ausdrückliches Ja von Mahmoud und Moayed.
- **Heute nicht ändern** (Mahmouds Läufe bauen darauf auf): `agents/sherlock/imitation_agent.py`,
  `agents/sherlock/config.py`, `agents/sherlock_r3t/*`, `scripts/imitate.py`, `scripts/par_eval.py`,
  `scripts/build_r3t_package.py`, `scripts/build_student_package.py`. Befunde bitte als Datei.
- **Karten:** Codex weiter nur 7165000–7165999 und 7173000–7173399. Reserviert für Mahmoud: 7258000–7259999 (Dev E/F),
  7260000–7261999 (Bestätigungen), ab 7262000 (DAgger). 7159000–7159399 ist verbraucht.
- Vor jedem Push `git pull --rebase`; Ergebnisse getrennt von Code committen; Eintrag im Arbeitsstand.

## Aufgaben (in dieser Reihenfolge)

1. **Moayed, bitte entscheiden:** Der reine Schüler v9 hat die frische Bestätigung bestanden. Ein Wechsel von R3
   braucht dein ausdrückliches Ja zusammen mit Mahmouds. Bitte im Arbeitsstand oder direkt an Mahmoud melden.
2. **Nachspielen unter Python 3.10** (bei Mahmoud fehlt Python 3.10), wichtig vor einem Wechsel:
   `scripts/xversion_replay.py record experiments/candidates/deve_20261117/agent_p9_reiner_schueler.zip spiel.pkl
   --seed 4242` in der Projektumgebung, dann `python3.10 -I scripts/xversion_replay.py replay … spiel.pkl`. Erwartet:
   0 abweichende Aktionen. Dazu die Ladeprüfung des Kursrunners auf beiden Seiten (`scripts.build_submission.check`).
   Ergebnis nach `experiments/analysis/deve_20261117/PY310_CODEX.md`.
3. **Code-Review (nur lesen):** `agents/sherlock_r3t/` (Taktikschicht und Schüler-Mix), `scripts/build_r3t_package.py`,
   `scripts/build_student_package.py`, die Schalter `imit_hold_points` und `imit_fill_points` in
   `agents/sherlock/imitation_agent.py`. Schwerpunkte: Koordinaten (kanonisch gegen Welt, Spiegelung für player_1),
   Matchwechsel, gestorbene Units, Gleichheit zwischen gemessener Variante und Kurspaket. Befunde nach
   `experiments/analysis/deve_20261117/REVIEW_CODEX.md`.
4. **Präsentation:** Falls das Team wechselt, Vorschlag für Mahmouds Folien 4–7 mit dem neuen Agenten (Schüler lernt
   vom Kaggle-Dritten über DAgger, schießt wie Kaggle, neue Regeln für Punktefelder), Zahlen nur aus den
   Ergebnisdateien. Als Vorschlag kennzeichnen.
