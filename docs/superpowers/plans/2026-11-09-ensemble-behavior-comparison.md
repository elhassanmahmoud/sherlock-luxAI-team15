# Ensemble-Verhalten – fester Vergleich

> Umsetzung mit Subagents, unabhängiger Review und tatsächlicher Root-Prüfung. Vor Aufnahme gilt die zugehörige Spec.

**Ziel:** Die zwei akzeptierten ON-Endnetze unter unveränderter Inferenz als BEHAVIOR38 gegen V14 und CONTROL38 prüfen.

**Architektur:** Schmale neue Quellen-/Abschluss-/Modellbindungen und fünf feste Jobdefinitionen; bestehende Montage-, Loader-, Spiel-, Statistik- und Lifecyclefunktionen direkt importieren. Keine Änderung bestehender Produktions-/Studienquellen.

## Global Constraints

- Drei neue Dateien: `scripts/ensemble_behavior_compare.py`, `scripts/ensemble_behavior_compare_owner.py`, `tests/test_ensemble_behavior_compare.py`. Profil `ensemble_behavior_compare_20261109`.
- Voraussetzung tatsächlicher Trainingsabschluss unter Quelle 71090f7, nicht nur fertige Vorläufe. Externe ungetestete Entwürfe dürfen während des Lernens vorbereitet werden (Root-Ablaufentscheidung); Integration und Testausführung erst nach Ende und Abschluss des Trainingsfreeze.
- Exakt 200 Spiele, 60 bereits reservierte Karten, vier ursprüngliche Gates. Keine Gewichtsänderung am produktiven V14/ZIP, Kalibrierung, Zwischenwahl oder automatische Folgephase.
- Eigene aktuelle Sourcebindung; historische Quellen als unveränderte Untermenge und alte akzeptierte Belege als Daten konsumieren. Keine alten Admissions gegen neuen HEAD aufrufen.
- Maximal zwei Modellworker, keine Tests neben Modellen, tatsächliche Quota, Akku erlaubt, keine Resets durch Codex.

## Review Focus

- Neue Finale haben `behavior`-Metadaten und Rollen on48/on49; keine falschen alten Matchweight-Felder prüfen.
- Training ersetzte Mitglied 18, Evaluation hängt beide neuen Netze an: genau originale 36 + 2 Endnetze, gleicher ursprünglicher Inferenzconfig.
- Kontrollkopien und historische Endmodelle nicht frei neu pinnen, sondern an bestehende akzeptierte Receipt/Root-Abnahme/Originalaufnahme binden.
- Keine CSV-Zeilen unterschlagen, keine Schnittmengenstatistik über unvollständige Karten, direkte Siege nicht mit halben Remispunkten verwechseln.
- Prozessgruppen wirklich beendet, bevor technische Folgeprüfung/Phasenwechsel; keine dritte Modellinstanz, keine automatische Admission oder Promotion.

## Task 1 – Werkzeuge und enge synthetische Prüfung

- Externe Entwürfe erst nach tatsächlichem Trainingsabschluss integrieren; zuerst echte Negativ-/Vertragstests ausführen und erforderliche Implementierung korrigieren. Keine Tests als vorher ausgeführt darstellen.
- Erwarteter Trainingsabschluss: profile, status COMPLETE_TRAINING_NO_STRENGTH_CLAIM, source, admission/hash, state/hash, technical_acceptance, models on48/on49 mit final/receipt/hash, files, protected, actual (4 Technik,80 Vorlauf,800 Lernen,120000 Updates), original_processes_ended und source_and_input_bindings_valid. Root erzeugt ihn ausschließlich aus echten Ergebnissen.
- Bestehende `inference_config`, `mount`, `validate_and_load`, `par_eval`, `validated_results`, `compare_results`, `direct_result` und Lifecyclehilfen verwenden. Keine globale Profilpatchung.
- Separate technische und Performanceaufnahme/Owner, exklusive Ausgabepfade; tatsächlicher Montagebeleg mit allen Mitgliedshashes/Config/Loaderbeweis. Performance nur nach tatsächlicher Root-Abnahme, fünf feste Jobs mit höchstens zwei aktiven Workern.
- Synthetisch falsche Bindungen, Montage-/Config-/Reihenfolgefehler, fehlende/duplizierte/falschseitige CSVs, Remisgrenzen, vier Gates und Fehlercleanup prüfen. Reale Archive/Spiele in Tests sperren. Gezielt passende alte Helfertests, keine unnötige Gesamtsuite.
- Unabhängiger Code-/Methodenreview, Root-Byteprüfung, sinnvolle Quellenpublikation und sichere Hauptkopieaktualisierung vor echten Modellen.

## Task 2 – Tatsächliche separate Aufnahmen

- Root nimmt nullspielige Montage-/Loaderprüfung separat auf; tatsächliche Tensor-/Config-/Reihenfolgeartefakte unabhängig prüfen. Keine implizite Performancefreigabe.
- Nach wirklicher Montageabnahme separate 200-Spiel-Aufnahme, Source/HEAD/Inputs bis Ende erhalten; echte Quota überwachen, Remote nur lesen, keine Tests parallel.
- Alle 200 tatsächlichen CSV-Zeilen, Ergebnisarithmetik, vier Gates und Ganzkartenintervalle unabhängig nachrechnen; Originalanalyse durch Root unter eingefrorener Quelle reproduzieren. Erst nach eigenen Prozessenden und versiegelter Abnahme Freeze lösen.
- Positive/negative Ergebnisse ehrlich mit Unsicherheit und historischem Kontrollvorbehalt dokumentieren, sinnvoll committen/pushen, Hauptkopie sicher aktualisieren. Erfolg nominiert nur, keine automatische Bestätigung/Promotion.
