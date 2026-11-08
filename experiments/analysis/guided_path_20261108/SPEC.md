# Geführte Exploration: feste Offline-Diagnose

Status: vorbereitet; echte Trace-Auswertung noch NICHT ausgeführt. Root-Review und ausdrücklich gebundene Freigabe sind erforderlich.

## Zweck und Hypothese

Auf den bereits archivierten V14-Zuständen feststellen, ob ein deterministischer geführter Luftlinienzug von der vorhandenen `_path_fix` korrigiert würde. Die produktive Trainingsschleife überspringt `_path_fix` bei Epsilon-Exploration trotz `rules_in_training=True`. Das ist ein konkreter Verhaltensunterschied, kein bewiesener Fehler und kein belegter Verbesserungsansatz. Zufallsfallbacks werden nicht gezogen oder geschätzt.

## Feste Quellen und Daten

Aktueller eingefrorener HEAD: `02ce1b2ce9a5b0780da1ee6462a2368b2226d495`. Historischer Trace-HEAD: `0c0dda642e9876141a705c2b8ed807a4f26ed870`. V14 laut altem Manifest: `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; Gewichte werden nicht geöffnet.

Genau die zwölf Einträge von `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/continuation_20261102/diagnostic_keys.json` in vorhandener Reihenfolge: sechs bekannte Niederlagen plus erste sechs Siege; keine repräsentative oder gematchte Stichprobe. Alle gzip-Dateien wurden nur als komprimierte Bytes gehasht, nicht dekomprimiert oder analysiert. Historisches Manifest bindet jeden Hash.

| Vollständiger Inputpfad | SHA-256 | Bytes |
|---|---|---|
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/continuation_20261102/targeting/831006_player_1.jsonl.gz` | `f5b81f554ad4d52f70bcb3a04008a1463c3887594cfd6be246dfe2556de97d08` | 2292559 |
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/continuation_20261102/targeting/831029_player_0.jsonl.gz` | `333dd18abe61ebc1945aef1765a32f7d6d0c643817da589c6f68c28c79bfce04` | 2447101 |
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/continuation_20261102/targeting/831042_player_0.jsonl.gz` | `9e05725ddf80814694711a5e63db1b5e940acad09c858189e46ba2d99a9fedb2` | 2456955 |
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/continuation_20261102/targeting/831042_player_1.jsonl.gz` | `c1f3844a1131595c8cd8a62ab77ca0a18fdf4a1f1073c1b848b4ba4a06a69571` | 2472426 |
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/continuation_20261102/targeting/831043_player_0.jsonl.gz` | `faab6800960eb4564e8c8a701bb6dc81ef30daaaf5c9b5538d44bff0e65e568d` | 2357228 |
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/continuation_20261102/targeting/831043_player_1.jsonl.gz` | `0d3e597db076c6a5e2057dd834e1cdc734d8ea495684c9618820bab7ff92b815` | 2353682 |
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/continuation_20261102/targeting/831000_player_0.jsonl.gz` | `2f03777deb7c9449dd7572389c4720191d22bdf4c10b5b2b275a1c177edb293b` | 2326031 |
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/continuation_20261102/targeting/831000_player_1.jsonl.gz` | `bccc367104077bd3ceb65b542e2f1cc6d695bcb67cf2a3cad88f87038ad55b98` | 2327008 |
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/continuation_20261102/targeting/831001_player_0.jsonl.gz` | `ac0109759057a874cafad0176393707247e92e3072681946bc493a42084f78cd` | 2397509 |
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/continuation_20261102/targeting/831001_player_1.jsonl.gz` | `1727faa1bb614124e76737ba2cd36a4e4c1b5f7bcd1b1b04260e8dca25b01f7d` | 2396826 |
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/continuation_20261102/targeting/831002_player_0.jsonl.gz` | `5a5637fab3d53cf43caff4b60a5217b7c16d7f2bb0d89a8505422b9df70d6f06` | 2448039 |
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/continuation_20261102/targeting/831002_player_1.jsonl.gz` | `65f89f8a8ac8b0559eeee9c0a68f2ec5aa8457090bbf9484d0e4378f74174a21` | 2435482 |

Weitere exakt gebundene Metadaten- und Quellpfade einschließlich ihrer Hashes stehen vollständig in `bindings.json`; Schlüsseldatei, historisches Manifest, aktuelle vorbereitete V14-Config und sechs relevante aktuelle Quelldateien sind vor/nach Ausführung auf Gleichheit zu prüfen. Historische Git-Blobs werden nur gelesen; ihre Hashes müssen dem historischen Manifest entsprechen.

## Bereits ausgeführte reine Quellprüfung

Die folgenden historischen/aktuellen ASTs sind exakt gleich (einschließlich Docstrings, ohne Zeilenattribute); Fingerprints stehen in bindings.json: `_path_fix`, `_step_toward`, `_guided_action`, `rules.distance_map`, `rules.first_step`, `PathCache.get`. `features.py`, `belief.py` und `geometry.py` sind sogar vollständig bytegleich. Keine Quellen werden importiert oder ausgeführt. Der historische Observer-Quellhash wird an das Manifest gebunden; die momentane vollständige Agentendatei ist wegen späterer anderer Änderungen erwartungsgemäß nicht insgesamt bytegleich.

Alle mathematischen Operationen werden unabhängig mit Stdlib-Listen/deque formuliert. Entscheidend: `rules.distance_map` startet auch ein als blockiert bekanntes Ziel bei Distanz0. Der ähnliche `_distance_map` aus targeting_probe hat hier andere Semantik und wird NICHT verwendet. `first_step` bevorzugt die größte gespeicherte Feldenergie; Gleichstand bleibt bei der ersten Richtung 1,2,3,4. Keine Aussage über sichere Gesamtwege oder zukünftige Energie.

## Validierung der gespeicherten Eingaben

Pro Datei exakt303 chronologische Frames: drei Resetzeilen und300 Entscheidungen. Pro Entscheidung prüft der Runner Seed/Seite/Schritt/Match, vollständige historische Config, aktive path_fix-Konfiguration, Kartenformen24×24, Typen/Endlichkeit, eindeutige UIDs, Übereinstimmung der Unitposition/-energie/Zielzuweisung zwischen public und unit sowie legale Bewegungsmasken gegen Kartenrand, Passierbarkeit und Zugenergie. Fehlende/unklare Felder führen zum unvollständigen Abbruch; keine Ergänzung durch neue Spiele.

Archivierte _path_fix-Events werden mit mask/a, call-time unit_context, beobachteter caller_action und arguments_after an denselben public-Kontext gebunden. Alle historischen Rückgaben müssen durch die unabhängige Rechnung exakt reproduziert werden. Die spätere Aufnahme von public am Ende des Zuges ist nur vertretbar, weil zugewiesene Ziele, passable und energy_map in diesem unveränderten Helferpfad gelesen werden; ein Event-Kontextwiderspruch bricht ab. Die Masken müssen zusätzlich exakt den pro Unit gespeicherten Masken entsprechen. Die Eingaben werden vor/nach Verarbeitung gehasht; keine Mutation.

## Vorab feste Metriken

- Golden: Zahl aller erreichten historischen _path_fix-Aufrufe, exakt reproduzierte Rückgaben, davon historische Helperänderungen; JSONL mit Seed/Seite/Schritt/UID/Event und alter/neuberechneter Klasse.
- Gelegenheit: aktive Unitentscheidungen, mit zugewiesenem Ziel, ohne deterministischen geführten Zug (kein Zufallsfallback), deterministische geführte Züge, hypothetische _path_fix-Änderungen. Änderungen nach Match und Zielklasse (Punktefeld/Kandidat/Erkundung), unterschiedliche Schritte/Partien/Kartenseeds. Jede geänderte Gelegenheit wird mit Position/Ziel/Maske, beiden Klassen, BFS-Distanzen und public-Kontexthash gespeichert.
- `0.035 = epsilon0.05 × guided_prob0.7` ist allein die theoretische Zweigwahrscheinlichkeit bei festgehaltenen archivierten Zuständen. `0.035 × Gelegenheiten` ist ein bedingter Rechenwert, KEIN beobachteter Trainingsanteil oder erwarteter Gewinn. Keine Inferenz aus Unitzeilen als unabhängigen Partien.

## Grenzen und Entscheidung

Zwischenkorrekturen sind keine geänderten Endaktionen: weitere Nebel-, SAP-, Rescue- und Overkill-Regeln können eingreifen. Diese Diagnose simuliert diese Gegenfaktik ausdrücklich nicht. Sie bewertet keine Rewardänderung, vermiedenen Tod, Lernwirkung oder Siegquote. Alte Evalzustände/Masken entsprechen nicht automatisch den besuchten Zuständen des aktuellen Einzelnetztrainings. Kein Schwellentuning, keine Kandidatenauswahl, kein Modell-/Bootstrap-Ansatz und kein Neustart/Verlängern negativer Studien.

## Betrieb

Exakt12 gzip-Dateien, insgesamt28,710,846 gespeicherte Bytes; Streaming pro Frame, BFS-Cache pro Frame/Ziel. Höchstens120 Sekunden während der eigentlichen Analyse, niedrigere Prozesspriorität (+10), kein Prozesspool und keine Modellimporte. Überschreitung erzeugt nur incomplete.json; kein automatischer Retry. Ausgaben ausschließlich unter /tmp/guided-path-diagnosis-20261108/run_v1; exklusives neues Verzeichnis. Keine Repo-/HEAD-/Trainingsplanänderung.

Die Vorab-Selbstprüfung hat18 synthetische Gegenbeispiele bestanden; siehe selfcheck.json. Das ist keine Auswertung der echten Spuren. Ein anfänglicher reiner Vorbereitungsfehler durch macOS /tmp→/private/tmp wurde vor bindings.json korrigiert; kein Trace war geöffnet.
