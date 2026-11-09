# Fortschrittsabhängige Kandidatenrettung — Umsetzung

Umgesetzt ausschließlich in `agents/sherlock/config.py`, `agents/sherlock/main.py`, neuem `agents/sherlock/candidate_progress.py` (74 Zeilen) und `tests/test_candidate_progress_rescue.py`. Diffbasis `30800a71079c41754c02e3e9b5ccd2e000a09137`; kein Commit/Push und keine Gewichts-, Reward-, Ziel- oder Maskenänderung.

`cand_stall_rescue=False` ist der Default. ON erfasst den öffentlichen Verlauf nach dem originalen `_decide`, vor der bisherigen Leer-Unit-Rückgabe, einmal pro neuer Beobachtung. Kandidaten-, Punkt- und Nichtpunktmasken werden unabhängig kopiert. Nichtnegative Besetzung einer vorherigen Kandidatenkachel, eigener Punktzuwachs und neue Relic-/Punkt-/Nichtpunktinformation setzen das Alter zurück. Wissensrücknahme, ungültige Übergänge, Seiten-/Matchwechsel, fehlende Angaben und fehlende Einheiten beginnen konservativ neu; `new_game` und die ursprüngliche Matchreset-Rückgabe löschen den Verlauf. Keine Zeit vor dem gültigen Fenster wird rückwirkend angerechnet.

Erst nach zwölf vollständigen Übergängen ohne Fortschritt kann `_rescue_for` für ein aktuell gültiges Kandidatenziel zusätzlich wahr werden. Der ursprüngliche globale True-Zweig steht weiterhin zuerst und sein30er-Ausdruck bleibt unverändert; der bisherige Zonenfallback bleibt erhalten. Training und OFF aktivieren den neuen Pfad nicht. Die originale Regelkette, Netzentscheidung und finale Buchhaltung bleiben erhalten.

Diagnoseschnittstelle mit dem Runneragenten abgestimmt:

- `candidate_progress_status()` liefert eine unabhängige Kopie: `step`, `age`, `ready`, `progress`, `reset_reason`, `early_uids`.
- `episode_stats()['cand_stall_early_unit_steps']` zählt tatsächlich abgefragte frühe Berechtigungen einmal pro UID/Step, ausschließlich ohne alten globalen Rescue. `cand_stall_early_steps` zählt die entsprechenden Schritte.
- Die Statusliste enthält die tatsächlichen frühen Hook-Abfragen dieses Schritts. Sie ist keine behauptete Endaktionsänderung. Diese prüft der Runner separat anhand der nativen Aktionsfolge.

Tatsächliche Prüfung ausschließlich mit synthetischen Eingaben; automatische Testwachen verbieten reale QNet-Konstruktion und `torch.load`:

1. RED vor Implementierung: `/tmp/candidate-progress-impl/red-1.log`,21 FAIL/1 PASS. Der originale Core zeigt konkret LEFT statt des erwarteten korrigierten RIGHT; die übrigen neuen Tests zeigen fehlende Schnittstelle/Config. Der unveränderte Fallback-Test besteht bereits vorher.
2. Erste Umsetzung: `green-1.log`,22 PASS.
3. Finale enge Prüfung ergänzt den echten OFF-Aktionspfad: **23 PASS in2,53s**, Exit0, `green-final.log`. Enthalten sind zwölf Übergänge/13 Beobachtungen, mehrfacher Hook-Aufruf, Zielbindung, Maskenaliasing, fortgesetzte Besetzung, alle Fortschrittsarten, Rücknahmen, Lücken, Seiten-/Match-/Spielreset, Training/OFF und originale Endaktions-/`_prev_actions`-Buchhaltung. Ein synthetischer Policyaufruf je Entscheidung; keine echten Netzforwards.
4. `git diff --check -- agents/sherlock/config.py agents/sherlock/main.py`: Exit0.

Exakter Testaufruf:

```
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_candidate_progress_rescue.py
```

Keine breite alte Suite, Modelle, Spiele oder Trainings gestartet. Stabile Bytes und tatsächlicher Log an den unabhängigen Reviewer übergeben. Reale OFF-Reproduktion und echte frühe ON-Wirkung auf den zwei festgelegten Technikschlüsseln sind noch offen und gehören Root/Runner. Der Offline-Alttrace belegt wegen fehlendem `dead_tiles` nur einen bedingten möglichen Trigger57 statt altem74; das ist kein vollständiger Timer- oder Stärkenachweis. Siehe `/tmp/candidate-progress-timer-check.md`.
