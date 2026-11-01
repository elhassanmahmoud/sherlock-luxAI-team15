# Kontrollpilot: Umsetzung zur Root-Prüfung

Stand 01.11.2026. Arbeitskopie `/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics`, Branch `improvement/november-battle-20261101`.

Nur die zugewiesenen Dateien wurden erstellt:

- `scripts/night_train_pilot.py`
- `tests/test_night_train_pilot.py`

Keine Commits, keine Änderungen an Agentenlogik, globalen Varianten oder `finetune.py`, keine echten Checkpoint-Extraktionen, Trainingsläufe oder Lux-Spiele. Keine Volltestsuite durch diesen Subagent. Die fokussierten Tests wurden zeitlich mit dem Inferenzagenten abgestimmt und liefen nach Roots Baseline.

## Verhalten

`prepare` verlangt standardmäßig exakt den aktiven V14-Dateihash `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`, eine vorhandene Quelle und ein neues Ziel außerhalb der geschützten Abgabe-Gewichte. Index 18 bedeutet `ensemble[17]`, weil das primäre `q` Index 0 ist. Die Daten müssen 79 Features und sechs Aktionen ausweisen; das ausgewählte State-Dict wird zusätzlich mit einem echten QNet strikt auf vollständige Architekturkompatibilität geprüft.

Der erzeugte Einzelnetz-Checkpoint hat geklonte, identische q-/target_q-Tensoren, kein Optimizerfeld, keine Ensemble-Extras, keinen CNN-Teil und keinen alten Replay-Buffer. `learn_steps=0`, der Epsilon-Zähler wird auf mindestens den Wert für epsilon=0,05 normalisiert. Dieser Zähler wird ausdrücklich nicht als wiederhergestellte Trainingshistorie von Komponente 18 bezeichnet. Adam entsteht beim normalen Laden frisch. Das ist ein Warm Start aus gelernten Tensoren, kein Resume mit Optimizer/Replay.

Konfiguration: V14-Quellconfig mit den bestehenden `full_rules_v12`-Trainingsregeln, `cand_rescue=true`, `rescue_after=30`, `frozen=false`, lr=1e-4, `w_explore=.3`, zunächst `w_discovery=.5`. Die bestehenden Bedingungen im Agenten bleiben unverändert: Rescue greift weiterhin nur außerhalb des Trainings. Kein Feature- oder Action-Space-Wechsel.

Der Init-Manifest enthält UTC-Zeit, Quellpfad/-SHA, Komponentenindex, deterministischen Tensorhash, geschriebenen Checkpointhash, Config und die Hinweise auf frischen Adam/Replay. Quelle und Initialgewichte werden vor/nach Vorbereitung bzw. Arm-Lauf auf Unverändertheit geprüft. `runarm` bricht bei fehlenden oder veränderten Startdateien, bestehendem Ziel, altem Replay, wieder vorhandenem Optimizer, Ensemble oder ungleichen q-/target-Hashes vor dem Training ab.

`runarm` trägt genau eine prozesslokale Variante für seinen Aufruf von `scripts.finetune.main()` ein. Auch bei Exceptions werden vorherige Registry-Einträge und `sys.argv` wiederhergestellt. Eine zusätzliche Provenienzdatei `INIT/arm_plans/NAME.json` erfasst Arm, Start-/Endzeit, Quelle, Tensorhash, genaue Args, Config und `done`/`incomplete`. Auf SIGTERM, der den Prozess ohne Python-Finally beendet, kann diese Datei bei `running` verbleiben; Root muss einen solchen Job über den fehlenden fertigen Run-Manifest als unvollständig einstufen. Keine Resume-Automatik.

Alle Trainingsparameter sind fest im Wrapper:

- 600 Training, 120 eigene Prefillspiele, seed=9, map_offset=4200.
- lr=1e-4, acht bekannte Val-Karten alle 300 Spiele, `--keep-final`, `--no-test`.
- Mix `solution92=.6, sol92_sq=.2, default=.1, rush=.1`, kein Pool und keine Snapshots.
- Kontrollarm `w_discovery=.5`, Discovery-Arm `2.0`; dies ist der einzige Config-Unterschied.
- Ein Arm pro Prozess. Der Supervisor von Root muss die gemeinsame Zwei-Stunden-Grenze, Netzteilzustand und maximal zwei Worker durchsetzen.

## CLI nach Root-Review und Netzteilfreigabe

In der Arbeitskopie ausführen; dort existiert keine eigene `.venv`, deshalb den vorhandenen Interpreter verwenden:

```sh
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m scripts.night_train_pilot prepare \
  --source /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/agents/sherlock/weights/agent_p0.pth \
  --out experiments/runs/20261101_nov_info_init18
```

Danach pro erlaubtem Worker genau einen der folgenden Aufrufe. Falls Root eine eingefrorene V14-Referenzkopie anlegt, kann diese bereits beim `prepare --source` mit unverändertem Dateihash verwendet werden.

```sh
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m scripts.night_train_pilot runarm \
  --init experiments/runs/20261101_nov_info_init18 --arm control --name 20261101_nov_info_control_s9

/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m scripts.night_train_pilot runarm \
  --init experiments/runs/20261101_nov_info_init18 --arm discovery --name 20261101_nov_info_discovery_s9
```

Vor dem echten Lauf initiale Policy-/Tensoridentität und geladenen frischen Optimizer durch Root separat prüfen. Der Helper hat absichtlich keine automatische Battle-Auswertung oder Abgabeübernahme.

## Tatsächliche Prüfungen

1. TDD RED: dieselbe fokussierte Testdatei vor Implementierung gestartet. **10 erwartete Fehler in 2,61 s**, weil die Helper-Funktionen noch fehlten.
2. GREEN: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest -q tests/test_night_train_pilot.py` aus der Arbeitskopie. **10 bestanden in 2,48 s**.

Tests nutzen kleine synthetische QNet-Checkpoints (79 Eingaben, sechs Aktionen, hidden=4), keine Env-Resets. Nachgewiesen sind Index-18-Auswahl, identische getrennt geklonte q-/target-Tensoren, frischer Optimizerzustand, Epsilon-/Config-Vorgaben, unveränderte Quelldatei, Indexfehler, fehlende/falsche Quelle, vorhandene Ausgabe, strikt ungültiger Netzstate, fehlendes Startgewicht, veränderte Quelle sowie Wiederherstellung der globalen Registry/argv und einziger Reward-Unterschied bei beiden Armen. Nur der tatsächliche finetune-Einstieg wird für den Wrapper-Test durch einen sofort abbrechenden Call ersetzt, damit keine Spiele laufen.

## Hinweise für Integration

- Die vorangehende Diagnose `/tmp/sherlock-20261101-training-design.md` enthält ursprünglich Index 0 und einen anderen Pool-Mix als Vorschlag. **Die freigegebene Root-Spec und diese Umsetzung ersetzen diese Vorschlagswerte mit Index 18 und dem oben genannten Mix.**
- Seed-Audit bleibt gültig: 294200–294499 Training und 295000–295059 Prefill waren in 271 Manifesten und 1.191 seedhaltigen CSV/CSV.gz mit 1.555.218 Zeilen frei. Keine neuen Seeds durch diesen Subagent verbraucht.
- Die verwendete temporäre Variante existiert nach Prozessende nicht dauerhaft. Rohresultate sind durch Init-Manifest und Arm-Provenienz reproduzierbar; eine spätere Fortsetzung braucht wieder einen expliziten Wrapper/Config, nicht einen blinden `finetune --init` ohne Variante.
- Die Volltestsuite und das unabhängige Root-Review stehen noch aus. Kein Training starten, bevor Root Netzteilzustand, gefrorene Quellen und Jobzulassung bestätigt hat.
