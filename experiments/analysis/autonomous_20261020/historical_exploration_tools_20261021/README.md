# Historische Exploration, 20./21.10.2026

Bytegleiche Quellen der damals geprüften Hilfswerkzeuge samt Fixtures, Vorab-Review und nachträglichem unabhängigen CSV-/Hash-Audit. Der Lauf verwendete HEAD `8517f88594e0e909a7d631e197e98b1ed4ca9dcb` (Pair47 zuvor `c0f9c159`; Übergang nur Daten/Dokumentation). `manifest.json` verzeichnet Originalpfade und SHA-256. Alle Pythontexte tragen `.py.txt`, damit sie weder als aktuelle ausführbare Werkzeuge noch als automatisch entdeckbare Tests erscheinen.

**Kein universeller Wiederausführungsbefehl:** Die Quellen enthalten historische absolute Benutzer-/Repository-/tmp-Pfade, feste Daten-/Modell-SHAs, exklusive bereits belegte Ausgaben und inzwischen vergangene Fristen. Die kopierten ursprünglichen READMEs dokumentieren damalige Bedienung, keine aktuelle Startfreigabe. Eine spätere Reproduktion braucht gesonderte Pfad-/Abhängigkeits-/Fristenprüfung; kein blindes Umbenennen und Starten. Confirmation wurde mangels qualifiziertem Entwicklungskandidaten nicht ausgeführt.

Ausgeführt: sechs feste Einzelnetze (Seeds47–49, je3000 Spiele),1440 Einzelnetz-Evaluationen und1200 Ensemble-Evaluationen auf bekannten Entwicklungskarten. Langsamer Epsilon-Abfall hat das vorab festgelegte Methodengate nicht bestanden; auch kein fester21-Netz-Kandidat qualifizierte sich. Keine Übernahme, kein frisches oder direktes Bestätigungsspiel.

`exploration_archive_check.json` belegt den unabhängigen Archivierungscheck: alle18000 Trainings-/2640 Evaluationszeilen, exakte Schlüssel, Seed-/Seitenpaarung, gleicher Gegnerplan/Initialhash, alleiniger Configdiff, alle gespeicherten Eingabe-/Quell-/Gewichtshashes und unabhängig per Indexsampling nachgerechnete5000/Seed0-Kartenintervalle. Kein Torch/JAX oder Modellladen für diesen Check. Endliche Q-/Target-Tensoren bleiben Befund der bereits abgeschlossenen separaten Paaraudits. Kartenintervalle schätzen keine Streuung über weitere Trainingsinitialisierungen.

Modelle/Replaybuffer bleiben lokal und ignoriert; dieses Archiv enthält nur Daten, Protokolle und Textquellen. Die separate40-Spiele-Punktfeld-Diagnose gehört nicht zu diesem Commit.
