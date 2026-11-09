# Matchgewicht-Studienrunner: Implementierungsbeleg

Schreibbereich ausschließlich `scripts/match_weight_study.py` und `tests/test_match_weight_study.py`. Keine produktiven Agent-/Config-/Rewardänderungen, keine Commits, keine echten Modellarchive, Spiele oder Trainings. Basis HEAD 4e23cebae531b7d18f7f5caa01b018db7fd59a72; Root und Owner arbeiten in getrennten Bereichen.

## Ergebnis

Fester direkter Ablauf um den unveränderten Agent_x/common.play_game: Originalmitglied 18, zwei Starts 48/49, Gewichte 2/20, je 40 Vorlauf + 400 Lernspiele. Instanzlokaler tatsächlicher buffer.push-Beobachter prüft Originalformeln, UID-Reihenfolge, finale kanonische Labels, nächste Features/Masken/Terminals und den wirklich gespeicherten Float32-Wert. Bestehender action_audit prüft zusätzlich native Aktionen einschließlich kanonischer Spiegelung. Formelkontrast unverändert abs_tol 1e-10 / rel_tol 1e-12; Offlinewerte berücksichtigen die konkret berechnete Float32-Quantisierung. Gültige finale Regelaktionen außerhalb der Netzmaske werden gezählt, nicht verworfen.

Feste Aufnahme mit Rollenconfigs, sieben flachen Kartenkohorten, Quellen-/Eingabe-/V14-/ZIP-Bindung und exaktem Owner/Worker-argv. Genau eine Env pro Worker, sichere Behandlung von STOP/Signal am Spielende und eigener incomplete-Checkpoint. Root-Freigabe bindet beide erhaltenen Vorläufe, Start, Aufnahme, Quelle und Root-Review; der Worker erzeugt niemals selbst eine Freigabe. Paar 49 verlangt einen akzeptierten Paar-48-Abschluss.

Technik archiviert vier komprimierte Outcome-/Originalreward-Arrays mit Dateihashes. Vorlauf archiviert beide Originalrewardströme, geordneten vollständigen Replay und unveränderten Checkpoint. Finalvalidator prüft 440 Spiele, 60.000 tatsächliche Adamupdates, 193.320 Envschritte, geänderte endliche Gewichte, Verlustwerte, endgültigen Replay und die manuelle Freigabe. Keine interne Validierung oder Modellwahl.

## Tatsächliche Prüfung

Aufruf: `PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_match_weight_study.py`.

- `red-1.log`: 14 erwartete Einrichtungsfehler, weil das Studienmodul noch nicht existierte.
- `green-1.log`: 14 PASS.
- `green-2.log`: 21 PASS, einschließlich Vorlaufarchiven/manueller Freigabe und Env-/Abbruchverhalten.
- `red-2.log`: 3 FAIL / 19 PASS für die konkreten Root-Ergänzungen (flache Kohorten, archivierte Technikarrays, Gegnerfehler).
- `green-3.log`: 22 PASS in 2,93 s; abschließender enger Prüflauf.

Tests verbieten echte torch.load und common.play_game. Für den Archivvertrag wird torch.save/load ausschließlich durch einen künstlichen In-Memory-Beleg ersetzt; die npz-Testdaten sind klein und synthetisch. Keine neue breite Suite ausgeführt.

## Grenzen und Anschluss

Die echten 36 Quellnetze, Lux-Ausführung, ursprüngliche Kartenexposition und tatsächlichen Endarchive sind absichtlich noch nicht ausgeführt/geprüft; dies gehört zur getrennten Root-Aufnahme nach unabhängigem Review. Technik- und Vorlauf-Rewardarrays erlauben numerische Offlineprüfung. Nach Lernbeginn werden die vollständigen Kontextdaten nicht archiviert: dort sind Originalformeln/Replaylabels live geprüft und pro Spiel geordnet gehasht; der finale Replay ist vollständig erhalten, aber die ursprünglichen Rewardkontexte sind daraus allein nicht rekonstruierbar. Keine Aussage zur Spielstärke.

Owner-API: stage `technical|pair48|pair49`, start `48|48|49`; ARMS `control|match`; `admission`, `output_dir`, `worker_command`, `check_technical(receipt)` und `validate_final_receipt(path,a,sha,role)`. `waiting.json` bleibt als historischer Beleg erhalten. Alle Details stehen im überprüfbaren Code.
