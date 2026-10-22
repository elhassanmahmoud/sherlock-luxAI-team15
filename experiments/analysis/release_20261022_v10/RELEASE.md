# Übernahme V10 (`v10_V8st`) als Abgabe – 22.10.2026, 09:21 Berlin

Durchgeführt von Claude Code im autonomen Betrieb mit Mahmouds Auftrag („alles automatisch machen“)
auf Grundlage der Freigabe vom 20.10. in `CLAUDE.md`. Die Tests waren vorab festgelegt im
[V10-Plan](../../../docs/superpowers/plans/2026-10-22-v10.md), bevor einer der Blöcke gespielt wurde.
Referenz war die damalige Abgabe **V7**.

## Was V10 ist

- **Dieselben 18 trainierten DQN-Netze wie V3/V7** (bitgleich). Neu ist nur die Konfiguration.
- V10 = V7 + `reach_assign` (Zielzuweisung nach Weglänge) + `sap_no_overkill` (keine Saps auf Ziele,
  die durch geplante Saps schon sterben) + `safe_moves`/`collision_guard` (keine Züge in Kollisionen
  mit stärkeren sichtbaren Gegnern) + `sap_still` (Halter-Saps nur auf stehende Gegner). Erklärung aller
  Änderungen: [Nachtbericht](../../../docs/NACHT_V7_V8_20261022.md).

## Nachweis (Karten-Bootstrap über Karten, 5000 Ziehungen, Seed 0; `scripts/v5_gates.py`)

| Schritt | Karten | V10 | V7 | Ergebnis |
|---|---|---|---|---|
| Entwicklung `dev_hard330`/`dev_easy330` | 660 | 77,9 % / 96,4 % | 58,3 % / 95,1 % | geschätzt gesamt ≈ 90,3 % statt 83,0 % |
| Auswahlblock 507220–507419 | 200 | Solution_92 93,0 %, default 100 % | 86,0 % / 100 % | Δ +7,0 [+2,8; +11,3], Hürde +1 bestanden |
| **Frisch 507420–508219** | **800** | **Solution_92 90,3 %**, default 99,75 % | 82,8 % / 99,9 % | **Δ +7,50 pp [+5,44; +9,62]** |
| **Direkt gegen V7 508220–508619** | 400 (800 Spiele) | **58,1 % [53,1; 62,75]** | – | untere Grenze > 0,5 |

Gates (`MIN_DELTA=0.02`), alle erfüllt: Solution_92 Δ ≥ +2 pp mit unterer 95%-Grenze > 0, default ≥ 99 %
und Δ ≥ −1 pp, direkt untere Grenze > 0,5. Rohdaten `experiments/compare/regeln/V10_*.csv`, Log
`experiments/pipeline_v10.log`.

Einordnung über die ganze Nacht (gegen Solution_92, frische Karten): V3 76,5 % → V7 83,5 %/84,6 % →
**V10 90,3 %**. Gegen V3 direkt (nur Info, mit V8): 75 %.

## Technische Prüfungen

- Installation per `scripts/release_candidate.py`: Manifest `experiments/releases/20261022_v10_V8st.json`.
- **Kurs-Runner unverändert: 8 Spiele bestanden** (beide Seiten, default und Solution_92, Seeds
  500720/500721), Gewichte verifiziert, frisches Gedächtnis je Spiel, `act` höchstens 11,3 ms pro Schritt
  (`experiments/analysis/release_v10_V8st_runner_installed.json`).
- Testsuite direkt nach der Installation: 463 bestanden. 31 Tests in
  `tests/test_early_curriculum_study.py` wurden von der Schutzsperre „Another model job is active“
  abgewiesen, weil gleichzeitig ein Training lief. Wiederholung ohne laufende Jobs: siehe Arbeitsstand.
- `agent.zip`-Bau mit `scripts/build_submission` am 22.10. mit V7 geprüft („Check ok“). Der Code ist
  derselbe, nur die Gewichtsdatei ist neu.

## Hashes und Rückweg

- Neu, beide Dateien: SHA-256 `03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67`.
- Vorher V7: `c394acba84f7a298f8f1e6107328d8e6ce151b367a28997b059aa82fc8a895e6`, bytegleich gesichert in
  `experiments/releases/20261022_v7_Bsnpd/` mit
  [Wiederherstellungsanleitung](../../releases/20261022_v7_Bsnpd/README.md). Ältere Sicherungen
  (`20261022_all18_v3`, `20261020_old3_sym3`) bleiben unverändert.

## Grenzen

- Gemessen gegen Solution_92, default und eigene frühere Stände. Gegner im Kursturnier sind unbekannt.
- Netze unverändert aus dem V3-Training (66.000 Trainingsspiele). Die Abgabe enthält weiterhin
  trainierte Gewichte. V10 ändert Regeln und Gedächtnis zur Laufzeit.
