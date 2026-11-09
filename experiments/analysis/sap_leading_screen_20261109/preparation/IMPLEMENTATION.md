# SAP-Leading: externer Runner zur Root-Prüfung

**Keine echte Ausführung erfolgt.** Diese Fassung implementiert den festen Entwurf `/tmp/sap-leading-screen-plan.md`. Sie startet keine anderen Prozesse, legt keine neue Queue an und enthält weder Training noch Promotion. Aufnahme/Orchestrierung bleiben bei Root. Der Dateiname `sap_leading_eval.py` nutzt bewusst das von den vorhandenen Prozesswächtern erkannte `eval`-Muster.

Dateien für spätere Aufnahme: `scripts/sap_leading_eval.py`, `tests/test_sap_leading_screen.py`. Sämtliche aktuellen Dateien liegen ausschließlich unter `/tmp/sap-leading-screen/`.

## Feste Ausführung

- Profil `sap_leading_screen_20261109`.
- `technical`: einmal OFF auf831006/player_1 und831000/player_0, danach ON auf denselben beiden Schlüsseln, höchstens vier vollständige Ausführungen. OFF prüft303 native Arrays, gemeinsamen Aktionsstreamhash, v2-Punkte/Matchsiege und vollständige Matchdaten gegen das alte Targeting-Manifest. ON benötigt insgesamt mindestens einen tatsächlich ausgeführten Offsetwechsel. Null Exposition schließt die Aufnahme ohne Ersatzspiel.
- Performancejobs: `off_solution`, `on_solution`, `on_direct`; genau40 Spiele je Job. Erste beiden auf9940000–9940019, Direkt auf9940100–9940119, jeweils aufsteigend und Seiten0/1. Zahlen sind bis Root-Abnahme keine Frischebehauptung.
- Root startet die beiden Paneljobs als erste Welle, höchstens zwei Worker. Jeder wartet vor Modellkonstruktion höchstens15 Sekunden auf die Registrierung beider Panelworker im Owner-State. Direkt folgt erst, nachdem beide Paneljobs mit Exit0 beendet sind, als einziger aktiver Worker. Das ist eine Registrierungsschranke, kein Spielwiederholungsmechanismus.
- Pro Rolle dieselbe explizite normalisierte V14-Config und derselbe Agentladeweg, auch im Direktduell. OFF/ON unterscheiden nur `lead_enabled`.36 Mitglieder,79 Merkmale/6 Aktionen, Eval/epsilon0, frozenFalse, AutosaveFalse, LernenFalse. Kein impliziter `common.make_opponent('self:…')`-Ladeweg.
- Vor jedem Spiel und am Ende erzwungene bestehende Quellen-/Input-/Prozess-/Quota-/AC-/STOP-Prüfung; während `act` spätestens alle10 Sekunden, STOP bei jedem Aufruf. NumPy-/BLAS-/Torch-Threadzahl1. Kein eigener Wachhalter oder Subprozess; Root besitzt Orchestrierung und Abbruch der Prozessgruppen.

## Externe Root-Aufnahme, nicht durch den Runner erzeugt

Für Technik und Performance **getrennte** JSON-Dokumente, jeweils mit ihrem vollständigen SHA256 im CLI. Mindestvertrag:

```json
{
  "schema_version": 1,
  "profile": "sap_leading_screen_20261109",
  "stage": "technical oder performance",
  "start_authorized": true,
  "root": "absoluter Studiencheckout",
  "out": "CHECKOUT/experiments/analysis/sap_leading_screen_20261109/technical_v1 oder performance_v1",
  "python": "exakter angeforderter Interpreterpfad",
  "plans": ["absolute gebundene Planpfade"],
  "source": "tatsächliches source_identity(root,python,plans)-Objekt",
  "protected": {"absolute beide V14-Gewichte und ZIP": "jeweils fester SHA256"},
  "inputs": {"alle absoluten Eingabepfade": "SHA256"},
  "config_manifest": "gebundene JSON mit source_sha256 und source_config",
  "config": "vollständiges source_config-Objekt, ausschließlich frozen=False normalisiert",
  "stop_file": "absoluter Root-STOP-Pfad"
}
```

Die Stringbeschreibungen für `source`/`config` sind schematische Hinweise, keine zulässigen tatsächlichen Werte. Aufnahme verlangt echten Quellenbestand samt Interpreter/Engine, richtige absolute Checkoutposition und Original-V14-Pins. Für `config_manifest` eignet sich die bestehende `experiments/runs/20261108_sampled_target_prepared/manifest.json`. Der Runner lädt nur dessen JSON-Config bei Aufnahme; tatsächliche Checkpointloads erfolgen erst nach Guard und einmaliger Launchreservierung im späteren echten Job.

Technikinputs müssen das alte `experiments/analysis/continuation_20261102/targeting/manifest.json` (SHA90324b…c435) und genau die zwei benutzten gzip-Dateien mit ihren Originalhashes enthalten. Diese werden vor dem ersten Modell gebunden. Der Quellenstand bleibt über Technik und Performance gleich; keine historische Quelle wird als heutiger HEAD ausgegeben.

Performanceaufnahme verlangt zusätzlich:

- `technical_receipt`: absoluter Pfad zum vollständig erzeugten `technical_v1/technical/receipt.json`, in `inputs` gehasht. Der Receipt muss dieselbe Quelle/Config binden und alle vier erfolgreichen Technikzeilen enthalten. Alle durch `receipt.files` gebundenen Rohbelege ebenfalls in `inputs` aufnehmen.
- `seed_acceptance`: absoluter, in `inputs` gehashter Root-Abnahmebeleg mit `status="PASS"`, passendem `profile`, `cohorts={panel:[9940000…9940019],direct:[9940100…9940119]}`, `no_observed_conflicts=true`, nichtleerer `limitations`-Liste und nichtleerem `files`-Inventar aus absoluten Belegpfaden/Hashes. Sämtliche darin genannten Belege müssen ebenfalls in `inputs` stehen. Kein pauschales Nie-verwendet-Versprechen.

## Root besitzt den vorhandenen Owner-State-Vertrag

State enthält `profile,status="running",owner_pid,root,out,python,plans,source,protected,inputs,stop_file,usage_file,admission_sha256,jobs,active`. Dieselben Quellen-/Inputdaten wie Aufnahme; zusätzlich der Aufnahmepfad samt CLI-SHA in `inputs`. `usage_file` bleibt eine tatsächlich aktuelle, vom vorhandenen `check_usage` akzeptierte Kontingentquittung, kein festgehashter veralteter Quotenwert.

Jeder Job unter `jobs[name]` bindet `pid,pgid,owner_pid,argv`. Workerstart im eigenen Prozessgruppen-/Sitzungsführer, Eltern-PID gleich `owner_pid`; maximal zwei aktive Einträge. Requested Interpreter wird über `sys.executable`, restlicher Startbefehl über `sys.orig_argv[1:]` gebunden, damit der bekannte macOS-Framework-argv0-Fall weiterhin funktioniert. Root schreibt Registrierung atomar und verwendet die vorhandenen Start-/Cleanup-Helfer. Kein fremder Prozess wird vom Runner beendet.

Nach Performance alle drei `returncode=0` und `finished_at` setzen, `active=[]`, `status="complete"`. `receipts[job]={path: absoluter Receiptpfad, sha256: tatsächlicher Hash}`. Die Analyse prüft exakt diese abgeschlossenen Prozesse, ihre Startbefehle und Receipts. Kein Analyse-PASS aus noch laufenden oder unvollständigen Daten.

## Spätere CLI nach gesonderter Aufnahme

```sh
python -B -m scripts.sap_leading_eval technical --admission TECH_JSON --admission-sha TECH_SHA --owner-state TECH_STATE
python -B -m scripts.sap_leading_eval run --job off_solution --admission PERF_JSON --admission-sha PERF_SHA --owner-state PERF_STATE
python -B -m scripts.sap_leading_eval run --job on_solution --admission PERF_JSON --admission-sha PERF_SHA --owner-state PERF_STATE
python -B -m scripts.sap_leading_eval run --job on_direct --admission PERF_JSON --admission-sha PERF_SHA --owner-state PERF_STATE
python -B -m scripts.sap_leading_eval analyze --admission PERF_JSON --admission-sha PERF_SHA --owner-state PERF_STATE
```

Diese Zeilen sind Schnittstellenbeschreibungen, **keine jetzige Ausführungsfreigabe**. Reale Worker müssen durch den passenden registrierten Elternprozess gestartet werden. Quelle/HEAD dürfen bis Abnahme nicht wechseln. Kein automatischer Wechsel von Technik zur Performance.

Pro Job genau eine globale exklusive `JOB_launch.json` und ein neues `OUT/JOB/` mit `games.jsonl`, `events_NN.jsonl`, anschließend `receipt.json`. Teilfehler erzeugen `failed.json` und lassen Reservierung/Rohdaten bestehen; kein Resume/Overwrite. Technik speichert alle303 Hookframes je Spiel, Performance nur tatsächlich geänderte Frames. Quelle/Schutzdateien werden vor dem erfolgreichen Receipt nochmals geprüft. Analyse verlangt alle41 Rohdateien je Performancejob; Eingriffszahl muss den Ereigniszeilen entsprechen. Ergebnisse werden ausschließlich einmalig in `performance_v1/summary.json` geschrieben.

Temporärer Messwrapper um `Agent_x._act` erfasst nur den eigenen Agenten, lässt fremde Instanzen direkt zum Original durch und wird im `finally` vollständig restauriert. Der eigene `act`-Wrapper prüft ursprünglichen Rückgabewert, unabhängige öffentliche Auswahlrekonstruktion, maximal einen Offset, Buchhaltung und das nachfolgende Original-Remember. Keine zweite Entscheidung/kein zusätzlicher Forward. Vorige öffentliche Beobachtungen für den Audit bleiben getrennt; keine Zukunfts-/Enginewahrheit zur Auswahl.

## Tatsächlich geprüft; Grenzen

Alle Tests synthetisch, `QNet`-Konstruktion und `torch.load` durch fehlschlagende Wächter gesperrt. NumPy-/Torch-Quellenimporte sind erfolgt; keine echten Gewichte/Tensorarchive gelesen, keine Netze konstruiert, keine Forwards/Spiele/Trainings gestartet. Vorhandene 120-Zeilen-Testmatrizen sind künstliche Pythonobjekte.

Exakter Aufruf (jeweils `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=CHECKOUT`, `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=VECLIB_MAXIMUM_THREADS=1`):

```sh
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B -m pytest -q -p no:cacheprovider /tmp/sap-leading-screen/tests/test_sap_leading_screen.py
```

RED: mit `-k fixed_120_matrix` 1FAIL/29abgewählt, Exit1,0,08s (`RED.log`). Nach erster Umsetzung30PASS0,29s; zusätzliche Aufnahme-/Wrapper-/Ladewegfälle33PASS2,44s. Separates RED für noch fehlende Abschlussprüfung: `-k analysis_requires`,3FAIL/34abgewählt, Exit1,2,26s (`RED_closed.log`). Finale vollständige Datei: **37PASS2,13s, Exit0** (`GREEN.log`). Fehlende/duplizierte Spiele, Score/Draw-Ganzzahlgrenzen, Exposition, geänderte Belegbytes, Mehrfach-/Klassenwechsel, falsches Remember/Buchhaltung, Prozessidentität und unvollständiger Abschluss sind gedeckt.

Reale Aufnahme-/Guard-/Engineintegration ist noch nicht ausgeführt. Root-Aufnahmedokumente und echter Owner-State existieren aus dieser Vorbereitung nicht. Keine große Projekttestsuite oder echte historische Reproduktion wurde behauptet. Der unabhängige Review erhält die feste Fassung; erst Root entscheidet über Aufnahme und tatsächliche Technikspiele.

Feste Hashes: Runner `e434dfcd81a159e3f0921c9c11011768fdb3910e4aaf79f5f58eeb071059226d`; Tests `d365cc0846ce24857a63905427d8b8cdbb4fdad64c38fc93fd71a182796a15b3`; GREEN-Log `483b1f9778476c61b674ee2f524d6dfac816c110c24878ec102e1b363411efd1`.

## Kleiner separater Root-Launcher (UNRUN)

`/tmp/sap-leading-screen/run_owned.py` orchestriert genau **eine** ausdrücklich aufgenommene Phase mit den bestehenden `compute_lock`, `spawn_owned`, `save_state`, Fog-`guard` und `shutdown_owned`-Helfern. Technik startet einen Worker; Performance die beiden Panelworker, nach deren erfolgreichem Ende den Direktworker. Keine freie Queue, keine Analyse danach, kein Technik→Performance-Übergang, kein Retry. Die Ausgabephase darf noch nicht existieren; erstes Statefile und alle Workerlogs entstehen exklusiv. Danach aktualisiert allein das vorhandene `save_state` diesen State atomar. Signale setzen den gebundenen STOP, alle registrierten eigenen Gruppen werden im `finally` aufgeräumt. Kein eigener Wachhalter/Caffeinate wird gestartet.

**Vor Root-Aufnahme** den tatsächlichen SHA256 dieses Launchers zusätzlich unter seinem absoluten aufgelösten Pfad in `admission.inputs` binden. Er verlangt diese Bindung und denselben angeforderten Interpreter wie die Worker. Kontingentquittung muss tatsächlich aktuell und extern bereitgestellt sein. Ohne AC sperrt der erste vorhandene Guard bereits vor Ausgabe-/Workerstart.

Exakter späterer Aufruf **aus dem Studiencheckout**, mit echten extern erzeugten Aufnahme-/Hash-/Usagewerten:

```sh
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B /tmp/sap-leading-screen/run_owned.py technical --admission /ABSOLUT/technical-admission.json --admission-sha TECH_SHA256 --usage-file /ABSOLUT/usage.json
# Separater späterer Root-Entscheid, nie automatisch anschließend:
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B /tmp/sap-leading-screen/run_owned.py performance --admission /ABSOLUT/performance-admission.json --admission-sha PERF_SHA256 --usage-file /ABSOLUT/usage.json
```

Die Pfad-/Hashplatzhalter müssen vor einem tatsächlichen Root-Aufruf konkret ersetzt werden. Launcher ausschließlich als Text vorbereitet; **keine Imports, Syntaxprüfung, Tests oder Ausführung dieses Launchers**. Die37 Runner-Tests sind kein Ausführungsnachweis für diesen später hinzugefügten Text. Statischer unabhängiger Review ist separat angefragt. Keine Modellstartfreigabe aus diesem Abschnitt.
