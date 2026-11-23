# Ein Wartezug nach dem Betreten eines ungewissen Punktefelds

**Gegen Solution gewann die Halteprobe 90 von 96 ganzen Partien, ebenso viele wie die ursprüngliche Feldprobe und eine mehr als V16. Im direkten Duell gegen Original-V16 gewannen Feldprobe und Halteprobe jeweils 43 von 96.** Der einzelne Zusatzhalt änderte dort keinen ganzen Sieg. Die Halteprobe verfehlt die vorher festgelegte Mindestzahl von 48 Direktsiegen. Auf den sechs frischen Solution-Sitzen mit echtem Zusatzhalt entstanden saldiert drei zusätzliche eigene Sofortpunkte. Die Studie ist als eigener Kandidat abgeschlossen. [Vollständiger Vergleich](leistung.json) · [Unabhängige Gegenrechnung](gegenpruefung_leistung.json) · [Drei gezielte Archivkontrollen](direktursache.json)

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

Alle vorab festgelegten Kriterien dieser historischen Mechanikprüfung sind erfüllt. Der Stärkevergleich auf 48 neuen Sicht-1-Karten startete am 23.11. um 12:42 Uhr. [Festgelegte Karten](karten_leistung.json) · [Quellbindungen](quellen_leistung.json)

## Ganze Spiele auf 48 neuen Karten

Die ersten 48 Sicht-1-Karten ab 163500000 wurden nach der Sensorweite ausgewählt. Beide Sitze jeder Karte traten in allen fünf vorab festgelegten Gruppen an. Insgesamt liefen 480 vollständige Spiele im ursprünglichen Kursablauf. Für 145.440 Runden wurden die Punktreihen erneut gegen die 1.440 Matchresultate und alle Gesamtresultate gerechnet. Bei jedem Zusatzhalt gegen Solution stimmten die gemeinsamen Befehlsfolgen der Halteprobe und ihrer Feldprobenkontrolle bis zum Eingriff überein. Auf den anderen 90 Sitzen stimmten die beiden Gruppen über das ganze Spiel überein.

| Gegner | Variante | Siege / Spiele | Sitz 0 | Sitz 1 |
|---|---|---:|---:|---:|
| Original-Solution | Original-V16 | 89/96 | 45/48 | 44/48 |
| Original-Solution | Feldprobe | 90/96 | 46/48 | 44/48 |
| Original-Solution | Halteprobe | 90/96 | 45/48 | 45/48 |
| Original-V16 | Halteprobe | **43/96** | 23/48 | 20/48 |
| Feldprobe | Halteprobe | 49/96 | 26/48 | 23/48 |

Gegen Solution führte die ursprüngliche Feldprobe auf 26 Sitzen eine Messbewegung aus. In 19 dieser Fälle ließ der Folgeschutz einen Halt zu, in sechs wählte ihn das Modell aus. Vier der sechs Schiffe standen auf einem tatsächlich punktebringenden Feld, zwei auf einem leeren. Die eigene Sofortdifferenz gegenüber der Feldprobe war viermal +1, einmal 0 und einmal −1. Über vier Züge betrug sie zusammen +5. Auf alle 96 Sitze umgelegt ergeben sich +0,031 eigene Sofortpunkte (95-%-Kartenintervall −0,010 bis +0,094). Der direkte Gewinnanteil gegen V16 lag bei 44,8 % (39,6 bis 50,0 %), gegen Feldprobe bei 51,0 % (50,0 bis 53,1 %). Alle Intervalle halten die beiden Sitze einer Karte zusammen.

Gegen Solution drehte der Zusatzhalt zwei volle Partien in entgegengesetzte Richtungen. Auf Karte 163500081, Sitz 1, brachte er sofort +1 auf (18,22). Das dritte Match ging von 598:606 auf 641:558, die ganze Partie von einer Niederlage zu einem Sieg. Auf Karte 163500159, Sitz 0, brachte der Halt auf (1,6) ebenfalls sofort +1 und über vier Züge +3. Das dritte Match wechselte von 416:406 zu 351:511, wodurch das Team die Partie verlor. Gegenüber Original-V16 blieb jeder von dessen 89 Solution-Siegen erhalten. [Eingriffs- und Ergebnispaare](leistung.json) · [Alle 480 Befehlsprüfsummen und Punktkurven](leistung_partien.jsonl.gz)

Gegen die unveränderte Feldprobe trat ein Zusatzhalt nur auf drei der 96 Sitze auf. Auf 46 Karten spielte somit in beiden Durchläufen die reine Feldprobe gegen sich selbst. Der zusätzliche Direktsieg entstand auf der Karte 163500081, auf der sich auf beiden Sitzen in derselben Runde die öffentlich begründete Halteentscheidung ergab. Auf der zweiten betroffenen Karte änderte der einseitige Zusatzhalt das ganze Ergebnis nicht. [Gegenprüfung mit vertauschten Varianten](gegenpruefung_leistung.json)

## Was die Niederlagen gegen V16 erklärt

Auf 93 der 96 direkten Sitze gegen V16 gab die Halteprobe genau die Befehle der Feldprobe. Beide Varianten gewannen dort 43 Partien. Für die drei übrigen Sitze wurden nach Abschluss des festen Vergleichs drei zusätzliche vollständige Feldprobenkontrollen auf denselben Karten gespielt. Alle gemeinsamen Befehle bis zur Halteentscheidung sowie die tatsächliche Ankunft und die Punktfolge bis zu diesem Zeitpunkt stimmten überein.

| Karte und Sitz | Wartezug und Feld | Zusätzliche eigene Punkte sofort / über vier Züge | Zweites Match mit Feldprobe → mit Zusatzhalt | Ganze Partie |
|---|---|---:|---|---|
| 163500055, Sitz 1 | Schritt 134 auf (18,18), leer | 0 / 0 | 385:380 → 392:422 | beide verloren |
| 163500081, Sitz 0 | Schritt 25 auf (1,5), aktiver Punkt | +1 / +1 | 557:600 → 533:520 | beide verloren |
| 163500081, Sitz 1 | Schritt 25 auf (18,22), aktiver Punkt | +1 / +1 | 557:600 → 533:520 | beide verloren |

Damit steht die ursprüngliche Feldprobe auf genau diesen 96 direkten Sitzen bei 43 Siegen. Die Halteprobe verlor mit denselben Schiffsbewegungen bis zum Zusatzhalt ebenfalls alle drei gezielt nachgespielten Gesamtpartien. Die späteren Punktverläufe und drei zweite Matchausgänge änderten sich. Der Rückstand unter die Hälfte der ganzen Spiele bestand schon vor dem Hinzufügen des Halteentscheiders. Die drei nachträglichen Kontrollspiele und ihre 909 Schritte sind separat archiviert. [Ergebnisse der drei Ursachenvergleiche](direktursache.json) · [Kontrollprotokolle](direktkontrollen.jsonl.gz) · [Gegenrechnung](gegenpruefung_direktursache.json)
