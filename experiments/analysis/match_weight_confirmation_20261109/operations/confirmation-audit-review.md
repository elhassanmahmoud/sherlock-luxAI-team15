# Unabhängiger Endaudit: einmalige MATCH38-Bestätigung

**Datenaudit PASS; Leistungsbestätigung nicht bestanden.** Der unveränderte externe Prüfer wurde genau einmal nach tatsächlichem Ende der Originalprozesse ausgeführt: Exit 0, leeres stderr, 24.837 protokollierte Checks, 512 Hashbindungen und 488 eindeutige gehashte Dateien. Keine Projektimporte, Tests, Modellladungen, neuen Spiele oder Projektänderungen.

## Tatsächliche Resultate

| Gegner | MATCH38 W/D/L | V14 W/D/L | Gepaarter Scorekontrast, 95%-Kartenintervall |
|---|---:|---:|---:|
| Solution | 38/0/2 | 38/0/2 | 0 pp [−7,5; +7,5] |
| default | 40/0/0 | 40/0/0 | 0 pp [0; 0], degeneriert |
| Square-Solution | 37/0/3 | 34/0/6 | +7,5 pp [−2,5; +17,5] |
| rush | 40/0/0 | 40/0/0 | 0 pp [0; 0], degeneriert |

Panel insgesamt MATCH38 155/0/5 gegen V14 152/0/8, mittlerer Scorekontrast **+1,875 pp [−1,25; +5,625]** auf 20 Karten. Direkt MATCH38 gegen V14 **58/0/62**, Score **48,3333 % [35; 61,6667 %]** auf 60 anderen Karten und 120 Spielen.

| Vorab festgelegtes Teilgate | Tatsächlich | Erfüllt |
|---|---:|---|
| Mindestens 72 echte Direkt-Siege | 58 | Nein |
| Untere Direkt-Scoregrenze > 0,5 + 1e-12 | 0,35 | Nein |
| Panelmittel ≥ −1e-12 | +0,01875 | Ja |
| Untere Panelgrenze ≥ −0,025 − 1e-12 | −0,0125 | Ja |
| Solution-Siege mindestens V14 | 38 ≥ 38 | Ja |
| default-Siege mindestens V14 | 40 ≥ 40 | Ja |
| Square-Siege höchstens zwei weniger | 37 ≥ 32 | Ja |
| rush-Siege höchstens zwei weniger | 40 ≥ 38 | Ja |

`passed=false`; `promotion_authorized=false`. Kein Nachschlag, Ersatzkandidat oder automatischer V14-Ersatz. Das breite Direktintervall beweist auch keine allgemeine Unterlegenheit. Solution-Gleichstand beweist keine Solution-Verbesserung. Die Panelbedingungen bleiben empirische Stabilitätskriterien, kein formaler allgemeiner Nichtunterlegenheitsnachweis; insbesondere [0,0] bei default/rush erfasst keine unbekannten Kartenrisiken.

## Unabhängig geprüfte Originaldaten und Bindungen

Alle **440 rohen CSV-Zeilen** unabhängig mit `csv.DictReader` gelesen: exakt 160/160/120 eindeutige feste Gegner/Karte/Seite-Schlüssel, beide Seiten, 303 Schritte, Punktzählung v2, endliche Messwerte und konsistente Matchresultate, Gewinnindikatoren sowie Punktvergleiche. Keine ausgeschlossenen oder ersetzten Zeilen. Die tatsächlichen Ownerbefehle entsprechen exakt den festen Modellen, Gegnern, Kohorten und jeweils einem Worker. Die zwei Paneljobs endeten vor Start des einzigen Direktjobs.

Absolute W/D/L, alle acht Teilgates, Panel-/Gegner-/Direktintervalle und sämtliche Degenerationsflags vollständig selbst nachgerechnet; kein Aufruf der ursprünglichen Analyse. Panelwerte wurden zuerst je Karte über alle vier Gegner und beide Seiten gepaart gemittelt, dann 20 ganze Karten gemeinsam resampelt. Direkt wurden 60 Kartenmittel aus beiden Seiten resampelt. Je Statistik frischer PCG64/default_rng(0), 5000 Ziehungen, feste 2,5-/97,5-Perzentile. Alle resultierenden Summaryfelder stimmen mit dem Original überein; numerischer Gleichheitsvergleich mit der vorher festen Toleranz 1e-12.

Tatsächliche eingefrorene Quelle **98f2b02de3923aa3b4b1c81ad2c2a56b620594e2** vor und nach Prüfung bestätigt; vollständiges Sourceinventar und alle zugelassenen Source-/Input-/Executable-/Schutzdateibindungen geprüft. V14 p0/p1 und ZIP sowie die beiden akzeptierten Evalkopien unverändert. Die versiegelte Auswahl, ihre fünf CSV-Bytehashes und historische technische Montage-/Loaderannahme wurden gebunden wiederverwendet; keine alten Rohdaten oder Tensorarchive erneut ausgewertet.

Vor dem Start und nochmals nach Abschluss des Audits tatsächlich abwesend: Owner **49127**, Originalworker **49144/49149/50193**, Awake **49266** sowie sämtliche Worker-Prozessgruppen. Alle drei ursprünglichen Returncodes 0, Owner complete/active leer. Unveränderte vollständige Owner- und CSV-Dateien während des Audits geprüft; Prozesssnapshots extern archiviert.

Der Seedbeleg behält das rohe **REVIEW_REQUIRED**. Sein einziger nachprüfungspflichtiger Treffer ist die eigene COHORTS-Definition, identische akzeptierte Sourcebytes und exakt die reservierten Bereiche. Keine beobachteten CSV-/JSON-Verwendungen im gebundenen Scan. Lokale Scanlücken, insbesondere nicht erneut gelesene JSONL-Historien, seedlose und externe Daten, bleiben bestehen. Keine neue Kartensuche und keine globale Frischebehauptung.

## Grenzen und Belege

Die CSV-Arithmetik ist unabhängig geprüft; Engineaktionen und interne einzelne Matchpunkte lassen sich ohne Rohtraces nicht neu rekonstruieren. Fehlerfreiheit beider Agenten ist durch unveränderten Quellabbruch und erfolgreiche Originaljobexits gebunden, keine separat archivierten Fehlerzähler in CSV. Historisch akzeptierte Montage-/Loader- und Tensoridentitäten werden über unveränderte Dateien/Receipts gebunden; hier keine Deserialisierung oder neue Inferenz. Deskriptive Intervalle für feste Agenten, keine Familienkorrektur über Projektversuche, Garantie oder isolierte Rewardkausalität.

SHA256:

- Admission: `3083a345f132d3e4fb51edbaf5fcaf8eb65f31f6507898a6140594359d736bdf`
- Originalsummary: `ab91bab17645443386e3106d90316dfc6d9eddb74ee617ec4d04068ad3ed589f`
- `check.py`: `aeeb5b30fcfbedb59ce685755c9a64199744a95d4ca3d5ef8d21e1fe00268fff`
- `results.json`: `1a031b806e5f47d5b4269f662b0e6cc9ce9e7e98efb23f1b809a66e83f7359fe`
- `bindings.json`: `c8a839e11d19dcf7cfbd4d972a89f7301803f6f423ad45b7f210654d93b0b58c`
- `run.log`: `485be3e6a92ddf8231035837e892387997ff1bd02e3f37eaac5ac3d08f78847b`

Sämtliche eigenen Ausgaben ausschließlich unter `/private/tmp/match-weight-confirmation-audit/`. Keine Folgephase freigegeben.
