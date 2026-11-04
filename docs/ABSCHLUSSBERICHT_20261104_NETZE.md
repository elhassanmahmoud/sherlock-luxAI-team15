# Abschlussbericht: Einzelnetz und 42 Netze – 04.11.2026

**V14 mit 36 Netzen bleibt die Abgabe.** Die zusätzliche Studie liefert keinen ausreichend bestätigten Nachfolger. FO42 gewinnt zahlenmäßig mehr Spiele gegen Solution, verfehlt aber drei der sieben Freigabebedingungen. Das geprüfte Einzelnetz SOLO28 scheitert bereits in der Auswahl. Die einzige Bestätigung endete am 04.11. um **11:13:00 Uhr Berlin** vollständig; unabhängige Datenprüfung und zusätzlicher Abschlussabgleich bestätigen die Ergebnisse.

## Was tatsächlich untersucht wurde

Auf den erneuten Auftrag wurden genau zwei vorab festgelegte Varianten gebaut, beide mit der V14-Spielkonfiguration:

- **SOLO28:** nur V14-Mitglied 28, tatsächlich ein Inferenznetz. Die Nominierung beruhte auf historischen 16/16 Siegen gegen Solution auf acht bereits bekannten Karten. Das war kein neuer Stärkenachweis und keine Suche nach dem besten aller möglichen Einzelnetze.
- **FO42:** alle 36 V14-Netze plus sechs unterschiedliche vorhandene FO-Netze aus `all24fo`, Mitglieder 18–23. Alle 42 gehen gleichgewichtet in die Inferenz ein. Der Vergleich verändert Zusammensetzung und Anzahl zugleich; er isoliert keinen reinen Effekt der Netzanzahl.

**In dieser Studie wurden null neue Netze trainiert.** Die zwei tatsächlichen Nachtrainingsarme mit je 1.200 Lernspielen gehören zum getrennten, zuvor abgeschlossenen Programm vom 03./04.11. ([dessen Bericht](MORGENBERICHT_20261104.md)). Seine Daten wurden nicht mit dieser Studie vermischt.

Nach 44 technischen Spielen auf zwei bekannten Karten folgten **920 Auswahlspiele auf 20 frischen Karten**. SOLO28 erreichte im Panel 137/240 statt V14 190/240, gegen Solution 31/40 statt 35/40 und direkt 16/40. Dieses Einzelnetz war klar schwächer im kleinen Auswahlsatz; daraus folgt kein Urteil über alle Einzelnetze. FO42 wurde mit Panel 193/240, Solution 39/40 und direkt 20/40 als einziger Kandidat nominiert. [Vollständige Auswahl](../experiments/analysis/network_breadth_20261104/selection/README.md).

## Die unabhängige Bestätigung

| Messung | FO42 | V14 | Differenz bzw. direkte Quote mit 95-%-Intervall |
|---|---:|---:|---|
| Sechserpanel, 80 Karten | 773/960 | 772/960 | Δ +0,104 pp [−3,646; +3,750] |
| Solution, 400 Karten | 771/800 = 96,375 % | 762/800 = 95,250 % | Δ +1,125 pp [−0,375; +2,750] |
| default, 80 Karten | 160/160 | 160/160 | Δ 0 pp |
| Direkt gegen V14, 160 Karten | 180/320 | 140/320 | 56,25 % [48,75; 63,75] |

**Nicht erfüllt:** Panelgewinn mindestens +1 pp, untere Panelgrenze über null und untere Direktduellgrenze über 50 %. **Erfüllt:** Solution-Differenz mindestens null, deren untere Grenze über −1 pp, default mindestens 99 % und default-Differenz mindestens −1 pp. Vier erfüllte Bedingungen reichen nicht; alle sieben waren erforderlich. Keine zweite Bestätigung, kein Nachrücken und keine Übernahme von FO42.

Die neun zusätzlichen Solution-Siege sind ein positiver Punktschätzer, aber kein gesicherter allgemeiner Vorteil. Das Solution-Intervall enthält null; auch Panel und Direktduell lassen keinen ausreichend abgesicherten Gesamtgewinn erkennen. Eine allgemeine Verschlechterung oder Unerreichbarkeit eines stärkeren Einzelnetzes ist damit ebenfalls nicht bewiesen. 100 % gegen Solution wurden nicht erreicht.

## Umfang und Verlässlichkeit

Insgesamt wurden **4.804 Spiele ausgeführt: 44 technisch + 920 Auswahl + 3.840 Bestätigung**. Dahinter stehen **580 unterschiedliche frische Karten**, zusätzlich zwei bekannte technische Karten. Auswahl: 861000–861019. Bestätigung: 80 Panel/default-Karten 862000–862079, weitere 320 Karten 862080–862399 nur gegen Solution sowie 160 getrennte Direktkarten 863000–863159. Solution umfasst somit insgesamt 400 Karten; seine zusätzlichen Karten erhöhen nicht das Gewicht im Sechserpanel.

Die Kartenbereiche waren anhand der geprüften lokalen Datenbestände zuvor unbenutzt. Seedlose oder nicht dokumentierte externe Läufe lassen sich dadurch nicht ausschließen.

Der Umfang wurde nach dem technischen Pilot **vor frischen Ergebnissen** aus Zeitgründen von ursprünglich 5.720 auf 4.760 Leistungsspiele begrenzt. Die sieben Gates blieben unverändert. 80 Panelkarten bedeuten breitere Unsicherheit als in der früheren 400-Karten-Studie.

Alle fünf Bestätigungsaufgaben endeten mit Exit 0. Sämtliche erwarteten Schlüssel, 303 Schritte, Punktezählung v2 und Ergebniswerte wurden geprüft; keine ausgeschlossenen Spiele. Der unabhängige Auditor bestätigte alle offiziellen Zahlen und Intervalle mit eigener Berechnung: 5.000 Ganzkarten-Bootstrapziehungen, PCG64-Seed 0, beide Seiten und alle Panelgegner gemeinsam. Quellenstand `bed06df` und eingefrorene Eingaben blieben gleich. [Rohdaten](../experiments/analysis/network_breadth_20261104/confirmation/README.md), [unabhängiger Review](../experiments/analysis/network_breadth_20261104/confirmation_review/confirmation_independent_review.md), [zusätzlicher Abschlussabgleich](../experiments/analysis/network_breadth_20261104/confirmation_review/final_root_checks.json).

## Unveränderte Abgabe und späterer Vorschlag

Abgabedatei bleibt `Gruppe15.zip` mit **22.228.404 Bytes**, Klasse `Gruppe15.main.Agent_x` und Gewichten `Gruppe15/agent.pth` für beide Seiten.

- Beide aktiven Rohgewichte: SHA-256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`.
- Bestehende ZIP: SHA-256 `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`.

Die früheren konkreten Python-3.13-/3.10-Prüfungen gelten für dieselben unveränderten Bytes. **Heute wurden Hashes und ZIP-Inhalt erneut geprüft; keine neue Laufzeitprüfung und kein FO42-Paket gebaut.**

Eine spätere Destillation könnte die mittleren Q-Werte des akzeptierten V14 in ein einzelnes breiteres Netz übertragen. Sie ist **nur ein Vorschlag, nicht implementiert oder trainiert**, ohne Stärkegarantie. Nach etwa 11 Uhr hätte schon der unveränderte frische Vergleich konservativ mindestens 3 h 45 min, mit Pilotzeiten 4 h 44 min benötigt – vor Training und Prüfung. Das passt nicht zum Spielende 14:30 und Abschluss 16:00 mit 90 Minuten Abschlussreserve. Das Kontingent war nach der natürlichen Erneuerung nicht der begrenzende Faktor. [Machbarkeit und Grenzen](../experiments/analysis/network_breadth_20261104/confirmation_review/single_distillation_feasibility.md).

Der [Betriebsabschluss](../experiments/analysis/network_breadth_20261104/confirmation_review/closure_checks.json) bestätigt um 11:22 Uhr Berlin: alle fünf erfassten eigenen Prozesse beendet, beide Automationen pausiert, Experimentquelle unverändert. Fremde Dateien und alte Sicherungen blieben erhalten; kein Moodle-Upload wurde ausgeführt.
