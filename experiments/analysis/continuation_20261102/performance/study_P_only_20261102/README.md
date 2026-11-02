# P-only: Auswahl abgeschlossen, Bestätigung läuft

Stand 02.11.2026, 19:03 Berlin. **Noch kein freigegebener V14-Nachfolger.**

P verwendet dieselben 36 Netze wie V14; nur `point_pair_swap` und
`art_move_guard` sind eingeschaltet. Die zwei nachtrainierten Teilwellen-Netze
werden nicht eingesetzt. Aktuelle Abgabe und ZIP bleiben unverändert.

## Abgeschlossene Auswahl

100 neue Karten 841000–841099, beide Startseiten, insgesamt 3.000 Spiele.
Panelmittel über sechs feste Gegner; default separat, alle Spiele ohne Remis.

| Messung | V14 | P | Gepaarter Unterschied, 95%-Intervall |
| --- | ---: | ---: | --- |
| Sechserpanel, je 1.200 Spiele | 940/1.200 (78,33 %) | 972/1.200 (81,00 %) | +2,67 pp [+0,42; +5,00] |
| Solution_92, je 200 Spiele | 184/200 (92,0 %) | 184/200 (92,0 %) | 0,00 pp [−1,50; +1,50] |
| Quadrat-Solution, je 200 Spiele | 176/200 | 177/200 | siehe Summary |
| V3, je 200 Spiele | 178/200 | 184/200 | siehe Summary |
| V7, je 200 Spiele | 150/200 | 154/200 | siehe Summary |
| V10, je 200 Spiele | 148/200 | 154/200 | siehe Summary |
| V13, je 200 Spiele | 104/200 | 119/200 | siehe Summary |
| default, je 200 Spiele | 200/200 | 200/200 | 0,00 pp |
| P direkt gegen V14, 200 Spiele | — | 118 Siege / 82 Niederlagen | 59,0 % [53,0; 65,0] |

Alle vier vorab festgelegten Auswahlbedingungen erfüllt; einzig P nominiert.
Die gepaarten Bootstrap-Intervalle resamplen ganze Karten einschließlich beider
Seiten und aller sechs Panelgegner zusammen (5.000 Ziehungen, PCG64 Seed 0).
Der unabhängige Auditor bestätigt Daten, Hashes, Zählungen, Intervalle und Gates
mit **137 Prüfungen ohne Abweichung**. Das ist eine Auswahl, keine Bestätigung.
Diese Karten und das lokale Panel unterscheiden sich von Mahmouds historischer
Liga; die absoluten Quoten dürfen nicht als deren Fortschreibung gelesen werden.

## Einzige Bestätigung

Seit 02.11., 19:03:10 Berlin läuft der bereits vor Auswahllektüre festgelegte
Vergleich: 4.200 V14- und 4.200 P-Spiele auf 842000–842299, zusätzlich 600 direkte
Spiele auf 843000–843299. Maximal zwei Evaluationsworker, kein paralleles Training.
Unverändert Source `03e54e267242ff642c126313fe5f512ed9d959ac` und Master
`e1731478088ec7bdaa2b63a51a6ae60f0c7ecedc4522fbedfbcfbb0f1517ba03`.
Auch zwischen beiden Phasen bleiben Quellen, HEAD, Interpreter und Gewichte
eingefroren. Keine Ergebnisse vor vollständigem Phasenabschluss zur Wahl nutzen.

Eine Übernahme verlangt sämtliche Bestätigungsgates und technische Kurs-/Paket-
und Reproduktionsprüfung. Bei Fehlschlag keine zweite Bestätigung, kein Nachrücken
und kein nachträgliches Vergrößern. Die bedingte PT2-Route ist durch die
P-Nomination endgültig ausgeschlossen; ihre Vorbereitung bleibt unbenutzt.

## Belege und Reproduktion

- `selection_summary.json`: vollständige Root-Auswertung und Einzelgegnerintervalle.
- `selection/`: bytegleiche CSVs, Pläne, abgeschlossener Status und Prozesslogs.
- `review/P_selection_independent_audit.*`: unabhängige Gegenrechnung und Belegliste.
- `review/P_confirmation_actual_admission_review.*`: tatsächliche Startprüfung.
- `selection_archive_provenance.json`: ursprüngliche Pfade und SHA-256 jeder Kopie.
- `P_candidate_manifest.json`: Herkunft und Tensor-/Config-Zusammensetzung.

Die archivierten JSON-Dateien enthalten absichtlich die ursprünglichen absoluten
Pfade der Performancekopie auf Moayeds Mac. Diese Belege nicht umschreiben.
Das Auditprogramm ist an genau diese archivierte Studie gebunden. Für eine neue
Messung auf einem anderen Rechner einen eigenen Plan und Ausgabepfad erzeugen;
historische Receipts sind kein verschiebbarer neuer Versuch. P kann aus der
festen V14-Sicherung mit dem versionierten Kandidatenbauer rekonstruiert werden.
Der ursprüngliche lokale P-Checkpoint bleibt bis Gesamtabschluss unangetastet.
