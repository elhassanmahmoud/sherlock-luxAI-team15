# Begrenzter Kartencheck: Threat-Warmstart

**Keine beobachtete frühere Nutzung oder fremde Reservierung der vorgesehenen 220 Karten.** Der einzige konkrete Treffer ist die eigene neue Planreservierung. Keine absolute Frischebehauptung oder Spielstartfreigabe.

Geprüft: Training **9950000–9950199** (200 Karten), Vorlauf **9950300–9950319** (20 Karten). Vorhandenes `/tmp/rank-mean-seeds/seed-audit.py` ausschließlich extern kopiert und **nur `RANGES` geändert**; Rücktausch reproduziert exakt die Ausgangsbytes. Ausgabeort folgt unverändert dem Skriptverzeichnis. Kein neuer Scanner, keine Code-/Gitänderung. Historischer Profilname/Überschrift SAP-leading sind absichtlich unverändert; maßgeblich sind die korrekten `ranges_inclusive`.

Einmaliger tatsächlicher Aufruf: `python3 -B /tmp/threat-warmstart-seeds/seed-audit.py --targeted-readonly-scan`, Exit 0. Zeitraum **2026-11-09T12:28:42.216021+00:00 bis 2026-11-09T12:29:03.548298+00:00**, Rohbericht-Dauer **21.38 Sekunden** (Konsolengesamtzeit 21,43 Sekunden).

Acht registrierte Worktrees, **14.679 JSON-/CSV-Pfade** einschließlich gzip und **9.312 Textpfade**. Nach exakter Byte-Deduplizierung: 1.587 JSON-, 1.695 CSV- und 1.905 Textinhalte. Geprüft wurden 1.647.885 CSV-Zeilen, 1.643.224 numerische CSV-Seedwerte, 118.236 JSON-Seedwerte und 728 konservative Intervallkandidaten.

Null CSV-Nutzungsüberschneidungen, null JSON-Zahlen-, Intervall- oder Stringtreffer. Null strukturierte/Text-Lesefehler, Dekodierlücken oder beobachtete Mutationen. **Ein Texttreffer**, weshalb das rohe Werkzeugverdikt unverändert `REVIEW_REQUIRED` bleibt:

- `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/docs/superpowers/plans/2026-11-09-threat-warmstart.md:16`: beide Bereiche werden ausdrücklich als feste Trainings-/Vorlaufkarten vor Start genannt. Eigene aktuelle beabsichtigte Reservierung des neuen Plans; kein Beleg früherer Spiele oder einer fremden Reservierung. Plan war bei gezielter Git-Statusprüfung unversioniert (`??`), kein historischer Dateicommit. Tatsächlicher Planhash gleich Scanbeleg: `dbebd7d9274bfc6ca82fac29b012b4580d176a13d628bc9a39d55468d18698b3`.

Primäre und Studienarbeitskopie standen vor/nach dem Scan auf **8234cbd74410d9359c18f0b31185259ccfee8efc**; alle acht HEADs und das registrierte Worktreeinventar blieben unverändert, vollständige HEADs im Rohbericht. Keine erneute Suche nach dieser gezielten Trefferklärung. Kein lückenloser Freeze behauptet: die Textpfadliste wird am Ende nicht vollständig neu inventarisiert.

Grenzen: 286 eindeutige CSVs ohne Seedspalte mit 4.661 Zeilen; 1.865 heuristisch ungültige Seedfelder ausschließlich in JSON, null ungültige CSV-Seedwerte. **1.992 Roh-JSONL-Pfade bewusst ausgeschlossen**, keine Tensorarchive gelesen. Andere Rechner/unregistrierte Checkouts, undokumentierte oder seedlose Historie, ausschließlich JSONL-belegte Nutzung, berechnete Seedformeln und unbekannte Schemas bleiben offen. Verzeichnis-Symlinks werden nicht verfolgt. Keine Projektimporte, Modelle, Tests, Spiele oder Subagents. Keine neue Leistungsdatenanalyse; bestehende CSVs wurden nur im unveränderten Seedscanverfahren gelesen.

| Beleg | SHA-256 |
|---|---|
| Ausgangsskript `/tmp/rank-mean-seeds/seed-audit.py` | `9374cd84578c9c9704e6415a98b5c9cf794a28740297cc1d83319df57eababfe` |
| `seed-audit.py` | `5538daf7f5bd2101d45515d7fe88886edbb41b9e910f00d6519ae8b7ecedfac3` |
| `seed-audit.json`, 17,822,706 Bytes | `a2d3bd21a50ccd39080e889f294c68914a1f068dec8146dc49d83c647aced4a0` |
| `seed-audit.md` (automatisches Rohverdikt) | `c7f1581eac47e0251709223312a4b157a618bd707cf978b4cb6c89a807e771e1` |

Lokale Beobachtungen erfordern keine Änderung der vorgesehenen Bereiche. Rohverdikt und diese manuelle Einordnung gemeinsam erhalten; eine technische Startaufnahme bleibt separat.
