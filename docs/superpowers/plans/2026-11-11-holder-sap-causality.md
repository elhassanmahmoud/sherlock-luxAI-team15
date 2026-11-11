# Halter-SAP: Implementation Plan für die begrenzte Kausalprobe

> **For agentic workers:** Bei Umsetzungsauftrag `superpowers:executing-plans` verwenden. Root implementiert inline; unabhängiger Review nur für Eingriff und Daten. Fortschritt siehe jüngsten Arbeitsstand; Ausführung nach Nutzerfreigabe.

**Goal:** Prüfen, ob öffentlich ausgewählte finale Schussverzichte produktiver Halter ganze verlorene V14-Spiele verbessern, bevor ein neuer Kandidat gelernt wird.

**Architecture:** Ein standardmäßig neutraler Hook vor der SAP-Schadensbuchhaltung, instrumentiert durch eine experimentelle Unterklasse. Ausschließlich Originalpräfix-Replay, keine kopierten Gegner. Pro Match höchstens ein einmaliger Eingriff; ganze Spiele als Endziel.

**Tech Stack:** Bestehendes Python, NumPy/PyTorch/LuxAI und vorhandene Prozess-/Quellenkontrollen. Keine neue Lernbibliothek.

**Spec:** [Design, Belege und feste Grenzen](../specs/2026-11-11-holder-sap-causality-design.md). Plan nachträglich ausdrücklich zur Umsetzung freigegeben; nur vorab begrenzte Phasen ausführen.

## Global Constraints

- V14/ZIP unverändert. Bekannte acht Karten und beide Seiten ausschließlich wie in der Spec; keine Ersatzkarten.
- Maximal 32 Referenz-/Sammler-, 48 Alternativ- und 8 Wiederholungspartien, zusammen 88 ganze Ausführungen beziehungsweise 26.664 Schritte. Null Gradienten.
- Ein Modellworker, keine Tests parallel, getrennte Technikabnahme vor Rest. Keine Deepcopies der Umgebung/des Gegners, kein automatischer Neustart.
- Mindestens 5 % Restkontingent; ab 92 % Verbrauch keine neue Phase, spätestens bei 95 % kontrolliert stoppen. Kein Reset durch Codex.
- Keine Änderung alter Studien oder ihrer Labels. Folge-Lernen und Leistungsprüfung brauchen ihre konkret begrenzte separate Festlegung.

## Review Focus

1. STAY-Netzvorschlag, spätere Regeländerung und endgültiger SAP sind unterschiedliche Stufen; kein beliebiger MOVE-/SAP-Veto.
2. Nachträgliches Ändern nur der fertigen Aktionsmatrix hinterlässt fiktive Schadens-/Nebelschussplanung; früherer Unit-Zustand darf beim Zurücknehmen nicht verloren gehen.
3. Gespiegelte Seite und gleiche Position mehrerer Einheiten dürfen Eligibility oder SAP-Offsets nicht verfälschen.
4. Fullgame- und Matchlabels unterscheiden; Energiegleichstand und spätere Gedächtnisfolgen berücksichtigen, keine Summen ausgewählter Gegenfakten als Siegquote.
5. Veraltete Referenzquelle, null Gelegenheiten, frühzeitiger Prozessabbruch und bereits vorhandener Ausgabeordner dürfen keine stillen Ersatzläufe auslösen.

## Task 1: neutralen Hook und enges Ereignis prüfen

**Dateien:** minimal ändern `agents/sherlock/main.py`; erstellen `scripts/holder_sap_probe.py` und `tests/test_holder_sap_probe.py`. Lesen `scripts/holder_rollout.py` nur für die Abgrenzung, nicht dessen Snapshotklasse verwenden.

**Schnittstellen:** `Agent_x._final_sap_policy(ctx, uid, mask, network_action, action, sap, fog_origin) -> tuple[int, object]` als neutraler Standard. `eligible_holder_sap(ctx, uid, mask, network_action, action, sap, fog_origin) -> bool` für öffentlichen Ereignisfilter. Experimentelle Unterklasse `HolderSapProbeAgent` mit explizitem Modus `observe` oder genau einem Schlüssel `(step, uid)`; keine allgemeine wiederholte Schutzpolicy.

- [x] Vor dem Hook eine unveränderliche vollständige Original-Agentenquelle aus `021d13e1a7808d67bf8a11c78fbc4beaae3c9956` separat für die Referenz sichern und hashen. Referenzloader muss diesen Modulpfad und Originalgewichte nachweislich verwenden; nicht den neu gepatchten Standardagenten als unabhängige Referenz ausgeben.
- [x] Rote synthetische Tests: Roh-STAY und finaler sichtbarer SAP nötig; MOVE, Netz-SAP, Nebelschuss, negative Energie, unbestätigtes Feld, mehrere produktive Halter, illegaler STAY und falscher Schritt/UID werden abgewiesen. Mehrere berechtigte Units wählen kleinste UID, erste Gelegenheit verbraucht den Matchslot.
- [x] Standardhook implementieren; Aufruf nach letzter SAP-Zielwahl, vor `_plan_damage`. Maskiertes Ensemble-Argmax bereits vor `_policy_greedy` sichern und explizit weiterreichen. Keine zweite Netzrechnung oder Belief-Aktualisierung; bestehende Buchhaltung im neutralen Standardpfad nicht umordnen.
- [x] Tests mit zwei Units: Veto entfernt nur tatsächlichen Beitrag des aktuellen Schusses; frühere Reservierungen bleiben, folgende Units planen ohne Phantomschaden. `_prev_actions` und alle SAP-/Vorhersageeinträge stimmen mit finalen Aktionen. Nebelschuss- und Smart-SAP-Voraussetzungen aus der Spec prüfen; beide Spiegelrichtungen und deaktivierte/Trainingspfade bleiben gleich.
- [x] Gezielte Tests mit bestehendem Projekt-Python ausführen; unabhängiger enger Review der Stufenfolge. Erst nach tatsächlichem Bestehen Codecommit. Keine echten Spiele in synthetischen Tests verstecken.

## Task 2: Original-Replay und vollständige Endlabels

**Dateien:** erstellen `scripts/holder_sap_replay.py`, `tests/test_holder_sap_replay.py`; Daten später unter `experiments/analysis/holder_sap_causality_20261111/`. Wiederverwenden: geprüfte Prinzipien von `scripts/match_outcome_replay.py`, Quellen-/Schutzdateibindung und `scripts/scoring.py`; den abgeschlossenen alten Runner nicht neu starten oder seine Artefakte überschreiben.

**Schnittstellen:** `run_phase(phase, output, weights, quota_receipt, previous_acceptance=None) -> Path` für `technical`/`remaining`; `summarize(pairs, executions) -> dict` mit Spiel- und Matchkontrasten sowie drei getrennten Gates. Paar enthält öffentlichen Eventdatensatz, originale vollständige Baseline, tatsächlichen Alternativverlauf, aktuelle Matchnummer und volle Drei-Match-Ergebnisse.

- [x] Rote Tests für exakt 16 Schlüssel, first-event-per-match, leere Ereignismengen, 88/26.664 Obergrenzen, Zählen vor Start/Engineaufruf, Abbruch, exklusive Outputs und verweigerte Folgephase ohne tatsächliche Abnahme.
- [x] Jeder Alternativlauf beginnt mit frischen ursprünglichen Agenten und RNGs beim Spielanfang. Alle Frames vor dem Eingriff exakt vergleichen; tatsächlichen Abweichungsframe vor Fehler archivieren. Danach bis zum ganzen Spielende, nicht nur Matchende. Pro Karte erste vorhandene Alternative vollständig wiederholen.
- [x] Match-/Spielpunkte, echte `team_wins`, terminale Energie-/Zufallsentscheidung, native Teamaktionen, Belief-/Ereignisbelege und Nullfälle archivieren. Instrumentierte Energiephasen nur nach verifiziertem passivem Enginevergleich als ursächlich ausgeben; sonst Grenze offen lassen.
- [x] Vollständigen zweiphasigen Controller synthetisch testen, inklusive positiver/negativer Spiel-Flips bei gleichem aktuellen Matchresultat und umgekehrtem Fall. Originaldateien/keine Modellmutation prüfen; gezielter Review und zusammenhängender Commit vor realem Start.

## Task 3: reale kleine Probe und feste Entscheidung

- [ ] Nutzerumfang, Quota, Git/Remote, laufende Jobs und geschlossene Studien prüfen; Gewichte und Quellen binden. Herkunfts-CSV und vorhandenen Trace erneut hashen. Aktuell unterschiedliche Config/Ergebnisse vor Beginn aufklären, nicht still ignorieren.
- [ ] Nur Technikschlüssel `9946007/player_0` und `2000000/player_0`, alle bereits im Gesamtbudget. Neutralität, Originalpräfix, ganze Wiederholung, mögliche Regelübersteuerung und Buchhaltung anhand realer Daten abnehmen. Kein technisches Bestehen aus Testnamen ableiten.
- [ ] Erst danach restliche 14 Schlüssel. Keine Tests/Quellenänderung parallel, keine Zusatzgelegenheiten. Jeder vollständige/fehlgeschlagene Lauf und jeder echte Schritt wird gezählt.
- [ ] Unabhängig anhand tatsächlicher Rohdaten nachrechnen: mindestens 12 wirksame Paare auf vier Karten; mindestens zwei negative ganze Spiele auf zwei Karten zu Siegen; positive Spiel-Flips überwiegen negative; Matchsiegkontrast insgesamt nicht negativ. Technische Integrität zwingend. Alle Ergebnisse einschließlich neutraler Karten berichten.
- [ ] Bei Verfehlung diesen Pilot schließen. Bei Bestehen ausschließlich Anlass für getrennt festgelegtes öffentliches Entscheidungslernen feststellen; noch keine Stärke- oder Übernahmebehauptung. Keine Implementierung einer Wiederholungspolicy aus dem besten Einzelbeispiel.
- [ ] Eigene Jobs beenden, tatsächliche Quellen-/Gewichtshashes und Reserven prüfen, Freeze erst danach lösen. Berichte/Arbeitsstand/Experimentprotokoll aktualisieren, sinnvoll committen/pushen und Hauptkopie sicher abgleichen.

## Nachgelagerte Entscheidung, hier keine ausführbare Aufgabe

Nur bei brauchbarem Pilot folgt ein eigener Plan mit klarer Datenmenge, öffentlichen Features, einer kleinen festen Modellklasse, getrennter Validierung und festem Eingriffslimit. Ein späterer Kandidat erhält zunächst den in der Spec skizzierten 120-Spiel-Screen. Ohne eine vollständig festgelegte unabhängige Bestätigung keine Übernahme. Diese Aufgaben sind absichtlich nicht als automatisch startbare neue Trainingswelle formuliert.

## Erfolg dieses Plans

Ein technisch korrekter kausaler Befund über eine konkret protokollierte Entscheidungsklasse. Der Plan garantiert weder einen besseren V14 noch allgemeine 100 % gegen Solution. Er begrenzt den Aufwand, bevor erneut trainiert wird, und lässt einen negativen Befund ausdrücklich zu.
