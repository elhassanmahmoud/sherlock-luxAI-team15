# Artillerie-Kartenprüfung

**Ergebnis nach Prüfung:** Keine beobachtete frühere Verwendung oder fremde Reservierung der angefragten Karten in den geprüften lokalen Quellen. Das ist keine Garantie über nicht protokollierte oder externe Läufe.

## Geprüfte inklusive Bereiche

- Training43:9430000–9430199; Vorlauf43:9435000–9435019.
- Training44:9440000–9440199; Vorlauf44:9445000–9445019.
- Diagnose:9600000–9600003.

## Tatsächliche Abdeckung

- Alle8 registrierten Worktrees; 15,171 strukturierte Artefaktpfade und 8,845 Textpfade. SHA-256-Deduplizierung identischer gespeicherter Bytes.
- Eindeutig geparst:1655 CSV,372 JSONL,1311 JSON; 1672 eindeutige Textdateien zusätzlich.
- 1,640,184 numerische CSV-Seedwerte,42,083 JSONL-Seedwerte; 694 konservative JSON-Intervallkandidaten.
- Verwendungsüberschneidungen CSV/JSONL:0; JSON-Nennungen/Intervallüberschneidungen/Stringnennungen:je0. Genau eine deduplizierte Textzeile nennt diese Bereiche: aktuelle Artillerie-Spec, ausdrücklich als eigene Reservierung erlaubt. Keine beobachtete Reservierung anderer Studien.
- Lese-/Parsefehler:0; Text-Decodierungslücken:0; geänderte/entfernte/hinzugekommene strukturierte Eingabedateien:0; Änderungen bereits erfasster Textdateien:0.

## Nachgerechnete formale Ausnahme

Das automatische Rohurteil bleibt in JSON als `REVIEW_REQUIRED` erhalten: Während der Prüfung wechselte nur der HEAD der Studienkopie von `b7332c8` auf `18a81c7`. Der überprüfte Commit verändert ausschließlich `agents/sherlock/config.py`, `agents/sherlock/main.py` und `tests/test_art_splash_training.py`; keine Seed-/Ergebnis-/Reservierungsdatei wurde verändert. Diese reine Commit-Metadatenänderung ist keine Kartenüberschneidung. **Root hat diese genaue HEAD-only-Ausnahme ausdrücklich bestätigt und akzeptiert**; die Freigabe ist separat unter `adjudication.root_accepted_exception` dokumentiert, ohne den Rohbefund umzuschreiben. Das gesonderte `adjudication`-Objekt hält Diffpfade, Zeitpunkt und endgültiges begrenztes Urteil fest.

Der erste technische Scannerversuch brach vor Berichtserzeugung wegen einer lokalen Variablenkollision ab. Nach Korrektur wurde die gesamte Prüfung erfolgreich erneut ausgeführt (51.82s). Keine teilweise gelesenen Daten als vollständiges Ergebnis verwendet.

## Bekannte Lücken

286 eindeutige CSV-Dateien ohne Seedspalte; 219 eindeutige JSONL-Dateien ohne numerisches Seedfeld; 258,913 JSONL-Zeilen ohne numerische Seedmetadaten; 1030 nichtleere ungültige oder uneindeutige Seedwerte. Einzelpfade/Werte sind in JSON erhalten. Diese Lücken bedeuten unbekannt, nicht unverwendet.

Strukturierte Prüfung: experiments/logs/replays mit CSV/JSONL/JSON einschließlich gzip. Zusätzliche Textprüfung: Wurzel/docs/scripts/experiments/logs/replays mit md/py/sh/txt/log, numerische Literale und explizite Intervalle. Rechnerisch erzeugte Bereiche, nicht unterstützte Schemas, Binärformate, andere Rechner und nicht registrierte Arbeitskopien bleiben mögliche Lücken. Textpfade wurden während der ergänzenden Passage inventarisiert; neue erst danach hinzugefügte reine Textdateien sind nicht zugesichert erfasst. Verzeichnissymlinks wurden nicht verfolgt. Eigene drei Audit-Dateien explizit ausgeschlossen; keine stillen weiteren Ausnahmen.

Vollständige Inventare, Hashes, Header, Feldschemata, Intervallkandidaten, Fehlerlisten und HEADs stehen in `seed-audit.json`; ausführbarer Stdlib-Scanner in `seed-audit.py`. Keine Modelle geladen, Spiele oder Tests gestartet; nur die drei beauftragten Audit-Dateien geschrieben. Nach dem Audit neu gestartete oder neu reservierte Läufe sind vor tatsächlichem Trainingsstart erneut mit dem festgelegten Plan abzugleichen.
