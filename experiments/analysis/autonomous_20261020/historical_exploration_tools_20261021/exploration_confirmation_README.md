# Frische Bestätigung und bedingter Direktvergleich

Vorbereitet, noch nicht ausgeführt. `exploration_confirmation.py` muss neben dem unveränderten `exploration_ensemble_eval.py` liegen. Der Helper wird vor dem Import gegen SHA-256 `27faea85202b6149aced00bd4c1cd85fd654101d7cbbcf7567fb713becd8099e` geprüft. Beide Dateien vor dem Entwicklungslauf archivieren; danach bleiben HEAD und alle Pythonquellen während Entwicklung, Bestätigung und Direktvergleich eingefroren. Bei Ausführung aus `/tmp` ist das Repository das Arbeitsverzeichnis; unter `experiments/analysis/autonomous_20261020/tools/` wird es aus `__file__.parents[4]` abgeleitet.

Reine Tests:

```sh
python3 -B /tmp/exploration_confirmation.py --self-test
```

Erst nach geprüftem vollständigem Entwicklungslauf, bei ausreichend Zeit und ohne andere schwere Arbeit:

```sh
.venv/bin/python -B /tmp/exploration_confirmation.py --run
```

Der Runner liest ausschließlich den bestehenden Entwicklungslauf aus `experiments/compare/autonomous_20261020/exploration_ensemble_development/`. Er verlangt dessen vollständigen Zustand, genau fünf vollständige 240er-CSVs, unveränderte CSV-/Quell-/Interpreter-/Modell-/Referenzhashes, identische Anfangs- und Endidentität erfolgreiche Rückgabecodes, exakt vorgesehene Befehle sowie eine aus allen fünf CSVs erneut berechnete identische Auswahlentscheidung. Der echte Preflight berechnet dazu NumPy-Statistik erst nach dem Idlecheck neu; Selbsttests laden keine numerischen Bibliotheken. Nur `v3_control3` oder `v3_slow3` mit 21 Netzen ist zulässig. Es wird keine Auswahl erneut optimiert und kein zweiter Kandidat ausprobiert. Die gemeinsame Inferenzconfig muss dem eingefrorenen Buildermanifest entsprechen; Checkpointdateien bleiben unverändert, ohne Config-Overrides.

Neue Ausgaben entstehen exklusiv unter:

`experiments/compare/autonomous_20261020/exploration_ensemble_confirmation/`

Vorhandene oder teilweise Ausgaben werden abgewiesen. Der Ablauf ist fest:

1. Eingefrorene installierte Referenz: 800 Spiele auf 510200–510399, beide Seiten, Default und Solution92.
2. Genau der im Entwicklungslauf ausgewählte Kandidat: dieselben 800 Keys. Die beiden vollständigen Datensätze ergeben zusammen 1.600 Spiele.
3. Gepaarte Differenz pro Karte, beide Seiten zusammen; 5.000 Bootstrap-Ziehungen, Seed 0. Solution92-Differenz und untere 95%-Grenze müssen strikt positiv sein; Default-Verlust darf höchstens 2 Prozentpunkte betragen. Die Default-Grenze wird in ganzzahligen Halbresultaten geprüft.
4. **Nur bei bestandenem frischem Gate:** 120 direkte Spiele des Kandidaten gegen die unveränderte eingefrorene Referenz auf 500720–500779, beide Seiten. 60 Karten werden gemeinsam mit ihren beiden Seiten resampelt; 5.000 Ziehungen, Seed 0. Untere 95%-Grenze des mittleren Resultats muss strikt über 0,5 liegen.

Bei einem statistischen Gatefehler endet der Runner korrekt mit `complete: true` und einer `no_promotion_*`-Entscheidung. Ein fehlender qualifizierter Entwicklungssieger wird bereits vor Ausgabeerstellung abgewiesen. Technische Fehler, unvollständige Daten, geänderte Hashes oder Abbruch ergeben `complete: false`. Selbst beim Bestehen aller Gates lautet die Entscheidung nur `ready_for_technical_review`; es gibt keine Promotion und keine Schreiboperation an Abgabegewichten.

Alle Jobs laufen nacheinander mit höchstens zwei Evaluationsworkern und einem Thread pro numerischer Bibliothek. Logausgabe bleibt live. Bekannte schwere Fremdjobs verhindern den Start; die Prozessprüfung ersetzt keine globale Ressourcensperre. Quellen, abgeschlossene CSVs und Entwicklungsevidenz werden vor und nach Jobs und währenddessen etwa alle 30 Sekunden geprüft. SIGINT, SIGTERM, SIGHUP, Fehler und Deadline beenden ausschließlich die eigene Prozessgruppe. Keine neuen Jobs nach 21.10.2026 03:00 UTC (05:00 Berlin); Abbruchreserve ab 03:59:50 UTC vor der 04:00-UTC-Deadline.

`state.json` hält Rohbefehle, Phasen, Zeiten, CSV-Hashes, Gatewerte, die vorab festgelegten Modelle/Config und Quellidentität fest. Der vollständige Entwicklungslauf und der Runner selbst bleiben zusätzliche gehashte Eingaben. Die Vorbereitung prüft synthetische Schemas, Gates, Gruppenabgrenzung und Evidenzänderungen ohne Torch/JAX/NumPy. Reale Prozess-/Spielintegration bleibt erst dem freigegebenen Lauf vorbehalten.
