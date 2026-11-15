# Was verrät der letzte eigene Befehl über die Lehreraktion?

Auf den 24 zurückgehaltenen Karten des Bewegungsberaters half die zuletzt tatsächlich ausgeführte eigene Aktion selbst dann, wenn bereits der aktuelle V14-Befehl, das Match, die Rolle, die grobe Zielrichtung und die Energieklasse bekannt waren. Eine einfache Häufigkeitstabelle traf **80.477 von 147.228** Lehreraktionen. Nach Berücksichtigung des letzten Befehls traf sie **82.345**, also **54,66 % gegenüber 55,93 %**. 5.232 frühere Fehler wurden korrigiert, zugleich entstanden 3.364 neue. Der Zugewinn von **1,27 Prozentpunkten** hat ein gepaartes 95-%-Intervall von **0,82 bis 1,71 Prozentpunkten**. Das richtige Ergebnis wurde auf 21 von 24 Karten häufiger vorhergesagt. Der mittlere logarithmische Verlust sank von 1,2670 auf 1,2256 Nats; das Vorzeichen war auf 23 Karten günstig.

| Diagnosegruppe | Karten | Entscheidungen mit sicherer Vorgeschichte | Treffer ohne / mit letztem Befehl | Veränderung in Prozentpunkten |
|---|---:|---:|---:|---:|
| Neue Schülerverläufe gegen Kaggle 3 | 8 | 38.838 | 19.918 / 20.218 | +0,77 |
| Neue Schülerverläufe gegen Solution_92 | 8 | 54.498 | 30.731 / 31.429 | +1,28 |
| Neue Schülerverläufe gegen V14 | 8 | 53.892 | 29.828 / 30.698 | +1,61 |
| Ältere V14-Verläufe, drei Gegner | 8 | 48.173 | 27.286 / 27.426 | +0,29 |

Auf den älteren Karten reicht das Intervall des Treffergewinns von −0,07 bis +0,63 Prozentpunkten. Der logarithmische Verlust sank dort auf allen acht Karten. Auf den neueren Karten waren von den 99.118 Beispielfällen, in denen der Lehrer tatsächlich in eine Richtung zog, 44.145 bzw. 45.328 korrekt. Der beobachtete Effekt umfasst somit auch Richtungsentscheidungen.

Bloß den letzten eigenen Befehl zu wiederholen hätte in den neueren Verlaufsdaten **50,58 %** der aktuellen Lehreraktionen getroffen. Mahmouds Beobachtung der Wiederholungsrate des Lehrers betraf einen anderen Vergleich. Hier erhält die Auswertung ausschließlich den vorigen echten eigenen Befehl als neue Eingabe. In den neueren Diagnosepartien wich dieser 17.630-mal vom damaligen Vorschlag von V14 ab.

Grundlage waren 368 anhand ihrer Originalprüfsumme verifizierte Sitzarchive. Die Häufigkeiten wurden nur auf den 32 ursprünglichen und 120 neuen Lernkarten geschätzt (932.206 geeignete Zeilen). Die 8+24 Diagnosekarten blieben zurückgehalten. Nur unmittelbar aufeinanderfolgende Zugpaare derselben lebenden Einheit im selben Match außerhalb der Spawnzelle gingen ein. Die Unsicherheitsintervalle wurden mit 10.000 Ziehungen der ganzen Karte einschließlich beider Sitze berechnet. Der vollständige Vorabplan, der Auswertungscode und die Daten je Diagnosesitz liegen bei.

Eine Tabelle mit fünf Gruppen bildet die 79 Merkmale und das Kartenbild des vorhandenen CNN nur grob ab. Ob dem CNN der eigene letzte Befehl ebenfalls zusätzliche Informationen liefert und wie die Information den Spielausgang verändert, ist offen. Es wurden keine neuen Spiele gestartet und keine Gewichte angepasst.
