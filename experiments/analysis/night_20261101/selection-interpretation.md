# Abgeschlossene Auswahl: Warum CONTROL nominiert wurde

**CONTROL ist auf den Auswahlkarten der einzige zugelassene Kandidat. Sein Panelgewinn kommt rechnerisch vollständig aus den Duellen gegen V10 und V13. Ein allgemeiner Fortschritt gegen jeden Gegner oder ein bestimmter verbesserter Spielmechanismus ist damit noch nicht bewiesen.**

Diese Interpretation verwendet ausschließlich `selection_summary.json` und die ausdrücklich benannten abgeschlossenen `selection_{baseline,control,discovery,overlap}.csv` sowie die CONTROL-/DISCOVERY-Direkt-CSVs in `sherlock-v10-mechanics/experiments/analysis/night_20261101/`. **Keine Bestätigungsdatei oder Zwischenresultate daraus gelesen.** Keine Modelle, Spiele, Tests, Quelländerungen oder Tuning ausgeführt.

## Woher +4,83 Prozentpunkte kommen

50 Karten × beide Seiten × sechs Gegner = 600 Panelspiele. Je Gegner 100 Spiele; alle folgenden W/D/L-Werte enthalten hier null Unentschieden.

| Gegner | V14 W/D/L | CONTROL W/D/L | Neu gewonnen / neu verloren auf gleichen Schlüsseln | Netto zusätzliche Siege | Beitrag zum Panelmittel |
|---|---:|---:|---:|---:|---:|
| Solution_92 | 94/0/6 | 95/0/5 | 3 / 2 | +1 | +0,17 pp |
| Quadrat-Solution | 93/0/7 | 94/0/6 | 3 / 2 | +1 | +0,17 pp |
| V3 | 86/0/14 | 90/0/10 | 8 / 4 | +4 | +0,67 pp |
| V7 | 82/0/18 | 76/0/24 | 10 / 16 | −6 | −1,00 pp |
| V10 | 68/0/32 | 86/0/14 | 26 / 8 | +18 | +3,00 pp |
| V13 | 51/0/49 | 62/0/38 | 29 / 18 | +11 | +1,83 pp |
| **Panel** | **474/0/126** | **503/0/97** | **79 / 50** | **+29** | **+4,83 pp** |

V10 und V13 liefern zusammen +29 Siege; V3/Solution/Quadrat liefern zusammen +6, die durch −6 gegen V7 aufgehoben werden. Deshalb tragen V10 und V13 netto den gesamten Mittelgewinn. Das ist eine **Zerlegung des Ergebnisses nach Gegnern**, keine kausale Erklärung des Verhaltens.

Das Mittel steigt von **79,00 auf 83,83 %**. Das bereits berechnete gepaarte Kartenintervall der Auswahl beträgt **+0,33 bis +9,33 pp**. Die 600 Spiele enthalten nur 50 gemeinsame Karten und sind nicht 600 unabhängige Karten; Ergebnisse verschiedener Seiten/Gegner derselben Karte hängen zusammen. Von diesen 50 Karten haben 25 einen positiven, 19 einen negativen und sechs einen netto unveränderten Panelbeitrag. Der Gewinn verteilt sich auf beide Seiten (+17 und +12 Siege).

Direkt gegen V14 gewinnt CONTROL **62/100** (62/0/38), Auswahlintervall **49–75 %**. Das erfüllt das vorab festgelegte Auswahlgate ≥50 %, belegt für sich allein aber keinen sicher über 50 % liegenden Direktvorteil. Gegen default bleiben beide bei 100/100. CONTROL ist damit gemäß Auswahlregeln nominiert; diese Zahlen sind **keine bestandene unabhängige Bestätigung**. `promotion_qualified` ist im Auswahlbericht false.

Das lokale Sechserpanel besteht aus Solution, Quadrat-Solution, V3, V7, V10 und V13. Sein Mittel ist ausdrücklich nicht Mahmouds früheres Panel mit `league_nets6` und `threat6`; 83,83 % hier darf nicht direkt mit dem alten historischen Sechsermittel verglichen werden.

## Was sich im Spiel deskriptiv verändert

Gleiche 600 Panel-Schlüssel, ohne default. Punkte/Sap/Endwissen sind Mittel je vollständigem Spiel über drei Matches. Wait/Stack sind über alle Unit-Schritte gewichtet; ihre Differenzen sind Prozentpunkte. Keine neuen Unsicherheitsintervalle oder Kausaltests für diese Begleitmetriken berechnet.

| Kennzahl | V14 | CONTROL | Veränderung |
|---|---:|---:|---:|
| Eigene Gesamtpunkte | 1239,68 | 1255,68 | +16,01 |
| Gegnerische Gesamtpunkte | 951,89 | 952,52 | +0,63 |
| Punktemarge | +287,79 | +303,16 | +15,38 |
| Sap-Aktionen je Spiel | 95,28 | 94,98 | −0,30 |
| Sap-Aktionen mit sichtbarem Gegner im Zielbereich | 80,81 | 80,56 | −0,25 |
| Anteil solcher Sap-Aktionen | 84,81 % | 84,82 % | +0,01 pp |
| Wait-Anteil | 46,34 % | 46,42 % | +0,08 pp |
| Stack-Anteil | 11,45 % | 11,35 % | −0,10 pp |
| Am Ende bekannte Punktefelder | 16,45 | 16,42 | −0,04 |

Das Gesamtbild liefert keinen klaren Hinweis auf mehr Saps, weniger Warten oder mehr entdeckte Punktefelder. Der geringere Stack-Anteil ist klein. Bekanntes Endwissen misst außerdem nicht, **wann** ein Punktefeld bewiesen wurde; schnelleres Erschließen lässt sich daraus weder nachweisen noch ausschließen.

Gerade beim größten Ergebnisbeitrag passen aggregierte Punkte nicht einfach zur Siegquote:

| Gegner | Änderung eigene Punkte | Änderung Gegnerpunkte | Änderung Punktemarge | Änderung Spielsiege |
|---|---:|---:|---:|---:|
| V10 | −16,18 | +14,42 | **−30,60** | **+18** |
| V13 | +44,16 | +27,14 | +17,02 | +11 |
| V7 | +34,82 | −25,34 | **+60,16** | **−6** |

Mehr Spielsiege gegen V10 entstehen also trotz schwächerer durchschnittlicher Gesamtpunktemarge; gegen V7 passiert das Gegenteil. Gewonnen wird über die Mehrzahl von drei Matches, nicht über die Summe aller Spielpunkte. Welche Matches knapper gewonnen oder höher verloren werden, müsste eine separate Match-/Zeitdiagnose zeigen. Die vorhandenen Gesamtwerte beweisen weder bessere Punktebesetzung noch gezielteres Kampfverhalten als Ursache.

`sap_hits` ist laut `scripts/metrics.py:10–11,78–86` eine Beobachtungsmetrik: Der 3×3-Zielbereich enthielt vor der Ausführung einen **sichtbaren** Gegner. Das ist kein Nachweis tatsächlich verursachten Schadens oder von Abschüssen und bewertet Nebel-Saps unvollständig. `wait_frac` misst STAY; Halten eines Punktefelds oder Energiesammeln kann sinnvoll sein. `stack_frac` zählt Unit-Schritte mit weiterer eigener Unit auf demselben Feld, nicht ausschließlich schädliches Stacking auf Punktefeldern.

## Warum DISCOVERY nicht nominiert ist

DISCOVERY erreicht gegen Solution **96/100 statt 94/100**, ist über das volle Panel aber **472/600 statt 474/600**, also **−0,33 pp**, und direkt gegen V14 **45/100**. Damit scheitern Panel- und Direktgate. Die bessere einzelne Solution-Zahl ersetzt die vorab festgelegten Robustheitsbedingungen nicht.

Rechnerisch: V10 +10, V7 +2 und Solution +2 zusätzliche Siege werden durch Quadrat-Solution −6, V13 −6 und V3 −4 überkompensiert. Endwissen steigt im Panel ebenfalls nicht (16,38 statt 16,45 bekannte Punktefelder); das belegt allerdings wie bei CONTROL keine Geschwindigkeit der Erkundung. „Stärkerer Entdeckungsreward führt zu besserer Erkundung und dadurch zu höheren Siegen“ ist durch diese Auswahl nicht gezeigt.

CONTROL verwendet den normalen Entdeckungsreward 0,5; DISCOVERY 2,0. Beide Kandidaten ergänzen V14 um je ein nachtrainiertes Netz (37 statt 36). Das ist ein gepaarter Pilot aus einem Ausgangsnetz, kein allgemeiner Methodenvergleich über mehrere Trainingsstarts. Gegenüber V14 ist zudem nicht isoliert, welcher Anteil eines CONTROL-Gewinns vom tatsächlichen Lernen und welcher von zusätzlichem Netz/anderer Ensemblegewichtung kommt: Ein ungeändert dupliziertes Startnetz als gleich großer 37er-Kontrollkandidat wurde hier nicht separat ausgewertet.

OVERLAP bleibt in der Auswahl bei 472/600 (−0,33 pp; zwei zusätzliche Niederlagen gegen V10), direkt 50 %. Sichere zusätzliche Informationsfakten aus der früheren Shadow-Diagnose garantieren somit keinen Spielstärkegewinn in diesem Auswahlsatz. Der getrennte Gauß-Prototyp war nicht Teil dieser Auswahl.

## Datenbeleg und Einordnung

Mit Python-Standardbibliothek nachgeprüft: je vier Panel-/Default-Dateien genau 700 eindeutige vollständige Schlüssel `(seed,side,opponent)`, exakt die geplanten Seeds 831000–831049 × beide Seiten × sieben Gegner; keine fehlenden/zusätzlichen/duplizierten Schlüssel. Alle Zeilen 303 Engine-Schritte und Punktezählung v2. Alle vier CSV-Hashes stimmen mit `selection_summary.json.csv_sha256` überein. CONTROL-/DISCOVERY-Direktdateien jeweils 100 eindeutige Seed-/Seiten-Schlüssel, ebenfalls hashgleich zum Summary. W/D/L, Gegenbeiträge und deskriptive Mittel aus den Rohzeilen unabhängig nachgezählt. Die Intervalle stammen unverändert aus dem abgeschlossenen Auswahlsummary.

Die Auswahl zwischen drei Kandidaten auf demselben kleinen Kartensatz kann den Gewinnerwert nach oben verzerren. Einzelgegner-Befunde und Begleitmetriken sind zusätzlich deskriptive Unterteilungen; die beobachtete Mischung aus Gewinn/Verlust gegen Gegner ist keine universelle Robustheitsgarantie. Deshalb bleibt die bereits laufende, vorher festgelegte unabhängige Bestätigung maßgeblich. Diese Interpretation liefert weder einen Zwischenstand daraus noch einen Anlass, währenddessen Quellen, Gewichte, Schwellen oder Kandidaten zu ändern.

## Kurze Fazitnachricht für Mahmoud

CONTROL ist der einzige Kandidat, der alle Auswahlbedingungen erfüllt: 503 statt 474 Siege im lokalen Sechserpanel (+4,83 pp), direkt 62/100 gegen V14. Der Nettogewinn kommt von V10 und V13; gegen V7 verliert er sechs Siege. Mehr oder bessere Erkundung/Saps sind als Ursache bisher nicht belegt. DISCOVERY schafft zwar 96 statt 94 Siege gegen Solution, fällt aber im Panel und Direktduell durch. Ob CONTROL wirklich besser ist, entscheidet die unabhängige Bestätigung; die Abgabe bleibt bis dahin V14.
