# Task 3 – feste Sampled-Target-Studie

Stand: 08.11.2026, implementiert und synthetisch geprüft. Keine echten Spiele, keine neuen Trainingsstarts, keine Vorbereitung mit echten Modellgewichten durchgeführt. Task 4 ist nicht implementiert. Die finale Fassung ist für den unabhängigen Review eingefroren.

## Geänderte Dateien

Nur diese drei neuen Dateien im Studiencheckout wurden installiert; externe Kopien liegen in diesem Stagingordner:

| Datei | SHA-256 |
|---|---|
| `scripts/sampled_target_study.py` | `40d18c9a8ad8c3ef9b497ce260b533a93e2581a6c7c158a06712d89537aee224` |
| `scripts/sampled_target_supervisor.py` | `df85b767962cffc9c903da86b4ac4f539143ef7b0b0faa24f21e017c2687d07d` |
| `tests/test_sampled_target_study.py` | `ea0c80d1c7c8cf8e89bf130cc7fbad0088c0a1bf8ec83e5d41bd4934d3ce8469` |

Das unveränderte Task-1/2-Modul `scripts/sampled_target_agent.py` hat weiterhin SHA-256 `c767ee07a6fcf9566e762e105eec36a3b51e44664cb1b4b77e82d93ddd414bf9`. Keine produktiven Agentdateien, historischen Studien, Dokumente, Gewichte oder Git-Zustände wurden durch diesen Teilauftrag geändert. Der Supervisor wurde als enges Teilpaket an `supervisor_primitives` delegiert und anschließend von mir integriert und synthetisch geprüft.

## Implementierter Vertrag

- Genau vier separate technische Ausführungen: bekannte Karte 4242, default, beide Seiten × beide Modi; je frische Initialisierung mit run_seed45, keine Gradienten. Kein automatischer Übergang zur Studie und kein Neustart.
- Genau vier Studienarme: control45/sampled45 und control46/sampled46, jeweils 40 Vorlauf- und 160 Lernspiele auf den sechs festgelegten Kohorten. Zwei Worker desselben Starts gleichzeitig; zweiter Start erst nach vollständiger Abnahme des ersten.
- `PilotLearners` initialisiert genau eine gemeinsame kanonische Agentinstanz für beide Seiten, ohne globale Variantenfactory oder alten unmittelbaren Replay-Audit.
- Echte Spiele würden ausschließlich den unveränderten `common.play_game` benutzen. Der lokale Agent liefert vollständige Episode/Frame/Capture/Commit/Confirmed-Ereignisse; der Stream ergänzt die tatsächlich erfasste Belohnung. Captures und Commits werden vollständig sequenziell geprüft, die Folgebefehle an das bestätigte nächste Frame gebunden und mit gespeicherten Replayarrays verknüpft.
- Nach dem Vorlauf werden alle fertigen Zeilen in 256er-Blöcken auf beiden Targetformeln geprüft, mit vorhandenen Netzen und ohne Sampling oder Optimizeränderung. Aufnahme erfordert identische semantische Initial-/Vorlaufzustände, RNG, Replay, Ereignisse, Trajektorien und Spielzeilen sowie tatsächlichen Index- und Targetwertunterschied. Arm-/Modusmetadaten und Containerbytes sind kein Gleichheitskriterium.
- Vorlaufbelege werden geschlossen und zuletzt atomar veröffentlicht. Beide Worker warten auf ein exklusives, atomar publiziertes Paargate und prüfen dessen Rohbezug selbst erneut, bevor Lernen aktiviert wird.
- Finale Abnahme verlangt je Arm 200 vollständige Spiele, 24.000 Updates und 120.600 Env-Schritte. Gespeicherter Replayinhalt wird mit vollständigen Ereignisstreams verknüpft, auch bei Ringüberlauf. Originallearner wird vor Reloadinspektion freigegeben; strikter bestehender Bundle-Loader prüft den finalen Stand. Keine Studienfortsetzung aus Reload.
- Root-Admission muss mit extern übergebenem SHA gebunden sein; Standard `None` verweigert die Aufnahme. Seedabnahme, Review, sämtliche referenzierten Artefakte und aktuelle Quellen/HEAD/geschützte Dateien sind gebunden. Study-Admission verlangt zusätzlich die unabhängige Abnahme genau der vier technischen Receipts.
- Supervisor nutzt bestehende ComputeLock-/AC-/Quota-/Source-/Protected-/Fremdprozess-/OwnedCleanup-Primitiven. PID, Gruppe, Elternprozess und tatsächliches `sys.orig_argv` werden geprüft. Registrierung hat begrenzte Wartezeit; unvollständige oder fehlerhafte Bereinigung ergibt keinen erfolgreichen Abschluss.

## Tatsächlich ausgeführte Tests

Arbeitsverzeichnis bei allen Aufrufen:
`/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15`

Interpreter bei allen Aufrufen:
`/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python`

Die folgende Tabelle ergänzt jeweils `-B -m pytest -q` hinter diesem Interpreter. Es lief immer höchstens ein pytest-Prozess. Sämtliche Daten waren synthetisch; kein Lux-Spiel wurde aufgerufen.

| Argumente | Exit | Ergebnis / Bedeutung |
|---|---:|---|
| `tests/test_sampled_target_study.py::test_exact_four_arms_and_six_disjoint_cohorts` | 1 | 1 failed in 0,03 s; anfänglicher RED auf leerem Scaffold, `ARMS` fehlt. Kein funktionaler Methodenbeleg aus diesem Scaffoldfehler. |
| `tests/test_sampled_target_study.py -k 'not supervisor'` | 0 | 25 passed, 2 deselected in 3,91 s; erste Workerfassung. |
| `tests/test_sampled_target_study.py -k 'frame_rejects or admission_rejects'` | 1 | 6 failed, 5 passed, 39 deselected in 3,23 s; echtes RED: Float-Nativewerte, UID16, Aktion6, Match3, negativer Zähler und leeres Seed-Inventar wurden noch nicht abgewiesen. |
| `tests/test_sampled_target_study.py -k 'not supervisor'` | 1 | 1 failed, 47 passed, 2 deselected in 2,42 s; die sechs Codefehler waren behoben. Der verbleibende Test erwartete fälschlich sechs statt fünf eindeutiger gebundener Dateipfade. Nur diese Fixturezählung korrigiert. |
| `tests/test_sampled_target_study.py -k 'technical_pair_requires'` | 1 | 1 failed, 58 deselected in 2,52 s; echtes RED: ein technischer Durchlauf ohne irgendeine nichtterminale Folgeaktionsbindung konnte als Paar durchgehen. Danach Null-Exposition blockiert. |
| `tests/test_sampled_target_study.py -k 'not supervisor'` | 0 | 57 passed, 2 deselected in 1,82 s. |
| `tests/test_sampled_target_study.py -k 'not supervisor'` | 0 | 59 passed, 2 deselected in 1,99 s; zusätzlicher vollständiger synthetischer 303-Frame-Stream mit NPZ-Verknüpfung und Prüfung der einmaligen gemeinsamen Initialisierung. |
| `tests/test_sampled_target_study.py -k 'exclusive_readiness'` | 1 | 1 failed, 61 deselected in 2,03 s; echtes RED: fehlgeschlagene Serialisierung ließ bereits einen leeren sichtbaren Marker zurück. Child-Review hatte außerdem den gleichartigen partiellen Leser-Race identifiziert. |
| `tests/test_sampled_target_study.py -k 'not supervisor'` | 0 | 60 passed, 2 deselected in 2,07 s; Payload vorab serialisiert, geschlossene temporäre Datei mit fsync und exklusivem atomarem Link veröffentlicht; kein Überschreiben. |
| `tests/test_sampled_target_study.py` | 0 | **70 passed in 2,28 s**; integrierte Supervisor-Prüfungen einschließlich fester Technikstufe, Fake-Prozessqueue, Fehlercleanup, exakter Registrierung und Timeout. |
| `tests/test_sampled_target_agent.py tests/test_sampled_target_study.py` | 0 | **123 passed in 3,19 s**; abschließender gemeinsamer gezielter Lauf, bestehende 53 Agenttests plus 70 Task-3-Tests. |

Die finalen vier Datei-SHAs oben wurden tatsächlich mit `shasum -a 256` aus dem Checkout gelesen. `git diff --check -- scripts/sampled_target_study.py scripts/sampled_target_supervisor.py tests/test_sampled_target_study.py` hatte Exit0; da die Dateien neu/ungetrackt sind, ist das kein eigenständiger Inhaltsnachweis für diese Dateien.

## Technische Belege / Auditor-Schnittstelle

Runs: `experiments/runs/20261108_sampled_target_technical_{control|sampled}_p{0|1}/`.

Technical-Receipt bindet genau neun Dateien:
`manifest.json`, `rollouts.jsonl`, `initial_agent.pth`, `technical_agent.pth`, `technical_proof.json`, `prefill/bundle.json`, `prefill/replay.npz`, `prefill/provenance.jsonl.gz`, `prefill/trajectory.jsonl.gz`.

`shared` enthält Initial-/Endhashes von Q, Target, Adam, Agent-RNG und globalem RNG, Lern-/Env-/Replayzähler, semantische Replay-/Event-/Rows-/Trajectoryhashes und vollständige Capture-/Commit-/Terminal-/Frame-/Confirmed-Zahlen. Separate Checkpoints erlauben direkte Tensor-/Optimizerprüfung. Das technische Paargate vergleicht Inhalte, keine Armnamen oder Modusfelder.

Der passive Env-Proxy protokolliert je Episode reset, danach pro Schritt submitted und result; bei303 Schritten607 Datensätze. `trajectory.jsonl.gz` enthält episode_id, kind, step, exakten Digest sowie bei submitted beide nativen Aktionsarrays. Die Digests stammen aus `holder_rollout.exact_digest` über `(reset, kwargs, result, env.state)`, `(submitted, actions)` bzw. `(result, result, env.state)`. Der Spielhash ist SHA256 über die aufeinanderfolgenden ASCII-Digests. Die Roh-Enginearrays werden nicht zusätzlich archiviert: vollständige Engine-Digests lassen sich offline vergleichen, aber nicht unabhängig aus diesen Transcripts neu berechnen. Das ist ausdrücklich kein Nachweis einer Enginewirkung des eingereichten Befehls. Der unabhängige Technikauditor ist über diese Grenze informiert.

Supervisor-Endstate: stage=technical, status=done, active=[], vier jobs mit tatsächlichen Kommandos/Returncodes, receipts als `{job: {absoluterReceiptpfad: SHA256}}`, technical_pairs mit player_0/player_1, paired_prefill leer. Der Launchmarker liegt im vorbereiteten Ordner. Root kann den gesamten Endstate extern pinnen.

## Offen / keine behauptete Ausführung

- Unabhängiger statischer Task-3-Review durch `artillery_design_review` läuft auf den oben angegebenen stabilen Hashes.
- Root-Admission, Commit/Freeze und genau vier echte technische Spiele sind noch ausstehend. Kein bereitgestelltes Admissionartefakt und kein Start aus diesem Bericht.
- Laufzeitverträglichkeit mit tatsächlichen Lux-Zuständen ist durch synthetische Tests allein nicht bewiesen. Dafür sind genau die vier vorab festgelegten Technikspiele vorgesehen, ohne zusätzliche Aufnahme- oder Wiederholungsserie.
- Keine Leistungsaussage, kein V14-Ersatz, keine Folgestudien oder Task-4-Implementierung aus Task3.
