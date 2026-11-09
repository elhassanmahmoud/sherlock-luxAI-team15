# Begrenzter Kartencheck: Threat-Vergleich

**Keine beobachtete frühere Nutzung oder fremde Reservierung in der geprüften lokalen Evidenz.** Drei eigene neue Planreservierungen und die während des Scans beobachtete Synchronisierung der primären Arbeitskopie sind gezielt eingeordnet. Keine absolute Frischebehauptung oder Spielstartfreigabe.

| Rolle | Inklusive Karten | Zahl |
|---|---|---:|
| Solution | 9946000–9946019 | 20 |
| Direkt gegen V14 | 9946100–9946119 | 20 |
| Direkt gegen Kontrolle | 9946200–9946219 | 20 |

Die Bereiche sind disjunkt (60 Karten), jeweils für beide Seiten. Der Scanner sucht Kartennutzung unabhängig von der Seite; keine neue Karte wurde simuliert oder außerhalb dieses Metadatenchecks aufgerufen.

Methode: vorhandenen `/tmp/threat-warmstart-seeds/seed-audit.py` extern wiederverwendet, RANGES angepasst. Die CSV-/JSON-/Textsuchlogik blieb unverändert. Einzig zusätzlich wurden die lesenden Git-Unterprozessaufrufe durch direkte Worktree-/HEAD-Metadatendateilesung mit Hashbeleg ersetzt (nach enger Auslegung des anfänglichen Gitaktionsverbots; Root stellte später klar, dass lesende Gitbefehle erlaubt waren). Kein Gitbefehl ausgeführt. Vollständige kleine Differenz in `scanner-diff.txt`. Keine allgemeine neue Auditstruktur; automatische historische Profilbezeichnung SAP-leading bleibt erhalten, maßgeblich sind `ranges_inclusive`.

Einmaliger Aufruf: `python3 -B /tmp/threat-comparison-seeds/seed-audit.py --targeted-readonly-scan`, **Exit 0**, 2026-11-09T13:47:00.036801+00:00 bis 2026-11-09T13:47:23.111487+00:00, **23,08 Sekunden**. Acht registrierte Worktrees; **14.714 JSON-/CSV-Pfade** inklusive gzip und **9.376 Textpfade**. Nach Byte-Deduplizierung 1.613 JSON-, 1.695 CSV- und 1.934 Textinhalte. 1.647.885 CSV-Zeilen, 1.643.224 numerische CSV-Seedwerte, 120.971 JSON-Seedwerte und 734 konservative Intervallkandidaten.

**Null CSV-Nutzungsüberschneidungen; null JSON-Zahlen-, String- oder Intervalltreffer; null Lese-/Text-/Dekodierfehler.** Die drei Texttreffer sind ausschließlich `docs/superpowers/plans/2026-11-09-threat-warmstart-comparison.md`, Zeilen 23/26/27: die gerade geplante eigene Reservierung, kein früherer Gebrauch. Planinhalt gezielt gelesen, Scan- und aktueller Hash identisch: `3a69536bc828fd809c6d6ad4d3f59a8f8d4a8e219c2f55f1b57e175cc134d952`. Das rohe Verdikt **REVIEW_REQUIRED bleibt unverändert**.

24 beobachtete Änderungen: Die primäre Arbeitskopie wechselte während des Scans von `af8b2711d37a9fd4509415972345c5849c21db62` zu `18c1b98b87725cb39842e084d9e49985643606d1` und erhielt 23 JSON-Dateien des abgeschlossenen Threat-Trainings. Die Studienkopie stand bereits vor/nach auf `18c1b98b87725cb39842e084d9e49985643606d1`. Alle 23 hinzugekommenen Dateien wurden **nur gezielt nachgehasht**: exakt dieselben Bytes wie ihre bereits im Scan erfassten Studienkopien. Beleg je Datei in `mutation-resolution.json`; keine zweite Suche. Die übrigen sechs HEADs blieben unverändert. Damit kein neuer konkreter Nutzungstreffer, jedoch ausdrücklich kein atomarer Gesamtbestand oder Freeze.

Das vorhandene Archivmanifest wurde gelesen und an den Scan gebunden: `555eab6ed8fd3ced18daf4eb442932b955d341b7ac625f6683218b8896f42bde`. Es beschreibt vier bekannte Replay-NPZ-Gziparchive mit Original-/Archivhashes; deren Binärinhalte wurden **nicht geöffnet**. Keine Gewichte, Tensorarchive oder Simulationen gelesen/geladen.

Grenzen: 286 eindeutige CSVs ohne Seedspalte (4.661 Zeilen); 1.997 heuristisch ungültige Seedfelder ausschließlich in JSON, null ungültige CSV-Seedwerte. **1.998 Roh-JSONL-Pfade bewusst ausgeschlossen**. Externe/unregistrierte Rechner/Checkouts, undokumentierte oder seedlose Historie, ausschließlich JSONL-belegte Nutzung, berechnete Seedformeln und nicht unterstützte Schemas bleiben unbekannt. Verzeichnis-Symlinks werden nicht verfolgt; Textpfadliste am Ende nicht neu inventarisiert. Später neu entstandene Dateien sind nicht ausgeschlossen. Keine Modelle, Tests, Spiele, Repoänderungen oder Wiederholung geschlossener Studien.

| Beleg | SHA-256 |
|---|---|
| Ausgangsskript | `5538daf7f5bd2101d45515d7fe88886edbb41b9e910f00d6519ae8b7ecedfac3` |
| `seed-audit.py` | `fd7474da6db3fa41d41a46067fd66af17874e6760da1f5d97ef98a0742c144be` |
| `seed-audit.json`, 17.951.764 Bytes | `b4502cfa7c4a38e19c74711ec77a4fc7df156858e7ce32b05c2988ed5c91c408` |
| `mutation-resolution.json` | `07f463bdaa3f54812b0ffdf4603c458ac7eda905e9e59e9e01b38ad9b7ac307e` |

Alle Ausgaben bleiben unter `/tmp/threat-comparison-seeds`; Rohverdikt und manuelle Einordnung gemeinsam verwenden. Die vorliegenden lokalen Beobachtungen erfordern keine Änderung der drei Bereiche. Root erstellt die separate Aufnahme.
