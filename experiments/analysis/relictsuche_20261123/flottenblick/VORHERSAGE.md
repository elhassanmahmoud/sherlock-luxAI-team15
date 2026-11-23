# Die spätere Mannschaftssicht lässt sich vorhersagen

Auf **160 neuen Karten** sagte das räumliche Netz die Sicht der übrigen Flotte nahe geeigneter Suchwege besser voraus als alle vier einfachen Entfernungsprojektionen. Auf 131 Karten gab es insgesamt 681 geeignete Entscheidungen. Der mittlere quadratische Wahrscheinlichkeitsfehler (Brier-Fehler) sank von **0,12122 auf 0,09948** gegenüber der im Training gewählten stärksten Referenz. Der Vorteil von 0,02174 lag im gepaarten 95-%-Kartenintervall von 0,01913 bis 0,02431.

| Prognose der übrigen Flotte | Alle erreichbaren Routenfelder | Außerhalb heutiger und nächster Sicht | Bisher ungesehene Routenfelder |
|---|---:|---:|---:|
| Heutige Stellung | 0,14057 | 0,16109 | 0,14397 |
| Heutige und nächste Stellung | 0,12707 | 0,15506 | 0,12872 |
| Geradeausprojektion über acht Schritte | 0,15320 | 0,16808 | 0,14608 |
| Kombinierte kalibrierte Entfernungen | 0,12122 | 0,14668 | 0,12311 |
| Gelerntes räumliches Netz | **0,09948** | **0,12810** | **0,10444** |

Auf der nachträglich identifizierbaren Teilmenge vorher neuer Felder, die in diesen acht Schritten tatsächlich irgendein eigenes Schiff sah, hatte das Netz einen Fehler von 0,34990 gegenüber 0,34516 für die kombinierte Referenz. Der Unterschied von −0,00474 beim Fehlervorteil hatte ein Kartenintervall von −0,01988 bis +0,00949. Über die untersuchten Präfixe waren 1.227 tatsächlich neu beobachtete physische Felder im Routenbereich ausschließlich der gewählten UID zuzurechnen. Verschiedene Entscheidungen auf derselben Karte können dabei dasselbe Feld enthalten.

Wenn die vorgeschlagenen Routen rechnerisch auf den schon bekannten Folgebewegungen der Originalflotte lagen, ergab sich mit dem Netz eine potentielle Sicht auf 15,005 vorher unbekannte und andernfalls ungesehene Relikt-Spiegelpaare pro Entscheidung. Die kombinierte Referenz erreichte 14,896. Der Unterschied von +0,108 hatte ein Kartenintervall von −0,048 bis +0,271. Auf rund neun von zehn Entscheidungen bevorzugten beide Modelle dieselbe erste Bewegungsrichtung. Zur Gate-Prüfung der tatsächlichen zusätzlichen Sicht speist ein separates Experiment die Befehle beider Planer in die Spielumgebung ein.

Das vollständige Trainingsmaterial umfasste 480 Karten, davon 362 mit einer geeigneten Flottenlage. Auf 1.788 Lagen erhielt der finale Fit 560 Gewichtsaktualisierungen in zehn Epochen. Die Auswahl der Trainingsdauer und der stärksten Referenz nutzte zuvor nur 96 interne Entwicklungskarten. Original-Solution und Original-V16 waren im Kartenplan je zur Hälfte vertreten, ebenso beide Startseiten. 986 direkte Neuberechnungen der originalen Sichtleistung ohne Sucher sowie der Abgleich mit den ursprünglichen öffentlichen Sensorbildern prüften die Labelbildung. Eine zweite Implementierung prüfte die 640 Rohdateien und rechnete die 681 getrennten Prognosedifferenzen und ihr Intervall nach.

[Messmethode und Sichtarithmetik](METHODE.md) · [Modelltraining](fit.json) · [Alle Fehlermaße und Kartenintervalle](pruefung.json) · [Einzelvorhersagen und Wegvergleiche](vorhersagen.jsonl.gz) · [Gegenrechnung](nachrechnung.json)
