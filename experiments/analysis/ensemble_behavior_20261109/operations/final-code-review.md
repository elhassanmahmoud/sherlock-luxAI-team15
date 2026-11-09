# Abschließender unabhängiger Code-/Methodenreview

**PASS für die unten gebundenen drei Task-1-Dateien; keine offenen konkreten Blocker gefunden.** Runner, Owner, Historienbindung, Goldenvergleich, gemeinsame Vorlaufbarriere und finale Artefaktvalidatoren vollständig statisch gelesen. Beim zuvor geprüften Adapter nur die stabile Doppelinstallationskorrektur und ihren Negativtest nachgeprüft. Kein erneuter breiter historischer Audit.

Tatsächlichen vorhandenen Log gelesen: **72 passed in 3.34s**, 28 neue synthetische Fälle plus 44 bestehende Matchgewichtsfälle. Implementerbericht und Testumfang stimmen damit überein. Keine eigenen Tests, Projektimporte, Archive, Modelle oder Spiele ausgeführt. Dies ist keine tatsächliche technische OFF-/ON-Abnahme und keine Leistungsfreigabe.

## Geschlossene Befunde

- Verschiedene Adapterinstanzen auf demselben Agenten werden jetzt durch `_behavior_ensemble_owner` vor Installation zurückgewiesen. Der Negativfall lässt den ersten Adapter korrekt weiterarbeiten und prüft anschließend ursprünglichen Aufruf und entfernte q-Hooks. Der bisherige konkret gemeldete Doppelmittelungsfehler ist damit geschlossen.
- `historical` bindet die alte technische Receipt jetzt zusätzlich an den ursprünglichen `train.inputs[train.technical_receipt]`-Hash. Eine bloß neue Inputmap kann die historische Referenz nicht austauschen; entsprechender synthetischer Negativfall vorhanden.
- Der Owner hält `status=running` während der gemeinsamen Wartephase und führt den Wartestatus separat. Nach gültigem manuellem Release setzt er `awaiting_root_release=False` und bindet den Releasehash. Tests prüfen auch diesen Übergang, fehlenden Release und Workerfehler.

## Vertrag und Ablauf

Historische Gesamtabnahme, beide Kontrollfinals 48/49, ursprüngliche Admissions/Owner/Receipts, Initial-/Vorlaufbelege und vollständige alte Runtime-Untermenge bleiben gehasht gebunden. Alter Admissioncode wird nicht gegen neuen HEAD ausgeführt. Kontrollconfig und geordnete Pläne werden mit tatsächlicher alter Aufnahme und unverändertem `rollout_plan(start)` verglichen. Aktuelle Interpreter-/Paketversionsmetadaten und die ausdrückliche historische Bibliotheksgrenze sind eigene Aufnahmefelder. Keine aktuelle MATCH20-Datei als Lernstart.

Technik: ein Worker, eine Env vor ursprünglicher Agentinitialisierung, OFF dann ON; je Arm ein frischer Start-48-Agent, zwei kumulative feste Fälle. Start 49 nur Initialprüfung ohne Spiel. OFF prüft die zehn alten `paired_row`-Felder, Initial-/Zähler-/epsilon-/Verlust-/Ergebnisbedingungen und Kontrollrewardarray-Identitäten. Der globale alte MATCH20-Replayhash wird korrekt nicht als OFF-Referenz verwendet. ON verlangt belegte legale Präferenzänderung und native Aktionsdivergenz bei korrektem Replay/Reward und unveränderten 35 Mitgliedern. Kein ON/OFF-Trajektoriengleichheitsgate.

Training: separate manuelle Aufnahme nach echter technischer Rootannahme, genau `on48` und `on49` gleichzeitig; keine einzelne weitere Startphase, Fallback oder automatische Folgereihe. Originales `make_learner`/`play_one`/Reward- und Finalaktionsaudit werden verwendet. Interner Rewardrole bleibt `control`, äußere Metadaten kennzeichnen ensemble und Start. Je 40 Vorläufe ohne Lernen, dann ausschließlich gemeinsamer gehashter Rootreview/Release für beide ursprünglichen Worker. Owner erzeugt selbst keinen Release.

Die tatsächlichen Vorlaufvalidatoren lesen eigene Replay-/Rewardarrays und gespeicherte q-/Target-/Adamzustände, prüfen die originale Kontrollformel einschließlich Float32-Speicherung, Initialgleichheit, leeren Adam, Chronologie und Mechanismusbelege. Eine ON-Gleichheit mit alten Kontrollverläufen wird nicht verlangt.

Nach Release je 400 Lernspiele, insgesamt 440 je Arm, 193.320 Envschritte und 60.000 Updates. Endvalidatoren binden gespeicherte JSONL-Chronologie, erhaltene Vorläufe, gemeinsamen Rootrelease, finale q-/Target-/Adamidentitäten, endliche Tensoren und Adam-Schritte, Replayform/-inhaltshash und Ringgröße. Kandidatencheckpoint enthält nur das gelernte Einzelnetz, `ensemble=[]`; die 35 Verhaltensnetze bleiben außerhalb. Mechanismusbelege prüfen Quellenreihenfolge, eingefrorene Identitäten und vollständige Handlungs-/Übergangszähler.

Der Owner wartet auf beide wirklichen Workerexits und verschwundene Gruppen, bevor er finale Checkpointvalidatoren ausführt. Gemeinsamer Compute-Lock, Original-PID-/PGID-/Kommandoidentität, aktuelle Quota, STOP, Quellen-/Input-/Schutzprüfung und eigener kontrollierter Cleanup sind erhalten. Fehler sichern ausdrücklich unvollständige Artefakte; vorhandene Phase verbietet Resume/Retry. Höchstens vier technische plus 880 Vorlauf-/Lernspiele, 120.000 Updates; spätere 200er-Auswahl hier nicht gestartet.

## Grenzen und tatsächliche nächste Abnahme

Synthetische Belege ersetzen keine reale OFF-Reproduktion, ON-Exposition, Runtimekosten oder gespeicherten Endartefakte. Historische vollständige Bibliotheksbinär- und RNG-Snapshots fehlen; neue Paketversionen und zwei bekannte OFF-Fälle beweisen keine universelle historische Identität. Rohbeobachtungen der alten Technik sind nicht archiviert. Kein heutiger Tensorvergleich aus diesen JSON-Belegen behauptet.

Reale Aufnahme erst nach Root-Quellcommit, frischer Quota und Prozessprüfung. Danach exakt vier bekannte Technikspiele; bei fehlender Treue/Exposition stoppen, kein automatischer Ersatz. Noch kein stärkerer Kandidat, kausaler Nachweis oder V14-Ersatz.

## Bytebindung

| Datei | SHA256 |
|---|---|
| `scripts/ensemble_behavior_study.py` | `d2c3ef012f5c09a94761bd768b013074d7b4498321cd0d7c9344efac3ce75863` |
| `scripts/ensemble_behavior_owner.py` | `e7f0aa6dc77a2416d115cf1e2f6fe632353540d11b4c26d4c33b25576cea2cde` |
| `tests/test_ensemble_behavior_study.py` | `73662170fc6427c637e6b76b12ea150e52043c829da3e022415788a421f4af20` |
| `/private/tmp/ensemble-behavior-impl/final-tests.log` | `594bf4536b185229d4b2bb68729b09a3c1788d04f8af6de090665f8c6e5412bc` |
| Bindende Spec | `3fbad1bb1f283e9719463e94d438600270e0878809d3d995ce05382ab8a1a7fb` |
| Bindender Plan | `d2b706abc9701f01498edae84f042d874188381a08ae23cd703625c5d9dd4b9b` |

Nur diesen externen Reviewbericht geschrieben; keine Quellenänderung, Freigabe oder nächste Phase ausgeführt.
