# Matchausgang statt weiterer Q-Korrektur – nächster Umsetzungsplan

**Abschluss 10.11.:** Aufgaben 1–3 einschließlich der datiert festgelegten technischen Reparatur sind umgesetzt und geprüft. Neuer Präfixvergleich: 48 Paare, 43 wirksam auf acht Karten, +1/−1/46 Null. Gates A/B bestanden, Gate C verfehlt. Damit ist die feste Stoppen-Entscheidung erreicht; Aufgabe 4 wird nicht ausgeführt, kein neuer Kopf oder V14-Ersatz. 48 ganze Partien +40 kurze Läufe/20.200 Schritte, alter ungültiger Versuch separat. [Ergebnis und tatsächliche Abnahme](../../../experiments/analysis/match_outcome_probe_20261110/ERGEBNIS.md). Die folgenden ursprünglichen Checklisten und Phasenangaben bleiben als Planhistorie erhalten; sie sind kein offener Startauftrag.

**Umsetzungsfreigabe 10.11.:** Nutzer hat den Plan einschließlich bedingter Fortsetzung freigegeben. Die ursprünglichen Hinweise „nur Planung“ dokumentieren die damalige Phase, nicht einen noch offenen Erlaubnisbedarf. Gates und 5-%-Reserve bleiben verbindlich.

**Reparatur nach technischem Abbruch:** Der Snapshotversuch ist mit19vollständigen/1teilweisen Ausführungen geschlossen. Maßgeblich ist jetzt die datierte technische Reparaturfestlegung oben in der Spec: keine Sets kopieren, sondern echte Historie neu abspielen. Einmalig32vollständige Referenz-/Sammelläufe, maximal48Alternativpräfixe und8Wiederholungspräfixe, insgesamt höchstens21.816neue Engine-Schritte. Karten/Gates unverändert; zuerst Fehlerkarte11011007/p0 und Kontrolle11011017/p0. Alte29Snapshotpaare nicht zum Lernen verwenden.

Reparaturaufgaben: separaten `scripts/match_outcome_replay.py` und synthetische `tests/test_match_outcome_replay.py` erstellen; vor jedem Eingriff alle Präfixframes exakt reproduzieren; echten Abweichungsframe vor Fehler speichern; frischen Root-Review und gezielte Tests abschließen; neue Quellen binden; erst technische Phase, tatsächliche Abnahme, dann Rest. Der bisherige Kernreviewer übernimmt die klar getrennte Reparaturdatei, Root prüft sie unabhängig und koordiniert die Datenabnahme. Keine parallelen Modelle oder Änderungen an Sherlock/Solution. Diese begrenzte Delegation spart Wiederlesen des bereits untersuchten Snapshotfehlers.

> **For agentic workers:** Bei späterer Umsetzungsfreigabe `superpowers:executing-plans` verwenden. Root implementiert den zusammenhängenden kleinen Pilot; unabhängige Subagents nur für die gezielte Snapshot-/Labelprüfung. Die folgenden Aufgaben sind noch nicht ausgeführt.

**Goal:** Herausfinden, ob öffentlich auswählbare Alternativen zur V14-Policy tatsächlich bessere Matchausgänge liefern und damit eine neue Lerngrundlage bieten.

**Architecture:** V14 bleibt eingefroren. Ein experimenteller Adapter liest einmalig die vorhandenen Merkmale und Q-Werte, kann genau einen legalen Rohvorschlag ersetzen und lässt alle Regeln unverändert folgen. Gepaarte Simulatorfortsetzungen liefern echte Matchendlabels. Noch kein neuer Lerner oder Produktivagent.

**Tech Stack:** vorhandenes Python, NumPy, PyTorch und LuxAI; Snapshot-/Prozess-/Statistikhilfen wiederverwenden, keine neue Plattform.

**Spec:** [Vorgeschlagenes Design mit festen Grenzen](../specs/2026-11-10-match-outcome-selector-design.md).

## Global Constraints

- Nur Planung abgeschlossen; zur Umsetzung muss eine weitere Nutzeranweisung vorliegen. Geschlossene Studien nicht neu starten.
- Ein Modellworker, Tests vorher; V14/ZIP unverändert. Bestehende Studienkopie weiterverwenden, fremde Dateien schützen.
- Acht bekannte Karten aus der Spec × beide Seiten × Referenz/Sammler = höchstens 32 vollständige Ausführungen, einschließlich der ersten vier Technikspiele.
- Höchstens 48 Hauptpaare / 5.856 zusätzliche Hauptschritte plus 976 technische Fortsetzungsschritte. Keine Gradienten, Ersatzkarten oder automatischen Neustarts.
- Mindestens 5 % Reserve, ab 92 % Verbrauch Abschluss einleiten, spätestens 95 % stoppen. Automation bleibt bis neuer ausdrücklicher Arbeitsfreigabe pausiert.

## Review Focus

1. Ein Minimum über zukünftige Schritte wäre Datenleck: Auswahl ausschließlich beim aktuellen ersten geeigneten Schritt 40–70.
2. Rohvorschlag und finale SAP-/Teamaktion unterscheiden: neutraler Adapter muss den vollständigen alten Verlauf erhalten.
3. Gedächtnis, Solution-Globals und RNG müssen bei Branchwechsel wirklich isoliert sein; passive Originalpartie darf sich nicht ändern.
4. Matchendpunkte werden zurückgesetzt; tatsächlichen Matchgewinn, Energiegleichstand und Endzeitpunkt aus der gebundenen Engine erfassen.
5. Gegenfakten sind keine spielbaren Gewinne; unwirksame Alternativen, negative Labels und Karten ohne Fälle im Bericht erhalten.

## Aufgabe 1 – isolierten Aktionsadapter und Endlabel bauen

**Neue Dateien:** `scripts/match_outcome_rollout.py`, `tests/test_match_outcome_rollout.py`.
**Lesen/wiederverwenden:** `agents/sherlock/main.py` (`_decide`, `_network_values`, `_policy_greedy`), `scripts/holder_rollout.py`, `scripts/scoring.py`. Alte HOLD-Semantik und ihren HORIZON nicht verändern. Wenn erforderlich generischen Snapshot-Helfer minimal erweitern und dessen vorhandene Tests erneut prüfen; keine neue allgemeine Laufplattform.

**Schnittstellen:** `choose_opportunity(ctx, ids, masks, q, used_match) -> Opportunity | None`; `rollout_to_match_end(snapshot, opportunity, alternative: bool) -> BranchResult`; `paired_match_outcome(...) -> PairResult`. Datenklassen führen Seed/Seite nur als externe Metadaten. `BranchResult` enthält finale Teamaktionen, Punkte, Energie, echten Matchgewinn und Abschlussgrund; nur öffentliche aktuelle Daten gelangen in einen späteren Featureexport.

- [ ] Kleine synthetische Tests zuerst: illegaler Rang 2, nicht endliche Q-Werte, nur eine legale Aktion, Gleichstände, Fenstergrenzen, fehlende Einheit, genau eine Gelegenheit. Erstes zulässiges Zeitfenster prüfen, keine Zukunftssuche.
- [ ] Experimentelle Unterklasse statt allgemeiner Agentenänderung: `_decide` genau einmal über `super` ausführen, Q-Werte ohne weitere Modellrechnung sichern, `_policy_greedy` nur für den exakt benannten Schritt/UID verändern. Nicht hinter Regeln an den fertigen Aktionsarrays manipulieren. Kein Stackframe-Trick, keine zweite Belief-Aktualisierung.
- [ ] Tests für Ablehnung/Nulladapter, spätere Regelübersteuerung, SAP-Offsets und identische komplette Teamaktion. Modellbytes und deren Reihenfolge erhalten.
- [ ] Endlabeltests mit Punktsieg, Punktgleichstand/Energieentscheidung, exaktem Energiegleichstand/Zufall und Matchreset. Schritt 100 einschließen, danach stoppen; Endgewinn aus `team_wins`-Änderung lesen, nicht aus akkumulierten Punktmargen erraten. Regelbegründung extern gegen Enginezustand prüfen.
- [ ] Snapshottests: Branchreihenfolge und Wiederholung, sämtliche beteiligten RNGs, Solution-Globals und Objektaliasse; nach Rückkehr Livezustand identisch. Echte Referenzpartien gehören später zu den 32 Ausführungen, nicht versteckt in Tests.
- [ ] Ein fokussierter unabhängiger Review dieses Kerns; Befunde beheben, betroffene Tests ausführen, zusammenhängenden Codecommit erstellen.

## Aufgabe 2 – begrenzten Sammler und Bericht vorbereiten

**Neue Dateien:** `scripts/match_outcome_probe.py`, `tests/test_match_outcome_probe.py`; Daten unter `experiments/analysis/match_outcome_probe_20261110/` erst bei tatsächlicher Umsetzung.
**Schnittstellen:** `run_probe(manifest) -> state.json`; `summarize_pairs(manifest, records) -> summary.json`. Vorhandene Quellen-/Eigentümer-/Abschlusskontrollen verwenden.

- [ ] Tests für 16 eindeutige Karten-/Seitenschlüssel, Referenz/Sammlerrolle, Schrittzähler samt technischen Wiederholungen, fehlende/duplizierte Zeilen, Nullfälle, positiven und negativen Matchflip, einzelne Karte mit vielen Fällen.
- [ ] Manifest mit exakten Karten, Rollen, Referenzquelle, Modellhashes, Policyflags, H12 und Endlabel schreiben. Erste vier Technikrollen und restliche 28 unterscheiden; kein automatischer Übergang vor echter Abnahme.
- [ ] Pro Snapshot Baseline/Alternative bis Matchende und H12-Zwischenstand archivieren. Baselinebranch mit dem späteren tatsächlichen Baselineverlauf vergleichen. Maximal die erste vorhandene Gelegenheit jeder Karte zusätzlich umgekehrt wiederholen; Obergrenzen strikt zählen.
- [ ] Bericht muss Gate A/B/C separat nennen, alle positiven/negativen/null Labels und Karten ohne effektive Aktion enthalten. Kein Bootstrap aus einzelnen korrelierten Einheiten als unabhängige Stichprobe; für explorative Intervalle ganze Karten ziehen.
- [ ] Zugehörige Tests durchführen und Commit. Aktionsadapter ausgeschaltet lässt V14 unverändert; noch keine Stärkeaussage.

## Aufgabe 3 – Pilot ausführen und Entscheidung treffen

- [ ] Aktuellen Nutzerumfang, Quota, Prozesse, Stromstatus, Remote/Worktrees prüfen. Keine Duplikate; bestehende Nutzerentscheidung zum Akkubetrieb beachten. Quellen und Schutzdateien fixieren.
- [ ] Nur die ersten vier bereits eingerechneten Ausführungen starten. Passivität, echte Matchabschlusslabels, Laufzeit/Speicher und Branchisolation tatsächlich prüfen. Bei Fehler stoppen, nicht still weitere Testpartien ergänzen.
- [ ] Erst danach restliche 28 Ausführungen aus derselben Festlegung. Ein Worker; keine parallelen Tests oder Quellenänderungen.
- [ ] Alle Schlüssel, 32 Vollausführungen beziehungsweise ehrliche Abbruchzahl, zusätzliche Schritte, Neutralfälle, Gates und Eingabehashes gegen Rohdaten prüfen. Endprozesse kontrollieren und Freeze erst nach Abschluss freigeben.
- [ ] Diagnose sinnvoll committen/pushen und Mahmouds Arbeitsstand aktualisieren. Gate verfehlt: diesen Pilot schließen, keine automatische Lernrunde. Gate bestanden: nur „nützliche Alternativen im Simulator vorhanden“, noch kein stärkerer Sherlock.

## Aufgabe 4 – nur bedingt: öffentliche Entscheidung lernen und beweisen

Diese Aufgabe beschreibt die Anschlussrichtung, **keinen bereits freigegebenen Modelllauf**. Vor Umsetzung ihre tatsächlichen Daten- und Modellgrenzen in einem ergänzenden Protokoll fixieren. Datenmenge aus der gemessenen Ereignisrate ableiten, keine beliebig verlängerte Suche nach positiven Fällen.

- [ ] Getrennte Lern-/Validierungskarten und Gegner Solution/V14 festlegen; beim V14-Gegner Snapshot seiner Modellreferenzen unabhängig prüfen. Alle Ergebnisse sammeln, nicht nur gewonnene Alternativen.
- [ ] Kleinen regulierten Kopf für erwartetes `delta_win` trainieren; ausschließlich öffentliche aktuelle Features und Aktion, keine zukünftigen Endwerte. Eine feste positive Entscheidungsschwelle vor Validierung; unveränderter V14 als Rückfall. Genau ein Versuch pro Match, auch bei Ablehnung verbraucht.
- [ ] Unabhängige Kartenvalidierung muss Nutzen und Schaden gewählter Eingriffe sowie Nichtstun mitzählen; erst bei brauchbarem Signal vollständige Policyspiele. Keine Summe ausgesuchter Gegenfakten als Siegquote verkaufen.
- [ ] Einen festen Endkandidaten zunächst gegen V14 und Solution auf jeweils 40 Spielen prüfen, V14-Solutionvergleich auf denselben Karten mit beiden Seiten. Kompakte Kontrollen und eine einzige begrenzte Bestätigung vor Resultaten festlegen; keine wiederholte Kandidaten-/Schwellenwahl an Testkarten.
- [ ] Nur belegten vollständigen Vorteil mit ausreichender Kartenunsicherheit, ohne beobachteten Gegner-/Kursrückschritt übernehmen; zuvor V14 sichern, Paket-/Loaderprüfung, Hashes und Wiederherstellung dokumentieren. Sonst V14 behalten. Allgemeine 100 % gegen Solution bleiben keine beweisbare Zusage.

## Definition des nächsten erledigten Schritts

Ein korrekt abgeschlossener 32-Ausführungen-Pilot mit einer klaren Fortsetzen-/Stoppen-Entscheidung. Ein verfehlter Einfluss- oder Lernzieltest wird als begrenzter negativer Befund dokumentiert. Ein Lernversuch ist erst dann begründet, wenn der Pilot ausreichend häufige nützliche Alternativen zeigt; ihre Vorhersagbarkeit aus öffentlichen Merkmalen bleibt vollständig Gegenstand von Phase B.
