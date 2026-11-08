# Unabhängiger Methodenreview: finaler Sampled-Target-Pilot

**METHOD PASS.** Die festgelegten Änderungen sind methodisch konsistent: zwei feste Zufallsstarts, sechs getrennte Kartenblöcke und vier klar abgegrenzte technische Integrationsspiele vor den eigentlichen Studiendaten. Kein fachlicher Startblocker aus diesem Textreview. Die dokumentierten Aufnahmebedingungen sind weiterhin zu erfüllen; dies ist keine Freigabe für einen noch ungeprüften Runner oder reale Läufe. Einige historische Statussätze sollten vor Übernahme der Dokumente bereinigt werden, siehe unten.

Geprüft ausschließlich lesend gegen die früher akzeptierten Entwürfe:

- `/tmp/sampled-target-pilot-spec.md`, SHA-256 `2c99912b1db2c601c14cdfa4681c494290ca385394638918574434a1f9517b94`.
- `/tmp/sampled-target-pilot-plan.md`, SHA-256 `c290ffebea23ce083c50021c1ef44c189535faba2294994b093055b5e3417a02`.

Die 53 bestandenen synthetischen Tests und der abgeschlossene Artillerievergleich sind der mitgeteilte Root-Stand. Dieser Review wiederholt weder diese Tests noch deren Datenabnahme.

## Kohorten und Anzahl

Alle sechs inklusiven Ganzzahlintervalle sind untereinander disjunkt. Die gemeinsame Verwendung innerhalb eines Startpaars bzw. für alle vier finalen Netze ist ausdrücklich vorgesehen und dient dem gepaarten Vergleich.

| Zweck | Karten pro Block | Ausführungen |
|---|---:|---:|
| Start 45: Vorlauf 9915000–9915019 | 20 × 2 Seiten | 40 je Arm, 80 insgesamt |
| Start 45: Lernen 9910000–9910079 | 80 × 2 Seiten | 160 je Arm, 320 insgesamt |
| Start 46: Vorlauf 9925000–9925019 | 20 × 2 Seiten | 40 je Arm, 80 insgesamt |
| Start 46: Lernen 9920000–9920079 | 80 × 2 Seiten | 160 je Arm, 320 insgesamt |
| Panel 9930000–9930019 | 20 × 2 Seiten × 2 Gegner | 80 je finalem Netz, 320 insgesamt |
| Direkte Paarduelle 9930100–9930119 | 20 × 2 Seiten | 40 je Paar, 80 insgesamt |

Damit stimmen 160 Vorlauf- und 640 Lernspiele = **800 Ausführungen**, anschließend **400 Leistungsspiele**. Je Arm 160 × 150 = **24.000 Updates**, insgesamt **96.000**. Der erwartete Env-Zähler am Ende jedes vollständigen Arms ist 60.000 + 200 × 303 = **120.600**. Die drei Matchstart-No-ops erklären die 303 Env-Schritte und sind mit der geplanten 150er-Lernfrequenz vereinbar; die tatsächlichen Zähler müssen weiterhin im Receipt geprüft werden.

Zusätzlich genau 2 Modi × 2 Seiten × eine bekannte Karte 4242 gegen default = **4 technische Ausführungen**, also maximal **1.204 vollständige Spiele**. Keine der vier technischen Ausführungen gehört in Vorlauf-, Trainings- oder Leistungsnenner. Frische ist durch diese bloße Intervallprüfung noch nicht bewiesen; der vorgesehene arbeitskopienübergreifende Audit mit ausdrücklich genannten externen/seedlosen Datenlücken bleibt nötig.

## Technischer Zusatz und Aufnahmebedingungen

Die vier bekannten Integrationsspiele schließen eine reale Schnittstellenlücke gegenüber rein synthetischen Tests: echte `act → env.step → update`-Folge, 303 Schritte, terminaler Abschluss und leere Captures. `learn_enabled=False`, frischer Agent pro Ausführung, unveränderte Q-/Target-/Adam-Zustände und gleiche exogene Zufallsfolgen zwischen beiden Modi je Seite verhindern eine zusätzliche Trainingsintervention. Gewinner werden nur protokolliert und nicht ausgewählt. Die technischen Replay-/RNG-Endstände dürfen gemäß dem weiterhin festen frischen Studienstart nicht als Startpuffer übernommen werden.

Die technischen Spiele sind vor neuen Leistungsdaten festgelegt und nicht von deren Ergebnis abhängig. Sie verändern weder Reward noch Regeln, Replayverzögerung oder Bootstrapformel. Der neue lokale `technical`-Einstieg verwendet ausdrücklich denselben Spiel-/Provenienzpfad wie spätere Worker; kein zusätzlicher allgemeiner Runner ist vorgesehen. Bei Fehler Aufnahme stoppen, Ursache und gesonderten Technikentscheid dokumentieren; keine stille Wiederholung. Diese Aufnahmebedingung rechtfertigt die vier getrennt gezählten Spiele, keine späteren Zusatzproben.

Die übrigen Aufnahmebedingungen bleiben erhalten: integrierter Methoden-/Codereview, tatsächliche technische Abnahme, akzeptierte Frische, sämtliche Input-/Quellen-/Gewichts-/Befehlsbindungen, neue gemeinsame Quellenfixierung, maximal zwei Worker und keine parallelen Tests. Die beiden Startpaare laufen nacheinander; innerhalb jedes Paars zuerst beide vollständigen Vorläufe und Machbarkeitsgate, dann Gradienten. Ein später gescheitertes Paar macht den Pilot unvollständig und erlaubt keinen Ersatzstart. Vorläufige und negative Daten bleiben erhalten.

## Keine Datenwahl oder methodische Ausweitung

- Starts 45/46 und alle Karten stehen vor neuen Daten fest; keine Umnummerierung bei Konflikt, Seednachziehung, Zwischenvalidierung, Checkpoint- oder Netzselektion.
- Unveränderte gemeinsame verzögerte Replayfreigabe; einziger vorgesehener Lernunterschied bleibt DDQN-Argmax gegenüber bestätigter historischer Folgeaktion. SARSA-artiges Replay-TD wird korrekt von echtem on-policy SARSA abgegrenzt.
- Das Vorlaufgate verlangt eine tatsächlich vorhandene Index- und Targetwertintervention ohne Gradienten und ohne RNG-Ziehung. Es ist ein Machbarkeitsnachweis, keine Schwellenwahl nach Spielstärke.
- Final ausschließlich vier Einzelnetze und feste 400 Spiele. Beide Direktduellseiten erhalten dieselbe gebundene Inferenzkonfiguration aus V14 mit unveränderten jeweiligen Endtensoren; keine einseitigen Overrides.
- Das Screeningsignal bleibt deskriptiv: pro Start positive Paneldifferenz, Mittel mindestens +5 Prozentpunkte; beide direkten Scores mindestens 0,5 und gemeinsam strikt größer. Bei vollständigen Nennern entspricht das je Start positivem Halbsieggewinn im 80er-Panel, zusammen mindestens 16 Halbsiegeinheiten Gewinn; direkt je Paar mindestens 40 und zusammen mehr als 80 Halbsiegeinheiten aus 80 Spielen. Das sind nur äquivalente Ganzzahlformulierungen der vorhandenen Regeln, keine neuen Gates.
- Gemeinsame Karten in beiden Starts sind keine unabhängigen Trainingsreplikate. Der Text vermeidet diese Behauptung und verlangt Kartenpaare, Startwerte einzeln und deskriptives Mittel. Bestehen liefert keinen V14-Vergleich, keine Übernahme oder automatische Folgestudie; Unklarheit beendet den Pilot ohne Nachschlag.

## P3 – verbliebene historische Statussätze präzisieren

Nur Befunde; die geprüften Dateien wurden nicht geändert:

1. **Spec Zeile 68:** „keine dieser neuen Mechaniken implementiert oder getestet“ widerspricht Spec Zeile 3 und Plan Zeile 88. Als historischen Stand des ursprünglichen Architekturentwurfs markieren; aktuelle Task-1/2-Implementierung und Root-Testnachweis davon unterscheiden.
2. **Plan Zeile 9:** „Gegenwärtig ausschließlich Entwurfsdateien unter `/tmp`“ passt nicht mehr zum in Zeile 88 genannten installierten Agent-/Replaymodul. Auf den tatsächlichen Stand aufteilen: Task 1/2 installiert und synthetisch geprüft, Task 3/4 sowie reale Läufe offen.
3. **Plan Zeile 84:** „Keine Tests oder Ausführung hier behauptet“ ist als pauschaler aktueller Status widersprüchlich zum unmittelbar folgenden 53-PASS-Nachweis. Auf die historische Entwurfsprüfung begrenzen oder auf den nachfolgenden tatsächlichen Status verweisen.
4. **Spec Zeile 13:** „erst nach Ende des heutigen Modelllaufs“ ist eine alte relative Zeitangabe. Der frühere Artillerielauf ist laut Kopf abgeschlossen; für die neue Phase präziser die bereits bestehende Regel „keine synthetischen Tests parallel zu Modellworkern“ und die technische Vorabprüfung nennen. Keine neue Warte- oder Erlaubnisbedingung daraus ableiten.

Die noch offenen Checkboxes sind durch Plan Zeile 3 als Anforderungen mit separatem tatsächlichem Status erklärbar. Historische UNRUN-Berichte müssen nicht rückwirkend umgeschrieben werden. Der relative Spec-Link in der externen Planfassung ist als vorgesehener Repositoryzielpfad zu lesen, nicht als bereits existierende Datei unter `/tmp`.

**Tatsächliche Arbeit dieses Reviews:** Dokumente/Diffs/Zeilen/Hashes gelesen und dieser Bericht unter `/tmp` geschrieben. Keine Python-, Test-, Modell- oder Spielausführung, keine Repositoryänderung, kein Kartenfrischeaudit und keine neue Ergebnisbehauptung.
