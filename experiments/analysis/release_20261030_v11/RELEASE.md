# Übernahme V11 (`v11_mix36c_as`) als Abgabe – 30.10.2026, 13:36 Berlin

Durchgeführt von Claude Code. Auftrag von Mahmoud: bis 04.11. den Agenten „perfekt trainieren“, vieles ausprobieren und weiterarbeiten. Grundlage ist die Freigabe vom 20.10. in `CLAUDE.md`. Alle Tests standen vorab im
[Battle-Plan](../../../docs/superpowers/plans/2026-10-29-battle-push.md) mit den Nachträgen vom 30.10. um
04:09, 08:13 und 10:35, bevor auf den Blöcken 805000–807399 gespielt wurde. Referenz war die damalige Abgabe
**V10**.

## Was V11 ist

- **36 DQN-Netze:** die 18 V10-Netze bitgleich und dieselben 18 Netze nach drei Runden Nachtraining unter allen
  V10-Regeln (`battle_ft3_18`). Jedes Netz trainierte 1.500 + 2.000 + 2.000 Spiele gegen gemischte Gegner:
  Solution_92 und zwei Varianten, eigene frühere Abgaben, default und einen Rush-Bot. Die Q-Werte aller
  36 Netze werden wie bisher gemittelt. Die alten Netze waren nie unter den späteren V10-Regeln trainiert
  worden. Gemischt mit den nachtrainierten Netzen wird das Ensemble robuster.
- **Config:** V10 plus zwei neue Regeln (Commit `f34f9c4`, Standard aus, hier eingeschaltet). Beide greifen nur,
  wenn der versteckte Sap-Streufaktor laut `param_est` sicher 1,0 ist. `param_est` schätzt ihn seit dem 21.10.
  aus den Energieverläufen der eigenen Einheiten.
  - `art_splash`: Die Artillerie sappt schon ab 2 Treffern im 3×3-Feld und auch in gegnerischer Reichweite.
  - `sap_still_splash`: Einheiten auf Punktefeldern dürfen auch ziehende Gegner sappen. Die Engine bewegt vor
    dem Sap, deshalb bekommt ein Gegner einen Schritt neben dem Zieltile trotzdem den vollen Schaden.
- **Herkunft der Regeln:** Auf 5.200 Spielen gewann V10 bei Streufaktor 1,0 nur 78,9 % gegen
  Solution_92/`sol92_sq`, bei 0,25 dagegen 89,1 %. Ein früherer Dev-A-Test mit aggressiverer Artillerie
  wirkte je nach Streufaktor −6,5 / −0,8 / +6,0 pp. Danach wurde die Regel auf dem unberührten Dev B geprüft
  ([Arbeitsstand 30.10., 07:55 und 09:45](../../../docs/ARBEITSSTAND.md); Daten unter
  `experiments/analysis/battle_params_20261030/`).

## Nachweis (gepaart, Karten-Bootstrap; `scripts/league_gates.py`)

R ist das Mittel über Solution_92, `sol92_sq`, `sol92_weak` und `old3_sym3`.

| Schritt | Karten | V11 | V10 | Ergebnis |
|---|---|---|---|---|
| Entwicklung Dev B (nur Regeln, V10 + R) | 300 | 88,6 % | 87,2 % | +1,4 [+0,6; +2,3] gegen Solution_92/`sol92_sq`, übriges Panel ohne Verlust |
| Entwicklung Dev A (6 Gegner, davon 2 zurückgehaltene RL-Gegner) | 300 | 81,8 % | 72,1 % | +9,7 [+7,3; +12,0]; R allein auf `mix36c`: +4,0 [+2,6; +5,4] |
| Auswahl 805000–805199 (direkt 805200–805399) | 200 | R 91,8 %, Solution_92 96,0 % | 89,6 / 90,75 % | R +2,19 [−0,25; +4,69], gewählt unter 3 Kandidaten |
| **Bestätigung 806000–806799** | **800** | **R 91,2 %** | 86,6 % | **R +4,66 pp [+3,45; +5,88]** |
| **Direkt gegen V10 807000–807399** | 400 (800 Spiele) | **59,5 % [54,5; 64,25]** | – | untere Grenze > 50 % |

| Gegner (Bestätigung, je 1.600 Spiele) | V10 | V11 |
|---|---|---|
| Solution_92 | 89,6 % | **94,1 %** (Δ +4,50 [+2,88; +6,25]) |
| `sol92_sq` (sappt im ganzen Quadrat) | 79,1 % | 84,1 % |
| `sol92_weak` (zielt auf die schwächste Einheit) | 91,5 % | 93,8 % |
| `old3_sym3` (unsere Abgabe vom 16.10.) | 86,1 % | 92,9 % |
| default | 99,9 % | 100 % |

Alle Hürden der Bestätigung sind erfüllt:
- R Δ ≥ +2 pp mit unterer 95%-Grenze > 0,
- Solution_92 Δ ≥ −0,5 mit unterer Grenze > −2,5,
- default ≥ 99 % und Δ ≥ −1,
- direkt untere Grenze > 50 %.

Rohdaten `experiments/compare/battle/G2_*.csv`, Log `experiments/pipeline_battle_gate.log`.

Zusätzlich (Dev A 800000–800299, nur Information, je 600 Spiele):

| Gegner | V10 | V11 |
|---|---|---|
| DQN-Beispiel des Profs | 100 % | 100 % |
| Rush-Bot | 100 % | 100 % |
| `sol92_sqweak` | 79,2 % | 87,7 % |
| V7 (frühere Abgabe) | 60,2 % | 74,0 % |
| `league_nets6` (zurückgehalten) | 52,0 % | 65,0 % |
| `threat6` (zurückgehalten) | 81,3 % | 87,7 % |

## Technische Prüfungen

- **Installation** per `scripts/release_candidate.py`, Manifest `experiments/releases/20261030_v11_mix36c_as.json`.
- **Kurs-Runner unverändert:** 8 Spiele bestanden (beide Seiten, default und Solution_92, Seeds 500720/500721).
  Die Gewichte sind verifiziert, jedes Spiel startet mit frischem Gedächtnis. `act` braucht im Median 5,4 ms,
  höchstens 8,8 ms pro Schritt (`experiments/analysis/release_v11_mix36c_as_runner_installed.json`).
- **Testsuite** direkt nach der Installation, ohne laufende Jobs: 576 bestanden, 14 Untertests.
- **Battle-Zip** `Gruppe15.zip` neu gebaut: 22,2 MB, „Check ok“ mit dem Ordner unter `agents/` und in der
  Projektwurzel. Auch mit `train=True` bleibt der Agent eingefroren, 36 Netze. `agent.pth` in der Zip hat
  SHA-256 `3200641ac0e4e7eae7eb445a7f207e0d57e646d229af5fb34b891e0b8cc8ecc0` (Config mit `frozen=True`).
- **Andere Python-Versionen:** Ein mit der Zip aufgezeichnetes Spiel (303 Schritte) ergibt beim Nachspielen
  unter Python 3.10 mit torch 2.14/numpy 2.2 und mit torch 2.2/numpy 1.26 **0 abweichende Aktionen**
  (`scripts/xversion_replay.py`).
- **Für eine mögliche Moodle-Größengrenze** baut `python -m scripts.build_submission --battle --half` eine
  10,7-MB-Fassung mit float16-Gewichten. Auch sie ergab beim Nachspielen 0 abweichende Aktionen. Sie ist aber
  nicht die Fassung, die in den Hürden gemessen wurde.

## Hashes und Rückweg

- **Neu**, beide Dateien `agents/sherlock/weights/agent_p0.pth` und `agent_p1.pth`: SHA-256
  `2ab463e9034357a40cb721b34286ad1f9bad250629bf9f9f17b1d175157cd2e0`. Quelle
  `experiments/ensembles/battle_mix36c_as.pth`.
- **Vorher V10:** `03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67`, bytegleich gesichert in
  `experiments/releases/20261030_v10_V8st/` mit [Wiederherstellungsanleitung](../../releases/20261030_v10_V8st/README.md).
  Eine weitere Kopie liegt in `experiments/releases/20261022_v10_baseline/`. Ältere Sicherungen bleiben
  unverändert.

## Grenzen

- Die Gegner im Battle sind unbekannt. Gemessen wurde gegen Solution_92 und Varianten, eigene frühere Abgaben,
  zwei zurückgehaltene RL-Ensembles, das DQN-Beispiel des Profs und einen Rush-Bot.
- Die neuen Regeln greifen nur bei sicher geschätztem Streufaktor 1,0. In Testspielen war das meist ab Match 2
  der Fall, in etwa einem Drittel dieser Spiele gar nicht.
- Die Gewichtsdatei ist mit 24 MB doppelt so groß wie bisher, weil es 36 statt 18 Netze sind.
- Die Netze enthalten weiterhin das V3-Training (66.000 Spiele). Dazu kommt das Nachtraining der 18
  `ft3`-Netze mit je 5.500 Spielen.
