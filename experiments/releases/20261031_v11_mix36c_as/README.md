# Sicherung der Abgabe v11_mix36c_as

Bytegleiche Kopien vor der Uebernahme von `v12_fog` (20261031). SHA-256 beider Dateien: `2ab463e9034357a40cb721b34286ad1f9bad250629bf9f9f17b1d175157cd2e0`.

## Wiederherstellen (vom Projektverzeichnis, bei gestoppten Laeufen)

```bash
shasum -a 256 experiments/releases/20261031_v11_mix36c_as/agent_p0.pth experiments/releases/20261031_v11_mix36c_as/agent_p1.pth
cp experiments/releases/20261031_v11_mix36c_as/agent_p0.pth agents/sherlock/weights/agent_p0.pth
cp experiments/releases/20261031_v11_mix36c_as/agent_p1.pth agents/sherlock/weights/agent_p1.pth
shasum -a 256 agents/sherlock/weights/agent_p0.pth agents/sherlock/weights/agent_p1.pth
```

Danach Kurspruefung (`python -m scripts.check_candidate_runner`) und eigenen Commit.
