# Checkliste Review 16.10.2026 (benotet, 1/3 der Note)

Stand: 14.10.2026. Grundlage: Kursfolien 9 und 11 sowie die konkrete Moodle-Aufgabe „Submission 1“ aus dem vom Team bereitgestellten Screenshot.

## Termin, Vortragszeit und Slot

- **Upload der Präsentation: Freitag, 16.10.2026, 08:00 Uhr** laut Moodle-Aufgabe.
- **Geplante Vortragsdauer: ungefähr zehn Minuten** laut Moodle-Aufgabe. Das ist keine sekundengenaue Abbruchgrenze; darauf soll die Vorbereitung zielen.
- **Slot: 20 Minuten** laut Moayeds Angabe vom 14.10. Vortragsdauer und Slotlänge sind getrennte Angaben. Dass die übrige Zeit für Fragen, Überziehen oder Puffer vorgesehen ist, ist eine plausible, noch nicht bestätigte Aufteilung.
- Für spätere Präsentationen könnten längere Vorträge und Battles vorgesehen sein. Die genaue Aufteilung je Termin noch anhand der jeweiligen Aufgabe bestätigen; nicht aus der Slotlänge ableiten.

## Stand der Präsentationsdatei

Aktuell: [Gamma-Fassung](https://gamma.app/docs/ltmbj9ep61c77yl), [PowerPoint mit ergänzten Notizen](Sherlock_Review_Gamma_16-10-2026.pptx) und [PDF](Sherlock_Review_Gamma_16-10-2026.pdf). **Zehn Vortragsfolien**, Ziel **10:40 Minuten**, höchstens **12 Minuten Vortrag**. [Aufteilung und Lernhilfe](VORTRAGSPLAN_1610.md): Moayed 5:15, Mahmoud 5:25. Auf Folie 10 spricht zuerst Mahmoud über Erkenntnisse/nächste Schritte und danach Moayed das Fazit. Diese Zusammenfassung hält den kostenlosen Gamma-Tarif mit maximal zehn Karten pro Erstellung ein.

Die ursprüngliche [PowerPoint](Sherlock_Review_16-10-2026.pptx) und [PDF](Sherlock_Review_16-10-2026.pdf) mit elf Haupt- und zwei Reservefolien bleiben als Rückfalloption erhalten. Die Reserveinformationen stehen auch im Leitfaden. Die Zeiten sind noch nicht durch eine gemeinsame Probe bestätigt. Die neue PDF endet nach Seite 10.

## Geforderte Inhalte und verfügbare Belege

| Vorgabe | Umsetzung im neuen Foliensatz | Vor der Präsentation |
|---|---|---|
| Agent und Algorithmus als Pseudocode | Folie 3: Ablauf beim Spielen; Folie 6: vereinfachter Trainingsschritt | Spielen und Lernen sicher unterscheiden |
| Netzarchitektur | Folie 5: 79 → 256 → 256, Dueling-Köpfe, sechs Netze | Q-Mittelwert und Aktionsmaske erklären |
| RL-Algorithmus | Folie 6: Double DQN, Replay Buffer, Target-Netz; Notizen | Online-Netz wählt, Target-Netz bewertet |
| Trainingskonfiguration | Folie 7 sowie Notizen/Reserveinformation im Leitfaden; Werte mit gespeicherter cfg abgeglichen | Lernbeginn nach 5000 Einheitenübergängen, nicht Spielen |
| Feature Engineering | Folie 4: 79 Merkmale, Belief, Inferenzbeispiel in Notizen | Beobachtetes Wissen und vollständige Zuschaueransicht unterscheiden |
| Trainingsablauf, Spiele, Gegner | Folie 7: 6 × 3000 = 18.000 Laufspiele; default und Solution_92 | Ausgewählte Checkpoints können früher liegen; keine Testspiele mitzählen |
| Ausgewählte Spiele | Folie 9: zwei Bilder desselben Spiels (Seed 900011, Frames 23/90) | Vergleich ohne Live-Demo erklären |
| Beobachtungen, Hypothesen, Erkenntnisse | Folien 8 und 10: Ergebnisse, Grenzen, erfolglose Versuche, Hypothese | Mehrfach verwendeten Benchmark offen benennen |
| Fragen und nächste Schritte | Folie 10; Reserveinformationen im Leitfaden | m1_early als späteren Kandidaten darstellen |

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
- [x] Neuen Folienexport erstellen; Pflichtinhalte auf Folien 2–10 und in den Sprechernotizen abdecken.
- [ ] Inhalt und Aufteilung gemeinsam bestätigen; Export auf dem Vortragsrechner prüfen.
- [x] Teamnamen, Gruppe 15, Agent Sherlock und aktuelle Ensemble-Architektur korrekt angeben.
- [x] Klare Kernaussage und nachvollziehbaren Aufbau verwenden: Aufgabe → Lösung → Training → Ergebnisse → Erkenntnisse → Ausblick.
- [x] Bilder/Diagramme/Spielbeispiele lesbar gestalten; historische Ergebnisse und aktuelle Abgabe sauber beschriften.
- [x] Replay-Ausschnitt festgelegt: Seed 900011, erstes Match, Frames 23 und 90. Echte Viewer-Bilder auf Folie 9, ohne Internet vorführbar.
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
