# Sicherung der Abgabe v12_fog

Bytegleiche Kopien vor der Uebernahme von `v13_neb` (20261101). SHA-256 beider Dateien: `b258dc9927a7094f3d4b83bf4de251b03c3ccc57d69a1da23080c27e806c924b`.

## Wiederherstellen (vom Projektverzeichnis, bei gestoppten Laeufen)

```bash
shasum -a 256 experiments/releases/20261101_v12_fog/agent_p0.pth experiments/releases/20261101_v12_fog/agent_p1.pth
cp experiments/releases/20261101_v12_fog/agent_p0.pth agents/sherlock/weights/agent_p0.pth
cp experiments/releases/20261101_v12_fog/agent_p1.pth agents/sherlock/weights/agent_p1.pth
shasum -a 256 agents/sherlock/weights/agent_p0.pth agents/sherlock/weights/agent_p1.pth
```

Danach Kurspruefung (`python -m scripts.check_candidate_runner`) und eigenen Commit.
