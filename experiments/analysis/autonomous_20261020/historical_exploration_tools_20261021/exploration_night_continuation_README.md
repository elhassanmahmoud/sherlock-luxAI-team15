# Feste Nachtfortsetzung — nur vorbereitet

Der Koordinator startet ausschließlich die vorab vereinbarte Restfolge. Kein Modellimport im Koordinator, keine Promotion, keine Git-Schreiboperation, keine Agentenänderung, keine Reparatur, kein Resume und keine Anpassung von Starts, Horizonten oder Gates nach Ergebnissen. Bestehende Helfer bleiben byte-identisch in `/tmp`; der Paar-Wrapper läuft von seinem bereits eingefrorenen Repositorypfad.

## Zulässiger Start

Aus dem Repository, erst nach vollständig abgeschlossenem s47 und erfolgreich geschriebenem Audit mit dem festen Auditor `2f4f1472d5e71e548ec444252e4503cd3691edf289e939b353e719472cda9574`:

```sh
.venv/bin/python -B /tmp/exploration_analysis.py --audit-pair --run-seed 47 --confirm-no-heavy-work
```

Dieser Audit muss schon existieren; der Koordinator erstellt ihn nicht und überschreibt ihn nicht. Root darf danach vor dem Koordinatorstart noch Daten-/Dokumentationsänderungen committen. Der Koordinator überprüft den Übergang vom s47-HEAD mit der unveränderten `head_transition`-Policy dieses Auditors und verlangt sonst identische Pythonquellen, Interpreter und geschützte Modelle. Das Präregistrierungsdokument muss exakt dem im s47-Audit gespeicherten Plan-SHA entsprechen; dieser SHA wird eingefroren und muss auch in den Audits für s48 und s49 identisch sein. Plan-Checkboxen bleiben deshalb bis Pipeline-Ende unverändert.

Erst nach Root-Review und Freigabe starten:

```sh
.venv/bin/python -B /tmp/exploration_night_continuation.py --run
```

Ab diesem Start bleiben HEAD, vollständiger Pythonquellensatz, Interpreter, Modelle und Helfer bis zum Pipeline-Ende exakt eingefroren. **Die `/tmp`-Helfer während der Pipeline nicht ins Repository kopieren:** neue Pythondateien würden den Quellensatz ändern. Keine andere schwere Arbeit gleichzeitig starten. Root bleibt zur Übernahme verfügbar.

Reine synthetische Tests:

```sh
python3 -B /tmp/exploration_night_continuation.py --self-test
```

## Feste Folge

1. s48: beide frischen 3.000-Spiele-Arme mit unverändertem Curriculum; anschließend Auditor.
2. s49: dieselbe Folge; anschließend Auditor.
3. Aggregation aller drei geprüften Starts.
4. Beschreibende Q-Margin-Diagnose.
5. Fester Ensemblebau: alle Starts, keine Netzauswahl.
6. Fünf Entwicklungsarme mit je 240 Spielen.
7. Ausschließlich bei einem qualifizierten 21-Netz-Entwicklungssieger und ausreichender Restzeit: separater Confirmation-Runner, der die bereits festgelegten frischen und bedingten direkten Gates durchsetzt.

Das Methodengate der Aggregation beendet diese feste Ensemblefolge nicht. Ohne Entwicklungssieger endet der Koordinator vollständig mit `no_promotion_no_development_candidate`. Ein frisches oder direktes statistisches Gatefail im Confirmation-Runner ist ebenfalls ein vollständiges Ergebnis ohne Promotion. Selbst ein bestandener Direktvergleich übergibt nur an die technische Schlussprüfung.

## Zeitregeln

Vor jedem neuen Paar werden ausschließlich vollständige bisherige Paare berücksichtigt. Pro Trainingsarm werden sowohl `manifest.runtime_secs` als auch die äußere Child-Walltime gelesen; der größere Wert zählt. Evaluationen verwenden die vollständigen Job-Start-/Endzeiten.

```
Paarbedarf = max(Trainingsarm) × 2 × 1,25
           + max(Evaluationsarm) × 2 × 1,25 + 30 Sekunden
Gesamtbedarf = Zahl aller verbleibenden Paare × Paarbedarf + 3600 Sekunden
```

Der Gesamtbedarf muss strikt vor 21.10.2026 **03:59:50 UTC / 05:59:50 Berlin** passen. Eingangsdaten, Maxima, Formel und Zulassungsentscheidung stehen im State. Keine Teilstarts oder verkürzten Trainings als Ersatz.

Nach den Paaren erhalten Audits 180 Sekunden, Aggregation 120 Sekunden, Q-Margin und Ensemblebau jeweils 300 Sekunden als konservative Zulassungsschätzungen. Entwicklung: fünf vollständige bisherige Evalarmzeiten × 1,25 + 30 Sekunden. Confirmation: 1.720 / 240 vollständige Evalarmzeiten × 1,25 + 60 Sekunden. Dies sind Schätzungen, keine Laufzeitgarantien; spätere Starts werden bei unzureichender Restzeit abgewiesen.

Jede neue Phase muss zusätzlich mindestens **900 Sekunden technische Schlussprüfung + 20 Sekunden Cleanupreserve** freilassen. Neue schwere Phasen beginnen niemals ab **03:00 UTC / 05:00 Berlin**. Aktive Arbeit endet spätestens um **03:44:30 UTC / 05:44:30 Berlin**, damit Cleanup und mindestens 15 Minuten technische Prüfung vor 05:59:50 möglich bleiben. Die bestehenden Child-Wrapper behalten ihre eigenen zusätzlichen Cutoff-/Deadlineprüfungen.

## Status, Quellen und Abbruch

Exklusives Verzeichnis:

`experiments/analysis/autonomous_20261020/exploration_night_continuation/`

Es enthält `state.json` und ein eigenes Log je Phase. Bereits vorhandene oder teilweise Verzeichnisse werden abgewiesen. Sämtliche s48-/s49-Laufverzeichnisse, Zustände, Logs, CSVs und Audits sowie alle späteren Ausgabeziele müssen vor dem Start fehlen.

Der State enthält Werkzeughashes, ursprüngliche und finale Identität, den erlaubten initialen HEAD-Übergang, Befehle, echte Jobzeiten, Zeitrechnungen und gehashte fertiggestellte Evidenz. Tool-/Quell-/Modellidentität wird vor und nach Phasen sowie ungefähr alle 30 Sekunden geprüft. Der Koordinator kontrolliert bekannte fremde schwere Prozesse und beobachtet den eigenen Prozessbaum; die Erkennung ersetzt keine systemweite Sperre.

Bei SIGINT, SIGTERM, SIGHUP, Deadline oder Fehler erhält zuerst ausschließlich der aktive Child-Wrapper SIGTERM. Er bekommt bis zu 15 Sekunden für sein eigenes `finally` und die Bereinigung seiner separaten Prozessgruppen. Danach beendet der Koordinator nur noch zuvor als eigene Nachfahren erfasste, weiterhin anhand PID, PGID und vollständigem Kommando übereinstimmende Gruppen. Eine geänderte PPID durch Reparenting ist zulässig; ein wiederverwendetes PID/PGID-Paar mit anderem Kommando wird nicht als eigener Prozess behandelt. Fremde Prozesse werden nicht beendet. Dieser Fallback kann sich nur auf beobachtete Prozessabstammung stützen; Root prüft nach außergewöhnlichen OS-/Prozessfehlern den Maschinenzustand.

Unklare oder fehlgeschlagene Guards führen zu `paused_incomplete`, `complete: false`, `requires_root_review: true`. Es gibt keine automatische Wiederaufnahme, Ersatzstrategie oder Reparatur. Scheitert bereits die initiale Werkzeug-/Repositoryprüfung vor der exklusiven Ausgabeerstellung, endet der Prozess mit einem Fehler ohne State; bestehende Dateien bleiben unangetastet.

## Vorbereitungsevidenz

Neun Stdlibtests decken feste Reihenfolge, ausgeschlossene Dreierkandidaten, vollständige Timingpaare, exakte Zeitformeln und strikte Grenzen, s47-Auditidentität, Prozessabstammung sowie Wrapper-first-Cleanup mit gemockten Signalen ab. Zusätzliche Regressionstests weisen geänderte Planinhalte/Audit-Plan-SHAs und wiederverwendete PID/PGIDs mit anderem Kommando ab; RED-Beleg: `/tmp/exploration_night_continuation_plan_pid_red.log`. Erwartete RED-Fehler und GREEN-Ergebnis liegen unter `/tmp/exploration_night_continuation_red.log` und `/tmp/exploration_night_continuation_green.log`. Es wurden keine echten Prozesse beendet, keine Modelle geladen und keine Trainings oder Spiele gestartet. Reale Maschinenintegration bleibt dem freigegebenen Lauf vorbehalten.
