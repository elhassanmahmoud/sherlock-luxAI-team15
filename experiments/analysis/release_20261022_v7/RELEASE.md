# Übernahme V7 (`v7_Bsnpd`) als Abgabe – 22.10.2026, 05:27 Berlin

Durchgeführt von Claude Code im autonomen Nachtbetrieb mit Mahmouds Auftrag („alles automatisch machen
und selber arbeiten“) auf Grundlage der Freigabe vom 20.10. in `CLAUDE.md`: Ein nach den festgelegten
Tests nachweislich besserer Kandidat darf die Abgabe ersetzen. Die Tests waren vorab festgelegt im
[V7-Plan](../../../docs/superpowers/plans/2026-10-22-v7.md), bevor einer der Blöcke gespielt wurde.

## Was V7 ist

- **Dieselben 18 trainierten DQN-Netze wie V3** (bitgleich). Neu ist nur die Konfiguration, also Regeln
  und Gedächtnis zur Laufzeit.
- Config-Unterschiede zu V3: `art_sap=true`, `art_min_hits=3`, `art_safe=true`, `art_reserve=0` (Sap aus
  sicherer Position in Gegnerhaufen), `nebula_avoid=true`, `nebula_avoid_min=25`,
  `nebula_avoid_mode=soft` (schädlichen Nebel ab 25 meiden, ohne Wege zu sperren), `nebula_infer=true`
  (unsichtbare Tiles in Sensorreichweite sind Nebel), `drift_track=true` (Drift der Asteroiden/Nebel
  erkennen und die Gedächtniskarte mitrollen), `path_fix=true` (BFS-Schritt statt Sackgasse an
  Asteroidenwänden).
- Anlass: Verlustanalyse vom 22.10. Die Gedächtniskarte war durch Drift zu ~18 % falsch, Units saßen
  hinter längst weggedrifteten Asteroiden fest oder pendelten vor Sackgassen.

## Nachweis (Karten-Bootstrap, 5000 Ziehungen, Seed 0; `scripts/v5_gates.py`)

| Schritt | Karten | V7 | V3 | Ergebnis |
|---|---|---|---|---|
| Entwicklung `dev_hard330`/`dev_easy330` (Solution_92) | 660 | 58,3 % / 95,1 % | 27,0 % / 100 % | geschätzt gesamt ≈ 82,9 % statt 75,9 % |
| Auswahlblock 505220–505419 | 200 | Solution_92 82,25 %, default 100 % | 78,0 % / 100 % | Δ +4,25 [+0,3; +8,3] → Hürde +3 bestanden |
| **Frisch 505420–505819** | 400 | **Solution_92 83,5 %**, default 99,75 % | 76,5 % / 99,75 % | **Δ +7,00 pp [+4,00; +10,00]** |
| **Direkt gegen V3 505820–506019** | 200 (400 Spiele) | **68,0 % [61,5; 74,25]** | – | untere Grenze > 0,5 |

Gates der Bestätigung, alle erfüllt: Solution_92 Δ ≥ +5 pp, untere 95%-Grenze > 0, default ≥ 99 % und
Δ ≥ −1 pp, direkt untere Grenze > 0,5. Rohdaten: `experiments/compare/regeln/V7_*.csv`,
Log `experiments/pipeline_v7.log`.

## Technische Prüfungen

- Installation per `scripts/release_candidate.py`: Kandidat `experiments/ensembles/v7_Bsnpd.pth`
  in beide Abgabe-Dateien kopiert, Hashes geprüft. Manifest: `experiments/releases/20261022_v7_Bsnpd.json`.
- **Kurs-Runner unverändert**: 8 Spiele bestanden (beide Seiten, default und Solution_92, Seeds
  500720/500721), geladene Gewichte verifiziert, frisches Gedächtnis je Spiel. `act` pro Schritt:
  Median ≈ 4 ms, Maximum 10,5 ms (`experiments/analysis/release_v7_Bsnpd_runner_installed.json`).
- Testsuite direkt nach der Installation: 452 bestanden. 31 Tests in
  `tests/test_early_curriculum_study.py` wurden von der Schutzsperre „Another model job is active“
  abgewiesen, weil zu dem Zeitpunkt eine Entwicklungsmessung lief. Das ist dasselbe Verhalten wie am
  21.10. Die Wiederholung ohne laufende Messung steht im Arbeitsstand.

## Hashes und Rückweg

- Neu, beide Dateien `agents/sherlock/weights/agent_p0.pth`/`agent_p1.pth`: SHA-256
  `c394acba84f7a298f8f1e6107328d8e6ce151b367a28997b059aa82fc8a895e6`.
- Vorher (V3 `all18_v3`): `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`, bytegleich
  gesichert in `experiments/releases/20261022_all18_v3/` mit Manifest und
  [Wiederherstellungsanleitung](../../releases/20261022_all18_v3/README.md). Die ältere Sicherung
  `experiments/releases/20261020_old3_sym3/` bleibt unverändert.

## Grenzen

- Gemessen nur gegen Solution_92 und default. Gegner im Kursturnier sind unbekannt.
- Die Netze stammen weiterhin aus dem V3-Training (66.000 dokumentierte Trainingsspiele). V7 ändert
  nur Regeln und Gedächtnis zur Laufzeit. Die Abgabe enthält damit unverändert trainierte Gewichte.
