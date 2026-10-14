# Checkliste Review 16.10.2026 (benotet, 1/3 der Note)

Stand: 14.10.2026. Grundlage: Kursfolien 9 und 11 sowie die konkrete Moodle-Aufgabe „Submission 1“ aus dem vom Team bereitgestellten Screenshot.

## Termin, Vortragszeit und Slot

- **Upload der Präsentation: Freitag, 16.10.2026, 08:00 Uhr** laut Moodle-Aufgabe.
- **Geplante Vortragsdauer: ungefähr zehn Minuten** laut Moodle-Aufgabe. Das ist keine sekundengenaue Abbruchgrenze; darauf soll die Vorbereitung zielen.
- **Slot: 20 Minuten** laut Moayeds Angabe vom 14.10. Vortragsdauer und Slotlänge sind getrennte Angaben. Dass die übrige Zeit für Fragen, Überziehen oder Puffer vorgesehen ist, ist eine plausible, noch nicht bestätigte Aufteilung.
- Für spätere Präsentationen könnten längere Vorträge und Battles vorgesehen sein. Die genaue Aufteilung je Termin noch anhand der jeweiligen Aufgabe bestätigen; nicht aus der Slotlänge ableiten.

## Stand der Präsentationsdatei

Ältere Notizen nennen einen externen Entwurf „Sherlock – Review 16.10.“ mit zunächst 17, später 19 Folien. **Im Repository liegt kein aktueller PPTX-/PDF-Folienexport.** Deshalb bestätigt diese Checkliste die verfügbaren Projektinhalte, nicht die Vollständigkeit oder Qualität dieses externen Entwurfs. Mahmoud erstellt laut Team die Präsentation; Export, Zeitumfang und tatsächliche Inhalte sind noch zu prüfen.

## Geforderte Inhalte und verfügbare Belege

| Vorgabe | Grundlage im Projekt | Noch an den Folien / im Vortrag prüfen |
|---|---|---|
| Agent und Algorithmus als Pseudocode | [README](../../README.md), `agents/sherlock/main.py` | Aktuellen Agenten `old3_sym3` erklären; Spielen und Training unterscheiden |
| Netzarchitektur | MLP 79 → 256 → 256, Dueling-Köpfe; sechs Netze im Ensemble | Q-Werte mitteln, dann beste erlaubte Aktion; nicht nur ein Netz als aktuelle Abgabe darstellen |
| RL-Algorithmus | Double DQN, Replay Buffer, Target-Netz | Online-Netz wählt, Target-Netz bewertet; verständlicher Pseudocode |
| Trainingskonfiguration | `AgentConfig`, gespeicherte Checkpoint-Konfigurationen, Lauf-Manifeste | Tatsächliche Einstellungen des dargestellten Laufs statt nur Standardwerte; Lernbeginn nach 5000 Einheiten-Übergängen |
| Feature Engineering | Belief, 79 Merkmale, Zielzuweisung, Masken | Beispiel für Punktefeld-Inferenz; kanonische Koordinaten und Symmetrie-Inferenz unterscheiden |
| Trainingsablauf, Spiele, Gegner | 3000 Spiele je trainiertem Lauf; ursprünglicher Batch 63.000, alle 34 Manifeste zusammen 99.000 Trainingsspiele | Trainingsumfang klar abgrenzen; Validierung/Tests/Buffer-Vorfüllung nicht als Trainingsspiele mitzählen; default und Solution_92 nennen |
| Ausgewählte Spiele | Fünf `sherlock_*.json`-Replays des aktuellen Ensembles in `docs/presentation/replays/` | Im Viewer ansehen, kurzen aussagekräftigen Ausschnitt wählen; Screenshot/Video als Ausweichmöglichkeit vorbereiten |
| Beobachtungen, Hypothesen, Erkenntnisse | Historische Ablation und spätere Ensemble-/Erkundungsversuche im [Experimentprotokoll](../EXPERIMENT_PROTOKOLL.md) | Messung von Hypothese unterscheiden; auch erfolglose Versuche einordnen |
| Fragen und nächste Schritte | `m1_early` als späterer Kandidat; offene Mess-/Trainingskorrekturen im [Arbeitsstand](../ARBEITSSTAND.md) | Änderungen nicht als bereits umgesetzt darstellen |

## Zahlen und Aussagen für die Ergebnisfolie

| Aktueller Agent `old3_sym3` | Siege | Siegquote |
|---|---|---|
| gegen default | 60/60 | 100,0 % |
| gegen Solution_92 | 28/60 | 46,7 % |

Quelle: [Einzelspiele](../../experiments/compare/TEST_old3_sym3.csv), reproduziert in der separaten Prüfung vom 14.10. Je Gegner 30 Karten × beide Seiten, ohne Lernen. Es sind keine 60 unabhängigen Karten. 100 % gelten nur für diese Stichprobe; die Testkarten wurden über mehrere Entwicklungsstände wiederverwendet.

- Historische `full`-Werte (87,8 % / 18,9 %, Mittel über drei Starts) und Diagramme aus `docs/report/` ausdrücklich als ursprüngliche Einzelnetz-/Ablationsstudie kennzeichnen.
- Die [120 neu gemessenen Benchmarkspiele](../../experiments/compare/TEST_old3_sym3_points_v2.csv) bestätigen die obigen Siege mit unveränderten Gewichten.
- Gesamtpunktzahlen nur aus neuen Messungen mit `point_counting_version=2` verwenden. Alte CSVs ohne diese Spalte lassen den letzten Zuwachs vor jedem Match-Reset aus und bleiben historische Rohdaten. Die Siegquoten sind nicht betroffen.
- `compare_report.py` ist jetzt nach Karte gruppiert. Für Folien nur die [neu berechneten Intervalle](../STATISTIK_20261014.md) oder neu erzeugte Berichte verwenden; historische Intervalle anderer Vergleiche bleiben ungeprüft. `m1_early` Runde 1 gegen Solution_92 schließt jetzt null ein. Kein signifikanter Unterschied bedeutet nicht „wirkungslos“ oder „mindestens gleich gut“.
- `no_belief` entfernt Gedächtnis aus den Netzmerkmalen, nicht aus allen Heuristiken und Belohnungen. Sap-Zielwahl ist heuristisch; Sap-Treffer sind geschätzt. Keine Garantie behaupten, dass die gesamte Shaping-Funktion die optimale Strategie unverändert lässt.

## Vorschlag für ungefähr zehn Minuten Vortrag

Dies ist eine Arbeitseinteilung, keine zusätzliche Kursvorgabe. Detailfolien können in den Anhang.

| Teil | Richtzeit |
|---|---|
| Aufgabe und Kernaussage | 0:45 |
| Agent, Merkmale und Gedächtnis | 2:00 |
| Netz, Ensemble und Double DQN | 2:00 |
| Trainingsablauf und Versuchsaufbau | 1:15 |
| Ergebnisse und wichtigste Erkenntnis | 1:30 |
| Ausgewählter Spielausschnitt | 1:30 |
| Grenzen und nächste Schritte | 1:00 |
| **Gesamt** | **10:00** |

## Bewertungsraster und Team-To-dos

- [ ] Slot/Buchung auf Moodle bestätigen; Buchungsstand ist hier nicht bekannt.
- [ ] Aktuellen Folienexport erstellen und alle Pflichtinhalte anhand der Tabelle prüfen.
- [ ] Teamnamen, Gruppe 15, Agent Sherlock und aktuelle Ensemble-Architektur korrekt angeben.
- [ ] Klare Kernaussage und nachvollziehbaren Aufbau verwenden: Aufgabe → Lösung → Training → Ergebnisse → Erkenntnisse → Ausblick.
- [ ] Bilder/Diagramme/Spielbeispiele lesbar gestalten; historische Ergebnisse und aktuelle Abgabe sauber beschriften.
- [ ] Replays unter <https://s3vis.lux-ai.org/> ansehen und den Ausschnitt vorab festlegen.
- [ ] Sprechanteile aufteilen und mindestens zweimal mit Uhr auf ungefähr zehn Minuten proben; frei und in eigenen Worten sprechen.
- [ ] Beide können Belief, Features, Double DQN, Reward Shaping, Ensemble und die Grenzen der Ablation erklären. Beide können sagen, was gelernt und was heuristisch vorgegeben ist.
- [ ] Präsentation bis **16.10., 08:00 Uhr** hochladen und den hochgeladenen Export prüfen.

## Technische Prüfungen und spätere Agentenabgabe

Die Moodle-Aufgabe für den 16.10. verlangt die Präsentation. Das finale Agentenpaket nach Kursfolie 51 ist für den 27.11. vorgesehen. Die Paketstruktur ist bereits vorhanden: Teamordner, leere `__init__.py`, `Agent_x`, Pflichtmethoden, `agents.yaml`, `paths.csv` und trainierte Gewichte.

**Bereits durchgeführt am 14.10., in separater Kopie desselben Dateistands:**

- 62 Tests bestanden; 120 Spiele mit dem ausgelieferten Sechser-Ensemble reproduziert.
- Paket gebaut, separat entpackt, beide Seiten geladen und zwei vollständige Spiele gegen default über den Kurs-Runner ausgeführt.
- Im lokalen Test durchschnittlich ungefähr 0,99 ms pro `act()`, maximal ungefähr 34,94 ms; keine Garantie für andere Rechner.

Diese Prüfungen wurden für die Dokumentationsänderung nicht wiederholt. Ältere Notizen mit 52/55 Tests und drei Netzen beziehen sich auf frühere Stände. Auch bestandene Tests beseitigen die im [Arbeitsstand](../ARBEITSSTAND.md) dokumentierten offenen Mess- und Trainingsfehler nicht.
