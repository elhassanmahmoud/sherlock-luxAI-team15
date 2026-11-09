# MATCH38-Bestätigung – Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Die unveränderte nominierte MATCH38-Variante einmalig in 440 frischen Spielen gegen V14 bestätigen oder verwerfen.

**Architecture:** Vorhandene par_eval-, Statistik- und Prozesshilfen verwenden. Eine neue eng begrenzte Aufnahme konsumiert die geschlossene Auswahl und dieselben zwei Evaldateien; drei feste Jobs, keine neue Montage oder Trainingsplattform.

**Tech Stack:** vorhandenes Python-3.13-venv, NumPy/Pandas/PyTorch und bestehende Lux-Runtime; keine neuen Abhängigkeiten.

**Spec:** [Feste Methodik und sämtliche Gates](../specs/2026-11-09-match-weight-confirmation.md).

## Global Constraints

- Genau 160 V14-Panelspiele, 160 MATCH38-Panelspiele und 120 Direktspiele. Panelgegner `solution92,default,sol92_sq,rush`; zwei Seiten je Karte.
- Panelkarten **9980000–9980019**; direkte Karten **9980100–9980159**. Einmaliger begrenzter Konfliktcheck vor Aufnahme, eigene Planreservierung unterscheiden, Lücken offen nennen.
- Exakte unveränderte Modellhashes aus der Spec; gesamte bisherige Runtime bytegleich zur akzeptierten Auswahlquelle. Keine alten Admissionvalidatoren gegen neuen HEAD starten.
- Alle Gatewerte, Bootstrapmethode, Remisbehandlung und Interpretationsgrenzen wörtlich aus der Spec übernehmen. Keine zusätzliche Auswahl oder Änderung nach Ergebnisansicht.
- Maximal zwei Modellworker, keine Tests parallel zu Modellen, Quellenfreeze; Akku und Restkontingent erlaubt, keine Resets durch Codex.

## Review Focus

- Historische Auswahl unvollständig, nicht nominiert oder manipuliert: Aufnahme muss verweigern.
- Neue Quelle mit verändertem alten Agenten-/Runtimecode oder veränderter Modellkopie: Aufnahme muss verweigern.
- Fehlende Seiten/Gegner, doppelte Keys, alte Punktezählung, Teilspiele oder inkonsistente Ergebnisse: keine erfolgreiche Reihe.
- 71 statt 72 echte Siege, Remis und Randgrenzen: keine Score-/Siegverwechslung; feste inklusive/strikte Vergleiche.
- Identische Panelkontraste: degeneriertes Intervall sichtbar, kein formaler Populationsnachweis oder automatischer Gewichtsersatz.

## Task 1: Enger Bestätigungsläufer und Auswertung

**Files:** Create `scripts/match_weight_confirmation.py`, `scripts/match_weight_confirmation_owner.py`, `tests/test_match_weight_confirmation.py`.

**Interfaces:** `admission(path, sha)` konsumiert gehashte neue Aufnahme, geschlossene Auswahl samt Originalsummary/-owner/-admission, technische Modellbelege, Seedannahme und feste Source-/Protected-/Inputmaps. Liefert validierte Aufnahme. `job_spec(a, name)` und `performance_command(a, name)` definieren ausschließlich `v14_panel`, `match_panel`, `match_v14`. `validate_csv(a, name)` liefert vollständiges geprüftes DataFrame. `analyze(a)` liefert W/D/L je Gegner, gepaarte Panel-/Solutionkontraste, Direktintervall, Degenerationshinweise, einzelne Gates und `passed`.

- [ ] Synthetische Negativtests für die fünf Reviewklassen sowie genau drei Jobs/2+1-Wellen/keinen Neustart schreiben; reale Archive und Spiele sperren.
- [ ] Tests vor Implementierung ausführen, erwarteten fehlenden Vertrag dokumentieren.
- [ ] Vorhandene `match_weight_compare`, `compare_report`, `league_gates.panel_delta(..., panel=...)`, `direct_result` und Lifecycle-/Guardhilfen eng nutzen. Alte `confirm_checks` haben andere Gates und sind unzulässig. Frühere Quellen nicht verändern; historische Bindungen ausdrücklich behandeln. Owner speichert tatsächliche Returncodes, CSV-Receipts und erst nach allen drei Jobs die Summary. Bei Fehler nur eigene Gruppen kontrolliert beenden, keine Wiederholung.
- [ ] Neue Suite plus bestehende Matchgewicht-Vergleichstests mit venv, Threads 1, `-B`, `TMPDIR=/private/tmp` ausführen; tatsächliches Ergebnis festhalten. Kein unnötiger Gesamtsuitenlauf.
- [ ] Unabhängiger finaler Code-/Methodenreview und Root-Abgleich; Quellencommit mit Vorbereitung/Seedbelegen, kein Modellstart davor.

## Task 2: Einmalige reale Bestätigung

**Files:** `experiments/analysis/match_weight_confirmation_20261109/` mit eigenen Aufnahmen, Status, CSVs, Review, Ergebnis und rohen Bytehashes; `.gitattributes` bewahrt CSV/JSONL/Log-Bytes.

- [ ] Prüfen, dass keine alten Modelljobs laufen; frische echte Quota einlesen, neue Aufnahme mit exakt festgelegten Karten/Modellkopien erstellen. Dieselben eingegangenen historischen Quellen und alle Schutzdateien prüfen.
- [ ] Root startet ausschließlich diese eine Phase. 160er-Paneljobs parallel, danach 120er-Direktjob; überwachen, keine Quellen-/HEADänderungen oder Tests.
- [ ] Nach tatsächlichem Prozessende originale Auswertung unter eingefrorener Quelle reproduzieren und unabhängig alle 440 Rohzeilen, Gates und Ganzkartenintervalle nachrechnen. Datenfehler sind kein negativer Leistungsbefund; keine Ersatzspiele ohne neue ausdrückliche Entscheidung.
- [ ] Root versiegelt Abschluss, erst dann Freeze lösen. Ergebnis mit Unsicherheit für Mahmoud dokumentieren; sinnvollen Ergebniscommit pushen und Hauptkopie verlustfrei aktualisieren.
- [ ] Nur bei bestandenem vollständigem Ergebnis separate Reproduktions-/Kurs-/Sicherungsarbeiten für eine mögliche Übernahme konkret planen. Sonst V14 erhalten und diesen Versuch schließen. Kein automatischer anderer Kandidat oder Trainingsstart.
