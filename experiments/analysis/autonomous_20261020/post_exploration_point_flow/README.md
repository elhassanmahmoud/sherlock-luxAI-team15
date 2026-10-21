# Punktfeld-Diagnose, 21.10.2026

40 vollständige Beobachtungsspiele, V3/V4 auf zehn bekannten Karten und beiden Seiten gegen Solution_92. [Ergebnisreview](point-flow-final-review.md), [Kennzahlen](point-flow-final-review.json), [Laufzustand](state.json). Kein Agentenpatch und kein Gewichtswechsel.

Die vollständigen Rohbeobachtungen werden platzsparend als `v3_observations.jsonl.gz` und `v4_observations.jsonl.gz` versioniert. Lokal sind die unkomprimierten Originale zusätzlich erhalten. Nach einem frischen Clone vor der historischen Prüfung mit `gzip -dk v3_observations.jsonl.gz v4_observations.jsonl.gz` entpacken. SHA-256 der entpackten Bytes steht im Archivmanifest. Keine Datenzeilen wurden gefiltert.

`historical_snapshots/` enthält bytegleiche Textkopien der ausgeführten Werkzeuge, Fixtures und des vorab festgelegten Plans. Dortige absolute Pfade, Zeitgrenzen und HEAD-Prüfungen dokumentieren den damaligen Lauf; dies sind keine universell ausführbaren neuen Skripte. Die Untersuchung ist abgeschlossen und wird nicht nochmals gestartet.

Root wiederholte die reine Datenprüfung am 21.10. um 07:31 Berlin: 104 Identitäten unverändert, alle 40 Referenzergebnisse reproduziert, gzip-Rohdaten und Snapshothashes geprüft. Installierte V3 und alte Sicherung unverändert.
