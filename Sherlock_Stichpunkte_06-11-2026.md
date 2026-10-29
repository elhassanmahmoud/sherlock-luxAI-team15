# Sherlock – Battle Session (06.11.2026): Vortrag zum Üben

> **Beim Vortrag nichts ablesen.** Laut Bewertungsschema (Kursfolie 11) zählt, dass wir in eigenen Worten frei sprechen. Diese Datei ist nur zum **Üben**. Ziel: Die **fett gedruckten Kernsätze** jeder Folie frei sagen können. Die Folie selbst ist die Gedächtnisstütze.

**Entwurf vom 29.10.2026** (Claude Code mit Mahmoud). Folien: `Sherlock_Battle_06-11-2026.pdf` im Projektordner, Quelle: `docs/presentation/Sherlock_Battle_06-11-2026.html`. Die Aufteilung ist ein Vorschlag, Moayed bitte einmal durchgehen.

| Wer | Folien | Zeit |
|---|---|---|
| Moayed | 1–5 · 10 · 12–13 | 5:10 |
| Mahmoud | 6–9 · 11 | 4:20 |
| **Gesamt** | | **9:30** (höchstens 10:00) |

Die Folien 14–16 sind Reserve für Fragen. *Kursiv in Klammern* = nur Hinweis, nicht sagen.

**Kernaussage:** **18 gelernte Netze entscheiden, Gedächtnis und Regeln helfen ihnen: 90 % gegen Solution_92.**

**Publikum:** Kommilitoninnen und Kommilitonen. Spielregeln und DQN kennen alle aus der Vorlesung, also nicht erklären. Unsere eigenen Begriffe (Gedächtnis, Maske, Ensemble) dagegen schon.

---

## Vor dem Vortrag

1. **Bis Mittwoch Nacht** `Gruppe15.zip` auf Moodle hochladen und die Pfade schicken (Text im Abschnitt „Für Moodle“ unten).
2. **Folie 11 aktualisieren**, falls bis zum 06.11. noch etwas Neues dazukommt. Der Prof will ausdrücklich die Entwicklungen der letzten Woche hören.
3. Zweimal mit Uhr proben. Ziel 9:30, damit Luft bleibt.

---

## Folie 1 – Sherlock
### Moayed · 0:20

- Hallo, wir sind Mahmoud und Moayed, Team 15. Unser Agent heißt Sherlock.
- **Sherlock gewinnt 90 % gegen Solution_92. Entscheiden tun 18 gelernte Netze, ein Gedächtnis und Regeln helfen ihnen.**
- Wir zeigen euch, wie ein Spielschritt abläuft, wie wir trainiert haben und was letzte Woche neu war.

---

## Folie 2 – Agenda
### Moayed · 0:15

- Erst, was Sherlock bekommt und zurückgibt. Dann einen Spielschritt im Detail und das Training.
- Danach der Weg auf 90 %, das Neue der letzten Woche und was wir gelernt haben.

---

## Folie 3 – Was Sherlock bekommt und zurückgibt
### Moayed · 0:45

- Sherlock bekommt in jedem Schritt nur, was es sieht: Einheiten, Felder, Relics und den Punktestand.
- **Was es nicht sieht: welche Felder Punkte bringen. Das muss es selbst herausfinden.**
- Zurück gibt es für jede der 16 Einheiten drei Zahlen: die Aktion und beim Schuss das Zielfeld.
- Ein Schritt dauert höchstens 11 Millisekunden.

---

## Folie 4 – Ein Spielschritt: wer macht was?
### Moayed · 1:00

- *(Von links nach rechts zeigen.)* Ein Schritt läuft in sechs Stufen ab.
- Gedächtnis, Ziele und Merkmale sind programmiert. Sie bereiten alles vor: 79 Zahlen pro Einheit.
- **Die eigentliche Entscheidung trifft Stufe 4: 18 trainierte Netze bewerten die 6 Aktionen.**
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
- Im Training gilt dieselbe Maske, für Zufallszüge und für das Lernziel. In jedem fünften Fall war die Lieblingsaktion der Netze verboten.

---

## Folie 7 – 18 Netze entscheiden gemeinsam
### Mahmoud · 0:50

- Die 18 Netze werden nicht auf Spiele verteilt. **Alle 18 bewerten jede Einheit in jedem Schritt, und wir mitteln ihre Q-Werte.**
- Jedes Netz ist ein Dueling-DQN mit zwei Schichten zu je 256 Neuronen.
- Ein Netz gilt für alle Einheiten und beide Seiten. Für Spieler 2 spiegeln wir die Karte.
- *(Beispiel rechts)* Hier waren die Netze uneinig: 8 wollten runter, 6 rechts. Der Mittelwert nimmt rechts, weil die Netze bei rechts sicherer waren.
- Warum 18? Einzelne Netze schwanken stark, der Mittelwert ist stabiler. 30 Netze waren nicht besser.

---

## Folie 8 – So wurden die 18 Netze trainiert
### Mahmoud · 1:00

- Trainiert haben wir mit Double DQN, Target-Netz und Replay Buffer.
- **Die Belohnung kommt in jedem Schritt für jede Einheit:** für Punktefelder, fürs Näherkommen ans Ziel, fürs Erkunden und für den Matchsieg. Für den Tod gibt es Abzug.
- *(Tabelle)* Drei Gruppen mit je 6 Netzen und verschiedenen Gegnern: anfangs default, dann vor allem Solution_92, in Gruppe C auch alte Versionen von uns selbst.
- Zusammen sind das 66.000 Trainingsspiele.

---

## Folie 9 – Das Netz entscheidet, Regeln sichern ab
### Mahmoud · 0:40

- Wie viel entscheiden die Netze wirklich? **92 % der Aktionen spielt Sherlock genau so, wie die Netze sie wollen.**
- Regeln greifen nur bei 7 % ein, zum Beispiel um schädlichen Nebel zu umgehen oder nicht zweimal auf denselben Gegner zu schießen.
- Nur mit einer einfachen Regel, ohne Netze, gewannen wir 3 % statt 38 %. Das Gelernte ist der Kern.

---

## Folie 10 – Von 47 % auf 90 % gegen Solution_92
### Moayed · 0:50

- *(Ersten Balken zeigen.)* Beim ersten Review waren wir bei 47 %.
- Bis 78 % halfen Training und Regeln: neu trainiert mit aktiven Regeln, 18 statt 6 Netze.
- **Danach half mehr Training nicht mehr. Den Rest bis 90 % brachte Fehlersuche.** Wir haben verlorene Spiele Schritt für Schritt mit dem wahren Spielzustand verglichen.
- Dabei haben wir drei Fehler gefunden: Die Karte im Gedächtnis war veraltet, Einheiten liefen in Sackgassen, und mehrere Einheiten schossen auf denselben Gegner.
- Die 18 Netze sind dabei dieselben geblieben.

---

## Folie 11 – Neu seit letzter Woche
### Mahmoud · 1:00  *(vor dem Vortrag auf den neuesten Stand bringen)*

- Im Battle spielen wir gegen eure Agents, nicht gegen Solution_92. Deshalb haben wir letzte Woche auf Robustheit trainiert.
- 6 neue Netze mit je 4.000 Spielen gegen eine gemischte Liga: Solution_92, eine Variante, die im ganzen Quadrat schießt, alte Sherlocks, default und ein Rush-Bot.
- **Ergebnis: nur +0,8 Punkte, unsere Hürde war +1,5. Also haben wir die neuen Netze nicht übernommen.**
- *(Tabelle rechts)* So stark ist die aktuelle Version gegen andere Spielweisen. Am schwersten ist Solution_92 mit Schüssen im ganzen Quadrat: 79 %.
- **Ein Tipp für alle:** Wir haben unsere Abgabe in der Original-Vorlage getestet. Liegt der Ordner unter agents/, stimmt der Gewichte-Pfad leicht nicht, und der Agent spielt dann ohne Fehlermeldung untrainiert. Das haben wir behoben. Prüft das bei euch auch.

---

## Folie 12 – Erkenntnisse
### Moayed · 0:50

- Drei Dinge haben wir gelernt.
- **Erstens: Das Gelernte trägt.** Ohne die Netze verlieren wir fast jedes Spiel.
- **Zweitens: Ab 78 % war nicht mehr das Training der Engpass, sondern Fehler in unserem Agenten.**
- **Drittens: Jede Idee auf neuen Karten prüfen.** Eine Energie-Korrektur sah in der Auswahl besser aus und war auf 1.600 neuen Spielen schlechter. Ohne diesen Test hätten wir sie eingebaut.

---

## Folie 13 – Fazit und Battle
### Moayed · 0:25

- **Kurz gesagt: Sherlock entscheidet gelernt und sichert programmiert ab.**
- Gleich im Battle könnt ihr darauf achten: Die Einheiten verteilen sich auf verschiedene Ziele, Einheiten auf Punktefeldern bleiben stehen und schießen nur auf stehende Gegner, und Sherlock umgeht schädlichen Nebel.
- Danke! Habt ihr Fragen?

---

## Bei Fragen

**„Ist das noch Reinforcement Learning, wenn Regeln eingreifen?“**
Ja. 92 % der Aktionen kommen unverändert aus den Netzen, Regeln ändern rund 7 %. Ohne Netze, nur mit einer einfachen Regel: 3 % statt 38 % gegen Solution_92.

**„Warum nicht PPO?“**
Haben wir probiert, das war auch die Empfehlung des Profs: CNN auf Kartenebenen, erst Nachahmung des Ensembles, dann PPO. Es erreichte die Netze (73,0 % gegen 73,25 %), war aber nicht besser. Deshalb bleibt das DQN-Ensemble.

**„Was sind die 79 Merkmale?“**
Eigene Lage und Spielparameter (10), Punktestand (4), Richtung und Abstand zu den nächsten Zielen (20), das aktuelle Feld (5), die vier Nachbarfelder und das eigene (30), der nächste Gegner (6), globale Zähler (4). Alle Werte liegen zwischen −1 und 1.

**„Warum Mittelwert und keine Mehrheitswahl?“**
Der Mittelwert berücksichtigt, wie sicher sich jedes Netz ist. In 8 % der Fälle entscheiden beide verschieden.

**„Koordinieren sich die Einheiten?“**
Ja, aber programmiert: Die Zielzuweisung gibt jeder Einheit ein eigenes Ziel, nach Weglänge. Beim Schuss wird geplanter Schaden geteilt, damit nicht mehrere auf einen schon sicher getroffenen Gegner schießen.

**„Warum stehen so viele Einheiten still?“**
Wer auf einem Punktefeld steht, muss stehen bleiben, um zu punkten. Rund die Hälfte aller Aktionen ist „stehen“.

**„Woher wisst ihr, dass 90 % stimmt?“**
800 neue Karten, beide Seiten, also 1.600 Spiele. Statistik mit gepaartem Bootstrap über ganze Karten (Reservefolie 14).

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

- Entscheidungsablauf, Maske, Ensemble, Regelanteile: `Sherlock_Entscheidungsprozess.md`, Messung `experiments/analysis/decision_trace_20261026.json` (10 Diagnosespiele, 36.258 Entscheidungen, kein Leistungsnachweis).
- 47 → 90 %: Übernahmeberichte `experiments/analysis/release_20261022_v7/RELEASE.md` und `release_20261022_v10/RELEASE.md`, Diagramm `docs/presentation/folie_2310_fortschritt.png`.
- Liga-Training und Robustheitstabelle: `docs/ARBEITSSTAND.md`, Eintrag 26.10., 21:50 (V10-Referenz auf 701000–701799, je 1.600 Spiele).
- Energie-Korrektur: `experiments/analysis/v10_mechanics_20261022/RESULTS.md` (Auswahl 367 statt 363 von 400, Bestätigung 89,81 % statt 90,50 %).
- Ladefehler und Abgabetest: `docs/ARBEITSSTAND.md`, Eintrag 29.10.
