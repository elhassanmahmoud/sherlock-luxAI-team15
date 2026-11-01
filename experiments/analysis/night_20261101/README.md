# Sherlock: Verbesserungsnacht 01./02.11.2026

Ausgangspunkt ist die unveränderte V14-Abgabe, nicht V10. Der Plan liegt unter
`docs/superpowers/plans/2026-11-01-night-improvement.md`; dieses lokale Sechserpanel
ist ausdrücklich ein anderes als Mahmouds historisches Battle-Panel.

## Bisher tatsächlich abgeschlossen

- Baseline 628 Tests +14 Untertests, danach 676 +14 mit den neuen Prüfungen.
- Flag-aus-Kompatibilität: vier Spiele je Version, insgesamt acht; Aktionen beider
  Spieler und alle Nicht-Zeit-Metriken identisch.
- Schattenprobe auf 40 Diagnosekarten, beide Seiten: 80 Spiele, zusätzliche
  51 positive und 200 Null-Fakten (je Spiel/Match/Feld), verteilt auf neun Spiele.
  Kein aufgezeichneter falscher Zusatzschluss; nur technische Zulassung, kein
  Stärkenachweis. `steps=300` zählt Nichtreset-Beobachtungen, nicht die 303 Engine-Schritte.
- Kontrollierter Trainingspilot: 600 Trainingsspiele und 120 Prefill-Spiele je Arm;
  zusätzlich je 96 Validierungsspiele auf bekannten Karten. Insgesamt 1632 Spiele.
  Einziger Konfigurationsunterschied: Entdeckungsreward 0,5 gegen 2,0.
- Nachweislich Endgewichte nach 600 Spielen/90000 Updates verwendet, keine Wahl des
  besten Zwischenstands. Unabhängige Datenabnahme in `training-data-review.md/.json`.

## Feste Auswahlkandidaten

A (`overlap`): V14 mit exakter Überlappungsinferenz, 36 unveränderte Netze.
B (`control`): V14 plus dem finalen Kontrollnetz, 37 Netze.
C (`discovery`): V14 plus dem finalen Bonusnetz, 37 Netze.
B/C haben dieselbe Laufzeitkonfiguration wie V14. Ihre 36 ursprünglichen Netze
sind unverändert. Der Reward-Versuch ist nur ein gepaarter Start; auch veränderte
Q-Wert-Skalierung kann den Effekt eines zusätzlichen Netzes beeinflussen.

Die Auswahl-/Bestätigungsbedingungen sind vorab im Plan und in den Jobmanifesten
festgehalten. Eine bestandene technische Abnahme ist kein Übernahmenachweis.
`selection_jobs.json` ist zugelassen; tatsächlichen Fortschritt ausschließlich
an `selection_state.json` und den Ergebnisdateien ablesen. Noch keine neue Abgabe.

## Belege und Reproduktion

- `baseline.json`, `environment.json`: Ausgang und tatsächliche lokale Versionen.
- `*_freeze.json`, `*_state.json`, `*_receipt.json`: Inputs, Aufrufe und Abschlüsse.
- `probe-data-review.md`, `training-data-review.*`, `code-review.md`,
  `statistics-review.md`: unabhängige Prüfungen und Grenzen.
- `run_jobs.py`: nur vollständige, quellengebundene Evaluationsphasen mit zwei
  Workern; alle tatsächlich geladenen Gewichte müssen vorhanden und eingefroren sein.
- `summarize.py selection|confirmation`: prüft die Bindung an vorregistrierte
  Jobs, vollständige Rohdaten und feste Karten/Gegner vor den Karten-Bootstraps.
  Vorhandene Zusammenfassungen werden nicht überschrieben.
- Historische Manifeste enthalten absolute Pfade auf Moayeds Mac. Nicht durch
  neue Pfade oder einen anderen HEAD ersetzen; für Reproduktionen neue Ausgaben
  und ein neues Manifest anlegen, kein alter Freeze auf neuer Quelle.
- CSV-Zeilenenden werden mit `.gitattributes` erhalten, damit Hashes über Git stabil sind.

Die anfänglichen Designberichte sind Vorschläge vor Umsetzung. Maßgeblich sind
Plan, endgültige Umsetzungsberichte und tatsächliche Journal-/Datenbelege. Die
36-Netz-V14-Sicherung bleibt unter `experiments/releases/20261101_v14_baseline/`.
