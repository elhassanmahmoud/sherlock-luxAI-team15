# Sampled-Target: Frischeaudit vorbereitet, noch nicht gestartet

**PREPARED / UNRUN.** Nur externe Textadaption des vorhandenen Auditors; kein Scan, Import, Syntaxcompile, Test, Modell oder Spiel ausgeführt. Die sechs neuen Kohorten und Pilotdateien bleiben bis zur Annahme ausschließlich unter `/tmp`. Karte **4242 ist bereits bekannt und wird für Technik wiederverwendet; sie gehört zu keinem Frischeurteil.**

| Kohorte | Inklusive Zielspanne |
|---|---|
| prefill45 | 9915000–9915019 |
| train45 | 9910000–9910079 |
| prefill46 | 9925000–9925019 |
| train46 | 9920000–9920079 |
| panel | 9930000–9930019 |
| direct | 9930100–9930119 |

Grundlage: `/tmp/sampled-target-pilot-spec.md`, bei Vorbereitung SHA-256 `2c99912b1db2c601c14cdfa4681c494290ca385394638918574434a1f9517b94`. Zusammen 240 verschiedene Zielkarten, keine Leistungsaussage oder Kartenreservierung durch diese Vorbereitung.

## Feste Herkunft und enger Unterschied

Vorlage `/tmp/artillery-comparison-seeds/seed-audit.py`, SHA-256 `b21292538e425f0caa709b01f96d6125f297a1a2ab2c8c006d438eb757ceb414`.

Vorbereitete Fassung `/tmp/sampled-target-seeds/seed-audit.py`, SHA-256 `f29a816897c411c8e7c133847b5f3793ca85e037a7a549fd8093ff0b64da6b4d`.

Änderungen beschränken sich auf neue Zielspannen/Profil und 4242-Abgrenzung, leere Repository-Reservierungsallowlist, explizite Startsperre/keine Ausgabeüberschreibung und Prüfung exakt derselben acht Worktrees. Der alte JSON-Stringfilter war auf Präfixe 943/944/960 festgelegt; er wird durch den bereits in der Textsuche verwendeten allgemeinen Zahlentokenansatz mit anschließender exakter Zielbereichsprüfung ersetzt. Unterstrichschreibweise wird berücksichtigt. Keine Rohdaten-/Dateitypen oder Konflikte ausgeschlossen. Die bestehende strukturierte/Text-Scanlogik und Rohstatusentscheidung bleiben ansonsten erhalten; zusätzlich wird eine Änderung des gesamten Worktree-Inventars als Mutation protokolliert.

## Genau dieselben acht Arbeitskopien

- `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15`
- `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15`
- `/Users/moayedshawesh/Desktop/KI/sherlock-counterplay`
- `/Users/moayedshawesh/Desktop/KI/sherlock-enemy-tie`
- `/Users/moayedshawesh/Desktop/KI/sherlock-ensemble-validation`
- `/Users/moayedshawesh/Desktop/KI/sherlock-november-followup`
- `/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics`
- `/Users/moayedshawesh/Desktop/KI/sherlock-v4-joint`

Die aktuelle registrierte Menge wird erst beim autorisierten Start gelesen und muss exakt übereinstimmen. Aktuelle HEADs werden vor/nach dem Lauf erfasst, keine historischen HEAD-Werte als heutige Identität ausgegeben.

## Vor tatsächlichem Start

Root **und** Watcher müssen gemeinsam ein stabiles Fenster bestätigen: keine Schreibvorgänge an gescannten Daten/Texten, auch keine Kontingent-/Statusdateiaktualisierungen, Installationen, Umbenennungen oder HEAD-/Worktree-Wechsel. Root bestätigt die geprüften Skriptbytes und dass die sechs Zahlenlisten unverändert zur Methode passen. Während des ganzen Scans stabil halten. Die CLI-Bestätigung dokumentiert nur die Bedienerbestätigung; sie ist kein automatischer Nachweis dieser Freigaben.

Erst danach einmalig mit dem vorhandenen gebundenen Interpreter:

```sh
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B /tmp/sampled-target-seeds/seed-audit.py --root-and-watcher-stable
```

Ohne Flag beginnt kein Inventar; Import ist gesperrt. Existierende `seed-audit.json` oder `seed-audit.md` sperren den Aufruf. Der Lauf erzeugt ausschließlich diese zwei Ergebnisse neben dem Skript, mit exklusivem Schreiben. Kein automatischer Neustart oder Löschen alter Belege. Root beurteilt Rohbefunde separat; `REVIEW_REQUIRED` bei Treffern/Fehlern/Mutationen bleibt im Rohbericht erhalten, auch wenn ein späterer Vermerk etwas erklärt.

## Abdeckung und Grenzen unverändert offenlegen

Strukturierte Rohsuche: `experiments`, `logs`, `replays`; CSV/JSONL/JSON und deren gzip-Varianten, Seedfelder, numerische Nennungen und konservative Intervallkandidaten. Ergänzend Texte an der Wurzel sowie unter `docs/scripts/experiments/logs/replays`: `.md/.py/.sh/.txt/.log`, Zahlen und explizite Intervalle. SHA-256 der gespeicherten Bytes, Deduplication, Pfade, Statwerte, Fehler, ungültige Werte, seedlose Dateien/Records, HEADs und beobachtete Mutationen werden vollständig erhalten. Keine erlaubten Pilotreservierungen innerhalb des Repositorys: jede dort gefundene Zielnennung bleibt zu prüfen.

Kein Beweis „nie verwendet“: andere Rechner, unregistrierte Kopien, fehlende/seedlose Daten, unbekannte Schemas, errechnete Formeln, Binärformate und nicht UTF-8-dekodierbare Texte bleiben Lücken. Verzeichnis-Symlinks werden nicht verfolgt; `.git/.venv/venv/node_modules/__pycache__` bleiben wie zuvor ausgeschlossen. Strukturierte Dateien werden am Ende erneut inventarisiert; bekannte Textdateien werden erneut auf Statänderungen geprüft. Die Vorlage inventarisiert neu angelegte Textdateien nicht in einem zweiten vollständigen Textdurchlauf; deshalb ersetzt ihr Mutationsprotokoll keine Stabilitätsbestätigung. Ein lokaler Rohstatus ohne beobachtete Konflikte ist nur ein begrenzter Befund und noch keine Root-Frischeabnahme.

Keine neuen Ergebnisdateien wurden in dieser Vorbereitung erzeugt. Tatsächliche Laufzeit-/Syntaxprüfung steht aus.
