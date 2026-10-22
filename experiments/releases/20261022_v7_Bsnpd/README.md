# Sicherung der Abgabe v7_Bsnpd

Bytegleiche Kopien vor der Uebernahme von `v10_V8st` (20261022). SHA-256 beider Dateien: `c394acba84f7a298f8f1e6107328d8e6ce151b367a28997b059aa82fc8a895e6`.

## Wiederherstellen (vom Projektverzeichnis, bei gestoppten Laeufen)

```bash
shasum -a 256 experiments/releases/20261022_v7_Bsnpd/agent_p0.pth experiments/releases/20261022_v7_Bsnpd/agent_p1.pth
cp experiments/releases/20261022_v7_Bsnpd/agent_p0.pth agents/sherlock/weights/agent_p0.pth
cp experiments/releases/20261022_v7_Bsnpd/agent_p1.pth agents/sherlock/weights/agent_p1.pth
shasum -a 256 agents/sherlock/weights/agent_p0.pth agents/sherlock/weights/agent_p1.pth
```

Danach Kurspruefung (`python -m scripts.check_candidate_runner`) und eigenen Commit.
