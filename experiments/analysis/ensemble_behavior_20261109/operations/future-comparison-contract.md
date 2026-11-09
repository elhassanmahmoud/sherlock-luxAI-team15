# Bauhinweise für die feste BEHAVIOR38-Auswahl

Nur Quellen und bereits abgeschlossene Referenzmetadaten gelesen. Keine laufenden Trainingsresultate, Modellladungen, Tests, Spiele, Aufnahme oder Projektänderung. Umsetzung erst nach vollständiger Root-Trainingsabnahme und Ende des Freeze.

## Direkt verwendbare Bausteine

| Aufgabe | Vorhandene Funktion und Grenze |
|---|---|
| Ursprüngliche Inferenzconfig | [`match_weight_compare.inference_config(source)`](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/scripts/match_weight_compare.py:130): normalisierte originale V14-Config, `frozen=False`. Keine Trainingsconfig, kein Behavior-Hook in der Evaluation. |
| Montage | `match_weight_compare.mount(source, [final48, final49])`: unveränderte ursprüngliche 36, danach q aus on48 und on49. Die Ersetzung an Index 18 gilt **nur während Training**; hier bleibt das ursprüngliche Mitglied 18 erhalten, insgesamt genau 38. |
| Tatsächlicher Lader | `match_weight_compare.validate_and_load(path, cp, expected)`: komplette Tensor-/Dimensions-/Configgleichheit, normaler `Agent_x`-Evalpfad, 1/8/16 synthetische Batchgrößen. Wiederverwendbar in einer separat aufgenommenen Montagephase mit **null Spielen**. |
| Spiele | [`par_eval`](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/scripts/par_eval.py) unverändert mit `--workers 1`, festem `--seed-list`, ohne `--set`; ein Solution-Gegner oder `self:<gebundener Modellpfad>`. Beide Seiten automatisch, Originaleval und Fehlerprüfung beider Agenten. |
| Rohdaten und Statistik | `compare_report.validated_results`, `compare_results` sowie `league_gates.direct_result` direkt importieren. Paarung über Gegner/Karte/Seite, beide Seiten als Kartenblock; 5000 Ziehungen, Seed 0, im gebundenen NumPy PCG64, 95%-Perzentile. |
| Betrieb | `compute_lock`, `spawn_owned`, `guard`, `shutdown_owned`, `safe_path`, `save_state`, exklusives `write` sowie [`match_weight_compare_owner.await_group_exit`](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/scripts/match_weight_compare_owner.py:11). Fünf Jobs in Wellen 2+2+1, höchstens zwei rechnende Worker. |

Die vollständigen alten `admission`, `accepted_training`, `job_spec`, `validate_csv`, `analyze` und Owner-`main` sind profil-/rollengebunden. Sie lassen sich nicht unverändert durch globale Umbenennung von `match` wiederverwenden. Benötigt werden nur schmale neue Bindungen/Jobtabellen und die bestehenden CSV-Invarianten: exakt 40 eindeutige erwartete Zeilen, richtige Gegnerpfade/Karten/beide Seiten, 303 Schritte, Punktzählung v2, konsistente ganzzahlige Matchpunkte/-siege und result/game_win/point_win. Keine neue Simulations- oder Statistikplattform.

## Neue Abschlussbindung

Nach echter Abnahme einen gehashten Root-Abschluss des Profils `ensemble_behavior_20261109` konsumieren; dessen endgültiges Schema erst am tatsächlichen Abschluss festmachen. Er muss ursprüngliche Trainingsaufnahme, Quelle 71090f7, vollständigen Ownerzustand, beide Receipts/Finaldateien und unabhängige Abnahme binden: Jobs genau on48/on49, beide Exit 0, Owner complete/active leer; insgesamt 4 Technik-, 80 Vorlauf-, 800 Lernspiele, 120000 Updates. Keine `incomplete.pth`, keine Zwischenwahl.

Je Final: Originalstart 48/49, 440 Spiele, env_steps 193320, learn_steps 60000, 79/6, leeres Ensemble und passende ursprüngliche Kontrollconfig. Checkpointmetadaten heißen **`behavior`**, nicht das frühere `match_weight`; Receipt hat `role=on48|on49`, `behavior="ensemble"`, ursprüngliche Admission/Quelle und reale q-/Target-/Adamidentitäten. [`ensemble_behavior_study.validate_final_receipt`](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/scripts/ensemble_behavior_study.py:537) ist für die Abschlussprüfung mit der **historischen** Aufnahme verwendbar. Danach reichen im Vergleich die versiegelten Bindungen plus Prüfung der tatsächlich montierten Endtensoren; nicht nochmals die Trainingsadmission gegen den neuen Vergleichs-HEAD ausführen.

Neue Vergleichsquelle separat pinnen; alle bisherigen Runtime-/Interpreter-/Enginebytes als unveränderte Untermenge prüfen, zusätzliche Dateien und neuer HEAD zulassen. Dies entspricht dem Bindungsprinzip von `match_weight_confirmation.accepted_selection`; dessen komplette Funktion wäre hier falsch, weil sie MATCH38-Nominierung, andere Modellrollen und die alte Auswahl voraussetzt.

## V14 und CONTROL38 wiederverwenden

Die vorhandene [Montagereceipt](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/match_weight_compare_20261109/technical_v1/technical-receipt.json) weist bereits aus:

- `technical_v1/v14.pth`: `817e565f8628a3a860c3dcb84e69e9d68c5f0954f791fbd06e0f115bf6cf95d2`, 36 Mitglieder.
- `technical_v1/control.pth`: `b8118e6a8a5656a725fa407466833ebcef24d899f00c79e00b3f848086321a95`, 38 Mitglieder.

Diese Dateien unverändert über damalige technische Aufnahme, Root-Montageannahme und Receipt einschließlich aller Mitgliedshashes binden. CONTROL38 enthält die beiden vorab festen historischen Kontrollfinals, keine Auswahl nach dem neuen Verlauf. Nicht neu serialisieren, sofern die alten Bytes weiter passen. Neue Montageprüfung bestätigt gemeinsame originale 36 und dieselbe Inferenzconfig; nur BEHAVIOR38 muss neu montiert werden. Alte Kontroll-Spielresultate ersetzen **keine** der neuen 40 Ausführungen.

## Fester Lauf und Auswertung

| Job | Modell gegen Gegner | Karten | Spiele |
|---|---|---|---:|
| v14_solution | V14 gegen Solution | 9990000–9990019 | 40 |
| control_solution | CONTROL38 gegen Solution | dieselben | 40 |
| behavior_solution | BEHAVIOR38 gegen Solution | dieselben | 40 |
| behavior_v14 | BEHAVIOR38 gegen V14 | 9990100–9990119 | 40 |
| behavior_control | BEHAVIOR38 gegen CONTROL38 | 9990200–9990219 | 40 |

Die vorhandenen drei Kohorten-JSONs und `preparation/seed-acceptance.json` des Ensemble-Behavior-Profils samt `files`/dokumentierten Grenzen binden; kein neuer breiter Scan. Genau vier boolesche Gates aus der Spec: Solution-Siege mindestens V14 **und** mindestens CONTROL38; direkt jeweils mindestens **24 echte Siege/40**. Remis zählen nur im beschreibenden Score als 0,5. Keine unteren Intervallgrenzen oder Panelregeln aus der späteren MATCH38-Bestätigung übernehmen.

Vor Statistik alle 20 Karten je Vergleich nachweisen; die gemeinsamen Schnittmengen der Statistikhelfer dürfen keine fehlenden Fälle verdecken. Degenerierte Kartenintervalle wie im Confirmation-Bericht kennzeichnen, ohne neue Gates. Historische Kontrollen sind keine neuen unabhängigen Trainingsreplikate; wiederholte Projektselektion bleibt unbereinigt. Montage und Performance getrennt aufnehmen; kein automatischer Phasenwechsel, Nachschlag, Resume oder Promotion. Bestehen nominiert ausschließlich für eine später getrennt festgelegte Bestätigung.
