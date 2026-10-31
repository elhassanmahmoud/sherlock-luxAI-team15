# Übernahme V12 (`v12_fog`) als Abgabe – 31.10.2026, 17:07 Berlin

Durchgeführt von Claude Code. Auftrag von Mahmoud (31.10., 14:20): Sherlock so stark wie möglich machen, nur
noch was wirklich weiterbringt. Grundlage ist die Freigabe vom 20.10. in `CLAUDE.md`. Alle Tests standen vorab
im [Battle-Plan](../../../docs/superpowers/plans/2026-10-29-battle-push.md), Nachtrag vom 31.10., 14:40, bevor
auf Dev A und auf dem Block 808000–809199 gespielt wurde. Referenz war die damalige Abgabe **V11**.

## Was V12 ist

- **Netze:** dieselben 36 DQN-Netze wie V11, bytegleich. Es wurde nichts neu trainiert.
- **Config:** V11 plus vier Schalter, alle standardmäßig aus und hier eingeschaltet. Commits: `fog_v2` in
  `27530ee`, `splash_min_drop` in `a912b9f`, `splash_safe_below` in `7c52545`; `fog_sap` gibt es seit dem 20.10.
  - **Nebel-Sap** `fog_sap` + `fog_v2`: Steht eine Einheit auf einem bewiesenen Punktefeld und punktet der Gegner,
    ohne dass genug Gegner sichtbar sind, sappt sie auf ein unsichtbares Punktefeld in Reichweite, auf dem keine
    eigene Einheit steht. Die Zahl der versteckten Halter folgt aus dem Punktezuwachs des Gegners. Bei einem
    sichtbaren Ziel bleibt es beim normalen Sap.
  - **Halbstreuung** `splash_min_drop=0.5` + `splash_safe_below=1.0` (= `v11h`): `art_splash` und
    `sap_still_splash` greifen auch bei sicher geschätztem Streufaktor 0,5. Dort behält die Artillerie ihre
    Sicherheitsprüfung.
- **Warum der Nebel-Sap:** V11 war bei Sichtweite 1 deutlich schwächer: gegen Solution_92 87,9 statt
  94,9–97,0 % bei Sicht 3/4, gegen V3 72,4 statt 88,7–88,8 %. Eine Probe auf 4 Karten ergab: 97 % der
  gegnerischen Halter-Schritte sind unsichtbar, und je Spiel stehen 28–343 Mal unsichtbare Halter in
  Sap-Reichweite einer Einheit mit genug Energie. V11 sappte dort nie.
- **Der Fehler in der alten Regel:** Die Regel `fog_sap` gab es seit dem 20.10. Mit `use_symmetry` galt aber das
  Spiegelbild des Sensors als gesehen. Die gegnerischen Punktefelder sind das Spiegelbild unserer, fielen deshalb
  aus den Kandidaten, und die Regel schoss kaum. Das erklärt die Nullergebnisse vom 20.–22.10. `fog_v2` nimmt
  nur, was der Sensor in diesem Schritt wirklich zeigt
  ([Arbeitsstand 31.10., 14:40](../../../docs/ARBEITSSTAND.md)).

## Nachweis (gepaart, Karten-Bootstrap; `scripts/league_gates.py`)

„Mittel 6“ ist das Mittel über Solution_92, `sol92_sq`, V3 (`all18_v3`), V7 (`v7_Bsnpd`) und die beiden
zurückgehaltenen RL-Ensembles `league_nets6` und `threat6`.

| Schritt | Karten | Ergebnis gegen V11 |
|---|---|---|
| Zulassung `v11h` (Halbstreuung allein), Dev A | 300 | +1,08 pp [−0,08; +2,39], direkt 55,5 % |
| Battle-Bestätigung `v11h` allein, 810400–811599 | 800 | +0,95 [+0,33; +1,57], Hürde +1,0 verfehlt |
| Zulassung `v11fog` (Nebel-Sap allein), Dev A | 300 | **+2,78 [+1,25; +4,36], direkt 57,8 % [54,3; 61,5]** |
| **Battle-Bestätigung V12, 808000–808799** | **800** | **Mittel 6: 87,08 statt 81,19 % (+5,90 pp [+4,75; +7,08])** |
| **Direkt gegen V11, 808800–809199** | 400 (800 Spiele) | **61,0 % [57,75; 64,38]** |

| Gegner (Bestätigung, je 1.600 Spiele) | V11 | V12 | Δ pp [95 %] |
|---|---|---|---|
| Solution_92 | 93,00 % | **94,38 %** | +1,38 [+0,06; +2,75] |
| `sol92_sq` (sappt im ganzen Quadrat) | 85,06 % | 89,25 % | +4,2 [+2,6; +5,9] |
| V3 (Abgabe 20.–22.10.) | 83,38 % | 88,88 % | +5,5 [+3,2; +7,9] |
| V7 (Abgabe 22.10.) | 70,56 % | 79,75 % | +9,2 [+6,2; +12,2] |
| `league_nets6` (zurückgehalten) | 66,38 % | 77,25 % | +10,9 [+8,0; +14,0] |
| `threat6` (zurückgehalten) | 88,75 % | 93,00 % | +4,2 [+2,2; +6,2] |
| default | 99,88 % | 99,88 % | ±0 |

Alle Hürden der Battle-Bestätigung sind erfüllt (`GATE Battle-Bestaetigung: BESTANDEN` in
`experiments/pipeline_battle_gate.log`):
- Mittel 6 Δ ≥ +1 pp mit unterer 95%-Grenze > 0,
- Solution_92 Δ ≥ −0,5 mit unterer Grenze > −2,5,
- default ≥ 99 % und Δ ≥ −1,
- direkt untere Grenze > 50 %.

Aufschlüsselung (Mittel 6, gepaart; Kartenparameter aus
`experiments/analysis/battle_params_20261030/map_params.csv`, 2.000 Ziehungen, nur zur Beschreibung):

| Teilmenge | V11 | V12 | Δ pp [95 %] |
|---|---|---|---|
| Sichtweite 1 (191 Karten) | 77,2 % | 85,6 % | +8,4 [+5,5; +11,5] |
| Sichtweite 2 (203 Karten) | 79,7 % | 86,4 % | +6,7 [+4,4; +9,1] |
| Sichtweite 3 (199 Karten) | 82,8 % | 88,1 % | +5,2 [+3,1; +7,3] |
| Sichtweite 4 (207 Karten) | 84,7 % | 88,2 % | +3,5 [+1,7; +5,4] |
| Streufaktor 0,25 / 0,5 / 1,0 | | | +1,8 / **+8,8** / +7,1 |
| umkämpfte Relics nahe der Mittellinie / sonst | | | **+9,3** / +2,0 |

- Direkt gegen V11 nach Sichtweite 1/2/3/4: 64,7 / 57,2 / 65,2 / 57,7 %.
- V12 sappt im Mittel 101,5 statt 83,8 Mal je Spiel.
- Bei Streufaktor 1,0 ändert die Halbstreuung nichts; die +7,1 pp dort kommen allein vom Nebel-Sap.

Rohdaten: `experiments/compare/battle/GC_V11_conf.csv`, `GC_v12_conf.csv`, `GC_v12_confdir.csv`.

## Technische Prüfungen

- **Installation** per `scripts/release_candidate.py`, Manifest `experiments/releases/20261031_v12_fog.json`.
- **Kurs-Runner unverändert:** 8 Spiele bestanden (beide Seiten, default und Solution_92, Seeds 500720/500721).
  Die Gewichte sind verifiziert, jedes Spiel startet mit frischem Gedächtnis. `act` braucht im Median 5,5 ms,
  höchstens 8,7 ms pro Schritt (`experiments/analysis/release_v12_fog_runner_installed.json`).
- **Battle-Zip** `Gruppe15.zip` neu gebaut: 22,2 MB, „Check ok“ mit dem Ordner unter `agents/` und in der
  Projektwurzel. Auch mit `train=True` bleibt der Agent eingefroren, 36 Netze.
  - `Gruppe15/agent.pth`: SHA-256 `17477a9868615afc860a672317bfc91f118831a125cf8e49d0d7dcce1d048201`. Tensoren
    und Config sind identisch mit der Abgabe; einziger Unterschied ist `frozen=True`, wie es
    `build_submission --battle` vorsieht. In der Config sind `fog_sap`, `fog_v2`, `splash_min_drop=0.5` und
    `splash_safe_below=1.0` gesetzt.
  - Alle 15 Python-Dateien der Zip sind bytegleich mit `agents/sherlock/`.
- **Andere Python-Versionen:** Mit der Zip wurden zwei Spiele aufgezeichnet: Karte 800004 mit Sichtweite 1 und
  Karte 4242, je 303 Schritte. Darin sappte Sherlock 20 bzw. 4 Mal auf Felder außerhalb des Sensors, der
  Nebel-Sap lief also mit. Beim Nachspielen unter Python 3.10.15 mit torch 2.14.1/numpy 2.2.6 und mit
  torch 2.2.2/numpy 1.26.4 gab es **0 abweichende Aktionen** (`scripts/xversion_replay.py`).
- **Testsuite** direkt nach der Installation: 598 bestanden, 14 Untertests.

## Hashes und Rückweg

- **Neu**, beide Dateien `agents/sherlock/weights/agent_p0.pth` und `agent_p1.pth`: SHA-256
  `b258dc9927a7094f3d4b83bf4de251b03c3ccc57d69a1da23080c27e806c924b`. Quelle
  `experiments/ensembles/battle_v12.pth`.
- **Vorher V11:** `2ab463e9034357a40cb721b34286ad1f9bad250629bf9f9f17b1d175157cd2e0`, bytegleich gesichert in
  `experiments/releases/20261031_v11_mix36c_as/` mit
  [Wiederherstellungsanleitung](../../releases/20261031_v11_mix36c_as/README.md). Eine weitere Kopie liegt in
  `experiments/releases/20261030_v11_baseline/`. Ältere Sicherungen bleiben unverändert.
- Zurück zu V11 mit derselben Zip: die Gewichte wie in der Anleitung zurückkopieren und
  `python -m scripts.build_submission --battle` erneut ausführen.

## Grenzen

- Die Gegner im Battle sind unbekannt. Gemessen wurde gegen Solution_92 und eine Variante, eigene frühere
  Abgaben und zwei zurückgehaltene RL-Ensembles. Laut Dev A schlägt V11 das DQN-Beispiel des Profs und einen
  Rush-Bot in allen 600 Spielen; V12 wurde dagegen nicht eigens neu gemessen.
- Der Nebel-Sap braucht Punktezuwachs des Gegners. Gegen Gegner, die nicht auf Punktefeldern stehen, ändert er
  nichts.
- Gegen Solution_92 ist der Gewinn klein (+1,4 pp), weil V11 dort schon 93 % erreichte.
- Der Testblock 808000–809199 ist jetzt verbraucht. Unbenutzt sind noch 809200–809599 und 810000–810399.
- Eine `--half`-Fassung (float16, etwa 10,7 MB) für eine mögliche Moodle-Größengrenze gibt es für V12 noch nicht.
  Bei Bedarf: `python -m scripts.build_submission --battle --half`. Sie wäre nicht die in den Hürden gemessene
  Fassung.

## Nachtrag 31.10.2026, 20:15: Zip mit Absturzschutz neu gebaut

- `Gruppe15.zip` (20:07, 22,2 MB) enthält zusätzlich den Absturzschutz in `agents/sherlock/main.py`: Nur mit
  `frozen` (also nur in der Zip) fangen `act()` und `update()` Fehler ab, die Units bleiben dann einen Schritt
  stehen. Außerdem sind die abgeschalteten Schalter `fog_prior`/`fog_drop_est` vom Abend im Code. Gewichte und
  Config sind unverändert, `Gruppe15/agent.pth` ist bytegleich (SHA-256 `17477a98…`).
- Nachweis: 3 mit der alten Zip aufgezeichnete Spiele (Karten 800004, 4242, 800009) mit der neuen Zip
  nachgespielt, in drei Umgebungen (Python 3.14.6; Python 3.10.15 mit torch 2.14.1/numpy 2.2.6 und mit torch
  2.2.2/numpy 1.26.4) jeweils 0 abweichende Aktionen. Testsuite 604 bestanden. Details im
  [Arbeitsstand](../../../docs/ARBEITSSTAND.md) vom 31.10., 20:15.
