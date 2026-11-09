# Unabhängiger technischer Artefaktaudit

**PASS.** Genau vier vollständige technische Fälle unter Quelle `71090f760788bdcec8d7158bc5aab4fd47d406cc` unabhängig geprüft. Einmaliger externer Prüfer: Exit 0, leeres stderr, **1.046 Checks, 503 Hashbindungen, 477 eindeutige Dateien**. Keine Projektimporte, Originalvalidatoraufrufe, Torch-/Modellladungen, Tests, Spiele oder Trainingsfreigabe.

| Modus | Karte / Seite | Matchresultat | Punkte | Rewardübergänge |
|---|---|---:|---:|---:|
| OFF | 9946007 / player_0 | 3:0 | 785:304 | 3489 |
| OFF | 831006 / player_1 | 1:2 | 1252:1037 | 3421 |
| ON | 9946007 / player_0 | 2:1 | 572:596 | 3323 |
| ON | 831006 / player_1 | 2:1 | 1055:1241 | 3167 |

Alle Keys/Reihenfolgen, 303/v2 und Ergebnis-/Punktarithmetik korrekt. Je Modus kumulativ 60000→60303→60606 Envschritte, null Updates, loss null und identische aufgezeichnete q-/Target-/leere-Adam-Identitäten. Die vier tatsächlichen JSONL-Zeilen stimmen mit der Receipt überein. Höhere Punkte sind kein Ersatz für gewonnene Matches.

**OFF:** Beide vollständigen `paired_row`-Blöcke exakt gleich der gebundenen Golden-Referenz. Beide tatsächlichen kompakten Reward-NPZs unabhängig mit den zwei alten Kontroll-NPZs verglichen: Keys, Dtypes und sämtliche UID-/Outcome-/Kontroll-/Gegenformelwerte exakt gleich. Semantische Arrayhashes und Gegenformeldigests eigenständig reproduziert. Alte globale MATCH20-Replayidentität bewusst nicht als Kontrollgate verwendet.

**ON:** Beide nativen Aktions- und öffentlichen Trajektoriendigests unterscheiden sich von OFF. Aufgezeichnet: 1119 geänderte legale Präferenzen auf 6490 aktiven Einheitsschritten, 600 Netzaufrufe und 21600 Mitgliedsforwards, konsistente kumulative Zähler. Die 36 geordneten Quellidentitäten einschließlich Lernmitglied 18, exakt 35 eingefrorene Identitäten und deren Gleichheit über alle Fälle und Start49 sind konsistent gebunden.

Die **drei verschiedenen realen Mechanismusbeispiele** numerisch selbst nachgerechnet: jeweils 36×6 endliche, Float32-repräsentierbare Werte, eigener Rohoutput exakt an Index 18 und echte legale Masken. Float64-Mittel aus den exakten Float32-Eingaben bestätigt jeweils die legale Präferenzänderung 3→2. Maximale Mittelwertabweichung **6,524×10⁻⁷**, innerhalb der vor Ausführung definierten Float32-Summations-/Divisionsgrenze von höchstens **1,068×10⁻⁵** (`u=2^-24`, gamma35). Keine nach Ergebnis angepasste Toleranz und kein zusätzlicher Forward.

Alle vier neuen Rewardarrays unabhängig auf Form/Finitheit/UIDs/Outcomes, semantische Hashes, gespeicherte Gegenformeldigests und ursprünglichen 18×Outcome-Kontrast geprüft; maximaler Kontrastrest **3,553×10⁻¹⁵** bei vorher fester Originaltoleranz. Kontrollwerte sind endlich nach Float32-Quantisierung. Das prüft die archivierten Formelbelege; der vollständige tatsächliche technische Replay wurde nicht separat archiviert.

**RNG/Start49:** Aufgezeichnete Vor-/Nach-Setupidentitäten aller vier RNG-Familien gleich; OFF/ON-Start48-Basis identisch. Python-, NumPy- und privater PCG64-Initialzustand für Start48 und Start49 eigenständig aus den festen Seeds rekonstruiert und deren Hashes verglichen. Torch-RNG-Gleichheit bleibt ein gebundener Livehashbeleg. Start49 hat korrekte Initialidentitäten und exakt null Handlungen, Forwards und Beispiele.

Admission, Receipt, Ownerkommando und -Receipt, alle sieben neuen Artefakte, vollständige neue Source-/Input-/Executable-/Schutzbindungen sowie die 406 alten Sourcebindungen geprüft. Golden-Referenz und versiegelte Trainingsclosure eng wiederverwendet; kein breiter alter Trainingsaudit. Originalowner **54667**, Worker **54679** und seine Prozessgruppe vor und nach Prüfung tatsächlich abwesend; Returncode 0, complete/active leer. V14 und ZIP unverändert.

**Grenzen:** Keine unabhängige Wiedergewinnung aller rohen eingefrorenen Tensoren aus den aufgezeichneten Hashes; keine Rohbeobachtungen, vollständigen technischen Replay-/Regelprovenienzspuren oder historischen Bibliotheks-/Torch-RNG-Snapshots. Native Digests binden beide Spieler; Aktionsfolgenänderung ist kein isolierter Regelursachennachweis. Beispiele prüfen drei gespeicherte Mittelungen, nicht jeden Liveforward. Keine Stärkeaussage oder automatische nächste Phase.

SHA256:

- Admission: `61c9a89f09509525a1ed9a8a024ec6ac4711e26459f7ce6ced39db7622b31922`
- Receipt: `61cb389468f835184e824f5838369e54442b6be7dcadd1a27ff1a8afa306ede3`
- `check.py`: `04e981030a7764ed2e7eb175406e71a45167dab62a96db35f74c5f1cac9e5614`
- `results.json`: `669bbab91a9f7dce8d4a8c5db304b1f148648094dbc89dbdd40c64528a8e42a2`
- `bindings.json`: `f5985a6cf40602fe0da10bb314d0a3d0b6fed21655165c76df6cfc63b7c4a3c0`
- `run.log`: `2e39c8099b61a6433c912c4b868318f480cd26bc414931ef00dd548330b92afc`
