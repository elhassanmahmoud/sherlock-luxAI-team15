# Task 2 — kontrolliertes Training und Wirkungsbelege

Status: Implementiert; unabhängiger Review und Root-Abnahme ausstehend. Keine eigenen Commits oder Pushes. Basis laut Root: `9ad6e9e`. Während der vier technischen Spiele ausschließlich gelesen; erste Python-Datei erst nach ausdrücklicher Freeze-Aufhebung geschrieben.

## Dateien und feste Schnittstellen

- `scripts/artillery_alignment_study.py`: `prepare --source ... --out ...`, `run --prepared ... --arm ... --name ... --supervisor-state ...`, Python-Validatoren `check_prepared`, `validate_prefill_bundle`, `compare_prefill_proofs`, `validate_final_receipt`.
- `scripts/artillery_alignment_supervisor.py`: `start --prepared ... --out ... --python ... --expected-head ...`; `stop`. Quota-Datei standardmäßig und verbindlich `experiments/analysis/artillery_alignment_20261108/operations/usage.json`, STOP verbindlich `/private/tmp/sherlock-artillery-alignment-20261108/STOP`.
- `tests/test_artillery_alignment_study.py`: ausschließlich synthetische Tests. Kein zusätzliches Beobachtermodul notwendig.

Vier feste Arme `control43/aligned43/control44/aligned44`, feste Laufnamen `20261108_artillery_alignment_<arm>`. Komponente 18, frischer Adam/leerer Replay, identisches Start-Q/Target. Direkter enger `experiment.Learners`/`common.play_game`-Loop mit unverändertem finetune-Rezept, fester Gegner-RNG-Folge und vorhandenen Initial-/Prefill-/End-/V14-Validierungsbelegen. Keine Änderung bestehender Module oder Studien.

Je Arm exakt 40 Vorläufe, dann nach Paarfreigabe 400 Lernspiele und Diagnose bei 0/400 Lernspielen (je 16, insgesamt 32). Endcheckpoint allein. Erwartete Zähler 60.000→72.120→193.320 env_steps, 60.000 Updates je Arm. Training 9.430.000–9.430.199 bzw. 9.440.000–9.440.199; Vorlauf jeweils +5.000; Diagnose 9.600.000–9.600.003. Keine Smoke-CLI, Wiederaufnahme oder automatische Wiederholung.

## Beobachter und Vorlaufannahme

- Temporäre Instanz-Hooks um `_artillery_ok`, `_plan_damage`, `act`, `update`, stets im `finally` entfernt/zurückgesetzt. Tatsächliche Helper-Rückgabe wird unverändert zurückgegeben. Der alternative Flagwert wird nur für den zweiten Helper-Aufruf gesetzt und restauriert.
- Vor/nach beiden Helper-Aufrufen werden Config/Trainingsmodus, Estimator einschließlich beobachteter Gegner-Sets, der vom Helper gelesene Punkteplan, gesamter Kontext/SAP und eigener/globaler RNG gehasht. Keine Kontextkopien im Artefakt, kein Modell-/Umgebungssnapshot je Ereignis.
- Konkrete UID und SAP-Tupel; tatsächliche Objektidentität am abschließenden `_plan_damage`-Aufruf; gespiegelte native Koordinaten, kanonische `_prev_actions` und reale Aktionsklasse an der Replay-Schreibposition. Fehlende/abweichende Herkunft führt zum Fehler. Spätere Abbrüche werden getrennt von ausgeführten zusätzlichen SAPs gezählt. Die dafür nötigen deaktivierten späteren SAP-Erzeuger sowie aktive `art_sap`, `art_splash`, `sap_no_overkill` werden explizit geprüft.
- Vollständige kompakte Ereignisse nur für den Vorlauf in `prefill_events.jsonl`; später pro Spiel Laufzeitzähler und Transkript-Hash. Der unabhängige Vorlaufvalidator liest Rohereignisse erneut, prüft eindeutige/chronologische UID-Schritte und berechnet Zähler/Hashes neu.
- Beide Arbeiter warten vor Gradienten. Supervisor verifiziert beide eingefrorenen Bündel und identische Initialparameter/Adam/RNG/Schedule sowie genau den einen Config-Unterschied. Unterschiedliche Trajektorien/Replay-Größen sind zulässig. Jeder Aligned-Arm braucht mindestens einen konkret ausgeführten zusätzlichen SAP. Nullbefund bewahrt den Vorlauf, beendet das Paar, setzt STOP und startet keine zweite Kartenfamilie.

## Betrieb und Abschlussbeleg

Vorhandene Prozess-/Ressourcensperren, genaue Worker-Eigentumsbelege, maximal zwei Worker, AC, echte frische Quota <100, Quellen-/HEAD-/Plan-/Interpreter-/Input-/V14-/ZIP-Prüfungen. Einmaliger Supervisor-Launchmarker und feste exklusive Laufverzeichnisse. Ein Fehler stoppt nur eigene Prozesse; kein Neustart.

`final_receipt.json` bindet Quelle, vollständige Config, Initialtensor, tatsächliche Zähler und neun Artefakte inklusive Replaydatei. Abschluss prüft vollständige Kartenfolge/Diagnosen, CSV gegen Rohzeilen, unveränderte isolierte Validierungsidentität, endliche/veränderte Q-/Target-/Adam-Tensoren, 60.000 Adam-Schritte und den tatsächlich durch `_prove_end` ausgeübten Loader. Der Abschluss bleibt `eligible=False`: technischer Trainingsnachweis, keine Stärke-/Übernahmeentscheidung.

## Tatsächlich ausgeführte Prüfungen

Interpreter: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python`.

1. RED: neue Testdatei vor Studienimplementierung, erwarteter Importfehler des noch fehlenden Moduls (Exit 2).
2. Erster GREEN: 39 Tests bestanden, 2,63 s.
3. Rohereignis-/Endbeleg-/Schutzfälle: 52 Tests bestanden, 2,73 s.
4. Abschließend `-B -m pytest tests/test_artillery_alignment_study.py -q`: **54 bestanden in 3,33 s**, Exit 0.
5. `git diff --check`: Exit 0.

Die letzten zwei Tests führen den echten Controller nur mit ersetzten Spiel-/Modell-/Umgebungsfunktionen aus: ohne reale Ausführung genau 40 False-/400 True-Lernfreigaben, zwei Diagnoseblöcke und genau einmal finales Speichern; Ablehnung nach Vorlauf erzeugt null Trainings-/Diagnoseaufrufe und keinen Abschlussbeleg. Andere Tests prüfen gespiegelte/finale/replay-Aktionen, spätere Abbrüche, falsche SAP-Objekte, Helpermutation/-ausnahme mit Hook-Restauration, Rohereignismanipulation, Nullbefund und fehlende/gemutierte Endbelege.

Keine echten Spiele, kein realer Lernlauf, keine Lernupdates und keine Vollsuite durch diesen Implementer. Keine Produktionsvorbereitung mit echten V14-Gewichten ausgeführt. Quellen-/Modelllauf-Freeze und unabhängige Review-/Abnahmetests verantwortet Root. Arbeitsstand und Experimentprotokoll bleiben bei Root. Zum Berichtszeitpunkt keine laufenden eigenen Prozesse und kein bekannter Implementierungsblocker.

## Fixrunde 1 — echter Belief im Spielkontext

Der unabhängige Gesamt-Callchainreview fand einen P1: `features.make_context` liefert das lebende `Belief`-Objekt unter `ctx['belief']`, während `_tree` bisher nur Container/Mengen projizierte. Der streng typisierte Hasher hätte daher beim ersten echten Helper-Aufruf `TypeError: Unsupported identity state: Belief` ausgelöst. Die bisherigen vereinfachten Testkontexte enthielten dieses Feld nicht.

Eng korrigiert ausschließlich in Studie und Testdatei: Der bekannte exakte Typ `Belief` wird explizit mit Typkennzeichnung und sämtlichen `vars`-Feldern rekursiv projiziert. Verschachtelte Mengen, Listen/Tupel und Arrays bleiben vollständig erfasst. Kein beliebiger Objekt-/`repr`-Fallback; unbekannte Objekttypen werden weiterhin abgewiesen. Der Supervisor blieb unverändert.

Tatsächliche Prüfung mit demselben oben genannten Interpreter:

1. RED vor dem Fix: `-B -m pytest tests/test_artillery_alignment_study.py -q -k real_belief --tb=short` — **4 erwartete Fehler, 54 abgewählt, 2,60 s**, Exit 1. Alle vier Fehler exakt `Unsupported identity state: Belief`.
2. GREEN nach dem engen Fix: `-B -m pytest tests/test_artillery_alignment_study.py -q` — **58 bestanden in 2,44 s**, Exit 0.

Die neuen Fälle erzeugen einen echten `Belief`, verarbeiten eine synthetische Beobachtung und verwenden den tatsächlich von `features.make_context` erzeugten Kontext; weder Spiel noch Netzberechnung. Mutationstests verändern während des alternativen Helper-Aufrufs jeweils `energy_map` (Array), `relic_positions` (Menge) und `records` (verschachtelte Liste/Tupel). Alle drei Mutationen werden als Verletzung der Read-only-Prüfung abgewiesen; Flag/Hooks werden restauriert. Eine tiefe Kontextkopie behält denselben Zustandsdigest.

Root-Abnahme und gezielte unabhängige Nachprüfung des Fixes bleiben offen. Keine weiteren Änderungen, Spiele, Lernupdates, Commits oder Pushes; keine laufenden eigenen Prozesse.
