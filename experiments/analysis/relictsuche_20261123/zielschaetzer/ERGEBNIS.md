# Die ersten Reliktorte lassen sich unterschiedlich gut absuchen

Auf 32 neuen Sicht-1-Karten vergab das Modell für die wirkliche erste Reliktlage im Mittel höhere Wahrscheinlichkeiten als eine gleichmäßige Verteilung, die erfolglose Sicht bereits berücksichtigt. Im bestbewerteten Viertel lagen **66,0 %** der wirklichen Paare gegenüber **30,6 %** beim Vergleichsmodell. Grundlage sind 94 öffentliche Beobachtungen aus unveränderten V16-Eröffnungen. Der Kandidat qualifiziert sich damit für den gemeinsamen Ganzspielvergleich. Ob die gewählte Route Sherlock tatsächlich früher ans Relikt bringt, blieb bei dieser Schattenprüfung offen. [Versuchsplan](PLAN.md) · [Alle Prüfsummen und Kennzahlen](sichtpruefung.json)

## Woher die Richtung kommt

Der Agent lernt aus 49.152 unabhängigen Karten des offiziellen Generators, wie häufig jede der 300 spiegelgleichen Erstpaarlagen auftritt. Vier tatsächliche Kurs-Resets reproduzierten beide Koordinaten, Punktfelddichte des jeweiligen Musters und Spawnzeit exakt. In den Trainingsmasken waren 20,04 % der Bits gesetzt. Auf 8.192 eigenen Prüfkarten traf das beste Viertel der gelernten Verteilung 53,23 % der Paare, die gleichmäßige Wahl physischer Felder 25,91 %. Der mittlere Logverlust sank von 5,695 auf 5,157. Diese Prüfung zählt Karten einmal, vor jeder Beobachtung. [Trainingsquelle und Messung](lernen.py) · [Häufigkeiten und Originalquellen](ort.json)

Im ersten Match kann das Paar in einer der ersten 50 öffentlichen Folgebeobachtungen erstmals aktiv sein. Sieht jemand ein Feld nach diesem Zeitpunkt ohne Relikt, scheidet die entsprechende Paarlage für diesen Aktivierungszeitpunkt aus. Fährt ein Schiff mit nichtnegativer Energie über ein Feld nahe einer vermuteten Lage und die eigene Punktzahl bleibt null, müsste das zugehörige Bit im Punktemuster leer sein. Das Modell zählt wiederholte Besuche desselben Feldes und seines Spiegelpartners für dasselbe Bit einmal. Es summiert anschließend über die 50 möglichen Zeitpunkte. Die Gegenrechnung enumerierte diese Rechnung ausdrücklich für alle 300 Paarlagen. [Implementierung](kandidat.py) · [Gegenrechnung](gegenrechnung.py)

Der Kandidat betrachtet Suchwege von vier, sechs oder acht Bewegungen. Er gewichtet die erreichbaren Reliktlagen mit der geschätzten Chance, sie bis zum Ende des Suchhorizonts sehen zu können. Bekannte Asteroiden sperren Wege, Nebel schwächt den erwarteten Blick auf Nachbarfelder. Nahe geplante Ziele anderer Schiffe erhalten weniger Gewicht. Ein ausgewähltes Schiff verfolgt bis zu drei Schritte desselben Plans, solange jeder Schritt frei und zulässig ist. Die Bewegungen anderer Schiffe bleiben die Originalbefehle. Von Zug 12 bis 94 ist die Suche bei Sichtweite eins möglich. V16 übernimmt beim ersten öffentlich sichtbaren Relikt oder ersten eigenen Punkt vollständig. Richtungswechsel des Gegners, unbekanntes Gelände und künftige Driften begrenzen die Vorhersage.

## Getrennte Prüfung auf V16-Verläufen

Für 32 weitere Sicht-1-Karten liefen beide Starts bis zur Beobachtung 80 gegen die originale Solution. Beide Kandidatensitze beobachteten jeweils den vom Original gefahrenen Verlauf. Die vier vorbestimmten Messzeitpunkte lieferten 56, 26, 10 und 2 Beobachtungen vor eigener erster Sicht und Gutschrift. 28 Karten trugen mindestens eine Beobachtung bei. Späte erfolglose Suchen sind in der Stichprobe entsprechend selten. [Alle 64 Sitzprotokolle](beobachtungen.jsonl.gz)

| Ortsmodell | Mittlerer Logverlust, kleiner ist besser | Tatsächliches Paar im besten Viertel |
|---|---:|---:|
| Gleiche Wahrscheinlichkeit je physischem Feld | 5,707 | 25,4 % |
| Gleichgewichtung mit Zeitpunkt der letzten Sicht | 5,667 | 30,6 % |
| Gelernte Häufigkeit mit Zeitpunkt der letzten Sicht | 5,028 | 64,9 % |
| Gelernte Häufigkeit, Sichtzeit und ausgebliebene eigene Punkte | **4,995** | **66,0 %** |

Beim Logverlust beträgt die Differenz des vollständigen Schätzers zur Gleichgewichtung mit Sichtzeit −0,671 (95-%-Kartenintervall −0,805 bis −0,534). Der zusätzliche Beitrag der ausgebliebenen Punkte ist mit −0,032 kleiner und unsicher (−0,075 bis +0,018). Je Ziehung blieben beide Starts und alle Zeitpunkte einer Karte zusammen. [Gegenrechnung und Kartenintervalle](gegenrechnung.json)

Bei 5.184 geprüften Teamentscheidungen schlug der Kandidat 994 abweichende Einzelbefehle auf 31 Karten vor. Davon entfielen 493 auf player_0 und 501 auf player_1. Über den gesamten Verlauf durfte nur dieselbe vorab festgelegte Schiffs-ID abweichen. Bei allen 994 Änderungen wurden der kanonische Befehl und der Schussmerker im Aktionsgedächtnis kontrolliert, ebenso der Weltbefehl bei vorhandenem Speichereintrag. Alle 3.634 Entscheidungen vor dem Zeitfenster oder nach Sicht beziehungsweise Gutschrift blieben identisch. Beim ersten Prüfkartenpaar reproduzierte eine zweite Original-ZIP-Instanz alle 2.592 Einzelbefehle des zugrunde liegenden V16. Für die hier geprüften Verläufe wurden keine Ganzspiele und keine Fortsetzungen mit abgeändertem Befehl gezählt.

## Eingefrorene Fassung

Der gemeinsame Runner lädt `create(side)` aus [kandidat.py](kandidat.py), dazu [ort.json](ort.json) und die [echte V16-Kurs-ZIP](../../../releases/20261117_sherlock_v16/agent.zip). Die originale Instanz steht in `.base`, tatsächlich geänderte Befehle in `.changes`. Die Modell- und Quellhashes stehen in der [Prüfung](sichtpruefung.json). Verwendet wurden Trainingsseeds 161100000–161149151, Ortsprüfseeds 161150000–161158191 und die ersten 32 Sicht-1-Karten ab 161180000 (letzte 161180103). Das Laufzeitmodell erhält ausschließlich die öffentliche Spielbeobachtung, die öffentliche Konfiguration sowie bereits darauf beruhende V16-Merkmale und Befehle.

Vor der ersten Leistungsmessung ergab eine separate technische Durchsicht, dass die [Vorfassung](vorpruefung/README.md) den Kundschafter während desselben Spiels austauschen konnte und V16s Aktionsgedächtnis die ursprüngliche Richtung behielt. Die korrigierte Fassung wurde auf denselben 64 Originalverläufen erneut geprüft. Es fanden insgesamt zwei Schattenprüfungen derselben 32 Karten statt. Die Zahlen in der Tabelle verwenden jede Position einmal.
