# Zusätzliches Lerngewicht für späte Feldsituationen

**Das stärkere Gewicht hat keine bessere Aktionsauswahl ergeben.** Im direkten Vergleich beider Lernverfahren änderte sich in keiner der 738 zurückgehaltenen Feldsituationen die am besten bewertete legale Aktion. Die Behandlung sagte die Lehreraktionen mit einem geringfügig schlechteren Logloss vorher. Entsprechend der Vorfestlegung endet der Pilot vor dem Spielvergleich. V16 ist weiterhin die Abgabe. [Vorabplan](PLAN.md) · [vollständige Messwerte](offline.json)

## Welche Beispiele Sherlock gesehen hat

Das V16-Kurspaket spielte zwölf neue DAgger-Partien. Der Kaggle-Lehrer erhielt in jedem Zug seine eigene öffentliche Beobachtung auf Sherlocks Seite. Für den nächsten Zug merkte er sich den Befehl, den Sherlock tatsächlich gespielt hatte. Zusammen kamen 41.670 rohe Einheitsentscheidungen hinzu. Acht Partien flossen ins Training ein. Die vier zurückgehaltenen Karten deckten jede Kombination aus Gegner (Solution oder Kaggle) und Startseite genau einmal ab. [Neue Datensammlung mit Dateihashes](sammlung.json)

Die breite Trainingsbasis bestand aus 32 vorhandenen v4-DAgger-Archiven und den acht neuen V16-Spielen. Nach Prüfung der Aktionsmaske und der Zielkoordinaten blieben **128.945 Lernbeispiele**, darunter 27.329 frische V16-Beispiele und insgesamt 6.602 Feldsituationen. 29 Lernspiele waren gegen Kaggle, sechs gegen V14 und fünf gegen Solution. P0 war 16-mal, P1 24-mal vertreten. Die älteren Trainingskarten können V16 aus früheren Lernrunden bekannt sein. [Archivindex der früheren Sammlung](../../umbau_20261115/dagger_zusatz/index-400.json)

Für die Feldgewichtung speichert die Auswertung pro Match die Positionen lebender eigener Einheiten bis Zug 50. In den Zügen 81 bis 100 markiert sie Einheiten, die höchstens einen Bewegungsschritt von einem solchen Ort entfernt sind, sofern Sherlock diesen Ort inzwischen als Punktefeld kennt. Die Auswertung verwendet kanonische Koordinaten beider Seiten und leert ihren Feldspeicher bei jedem Matchwechsel. Alle fünf archivierten Vorbewegungsmerkmale stimmten für sämtliche Zeilen mit der schrittweisen Berechnung des Spieltrackers überein. Der Tracker in V16 und im Projekt stimmt byteweise überein.

## Ergebnis der vier zurückgehaltenen Partien

Bei jeder Messung wurden v9 und v8L zusammen ausgewertet. Beide Lernarme änderten ausschließlich die Gewichts- und Bias-Tensoren des v9-Aktionskopfs. Dafür nutzten sie dieselben 96 Mini-Batches mit je 512 zugelassenen Lehrerbeispielen. Niedrigerer Logloss bedeutet, dass das Ensemble der beobachteten Lehreraktion im Mittel höhere Wahrscheinlichkeit zuweist.

| Ensemble | Logloss insgesamt | Lehreraktion getroffen | Logloss am Feld | Lehreraktion am Feld getroffen |
| --- | ---: | ---: | ---: | ---: |
| Original V16 | 0,54509 | 11.645 / 14.085 | 0,49416 | 616 / 738 |
| Normales Nachlernen | **0,53647** | 11.642 / 14.085 | **0,46461** | 622 / 738 |
| Feldbeispiele dreifach gewichtet | 0,53654 | 11.641 / 14.085 | 0,46571 | 622 / 738 |

Alle vier Prüfpartien enthielten Fokusbeispiele (31, 142, 260 und 305). Gegenüber dem Original wechselte die jeweils höchste legale Netzempfehlung in beiden Lernarmen 196-mal, davon 13-mal am Feld. Zwischen den Armen gab es sieben Unterschiede insgesamt und null am Feld. Gezählt wurde die Ensembleentscheidung vor Stay-Bias, Halter- und Entstapelungsregel. Ausgespielte Eingriffe oder zusätzliche Siege lassen sich daraus nicht ableiten.

Beide Arme konnten die Stärke einzelner Empfehlungen gegenüber dem Original verschieben. Der vorab geforderte Vorteil **der Feldgewichtung gegenüber normalem Nachlernen** blieb aus. Die vier Prüfungskarten erlauben zudem keine stabile Schätzung kleiner Unterschiede. Sollte das Team normales Nachlernen getrennt prüfen, braucht diese Frage eine eigene Auswahlregel und zusätzliche Spielkarten. [SHA-gebundene V16-Abgabe](../../../releases/20261117_sherlock_v16/README.md)

## Reproduzieren

Python 3.13.13 mit den Projektabhängigkeiten; die Merkmale wurden auf Apple MPS berechnet, die beiden Aktionsköpfe auf der CPU trainiert. Die komprimierten Rohpartien und die beiden neuen Modellkopien liegen lokal im Hauptcheckout unter `experiments/imitation/finalwoche_20261122/`. Die vorliegende Analyse enthält Belege und Prüfsummen. Der folgende Befehlssatz schreibt einen eigenen Durchlauf in ein leeres Verzeichnis. Er setzt das vorhandene zusätzliche v4-Archiv und die installierten Kaggle-Lehrergewichte voraus.

```sh
haupt="$HOME/Desktop/KI/sherlock-luxAI-team15"
python="$haupt/.venv/bin/python"
pilot=experiments/analysis/v16_finalwoche_20261122/lernversuch
ausgabe=$(mktemp -d)
export PYTHONHASHSEED=0
"$python" "$pilot/sammlung.py" "$ausgabe/frisch"
"$python" "$pilot/lernen.py" --archive "$haupt/experiments/imitation/k3_v4_extra_7172000/data" \
  --recent "$ausgabe/frisch" --out "$ausgabe/modelle"
```

Die Sammlung umfasst 12 vollständige Partien mit je 303 Schritten. Jeder Arm nutzte genau dieselben zugelassenen Entscheidungen. Die Holdout-Karten sind zu den Trainingskarten disjunkt. Bei dem vorliegenden Ergebnis verweigert das vorbereitete Spielwerkzeug den Start. Der Kurzvergleich umfasst daher **null Spiele**.
