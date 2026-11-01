# Abschließender unabhängiger Code-/Spec-Review

Basis `6cd0403` plus uncommittete Nachtimplementierungen in `sherlock-v10-mechanics`; historische V14-Baseline `93a2ddd`. Overlap, Pilot, Tests, Evaluationsjournal, Schattenprobe und Trainingssupervisor samt Lade-/Trainingspfaden read-only geprüft. Keine eigenen Tests/Modelljobs gestartet, keine Quellen geändert.

**Urteil nach abschließender Nachprüfung:** Keine offenen Blocker im geprüften Umfang. Beide P1-Ausführungslücken und beide P2-Abschlussbedingungen sind im aktuellen Code geschlossen. Die integrierte Volltestsuite läuft zentral bei Root; dieser Bericht behauptet keinen eigenen Testlauf oder bereits belegte Spielstärke.

## Geschlossene Befunde

- `run_jobs.py:64–82,98–99` leitet jetzt die tatsächlich verwendeten Gewichte, self-/ppo-Gegner, CNN- und impliziten DQN-Dateien ab und verlangt Existenz sowie Freeze-Zugehörigkeit. Damit verhindert der Runner den vorher möglichen stillen untrainierten Ersatzgegner. Der neue Regressionstest prüft fehlende und nicht eingefrorene Inputs ohne Lux-Spiele.
- `probe_overlap.py:23–27,81` verlangt vor Laden und nach Diagnose exakt die eingefrorene V14-Datei. Kein stiller Zufallsstart mehr.
- `run_jobs.py:137–155` kontrolliert laufend AC, Quellen und Deadline, behandelt SIGTERM und räumt mit begrenztem TERM→KILL auf. Trainingssupervisor verhindert neue lange Starts nach 05:00, begrenzt die Pollwartezeit auf die Restzeit und startet genau zwei getrennte Childgruppen.

## Inhaltlich ohne gefundenen Blocker

- **Overlap:** Die Extremfall-Algebra ist für gültige binäre Gleichungen korrekt; bekannte Punkte/Nullfelder werden normalisiert, direkte/symmetrische Konflikte verworfen. Höchstens 400×16 Eingaben und zwei Aggregatgleichungen. Anwendung außerhalb des Spawnfensters; bestehende Match-/Game-Resets löschen Records. Flag-aus-Diff semantisch unverändert. Die gelesenen Tests enthalten unabhängige exhaustive Vier-Feld-Wahrheit, Symmetrie, Reset, Widersprüche und Cap. Reale Flag-aus-Aktionskompatibilität und zusätzliche korrekte Trace-Fakten bleiben geplante Zulassungsvoraussetzungen.
- **Pilot:** Index 18 ist `ensemble[17]`; strikter QNet-Loader, q-/target-Tensorhash und getrennte Klone; keine Ensemble-/Optimizer-/Replay-Übernahme. Adam entsteht frisch. Die explizite Variant-Config erreicht den echten Learner; nur `w_discovery` unterscheidet die Arme. V12-Trainingsschalter aktiv, Rescue weiterhin eval-only. Registry/argv werden zurückgesetzt; Quelle/Init ausschließlich gelesen und gehasht. Roots realer Warm-Start-Beleg bestätigt q/target, null Optimizerzustände und keine Extranetze.
- **Schattenprobe:** Belief-Kopie nach Seiten-/Game-Reset, gleiche Beobachtungen, Sensorreichweite, kanonische Orientierung und übrige Schalter. Nur Overlap ist zusätzlich aktiv. Engine-Wahrheit validiert anschließend neue Fakten; sie ändert weder aktiven Belief noch Aktionen. Falsche zusätzliche Fakten führen zum Fehler.
- **Evaluationsbeleg:** Erwartete vollständige Seed/Seite/Gegner-Schlüssel, keine Duplikate, 303 Schritte, v2, endliche Werte und konsistente Sieg-/Punktwerte werden verlangt; vollständige CSV erhält einen Hash. Keine Auswahl-/Releaseautomatik im Runner.

## P2-Befunde nach Nachprüfung ebenfalls geschlossen

1. **Endzeit:** `run_training.py:65` verlangt nach dem Ende beider Childprozesse ausdrücklich `time.time() <= deadline`, bevor Erfolg möglich ist. Damit kann ein gerade nach Deadline beendeter Arm nicht mehr als vollständiger zulässiger Lauf gelten.
2. **Trainings-CSV:** `validate_training_pair()` in `run_training.py:11–28` verlangt pro Arm genau 600 geordnete Spiele, `game=0..599`, Seed `294200+g//2`, korrekte alternierende Seite, 303 Schritte und Punktezählung v2; beide vollständigen Gegnerfolgen müssen gleich sein. Beide CSV-Hashes werden erfasst. Der Supervisor journalisiert diesen Nachweis in Zeilen 73–75 **vor** `status=complete`.

Alle vier Befunde wurden durch erneute Codelektüre nach den Korrekturen geschlossen. Kein eigener Modelljob, Test oder Quellen-/Gewichts-Freeze durch diesen Reviewer gestartet. Reale Aktionskompatibilität, Diagnosenutzen, Laufvollständigkeit und Stärkenbestätigung sind weiterhin vor einer Kandidaten-/Abgabeübernahme anhand ihrer tatsächlich erzeugten Belege zu prüfen.
