# Technischer Abbruch und begründete Reparatur

10.11.2026. Der ursprüngliche Snapshot-Pilot wird **nicht als auswertbare Leistungs-/Lernzielstudie verwendet**. Keine Trainingsupdates oder Gewichtsänderungen.

## Tatsächlich ausgeführt

Die vier technischen Vollausführungen bestanden Root- und unabhängige Datenprüfung. In der zweiten Phase endete der Prozess mit Fehler, nach weiteren15 vollständigen Ausführungen und einer unvollständigen Sammelpartie. Insgesamt **19 vollständige + 1 unvollständige Ausführung**, 29 angelegte Alternativenpaare, 3.538 Hauptfortsetzungs- und732 Wiederholungsschritte; zusammen10.203 tatsächliche Engine-Schritte. Kein Ersatzlauf oder stiller Neustart.

Abbruch: `11011007/player_0`, Sammler nach Schritt175, zweite Gelegenheit bei Schritt141 (Matchschritt40). Der unveränderte Baselinebranch und der tatsächliche Verlauf stimmten nicht mehr überein. Der Sammler archivierte den gerade berechneten abweichenden Frame noch nicht; diese Diagnoselücke wird im reparierten Sammler geschlossen.

## Was die vorhandenen Daten beweisen

- Alle175 gespeicherten Sammlerframes (Schritte0–174) sind exakt gleich dem bereits vollständigen Referenzspiel.
- Baselinebranch und Referenz stimmen von141 bis174 exakt überein. Bei175 sind vorheriger Engine-/Beobachtungszustand und alle Sherlock-Aktionen gleich; allein Solutions Einheit0 unterscheidet sich: im Branch STAY, in der Referenz Bewegung1. Danach unterscheiden sich Zustände und spätere Punkte.
- Das lokalisiert die erste archivierte Abweichung auf gegnerinternen Entscheidungszustand, nicht auf Sherlocks Netzvorschlag oder einen bereits zuvor anderen sichtbaren Spielzustand. Die tatsächlich fehlende Sammleraktion175 wird nicht erfunden.

## Unabhängig demonstrierter Kopierfehler

Python-`deepcopy` rekonstruiert Sets. Mitgliedschaft und Objektaliasse können identisch bleiben, während sich die Iterationsreihenfolge ändert. Solution iteriert persistente Knoten-/Belohnungsmengen und wählt in `find_closest_target` bei gleichem Abstand das zuerst besuchte Ziel.

Zwei rein synthetische Gegenbeispiele mit tatsächlichem Solution-Code, null Spiele:

- Root: unveränderte Mitgliedschaft, Start(0,15), vor Kopieren Ziel(0,18), danach(1,13); jeweils Distanz3.
- Unabhängig: symmetrisch eingefügte Knoten, gemeinsame zweimalige Kopie wie capture/fork, Aliasidentitäten erhalten. Tatsächliche harvest-artige Zielmengen wählen von(5,8) ursprünglich(6,4), im Branch(3,11); jeweils Distanz5. Wiederholte Branchkopien stimmen untereinander überein, also können Wiederholungsprüfungen den Fehler übersehen.

Diese Belege zeigen, dass das Kopieren die Gegnerpolicy verändern kann. Ohne gespeicherte interne Mengen am echten Schritt141 ist dies **nicht die abschließend bewiesene Einzelursache von Schritt175**. Die Methode ist dennoch nicht zuverlässig genug für die geplanten Labels. Alte HOLD-Snapshot-Ergebnisse sind vor einer erneuten Verwendung ebenfalls auf diese Grenze zu prüfen; frühere Studien werden nicht neu gestartet.

## Reparaturentscheidung unter dem autonomen Auftrag

Keine Änderung oder Sortierung in Solution, keine Manipulation des Gegners. Stattdessen jede Alternative mit frischen unveränderten Agenten vom ursprünglichen Seed neu abspielen; alle Frames vor dem Eingriff müssen exakt dem vollständigen Referenzverlauf entsprechen. Erst dann genau denselben öffentlichen Vorschlag ändern. Das baut den Gegnerzustand durch dieselbe tatsächliche Historie auf und vermeidet Objektkopien vollständig.

Der ursprüngliche Versuch bleibt unverändert archiviert. Ein einziger separat begrenzter Reparaturdurchlauf wird vor Start festgelegt: dieselben8 Karten, dieselbe Auswahlregel, dieselben Gates; zuerst die bekannte Fehlerkarte und eine Kontrollkarte technisch aufnehmen. Neue Grenzen und Zählweise stehen als datierter Zusatz im Design/Plan. Keine Schwellenänderung aufgrund vorläufiger Erfolge, kein Modelltraining mit den alten Labels.

Alle vorher gebundenen Quellen/Eingaben/Schutzdateien nach Prozessende erneut gehasht, eigener Worker beendet, alte Phase erst danach geschlossen. [Abschlussnachweis](failed_snapshot_closure.json), [unabhängiger Mechanismusbeleg](set_order_independent.json).
