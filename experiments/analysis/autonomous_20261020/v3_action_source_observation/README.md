# V3-Aktionsfluss: passive Beobachtung auf bekannten Karten

**20 Spiele vollständig reproduziert; keine Policy- oder Gewichtsänderung.** Vorab festgelegter [Plan](../../../../docs/superpowers/plans/2026-10-21-v3-action-source-observation.md), Commits `fd5b350` und vor dem Lauf präzisierter Wahlmöglichkeiten-Nenner `e831f08`. Beobachtet am 21.10.2026, 08:20:36–08:21:17 Berlin: V3 gegen Solution_92, Karten 500720–500729, beide Seiten. Keine Stichprobenerweiterung.

## Ergebnis

| Beobachtung | Anzahl | Bezugsgröße |
|---|---:|---|
| Aktive Unitentscheidungen | 70.200 | maskierte Units mit Energie ≥ 0, außerhalb Matchstart |
| Davon nur eine legale Aktionsklasse | 8.320 | erzwungene Wahl, getrennt betrachten |
| Davon mindestens zwei legale Aktionsklassen | 61.880 | Situationen mit Wahlmöglichkeit |
| Greedy- und Endklasse gleich, bei Wahlmöglichkeit | 56.352 / 61.880 = **91,07 %** | nach Netzmittelung und Aktionsmaske |
| Durch Erkundungsregel veränderte Aktionsklasse | 3.702 / 70.200 = 5,27 % | alle aktiven Entscheidungen |
| Durch allgemeine Regel veränderte Aktionsklasse | 0 / 70.200 | keine Änderung im beobachteten V3-Pfad |
| Durch späte Nachbearbeitung veränderte Aktionsklasse | 1.826 / 70.200 = 2,60 % | ohne kausale Zuschreibung an einzelnen Schalter |
| Mindestens eine Änderung | 5.528 / 70.200 = 7,87 % | keine Rückänderung in diesen Daten |

Über alle aktiven Entscheidungen einschließlich erzwungener Wahl stimmen Greedy- und Endklasse in 64.672 / 70.200 = 92,13 % überein. Negative, noch maskierte Energieslots (454 Entscheidungen) sind separat protokolliert. 60 Matchstart-Schritte mit 600 maskierten Slots erzeugen No-ops ohne erfundene Netzentscheidung; 70.654 sonstige maskierte Entscheidungen + 600 Startslots stimmen exakt mit dem Spieltracker überein.

Bei mindestens zwei legalen Klassen blieb die Greedyklasse in Match 1 zu 89,31 %, in Match 2 zu 91,16 % und in Match 3 zu 92,77 % erhalten. Das sind über Unitentscheidungen gepoolte Häufigkeiten, keine unabhängigen Kartenstichproben oder mittleren Siegquoten.

## Aussagegrenze

Die Netze werden im heutigen V3 nicht bei jeder Entscheidung von späteren Regeln ersetzt. Diese Beobachtung misst jedoch **keinen kausalen Nutzen der Netze oder Regeln**. Features, Zielzuweisung, Gedächtnis, Aktionsmasken und Sap-Zielwahl sind bereits regelgestützt; gleiche Aktionsklasse beweist keine alleinige Netzursache. Ohne-Regel- oder Ohne-Netz-Gegenfaktiken wurden nicht gespielt. Bekannte zehn Karten, keine frische Stärkebestätigung und keine Konfidenzintervalle über korrelierte Unitschritte. Die zukünftige Curriculum-Studie bleibt eine Hypothese, nicht durch diese Häufigkeiten als erfolgreich bewiesen.

## Prüfung und Reproduktion

Die bestehenden Methoden wurden je Aufruf genau einmal ausgeführt; Wrapper protokollieren nur Eingänge/Ausgänge. Keine zweite Q-Berechnung, kein Training/Speichern, keine Konfigurationsänderung. Jede beobachtete Kette wurde zur Laufzeit auf vollständige Stufen, legale Klassen und endgültige Weltaktion einschließlich Spiegelung geprüft. 13 isolierte Tests decken Ketten, Rückänderungen, SAP, Spiegelung, Matchstarts, negative Energie sowie erzwungene und freie Entscheidungen ab.

Alle 23 nichtzeitlichen Spielkennzahlen stimmen in jedem Spiel sowohl mit der Entwicklungs-CSV als auch der früheren Punktfeld-Beobachtung überein (920 Vergleichswerte). Root und unabhängiger Review rechnen alle Zähler aus den gespeicherten gemeinsamen Aktionsketten neu nach, einschließlich legaler Optionszahl und Match→Spiel→Gesamt-Summen. Quellenstand `e831f08`, Interpreter, 91 Quelldateien, 11 Eingaben sowie Ausgabehashes unverändert. Aktuelle V3 und alte Sechser-Sicherung bytegleich.

Die individuellen Masken, Energien und Weltaktionsvektoren wurden nicht gespeichert. Ihre Legalität/Konsistenz wurde durch den geprüften Beobachter zur Laufzeit kontrolliert, nicht im nachträglichen Audit unabhängig aus Einzelzuständen rekonstruiert. Die gespeicherten `legal_count_chains` und `negative_chains` erlauben alle veröffentlichten Häufigkeiten und Nenner nachzurechnen.

`games.jsonl`, `report.json`, `state.json`, Prüfbelege und `archive_manifest.json` enthalten die Daten. Die `.py.txt`-Dateien sind historische Textsnapshots mit festen Pfaden, Hashes und abgelaufener Frist. Nicht unverändert als neue allgemeine Pipeline starten; ursprüngliche Quellen und geschützte Gewichte sind per Hash dokumentiert. Der unabhängig nachvollziehbare Rechenweg für gespeicherte Ketten benötigt keine Modelle. Für eine neue Beobachtung einen neuen exklusiven Ordner und einen neu geprüften Ablauf verwenden.
