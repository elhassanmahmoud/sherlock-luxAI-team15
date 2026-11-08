# Enger unabhängiger Review der Launcher-Korrektur

**PASS_STATIC – keine Blocker in der geprüften Korrektur.**

08.11.2026. Nur Quelltext, Diff und bestehender Fehlerbeleg gelesen; keine eigenen Imports, Tests, Modelle, Spiele oder Repoänderungen. Die Prüfung beschränkt sich auf die macOS-Startidentität und ihre Regressionstests, nicht auf eine erneute vollständige Task3-Abnahme.

## Geprüfte Bindungen

| Datei | selbst geprüfter SHA-256 |
|---|---|
| `scripts/sampled_target_supervisor.py` | `e6d5bb238fe0fd4d27f00c103ec4824f04c01ce3b7a5cd51297b877c5a1bb443` |
| `tests/test_sampled_target_study.py` | `ef5ee98e0cba3ec57650130ee622e87735d2349c9c5b3abbd52d2af43425ad92` |
| unveränderter Worker `scripts/sampled_target_study.py` | `40d18c9a8ad8c3ef9b497ce260b533a93e2581a6c7c158a06712d89537aee224` |
| `operations/technical_v1_failure.json` unter `experiments/analysis/sampled_target_20261108/` | `7ac46fe69712f11cb71993c6273992f7316816fa082a92ee02173f4577d03121` |

Der versiegelte Fehlerbeleg bezeichnet v1 als `CLOSED_FAILED_BEFORE_MODEL`, verzeichnet null gestartete/abgeschlossene Spiele, null Updates sowie alle eigenen Prozesse beendet. Root berichtet dazu den separaten Stdlib-Reproduktionslauf: macOS schreibt lediglich `sys.orig_argv[0]` auf den Framework-App-Pfad um; `sys.executable`, Argumentrest und Prozessidentität stimmen. Diesen Prozesslauf habe ich nicht selbst wiederholt.

## Bewertung

`worker_guard` Zeilen92–103 bindet den angeforderten Interpreter jetzt über **exakte Gleichheit von `sys.executable` und `expected[0]`**. `sys.orig_argv` muss eine Liste gleicher Länge sein; sämtliche Elemente ab Index1 müssen exakt dem registrierten Befehl entsprechen. Nur `orig_argv[0]` wird nicht mehr als Interpreteridentität verwendet. Es gibt weder Pfadnormalisierung noch allgemeinen Interpreter-/Befehlsfallback.

Die bestehenden Bedingungen für aktive Rolle, eigene PID, PID=PGID, Parent/Owner und vollständig identischen gespeicherten Startbefehl bleiben erhalten. Pfad-, STOP-, Peerregistrierungs- und Quellenprüfungen sind unverändert. Der Fix verändert keine Spiel-, Lern-, Replay- oder Freigabelogik.

Die Regression in `test_worker_ownership_registration_is_bounded_and_exact` akzeptiert den konkret beobachteten Framework-argv0 bei richtigem `sys.executable` und verwirft einen falschen Interpreter trotz unverändertem argv. Vorhandene falsche PID/Befehlsregistrierung und Peer-Timeout bleiben Negativfälle. Root meldet den tatsächlichen RED-Nachweis mit2 FAIL/4 PASS und anschließend den gemeinsamen Lauf mit125 PASS in3,42s, Exit0. **Keine eigene Testausführung durch diesen Reviewer.**

Eine separat dokumentierte technische Aufnahme v2 mit neuen Vorbereitung-/Ausgabeordnern bleibt Root-Aufgabe. Der alte Fehlerbeleg, Zustand und STOP-Verlauf sind historisch zu erhalten. Da v1 null Spiele startete, erweitert die noch ausstehende feste Vier-Spiel-Technikphase den vereinbarten Spielumfang nicht. Dieser Review startet sie nicht und behauptet keine erfolgreiche reale Integration.
