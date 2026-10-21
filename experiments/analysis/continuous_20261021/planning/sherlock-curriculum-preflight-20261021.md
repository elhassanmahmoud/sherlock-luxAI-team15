# Curriculum: kleine Zustandsisolation und Ressourcenprüfung

Read-only am 21.10.2026 in `/Users/moayedshawesh/Desktop/KI/sherlock-counterplay`. Geprüft: verbindlicher Curriculumplan, `scripts/experiment.py`, `scripts/common.py`, `scripts/variants.py`, `agents/sherlock/{main,model,replay_buffer,config}.py` und vorhandene Laufzeitmetadaten. Keine Modellimporte, Jobs, Quelländerungen oder neue wissenschaftliche Gates.

## Entscheidung vorweg

Die Isolation ist ohne Agentenkopie und ohne Kopie des ungefähr 250-MB-Replaybuffers implementierbar. Eingriff ausschließlich opt-in in das Experimentwerkzeug. **Acht Stunden sind unter der vorgegebenen Maxzeit×1,25-Regel nicht ausreichend.** Root hat nach diesem Befund ausdrücklich **zwölf Stunden** vor neuen Studiendaten beschlossen; wissenschaftlicher Umfang, drei Paare und alle Gates bleiben unverändert. Root passt Plan/Spec vor Implementierung an; dieser Bericht ändert sie nicht.

## Genau welche Zustände sichern?

`run_validation(env, learners, seeds, opponents, *, isolate=True)` arbeitet ausschließlich zwischen vollständig beendeten Trainingsspielen, nicht mitten in einem Rollout. `Learners.unique()` verwenden: full_rules_v3 hat für beide Seiten dasselbe Agentenobjekt (`experiment.py:72–105`). Nicht zweimal sichern/zurücksetzen.

| Zustand | Kleiner Snapshot / Wiederherstellung | Grund |
|---|---|---|
| Globales Python-RNG | `random.getstate()` / `setstate()` | `play_game` setzt es neu (`common.py:107`); exakte Isolation nicht nur „nächster Seed wird ohnehin gesetzt“. |
| Globales NumPy-Legacy-RNG | `np.random.get_state()`; enthaltenes kleines Array kopieren / `set_state()` | Gegnerkonstruktion und Spiel beeinflussen es; Defaultkonstruktor setzt Seed0, `play_game` setzt Spielseed (`default/default.py:17`, `common.py:108`). |
| Torch-CPU-RNG | `torch.get_rng_state().clone()` / `set_rng_state()` | Init/zufällige Operationen außerhalb des aktuellen deterministischen Forwardpfads dürfen keine Paarung verschieben. |
| Eigener Generator je eindeutigem Learner | `deepcopy(agent.rng.bit_generator.state)` / Rückzuweisung | Derselbe Generator steuert Exploration UND Replay-Sampling (`main.py:258–263,561`), unabhängig vom globalen NumPy-RNG. |
| Trainings-/Netzmodus | `agent.training`, `q.training`, `target_q.training` speichern, exakt wiederherstellen | `set_to_eval_mode` setzt nur Agent und q; target-Modus bleibt heute unverändert (`main.py:175–181`). Nicht pauschal am Ende `train=True` erfinden. |
| Kontextidentität | ursprünglichen Spieler und kleines `env_cfg` speichern | Validierung läuft beide Seiten und hinterlässt sonst die letzte Seite/Spielparameter. Anschließend öffentliche Config zurücksetzen und `agent.new_game(original_player)` nutzen. |

Auf dem M3 wählt dieser Agent **CPU**, nicht MPS (`main.py:70`). Kein MPS-RNG-Framework nötig. Falls dieselbe Implementierung auf einer tatsächlich bereits initialisierten CUDA-Ausführung zugelassen wird, deren verwendete Generatorzustände ebenfalls sichern; keine GPU nur für den Snapshot initialisieren. Für die konkrete Studie tatsächliches Gerät im Manifest binden.

**`finally`-Reihenfolge:** temporäre Schutzflags lösen, ursprüngliche Config/Seite und leeren Episodenzustand herstellen, Modi zurücksetzen, ganz zuletzt alle RNG-Zustände restaurieren. Auch bei Ausnahme; Ausnahme weiterreichen und Phase abbrechen. Keine Mutation von Lerndaten „reparieren“ und dann weitertrainieren.

`new_game` leert Belief und `_prev_*`, `_cache`, `_sticky_prev`, `_enemy_prev`, Sapzähler und Episodenstatistik (`main.py:121–153`). Die alte abgeschlossene Episode muss nicht tief kopiert werden. `_paths` wird dadurch nicht geleert; im aktuellen V3 ist `pt_walk=False`. Für den generischen Cleanup kann der vorhandene kleine Pfadcache experimentseitig geleert werden, ohne Agentenlogik zu ändern; keine Distanzkarten aus einem Validierungsspiel weiterverwenden.

Die Env besitzt einen expliziten JAX-Key, kein globales JAX-RNG. `reset(seed=...)` ersetzt ihn vor jedem Spiel und erzeugt neue Parameter/State (`luxai_s3/wrappers.py:40–59` im bestehenden Hauptrepo-venv). Deshalb für **Fortsetzung am nächsten vollständigen Spiel** weder Enginezustand kopieren noch JAX initialisieren/serialisieren. Ein Test muss zeigen, dass das nächste Training tatsächlich mit seinem vorgesehenen Seed `reset` und `new_game` aufruft. Wer zusätzlich exakte Env-Objektwiederherstellung möchte, kann vorhandene immutable State-/Key-/Parameterreferenzen zurücksetzen; dies ist hier nicht notwendig und `state` existiert vor der ersten Validierung noch nicht.

Solution_92-Globals werden bei jedem `make_opponent('solution92',...)` aus unveränderten Defaults zurückgesetzt (`common.py:49–75`); mit pool_frac0 wird kein Gegner zwischen Spielen weiterbenutzt. Kein großer Gegner-Deepcopy erforderlich. Dies ausdrücklich auf die zwei festgelegten Gegner begrenzen.

## Was darf nicht geschrieben werden – und wo genügt ein Test?

Der vorhandene `play_set` ruft `play_game(...,train=False)` auf (`experiment.py:128–137`). Nur dessen `train=True`-Pfad ruft `agent.update` auf (`common.py:129–137`). Das ist wichtig: `update` erhöht `env_steps` **vor** dem Trainingsflag-Test (`main.py:522–526`); allein Evalmodus wäre kein ausreichender Schutz gegen versehentliche Aufrufe.

**Runtime, klein und sinnvoll:** vor/nach jeder Validierung Zähler `env_steps/learn_steps`, `learn_enabled`, `autosave_on_terminate`, `recent_losses`, Replay-Objektidentität, Arrayidentitäten/-formen/-dtypes, `pos/size/_mask_dim` vergleichen. q-/target-Parameter und Optimizerzustand sind im Verhältnis zum Buffer klein; kanonische Hashes vor/nach sind eine vernünftige zusätzliche Laufzeitsicherung. Keine `torch.save`-Datei als Tensorhash benutzen; Namen, Shapes, Dtypes und Bytes deterministisch hashen. Gradienten im Test ebenfalls unverändert prüfen, aber nicht als neue große Runtime-Artefakte archivieren.

**Replay ohne Kopie:** der normale Evalpfad liest den Buffer gar nicht; `push`/`sample` dürfen nicht aufgerufen werden. Kleine echte Agenten-Fixtures mit kleinem Buffer und eindeutigem Inhalt prüfen sämtliche Arrays bytegenau sowie `pos/size`; im Test `push`, `_learn`, `opt.step`, `save_agent` und `pop_mean_loss` als verbotene Aufrufe markieren. Mutations-/Ausnahmefixtures müssen scheitern. Ergänzend lassen sich die vorhandenen NumPy-Arrays während Validierung optional temporär auf `writeable=False` setzen und ihre ursprünglichen Flags im `finally` restaurieren (keine Datenkopie). Arrayersetzung bleibt durch Identitäts-/Metadatentest erkennbar. Das ist ein Guard für den geprüften Code, kein Beweis gegen absichtlich umgangene NumPy-Flags.

**Nicht nötig:** vor allen 30 Validierungspunkten einen 250-MB-Buffer kopieren, ihn speichern/laden oder alle unbenutzten Slots hashen. Ein Samplehash einzelner Zeilen wäre außerdem kein vollständiger Inhaltsbeweis. Tests plus eingefrorener read-only-Aufrufpfad und Runtime-Metadaten sind hier die passende Abgrenzung. Falls ausdrücklich voller Inhaltshash verlangt wird: aktive Arrays stückweise über `memoryview` hashen, ohne `.tobytes()` des gesamten Buffers; es bleibt zusätzlicher Lesedurchsatz, kein notwendiger Standard.

**Initialidentität:** direkt nach tatsächlich benutztem `Learners(...)` und vor Validierung0 aufnehmen (`experiment.py:198–199`). q/target, tatsächlicher Optimizer-State samt Parametern, vollständige Config, Zähler, sämtliche obigen RNGs. Replay frisch `size=pos=0`, erwartete Capacity/Obs-Dimension/Shapes/Dtypes und `_mask_dim=1`; seinen leeren **logischen Inhalt** mit einem eindeutigen Schema/Marker darstellen. Unbenutzte vorallokierte Nullslots beeinflussen kein Sample und müssen nicht einzeln archiviert/gehasht werden. Den Konstruktor/Initialinhalt in kleinen Tests prüfen; tatsächlichen leeren Cursor zur Laufzeit assertieren. Keine nachträglich neu erzeugte Kopie als Initialbeleg, kein vollständiger `torch.save`-Bytestrom als zuverlässiger Tensoridentitätsvergleich.

**Minimale Tests:** (1) absichtlich alle drei globalen RNGs und Learner-RNG konsumierender Callback plus exakte nächste Ziehungen; (2) echtes kleines Netz/gefüllter kleiner Buffer vollständig unverändert, Modus/Config/Seite korrekt; (3) Ausnahme nach RNG-/Beliefmutation restauriert Cleanup; (4) verbotenes `update`/Bufferwrite wird erkannt; (5) aliasierte Learners nur einmal restaurieren; (6) nächstes Spiel frisch gesetzt, Initialsnapshot vor erstem Callback. Keine Tests mit 300.000 Replayzeilen nötig. QNet besteht aktuell aus Linear/ReLU, ohne BatchNorm/Dropout (`model.py:18–41`); `torch.no_grad` plus Evalpfad mutiert daher keine Running-Statistics.

## Laufzeit und Admission: acht Stunden nicht schönrechnen

Aus `experiments/analysis/autonomous_20261020/exploration_replication_s{47,48,49}_state.json`, Job-Start/Ende, jeweils 3.000 Spiele:

| Seed | control | slow |
|---|---:|---:|
| 47 | 3.344 s | 3.130 s |
| 48 | 3.033 s | 3.100 s |
| 49 | 3.051 s | 3.088 s |

Die Manifeste bestätigen `val_every=0`; Maximum `train_secs=3338,3`, somit konservativ **3344 s Childwall** verwenden. Die neuen 960 Zwischenvalidierungen sind zusätzlich, nicht darin enthalten. Sobald neue `train_secs` Zwischenvalidierung einschließt, beim Aktualisieren der Restprognose keinen Doppelaufschlag dafür einbauen; Komponenten getrennt protokollieren.

Langsamster Einzelnetz-Evalarm: **144 s / 240 Spiele / zwei Worker**. Langsamster V3+3-Developmentarm: **202 s / 240 / zwei Worker** aus `experiments/compare/autonomous_20261020/exploration_ensemble_development/state.json`. Für serielle In-process-Zwischenvalidierung zunächst konservativ `2×144/240=1,2 s/Spiel` ansetzen; das ist eine abgeleitete Schätzung, keine gemessene Einzelworker-Garantie. Direkte21-vs18-Laufzeit ist ebenfalls noch nicht exakt gemessen; bisheriger18-vs18-Job brauchte565s/800, kein Grund, die unbekannte21er-Zeit als garantiert zu behandeln.

| Verbleibender Umfang vor Start | Ansatz inklusive Faktor1,25 |
|---|---:|
| Sechs Trainingsarme | 25.080 s |
| 960 serielle Zwischenvalidierungsspiele | 1.440 s |
| 1.440 finale Einzelnetz-Evalspiele | 1.080 s |
| 480 Kandidat-/V3-Developmentspiele | 505 s |
| 1.600 bedingte frische Gegner-Spiele | 1.683,33 s |
| 400 bedingte direkte Spiele, vorläufig Ensemble-Evalrate | 420,83 s |
| Technische Mindestreserve | 900 s |
| **Summe, noch ohne gesonderten Audit-/Build-/Verpackungsaufwand** | **31.109,17 s = 8 h 38 min 29 s** |

Damit hätte der alte Achtstundenplan bereits vor Start **Admission=false**; bekannte negative Methodenergebnisse dürfen nicht vorausgesetzt werden, um die bedingten Jobs wegzurechnen. Selbst Methode ohne Kandidatenzweig liegt mit dieser Regel/Reserve bei7h55 und hat kaum Platz für weitere Arbeiten.

**Explizite neue Rootentscheidung:** zwölf Stunden ab protokolliertem Studienstart, vor Implementierung/Ergebnissen in Plan und Spec aktualisieren; achtstündige Historie bleibt erhalten. Damit verbleiben gegenüber obiger Schätzung rund **3 h 21 min**, ausreichend plausibler Spielraum für Audits, Build, technische Releaseprüfung und Geschwindigkeitsunsicherheit. Keine Laufzeitgarantie: tatsächliche Maxima je Phase weiter nachführen, alle restlichen Jobs prüfen, mindestens15min technische Reserve und sichere eigene Prozessgruppenbereinigung behalten. Ein Trainer ODER höchstens zwei Evalworker; Modell-/Tensor-Audits erst nach beendetem schwerem Kind. Kein Gate, keine Karten und kein Trainingsumfang ändern. Nutzerfreigabe ohne Gesamtdeadline ersetzt nicht die dokumentierte interne Deadline; die hier erfolgte zwölfstündige Änderung ist eine ausdrückliche Ressourcenentscheidung.
