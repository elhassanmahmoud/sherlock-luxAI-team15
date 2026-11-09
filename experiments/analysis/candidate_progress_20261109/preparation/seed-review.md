# Begrenzter Seedcheck: vorgeschlagene Candidate-Progress-Karten

**Keine beobachtete frühere Nutzung oder vorhandene Reservierung im erfassten lokalen Bestand.** Keine Seedkollision gefunden. Das ist keine absolute Frischegarantie, eigene Kartenreservierung oder Startfreigabe; Root legt den neuen festen Plan separat fest.

Geprüft: **9948000–9948019** für Solution und **9948100–9948119** für den Direktvergleich, jeweils 20 disjunkte Karten und beide Seiten. Die Suche erfasst Kartennummern unabhängig von der Seite; frühere einseitige Verwendung würde ebenfalls zählen.

Einmaliger tatsächlicher Aufruf: `python3 -B /tmp/candidate-progress-seeds/seed-audit.py --targeted-readonly-scan`, Exit 0, **2026-11-09T14:37:28.161271+00:00 bis 2026-11-09T14:38:14.044902+00:00**, Rohbericht-Dauer **45,93 Sekunden** (Konsolengesamtzeit 46,02). Vorhandenes Threat-Warmstart-Skript kopiert und ausschließlich `RANGES` geändert; exakter Rücktausch reproduziert die Ausgangsbytes. Ausgabeort folgt automatisch dem externen Skriptverzeichnis. Kein neuer Scanner. Historischer automatischer Profilname SAP-leading bleibt unverändert; gültige neue Bereiche stehen unter `ranges_inclusive`.

**Abdeckung:** acht registrierte lokale Worktrees; **14.813 strukturierte Pfade** (5.888 JSON, 31 JSON.gz, 8.882 CSV, 12 CSV.gz), **9.453 Textpfade**. Inhaltlich nach SHA-Deduplizierung: 1.645 JSON-, 1.701 CSV- und 1.972 Textdateien. 1.648.385 CSV-Zeilen, 1.643.424 numerische CSV-Seedwerte, 120.984 JSON-Seedwerte und 740 konservative Intervallkandidaten. Strukturierte Suche in `experiments`, `logs`, `replays`; ergänzende Protokoll-/Plan-/Quelltextsuche in Root, `docs`, `scripts`, `experiments`, `logs`, `replays` für `.md/.py/.sh/.txt/.log`. Keine binären Gewichte oder Replayarchive geöffnet.

**Befund:** null CSV-Nutzungsüberschneidungen, null JSON-Zahlen-/String-/Intervalltreffer und null Texttreffer. Somit zum Scanzeitpunkt auch keine eigene neue Planungsnennung im erfassten Bestand. Null Lesefehler, Textdekodierlücken oder beobachtete Datei-/HEAD-/Worktreeänderungen. Rohverdikt unverändert: `NO_OBSERVED_OTHER_CONSUMPTION_OR_RESERVATION_WITH_REPORTED_LIMITS`.

**Git-/Prozesslage:** Studien- und primäre Arbeitskopie jeweils vor/nach auf `30800a71079c41754c02e3e9b5ccd2e000a09137`; Studienbranch `improvement/decision-learning-20261108`. Alle acht HEADs und registrierten Worktrees während des Scans unverändert, vollständig im Rohbericht. Git-Status vor/nach: keine Änderungen an versionierten Dateien, 87 unversionierte Statuszeilen mit vorhandenen Experimentlogs/-ausgaben; keine Bereinigung vorgenommen. Lokale Prozesssnapshots **2026-11-09T14:37:27.904897+00:00** und **2026-11-09T14:38:47.837419+00:00**: keine passenden Python-/pytest-/caffeinate-Prozesse mit Projektmarkern. Das ist eine Momentaufnahme des dokumentierten Filters, keine kontinuierliche Überwachung oder Garantie für anders benannte/entfernte Prozesse.

**Grenzen:** 287 eindeutige CSVs ohne Seedspalte (4.961 Zeilen); 2.131 heuristisch ungültige Seedfelder ausschließlich in JSON, keine ungültigen CSV-Seedwerte. **2.004 Roh-JSONL-Pfade bewusst ausgeschlossen**. Externe Rechner, unregistrierte Checkouts, nicht dokumentierte/seedlose oder ausschließlich JSONL-belegte Historie, berechnete Seedformeln, opaque Binärformate und nicht erkannte Schemas bleiben unbekannt. Verzeichnis-Symlinks sowie `.git/.venv/venv/node_modules/__pycache__` werden im Inhaltsscan übersprungen. Textpfadliste wird am Ende nicht neu inventarisiert; nach ihrer Aufnahme neu entstandene Planungen sind nicht ausgeschlossen. Deshalb kein atomarer Freeze oder pauschales „nie gespielt“. Keine Modelle, Tests, Spiele, Simulationen, Repoänderungen oder Gitmutationen.

| Beleg | SHA-256 |
|---|---|
| Ausgangsskript | `5538daf7f5bd2101d45515d7fe88886edbb41b9e910f00d6519ae8b7ecedfac3` |
| `/tmp/candidate-progress-seeds/seed-audit.py` | `6071542f05a9d5ee1afe9976d6642c44bf87e83fbb03c2453da5ed8d4f266655` |
| `seed-audit.json`, 18.112.235 Bytes | `a96c2bd0df793772d727b16508d173fe6a9c0ba7acee78de3a1040e541a711c2` |
| `context-before.json` | `657c5c2323711755173ba247b5f6f72ad262c3d95185c807134ef4176ac94563` |
| `context-after.json` | `6b420798aa062e9528f499046c1cd666b480e9c11153c13a98326a4c0a7988a4` |

Rohbericht mit Dateiinventar und Einzelhashes, automatisches Kurzverdikt, Aufrufbeleg, Prozess-/Git-Snapshots und dieses Review sind über `/tmp/candidate-progress-seeds/hashes.json` gebunden. Die lokale Evidenz zeigt keinen Grund, die vorgeschlagenen Bereiche wegen beobachteter Vorverwendung zu ändern.
