# Sherlock – Vortrag zum Üben (16.10.2026)

> **Wichtig:** Der Prof verlangt freies Sprechen – **beim Vortrag nichts ablesen** (kein Papier, kein Handy, kein Bildschirm). Diese Datei ist zum **Üben**. Ziel: Pro Folie die **fett gedruckten Kernsätze** frei sagen können; die Folie selbst ist eure Gedächtnisstütze.

| Wer | Folien | Zeit |
|---|---|---|
| Moayed | 1, 2, 3, 4 · 9, 10 · 12 | 5:35 |
| Mahmoud | 5, 6, 7, 8 · 11 | 5:35 |
| **Gesamt** | | **11:10** (höchstens 12) |

Jeder Punkt ist ein Satz, den man beim Üben so sagen kann. *Kursiv in Klammern* = nur Hinweis, nicht vorlesen.

**Inhalt:** Vortrag (Folien 1–12) · Bei Fragen · Unser Projekt einfach erklärt · Wörterbuch

---

## Folie 1 – Sherlock
### Moayed · 0:30

- Hallo, wir sind Mahmoud und Moayed, Team 15.
- Unser Agent heißt Sherlock und spielt Lux AI Season 3.
- Sherlock verbindet zwei Dinge: Er lernt mit Double DQN, und er hat ein Gedächtnis für die Karte.

---

## Folie 2 – Agenda
### Moayed · 0:20

- Zuerst erklären wir die Spielidee und den Aufbau unseres Agenten.
- Danach geht es um Merkmale, Netz und Lernverfahren.
- Dann zeigen wir Training und Auswertung.
- Zum Schluss kommen Ergebnisse, ein Spielbeispiel und unsere nächsten Schritte.

---

## Folie 3 – Spielidee und Ziel
### Moayed · 1:00

- Lux AI spielt auf einer Karte mit 24 mal 24 Feldern.
- Jedes Team steuert bis zu 16 Einheiten.
- Im Kurs hat ein Spiel drei Matches. Wer mehr Matches gewinnt, gewinnt das Spiel.
- Punkte bekommt man, wenn eigene Einheiten auf bestimmten Punktefeldern stehen.
- Das Schwierige: Der Agent sieht nicht die ganze Karte, und die Punktefelder sind unsichtbar.
- Außerdem ist die Energie der Einheiten begrenzt.
- Der Agent muss also erkunden, Energie einteilen und die Punktefelder finden und besetzen.
- **Genau deshalb braucht er ein Gedächtnis.**
- *(aufs Bild zeigen)* Sherlock ist blau, der Gegner rot. Gelb sind Relics und Punktefelder.
- Das ist die Zuschauer-Ansicht. Der Agent selbst sieht nicht alles.

---

## Folie 4 – Unser Agent
### Moayed · 0:55

- Unser Agent arbeitet in drei Schritten: Merken, Bewerten, Handeln.
- **Merken:** In jedem Spielschritt kommen die neuen Beobachtungen ins Gedächtnis.
- **Bewerten:** Für jede Einheit berechnen wir 79 Merkmale.
- Sechs Netze bewerten damit die möglichen Aktionen, und wir nehmen den Mittelwert.
- **Handeln:** Jede Einheit führt die beste erlaubte Aktion aus.
- *(auf den Pseudocode zeigen)* Rechts seht ihr genau diesen Ablauf als Pseudocode.
- Das Gedächtnis folgt festen Regeln. Die Bewertung der Aktionen ist gelernt.
- Beim Spielen lernt der Agent nicht mehr. Die Gewichte sind fest.
- **Übergabe:** „Mahmoud erklärt jetzt, welche Informationen in die Netze gehen und wie das Training funktioniert.“

---

## Folie 5 – Merkmale und Gedächtnis
### Mahmoud · 1:05

- Jede Einheit wird durch 79 Zahlen beschrieben, die Merkmale.
- Das Netz bekommt also kein Bild der Karte, sondern eine Liste von Zahlen.
- *(auf die Tabelle zeigen)* Die Merkmale haben vier Gruppen: die eigene Einheit, die Umgebung mit dem Gedächtnis, Ziele und Gegner sowie der Spielstand.
- Das Gedächtnis nennen wir Belief. Es merkt sich gesehene Relics, erkundete Gebiete und bewiesene Punktefelder.
- Ein Beispiel: Eine Einheit steht auf einem unbekannten Feld, und unsere Punkte steigen um eins.
- Dann wissen wir: Dieses Feld ist ein Punktefeld.
- Stehen mehrere Einheiten auf unbekannten Feldern, brauchen wir weitere Beobachtungen.
- Außerdem ist die Karte spiegelsymmetrisch. Was wir auf einer Seite wissen, gilt gespiegelt auch auf der anderen.
- Diese Regeln liefern nur Informationen. **Die Entscheidung trifft das gelernte Netz.**

---

## Folie 6 – Netzarchitektur und Ensemble
### Mahmoud · 1:05

- Jedes unserer Netze bekommt die 79 Merkmale.
- Dann folgen zwei Schichten mit je 256 Neuronen.
- Danach teilt sich das Netz in zwei Köpfe. Das nennt man Dueling.
- Der erste Kopf schätzt: Wie gut ist die Lage insgesamt?
- Der zweite schätzt: Wie viel besser ist jede einzelne Aktion?
- Zusammen ergibt das sechs Q-Werte, einen pro Aktion.
- Die sechs Aktionen sind: stehen bleiben, vier Richtungen und Sap, also ein Schuss auf Gegner.
- Wir benutzen sechs solche Netze, drei davon mit Symmetrie trainiert.
- Wir mitteln ihre Q-Werte, sperren unerlaubte Aktionen und nehmen die beste.
- Kurz zu den Begriffen: Double DQN ist das Lernverfahren, Dueling die Architektur, und Ensemble ist die Kombination der Netze.

---

## Folie 7 – Double DQN
### Mahmoud · 1:15

- Jetzt zum Training.
- Wir sammeln für jede Einheit Erfahrungen: Situation, Aktion, Belohnung und nächste Situation.
- Diese Erfahrungen kommen in einen Speicher, den Replay Buffer.
- Gelernt wird mit zufälligen Paketen von 256 Erfahrungen, nicht nur mit den letzten Zügen.
- **Der Kern von Double DQN: Das Online-Netz wählt die beste nächste Aktion. Das Target-Netz bewertet sie.**
- Dadurch überschätzt das Netz seine eigenen Werte weniger.
- Das Lernziel ist: Belohnung plus Gamma mal der Wert der nächsten Situation.
- Im letzten Schritt zählt nur die Belohnung.
- Alle 500 Updates kopieren wir das Online-Netz ins Target-Netz.
- Die Belohnung besteht aus Punkten, Matchsiegen und Zusatzsignalen, zum Beispiel für Annäherung ans Ziel, Erkundung und Energie.

---

## Folie 8 – Training und Auswertung
### Mahmoud · 1:05

- Wir haben sechs Trainingsläufe mit je 3.000 Spielen gemacht, zusammen 18.000 Spiele.
- Zuerst haben wir gegen default trainiert, danach abwechselnd gegen default und Solution_92.
- Den besten Zwischenstand wählen wir auf eigenen Validierungskarten aus.
- *(rechte Tabelle zeigen)* Die wichtigsten Einstellungen: Lernrate 0,0003, Gamma 0,99, Batch 256 und ein Buffer mit 300.000 Erfahrungen.
- Epsilon steuert das Ausprobieren.
- Am Anfang wählt der Agent immer zufällig, am Ende nur noch in 5 Prozent der Fälle.
- Das sinkt über 60.000 Schritte.
- In der Auswertung spielen wir beide Seiten, ohne Zufall und ohne Lernen.
- **Übergabe:** „Damit steht unser Agent fest. Moayed zeigt jetzt, wie er abschneidet.“

---

## Folie 9 – Benchmark-Ergebnisse
### Moayed · 1:05

*(Zeit prüfen: Ihr solltet hier bei etwa 7:15 sein. Seid ihr schon bei 8:00, Folie 10 kürzer machen.)*

- Jetzt zu den Ergebnissen.
- Gegen den Gegner default hat Sherlock **alle 60 Spiele** gewonnen.
- Gegen Solution_92, einen starken regelbasierten Bot, waren es **28 von 60**. Das sind etwa 47 Prozent.
- Wir haben pro Gegner 30 Karten gespielt, jede Karte auf beiden Seiten.
- Das sind also 60 Spiele, aber nur 30 verschiedene Karten.
- Ehrlich gesagt gelten die Zahlen nur für diese Karten, und wir haben sie schon mehrfach benutzt.
- Unser Fazit: Der Ansatz funktioniert. Gegen den starken Gegner ist aber noch Luft nach oben.

---

## Folie 10 – Spielbeispiel
### Moayed · 1:20

- Hier seht ihr zwei Bilder aus demselben Spiel gegen default, im ersten Match.
- *(links zeigen)* Links, bei Schritt 23, sind unsere Einheiten noch verteilt. Es steht 0 zu 0.
- *(rechts zeigen)* Rechts, bei Schritt 90, stehen viele blaue Einheiten auf den gelben Punktefeldern.
- Jetzt steht es 374 zu 11.
- Das zeigt: Sich zu bewegen ist allein nicht das Ziel.
- **Wenn ein Punktefeld gefunden ist, ist Stehenbleiben sinnvoll. Ein besetztes Feld bringt jede Runde Punkte.**
- Das Gedächtnis hilft, einmal gefundene Felder weiter zu nutzen.
- Das ist die Zuschauer-Ansicht und ein gelungenes Beispiel. Nicht jedes Spiel läuft so gut.
- **Übergabe:** „Mahmoud ordnet jetzt ein, was wir gelernt haben und wie es weitergeht.“

---

## Folie 11 – Erkenntnisse und Ausblick
### Mahmoud · 1:05

- Wir haben drei Erkenntnisse.
- **Erstens: Am meisten haben gezielte Verbesserungen gebracht.**
- Wir haben unsere Niederlagen ausgewertet und die Ursachen behoben.
- Zum Beispiel die Symmetrie: Wer ein Relic sieht, kennt auch das gegenüberliegende.
- Und das Erkundungsgedächtnis: Vorher hat der Agent auf manchen Karten nie ein Relic gefunden.
- Dazu kommen sechs Netze statt einem.
- **Damit sind wir gegen Solution_92 von 12 auf 28 von 60 Siegen gestiegen, auf denselben Karten.**
- **Zweitens: Mehr Training hat kaum geholfen.** Weitertraining und Self-Play brachten in unseren Versuchen keinen klaren Gewinn.
- **Drittens, unser nächster Schritt:** Im ersten Match wollen wir die Relics früher finden und das auf neuen Testkarten prüfen.
- **Übergabe:** „Damit zurück an Moayed für unser Fazit.“

---

## Folie 12 – Fazit und Fragen
### Moayed · 0:25

- Zusammengefasst: Sherlock verbindet ein Gedächtnis für die Karte mit sechs trainierten Netzen.
- Gegen default gewinnen wir 60 von 60, gegen Solution_92 28 von 60.
- Als Nächstes verbessern wir die frühe Erkundung und testen auf neuen Karten.
- **Vielen Dank! Welche Fragen habt ihr?**

### 🛑 HIER STOPPEN – nicht weiterklicken

---

# Bei Fragen (Mahmoud antwortet, Moayed kann übergeben)

### „Ist das alles Reinforcement Learning?“
- Nein, nicht alles. Gelernt ist die Bewertung der Aktionen.
- Gedächtnis, Merkmale, Belohnung und das genaue Sap-Ziel haben wir programmiert.
- Genau diese Mischung ist unser Ansatz.
- *(bei Bedarf Folie 14 zeigen)*

### „Wie sieht die Belohnung genau aus?“
- *(Folie 15 zeigen)*
- Jede Einheit bekommt in jedem Schritt eine eigene Belohnung, weil das Spiel nur am Matchende ein Signal gibt.
- Die erste Einheit auf einem Punktefeld bekommt plus eins.
- Eine zweite Einheit auf demselben Feld bekommt einen Abzug, weil das Feld nur einmal zählt.
- Dazu kommen kleine Signale für Annäherung ans Ziel, Erkundung und Energie.
- Ein gewonnenes Match gibt plus zwei.

### „Welche Trainingsparameter habt ihr noch?“
- *(Folie 13 zeigen)*
- Das Lernen startet, sobald 5.000 Erfahrungen im Speicher sind.
- Danach lernen wir alle zwei Spielschritte.

### „Warum sechs Netze?“
- Einzelne DQN-Netze schwanken stark.
- Der Mittelwert aus sechs Netzen ist stabiler.

### „Sind 100 Prozent gegen default perfekt?“
- Nein. Das gilt nur für diese 30 Karten.

### „Sieht der Agent die gelben Felder?“
- Nein. Die Bilder zeigen die Zuschauer-Ansicht.
- Der Agent muss die Punktefelder selbst erschließen.

### „Was ist ein Q-Wert?“
- Der geschätzte langfristige Nutzen einer Aktion.
- Es ist keine Gewinnwahrscheinlichkeit.

### „Wie viel habt ihr trainiert?“
- Sechs Läufe mit je 3.000 Spielen, also 18.000 Spiele.

### „Was ist m1_early?“
- Eine Verbesserung, damit der Agent Punktefelder früher erkennt.
- Wir haben sie getestet, aber sie ist noch nicht in der Abgabe.

### „Wer hat was gemacht?“
- *(Ehrlich die tatsächliche Aufteilung sagen. Vorher absprechen.)*

### Wenn eine Frage zu schwer ist
- „Die Grundidee ist … Die genaue Umsetzung kann Mahmoud ergänzen.“
- *(Nichts erfinden.)*

---

# Unser Projekt einfach erklärt

Das ist Hintergrundwissen, damit ihr das Projekt als Ganzes versteht und Fragen sicher beantworten könnt. **Nicht vorlesen.**

## In einem Satz

Wir haben einen Agenten namens **Sherlock** gebaut, der das Strategiespiel **Lux AI Season 3** spielt. Er **lernt** mit Reinforcement Learning (Double DQN), welche Aktion gut ist, und hat ein **programmiertes Gedächtnis**, das sich die Karte merkt und versteckte Punktefelder herausfindet.

## Die Aufgabe im Kurs

- Kurs **„Anwendungen der KI“** an der HTW Berlin. Wir sind **Team 15**: Mahmoud El-Hassan und Moayed Shawesh.
- Jedes Team baut einen **KI-Agenten für Lux AI Season 3** mit Reinforcement Learning, zum Beispiel DQN, PPO oder A2C, in PyTorch.
- Die Abgabe muss **trainierte Gewichte** enthalten (`.pth`-Datei). Ein Agent nur aus festen Regeln reicht **nicht**.
- Kursregel: Ein Spiel hat **3 Matches** mit je **100 Schritten**.
- Vom Dozenten gab es eine Vorlage mit einem einfachen Beispiel-DQN und einem Programm, das Spiele startet (Runner).
- Benchmark-Gegner aus dem Kurs: **default** (schwach) und **Solution_92** (stark, feste Regeln).

## Die Termine

| Datum | Was | |
|---|---|---|
| **16.10.** | Review: erster trainierter Agent und Präsentation | ← morgen |
| 06.11. | Zwischenpräsentation und Battle gegen ein anderes Team | |
| 27.11. | Finale: Präsentation, Turnier und Abgabe des Agenten | |

Laut Kursfolien kommt die **Note aus den drei Präsentationen**. Bewertet werden Kernaussage, Aufbau, Erklärungen, freies Sprechen, Folien und Originalität. Für die Battles gibt es einen Preis.

## Das Spiel in einfachen Worten

- Zwei Teams spielen auf einer **24 × 24 Karte**. Jedes Team hat **bis zu 16 Einheiten** (Raumschiffe).
- Auf der Karte liegen **Relics**. In ihrer Nähe gibt es **Punktefelder**. Steht eine eigene Einheit darauf, bekommt das Team **jede Runde einen Punkt**.
- **Die Punktefelder sind unsichtbar.** Man findet sie nur durch Ausprobieren: Man stellt Einheiten hin und schaut, ob die Punkte steigen.
- Jede Einheit sieht nur einen **kleinen Bereich** um sich herum. Der Rest der Karte ist verdeckt.
- Einheiten haben **Energie**. Bewegen und Angreifen (Sap) kosten Energie.
- Es gibt Hindernisse (Asteroiden) und Nebel, der die Sicht einschränkt.
- Wer in einem Match **mehr Punkte** hat, gewinnt das Match. Wer **mehr Matches** gewinnt, gewinnt das Spiel.
- **Wichtig für uns:** Die Karte bleibt zwischen den Matches gleich. Was man in Match 1 gelernt hat, hilft in Match 2 und 3. Deshalb lohnt sich ein Gedächtnis.

## Das Problem mit der Vorlage

Das Beispiel des Dozenten hatte Schwächen:
- Der Runner hat den Agenten **in jedem Spiel neu erzeugt** und **vor** dem Spiel gespeichert. Gelerntes ging dadurch verloren.
- Das Beispiel-DQN konnte nur laufen, nicht angreifen. Es hatte keinen Replay Buffer und kein Target-Netz.
- Belohnung gab es **nur am Matchende**, und es hatte nur 17 Merkmale **ohne Gedächtnis**.

## Was wir gebaut haben – Schritt für Schritt

1. **Eigenes Trainingsprogramm**, das den Agenten einmal erzeugt, viele Spiele lang trainiert und richtig speichert. Dazu ein eigenes Programm zur **Auswertung** mit festen Karten und beiden Seiten.
2. **Besseres DQN:** Replay Buffer, Target-Netz, **Double DQN**, **Dueling**-Aufbau und abnehmende Exploration (Epsilon).
3. **Belohnung pro Einheit und Schritt** (Reward Shaping): Punktefeld besetzen, Ziel ansteuern, Erkunden, kein Stapeln auf einem Feld, Matchsieg.
4. **Gedächtnis (Belief):** merkt sich Relics, erkundete Gebiete und **beweist Punktefelder** aus dem Punktezuwachs. Beispiel: Eine Einheit steht auf einem unbekannten Feld, die Punkte steigen um eins. Dann ist das Feld ein Punktefeld.
5. **79 Merkmale pro Einheit**, die auch das Wissen aus dem Gedächtnis enthalten.
6. **Sap-Angriff** als sechste Aktion. Das Netz entscheidet, **ob** angegriffen wird, eine Regel wählt das **Ziel**.
7. **Experimente:** In Vergleichen haben wir einzelne Bausteine weggelassen. Ergebnis in unseren Versuchen: Das **Gedächtnis in den Merkmalen** brachte am meisten, das Shaping macht das Lernen stabiler, und Sap hilft gegen Solution_92. Unser Agent war deutlich besser als das Beispiel-DQN des Dozenten.
8. **Gezielte Verbesserungen** nach Auswertung von Niederlagen:
   - **Ensemble:** Einzelne Netze schwankten stark, deshalb mitteln wir mehrere.
   - **Spiegelsymmetrie:** Die Karte ist gespiegelt. Ein gefundenes Relic verrät auch das gegenüberliegende.
   - **Erkundungsgedächtnis:** Vorher hat der Agent auf manchen Karten nie ein Relic gefunden, weil er jedes Match wieder dieselbe Ecke abgesucht hat.
   - Drei zusätzliche Netze mit Symmetrie trainiert. Daraus entstand das **Ensemble aus sechs Netzen**, unsere aktuelle Abgabe.
9. **Ausprobiert, aber ohne klaren Gewinn:** Weitertraining und Self-Play (gegen sich selbst trainieren).
10. **Prüfung und Korrekturen (Moayed mit Codex):**
    - Zwei Messfehler behoben, bei der Punktezählung und bei der Statistik.
    - Die Abgabe-Gewichte gegen versehentliches Überschreiben geschützt.
    - Die Präsentation erstellt.

## Wie Sherlock in einem Spielschritt entscheidet

```
Beobachtung vom Spiel
   → Gedächtnis aktualisieren (Relics, Punktefelder, erkundete Gebiete)
   → für jede Einheit 79 Merkmale berechnen
   → 6 Netze schätzen die Q-Werte der 6 Aktionen
   → Mittelwert bilden, unerlaubte Aktionen sperren
   → beste Aktion ausführen
```

## Die Ergebnisse

| Agent | gegen default | gegen Solution_92 |
|---|---|---|
| Erster Agent (ein Netz) | 51 von 60 | 12 von 60 |
| **Heute (6 Netze + Symmetrie + Erkundungsgedächtnis)** | **60 von 60** | **28 von 60** (≈ 47 %) |

Beides wurde auf **denselben 30 Karten**, jede von beiden Seiten, gespielt. Diese Karten haben wir schon mehrfach benutzt. Für November legen wir neue Testkarten fest, die wir bis zur Endbewertung nicht anfassen.

## Was uns besonders macht (Originalität)

- **Lernen und Logik zusammen:** Das Netz lernt, was gut ist. Das Gedächtnis findet mit Logik heraus, wo die unsichtbaren Punktefelder sind.
- **Wir verbessern gezielt:** Wir schauen uns Niederlagen genau an, finden die Ursache und prüfen jede Änderung auf neuen Karten. Mehr Training allein hat kaum geholfen.
- **Ehrliche Auswertung:** beide Seiten, feste Karten, offene Grenzen.

## Wie es weitergeht

- **Bis 06.11.:**
  - Match 1 verbessern: Relics früher finden. Ein getesteter Kandidat dafür ist `m1_early`.
  - Vor neuem Training bekannte Fehler in der Belohnung prüfen.
  - Neue Testkarten festlegen.
- **Bis 27.11.:** Feinschliff, Tests für das Turnier und Abgabe als `agent.zip` mit Gewichten.
- **Mögliche größere Schritte:** ein Netz, das die Karte als Bild sieht (CNN), oder ein anderes Lernverfahren wie PPO.

---

# Wörterbuch – alle schweren Wörter von den Folien und aus dem Vortrag

In Klammern steht, auf welcher Folie das Wort vorkommt. **V** heißt: Es wird im Vortrag gesagt. **F** heißt: Es kommt bei den Fragen vor. **Projekt** heißt: Es steht in der Projekterklärung.

## Wörter von A bis Z

- **A2C, PPO** (Projekt) – Andere Lernverfahren für Reinforcement Learning, die der Kurs neben DQN erlaubt. PPO wäre ein möglicher späterer Schritt.
- **Agent** (1, 4) – Das Programm, das spielt. Es bekommt eine Beobachtung und entscheidet, was jede Einheit tut.
- **agent.zip** (Projekt) – Die Datei, die wir am 27.11. abgeben: Agent-Code plus trainierte Gewichte.
- **Aktion** (4, 6) – Was eine Einheit in einem Schritt tut: stehen bleiben, in eine von vier Richtungen gehen oder Sap.
- **Aktionsmaske** (6) – Sperrt Aktionen, die gerade nicht erlaubt sind. Beispiel: Die Einheit kann nicht in ein Hindernis laufen, und Sap geht nur, wenn ein Gegner in Reichweite und genug Energie da ist. Stehenbleiben ist immer erlaubt.
- **Aktionsnutzen** (4) – Anderes Wort für Q-Wert: wie gut eine Aktion ist.
- **Aktionspräferenzen** (14) – Welche Aktion das Netz in einer Lage bevorzugt. Das ist gelernt.
- **Aktionsvorteil A** (6) – Der Teil des Netzes, der schätzt, wie viel besser oder schlechter jede einzelne Aktion ist als der Durchschnitt.
- **Annäherung** (15) – Die Einheit kommt ihrem Ziel näher. Dafür gibt es im Training eine kleine Belohnung.
- **Architektur / Netzarchitektur** (2, 6, 14) – Der Aufbau des Netzes: wie viele Schichten, wie viele Neuronen, welche Köpfe.
- **Asteroid** (Projekt) – Ein Hindernis auf der Karte. Einheiten können nicht hineinlaufen.
- **Auswertung** (2, 4, 8) – Wir lassen den fertigen Agenten spielen und messen, wie gut er ist. Dabei lernt er nicht.
- **Basisläufe** (8) – Unsere sechs Trainingsläufe, aus denen die sechs Netze stammen. Jeder Lauf hatte 3.000 Spiele.
- **Battle / Turnier** (Projekt) – Spiele gegen Agenten anderer Teams am 06.11. und 27.11.
- **Batch** (7, 8, 13) – Ein Paket von Erfahrungen, mit dem auf einmal gelernt wird. Bei uns 256 zufällig gezogene.
- **Belegung** (5) – Ob ein Feld schon von einer eigenen Einheit besetzt ist.
- **Belief** (4, 5, 14) – Das Gedächtnis des Agenten: alles, was er gesehen oder sicher herausgefunden hat, also Relics, erkundete Gebiete und bewiesene Punktefelder.
- **Belohnung (Reward)** (7, 15) – Eine Zahl als Rückmeldung im Training: plus heißt gut, minus heißt schlecht.
- **Benchmark** (9, 12) – Ein fester Test, mit dem man verschiedene Versionen fair vergleicht. Bei uns 30 Karten gegen default und Solution_92.
- **Beobachtung** (4) – Das, was der Agent in einem Schritt vom Spiel bekommt: was in Sichtweite ist, Punktestand und so weiter.
- **Bewiesenes Punktefeld** (15) – Ein Feld, von dem der Agent sicher weiß, dass es Punkte bringt.
- **Buffer / Replay Buffer** (7, 8, 13) – Ein Speicher für Erfahrungen. Bei uns passen 300.000 hinein (Buffer-Kapazität). Ist er voll, werden die ältesten ersetzt.
- **Checkpoint** (8) – Ein gespeicherter Zwischenstand der Gewichte während des Trainings.
- **CNN** (Projekt) – Ein Netz, das Bilder verarbeiten kann. Es könnte die ganze Karte als Bild sehen statt nur 79 Zahlen pro Einheit.
- **default** (8, 9, 12) – Ein einfacher Beispielgegner aus dem Kurs.
- **DQN** (1, 7) – Abkürzung für „Deep Q-Network“, ein neuronales Netz, das Q-Werte schätzt.
- **Double DQN** (1, 7, 14) – Unser Lernverfahren, eine bessere DQN-Variante: Das Online-Netz wählt die nächste Aktion, das Target-Netz bewertet sie.
- **Dueling / Dueling-Kopf** (6, 14) – Ein Netzaufbau mit zwei Köpfen. Einer schätzt den Zustandswert V, der andere den Aktionsvorteil A. Zusammen ergeben sie die Q-Werte.
- **Einheit** (3, 4) – Eine Spielfigur. Jedes Team hat bis zu 16 davon.
- **Einheitenübergänge** (13) – Siehe **Übergang**. „Einheiten“ heißt: pro Einheit gezählt, nicht pro Spiel.
- **Energie** (3, 5) – Der „Treibstoff“ einer Einheit. Bewegen und Sap kosten Energie. Fällt sie durch Gegner unter null, wird die Einheit entfernt und kommt später neu.
- **Ensemble** (6, 8, 14) – Mehrere Netze bewerten dasselbe, und man nimmt den Mittelwert. Das ist stabiler als ein einzelnes Netz. Bei uns sind es sechs Netze.
- **Erfahrung** (7) – Siehe **Übergang**.
- **Erkunden** (3) – Unbekannte Teile der Karte anschauen, um Relics und Punktefelder zu finden.
- **Erkundungsgedächtnis** (11) – Der Agent merkt sich über alle Matches hinweg, welche Gebiete er schon angeschaut hat. So sucht er nicht immer wieder an derselben Stelle.
- **Exploration** (8, 13) – Zufälliges Ausprobieren im Training, damit der Agent auch neue Aktionen kennenlernt. Gesteuert durch Epsilon.
- **Fehlschuss** (15) – Ein Sap, der keinen Gegner trifft.
- **Folgeaktion** (7) – Die Aktion im nächsten Schritt.
- **Gedächtnis** (1, 4, 5, 12) – Siehe **Belief**.
- **Gelände** (5) – Was auf einem Feld liegt, zum Beispiel ein Hindernis (Asteroid) oder ein Nebel.
- **Gewichte** (14) – Die Zahlen im Netz, die beim Training angepasst werden. Sie sind das „Gelernte“ und werden in der `.pth`-Datei gespeichert.
- **Kandidatenfeld** (V, Folie 5) – Ein Feld, das ein Punktefeld sein **könnte**, weil es nah an einem Relic liegt. Bewiesen ist es noch nicht.
- **Kaggle** (F) – Eine Internet-Plattform für KI-Wettbewerbe. Dort lief Lux AI.
- **Kurs** (3) – Unsere Lehrveranstaltung. Dort gilt: 3 Matches pro Spiel.
- **Lernbeginn** (13) – Ab wann gelernt wird: sobald 5.000 Erfahrungen im Buffer sind.
- **Lernrate** (8, 13) – Wie stark ein Lernschritt die Gewichte verändert. 0,0003 bedeutet kleine, vorsichtige Schritte.
- **Lernupdate / Update** (7, 8, 13) – Ein einzelner Lernschritt, in dem die Gewichte ein bisschen angepasst werden.
- **Lernverfahren** (2, 14) – Die Methode, mit der das Netz lernt. Bei uns Double DQN.
- **Lernziel** (V, Folie 7) – Der Wert, an den das Netz seine Schätzung anpassen soll: Belohnung plus Gamma mal Wert der nächsten Situation.
- **Lux AI Season 3** (1) – Ein Wettbewerb, in dem KI-Programme ein Strategiespiel gegeneinander spielen.
- **m1_early** (F) – Eine getestete Verbesserung, damit der Agent im ersten Match Punktefelder früher erkennt. Noch nicht in der Abgabe.
- **Match** (3, 10, 11) – Eine Runde mit 100 Spielschritten. Im Kurs besteht ein Spiel aus 3 Matches.
- **Matchfortschritt** (5) – Wie weit das aktuelle Match schon ist, also welcher Schritt von 100.
- **Merkmale (Features)** (2, 4, 5) – Zahlen, die die Lage einer Einheit beschreiben, zum Beispiel Energie oder Richtung zum Ziel. Bei uns 79 pro Einheit.
- **Merkmalsgruppe** (5) – Eine Gruppe ähnlicher Merkmale, zum Beispiel alles über die eigene Einheit.
- **Mittelwert / Q-Mittelwert** (4, 6, 14) – Der Durchschnitt: Alle Werte werden zusammengezählt und durch ihre Anzahl geteilt. Q-Mittelwert heißt: der Durchschnitt der Q-Werte aller sechs Netze.
- **MLP** (6) – Ein einfaches neuronales Netz, bei dem Schichten hintereinander geschaltet sind.
- **Nebel** (Projekt) – Bereiche auf der Karte, die die Sicht einschränken und Energie kosten können.
- **Netz (neuronales Netz)** (4, 6) – Ein Rechenmodell aus vielen kleinen Recheneinheiten. Es lernt aus Beispielen, Merkmale in Q-Werte umzurechnen.
- **Neuron** (V, Folie 6) – Eine kleine Recheneinheit im Netz. Sie rechnet eine gewichtete Summe ihrer Eingaben aus.
- **Online-Netz** (7) – Das Netz, das gerade lernt und spielt.
- **Parameter** (8, 13) – Einstellungen für das Training, zum Beispiel Lernrate oder Batch-Größe.
- **Potentialbasiert** (15) – Eine Art Zusatzbelohnung: Annäherung ans Ziel gibt Plus, Entfernen gibt Minus. So bringt Hin-und-her-Laufen nichts.
- **Pseudocode** (4, 7) – Ein Ablauf in einfacher Sprache, der aussieht wie Programmcode, aber leichter zu lesen ist.
- **Punktefeld** (3, 5, 10, 15) – Ein Feld in der Nähe eines Relics. Steht eine eigene Einheit darauf, bekommt das Team jede Runde einen Punkt. Man sieht es nicht, man muss es herausfinden.
- **PyTorch** (Projekt) – Eine Programmbibliothek für neuronale Netze. Damit haben wir unsere Netze gebaut.
- **Q-Wert** (4, 6, 14) – Wie viel Belohnung insgesamt man erwartet, wenn man jetzt diese Aktion macht und danach gut weiterspielt. Das ist **keine** Gewinnwahrscheinlichkeit.
- **Reinforcement Learning (RL)** (F) – Lernen durch Ausprobieren. Der Agent bekommt für gute Aktionen Belohnung und lernt, mehr davon zu machen.
- **Relic** (5, 11) – Ein besonderer Punkt auf der Karte. In seiner Nähe liegen versteckte Punktefelder.
- **ReLU** (6) – Eine einfache Rechenregel im Netz: Negative Werte werden zu null, positive bleiben. Dadurch kann das Netz auch komplizierte Zusammenhänge lernen.
- **Replay / Vollständige Replay-Ansicht** (10) – Die Aufzeichnung eines Spiels. Sie zeigt die ganze Karte, also mehr, als der Agent selbst sieht.
- **Reward Shaping / Shaping-Signale** (7, 14) – Kleine Zusatzbelohnungen zwischendurch, zum Beispiel für Annäherung ans Ziel. Sonst gäbe es nur am Matchende eine Rückmeldung, und der Agent würde sehr langsam lernen.
- **Runner** (Projekt) – Das Programm vom Dozenten, das zwei Agenten gegeneinander spielen lässt.
- **Sap / Sap-Möglichkeiten / Sap-Ziel** (5, 14, 15) – Sap ist ein Angriff: Die Einheit schießt auf ein Feld in Reichweite und nimmt Gegnern dort Energie weg. Das kostet eigene Energie. Ob gesapt wird, entscheidet das Netz. Auf welches Feld, entscheidet eine Regel.
- **Schicht** (6) – Eine Reihe von Neuronen. Unsere Netze haben zwei Schichten mit je 256 Neuronen.
- **Seed** (10) – Eine Startzahl für den Zufall. Mit demselben Seed entsteht immer dieselbe Karte, so kann man Spiele wiederholen. Seed 900011 ist die Karte aus dem Spielbeispiel.
- **Seiten / beide Seiten** (8, 9) – Jedes Spiel hat zwei Startseiten (Spieler 0 und Spieler 1). Wir spielen jede Karte auf beiden, damit es fair ist.
- **Self-Play** (11) – Der Agent trainiert gegen Kopien von sich selbst.
- **Siegquote** (F) – Anteil der gewonnenen Spiele, zum Beispiel 28 von 60, also etwa 47 %.
- **Signal** (15) – Ein Teil der Belohnung, zum Beispiel „Einheit verloren“.
- **Solution_92** (8, 9, 11, 12) – Ein starker Gegner aus dem Kurs. Er spielt nach festen Regeln und stammt aus dem Kaggle-Wettbewerb.
- **Spiegelsymmetrie** (6, 11) – Die Karte ist gespiegelt aufgebaut. Was auf der einen Hälfte liegt, liegt gespiegelt auch auf der anderen. Wer ein Relic sieht, kennt also auch das gegenüberliegende.
- **Spielkontext** (5) – Allgemeine Infos zum Spiel, zum Beispiel welcher Schritt gerade ist.
- **Spielschritt / Schritt** (4, 10, 15) – Ein Zug. Alle Einheiten handeln gleichzeitig.
- **Stapeln** (Projekt) – Mehrere eigene Einheiten auf demselben Feld. Bei Punktefeldern bringt das nichts, weil das Feld nur einmal zählt.
- **Target-Netz / Target-Kopie** (7, 8, 13) – Eine Kopie des Online-Netzes, die nur alle 500 Updates erneuert wird. Sie gibt dem Lernen ein ruhigeres Ziel.
- **Teamzustand** (5) – Infos über das ganze eigene Team, zum Beispiel wie viele Einheiten leben.
- **Testkarten** (11, 12) – Karten für die Endbewertung. Eigentlich sollte man sie vorher nicht benutzen. Unsere haben wir schon mehrfach benutzt, deshalb sagen wir das offen.
- **Training** (2, 8) – Die Phase, in der das Netz lernt und sich die Gewichte ändern.
- **Trainingsintervall** (13) – Wie oft gelernt wird: bei uns alle 2 Spielschritte.
- **Treffer** (15) – Ein Sap, der einen Gegner trifft.
- **Übergang / Erfahrung** (7, 8, 13) – Ein gespeicherter Moment aus dem Spiel: Situation, Aktion, Belohnung und nächste Situation.
- **Überschätzung** (V, Folie 7) – Normales DQN nimmt immer den höchsten geschätzten Wert. Weil Schätzungen Fehler haben, ist der höchste oft zu optimistisch. Double DQN verringert das.
- **Umgebungsschritt** (8, 13) – Anderes Wort für Spielschritt.
- **Validierung / Validierungskarten** (8) – Eigene Karten, mit denen wir während der Entwicklung den besten Checkpoint auswählen. Sie sind getrennt von den Testkarten.
- **Weitertraining** (11) – Ein schon trainiertes Netz noch länger trainieren.
- **Zielrichtung** (5) – In welche Richtung das Ziel einer Einheit liegt.
- **Zielzuweisung / zugewiesenes Ziel** (14, 15) – Eine Regel verteilt Ziele an die Einheiten, zum Beispiel „geh zu diesem Punktefeld“ oder „erkunde dort“.
- **Zustandswert V** (6) – Der Teil des Netzes, der schätzt, wie gut die Lage insgesamt ist, egal welche Aktion man wählt.

## Zeichen und Formeln auf den Folien

- **x** (4) – Die 79 Merkmale einer Einheit.
- **Q** (4) – Die Q-Werte, also eine Zahl pro Aktion.
- **a** (4, 7) – Eine Aktion.
- **s** (7) – Die Situation jetzt (englisch „state“).
- **r** (7) – Die Belohnung (englisch „reward“).
- **s'** („s Strich“) (7) – Die Situation im nächsten Schritt.
- **Ende** (7) – Danach geht es nicht weiter, weil das Match oder Spiel vorbei ist oder die Einheit verloren wurde. Dann zählt nur die Belohnung.
- **a\*** („a Stern“) (7) – Die beste nächste Aktion, die das Online-Netz auswählt.
- **Q_Target(s', a\*)** (7) – Wie das Target-Netz die Aktion a\* in der nächsten Situation bewertet.
- **γ = Gamma** (7, 8, 13) – Wie wichtig zukünftige Belohnungen sind. 0,99 bedeutet: Die Zukunft zählt fast genauso viel wie jetzt.
- **ε = Epsilon** (4, 8, 13) – Wie oft im Training zufällig ausprobiert wird. 1,0 heißt immer, 0,05 heißt in 5 % der Fälle. **ε = 0** heißt: kein Zufall, wie beim echten Spielen.
- **V und A** (6) – Zustandswert und Aktionsvorteil (siehe oben).
- **79 → 256 → 256** (6) – 79 Merkmale gehen hinein, dann folgen zwei Schichten mit je 256 Neuronen.
- **256 → 128 → 1 / 6** (6) – Jeder Kopf hat eine Schicht mit 128 Neuronen. Der V-Kopf gibt 1 Wert aus, der A-Kopf 6 Werte, einen pro Aktion.
- **6 × 3.000 = 18.000** (8) – Sechs Trainingsläufe mit je 3.000 Spielen ergeben 18.000 Trainingsspiele.
- **30 Karten × 2 Seiten** (9) – 30 Karten, jede von beiden Seiten gespielt, ergeben 60 Spiele.
- **60/60, 28/60, 12/60** (9, 11, 12) – So viele von 60 Spielen wurden gewonnen.
- **374 : 11** (10) – Der Punktestand blau zu rot bei Schritt 90.
- **÷ 400** (15) – Die Energieänderung wird durch 400 geteilt, damit die Zahl klein bleibt.
- **+1,0 / −0,3 …** (15) – Wie viel Belohnung (plus) oder Abzug (minus) es für ein Signal gibt.
