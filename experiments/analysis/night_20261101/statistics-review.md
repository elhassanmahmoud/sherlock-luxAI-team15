# Unabhängiger Lesereview: Nachtstatistik und Trainingsabnahme

Geprüft: `experiments/analysis/night_20261101/summarize.py`, `run_training.py` sowie die tatsächlich aufgerufenen Funktionen in `run_jobs.py`, `scripts/compare_report.py`, `scripts/league_gates.py` und `scripts/early_curriculum_study.py`. Gegenstand ist der Nachtplan `docs/superpowers/plans/2026-11-01-night-improvement.md`.

**Keine Quelländerungen, Tests, Modelljobs oder Lux-Spiele ausgeführt.** Root führte währenddessen Kompatibilitätsjobs aus. Ein gefälschter CSV-Test war für die unten direkt aus dem Kontrollfluss ableitbaren Lücken nicht erforderlich und wurde nicht gestartet. Es lagen beim Review noch keine Auswahl-/Bestätigungsphasendateien zur Prüfung ihrer konkreten Inhalte vor; die Abnahmelogik wurde überprüft.

## Nachprüfung nach Roots Korrektur – aktueller Abnahmestand

Die korrigierte `summarize.py` wurde erneut vollständig gelesen. Die ursprünglichen P1-Phasenbindungen und die P2-Panel-/Tie-Bindungen sind **geschlossen**: exaktes lokales Sechserpanel und V14-Direktreferenz, eingebettete Phase gleich Original-JSON, vollständiger tatsächlicher Command gleich geplantem Command, feste Kartenanzahl und Seedblöcke, exakte Gegnerstrings, eindeutige Jobliste in A/B/C-Reihenfolge sowie Bestätigung an SHA und Nominee der Auswahl gebunden. Dadurch erzwingt der vorhandene CSV-Validator jetzt auch die vorregistrierten vollständigen 50-/300-Karten-Schlüssel. Keine weiteren Statistikblocker für Trace und Trainingsstart gefunden. Keine Zusatztests oder Spiele für diese Nachprüfung ausgeführt.

**Offen vor Zulassung von B/C, nicht vor Trainingsstart:** Eine technisch abgeschlossene Supervisorphase (`training_state.status=complete`) ist noch keine fachlich abgenommene Trainingsstudie. Wie Root ausdrücklich festgelegt hat, prüft dieser Reviewer nach Trainingsende unabhängig die tatsächlichen Manifeste, Arm-Provenienz, Initial-/Quellhashes, vollständigen Trainings-/Valdaten und den einzigen Config-Unterschied gegen den festen Plan. Dabei kann ein technisch fertiges Paar vor Kandidatenzulassung abgelehnt werden. Dafür sind keine weiteren Supervisoränderungen vor dem Start erforderlich. Die konkrete Checkliste steht im Abschnitt zur Trainingsabnahme unten.

Die ursprünglichen Befunde und Begründungen folgen als Reviewhistorie; die beiden geschlossenen Statistikbefunde sind keine aktuellen offenen Punkte.

## Ursprüngliches Ergebnis vor der Korrektur

Die mathematischen Aggregationen und numerischen Gates entsprechen dem Plan. Vor einer automatischen Freigabe sollten jedoch die Bindung der tatsächlichen CSV-Jobs an die vorregistrierte Phase und die Trainingspaar-Abnahme verstärkt werden. Das ist kein Befund, dass die laufenden Kompatibilitätsmessungen oder spätere Daten tatsächlich falsch sind.

### P1: `summarize.py:24–34` bindet die ausgewerteten Job-Commands nicht an die Vorregistrierung

Das Skript prüft den SHA-256 der originalen Phasendatei, liest für seine Regeln aber `state['phase']`. Es prüft weder `json.loads(original.read_text()) == state['phase']` noch die Zuordnung jedes geloggten Jobs zu dem gleichnamigen vorregistrierten Job samt vollständigen Argumenten. `validate_output(path, args)` erhält die **geloggten** Argumente und ist somit nur ein Vollständigkeitscheck relativ zu diesen Argumenten. `len(frames)==len(spec['jobs'])` schützt weder erwartete Namen/Commands noch Seedbereich, Stichprobengröße, tatsächlich verwendete Gewichte und Overrides gegenüber dem Plan.

Konkreter Fehlerpfad ohne statistische Spezialfälle: Die Originalphase kann unverändert 300 Bestätigungskarten verlangen, während die drei geloggten Commands versehentlich `--n 2` tragen. Haben ihre CSVs die laut diesen Commands vollständigen zwei Karten, stimmen ihre CSV-Hashes und bleibt die Zahl der Jobs drei, akzeptiert `summarize.py` diese kleinere Phase. Es gibt keinen Check `panel['maps']==300` oder `direct['maps']==300`. Bei auf diesen zwei Karten stets positivem Ergebnis wären auch Bootstrap-Untergrenzen positiv und eine falsche Freigabe möglich. Dafür muss weder die Originaldatei verändert noch ihr SHA gebrochen werden.

**Minimaler Fix:** Original-JSON tatsächlich laden und mit eingebettetem `state['phase']` vergleichen; eindeutige Jobnamen verlangen; exakten Namenssatz vergleichen; pro Name den vollständigen `record['command']`-Payload an `spec['jobs'][name]['args']` binden, einschließlich Script, `--weights`, `--set`, `--first`, `--n`, Gegner und Ausgabepfad. Zusätzlich die erwarteten Kartenanzahlen/-bereiche, die sieben Panel/default-Gegner pro normalem Job und genau einen Direktgegner prüfen. Dadurch bleiben die bereits guten CSV-Schlüsselchecks von `run_jobs.validate_output` wirksam gegen den echten Plan.

### P2: `summarize.py:25,36,53–54` prüft Panelidentität und A/B/C-Gleichstand nicht explizit

Es werden nur sechs unterschiedliche Panelnamen verlangt. Der Plan verlangt genau Solution, Quadrat-Solution, V3, V7, V10 und V13 mit vorab eingefrorenen konkreten Gewichten. Die spätere Konfidenzberechnung ist für jedes beliebige Sechserpanel korrekt; sie beweist deshalb nicht, dass es das vereinbarte Panel ist.

Gleichstände behalten den ersten Namen in `spec['candidates']`. Das erfüllt „A vor B vor C“ nur, wenn der Phasenersteller diese Reihenfolge richtig vorgibt. Es existiert kein expliziter Prioritätsvergleich und keine Validierung der Reihenfolge. Eine Kandidatenliste C/B/A würde unbemerkt die umgekehrte Tie-Regel ausführen.

**Fix:** Bei der Phasenherstellung und Abnahme das genaue Panel samt Referenz-/Gegnerdateibindung sowie Rollen/Prioritäten A/B/C prüfen. Entweder Kandidaten vor der Auswahl anhand deklarierter Rollen sortieren oder die vorregistrierte Reihenfolge strikt gegen A/B/C validieren. Der aktuell verwendete EPS-Abstand ist für praktisch gleiche Gleitkommazahlen angemessen; die Priorität selbst ist der fehlende Teil.

### P2: `run_training.py:11–28,67–75` erklärt unvollständig validierte Paare für vollständig

Positiv: exakt 600 CSV-Zeilen, fortlaufendes `game`, exakt die vorregistrierten Trainingskarten und beide Seiten, 303 Steps, Punktezählung v2 und identische Gegnerfolge beider Arme sind geprüft. Damit sind fehlende/verschobene Trainingsspiele gut abgesichert.

Der abschließende Manifestcheck verlangt jedoch nur `status=='done'` und `train_games==600`. Der CSV-Check verlangt nicht das exakte `TRAIN_FIELDS`-Schema, erlaubt identische aber beliebige Gegnerfolgen und prüft keine endlichen Leistungs-/Loss-/Lernzähler. Die beiden realen Manifest-Configs, Mix/Pfad/Seed/LR/Prefill/Val/Endstandparameter und die zugehörigen `INIT/arm_plans/...json` werden nicht miteinander abgeglichen. Ein `status=done` aus einem früheren Wrapperfehler mit z. B. anderem Reward, gleicher Default-only-Folge oder falscher Validierung könnte somit als korrektes gepaartes Experiment durchgehen. Der derzeit eingefrorene Helper setzt diese Parameter richtig; diese Lücke betrifft die unabhängige Endabnahme.

**Empfohlene Abnahme vor `journal['status']='complete'`:**

- Eindeutig genau zwei Rollen control/discovery und erwartete Namen; Manifestpfade und Initialpfad fest binden.
- Je Manifest seed 9, Training 294200–294499, lr 1e-4, prefill 120, kein geladenes altes Replay, Gegner-Mix .6/.2/.1/.1, kein Pool/Snapshot, bekannte acht Val-Karten und `val_every=300`, keine Testkarten, Endstandauswahl prüfen. Das im bestehenden finetune-Manifest gespeicherte obere `train_seeds`-Ende ist exklusiv 294500; die tatsächliche CSV endet bei 294499.
- Tatsächliche Configs vergleichen: ausschließlich `w_discovery` darf verschieden sein, control=.5/discovery=2.0; `w_explore=.3`, V14-/V12-Trainingsregeln und frozen=false prüfen.
- Arm-Provenienz `status=done`, identische Init-/Quell-/Starttensorhashes und genau eine gewollte Config-Abweichung prüfen; Quellfreeze ist bereits vorhanden.
- Vollständiges TRAIN_FIELDS-Schema und sinnvolle/endliche numerische Werte prüfen; Ergebnisse müssen zu Matchsiegen/Punkten passen. Lernzähler müssen plausibel steigen und am Ende >0 sein. Ein fertiger Job ohne Lernen darf nicht als neues Training gelten.
- `val.csv` vollständig für (after_games 0/300/600) × (default/solution92), jeweils 16 Spiele, prüfen. Diese Val ist bekannte Diagnose; kein günstiger Zwischencheckpoint darf den Endstand ersetzen.
- Falls Root eine komplette Zahl aller simulierten Spiele nennt: 120 Prefill +600 Training +96 Val =**816 pro Arm**, **1632 insgesamt**. Die 1200 Trainingszeilen sind korrekt als Trainingsspiele bezeichnet, aber nicht die Gesamtspielzahl des Piloten.

## Mathematisch und bezüglich des Plans korrekt

- `result` ist 1/0,5/0; Remis gehen mit halbem Gewicht in Siegquote und Delta ein. `counts()` zeigt volle Siege/Remis/Niederlagen separat und verdoppelt keine Zahl. `completed_games` summiert die tatsächlichen Frames einmal, nicht die wiederholt dargestellten Baseline-Zahlen jeder Kandidatentabelle.
- Für jedes Gegner-Delta werden Kandidat und Referenz auf `(opponent, seed, side)` eins zu eins gepaart. Erst dann werden beide Seiten pro Karte gemittelt. 5000 Bootstrapziehungen, RNG-Seed 0, 2,5/97,5-Perzentile. Keine Pseudoreplikation durch separat gezogene Seiten.
- Das Paneldelta mittelt pro Karte die zwölf Ergebnisse (sechs Gegner × zwei Seiten), zieht ganze Karten als Cluster und berücksichtigt so die gemeinsame Karte über alle Gegner. Es gibt keinen zweiten Bootstrap über schon gebootstrappte Einzelgegnerintervalle. Der Panel-Score gewichtet die sechs Gegner gleich.
- Das Direktduell mittelt ebenfalls beide Seiten je Karte und bootstrapt ganze Karten. Exakter einzelner Direktgegner wird verlangt.
- Auswahlgates: Panel-Delta ≥0,5 pp; Solution-Delta ≥0; default ≥99 %; direkt ≥50 %. Numerisch richtig mit EPS.
- Bestätigung: Panel-Delta ≥1 pp und untere Grenze >0; Solution-Delta ≥0 und untere Grenze ≥−1 pp; default ≥99 % und Delta ≥−1 pp; direkt untere Grenze >50 %. Inclusive/strict-Grenzen sind entsprechend dem Plan umgesetzt; kein V14-Teamentscheidungsbonus.
- Eine auf der Auswahl gewählte feste Modellkonfiguration wird auf separaten frischen Karten bestätigt. Keine Korrektur für Trainingsinitialisierungen wird behauptet; der Reward-Versuch bleibt ein gepaarter Start. Der Code hat keine implizite Stichprobenverlängerung und keine automatische Kandidatennachrückung.
- `run_jobs.validate_output` schützt die tatsächlich benannte CSV gut: exakt erwartete Schemafolge, keine fehlenden/zusätzlichen/doppelten Schlüssel, beide Seiten, endliche numerische Angaben, 303 Steps/v2, Ergebnis-/Punktkohärenz. Die P1-Lücke liegt eine Ebene davor, bei der Bindung dieser Erwartungen an die Vorregistrierung.
- Zeitzonen sind korrekt: 02.11. 04:00 UTC =05:00 Berlin; 04:30 UTC =05:30 Berlin. Beide Arme teilen eine maximale 7200-s-Frist ab Supervisorstart, Netzteil und eingefrorene Quellen werden während des Laufs geprüft; Fehler/Timeout stoppen beide eigenen Prozessgruppen.

## Erwartete Spielzahlen der Bewertungsphasen

Mit allen drei Auswahlkandidaten A/B/C: Baseline 50×2×7=700 Spiele, je Kandidat 700 Panel/default +100 direkte =800, also **3100 Auswahlspiele**. Bei zwei Kandidaten **2300**, bei einem **1500**. Es gibt pro normalem Bewertungsjob sechs Panelgegner plus default; default zählt nicht zum Panelmittel.

Bestätigung: Referenz 300×2×7=4200, Kandidat ebenfalls4200, separates Direktduell300×2=600, insgesamt **9000 Spiele**. Diese Zahlen sollten nach vollständiger Job-/Args-Bindung exakt zu `completed_games` passen. Eine Abweichung muss die Phase verwerfen, nicht bloß im Bericht erscheinen.

## Reviewstatus

Keine statistischen Formelfehler oder vertauschten Gategrenzen gefunden. Die Statistikbindungen wurden von Root korrigiert und per erneutem Lesereview bestätigt. Offener Pflichtpunkt ist ausschließlich die unabhängige fachliche Trainingsdaten-Abnahme vor B/C-Zulassung. Kein weiterer Framework- oder Supervisorumbau für den Start verlangt.
