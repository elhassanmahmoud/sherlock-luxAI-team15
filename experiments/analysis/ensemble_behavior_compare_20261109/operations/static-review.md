# Statische Review: Ensemble-Behavior-Vergleichsentwürfe

**Status:** Kein konkreter Implementierungsblocker in der statischen Prüfung gefunden. Das ist keine Laufzeit- oder Testfreigabe. Die Entwürfe wurden nicht importiert und nicht ausgeführt.

## Geprüfter Umfang

- Vertrag: `/private/tmp/ensemble-behavior-comparison-plan/spec.md` und `plan.md`
- `/private/tmp/ensemble-behavior-compare-draft/ensemble_behavior_compare.py` (425 Zeilen)
- `/private/tmp/ensemble-behavior-compare-draft/ensemble_behavior_compare_owner.py` (101 Zeilen)
- `/private/tmp/ensemble-behavior-compare-draft/test_ensemble_behavior_compare.py` (518 Zeilen)
- Bestehende Hilfsfunktionen/CLI-Signaturen wurden nur als Quelltext gelesen. Keine Tests, Imports, Archive, Simulatoren oder Modelle ausgeführt.

## Vertrag gegen Implementierung

- Die Montage nimmt die Original-36 in Reihenfolge und hängt nur die beiden akzeptierten ON-Endnetze an. Die bestehenden Referenzkopien werden nur geladen; die technische Phase serialisiert ausschließlich `behavior.pth`. Stock-Loader und unveränderte Inferenzkonfiguration werden geprüft.
- Trainingsschluss wird an Root-Closure, getrennte Trainingsaufnahme, State, Release, technische Abnahme, beide Final-Receipts und geschützte Inputs gebunden. Die Performanceaufnahme verlangt zusätzlich eine getrennte Root-Abnahme der Nullspiel-Montage.
- Die fünf festen Jobs, drei 20-Karten-Kohorten und 2/2/1-Wellen entsprechen dem Vertrag. Jede `par_eval`-Invocation verwendet `--workers 1`; parallele Owner-Jobs sind auf zwei begrenzt.
- CSV-Prüfung verlangt 40 eindeutige Seed/Seiten-Schlüssel je Job, vollständige Kohorten, beide Seiten, 303 Schritte, Punktzählversion 2 sowie konsistente Match- und Punktresultate. Die Analyse prüft alle fünf CSVs vor Gates/Intervallen und maskiert keine fehlenden Spiele durch Schnittmengen.
- Die vier Gates zählen tatsächliche Siege; Remis gehen nur mit 0,5 in beschreibende Scores ein. Bestehen führt nur zu Nominierung. Bootstrap-Auswertung nutzt die bestehenden Ganzkartenhelfer und legt degenerierte Intervalle sowie historische Kontrollen und wiederholte Auswahl offen.
- Owner-Entwurf verwendet begrenzte Prozessgruppen, Quota-/Quellen-/Input-Guards, feste Joblisten, Fehlerstopp und Cleanup der eigenen Gruppen; nach Fehlern werden keine späteren Wellen gestartet. Es gibt keinen automatischen Phasenwechsel oder Resume.
- Die synthetischen Tests decken Bindungen, Montage, CSV-Vollständigkeit, Resultatarithmetik, Gates, Wellen und Cleanup gezielt ab und markieren selbst, dass sie noch nicht ausgeführt wurden.

## Grenzen vor Integration

Die statische Prüfung bestätigt weder, dass die echte Root-Closure alle vom Draft verlangten Felder/Formen hat, noch die Laufzeitverbindung der gebundenen Referenz-Receipts und Python-Imports. Vor einer echten Aufnahme müssen nach Trainingsabschluss die geplanten gezielten synthetischen Tests und unabhängigen Admission-/Receipt-Prüfungen tatsächlich laufen. Die Tests dürfen nicht als bereits ausgeführt dargestellt werden.
