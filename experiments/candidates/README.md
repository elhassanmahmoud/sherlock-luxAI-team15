# Kandidaten-Gewichte (zum Teilen im Team)

Auf Wunsch von Moayed und Mahmoud (20.10.2026) liegen die aktuellen Kandidaten hier
**versioniert**, damit beide Arbeitsumgebungen mit identischen Dateien arbeiten.
Das ist **keine** neue Abgabe: `agents/sherlock/weights/` bleibt unverändert, bis die
Übernahme ausdrücklich beschlossen ist.

| Datei | Inhalt | SHA-256 | Ergebnis (frische Karten, beide Seiten) |
|---|---|---|---|
| **`all18_v3.pth`** (bester Stand 20.10. abends) | `all18_fo10` + `pt_sap` + `far_cand` in der Config | `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935` | 502220–502419: default 400/400, Solution_92 78,5 % (`all18_fo10` dort 71,75 %, +6,75, KI [+1,8; +12,0]) |
| `all18_fo10.pth` | 18 DQN-Netze (rules6 + sol70 + opp), Config inkl. `keep_dead_fast`, `far_opp=10` | `b2b7ffcc506d71a4657bb8990a71c0b25c4535f0f41564054ff687a1fa7b4607` | 501620–501819: default 400/400, Solution_92 320/400 = 80,0 %; 501820–502019: 400/400, 74,75 % |
| `all24fo.pth` | `all18` + 6 Netze `full_rules_fo`, Config inkl. `keep_dead_fast`, `far_opp=10` | `e9ff09a64ae0327e49ea8a4c0810abcf47bf2f1b05db02a4f4a6c8266f868b03` | 501820–502019: default 400/400, Solution_92 77,5 % |
| `rules6.pth` | 6 DQN-Netze `full_rules` (Lehrer für BC/PPO `cnn2`, Gegneranteil „teacher“ im PPO) | `124ec118a55f9653483c8cf2b518f5af8a1d4dfedbbd154c74c3cd79ff95bf6a` | 500820–500919: default 99,5 %, Solution_92 69,0 % |
| `cnn2_ppo0040.pth` | CNN-Policy, BC vom Lehrer rules6 + 40 PPO-Iterationen (`experiments/ppo/cnn2`) | `007da1f1b040e54af61615ad817cf55cb8c025f6133a136a74f0fe9ca078d246` | 501420–501619: default 400/400, Solution_92 72,75 % |

Herkunft, Quellnetze und Bauschritte: [`../candidates_20261020.json`](../candidates_20261020.json),
Messungen: `experiments/compare/regeln/` (`G_*`, `J_*`, `Z_*`), Verlauf: `docs/ARBEITSSTAND.md`.

Auswerten (Schalter stecken in der Datei, kein `--set` nötig):

```bash
.venv/bin/python -m scripts.par_eval --weights experiments/candidates/all18_fo10.pth \
    --first 720 --n 100 --workers 6 --out experiments/compare/regeln/NAME.csv
```

Val-Seeds bis 502 019 sind verbraucht (nächster freier Index 2020), Test-Seeds 900 000+ nicht anfassen.

## Einrichten auf einem zweiten Rechner (z. B. Moayed)

Nach `git pull` einmal ausführen – kopiert alle Dateien an die Originalpfade, die
Arbeitsstand, Pipeline und Vergleichsbefehle verwenden (`experiments/ensembles/`,
`experiments/ppo/cnn2/`, beide gitignored), prüft jede SHA-256 und überschreibt keine
abweichende vorhandene Datei. Die Abgabe-Gewichte bleiben unberührt:

```bash
bash scripts/install_candidates.sh
```

Die Configs (alle Schalter, z. B. `far_opp=10`, `keep_dead_fast`) stecken in den Checkpoints
(`cfg`), eine Übersicht der abweichenden Werte steht in `../candidates_20261020.json`.

Kurzer Funktionstest (2 Karten, beide Seiten, default + Solution_92, ca. 1 Minute):

```bash
.venv/bin/python -m scripts.par_eval --weights experiments/ensembles/all18_fo10.pth \
    --first 720 --n 2 --workers 2 --out /tmp/check_all18_fo10.csv
```

Die Spiele sind deterministisch; das Ergebnis muss mit den Zeilen für Seeds 500720/500721
in `experiments/compare/regeln/F_a18_fo10_720.csv` übereinstimmen.

Hinweise für Rechner mit 8 GB RAM: Ein DQN-Training (`scripts.experiment`) hält einen
Replay Buffer von bis zu 300 000 Übergängen (gespeichert ca. 200 MB) – einen Lauf
gleichzeitig starten. Für Messungen `--workers 2–3`. Das BC-Vortraining des CNN braucht
`bc_data.npz` (3,2 GB, nicht im Repo) und passt kaum in 8 GB. PPO ab `ppo_0040.pth` braucht
`experiments/ppo/cnn2/teacher.json` (im Repo) und den Lehrer `rules6.pth` (über das Skript).
