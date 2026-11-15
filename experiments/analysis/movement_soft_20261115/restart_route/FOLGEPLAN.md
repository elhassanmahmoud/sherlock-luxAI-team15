# R3-Frühroute auf vollständigen und neuen Karten

Am 15. November vor dem Folgeversuch festgelegt. Die gezielte historische Gegenprobe rettete die einzige Niederlage von R3 gegen Solution und hielt die fünf vorherigen Rettungen sowie die sechs anderen Startpositionen. Diese zwölf Positionen wurden anhand der ursprünglichen Ergebnisse ausgewählt. Der neue Kandidat verwendet exakt den geprüften R3-Checkpoint und dieselbe frühe Wegentscheidung.

1. Auf dem bereits bekannten Solution-Satz 7273100–7273159 werden die zwölf vorhandenen Routenergebnisse übernommen. Die übrigen 108 Positionen spielt ausschließlich die Routenvariante. Die ursprünglichen vollständigen V14- und R3-Ergebnisse bilden die Referenzen. Alle 120 Positionen sind Entwicklungsdaten. Der Ausgang entscheidet nicht über den Start der nächsten Stufe.
2. Auf den neuen 60 Karten 7283000–7283059 spielen V14, der normale R3-Bewegungsberater und R3 mit Frühroute je 120 Spiele gegen Solution. Beide Startpositionen werden verwendet. Für den nächsten Schritt muss die Route mindestens die Zahl ganzer Siege von R3 und mehr ganze Siege als V14 erreichen. Für beide Vergleiche werden auch die Kippfälle, die Matchsiege und ein gepaartes 95-%-Intervall berichtet.
3. Nur bei erfüllter Solution-Bedingung werden auf denselben 60 Karten V14 und R3 mit Route je 120-mal gegen den nativen Kaggle-Drittplatzierten gespielt. Der direkte Vergleich R3 mit Route gegen V14 findet auf 60 anderen Karten 7283100–7283159 mit beiden Sitzen statt. Über beide externen Gegner muss die untere Grenze des gepaarten 95-%-Intervalls für den Sieganteilsunterschied über null liegen. Für die direkte Siegquote muss die Untergrenze über 50 % liegen. Bootstrap mit 10.000 Ziehungen ganzer Karten und Seed 2711, externe Gegner und beide Sitze innerhalb einer Karte gemeinsam.

Wenn der direkte Nachweis gegen V14 gelingt und die Routenvariante auf Solution nur gleichauf mit R3 liegt, bleibt der zusätzliche Nutzen der Route gegenüber R3 offen. Jede Übernahme erfordert zusätzlich die separate Default-, Kurs-, Paket- und Sicherungsprüfung. Der Solution-Satz wird als vorgelagerte Auswahl für den zweiten Gegner verwendet. Das externe Intervall muss zusammen mit dieser Auswahl beschrieben werden. [Gezielte Gegenprobe](PLAN.md).

## Ausführung

Die Spielquelle ist die Archivkopie von `0105658` mit demselben R3-Adapter und demselben Routenmodul wie im gezielten Versuch. Hinzu kommen die in diesem Plan verlinkten Folgemodule und die nativen Kaggle-Gegnerdateien. Identität des ursprünglichen R3-Laufs, reale R3-/V14-Gewichte, Laufzeit und die vollständigen Quelldateien werden in jedem Lauf geprüft. In den zwölf importierten Entwicklungspositionen werden beide gespeicherten Aktionsströme, das Maßnahmenprotokoll und die ursprünglichen V14-/R3-Ergebnisse kontrolliert. Die übrigen Positionen erhalten je eine neue vollständige Partie. Jeder Aufruf belegt einen Worker. `P` bezeichnet `experiments/analysis/movement_soft_20261115`, `R3` die Datei `experiments/candidates/movement_dagger_20261115/r3_soft.pth`; beide Pfade absolut angeben.

```bash
A=(--confirmation "$P/confirmation" --dev "$P/restart_route/dev" --r3 "$R3" --out "$P/restart_route/followup")
"$PY" -m scripts.r3_route_games "${A[@]}" development route
"$PY" -m scripts.r3_route_assess "${A[@]}" development
for arm in v14 r3 route; do
  "$PY" -m scripts.r3_route_games "${A[@]}" solution "$arm" || exit 1
done
"$PY" -m scripts.r3_route_assess "${A[@]}" solution
```

Bei erfüllter Solution-Bedingung die beiden externen Kaggle-Arme und das direkte Duell ausführen.

```bash
"$PY" -m scripts.r3_route_games "${A[@]}" kaggle v14 &&
"$PY" -m scripts.r3_route_games "${A[@]}" kaggle route &&
"$PY" -m scripts.r3_route_games "${A[@]}" direct route &&
"$PY" -m scripts.r3_route_assess "${A[@]}" confirm
```

Die drei Auswertungen landen unter `followup/{development,solution,confirm}/assessment.json`. Jede Auswertung verweist auf ihre einzelnen versiegelten Eingabedateien. [Spielwerkzeug](../../../../scripts/r3_route_games.py) · [Paarvergleich](../../../../scripts/r3_route_assess.py).
