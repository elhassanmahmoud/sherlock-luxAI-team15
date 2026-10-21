# V3: Aktionsstufen beobachten, 21.10.2026

Vor neuen Beobachtungsdaten festgelegt. Nach abgeschlossener V4-Bestätigung bleibt V3 unverändert Abgabe. Diese begrenzte Diagnose beantwortet eine noch offene Vorbereitungsfrage für Training und Professor-Review: Wie oft wird die maskierte Greedy-Aktionsklasse der Netze anschließend verändert?

## Fester Umfang und Grenzen

- Installierte V3, SHA-256 `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`; keine Overrides, kein Training, keine Gewichtsspeicherung.
- Zehn **bekannte** Entwicklungskarten 500720–500729, beide Seiten gegen Solution_92: genau **20 Spiele**. Keine Erweiterung nach Ergebnis.
- Ein Evaluationsworker, numerische Threads eins, keine parallelen Modelljobs.
- Vollständige Reproduktion sämtlicher vorhandener nichtzeitlicher Spielkennzahlen aus V3-Referenzen. Beobachtung darf weder Aktionswahl, Zufallszustand, Belief, Lernmodus noch Masken verändern.
- Aktive Unitentscheidungen über alle drei Matches als Hauptnenner. Matchstart-No-ops getrennt, keine erfundenen Netzentscheidungen an Reset-Schritten. Zusätzlich nach Match 1/2/3 aufschlüsseln.

## Instrumentierung und Auswertung

Die bestehende `act`-Implementierung bleibt unverändert. Beobachtende Wrapper um `_explore_action` und `_rule_override` zeichnen ihre Eingangs- und Ausgangsaktionsklasse je Unit auf. Daraus wird die maskierte Greedyklasse rekonstruiert: Eingabe der Erkundungsregel, falls aufgerufen, sonst Eingabe der allgemeinen Regel. Nach `act` liegt die endgültige kanonische Aktionsklasse in `_prev_actions`; die ausgegebene Weltaktion muss dazu einschließlich Spiegelung passen. Keine zweite Netzberechnung oder neue Q-Auswahl.

Vor dem Lauf Tests für Kettenkonsistenz, ausgelassene Erkundungsregel bei Sap, identische Aktionen, Änderungen und Rückänderungen, Matchstart und beide Spiegelungsseiten. Feste Config muss den erwarteten Evaluationspfad ohne CNN-Mischung verwenden. Bei unklarer Aktionsherkunft oder Inkonsistenz abbrechen, nicht still eine Kategorie zuordnen.

Pro Spiel und Match erfassen:

- Anzahl aktiver Unitentscheidungen sowie Häufigkeit jeder Aktionsklasse am Greedy- und Endstadium.
- Änderung durch Erkundungsregel, Änderung durch allgemeine Regel, weitere Änderung zwischen Regel-Ausgabe und Endaktion.
- Greedyklasse gleich Endklasse; mindestens eine Zwischenänderung; Zwischenänderungen, die am Ende zur Greedyklasse zurückführen.
- Vollständige Übergangszahlen Greedy → Erkundung → Regel → Endaktion, damit die Summen unabhängig nachrechenbar sind. Überlappende Änderungsraten nicht als disjunkte Anteile addieren.

## Zulässige Schlussfolgerung

Nur deskriptive Aktionsfluss-Häufigkeiten auf zehn bekannten Karten. Keine Konfidenzintervalle oder Tausende Unitentscheidungen als unabhängige Stichprobe. Gleiche Aktionsklasse beweist keine alleinige Netzursache: Features, Zielzuweisung, Masken und Sap-Zielwahl sind bereits regelgestützt. Eine Änderungshäufigkeit beweist keinen kausalen Nutzen einer Regel; die Gegenfaktik ohne Regel wurde nicht gespielt. Das ist **keine** neue Netz-/Regel-Ablation und kein Stärkevergleich.

## Schutz und Abschluss

Plan, Beobachter, Quellen, Interpreter, Kandidat, aktuelle Abgabe und alte Sicherung vor/nachher per Hash prüfen; während des Laufs HEAD/Quellen einfrieren. Neue exklusive Ausgabepfade, keine Überschreibung bestehender Daten. Unabhängiger Review vor Start, Rohsummenprüfung und Referenzabgleich danach. Spätestens 08:40 Berlin abschließen oder als unvollständig abbrechen; keine Policy- oder Gewichtsübernahme aus dieser Beobachtung. Danach Morgenbericht bis 09:00. Falls Vorbereitung/Prüfung nicht rechtzeitig fertig wird, den Lauf auslassen und ehrlich dokumentieren.
