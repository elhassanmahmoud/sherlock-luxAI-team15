# Statische Nachprüfung: Sampled-Target Task 1/2, Fix 1

**PASS für die drei gezielt nachgeprüften Korrekturen.** Keine offenen Befunde aus dieser engen Nachprüfung. Das ist keine Funktions-, Laufzeit-, Studien- oder Trainingsfreigabe; sämtliche Tests bleiben **UNRUN**.

Geprüfte unveränderte Dateien:

- `/tmp/sampled-target-staging/scripts/sampled_target_agent.py`: SHA-256 `c767ee07a6fcf9566e762e105eec36a3b51e44664cb1b4b77e82d93ddd414bf9`.
- `/tmp/sampled-target-staging/tests/test_sampled_target_agent.py`: SHA-256 `020819bc80df0b1ff81d4c390110bf8ca13fbff84ee74f54636d3625252657eb`.

1. **Spiegelungsfixture korrigiert:** Tests Zeile 242 erwarten jetzt 1→2 und 2→1 bei gespiegelter Seite. Das entspricht unverändertem `geo.MIRROR_DIR = [0,2,1,4,3]`. Keine Anpassung der Agentgeometrie an die zuvor falschen Testdaten.

2. **Adam-Vollständigkeit vor Live-Mutation:** Agent Zeilen 556–581 verlangt bei `learn_steps > 0` die drei Pflichtfelder jedes gelieferten Zustands und nach dem temporären Load exakt einen vollständigen Zustand für jeden gebundenen Parameter. Damit werden sowohl der leere Gesamtstate als auch fehlende Parameter/Momente abgefangen. Der Step muss skalar, endlich, nichtnegativ und exakt gleich dem gebundenen Lernzähler sein; bestehende Moment-Tensor-/Shape-/Dtype- und Endlichkeitsprüfungen bleiben erhalten. Bei null Updates wird ausschließlich leerer frischer State zugelassen. Q-, Target-, Adam- und Replaymutation beginnen weiterhin erst danach (583–587). Die neun neuen Negativfälle in Tests 489–526 erneuern äußere Datei-/Statehashes ausdrücklich, sodass sie die semantische Prüfung statt nur den Hashfehler erreichen; sie verlangen unveränderte Zielzustände. Die positive Reloadprüfung 529–548 umfasst jetzt 0 und 1 Update. Das passt zum festen Pilot mit frischem Adam und durchgehend trainiertem QNet; kein Resume eingeführt.

3. **Vorzeichen getrennt gezählt:** Agent 461–462 ergänzt ausschließlich positive/negative nichtterminale Targetdifferenzzähler im bereits berechneten Batch. Kein zusätzlicher Forward, Samplingzug, Target- oder Optimizerschritt. Die synthetische Fixture 426–450 enthält je eine positive, negative, Null- und terminale Differenz und prüft, dass die beiden Nichtnullfälle trotz sich aufhebender Summe sichtbar bleiben. Zeitbezug, Maskenmitgliedschaft und bisherige Summen unverändert.

Die Änderungen berühren keine Folgeaktionsbindung, Capture-/Commit-Reihenfolge, Core-Terminaldefinition, No-op-Behandlung oder produktive Aktionskette. Der frühere Bericht gilt im Übrigen weiter, einschließlich der noch ausstehenden realen Control-Paritäts-, Persistenz- und Integrationsnachweise. Der einzelne native SAP-Test bleibt eine Prüfung eingereichter Ausgabe, keine zusätzliche Behauptung eines getesteten gespiegelten SAP-Vektors.

Tatsächlich nur Textbereiche und Dateihashes gelesen sowie dieser Bericht unter `/tmp` geschrieben. Kein Python, Import, Compile, NumPy/Torch-Aufruf, Test, Modell oder Spiel; keine Repo-, HEAD-, Gewichts- oder Ergebnisänderung und keine laufenden Bestätigungsresultate gelesen. Root muss nach dem Leistungsfreeze die tatsächliche technische Prüfung separat freigeben.
