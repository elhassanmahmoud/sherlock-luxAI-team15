# Sherlock: Morgenbericht vom 2. November 2026

**Diese Nacht hat keinen nachweislich stärkeren Bot geliefert. V14 bleibt unverändert die Abgabe.** Der einzige nominierte Kandidat CONTROL hat die vollständige unabhängige Bestätigung nicht bestanden. Die Daten sind geprüft; es gibt keine Übernahme und kein Nachrücken. Das lokale V14-Abgabepaket ist gebaut und geprüft. Wesentliche Code- und Datenstände sind auf GitHub übertragen; nachfolgende Dokumentation und abschließendes Aufräumen werden separat abgeschlossen.

## Ergebnisse: Auswahlvorteil nicht bestätigt

V14 besteht aus 36 Netzen. OVERLAP ergänzt nur eine standardmäßig ausgeschaltete exakte Inferenzregel; CONTROL und DISCOVERY ergänzen das V14-Ensemble jeweils um ein nachtrainiertes Netz auf 37 Netze. CONTROL verwendet den normalen Entdeckungsreward 0,5, DISCOVERY den Wert 2,0. Alle ursprünglichen V14-Netze bleiben identisch.

Die feste Auswahl umfasste 50 Karten, beide Seiten, sechs Gegner plus default und je einen Direktvergleich gegen V14: insgesamt **3.100 Spiele**. Intervalle in den Tabellen sind 95%-Kartenintervalle; Δ bezeichnet die Veränderung gegenüber V14 in Prozentpunkten.

| Kandidat | Δ lokales Panel, 95%-KI | Solution_92 | Direkt gegen V14, 95%-KI | Auswahl |
|---|---|---|---|---|
| OVERLAP | −0,33 pp [−1,67; +0,67] | 94/100 statt 94/100; Δ 0 [0; 0] pp | 50,0 % [50; 50] % | Nicht zugelassen |
| CONTROL | **+4,83 pp [+0,33; +9,33]** | 95/100 statt 94/100; Δ +1 [−4; +6] pp | 62,0 % [49; 75] % | Einziger Nominee |
| DISCOVERY | −0,33 pp [−4,83; +4,17] | **96/100** statt 94/100; Δ +2 [0; +5] pp | 45,0 % [32; 58] % | Nicht zugelassen |

CONTROL erreichte 503 statt 474 Siege im 600-Spiele-Panel. Netto stammt der gesamte Auswahlgewinn aus V10 (+18 Siege) und V13 (+11); gegen V7 gingen sechs Siege verloren. Die einzelnen Erkundungs-/Sap-/Belegungsmetriken beweisen keine bestimmte Ursache. Insbesondere war der höhere Entdeckungsreward trotz seiner guten einzelnen Solution-Zahl insgesamt nicht robust genug. [Auswertung und Grenzen](../experiments/analysis/night_20261101/selection-interpretation.md), [Auswahldaten](../experiments/analysis/night_20261101/selection_summary.json).

Die anschließende unabhängige Bestätigung enthielt **6.000 Spiele** auf 200 frischen Karten für die Gegnervergleiche und 200 getrennten Direktkarten:

| Kriterium | CONTROL gegen V14 | Bedingung und Entscheidung |
|---|---|---|
| Lokales Panel | 81,375 statt 81,542 %; **Δ −0,167 pp**, KI **[−2,375; +2,000] pp** | Δ ≥ +1 pp und untere Grenze > 0: verfehlt |
| Solution_92 | **384/400 statt 382/400**; Δ +0,50 pp, KI **[−1,25; +2,50] pp** | Untere Grenze mindestens −1 pp: verfehlt |
| Direkt gegen V14 | **201/400**, 50,25 %; KI **[43,50; 57,00] %** | Untere Grenze > 50 %: verfehlt |
| default | Beide **400/400** | Bestanden |

Der Auswahlgewinn von +4,83 pp hat sich nicht wiederholt. Das bestätigt weder einen sicheren Schaden durch CONTROL noch seine Gleichwertigkeit; der geforderte Verbesserungsnachweis fehlt. Auswahl- und Bestätigungskarten werden nicht nachträglich gepoolt. [Entscheidung](../experiments/analysis/night_20261101/DECISION.md), [Bestätigung](../experiments/analysis/night_20261101/confirmation200_summary.json), [unabhängige Daten- und Statistikprüfung](../experiments/analysis/night_20261101/confirmation200-independent-audit.md).

Der Wechsel von ursprünglich 300 auf 200 Bestätigungskarten wurde **vor Ergebnislektüre am 01.11., 22:33:45 Berlin** wegen der gemessenen Laufzeit festgelegt, bevor ein Auswahljob abgeschlossen war. Es war eine eigene vollständige Phase mit unveränderten Gates und genau einem Nominee; die kleinere Stichprobe hat geringere Präzision. [Zeitnachtrag](../experiments/analysis/night_20261101/confirmation_time_addendum.json).

Das lokale Panel umfasst Solution, Quadrat-Solution, V3, V7, V10 und V13. Es ist ein anderes Panel als Mahmouds historischer Vergleich mit `league_nets6` und `threat6`; die Mittelwerte sind nicht direkt vergleichbar. Der Trainingsversuch ist außerdem nur **ein gepaarter Start**. Er beweist weder die allgemeine Wirkungslosigkeit von Nachtraining noch eine allgemeine Überlegenheit eines Rewards. Lernen, zusätzliches Netz und veränderte Ensemblegewichtung sind gegenüber V14 nicht vollständig getrennt.

## Training, Informationsdiagnose und Spielumfang

Beide Trainingsarme starteten aus derselben geprüften V14-Komponente mit frischem Optimierer und neu gefülltem Replay. Je Arm wurden 600 Trainingsspiele und 120 Prefill-Spiele vollständig ausgeführt; hinzu kamen je 96 Validierungsspiele auf bekannten Karten. Der einzige Configunterschied war der Entdeckungsreward. Verwendet wurden nachweislich die Endgewichte nach **90.000 Lernupdates**, keine günstig ausgewählten Zwischenstände. Gesamte Pilotdauer: rund 40 Minuten 42 Sekunden. [Unabhängige Trainingsabnahme](../experiments/analysis/night_20261101/training-data-review.md).

Die Overlap-Schattenprobe fand auf 40 Diagnosekarten, beide Seiten, **51 zusätzliche positive und 200 Null-Fakten** in neun von 80 Spielen, ohne aufgezeichnete falsche Zusatzfakten. Das war ein technischer Informationsnachweis, kein Stärkenachweis; die spätere Auswahl blieb negativ. Die 300 gezählten Nichtreset-Beobachtungen je Diagnose entsprechen nicht der Spalte mit 303 Engine-Schritten regulärer Spielausgaben. [Daten- und Mechanismusprüfung](../experiments/analysis/night_20261101/probe-data-review.md).

Ein begrenzter exakter Gauß-Prototyp wurde getrennt technisch vorbereitet und rein geprüft. Er ist weder Bestandteil dieser Abgabe noch dieser Stärkenstudie; es wurden damit keine neuen Stärke- oder Shadow-Spiele gestartet.

| Explizit protokollierter Umfang | Spiele |
|---|---:|
| Training: 2 × 600 | 1.200 |
| Prefill: 2 × 120 | 240 |
| Bekannte Validierung: 2 × 96 | 192 |
| Feste Auswahl | 3.100 |
| Unabhängige Bestätigung | 6.000 |
| Technik und Schattenprobe: 8 Kompatibilität + 2 Rauchprobe + 80 Diagnose | 90 |
| Abschließende vollständige Kursprüfspiele | 8 |
| Zwischensumme vor zusätzlicher Verlustdiagnose | 10.830 |
| Zusätzliche Verlustdiagnose: 6 bekannte Spiele × 2 Werkzeuge | 12 |
| **Gesamtzahl explizit protokollierter Spiele** | **10.842** |

Damit sind **1.632 Trainings-/Prefill-/Validierungsspiele**, **9.100 Vergleichsspiele** und **98 Technik-/Schatten-/Kursprüfspiele** dokumentiert; die **zwölf zusätzlichen Diagnosen** kommen separat hinzu. Softwaretests sind keine zusätzlichen Spiele. Aus dieser lokalen Zählung wird die historische projektweite Millionenzahl nicht neu hochgerechnet.

## Tatsächlich abgeschlossene technische Prüfungen

- Abschließende Suite: **694 Tests und 14 Untertests bestanden**, 119,95 Sekunden. Ausgangsprüfung: 628 und 14; integrierter Zwischenstand: 676 und 14. [Finaler Testlog](../experiments/analysis/night_20261101/final-tests.log).
- Opt-in aus: vier vollständige Spiele je Codeversion, insgesamt acht; Aktionen beider Spieler und alle Nicht-Zeit-Metriken identisch. [Kompatibilitätsbeleg](../experiments/analysis/night_20261101/compatibility_verdict.json).
- **Acht vollständige Kurs-Runner-Spiele mit V14 bestanden**, jeweils 303 Schritte: beide Seiten gegen default/Solution auf zwei bereits bekannten Karten, jeweils frisch geladenes Gedächtnis und korrekt geladenes Modell. Aktionsmediane 6,47–7,97 ms, größtes gemessenes Maximum 12,00 ms. Das prüft Integration und Aktionsformat, keine neue Siegquote und kein unbekanntes Kurs-Zeitlimit. Gewichte und Kurs-Runner blieben unverändert. [Runnerbericht](../experiments/analysis/night_20261101/v14_final_runner.json).
- Das Paket enthält 36 Netze und alle **14 Python-Quelldateien bytegleich**, zusätzlich einen leeren Paketinitializer: 15 Python-Dateien insgesamt. Alle Checkpointfelder und Tensoren stimmen mit V14 überein; einzige beabsichtigte Änderung ist `cfg.frozen=True`. Zwei Kursverzeichnis-Layouts und vier Prüfungen mit `train=True` bestätigen das eingefrorene Ladeverhalten. Interne Dokumentation sowie lokale `config 2.py`-/`reward 2.py`-Kopien sind ausgeschlossen. [Paketprüfung](../experiments/analysis/night_20261101/submission_validation.json), [unabhängiger Abschlussreview](../experiments/analysis/night_20261101/final-code-review.md).

## Abgabe und Identitäten

Die geprüfte lokale ZIP liegt unter `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/Gruppe15.zip`: **22.228.404 Bytes**, SHA-256:

```text
88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6
```

| Stand | SHA-256 der Gewichtsdatei |
|---|---|
| **V14 aktiv, beide Seiten und gesicherte Baseline** | `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8` |
| OVERLAP, abgelehnt | `ea7de4b22d81163e6e2cb7efe45aff78978827879c9707092f406035369e756d` |
| CONTROL, nicht bestätigt | `7a05e43f7ccc85ac9380c7140f94edf67d45c0bd50225f3dfdae4eb3d5c99600` |
| DISCOVERY, abgelehnt | `765d8ff758548c41929097e52db364377c9f3d99b251a2a2bb1adbe0a4ab31ab` |
| V14 im Paket, nur `frozen=True` ergänzt | `d3d87209ca3a0a44eae26f052d863e68f54b427cb1b0e19082a21b3bd02e05c4` |

Die V14-Sicherung bleibt unter `experiments/releases/20261101_v14_baseline/`. Herkunft, Einzelnethashes und unveränderte Ensemblebestandteile sind in den [Kandidatenprüfungen](../experiments/analysis/night_20261101/trained_candidate_checks.json) und im [Overlap-Checkpointbeleg](../experiments/analysis/night_20261101/overlap_checkpoint.json) dokumentiert. Plan, eingefrorene Inputs, Rohdaten und Reviews sind über das [Studien-README](../experiments/analysis/night_20261101/README.md) erreichbar.

## Bereitstellung für Mahmoud

Die wichtigen Code- und Datenstände sind auf GitHub: `c905c63` (Paketfilter) und
`139057f` (vollständige Auswahl/Bestätigung, Datenabnahme und negative Entscheidung).
Zuvor wurden bereits `6cd0403` (Vorabplan), `a67b785` (opt-in Overlap),
`a74abe9` (bewachter Trainingspilot), `7361371` (Datenbindungen und Kompatibilität),
`390de37` (Shadow-Probe) und `aa06601` (geprüfte Trainingsendstände/Kandidaten) übertragen.
Dieser Bericht, die zusätzliche Verlustdiagnose und die Quellenmemo gehören zum
abschließenden Dokumentationsstand auf main; dessen genaue ID steht im Git-Log.

Der technische Gauß-Folgeprototyp ist getrennt auf
`improvement/november-followup-20261101` bis `307b1ed` veröffentlicht (Umsetzung
`929b11f`). **Kein Merge in main, keine Battle-Freigabe:** echte Agenten-/Shadow-
und Stärkenprüfungen bleiben dort offen. Der Zweig enthält eine entsprechende Übergabe.

Alle eigenen Modellläufe sind beendet; der eigene Remote-Watcher ist beendet,
beide Nachtaufträge sind deaktiviert. Der frühere Oktoberauftrag bleibt pausiert.
[Abschlusskontrolle](../experiments/analysis/night_20261101/handoff_checks.json).
Der kurze Wachhalteschutz wird nach dem abschließenden Git-Abgleich beendet.
Das lokale Paket ist geprüft; Moodle-Upload und eine neue Folienbearbeitung wurden
nicht ausgeführt. **Das Ziel von 100 % gegen Solution ist nicht erreicht.**

## Zusätzliche Diagnose der sechs bekannten V14-Niederlagen

Die separat freigegebenen **zwölf Nachspiele** sind abgeschlossen: sechs bekannte Auswahlspiele je Werkzeug, am 02.11. von **03:57:17 bis 03:58:16 Berlin**. Quellen, Gewichte, Engine und der während dieser Diagnose eingefrorene HEAD `139057f` blieben unverändert. Die Match-CSV reproduziert die ursprünglichen Gesamtpunkte und alle sechs 1:2-Gesamtstände; die Mechanismus-JSON reproduziert diese endgültigen Gesamtstände ebenfalls. Diese JSON gibt jedoch **keinen Gesamtschrittzähler, keine Matchendpunkte und keine einzelnen Matchsieger** aus. Solche fehlenden Felder wurden dort nicht unabhängig geprüft; die 303 Schritte stammen aus der ursprünglichen Vergleichs-CSV. [Datenabnahme und Ausgabegrenzen](../experiments/analysis/night_20261101/remaining_solution_losses/validation_summary.json).

In den **zwölf verlorenen Matches** dieser gezielt ausgewählten Spiele kam unser erster Punkt in zehn Fällen nicht später als beim Gegner. Trotzdem war die mittlere Belegung ab Schritt 50 in allen zwölf Fällen niedriger. **Frühes erstes Punkten beweist keine vollständige Zonenkenntnis; ein Besetzungsdefizit allein beweist keine Ursache.** Die Diagnose zeigt konkurrierende Lücken: 17,5 % unbekannte eigene Punktefeld-Schritte trotz bekanntem Relic, 3,8 % bei unbekanntem Relic; 38,1 % der freien bekannten eigenen Feld-Schritte hatten keine Zielzuweisung. Auf Punktefeldern lag die Energie bei uns in 40,9 %, beim Gegner in 27,3 % der Einheitenschritte unter den Sapkosten; Stacking lag bei 17,9 gegenüber 8,2 %. Das sind Begleitbilanzen dieser kleinen Verlustauswahl, keine neue Siegquotenmessung oder gesicherte Kausalkette. [Befunde, Tabelle und Rohdaten](../experiments/analysis/night_20261101/remaining_solution_losses/findings.md).

Definitionshinweis zu **38,1 % = 1681/4417**: „Frei“ heißt hier ohne eigene oder **sichtbare** gegnerische Unit im Vor-Aktionszustand, nicht nachweislich unbesetzt. „Zugewiesen“ ist der aktuelle Zielplan **vor Netzentscheidung und Aktionsüberschreibungen**, kein tatsächlich ausgeführter Zug. Einheitenknappheit, unerreichbare Felder und gleichrangige nahe Gegnerfelder sind darin nicht als Ursachen getrennt. [Quellenprüfung der Zielmetrik](../experiments/analysis/night_20261101/targeting_metric_notes.md).

Die konkrete nächste Messfrage lautet: **Welche tatsächlich freien, bereits bewiesenen eigenen Punktefelder bleiben trotz erreichbarer und handlungsfähiger Unit wie lange unversorgt?** Einheitenmangel, Zielkosten und konkurrierende Störwirkung auf Gegnerfeldern, Laufwege/Rückkehr sowie Energie-/Halterverluste und Aktionsüberschreibungen müssen dabei von noch ungeklärten Relic-Zonen getrennt werden. Frühere pauschale Heimprioritäten brachten keinen belegten Gewinn; diese Diagnose empfiehlt keinen solchen Sofortfix, keine neue Kandidatenwahl und keine Übernahme. V14 bleibt unverändert die Abgabe.
