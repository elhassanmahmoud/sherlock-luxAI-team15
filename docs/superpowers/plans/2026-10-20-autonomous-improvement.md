# Sherlock: autonomer Prüf- und Verbesserungsplan

> **For agentic workers:** Use superpowers:executing-plans to implement this
> plan task-by-task. Moayed requests sequential autonomous execution and
> pushing verified changes; do not ask again for routine stage approvals.

**Goal:** Den aktuellen Kandidaten im Kursbetrieb absichern und höchstens
eine klar bestätigte Verbesserung aus einem begrenzten Versuch übernehmen.

**Architecture:** Bestehende Auswertungswerkzeuge und Kandidaten verwenden.
Messung und Auswahl von Agentenlogik trennen; zunächst nur vorhandene Config-
Schalter variieren. Kurs-Runner in einer temporären Kopie mit instrumentiertem
Agenten prüfen, ohne seine Quelldatei oder die Abgabe zu verändern.

**Tech Stack:** Python 3.13, PyTorch, LuxAI-S3, pytest, bestehende CSV-Auswertung.

**Spec:** [Arbeitsauftrag und Auswahlregeln](../specs/2026-10-20-autonomous-improvement-design.md)

## Global Constraints

- Abgabe-Gewichte unverändert; beide SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.
- Maximal zwei Evaluationsprozesse, höchstens ein Training; keine Cloud-Kosten.
- Kurs-Runner unverändert; bestehende Kandidaten und Messdateien nicht ersetzen.
- Ende dieses Zyklus spätestens 20.10.2026 23:15 UTC.
- Entwicklung 500720–500779; Bestätigung 502420–502619 exklusiv reserviert.
- CNN3 nicht doppelt starten; keine BC-Datensammlung auf dem 8-GB-Rechner.
- Keine neue Abgabe ohne ausdrücklichen Auftrag.

## Review Focus

- Mehrere Spiele/Seiten im selben Prozess: Gedächtnis darf nicht über Spiele lecken.
- Runner lädt unerwartete Gewichte: temporäre Pfade und Hashes prüfen.
- Partiell geschriebene CSV/Prozessfehler: nicht als fertiges Experiment auswerten.
- Durch Auswahldaten verzerrte Verbesserung: nur einen Herausforderer bestätigen.
- Push während fremder Änderungen: abgleichen, nie Force-Push; relevante Tests wiederholen.

## Fortschritt

- [x] Aufgabe 1: Referenz und technische Basis prüfen.
- [x] Aufgabe 2: Kursbetrieb prüfen.
- [ ] Aufgabe 3: Begrenzte Entwicklungsmessung.
- [ ] Aufgabe 4: Bestätigung und Gegnervergleich, falls Auswahlregel erfüllt.
- [ ] Aufgabe 5: Abschlussbericht, Kandidat nur bei bestätigtem Vorteil, Push.

## Aufgabe 1: Referenz und technische Basis

**Files:** vorhandene `tests/`, `scripts/par_eval.py`, Kandidatenmanifest;
Ausgaben `experiments/analysis/autonomous_20261020/`.

**Interfaces:** Eingang `all18_v3.pth`; Ausgang geprüfter Hash, Testergebnis,
CSV für Seeds 500720/500721 und dokumentierte Pakete.

- [x] `pytest -q` ausführen. Erwartung: alle vorhandenen Tests erfolgreich;
  Fehler zunächst diagnostizieren, keine Agentenänderung auf Verdacht.
- [x] `all18_v3` auf zwei Entwicklungskarten gegen beide Gegner/beide Seiten
  auswerten und mit `M_fo10_ptsap_fc_720.csv` vergleichen.
  Erwartung: alle Spielkennzahlen außer Zeit identisch.
- [x] Abgabe-/Kandidatenhashes vor/nachher prüfen und Befund dokumentieren.

## Aufgabe 2: Kursbetrieb

**Files:** neues `scripts/check_candidate_runner.py`,
`tests/test_candidate_runner.py`; Ergebnis
`experiments/analysis/autonomous_20261020/runner.json`.

**Interfaces:** CLI `--weights PATH --out NEW_JSON`; Bericht über 8 Spiele
(2 je Seite/Gegner), Aktionsvalidierung und Zeitverteilung.

- [x] Tests zuerst: temporäre Paths.csv zeigt für Gruppe 15 auf die
  Kandidatenkopie; Original bleibt bytegleich; bestehender Ausgabebericht
  wird abgewiesen. Erwartung vor Implementierung: fehlendes Modul/Funktion.
- [x] Hilfsfunktionen `prepare_workspace(root, weights, destination)` und
  `validate_actions(actions, max_units)` implementieren. Workspace enthält
  kopierte Kandidatengewichte, eigene Paths.csv und Verweise auf Agentenmodule.
- [x] Aktionsvalidierung prüft Shape `(max_units, 3)`, endliche ganzzahlige
  Werte und Aktionstyp 0–5. Energie-/Asteroidenmasken bleiben vorhandenen
  Agententests und Evaluationsmetriken zugeordnet.
- [x] Runner-Aufruf `train=False`; Agent instrumentieren, Entscheidungslatenz
  messen und frisches Belief bei neuer Instanz prüfen. Startgewichte erhalten.
  Verwendete Zufallsseeds protokollieren; Runner-Ergebnisse nicht mit festen
  Benchmarkkarten verwechseln.
- [x] Unit-Tests und tatsächliche 8-Spiele-Prüfung ausführen; nur bei Erfolg
  Bericht/Code committen. Kein erfundenes Zeitlimit als bestanden melden.

## Aufgabe 3: Begrenzte Entwicklungsmessung

**Files:** neue CSVs unter `experiments/compare/autonomous_20261020/`,
Ergebniszusammenfassung unter `experiments/analysis/autonomous_20261020/`.

**Interfaces:** `scripts.par_eval` → vollständige CSVs, `scripts.compare_report`
→ gepaarte Vergleiche. Eingabe feste Referenz und vier Config-Overrides aus Spec.

- [ ] Referenz und vier Varianten nacheinander ausführen, je 60 Karten,
  beide Seiten und Gegner, `--workers 2`. Neue Ausgabepfade verwenden.
- [ ] Je Datei 240 eindeutige Zeilen und vollständige Seitenpaare prüfen;
  `point_counting_version=2`, keine fehlenden Ergebnisse.
- [ ] Nach festgelegter Regel höchstens einen Herausforderer wählen;
  Entscheidung inklusive verworfener Varianten dokumentieren.
- [ ] Zwischenstand samt verwendeten Seeds und unveränderten Gewichtshashes pushen.

## Aufgabe 4: Bestätigung und Gegnervergleich

**Files:** neue Referenz-/Herausforderer-CSVs auf Seeds 502420–502619 und
zusätzliche CSVs gegen alte Abgabe auf Entwicklungskarten.

**Interfaces:** eindeutige Auswahl aus Aufgabe 3; gepaarte Auswertung über Karten.

- [ ] Wenn keine Variante die Auswahlregel erfüllt: Aufgabe begründet überspringen.
- [ ] Referenz und genau einen Herausforderer auf den reservierten 200 Karten
  auswerten, beide Seiten, default/Solution_92, je 800 Spielzeilen.
- [ ] Gegen alte Abgabe (`self:agents/sherlock/weights/agent_p0.pth`) beide
  Varianten auf den 60 Entwicklungskarten prüfen.
- [ ] Auswahlregel aus Spec anwenden; bei Unsicherheit Referenz behalten.
  Nicht nachträglich andere Varianten auf demselben Bestätigungsblock suchen.

## Aufgabe 5: Abschluss

**Files:** `docs/ARBEITSSTAND.md`, dieser Plan, neuer Ergebnisbericht;
nur bei Erfolg neue Kandidatendatei und Manifest.

- [ ] Vollständige Ergebnisse und Grenzen zusammenfassen; bei Erfolg Config
  in neuen Checkpoint schreiben und gespeicherte Config gegen Override
  auf zwei bereits benutzten Karten prüfen.
- [ ] Betroffene Tests und Hash-Prüfungen durchführen.
- [ ] Änderungen unabhängig prüfen lassen, wichtige Befunde beheben.
- [ ] GitHub abgleichen, geprüfte Änderungen pushen; Planstatus aktualisieren.
- [ ] Weiterführung beenden, sobald Zyklus fertig oder Arbeitsgrenze erreicht.
  Offene Schritte und laufende Prozesse ausdrücklich benennen.

## Laufendes Protokoll

- 20.10.: Basis 153 Tests bestanden, V3 auf 8 Spielen identisch zur Referenz.
- Kursprobe: 8 Spiele, beide Seiten/Gegner, je 303 Schritte, frisches Belief und gültiges Aktionsformat. 9 neue Unit-Tests bestanden.
- Korrektur während Instrumentierung: Runner verwendet `np.random.default_rng`, nicht `np.default_rng`; eigener Regressionstest ergänzt und erfolgreich erneut geprüft. Agentenlogik blieb unverändert.
- Ausführungsentscheidung: bestehender Hauptcheckout und direkte kleine main-Commits gemäß Teampräferenz; kein zusätzlicher Worktree.

- Abschluss Aufgabe 2: unabhängiger Review-Befund zum stillen Checkpoint-Fallback behoben; 163 Tests bestanden und 8 Runner-Spiele mit verifizierten 18 Netzständen erfolgreich (`runner_verified.json`). Kein offener wichtiger Befund.
- Automation: `sherlock-verbesserungsplan-fortsetzen`, alle 30 Minuten; bei Abschluss oder Arbeitsgrenze deaktivieren.

- Aufgabe 3 gestartet: fünf sequenzielle Evaluationsläufe, je 240 Spiele, maximal zwei Worker. Status/PID/Commands und fertige Ergebnisse: `experiments/analysis/autonomous_20261020/development_state.json`. Laufprozess nicht duplizieren; unfertige CSVs nicht werten.
- Leerlauf-Ruhezustand bis zur Arbeitsgrenze verhindert. Eigener Prozess ist in `experiments/analysis/autonomous_20261020/awake_until_deadline.json` dokumentiert. Bei frühem Abschluss nur diesen anhand PID und Kommando verifizierten caffeinate-Prozess beenden; keine fremden Prozesse stoppen.
- Nächste Fortsetzung: laufenden Entwicklungsbatch prüfen, vollständige Ergebnisse auswerten, maximal einen eindeutigen Gewinner bestätigen. Bei Ende Automation deaktivieren.
