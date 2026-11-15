# Bleibt ein gegnerischer Halter auf einem bekannten Punktefeld?

Auf den gespeicherten V14-Partien gegen Kaggle3 und Solution_92 sagt die Belegung im vorigen Zug etwas über die Belegung im nächsten aus. Sherlock sah zum Entscheidungszeitpunkt auf dem betrachteten, bereits bestätigten Punktefeld **genau eine gegnerische Einheit**. In der Tabelle steht, wie oft Sherlock dort einen Zug später wieder einen Gegner sah.

| Gegner | Feld bereits im vorigen Zug sichtbar besetzt | Zuvor dort kein Gegner gesehen | Karten mit höherer Quote bei wiederholter Belegung |
|---|---:|---:|---:|
| Kaggle3 | 2.090/2.418 (86,4 %) | 420/932 (45,1 %) | 14/14 |
| Solution_92 | 1.758/2.296 (76,6 %) | 572/948 (60,3 %) | 10/13 |

Die Nenner zählen Feldbeobachtungen über drei Matches. Ein Feld kann in mehreren aufeinanderfolgenden Zügen zählen. Für die letzte Spalte wurden beide Sitze auf jeder Karte zusammengezählt. Die 80 protokollierten Spiele verteilen sich auf 14 Kaggle-, 13 Solution- und 13 Selbstspielkarten, jeweils beide Sitze. Die Tabelle verwendet die 54 Spiele gegen externe Gegner. [Datensatzprotokoll](../combat_advice_20261115/data_protocol.json) · [Dateiprüfsummen](../combat_advice_20261115/v14_advice_audit.json) · [Zähler](observations.json)

**War das Feld wirklich noch besetzt?** Zwölf ältere vollständige V14-Partien gegen Solution enthalten zusätzlich die direkte Sichtmaske und den tatsächlichen Zustand nach jeder Aktion. Betrachtet man nur Felder, die Sherlock schon im vorigen Zug direkt einsehen konnte, stand anschließend ein punktberechtigter Gegner auf **599/883 (67,8 %)** der wiederholt besetzten Felder und auf **112/285 (39,3 %)** der zuvor sichtbar leeren. Auf fünf der sieben gezielt ausgewählten Karten ging der Unterschied in diese Richtung. Das Label prüft die Belegung durch irgendeine gegnerische Einheit mit Energie ≥ 0. Für Kaggle liegt hier nur die sichtbare Folgebelegung vor. [Zwölf historische Traces](../continuation_20261102/targeting/manifest.json)

**Die Beobachtung gilt für bereits besetzte Felder.** War das bekannte Punktefeld aktuell leer und ein sichtbarer Gegner direkt benachbart, folgte auf eine frühere Belegung in den letzten zwei Zügen keine häufigere sichtbare Rückkehr. Gegen Kaggle lauten die Quoten mit und ohne frühere Beobachtung 122/518 (23,6 %) und 452/1.822 (24,8 %), gegen Solution 94/543 (17,3 %) und 466/2.498 (18,7 %). Auch der erste Punkt liefert in diesem Kartensatz wenig Orientierung. V14 punktete gegen Kaggle in 16/28 ersten Matches zuerst, gewann davon zwei Matches und insgesamt kein Spiel. Gegen Solution erzielte V14 18-mal den ersten Punkt, Solution siebenmal, einmal punkteten beide gleichzeitig. V14 gewann alle 26 Spiele. [Zähler nach Gegner](observations.json)

## Bedeutung für den Bewegungsberater

Der bisherige CNN-Berater erhält 16 Kartenebenen und 79 Merkmale je Einheit. Seine aktuelle Gegnerkarte zeigt beobachtete Dichte und Energie. Eine weitere Ebene mit der **im unmittelbar vorherigen Zug beobachteten gegnerischen Belegung pro Feld** könnte dem Bewegungsnetz helfen, einen bereits sichtbaren Halter einzuschätzen. V14 verwendet den Stillstand einer sichtbaren gegnerischen Einheit anhand ihrer UID bereits bei seinen Schussregeln. Ein früheres Bewegungsmodell zum Vorhalten änderte gegen Solution 478 Schüsse, beide Varianten gewannen dieselben 38/40 Partien. Die vorliegenden Zähler belegen weder die beste Bewegungsrichtung noch zusätzliche Siege. [Eingaben des Beraters](../../../scripts/selective_advice_agent.py) · [Kartenebenen](../../../agents/sherlock/cnn_model.py) · [Frühere Vorhalteversuche](../sap_motion_screen_20261109/ERGEBNIS.md)

## Nachrechnen

Python mit NumPy genügt. In einem Checkout mit den lokal gespeicherten 80 Original-NPZs unter `experiments/imitation/final_20261115_v14_advice` genügt folgender Aufruf aus dem Projektstamm. Er schreibt JSON auf die Standardausgabe.

```sh
python experiments/analysis/temporal_movement_20261115/diagnose.py
```

Liegen die NPZs in einem anderen Checkout, übergibt `--data PFAD_ZU_DEN_NPZ` den Ordner mit `protocol.json` und den 80 Archiven. Der Zähler prüft deren SHA-256-Werte gegen die versionierte Erhebung und die zwölf historischen Traces gegen ihr Manifest. Die Protokollprüfsummen sind im [gespeicherten Ergebnis](observations.json) enthalten.

Für die NPZ-Zählung bilden vier fortlaufende globale Schritte desselben Matches ein Fenster von t−2 bis t+1. Die Vorinformation kommt aus t−1 bzw. bei der Rückkehrfrage aus t−1 und t−2. Das Punktemerkmal und die aktuelle Gegnerzahl stammen aus t. Erst die Ergebnismessung verwendet t+1. Gegen Kaggle sind 8.398 von 8.400 möglichen Nicht-Reset-Boards vorhanden, gegen Solution alle 7.800. Fehlende Schritte und Matchgrenzen werden nie überbrückt. Die NPZs halten keine Gegner-UIDs fest. Ihre Ebene `visible_now` ist bei V14 durch Symmetrie erweitert und belegt bei fehlender Gegnerbeobachtung keine tatsächlich leere Zelle. Die alte Solution-Gegenprobe kann die direkte Sicht ausdrücklich verlangen. [Aufzeichnung](../../../scripts/collect_combat_advice.py) · [Sichtgedächtnis](../../../agents/sherlock/belief.py) · [Auswertung](diagnose.py)
