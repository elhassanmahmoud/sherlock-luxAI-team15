# Übernahme V13 (`v13_neb`) als Abgabe – 01.11.2026, 10:46 Berlin

Durchgeführt von Claude Code im Nachtauftrag von Mahmoud (31.10./01.11.: alle Genehmigungen, Ziel Platz 1 und mehr
Prozent gegen Solution_92). Grundlage ist die Freigabe vom 20.10. in `CLAUDE.md`. Die Regeln standen vorab im
[Battle-Plan](../../../docs/superpowers/plans/2026-10-29-battle-push.md), Nachträge vom 01.11., 04:25 und 04:45:
Zuerst bekam Runde 6 (`v17a`) ihre Battle-Bestätigung. Nur wenn sie durchfällt, zählt die gezielte
Nebel-Bestätigung von `v15cx`, und dann wird V13 = `v13_neb`.

- `v17a` (V12-Netze + 12 nachtrainierte Netze + Nebel-Korrektur) fiel am 01.11., 10:40 durch: Mittel 6 +0,41 pp
  [−0,68; +1,52] auf 813200–813999, direkt gegen V12 53,75 % [49,0; 58,75]. Damit gilt die zweite Regel.
- Die gezielte Nebel-Bestätigung von `v15cx` hatte um 09:04 alle 7 Hürden bestanden.

## Was V13 ist

- **Netze:** dieselben 36 DQN-Netze wie V12 und V11, alle Tensoren identisch. Es wurde nichts neu trainiert.
- **Config:** V12 plus zwei Schalter, beide standardmäßig aus und hier eingeschaltet (seit Commit `2e4eee7` im Code):
  - `est_censor`: Die Parameterschätzung wertet keine Beobachtung mit Energie 0 aus. Die Engine kappt die Energie
    bei 0. Eine Unit mit 0 Energie auf einem Nebel-Tile ohne Feldenergie zeigte deshalb „Verlust 0“ und galt als
    Beleg für Nebelabzug 0.
  - `neb_cross`: Eine Unit betritt Nebel nur mit genug Energie für die ganze Durchquerung bis zum Ziel. Vorher galt
    pauschal der doppelte Nebelabzug. Reicht die Energie nicht, sammelt sie erst Energie. Steckt sie schon im Nebel,
    nimmt sie den nächsten Ausgang.
- **Warum:** Auf Karten mit Nebelabzug 25 kippte bei V12 die Schätzung des Abzugs auf 0 (Karte 812584: in Match 1
  bei Schritt 33 von 25 auf 0). Danach war die Nebel-Meidung für das ganze Spiel aus, und Units blieben mit
  0 Energie im Nebel stecken. Auf Dev A lagen 84 der 87 veränderten Ergebnisse auf solchen Karten.

## Nachweis (gepaart, Karten-Bootstrap; `scripts/battle_neb25.sh`)

Die Korrektur wirkt nur auf Karten mit Nebelabzug 25. Das ist etwa jede sechste Karte (16,7 % in 800000–809999).
Deshalb wurde vorab ein Test genau dort festgelegt, dazu ein Gleichheitstest für alle übrigen Karten. Die Karten
wurden nur nach ihren Parametern aus `env.reset` gewählt, bevor ein Spiel lief
(`experiments/analysis/neb25_20261101/`).

| Prüfung | Karten | Ergebnis | Hürde |
|---|---|---|---|
| Abzug 25: Mittel 6 | 300 (816000–817792) | **87,17 statt 84,78 % (+2,39 pp [+0,31; +4,36])** | ≥ +1 pp, untere Grenze > 0 |
| Abzug 25: Solution_92 | 300 | 95,0 statt 94,2 % (+0,83 [−1,17; +2,83]) | ≥ −0,5 pp |
| Abzug 25: default | 300 | 100 % | ≥ 99 % |
| Abzug 25: direkt gegen V12 | 300 (600 Spiele) | **56,0 % [50,8; 61,3]** | ≥ 50 % |
| übrige Karten: gleiche Ergebnisse | 60 (720 Spiele) | **720 von 720 gleich** | ≥ 98 % |
| übrige Karten: Mittel 6 | 60 | ±0 | ≥ −0,5 pp |

`GATE Nebel-25-Bestaetigung: BESTANDEN` in `experiments/pipeline_battle_gate.log`.

| Gegner (Abzug-25-Karten, je 600 Spiele) | V12 | V13 | Δ pp [95 %] |
|---|---|---|---|
| Solution_92 | 94,17 % | 95,00 % | +0,83 [−1,17; +2,83] |
| `sol92_sq` (sappt im ganzen Quadrat) | 91,67 % | 91,00 % | −0,67 [−3,17; +1,83] |
| V3 (Abgabe 20.–22.10.) | 89,50 % | 91,33 % | +1,83 [−1,83; +5,50] |
| V7 (Abgabe 22.10.) | 72,83 % | 76,00 % | +3,17 [−3,00; +9,17] |
| `league_nets6` (zurückgehalten) | 65,67 % | **76,00 %** | **+10,33 [+4,00; +16,33]** |
| `threat6` (zurückgehalten) | 94,83 % | 93,67 % | −1,17 [−4,33; +2,00] |
| default | 100 % | 100 % | ±0 |

Weitere Belege, nur zur Beschreibung:

- **Dev A (800000–800299, alle Karten):** `v15cx` gegen V12 Mittel 6 +0,42 pp. Auf den Abzug-25-Karten +2,68 pp,
  jeder der 6 Gegner +1,8 bis +5,4 pp, direkt 57,1 %. Auf den übrigen Karten direkt 50,2 %, also praktisch gleich.
- **Erwartung über alle Karten:** etwa +0,4 pp im Mittel 6 (+2,4 pp auf jeder sechsten Karte, sonst gleich). Die
  Korrektur ist klein, schadet aber nirgends messbar.
- **Gleiche Korrektur in `v17a`:** `v17a` hat dieselbe Korrektur plus 12 nachtrainierte Netze. In seiner
  Battle-Bestätigung auf 813200–813999 (gegen V12, nachträglich nach Kartenparametern getrennt, nur Beschreibung):
  - auf den 115 Karten mit Abzug 25: +3,26 pp [−0,29; +6,74], Solution_92 +4,35 [+1,30; +7,83],
  - auf den übrigen 685 Karten: −0,07 pp [−1,24; +1,08].

  Der Gewinn von `v17a` kam also aus der Nebel-Korrektur. Die 12 neuen Netze brachten nichts Messbares.

Rohdaten: `experiments/compare/battle/GN_V12_n25.csv`, `GN_v15cx_n25.csv`, `GN_v15cx_n25dir.csv`,
`GN_V12_rest.csv`, `GN_v15cx_rest.csv`.

## Technische Prüfungen

- **Prüfskript korrigiert, bevor installiert wurde** (Commit `a5d6dd6`): Die Nebel-Bestätigung und die
  Battle-Bestätigung von `v17a` liefen gleichzeitig. Ihre Zeilen stehen deshalb gemischt im Gate-Log. Das alte
  `gate_passed` erkannte `v15cx` nicht. Umgekehrt hätte es `v17a` fälschlich als bestanden gewertet, weil es das
  BESTANDEN der Nebel-Bestätigung mitzählte. Jetzt zählt nur die Urteilszeile derselben Art. Auf allen alten
  Gate-Logs gibt es dieselben Antworten wie vorher, außer in diesen zwei Fällen. Dazu kommen 2 neue Tests.
- **Installation** per `scripts/release_candidate.py`, Manifest `experiments/releases/20261101_v13_neb.json`.
- **Kurs-Runner unverändert:** 8 Spiele bestanden (beide Seiten, default und Solution_92, Seeds 500720/500721).
  Jedes Spiel startet mit frischem Gedächtnis, die geladenen Gewichte sind verifiziert. `act` braucht im Median
  5,4–6,7 ms, höchstens 10,3 ms pro Schritt (`experiments/analysis/release_v13_neb_runner_installed.json`).
- **Battle-Zip** `Gruppe15.zip` neu gebaut (01.11., 10:46): 22,2 MB (22.224.056 Bytes), SHA-256 `dad66c4d…`. Mit dem
  Ordner unter `agents/` und in der Projektwurzel jeweils „Check ok“. Auch mit `train=True` bleibt der Agent
  eingefroren, 36 Netze.
  - `Gruppe15/agent.pth`: SHA-256 `93451fb03fa152e2abb8521679e156087b4fa2eddfdb888c60af1e4df96f058a`. Tensoren und
    Config sind identisch mit der Abgabe. Einziger Unterschied ist `frozen=True`, wie es
    `build_submission --battle` vorsieht. In der Config sind `est_censor`, `neb_cross`, `fog_sap` und `fog_v2`
    gesetzt.
  - Alle 15 Python-Dateien der Zip sind bytegleich mit `agents/sherlock/`.
- **Andere Python-Versionen:** Mit der Zip wurden 3 Spiele aufgezeichnet (Python 3.14.6), je 303 Schritte:
  - Karte 800000 mit Nebelabzug 25,
  - Karte 800004 mit Sichtweite 1,
  - Karte 4242.

  Beim Nachspielen unter Python 3.10.15 mit torch 2.14.1/numpy 2.2.6 und mit torch 2.2.2/numpy 1.26.4 gab es
  **0 abweichende Aktionen** (`scripts/xversion_replay.py`).
- **Testsuite** (Code `a5d6dd6`): vor und nach der Installation je 621 bestanden, 14 Untertests.

## Hashes und Rückweg

- **Neu**, beide Dateien `agents/sherlock/weights/agent_p0.pth` und `agent_p1.pth`: SHA-256
  `6d00b6c52366a613eed3b7b5b6f9c3c088802716a85c30fe192c46c57bdd8e62`. Quelle
  `experiments/ensembles/battle_v15cx.pth`.
- **Vorher V12:** `b258dc9927a7094f3d4b83bf4de251b03c3ccc57d69a1da23080c27e806c924b`, bytegleich gesichert in
  `experiments/releases/20261101_v12_fog/` mit
  [Wiederherstellungsanleitung](../../releases/20261101_v12_fog/README.md). Weitere Kopien:
  `experiments/ensembles/battle_v12.pth`. Ältere Sicherungen bleiben unverändert.
- Zurück zu V12 mit derselben Zip: Gewichte wie in der Anleitung zurückkopieren, dann
  `python -m scripts.build_submission --battle`. Die alte V12-Zip (31.10., 20:07, SHA-256 `feddb723…`) lässt sich
  so jederzeit neu bauen.

## Grenzen

- Der Gewinn ist klein: etwa +0,4 pp über alle Karten. Er liegt nur auf Karten mit Nebelabzug 25, dort aber
  deutlich (+2,4 pp). Gegen Solution_92 ändert sich praktisch nichts.
- Die Gegner im Battle sind unbekannt. Gemessen wurde gegen Solution_92 und eine Variante, gegen eigene frühere
  Abgaben und gegen zwei zurückgehaltene RL-Ensembles.
- Testblöcke: 816000–817792 (Abzug 25) und die 60 Rest-Karten aus `seeds_rest.json` sind jetzt verbraucht, ebenso
  813200–814399 durch `v17a`. Reserviert und unbenutzt: 820000–820799, direkt 821000–821399 (Nachtrag 07:15).
- Eine `--half`-Fassung (float16, etwa 10,7 MB) für eine mögliche Moodle-Größengrenze gibt es für V13 noch nicht.
  Bei Bedarf: `python -m scripts.build_submission --battle --half`. Sie wäre nicht die in den Hürden gemessene
  Fassung.
