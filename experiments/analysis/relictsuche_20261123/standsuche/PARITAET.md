# Identische Vorentscheidung auf sechs festen Karten

Für die ersten sechs Karten mit einem Warteereignis im vollständigen Präfix der Trainingsindizes 0 bis 6 wurden Original-V16 und jede zulässige Richtungsalternative erneut vom Kurs-Reset gespielt. Die Auswahl erfolgte anhand des Vorhandenseins eines Ereignisses. Sie verwendete keine Punktestände oder Ergebnisse der Richtungszweige. **Alle 20 Alternativen reproduzierten die gesamte öffentliche Vorgeschichte beider Spieler und die ursprünglichen V16-Vorschläge exakt.**

| Karte | Sitz | Zug | Schiff | Öffentliche Energie | Schon ausgeführte STAY | Geprüfte Richtungen |
|---|---:|---:|---:|---:|---:|---:|
| 161500001 | 0 | 22 | 0 | 188 | 11 | 3 |
| 161500008 | 0 | 22 | 0 | 210 | 6 | 4 |
| 161500012 | 1 | 39 | 4 | 226 | 3 | 2 |
| 161500013 | 0 | 30 | 4 | 136 | 3 | 4 |
| 161500015 | 1 | 22 | 3 | 113 | 4 | 4 |
| 161500016 | 0 | 30 | 3 | 204 | 3 | 3 |

Der direkte Vergleich prüfte 13.200 einzelne Beobachtungsarrays einschließlich Typ, Form und Byteinhalt. Er umfasste die vollständigen Beobachtungen beider Spieler, alle früher ausgeführten eigenen und gegnerischen Befehle sowie alle 16 originalen V16-Vorschläge und Gegnerbefehle im Entscheidungszug. Nach der Änderung stimmten die übrigen 15 gleichzeitig ausgeführten Befehle weiterhin überein. Die gewählte UID, ihr Energie- und Positionswert, der V16-Wartebefehl, die Zahl bereits ausgeführter Wartebefehle am selben Ort, die gesamte archivierte Ereignisbeschreibung und der ursprünglich gespeicherte Prüfsummenanker wurden für jeden Lauf bestätigt. Der gespiegelte bzw. ungespiegelte Alternativbefehl war zugelassen und wurde an die echte Umgebung übergeben.

Die 26 unabhängigen Präfixläufe umfassten 721 Kursschritte. Die Prüfung endet mit dem ersten abweichenden Befehl. Die danach entstehenden unterschiedlichen Punkteverläufe und spätere Spielstärke sind Gegenstand der Lern- und Ganzspielmessungen. Der vollständige Bytevergleich gilt für diese sechs Karten. Der Trainingssammler bindet auf den übrigen Karten eine kleinere Merkmalsmenge zusammen mit gemeinsamen früheren Aktionen und der Ereignisbeschreibung.

Die Studienrunner erzeugen je Sitz eine neue Instanz. Bei einer wiederverwendeten Instanz nach `new_game` mit anderem Sitz muss ein portabler Laufzeitwrapper zusätzlich die Sitznummer des Grundagenten übernehmen. Dieses Verhalten war für die gemessenen frischen Instanzen ohne Auswirkung.

[Einzellauf-Prüfsummen und Eingabedateien](paritaet.json) · [Unabhängiger Prüfcode](paritaet.py)
