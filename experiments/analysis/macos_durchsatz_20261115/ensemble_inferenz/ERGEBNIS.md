# Dieselben 36 Netze berechnen einen Zug auf dem M3 schneller

Sherlock kann die 36 gleich aufgebauten Netze schichtweise gemeinsam auswerten. Auf 1.800 echten Kartenbeobachtungen (19.230 Einheitsentscheidungen) erreichte die gemeinsame Rechnung etwa den **dreifachen Durchsatz der bisherigen Netzauswertung**. Beleuchtung der Karte, Gedächtnis und taktische Regeln benötigen zusätzlich Zeit. Über das vollständige Nachspielen von 606 Agentenzügen sank die mediane Laufzeit deshalb von **10,69 auf 8,82 Sekunden** (−17,5 %).

| Prüfung | Ergebnis |
|---|---:|
| Gleiche beste erlaubte Aktion nach Netzbewertung | 19.230/19.230 |
| Beobachtungen mit vollständig bitgleichen Q-Werten | 1.551/1.800 |
| Größte absolute Rundungsabweichung der Q-Werte | 0,00000763 |
| Übereinstimmende vollständige Weltbefehle auf Karte 4242 | 606/606 in jeder Wiederholung |

Beide Verfahren verwendeten dieselbe V14-Gewichtsdatei und einen Torch-Thread. Die sechs aufgezeichneten Spielverläufe für die Netzprüfung stammen von R3 und enthalten beide Sitze sowie drei Gegner. Für die vollständigen Befehle spielten beide Verfahren den getrennten V14-Kursverlauf zweimal nach. Gemessen wurde die Zeit für die Agentenaktionen einschließlich Einlesen der gespeicherten Beobachtungen und Fehlerkontrolle, bei gleichzeitig laufenden anderen Studien. Der Geschwindigkeitsgewinn für vollständige Turnierpartien hängt auch von Gegner und Spielumgebung ab.

Alle ursprünglichen Gewichte und die abschließende Mittelwertbildung bleiben Teil der gemeinsamen Rechnung. Einige Q-Werte weichen durch Gleitkommaarithmetik geringfügig ab. Für neue Versuche ist deshalb eine zusätzliche Gegenprobe im gewöhnlichen Spielevaluator vorgesehen. Die bereits laufende 400-Karten-Bestätigung verwendet die ursprüngliche Berechnung.

Zum Wiederholen im Desktopprojekt mit den sechs archivierten NPZs:

```sh
.venv/bin/python -B experiments/analysis/macos_durchsatz_20261115/ensemble_inferenz/benchmark.py --project . --out /tmp/sherlock-qvergleich.json
```

[Messplan](PLAN.md) · [Einzelzeiten und Prüfsummen](result.json)

## Gegenprobe mit vollständigen Partien

Der gewöhnliche parallele Evaluator hat die originale Solution und den Kaggle-Dritten auf 7158000–7158002 jeweils auf beiden Sitzen gespielt. Derselbe V14 trat je zwölfmal in der ursprünglichen und in der beschleunigten Auswertung an. **Alle 7.272 verglichenen Befehlsmatrizen beider Spieler** (12 gepaarte Partien × 303 Züge × zwei Spieler), alle 36 Matchendstände und alle zwölf Gesamtergebnisse stimmten überein. Auch die zwölf früher veröffentlichten V14-Spielstände konnten reproduziert werden. Diese 24 technischen Ausführungen gehören nicht zur Siegstatistik eines neuen Agenten.

Für neue Vergleichsläufe bietet `scripts.par_eval` die Option `--packed-v14`. Sie gilt für die ursprünglichen 36 V14-Netze im CPU-Spielmodus und betrifft nur den ausgewerteten Agenten. Ein Aufruf ohne diesen Schalter nutzt den bisherigen Rechenweg. Der Gegner und die Spielumgebung liefen in beiden Armen auf den ursprünglichen Pfaden. Für eine Wiederholung der Gegenprobe werden die ursprünglichen Referenz-CSV und der lokal installierte Kaggle-Gegner benötigt.

```sh
.venv/bin/python -m scripts.v14_packed_parity run --out /tmp/v14-spielvergleich --reference experiments/analysis/umbau_20261115/confirm/v14_ref.csv
.venv/bin/python -m scripts.v14_packed_parity verify --out /tmp/v14-spielvergleich --reference experiments/analysis/umbau_20261115/confirm/v14_ref.csv
```

[Alle gepaarten Endstände](spielvergleich.json) · [Vollständige Befehle und Quellenbindung](spielbefehle.tar.gz)
