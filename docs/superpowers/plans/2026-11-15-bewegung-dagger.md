# Bewegungsschüler auf eigenen Spielverläufen

## Ausgangspunkt

Mit einem echten Lehrer für Bewegungen gewann V14 auf zwölf bekannten Karten sechs zusätzliche Partien. Der erste eigene Schüler lernte ausschließlich aus Situationen, in die V14 allein geraten war. Sobald der Schüler einen anderen Zug ausführt, begegnet ihm eine andere Stellung. Dieses Experiment prüft, ob er auf den Folgen seiner eigenen Züge zuverlässiger helfen kann. Mahmoud trainiert separat einen vollständigen CNN-Spieler. Hier bleibt V14 für jeden Grundbefehl und alle Schüsse zuständig.

## Sammlung und Lernen

1. Der erste Bewegungsberater spielt mit seinen eingefrorenen Gewichten `5327d0ff4e2cc4b09bdcb43ae51fbd7dcc9f6d8487f79f4a7cfd1ad176813575`. Bei jeder Beobachtung werden der ursprüngliche V14-Zug, der ausgeführte Zug und der Vorschlag des Schattenlehrers getrennt erfasst. Der Lehrer sieht nur die öffentliche Beobachtung dieser Seite. In seine Zughistorie kommt der tatsächlich ausgeführte Zug.
2. Es gibt 120 neue Lernkarten (7272000–7272119) und 24 neue Diagnosekarten (7272200–7272223), jeweils beide Seiten. Die Gegner Kaggle3, Solution_92 und V14 rotieren gleich häufig. Zusammen mit den ursprünglichen 32 Lern- und acht Diagnosekarten ergibt das 152 Lern- und 32 Diagnosekarten. Kein Wechsel eines Sitzes oder einer Karte zwischen den Mengen.
3. Ein Refit startet mit demselben Initialisierungsseed. Architektur, fünf Epochen, Verlust und die Einsatzschwelle 0,70 bleiben identisch. Das Experiment verändert Datenmenge und Herkunft der Stellungen gemeinsam. Der Vergleich erlaubt keine Trennung der Effekte dieser zwei Änderungen.
4. Wir dokumentieren je Datenquelle Zahl der Karten, Sitze, Schiffe/Aktionen, tatsächliche Eingriffe und Übereinstimmung mit dem Lehrer. Ein besserer Validierungswert ist noch keine höhere Siegquote.

## Entscheidung

Wenn der erste Schüler für die unabhängige Bestätigung nominiert wird, hat dessen Prüfung Vorrang. Andernfalls folgt genau ein Refit auf der erweiterten Sammlung. Das neue Netz spielt auf 16 frischen Karten (7272300–7272315) beide Seiten gegen Kaggle3, Solution_92 und direkt gegen V14. Die V14-Referenz spielt auf denselben Karten gegen die beiden externen Gegner. Für eine Nominierung braucht der Schüler über die beiden externen Gegner mindestens zwei zusätzliche ganze Siege, gegen Solution mindestens so viele Siege wie V14 und direkt gegen V14 mehr als 16 von 32 gewonnenen Spielen.

Bei Nominierung folgen 60 weitere Karten gegen die beiden externen Gegner (7272400–7272459), beide Seiten, und 60 andere direkt gegen V14 (7272500–7272559). Die beiden externen Gegner erhalten gleiches Gewicht. Wir ziehen Karten mit beiden Seiten gemeinsam, über beide externen Gegner synchron, 10.000-mal mit Seed 2711. Für eine Übernahme müssen die untere 95-%-Grenze des externen Vorteils über null und die des Direktvergleichs über 50 % liegen. Gegen Solution muss der Punktschätzer mindestens gleich hoch sein. Erst nach Default-Vergleich, gesicherter alter Abgabe, Ladetest im Kursrunner und reproduziertem Paket kommt ein Wechsel infrage.

Die 288 neuen Lern- und Diagnosespiele sind von den Leistungsvergleichen getrennt. Wir protokollieren auch den Fall, dass das neue Netz auf eigenen Karten mehr Lehrerbefehle reproduziert und trotzdem weniger Spiele gewinnt.
