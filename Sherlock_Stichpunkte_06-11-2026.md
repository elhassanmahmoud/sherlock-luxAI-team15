# Sherlock – Battle Session (06.11.2026): Vortrag zum Üben

> **Beim Vortrag nichts ablesen.** Laut Bewertungsschema (Kursfolie 11) zählt, dass wir in eigenen Worten frei sprechen. Diese Datei ist nur zum **Üben**. Ziel: Die **fett gedruckten Kernsätze** jeder Folie frei sagen können. Die Folie selbst ist die Gedächtnisstütze.

**Entwurf vom 29.10.2026, am 30.10. auf die neue Abgabe V11 umgestellt** (Claude Code mit Mahmoud; geändert: Folien 1–4, 6–14, 16). **31.10.:** erst Folien 11, 12 und 14 um die knapp verfehlte Prüfung ergänzt, um 17:20 auf die neue Abgabe **V12** umgestellt (Folien 9 und 11–14, Sprechtext, Rückfragen, Belege). **01.11., 18:47:** auf die Abgabe **V14** umgestellt (Folien 1–3, 10–14, 16, neue Reservefolie 17 zum Orakel-Test; Sprechtext, Zeitplan, Rückfragen, Belege). Folien: `Sherlock_Battle_06-11-2026.pdf` im Projektordner, Quelle: `docs/presentation/Sherlock_Battle_06-11-2026.html`. Die Aufteilung ist ein Vorschlag, Moayed bitte einmal durchgehen.

| Wer | Folien | Zeit |
|---|---|---|
| Moayed | 1–5 · 10 · 12–13 | 5:20 |
| Mahmoud | 6–9 · 11 | 4:30 |
| **Gesamt** | | **9:50** (höchstens 10:00) |

Die Folien 14–17 sind Reserve für Fragen. *Kursiv in Klammern* = nur Hinweis, nicht sagen.

**Kernaussage:** **36 gelernte Netze entscheiden, Gedächtnis und Regeln helfen ihnen: 95 % gegen Solution_92.**

**Publikum:** Kommilitoninnen und Kommilitonen. Spielregeln und DQN kennen alle aus der Vorlesung, also nicht erklären. Unsere eigenen Begriffe (Gedächtnis, Maske, Ensemble) dagegen schon.

---

## Vor dem Vortrag

1. **Bis Mittwoch Nacht** `Gruppe15.zip` auf Moodle hochladen und die Pfade schicken (Text im Abschnitt „Für Moodle“ unten).
   Die Zip mit **V14** (gebaut am 01.11., 17:51) ist 22,2 MB groß. Lehnt Moodle die Größe ab, baut
   `python -m scripts.build_submission --battle --half` eine Fassung mit etwa 10,7 MB und demselben Namen. Gemessen wurde
   die volle Fassung; die halbe wich bei V12 in 3 Testspielen in 1 von 1.818 Zügen ab.
2. **Folie 11 aktualisieren**, falls bis zum 06.11. noch etwas Neues dazukommt. Der Prof will ausdrücklich die Entwicklungen der letzten Woche hören.
3. Zweimal mit Uhr proben. Ziel 9:50, damit Luft bleibt.

---

## Folie 1 – Sherlock
### Moayed · 0:20

- Hallo, wir sind Mahmoud und Moayed, Team 15. Unser Agent heißt Sherlock.
- **Sherlock gewinnt 95 % gegen Solution_92. Entscheiden tun 36 gelernte Netze, ein Gedächtnis und Regeln helfen ihnen.**
- Wir zeigen euch, wie ein Spielschritt abläuft, wie wir trainiert haben und was letzte Woche neu war.

---

## Folie 2 – Agenda
### Moayed · 0:15

- Erst, was Sherlock bekommt und zurückgibt. Dann einen Spielschritt im Detail und das Training.
- Danach der Weg auf 95 %, das Neue der letzten Woche und was wir gelernt haben.

---

## Folie 3 – Was Sherlock bekommt und zurückgibt
### Moayed · 0:45

- Sherlock bekommt in jedem Schritt nur, was es sieht: Einheiten, Felder, Relics und den Punktestand.
- **Was es nicht sieht: welche Felder Punkte bringen. Das muss es selbst herausfinden.**
- Zurück gibt es für jede der 16 Einheiten drei Zahlen: die Aktion und beim Schuss das Zielfeld.
- Ein Schritt dauert meist 5, höchstens 12 Millisekunden.

---

## Folie 4 – Ein Spielschritt: wer macht was?
### Moayed · 1:00

- *(Von links nach rechts zeigen.)* Ein Schritt läuft in sechs Stufen ab.
- Gedächtnis, Ziele und Merkmale sind programmiert. Sie bereiten alles vor: 79 Zahlen pro Einheit.
- **Die eigentliche Entscheidung trifft Stufe 4: 36 trainierte Netze bewerten die 6 Aktionen.**
- Danach streicht die Maske verbotene Aktionen, und Regeln korrigieren Fehler, die wir kennen.
- Ob geschossen wird, entscheidet das Netz. Wohin, rechnet eine Formel aus: dorthin, wo wir die meiste Gegnerenergie treffen.

---

## Folie 5 – Gedächtnis: Welche Felder bringen Punkte?
### Moayed · 0:45

- Das Gedächtnis arbeitet wie ein Detektiv, daher der Name Sherlock.
- *(Auf die Tabelle zeigen.)* Wir bekommen 3 Punkte und stehen auf 4 Feldern. 2 davon kennen wir schon als Punktefelder. **Also bringt genau eines der beiden anderen einen Punkt.**
- Solche Gleichungen sammeln wir, bis klar ist, welches Feld es ist.
- Die Karte ist spiegelsymmetrisch, ein Fund gilt also auch auf der Gegnerseite. Weil Asteroiden und Nebel wandern, verschiebt das Gedächtnis die Karte mit.

---

## Folie 6 – Action Masking: nur erlaubte Aktionen
### Mahmoud · 0:50

- **Action Masking heißt: Bevor gewählt wird, streichen wir alle Aktionen, die gerade nicht erlaubt oder sinnlos sind.**
- *(Tabelle)* Ein Zug geht nur mit genug Energie und ohne Asteroid. Ein Schuss geht nur, wenn ein Gegner in Reichweite ist.
- Technisch setzen wir den Q-Wert dieser Aktionen auf minus unendlich.
- *(Beispiel rechts)* **Die Netze wollten am liebsten nach unten, dort ist aber ein Asteroid. Also nimmt Sherlock die beste erlaubte Aktion: rechts.**
- Im Training gilt dieselbe Maske, für Zufallszüge und für das Lernziel. In gut jedem fünften Fall (22 %) war die Lieblingsaktion der Netze verboten.

---

## Folie 7 – 36 Netze entscheiden gemeinsam
### Mahmoud · 0:50

- Die 36 Netze werden nicht auf Spiele verteilt. **Alle 36 bewerten jede Einheit in jedem Schritt, und wir mitteln ihre Q-Werte.**
- Jedes Netz ist ein Dueling-DQN mit zwei Schichten zu je 256 Neuronen.
- Ein Netz gilt für alle Einheiten und beide Seiten. Für Spieler 2 spiegeln wir die Karte.
- *(Beispiel rechts)* Hier waren die Netze uneinig: 15 wollten runter, 12 rechts, 9 stehen bleiben. Der Mittelwert nimmt rechts, weil die Netze bei rechts sicherer waren.
- Warum 36? Es sind die 18 Netze vom 20.10. und dieselben 18 nach einem Nachtraining diese Woche. Gemischt sind sie besser als jede Hälfte allein. Mehr dazu auf Folie 11.

---

## Folie 8 – So wurden die 36 Netze trainiert
### Mahmoud · 1:00

- Trainiert haben wir mit Double DQN, Target-Netz und Replay Buffer.
- **Die Belohnung kommt in jedem Schritt für jede Einheit:** für Punktefelder, fürs Näherkommen ans Ziel, fürs Erkunden und für den Matchsieg. Für den Tod gibt es Abzug.
- *(Tabelle)* Drei Gruppen mit je 6 Netzen und verschiedenen Gegnern: anfangs default, dann vor allem Solution_92, in Gruppe C auch alte Versionen von uns selbst.
- Zusammen sind das 66.000 Trainingsspiele.
- Diese Woche haben wir Kopien der 18 Netze noch einmal je 5.500 Spiele weitertrainiert, jetzt mit allen heutigen Regeln. Das sind 99.000 Spiele mehr.

---

## Folie 9 – Das Netz entscheidet, Regeln sichern ab
### Mahmoud · 0:40

- Wie viel entscheiden die Netze wirklich? **91 % der Aktionen spielt Sherlock genau so, wie die Netze sie wollen.**
- Regeln greifen nur bei 8 % ein, zum Beispiel um schädlichen Nebel zu umgehen oder nicht zweimal auf denselben Gegner zu schießen.
- Nur mit einer einfachen Regel, ohne Netze, gewannen wir 3 % statt 38 %. Das Gelernte ist der Kern.

---

## Folie 10 – Von 47 % auf 95 % gegen Solution_92
### Moayed · 0:55

- *(Ersten Balken zeigen.)* Beim ersten Review waren wir bei 47 %.
- Bis 78 % halfen Training und Regeln: neu trainiert mit aktiven Regeln, 18 statt 6 Netze.
- **Von 78 auf 90 % brachte Fehlersuche, mit denselben 18 Netzen.** Wir haben verlorene Spiele Schritt für Schritt mit dem wahren Spielzustand verglichen und drei Fehler gefunden: Die Karte im Gedächtnis war veraltet, Einheiten liefen in Sackgassen, und mehrere Einheiten schossen auf denselben Gegner.
- Dann kam das Nachtraining unter den heutigen Regeln: 94 %.
- **Diese Woche ging es mit gezielten Korrekturen auf 95,4 %.** Das erklärt Mahmoud gleich auf Folie 11.

---

## Folie 11 – Neu seit letzter Woche: V11 bis V14
### Mahmoud · 1:10

- Diese Woche gab es vier neue Versionen. Jede haben wir auf neuen Karten gegen die vorige geprüft.
- *(V11)* **Die 18 Netze vom 20.10. kannten unsere späteren Regeln nicht.** Wir haben Kopien je 5.500 Spiele mit allen Regeln weitertrainiert und alt und neu gemischt, also 36 Netze. Gegen Solution_92 von 89,6 auf 94,1 %.
- *(V12, der größte Sprung)* **Bei Sichtweite 1 sieht man fast keinen Gegner. Sherlock sieht aber den Punktestand: Steigen die Gegnerpunkte, obwohl kein Gegner auf einem Punktefeld zu sehen ist, steht dort jemand unsichtbar. Dann schießt Sherlock auf ein verdecktes Punktefeld in Reichweite.** Im Mittel über 6 Gegner von 81 auf 87 %.
- *(V13)* Ein kleiner Fehler: Eine Einheit mit 0 Energie im Nebel verliert nichts mehr. Das sah für Sherlock aus wie „Nebel kostet nichts“, danach liefen alle hinein. Behoben; das wirkt nur auf Karten mit starkem Nebel, dort +2,4 Punkte.
- *(V14)* **Findet Sherlock 30 Schritte nach einem Relic noch kein Punktefeld, testen die Einheiten gezielt die Felder darum,** statt auf Energiefeldern zu warten. Gegen jeden der 6 Gegner besser, gegen Solution_92 95,4 %.
- **V14 ist unsere Abgabe für heute.**

---

## Folie 12 – Erkenntnisse
### Moayed · 0:55

- Vier Dinge haben wir gelernt.
- **Erstens: Das Gelernte trägt.** Ohne die Netze verlieren wir fast jedes Spiel.
- **Zweitens: Fehler suchen bringt mehr als weitertrainieren.** Fehlersuche brachte 78 → 90 % und mit V12 noch einmal 5,9 Punkte. Ein Nachtraining half einmal; ein zweites mit 24.000 Spielen brachte auf neuen Karten gar nichts mehr.
- **Drittens: Nur neue Karten zählen.** Eine Regel war auf unseren Entwicklungskarten 1,8 Punkte besser, auf 800 neuen Karten aber schlechter. **Ohne den Test auf neuen Karten hätten wir eine schlechtere Version abgegeben.** V14 lag knapp unter unserer Hürde, war aber in zwei Messungen und gegen jeden Gegner besser. Das haben wir bewusst als Team entschieden.
- **Viertens: Was noch fehlt, ist Information.** In einem Test haben wir Sherlock verraten, wo die Punktefelder liegen. Dann gewinnt es bei Sichtweite 1 96,5 statt 85 %. Da liegt die nächste Verbesserung.

---

## Folie 13 – Fazit und Battle
### Moayed · 0:25

- **Kurz gesagt: Sherlock entscheidet gelernt und sichert programmiert ab.**
- Gleich im Battle könnt ihr darauf achten: Die Einheiten verteilen sich auf verschiedene Ziele, Einheiten auf Punktefeldern bleiben stehen und schießen, bei kleiner Sicht auch auf Gegner, die sie gar nicht sehen, Sherlock umgeht schädlichen Nebel, und wenn lange kein Punktefeld gefunden ist, testen die Einheiten die Felder um das Relic.
- Danke! Habt ihr Fragen?

---

## Bei Fragen

**„Ist das noch Reinforcement Learning, wenn Regeln eingreifen?“**
Ja. 91 % der Aktionen kommen unverändert aus den Netzen, Regeln ändern rund 8 %. Ohne Netze, nur mit einer einfachen Regel: 3 % statt 38 % gegen Solution_92.

**„Warum nicht PPO?“**
Haben wir probiert, das war auch die Empfehlung des Profs: CNN auf Kartenebenen, erst Nachahmung des Ensembles, dann PPO. Es erreichte die Netze (73,0 % gegen 73,25 %), war aber nicht besser. Deshalb bleibt das DQN-Ensemble.

**„Was sind die 79 Merkmale?“**
Eigene Lage und Spielparameter (10), Punktestand (4), Richtung und Abstand zu den nächsten Zielen (20), das aktuelle Feld (5), die vier Nachbarfelder und das eigene (30), der nächste Gegner (6), globale Zähler (4). Alle Werte liegen zwischen −1 und 1.

**„Warum Mittelwert und keine Mehrheitswahl?“**
Der Mittelwert berücksichtigt, wie sicher sich jedes Netz ist. In 6 % der Fälle entscheiden beide verschieden.

**„Wie schätzt Sherlock den Streuschaden?“**
Trifft ein Sap ein Feld, verlieren Einheiten auf den 8 Nachbarfeldern 25, 50 oder 100 % der Sap-Kosten. Welcher Wert gilt, verrät das Spiel nicht. Sherlock vergleicht die Energieverluste der eigenen Einheiten mit den drei möglichen Werten, bis einer zu 90 % sicher ist. Meist ist das in Match 2 so weit. Fälschlich 100 % kam in unseren Tests nur ganz selten vor.

**„Koordinieren sich die Einheiten?“**
Ja, aber programmiert: Die Zielzuweisung gibt jeder Einheit ein eigenes Ziel, nach Weglänge. Beim Schuss wird geplanter Schaden geteilt, damit nicht mehrere auf einen schon sicher getroffenen Gegner schießen.

**„Warum stehen so viele Einheiten still?“**
Wer auf einem Punktefeld steht, muss stehen bleiben, um zu punkten. Rund die Hälfte aller Aktionen ist „stehen“.

**„Woher wisst ihr, dass 95 % stimmt?“**
800 neue Karten, beide Seiten, also 1.600 Spiele gegen Solution_92: V14 95,4 %, V13 auf denselben Karten 94,9 %. Davor V12 94,4 % und V11 94,1 %, jeweils auf eigenen neuen Karten. Statistik mit gepaartem Bootstrap über ganze Karten (Reservefolie 14).

**„Warum habt ihr V14 übernommen, obwohl es eure Hürde verfehlt hat?“**
Die Hürde war +1 Punkt im Mittel über 6 Gegner, V14 schaffte +0,86 (95-%-Intervall +0,48 bis +1,28). Schon auf den Entwicklungskarten war es +0,5, und auf den neuen Karten war es gegen jeden der 6 Gegner besser, gegen keinen schlechter. Deshalb haben wir als Team bewusst entschieden, es zu nehmen, und das so dokumentiert. Die Hürde selbst haben wir nicht verändert.

**„Was ist der Orakel-Test?“**
Eine reine Diagnose: Wir geben Sherlock im Test das wahre Wissen, wo Relics liegen und welche Felder Punkte bringen. Das hat im Spiel kein Agent. Im Mittel über 6 Gegner stieg die Siegquote von 86,5 auf 91 %, bei Sichtweite 1 gegen Solution_92 von 85 auf 96,5 %. So wissen wir, wo noch etwas zu holen ist (Reservefolie 17).

**„Warum trainiert ihr nicht einfach weiter?“**
Haben wir: 12 Netze je 2.000 Spiele unter allen heutigen Regeln, zusammen 24.000 Spiele. Auf 685 neuen Karten ohne starken Nebel: −0,07 Punkte, also nichts. Die Netze sind mit diesen Merkmalen ausgereizt; Fortschritt kam zuletzt aus Fehlersuche und gezielten Regeln.

**„Was war mit der Regel, die auf euren Karten +1,8 brachte?“**
Sie lässt die Einheiten zuerst die Felder testen, die am wahrscheinlichsten Punkte bringen. Wir haben sie auf unseren 300 Entwicklungskarten entwickelt und dort aus vier Varianten die beste gewählt. Dadurch sah sie dort zu gut aus. Auf 800 neuen Karten: −0,35. Nicht übernommen.

**„Die Regel für 50 % Streuschaden lag knapp unter der Hürde. Warum ist sie in V12 drin?“**
Allein verfehlte sie die Hürde knapp: +0,95 statt +1,0 Punkte, deshalb blieb V11. Vor der nächsten Messung haben wir festgelegt: V12 ist diese Regel plus die Nebel-Regel, einmal geprüft auf neuen, unbenutzten Karten und mit denselben Hürden. V12 bestand mit +5,9. Den größten Teil bringt die Nebel-Regel, allein brachte sie in der Entwicklung +2,8.

**„Woher weiß Sherlock, wo unsichtbare Gegner stehen?“**
Sherlock kennt die Punktefelder aus dem Gedächtnis und sieht den Punktestand des Gegners. Steigt der um 3, aber nur 1 Gegner steht sichtbar auf einem Punktefeld, stehen 2 unsichtbar auf Punktefeldern. Sherlock schießt dann auf ein Punktefeld in Reichweite, das gerade nicht im Sichtfeld liegt und auf dem keine eigene Einheit steht. Der Schütze bleibt dabei auf seinem Feld stehen und punktet weiter. Geschossen wird nur mit genug Energiereserve.

**„Was war der Fehler in der Nebel-Regel?“**
Die Karte ist spiegelsymmetrisch, deshalb trägt das Gedächtnis alles Gesehene auch gespiegelt ein, auch als „gesehen“. Die gegnerischen Punktefelder sind genau das Spiegelbild unserer. Sie galten deshalb als gesehen und leer, und die Regel schoss fast nie. Jetzt zählt nur, was der Sensor in diesem Schritt wirklich zeigt.

**„Was ist ein Halter?“**
Eine eigene Einheit, die auf einem Punktefeld steht und es hält.

---

## Für Moodle (zum Kopieren)

```
Gruppe 15 – Agent Sherlock (Mahmoud El-Hassan, Moayed Shawesh)

Datei: Gruppe15.zip
Pfad zur Agent-Klasse (act, update): Gruppe15.main.Agent_x
Pfad zum trainierten Agenten: Gruppe15/agent.pth (gleiche Datei für Player 0 und Player 1)

Zeile für Paths.csv: 15;Gruppe15.main.Agent_x;Gruppe15/agent.pth;Gruppe15/agent.pth
Bitte mit train=False starten. Der Ordner Gruppe15 kann unter agents/ oder in der Projektwurzel liegen.
```

---

## Belege

- Entscheidungsablauf, Maske, Ensemble, Regelanteile: `Sherlock_Entscheidungsprozess.md`, Messung für V12 `experiments/analysis/decision_trace_20261031_v12.json` (dieselben 10 Diagnosespiele wie am 26.10., 36.204 Entscheidungen, kein Leistungsnachweis; V11: `decision_trace_20261030_v11.json`, daraus die Beispiele auf Folie 6 und 7 mit denselben Netzen; V10: `decision_trace_20261026.json`).
- 47 → 95 %: Übernahmeberichte `experiments/analysis/release_20261022_v7/RELEASE.md`, `release_20261022_v10/RELEASE.md`, `release_20261030_v11/RELEASE.md`, `release_20261031_v12/RELEASE.md`, `release_20261101_v13/RELEASE.md` und `release_20261101_v14/RELEASE.md`, Diagramm `docs/presentation/folie_0611_fortschritt.png` (Quelle `docs/presentation/source/fortschritt_0611.py`).
- Folie 11, V13: gezielte Bestätigung auf 300 Karten mit Nebelabzug 25 (816000–817792), Daten `experiments/compare/battle/GN_*.csv`; V14: Battle-Bestätigung auf 820000–821399, Daten `GF_*.csv`, Teamentscheidung im Manifest `experiments/releases/20261101_v14_rescue.json`.
- Folie 12, Punkt 2: Runde 6 (`v17a`) auf 813200–814399, Daten `GE_*.csv`, nach Nebelabzug getrennt im Arbeitsstand 01.11., 10:55. Punkt 3: `v19cr` auf Dev A `D_v19cr*.csv` (+1,81) und neu auf 822000–823399 `GG_*.csv` (−0,35). Punkt 4 und Reservefolie 17: Orakel-Test `experiments/compare/battle/O_v18r_full.csv` gegen `D_v18r*.csv`.
- Reservefolie 16, Lage der Relics und Punktefelder: Zählung auf 10.000 bzw. 1.500 Karten, Arbeitsstand 01.11., 11:35 und 12:19; Tabelle `RELIC_P6` und `OVERLAP_POINT_P` in `agents/sherlock/features.py`.
- Folie 11, V11: Bestätigung Runde 2 (806000–806799, je Gegner 1.600 Spiele) in `experiments/pipeline_battle_gate.log`; Arbeitsstand 30.10.
- Folie 11, V12: Battle-Bestätigung auf 808000–809199 in `experiments/pipeline_battle_gate.log`, Daten `experiments/compare/battle/GC_*.csv`, Tabelle nach Sichtweite mit `experiments/analysis/battle_params_20261030/map_params.csv`; Schwachstelle Sicht 1 und Fehler: Arbeitsstand 31.10., 14:40; Ergebnis: Arbeitsstand 31.10., 17:15 und Übernahmebericht.
- Mischung ohne neue Regeln (+1,8 statt +2): Bestätigung Runde 1 von `mix36b` in `experiments/pipeline_battle_gate.log`, Arbeitsstand 30.10., 05:35.
- Regel für 50 % Streuschaden (`v11h`, +0,95 statt +1,0): Battle-Bestätigung auf 810400–811599 in `experiments/pipeline_battle_gate.log`, Daten `experiments/compare/battle/GB_*.csv`, nach Streufaktor mit `experiments/analysis/battle_params_20261030/map_params_810400.csv`; Arbeitsstand 31.10., 01:05.
- Ladefehler und Abgabetest: `docs/ARBEITSSTAND.md`, Eintrag 29.10.
