# Erkennt der Bewegungsberater gegnerische Halter besser?

V14 und der bisherige CNN-Schüler sehen die aktuelle Belegung eines gegnerischen Punktefelds. Auf denselben Typen von Stellungen machte es einen Unterschied, ob dort bereits im vorigen Zug ein Gegner sichtbar war. Gegen den nativen Kaggle-Gegner blieb das Feld im nächsten Zug in 86 % gegenüber 45 % der Beobachtungen sichtbar besetzt, gegen Solution in 77 % gegenüber 60 %. Der Zusammenhang motiviert einen einzelnen zusätzlichen Eingang für unseren Bewegungsberater.

## Ein zusätzlicher Kartenkanal

Der Vergleich verwendet den auf eigenen Spielverläufen trainierten Bewegungsschüler mit harten Lehrerbefehlen als Kontrolle. Sein Gegnerkanal enthält bei vier Einheiten die maximale Belegung. Dieselbe öffentliche Belegung aus dem direkt vorigen verfügbaren Zug kommt als 17. Kartenkanal hinzu. Bei Spielbeginn, Matchwechsel oder einer Lücke in den Beobachtungen ist die Ebene null. Die beiden Spielseiten verwenden ihre eigene kanonische Sicht. Die Lehrerempfehlung, der Spielausgang und verborgene Gegnerpositionen sind keine Eingaben.

Beide Netze erhalten die identischen 152 Lern- und 32 Diagnosekarten, denselben Spielschrittplan, dieselbe Initialisierung der gemeinsamen Gewichte und fünf Epochen mit denselben Lernparametern. Der Filter für den neuen Eingang startet bei null. Vor dem Training wird geprüft, dass beide Architekturen dieselben Ausgaben liefern. Offline gespeicherte und im Spiel gebildete Vorgängerkanäle müssen einschließlich Beobachtungslücken und Matchwechseln übereinstimmen. Die sechs Aktionsausgänge, V14s Schüsse und die Eingriffsschwelle von 0,70 bleiben gleich.

## Wann echte Auswahlspiele folgen

Auf den 24 zurückgehaltenen Karten mit eigenen Spielverläufen werden bei beiden Kandidaten dieselben Befehle gezählt. Primär werten wir Entscheidungen eigener Einheiten in höchstens drei Feldern Chebyshev-Abstand zu einem bestätigten Punktefeld aus, auf dem gerade genau ein Gegner sichtbar ist und auf dem schon im direkt vorigen Zug ein Gegner sichtbar war. Die anderen acht Diagnosekarten werden getrennt ausgewiesen. Zur Nachvollziehbarkeit zählen wir je Gruppe Entscheidungen, Eingriffe, neu hergestellte und verlorene Lehrerübereinstimmungen.

Auswahlspiele folgen, wenn der zeitliche Eingang in diesem Nahbereich mehr zusätzliche Lehrerbefehle über V14 reproduziert als der Kontrollschüler, seine Nettoverbesserung über alle Entscheidungen mindestens hält und insgesamt höchstens 10 % mehr bereits richtige V14-Bewegungen verschlechtert. Bei einem positiven Befund spielen beide Schüler auf den gleichen externen Karten. Die Vergleichsgegner sind der native Kaggle-Agent und Solution, jeweils 16 neue Karten 7275000–7275015 mit beiden Seiten. Dazu kommen eine gepaarte V14-Referenz und 32 direkte Duelle des neuen Schülers gegen V14.

Für eine Nominierung braucht der neue Berater über beide externen Gegner mindestens zwei Siege mehr als V14, mindestens die Anzahl Solution-Siege von V14, insgesamt mindestens die Siege des Kontrollschülers gegen die externen Gegner und mehr als 16 direkte Siege. Für eine Übernahme folgen wie beim Kontrollschüler separate 60 Karten je externer Gegner (7275100–7275159) und 60 direkt (7275200–7275259), gepaarte Kartenintervalle und die abschließenden Default- und Kursprüfungen. Ein inzwischen bestätigter stärkerer Agent müsste ebenfalls geschlagen werden.
