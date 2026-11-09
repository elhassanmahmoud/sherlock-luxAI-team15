# Task 1 – Implementerbericht

## Ergebnis und Grenze

Die drei neuen Dateien sind implementiert; alte Quellen, Gewichte und historische Studien bleiben unverändert. Keine echten Archive geladen, keine Simulator- oder Modellspiele, kein Training außerhalb künstlicher Testnetze, keine Commits. Noch keine reale technische Abnahme, keine Aussage über Laufzeit oder Spielstärke.

- `scripts/ensemble_behavior_study.py`: 590 Zeilen, SHA256 `d2c3ef012f5c09a94761bd768b013074d7b4498321cd0d7c9344efac3ce75863`.
- `scripts/ensemble_behavior_owner.py`: 109 Zeilen, SHA256 `e7f0aa6dc77a2416d115cf1e2f6fe632353540d11b4c26d4c33b25576cea2cde`.
- `tests/test_ensemble_behavior_study.py`: 504 Zeilen, SHA256 `73662170fc6427c637e6b76b12ea150e52043c829da3e022415788a421f4af20`.

Der Adapter ersetzt nur den instanzlokalen `_act_est`-Aufruf. Sein temporärer q-Hook verwendet den bereits berechneten Lernoutput an Originalindex 18 und genau 35 eingefrorene Mitglieder. Er wird bei Rückkehr und Ausnahme entfernt; eine zweite Adapterinstallation auf derselben Instanz wird verweigert. q/Target/Adam bleiben dieselben Objekte, `extra_q` bleibt leer. OFF führt keine zusätzlichen Netzforwards aus. Kopien der passiven Roh-Q-/Maskenbelege entstehen vor der maskierenden Numpy-Sicht des Core.

Alte `training_config`, `make_learner`, `rollout_plan`, `play_one`, Reward-/Aktionsaudit, Replay-/Identitäts-/Hash- und Lifecyclehelfer werden tatsächlich importiert. Historische Zulässigkeit nutzt den vorhandenen reinen `accepted_training`-Prüfer, nicht eine alte Admission gegen neuen HEAD. Neue Logik beschränkt sich auf Adapter, eigenes Profil/Metadaten, gemeinsame Vorlaufsperre, tatsächliche Artefaktprüfung und den schmalen Owner.

## Tatsächliche Prüfung

Final ausgeführt:

```text
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_ensemble_behavior_study.py tests/test_match_weight_study.py tests/test_match_weight_owner.py
```

**72 passed in 3.34s; Exit 0.** Darunter 28 neue Fälle und 44 bestehende Matchgewichtsfälle. Log: `/private/tmp/ensemble-behavior-impl/final-tests.log`, SHA256 `594bf4536b185229d4b2bb68729b09a3c1788d04f8af6de090665f8c6e5412bc`; Exitbeleg daneben `final-tests.exit`.

Reale Red/Green-Schritte liegen in demselben Ordner:

- `red-1.log`: erste Fehlstelle als Fixturefehler wegen fehlendem Modul; anschließend als klarer Testfehlbefund präzisiert.
- `red-2.log`: 1 erwarteter FAIL, 13 SKIP wegen noch fehlendem Einstiegspunkt; `green-adapter.log`: 14 PASS.
- `red-3.log`: 3 FAIL für fehlende Worker-/Vorlauf-/Runtimeverträge; `green-barrier.log`: 17 PASS.
- `red-4.log` / `red-owner.log`: fehlender Technikprüfer/Owner; `green-owner.log`: 26 PASS.
- `red-review.log`: 2 FAIL für Doppeladapter und fehlenden historischen Technikhashlink; `green-review.log`: 2 PASS.
- `red-owner-status.log`: 2 FAIL für den fälschlich fortbestehenden Wartestatus; anschließend `green-lifecycle.log`: 27 PASS.
- `red-golden-fields.log`: 1 FAIL für ungeprüfte Golden-Metadaten; finale gemeinsame Suite oben grün.

Geprüft sind geordnete 36 Beiträge, genau einmalige Forwards, Verwendung später veränderter Lerngewichte, Aliasfreiheit der Belege, Aufbau ohne RNGänderung, OFF/Reset/leere Entscheidung und Ausnahmebereinigung. Ein echter originaler `_learn` auf identischem künstlichem Replay/RNG liefert mit ruhendem Adapter exakt dieselben q-/Target-/Adamzustände wie ohne Adapter; eingefrorene Netze erhalten keine Gradienten.

Synthetische Aufnahme-/Artefaktfälle prüfen historische Source-Untermenge, ursprünglichen Technikreceipt-Hash, geänderte Konfigurationen/Counter/Adam, gemeinsame manuelle Freigabe, einmalige Ownerphase und eigenen Fehlercleanup. Ein künstlicher Worker erreicht exakt 40 Vorlaufspiele auf einer Env, stoppt ohne Freigabe und sichert `incomplete.pth`, ohne Lernupdates oder `final.pth`. Tensorlesen ist standardmäßig gesperrt; Artefakttests erlauben nur explizit erzeugte künstliche Payloads. Spielaufruf und echter Simulatorimport sind gesperrt; der Workerfall verwendet eine FakeEnv.

## Aufnahmevertrag

`admission(path, sha, stage)` erlaubt ausschließlich `technical` oder `training`, Schema 1, Profil `ensemble_behavior_20261109`. Gemeinsame Pflichtfelder:

```text
schema_version=1, profile, stage, start_authorized=true, allow_battery=true,
starts=[48,49], historical_runtime_gap_acknowledged=true,
root, out, python, plans, source, protected, inputs, stop_file,
runtime, training_completion, v14_source, config, rollout_plans, initial
```

- `out`: ausschließlich `<ROOT>/experiments/analysis/ensemble_behavior_20261109/<stage>_v1`; Owner verweigert bereits vorhandene Phase, keine Wiederaufnahme.
- `source`: tatsächliche `source_identity(ROOT, python, plans)` der neuen Quelle. `plans` muss die alten gebundenen Plandateien zusätzlich zur neuen Spec/Plan enthalten, damit alle 406 alten Dateihashes als unveränderte Untermenge passen. Neuer HEAD und zusätzliche Dateien sind gegenüber historischer Quelle erlaubt. Neue technische und Trainingsaufnahme müssen denselben aktuellen `source`-Block verwenden.
- `runtime`: tatsächliche Ausgabe von `runtime_identity()` im verwendeten Interpreter: `python=sys.version`, `packages` mit Versionen für torch/numpy/jax/jaxlib/luxai-s3. Roots zusätzliche aktuelle Umgebungsdatei kann unabhängig als Input gebunden werden.
- `protected`: die beiden produktiven V14-Pfade mit SHA `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8` und `Gruppe15.zip` mit SHA `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`.
- `training_completion`: akzeptierte Gesamtclosure mit festem SHA `41cb8fa0689bb1a5b98bbd692e147fceb8471b5e72387b661b06e7484c244b94`.
- `config`: eine flache vollständige historische Kontrollconfig, keine Rollenmap; `w_match=2`.
- `rollout_plans`: `{"48": <alter 440er-Plan>, "49": <alter 440er-Plan>}`, exakt ursprüngliche Reihenfolge.
- `initial`: `{"48": <control-initial.json.initial>, "49": <control-initial.json.initial>}`; jeweils q/Target/Optimizer-Digests.
- `v14_source`: gebundene originale V14-Datei. Der reale Worker prüft alle 36 States und die tatsächliche abgeleitete Kontrollconfig erneut.

### Vollständig ableitbare historische Inputliste

`inputs` ist eine absolute Pfad→SHA256-Map. Notwendig sind:

1. `training_completion` selbst.
2. Für beide `completion.pairs["48"/"49"]`: `admission`, `state`, `closure`; deren gespeicherte Hashes müssen stimmen.
3. Für beide historischen Rollen `control` und `match` je Paar: `models[role].path` und `.receipt`. Der vorhandene geschlossene Prüfer bindet bewusst beide ursprünglichen Arme; die MATCH-Dateien werden hier **nur gehasht**, niemals als neue Lernstarts geladen.
4. Im jeweiligen akzeptierten Kontrollverzeichnis zusätzlich `control-initial.json` und `prefill.json`; ihre Hashes müssen auch in der akzeptierten Kontrollreceipt stehen.
5. Die `technical_receipt` aus beiden alten Trainingsaufnahmen (derselbe Pfad) und sämtliche darin unter `files` gebundenen Dateien. Zusätzlich muss ihr Hash dem ursprünglichen `train.inputs[train.technical_receipt]` entsprechen. Kein Austausch durch bloß neuen Inputhash.
6. `v14_source`, neue Ownerdatei (Owner prüft ihren Inputhash explizit), sinnvollerweise alle drei neuen Dateien sowie alle neuen Plan-/Rootvorbereitungsbelege. Sourcebindungsdateien sind unabhängig vollständig in `source.files` gepinnt. Zusätzliche Inputs, etwa Goldenreferenz, aktueller Runtimebericht und spätere Seedannahme, sind erlaubt; der Trainer erfindet daraus kein neues Seedgate.

Es müssen keine historischen Replayarchive neu geöffnet werden. Die historische Kontrolle wird über die fest versiegelten Abschluss-, Receipt- und Modellbindungen übernommen. Die vollständigen alten Bibliotheksbinärstände/RNG-Snapshots fehlen weiterhin; diese Grenze wird ausdrücklich bestätigt, nicht durch gleiche Venvpfade als bewiesen ersetzt.

### Zusätze für `training`

`technical_receipt`, `technical_acceptance`, `source_members` sowie technische Receipt und sämtliche `receipt.files` in `inputs`. Die tatsächliche Receipt liegt unter `technical_v1/technical/receipt.json`. Rootannahme braucht `status="PASS"`, `profile`, denselben `source` und `technical_receipt_sha256`. `source_members` sind exakt die 36 Digests aus `receipt.games[0].mechanism.source_members`.

Technik prüft OFF dann ON, je beide bekannten Fälle fortlaufend, eine Env **vor** Agentinitialisierung. OFF vergleicht die zehn ursprünglichen `paired_row`-Felder, Kontrollrewardarrayhashes, Initialzustände, 60000→60303→60606, tatsächliches epsilon, Nullverlust/Updates und Ergebnisflags. `masked_final_actions=16/65` bleibt legitim. Der globale alte MATCH20-Replayhash wird nicht verwendet. ON braucht geänderte legale Präferenz und geänderten nativen Aktionsdigest; keine ON/OFF-Trajektoriengleichheit.

## CLI und Phasen

```text
python -B -m scripts.ensemble_behavior_owner --stage technical --admission TECH.json --admission-sha SHA --usage-file USAGE.json
python -B -m scripts.ensemble_behavior_owner --stage training --admission TRAIN.json --admission-sha SHA --usage-file USAGE.json
```

Dies sind getrennte manuelle Aufnahmen, kein automatischer Folgestart. Technical startet genau Worker `technical`; Training genau `on48` und `on49` parallel. Workerkommando wird ausschließlich vom Owner gebaut:

```text
python -B -m scripts.ensemble_behavior_study worker --admission TRAIN.json --admission-sha SHA --owner-state OUT/state.json --role on48
```

Der interne Agent behält `role="control"` für den unveränderten Rewardaudit. Äußere Trainingsreceipt nennt `role=on48|on49`, `behavior="ensemble"`, Start, Profil, Phase, Quelle, Admissionhash und exaktes Kommando. Spielezeilen behalten das interne Rewardlabel und kennzeichnen zusätzlich `behavior`/`start`.

Nach beiden Vorläufen entstehen je Rolle `prefill.json`, eigenes Replay/Checkpoint/Rewardarray und `waiting.json`. Owner meldet nur Readiness. Root prüft mit `validate_prefill_file(path,a,role)` die echten Dateien und schreibt einen Beleg mit `status="PASS"`, `profile`, `source`, `admission_sha256` und `prefill_sha256={on48:SHA,on49:SHA}`. Danach ausdrücklich:

```text
python -B -m scripts.ensemble_behavior_study approve-prefill --admission TRAIN.json --admission-sha SHA --review ROOT_REVIEW.json --review-sha REVIEW_SHA
```

Der Befehl validiert beide Vorläufe erneut und veröffentlicht exklusiv ein einziges gemeinsames `release.json`; vorhandene Datei wird nicht überschrieben. Erst dann lernen beide originalen Worker. Owner setzt seinen Wartestatus nach geprüftem Release zurück und bindet dessen Hash. Nach beiden Exits prüft er mit `validate_final_receipt` eigene tatsächliche Endarchive, 440 Spiele/193320 Envschritte/60000 Adamupdates, finales Replay und die unveränderten 35 Mitglieder. STOP/Fehler erzeugt einen eigenen unvollständigen Checkpoint und niemals eine automatische Ersatzphase.

## Offen vor echten Phasen

Unabhängige Endreview und Rootprüfung der hier angegebenen Bytes, Quellencommit, reale Aufnahme und technische OFF/ON-Reproduktion. Erst danach gemeinsame Vorlaufphase und Root-Freigabe. Tatsächliche Runtimekosten, reale Modellidentitäten und Wirksamkeit wurden durch diese synthetischen Tests nicht gemessen. Die späteren 200 Auswahlspiele haben hier noch keinen Runner und werden erst nach vollständiger Trainingsabnahme separat aufgenommen.
