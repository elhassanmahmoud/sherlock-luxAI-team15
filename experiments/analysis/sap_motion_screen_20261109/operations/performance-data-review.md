# Unabhängige SAP-Motion-Ergebnisnachrechnung

**Tatsächlich ausgeführt: PASS, Exit 0, 2833 Prüfungen.** Alle 120 abgeschlossenen Spiele, 123 gebundene Rohdateihashes, die drei erfolgreichen Jobabschlüsse, Zulassung/Quelle/Config sowie originale Zusammenfassung wurden mit dem vorab vorbereiteten reinen Datenchecker geprüft. Keine Projektimporte, Modelle, Tensorloads, Spiele oder Tests; ausschließlich JSON/JSONL, Dateihashes und unabhängige NumPy-Bootstraprechnung.

- Gegen Solution: OFF 38/40, ON 38/40, jeweils Score 95 % und deskriptives 95%-Kartenbootstrapintervall [87,5; 100] %. Gepaarter Kontrast 0 Prozentpunkte [0; 0]. Das degenerierte Intervall beschreibt ausschließlich diese 20 beobachteten Kartencluster und beweist keine Gleichwertigkeit außerhalb dieses Datensatzes.
- Direkt ON gegen OFF: 21 Siege, 0 Remis, 19 Niederlagen; Score 52,5 %, deskriptives Intervall [50; 57,5] %. Vorgegebene Schwelle 60 % verfehlt (2W+D=42 statt mindestens48).
- Exposition: 10 von20 Panelkarten; 478 geänderte Schüsse gegen Solution, 12 im direkten Vergleich, OFF null. Expositions- und Solution-Gate erfüllt, Direktgate verfehlt. Kein qualifizierter Folgeversuch aus diesem Screen, keine Übernahme, kein belegter Stärkezuwachs.
- Bootstrap unverändert: ganze Karten mit beiden Seiten, gepaarter Panelkontrast, 5000 Ziehungen, PCG64 Seed0, Perzentile2,5/97,5; 20 Kartencluster je Block, deskriptive unadjustierte Unsicherheit.

Die separate enge Dateiprüfung bestätigt beide V14-Gewichte sowie Gruppe15.zip unverändert und tatsächlichen HEAD `4ceff1943e274f476dab82c37b9a93e682a00c63` weiter gleich zur Laufaufnahme. Sie liest lediglich die drei Dateien für SHA-256 und den aktuellen Commit; keine Tensorarchive werden deserialisiert.

Ausgeführt mit dem bestehenden Projektinterpreter und begrenzten Threads:

`env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B /tmp/sap-motion-data-review/performance-data-check.py`

Belege: `execution.log`, `performance-data-review.json`, `protection-check.json`; Quellenanpassung unverändert dokumentiert in `preparation.json` und `adaptation.diff`. Die technischen ON-Modellgrößen wurden hier nicht erneut aus Frames rekonstruiert; das bleibt die getrennte abgeschlossene technische Aufnahme. Kein breiter neuer Quellenaudit.
