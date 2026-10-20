# Sherlock: autonomer Prüf- und Verbesserungsplan

> **For agentic workers:** Use superpowers:executing-plans to implement this
> plan task-by-task. Moayed requests sequential autonomous execution and
> pushing verified changes; do not ask again for routine stage approvals.

**Goal:** Den ersten begrenzten Verbesserungszyklus abschließen und anschließend
gemäß Moayeds erweitertem Nachtauftrag kontrolliert weiter verbessern und trainieren.

**Architecture:** Bestehende Auswertungswerkzeuge und Kandidaten verwenden.
Messung und Auswahl von Agentenlogik trennen; zunächst nur vorhandene Config-
Schalter variieren. Kurs-Runner in einer temporären Kopie mit instrumentiertem
Agenten prüfen, ohne seine Quelldatei oder die Abgabe zu verändern.

**Tech Stack:** Python 3.13, PyTorch, LuxAI-S3, pytest, bestehende CSV-Auswertung.

**Spec:** [Arbeitsauftrag und Auswahlregeln](../specs/2026-10-20-autonomous-improvement-design.md)

## Global Constraints

- Abgabe bis zur bestandenen Übernahmeprüfung unverändert; bisher beide SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`. Versionierte Sicherung unter `experiments/releases/20261020_old3_sym3/` dauerhaft erhalten.
- Maximal zwei Evaluationsprozesse, höchstens ein Training; keine Cloud-Kosten.
- Kurs-Runner unverändert; bestehende Kandidaten und Messdateien nicht ersetzen.
- Neue Arbeitsgrenze: 21.10.2026 04:00 UTC / 06:00 Berlin. Ab 05:30 Berlin nur noch rechtzeitig abschließbare Arbeiten; um 06:00 Morgenbericht und kontrollierter Abschluss.
- Entwicklung 500720–500779; Bestätigung 502420–502619 exklusiv reserviert.
- CNN3 nicht doppelt starten; keine BC-Datensammlung auf dem 8-GB-Rechner.
- Moayed hat den Austausch am 20.10. ausdrücklich freigegeben, sofern der Kandidat nachweislich besser ist. Übernahmeprüfung gemäß ergänztem Spec; Training überschreibt die Abgabe weiterhin nicht.
- Sinnvolle Commit-Grenzen: Prüfwerkzeug mit Tests; abgeschlossene Entwicklungsmessung mit Auswahlentscheidung; bestätigte Kandidatenänderung mit Prüfungen; Abschlussbericht. Zugehörige Dokumentation jeweils mitführen. Nur geprüfte Arbeit pushen, laufende Messungen nicht als abgeschlossen einchecken.

## Review Focus

- Mehrere Spiele/Seiten im selben Prozess: Gedächtnis darf nicht über Spiele lecken.
- Runner lädt unerwartete Gewichte: temporäre Pfade und Hashes prüfen.
- Partiell geschriebene CSV/Prozessfehler: nicht als fertiges Experiment auswerten.
- Durch Auswahldaten verzerrte Verbesserung: nur einen Herausforderer bestätigen.
- Push während fremder Änderungen: abgleichen, nie Force-Push; relevante Tests wiederholen.

## Fortschritt

- [x] Aufgabe 1: Referenz und technische Basis prüfen.
- [x] Aufgabe 2: Kursbetrieb prüfen.
- [x] Aufgabe 3: Begrenzte Entwicklungsmessung.
- [x] Aufgabe 4: Bestätigung und Gegnervergleich, falls Auswahlregel erfüllt.
- [x] Aufgabe 5a: Erster Zyklus abgeschlossen; V3 installiert, geprüft, gesichert und gepusht (`9d657dc`).
- [ ] Aufgabe 5b: Erweiterter Nachtauftrag und Morgenbericht um 06:00.

## Aufgabe 1: Referenz und technische Basis

**Files:** vorhandene `tests/`, `scripts/par_eval.py`, Kandidatenmanifest;
Ausgaben `experiments/analysis/autonomous_20261020/`.

**Interfaces:** Eingang `all18_v3.pth`; Ausgang geprüfter Hash, Testergebnis,
CSV für Seeds 500720/500721 und dokumentierte Pakete.

- [x] `pytest -q` ausführen. Erwartung: alle vorhandenen Tests erfolgreich;
  Fehler zunächst diagnostizieren, keine Agentenänderung auf Verdacht.
- [x] `all18_v3` auf zwei Entwicklungskarten gegen beide Gegner/beide Seiten
  auswerten und mit `M_fo10_ptsap_fc_720.csv` vergleichen.
  Erwartung: alle Spielkennzahlen außer Zeit identisch.
- [x] Abgabe-/Kandidatenhashes vor/nachher prüfen und Befund dokumentieren.

## Aufgabe 2: Kursbetrieb

**Files:** neues `scripts/check_candidate_runner.py`,
`tests/test_candidate_runner.py`; Ergebnis
`experiments/analysis/autonomous_20261020/runner.json`.

**Interfaces:** CLI `--weights PATH --out NEW_JSON`; Bericht über 8 Spiele
(2 je Seite/Gegner), Aktionsvalidierung und Zeitverteilung.

- [x] Tests zuerst: temporäre Paths.csv zeigt für Gruppe 15 auf die
  Kandidatenkopie; Original bleibt bytegleich; bestehender Ausgabebericht
  wird abgewiesen. Erwartung vor Implementierung: fehlendes Modul/Funktion.
- [x] Hilfsfunktionen `prepare_workspace(root, weights, destination)` und
  `validate_actions(actions, max_units)` implementieren. Workspace enthält
  kopierte Kandidatengewichte, eigene Paths.csv und Verweise auf Agentenmodule.
- [x] Aktionsvalidierung prüft Shape `(max_units, 3)`, endliche ganzzahlige
  Werte und Aktionstyp 0–5. Energie-/Asteroidenmasken bleiben vorhandenen
  Agententests und Evaluationsmetriken zugeordnet.
- [x] Runner-Aufruf `train=False`; Agent instrumentieren, Entscheidungslatenz
  messen und frisches Belief bei neuer Instanz prüfen. Startgewichte erhalten.
  Verwendete Zufallsseeds protokollieren; Runner-Ergebnisse nicht mit festen
  Benchmarkkarten verwechseln.
- [x] Unit-Tests und tatsächliche 8-Spiele-Prüfung ausführen; nur bei Erfolg
  Bericht/Code committen. Kein erfundenes Zeitlimit als bestanden melden.

## Aufgabe 3: Begrenzte Entwicklungsmessung

**Files:** neue CSVs unter `experiments/compare/autonomous_20261020/`,
Ergebniszusammenfassung unter `experiments/analysis/autonomous_20261020/`.

**Interfaces:** `scripts.par_eval` → vollständige CSVs, `scripts.compare_report`
→ gepaarte Vergleiche. Eingabe feste Referenz und vier Config-Overrides aus Spec.

- [x] Referenz und vier Varianten nacheinander ausführen, je 60 Karten,
  beide Seiten und Gegner, `--workers 2`. Neue Ausgabepfade verwenden.
- [x] Je Datei 240 eindeutige Zeilen und vollständige Seitenpaare prüfen;
  `point_counting_version=2`, keine fehlenden Ergebnisse.
- [x] Nach festgelegter Regel höchstens einen Herausforderer wählen;
  Entscheidung inklusive verworfener Varianten dokumentieren.
- [x] Zwischenstand samt verwendeten Seeds und unveränderten Gewichtshashes pushen.

## Aufgabe 4: Bestätigung und Gegnervergleich

**Files:** neue Referenz-/Herausforderer-CSVs auf Seeds 502420–502619 und
zusätzliche CSVs gegen alte Abgabe auf Entwicklungskarten.

**Interfaces:** eindeutige Auswahl aus Aufgabe 3; gepaarte Auswertung über Karten.

- [ ] Wenn keine Variante die Auswahlregel erfüllt: Aufgabe begründet überspringen.
- [ ] Referenz und genau einen Herausforderer auf den reservierten 200 Karten
  auswerten, beide Seiten, default/Solution_92, je 800 Spielzeilen.
- [ ] Gegen alte Abgabe (`self:agents/sherlock/weights/agent_p0.pth`) beide
  Varianten auf den 60 Entwicklungskarten prüfen.
- [ ] Auswahlregel aus Spec anwenden; bei Unsicherheit Referenz behalten.
  Nicht nachträglich andere Varianten auf demselben Bestätigungsblock suchen.
- [ ] Zusätzliche Übernahmeprüfung: alte Abgabe auf 502420–502619 gegen beide Gegner auswerten und gepaart mit dem ausgewählten Stand vergleichen. Ohne erfolgreichen Herausforderer V3 als einzigen Kandidaten gegen die alte Abgabe prüfen; dann diesen Teil trotz übersprungener Variantenbestätigung ausführen.
- [ ] Für die Übernahme auch direkten Vergleich des ausgewählten Stands gegen die gesicherte alte Abgabe auf den 60 Entwicklungskarten prüfen; Sicherungspfad als Gegner verwenden.

## Aufgabe 5: Abschluss

**Files:** `docs/ARBEITSSTAND.md`, dieser Plan, neuer Ergebnisbericht;
nur bei Erfolg neue Kandidatendatei und Manifest.

- [ ] Vollständige Ergebnisse und Grenzen zusammenfassen; bei Erfolg Config
  in neuen Checkpoint schreiben und gespeicherte Config gegen Override
  auf zwei bereits benutzten Karten prüfen.
- [ ] Betroffene Tests und Hash-Prüfungen durchführen.
- [ ] Änderungen unabhängig prüfen lassen, wichtige Befunde beheben.
- [ ] Nur bei erfüllten Übernahmekriterien: Sicherungsmanifest prüfen, beide Abgabedateien durch den geprüften Kandidaten ersetzen, Hash-Identität, Kursbetrieb und betroffene Tests erneut prüfen; bei Fehlern zurückrollen. Eigenen Übernahme-Commit samt Bericht und Rückweg erstellen. Andernfalls alte Abgabe behalten.
- [ ] GitHub abgleichen, geprüfte Änderungen pushen; Planstatus aktualisieren.
- [ ] Nach dem ersten Zyklus begründete weitere Schritte bis zur neuen Arbeitsgrenze bearbeiten; um 06:00 Morgenbericht und Weiterführung beenden.
  Offene Schritte und laufende Prozesse ausdrücklich benennen.

## Laufendes Protokoll

- 20.10.: Basis 153 Tests bestanden, V3 auf 8 Spielen identisch zur Referenz.
- Kursprobe: 8 Spiele, beide Seiten/Gegner, je 303 Schritte, frisches Belief und gültiges Aktionsformat. 9 neue Unit-Tests bestanden.
- Korrektur während Instrumentierung: Runner verwendet `np.random.default_rng`, nicht `np.default_rng`; eigener Regressionstest ergänzt und erfolgreich erneut geprüft. Agentenlogik blieb unverändert.
- Ausführungsentscheidung: bestehender Hauptcheckout und direkte kleine main-Commits gemäß Teampräferenz; kein zusätzlicher Worktree.

- Abschluss Aufgabe 2: unabhängiger Review-Befund zum stillen Checkpoint-Fallback behoben; 163 Tests bestanden und 8 Runner-Spiele mit verifizierten 18 Netzständen erfolgreich (`runner_verified.json`). Kein offener wichtiger Befund.
- Automation: `sherlock-verbesserungsplan-fortsetzen`, nur noch Morgenbericht um 06:00. Moayed verlangt seit 19:39 kontinuierliche aktive Arbeit statt Intervallsteuerung; bis dahin im aktiven Chat weiterarbeiten.

- Aufgabe 3 gestartet: fünf sequenzielle Evaluationsläufe, je 240 Spiele, maximal zwei Worker. Status/PID/Commands und fertige Ergebnisse: `experiments/analysis/autonomous_20261020/development_state.json`. Laufprozess nicht duplizieren; unfertige CSVs nicht werten.
- Leerlauf-Ruhezustand bis zur Arbeitsgrenze verhindert. Eigener Prozess ist in `experiments/analysis/autonomous_20261020/awake_until_deadline.json` dokumentiert. Bis zum Morgenbericht aktiv lassen; danach nur diesen anhand PID und Kommando verifizierten caffeinate-Prozess beenden; keine fremden Prozesse stoppen.
- Nächste Fortsetzung: laufenden Entwicklungsbatch prüfen, vollständige Ergebnisse auswerten, maximal einen eindeutigen Gewinner bestätigen. Nach dem Morgenbericht Automation deaktivieren.
- Neue Freigabe: geprüften besseren Stand auch als Abgabe übernehmen. Bisherige Abgabe vorab bytegleich gesichert; ergänzende Vergleichsregel gegen die alte Abgabe vor Sichtung der neuen Karten festgelegt. Keine Änderung laufender Entwicklungsmessungen.
- Git-Abgleich während Aufgabe 3: origin/main enthält zusätzlich `790997a` und `96bbf6f` von Mahmoud (weitere standardmäßig deaktivierte Sap-/Bewegungsschalter, CNN-Eval-Anpassung und neue Trainingspipeline). Laufenden Batch zunächst mit seinem ursprünglichen Code abschließen. Danach eigenen Sicherungs-/Freigabe-Commit auf origin/main rebasen, neue Tests und Referenzreproduktion prüfen, bevor die nächste Messreihe startet und gepusht wird. Keine zweite V3-Trainingspipeline starten. Die Sicherung ist lokal committet; Push steht bis zu diesem Abgleich aus.

## Weitere Nachtarbeit und Morgenbericht

- [ ] Nach dem ersten Zyklus aktuelle Remote-Ergebnisse abgleichen und nächsten begründeten Schritt vorab dokumentieren. Vorrang: belastbare Übernahmeprüfung, Verlustdiagnose auf Entwicklungskarten, Robustheit gegen weitere vorhandene Gegner; neues Training nur mit konkreter Hypothese und ausreichender Laufzeit.
- [ ] Keine zweite CNN3-/V3-Netz-Pipeline starten; weitere frische Karten erst nach Remote-Abgleich reservieren.
- [ ] Bis 05:30 Berlin regulär arbeiten; danach Bericht und abschließende Prüfungen priorisieren.
- [ ] Um 06:00 Berlin Bericht in `docs/MORGENBERICHT_20261021.md` und im Chat: Tests/Spielzahlen, belegter Stärkevergleich, negative Ergebnisse, Abgabe/Sicherung, gepushte Commits, Grenzen und offene Punkte.
- [ ] Eigene verbleibende Jobs kontrolliert beenden, Wachhalteprozess anhand PID/Kommando beenden und Automation deaktivieren.

Moayed hat diese Verlängerung und selbstständige Fortsetzung ausdrücklich beauftragt; keine erneute Freigabe für gewöhnliche Arbeitsschritte nötig.

- Aufgabe 3 abgeschlossen: fünf vollständige CSVs, insgesamt 1.200 Spiele; alle Schlüssel/Seitenpaare/Punktzählversion geprüft. V3 102/120 Siege gegen Solution_92, Reserve30 und far6 jeweils 101/120, Reserve60 96/120, far14 100/120; default stets 120/120. Kein Herausforderer ausgewählt. Vergleichsbericht: `experiments/analysis/autonomous_20261020/development_report.json`.
- Rebase der zwei Dokumentations-/Sicherungs-Commits auf `96bbf6f` erfolgreich. Vor den frischen Karten gesamte Testsuite und V3-Reproduktion auf zwei Entwicklungskarten prüfen.
- Nächster Batch: V3 und gesicherte alte Abgabe jeweils 200 frische Karten 502420–502619, beide Seiten/default/Solution_92; zusätzlich V3 direkt gegen gesicherte alte Abgabe auf 60 Entwicklungskarten. Keine Variante auf den frischen Karten nachselektieren.

- Nach Remote-Abgleich: 167 Tests bestanden (129,41 s, numerische Threads auf eins begrenzt). Vorherigen langsamen Lauf während JAX-Kompilierung nach 88 Tests abgebrochen, kein vollständiger Erfolg behauptet.
- Übernahmebatch gestartet: `experiments/analysis/autonomous_20261020/release_check_state.json`. Vier sequenzielle Aufgaben (Reproduktion, alte Abgabe frisch, V3 frisch, V3 direkt gegen alte Abgabe), maximal zwei Worker. Keine parallelen Rechenläufe oder Codeänderungen an diesem Checkout bis Batchende.

- Delegation ausdrücklich beauftragt: `target_diagnosis` prüft Phantom-Zielreservierungen und besitzt ausschließlich `/tmp/sherlock-target-diagnosis-20261020.py`; `release_evidence_review` prüft Daten/Übernahmekriterien und bereitet `/tmp/sherlock-release-analysis-20261020.py` vor; `strategy_review` prüft unabhängige nächste Hebel. Alle ohne Repo-Code-/Gitmutation und ohne zusätzliche Spiele/Trainings, solange der Übernahmebatch die zwei Evalworker belegt. Koordinator prüft jeden Befund und integriert selbst.

- Präzisierung vor Sichtung des Direktvergleichs: V3 gegen alte Abgabe auf den 60 Entwicklungskarten, Karten-Bootstrap (5.000 Wiederholungen, Seed 0). Untere 95%-Grenze des mittleren `result` strikt über 0,5: bestanden; obere Grenze unter 0,5: Veto; sonst unklar und keine automatische Übernahme. Dies ersetzt keinen Vergleich gegen unbekannte Gegner.
- Technische Schlussprüfung vor Übernahme: beide Checkpoints explizit gegen tatsächlich geladene Netze/Config prüfen; nach Remote-Integration für beide Stände die zwei bereits verwendeten Karten 502420/502421 gegen beide Gegner/Seiten reproduzieren (alle Kennzahlen außer Zeit); gesamte Testsuite und V3-Kursprobe. Reproduktionskarten sind keine neue unabhängige Stichprobe.
- Nächsten Remote-Stand erst nach Batchende normal mergen, nicht erneut rebasen: Der in `release_check_state.json` referenzierte Commit `14d239f` muss in der veröffentlichten Historie erhalten bleiben. Externe standardmäßig ausgeschaltete Schalter einzeln prüfen; abweichende Reproduktion blockiert die Übernahme.

## Nächste begründete Versuche (noch nicht in den Agenten übernommen)

1. **Aktive Zielbesitzer:** Die Engine entfernt Einheiten mit negativer Energie vor ihrer nächsten Aktion; die Zielzuweisung berücksichtigt sie derzeit noch. Ein synthetischer Fall reserviert dadurch ein Punktefeld für eine bereits ausgeschiedene Einheit. Zunächst auf 20 bekannten Entwicklungskarten/beiden Seiten gegen Solution_92 rein beobachtend zählen, ob dadurch wiederholt Ziele lebender Einheiten betroffen sind. Nur dann den standardmäßig ausgeschalteten Schalter `active_targets` testen. Keine Änderung an Belegung, Gegnermerkmalen oder `first_on_tile` in diesem Versuch.
2. **Sap-Zielgeometrie:** Bei bereits gewähltem Sap können freie Zentren zwischen sichtbaren Gegnern unter dem bestehenden Energiescore günstiger sein. In denselben Beobachtungsspielen Häufigkeit messen; der Score ist weder tatsächlicher Schaden noch bewiesener Sieggewinn. Getrennter Schalter `sap_geometry`, standardmäßig aus, erhält Verfügbarkeit/Aktionsmaske und bisherige Gleichstände; keine neue Sap-Regel hinzufügen.
3. Subagents bereiten isolierte Vorschläge und Grenzfalltests unter `/tmp` vor; Koordinator besitzt jetzt das zusammengeführte Diagnosewerkzeug. Gegenseitige Reviews erfolgen vor Übernahme. Keine zusätzlichen Spiele parallel zum laufenden Übernahmebatch.
4. Nach Diagnose und Tests maximal diese zwei Einzelvarianten auf dem bekannten Entwicklungsblock vergleichen. Kein blindes Kombinieren. Einen überzeugenden Gewinner auf einem nach Remote-Abgleich neu reservierten Block bestätigen; die bereits betrachteten Karten 502420–502619 dafür nicht wieder als frisch bezeichnen. Ohne bestätigten Vorteil bleiben die Schalter aus.

## Zusätzlicher Trainingsauftrag

Moayed hat während der Arbeit ausdrücklich auch neues Training verlangt.
Kontrollierter Pilot nach Abschluss der laufenden Prüfungen: `full_rules_v3`
mit identischer Initialisierung/Trainingsfolge, einziger Unterschied ein
standardmäßig ausgeschalteter Schalter `terminal_death_potential`.
Beide Arme halten `active_targets=False` und `sap_geometry=False`.
Je 400 Spiele, Startseed 46 (Karten 460000–460199), 70 % Solution_92 nach
25 % Default-Aufwärmphase, keine Zwischencheckpoint-Auswahl, keine historischen
Testkarten (`--no-test --val-every 0`). Danach beide finalen Einzelnetze auf
500720–500779 gegen beide Gegner/Seiten vergleichen. Ein Startpaar ist ein
Pilot, kein Nachweis über Trainingsstarts und kein automatischer Ersatz des
18er-Ensembles. Laufzeit zunächst messen; höchstens ein Training gleichzeitig.
Neue Bestätigungskarten erst nach Remote-Abgleich reservieren.

Ein separater Remote-Beobachter meldet neue Commits, Änderungen und
Seedreservierungen; nur der Koordinator integriert zwischen Messreihen.

## Eingetroffener Kandidat V4: eigener Freigabeplan

Vor weiteren lokalen Ergebnissen festgelegt: Mahmouds Commit `082057c`
enthält V3 plus `contest_sap` und `opp_infer`. Seine vorab in `3a4f32f`
dokumentierte Bestätigung auf 400 Karten 502820–503219 ergibt gegen
Solution_92 +2,375 Prozentpunkte, KI [0,125; 4,625]; Default auf 100 Karten
−0,5 Prozentpunkte. Unabhängig aus Git-Blobs nachgerechnet.

Diese bestehende Bestätigung wird verwendet, nicht erneut als neue lokale
Stichprobe ausgegeben. Die beobachtete Default-Grenze von höchstens −2 pp
bleibt bestehen; für V4 wird die vorhandene 100-Karten-Default-Kontrolle
transparent akzeptiert. Zusätzlich unverändert strenges direktes Gate:
V4 gegen V3 auf 500720–500779/beiden Seiten, untere 95%-Kartenbootstrap-Grenze
des mittleren Ergebnisses strikt über 0,5. Bei Überlappung keine automatische
Übernahme, auch bei positivem externem Solution_92-Vergleich.

Vorher Config-Differenz exakt die beiden genannten Flags sowie identische
Netzparameter prüfen; danach einige vorhandene Karten lokal reproduzieren.
Kursprobe und Sicherung von V3 vor einem eventuellen Austausch. Keine neuen
Heuristikspiele vor Auswahl der festen Ausgangsbasis. V3 ist bereits installiert
und vollständig geprüft; seine Übernahme wird durch diesen neuen Vergleich
nicht zurückgenommen.

Ergebnis: Identitätsprüfung bestanden; direkt V4 61/120 gegen V3,
95%-Kartenbootstrap [43,33; 58,33] %. Damit unklar, keine automatische
Übernahme. V3 bleibt Abgabe und feste Basis der folgenden eigenen Versuche.
V4-Kursprobe/Reproduktion vorerst zurückgestellt, weil das Stärke-Gate nicht
bestanden ist. CSV und JSON-Audit versioniert; keine Gewichtsänderung.

## Fortsetzung nach beobachtender Diagnose

40 Spiele auf 500720–500739 vollständig reproduziert; beide Mechanismen treten
wiederholt auf (`DIAGNOSIS.md` im Analyseordner). Beide Varianten standardmäßig
aus implementiert und unabhängig geprüft; Terminal-Reward-Pilot ebenfalls
vorbereitet. Mahmouds `d41d1bf` mit deaktivierter `explore_quota` integriert.
Nach Gesamttests und kurzem Funktionstest startet zuerst der feste
400+400-Spiele-Trainingspilot. Währenddessen keine Code-/HEAD-Änderung.

Anschließend die beiden **einzelnen** Inferenzvarianten `active_targets=True`
und `sap_geometry=True` gegen V3 auf 500720–500779 messen, beide Seiten/Gegner,
je 240 Spiele. Keine Kombination und keine zusätzlichen Parameterversuche.
Vorab Auswahlregel: Solution_92-Differenz positiv und untere 95%-Grenze des
gepaarten Kartenbootstraps über null, beobachteter Default-Verlust höchstens
2 Prozentpunkte. Bei zwei geeigneten Varianten größere Solution_92-Differenz;
bei Gleichstand keine automatische Auswahl. Entwicklungsintervalle sind
explorativ; die Auswahl wird anschließend unabhängig bestätigt.

Für genau einen so ausgewählten Kandidaten **510000–510199** reservieren
(vor Nutzung nochmals auf Remote-Kollision prüfen). V3 und Kandidat dort
gepaart auf beiden Seiten/Gegnern; Solution_92-Untergrenze > 0, Default-Verlust
höchstens 2 pp sowie bereits festgelegtes strenges direktes Gate gegen V3.
Ohne klare Bestätigung bleibt V3. Trainingspilot separat auswerten; ein einzelner
400-Spiele-Start reicht nicht zur generellen Bewertung einer Trainingsmethode.
