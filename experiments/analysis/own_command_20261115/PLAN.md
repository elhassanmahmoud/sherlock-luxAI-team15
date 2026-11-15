# R5 mit dem letzten tatsächlich gespielten Befehl

Auf 24 getrennten Diagnosekarten half der zuvor ausgeführte eigene Befehl einer einfachen Häufigkeitstabelle, die nächste Lehreraktion vorherzusagen. Sie traf 1.868 zusätzliche Entscheidungen bei 147.228 gültigen Vorgeschichten. Ob dieser Hinweis über das Kartenbild und alle 79 bereits verfügbaren Merkmale hinaus etwas beiträgt, ist die Frage des kontrollierten CNN-Versuchs. [Archivauswertung](archive/ERGEBNIS.md).

## Vergleich mit R2

Der einzige neue Eingang ist der zuletzt tatsächlich von dieser Einheit gespielte Befehl. Sechs zusätzliche Binärwerte stehen für Stillstand, vier Bewegungen und Schuss. Bei unbekannter Vorgeschichte sind alle sechs null. Beide Beobachtungen müssen zum selben Match und zur selben lebenden Einheit gehören, aufeinanderfolgen und außerhalb der Spawnzelle liegen. Die beobachtete Positionsänderung muss zum ausgeführten Befehl passen. Der Schüler erhält weder den früheren Vorschlag des Lehrers noch den aktuellen Spielausgang.

Die fünf Trainingsdurchläufe, 152 Lernkarten, 32 zurückgehaltenen Karten, Reihenfolge, Maske und Einsatzschwelle 0,70 entsprechen R2. Die bisherigen Gewichte werden mit demselben Startwert initialisiert. Die sechs neuen Gewichtsspalten starten bei null. Vor den fünf Epochen wird geprüft, dass derselbe Eingang anfangs dieselben Bewertungen ergibt. Ein Spieltest mit diesen Gewichten ist nur sinnvoll, wenn das Nachspielen des Archivs und der echte Entscheidungsweg dieselben sechs Werte erzeugen. Besonders zu prüfen sind Seitenwechsel der Perspektive, Wiederauftauchen einer UID, Matchwechsel, Lücken und von V14 überstimmte Schülervorschläge.

## Vorab festgelegte Entscheidung

Auf den 24 gemischten Diagnosekarten braucht R5 auf Zeilen mit gültiger Vorgeschichte netto mehr Übereinstimmungen mit dem Lehrer als R2. Über alle Zeilen muss er R2 netto mindestens erreichen und darf höchstens 10 % mehr vorher richtig gewählte V14-Befehle verschlechtern. Die acht älteren Karten werden getrennt berichtet. Maßgeblich ist der feste Checkpoint der fünften Epoche.

Erfüllt R5 diese Bedingungen, folgt eine Auswahl auf 16 neuen Karten (7277000–7277015, beide Seiten). R5, V14 und R2 spielen auf denselben Karten gegen Solution und den nativen Kaggle-Agenten, R5 zusätzlich direkt gegen V14. Für eine Nominierung sind zwei zusätzliche externe Siege gegenüber V14, mindestens die Solution-Siegzahl von V14, eine direkte Mehrheit und mindestens die externe Gesamtsiegzahl von R2 erforderlich.

Die unabhängige Bestätigung verwendet extern 7277100–7277159 und direkt 7277200–7277259. Maßgeblich sind ganze Spiele und je Karte gepaarte 95-%-Intervalle. Die untere Grenze für den externen Vorteil gegenüber V14 muss positiv sein, direkt muss sie über 50 % liegen. Solution muss mindestens V14 erreichen, extern muss der Punktschätzer mindestens R2 erreichen. Eine Ablösung erfordert die bisherige Default-, Kurs-, Paket- und Sicherungsprüfung sowie einen Vergleich mit einer inzwischen nachgewiesen stärkeren Version.
