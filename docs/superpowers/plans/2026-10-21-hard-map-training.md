# Training mit Schwerpunkt auf schweren Karten (Prioritized Level Replay): vorab festgelegt

21.10.2026, ca. 22:30, Claude Code mit Mahmoud. Festgelegt vor dem Training und vor jeder
Auswertung der neuen Netze.

## Hypothese

V3 verliert vor allem auf Karten mit umkämpften Relic-Haufen (Festung, Wettlauf, neues
Relic-Paar; [Diagnose](../../../experiments/analysis/mechanism_probe_20261021/README.md)).
Im bisherigen Training sind solche Karten selten, die Netze sehen diese Lagen kaum. Mehr
Trainingsspiele genau auf diesen Karten sollen die gelernte Entscheidung dort verbessern.

## Kartensuche (vor dem Training)

- V3 (Abgabe, unverändert) gegen Solution_92 auf 2000 neuen Trainingskarten 360000–361999,
  beide Seiten (`experiments/compare/regeln/H21_screen_v3_360000.csv`). Bereich vorher in
  allen CSVs ohne Treffer geprüft; liegt unter 500000, also außerhalb aller Bewertungsblöcke.
- Schwere Karte = V3 verliert mindestens eine Seite. Liste unverändert als JSON gespeichert
  (`experiments/analysis/hard_map_training_20261021/hard_seeds.json`).

## Training

- Variante `full_rules_v3` (wie Kontrolle `v3nets6`), Starts 40–45, je 3000 Spiele,
  `--sol92-frac 0.7`; einziger Unterschied: `--seed-file hard_seeds.json` – alle
  Solution_92-Spiele laufen auf schweren Karten (beide Seiten je Karte, je Start versetzt).
  Aufwärm-/default-Spiele unverändert. Läufe `20261021_full_rules_v3_s4X_hard`.

## Auswahl (Block 503820–504019, 200 Karten, beide Seiten, default + Solution_92)

- `hard6` (6 neue Netze) und `hard24` (`hard6` + 18 V3-Netze), dazu V3 und `v3nets6` auf
  denselben Karten. Keine Auswahl einzelner Netze oder Zwischenstände.
- Methodenfrage: `hard6` gegen `v3nets6`.
- Genau ein Kandidat (der bessere von `hard6`/`hard24`) geht weiter, wenn er ≥ +3
  Prozentpunkte vor V3 liegt und default ≥ 99 % erreicht. Sonst Ende.

## Bestätigung (einmalig, frisch) und Übernahme

Wie im [Plan Gefahr-Merkmale](2026-10-21-threat-features.md): 503420–503619 Kandidat und V3
gegen beide Gegner, 503620–503819 direkt gegen V3. Übernahme nur bei Solution_92 Δ ≥ +5 pp
mit unterer 95%-Grenze > 0, default ≥ 99 % und Δ ≥ −1 pp, direkt untere Grenze > 0,5. Vorher
V3 sichern, Kurs-Runner-Prüfung, Testsuite, Rücksprache mit Moayed.
