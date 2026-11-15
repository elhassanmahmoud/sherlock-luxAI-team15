# Ein Einzelnetz verbessert beide Diagnosegruppen

Die historische Warmkontrolle und R8 haben dieselbe Netzarchitektur und wurden aus demselben R3 gestartet. Ihre entsprechenden trainierten Gewichte sind zu gleichen Teilen in **einem** Netz gemittelt. Jede Stellung benötigt wieder nur einen Aufruf des Bewegungsberaters.

| Identische Eingaben | R3 | Historische Warmkontrolle | R8 | Gewichtsmittelwert |
|---|---:|---:|---:|---:|
| 24 Karten mit R3-Stellungen, 160.863 Entscheidungen | 109.585 | 109.571 | 109.838 | **109.947** |
| 24 Karten mit älteren Stellungen, 156.243 Entscheidungen | 98.938 | 99.296 | 98.774 | **99.107** |

Auf neuen Stellungen gewinnt der Mittelwert netto 362 Lehrerübereinstimmungen gegenüber R3, auf älteren netto 169. Auf den älteren Stellungen traf die nur mit historischen Daten nachtrainierte Warmkontrolle am häufigsten. Die beiden Verbesserungen des Einzelnetzes erfüllen die vorab festgelegten Bedingungen für 224 Spiele. Die Rolle des Beraters bleibt die Bewegungswahl mit dem ursprünglichen R3-Vertrauensschwellwert. Eine Änderung der Zahl richtiger Lehrerbefehle ist noch kein Beleg für mehr Spielsiege.

Alle drei Ausgangsnetze reproduzierten für die 96 Sitzarchive die abgelegten Trefferzahlen. Der neue Checkpoint hat SHA-256 `51a52f0453d5ac8e9a4ea70b3792572356761054cb2890520005160f77097cf2`. [Vergleich](validation.json) · [Checkpoint](../../candidates/r8_warm_20261115/midpoint.pth) · [Vorab festgelegte Prüfungen](PLAN.md)
