# Sherlock: Zielplanung und Energie gezielt prüfen

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Aufgaben einzeln prüfen, keine Studien duplizieren.

**Goal:** Bis 03.11.2026, 06:00 Berlin einen begründeten Verbesserungsversuch
vollständig prüfen und nur einen nachgewiesen besseren V14-Nachfolger übernehmen.
**Architecture:** Passiver Entscheidungs-/Versorgungstrace, bedingte minimale
Intervention, getrennte technische Abnahme und frische Leistungsbestätigung.
**Tech Stack:** bestehendes Python/PyTorch/LuxAI; Kurs-Engine mit drei Matches.
**Spec:** `docs/superpowers/specs/2026-11-02-targeting-continuation-design.md`.

## Global Constraints

- V14-SHA `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`.
- Maximal zwei schwere Worker; kein paralleler Volltest. Nutzer erlaubt Akku;
  unter 35 % keine neue lange Phase, bei 25 % schwere Jobs sichern/beenden.
- Mindestens 30 % Kontingent erhalten, ab 65 % Abschluss; kein Reset.
- Wahrheit nur nachgelagerte Diagnose, keine Agenten-/Rewardeingabe.
- Quellen/HEAD/Gewichte über feste Vergleiche unverändert halten.
- Fremde Dateien/Sicherungen erhalten; Abgabetausch ausschließlich nach allen Gates.

## Review Focus

- Beobachter darf Q-Ausgaben, RNG, Kontexte und Aktionen nicht verändern.
- Spieler-1-Spiegelung und Reset-Schritte müssen korrekt markiert sein.
- Negative Energie, sole holder, verdeckter Gegner und unerreichbares Feld
  dürfen nicht als nachgewiesene verpasste Versorgung zusammenfallen.
- Geplantes Ziel, rohe Netzpräferenz, maskierte Präferenz und Endaktion sind
  verschiedene Größen; fehlende Instrumentierung nicht erfinden.
- Fehlende Gegner/Startmodelle oder veränderte Quellen machen einen Lauf ungültig.

## Aufgaben

- [x] 1. Repo/Remote/Prozesse/Kontingent prüfen, isolierten vorhandenen Worktree
  wiederverwenden. Letzte 694 Tests + 14 Untertests stammen vom unveränderten
  Ausgang; nicht ohne neue Änderung denselben Volltest wiederholen.
- [x] 2. Konkreten Trace-Schema-Nachtrag aus Quellenprüfung schreiben; Review.
  Implementer schreibt erst rote Verhaltenstests, dann das externe Werkzeug
  `scripts/targeting_probe.py` und `tests/test_targeting_probe.py`. Agentenlogik,
  Gewichte und Kursrunner unverändert. Mindestens: Spiegelung, freie/verdeckt
  besetzte Felder, BFS unerreichbar, negative Energie, Halter/Stacker,
  tatsächliche Endaktion, fehlender/passender Cache. Passivität real abgleichen.
- [x] 3. Vorab bestimmte verbrauchte Verlust- und Kontrollschlüssel vollständig
  diagnostizieren. Ausgaben/Hashes/303 Schritte/Ergebnisse separat nachrechnen;
  Messgrenzen und konkurrierende Erklärungen dokumentieren.
- [ ] 4. Auf Evidenz begrenzten Eingriff oder separaten Gauß-Admissionpfad wählen,
  bevor neue Leistungsdaten entstehen. Maximal zwei begründete Kandidaten;
  getrennte Configschalter default aus, rote Regression, minimale Umsetzung,
  grüne relevante Tests, unabhängiges Review und echte Kompatibilitätsspiele.
  Falls Training sinnvoll ist: Startkomponenten und echte Rollout-Config,
  Lernrate, Karten, Gegner, Endstandwahl und Abbruchgrenze vorher fixieren.
- [ ] 5. Seed-Audit und verbindlichen Leistungsnachtrag abschließen: genaue
  Auswahl-/Bestätigungsumfänge, Kandidaten/Hashes, Gegner/Hashes, feste
  Nominierungsregel, Source-Freeze und erwartete Schlüssel vor dem ersten Spiel.
  Vollständige Auswahl; höchstens einen Nominierter unabhängig bestätigen.
- [ ] 6. Daten/Statistik unabhängig prüfen. Nur bei allen Gates Vorgänger sichern,
  Abgabe übernehmen, Kurs-/ZIP-Kompatibilität prüfen. Sonst V14 unverändert.
- [ ] 7. Arbeitsstand/Protokoll und `docs/MORGENBERICHT_20261103.md` mit tatsächlichen
  Ergebnissen/Unsicherheiten aktualisieren. Geprüfte Einheiten sinnvoll committen,
  Remote sicher abgleichen und pushen; eigene Jobs/Watcher/Wachhalter und die
  beiden neuen Nachtaufträge nach Abschluss beenden.

## Noch nicht erfolgte Arbeit

Bei Anlage dieses Plans: keine neuen Spiele, Trainings, Agentenänderungen oder
Gewichtsübernahmen. Drei getrennte Lesediagnosen laufen. Nutzer erlaubt inzwischen
Weiterarbeit auf Akku; Netzteil kommt später, Ladestand wird überwacht.
