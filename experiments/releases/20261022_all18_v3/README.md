# Sicherung der Abgabe all18_v3

Bytegleiche Kopien vor der Uebernahme von `v7_Bsnpd` (20261022). SHA-256 beider Dateien: `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`.

## Wiederherstellen (vom Projektverzeichnis, bei gestoppten Laeufen)

```bash
shasum -a 256 experiments/releases/20261022_all18_v3/agent_p0.pth experiments/releases/20261022_all18_v3/agent_p1.pth
cp experiments/releases/20261022_all18_v3/agent_p0.pth agents/sherlock/weights/agent_p0.pth
cp experiments/releases/20261022_all18_v3/agent_p1.pth agents/sherlock/weights/agent_p1.pth
shasum -a 256 agents/sherlock/weights/agent_p0.pth agents/sherlock/weights/agent_p1.pth
```

Danach Kurspruefung (`python -m scripts.check_candidate_runner`) und eigenen Commit.
