# Ein Wartezug nach dem Betreten eines ungewissen Punktefelds

## Was der Spieler erfährt

Die bestehende Feldprobe ändert einmal den Bewegungsbefehl eines freien V16-Schiffs. Eine Runde später kann Sherlock öffentlich sehen, ob dieses Schiff am Ziel angekommen ist, welche Felder die eigene Flotte jetzt belegt und wie viele Punkte das Team gerade erhalten hat. Bei mehreren gleichzeitig besetzten unbekannten Feldern kann dieselbe Punktzahl verschiedene Ursachen haben.

Das Modell berücksichtigt, dass mehrere Schiffe auf derselben Weltzelle zusammen höchstens einen Punkt verdienen. Zwei unterschiedliche besetzte Spiegelpositionen können dagegen zwei Punkte beitragen. Aus den Belegungen, den letzten beiden Teamgutschriften und den bereits von V16 eingestuften Feldern schätzt es, welche unbekannten Zellen die Gutschrift erklären. Der gelernte Entscheider bewertet sowohl den gerade betretenen Ort als auch das andere Feld, zu dem V16 weiterfahren möchte. Eine rechnerisch eindeutige Zuschreibung gilt unter den verwendeten V16-Feldurteilen. Das Modell greift auf die aktuelle Gutschrift allein zurück, falls die beiden Beobachtungen zusammen unvereinbar sind oder das Auftauchen eines neuen Reliktpaars zwischen ihnen noch möglich ist.

Der mögliche Zusatzbefehl ist ein einziger Wartezug derselben Einheit direkt nach der Messbewegung. Das Schiff muss lebend und allein am Ziel stehen. Der Spieler schützt bestätigte Punktefelder, konkurrierende bekannte Punktaufträge, ankommende Mitspieler, sichtbare Feinde in SAP-Reichweite, geringe Energie und ursprüngliche SAP-Befehle. Der Feldstatus des Schiedsrichters ist ausschließlich bei der Auswertung zugänglich. [Spieler](kandidat.py) · [Öffentliche Merkmale und Schutzbedingungen](rueckmeldung.py) · [Vorab festgelegte Auswahlkriterien](PLAN.md)

## Was sich aus natürlichen Abfahrten lernen lässt

Von 160 Original-V16-Partien lieferten 157 zusammen 1.982 vergleichbare Übergänge. Auf 47 von 48 separat zurückgelegten Karten kamen 633 weitere Beispiele hinzu. Das Lernziel vergleicht die Punktwirkung eines möglichen Halts mit der tatsächlichen V16-Abfahrt, während die Positionen der übrigen Schiffe festgehalten werden. Der echte alternative Spielverlauf wird erst in der nachfolgenden Paarprüfung ermittelt. Die aufgezeichneten natürlichen Übergänge enthalten zudem keinen historischen internen V16-Zielauftrag pro Schiff. Der tatsächliche Spieler prüft diesen Auftrag zusätzlich.

| Getrennte natürliche Prüfung | Ohne jüngste Gutschrift | Mit öffentlicher Rückmeldung |
|---|---:|---:|
| Mittlerer Log-Loss, jede Karte gleich gewichtet | 0,405 | 0,326 |
| Ausgewählte Halte unter 633 natürlichen Übergängen | 0 | 10 |
| Davon zusätzlicher / gleicher / verlorener eigener Punkt | 0 / 0 / 0 | 5 / 3 / 2 |

Die Verringerung des Log-Loss beträgt 0,078. Das 95-%-Kartenintervall reicht von 0,033 bis 0,135. Über alle 633 möglichen Abfahrten hätten 22 Halte unter der geometrischen Annahme einen zusätzlichen Punkt gebracht, 45 einen Punkt gekostet und 566 denselben Beitrag geliefert. Ein zweiter Rechenweg prüfte alle 2.615 Lern- und Validierungsetiketten anhand der Originalstellungen und verglich 1.260 berechnete Feldwahrscheinlichkeiten mit vollständig aufgezählten Belegungsmöglichkeiten. [Lernresultat](natur.json) · [Getrennte Prüfung](gegenpruefung_natur.json) · [Gewichte](modell.json)

Die fünf positiven ausgewählten Fälle der natürlichen Validierung stammen von nur zwei Karten gegen V16, jeweils auf Sitz 0. Die zwei negativen Fälle traten auf zwei weiteren V16-Karten auf Sitz 1 auf. Gegen Solution wurde auf einer Karte ein geometrisch gleichwertiger Halt ausgewählt. Damit war der im Voraus verlangte echte Zusatzpunkt gegen jeden der beiden Gegner für die nachfolgende Paarprüfung besonders wichtig. [Natürliche Validierungsbeispiele](natur_valid.jsonl.gz)

## Welche tatsächlichen Feldproben untersucht wurden

Die historische Auswahl umfasste 48 Sicht-1-Karten. Auf 25 davon wurden insgesamt 56 echte Messbewegungen ausgelöst. Je Gegner entfallen 14 auf jeden Sitz. Die ursprüngliche Sichtung von 100 vollständigen Diagnosedateien ist nachgerechnet. Für 84 dieser Dateien lagen zusätzlich Befehlsprüfsummen und drei Matchresultate im früheren Feldprobe-Archiv vor. Alle 56 Messbewegungen sind im ursprünglichen Archiv enthalten. [Prüfung der Ausgangsdaten](vorbefund.json) · [Ursprüngliche Gelegenheiten](../feldbindung/fenster.jsonl.gz)

| Ursprüngliche Feldprobe | Gegen Solution | Gegen V16 |
|---|---:|---:|
| Tatsächliche Messbewegungen | 28 | 28 |
| Bewegtes Schiff erreichte ein aktives Punktefeld | 13 | 19 |
| Davon stand es die ersten vier Züge durchgehend dort | 4 | 6 |
| Rückblickend punktebringende Ankünfte mit möglicher Abfahrt | 5 | 11 |

Die 16 rückblickend erkannten Fälle enthalten bereits Wissen über das echte Punktefeld. Die neue öffentliche Entscheidung musste sich auf allen 56 tatsächlichen Messbewegungen bewähren, darunter 24 zunächst erfolglose.

## Wirkung in echten Gegenfortsetzungen

**Zehn der elf ausgewählten Wartebefehle brachten sofort einen zusätzlichen eigenen Teampunkt.** Alle 56 Originalpartien reproduzierten sämtliche 303 gemeinsamen Befehlsrunden, die ursprüngliche Punktfolge und alle drei Matchresultate. Bei jeder ausgewählten Alternative wurden die Partie und beide Spieler neu gestartet und derselbe Präfix bis zur Abfahrt erneut gespielt. Beide Verläufe hatten bis dahin auch dieselbe eigene Gutschrift und dieselbe Ankunft der gewählten Einheit. Der experimentelle Zweig änderte allein deren anschließenden Befehl in einen Wartezug.

| Echte Feldprobe mit möglichem Anschluss | Gegen Solution | Gegen V16 | Zusammen |
|---|---:|---:|---:|
| Öffentlich geeignete Linien unter allen ausgeführten Feldproben | 15 | 14 | 29 |
| Tatsächlich gewählter einzelner Wartebefehl | 5 | 6 | 11 |
| Davon sofort mehr / gleich viele / weniger eigene Punkte | 4 / 1 / 0 | 6 / 0 / 0 | 10 / 1 / 0 |
| Zusätzliche eigene Teampunkte im ersten Zug | +4 | +6 | +10 |
| Zusätzliche eigene Teampunkte über vier Züge | +12 | +9 | +21 |
| Zusätzliche Belegungspunkte am konkreten Ziel über vier Züge | +13 | +12 | +25 |

Alle elf gewählten ursprünglichen Ankünfte waren punktebringend. Unter den 18 öffentlich geeigneten, aber abgelehnten Fällen hatte nur eine Ankunft einen Punkt gebracht. Alle fünf rückblickenden Gelegenheiten gegen Solution kamen zum Einsatz. Von elf gegen V16 entfielen vier durch die zusätzlichen öffentlichen Schutzbedingungen und eine durch die Modellschwelle. Auf Sitz 0 ergaben sich vier Halte mit zusammen +4 sofort und +7 über vier Züge, auf Sitz 1 sieben mit +6 und +14. Die Gegner erhielten über dieses Zeitfenster in keinem Vergleich andere Punktsummen. Über die 25 historischen Karten mit ausgeführter Messbewegung beträgt der eigene Zusatzgewinn auf beiden Sitzen und gegen beide Gegner zusammengenommen 0,40 pro Karte sofort (95-%-Kartenintervall 0,16 bis 0,68), über vier Züge 0,84 (0,24 bis 1,52).

Die vier Züge zeigen auch den Preis eines verzögerten Auftrags. Auf Karte 162400078 (Sitz 1, V16) brachte der Halt auf (18,22) sofort +1, über vier Züge lag das Team bei −2. Auf 162400011 (Sitz 1, Solution) blieb die unmittelbare Teamgutschrift gleich, über vier Züge lag sie um einen Punkt niedriger. Auf 162400056 (Sitz 1, Solution) brachte der Halt auf (16,10) dagegen vier zusätzliche Punkte in vier Zügen. [Fallbilanz einschließlich verworfener Gelegenheiten](fallbilanz.json) · [Alle echten Paarergebnisse](mechanik.json) · [Komprimierte Protokolle](mechanik_partien.jsonl.gz) · [Gegenprüfung](gegenpruefung_mechanik.json)

Alle vorab festgelegten Kriterien dieser historischen Mechanikprüfung sind erfüllt. Der Stärkevergleich auf 48 neuen Sicht-1-Karten ist am 23.11. um 12:42 Uhr gestartet. [Festgelegte Karten](karten_leistung.json) · [Quellbindungen](quellen_leistung.json)
