# Unabhängiger Review — Guided/Path-Offline-Diagnose

**PASS, bedingt auf die noch ausstehende vollständige echte Datenprüfung.** Keine blockierenden Befunde im geprüften Stand. Dies ist keine Ergebnisabnahme und keine Freigabe neuer Spiele oder Policyänderungen.

Geprüfter Runner: `/tmp/guided-path-diagnosis-20261108/diagnose.py`, SHA-256 `997dc49f332de7aa6fba18cb314725c89b3824a6fde6d87b521bcfc7d12bafa2`. Dazu SPEC `177b8f071dc8cdb9a2e086e8f330855026e89c436767ed1a4b93b55a39a1d9a7`, PLAN `a603a34a93065416c3b2e78a47bd72836dcb81f41c99b2dbd7ff8bcbed472bd1`, bindings `f4975b0922ea37784726928c903fe534a3ee0b4016c8a25356857ae2ec98dbce`, selfcheck `22c9e720f7b1b4782b00ae6cc2f88c498c76bc2d76295397cff72fa12cb9ff9a`.

## Port und Herkunft

- Der unabhängige Listen/deque-Port entspricht den gebundenen Agentenhelfern: vier Richtungen in Reihenfolge 1/2/3/4; **blockiertes Ziel trotzdem Distanz 0**, Ausbreitung nur in passierbare Nachbarn; `first_step` wählt geringere BFS-Distanz mit maximaler Feldenergie und behält bei Energiegleichstand die erste Richtung.
- `toward` reproduziert den deterministischen Teil von `_guided_action` über `_step_toward`: längere Achse zuerst, horizontal bei Gleichstand, Nullachsen entfernen, nur erlaubte Richtungen. Fehlendes Ziel/fehlende Richtung führt ausdrücklich zu keiner Zufallsziehung.
- `path_fix` erhält die Originalabbrüche für fehlendes Ziel, bereits erreicht/unerreichbar, vorhandenen BFS-Fortschritt und seitlichen/abgewandten Luftlinienzug. Nur dessen Rückgabeklasse wird reproduziert; das Original ändert zusätzlich einen Statistikzähler, der für diese Frage keine Eingabe ist. Die abweichende BFS aus `targeting_probe` wird korrekt nicht benutzt.
- `source_proof` bindet historische Git-Blobs an das alte Manifest, vergleicht die sechs benötigten Funktions-ASTs einschließlich Docstrings und bindet aktuelle Dateien erneut. Aktuelle sechs Quellhashes stimmen mit bindings überein. Die relevante historische/aktuelle Quelldifferenz wurde lesend geprüft; keine Python-/AST-Neuberechnung durch diesen Reviewer.

## Archivschema und Kontext

Der Observer speichert `mask/a`, Calleraktion, Call-time Position/Energie/Ziel und `arguments_after` tatsächlich an der jeweiligen Helfergrenze. `public`, Unitmasken und Ziele stammen anschließend aus demselben kanonischen Entscheidungscontext. Historische `assigned`, `passable` und `energy_map` werden zwischen diesen Punkten im relevanten Aktionspfad nicht geändert; der frameweise Zielcache entspricht hier `PathCache.get`. Die Spiegelung ist bereits in diesem Kontext enthalten; eine zusätzliche Spiegelung im Port wäre falsch.

Der Runner bindet Golden-Eingaben an Unit/public, prüft Reihenfolge und doppelte `_path_fix`-UIDs, akzeptiert ausschließlich beobachtete unveränderte Argumente und legale Bewegungen und verlangt exakte historische Rückgaben. Erst danach zählt er die hypothetischen Fälle des Frames. Ein späterer Fehler verhindert die gesamte `summary.json`; zuvor geschriebene JSONL-Zeilen bleiben Teil eines unvollständigen Laufs. Fehlende Kontexte, Schlüssel, Formen, nicht reproduzierbare Goldenfälle oder unvollständige 303/300/3-Framezahlen führen zum Abbruch.

## Nenner und Interpretation

Die Nenner sind nachvollziehbar: `unit_decisions` zählt archivierte `ally_ids` pro Entscheidungsframe, also keine unabhängigen Partien und nicht ausschließlich bewegungsfähige Units. Es zerfällt in `no_assigned_target + assigned_units`; letzteres in `no_deterministic_guided_move + deterministic_guided_moves`. Zufallsfallbacks bleiben ausgeschlossen und sichtbar gezählt. Änderungen werden pro Match/Zielklasse, Schritt, Partie und unterschiedlichem Kartenseed berichtet.

`0.035 × hypothetical_helper_changes` ist nur die vorab beschriebene theoretische Masse unter festgehaltenen Archivzuständen und den angenommenen Zweigwahrscheinlichkeiten. Sie ist weder beobachteter Trainingsanteil noch Endaktionsänderung, Qualitätsgewinn oder Wirkungsschätzung. Auswahl bekannter Niederlagen/Siege, alte Evalmasken und abhängige Unitzeilen sind in SPEC und Ausgabegrenzen ausdrücklich begrenzt.

## Noch erforderliche echte Abnahme

Root muss die exakt geprüften Bytes freigeben. Ein zulässiges Ergebnis erfordert alle zwölf gebundenen Dateien, 3636 Frames/3600 Entscheidungen, sämtliche Goldenfälle exakt, mindestens einen Goldenaufruf, unveränderte Inputs/Quellen/HEAD am Ende und konsistente JSONL-/Summenzähler. Laufzeitgrenze oder Datenfehler bedeutet unvollständig, ohne Zusatzarchive oder automatische Wiederholung. Ein PASS des 18-Fälle-Selfchecks ersetzt diese Abnahme nicht.

Dieser Review führte keine Pythonprogramme, Tests, Modellimporte, Spiele oder gzip-Inhaltsanalyse aus und änderte keine Repo-/Trainingsdateien. Die gemeldeten 18 synthetischen PASS-Fälle wurden nur gelesen. Geschrieben wurde ausschließlich dieser Reviewbericht.
