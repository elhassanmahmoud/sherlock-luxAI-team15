# Randomisierter Lernversuch zur Energie einzelner Scouts

Der Gegner kaggle3 ist mit seinem bereits im Projekt festgelegten Download und beiden SHA-256-Prüfsummen ausschließlich ein Spielgegner. Die Lernzeilen enthalten öffentliche Merkmale des eigenen V14, die zufällig ausgeführte eigene Aktion und die später beobachtete Energie der eigenen Einheit. Sie enthalten keine Aktionen, Gewichte oder internen Bewertungen des Gegners.

## Vor der ersten Messung festgelegt

- Acht Lernkarten 7162000–7162007 und vier getrennte Diagnosekarten 7162100–7162103, jeweils beide Sitzplätze, gegen den nativen Kaggle3. Die alten Kaggle-Dateien enthalten Match- und Spielsummen. Historische V14-Traces liefern keine zufällige Aktionszuweisung mit bekannter Wahrscheinlichkeit.
- Der Actor beginnt als unverändertes V14. Ein deterministisch rotierender Einheitenslot bekommt frühestens alle vier Züge eine Gelegenheit. Er steht auf keinem bekannten Punktefeld, betritt mit der V14-Aktion keines, soll nicht schießen, besitzt höchstens 150 Energie, und hat mindestens zwei legale Bewegungsmöglichkeiten einschließlich Stillstehen. Nahe dem eigenen Spawn und innerhalb der letzten fünf Matchschritte sind die Eingriffe ausgesetzt.
- Die ausgeführte Aktion ist gleichverteilt über alle freigegebenen V14-Bewegungen. Alle übrigen Einheiten und die drei Folgeschritte bleiben bei V14. Eigene Energie nach vier Schritten minus eigene Startenergie ist das Ziel. Verschwindet die Einheit, ist die Energie negativ oder teleportiert der Slot zum Respawn, beträgt der Zielwert minus Startenergie minus 40. Einheiten werden über alle vier Zwischenbeobachtungen verfolgt. Ein Matchreset darf kein Label erzeugen.
- Ein einziges lineares Ridge-Modell mit 19 Merkmalen (inklusive unbestrafter Konstante), feste Regularisierung 5. Keine Gradienten oder weiteren Netzgewichte, kein Nachtraining auf Diagnosedaten. Es wechselt die endgültige Bewegung erst bei einem vorhergesagten Vorteil von mindestens sechs Energieeinheiten. Maximal ein Scout pro vier Schritte.
- Die Diagnose schätzt den Wertunterschied der festgelegten und ursprünglichen Bewegung mit dem randomisierten Log und einer modellgestützten Korrektur nach inverser Auswahlwahrscheinlichkeit. Sie mittelt erst pro Karte und dann über die vier Karten. Ein isolierter frischer Spielscreen kommt bei mindestens 20 vorgeschlagenen Änderungen, positivem Mittel und mindestens drei positiven Karten in Betracht. Diese kleine Diagnose misst einen kurzfristigen Energieindikator. Spielstärke benötigt einen getrennten Vergleich ganzer Partien.

## Befehle

Aus dem Projektverzeichnis, im vorhandenen Lux-Kursumfeld:

```sh
python -m scripts.final_learning_study collect --split train --workers 1
python -m scripts.final_learning_study fit
python -m scripts.final_learning_study collect --split diagnose --workers 1
python -m scripts.final_learning_study diagnose
```

Ein Worker genügt. Höchstens zwei lokale Spielprozesse insgesamt. Die Sammlung schreibt jedes vollständig gespielte Spiel exklusiv und kann unveränderte, vorhandene Spiele später validieren. Fit und Diagnose schreiben einmalig. Der gemeinsame Spielrunner kann die Klasse `scripts.final_learning_agent.EnergyReturnAgent` mit den üblichen V14-Konstruktorargumenten und `model_path` auf die erzeugte Datei `model.json` verwenden. Das Modell und die Untersuchungsdaten liegen ausschließlich in diesem Ordner.
