<!-- automatisch erzeugt von scripts/report.py - nicht von Hand bearbeiten -->

## Winrate auf den Test-Seeds (ε = 0)

Winrate = Mittel von `result` (Sieg 1, Remis 0,5). KI: 95 %, zweistufiger Bootstrap (Starts × Seeds). ± = Standardabweichung über die Trainingsstarts.

### Gegner: default

| Variante | Starts | Spiele | Winrate | 95-%-KI | Mittel ± SD (Starts) | Match-WR | Punkte-WR | Punkte wir : Gegner |
|---|---:|---:|---:|---|---|---:|---:|---|
| `baseline_prof` | 1 | 60 | 0.0 % | [0.0, 0.0] | – | 0.6 % | 0.0 % | 5 : 268 |
| `baseline_prof_retrained` | 3 | 180 | 0.0 % | [0.0, 0.0] | 0.0 ± 0.0 | 1.3 % | 0.0 % | 4 : 269 |
| `full` | 3 | 180 | 87.8 % | [76.7, 96.7] | 87.8 ± 3.5 | 83.1 % | 92.2 % | 541 : 142 |
| `no_belief` | 3 | 180 | 56.1 % | [41.7, 71.7] | 56.1 ± 8.2 | 53.7 % | 59.7 % | 267 : 228 |
| `no_shaping` | 3 | 180 | 55.0 % | [23.3, 80.6] | 55.0 ± 30.3 | 51.9 % | 61.1 % | 417 : 242 |
| `no_sap` | 3 | 180 | 71.7 % | [47.8, 90.0] | 71.7 ± 21.7 | 65.7 % | 75.3 % | 516 : 253 |
| `no_guided_explore` | 3 | 180 | 87.8 % | [76.7, 95.6] | 87.8 ± 5.4 | 81.9 % | 89.4 % | 524 : 130 |
| `no_canonical` | 3 | 180 | 80.0 % | [68.3, 90.6] | 80.0 ± 5.0 | 76.1 % | 80.3 % | 509 : 176 |

### Gegner: Solution_92

| Variante | Starts | Spiele | Winrate | 95-%-KI | Mittel ± SD (Starts) | Match-WR | Punkte-WR | Punkte wir : Gegner |
|---|---:|---:|---:|---|---|---:|---:|---|
| `baseline_prof` | 1 | 60 | 0.0 % | [0.0, 0.0] | – | 0.6 % | 0.0 % | 4 : 1655 |
| `baseline_prof_retrained` | 3 | 180 | 0.0 % | [0.0, 0.0] | 0.0 ± 0.0 | 0.6 % | 0.0 % | 3 : 1654 |
| `full` | 3 | 180 | 18.9 % | [8.3, 31.7] | 18.9 ± 3.5 | 20.4 % | 15.8 % | 497 : 993 |
| `no_belief` | 3 | 180 | 1.7 % | [0.0, 5.0] | 1.7 ± 0.0 | 4.6 % | 0.6 % | 236 : 1250 |
| `no_shaping` | 3 | 180 | 2.2 % | [0.0, 8.9] | 2.2 ± 1.9 | 2.4 % | 2.8 % | 350 : 1410 |
| `no_sap` | 3 | 180 | 2.8 % | [0.0, 6.7] | 2.8 ± 1.0 | 5.2 % | 2.2 % | 435 : 1387 |
| `no_guided_explore` | 3 | 180 | 15.6 % | [6.1, 26.7] | 15.6 ± 1.0 | 17.6 % | 13.9 % | 465 : 1041 |
| `no_canonical` | 3 | 180 | 12.2 % | [4.4, 21.7] | 12.2 ± 1.9 | 13.9 % | 7.8 % | 450 : 1063 |

## Unterschied zu `full` (gepaarter Bootstrap, gleicher Seed + gleiche Seite)

Δ in Prozentpunkten (Winrate) bzw. Punkten (Punktedifferenz wir − Gegner pro Spiel). KI schließt 0 ein ⇒ kein belegter Unterschied.

| Variante | Gegner | Δ Winrate | 95-%-KI | Δ Punktedifferenz | 95-%-KI |
|---|---|---:|---|---:|---|
| `baseline_prof` | default | -87.8 | [-96.7, -76.7] | -661.8 | [-752.8, -565.6] |
| `baseline_prof_retrained` | default | -87.8 | [-96.7, -76.7] | -663.6 | [-755.3, -567.9] |
| `no_belief` | default | -31.7 | [-48.9, -13.3] | -360.5 | [-472.6, -240.0] |
| `no_shaping` | default | -32.8 | [-65.6, -6.1] | -224.5 | [-523.1, +13.5] |
| `no_sap` | default | -16.1 | [-40.6, +5.0] | -135.9 | [-316.1, +41.0] |
| `no_guided_explore` | default | +0.0 | [-11.1, +10.0] | -5.0 | [-117.7, +100.9] |
| `no_canonical` | default | -7.8 | [-18.9, +4.4] | -66.3 | [-159.9, +37.8] |
| `baseline_prof` | Solution_92 | -18.9 | [-31.7, -7.8] | -1154.0 | [-1301.0, -1002.6] |
| `baseline_prof_retrained` | Solution_92 | -18.9 | [-31.7, -7.8] | -1154.5 | [-1298.4, -1005.6] |
| `no_belief` | Solution_92 | -17.2 | [-28.9, -6.7] | -517.6 | [-636.6, -400.5] |
| `no_shaping` | Solution_92 | -16.7 | [-28.9, -5.6] | -563.5 | [-1009.2, -209.7] |
| `no_sap` | Solution_92 | -16.1 | [-27.8, -5.6] | -455.5 | [-695.6, -212.2] |
| `no_guided_explore` | Solution_92 | -3.3 | [-11.1, +4.4] | -79.2 | [-205.6, +42.0] |
| `no_canonical` | Solution_92 | -6.7 | [-15.6, +1.7] | -116.2 | [-226.4, +1.5] |

## Verhalten (Test-Spiele, beide Gegner)

| Variante | Warten | ungültig | Maske griff | Saps/Spiel | Sap-Treffer | Stacking | Relics | Punkte-Tiles |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `baseline_prof` | 0.0 % | 86.5 % | – | 0.0 | – | 91.3 % | 0.2 | – |
| `baseline_prof_retrained` | 0.0 % | 86.7 % | – | 0.0 | – | 91.9 % | 0.3 | – |
| `full` | 47.2 % | 0.0 % | 51.5 % | 122.7 | 100.0 % | 28.4 % | 2.7 | 5.6 |
| `no_belief` | 45.2 % | 0.0 % | 61.2 % | 85.3 | 100.0 % | 37.8 % | 2.0 | 2.7 |
| `no_shaping` | 35.4 % | 0.0 % | 36.6 % | 5.6 | 100.0 % | 45.3 % | 1.9 | 4.3 |
| `no_sap` | 51.1 % | 0.0 % | 23.6 % | 0.0 | – | 37.2 % | 1.8 | 4.2 |
| `no_guided_explore` | 43.0 % | 0.0 % | 49.7 % | 129.6 | 100.0 % | 29.7 % | 2.8 | 5.7 |
| `no_canonical` | 47.5 % | 0.0 % | 58.8 % | 121.9 | 100.0 % | 33.2 % | 2.6 | 4.8 |

## Läufe

| Lauf | Trainingsspiele | Laufzeit | Commit | dirty |
|---|---:|---:|---|---|
| `20261010_baseline_prof_retrained_s0` | 3000 | 60 min | `503ada4` | False |
| `20261010_baseline_prof_retrained_s1` | 3000 | 60 min | `503ada4` | False |
| `20261010_baseline_prof_retrained_s2` | 3000 | 57 min | `6a8ebf3` | False |
| `20261010_baseline_prof_s0` | 0 | 2 min | `503ada4` | False |
| `20261010_full_s0` | 3000 | 70 min | `503ada4` | False |
| `20261010_full_s1` | 3000 | 71 min | `503ada4` | False |
| `20261010_full_s2` | 3000 | 66 min | `6a8ebf3` | False |
| `20261010_no_belief_s0` | 3000 | 72 min | `503ada4` | False |
| `20261010_no_belief_s1` | 3000 | 72 min | `503ada4` | False |
| `20261010_no_belief_s2` | 3000 | 66 min | `6a8ebf3` | False |
| `20261010_no_canonical_s0` | 3000 | 70 min | `503ada4` | False |
| `20261010_no_canonical_s1` | 3000 | 66 min | `6a8ebf3` | False |
| `20261010_no_canonical_s2` | 3000 | 65 min | `6a8ebf3` | False |
| `20261010_no_guided_explore_s0` | 3000 | 71 min | `503ada4` | False |
| `20261010_no_guided_explore_s1` | 3000 | 67 min | `6a8ebf3` | False |
| `20261010_no_guided_explore_s2` | 3000 | 65 min | `6a8ebf3` | False |
| `20261010_no_sap_s0` | 3000 | 68 min | `503ada4` | False |
| `20261010_no_sap_s1` | 3000 | 66 min | `6a8ebf3` | False |
| `20261010_no_sap_s2` | 3000 | 64 min | `6a8ebf3` | False |
| `20261010_no_shaping_s0` | 3000 | 68 min | `503ada4` | False |
| `20261010_no_shaping_s1` | 3000 | 69 min | `503ada4` | False |
| `20261010_no_shaping_s2` | 3000 | 64 min | `6a8ebf3` | False |
