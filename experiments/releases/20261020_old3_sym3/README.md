# Sicherung der bisherigen Abgabe

Die beiden Dateien sind bytegleiche Kopien der Abgabe vor der am 20.10.2026
freigegebenen Übernahme eines nachweislich besseren Kandidaten. Herkunft,
Dateigrößen und SHA-256 stehen in `manifest.json`. Beide Hashes:
`3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.

Diese Sicherung nicht für Trainingsausgaben verwenden oder überschreiben.
Sie wird mit Git geteilt, damit Mahmoud denselben Rückfallstand besitzt.
Die Sicherung allein bedeutet noch keine Übernahme eines neuen Kandidaten.

## Gewichte wiederherstellen

Vom Projektverzeichnis aus, bei gestoppten Läufen:

```bash
shasum -a 256 experiments/releases/20261020_old3_sym3/agent_p0.pth experiments/releases/20261020_old3_sym3/agent_p1.pth
```

Nur wenn beide Hashes dem Manifest entsprechen, die Sicherung zurückkopieren:

```bash
cp experiments/releases/20261020_old3_sym3/agent_p0.pth agents/sherlock/weights/agent_p0.pth
cp experiments/releases/20261020_old3_sym3/agent_p1.pth agents/sherlock/weights/agent_p1.pth
shasum -a 256 agents/sherlock/weights/agent_p0.pth agents/sherlock/weights/agent_p1.pth
```

Danach die Kursprüfung mit einem neuen Berichtspfad ausführen und die
Wiederherstellung als eigenen Commit dokumentieren. Dieser Rückweg stellt
die Gewichte einschließlich gespeicherter Konfiguration wieder her, nicht
zwischenzeitliche Änderungen am Agenten-Code. Den damaligen Code findet
man bei Bedarf über `source_commit` im Manifest.
