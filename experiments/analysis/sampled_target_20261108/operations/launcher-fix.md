# Technischer Startfehler und eng begrenzte Korrektur

08.11.2026, Root. Der erste technische Start unter `a7e42037dd26774e556aac3f7513c927596bcc72` endete vor Konstruktion eines Learners und vor Erstellung eines Runverzeichnisses. Beide ersten Worker wurden von ihrer eigenen Befehlsprüfung zurückgewiesen. **Null gestartete oder abgeschlossene Spiele, null Lernupdates.** Das zweite Seitenpaar wurde nicht gestartet. Supervisor, beide Worker und Wachhalter sind nachweislich beendet; der fehlgeschlagene Zustand und beide Fehlerlogs bleiben unter `../technical_v1/` erhalten.

Root hat vor Aufhebung der fehlgeschlagenen Quellensperre 397 Datei-/Eingabe-/Schutzbindungen geprüft und den Abschluss unter `technical_v1_failure.json` festgehalten (SHA-256 `7ac46fe69712f11cb71993c6273992f7316816fa082a92ee02173f4577d03121`). Der ursprüngliche STOP ist zusätzlich bytegleich unter `technical_v1_STOP` erhalten. Historische Quellen-/Pfadbindungen beschreiben diesen damaligen Stand; spätere Korrekturen sind nicht dessen Laufquelle.

## Tatsächlich reproduzierte Ursache

Eine einzelne reine Standardbibliotheks-Prozessprobe benutzte denselben `os.execvpe`-Startweg, ohne Projektimport, Modell oder Spiel. Parent38538/Child38539: PID, Prozessgruppe und Elternprozess passten. `sys.executable` entsprach exakt dem verlangten Venv-Python. macOS ersetzte jedoch `sys.orig_argv[0]` durch `/Library/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python`; alle folgenden Argumente waren identisch. Deshalb war der bisherige vollständige Listenvergleich falsch.

Die Korrektur bindet den Interpreter ausdrücklich über `sys.executable`, die übrigen Argumente weiterhin vollständig und zusätzlich unverändert registrierten Befehl, PID, Prozessgruppe, Elternprozess und Studie. Keine Änderung an Lernziel, Agent, Regeln, Rewards, Karten oder Gewichten.

## Tatsächliche Tests

Interpreter `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python`, Studiencheckout, jeweils `-B -m pytest -q`:

- RED: `tests/test_sampled_target_study.py -k worker_ownership_registration`: Exit1, zwei Fehler, vier bestanden,66 abgewählt,2,55s. Reproduzierte Mac-Startablehnung und fehlende separate Prüfung eines falschen `sys.executable`.
- GREEN nach enger Korrektur: `tests/test_sampled_target_agent.py tests/test_sampled_target_study.py`: Exit0, **125 bestanden in3,42s**. Keine echten Spiele oder Lernupdates aus diesen Tests.
- Supervisor SHA-256 `e6d5bb238fe0fd4d27f00c103ec4824f04c01ce3b7a5cd51297b877c5a1bb443`; Testdatei `ef5ee98e0cba3ec57650130ee622e87735d2349c9c5b3abbd52d2af43425ad92`. Studienworker unverändert `40d18c9a8ad8c3ef9b497ce260b533a93e2581a6c7c158a06712d89537aee224`.

## Gesonderter Root-Technikentscheid

Der [unabhängige enge Fixreview](launcher-review.md) ist abgeschlossen: PASS_STATIC, keine Blocker, geprüfte finale Hashes unverändert. Keine eigenen Test-/Spielausführungen des Reviewers.

Nach unabhängigem Fixreview und Commit wird eine neue technische Aufnahme mit neuem vorbereiteten Ordner `20261108_sampled_target_technical_prepared_v2` und Ergebnisordner `technical_v2` gebunden. Die alte Vorbereitung, Aufnahme und fehlgeschlagenen Ergebnisse bleiben erhalten. Erst dann darf Root den archivierten STOP dieser eindeutig diagnostizierten Stufe entfernen und einmal neu starten; keine automatische Wiederholung.

Es bleiben exakt die ursprünglichen vier Technikspiele auf Karte4242, Modi×Seiten, null Gradienten. Da v1 keines begonnen hat, erhöht sich der festgelegte Spielumfang nicht. Ein neuer Fehler sperrt die frische Studie erneut und benötigt eine weitere ausdrückliche Root-Diagnoseentscheidung. Keine ausstehende Frischstudie oder erfolgreiche Technikabnahme aus diesem Dokument ableiten.
