# Sherlock – Vortrag zum Üben (23.10.2026)

> **Wichtig:** Der Prof verlangt freies Sprechen – **beim Vortrag nichts ablesen** (kein Papier, kein Handy, kein Bildschirm). Diese Datei ist zum **Üben**. Ziel: Pro Folie die **fett gedruckten Kernsätze** frei sagen können; die Folie selbst ist eure Gedächtnisstütze.

**Stand 22.10.2026** (Claude Code mit Mahmoud). Folien: `Sherlock_Review_23-10-2026.pdf` im Projektordner, Quelle: `docs/presentation/Sherlock_Review_23-10-2026.html`. Die Aufteilung ist ein Vorschlag; Moayed bitte vor dem Vortrag einmal durchgehen und mit Uhr proben.

| Wer | Folien | Zeit |
|---|---|---|
| Moayed | 1, 2, 3, 4 · 8, 9, 10 · 13 | 5:10 |
| Mahmoud | 5, 6, 7 · 11, 12 | 4:30 |
| **Gesamt** | | **9:40** (höchstens 10) |

Folien 14 und 15 sind Reserve für Fragen. Jeder Punkt ist ein Satz, den man beim Üben so sagen kann. *Kursiv in Klammern* = nur Hinweis, nicht vorlesen.

**Kernaussage:** **Von 47 % auf 90 % gegen Solution_92: Regeln und Training brachten uns auf 78 %, die Fehlersuche gegen den wahren Spielzustand auf 90 %.**

**Inhalt:** Vortrag (Folien 1–13) · Bei Fragen · Live-Demo · Wörterbuch

---

## Folie 1 – Sherlock
### Moayed · 0:20

- Hallo, wir sind Mahmoud und Moayed, Team 15, und unser Agent heißt Sherlock.
- **Beim letzten Review hat Sherlock 47 % gegen Solution_92 gewonnen, heute sind es 90 %.**
- Wir zeigen, was davon Training war und was Fehlersuche.

---

## Folie 2 – Agenda
### Moayed · 0:20

- Zuerst ein kurzer Rückblick und die Fragen aus dem letzten Review.
- Dann zeigen wir, wie Sherlock heute aufgebaut ist und was Training gebracht hat.
- Danach kommen drei Fehler, die wir gefunden haben, und die Ergebnisse.

---

## Folie 3 – Rückblick auf den 16.10.
### Moayed · 0:50

- Am 16.10. hatten wir 6 Netze und ein Gedächtnis für die Karte.
- Damit haben wir 28 von 60 Spielen gegen Solution_92 gewonnen.
- Der Prof hat gefragt: **Warum nur 47 % nach 18.000 Trainingsspielen?**
- Er hat auch gefragt, ob die Belohnung in jedem Schritt kommt. **Ja: jede Einheit bekommt in jedem Schritt eine Belohnung**, für Punkte und für Annäherung an Ziele, plus einen Bonus für den Matchsieg.
- Seine Empfehlung war CNN und PPO. Das haben wir ausprobiert, dazu gleich mehr.
- *(Auf die 90,3 % rechts zeigen.)* Heute stehen wir bei 90,3 % auf 800 neuen Karten.

---

## Folie 4 – Sherlock heute
### Moayed · 1:00

- Sherlock macht drei Dinge: merken, bewerten, absichern.
- **Merken:** Das Gedächtnis speichert Relics, Punktefelder und die Karte, auch wenn sie wandert.
- **Bewerten:** 18 Double-DQN-Netze bekommen 79 Merkmale pro Einheit und schätzen den Nutzen jeder Aktion. Wir nehmen den Mittelwert der 18 Netze.
- **Absichern:** Regeln verhindern Fehler, die wir kennen, zum Beispiel Sackgassen oder Kollisionen.
- *(Pseudocode kurz durchgehen.)* In jedem Schritt: Gedächtnis aktualisieren, Ziele verteilen, dann wählt jede Einheit die beste erlaubte Aktion.
- **Die Netze sind seit dem 20.10. dieselben. Neu sind die Regeln.**

---

## Folie 5 – Training und Regeln: der Weg bis 78 %
### Mahmoud · 1:20

- Bis zum 20.10. hat uns eine Mischung aus Regeln und Training geholfen.
- Zuerst kamen Regeln für die Relic-Suche, noch ohne neues Training: von 47 auf 61 %.
- **Dann haben wir neu trainiert, mit aktiven Regeln und korrigierter Belohnung: 69 %.**
- 18 statt 6 Netze brachten noch einmal 7 Punkte. Zusammen sind das 66.000 Trainingsspiele.
- Regeln für Ziele und Schüsse brachten jeweils 6 bis 7 Punkte. So kamen wir auf 78 %.
- Danach hat mehr Training nichts mehr gebracht: CNN mit PPO hat das Ensemble eingeholt, aber nicht übertroffen. Neue Merkmale für Schussgefahr und 12 weitere Netze auch nicht.
- **Ab 78 % war Training nicht mehr der Engpass.**
- *(Falls gefragt: Die Zeilen sind auf unterschiedlichen Kartenblöcken gemessen, jeder Vergleich aber auf denselben Karten.)*

---

## Folie 6 – Wie wir Fehler gefunden haben
### Mahmoud · 0:50

- Also haben wir uns die verlorenen Spiele genau angesehen.
- **Wir haben Schritt für Schritt verglichen, was Sherlock glaubt und was im Spiel wirklich passiert.**
- Für jede Ursache gibt es eine gezielte Änderung, als Schalter und mit Tests gegen die Spiel-Engine.
- Jede Änderung prüfen wir zuerst auf 1.330 Entwicklungsspielen und dann auf frischen Karten mit vorher festgelegten Hürden.

---

## Folie 7 – Fehler 1: Die Karte im Gedächtnis war veraltet
### Mahmoud · 1:00

- Asteroiden und Nebel wandern im Spiel diagonal über die Karte.
- Nebel ist bei kleiner Sicht unsichtbar. Deshalb hat das Gedächtnis alte Asteroiden behalten.
- **Im Mittel waren 18 % der gemerkten Felder falsch.**
- *(Links zeigen.)* Hier sind unsere Einheiten am Start eingesperrt, mit 0 Energie. Schritt 90: 112 zu 717.
- Lösung: Wir erkennen die Drift und rollen die Karte im Gedächtnis mit. Wenn ein Feld trotz Sichtweite unsichtbar ist, muss es Nebel sein.
- *(Rechts zeigen.)* Gleiche Karte nachher: Die Einheiten laufen sofort los. Schritt 90: 541 zu 488.

---

## Folie 8 – Fehler 2: Wege und Ziele
### Moayed · 0:50

- Das Netz läuft gern nach Luftlinie, auch wenn eine Wand im Weg ist.
- *(Links zeigen.)* Hier pendeln die Einheiten vor einer Sackgasse. Schritt 85: 163 zu 550.
- Außerdem lagen manche Ziele unter Asteroiden und waren gar nicht erreichbar.
- **Lösung: In Sackgassen nimmt Sherlock den kürzesten Weg, und Ziele werden nach Weglänge verteilt.**
- *(Rechts zeigen.)* Nachher läuft Sherlock um die Wand und hält mit: 514 zu 519.

---

## Folie 9 – Fehler 3: Energie und Kollisionen
### Moayed · 0:50

- Ein Schuss kostet 30 bis 50 Energie.
- *(Pfeile zeigen.)* Hier schießen drei unserer Einheiten auf einen Gegner, der nur 21 Energie hat. Zwei Schüsse sind verschwendet.
- **Bei Kollisionstoden hatten unsere Einheiten im Mittel 41 Energie, die Gegner 102.**
- Lösung: Kein Schuss auf Gegner, die schon sicher sterben. Halter schießen nur auf stehende Gegner. Und keine Züge in Kollisionen mit stärkeren Gegnern.

---

## Folie 10 – Ergebnis auf neuen Karten
### Moayed · 0:50

- *(Diagramm von links nach rechts.)* 47 % beim Review, 78 % am 20.10., dann 83,5 % und heute 90,3 %.
- **Der Schritt von 78 auf 90 % kam aus der Fehlersuche, mit denselben 18 Netzen.**
- Gemessen auf 800 neuen Karten, beide Seiten. Gegen V7 sind das 7,5 Punkte mehr, das Intervall liegt zwischen 5,4 und 9,6.
- Gegen default gewinnen wir 99,75 %, und direkt gegen die Vorversion 58 %.
- Wir übernehmen eine Version nur, wenn sie vorher festgelegte Hürden schafft.

---

## Folie 11 – Robust gegen andere Spielweisen?
### Mahmoud · 0:40

- Im Turnier spielen wir nicht nur gegen Solution_92. Deshalb haben wir andere Spielweisen getestet.
- Gegen das Prof-DQN, einen Zufallsagenten und einen Rush-Bot gewinnen wir alle Testspiele.
- Gegen unsere alte Abgabe und unseren CNN-PPO-Agenten gewinnen wir knapp 90 %.
- **Am schwersten ist eine Solution_92-Variante, die im ganzen Quadrat schießt.** Da sind es je nach Karten 74,5 bis 83,5 %.
- Unsere ältere Version verliert dort genauso stark. Diesen Gegner nehmen wir für die nächsten Tests.

---

## Folie 12 – Erkenntnisse und Ausblick
### Mahmoud · 0:40

- **Erstens: Training mit Regeln hat bis 78 % geholfen, danach nicht mehr.**
- **Zweitens: Die Fehlersuche hat uns von 78 auf 90 % gebracht.**
- Bis zum 27.11. wollen wir die Kämpfe um gemeinsame Relic-Felder verbessern, gegen weitere Spielweisen testen und die Abgabe vorbereiten.

---

## Folie 13 – Fazit und Fragen
### Moayed · 0:20

- **Training, Regeln und Fehlersuche: 90 % gegen Solution_92.**
- Jede Änderung haben wir vorher festgelegt und auf neuen Karten geprüft.
- Danke! Habt ihr Fragen?

---

## Bei Fragen

**Ist das noch Reinforcement Learning, wenn so viele Regeln drin sind?**
Ja. Das Netz entscheidet in jedem Schritt für jede Einheit: laufen, stehen oder schießen. Die Regeln greifen nur in bestimmten Fällen ein. Am 19.10. haben wir die gleichen Regeln ohne Netz getestet: 3 % gegen Solution_92 statt 38 % mit Netz. Das Netz trägt also den Großteil.

**Warum nicht PPO, wie empfohlen?**
Wir haben CNN mit PPO trainiert. Zuerst hat das CNN das Ensemble nachgeahmt, dann lief PPO. Es erreichte den Lehrer (73,0 % gegen 73,25 %), aber nicht mehr. 150 weitere PPO-Iterationen brachten keinen Gewinn. Das Ensemble aus 18 DQN-Netzen bleibt deshalb unser Agent.

**Wie sicher sind die 90 %?**
800 neue Karten, jede Karte von beiden Seiten gespielt, also 1.600 Spiele. Das 95-%-Intervall für den Vorsprung gegenüber der Vorversion reicht von 5,4 bis 9,6 Punkten. Gegen unbekannte Gegner im Turnier ist das keine Garantie.

**Was ist ein gepaarter Karten-Bootstrap?**
Beide Versionen spielen auf denselben Karten. Wir ziehen viele Male zufällig ganze Karten mit Zurücklegen und rechnen den Unterschied jedes Mal neu aus. Daraus ergibt sich das Intervall.

**Wie sieht die Belohnung genau aus?**
Pro Einheit und Schritt: Plus für neue Teampunkte und für Annäherung an Relic- oder Kandidatenfelder. Minus, wenn Einheiten auf demselben Feld stehen oder zu wenig Energie für eine Bewegung haben. Am Matchende gibt es einen Bonus für den Sieg und einen Abzug für die Niederlage. *(Folie 3)*

**Wie habt ihr Solution_92 so oft geschlagen, ist das nicht Überanpassung?**
Die Änderungen beheben allgemeine Fehler: falsche Karte, schlechte Wege, verschwendete Energie. Das hilft gegen jeden Gegner. Gegen andere Spielweisen haben wir extra getestet *(Folie 11)*.

**Wie viele Spiele habt ihr insgesamt trainiert?**
Die 18 Netze der Abgabe wurden zusammen mit 66.000 Trainingsspielen trainiert.

**Was passiert in den Reservefolien?**
Folie 14 erklärt, wie wir prüfen (Hürden, Statistik). Folie 15 zeigt die Spielregeln, die wir nutzen.

---

## Live-Demo, falls der Prof fragt

Im Terminal im Projektordner:

```
cd ~/Documents/AKI_LuxAgent15
.venv/bin/python -m scripts.play_and_view
```

- Startet ein Spiel Sherlock gegen Solution_92 über den unveränderten Kurs-Runner (etwa 6 Sekunden) und öffnet das Replay automatisch im Browser (Lux-Viewer, braucht Internet). Im Viewer auf ▶ klicken.
- Im Terminal steht das Ergebnis, z. B. „Sherlock (player_0) gewinnt 3:0 Matches gegen Solution_92_Kaggle“.
- Gegen default: `--gegner default`, gegen das Prof-DQN: `--gegner dqn`, Sherlock auf der anderen Seite: `--seite 1`.
- Jede Karte ist neu und zufällig. Wir gewinnen etwa 9 von 10 Spielen gegen Solution_92, eine Niederlage ist also möglich.
- Ohne Internet: `.venv/bin/python main.py` spielt dasselbe Spiel; das Replay liegt dann als JSON in `replays/15_vs_2/` und kann später auf https://s3vis.lux-ai.org/ hochgeladen werden.

---

## Wörterbuch

- **Relic:** Objekt auf der Karte. Felder in seiner Nähe geben Punkte, wenn eine Einheit darauf steht.
- **Punktefeld:** ein solches Feld, das Punkte bringt.
- **Sap:** Schuss auf ein Feld in Reichweite. Kostet Energie und zieht dem Ziel Energie ab.
- **Drift:** Asteroiden und Nebel verschieben sich alle paar Schritte.
- **Ensemble:** mehrere Netze; wir nehmen den Mittelwert ihrer Bewertungen.
- **Q-Wert:** geschätzter Nutzen einer Aktion.
- **Hürde (Gate):** vorher festgelegte Bedingung, die eine neue Version schaffen muss.
- **V3, V7, V10:** unsere Versionen vom 20.10. und 22.10. Alle nutzen dieselben 18 Netze.
