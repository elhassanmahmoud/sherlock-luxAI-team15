# Das nachtrainierte Bewegungsnetz im Kursformat

Der Forschungsagent und der separat aus dem Archiv geladene Kursagent gaben auf Karte 7271000 für beide Startpositionen in jedem der 303 Züge dieselbe vollständige Befehlsmatrix aus. Dieser Vergleich wurde unter Python 3.13.13 und 3.10.15 durchgeführt. Auch zwischen den Versionen stimmen beide 303 Züge langen Folgen bytegenau überein. Alle Kursaufrufe von `update` und `save_agent` ließen die Gewichte unverändert. Beide Sitze führten Schüsse mit Zielversatz aus und zeigten gegenüber dem ursprünglichen R3 mindestens eine andere Aktion.

Der Bewegungsberater ist ein einzelnes nachtrainiertes CNN mit einer Kartenansicht. Der ursprüngliche V14 mit 36 Netzen gibt die Grundbefehle. Der Kurs importiert `agents.sherlock.main.Agent_x`; beide Sitze laden `agents/sherlock/weights/agent.pth`. Die Kurs-ZIP liegt lokal im Hauptprojekt neben diesem Bericht unter `midpoint-kandidat.zip`. Zwei getrennte Paketbauten ergaben dieselben Bytes. Die technischen Prüfungen betreffen eine bekannte Karte. Die Spielstärke wird auf eigenen unabhängigen Vergleichskarten gemessen.

| Datei | SHA-256 |
| --- | --- |
| Kurs-ZIP | `b9bb2c26cdd0fc7ad88906e287fac6f50e6e9ed9c1a1540fb285999999c292a2` |
| Paketierte Gewichtsdatei | `61b495be9c87dfba36f5747154a367402f49c76897eb63098caadedd7a919e8f` |
| V14 im Paket | `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8` |
| Beratungsnetz | `51a52f0453d5ac8e9a4ea70b3792572356761054cb2890520005160f77097cf2` |

## Reproduktion

Im Repository mit torch 2.14.1 bauen. Für eine tatsächliche Kursprüfung die übliche Lux-Umgebung mit drei Matches nutzen. Der erste 3.10-Versuch brach beim Import des Solution-Gegners ab, weil der lokale Mac die installierte SciPy-1.15.3-Bibliothek nicht laden konnte. Der ausgewiesene vollständige 3.10-Lauf verwendet dieselbe separat geprüfte SciPy-1.14.1-Installation wie der V15-Kurstest. Sämtliche Quellen und Modellbefehle des Kandidaten sind in beiden Läufen dieselben.

```sh
TMPDIR_KURS=$(mktemp -d)
mkdir "$TMPDIR_KURS/research"
git archive 0105658188b2ec5eaf5c3a4b0ef477be9a1412f8 agents scripts lux | tar -x -C "$TMPDIR_KURS/research"
.venv/bin/python -B -m scripts.build_r3_course_candidate --midpoint --repo . --out "$TMPDIR_KURS/midpoint-kandidat.zip"
.venv/bin/python -I scripts/check_r3_course_parity.py --midpoint --zip "$TMPDIR_KURS/midpoint-kandidat.zip" \
    --research "$TMPDIR_KURS/research" --v14 "$TMPDIR_KURS/research/agents/sherlock/weights/agent_p0.pth" \
    --r3 experiments/candidates/r8_warm_20261115/midpoint.pth --out "$TMPDIR_KURS/paritaet.json"
```

[Ergebnisse unter Python 3.10](python310.json) · [Ergebnisse unter Python 3.13](python313.json) · [Spielergebnisse der Vorauswahl](../VORAUSWAHL.md).
