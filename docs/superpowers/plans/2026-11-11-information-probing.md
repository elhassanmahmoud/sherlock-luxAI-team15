# Gezielte Feldtests Implementation Plan

> **For agentic workers:** Bei einem Umsetzungsauftrag `superpowers:executing-plans` nutzen. Root implementiert inline; gezielte unabhängige Reviews für öffentliche Beweise/Aktionsfolge und tatsächliche Resultate. Dieser Auftrag betrifft zunächst nur Planung, keine Ausführung.

**Goal:** Nachweisen, ob gezielt koordinierte Besetzung unbekannter Felder frühere nutzbare Information und anschließend einen stärkeren Agenten als V14 ergibt.

**Architecture:** Öffentliche historische Gleichungen rekonstruieren; nur bei ausreichenden Gelegenheiten eine experimentelle Unterklasse über den vorhandenen `_policy_greedy`-Hook bauen. Netze, Gewichte und nachgelagerte Regeln bleiben unverändert. Jede Phase hat eine feste Fortsetzungs- oder Stoppen-Entscheidung.

**Tech Stack:** Bestehendes Python/NumPy/PyTorch/LuxAI, keine neue Lernbibliothek.

**Spec:** [Belege, Auswahlalgorithmus, Karten, Grenzen und Übernahmehürden](../specs/2026-11-11-information-probing-design.md). Maßgeblich zusammen mit dem neuesten [Arbeitsstand](../../ARBEITSSTAND.md).

## Global Constraints

- Nur Planung freigegeben; alle folgenden Kästchen bleiben offen. Kein Agenten-/Gewichtstausch ohne bestandene Bestätigung und Kursprüfung.
- A: zwölf vorhandene Traces, null neue Spiele. B: höchstens 38 ganze Partien/11.514 Schritte. C: 120 und D: 680 Partien, jeweils nur nach tatsächlichem Bestehen der vorherigen Phase. Keine Gradienten.
- Genau ein Kandidat: einmal pro Spiel, erstes Match, Schritte 50–80, höchstens zwei Nicht-Halter, höchstens 113 Belegungsentwürfe und 400 Gleichungen. Keine Ausweitung bei zu wenigen Gelegenheiten.
- Originale Referenz und Schutzdateien binden; keine Engine-/Gegner-Deepcopies, stillen Ersatzspiele oder Wiederstarts. Quellenfreeze während jeder realen Phase, keine parallelen Tests.
- Mindestens 5 % Kontingent übrig; ab 92 % Verbrauch keine neue Phase, spätestens 95 % stoppen, keine Resets. V14/ZIP unverändert bis zur belegten Übernahme.

## Review Focus

1. Zeitversatz zwischen Aktion, Belegung und Punktzuwachs; negative Energie, Stapel und Matchreset korrekt behandeln.
2. Keine versteckte Wahrheit, zukünftigen Frames oder Gleichsetzung von Nicht-Kandidat und bekanntem Nullfeld für die Entscheidung.
3. Bereits aktive Teilmengen-Inferenz nicht als neue Erfindung ausgeben; konservative Vorbedingungen dürfen Gelegenheiten verwerfen.
4. Netzwahl, Probevorschlag, Regelübersteuerung und reale Information getrennt belegen; keine nachträglich gefälschte Aktionsbuchhaltung.
5. Bekannte Karten nicht als unabhängige Bestätigung; Kartencluster statt einzelne Seiten, degenerierte Intervalle nicht als Sicherheit verkaufen.

## Aufgabe 1: Öffentliche Gelegenheit offline nachweisen

**Neu:** `scripts/information_probe.py`, `tests/test_information_probe.py`; Ausgaben später unter `experiments/analysis/information_probe_20261111/offline/`.

**Schnittstellen:** `PublicEquation(tiles, residual, observed_step)`; `advance_public_history(previous, current, history) -> history`; `choose_probe(public, ids, masks, greedy, history) -> ProbeProposal | None`; `audit_archived_traces(manifest, output) -> report`. Proposal enthält ausgewählte UIDs/Aktionen, x, alte/neue Mengen, öffentliche Voraussetzungen, Originalvorschlag und festen Entscheidungsgrund. Keine Modelle in der Offlinefunktion laden.

- [ ] Eingabemanifest/zwölf tatsächliche Traces binden, Schema und historische Config prüfen. Öffentlich erlaubte Felder explizit auswählen; `posthoc` nicht an die Policy übergeben. Fehlende Informationen als Ausschluss protokollieren.
- [ ] Zuerst synthetische Tests schreiben/fehlschlagen lassen: A+B=1 und B isolierbar; bekannter Punktbeitrag; Stapel; Energie −1; Punktzuwachs am aktuellen Frame; Symmetrie ohne falsche Zusammenfassung; Matchreset/Widerspruch; keine eigenen Gleichungen/Nullannahmen vor Schritt 50; fehlende Sicht-/Kostenfelder; Originalvorschlag bereits informativ; zwei gleichrangige Vorschläge deterministisch; keine echten Spiele in Tests.
- [ ] Minimalen öffentlichen Gleichungsspeicher und exakt den Auswahlalgorithmus der Spec implementieren. Höchstens 113 Entwürfe, 400 Gleichungen. Keine freie Reward- oder Q-Schwelle ergänzen.
- [ ] Präfixtest: Änderungen an späteren Frames und versteckten `posthoc`-Werten verändern frühere Vorschläge nicht. Gezielte Tests mit Projekt-Python ausführen; unabhängigen Beweisreview einmalig einholen.
- [ ] Die zwölf alten Traces einmal auswerten: erste Gelegenheit/Spiel, Gates und Ausschlussgründe, konkrete öffentliche Gleichung pro Gelegenheit. Bei Gate-A-Verfehlung dokumentieren und schließen; keine Engineaufnahme. Offlinebelege/Werkzeug sinnvoll committen.

## Aufgabe 2: Prototyp und tatsächliche Informationswirkung

**Neu:** `scripts/information_probe_runner.py`, `tests/test_information_probe_runner.py`. In `scripts/information_probe.py` die experimentelle `InformationProbeAgent`-Unterklasse ergänzen; `agents/sherlock/main.py` nur lesen, vorhandenen Hook nutzen.

**Schnittstellen:** `InformationProbeAgent(..., probe_enabled: bool)`; `run_known_phase(phase, output, source_manifest, prior_acceptance=None)` für `technical`/`remaining`; `summarize_known(rows) -> gate_report`. Getrennte Archivfelder für Vorschlag, finale Aktion, beobachtete Belegung und erstmalige tatsächliche Bestimmung von x in AN/AUS.

- [ ] Unveränderte vollständige V14-Referenz aus aktuellem akzeptiertem Stand separat archivieren, Hashes/Loader/36 Modelle prüfen. Kein Originalvergleich nur gegen denselben neuen Adapter.
- [ ] Rote Tests für einmaliges Eingriffsbudget, Schritte 50/80 und außerhalb, Holder-Schutz, spätere Regelübersteuerung, keine doppelte Belief-/Netzrechnung, beide Seiten, komplette Resetfolge. Tatsächliche aktuelle Sicht gegenüber alter/symmetrisch ergänzter Sicht abgrenzen. AN verbraucht auch einen aufgehobenen Versuch; AUS bleibt neutral.
- [ ] Unterklasse implementieren: nur legale vorläufige Aktionen ändern, bestehende Regelkette/Buchhaltung unangetastet. Aktuelle `sensor_mask` aus der Beobachtung korrekt kanonisieren und ausschließlich an die Probe geben; Live-`ctx` enthält sie bisher nicht, `belief._vis_now` ist wegen Symmetrieergänzung ungeeignet. Basispfad genau einmal aufrufen. Neue tatsächliche Fakten ausschließlich über den unveränderten Belief aus echten Beobachtungen.
- [ ] Runner synthetisch prüfen: exakt 38/11.514 Obergrenze, frische Originalstarts, Zählung auch fehlgeschlagener Läufe, exklusive Ausgabeordner, Quellenbindung, keine Folgephase ohne Abnahme. Rechtszensierte Informationszeit und Match-/Spielwertung getrennt testen. Die zwei zusätzlichen AN-Wiederholungen dürfen keine der zwölf gepaarten Erfolgs-/Gelegenheitszählungen verändern.
- [ ] Quota/Jobs/Git/Schutzdateien tatsächlich prüfen; nur die acht Technik-Ausführungen auf 831006/p1 und 831000/p0 starten. Original/AUS-Gleichheit, AN-Präfix und volle AN-Wiederholung tatsächlich abnehmen. Kein Hintergrund-Autostart des Rests.
- [ ] Erst danach 30 übrige Ausführungen, keine Quellenänderung währenddessen. Gate B aus sämtlichen Rohdaten nachrechnen. Bei Verfehlung schließen; positive Einzelfälle nicht als Policy-Erfolg verkaufen. Bericht und Arbeitsstand aktualisieren, nach gelöstem Freeze committen/pushen.

## Aufgabe 3: Frische Stärkeprüfung, nur bei bestandenem B

**Neu:** `scripts/information_probe_compare.py`, `tests/test_information_probe_compare.py`; Daten unter `experiments/analysis/information_probe_20261111/selection/` bzw. `confirmation/`. Vorhandene geprüfte Wertungs-/Quellenkontrollen wiederverwenden, abgeschlossene Studien nicht neu starten.

**Schnittstelle:** `run_comparison(phase, output, frozen_manifest, prior_acceptance) -> report` für `selection`/`confirmation`; `evaluate_gates(paired_rows, direct_rows, default_rows=None) -> decision`.

- [ ] Reservierte Seeds der Spec vor Spielen gegen verfügbare Trainings-/Benchmarkarchive prüfen; Suchumfang und Lücken offen dokumentieren. Bei Überschneidung stoppen, nicht automatisch neue Seeds suchen.
- [ ] Vergleichsvertrag und genau eine Config vor Ergebnisansicht binden. Tests für Karten/Seiten/Gegnerzählung, identische Modelle, 40/40-Gleichstand, gepaarte Clusterintervalle, Unentschieden, Abbruch/Fehler, degenerierte Intervalle und klare Nichtübernahme schreiben und ausführen.
- [ ] Feste 120 Auswahlpartien durchführen. Nur bei beiden Auswahlhürden separate Bestätigungsaufnahme erwägen; Quota und Source-Freeze am Übergang erneut prüfen.
- [ ] Bei ausreichender Quota und C-Erfolg genau 680 unabhängige Partien. Alle D-Hürden aus der Spec unverändert anwenden. Einmaliger unabhängiger Datenreview vor jeder Stärke-/Übernahmeaussage. Kein Nachfüllen bei knappem Ergebnis.
- [ ] Nur bei D-Erfolg zusätzlich konkrete Kurs-/Exportprüfung festlegen und durchführen, frühere Abgabe sichern, neue ZIP auf tatsächliche Quelldateien/Interface/Hashes prüfen. Keine Garantie allgemeiner 100 % behaupten. Bei jedem anderen Ausgang V14 behalten.
- [ ] Tatsächliche Ausführungen/Updates/Fehler/Unsicherheit sowie Grenzen für Mahmoud festhalten, eigene Jobs beenden, kontrolliert committen/pushen und Primary ohne Verlust fremder Dateien synchronisieren. Nur erreichte Schritte abhaken.

## Abschluss dieser Planungsrunde

Diese Dateien enthalten einen Vorschlag, keinen erreichten Agenten. Die nächste ausführbare Arbeit ist ausschließlich Aufgabe 1. Ergebnisabhängige spätere Schritte dürfen nicht vorgezogen oder als bereits freigegebene Dauerexperimente gestartet werden.
