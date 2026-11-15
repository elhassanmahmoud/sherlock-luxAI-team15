# R7 kombiniert den letzten eigenen Befehl mit Lehrerbewertungen

R5 traf auf 24 gemischten Diagnosekarten netto 17.481 zusätzliche Lehrerbefehle gegenüber V14. R3 überschrieb nur 2.343 Entscheidungen von V14, die bereits mit dem Lehrer übereinstimmten. R7 soll beide Eigenschaften in einem einzigen Bewegungsnetz vereinigen. Ein Lehrerzug zählt hier als Aktionsklasse. Das Schussziel entscheidet weiterhin V14.

## Was R7 lernt

Das CNN erhält 16 Kartenebenen, die bisherigen 79 Einheitsmerkmale und sechs Zusatzwerte für den letzten tatsächlich ausgeführten Befehl der Einheit. Die sechs neuen Gewichtsspalten starten bei null. Ohne gültige Vorgeschichte sind alle sechs Eingabewerte null. Vor dem ersten Gewichtsupdate wird mit allen sechs Vorgängeraktionen und der unbekannten Vorgeschichte geprüft, ob die Erweiterung alle drei ursprünglichen Netzausgaben erhält.

Wie R3 ahmt R7 die ausgeführten Lehrerbefehle nach und lernt auf geeigneten Stellungen zusätzlich aus den relativen Bewertungen der fünf legal maskierten Bewegungen einschließlich Stillstand. Für diesen Zusatzverlust gelten Temperatur 2 und Gewicht 0,5 nach Temperaturkorrektur. 656.134 zulässige Zeilen müssen in jeder der fünf Epochen tatsächlich zum zusätzlichen Lernziel beitragen. Bei 631.325 davon sind mindestens zwei Bewegungen erlaubt. Beim Spielen gilt weiterhin die 0,70-Schwelle. Bereits gewählte Schüsse und Schussziele bleiben in V14s Zuständigkeit.

Die 32 ursprünglichen und 120 gemischten Lernkarten sind bei R2, R3, R5 und R7 identisch. Ebenso die acht ursprünglichen und 24 gemischten Diagnosekarten. Keine der 32 Diagnosekarten beeinflusst die Gewichte. Initialisierung 2711, Architektur mit 32 Kanälen und drei Residualblöcken, Lernrate 0,001, fünf Epochen. Der feste fünfte Gewichtsstand ist der Kandidat. Die drei früheren Kontrollmodelle werden anhand der tatsächlich veröffentlichten SHA-256-Werte gebunden. Der neue Gewichtsstand enthält die Quellenprüfsummen einschließlich der Datei, aus der die ausführende Trainingsfunktion geladen wurde.

## Wann R7 in Spielen geprüft wird

Auf allen 156.243 Entscheidungen der 24 gemischten Diagnosekarten muss R7 netto mindestens R5s 17.481 zusätzliche Übereinstimmungen erzielen und darf höchstens R3s 2.343 vorher richtige Entscheidungen verschlechtern. Mindestens eine Grenze muss strikt verbessert werden. Die acht älteren Karten werden getrennt berichtet, ebenso die 147.228 gemischten Entscheidungen mit gültigem Vorbefehl. Das Audit verbindet R2 und R5 mit den versiegelten Originalmessungen pro Karte und Sitz. Für R3 und R7 berechnet es sämtliche Gruppen auf denselben Archivbytes. Die neuen R3-Zahlen über alle Zeilen müssen sämtliche früher veröffentlichten Zähler pro Sitz reproduzieren.

Nur bei bestandenem Archivvergleich spielen zunächst 16 neue Karten (7284000–7284015), je beide Sitze. V14, R3, R5 und R7 spielen dort gegen Solution und den nativen Kaggle-Agenten. Zusätzlich spielt R7 direkt gegen V14. Für die Nominierung muss er mindestens zwei zusätzliche externe Siege gegenüber V14, mindestens dessen Zahl an Solution-Siegen und eine direkte Mehrheit erreichen. Über beide externen Gegner zusammen muss er auch mindestens so viele Spiele gewinnen wie jeder der beiden einzelnen Erweiterungen R3 und R5. Die Unterschiede zu R3 und R5 auf denselben Spielschlüsseln werden einzeln berichtet.

Ein positiver Auswahllauf rechtfertigt einen getrennten Vergleich auf 60 weiteren Karten, extern 7284100–7284159 und direkt 7284200–7284259. Beide Sitze einer Karte und externe Gegner werden gemeinsam 10.000-mal mit Zurücklegen gezogen (PCG64, 2711). Im externen Vergleich zu V14 muss die untere 95-%-Grenze des Vorteils über null und im direkten Duell die Untergrenze der Siegquote über 50 % liegen. Gegen Solution soll der Punktschätzer mindestens V14 erreichen. Für eine Ablösung müssen außerdem der aktuell stärkste freigegebene Agent, die Kurs- und Paketprüfung und die Sicherung berücksichtigt werden. Ein höherer Anteil nachgeahmter Lehrerzüge belegt noch keine höhere Siegquote.

## Reproduktion

Im festgehaltenen Studienstand ausführen. `M` zeigt auf das Hauptrepo mit den ursprünglichen Archiven. Die beiden Ausgaben müssen neu sein. Trainingsdaten, veröffentlichte Modellpfade und Abgabe erhalten keine Schreibzugriffe. Das Audit braucht die beiden ursprünglichen Messberichte im Hauptrepo.

```sh
M=/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15
P="$M/.venv/bin/python"
A="$M/experiments/imitation"
C="$M/experiments/candidates/movement_dagger_20261115"
O="$A/final_20261115_r7_combined/student.pth"
"$P" -m scripts.combined_movement train --controls "$C" --parent "$A/final_20261115_selective/student.pth" \
  --original-data "$A/final_20261115_v14_advice" --mixed-data "$A/final_20261115_movement_dagger" --device auto --out "$O"
"$P" -m scripts.combined_movement audit --controls "$C" --candidate "$O" --reports "$M/experiments/analysis" \
  --data "$A/final_20261115_v14_advice" "$A/final_20261115_movement_dagger" \
  --out "$M/experiments/analysis/combined_movement_20261115/paired_validation.json"
```

Für die exakt ausgeführte Trainingsfassung dient Git-Stand `0105658188b2ec5eaf5c3a4b0ef477be9a1412f8` als Basis. Darüber liegen `agents/sherlock/own_command.py`, `scripts/imitate.py`, `scripts/imitation_storage.py`, `scripts/own_command_study.py`, `scripts/selective_advice_agent.py`, `scripts/selective_agreement.py`, `scripts/selective_dagger.py` und `tests/test_own_command.py` aus `f4c55d6919d98d84cd258beac6f11ad8a3676869`, anschließend die vier Dateien dieser R7-Erweiterung. Der ausgeführte Trainingscode wird im Checkpoint an seine tatsächlichen Dateiprüfsummen gebunden.
