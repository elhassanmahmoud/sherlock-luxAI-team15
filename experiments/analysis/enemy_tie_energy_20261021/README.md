# Gegnerenergie bei gleicher Entfernung: kein bestätigter Vorteil

Genau eine vorab festgelegte Änderung an V3: Unter gleich nahen sichtbaren Gegnern wird die höhere Energie bevorzugt. Kein Training; sämtliche 18 Netze und übrigen Checkpointinhalte bleiben identisch. Nur `enemy_tie_energy=True` unterscheidet den gespeicherten Kandidaten.

## Ergebnis

60 bekannte Entwicklungskarten 500720–500779, beide Seiten, je V3/Kandidat und Default/Solution_92: **480 vollständige Spiele**. Solution_92: Kandidat **105/120**, V3 **102/120**, keine Unentschieden; Differenz **+2,5 Prozentpunkte**, gepaartes 95%-Kartenintervall **[−2,5; +8,33]**. Default jeweils **120/120**.

Der Punktschätzer ist positiv, der vorab festgelegte Vorteilsnachweis fehlt. **Entwicklungsgate nicht bestanden; Variante beendet, Abgabe bleibt V3.** Kein Nachlegen neuer Karten, keine nachträgliche Schwelle, keine Aussage über Gleichwertigkeit oder bewiesene Schädlichkeit. Die reservierten Blöcke 522000–522399 und der finale 520000–520999-Audit wurden nicht gespielt.

[Root-Auswertung](development_analysis.json), [unabhängige Datenprüfung](independent_audit.md) und [maschinenlesbare Prüfung](independent_audit.json). Ganze Kartenpaare, 5.000 Bootstrapziehungen, Seed 0; feste Agenten auf bereits verwendeten Entwicklungskarten. Alle Schlüssel, Messwerte und 303 Schritte/Punktezählung v2 geprüft. Sämtliche Nichtzeitfelder der 240 V3-Spiele reproduzieren die historische Referenz ([Beleg](baseline_reproduction.json)).

## Technische Prüfung und Herkunft

Quellenstand `8281c1c392b92c2660b07f24bc27ac0ce8b703bd`, experimenteller Zweig `improvement/enemy-tie-20261021`. 439 Tests und 14 Untertests bestanden in 77,57 Sekunden. Acht separate Spiele im unveränderten Kurs-Runner bestanden Lade-, Config-, Modellidentitäts-, frisches-Gedächtnis- und Aktionsformatprüfung; sie sind kein weiterer Stärkenachweis. [Testlog](repository_tests.log), [Runnerbericht](runner_candidate.json), [Identität](candidate_identity.json).

V3-SHA256 `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`; experimenteller Kandidat `184f596c12d7bc860cd6d78d6196a3b4900ba4c42893cac9ce1200ef8eaab7b3`. Der Kandidat gehört zum Featurezweig, nicht zur Abgabe. Er darf nicht unter altem Code ohne den Configschalter ausgewertet werden. Quellimplementierung bleibt auf dem experimentellen Zweig, nicht in main; main enthält das Ergebnisarchiv.

[State und genaue Aufrufe](state.json) binden Quellen, Interpreter, Engine und geschützte Gewichte. Alle 111 gebundenen Dateien, zehn geschützten Eingaben und der Kandidat wurden nach Abschluss geprüft. Der kleine Jobstarter wurde vor seinem ersten Aufruf ergänzend gebunden; Ablauf und Zeitpunkt sind im unabhängigen Audit erhalten. Große Curriculumstudie separat als unvollständig abgebrochen; ihre Daten wurden weder gepoolt noch für diesen Vorteilsnachweis benutzt.

`job_launcher.py.txt` ist ein historischer Ausführungssnapshot mit lokalen Pfaden und abgelaufener Studienidentität, keine aktuelle Startanleitung. Originalpfade in Metadaten bleiben absichtlich erhalten. Die aktuelle Auftragspriorität steht in `docs/ARBEITSSTAND.md`.
