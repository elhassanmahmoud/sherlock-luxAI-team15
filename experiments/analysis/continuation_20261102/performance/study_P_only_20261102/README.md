# P-only abgeschlossen: V14 bleibt

Abschluss 03.11.2026, 01:36:40 Berlin. **P verfehlt fünf von sieben
Bestätigungsgates und wird nicht übernommen. V14 und die bestehende ZIP bleiben.**

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

## Abgeschlossene einzige Bestätigung

Vom 02.11., 19:03:10 bis 03.11., 01:36:40 Berlin lief der bereits vor Auswahllektüre festgelegte
Vergleich: 4.200 V14- und 4.200 P-Spiele auf 842000–842299, zusätzlich 600 direkte
Spiele auf 843000–843299. Maximal zwei Evaluationsworker, kein paralleles Training.
Unverändert Source `03e54e267242ff642c126313fe5f512ed9d959ac` und Master
`e1731478088ec7bdaa2b63a51a6ae60f0c7ecedc4522fbedfbcfbb0f1517ba03`.
Auch zwischen beiden Phasen bleiben Quellen, HEAD, Interpreter und Gewichte
eingefroren. Ergebnisquoten wurden erst nach vollständigem Phasenabschluss gelesen.

| Messung auf frischen Karten | V14 | P | Unterschied, 95%-Intervall |
| --- | ---: | ---: | --- |
| Sechserpanel, je 3.600 Spiele | 2.885/3.600 (80,14 %) | 2.896/3.600 (80,44 %) | +0,31 pp [−0,86; +1,47] |
| Solution_92, je 600 Spiele | 578/600 (96,33 %) | 572/600 (95,33 %) | −1,00 pp [−2,33; +0,17] |
| default, je 600 Spiele | 600/600 | 600/600 | 0,00 pp |
| P direkt gegen V14, 600 Spiele | — | 309 Siege / 291 Niederlagen | 51,50 % [48,17; 55,17] |

Keine Remis. Der Auswahlvorsprung wurde nicht repliziert. Die Daten belegen weder
einen gesicherten Gesamtvorteil noch eine generelle Verschlechterung; die
Intervalle enthalten jeweils den neutralen Vergleichswert. Gegen Solution liegt
P auf diesem Block numerisch zurück. Das Ziel 100 % ist nicht erreicht.

| Unverändertes Übernahmekriterium | Istwert | Ergebnis |
| --- | ---: | --- |
| Panel Δ ≥ +1 pp | +0,31 pp | verfehlt |
| Untere Panelgrenze > 0 | −0,86 pp | verfehlt |
| Solution Δ ≥ 0 | −1,00 pp | verfehlt |
| Untere Solutiongrenze ≥ −1 pp | −2,33 pp | verfehlt |
| default ≥ 99 % | 100 % | erfüllt |
| default Δ ≥ −1 pp | 0,00 pp | erfüllt |
| Untere direkte Grenze > 50 % | 48,17 % | verfehlt |

Root-Auswertung, unabhängiger Auditor (**276 Prüfungen**) und abschließender
zweiter Datenreview stimmen überein. Letzterer rechnete die 9.000 CSV-Zeilen und
Ganzkarten-Bootstraps separat nach und prüfte 237 Belegdateien. Alle vollständigen
Datensätze, Source-/Modellbindungen und die absolute Frist wurden akzeptiert;
**Datenabnahme bedeutet hier Ablehnung des Kandidaten**, keine Releasefreigabe.

Eine Übernahme hätte sämtliche Bestätigungsgates und technische Kurs-/Paket-
und Reproduktionsprüfung verlangt. Daher keine technische P-Freigabeprüfung oder
Installation. Keine zweite Bestätigung, kein Nachrücken
und kein nachträgliches Vergrößern. Die bedingte PT2-Route ist durch die
P-Nomination endgültig ausgeschlossen; ihre Vorbereitung bleibt unbenutzt.

Das Betriebssystem protokolliert Clamshell-Ruhezustand am 02.11. von 22:22:49 bis
23:35:47 Berlin mit kurzen Sleep-Service-Weckphasen. Beim P-Panel liegen rund
4.353,7 Sekunden zwischen Kalenderdauer und dem gespeicherten monotonen Timer.
Letzterer misst auf diesem Mac ohne die Schlafzeit. Kein langsamerer Algorithmus
im Umfang dieser Kalenderdifferenz wird daraus abgeleitet. Alle absoluten
Zulassungs-/Endfristen wurden weiterhin anhand der Kalenderzeit geprüft;
Quellen, Eingaben und Gewichte blieben über die Unterbrechung gleich.
`review/P_sleep_timing_metadata.json` enthält die getrennten Zeitbelege.

Die Performancekopie bleibt für historische Reproduktion auf 03e. Erst nach
vollständiger Auswertung/Audit/Freezeabschluss wurde der primäre Checkout auf
Mahmouds 35a9ebc aktualisiert. `zone_rescue` bleibt aus und wurde hier nicht als
neuer Stärkekandidat ausprobiert. Der Server wurde nicht gestartet. Sein Review
nennt zwei konkrete Ressourcenbegrenzungen, die vor einem öffentlichen Einsatz
noch korrigiert werden sollten; siehe den separat archivierten Commitreview.

## Belege und Reproduktion

- `selection_summary.json`: vollständige Root-Auswertung und Einzelgegnerintervalle.
- `confirmation_summary.json`: vollständige Bestätigung mit allen sieben Gates.
- `confirmation/`: sämtliche 9.000 CSV-Zeilen, Prozesslogs, Plan und vollständiger Status.
- `review/P_confirmation_independent_audit.*`, `P_confirmation_final_review.*`: beide Datenabnahmen.
- `review/P_confirmation_source_freeze_closed.json`: geprüfter Abschluss, keine Übernahme.
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
