# CNN3-Verfügbarkeit – 21.10.2026

Geprüft: 2026-10-21T08:15:35.440800+00:00; Remote-main `ec29a17ef3f0beb77ba921036752e1c3aa6ecf57`.

**Ergebnis: Die Originalgewichte sind über die geprüften verfügbaren Wege weiterhin nicht abrufbar.** Keine großen Dateien heruntergeladen, kein Training/Experiment und keine Nachricht an Mahmoud.

## Genau benötigte Originaldateien

- Für Reproduktion des gemeldeten frischen Ergebnisses: `experiments/ppo/cnn3/ppo_0050.pth` (im Pipeline-Log als ausgewählter Stand verzeichnet).
- Für den BC-Ausgangspunkt beziehungsweise eine BC/PPO-Konsistenzprüfung: `experiments/ppo/cnn3/bc.pth`.
- Für den letzten Trainingsstand gegebenenfalls `experiments/ppo/cnn3/ppo_0060.pth`; dieser ersetzt nicht den ausgewerteten Stand 0050.
- Herkunft laut vorhandenen Logs: Mahmouds Rechner, Laufordner `/Users/elhassanmahmoud/Documents/AKI_LuxAgent15/experiments/ppo/cnn3/`. Lehrer laut `teacher.json` und collect-Log: `experiments/ensembles/all18_fo10.pth`, 1200 gesammelte Spiele; BC mit 48 Kanälen und 4 Blöcken. Einzelne CLI-Defaults in BC/PPO-Logs sind kein Nachweis der tatsächlich gespeicherten Checkpoint-Config.
- Für CNN3 selbst sind weder verifizierbare SHA-256-Werte noch Dateigrößen oder ein Downloadlink dokumentiert. Originaldateien samt Hashes und gespeicherter Config bleiben erforderlich; Hashes wurden nicht erfunden.

## Nachweise

1. Lokal enthält `experiments/ppo/cnn3/` keine `.pth`-Dateien. Git meldet ausdrücklich die Ignore-Regel `.gitignore:23: experiments/ppo/**/*.pth`.
2. Remote `main`, alle drei weiteren veröffentlichten Branchspitzen und beide veröffentlichten Tags per `git ls-remote --heads --tags` ermittelt und ihre lokal verfügbaren Git-Bäume geprüft: keine CNN3-Gewichte. Die erreichbare lokale Git-Historie enthält für CNN3 nur Logs, CSV, `teacher.json` und Pipeline-Skript, keine Checkpoints.
3. Git-LFS-CLI ist nicht installiert. Ersatzweise veröffentlichte Git-Bäume und sämtliche darin enthaltenen `.gitattributes` geprüft: keine CNN3-Datei/LFS-Pointer und keine LFS-Filterregel. Die vorhandenen Attribute regeln ausschließlich CSV-Zeilenenden. Nicht referenzierte serverseitige LFS-Objekte lassen sich dadurch nicht ausschließen, liefern aber keinen auffindbaren Downloadweg.
4. GitHub Releases über die bestehende authentifizierte GitHub-Verbindung read-only abgefragt: `GET https://api.github.com/repos/elhassanmahmoud/sherlock-luxAI-team15/releases?per_page=100` liefert `[]`; damit keine sichtbaren Releases oder Release-Assets. Die lokale `gh`-CLI fehlt, daher wurde die vorhandene Verbindung genutzt.
5. Repository-Dokumentation, JSON-Metadaten und Skripte nach CNN3/0050/Download-/LFS-Hinweisen durchsucht: kein dokumentierter direkter Download. `docs/ARBEITSSTAND.md` bezeichnet CNN3-Checkpoints ausdrücklich als gitignored. README und Morgenbericht bestätigen die fehlenden Originaldateien.
6. Der vorhandene Kandidat `experiments/candidates/cnn2_ppo0040.pth` ist CNN2 und kein Ersatz für CNN3.

**Abgrenzung:** Geprüft sind sichtbare Repository-Refs, lokale erreichbare Historie, sichtbare GitHub-Releases und dokumentierte Links. Keine Aussage über unveröffentlichte Dateien auf Mahmouds Rechner oder andere nicht dokumentierte Speicherorte.
