# Artillery alignment — unabhängiger integrierter Review

Basis: `9ad6e9e59128ac8a04fbab214113694e6e098538`. Geprüft: neue Studien-/Supervisor-/Testdateien, Spec und Task2-Plan/Brief/Implementerbericht; zusätzlich Core-Diff `18a81c7` sowie relevante Aufrufketten in Agent, Features, Replay, vorhandenen Validierungs-/Prozess-/Abschlusshelfern.

## Ergebnis: Änderungen erforderlich

**[P1] Tatsächlichen Belief-Kontext vor dem Hashen in unterstützte Daten überführen.** `scripts/artillery_alignment_study.py:164–167` reicht den vollständigen echten `ctx` an `_tree` und anschließend `experiment.state_sha256` weiter. `make_context` setzt jedoch in `agents/sherlock/features.py:689` das lebende `Belief`-Objekt unter `ctx['belief']`. `_tree` unterstützt nur Dictionaries, Listen/Tupel und Mengen; das Objekt bleibt unverändert. Der nachgeschaltete streng typisierte Hasher wirft für `Belief` einen `TypeError` (`scripts/experiment.py:192`). Somit bricht der erste tatsächliche Artillerie-Helper-Aufruf bereits bei der Vorher-Prüfsumme ab, vor dem Vorlauf-Gate und Training. Die bisherigen synthetischen Observerfälle verwenden einen vereinfachten Kontext ohne `belief` und erkennen den Fehler nicht. Enger Fix: den bekannten Belief-Typ ausdrücklich über seine relevanten/gesamten einfachen Zustandsfelder repräsentieren, einschließlich verschachtelter Mengen; keinen beliebigen `repr`-Fallback verwenden. Regression mit echtem Belief im Kontext und einem Belief-Mutationsfall hinzufügen; kein vollständiges Spiel erforderlich.

## Sonstige Prüfung

Keine weiteren konkreten Blocker gefunden. Fester Start/Q/Target/Adam, vier Arme, paarweise Initial-/Gegner-/Kartenbindung und Ein-Flag-Unterschied sind nachvollziehbar. Vorlaufbelege werden aus Rohereignissen erneut berechnet; Gradienten werden erst nach Paarfreigabe aktiviert. NULL-Effekt stoppt ohne Zusatzkarten. Der Observer verfolgt die tatsächliche SAP-Identität, native und kanonische Aktion sowie den realen Replay-Schreibplatz; spätere Abbrüche werden getrennt behandelt. Späte alternative SAP-Erzeuger werden in der Quellkonfiguration ausgeschlossen.

Core: StandardFalse und Inferenzbedingung bleiben erhalten; `_act_est` versorgt den neuen Trainingsfall mit Parameterbeobachtung/-gedächtnis. Die feste Studie setzt `rules_in_training_all=True` auf beiden Seiten, sodass der betrachtete Unterschied innerhalb `_artillery_ok` liegt. Der getrennte bestehende Core-Test-/Frame-Nachweis wurde als dokumentierter Nachweis gelesen, nicht nochmals ausgeführt.

Supervisor: bestehende atomare Zustandsveröffentlichung, exklusive Ausgaben, zwei registrierte Worker, genaue PID/PGID/argv-Bindung, STOP/AC/Quota, Source/HEAD-/Input-/Gewichtsschutz werden korrekt wiederverwendet. Kein automatischer Neustart. Finale Speicherung und tatsächlicher Reload sowie Q/Target/Adam-/CSV-/Chronologie-Prüfungen sind passend. `eligible=False` ist beabsichtigt: technischer Trainingsabschluss ist keine Stärkefreigabe.

## Prüfung und Grenzen

Nur statische Prüfung/Dateilesen; durch diesen Reviewer null Tests, Spiele, Modellvorwärtsläufe oder Lernupdates. Root berichtet separat 99 integrierte Tests PASS. Kein zusätzlicher Spiel-Smoke empfohlen: den konkreten Fehler synthetisch reproduzieren/fixen und nur diesen Fix nachprüfen; danach kann der registrierte Vorlauf als erste tatsächliche Ausführung dienen.

Geprüfte Dateihashes vor Fix:

- Studie: `88723ef50896bf197c71b9e623b0710d37bb3ae2216f1a6f0c925b195bd2fe0c`
- Supervisor: `1c6b37c33f5a2c2098417cf50da07b911976111a2e95a366347b7e26874e929f`
- Tests: `d48893cc951b96d2684796ada2f291f7562301f3603da7cc54d0127ed9329a6d`

Spec-/Qualitätsfreigabe bis zum P1-Fix ausgesetzt. Nach diesem Fix ist eine gezielte Nachprüfung ausreichend; keine weitere umfassende Reviewwelle erforderlich.
