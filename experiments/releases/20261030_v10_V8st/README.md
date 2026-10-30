# Sicherung der Abgabe v10_V8st

Bytegleiche Kopien vor der Uebernahme von `v11_mix36c_as` (20261030). SHA-256 beider Dateien: `03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67`.

## Wiederherstellen (vom Projektverzeichnis, bei gestoppten Laeufen)

```bash
shasum -a 256 experiments/releases/20261030_v10_V8st/agent_p0.pth experiments/releases/20261030_v10_V8st/agent_p1.pth
cp experiments/releases/20261030_v10_V8st/agent_p0.pth agents/sherlock/weights/agent_p0.pth
cp experiments/releases/20261030_v10_V8st/agent_p1.pth agents/sherlock/weights/agent_p1.pth
shasum -a 256 agents/sherlock/weights/agent_p0.pth agents/sherlock/weights/agent_p1.pth
```

Danach Kurspruefung (`python -m scripts.check_candidate_runner`) und eigenen Commit.
