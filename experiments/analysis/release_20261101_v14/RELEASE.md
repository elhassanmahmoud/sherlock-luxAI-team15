# Übernahme V14 (`v14_rescue`) als Abgabe – 01.11.2026, 17:51 Berlin

Durchgeführt von Claude Code. **Teamentscheidung von Mahmoud** (01.11., 17:51, ausdrücklich „ja lets go“) auf Empfehlung
von Claude Code. Der Kandidat hat die vorab festgelegte Battle-Bestätigung **nicht bestanden**: Er verfehlte die Hürde
„Mittel über 6 Gegner ≥ +1 pp“ mit +0,86 pp und die untere Grenze des Direktduells. Trotzdem war er in zwei
unabhängigen Messungen besser als V13, gegen jeden Gegner. Die Übernahme lief deshalb mit
`scripts/release_candidate.py --team-decision`; Begründung und `gate_passed: false` stehen im Manifest
`experiments/releases/20261101_v14_rescue.json`.

## Was V14 ist

- **Netze:** dieselben 36 DQN-Netze wie V13, V12 und V11, alle Tensoren identisch. Es wurde nichts neu trainiert.
- **Config:** V13 plus `cand_rescue=true` und `rescue_after=30`. Die Regel gibt es seit dem 22.10. im Code.
  - Ist ein Relic seit 30 Schritten bekannt und noch kein Punkte-Tile bewiesen, gehen die Units gezielt auf
    Kandidaten-Tiles: `obey_target`, `neb_cand` und `idle_approach` sind dann aktiv.
  - Sonst ändert sich nichts. Die Regel ist ein Sicherheitsnetz für Spiele, in denen Units auf Energiefeldern pendeln
    oder von ihren Kandidaten weglaufen und lange keinen Punkt finden (Diagnose 812121: 0:202 in Match 2).
- Die am 01.11. neu gebauten Schalter `cand_post` und `spawn_proof` stehen im Code, sind in V14 aber **aus**.
  `v19cr` mit beiden ist auf frischen Karten durchgefallen.

## Nachweis

| Messung | Karten | Ergebnis gegen V13 |
|---|---|---|
| Screen Dev A (800000–800299), Nachtrag 07:15 | 300 (600 Spiele je Gegner) | Mittel 6 **+0,50 pp [+0,14; +0,94]**, Solution_92 +0,17, direkt 52,3 % [51,0; 53,7] |
| **Battle-Bestätigung 820000–820799** | **800 (1.600 Spiele je Gegner)** | **Mittel 6 87,59 statt 86,73 % (+0,86 pp [+0,48; +1,28])** |
| Direkt gegen V13, 821000–821399 | 400 (800 Spiele) | 50,6 % [49,25; 52,0] |

| Gegner (Bestätigung, je 1.600 Spiele) | V13 | V14 | Δ pp [95 %] |
|---|---|---|---|
| Solution_92 | 94,94 % | **95,44 %** | +0,50 [+0,12; +0,88] |
| `sol92_sq` | 89,44 % | 90,12 % | +0,69 [+0,25; +1,25] |
| V3 (Abgabe 20.–22.10.) | 87,75 % | 88,50 % | +0,75 [−0,12; +1,62] |
| V7 (Abgabe 22.10.) | 80,50 % | 81,63 % | +1,12 [+0,00; +2,25] |
| `league_nets6` (zurückgehalten) | 75,12 % | 76,38 % | +1,25 [+0,38; +2,25] |
| `threat6` (zurückgehalten) | 92,63 % | 93,50 % | +0,88 [+0,00; +1,75] |
| default | 99,94 % | 100 % | +0,06 |

- Hürden der Battle-Bestätigung (`league_gates battle`):
  - **verfehlt:** Mittel 6 Δ ≥ +1 pp (+0,86) und direkt untere Grenze > 50 % (49,25 %);
  - erfüllt: untere Grenze Mittel 6 > 0, Solution_92 Δ ≥ −0,5 und untere Grenze > −2,5, default ≥ 99 % und Δ ≥ −1.
- **Warum trotzdem:** Beide Messungen sind unabhängig, denn die Regel wurde nicht auf Dev A entwickelt. Beide schließen 0
  aus, und kein Gegner wird schlechter. Zusammen ergeben sie etwa +0,7 pp. Die Hürde +1 pp soll Zufallstreffer
  verhindern; hier ist der Gewinn klein, aber belegt.
- Rohdaten: `experiments/compare/battle/D_v18r*.csv`, `GF_v15cx_conf.csv`, `GF_v18r_conf.csv`, `GF_v18r_confdir.csv`;
  Gate-Zeilen in `experiments/pipeline_battle_gate.log` (`GATE Battle-Bestaetigung: NICHT BESTANDEN`).

## Technische Prüfungen

- **Installation** per `scripts/release_candidate.py --team-decision` (Code `95a9627`), Manifest
  `experiments/releases/20261101_v14_rescue.json` mit `gate_passed: false` und der Begründung.
- **Kurs-Runner unverändert:** 8 Spiele bestanden (beide Seiten, default und Solution_92, Seeds 500720/500721).
  `act` braucht im Median 4,7–5,7 ms, höchstens 11,6 ms (`experiments/analysis/release_v14_rescue_runner_installed.json`).
- **Battle-Zip** `Gruppe15.zip` neu gebaut (01.11., 17:51): 22,2 MB (22.227.522 Bytes), SHA-256 `50c188b1…`. „Check ok“
  unter `agents/` und in der Projektwurzel. Auch mit `train=True` eingefroren, 36 Netze.
  - `Gruppe15/agent.pth`: SHA-256 `d3d87209ca3a0a44eae26f052d863e68f54b427cb1b0e19082a21b3bd02e05c4`. Tensoren und
    Config wie die Abgabe, einziger Unterschied `frozen=True`. In der Config stehen `cand_rescue=true`,
    `rescue_after=30`, `est_censor`, `neb_cross`, `fog_sap` und `fog_v2`.
  - Alle 15 Python-Dateien der Zip sind bytegleich mit `agents/sherlock/`.
- **Andere Python-Versionen:** 3 Spiele mit der Zip aufgezeichnet (Python 3.14.6): 800000 (Nebelabzug 25), 800004
  (Sichtweite 1) und 4242. Beim Nachspielen unter Python 3.10.15 mit torch 2.14.1/numpy 2.2.6 und mit torch
  2.2.2/numpy 1.26.4 gab es **0 abweichende Aktionen**.
- **Testsuite** nach der Installation: 632 bestanden, 14 Untertests.

## Hashes und Rückweg

- **Neu**, beide Dateien `agents/sherlock/weights/agent_p0.pth` und `agent_p1.pth`: SHA-256
  `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`. Quelle `experiments/ensembles/battle_v18r.pth`.
- **Vorher V13:** `6d00b6c52366a613eed3b7b5b6f9c3c088802716a85c30fe192c46c57bdd8e62`, bytegleich gesichert in
  `experiments/releases/20261101_v13_neb/` mit [Wiederherstellungsanleitung](../../releases/20261101_v13_neb/README.md).
  Weitere Kopie: `experiments/ensembles/battle_v15cx.pth`.
- Zurück zu V13: Gewichte wie in der Anleitung zurückkopieren, dann `python -m scripts.build_submission --battle`.

## Grenzen

- Der Gewinn ist klein (+0,86 pp auf frischen Karten, gegen Solution_92 +0,5). Die Regel greift nur in Spielen, in denen
  lange kein Punkte-Tile gefunden wird.
- Das Direktduell gegen V13 ist praktisch ausgeglichen (50,6 %).
- Die Gegner im Battle sind unbekannt.
- Verbraucht sind jetzt auch 820000–821399 (`v18r`) und 822000–823399 (`v19cr`).
- Eine `--half`-Fassung (float16, etwa 10,7 MB) für eine mögliche Moodle-Größengrenze gibt es für V14 noch nicht. Bei
  Bedarf: `python -m scripts.build_submission --battle --half`.
