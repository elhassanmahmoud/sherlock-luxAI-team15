# Schlussreview: künftige Curriculum-Studie

**Kein widersprüchlicher aktueller Startauftrag gefunden.** Beide Dokumente kennzeichnen die Studie als nicht implementierten Entwurf und verlangen vor einem Lauf weitere Festlegungen. Die vorhandenen Warnungen vor dem alten Supervisor, nicht exklusiven Ausgaben, Starts≥50 und automatischen historischen Tests sind korrekt. Keine abgeschlossenen Audits wiederholt, keine Jobs oder Repoänderungen.

## Vor einem tatsächlichen Auftrag noch verbindlich präzisieren

1. **Referenz eindeutig benennen.** „Gleiche V3-Konfiguration“ sollte im Studienplan heißen: beide Arme frische Einzelnetze mit derselben eingefrorenen `full_rules_v3`-Config, `eps_decay_steps=60000`, `sol92_frac=0.7`, `pool_frac=0`; keine Initialisierung aus dem installierten18er-V3. Beide Kontroll- und Versuchsarme unter derselben Quelle neu trainieren. Die alten Kontroll-CSVs47–49 nicht als Ersatz für neue gepaarte Kontrollläufe behandeln. Vorab identische initiale Tensoren/RNG-Zustände prüfen. Fundstelle: Trainingsentwurf Zeilen44–49,77; `scripts/variants.py`, `scripts/experiment.py`.

2. **Entwurf ist noch keine ausführbare Präregistrierung.** Starts sind derzeit nur „beispielsweise47–49“; Validierungszeitpunkte und konkrete Karten sind offen. Vor Start genau diese Angaben, finale Stichprobengröße, Paarung/Bootstrap und technische Abbruchregeln festschreiben. Den Tausch nicht als gesamten Bereich752–893 lesen: Nur die ersten50 ursprünglichen **Sol-Paare** in diesem Bereich werden getauscht, vorhandene Defaultpaare bleiben. Die jetzige Formulierung ist richtig; das muss die Implementierung erhalten. `train_opponent` besitzt bisher keinen auswählbaren frühen Plan.

3. **Methodenbestätigung von Modellübernahme trennen.** „Erst danach getrennte frische Bestätigung“ lässt noch offen, was bestätigt wird: der mittlere Unterschied aller drei Einzelnetzpaare oder ein fest gebauter Ensemblekandidat. Vorab eines ausdrücklich festlegen und gegebenenfalls zwei getrennte Gates definieren. Keine Best-Seed-Auswahl, kein automatisch angehängtes Gewinnernetz. Das +3pp-Gate muss ausdrücklich die gleichgewichtete mittlere Differenz **Versuch minus Kontrolle** meinen; positive Starts ebenfalls paarweise. Fundstellen: Zeile49 und Schlussabschnitt. Der Morgenbericht trennt diese Fragen für die abgeschlossene Studie bereits korrekt.

Diese Punkte verhindern einen falsch designten späteren Lauf; sie verlangen heute keine Umsetzung. Eine abschließende Zeile „Start erst nach eigener Freigabe des vollständigen Studienplans“ würde die ohnehin vorhandene Entwurfskennzeichnung noch eindeutiger machen.

## Historische18.000 gegenüber66.000: Identität statt Zahlenähnlichkeit

Hier ist die Trennung durch konkrete Pfade belegt:

- Erstpräsentation: `docs/presentation/source/QUELLEN.md:13,37,71` nennt `20261010_full_s0..2` und `20261011_full_sym_s0..2`, `old3_sym3`, sechs Basisläufe. Das ist **nicht** die spätere `rules6`-Gruppe vom19.10.
- V3-Herkunft laut Kandidatenmanifest/Herkunftsprüfung: `20261019_full_rules_s0..5` sowie die zwölf4000er-Läufe `sol70`/`opp_pool`, zusammen66.000 dokumentierte Laufspiele. Die Logs beweisen nicht neu den genauen ausgewählten Tensorzeitpunkt; diese Grenze ist im Dokument korrekt benannt.
- Neue Exploration: getrennt benannte Läufe47–49 vom20.10., weitere18.000 Spielausführungen.

**Kleine sprachliche Präzisierung empfohlen:** „getrennte Mengen“ im Trainingsentwurf durch „getrennte Trainingsläufe/Budgetangaben“ ersetzen. Getrennte Läufe bedeuten keine disjunkten Karten: Die drei konkret gelesenen Manifeste `20261010_full_s0`, `20261011_full_sym_s0` und `20261019_full_rules_s0` nennen jeweils Trainingsseeds **0–1499**. Daraus keine unbekannte Checkpointübernahme oder zusätzliche Budgetüberlappung ableiten. Insbesondere nicht allein wegen gleicher18.000-Zahl Erstpräsi und spätere `rules6` gleichsetzen.

## Gesamturteil

Die Übergabe ist als **nicht startfertiger Studienentwurf** konsistent. Keine neue experimentelle Frage oder ein heutiger Lauf nötig. Die sinnvollen Ergänzungen sind konkrete Start-/Vergleichsdefinitionen und die Unterscheidung von Laufidentität und Kartenwiederverwendung; die gemessenen negativen Ergebnisse müssen dafür nicht erneut untersucht werden.
