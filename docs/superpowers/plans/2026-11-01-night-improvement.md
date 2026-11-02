# November-Battle: Nachtplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Schritte taskweise prüfen.

**Goal:** V14 gezielt verbessern und die Abgabe bis 02.11., 06:00 Berlin prüfen.
**Architecture:** Opt-in Überlappungsinferenz plus kontrollierter Entdeckungsreward-Pilot;
höchstens ein Kandidat erhält eine unabhängige Bestätigung.
**Tech Stack:** vorhandenes Python/PyTorch/LuxAI, identische Kurs-Engine mit 3 Matches.
**Spec:** `docs/superpowers/specs/2026-11-01-night-improvement-design.md`.

## Global Constraints

- V14-Referenz SHA `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`.
- Maximal zwei Rechenworker; lange Jobs nur am Netzteil; kein paralleler Volltest.
- Keine fremden Dateien löschen, kein Force-Push, kein ungeprüfter Abgabetausch.
- Inferenz nutzt nur gültige Beobachtungsgleichungen; Orakel ausschließlich Diagnose.
- Mindestens 30 % Codex-Kontingent behalten; ab 65 % Verbrauch Abschluss einleiten.

## Review Focus

- Überlappung darf aus widersprüchlichen oder alten Spawn-Gleichungen nichts beweisen.
- MAX_RECORDS und Arbeitsgrenzen müssen auch bei dicht überlappenden Mengen gelten.
- Ausgeschalteter Schalter darf vorhandene Aktionen nicht ändern.
- Fehlende Startgewichte/Gegner müssen vor Jobs abbrechen; kein zufälliger Ersatzagent.
- Veränderte Quellen oder unvollständige Spielschlüssel machen eine Messung ungültig.

## Aufgaben

- [x] 1. V14 aktualisieren, Referenz-/Umgebungsbelege sichern, Baseline-Tests ohne andere Modelljobs.
- [x] 2. Überlappungsinferenz: rote Regression, minimale opt-in Umsetzung, grüne Regression,
  erschöpfender kleiner Wahrheitsvergleich, Leistungsgrenze und unabhängiges Review.
  Dateien: `agents/sherlock/{belief,config,main}.py`, `tests/test_overlap_inference.py`.
- [x] 3. Kontrollpilot vorbereiten: deterministisch Netzindex 18 aus V14 extrahieren,
  q/target=q, frischer Optimierer, keine Ensemble-Extras, Tensoridentität prüfen.
  Fehlende Quelle/ungültiger Index/existierendes Ziel ablehnen. Beide Arme erhalten
  identischen Ausgang und neue Buffer. Dateien: `scripts/night_train_pilot.py`,
  `tests/test_night_train_pilot.py`. Keine globale Variante dauerhaft verändern.
- [x] 4. Maximal 600 Trainingsspiele je Arm, gleiche Karten, seed=9/map_offset=4200,
  120 Prefill-Spiele, Lernrate 1e-4, bestehender Gegner-Mix 60 % Solution,
  20 % Quadrat-Solution, 10 % default, 10 % rush. Gleiche V12-Trainingsregeln
  plus V14-Konfiguration; eval-only Regeln bleiben ausdrücklich eval-only.
  Kontrolle `w_discovery=0.5`, Behandlung `2.0`; `w_explore=0.3` unverändert.
  Nur Endcheckpoint; Validierung unverändert 8 Karten, keine Optimierung danach.
  Höchstens zwei Stunden für beide Arme ab Trainingsstart. Bei unvollständigem
  Arm kein trainierter Kandidat für diese Nacht; Zwischenstände ehrlich sichern.
  Der Supervisorstatus `complete` bezeichnet nur den technischen Abschluss.
  Vor B/C-Zulassung prüft ein unabhängiger Datenreview zusätzlich Starttensor/
  Arm-Provenienz, tatsächliche Configs (einziger Unterschied Entdeckungsreward),
  Seed-/Gegnerplan, Prefill/Lernrate/Endstandwahl, vollständige Trainings- und
  Validierungsdaten, endlichen Loss und tatsächlichen Lernfortschritt.
- [x] 5. Kompatibilität mit Opt-in aus (4 Spiele) und Diagnosetrace (40 Karten)
  prüfen; ohne zusätzliche sichere Fakten im Trace keinen Inferenzkandidaten.
- [x] 6. Festen Auswahlsatz vollständig spielen; genau einen zugelassenen
  Kandidaten nominieren, danach frischen Bestätigungsblock ohne Nachjustieren.
- [x] 7. Nur qualifizierten Kandidaten sichern/übernehmen; sonst V14 behalten.
  Kurs-Runner, portable Battle-ZIP und Hashprüfung; Bericht, Commits und Push.

## Vorab festgelegte Karten und Kandidaten

Seed-Audits aller getrackten und vorhandenen lokalen Tabellen/Manifeste archivieren.
Absolute Env-Seeds, `par_eval --first = seed - 500000`:

| Block | Seeds | Zweck |
|---|---|---|
| Diagnose | 830000–830039 | Inferenztrace, keine Stärkenauswahl |
| Auswahl | 831000–831049 | 50 Karten × beide Seiten je Gegner |
| Bestätigung | 832000–832299 | 300 Karten × beide Seiten je Gegner |
| Direkt | 833000–833299 | 300 Karten × beide Seiten gegen V14 |
| Technikreserve | 834000–834099 | nur Kompatibilität/Kursprüfung |
| Training | 294200–294499 | 600 Spiele/Arm, Karten je beide Seiten |
| Prefill | 295000–295059 | 120 Spiele/Arm |

Schutzreservierung des Audits reicht ggf. weiter als die hier tatsächlich genutzten
Blöcke; keine nicht gespielten Karten als verbraucht ausgeben.
Alle weiteren Blöcke brauchen einen vor Ergebnissen dokumentierten Nachtrag.

Auswahlkandidaten: (A) V14 + Überlappungsinferenz, falls technisch zugelassen;
(B) V14-Ensemble plus finalem Kontrollnetz; (C) V14-Ensemble plus finalem
Entdeckungsreward-Netz. B/C verwenden V14-Inferenzconfig und jeweils 37 Netze,
keine gemeinsame Kombination mit A. Trainingspilot ist nur ein gepaarter Start.

Neues lokales Sechserpanel: `solution92`, `sol92_sq`, eingefrorene V3, V7, V10, V13.
Alle konkreten Gegnerdateien/Hashes vorab festhalten. Fehlende historische
`league_nets6`/`threat6` niemals durch untrainierte Netze ersetzen. Kein Vergleich
dieses neuen Panelmittels mit früheren Sechsermitteln.

Auswahl: V14 und Kandidaten auf denselben 50 Karten, alle sechs Gegner und default;
Kandidaten zusätzlich direkt gegen V14 auf denselben Auswahlkarten. Zulassung:
Panel-Δ ≥ +0,5 pp, Solution-Δ ≥ 0, default ≥ 99 %, direkt ≥ 50 %.
Nominiert wird höchstes Panel-Δ; Gleichstand A vor B vor C. Kein Nachrücken nach
gescheiterter Bestätigung. Auswahlwerte sind keine unabhängige Bestätigung.

Bestätigung: nominierter Kandidat und V14 auf den 300 neuen Bestätigungskarten
gegen Sechserpanel und default; Kandidat direkt auf dem getrennten Direktblock.
Alle Bedingungen müssen gelten: Panel-Δ ≥ +1 pp UND untere 95-%-Grenze > 0;
Solution-Δ ≥ 0 UND untere Grenze ≥ −1 pp; default ≥ 99 % UND Δ ≥ −1 pp;
Direktduell untere Grenze > 50 %. Vorher vollständige erwartete Schlüssel,
303 Schritte, Punktezählung v2 und identische Inputs prüfen. Gepaarter Bootstrap
ganzer Karten, 5.000 Ziehungen, Zufallsseed 0, 2,5/97,5-Perzentile.
Frühere Team-Ausnahme für V14 senkt diese Bedingungen nicht.

## Uhrzeit und Abbruch

Vor jeder Phase Laufzeit aus tatsächlich gemessenen Sekunden/Spiel abschätzen.
Nur beginnen, wenn vollständige Phase bis 05:30 Berlin mit Reserve passt; sonst
auslassen. Ab 05:00 keine neuen langen Jobs, 05:30–06:00 Schlussprüfung/Übergabe.
Keine selektive Auswertung unfertiger Blöcke, keine unbestätigte Übernahme.

## Ausführungsnachtrag vom 02.11. nach Ende der Messung

Der ursprüngliche Plantext bleibt als Vorabstand erhalten. Der vor Ergebnislektüre
um 21:33:45 UTC geschriebene `confirmation_time_addendum.json` reduzierte aus
gemessenen Laufzeiten die unabhängige Bestätigung auf **200 Karten**, alle Gates
unverändert. Diese vollständige Phase heißt `confirmation200`; 6.000 Spiele, kein
Abschneiden eines 300er-Laufs. Auswahl und Bestätigung liefen durchgehend auf
HEAD `aa06601` mit unveränderten Quellen und Gewichten.

3.100 Auswahlspiele nominierten CONTROL. Die 6.000 frischen Bestätigungsspiele
zeigten keinen Übernahmenachweis: Panel −0,167 pp [−2,375; +2,000], Solution
384/400 statt 382/400, direkt 201/400. Vier Gates verfehlt, Daten unabhängig exakt
nachgerechnet. V14 bleibt; kein Nachrücken. Details in
`experiments/analysis/night_20261101/DECISION.md`.

Nach Ende und Audit des Source-Freeze: Paketfilter separat übernommen,
694 Tests + 14 Untertests und acht Kurs-Runner-Spiele bestanden. Lokale Battle-ZIP
mit V14, zwei Ablageorten und eingefrorenem Training geprüft. Der Morgenbericht
und die Git-/Prozess-Abschlussprüfung dokumentieren den letzten Schritt.

Abschluss: zwölf qualitative Nachspiele auf sechs verbrauchten Verlustschlüsseln
reproduziert und separat nachgerechnet, ohne neue Gewichts-/Regeländerung.
Eigene Modellläufe/Remote-Watch beendet, Nachtaufträge deaktiviert. Bericht,
Paketbelege und Schlussdokumentation werden mit main abgeglichen. Keine neue
Stärkenstudie oder automatische Fortsetzung nach dieser Nacht.
