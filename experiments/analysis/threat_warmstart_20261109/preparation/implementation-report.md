# Task 1: Implementierungsbericht

Stand: 09.11.2026. Umsetzung zur unabhängigen Prüfung bereit; keine echte V14-Ladung, kein Spiel und kein Commit/Push ausgeführt.

## Umfang

- `scripts/threat_warmstart.py`: feste Karten-/Gegnermischung mit unabhängigem Generator47; explizite Erweiterung des festen V14-Mitglieds18 von79 auf101 Eingaben mit22 Nullspalten; zwei gleiche101er-Arme. Eigener Adapter nullt ausschließlich die Zusatzmerkmale der Kontrolle im tatsächlich benutzten Cache. Originale Aktionen, Regeln, Reward und DDQN bleiben erhalten.
- Instanzlokales Replay prüft jede tatsächlich eingetragene aktuelle und nächste Featurezeile, finale kanonische Aktionslabels, Folgemasken und Terminalkennzeichnung. Native Bewegungs-IDs werden bei Spiegelung zurücktransformiert. Originale Fog-SAP-Regeln dürfen außerhalb der vorherigen Netzmaske handeln; diese Fälle werden mit `masked_final_rule_actions` gezählt und nicht abgewiesen.
- Tatsächliche Lernbatches und Gradienten der neuen Spalten werden geprüft. Kontrollspalten müssen null bleiben. Der Endnachweis verlangt exponierte Trainingsbatches, echte Zusatzspaltengradienten und veränderte Zusatzspalten im Merkmalsarm.
- Kompakte direkte `common.play_game`-Schleife: vier bekannte Technikspiele oder zwei feste440-Spiel-Worker. Beide Trainingsworker warten nach40 Vorlaufspielen auf eine einmalige, an beide tatsächlichen Vorlaufbelege und einen ausdrücklichen Root-Review gebundene Freigabe. Kein automatischer Technik-/Trainingswechsel und keine automatische Lernfreigabe.
- `scripts/threat_warmstart_owner.py`: vorhandene Compute-Lock-, Quellen-, Quota-, Akku-, Besitz-, Spawn- und Shutdown-Hilfen. Höchstens zwei Worker. STOP/Signal/Quota endet am abgeschlossenen Spiel; noch vorhandene Lernarbeit wird ausdrücklich als `incomplete` gesichert, ohne Wiederaufnahme oder Kandidatenfreigabe.
- Kompakte Spielzeilen mit Ergebnis, Zählern, Verlust, nativen/öffentlichen Trajektorie- und Replay-Präfixdigests sowie höchstens vier Merkmalsbeispielen je Spiel. Keine Rohbeobachtungen oder vollständigen Netzoutputs. Vorlauf- und Endreplay werden für tatsächliche Dateinachrechnung erhalten.

## Tatsächlich ausgeführte Prüfungen

Finaler Aufruf:

`env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_threat_warmstart.py`

**Final nach den engen Review-/Rootkorrekturen: 31 Tests PASS, Exit0, 1,98 Sekunden.** Ausschließlich synthetische Daten und frische kleine Testzustände; `torch.load` und echte Spielausführung sind in der Suite verboten. Zwei einzelne synthetische Optimizerupdates prüfen die Null-/Echtmerkmalswirkung; das sind keine Studienlernläufe. Ein temporärer synthetischer Checkpoint prüft die ausdrückliche Incomplete-Kennzeichnung und den Überschreibschutz.

Abgedeckt: exakte Spaltenerweiterung, Konfiguration und feste Pläne, Cache-Hits, tatsächliche101er-Lernbatches und Gradienten, finale Labels einschließlich Spiegelung und Fog-SAP außerhalb der Netzmaske, originale `_update`-Folgefeatures, Vorlaufgleichheit, tatsächliche Replaydatei-Nachrechnung, Worker-/Quellenbindung, Root-Freigabe und einmaliges Schreiben sowie Incomplete-Sicherung.

Originalbelege unter `/tmp/threat-warmstart-impl/`: `red.log` (noch fehlendes Modul), `green-1.log` (eine fehlerhafte synthetische Folgepräfix-Fixture, danach korrigiert), `green-2.log`, `fog-label-red.log` (gezielt reproduzierter falscher Netzmaskenfilter), `green-3.log` (ursprüngliche23Tests), `epsilon-red.log` (23PASS/1FAIL), `epsilon-green.log` (24PASS), `atomic-json-red.log` (25PASS/4FAIL), `review-fixes-green.log` (29PASS), `env-reuse-red.log` (29PASS/2FAIL) und `env-reuse-green.log` (final31PASS). Die ursprünglichen drei neuen Python-Dateien zusätzlich nur statisch geparst; No-index-Diffchecks ohne Whitespacebefund. Keine breiten oder historischen Tests erneut ausgeführt.

## Enge Reviewkorrekturen

- `make_learner` akzeptiert den tatsächlichen binären Wert der unveränderten `Agent_x.epsilon`-Formel mittels `math.isclose(..., abs_tol=1e-12, rel_tol=0)`. Der neue Fabriktest verwendet einen künstlichen101er-Nullzustand und die originale Epsilonformel; beide Arme werden frisch, identisch und ohne Archive geladen. Der vorherige exakte Vergleich scheiterte nachweislich bei `0.050000000000000044`.
- Der gemeinsame exklusive JSON-Schreiber schreibt und synchronisiert zunächst eine temporäre Nachbardatei. Erst danach veröffentlicht `os.link` den vollständigen Inhalt atomar und ohne ein bestehendes Ziel zu ersetzen. Die temporäre Datei wird auch bei Serialisierungs-, Synchronisierungs- und Linkfehlern entfernt. Gezielte Tests prüfen insbesondere, dass eine halbgeschriebene `release.json` noch nicht sichtbar ist und vorhandene `prefill.json`-Bytes erhalten bleiben. Owner und übrige Studienmethodik unverändert.
- Ein weiterer konkreter Rootbefund betraf die Lebensdauer der Lux-Umgebung: Wegen JAX-JIT mit statischem `self` darf nicht jedes Spiel eine neue Engineinstanz erzeugen. `run_worker` erzeugt jetzt genau eine Umgebung, reicht sie an `play_one` weiter und schließt sie im äußeren `finally` einmal. `common.play_game` setzt dieselbe Instanz weiterhin je Spiel mit dem festen Seed zurück. Zwei synthetische Workerläufe mit FakeEnv/Fakeplay_game reproduzierten vorher vier beziehungsweise zwei Konstruktionen; nach Korrektur bestätigen sie eine gemeinsame Instanz, die richtigen Resetseeds und genau einen Close sowohl bei Erfolg als auch nach einem Fehler im zweiten Spiel. Keine echte Lux-Umgebung wurde dafür gestartet.

## Finale Bytebindung

| Datei | SHA-256 |
|---|---|
| scripts/threat_warmstart.py | 2548514bda2e9b7ecd7ff508704a2a5d59ee4bb556b018c83893156517badd53 |
| scripts/threat_warmstart_owner.py | 137aec6383b6186b9ab0cad728b06b173964e93290977f490686d5d0ef9288f0 |
| tests/test_threat_warmstart.py | a07f9208316d25a70cdd2c417404c0b0ff2a214b835fd48d6dce0f230a513be8 |
| /tmp/threat-warmstart-impl/env-reuse-green.log | b54bbae942774d7905687fd1ebede86a09dcf6b5d6302ca81bfa29898e0ed564 |

## Root-Aufnahme und offene Grenzen

Aufnahmefelder: `profile=threat_warmstart_20261109`, `schema_version=1`, `stage=technical|training`, `start_authorized=true`, `root`, `out`, `python`, `plans`, `source`, `protected`, `inputs`, `stop_file`, `allow_battery`, `config_manifest`, `config`, `rollout_plan`, `seed_acceptance`; für Training zusätzlich gebundene `technical_receipt`. Die Ausgaben liegen fest unter dem Studienprofil in `technical_v1` beziehungsweise `training_v1`. `config_manifest` enthält `source_sha256` und `source_config`; `seed_acceptance` folgt dem bisherigen Schema mit `cohorts`, `files` und offengelegten Grenzen.

Owner-Aufruf: `python -B -m scripts.threat_warmstart_owner technical|training --admission ABS --admission-sha SHA --usage-file ABS`. Der Owner startet ausschließlich die passenden Worker. Nach Vorlauf liegen `control/prefill.json`, `threat/prefill.json` und beide eingefrorenen Replaydateien vor.

Root-Review vor Lernfreigabe: eigene JSON-Datei mit `status=PASS`, `profile`, derselben `source`, `admission_sha256` und `prefill_sha256={control:SHA,threat:SHA}`. Danach einmalig `python -B -m scripts.threat_warmstart approve-prefill --admission ABS --admission-sha SHA --review ABS --review-sha SHA`. Dieser Aufruf liest die tatsächlichen Vorlauf-Replays, prüft die Paaridentität und schreibt ausschließlich die gebundene `release.json`; er startet keine Ersatzworker.

Noch offen: unabhängiger Review, Root-Aufnahme und echte vier technische Ausführungen. Die echte Paaridentität vor Gradienten und das Lernen aus real exponierten Gefahrmerkmalen sind noch nicht nachgewiesen. Runtimeprüfungen erfassen sämtliche Übergänge; unabhängig offline nachrechenbar bleiben die gespeicherten Replaydateien, kompakten Beispiele, Resultate und Dateibindungen. Vollständige öffentliche Trajektorien werden nur live geprüft und per Digest gebunden, nicht als Rohdaten gespeichert. Keine Spielstärkeaussage und kein Performancecode in dieser Aufgabe.
