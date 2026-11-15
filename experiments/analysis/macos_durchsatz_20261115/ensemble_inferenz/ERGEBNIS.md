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
