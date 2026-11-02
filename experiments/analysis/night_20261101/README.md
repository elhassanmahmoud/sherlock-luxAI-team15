# Sherlock: Verbesserungsnacht 01./02.11.2026

Ausgangspunkt ist die unveränderte V14-Abgabe, nicht V10. Der Plan liegt unter
`docs/superpowers/plans/2026-11-01-night-improvement.md`; dieses lokale Sechserpanel
ist ausdrücklich ein anderes als Mahmouds historisches Battle-Panel.

## Entscheidung: V14 bleibt die Abgabe

Die Auswahl mit 3.100 Spielen und die unabhängige Bestätigung mit 6.000 Spielen
sind vollständig und unabhängig geprüft. **CONTROL ist nicht qualifiziert.**
Keine Übernahme, kein Nachrücken. Einzelheiten und Bedingungen: [DECISION.md](DECISION.md).

| Vergleich | Auswahl: 50 Karten | Unabhängige Bestätigung: 200 Karten |
|---|---|---|
| CONTROL gegen V14 im lokalen Panel | +4,83 pp | **−0,167 pp**, 95%-KI [−2,375; +2,000] pp |
| Solution_92 | 95/100 statt 94/100 Siege | **384/400 statt 382/400**, Δ +0,50 pp, KI [−1,25; +2,50] pp |
| Direkt gegen V14 | 62/100 | **201/400**, KI [43,50; 57,00] % |
| default | Beide 100/100 | Beide **400/400** |

Der Auswahlvorteil wurde nicht repliziert. Panel-Mindestgewinn und Panel-
Untergrenze, Solution-Untergrenze und Direkt-Untergrenze sind verfehlt.
`overlap` und `discovery` haben bereits die Auswahlbedingungen nicht erfüllt.
Die Abgabe bleibt V14 mit 36 Netzen, SHA-256 beider Gewichtsdateien
`98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`.

Der Zeitnachtrag [confirmation_time_addendum.json](confirmation_time_addendum.json)
wurde am 01.11., **22:33:45 Berlin**, vor Ergebnislektüre und vor dem Abschluss
des ersten Auswahljobs festgelegt: 200 statt ursprünglich 300 Karten, eigene
vollständige Phase, unveränderte Gates und genau ein Nominee. Geringere Präzision
wird offen ausgewiesen; keine nachträgliche Teilmengenauswertung. Bestätigungsseeds
832000–832199 und getrennte Direktseeds 833000–833199. Alle Spielquellen, HEAD
`aa06601` und Gewichte blieben bis zum Abschluss eingefroren.

Dieses lokale Panel enthält Solution, Quadrat-Solution, V3, V7, V10 und V13.
Es ersetzt nicht Mahmouds historisches Panel. Ein gepaarter Trainingsstart
beweist keine allgemeine Wirkung oder Wirkungslosigkeit der Lernverfahren;
aus den Gesamtwerten ist keine einzelne Verhaltensursache nachgewiesen.

## Tatsächlich abgeschlossene Vorarbeiten

- Baseline: 628 Tests und 14 Untertests, danach 676 Tests und 14 Untertests
  mit den neuen Prüfungen.
- Flag-aus-Kompatibilität: vier Spiele je Version, insgesamt acht; Aktionen beider
  Spieler und alle Nicht-Zeit-Metriken identisch.
- Schattenprobe auf 40 Diagnosekarten, beide Seiten: 80 Spiele, zusätzliche
  51 positive und 200 Null-Fakten (je Spiel/Match/Feld), verteilt auf neun Spiele.
  Kein aufgezeichneter falscher Zusatzschluss; nur technische Zulassung, kein
  Stärkenachweis. `steps=300` zählt Nichtreset-Beobachtungen, nicht die 303 Engine-Schritte.
- Kontrollierter Trainingspilot: 600 Trainingsspiele und 120 Prefill-Spiele je Arm;
  zusätzlich je 96 Validierungsspiele auf bekannten Karten. Insgesamt 1632 Spiele.
  Einziger Konfigurationsunterschied: Entdeckungsreward 0,5 gegen 2,0.
- Nachweislich Endgewichte nach 600 Spielen und 90.000 Updates verwendet, keine Wahl des
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
Alle drei Kandidaten bleiben Experimente; V14 wurde nicht ersetzt. Abschließende
Tests, Paketprüfung, Archivierung und Übertragung sind getrennte Arbeiten und
werden hier nicht als abgeschlossen ausgegeben. Die optionale Verlustdiagnose
ist bis zum Ende der Kernprüfungen und einer eigenen Freigabe zurückgestellt.

## Belege und Reproduktion

- `baseline.json`, `environment.json`: Ausgang und tatsächliche lokale Versionen.
- `*_freeze.json`, `*_state.json`, `*_receipt.json`: Inputs, Aufrufe und Abschlüsse.
- `selection_summary.json`, `confirmation200_summary.json`, `DECISION.md`:
  abgeschlossene Ergebnisse und endgültige Entscheidung.
- `confirmation200_jobs.json`, `confirmation_time_addendum.json`: konkrete
  Bestätigungsphase und vor Ergebnislektüre festgelegter Zeitnachtrag.
- `probe-data-review.md`, `training-data-review.*`, `code-review.md`,
  `statistics-review.md`: unabhängige Prüfungen und Grenzen.
- `run_jobs.py`: nur vollständige, quellengebundene Evaluationsphasen mit zwei
  Workern; alle tatsächlich geladenen Gewichte müssen vorhanden und eingefroren sein.
- `summarize.py selection|confirmation`: prüft die Bindung an vorregistrierte
  Jobs, vollständige Rohdaten und feste Karten/Gegner vor den Karten-Bootstraps.
  Für `confirmation200` **nicht** das alte, auf 300 Karten festgelegte
  `summarize.py confirmation` verwenden. Der geprüfte externe Auswerter liegt
  während der Messung unter `/tmp/sherlock-night-20261101/`; bytegleiche Kopien
  sind jetzt hier als `confirmation200-summary.py` und
  `confirmation200-independent-audit.md` archiviert. Beide Auswertungen stimmen
  überein; `external_evidence_archive.json` bindet die ursprünglichen Hashes.
  Vorhandene Zusammenfassungen werden nicht überschrieben.
- Historische Manifeste enthalten absolute Pfade auf Moayeds Mac. Nicht durch
  neue Pfade oder einen anderen HEAD ersetzen; für Reproduktionen neue Ausgaben
  und ein neues Manifest anlegen, kein alter Freeze auf neuer Quelle.
- CSV-Zeilenenden werden mit `.gitattributes` erhalten, damit Hashes über Git stabil sind.

Die anfänglichen Designberichte sind Vorschläge vor Umsetzung. Maßgeblich sind
Plan, endgültige Umsetzungsberichte und tatsächliche Journal-/Datenbelege. Die
36-Netz-V14-Sicherung bleibt unter `experiments/releases/20261101_v14_baseline/`.

## Nach der abgeschlossenen Entscheidung

694 Tests + 14 Untertests und acht vollständige Kursprüfspiele bestanden.
Das lokal neu gebaute V14-Paket ist in `submission_validation.json` dokumentiert;
beide Ablageorte, eingefrorenes Training und Tensor-/Dateiidentität sind geprüft.
Die Gewichte bleiben unverändert. Der Paketfilter entfernt ungültige lokale
Python-Dateikopien; interne Repo-Dokumente werden nicht mitgeliefert.

Zwölf zusätzliche Nachspiele auf sechs bereits bekannten Verlustschlüsseln sind
unter `remaining_solution_losses/` gespeichert. Das sind qualitative Fälle,
keine neue Stärkenbestätigung oder Kandidatenauswahl. Der unabhängige
Diagnosereview prüft die verfügbaren Felder und nennt die Ausgabengrenzen.
Die weitere Schluss-/Git-Übergabe steht im Morgenbericht.
