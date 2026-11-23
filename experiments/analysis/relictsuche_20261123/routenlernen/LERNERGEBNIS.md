# Gezielte Richtungswahl für ein freies Schiff

Der gelernte Bewerter wählte auf getrennten Karten Suchwege, die den geometrischen Abstand zum tatsächlichen ersten Reliktpaar stärker verkürzten als eine Fortsetzung der ursprünglichen V16-Richtung. Der Unterschied im zusammengesetzten Lehrerwert betrug **+1,05** mit einem gepaarten 95-%-Kartenintervall von **+0,72 bis +1,37**. Gegen die Route mit dem höchsten Anteil zuvor ungesehener Felder betrug er **+0,52** [ +0,18 bis +0,86 ]. In diesem Maß sind gesparte Bewegungsschritte, der Vorsprung vor anderen Schiffen und eine mögliche Sicht nach dem Reliktstart enthalten. Ob früherer Kontakt mehr Spielpunkte oder ganze Siege bringt, wird separat im Spiel gemessen.

| Daten | Karten | Karten mit auswertbarer Wahl | Richtungsentscheidungen | Bewertete Strecken |
|---|---:|---:|---:|---:|
| Training | 320 | 310 | 2.265 | 76.279 |
| Getrennte Offlineprüfung | 128 | 125 | 928 | 30.413 |

Die Trainingskarten lagen zwischen 161030002 und 161031118, die Prüfkarten zwischen 161040020 und 161040496. Die Erhebung nahm in getrennten Blöcken jeweils die ersten Karten mit öffentlicher Sensorreichweite eins. Eine Richtungsentscheidung besteht aus den zulässigen Alternativen eines einzigen Schiffs. 64 zusätzliche Lerngruppen und 19 Prüfgruppen mit dem Schiff auf einem öffentlich unbegehbaren Feld hatten keine ruhende Vergleichsstrecke. Auf solchen Eingaben gibt die neue Richtungswahl keinen eigenen Vorschlag ab.

Die 48 öffentlich berechneten Merkmale beschreiben den acht Schritte langen Suchweg, Abstände zu anderen Schiffen, Sichtalter, bisher besuchte Felder sowie die Energie- und Hindernissituation. Ein neuronales Netz mit 32 verborgenen ReLU-Einheiten lernt aus der Strecke und dem tatsächlichen ersten Reliktpaar, welchen Annäherungswert sie hat. Die ersten 256 Trainingskarten und die letzten 64 bestimmten die Trainingsdauer. Vier Epochen erreichten in der internen Auswahl einen mittleren Wert von 1,738 gegenüber 1,689 nach zehn und 1,635 nach zwanzig Epochen. Der endgültige Fit auf allen 320 Trainingskarten erforderte 400 Gewichtsaktualisierungen. Die 128 späteren Karten hatten keinen Einfluss auf Architektur, Gewichte oder Eingriffsschwelle.

Im Mittel wechselte der Modellvorschlag auf 64,9 % der auswertbaren Entscheidungen die erste Bewegungsrichtung. Die Richtung des ursprünglichen V16-Befehls war in 98,7 % der Fälle im begehbaren Streckenangebot vertreten. Die Vergleichsfortsetzung nimmt unter den öffentlich möglichen Strecken mit dieser Richtung die mit den wenigsten seitlichen Schritten. Fehlt eine solche Strecke, erhält sie die ruhende Referenz. Die Sicherheitsprüfung wird in jedem echten Zug neu ausgeführt. Nach dem ersten Fund bzw. eigenen Punkt geht die weitere Bewegung an V16. Die maximal eine geänderte Einheit pro Zug gehört immer zu derselben Schiffs-ID der Partie. Die tatsächliche Aktion wird in V16s Welt- und Richtungsgedächtnis eingetragen.

[Vorabplan](PLAN.md) · [Modellgewichte](routengewichte.json) · [Fit, interne Auswahl und Rohdaten-Hashes](training.json) · [Unabhängige Kartenprüfung](offline.json) · [Streckenmerkmale](routes.py) · [Geometrische Lehrerlabels](collect.py) · [Laufzeitagent](kandidat.py)

## Nachrechnen

Im Projektstamm wird die für dieses Projekt eingerichtete Python-3.13-Umgebung verwendet. Die folgenden Befehle erfassen die Lern- und Prüferöffnungen, passen die Gewichte an und prüfen die fertige Schätzung. Vorhandene Rohkarten im externen Experimentordner werden wiederverwendet. Die JSON-Berichte führen den Hash jeder verwendeten Karte auf. Das veröffentlichte Modell enthält 1.601 trainierte Parameter.

```sh
export PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1
d=experiments/analysis/relictsuche_20261123/routenlernen
python "$d/collect.py" all
python "$d/fit.py" fit
python "$d/fit.py" validate
python "$d/pruefen.py" smoke
python "$d/pruefen.py" replay
python "$d/auswertung.py"
python "$d/paket.py"
python "$d/nachpruefen.py"
```

Die Daten liegen unter `experiments/imitation/relictsuche_20261123/routenlernen` im Desktop-Checkout. Der Unterordner `direction_train` enthält Richtungslabels aus 320 Eröffnungen, `direction_valid` diejenigen aus 128 anderen Eröffnungen. Die ältere, vor der Aufgabentrennung angelegte Ortsverteilung und ihre Teilmenge an Verlaufsdaten flossen in keinen dieser beiden Datensätze oder Modellfits ein.
