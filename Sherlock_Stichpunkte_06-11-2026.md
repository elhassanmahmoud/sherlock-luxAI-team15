# Sherlock – Battle Session (06.11.2026): Vortrag zum Üben

> **Beim Vortrag nichts ablesen.** Laut Bewertungsschema (Kursfolie 11) zählt, dass wir in eigenen Worten frei sprechen. Diese Datei ist zum **Üben**. Die **fett gedruckten Kernsätze** sollen frei sitzen; die Folien sind die Gedächtnisstütze.

**Stand 05.11.2026, nach der Kürzung vom 04.11. und einer Ergänzung am 05.11.** Der Vortrag erklärt den abgegebenen Agenten: Ziele, konkrete Merkmale, unterschiedliche Netze und Regeln vor beziehungsweise nach der Netzauswahl. Die lange Versions- und Fortschrittschronik bleibt weg. Weil die Aufgabe ausdrücklich „die neuesten Entwicklungen der letzten Woche“ verlangt, stehen V11–V14 und die Prüfungen vom 02.–04.11. kompakt auf der neuen **Folie 9**, jeweils mit dem Schritt im Ablauf, an dem sie eingreifen. Die Verteilung lautet jetzt: **Moayed 1–4 und 10, Mahmoud 5–9**. Abgabe bleibt **V14 mit 36 Netzen**. Folien: [Battle-PDF](Sherlock_Battle_06-11-2026.pdf), Quelle: [HTML](docs/presentation/Sherlock_Battle_06-11-2026.html).

| Wer | Folien | Planzeit |
|---|---|---:|
| Moayed | 1–4 · 10 | 4:35 |
| Mahmoud | 5–9 | 5:40 |
| **Gesamt** | **1–10** | **10:15** |

Die Zeiten enthalten kurze Zeigepausen und die Übergaben nach Folie 4 und 9; sie sind **keine gemessene Probe**. Folien 11–13 sind Reserve. *Kursiv in Klammern* = Übungshinweis, nicht sagen.

**Kernaussage:** **Sherlock sammelt Wissen, lässt 36 Netze Aktionen bewerten und koordiniert die Ausführung mit Regeln.**

**Publikum:** Kommilitoninnen und Kommilitonen. Spielregeln und DQN sind aus der Vorlesung bekannt. Unsere Begriffe und konkreten Entscheidungen erklären wir an Beispielen.

## Vor dem Vortrag

1. Die Agentenabgabe ist laut Moayeds Mitteilung bereits erledigt; der Moodle-Upload wurde hier nicht selbst eingesehen. Die Pfadangaben unten bleiben als Referenz erhalten.
2. Mit der aktuellen PDF üben. Zehn Hauptfolien, drei Reservefolien; die Neuerungen nur kompakt auf Folie 9, keine weitere Versionsgeschichte erzählen.
3. Zweimal mit Uhr proben, mit Übergabe **nach den 79 Merkmalen** an Mahmoud und **vor dem Battle-Abschluss** zurück an Moayed. Ziel etwa 10 Minuten (Plan 10:15). Bei Zeitdruck Zusatzdetails in die Fragerunde verschieben.

---

## Folie 1 – Sherlock
### Moayed · 0:30

- Hallo, wir sind Mahmoud und Moayed, Team 15. Unser Agent heißt Sherlock.
- **Sherlock verbindet Gedächtnis, 36 gelernte Netze und programmierte Regeln.** Wir zeigen ihr Zusammenspiel.
- Welche Ziele bekommen Einheiten, was sehen die Netze und wann greifen Regeln ein?

---

## Folie 2 – Entscheidungsablauf
### Moayed · 1:00

- *(Die Stationen nacheinander zeigen.)* Sherlock bekommt sichtbare Felder, Einheiten und den Punktestand. Punktefelder werden nicht direkt verraten.
- Zuerst aktualisiert das **Gedächtnis** das Kartenwissen. Dann werden den Einheiten **Ziele** zugeteilt.
- Aus Beobachtung, Gedächtnis und Ziel entstehen pro Einheit **79 Merkmale**. Auch Aktionsmaske und sichtbares Schussziel werden vorbereitet.
- Alle 36 Netze bewerten dieselben sechs Aktionen. Wir mitteln ihre Werte und wählen die beste Aktion, die nach der Maske übrig bleibt.
- Danach können **Regeln** die Auswahl verändern. Dann geht die Aktion ans Spiel.
- **Vor den Netzen wird vorbereitet; nach der Bewertung wird ausgewählt und korrigiert.**

---

## Folie 3 – Gedächtnis und Ziele
### Moayed · 1:15

- Sherlock kombiniert Beobachtungen wie ein Detektiv. Beispiel: Wir bekommen drei Punkte und besetzen vier Felder. Zwei davon kennen wir schon als Punktefelder. **Genau eines der beiden übrigen Felder bringt also einen Punkt.**
- Weitere Beobachtungen und die Spiegelsymmetrie helfen, offene Fälle aufzulösen. Relic- und Punktewissen bleibt über die drei Matches erhalten; Erkundungs- und Sichtzeitstempel werden beim Matchwechsel zurückgesetzt.
- **Das Ziel einer Einheit legt die programmierte Zielzuweisung fest.** Grundsätzlich kommen bekannte Punktefelder zuerst, dann mögliche Punktefelder und danach unbekannte Bereiche zur Erkundung.
- Bei der Verteilung zählt die begehbare Weglänge. Dadurch laufen Einheiten nicht einfach alle zum geometrisch nächsten Feld.
- Richtung und Abstand zum zugewiesenen Ziel gehen anschließend als Merkmale ins Netz. **Das Netz bewertet dazu die nächste Aktion.**

---

## Folie 4 – Die 79 Merkmale
### Moayed · 1:05

- **Jede Einheit bekommt in jedem Schritt ihren eigenen Vektor mit 79 Zahlen.** Alle Netze sehen für diese Einheit denselben Vektor.
- *(Tabelle zeigen.)* Zehn Werte beschreiben eigene Lage und Spielparameter, etwa Energie und Schussreichweite. Vier beschreiben den Punktestand.
- Zwanzig Werte beschreiben fünf Zielarten: jeweils Richtung, Abstand und ob das Ziel vorhanden ist. Darunter ist das zugewiesene Ziel.
- Fünf Werte beschreiben das aktuelle Feld. Dreißig beschreiben das eigene Feld und die vier Nachbarn, zum Beispiel Begehbarkeit, Energie und Punktewissen.
- Sechs Werte betreffen sichtbare Gegner, etwa Richtung, Energievergleich und Reichweite. Vier sind globale Zähler, etwa bekannte Punktefelder.
- **Die Merkmale ändern sich beim Spielen; die gelernten Gewichte bleiben fest.** Mahmoud erklärt jetzt die Netzbewertungen.

---

## Folie 5 – Das Ensemble
### Mahmoud · 1:25

- **Alle 36 Netze haben dieselbe Bauart, aber unterschiedliche gelernte Gewichte.** Jedes verarbeitet 79 Eingaben über zwei Schichten mit je 256 Neuronen. Der Dueling-Aufbau erzeugt sechs Aktionswerte.
- Die ursprünglichen 18 Netze lernten mit verschiedenen Zufallsstarts und Karten. Die Gegnermischungen unterschieden sich; eine Gruppe bestrafte gegnerische Punkte.
- Von jedem Original wurde eine Kopie jeweils 5.500 Spiele unter den damaligen V10-Regeln weitertrainiert. **Wir kombinieren also 18 Originale mit 18 weitergelernten Verwandten, keine 36 unabhängigen Neustarts.**
- Alle Netze bewerten jede Einheit, ohne feste Spezialrollen. Das Mitteln kann unterschiedliche Einzelfehler dämpfen, garantiert aber keinen besseren Zug.
- *(Beispiel zeigen.)* Hier bevorzugen 15 Netze „runter“, 12 „rechts“ und 9 „stehen“. Trotzdem gewinnt „rechts“ mit einem mittleren Q-Wert von 27,0 vor „runter“ mit 26,9.
- **Wir mitteln Bewertungen, nicht Stimmen.** Q-Werte schätzen den erwarteten zukünftigen Reward; sie sind keine Wahrscheinlichkeiten.

---

## Folie 6 – Training und Reward
### Mahmoud · 1:10

- **Gelernt wurde vor dem Battle. Im Spiel werden die Gewichte nur ausgewertet.** Das Gedächtnis sammelt weiter Informationen.
- Beim Training entstehen Erfahrungen aus Zustand, Aktion, Belohnung und Folgezustand. Der Replay Buffer speichert sie; das Netz lernt aus gemischten Stichproben.
- Double DQN trennt Auswahl und Bewertung im Lernziel: Das Online-Netz wählt die nächste Aktion, das Target-Netz bewertet sie.
- **Reward gibt es pro Schritt**, etwa fürs Halten von Punktefeldern, Veränderungen der Zielnähe und Erkundung. Tod bringt einen Abzug. Der Matchbonus kommt erst am Matchende.
- Die drei ursprünglichen Gruppen mit je sechs Netzen umfassen zusammen **66.000 Trainingsspiele**. Das Nachtraining der 18 Kopien umfasst **99.000 weitere Spiele**.
- Das ist das Herkunftsbudget dieser Netzfamilien; weitere Projektversuche zählen separat.

---

## Folie 7 – Action Masking
### Mahmoud · 1:00

- **Die Maske wird vor den Netzen vorbereitet und nach dem Q-Mittelwert angewandt.** Sie sperrt Aktionen für die Auswahl.
- Darin stehen Spielbedingungen und eigene Sicherheitsregeln: Bewegung braucht genügend Energie und ein begehbares Zielfeld; außerdem vermeiden wir bestimmte gefährliche Zusammenstöße. Für Sap braucht diese Netzauswahl ein geeignetes sichtbares Ziel.
- *(Beispiel zeigen.)* „Runter“ hat mit 53,8 den höchsten Q-Wert. Dort liegt aber ein Asteroid. Wir setzen diesen Aktionswert auf minus unendlich. „Rechts“ gewinnt mit 52,2.
- **Die Maske begrenzt die Auswahl.** Spätere Regeln können sie noch ändern. Ein späterer Blindschuss hat dafür eigene Prüfungen zu Ziel, Reichweite und Energie.

---

## Folie 8 – Regelkorrekturen
### Mahmoud · 1:25

- **Nach der maskierten Netzauswahl kann Sherlock Aktionen korrigieren.** Drei Beispiele:
- Erstens die **Wegkorrektur**: Ein Zug verkleinert den direkten Abstand zum bereits zugewiesenen Ziel, wegen eines Hindernisses aber nicht den begehbaren Weg. Dann nimmt Sherlock, falls möglich, den ersten Schritt eines kürzesten Wegs. *(Nur bei Nachfrage: Seitliche oder bewusst abgewandte Züge korrigiert diese Regel nicht automatisch.)*
- Zweitens der **Blindschuss**: Sherlock sieht den gegnerischen Punktezuwachs. Punkte, die keine sichtbare Einheit erklärt, deuten auf verdeckte Halter hin; die genauen Felder kennt es nicht sicher. Dann kann eine Regel **STAY zu SAP** ändern. Sie prüft Reichweite, Energiereserve und ob eine eigene Einheit auf dem Ziel steht. Die Einheit hält dabei ihr Punktefeld.
- Drittens der **Overkill-Schutz**: Mehrere Einheiten können Schüsse auf denselben Gegner planen. Sherlock berücksichtigt den bereits geplanten Schaden. Wird ein weiterer Schuss dadurch überflüssig, ändert es **SAP zu STAY**. Es nimmt nicht die zweitbeste Netzempfehlung.
- **Regeln können also Bewegung ändern, einen Schuss verhindern oder selbst auslösen.** Was davon seit letzter Woche neu ist, zeigt die nächste Folie.

---

## Folie 9 – Neu seit letzter Woche
### Mahmoud · 0:40

- **Seit letzter Woche kamen vier Versionen dazu. Jede greift an einer bestimmten Stelle unseres Ablaufs ein.**
- V11 verdoppelt die Netze auf 36, das ist Schritt 4. V12 bringt den Blindschuss, den ich gerade gezeigt habe, also eine Regel.
- V13 korrigiert die Nebel-Schätzung im Gedächtnis, damit Einheiten nicht mehr ohne Energie im Nebel feststecken. V14 lässt Einheiten ihre Kandidatenfelder gezielt testen, wenn 30 Schritte nach dem ersten Relic noch kein Punktefeld bekannt ist.
- Jede Version lag in ihrem eigenen Vergleich auf neuen Karten vor ihrer Vorgängerin; die Unterschiede sind teils klein. *(Zahlen zeigen, nicht vorlesen. Die Zeilen sind getrennte Messungen, keine durchgehende Kurve.)*
- **Vom 2. bis 4. November haben wir weitere Netze und Trainingsvarianten getestet. Keine war nachweislich besser, deshalb spielt im Battle V14.** Moayed zeigt zum Schluss, worauf wir im Battle achten.

---

## Folie 10 – Im Battle
### Moayed · 0:45

- **Sherlock arbeitet in drei Schritten: Wissen sammeln, Aktionen bewerten und die Ausführung koordinieren.**
- Im Battle achten wir darauf, wie Einheiten Ziele verteilen, Punktefelder halten und dabei schießen. Wenn trotz bekanntem Relic lange kein Punktefeld gefunden wird, testen sie gezielt Kandidaten.
- Unsere Abgabe erreichte in ihrer historischen Bestätigung **95,4 Prozent gegen Solution_92: 1.600 Spiele auf 800 neuen Karten, jeweils auf beiden Seiten.** Das ist ein gemessenes Ergebnis, kein Versprechen für jeden Gegner.
- Damit sind wir bereit fürs Battle. Danke!

---

## Reservefolie 11 – Trainingsdetails
### Mahmoud · nur bei Rückfragen

**Bauart je Netz:** 79 → 256 → 256 mit ReLU. Danach zwei Köpfe mit je 128 Neuronen: ein Zustandswert V und sechs Aktionsvorteile A. Zusammen: `Q(a) = V + A(a) − Mittelwert(A)`. Ein Netz hat 152.967 Parameter. Alle Einheiten teilen seine Gewichte; ihre Eingaben unterscheiden sich. Für die andere Spielseite wird die Karte in dieselbe kanonische Sicht gespiegelt.

| Ursprüngliche Gruppe | Netze | Spiele je Netz | Gegner nach den ersten 25 % gegen default |
|---|---:|---:|---|
| A | 6 | 3.000 | abwechselnd default und Solution_92 |
| B | 6 | 4.000 | 70 % Solution_92, Rest default |
| C | 6 | 4.000 | 60 % Solution_92, 20 % alte eigene Agenten, Rest default; zusätzliche Strafe für Gegnerpunkte |

Die 18 nachtrainierten Kopien lernten je 1.500 + 2.000 + 2.000 Spiele unter V10-Regeln. Gegner waren Solution_92 und zwei Varianten, eigene frühere Abgaben, default und ein Rush-Bot.

**Verfahren:** Double DQN, Huber-Loss, Replay Buffer mit 300.000 Übergängen, Batch 256, Lernrate 0,0003, γ = 0,99; Target-Kopie alle 500 Lernupdates. Ein Spiel umfasst viele Umgebungsschritte; ein Schritt erzeugt Erfahrungen mehrerer Einheiten. Spiele, Übergänge und Lernupdates deshalb auseinanderhalten.

## Reservefolie 12 – Prüfverfahren
### Mahmoud · nur bei Rückfragen

- Auf Entwicklungskarten werden Ideen verglichen. Die Auswahl nutzt neue Karten; für die Bestätigung folgt ein weiterer vorher zurückgehaltener Block. Umfang und Hürden werden vor den Ergebnissen festgelegt.
- Beide Spielseiten derselben Karte werden gemeinsam ausgewertet. Der gepaarte Bootstrap zieht ganze Karten, keine vermeintlich unabhängigen Einzelspiele.
- **V14 wurde ausdrücklich per Teamentscheidung übernommen, obwohl zwei Hürden verfehlt waren:** Panelgewinn +0,86 statt mindestens +1 Prozentpunkt; im Direktduell lag die untere Intervallgrenze bei 49,25 % statt über 50 %.
- Der Panelgewinn hatte ein Intervall von +0,48 bis +1,28 Prozentpunkten; alle sechs Gegner lagen im gemessenen Ergebnis im Plus. Das erklärt die Entscheidung, ersetzt aber keine bestandene automatische Prüfung.

## Reservefolie 13 – Spielregeln, die wir nutzen
### Moayed oder Mahmoud · nur bei Rückfragen

- Sap erreicht Ziele im ganzen Quadrat innerhalb der Reichweite und trifft mit geringerem oder gleichem Schaden auch die acht Nachbarfelder. Der zunächst verdeckte Streufaktor kann 0,25, 0,5 oder 1 sein.
- Bei Kollisionen zählt die Gesamtenergie beider Teams auf dem Feld; bei Gleichstand sterben beide. Benachbarte Gegner können zusätzlich Energie abziehen.
- Asteroiden und Nebel driften. Relics können in späteren Matches dazukommen, daher bleibt Erkundung wichtig.
- Punktefelder liegen im 5×5-Bereich um Relics. Die Grundwahrscheinlichkeit pro Feld beträgt 20 %. Bei überlappenden Relic-Bereichen wurde auf unseren Karten eine höhere Häufigkeit gemessen.
- Muster in der Relic-Lage und Häufigkeiten sind aus Kartenstatistiken abgeleitet; sie sind kein sicheres Wissen über eine einzelne Karte.

---

## Bei Fragen

**„Wer legt das Ziel fest – das Netz oder die Regeln?“**
Die programmierte Zielzuweisung. Sie priorisiert grundsätzlich Punktefelder, Kandidaten und Erkundung und berücksichtigt unter anderem begehbare Weglängen. Das Netz bekommt Richtung und Abstand dieses Ziels als Merkmale. Die spätere Wegkorrektur benutzt dasselbe zugewiesene Ziel; sie erfindet kein neues. Je nach Zielart und Situation können mehrere Einheiten dasselbe Ziel erhalten.

**„Was genau sind die 79 Merkmale?“**
10 eigene Lage/Spielparameter + 4 Punktestand + 20 Zielmerkmale + 5 aktuelles Feld + 30 Umgebung + 6 Gegner + 4 globale Zähler. Die fünf Zielarten sind nächstes Punktefeld, Kandidatenfeld, Relic, unbekanntes Feld und zugewiesenes Ziel. Jede liefert dx, dy, direkten Gitterabstand und ein Vorhandensein-Signal. Weglängen helfen bei der Zielzuweisung; der Zielabstand im Merkmalsvektor ist der Manhattan-Abstand.

**„Warum sind die Netze verschieden, wenn sie dieselbe Bauart haben?“**
Die Bauart legt Rechenschritte und Größen fest. Die Gewichte sind die im Training angepassten Zahlen. Andere Zufallsstarts, Karten, Gegner und teilweise Rewards erzeugen andere gelernte Gewichte und Bewertungen. Gleiche Architektur bedeutet deshalb nicht dieselbe Funktion.

**„Sind die nachtrainierten Kopien nur identische Duplikate?“**
Sie beginnen jeweils mit den Gewichten eines Originals und lernen dann weiter. Original und nachtrainierter Stand bleiben beide im Ensemble. Es sind verwandte Paare mit unterschiedlichen Trainingsständen, keine 36 unabhängigen Starts. 36 identische Kopien würden nach dem Mitteln genau dieselben Q-Werte wie ein einziges Netz liefern.

**„Was ist der Vorteil des Ensembles?“**
Wenn einzelne Netze unterschiedlich falsch liegen, kann das Mitteln diese Fehler dämpfen. Gemeinsame Fehler bleiben bestehen; viele Netze sind deshalb keine Garantie. Außerdem kostet das Ensemble mehr Rechenzeit als ein einzelnes Netz. Der Nutzen hängt von den konkreten trainierten Mitgliedern ab.

**„Hat jedes Netz eine feste Rolle?“**
Nein. Es gibt kein eigenes Netz nur für Angriff, Erkundung, eine Einheit, ein Match oder eine Spielseite. Alle 36 bewerten dieselben sechs Aktionen für jede Einheit. Die Einheit bekommt ihre eigene Situation als Eingabe, und die Bewertungen werden pro Aktion gemittelt.

**„Warum Mittelwert und keine Mehrheitswahl?“**
Der Mittelwert berücksichtigt die Höhe der Bewertungen. Eine Mehrheitswahl zählt nur, welche Aktion jedes Netz bevorzugt. Netze mit größeren Wertunterschieden können das Mittel stärker beeinflussen. Q-Werte sind geschätzte zukünftige Rewards, keine Sicherheit oder Wahrscheinlichkeit.

**„Ist jede Annäherung positiv und jedes besetzte Punktefeld belohnt?“**
Das Ziel-Shaping nutzt die diskontierte Potentialänderung γΦ(s′) − Φ(s), nicht nur „näher ist gut“. Außerdem werden Ziele neu zugewiesen und terminale Zustände gesondert behandelt. Beim Punktefeld erhält der ausgewählte Halter den positiven Anteil; zusätzliche gestapelte Einheiten können einen Abzug bekommen. Die Folie zeigt einzelne Reward-Anteile, nicht die gesamte Belohnung eines Schritts.

**„Was lernt Sherlock während des Battles?“**
Die Netzgewichte bleiben fest. Das Gedächtnis aktualisiert Karten- und Punktewissen und schätzt verdeckte Spielparameter aus Beobachtungen. Das ist Anpassung des Wissens, kein weiteres Training der Netze.

**„Ist das noch Reinforcement Learning, wenn Regeln eingreifen?“**
Ja. Die Aktionsbewertungen sind aus Erfahrungen und Rewards gelernt. Die Gesamtlösung ist ein hybrider Agent: Ziele, Merkmale, Maske und Korrekturen sind programmiert. Der Beitrag eines Netzes lässt sich deshalb nicht allein daran ablesen, wie oft eine spätere Regel die Aktion ändert.

**„Wie kann Sherlock schießen, wenn die Maske Sap gesperrt hat?“**
Die vorbereitete Maske gilt für die Netzauswahl; dort wird ein geeignetes sichtbares Schussziel benötigt. Danach kann eine Regel einen eigenen Schuss auslösen, etwa auf ein verdecktes Punktefeld. Dieser Pfad prüft seine eigenen Bedingungen, einschließlich Reichweite und Energiereserve. Die Spielregeln gelten weiterhin.

**„Weiß Sherlock dadurch genau, wo ein unsichtbarer Gegner steht?“**
Nein. Bekannte Punktefelder und nicht durch sichtbare Gegner erklärter Punktezuwachs deuten auf verdeckte Besetzungen hin. Sie verraten nicht eindeutig, welche einzelnen Felder besetzt sind. Der Blindschuss ist eine regelbasierte Entscheidung unter dieser Unsicherheit.

**„Nimmt Sherlock beim Overkill-Schutz die zweitbeste Aktion?“**
Nein. Wenn der bereits geplante Schaden einen weiteren Schuss überflüssig macht, wird SAP zu STAY. Die Netze wählen dafür nicht erneut.

**„Wie schätzt Sherlock den Streuschaden?“**
Es vergleicht beobachtete Energieverluste eigener Einheiten mit den möglichen Streufaktoren. Bestimmte Schussregeln werden erst aktiv, wenn die Schätzung ausreichend eindeutig ist. Sichtbare Schussziele werden auch anhand von Gegnerenergie und Streuwirkung bewertet.

**„Warum stehen Einheiten auf Punktefeldern still?“**
Punkte entstehen durch Besetzung. STAY erhält die Position; SAP ebenfalls, deshalb kann eine Einheit halten und schießen. Eine Bewegung auf ein anderes Punktefeld kann auch punkten. STAY ist also nicht grundsätzlich zum Punkten vorgeschrieben.

**„Bleibt das Gedächtnis immer erhalten?“**
Relic- und Punktewissen bleibt innerhalb eines Spiels über die drei Matches erhalten. Erkundungs- und Sichtzeitstempel werden beim Matchwechsel zurückgesetzt. Ein neues Spiel beginnt mit neuem Gedächtnis.

**„Woher kommt die Zahl 95,4 Prozent?“**
Aus der historischen V14-Bestätigung: 800 neue Karten auf beiden Seiten, also 1.600 Spiele gegen Solution_92, mit 95,44 % Siegen. Die Unsicherheit wurde über ganze Karten berechnet. Kleine spätere Diagnosen mit einzelnen 100-%-Ergebnissen ersetzen diesen Nachweis nicht.

**„Warum habt ihr V14 trotz verfehlter Hürden übernommen?“**
Das war eine dokumentierte Teamentscheidung. Der Panelgewinn von +0,86 Prozentpunkten lag unter der Mindesthürde von +1; im Direktduell lag die untere Intervallgrenze mit 49,25 % unter der verlangten Grenze von über 50 %. Das Panelintervall war positiv, und alle sechs Gegner lagen im gemessenen Ergebnis im Plus. Die Hürden wurden nicht nachträglich geändert.

**„Warum nicht mehr Netze, ein Einzelnetz oder PPO?“**
Solche Varianten wurden geprüft; keine belegte einen ausreichenden Gesamtvorteil als Ersatz für die Abgabe. Das gilt für unsere untersuchten Kandidaten und beweist keine allgemeine Grenze einer Methode. Deshalb präsentieren wir den tatsächlich abgegebenen Agenten.

**„Was ist der Orakel-Test?“**
Eine Diagnose mit wahren Relic- und Punktefeldern als Zusatzwissen, das im echten Spiel nicht verfügbar ist. Sie untersucht mögliche Informationsengpässe. Das Ergebnis ist weder ein einsetzbarer Agent noch eine garantierte erreichbare Siegquote.

---

## Moodle-Pfade – archivierte Referenz

Die Abgabe ist laut Moayeds Mitteilung bereits erfolgt. Diese Angaben sind die dokumentierte Referenz, keine erneute Upload- oder Bauanweisung.

```text
Gruppe 15 – Agent Sherlock (Mahmoud El-Hassan, Moayed Shawesh)

Datei: Gruppe15.zip
Pfad zur Agent-Klasse (act, update): Gruppe15.main.Agent_x
Pfad zum trainierten Agenten: Gruppe15/agent.pth (gleiche Datei für Player 0 und Player 1)

Zeile für Paths.csv: 15;Gruppe15.main.Agent_x;Gruppe15/agent.pth;Gruppe15/agent.pth
Bitte mit train=False starten. Der Ordner Gruppe15 kann unter agents/ oder in der Projektwurzel liegen.
```

## Belege

- Für diese Kürzung geprüfte [36 Netzgewichte und Herkunftsketten](docs/presentation/source/ENSEMBLE_BATTLE_0611_20261104.json); alle sind verschieden, die 18 Nachtrainingspartner sind mit ihren Originalen verwandt.

- Ablauf, Ziele, Merkmale, Maske und Regeln: [Präsentationsreview](docs/presentation/PRUEFUNG_BATTLE_0611_20261104.md), [quellengestützter Ablauf](experiments/analysis/final_battle_20261103/preflight/decision_flow_sources.md), [Agent](agents/sherlock/main.py), [Merkmale und Zielzuweisung](agents/sherlock/features.py), [Gedächtnis](agents/sherlock/belief.py), [Netzarchitektur](agents/sherlock/model.py) und [Konfiguration](agents/sherlock/config.py). Die [ältere Ablaufbeschreibung](Sherlock_Entscheidungsprozess.md) enthält historische Formulierungen; bei Abweichungen gelten der aktuelle Code und der Review.
- Reale Beispiele auf Folien **5 und 7**: [V11-Diagnose](experiments/analysis/decision_trace_20261030_v11.json), dieselben 36 Netze. Beide Beispiele betreffen Karte 690000, Schritt 114: Maske bei Einheit 0, Ensemble bei Einheit 2. Die Q-Werte sind gerundet.
- Trainingsherkunft für Folien **5, 6 und 11**: [V11-Übernahmebericht](experiments/analysis/release_20261030_v11/RELEASE.md), [Netzherkunft](Sherlock_Entscheidungsprozess.md#9-wie-die-18-netze-trainiert-wurden). 66.000 + 99.000 bezeichnet die Herkunftsbudgets dieser Familien, nicht alle Projektversuche.
- Historisches Ergebnis auf Folie **10** und Ausnahme auf Reservefolie **12**: [V14-Übernahmebericht](experiments/analysis/release_20261101_v14/RELEASE.md), [Teamentscheidungsmanifest](experiments/releases/20261101_v14_rescue.json). 800 Panelkarten 820000–820799; getrennte Direktkarten 821000–821399; Rohdaten `experiments/compare/battle/GF_*.csv`.
- Neuerungen auf Folie **9**: Übernahmeberichte [V11](experiments/analysis/release_20261030_v11/RELEASE.md), [V12](experiments/analysis/release_20261031_v12/RELEASE.md), [V13](experiments/analysis/release_20261101_v13/RELEASE.md) und [V14](experiments/analysis/release_20261101_v14/RELEASE.md); dieselben Zahlen in der Versionstabelle des [README](README.md). Je Zeile eigener gepaarter Vergleich gegen die Vorgängerversion auf frischen Karten (V11 806000–806799, V12 808000–808799, V13 nur Nebelabzug 25 auf 300 Karten 816000–817792, V14 820000–820799). Schritt im Ablauf aus `agents/sherlock/config.py` und `main.py` (`art_splash`, `sap_still_splash`, `fog_sap`, `splash_min_drop`, `est_censor`, `neb_cross`, `cand_rescue`). Schülerzahlen: [Aktionsschüler-Bericht](docs/AKTIONSSCHUELER_20261104.md), A2 und V14 je 38/40 gegen Solution, A2 direkt 14/40.
- Reservefolie **13**: [Arbeitsstand](docs/ARBEITSSTAND.md), 01.11., 11:35 und 12:19, Relic-/Punktefeldzählung auf 10.000 beziehungsweise 1.500 Karten; Tabellen `RELIC_P6` und `OVERLAP_POINT_P` in [features.py](agents/sherlock/features.py).
- FAQ zu weiteren Kandidaten: [Einzelnetz/42 Netze](docs/ABSCHLUSSBERICHT_20261104_NETZE.md), [Aktionsschüler](docs/AKTIONSSCHUELER_20261104.md), [Nachtraining mit Lehreranker](docs/A2_LEHRERANKER_20261104.md); weitere historische Befunde im [Arbeitsstand](docs/ARBEITSSTAND.md). Orakel-Diagnose: `experiments/compare/battle/O_v18r_full.csv` gegen `D_v18r*.csv`. Keine der dort beschriebenen experimentellen Varianten ersetzt V14.
