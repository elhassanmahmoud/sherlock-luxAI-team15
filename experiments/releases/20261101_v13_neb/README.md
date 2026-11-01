# Sicherung der Abgabe v13_neb

Bytegleiche Kopien vor der Uebernahme von `v14_rescue` (20261101). SHA-256 beider Dateien: `6d00b6c52366a613eed3b7b5b6f9c3c088802716a85c30fe192c46c57bdd8e62`.

## Wiederherstellen (vom Projektverzeichnis, bei gestoppten Laeufen)

```bash
shasum -a 256 experiments/releases/20261101_v13_neb/agent_p0.pth experiments/releases/20261101_v13_neb/agent_p1.pth
cp experiments/releases/20261101_v13_neb/agent_p0.pth agents/sherlock/weights/agent_p0.pth
cp experiments/releases/20261101_v13_neb/agent_p1.pth agents/sherlock/weights/agent_p1.pth
shasum -a 256 agents/sherlock/weights/agent_p0.pth agents/sherlock/weights/agent_p1.pth
```

Danach Kurspruefung (`python -m scripts.check_candidate_runner`) und eigenen Commit.
