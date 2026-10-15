# Checkliste Review 16.10.2026 (benotet, 1/3 der Note)

Stand: 15.10.2026. Grundlage: Kursfolien 9 und 11 sowie die konkrete Moodle-Aufgabe „Submission 1“ aus dem vom Team bereitgestellten Screenshot.

## Termin, Vortragszeit und Slot

- **Upload der Präsentation: Freitag, 16.10.2026, 08:00 Uhr** laut Moodle-Aufgabe.
- **Geplante Vortragsdauer: ungefähr zehn Minuten** laut Moodle-Aufgabe. Das ist keine sekundengenaue Abbruchgrenze; darauf soll die Vorbereitung zielen.
- **Slot: 20 Minuten** laut Moayeds Angabe vom 14.10. Vortragsdauer und Slotlänge sind getrennte Angaben. Dass die übrige Zeit für Fragen, Überziehen oder Puffer vorgesehen ist, ist eine plausible, noch nicht bestätigte Aufteilung.
- Für spätere Präsentationen könnten längere Vorträge und Battles vorgesehen sein. Die genaue Aufteilung je Termin noch anhand der jeweiligen Aufgabe bestätigen; nicht aus der Slotlänge ableiten.

## Stand der Präsentationsdatei

Am 14.10. auf Moayeds Auftrag erstellt, am 15.10. um eine Agenda ergänzt: [PowerPoint mit Sprechernotizen](Sherlock_Review_16-10-2026.pptx) und [PDF](Sherlock_Review_16-10-2026.pdf). **12 Vortragsfolien + 2 Reservefolien**, Ziel **11:00 Minuten**, höchstens **12 Minuten Vortrag**. [Aufteilung, Zeitplan, Formulierungshilfen und Fragen](VORTRAGSPLAN_1610.md): Moayed 5:35 Minuten (Aufgabe, Überblick, Ergebnisse, Spielbeispiel, Abschluss), Mahmoud 5:25 Minuten (technischer Teil und nächste Schritte). Frühere externe Entwürfe sind damit nicht die aktuelle Arbeitsgrundlage.

Die Zeiten sind noch nicht durch eine gemeinsame Probe bestätigt. Die beiden Anhangsfolien sind in PowerPoint ausgeblendet; in der PDF nach Seite 12 stoppen und Seiten 13–14 nur bei Rückfragen zeigen.

## Geforderte Inhalte und verfügbare Belege

| Vorgabe | Umsetzung im neuen Foliensatz | Vor der Präsentation |
|---|---|---|
| Agent und Algorithmus als Pseudocode | Folie 4: eingerückter Pseudocode beim Spielen; Folie 7: Pseudocode des Double-DQN-Lernupdates | Spielen und Lernen sicher unterscheiden |
| Netzarchitektur | Folie 6: 79 → 256 → 256, Dueling-Köpfe, sechs Netze | Q-Mittelwert und Aktionsmaske erklären |
| RL-Algorithmus | Folie 7: Double DQN, Replay Buffer, Target-Netz; Notizen | Online-Netz wählt, Target-Netz bewertet |
| Trainingskonfiguration | Folie 8: Lernrate, γ, Batch/Buffer, Exploration und Target-Kopie sichtbar; weitere Werte auf Reservefolie 13 | Umgebungsschritte, Einheitenübergänge und Lernupdates unterscheiden |
| Feature Engineering | Folie 5: 79 Merkmale, Belief, Inferenzbeispiel in Notizen | Beobachtetes Wissen und vollständige Zuschaueransicht unterscheiden |
| Trainingsablauf, Spiele, Gegner | Folie 8: 6 × 3000 = 18.000 Laufspiele; default und Solution_92 | Ausgewählte Checkpoints können früher liegen; keine Testspiele mitzählen |
| Ausgewählte Spiele | Folie 10: zwei Bilder desselben Spiels (Seed 900011, Frames 23/90) | Vergleich ohne Live-Demo erklären |
| Beobachtungen, Hypothesen, Erkenntnisse | Folien 9 und 11: Ergebnisse, Grenzen, erfolglose Versuche, Hypothese | Mehrfach verwendeten Benchmark offen benennen |
| Fragen und nächste Schritte | Folien 11–12; Reserve 13–14 | m1_early als späteren Kandidaten darstellen |

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

## Verbindliche Arbeitsplanung des Teams

Der aktuelle [Vortragsplan](VORTRAGSPLAN_1610.md#aufteilung-und-zeitplan) enthält Folien, Sprecher, Zeitfenster, Übergaben und eine auf zehn Minuten gekürzte Variante. Er ist eine Teamplanung, keine zusätzliche Kursvorgabe. Der technische Vortragsteil liegt bei Mahmoud, der anschauliche Teil bei Moayed. Beide bereiten die Grundbegriffe und mögliche Rückfragen vor.

## Bewertungsraster und Team-To-dos

- [ ] Slot/Buchung auf Moodle bestätigen; Buchungsstand ist hier nicht bekannt.
- [x] Neuen Folienexport erstellen; Pflichtinhalte auf Folien 3–11 und in den Sprechernotizen abdecken.
- [ ] Inhalt und Aufteilung gemeinsam bestätigen; Export auf dem Vortragsrechner prüfen.
- [x] Teamnamen, Gruppe 15, Agent Sherlock und aktuelle Ensemble-Architektur korrekt angeben.
- [x] Klare Kernaussage und nachvollziehbaren Aufbau verwenden: Aufgabe → Lösung → Training → Ergebnisse → Erkenntnisse → Ausblick.
- [x] Bilder/Diagramme/Spielbeispiele lesbar gestalten; historische Ergebnisse und aktuelle Abgabe sauber beschriften.
- [x] Replay-Ausschnitt festgelegt: Seed 900011, erstes Match, Frames 23 und 90. Echte Viewer-Bilder auf Folie 10, ohne Internet vorführbar.
- [ ] Beide können den Bildvergleich in eigenen Worten erklären.
- [x] Sprechanteile und Übergaben im Vortragsplan aufteilen.
- [ ] Mindestens zweimal gemeinsam mit Uhr auf 10–12 Minuten proben; frei und in eigenen Worten sprechen.
- [ ] Beide können Belief, Features, Double DQN, Reward Shaping, Ensemble und die Grenzen der Ablation erklären. Beide können sagen, was gelernt und was heuristisch vorgegeben ist.
- [ ] Präsentation bis **16.10., 08:00 Uhr** hochladen und den hochgeladenen Export prüfen.

## Technische Prüfungen und spätere Agentenabgabe

Die Moodle-Aufgabe für den 16.10. verlangt die Präsentation. Das finale Agentenpaket nach Kursfolie 51 ist für den 27.11. vorgesehen. Die Paketstruktur ist bereits vorhanden: Teamordner, leere `__init__.py`, `Agent_x`, Pflichtmethoden, `agents.yaml`, `paths.csv` und trainierte Gewichte.

**Bereits durchgeführt am 14.10., in separater Kopie desselben Dateistands:**

- 62 Tests bestanden; 120 Spiele mit dem ausgelieferten Sechser-Ensemble reproduziert.
- Paket gebaut, separat entpackt, beide Seiten geladen und zwei vollständige Spiele gegen default über den Kurs-Runner ausgeführt.
- Im lokalen Test durchschnittlich ungefähr 0,99 ms pro `act()`, maximal ungefähr 34,94 ms; keine Garantie für andere Rechner.

Diese Prüfungen wurden für die Dokumentationsänderung nicht wiederholt. Ältere Notizen mit 52/55 Tests und drei Netzen beziehen sich auf frühere Stände. Auch bestandene Tests beseitigen die im [Arbeitsstand](../ARBEITSSTAND.md) dokumentierten offenen Mess- und Trainingsfehler nicht.
