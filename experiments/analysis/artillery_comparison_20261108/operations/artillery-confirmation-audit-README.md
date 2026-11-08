# Optionaler unabhängiger Artillerie-Bestätigungsaudit

**Statisch vorbereitet; Ausführung, Syntaxprüfung und Tests: UNRUN.** Keine Python-, Modell-, Test- oder Spielausführung; keine laufenden Auswahlresultate gelesen. Nur `/tmp/artillery-confirmation-audit.py` und diese Anleitung wurden angelegt. Ohne akzeptierten Auswahlkandidaten bleibt das Skript ungenutzt.

Der Prüfer adaptiert den vorhandenen unabhängigen Auswahlprüfer eng auf die festgelegte Bestätigung: genau V14 und der eine akzeptierte Kandidat, 20 Karten 9801000–9801019 × beide Seiten × lokales Sechserpanel plus default = 560 Spiele, dazu 40 Direktspiele auf 9801100–9801119. Zusammen 15 Jobs und 600 vollständige Datensätze. Das lokale Panel besteht aus solution92, sol92_sq, V3, V7, V10 und V13. Kein zweiter Kandidat, Nachrücken, Pooling oder Nachschlag.

Unabhängig rekonstruiert werden vollständige CSV-Schlüssel/Zeilen/Ergebnisarithmetik, sämtliche sieben Haupt- und drei Zusatzbedingungen, Ganzzahl-Halbsiege sowie gepaarte Kartenmittel und 5000 Bootstrapziehungen mit explizitem PCG64(0), 95-%-Perzentilen und identischer Grenztoleranz 1e-9. Default muss bei 40 Spielen wegen der zusätzlichen strikten 99-%-Bedingung 40 Siege erreichen. Nur NumPy für gespeicherte Zahlen; keine Projekt- oder Modellimporte und keine Vorwärtsläufe.

## Von Root später benötigte tatsächliche Pins

Root erzeugt nach unabhängiger Auswahlabnahme und vor Bestätigungsstart `/tmp/artillery-confirmation-root-pins.json` aus verifizierten Istwerten. Hier wurde keine Pindatei mit Platzhalterwerten angelegt. Schema:

- `schema_version`: 1; `approved`: true; `profile`: `artillery_alignment_20261108`; `phase`: `confirmation`; `root`: absoluter Studiencheckout.
- `expected_head`: `70669eb9e1509b1bddff902c22a2b7e394167f97`. Quelleninventar und Interpreter müssen exakt zur akzeptierten Auswahl identisch bleiben.
- `nominee`: genau `CONTROL38` oder `ALIGNED38`, wie in der akzeptierten Auswahl; niemals manuell einen anderen Kandidaten einsetzen.
- `selection_acceptance`: Objekt mit `path` (absoluter Pfad des akzeptierten unabhängigen Auswahlaudits) und `sha256` (dessen tatsächlich geprüfter Hash).
- `selection_summary_sha256`: tatsächlicher Hash der vollständig akzeptierten Auswahlzusammenfassung.
- `confirmation_plan_sha256`: tatsächlicher Hash des erst nach Auswahl erzeugten `plans/confirmation_jobs.json`.
- `historical_acceptance_sha256`, `admission_sha256`, `seed_acceptance_sha256`: tatsächliche, zuvor verifizierte Abnahmehashes.
- `model_sha256`: exakt V14 und der Nominierte mit ihren wirklichen SHA-256-Werten; kein drittes Rollenmodell.
- `source_identity`: vollständige akzeptierte Auswahlquellenidentität einschließlich Interpreter, ausführbarer Datei und Quellinventar. Bestätigungsstate, Launch und Provenance müssen damit vollständig übereinstimmen.
- `files`: absolute Pfade → SHA-256 aller akzeptierten Vorabinputs: Bestätigungsjobplan; Zulassung und sämtliche `admission.input_sha256`-Dateien; aktuelle Rollenmodelle und die fünf festen archivierten Gegner; Spec/Plan/Größenvermerk; vollständige Frischebelege und alle vier Kartenlisten; zusätzlich genau die vom Adapter eingebundenen Auswahlnachweise (Auswahlabnahme, Auswahl-Launch, -Summary, -State, -Provenance, -Jobplan sowie alle elf CSVs und elf Receipts). Diese Dateipins müssen auch im eingefrorenen Bestätigungssupervisorinput stehen. Nicht stattdessen zukünftige Bestätigungsergebnisse oder ungeprüfte Statewerte pinnen.

Die Auswahlabnahme bindet ihre eigene komplette `input_sha256`-Kette einschließlich ursprünglicher Auswahl-Rootpins. Diese Kette wird zusätzlich vor und nach der Nachrechnung bytegenau geprüft; ihre nur auditinternen Dateien müssen nicht künstlich in die Bestätigungssupervisorinputs aufgenommen werden. Die feste Nominierungsrangfolge wird aus den akzeptierten Ganzzahlzählungen erneut geprüft, aber die Auswahlspiele werden nicht als Bestätigungsdaten verwendet und nicht erneut statistisch ausgewertet.

Die Frischekette folgt der akzeptierten Seedabnahme einschließlich Rohartefakt und bekannten Grenzen. Es wird kein neuer historischer Kartenscan ausgeführt. Die zukünftigen Auswahl-/Bestätigungshashes werden ausdrücklich nicht aus einem ungeprüften späteren State als Vertrauensanker übernommen.

## Späterer einmaliger Aufruf

Erst nach vollständigen 600 Datensätzen, beendetem Supervisor einschließlich Rechen- und Wachhalteprozessen, erzeugter Zusammenfassung und ausdrücklicher Root-Freigabe. Root übergibt den separat verifizierten Pindateihash:

```text
<vorhandene .venv/bin/python> -B /tmp/artillery-confirmation-audit.py --completed-authorized --pins-sha256 <von Root separat bestätigter SHA-256 der Pindatei>
```

Ausgaben ausschließlich und exklusiv `/tmp/artillery-confirmation-audit.json` und `/tmp/artillery-confirmation-audit.md`. Existierende Ausgaben führen zum Abbruch; keine automatische Wiederholung oder Überschreibung. Dateihashes, Freeze, vollständige Matrix, Befehle und Receipts werden vor jeder Statistik kontrolliert und am Ende erneut gebunden. Numerische Threads = 1, Bootstrap maximal 5000 × 20 Zahlen pro Aufruf.

`status=PASS` bedeutet nur, dass der Daten-/Statistikaudit besteht. `passed` und die zehn einzelnen Bedingungen berichten separat den festgelegten Leistungsvergleich; das ist noch keine Übernahmefreigabe. Es bleiben nur 20 unabhängige Kartencluster, unadjustierte Intervalle, zwei Trainingsstarts und keine quantitative Powergarantie. Keine allgemeine Regelwirkung, TD- oder Kausalaussage. Eine etwaige Übernahme und technische Abgabeprüfung bleiben Root vorbehalten.
