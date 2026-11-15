# Umbau: Sherlock lernt vom Kaggle-Platz-3-Agenten (Plan, festgelegt 15.11.2026, 15:20 Berlin, vor dem ersten Spieltest eines Schülers)

## Auftrag und Grund

Mahmoud wünscht am 15.11. einen großen Umbau, damit Sherlock deutlich stärker wird. Laut Battle vom 06.11.
spielten Platz 1 und 2 koordinierter und strukturierter. Gegen den öffentlichen Kaggle-Platz-3-Agenten gewinnt
V14 nur 3–4 % der Spiele. 13 Handregel-Varianten brachten keinen messbaren Vorteil (alle innerhalb ±1 pp
Matchanteil auf Dev A); selbst ein Orakel mit allen Punktefeldern erreicht nur 2 % der Spiele
([Befund](../../../experiments/analysis/kaggle3_20261115/README.md)).

## Verfahren

1. Lehrerdaten: Der Kaggle-Agent spielt gegen sich selbst, V14 und Solution_92 auf Trainingskarten ab 7200000.
   Ein Schatten-Sherlock baut für seine Seite die Netzeingaben (16 Kartenebenen aus dem Gedächtnis, 79 Merkmale je
   Unit, kanonischer Raum) und notiert seine Aktion und sein Schussziel je Unit (`scripts/imitate.py collect`).
2. Nachahmung: `ImitationNet` (CNN wie `PolicyNet` plus gelernte Zielkarte für Schüsse), maskierte
   Kreuzentropie; Schüsse sind erlaubt, wenn die Unit die Kosten bezahlen kann (41 % der Lehrerschüsse gehen auf
   Felder ohne sichtbaren Gegner).
3. DAgger: Der Schüler spielt, ein Schatten-Lehrer beschriftet die besuchten Lagen, dann wird neu trainiert.
4. Optional später: RL-Feinschliff.

Der Lehrer ist nur Lehrer und Testgegner und wird nie verpackt. Die Schülergewichte sind eigene, von uns
trainierte Gewichte. In der Präsentation sagen wir offen, dass das Netz vom Kaggle-Agenten gelernt hat.

## Kartensätze

Entwicklung und Auswahl auf Dev A (7150000–7150099) und Dev B (7151000–7151099). Die Bestätigung erfolgt
einmalig auf 7158000–7158399 (400 Karten, beide Seiten), erst nach Abschluss der Auswahl.

## Hürden für eine Übernahme als Abgabe (alle auf dem Bestätigungssatz)

1. Gegen kaggle3: Spielsiegquote höher als V14, untere Grenze des gepaarten 95-%-Intervalls (Bootstrap über
   Karten) größer als 0.
2. Gegen Solution_92: höchstens 3 Prozentpunkte schlechter als V14 (Punktschätzer).
3. Direkt gegen V14: Siegquote über 50 %, untere Intervallgrenze über 50 %.
4. Gegen default: mindestens 98 %.
5. Technik: Kurs-Runner beide Seiten, Zip-Prüfung, keine Fehler; Absturzschutz wie bei V14.

Verfehlt der beste Schüler eine Hürde, bleibt V14 die Abgabe, außer Mahmoud entscheidet ausdrücklich anders
(mit Begründung im Übernahmebericht). Freeze spätestens 23.11.
