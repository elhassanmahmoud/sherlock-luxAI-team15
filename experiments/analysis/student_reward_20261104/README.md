# Schülernetz-/Reward-Studie vom 04.11.2026

Abgeschlossen: **V14 bleibt**. [Deutscher Bericht](../../../docs/SCHUELERNETZ_REWARD_20261104.md). 464 RL-bezogene und 600 diagnostische Spielausführungen; keine Ausfälle oder ausgeschlossenen Spiele. Die vier Einzelnetz-Kandidaten sind keine freigegebenen Abgaben.

- `preflight/`: Vorabprotokolle, lokale Seed-Prüfung, Test- und Codebelege.
- `student/` und `student30/`: vollständige Laufmanifeste, historische Zeilendiagnostik, Originalbefehle.
- `rl/`: beide ursprünglichen Trainingsbelege unter Commit `5b9f883`, alle 200 Rollout- und 32 Validierungszeilen je Arm; unabhängige 94-Punkte-Prüfung.
- `diagnostic/`: fünf CSVs mit je 120 Spielen, vorab eingefrorenes Protokoll, Quellen-/Modellkontrolle, unabhängiger Datenbericht und Abgleich mit `scripts.compare_report`.
- `candidate_manifest.json`: exakte Hashes und Größen aller vier versionierten Checkpoints.

Die historischen Roh-Replays und die neu entstandenen Lernpuffer sind lokale Daten, kein Bestandteil dieses Git-Archivs. Für neue Läufe müssen Eingaben vorhanden und neue Ausgabeordner gewählt sein. Historische Prüfbelege enthalten die damaligen absoluten Pfade und Quellhashes; sie sind keine Aufforderung, alte Ergebnisse mit neuem Code zu überschreiben. Die ursprünglichen RL-Hashprüfungen wurden vor der nachfolgenden Veröffentlichungskorrektur abgenommen.

20 frische Karten, beide Seiten, drei Gegner; Bootstrap nach ganzen Karten, 5.000 Ziehungen, Seed 0. Ein Trainingsstart und mehrere explorative Vergleiche begrenzen die Aussage. Keine Freigabehürde wird durch diese Diagnose ersetzt.
