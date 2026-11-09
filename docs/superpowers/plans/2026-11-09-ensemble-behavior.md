# Ensemble-Verhalten – Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox syntax.

**Goal:** Zwei feste Einzelnetze unter Ensemble-Aktionsauswahl trainieren und bei technischer Treue gegen die vorhandenen Kontrollen sowie V14 prüfen.

**Architecture:** Instanzlokaler temporärer Handlungs-Hook, regulärer alter Einzelnetz-DDQN-Lerner. Bestehende Spiel-/Reward-/Replay-/Lifecyclefunktionen direkt importieren; neue enge Aufnahme für vier Technikspiele und genau zwei gemeinsame ON-Worker mit manueller Vorlaufbarriere.

**Tech Stack:** bestehendes Python-3.13-venv, Torch CPU, NumPy/JAX/Lux. Keine neuen Abhängigkeiten oder produktiven Änderungen.

**Spec:** [Fester Versuchsvertrag](../specs/2026-11-09-ensemble-behavior.md). Read-only Bauhinweise zusätzlich `/private/tmp/ensemble-behavior-implementation-contract.md`; bei Unterschied gilt die Spec.

## Global Constraints

- Profil `ensemble_behavior_20261109`; neue Dateien ausschließlich `scripts/ensemble_behavior_study.py`, `scripts/ensemble_behavior_owner.py`, `tests/test_ensemble_behavior_study.py`. Alter Core und alte Studienquellen unverändert.
- Technisch vier Spiele OFF/ON auf den zwei festgelegten bekannten Keys; danach gemeinsam zwei ON-Arme Starts 48/49 mit je 40 Vorlauf- und 400 Lernspielen und je 60.000 Updates. Kein automatischer Folgestart, Resume oder Ersatzlauf.
- Historische Kontrollen fest gebunden; keine unveränderte alte Paargleichheitsprüfung für ON verwenden. Kontrollreward w_match=2, originale Konfiguration/Initialisierung/Gegnerfolge.
- Maximal zwei Modellworker; keine Tests neben realen Modelljobs. Akku/Restkontingent erlaubt; tatsächliche Quota, keine Resets durch Codex. V14/ZIP unverändert.
- Später exakt 200 Auswahlspiele und vier Gates aus Spec; deren Werkzeuge erst nach Trainingsabnahme separat aufnehmen. Keine Bestätigung oder Promotion in diesem Plan.

## Review Focus

- Hook wirkt versehentlich während `_learn`, zählt Originalmitglied 18 doppelt oder setzt es an falsche Stelle: Tests müssen eigene Lern-/Adam-/Targetgleichheit und exakt 36 geordnete Beiträge sichern.
- Alias von CPU-Tensornumpy zerstört rohe Q-Belege; Observer kopiert vor Coremaskierung, keine weiteren Inferenzaufrufe.
- Setup verändert RNG, Optimizerparameter oder eingefrorene Tensoren: vor/nach Identitäten und tatsächliche RNG-Zustände vergleichen; CPU-only erzwingen.
- Historische Referenz falsch/unvollständig oder Runtime geändert: Aufnahme verweigert; OFF-Treue vor ON-Lernen, fehlende Binärhistorie transparent.
- STOP/Fehler/Quota führt zu heimlichem Resume, Lernen vor Freigabe oder dritter Modellinstanz: genaue Einmalphase, Register/Rootrelease, kontrollierter eigener Abbruch und unvollständige Checkpoints.

## Task 1: Adapter und feste technische/trainierende Laufwerkzeuge

**Files:** die drei neuen Dateien aus Global Constraints. Keine anderen Codeänderungen, keine Commits/Spiele durch Implementer.

**Interfaces:**
- `BehaviorEnsemble(agent, states, enabled)` als Kontextadapter. Originale 36 States in Archivfolge; ON mit 35 eingefrorenen Netzen plus aktuellem q an Index 18, OFF direkt. Speichert passive Mechanismus-/RNG-/Identitätsbelege; stellt ursprünglichen Instanzzustand nach Verlassen wieder her.
- `admission(path, sha, stage)`: nur `technical` oder `training`. Prüft exklusiven Profilpfad, aktuelle Quelle, Schutzbytes und gebundene Inputs und historische Kontrollen und Runtime. Training braucht tatsächliche technische Root-Annahme und beide feste Starts. Neue HEAD/Dateien erlaubt; alte Quellen und Modelle bleiben bytegleich. Kein Aufruf historischer Admission gegen neuen HEAD.
- `worker_command(a,path,sha,state_path,role)`: role `technical` oder `on48`/`on49`. Historischer interner Agent.role bleibt `control`; äußere Metadaten nennen `behavior=ensemble` und Start, niemals falsches Kontrolllabel.
- `check_technical(receipt, historical)`: vier feste Fälle, OFF-Originalgleichheit, ON-Exposition, alle eingefrorenen Gewichte/RNG-/Lernerinitialzustände, Reward/Replay. Start 49 nur ohne Spiel initialprüfen. Vergleich der alten paired_rows darf bei OFF exakte native/trajectory/audit-Werte verwenden; bei ON keine Gleichheit fordern.
- `validate_prefill_file(path,a,role)`, `approve_prefill(a,sha,review_path,review_sha)`, `validate_final_receipt(path,a,sha,role)`: eigene tatsächliche gespeicherte Replays/Tensoren/Adam/Counter/Rewardformeln/eingefrorene Identitäten prüfen. Release bindet beide Vorlaufhashes und Rootreview, erst danach ursprüngliche Worker lernen lassen.
- Owner CLI wie bisher `--admission --admission-sha --usage-file --stage`. Technical genau ein Worker; Training exakt beide ON-Worker parallel, keine automatischen weiteren Phasen. CLIdetails im Implementerbericht eindeutig angeben. Root hält jede Aufnahme separat.

- [ ] Synthetische Negativ-/Grenztests schreiben und tatsächlichen erwarteten fehlenden Vertrag ausführen. Produktionsarchive, Spiel- und Simulatorzugriffe in Tests sperren.
- [ ] Hookgleichheit mit Originalstapel; einmalige Forwards, aktuelle Lerngewichte, OFF-Bypass, keine Aliase oder RNG-Änderung, Exceptioncleanup, leere Batches und Reset testen. Originales `_learn` mit demselben kleinen synthetischen Replay und RNG mit/ohne ruhenden Adapter muss tatsächlich identische q/Target/Adam liefern; keine eingefrorenen Gradienten.
- [ ] Alte unveränderte `training_config`, `make_learner`, `rollout_plan`, `play_one`, `reward_audit`, Replay-/Hash-/Lifecyclehelfer verwenden. Kein Patching alter globaler PROFILE/ARMS und keine Kopie des vollständigen Frameworks. Nur profilspezifische Metadaten/Admission/Barriere/Abnahme ergänzen.
- [ ] Historische Schluss-/Receipt-/Modellpins sowie Kontrollkonfiguration und Startpläne prüfen. Vier Technikfälle mit unveränderten Originalinitialisierungen; OFF gegen tatsächliche ursprüngliche Technikreceipt. Alle Rewards weiter originale Kontrollformel.
- [ ] Tatsächliche Spielchronologie, native Labels, sichere vollständige Spielgrenzen und Signal/STOP-Verhalten erhalten. 40 Vorlaufspiele, Nullupdates, Rootrelease, danach 400 Spiele und 60.000 Updates. Eigene finale Replays und nur finale Einzelnetze speichern; keine automatische interne Leistungsprüfung.
- [ ] Gezielt neue Suite plus vorhandene Matchgewichtsstudientests ausführen (genauen existierenden Testpfad ermitteln), Threads 1, venv `-B`, TMPDIR=/private/tmp, ohne pytest-Cache. Kein unnötiger Gesamtlauf. Tests/Dateihashes/Interfaces in externem Bericht; unabhängiger finaler Review und Rootprüfung vor Quellencommit.

## Task 2: Getrennte reale Aufnahmen

**Files:** Profil `experiments/analysis/ensemble_behavior_20261109/`, Spec/Plan, Arbeitsstand. Keine produktiven Änderungen.

- [ ] Aktuellen abgeschlossenen MATCH38-Stand und historische Kontrollarchive prüfen; noch keine neuen Spiele. Vorab einmaliger begrenzter Seedcheck für die 60 künftigen Leistungskarten; Trainingskarten absichtlich dieselben wie bei den Kontrollen, Originalbelege wiederverwenden. Grenzen nennen.
- [ ] Nach Quellcommit frische Quota und Prozesskontrolle, separate technische Aufnahme. Exakt vier Spiele plus Initialcheck für Start 49 ohne Spiel; Originalvalidator und unabhängige Artefaktprüfung, Rootclosure. Bei Fehler keine automatische Erweiterung.
- [ ] Erst nach wirklicher Technikannahme Training separat aufnehmen, genau zwei Worker, beide 40er-Vorläufe prüfen. Tatsächliche Replays, Optimizer, eingefrorene Tensoren und Hookaktivität unabhängig prüfen; originale Worker durch gehashte Root-Freigabe fortsetzen. Keine ON/OFF-Trajektoriengleichheit fordern.
- [ ] Beide vollständigen 400er-Lernteile ohne Zwischenwahl abschließen, Endmodelle, Adam, Replays und 60.000 Updates unabhängig prüfen, Root-Originalvalidatoren unter eingefrorener Quelle. Eigene Prozesse beenden und Abschluss vor Freigabe der Quellen versiegeln.
- [ ] Trainingsergebnis samt Grenzen sinnvoll committen und pushen, Hauptkopie verlustfrei aktualisieren. Erst danach bereits vorab fixierten 200er-Vergleich separat bauen und aufnehmen; keine automatische Folgephase.
