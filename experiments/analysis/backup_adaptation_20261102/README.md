# Bedingte PT2-Studienwerkzeuge

Vorbereitete, getrennte Forschungsroute gemäß
`docs/superpowers/plans/2026-11-02-conditional-backup-adaptation.md`.
Import, `freeze`, `prepare`, Schätzung und Statistik starten weder Modelle noch Spiele.
Eine echte Ausführung verlangt ausdrücklich `run --plan … --start` und Root-Abnahme.
Diese Werkzeuge wurden ausschließlich mit synthetischen Dateien geprüft.

## Feste Studie

- Rollen exakt `baseline` und `PT2`; keine P/PT-Ergänzung oder Archivreuse.
- Auswahl: 844000–844049, beide Seiten, sieben Gegner: 700 baseline + 700 PT2 + 100 direkt = 1.500.
- Einzige mögliche Bestätigung: 842000–842299, beide Seiten, sieben Gegner: 8.400; dazu 600 direkte Spiele auf 843000–843299; insgesamt 9.000.
- Sechserpanel: `solution92`, `sol92_sq`, V3, V7, V10, V13 mit denselben vollständigen Release-Labels wie im P-Protokoll. `default` bleibt separat.
- Auswahlgates: Panel Δ ≥ +0,5 pp, Solution Δ ≥ 0, default ≥ 99 %, direkt ≥ 50 %.
- Bestätigung: Panel Δ ≥ +1 pp und untere 95%-Grenze > 0; Solution Δ ≥ 0 und untere Grenze ≥ −1 pp; default ≥ 99 % und Δ ≥ −1 pp; direkte untere Grenze > 50 %.
- Bestehende gepaarte Ganzkarten-Statistik: 5.000 Bootstrap-Ziehungen, RNG 0, 2,5/97,5-Perzentile. Beide Seiten und alle sechs Panelgegner bleiben je Karte zusammen.

## Eintritt und historische Parent-Kette

`check_parent(parent)` erwartet genau:

```python
parent = {
    'state_path': '/absolute/P-study/selection/state.json',
    'summary_path': '/absolute/P-selection-summary.json',
    'audit_path': '/absolute/P-independent-audit.json',
    'close_path': '/absolute/P-root-freeze-close.json',
}
```

Nur eine vollständig abgeschlossene 3.000-Spiele-P-Auswahl mit `nominee=null`,
P `passed=false`, unabhängigem `ACCEPTED`-Audit und Root-Freezeabschluss ist zulässig.
Master, Plan, Status, alle CSVs, alte Quell-/Protokolldateien, Interpreter, Modelle
und Prüfnachweise werden anhand tatsächlicher Bytes geprüft. Der ursprüngliche
Status muss `source_before == source_after == master.identity` belegen.
Der alte Live-HEAD-Check wird absichtlich nicht importiert: ein späterer legaler
Tool-Commit und zusätzliche Python-Dateien sind zulässig; alle alten Dateien
müssen unverändert bleiben. HEAD des historischen Masters ist fest
`03e54e267242ff642c126313fe5f512ed9d959ac`.

Der Parent-Audit wird in seinem tatsächlichen Format geprüft: Top-Level
`verdict=ACCEPTED`, `phase=selection`, `failed=[]`; in `results.selection`
Status/Nomination/Pass/3.000 Spiele und sämtliche Plan-/Status-/Master-/CSV-Hashes.
`evidence_sha256` muss mindestens Plan, Master, Status, Summary und alle CSVs
mit absoluten Pfaden enthalten. Sämtliche weiteren aufgeführten Evidenzdateien
werden ebenfalls geprüft.

Root-Abschlussformat:

```python
{
    'status': 'closed', 'phase': 'selection', 'head': '03e54e267242ff642c126313fe5f512ed9d959ac',
    'master_sha256': '…', 'selection_state_sha256': '…',
    'selection_summary_sha256': '…', 'independent_audit_sha256': '…',
    'source_unchanged': True, 'weights_unchanged': True,
}
```

Die Booleans ersetzen keine Datei- oder Hashprüfung. Schon ein vorhandenes
Parent-`confirmation`-Verzeichnis oder eine Parent-Bestätigungsreservierung
verhindert den Eintritt, auch wenn kein Spiel persistiert wurde.

## Zwei neue vollständige Arme und Kandidatenabnahme

`check_candidate_admission(path, candidate_path)` verlangt das von Root nach
Training, Endreload und tatsächlichem Kandidatenaudit erzeugte JSON:

```python
{
    'verdict': 'ACCEPTED_PT2', 'source_sha256': '<V14 SHA>',
    'candidate': {'path': '/absolute/PT2.pth', 'sha256': '…'},
    'components': {'total': 36, 'replaced': [18, 19], 'ordered_sha256': ['…'] * 36},
    'training': {
        'arms': ['adapt18', 'adapt19'], 'seeds': [30, 31],
        'each_games': {'prefill': 120, 'train': 600, 'val': 96},
        'checkpoints': {'/absolute/adapt18/end.pth': '…', '/absolute/adapt19/end.pth': '…'},
        'accepted_audit': {'path': '/absolute/new-two-arm-audit.json', 'sha256': '…'},
    },
    'warnings': [],
}
```

V14-SHA ist
`98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`.
Der neue Trainingsaudit muss `verdict=ACCEPTED_TWO_ARM_BACKUP`, `failed=[]`,
`warnings=[]` und genau die beiden Arme enthalten, mit je `seed`, `train_games=600`,
`prefill_games=120`, `validation_games=96`. Seine `evidence_sha256` muss beide
absoluten Endcheckpoint-Pfade mit tatsächlichen Hashes belegen. Alle gelisteten
Trainingsnachweise werden gegen ihre Dateien geprüft. Keine Legacy-Vierarmabnahme.

Diese Prüfschicht lädt keine Tensoren und ersetzt den unabhängigen Trainings-,
Assembler- und Actual-Load-Audit durch Root nicht. Admission, Trainingsaudit,
Endcheckpoints und sämtliche schon zuvor geschützten Gewichte werden auch im
neuen Master fest gebunden.

## Zeitprüfung vor der Aufnahme und vor jeder Phase/jedem Job

```python
estimate = driver.estimate_backup(parent)
driver.admit_backup(parent, now=time.time())
```

`estimate_backup` gibt alle Komponenten zurück. Die komplette Aufnahme verlangt
9.800 kombinierte und 700 direkte Spiele, jeweils +20 %, dazu fest 50 Minuten
Training, 20 Minuten Setup/Audit und 60 Minuten Abschlussreserve. Der
Trainingsparameter kann nicht zur Laufzeit verkürzt werden.

Klassenfloors sind 2,22 bzw. 3,00 WALL-Sekunden/Spiel bei insgesamt zwei Workern.
Alle tatsächlich beobachteten Parent-Klassenraten werden aufgenommen; die jeweils
langsamste relative Klasse skaliert beide Floors. PT2-Beobachtungen kommen hinzu.
Kein Reset zwischen Phasen, keine Division durch zwei. Auch jede spätere
Eval-Zulassung reserviert weiterhin volle 20 Minuten Setup/Audit und 60 Minuten
Abschluss. Deadline 03.11.2026 04:30 UTC / 05:30 Berlin; harter Spielschluss
03:30 UTC / 04:30 Berlin. Zu Beginn der Auswahl wird die vollständige mögliche
9.000-Spiele-Bestätigung bereits mitgerechnet.

AC/Quotareserve ≥30 %, Seed-Freshness und globale Ressourcenfreigabe prüft Root
vor Aufnahme zusätzlich. Der Supervisor prüft AC/Batterie und sichtbare fremde
Modelljobs sowie den gemeinsamen Ressourcenlock. Es laufen höchstens zwei
Evaluationsworker; ein Training darf nicht parallel laufen.

## Master, kanonische Phasen und einmalige Bestätigung

```python
frozen = driver.create_freeze(
    root, study_directory / 'study_freeze.json',
    {'baseline': baseline_path, 'PT2': candidate_path},
    python=python_path, protocols=protocol_paths, expected_head=reviewed_head,
    parent=parent, candidate_admission=admission_path,
)
selection = driver.prepare_phase(
    study_directory / 'study_freeze.json', study_directory / 'selection', 'selection',
)
# Nur nach vollständiger Auswahl und geprüfter Summary mit qualifiziertem PT2:
confirmation = driver.prepare_phase(
    study_directory / 'study_freeze.json', study_directory / 'confirmation', 'confirmation',
    candidate='PT2', selection_state=selection_state, selection_summary=selection_summary,
)
```

Master und Phasenpfade sind fest; ein Umzug oder ein zweites Ausgabeverzeichnis
wird abgelehnt. Vor Erstellung des Bestätigungsplans wird im historischen
Parent-Studienverzeichnis `conditional_confirmation_reservation.json` mit
`O_EXCL`, fsync und Master-/Planbindung reserviert. Dieser gemeinsame Slot
bleibt bei jedem Fehler und bei null persistierten Spielen bestehen. Auch ein
zweiter neuer Master kann damit keine zweite Bestätigung beginnen. Die eigene
bereits reservierte Studie darf ihre gebundenen Pläne weiterhin prüfen.

Nur eigene registrierte Prozessgruppen werden bei Signal, Batteriegrenze,
Dateidrift oder Deadline gestoppt. Statusdateien werden atomar geschrieben;
ein verlorener Lock-/Dateirace überschreibt keine fremde Statusdatei.
Mac-Systemaliase `/tmp` und `/var` werden kanonisiert, Nutzer-Symlinks abgelehnt.

## Synthetische Prüfung

```sh
.venv/bin/python -B -m unittest discover -s experiments/analysis/backup_adaptation_20261102 -p 'test_study_*.py'
.venv/bin/python -B -O -m unittest discover -s experiments/analysis/backup_adaptation_20261102 -p 'test_study_*.py'
```

Die Tests verwenden ausschließlich temporäre synthetische Dateien, die schon
vorhandenen Stdlib-/NumPy-/Pandas-Helfer und eine kontrollierte Prozessgrenze.
Keine Modelle, Torch, Umgebung, echten Spiele, Installationen oder Projektsuite.
Statistische Integritätsprüfungen bleiben auch unter Python `-O` aktiv.
