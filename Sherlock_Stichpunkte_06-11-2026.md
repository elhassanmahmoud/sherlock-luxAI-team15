# Sherlock – Battle Session (06.11.2026): Vortrag zum Üben

> **Beim Vortrag nichts ablesen.** Laut Bewertungsschema (Kursfolie 11) zählt, dass wir in eigenen Worten frei sprechen. Diese Datei ist nur zum **Üben**. Ziel: Die **fett gedruckten Kernsätze** jeder Folie frei sagen können. Die Folie selbst ist die Gedächtnisstütze.

**Stand 04.11.2026, nach dem Präsentationsreview.** Die Aufteilung ist verbindlich: Moayed übernimmt 1–5 und 12–13, Mahmoud 6–11. Abgabe bleibt **V14 mit 36 Netzen**. Folien: [Battle-PDF](Sherlock_Battle_06-11-2026.pdf), Quelle: [HTML](docs/presentation/Sherlock_Battle_06-11-2026.html). Fachliche Grundlage: [Review vom 04.11.](docs/presentation/PRUEFUNG_BATTLE_0611_20261104.md).

| Wer | Folien | Planzeit |
|---|---|---:|
| Moayed | 1–5 · 12–13 | 4:25 |
| Mahmoud | 6–11 | 5:25 |
| **Gesamt** | **1–13** | **9:50** |

Die Planzeiten enthalten kurze Zeigepausen und die beiden Übergaben; sie sind **keine gemessene Probe**. Die Folien 14–17 sind Reserve für Fragen. *Kursiv in Klammern* = nur Hinweis, nicht sagen.

**Kernaussage:** **Sherlock verbindet 36 gelernte Netze mit Gedächtnis und Regeln. V14 erreichte rund 95 % gegen Solution_92.**

**Publikum:** Kommilitoninnen und Kommilitonen. Spielregeln und DQN kennen alle aus der Vorlesung, also nicht erneut erklären. Unsere eigenen Begriffe (Gedächtnis, Maske, Ensemble) dagegen schon.

---

## Vor dem Vortrag

1. **Die Agentenabgabe ist laut Moayeds Mitteilung bereits erledigt.** Der Moodle-Upload wurde hier nicht selbst eingesehen. Die Pfadangaben unten bleiben nur als Referenz erhalten.
2. Mit der aktuellen PDF üben. Die Entwicklungen vom 02.–04.11. sind auf Folie 12 zusammengefasst; die abgegebene Version bleibt V14.
3. Zweimal mit Uhr proben, einschließlich Zeigepausen und Übergaben nach Folie 5 und 11. Ziel 9:50; bei Überschreitung Beispiele kürzen. Die Reserve gehört nicht in die zehn Minuten.

---

## Folie 1 – Sherlock
### Moayed · 0:20

- Hallo, wir sind Mahmoud und Moayed, Team 15. Unser Agent heißt Sherlock.
- **Sherlock verbindet 36 gelernte Netze mit Gedächtnis und Regeln. Unsere Abgabe V14 erreichte rund 95 % gegen Solution_92.**
- Wir zeigen euch den Ablauf, das Training und unsere letzten Verbesserungen.

---

## Folie 2 – Agenda
### Moayed · 0:15

- Erst zeigen wir, was Sherlock bekommt und wie daraus eine Aktion entsteht.
- Dann erklärt Mahmoud die Netze, das Training und die Entwicklung. Zum Schluss kommen unsere drei wichtigsten Erkenntnisse und das Battle.

---

## Folie 3 – Was Sherlock bekommt und zurückgibt
### Moayed · 0:45

- Sherlock bekommt in jedem Schritt sichtbare Einheiten, Felder und Relics sowie den Punktestand. Der Rest der Karte bleibt zunächst unbekannt.
- **Welche Felder Punkte bringen, wird nicht direkt verraten. Das muss Sherlock selbst herausfinden.**
- Zurück gibt es für jede der 16 Einheiten drei Zahlen: die Aktion und beim Schuss das Ziel.
- Im damaligen V14-Test dauerte ein Aufruf typischerweise etwa 5 und höchstens rund 12 Millisekunden. Das ist eine Messung auf unserem Testrechner.

---

## Folie 4 – Ein Spielschritt: wer macht was?
### Moayed · 1:00

- *(Die sechs Stationen nacheinander zeigen.)* Zuerst aktualisiert das **Gedächtnis** unser Wissen. Dann werden den Einheiten **Ziele** zugeteilt.
- Die **Vorbereitung** erstellt 79 Merkmale, die Aktionsmaske und ein mögliches sichtbares Schussziel.
- **Alle 36 Netze bewerten die sechs Aktionen. Ihre Bewertungen werden gemittelt.**
- Bei der **Auswahl** wird die vorbereitete Maske angewandt. Sherlock nimmt die beste verbleibende Aktion.
- Danach kommen die **Regeln**. Sie können die Aktion ändern, einen Schuss verhindern oder selbst auslösen. Für verdeckte Schussziele gibt es eigene Bedingungen.
- **Die gelernte Bewertung ist also ein Teil des gesamten Ablaufs.**

---

## Folie 5 – Gedächtnis: Welche Felder bringen Punkte?
### Moayed · 0:45

- Das Gedächtnis arbeitet wie ein Detektiv, daher der Name Sherlock.
- *(Auf die Tabelle zeigen.)* Wir bekommen 3 Punkte und besetzen 4 Felder. 2 kennen wir schon als Punktefelder. **Genau eines der beiden anderen bringt also einen Punkt.**
- Sherlock sammelt solche Gleichungen und nutzt die Spiegelsymmetrie der Karte.
- **Relic- und Punktewissen bleibt über die drei Matches erhalten.** Erkundungs- und Sichtzeitstempel werden beim Matchwechsel zurückgesetzt.
- Damit kennen wir Sherlocks Informationen. Mahmoud zeigt jetzt, wie daraus eine Aktion entsteht.

---

## Folie 6 – Action Masking
### Mahmoud · 0:50

- **Die Maske entfernt Aktionen vor der Auswahl.** Sie enthält Spielbedingungen und programmierte Sicherheitsregeln, etwa gegen gefährliche Zusammenstöße.
- *(Tabelle zeigen.)* Bewegung braucht genug Energie und ein Feld ohne Asteroid. Für die Netzauswahl braucht Sap ein geeignetes sichtbares Ziel.
- Technisch setzen wir gesperrte Aktionswerte auf minus unendlich.
- *(Beispiel rechts.)* Die höchste Bewertung hat „runter“, dort liegt aber ein Asteroid. **Die beste verbleibende Aktion ist „rechts“.**
- Im Training nutzen Zufallsaktionen und Lernziel die jeweilige Trainingsmaske. Spätere Regeln bleiben ein eigener Schritt: Ein verdeckter Schuss prüft eigene Bedingungen, auch wenn zuvor kein sichtbares Ziel vorlag.

---

## Folie 7 – 36 Netze entscheiden gemeinsam
### Mahmoud · 0:50

- **Alle 36 Netze bewerten jede Einheit in jedem Schritt. Wir mitteln ihre Q-Werte für jede Aktion.**
- Jedes ist ein Dueling-DQN mit zwei Schichten zu je 256 Neuronen. Ein Netz gilt für alle Einheiten und beide Seiten; für Spieler 2 spiegeln wir die Karte.
- *(Beispiel rechts.)* 15 Netze bevorzugen „runter“, 12 „rechts“, 9 „stehen“. Trotzdem gewinnt im Mittel „rechts“.
- **Q-Werte sind geschätzte Aktionswerte, keine Sicherheit oder Wahrscheinlichkeit.** Der Mittelwert berücksichtigt die Höhe der Bewertungen; eine Mehrheitswahl zählt nur Stimmen.
- Die 36 bestehen aus 18 ursprünglichen Netzen und 18 nachtrainierten Kopien.

---

## Folie 8 – So wurden die 36 Netze trainiert
### Mahmoud · 1:00

- Trainiert haben wir mit Double DQN, Target-Netz und Replay Buffer. Einheiten sammeln Erfahrungen, aus denen die Netze lernen.
- **Belohnungen werden pro Schritt berechnet:** etwa für Punktefelder, Annäherung ans Ziel und Erkundung; Tod bringt einen Abzug. Der Matchbonus kommt erst am Matchende.
- *(Tabelle zeigen.)* Die ursprünglichen 18 Netze stammen aus drei Gruppen mit je 6 Netzen: anfangs gegen default, dann vor allem gegen Solution_92, teils auch gegen ältere eigene Versionen.
- Diese Gruppen umfassen 66.000 Trainingsspiele. Kopien der 18 Netze wurden jeweils 5.500 Spiele **unter den V10-Regeln** weitertrainiert: weitere 99.000 Spiele.
- Das ist das Herkunftsbudget dieser Netzfamilien, nicht die Summe aller Projektversuche. Spätere Regeln kamen danach hinzu.

---

## Folie 9 – Netze und Regeln
### Mahmoud · 0:40

- **In zehn V12-Diagnosespielen entsprach die finale Aktion zu rund 91 % der maskierten Netzauswahl, ohne protokollierten Regeleingriff.** Regeln änderten rund 8 % der Aktionen.
- Das ist keine neue V14-Messung. Ziele, Merkmale und Maske waren bereits programmiert.
- Ein Beispiel: Der Overkill-Schutz ändert einen überflüssigen Schuss in „stehen“, nicht in die zweitbeste Netzempfehlung.

---

## Folie 10 – Von 47 % auf 95 % gegen Solution_92
### Mahmoud · 0:55

- *(Die Entwicklung von links nach rechts zeigen.)* Beim ersten Review lagen wir bei rund 47 %. Später kamen neue Trainingsstände, mehr Netze und gezielte Regelkorrekturen hinzu.
- **Mit denselben 18 Netzen stieg die gemessene Siegquote von etwa 78 auf 90 %.** Wir korrigierten unter anderem das Kartengedächtnis, Sackgassen und überflüssige Mehrfachschüsse.
- V11 kombinierte nachtrainierte Netze mit neuen Schussregeln. Danach folgten die Korrekturen bis V14 mit 95,4 %.
- Die Balken stammen aus verschiedenen Testblöcken. Sie zeigen unseren Fortschritt; die einzelnen Ursachen lassen sich daraus nicht vollständig voneinander trennen.

---

## Folie 11 – Neue Versionen
### Mahmoud · 1:10

- Vier Versionen wurden gegen ihre Vorgänger auf neuen Karten geprüft.
- **V11:** 36 Netze aus Originalen und Nachtraining unter V10-Regeln, dazu neue Schussregeln.
- **V12:** Aus gegnerischen Punkten werden verdeckte Besetzungen erschlossen; Sherlock kann auf solche Punktefelder schießen.
- **V13:** Die Schätzung des Nebelabzugs und das Durchqueren von Nebel wurden korrigiert.
- **V14:** Nach 30 Schritten ohne gefundenes Punktefeld bei bekanntem Relic testen Einheiten gezielt Kandidatenfelder.
- **V14 erreichte 95,44 % in 1.600 Spielen gegen Solution_92 und bleibt unsere Abgabe.**
- Moayed fasst jetzt unsere drei wichtigsten Erkenntnisse zusammen.

---

## Folie 12 – Erkenntnisse
### Moayed · 0:55

- **Erstens: Netze und Regeln ergänzen sich.** Die Netze bewerten Aktionen; Gedächtnis und Regeln helfen beim Entscheiden.
- **Zweitens: Neue Karten entscheiden.** Was auf bekannten Karten besser aussieht, muss sich auf neuen Karten erst bestätigen.
- **Drittens: Mehr ist nicht automatisch besser.** Vom 02. bis 04. November haben wir kleinere und größere Ensembles, Einzelnetz-Schüler und weiteres Nachtraining mit Lehrerbeispielen geprüft.
- **Kein Kandidat war ausreichend als Ersatz belegt. Deshalb bleibt V14.** Das gilt für unsere geprüften Varianten; andere Ansätze können künftig trotzdem besser werden.

---

## Folie 13 – Fazit und Battle
### Moayed · 0:25

- **Sherlock verbindet gelernte Bewertungen mit Gedächtnis und programmierten Regeln.**
- Im Battle könnt ihr darauf achten: Sherlock verteilt Einheiten auf Ziele, hält Punktefelder auch beim Schießen und sucht gezielt weiter, wenn Punktefelder lange fehlen.
- Unsere Abgabe bleibt V14 mit 36 Netzen. Danke! Habt ihr Fragen?

---

## Bei Fragen

**„Ist das noch Reinforcement Learning, wenn Regeln eingreifen?“**
Ja. Die Netze wurden aus Erfahrungen und Belohnungen trainiert und bewerten die Aktionen. In der historischen V12-Diagnose mit zehn Spielen entsprach die finale Aktion in 91,2 % der Fälle der maskierten Netzauswahl, ohne protokollierten Regeleingriff. Regeln änderten 8,3 % der Aktionen. Die beiden Diagnosegrößen ergänzen sich nicht exakt zu 100 %. Vorher wirken bereits programmierte Ziele, Merkmale und Maske. Die Zahlen beschreiben diese Diagnose, nicht jeden V14-Einsatz. Der alte Vergleich 3 % gegen 38 % betraf genau einen einfachen Regelersatz; er bewertet nicht regelbasierte Agenten allgemein.

**„Warum nicht PPO?“**
Wir haben einen CNN-/PPO-Ansatz mit Nachahmung des Ensembles ausprobiert. Im damaligen Vergleich erreichte er 73,0 % gegen 73,25 % und belegte keinen Vorteil. Deshalb wurde dieser Kandidat nicht übernommen. Daraus folgt keine allgemeine Aussage gegen PPO.

**„Was sind die 79 Merkmale?“**
Eigene Lage und Spielparameter (10), Punktestand (4), Richtung und Abstand zu den nächsten Zielen (20), das aktuelle Feld (5), die vier Nachbarfelder und das eigene (30), der nächste Gegner (6), globale Zähler (4).

**„Warum Mittelwert und keine Mehrheitswahl?“**
Der Mittelwert berücksichtigt, wie hoch jedes Netz eine Aktion bewertet. Die Mehrheitswahl zählt nur die bevorzugten Aktionen. Q-Werte sind geschätzte Aktionswerte, keine Wahrscheinlichkeiten oder Sicherheitsangaben. Netze mit größeren Wertunterschieden können den Mittelwert stärker beeinflussen.

**„Wie kann Sherlock schießen, wenn die Maske Sap gesperrt hat?“**
Die vorbereitete Maske gilt für die Netzauswahl. Dort wird ein geeignetes sichtbares Sap-Ziel benötigt. Danach können Regeln einen eigenen Schuss auslösen, etwa auf ein verdecktes Punktefeld. Dieser Pfad prüft seine eigenen Bedingungen wie Reichweite und Energiereserve. Die Spielregeln gelten weiterhin. Sichtbare Ziele werden anhand von Gegnerenergie und Streuwirkung bewertet; verdeckte Ziele nutzen einen eigenen Regelpfad.

**„Nimmt Sherlock beim Overkill-Schutz die zweitbeste Aktion?“**
Nein. Ist ein geplanter Sap nach der Schadensteilung überflüssig, wird er zu STAY, also Stehen. Das ist eine spätere Regelkorrektur, keine erneute Rangwahl der Netze.

**„Wie schätzt Sherlock den Streuschaden?“**
Ein Sap kann auch Einheiten auf den acht Nachbarfeldern treffen. Der Streufaktor ist zunächst unbekannt. Sherlock vergleicht beobachtete Energieverluste eigener Einheiten mit den möglichen Werten. Bestimmte Schussregeln werden erst aktiv, wenn die Schätzung ausreichend eindeutig ist.

**„Koordinieren sich die Einheiten?“**
Ja, über programmierte Zielzuweisung und geteilten geplanten Schussschaden. Bei der Zielwahl zählt unter anderem die Weglänge. Nicht jedes Ziel ist exklusiv: Je nach Zielart und Situation können mehrere Einheiten dasselbe Ziel erhalten. Der Overkill-Schutz verhindert bestimmte überflüssige Mehrfachschüsse.

**„Warum stehen so viele Einheiten still?“**
Punkte entstehen durch die Besetzung eines Punktefeldes. Stehen erhält diese Position; Sap ebenfalls, deshalb kann eine Einheit halten und schießen. Eine Bewegung auf ein anderes Punktefeld kann auch punkten. Man muss also nicht grundsätzlich die Aktion STAY wählen. In der historischen V12-Diagnose war etwa die Hälfte der Aktionen STAY.

**„Bleibt das Gedächtnis immer erhalten?“**
Relic- und Punktewissen bleibt innerhalb eines Spiels über die drei Matches erhalten. Erkundungs- und Sichtzeitstempel werden beim Matchwechsel zurückgesetzt. Ein neues Spiel beginnt mit neuem Gedächtnis. Die trainierten Gewichte bleiben beim Battle fest.

**„Woher wisst ihr, dass 95 % stimmt?“**
Die historische V14-Bestätigung nutzte 800 neue Karten auf beiden Seiten, also 1.600 Spiele gegen Solution_92: V14 95,44 %, V13 auf denselben Karten 94,94 %. Die Unsicherheit wurde mit gepaartem Bootstrap über ganze Karten berechnet. Die späteren 40/40 in einer kleinen separaten Diagnose ersetzen diesen Nachweis nicht und bedeuten keine garantierten 100 %. Details stehen auf Reservefolie 14.

**„Warum habt ihr V14 trotz verfehlter Hürden übernommen?“**
V14 verfehlte **zwei** Hürden: Im Mittel über sechs Gegner +0,86 statt mindestens +1 Prozentpunkt; im Direktduell lag die untere Intervallgrenze bei 49,25 % statt über 50 %. Der Panelgewinn hatte ein Intervall von +0,48 bis +1,28 Prozentpunkten, alle sechs Gegner lagen im gemessenen Ergebnis im Plus. Das Team entschied sich deshalb ausdrücklich für die Übernahme und dokumentierte die Ausnahme. Die Hürden wurden nicht geändert; die automatische Prüfung war nicht bestanden. Details stehen auf Reservefolie 14.

**„Was ist der Orakel-Test?“**
Eine reine Diagnose mit Zusatzwissen, das im echten Spiel nicht verfügbar ist: Sherlock erhält die wahren Relic- und Punktefelder. Im damaligen Test stieg das Mittel über sechs Gegner von 86,5 auf 91 %, bei Sichtweite 1 gegen Solution_92 von 85 auf 96,5 %. Das macht Information zu einem möglichen Verbesserungsansatz. Es ist kein einsetzbarer Agent und keine garantierte erreichbare Siegquote. Details stehen auf Reservefolie 17.

**„Warum trainiert ihr nicht einfach weiter oder nehmt mehr Netze?“**
Das haben wir in mehreren abgeschlossenen Studien geprüft. Vom 02.–04.11. gehörten kleinere Ensembles, ein 42-Netz-Ensemble, neu trainierte Einzelnetz-Schüler und weiteres Nachtraining dazu, zuletzt auch mit Lehrerbeispielen. Einzelne Ansätze verbesserten ihre jeweilige Kontrolle, aber kein Kandidat belegte einen ausreichenden Gesamtvorteil für einen V14-Ersatz. Die neu trainierten Netze bleiben experimentell. Das beweist weder, dass die Netze ausgereizt sind, noch dass mehr Training grundsätzlich nichts bringt.

**„Was ist ein Einzelnetz-Schüler?“**
Ein neu trainiertes einzelnes Netz lernt aus Beispielen des Ensembles. Der spätere Aktionsschüler A2 war deutlich besser als sein Ausgangsnetz S30. Auf einer kleinen frischen Diagnose erreichten A2 und V14 gegen Solution jeweils 38/40. Gegen das gesamte Gegnerfeld und im Direktvergleich belegte A2 aber keinen ausreichenden Vorteil. Gleich viele Siege in einem Teilvergleich reichen für den Abgabewechsel nicht.

**„Was war mit der Regel, die auf euren Karten +1,8 brachte?“**
Sie priorisierte wahrscheinliche Punktefelder. Auf 300 bekannten Entwicklungskarten wurde die beste von vier Varianten ausgewählt: dort +1,81 Prozentpunkte. Auf 800 neuen Karten lag sie bei −0,35 und wurde nicht übernommen. Die Auswahl auf bekannten Karten kann den dortigen Eindruck zu günstig machen; deshalb braucht es neue Karten.

**„Die Regel für 50 % Streuschaden lag knapp unter der Hürde. Warum ist sie in V12 drin?“**
Allein verfehlte sie die Hürde mit +0,95 statt +1,0 Prozentpunkten. Vor der nächsten Messung wurde V12 als Kombination aus dieser Regel und der Regel für verdeckte Schüsse festgelegt. Diese Kombination bestand die neue Prüfung mit +5,9 Prozentpunkten. Das gemeinsame Ergebnis trennt die Beiträge der beiden Änderungen nicht exakt.

**„Woher weiß Sherlock, wo unsichtbare Gegner stehen?“**
Es kennt einige Punktefelder und sieht den gegnerischen Punktezuwachs. Nicht durch sichtbare Einheiten erklärte Punkte sprechen für verdeckte Besetzungen. Daraus folgt nicht eindeutig, welche einzelnen Felder belegt sind. Sherlock prüft passende verdeckte Punktefelder in Reichweite und schießt unter eigenen Bedingungen, unter anderem ohne eigene Einheit auf dem Ziel und mit genügend Energiereserve.

**„Was war der Fehler in der Nebel-Regel?“**
Das Gedächtnis übernimmt Kartenwissen auch gespiegelt. Dadurch galten gegnerische Punktefelder als gesehen und leer, obwohl sie der Sensor gerade nicht zeigte. Die Regel für verdeckte Schüsse nutzt deshalb die tatsächliche aktuelle Sicht. Separat korrigierte V13 die Nebelabzugsschätzung bei Energie null und prüft die Energie für eine ganze Nebeldurchquerung.

**„Was ist ein Halter?“**
Eine eigene Einheit, die ein Punktefeld besetzt und hält.

---

## Moodle-Pfade – archivierte Referenz

Die Abgabe ist laut Moayeds Mitteilung bereits erfolgt. Diese Angaben sind nur die dokumentierte Referenz, keine erneute Upload- oder Bauanweisung.

```text
Gruppe 15 – Agent Sherlock (Mahmoud El-Hassan, Moayed Shawesh)

Datei: Gruppe15.zip
Pfad zur Agent-Klasse (act, update): Gruppe15.main.Agent_x
Pfad zum trainierten Agenten: Gruppe15/agent.pth (gleiche Datei für Player 0 und Player 1)

Zeile für Paths.csv: 15;Gruppe15.main.Agent_x;Gruppe15/agent.pth;Gruppe15/agent.pth
Bitte mit train=False starten. Der Ordner Gruppe15 kann unter agents/ oder in der Projektwurzel liegen.
```

---

## Belege

- Ablauf, Maske, Regeln und Gedächtnis: [Präsentationsreview](docs/presentation/PRUEFUNG_BATTLE_0611_20261104.md), [quellengestützter Ablauf](experiments/analysis/final_battle_20261103/preflight/decision_flow_sources.md), `agents/sherlock/main.py`, `belief.py`, `model.py`. Die [ältere Ablaufbeschreibung](Sherlock_Entscheidungsprozess.md) enthält historische Formulierungen; bei Abweichungen gelten der aktuelle Code und der Review.
- Historische Anteile auf Folie 9: [V12-Diagnose](experiments/analysis/decision_trace_20261031_v12.json), zehn Spiele auf fünf Karten, 36.204 Entscheidungen; kein Leistungsnachweis. Beispiele auf Folien 6/7 aus [V11-Diagnose](experiments/analysis/decision_trace_20261030_v11.json), dieselben 36 Netze. Alter Regelersatz 3 % gegen 38 %: [Arbeitsstand](docs/ARBEITSSTAND.md), 19.10.
- Trainingsherkunft: [V11-Übernahmebericht](experiments/analysis/release_20261030_v11/RELEASE.md) und Netzherkunft in [Entscheidungsprozess](Sherlock_Entscheidungsprozess.md). 66.000 + 99.000 bezeichnet die Herkunftsbudgets, nicht alle Projektversuche.
- Fortschritt auf Folie 10: Übernahmeberichte [V7](experiments/analysis/release_20261022_v7/RELEASE.md), [V10](experiments/analysis/release_20261022_v10/RELEASE.md), [V11](experiments/analysis/release_20261030_v11/RELEASE.md), [V12](experiments/analysis/release_20261031_v12/RELEASE.md), [V13](experiments/analysis/release_20261101_v13/RELEASE.md), [V14](experiments/analysis/release_20261101_v14/RELEASE.md). Diagramm: [PNG](docs/presentation/folie_0611_fortschritt.png), [Quelle](docs/presentation/source/fortschritt_0611.py). Jeweils eigene Testblöcke; keine isolierte Ursachenmessung durch die Balken.
- V13: 300 Karten mit Nebelabzug 25 (816000–817792), `experiments/compare/battle/GN_*.csv`. V14: 800 Panelkarten 820000–820799 und getrennte Direktkarten 821000–821399, `GF_*.csv`; [Übernahmebericht einschließlich beider verfehlter Hürden und damaliger Laufzeitmessung](experiments/analysis/release_20261101_v14/RELEASE.md), [Teamentscheidungsmanifest](experiments/releases/20261101_v14_rescue.json).
- Aktuelle Studien für Folie 12: [02.11.](docs/MORGENBERICHT_20261102.md), [03.11.](docs/MORGENBERICHT_20261103.md), [kleinere Ensembles und Nachtraining](docs/MORGENBERICHT_20261104.md), [Einzelnetz/42 Netze](docs/ABSCHLUSSBERICHT_20261104_NETZE.md), [Schüler-/Reward-Studie](docs/SCHUELERNETZ_REWARD_20261104.md), [Aktionsschüler](docs/AKTIONSSCHUELER_20261104.md), [Nachtraining mit Lehreranker](docs/A2_LEHRERANKER_20261104.md). Studien getrennt betrachten; keine ihrer experimentellen Varianten ersetzt V14.
- Neue Karten und Reserve: `v19cr` auf bekannten Dev-A-Karten `D_v19cr*.csv` (+1,81 pp), frisch auf 822000–823399 `GG_*.csv` (−0,35 pp). Orakel-Test: `experiments/compare/battle/O_v18r_full.csv` gegen `D_v18r*.csv`; [Arbeitsstand](docs/ARBEITSSTAND.md), 01.11.
- Reservefolie 16: Relic-/Punktefeldzählung auf 10.000 bzw. 1.500 Karten; Arbeitsstand 01.11., 11:35 und 12:19; Tabellen `RELIC_P6` und `OVERLAP_POINT_P` in `agents/sherlock/features.py`.
- Weitere historische Rückfragen: PPO-Vergleich, Mischung ohne neue Regeln und 50-%-Streuschaden in [Arbeitsstand](docs/ARBEITSSTAND.md) und `experiments/pipeline_battle_gate.log`. Ladefehler und damaliger Abgabetest: Arbeitsstand 29.10. Aktueller Abgabestatus nach Teammitteilung: jüngster Arbeitsstand 04.11.
