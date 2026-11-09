# MATCH38-Bestätigung: unabhängiger Review

## Vorabprüfung von Spec und Plan

Beide Dokumente vollständig gelesen und gegen den freigeprüften Methodenvertrag `/tmp/match-weight-confirmation-method-review.md` abgeglichen. **Keine methodische Abweichung oder offene Planblockade gefunden.** Noch kein abschließendes Codeurteil und keine Prüfung realer Laufdaten.

- Genau 440 Spiele: zweimal 160 Panelspiele auf denselben 20 Karten, anschließend 120 direkte Spiele auf 60 anderen Karten; feste Bereiche 9980000–9980019 und 9980100–9980159.
- Unveränderte akzeptierte MATCH38-/V14-Evalkopien und bisherige Runtime; historische Aufnahme ausdrücklich ohne erneute HEAD-Zulassung gebunden. Neue Werkzeuge erhalten eigene Aufnahme und Tests.
- Alle geprüften Gates unverändert: mindestens 72 echte Direkt-Siege plus strikte untere Scoregrenze; Panelmittel und untere Grenze; zwei exakte gegnerspezifische Siegschutzgruppen. Remis zählen nur im Score 0,5.
- 5000 PCG64-Seed-0-Resamples, ganze Karten; im Panel gemeinsam über alle Gegner und Seiten. Feste Rundungstoleranz 1e-12 einschließlich strikter Direktgrenze vor Daten ergänzt.
- Direktvergleich primär, Panel ausdrücklich empirische Stabilitätswache. Degenerierte Intervalle offenlegen; keine formale allgemeine Nichtunterlegenheit, Solution-Verbesserung bei Gleichstand, Rewardkausalität oder Garantie behaupten.
- Vollständige und konsistente 303/v2-Daten, Fehlerabbruch, feste Schlüssel, keine Zwischenwahl, Verlängerung, Ersatzspiele oder automatische Übernahme. Höchstens zwei Modellworker, Quellenfreeze und getrennte Root-Aufnahme.

Gebundene Dokumente:

- Spec: `docs/superpowers/specs/2026-11-09-match-weight-confirmation.md`, SHA256 `f44fc48d0c73f5307559d1ec217364f51038e810f9e31504a42c05f5e66ee545`.
- Plan: `docs/superpowers/plans/2026-11-09-match-weight-confirmation.md`, SHA256 `3e639507319e0b92acd410645c52f6e95f52a4f1475409aa17b139cbcb32f6d3`.

Finaler Code-/Methodenreview folgt erst nach stabilen Implementierungsbytes und tatsächlicher synthetischer Testmeldung. Bis dahin keine Modelle, Spiele, Tests oder Quellenänderungen durch diesen Reviewer.

## Abschließender Code-/Methodenreview

**Keine offenen konkreten Blocker gefunden.** Runner, Owner und neue Tests vollständig gelesen; die verwendeten Statistik-, Bindungs-, Fehler- und Prozesshilfen gezielt nachgelesen. Die vorhandene Testausgabe enthält tatsächlich `94 passed in 4.72s` (45 neue synthetische Bestätigungsfälle plus bestehende Vergleichssuite). Nicht selbst ausgeführt. Dieses Urteil betrifft die vorliegenden Bytes, keine noch nicht aufgenommenen Laufdaten.

### Aufnahme und unveränderte Modelle

`accepted_selection` verlangt den exakten versiegelten Abschluss, 200 Spiele, erfolgreiche Nominierung und alle vier alten Gates; Summary/Audit/Zähler/Dateien müssen übereinstimmen. Beide alten Jobsätze und Receipts müssen vollständig sein, Returncodes null, Owner complete und active leer; das historische Prozessende bleibt ausdrücklich über den Root-Abschluss gebunden. Alle historischen Inputs und Runtime-Dateien sowie Interpreter/Executable bleiben unverändert. Die frühere Admission wird nicht gegen den neuen HEAD aufgerufen. Nur die zwei historisch akzeptierten Modellpfade mit ihren festen Bytehashes sind zulässig. Keine erneute Montage, Archivladung oder Konfigurationsänderung durch die neuen Werkzeuge.

### Genau 440 gültige Spiele

`COHORTS` stimmt wörtlich mit den beiden Planbereichen überein. Drei Jobs mit 160/160/120 Spielen, zwei Paneljobs dann ein Direktjob, jeder bestehende `par_eval` mit genau einem Worker und ohne Overrides. Der bestehende Runner verweigert erfolgreiche Resultate bei abgefangenen Fehlern eines der beiden Spieler. Die neue CSV-Prüfung verlangt genau die vollständigen, eindeutigen Gegner/Karte/Seite-Schlüssel und kontrolliert 303 Schritte, Punktzählung v2, endliche nichtnegative Ganzzahlmetriken sowie Resultat-/Matchgewinn-/Punktgewinnkonsistenz. Keine stillschweigende Auswahl gültiger Teilzeilen.

### Rechnung und Aussage

Panel wird ausdrücklich mit den vier vorgeschriebenen Gegnern an `panel_delta` übergeben. Die vorhandene Hilfe paart nach Gegner/Karte/Seite und mittelt zuerst die acht Resultate je Karte; genau diese 20 Kontraste werden gemeinsam resampelt. Direkt werden 60 Kartenmittel aus beiden Seiten gezogen. Beide Hilfen starten je Statistik `default_rng(0)`, 5000 Ziehungen, 2,5-/97,5-Perzentile. Genau die acht Teilgates der vier methodischen Gruppen werden konjunktiv geprüft; echte Siege bleiben `result == 1`, Remis nur im Score halb. Die feste 1e-12-Regel einschließlich `direct.low > 0.5 + 1e-12` ist korrekt umgesetzt. Historische `confirm_checks` werden nicht verwendet.

Absolute W/D/L je Modell/Gegner und direkt, Kartenanzahlen, Intervalle und Degenerationsflags werden ausgegeben. Gleiche Kartenkontraste und Nullbreite werden markiert. Die Summary benennt das Panel als empirische Stabilitätswache und schließt formalen Populations-Nichtunterlegenheitsnachweis, allgemeine Garantie, isolierte Rewardkausalität sowie automatische Übernahme ausdrücklich aus.

### Owner und verbleibende Aufnahmebedingungen

Neues exklusives Verzeichnis, kein Resume; vorhandener Compute-Lock, aktuelle Quota/STOP-/Quell-/Input-/Schutz- und Fremdprozessprüfung. Tatsächliche Returncodes, beendete eigene Prozessgruppen und erfolgreiche CSV-Prüfung sind vor Receipt beziehungsweise nächster Welle nötig. Summary erst nach allen drei Jobs; Leistungsfehlschlag ist eine vollständig berichtete negative Reihe. Fehler stoppen ausschließlich registrierte eigene Gruppen; keine Wiederholung oder Ersatzvariante. Die Testfälle decken fehlende/manipulierte Historie, Runtime-/Modelländerung, CSV-Lücken/Duplikate/Konsistenz, Grenzwerte, Degeneration, Reihenfolge und Abbruchpfade ab.

Die neue Kartenannahme ist noch eine separate Root-Aufnahmebedingung: Der von Root gemeldete einzelne eigene Vorbereitungsfund ist statisch die exakt passende `COHORTS`-Definition im neuen Runner. Er ist keine gespielte CSV-/JSON-Verwendung. Seine explizite Klassifikation und die Grenzen des lokalen Scans müssen im gebundenen Seedbeleg stehen. Keine breite Suche wiederholt und keine globale Kartenfrische behauptet. Quellencommit, neue reale Admission, frische Quota und tatsächliche Prozessprüfung bleiben Root vorbehalten.

### Bytebindung

- `scripts/match_weight_confirmation.py`: `956d26e376b6aa2a1919940f833433c62a537e43d9da4515ffcefac6ccc30694`
- `scripts/match_weight_confirmation_owner.py`: `08711dcd29902c5e3c2700e36658e3e89702600ac8bde4d5c92ea86cdea4f1ef`
- `tests/test_match_weight_confirmation.py`: `1746ef1c7146b14ccdf2b3867d2209d4550924fa0a956bea8e70088ede81c5a4`
- Tatsächlicher Testlog `/tmp/match-weight-confirmation-tests.log`: `dfcd6e4cd8f753466abb094ddc20b8a845929c5a22d265c8f21d92d38bab0991`

Nur externe Reviewdatei geschrieben. Keine eigenen Tests, Projektimporte, Modellladungen, Spiele, Quelländerungen oder Freigabe ausgeführt.
