# Kontinuierliche Verbesserung ab 21.10.2026

**Freigabe:** Moayed beauftragt nach dem Abschluss bis 09:00 erneut autonome Arbeit ohne feste Enduhrzeit, mit Subagents, sinnvollen Commits, Pushes und regelmäßigem Remote-Abgleich. Die frühere Uhrzeitbegrenzung ist für diesen neuen Auftrag aufgehoben. Ziel ist eine möglichst robuste Siegquote gegen Solution_92, angestrebt 100 % auf einer vorab festgelegten unabhängigen Stichprobe. Eine universelle Sieg-Garantie ist weder zugesagt noch aus endlichen Tests ableitbar.

**Ausgangspunkt:** main b008252, installierte all18_v3, SHA-256 aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935. Vorhandene Sicherung experiments/releases/20261020_old3_sym3 bleibt unverändert. Jeder spätere Austausch sichert zusätzlich V3. Source/HEAD/Inputs während laufender Reihen eingefroren; Integration fremder Commits nur am sicheren Übergang. Maximal ein Trainer ODER zwei Evalworker. Keine Agenteninformationen aus Engine-Ground-Truth.

## Ablauf und feste Grenzen

1. Vorliegende 400 Solution-Spiele inventarisieren, Gegnercode prüfen und auf einem fest ausgewählten Diagnoseblock Mechanismen messen. Die nun untersuchten Karten 510800–510999 sind fortan bekannte Entwicklungsdaten, kein unberührter Test.
2. Einen belegten Mechanismus als einzelne optionale Änderung implementieren und unabhängig prüfen. Keine Wiederholung unveränderter negativer Varianten, keine Kombination mehrerer neuer Regeln vor Einzelvergleich.
3. Den bereits geprüften Plan 2026-10-21-early-opponent-curriculum.md implementieren und nach technischen Prüfungen ausführen. Seine früher nur zukünftige Freigabe ist durch diesen neuen Auftrag ersetzt; fachliche Gates, drei gepaarte Starts und Kartenreservierungen bleiben gleich. Jede Studie behält ihr eigenes vorab dokumentiertes Rechenbudget.
4. Qualifizierte Kandidaten auf getrennten frischen Karten gegen V3 und beide Benchmarkgegner bestätigen. Keine Stichprobenverlängerung nach Sichtung negativer Resultate; kein Umdeuten bekannter Karten als frisch. Technische Kurs-/Paket-/Reproduktionsprüfung vor Übernahme.
5. Ergebnisse und Grenzen für Mahmoud laufend dokumentieren. Finaler Auditblock 520000–520999 (1000 Karten, beide Seiten gegen Solution_92) wird ab diesem Plan ausschließlich für einen eingefrorenen, zuvor qualifizierten Kandidaten reserviert. Vor Nutzung erneut Remote-Kollisionen prüfen. Dieses Ziel verlangt keine vorzeitige Auswertung dieses Blocks; nach Nutzung ist er verbraucht. 100 % ist ein Ziel, kein Abbruch- oder Schönrechenkriterium.

Remote-Check vor Beginn: lokal = origin/main b008252, keine Modelljobs, zwölf vorhandene Laufzustände abgeschlossen. 507 versionierte CSVs / 358716 Zeilen ohne 511000–511399 oder 520000–520999. 511000–511399 bleiben dem Curriculumplan zugeordnet. Bereits gescheiterte Ansätze und Messgrenzen: Morgenbericht und jeweilige Roharchive.

### Task 1: Passive Verlust- und Sap-Beobachtung

**Files:** Create scripts/observe_loss_mechanisms.py, tests/test_loss_mechanisms.py. Existing agent/common/scoring/engine files read-only. Root owns plan/docs and data archive.

- [x] Exakt zehn Karten 510862, 510847, 510930, 510956, 510950, 510972, 510819, 510858, 510911, 510839, jeweils beide Seiten, Solution_92, unveränderte V3. Auswahl nach vorliegenden Ergebnissen geschichtet: 13 Verluste/7 Siege; keine Prävalenzhochrechnung.
- [x] Minimaler passiver Observer um vorhandenes play_game, keine zweite Policyauswertung und kein Agentenpatch: zeitlich ausgerichtete t/act/t+1-Ereignisse, einzelne Matchpunkte/-Siege und Snapshots bei Matchschritten 25/50/75/100; bekannte/aktive/produktive Punktefelder und Energie getrennt. Replay/komprimierte Rohereignisse im selben Durchlauf.
- [x] Spezifisch prüfen: pt_sap/STAY-zu-SAP-Übergänge auf Punktefeldern, legal sichtbare gegnerische Nachbarpositionen/Energien vor Entscheidung, tatsächliche Bewegungen/Schäden/Kollisionen danach. Bloße räumliche Nähe beweist keinen Schaden. Optionaler externer Ein-Schritt-Gegenvergleich nur mit exakt demselben Enginezustand/RNG und fixierten gegnerischen Aktionen; niemals an Policy rückführen, nicht als mehrzügige Siegprognose ausgeben.
- [x] Tests vor Implementierung: korrekte Zeitbasis, Matchreset/letzter Punkt, beide Seiten/Koordinaten, sichtbare vs unsichtbare Gegner, Sapkosten/Kollisionsbedingungen; Instrumentierung verändert keine Aktionen. Keine große neue Diagnoseplattform.
- [x] Exklusive Outputpfade, gebundene Quell-/Inputhashes, 20 exakte Schlüssel, 303 Schritte/v2; sämtliche nichtzeitlichen GAME_FIELDS gegen fresh_v3.csv vergleichen. Erste Abweichung stoppt. Tests und unabhängiger Review vor Modellbatch.
- [x] Root führt einmal aus, prüft Rohdaten und entscheidet anhand konkret belegter Sequenzen über nächsten eng abgegrenzten Versuch. Keine willkürliche Regeländerung aus aggregierten Endwerten.

### Task 2: Gezielt testen und trainieren

- [ ] Nach Task 1 Ursache, genaue einzelne Änderung und Entwicklungs-/Bestätigungsgates VOR Ergebnisbeobachtung in eigenem Plan fixieren; TDD, unabhängiger Review, isolierter Kandidat.
- [x] Curriculumplan Tasks 1–4 nacheinander implementieren, prüfen, committen. Neuer frischer Implementer je Task; keine parallelen Codeautoren auf denselben Schnittstellen.
- [ ] Training nach Quellenfreeze starten, Paare vollständig auditieren und nach vorab festgelegten Gates auswerten. Kein Austausch der Livegewichte durch Trainingswerkzeuge.

## Plan-Preflight / Rulings

Task 1 schreibt nur neue Observerdateien; Curriculum Tasks 1/2/4 teilen experiment.py-Interfaces bzw. Studienrunner und müssen sequenziell erfolgen. Analyse-Task 3 verlangt exakt die Spielschlüssel und Ergebniswerte des Runners; die Auswertung akzeptiert keine stillen Inner Joins. Root integriert erst geprüfte Commits. Die Diagnose ist absichtlich begrenzt: nicht jede mögliche Latenz erfordert neue Instrumentierung vor dem ersten konkreten Mechanismustest. Bei fehlender Ursache kein spekulativer Agentenpatch, stattdessen kontrollierter Curriculumversuch. Kosten einer falschen Sap-Hypothese bleiben auf Observer und eine präregistrierte Entwicklungsprüfung begrenzt.

## Ergebnis der ersten Diagnose

Task 1 mit unveränderter V3 abgeschlossen und archiviert. Alle 20 Referenzen exakt reproduziert. Der postulierte unmittelbare Sap-Kollisionsmechanismus wurde durch die tatsächliche Engine widerlegt; kein Agentenpatch daraus. Späte Belegungsrückstände sind beschrieben, nicht kausal isoliert. Daher nächste Ausführung des unveränderten Curriculumplans, keine neue Inferenzvariante. Siehe loss_observation im Archiv continuous_20261021 und neuesten Arbeitsstand.

## Tatsächliche Ausführung

Curriculumstudie `20261021_early_contact_v1` am 21.10. um 11:44:34 Berlin gestartet, eingefrorener Arbeitszweig `sherlock-counterplay` Commit `a5d2e61`. Geprüfte Implementierung auf main veröffentlicht; Anlaufcheck ohne Befund. Training läuft fortlaufend unter exklusivem Supervisor. Noch kein neuer qualifizierter Kandidat. Hauptcheckout-Dokumentation ist vom eingefrorenen Versuch getrennt; dortiger Plan darf während des Versuchs nicht nachgezogen werden.
