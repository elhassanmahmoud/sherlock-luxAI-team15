# Begrenzter Kartencheck: Matchgewicht-Studie

**Keine beobachtete frühere Nutzung oder fremde Reservierung der sieben vorgesehenen Bereiche.** Drei Nennungen im eigenen neuen Plan sind geplante Reservierungen, keine historischen Ausführungen. Keine absolute Frischebehauptung oder Modellstartfreigabe.

| Block | Inklusive Karten | Zahl |
|---|---|---:|
| train48 | 9960000–9960199 | 200 |
| prefill48 | 9960300–9960319 | 20 |
| train49 | 9961000–9961199 | 200 |
| prefill49 | 9961300–9961319 | 20 |
| solution | 9970000–9970019 | 20 |
| direct_v14 | 9970100–9970119 | 20 |
| direct_control | 9970200–9970219 | 20 |

Alle Bereiche sind disjunkt: **500 Karten**, jeweils beide Seiten. Gesucht wurde nach Kartennummern unabhängig von der Seite; auch frühere einseitige Nutzung würde zählen.

**Methode:** vorhandenen `/tmp/candidate-progress-seeds/seed-audit.py` extern kopiert; ausschließlich `RANGES` und die Ausnahme `ALLOWED_CURRENT` für den exakten Pfad `docs/superpowers/plans/2026-11-09-match-weight-training.md` geändert. Rücktausch reproduziert die Ausgangsbytes; `scanner-diff.txt` enthält beide Änderungen. Keine neue Suchlogik. Einmalig `python3 -B /tmp/match-weight-seeds/seed-audit.py --targeted-readonly-scan`, **Exit 0**, 2026-11-09T15:14:25.727752+00:00 bis 2026-11-09T15:14:51.369042+00:00, **25,69 Sekunden**.

**Abdeckung:** acht registrierte Worktrees; **14.875 strukturierte Pfade** (5.940 JSON, 33 JSON.gz, 8.890 CSV, 12 CSV.gz) und **9.536 Textpfade**. Nach SHA-Deduplizierung: 1.672 JSON-, 1.705 CSV- und 2.012 Textinhalte. 1.648.605 CSV-Zeilen, 1.643.544 numerische CSV-Seedwerte, 120.999 JSON-Seedwerte und 742 konservative Intervallkandidaten. Metadaten/CSV unter `experiments/logs/replays`; ergänzende `.md/.py/.sh/.txt/.log` unter Root und `docs/scripts/experiments/logs/replays`. Keine Binärarchive oder Roh-JSONL-Inhalte geöffnet.

**Befund:** null CSV-Nutzungstreffer; null JSON-Zahlen-, String- oder Intervallüberschneidungen; null Lese-/Text-/Dekodierfehler oder während des Scans beobachtete Mutationen. Genau drei erlaubte Texttreffer im gelesenen eigenen Plan: Zeile 15 (vier Lern-/Vorlaufbereiche), 31 (Solution), 32 (beide Direktbereiche). Die Ausnahme betrifft nur diesen Planpfad.

Plan vor dem Scan unversioniert (`??`), initialer und gescannter Hash `ba7279181e46fb574a42c9d951a9b0373adc7c6fcf422991a03f380e5214eeb8`. **Nach Scanende änderte sich der Plan** auf `b5a19159f30b7d8aedba28971ab3650fa74ab7a97b0cace1b8e08d46bed69f75`. Die drei konkreten Seedzeilen wurden gezielt nachgelesen und sind exakt unverändert; `plan-postscan-check.json` bindet diesen Befund. Kein zweiter Scan und keine Behauptung einer eingefrorenen Planfassung.

Rohverdikt unverändert: **`NO_OBSERVED_OTHER_CONSUMPTION_OR_RESERVATION_WITH_REPORTED_LIMITS`**. Historische automatische SAP-leading-Profil-/Überschrifttexte bleiben wegen der engen Wiederverwendung erhalten. Die automatische `seed-audit.md` enthält die alte Vorlagenzeile „repository reservation allowlist is empty“; diese trifft hier **nicht** zu. Maßgeblich sind die tatsächliche Ein-Pfad-Ausnahme `allowed_current_relative_paths`, `ranges_inclusive` im JSON und diese Einordnung.

Beide Hauptarbeitskopien vor/nach Scan auf **`4e23cebae531b7d18f7f5caa01b018db7fd59a72`**; alle acht HEADs und registrierten Worktrees unverändert. Vollständiges Inventar mit Dateihashes und HEADs im Rohbericht. Kein lückenloser Freeze: nach Textinventarisierung neu entstandene Dateien bleiben möglich.

**Grenzen:** 288 eindeutige CSVs ohne Seedspalte (**5.061 Zeilen**); 2.265 heuristisch ungültige Seedfelder ausschließlich in JSON, keine ungültigen CSV-Seedwerte. **2.004 Roh-JSONL-Pfade bewusst ausgeschlossen**. Externe/unregistrierte Arbeitskopien, undokumentierte/seedlose oder ausschließlich JSONL-belegte Historie, berechnete Seedformeln, Binärinhalte und unbekannte Schemas bleiben unprüfbar. Verzeichnis-Symlinks werden nicht verfolgt; `.git/.venv/venv/node_modules/__pycache__` im Inhaltsscan übersprungen. Keine Modelle, Tests, Spiele, Simulationen, Repoänderungen oder Wiederholung geschlossener Studien.

| Beleg | SHA-256 |
|---|---|
| Ausgangsskript | `6071542f05a9d5ee1afe9976d6642c44bf87e83fbb03c2453da5ed8d4f266655` |
| `seed-audit.py` | `ecfaf1e859394b0e2e6ee84edb4cdc91c680c9f6470d01ecbc1ec36d727e2c12` |
| `seed-audit.json`, 18.264.644 Bytes | `050b631ed74ff87320137e079f229a7c10424da7c987744f54298dbc0fc0499c` |
| `scanner-diff.txt` | `9aa811034d40450b5d12210901dabad2aa627dd0561a2d0ec6b7935625f60c25` |
| `plan-postscan-check.json` | `76a70b1dce740c89b2458b9c5380ec10492b74ddb85adbdf0278f95d0ec25c89` |

Rohbericht, Skript, Originallog, Methodenbeleg und Hashliste liegen unter `/tmp/match-weight-seeds`. Die lokale Evidenz erfordert keine Änderung der vorgesehenen Kartenbereiche.
