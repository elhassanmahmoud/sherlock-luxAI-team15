# Legales Rangmittel: Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development. Getrennte Schreibbereiche, Umsetzung und Prüfung vor Modellläufen.

**Goal:** Einen einzigen neuen Ensembleansatz mit denselben 36 V14-Netzen prüfen: gleichgewichtiges Mittel der legalen Aktionsränge.

**Architecture:** Separate Eval-Unterklasse, keine Corekopie oder globalen Laufzeitpatches. Nur ON ersetzt das Q-Modul der konkreten Agentinstanz durch ein Modul mit Referenzen auf ihre bereits geladenen 36 Netze und entfernt diese aus dem äußeren extra_q-Pfad. Der originale Entscheidungsablauf bleibt einmalig bestehen. OFF bleibt der unveränderte V14-Lade-/Aktionspfad.

**Tech Stack:** vorhandenes Python, NumPy und Torch; keine neuen Abhängigkeiten.

**Spec:** Die folgenden festen Methodenentscheidungen und die gezielte Voruntersuchung in preparation/aggregation-rationale.md. Keine Variante, Schwelle oder Mischung anhand dieser neuen Leistungsdaten nachjustieren.

## Methodik und Grenzen

Für die legalen Aktionen L einer Einheit und Netz j: `r_j(a) = (Anzahl legaler b mit Q_j(b)<Q_j(a) + 0.5*(Anzahl legaler b mit Q_j(b)=Q_j(a)-1))/(|L|-1)`. Bei einer legalen Aktion bekommt diese 0.5. Alle legalen Gleichstände erhalten Midranks; ein völlig indifferentes Netz gibt jeder legalen Aktion 0.5. Illegale Aktionen tragen nicht zum Rang bei und erhalten Ausgabewert -1 vor der unveränderten Core-Maske. Bei mindestens zwei Aktionen gilt genau die Formel. Anschließend Mittel aller 36 Rangwerte; argmax mit kleinster Aktions-ID wie bisher. Nichtendliche Q-Werte oder keine legale Aktion sind technische Fehler, kein stiller Ausweichmodus.

Große Q-Aktionsabstände können Präferenzen bisher stärker gewichten. Ein Skalenfehler von V14 ist NICHT belegt; additive Offsets allein sind keine Ursache. Rangmittel verwirft möglicherweise sinnvolle Abstands-/Konfidenzinformation und kann korrelierte Mehrheitsfehler verstärken. Keine Kombination mit den beiden abgeschlossenen SAP-Prototypen. Keine neuen Gewichte oder Lernupdates.

## Globale Grenzen und Review-Fokus

- V14-Gewichte, ZIP, produktive Core-/Configdateien unverändert; keine Checkpoints schreiben oder Trainingsmodi zulassen.
- Exakt 36 verschiedene bereits geladene Mitglieder in gleicher Reihenfolge, je ein Forward pro aktivem Einheitensatz, gleiche Featurebreiten. Keine zweiten Forwards zur Diagnose.
- Masken/IDs aus genau dem aktuellen _decide-Cache; Row-Reihenfolge und Features gegen den echten Input prüfen. Matchreset oder keine Einheiten benötigen kein Netz.
- Originaler Core, nachgelagerte Regeln und Remember bleiben erhalten; new_game löscht nur Diagnosen, nicht den Aggregator oder die Gewichte. Playerwechsel beachten.
- Vor realen Läufen gezielte synthetische Tests und ein enger unabhängiger Review. Während Modellläufen keine Tests oder Quellen-/HEADänderungen. Maximal zwei Worker; echte frische Quota, Akku ausdrücklich erlaubt, kein Reset durch Agent.

## Task 1: Instanzlokaler Prototyp

Dateien: scripts/rank_mean_agent.py, tests/test_rank_mean_agent.py. Interface: `RankMeanAgent(Agent_x)` mit optionalem `rank_enabled=False`; `aggregation_members` liefert die geordneten 36 Originalmodule in beiden Modi. `aggregation_stats` enthält `calls`, `proposal_changes` (Einheiten) und `proposal_changed_steps`; `aggregation_last` enthält step, ids, masks, member_q, raw_mean, rank_mean, raw_greedy, rank_greedy bei ON, sonst None. Bei Reset/No-units ebenfalls None. Eine reine `legal_midrank_mean(member_q, masks)`-Funktion für Torch-Tensoren [M,N,6]/[N,6] produziert [N,6].

- [ ] Zuerst synthetische Tests: exakte Midranks, ein erlaubter Zug, gleiche Q-Werte, illegale Werte ausgeschlossen, große Skalen/positive affine Transformation, ungültige Werte/Nullmaske, Reihenfolge/Featurebreite und einmalige Forwards, Reset/Off/Trainings- und Speichersperre.
- [ ] Minimal umsetzen; gewöhnlichen Konstruktor/Core in Tests ersetzen, keine echten Gewichte laden. Projekt-venv verwenden.
- [ ] Nur diese Tests ausführen, tatsächlichen Aufruf/Log sichern, Root nimmt geprüfte Bytes auf und committet gemeinsam mit Werkzeugen.

## Task 2: Kleiner fester Runner

Dateien: scripts/rank_mean_eval.py, scripts/rank_mean_owner.py, tests/test_rank_mean_screen.py. Geprüften festen Motion-Runner als Ausgangspunkt eng anpassen, keine neue allgemeine Infrastruktur. Profil rank_mean_screen_20261109. Vorhandene Aufnahme-, Quellen-, Prozess-, Batterie-, Quota- und Scoreprüfungen beibehalten. Owner nur neuer Modulname. Factory prüft tatsächliche aggregation_members statt äußerer extra_q-Länge.

- [ ] Neue Factory/Profile/Karten und unabhängige Rangrekonstruktion gezielt testen. Keine alte Komplettsuite wiederholen.
- [ ] Passive instanzlokale Forward-Hooks erfassen die tatsächlichen 36 Outputs beider Rollen ohne Zusatzforwards. Aktuelle Masken/ID-Reihenfolge, Zahl und Featureinputs prüfen. ON-Ränge unabhängig in NumPy/Schleifen berechnen und gegen echte Modulausgabe/Diagnose prüfen; die originale V14-Aktionspipeline und Remember bleiben unverändert.
- [ ] Vier bekannte technische Spiele in Reihenfolge OFF831006/player_1, OFF831000/player_0, dann beide ON. OFF alle303nativenAktionen und historische Hash-/Punkte-/Matchdaten exakt. ON mindestens eine abweichende legale Netzpräferenz und insgesamt mindestens ein nativer Befehl gegenüber dem jeweiligen historischen Stream verschieden; kein Ersatzspiel. Das ist Integration, kein Stärkenachweis oder Frame-für-Frame-Kausalvergleich nach Trajektoriendivergenz.
- [ ] Rowdiagnose `aggregation`, `observed_proposal_changed_steps`, nicht SAP-Schussänderung nennen. Performance protokolliert Zustände mit geänderter legaler Netzpräferenz; beide Rollen sind gleiche V14-Konfiguration, frozen=False, Eval/Epsilon0, learn_enabled=False und Autosave aus.

## Task 3: Aufnahme und exakt 120 Spiele

Karten vorab: Panel9944000–9944019, Direkt9944100–9944119, jeweils beide Seiten; örtlicher Konfliktcheck vor Aufnahme. Vier Technikspiele separat abnehmen. Dann OFF/ON gegen Solution je40 und ON gegenOFF direkt40, kein automatischer Phasenwechsel/Wiederholungsstart. Technikquellen über beide Phasen unverändert halten.

Drei feste Hürden: geänderte legale Netzpräferenz auf mindestens fünf ON-Panelkarten; Solution-ScoreON≥OFF; direkt `2W+D>=48` von40. Netzpräferenz-Exposition ist ausdrücklich kein Beweis einer geänderten finalen Aktion nach Regeln. Ganze Karten einschließlich beider Seiten/gepaarter Rollen resampeln,5000PCG64-Seed0-Ziehungen, unadjustierte deskriptive95%-Intervalle. Fehlschlag schließt diesen Versuch ohne Nachschlag. Erfolg erlaubt eine separat festgelegte Bestätigung, keine direkte Übernahme.

- [ ] Root tatsächliche technische Daten akzeptieren, dann separat Performance aufnehmen.
- [ ] Vollständige Ergebnisse und Unsicherheit unabhängig nachrechnen, Quelle vor Änderung versiegelt abschließen.
- [ ] Dokumentation für Mahmoud, sinnvolle Ergebniscommits und sicherer Push/Lokalabgleich. V14 bleibt bis belegtem besseren Kandidaten.
