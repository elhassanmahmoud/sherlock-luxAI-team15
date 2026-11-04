# Finale Bestätigung vom 04.11.2026: V14 bleibt

**12.000 Spiele vollständig, unabhängige Datenabnahme PASS. FT18 verfehlt vier von sieben festen Gates und ist nicht zur Übernahme qualifiziert. V14 bleibt unverändert die Abgabe.**

400 Vergleichskarten **852000–852399**, beide Seiten, V14 und FT18 gegen sechs Panelgegner plus default: je 5.600 Spiele. Dazu 800 direkte Spiele auf 400 getrennten Karten **853000–853399**. Alle drei Jobs complete und Exit 0; vollständig erwartete Schlüssel, 303 Schritte und Punktezählung v2 wurden im unabhängigen Review geprüft.

Verfehlt sind Panelgewinn mindestens +1 pp, positive Panel-Untergrenze, Solution-Differenz mindestens 0 und Solution-Untergrenze über −1 pp. Die beiden default-Bedingungen und das Direktduell-Gate sind erfüllt. Der Auswahlvorteil wurde im neuen Panel nicht bestätigt; daraus folgt keine gesicherte allgemeine Verschlechterung. Keine Installation von FT18, kein nachrückender Kandidat und keine zweite Bestätigung.

## Belege

- [Offizielle vollständige Auswertung](confirmation_summary.json)
- [Unabhängige tatsächliche Abnahme](review/confirmation_actual_review.md) und [Maschinenreview](review/independent_confirmation_review.json)
- Originale drei CSVs, drei Logs, Plan und Abschlussstate unter [confirmation/](confirmation/)
- [Gemeinsamer Studienfreeze](freeze.json), [Gewichtezuordnung](weights.json), unveränderte [Auswahlzusammenfassung](selection_summary.json)
- [Vorherige vollständige Auswahl](../performance_selection/README.md)
- Zulassung, Seed-Freshness, Startreview und Kandidatenmanifest unter [admission/](admission/)
- [Fester Studienplan](provenance/final_battle_plan.md)
- [Abschlussidentität](closing_identity.json): beide aktiven V14-Gewichte je Checkout, beide V14-Sicherungen, primäre ZIP und Gitstatus
- [Archivmanifest](archive_manifest.json): Originalpfad, Bytes und SHA-256 jeder unveränderten Kopie

CSV-Zeilenumbrüche sind bytegleich erhalten; die übergeordnete `.gitattributes` setzt `*.csv -text`. Originale Ausführungspfade in JSON/Logs bleiben unverändert. Die unveränderte Auditorquelle ist als `.py.txt` archiviert; sie ist keine neue ausführbare Studienquelle. Dieses Archiv bewahrt Nachweise, führt keine Statistik neu aus und ersetzt keine Laufzeitdateien. Interne Belege gehören ins Repository, nicht in die Battle-ZIP.
