# Der Wechsel zu V15 rettet gegen Solution zwei Partien und kostet zwei Siege

Auf **184 früheren Solution-Karten mit beiden Startseiten** gewinnen Original-R3 und der Wechselagent jeweils **364 von 368 Partien (98,91 %)** und **1.054 von 1.104 Matches**. Für die Differenz der Spielsiegraten beträgt das gepaarte 95-%-Kartenintervall **−1,09 bis +1,09 Prozentpunkte**, für die Differenz der Matchsiegraten **−0,36 bis +0,36 Prozentpunkte**. Je Ziehung blieben beide Sitze derselben Karte zusammen (10.000 Ziehungen, PCG64, Seed 2711). [Vollständige Auswertung nach Sitz und Karte](solution_scope/assessment.json)

Der Agent übernimmt V15 nur im dritten Match, wenn R3 das erste Match gewonnen und das zweite verloren hat. Dieser öffentliche Auslöser trat auf **15 Sitzen auf zwölf Karten** ein. Von den vier zuvor verlorenen Partien rettete V15 zwei. Von den elf zuvor gewonnenen Partien verlor V15 zwei. Damit entschieden beide Spielweisen jeweils elf der 15 tatsächlich umgeschalteten Spiele für sich. Die vier Spiele mit anderem Sieger verteilen sich auf vier Karten.

| Karte und eigener Sitz | M3 mit R3, Sherlock : Solution | M3 mit V15, Sherlock : Solution | Ganzer Spielausgang |
|---|---:|---:|---|
| 7170236 / Spieler 0 | 456 : 519 | 636 : 458 | Niederlage → Sieg |
| 7273148 / Spieler 0 | 343 : 398 | 473 : 114 | Niederlage → Sieg |
| 7286000 / Spieler 1 | 750 : 698 | 671 : 721 | Sieg → Niederlage |
| 7286005 / Spieler 0 | 538 : 461 | 345 : 413 | Sieg → Niederlage |

Auf Spieler 0 stieg die Siegzahl von 182 auf 183 der 184 Spiele, auf Spieler 1 sank sie von 182 auf 181. Die früher gezielt ausgewählten 20 Diagnosepartien sind in diesem Vergleich nicht enthalten. Der dort beobachtete Vorteil auf den gewählten Solution-Verlustsitzen ergibt über diese sechs früheren Kartenblöcke keinen Nettozuwachs. Die Entscheidung zum allgemeinen Umschalter bleibt abgeschlossen. [Gezielter Vorversuch](ERGEBNIS.md) · [Festgelegter Umfang der separaten Solution-Frage](solution_scope_design/PLAN.md)

## Woher die 368 Sitzresultate kommen

1. **322 archivierte 3:0-Siege.** Auf jedem dieser Sitze gewann R3 M1 und M2. Beide Varianten folgen bis dahin R3. Mit 2:0 am Anfang von M3 bleibt R3 auch im dritten Match aktiv. Das ursprüngliche Ergebnis gilt für beide Spielweisen. Diese 322 Spiele wurden nicht erneut ausgeführt. Ein 0:3-Ergebnis kam im Register nicht vor.
2. **46 neu reproduzierte R3-Kontrollen.** Das sind sämtliche ursprünglichen 1:2- und 2:1-Sitze. Alle 46 reproduzierten die archivierten Matchsummen sowie die Gesamtpunktzahlen beider Teams. In 31 Partien blieb der Auslöser aus. Ihr reproduziertes R3-Ergebnis gilt für beide Varianten.
3. **15 neu gespielte Variantenpartien.** Für jeden der übrigen Sitze wurde die Übernahme in M3 mit derselben Vorgeschichte gespielt. Für alle 15 Paare sind die tatsächlichen eigenen und gegnerischen Weltbefehle in den ersten 202 Zügen bytegleich und stimmen beide ersten Matchendscores und -sieger überein. Auf allen 15 Sitzen führte eine aktive Einheit tatsächlich mindestens einen anderen Befehl aus, insgesamt 3.459 Einheitsbefehle.

Die **61 neuen Partien** (46 Kontrollen und 15 Varianten) sind vollständig im Roharchiv enthalten. Für jede Partie wurden die Befehle beider Spieler über 303 Züge dekodiert und gegen die hinterlegten Prüfsummen geprüft. Die 368 Ausgangszeilen, alle Endstände, die vier geänderten Ergebnisse und das gepaarte Intervall wurden unabhängig nachgerechnet. Die historischen Karten waren bereits ausgewertet. Der Vergleich beantwortet die separate Frage für Solution auf diesem Bestand. [Register aller 368 Sitze](solution_scope_design/roster.json) · [Rohdaten der 61 Partien, gzip-komprimiertes TAR](solution_scope/partien.tar.gz) · [SHA-256 je Partie](solution_scope/completed.json) · [Quellen und Kriterien](solution_scope/protocol.json)
