# Combined actual independent reviews for technical v2

Original Task3 review followed by the narrow macOS launcher correction review. No new test claim from this compilation.

# Unabhängiger statischer Task3-Review

**Ergebnis: PASS_STATIC – keine konkreten Blocker in der geprüften Fassung.**

08.11.2026. Ausschließlich lesende Prüfung im Studiencheckout bei HEAD `49104d138aa82662bb1610fe8db3d6cda0e1fa44`. Keine Imports, Tests, Modelle, Spiele oder Git-/Repoänderungen durch diesen Review. Dieser Befund ersetzt weder die Root-Aufnahme noch die noch ausstehenden vier echten technischen Integrationsspiele und ist kein Laufzeit- oder Wirkungsnachweis.

## Geprüfte Fassungen

SHA-256, selbst aus den tatsächlich gelesenen Repo-Dateien ermittelt; die drei Implementierungshashes stimmen mit der vom Implementer eingefrorenen Fassung überein:

| Datei | SHA-256 |
|---|---|
| `scripts/sampled_target_study.py` | `40d18c9a8ad8c3ef9b497ce260b533a93e2581a6c7c158a06712d89537aee224` |
| `scripts/sampled_target_supervisor.py` | `df85b767962cffc9c903da86b4ac4f539143ef7b0b0faa24f21e017c2687d07d` |
| `tests/test_sampled_target_study.py` | `ea0c80d1c7c8cf8e89bf130cc7fbad0088c0a1bf8ec83e5d41bd4934d3ce8469` |
| `docs/superpowers/specs/2026-11-08-sampled-target.md` | `0b3e86ca7e1ca2559f9001343f8c8073127d5d46c363ec761500964e8ae91a2d` |
| `docs/superpowers/plans/2026-11-08-sampled-target.md` | `2649209104db363c8b5fb0efcfdf6cb5ccaf8a4de27957abe86159f351b44d34` |

## Wesentliche Prüfpunkte

- **Technik vor Frischstudie:** `technical_plan`, `validate_admission`, `validate_technical_receipt` und `compare_technical_receipts` binden genau Kontroll-/Sampled-Modus × beide Seiten auf bekannter Karte4242 gegen default, Anker45, jeweils303 Schritte und null Updates. Die Studienaufnahme verlangt vier geprüfte technische Receipts und beide Seitenvergleiche; keine automatische Weiterleitung vom technischen Supervisor in das Training.
- **Fester Umfang:** Vier Arme, Starts45/46, jeweils40 Vorlauf- und160 Lernspiele mit identischer exogener Paarfolge und getrennten festen Kartenkohorten. Die Endprüfung verlangt200 Spiele,24.000 Updates und120.600 Env-Schritte pro Arm. Task4-Leistungsspiele werden hier weder gestartet noch als bestanden dargestellt.
- **Folgeaktion und Replay:** `EventValidator`, `validate_stream` und `validate_phase_bundle` prüfen Capture-/Commit-Reihenfolge, eindeutige Übergänge, spätere bestätigte Framebindung derselben Unit/Episode/Matchgrenze, kanonisches Label, Features/Masken und Zählerzeitpunkt. Terminalzeilen verwenden die festgelegten Sentinels. Der komplette Vorlauf wird mit gespeicherten Replayzeilen verbunden; beim Endpuffer werden alle gespeicherten Ringzeilen gegen das vollständige Ereignisprotokoll geprüft. Keine Gleichsetzung eingereichter Befehle mit garantierter Enginewirkung.
- **Paargate vor Gradienten:** Beide vollständigen Vorläufe müssen einschließlich Trajektorien, Rewards, Replay, RNG und unveränderter Q-/Target-/Adam-Zustände übereinstimmen. Die deterministische Diagnose benötigt mindestens eine Index- und eine Targetwertabweichung und prüft unveränderte Lern-/RNG-/Replayzustände. Worker lesen die Rohbelege erneut, bevor `learn_enabled` gesetzt wird. Die native Aktionskette und `_update` werden nicht kopiert; produktive Coredateien bleiben außerhalb der Änderung.
- **Atomare Bereitschaft:** `write(exclusive=True)` serialisiert vorab, schreibt und synchronisiert die temporäre Datei und veröffentlicht sie exklusiv mit `os.link`. Der zugehörige Test deckt den Serialisierungsfehler und Überschreibschutz ab. Auch das Paargate wird erst vollständig veröffentlicht.
- **Betrieb und Abbruch:** Quellen-/HEAD-/Plan-, Eingabe- und V14/ZIP-Bindungen, frischer Kontingentbeleg, AC, Threads1, Fremdprozessprüfung und maximal zwei registrierte Worker sind vorgesehen. Startregistrierung ist zeitlich begrenzt und an PID/PGID/Parent/Befehl gebunden. Paare laufen nacheinander. Fehler führen zu STOP/unvollständigem Status; der wiederverwendete Cleanup signalisiert ausschließlich eigene Prozessgruppen. Kein automatischer Wiederholungsweg.

Die synthetischen Tests wurden vollständig als Text geprüft, insbesondere falsche Labels/Replayfelder, unvollständige Ereignisse, Nullintervention, fehlerhafte Aufnahme, feste Technikbefehle, Markerpublikation, Eigentumsregistrierung und Cleanup. **Dieser Reviewer hat keine Tests ausgeführt.** Root und Implementer melden separat den finalen gemeinsamen Lauf mit123 bestandenen Tests in3,19s; deren Ausführung wird hier nicht als eigene Prüfung ausgegeben.

Offen bleiben die ausdrücklich vorgesehenen realen Aufnahmebedingungen und technischen Integrationsbelege. Aus dem statischen Task3-Scope ergibt sich kein zusätzlicher Änderungsbedarf.


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
