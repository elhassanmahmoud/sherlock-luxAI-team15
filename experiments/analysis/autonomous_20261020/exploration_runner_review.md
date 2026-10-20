# Unabhängiger Review des Explorationsversuchs

20.10.2026; rein statisch gegen `docs/superpowers/plans/2026-10-20-exploration-replication.md` und das bereits geprüfte Reward-Replikationsgerüst. **Keine konkreten Blocker gefunden.**

Geprüfte Dateien (SHA-256):

- `/tmp/exploration_replication.py`: `bf3b6f1e1010a4e3c62a61b58839224283b760783e3e62e03cd67fa530585774`
- `/tmp/test_slow_exploration.py`: `a7d528a9173ac85680c0d3776f086c26ac2b86e4a7947fa1c5f55f63d390999e`
- `/tmp/slow_exploration_registry.patch`: `a6f88bccff80e426b238a88382fe2bbf6297f10e92b7ed6c00052e7ec2ccd319`

Die Registry kopiert die bestehenden V3-Overrides in ein eigenes Dict und setzt ausschließlich `eps_decay_steps=454500`. Tests verlangen den exakten Ein-Feld-Unterschied zu 60000, unveränderte Baseline, getrennte Konfigurationsobjekte, deaktivierte Terminal-/Inferenzexperimente und Epsilon-Meilensteine der tatsächlichen Property. Sie allokieren keine Netze; ihre normalen Modulimporte würden dennoch Torch laden und wurden hier nicht ausgeführt.

Der Runner akzeptiert nur Seeds 47–49 und 3.000 Spiele. Neue `exploration`-Pfade und Labels trennen ihn vom Reward-Piloten und dessen verworfener Replikation. Seed und Horizont werden an jeden Childprozess weitergereicht. Die Trainingsfolge entspricht dem tatsächlichen Protokoll: Kartenpaare ab 470000/480000/490000, beide Seiten, 750 Default-Spiele, danach deterministischer Solution92-Anteil 0,7, kein Pool, keine Zwischenvalidierung/Testkarten. Evaluation verwendet je 240 vollständige Spiele auf 500720–500779.

Preflight erzwingt identische frische Q-/Target-Tensoren und Agent-RNG innerhalb jedes Paars, exakten Epsilon-Diff und ausgeschaltete neue Reward-/Inferenzflags. Der tatsächliche Trainingsstart wird erneut mit diesem Preflight verglichen. Finale Tensoren müssen endlich sein; Trainingszeilen, monotone Zähler, NaN-Loss nur vor Lernbeginn, finale Checkpointidentität und vollständige Evaluationskeys werden geprüft.

HEAD, Pythonbinary, Pythonquellen, feste V3-Basis und alte Sicherungen werden erfasst und während des Paars geprüft; aktuelle Abgabegewichte werden am Start erfasst und ebenfalls geschützt. Ausgaben werden exklusiv beansprucht. Jobs laufen sequentiell in eigenen Prozessgruppen. SIGINT/TERM/HUP, Fehler und Deadline führen zur Bereinigung der eigenen Gruppe; keine neuen schweren Jobs ab 03:00 UTC, Abbruchreserve vor 04:00 UTC.

Die vorgesehene Root-Zulassung bleibt Voraussetzung: Gesamtbudget für alle drei Paare plus mindestens eine Stunde Abschlussreserve, keine parallelen Fremdjobs, keine Änderungen der fachlichen Quellen zwischen Paaren. Das Einzelpaar-Skript automatisiert diese übergreifenden Entscheidungen und die spätere Ensembleauswahl ausdrücklich nicht. Der aktuelle Plan legt Bootstrap und Vergleichsidentität bereits konsistent fest.

Verifikation dieses Reviews: beide Pythondateien per stdlib-AST geparst, Hashes ermittelt, Änderungen gegen geprüftes Gerüst gelesen. Keine Torch-/JAX-Imports, Tests, Trainings, Spiele, Git-Aktionen oder Repositoryänderungen. Diese Quellenprüfung ersetzt nicht die vom Hauptagenten vorgesehenen serialisierten RED/GREEN-Tests und tatsächlichen Initialisierungsnachweise.

Root-Integration: gegenüber dem geprüften Runner nur der veraltete Ausdruck „pilot gate“ im Modul-Docstring entfernt. Der verworfene Reward-Pilot ist keine Startbedingung dieses neuen Explorationsversuchs. Codekörper unverändert.
