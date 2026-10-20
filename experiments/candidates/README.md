# Kandidaten-Gewichte (zum Teilen im Team)

Auf Wunsch von Moayed und Mahmoud (20.10.2026) liegen die aktuellen Kandidaten hier
**versioniert**, damit beide Arbeitsumgebungen mit identischen Dateien arbeiten.
Das ist **keine** neue Abgabe: `agents/sherlock/weights/` bleibt unverändert, bis die
Übernahme ausdrücklich beschlossen ist.

| Datei | Inhalt | SHA-256 | Ergebnis (frische Karten, beide Seiten) |
|---|---|---|---|
| `all18_fo10.pth` | 18 DQN-Netze (rules6 + sol70 + opp), Config inkl. `keep_dead_fast`, `far_opp=10` | `b2b7ffcc506d71a4657bb8990a71c0b25c4535f0f41564054ff687a1fa7b4607` | 501620–501819: default 400/400, Solution_92 320/400 = 80,0 %; 501820–502019: 400/400, 74,75 % |
| `all24fo.pth` | `all18` + 6 Netze `full_rules_fo`, Config inkl. `keep_dead_fast`, `far_opp=10` | `e9ff09a64ae0327e49ea8a4c0810abcf47bf2f1b05db02a4f4a6c8266f868b03` | 501820–502019: default 400/400, Solution_92 77,5 % |
| `cnn2_ppo0040.pth` | CNN-Policy, BC vom Lehrer rules6 + 40 PPO-Iterationen (`experiments/ppo/cnn2`) | `007da1f1b040e54af61615ad817cf55cb8c025f6133a136a74f0fe9ca078d246` | 501420–501619: default 400/400, Solution_92 72,75 % |

Herkunft, Quellnetze und Bauschritte: [`../candidates_20261020.json`](../candidates_20261020.json),
Messungen: `experiments/compare/regeln/` (`G_*`, `J_*`, `Z_*`), Verlauf: `docs/ARBEITSSTAND.md`.

Auswerten (Schalter stecken in der Datei, kein `--set` nötig):

```bash
.venv/bin/python -m scripts.par_eval --weights experiments/candidates/all18_fo10.pth \
    --first 720 --n 100 --workers 6 --out experiments/compare/regeln/NAME.csv
```

Val-Seeds bis 502 019 sind verbraucht (nächster freier Index 2020), Test-Seeds 900 000+ nicht anfassen.
