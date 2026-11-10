# Residualer V14-Kandidat: vorgeschlagener Umsetzungsplan

**Abschluss10.11.2026:** Nach späterer Nutzerfreigabe umgesetzt. Beide Starts haben die feste200er-Auswahl verfehlt; Pilot nach448 Ausführungen geschlossen, V14/ZIP unverändert. [Endergebnis](../../../experiments/analysis/residual_ensemble_20261110/ERGEBNIS.md). Der folgende Planungs-/Freigabeverlauf bleibt als ursprüngliche Festlegung erhalten; er autorisiert keinen Neustart.


> **For agentic workers:** Nach ausdrücklicher Fortsetzung `superpowers:executing-plans` verwenden. Root implementiert selbst; Subagents nur für die hier benannten unabhängigen Prüfungen. Dieser Plan ist noch nicht umgesetzt.

**Goal:** Einen kleinen additiven Korrekturlerner für V14 prüfen und nur bei belegtem Vorteil einen Kandidaten übernehmen.
**Architecture:** Die ursprüngliche 36er-Mittelung bleibt erhalten; ein getrenntes R-Netz ergänzt sechs Werte. Sammlung verwendet die vollständige Auswertungs-Regelkette, Lernen verwendet durchgängig M+R und einen an dieselben Replayzeilen gebundenen Cache.
**Tech Stack:** Bestehendes Python/PyTorch/NumPy und lokale LuxAI-Umgebung, keine neue große Abhängigkeit.
**Spec:** [Design und feste Versuchsbedingungen](../specs/2026-11-10-residual-ensemble-design.md).

## Global Constraints

- Nur Planung beauftragt; keine Tests, Modelle, Spiele oder Implementierung in dieser Runde.
- V14-/ZIP-Hashes aus der Spec erhalten; Export additiv, kein normaler 37er-Mittelwert und keine Tensorumschichtung der Originale.
- Acht technische Ausführungen; zwei Starts 61/62 mit je 40 Vorlauf + 80 Lernspielen und 12.000 Updates; Auswahl 200; Bestätigung ausschließlich bei bestandener Auswahl 600; danach acht Kursprüfungen. Höchstens 1.056 Ausführungen.
- Keine neuen Rewards, Features, Spielregeln, längeren Ersatztrainings, Zwischencheckpointwahl oder Mischungen.
- Maximal zwei Modellworker, keine Tests parallel. Ab 92 % Kontingentverbrauch Abschluss einleiten; spätestens 95 % stoppen. Keine Resets. Planung lässt Automation pausiert.
- Vor konkreter Aufnahme einmalig Kartenlisten/Hashes, Runtime, Quellenstand, Modell- und Optimiererinitialisierung fixieren. Ein Manifest, ein Status und ein Abschluss je Phase; vorhandene Lifecycle-/Statistikhilfen wiederverwenden, kein neuer allgemeiner Orchestrator.

## Review Focus

1. Null-R muss echte finale Aktionen, SAP-Offsets und Gedächtnisablauf des bisherigen Agenten erhalten; nur rohe Q-Gleichheit reicht nicht.
2. Sammel-/Lernmodus darf keine Auswertungsregel still abschalten oder Exploration hinter die Regeln verschieben.
3. Ringpufferüberlauf, Tod/Respawn und Reihenfolge beim Speichern dürfen Cachewerte nicht falschen Übergängen zuordnen.
4. Sämtliche DDQN-Terme müssen dieselbe additive Definition verwenden; ursprüngliche Netze dürfen weder Gradienten noch geänderte Tensoren erhalten.
5. Kandidatenexport und Kursloader müssen die Korrektur tatsächlich laden; kein stiller Rückfall auf V14 und kein irrtümlicher arithmetischer 37er-Export.

## Task 1: Minimalen additiven Aktionspfad bauen

**Files:** Minimal ändern: `agents/sherlock/main.py`; neu: `agents/sherlock/residual.py`, `tests/test_residual_policy.py`.
**Interfaces:** `Agent_x._network_values(features: torch.Tensor) -> torch.Tensor` enthält exakt den bisherigen Score-Rechenweg. `ResidualPolicy` besitzt unveränderte Basisnetze und R, liefert `baseline(features)` und `values(features)`, beide `[N,6]`. Keine neue Merkmalsberechnung.

- [ ] Zuerst Tests für unveränderte Basismittelung, Nullkorrektur, additive sechs Werte, eingefrorene Tensoren und fehlende/falsche Residualmetadaten schreiben und scheitern sehen.
- [ ] Nur den bestehenden Scoreblock in die Methode auslagern; Reihenfolge, dtype und bestehendes Einzelnetz-Training erhalten. Residualpfad addiert R nach M. Kein Refactoring der großen Regelkette.
- [ ] R aus Mitglied 18 mit genullten Endschichten aufbauen; Parameter-/Gradienteneigentum exakt prüfen. Die Zwischenfeatures bleiben nicht null.
- [ ] Passende Tests ausführen; bestehende Aktions-/Ladeprüfungen für den berührten Pfad ergänzend verwenden. Ein zusammenhängender Commit nach Prüfung.

## Task 2: Sammler, additive TD-Funktion und Replaycache

**Files:** Neu: `scripts/residual_ensemble_train.py`, `tests/test_residual_ensemble_train.py`. Wiederverwenden: `scripts/student_collect.py` für passives Erfassen, `agents/sherlock/reward.py`, bestehende Prozess-/Quellen-/Ausgabeschutzfunktionen. Historische Studiendateien nicht umschreiben.
**Interfaces:** `ResidualReplay.push(transition, base_s, base_ns)` schreibt alle Werte in denselben Slot; `sample(batch_size, rng)` zieht genau einen Indexsatz und liefert Übergänge samt Basiswerten/Generationen. `residual_td_loss(batch, online, target, gamma)` implementiert ausschließlich die Formel der Spec. Explizite Versionsmetadaten für Training und Export.

- [ ] Handberechnete DDQN-Tests: Baselinebeitrag in Vorhersage, Online-Argmax und Target; terminaler Übergang ohne Bootstrap; unzulässige beste Aktion; nur erlaubtes STAY; Target ohne Gradienten.
- [ ] Cachetests: kleiner Ring nach mehreren Überschreibungen, Speichern/Laden mit derselben Reihenfolge, identische Stichproben, falsche Basis/Features, nicht endliche Werte. Direkte versus gespeicherte Werte mit festgelegter numerischer Toleranz prüfen; keine erfundene bitgenaue Portabilität behaupten.
- [ ] Sammler mit Auswertungs-Regelkette und getrenntem Lernobjekt; explizite Exploration vor Regeln. Merkmale, Masken, tatsächlicher Aktionstyp, SAP-Weltaktion und Transition speichern, ohne zweite verhaltensändernde Belief-Auswertung. Erkundungs- und Sampling-RNG getrennt manifestieren.
- [ ] Vor-/Nachkontexte für Reward, Einheitenlebensdauer und Matchreset wie im vorhandenen Agenten behandeln. Keine versteckten Simulatorzustände als Netzeingaben oder Agentenentscheidungen verwenden.
- [ ] Ein unabhängiger fokussierter Review nach vollständigem Kerncode. Offene Befunde beheben und nur betroffene Prüfungen wiederholen; Root kontrolliert Ergebnis selbst. Dann Quellencommit.

## Task 3: Technik abnehmen und kleinen Pilot durchführen

**Files:** Neue Daten ausschließlich `experiments/analysis/residual_ensemble_20261110/`; feste Kartenlisten und kompakte Manifeste dort. Vorhandenen Ownerrunner nur adaptieren, kein neues Framework.

- [ ] Tatsächliche acht Ausführungen der Spec: vier Stock-/Null-R-Paare. Sammler und Kandidat müssen bei epsilon 0 identische finale Aktionen einschließlich SAP und Reset liefern. Aufnahme ohne Lernupdates.
- [ ] Rechenzeit, Speicher, Ringcache und echte Lernupdates im ersten bereits budgetierten Lernabschnitt messen. Keine zusätzlichen versteckten Pilotspiele. Prognose dokumentieren; bei untragbarer Laufzeit technische Arbeit stoppen statt unkontrolliert über Nacht starten.
- [ ] Getrennte Aufnahme der beiden 40+80-Läufe; Vorläufe auf reale Übergänge/Reward/Masken/Tensoridentität prüfen. Nur R aktualisieren, je 12.000 Updates, Endstände vollständig sichern. Keine Zwischencheckpointauswahl.
- [ ] Diagnose speichern: TD-Loss, R-Wert-/Vorteilanteil, finale Aktionsänderungen und Anteil durch Regeln aufgehobener Änderungen. Diese Werte haben keine Leistungsfreigabe-Funktion.
- [ ] Nach echten Prozessenden Quellen-/Input-/Originalgewichtshashes kontrollieren, Trainingsabschluss dokumentieren und sinnvoll committen.

## Task 4: Auswahl und nur nötigenfalls Bestätigung

**Files:** Neu: `scripts/residual_ensemble_compare.py`, `tests/test_residual_ensemble_compare.py`; wiederverwenden: `scripts/compare_report.py`, `scripts/league_gates.py` und die vorhandenen CSV-/Prozessverträge. Quellen vor jeder neuen tatsächlichen Phase einfrieren.

- [ ] Synthetische Tests für exakt vollständige Schlüssel, beide Seiten, 303 Schritte/Punktezählung v2, Remis versus Siege, fehlende/duplizierte Zeilen, Nominierungsreihenfolge und alle festen Hürden aus der Spec.
- [ ] Genau 200 Auswahlspiele, keine historischen Resultate als Ersatz für die geteilte V14-Baseline. Beide Starts müssen die feste Auswahl bestehen. Sonst Phase schließen; kein Nachschlag.
- [ ] Nur bei Erfolg höchstens einen Endstand fest nominieren und dessen unveränderte Bytes separat auf den 600 vorher reservierten Bestätigungsausführungen testen. Rohdaten und ganze Karten verwenden; keine neue Kandidatenentscheidung am Bestätigungssatz.
- [ ] Ein unabhängiger fokussierter Datenreview bei der endgültigen Auswahl-/Bestätigungsentscheidung. Vollständigkeit und Hürden durch Root nachrechnen. Ergebnis mit Unsicherheit und auch negativen Befunden dokumentieren.

## Task 5: Nur qualifizierten Kandidaten ausliefern

**Files:** Kandidatenloader aus Task 1, eigener additiver Export; bestehende `scripts/build_submission.py`/`scripts/release_candidate.py` nur gezielt erweitern, falls für das neue Schema nötig. `lux/runner.py` unverändert.

- [ ] Export lädt genau die akzeptierten Basis- und R-Tensoren mit passender Architektur. Candidate-Datei, Trainingcheckpoint und alte V14-Datei nicht verwechseln. Fehlende Korrektur darf nicht still ignoriert werden.
- [ ] Acht Kursausführungen gemäß Spec und entpacktes ZIP prüfen; Latenz, Speicher und Ausnahmen dokumentieren. Keine Abgabe bei unklarem Lade-/Reproduktionsverhalten.
- [ ] Alte Gewichte/ZIP bytegleich sichern; nur bei allen bestandenen Bestätigungs- und Technikbedingungen ersetzen. Rückweg, Hashes und Erkenntnisse für Mahmoud in `docs/ARBEITSSTAND.md` und `docs/EXPERIMENT_PROTOKOLL.md` festhalten.
- [ ] Remote vor Push prüfen, neue Mahmoud-Commits ohne Verlust integrieren, Hauptkopie aktualisieren. Eigene Jobs/Wachhalter beenden; keine automatische nächste Studie.

## Planung abgeschlossen bedeutet noch keine Verbesserung

Ein Review hat die neue Hypothese gegen die abgeschlossenen Versuche geprüft. Der Ansatz ist neu, aber sein Nutzen offen. Insbesondere bleiben regelbedingte Abweichungen vom DDQN-Target und Rewardkalibrierung mögliche Grenzen. Kein Quellcode wurde in dieser Planungsrunde verändert; keine dieser Checkboxen gilt bereits als umgesetzt.


**Freigabe 10.11.2026:** Moayed hat diesen Plan ausdrücklich zur selbstständigen Umsetzung freigegeben. Der frühere Planungsstatus oben ist historisch. V14 nur nach belegtem Vorteil ersetzen; mindestens 5 % Kontingent erhalten.
