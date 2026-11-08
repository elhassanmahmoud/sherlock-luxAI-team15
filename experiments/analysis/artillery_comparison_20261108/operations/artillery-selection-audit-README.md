# Vorbereiteter unabhängiger Artillerie-Auswahlaudit

**Nur statisch vorbereitet, nicht ausgeführt.** Es wurden weder Python/Modelle/Tests/Spiele gestartet noch Ergebnisdateien der laufenden Artilleriestudie gelesen. Einzig `/tmp/artillery-selection-audit.py` und diese Anleitung wurden geschrieben. Der Code adaptiert eng den vorhandenen unabhängigen Fog-Auswahlaudit.

Fest: V14 / CONTROL38 / ALIGNED38, 11 Jobs / 440 vollständige Spiele. Auswahl-Panel 9800000–9800019, direkte Vergleiche 9800100–9800119, jeweils beide Seiten. Reservierte Bestätigungslisten 9801000–9801019 und 9801100–9801119. CSV-Matrix, Befehle/Receipts, Ganzzahl-Halbsiege, fünf Auswahlbedingungen und feste Rangfolge werden unabhängig nachgerechnet. Ganze Karten als Einheiten, 5000 PCG64(0)-Bootstrapziehungen mit 95-%-Perzentilen. Keine neuen Spiele, Kandidatennachrücker oder Promotionentscheidung.

## Noch erforderliche tatsächliche Root-Pins

HEAD, Kandidatengewichte und Abnahmehashes werden ausdrücklich **nicht** aus einem ungeprüften späteren state.json übernommen. Root muss nach abgeschlossener Trainingsabnahme, akzeptierter Kandidatenmontage, Kartenaudit und finalem Vergleichscommit eine separate `/tmp/artillery-selection-root-pins.json` erzeugen. Sie enthält echte, von Root geprüfte Vorabwerte; idealerweise vor dem ersten Auswahlspiel:

- `schema_version`: 1; `approved`: true; `profile`: `artillery_alignment_20261108`; `phase`: `selection`; `root`: absoluter Studiencheckout.
- `expected_head`: vollständiger späterer Vergleichs-HEAD (40 Hexzeichen).
- `historical_acceptance_sha256`: tatsächlicher Trainingsabnahmehash.
- `admission_sha256`: tatsächlicher Kandidatenzulassungshash.
- `seed_acceptance_sha256`: tatsächlicher Hash von `experiments/analysis/artillery_comparison_20261108/operations/seed_acceptance.json`.
- `model_sha256`: exakt die Rollen V14, CONTROL38, ALIGNED38 mit ihren tatsächlichen SHA-256-Werten.
- `source_identity`: vollständige vorab geprüfte Vergleichsquellenidentität, einschließlich Interpreter und Quellinventar. Sie muss im späteren State/Launch/Provenance exakt wiederkehren.
- `files`: absolute Pfade → SHA-256 für alle akzeptierten Vorabinputs: Auswahljobplan, Kandidatenzulassung und sämtliche `admission.input_sha256`-Dateien, drei Rollenmodelle, die fünf festen archivierten Gegnergewichte, Spec/Plan/Größenvermerk sowie vollständige Frischebelege und alle vier Kartenlisten. Quellidentität ist separat gebunden. Keine späteren CSVs, Laufzustände oder Auswahlzusammenfassung als Ersatz für diese Vorabpins einsetzen.

Der Auditor verlangt den separat von Root übergebenen SHA-256 dieser Pindatei (`--pins-sha256`), prüft ihre Bytes vor und nach der Analyse und bindet die Datei im Bericht. Ohne tatsächliche Pins ist der Ablauf gesperrt. Keine Muster-Pindatei oder erfundene Istwerte wurden angelegt.

Frischeprüfung folgt dem Adapter: exakte vier Kohorten, akzeptiertes Audit mit `no_observed_conflicts=true` und nichtleeren Grenzen, ursprüngliches Rohartefakt (auch `.json.gz` möglich) sowie optionale weitere Belege. Alle Artefakte müssen gehasht, im Checkout und im eingefrorenen Supervisorinput vorhanden sein. Dieser Auditor wiederholt nicht den vollständigen historischen Kartenscan, sondern prüft dessen zuvor unabhängig freigegebene Hash-/Entscheidungskette.

## Einmalige spätere Ausführung

Erst wenn Supervisor und eigene Worker vollständig beendet sind, alle 440 Datensätze samt Zusammenfassung vorliegen und Root die Ausführung ausdrücklich freigibt:

```text
<vorhandene .venv/bin/python> -B /tmp/artillery-selection-audit.py --completed-authorized --pins-sha256 <von Root geprüfter echter Pindateihash>
```

Ausgaben exklusiv `/tmp/artillery-selection-audit.json` und `.md`; keine Überschreibung oder automatische Wiederholung. Der numerische Teil importiert nur NumPy nach vollständiger Artefakt-/CSV-Prüfung, mit numerischen Threads=1. Keine Projekt-, Torch- oder Modellimporte.

Grenzen: Auswahl ist explorativ, keine Übernahmefreigabe. Zwei Trainingsstarts und nur 20 Kartencluster begrenzen die Aussagekraft. ALIGNED minus CONTROL wird deskriptiv verglichen; keine allgemeine kausale Regelwirkung. Spielstärke kann nur aus dem gesamten vorgesehenen Verfahren einschließlich ggf. unabhängiger Bestätigung beurteilt werden. Das vorbereitete Skript ist noch nicht zur Laufzeit geprüft.
