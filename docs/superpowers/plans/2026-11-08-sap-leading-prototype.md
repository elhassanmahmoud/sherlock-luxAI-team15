# SAP-Vorhalteprototyp: technische Vorbereitung

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Einen separaten, standardmäßig inaktiven Prototyp bauen, der bei einem ohnehin finalen SAP auf die öffentlich prognostizierte nächste Gegnerposition zielen kann.

**Architecture:** Experimentlokale Unterklasse von Agent_x, keine Produktionsänderung und keine neuen Gewichte. Alle36 V14-Netze und die normale Entscheidungskette bleiben erhalten. Nach genau einem originalen _act-Aufruf darf höchstens der kleinste geeignete Schützen-UID pro Schritt einen anderen nativen SAP-Offset erhalten; vor dem originalen _act_est/param_est.remember. Keine zweite Aktionsberechnung und kein Nachplanen anderer Einheiten.

**Tech Stack:** Vorhandene Python-/NumPy-Agentenschnittstelle und kleine synthetische Tests; keine Trainingsausführung.

**Spec:** Der abgeschlossene [Archivbefund](../../../experiments/analysis/sap_leading_archive_20261108/README.md) rechtfertigt nur diese technische Vorbereitung. Codex wählt zunächst einen kleinen direkten Leistungsvergleich als mögliche Fortsetzung, um zusätzliche Gegenfakteninfrastruktur zu vermeiden. Ein Vergleich darf erst nach eigenem festen Karten-/Auswertungsplan und technischem Review starten; aus diesem Dokument starten null Spiele.

## Festgelegtes Verhalten

- Reiner Eval-Agent; Training ablehnen, Autosave deaktivieren, keine Änderungen der Gewichtsdateien.
- Sämtliche öffentlichen Archiv-Eignungsfilter gelten: finale SAP-Aktion; eigene Energie mindestens SAP-Kosten; legales altes Zentrum; genau eine aktuell sichtbare Ziel-UID; dieselbe sichtbare UID im direkt vorangehenden Schritt/Match; letzte Bewegung ein kardinaler Schritt; beide Gegnerenergien nichtnegativ, aktuelle mindestens Bewegungskosten. Neue Position = aktuelle + letzte Bewegung; auf Karte, aktuell sichtbar/passierbar und in SAP-Reichweite.
- Zusätzlich nur vorhandene öffentliche Parameterschätzung nach Beobachtungsupdate: `dropoff(default=1.0,min_conf=0.9)<1`; unbekannt/Faktor1 bleibt unverändert. Keine versteckten Engineparameter, kein Zukunftszugriff.
- Höchstens ein geeigneter Schütze je Schritt, kleinste UID. Keine zusätzlichen SAPs, Bewegungs-/Zielzuweisungsänderungen oder neuen Netze.
- Getrennte vorige öffentliche Positionen mit strikten Reset-/Match-/Schrittgrenzen; kein Zugriff auf den bereits überschriebenen Stationaritätscache.
- SAP→SAP erhält die Aktionsklasse. Vor Implementierung alle relevanten Erinnerungs-/Buchhaltungsfelder anhand des Cores prüfen. Zielabhängige `_sap_hits`, `sap_hits_est` und `_sap_unknown` konsistent korrigieren; keine behauptete Sicherheit über tatsächliche physische Wirkung. `param_est.remember` erhält den tatsächlich ausgegebenen nativen Befehl.
- Kumulative reine Messzähler für Ausschlüsse, Gelegenheiten und echte Änderungen; keine Entscheidungsabhängigkeit von diesen Zählern. Daten pro Spiel auswertbar.

## Aufgaben

- [x] Kleinste lokale Unterklasse und synthetische Tests außerhalb des produktiven Agenten entwickeln. Bis Root-Review nur `/tmp/sap-leading-prototype/` beschreiben. Keine echten Netze laden oder Spiele starten.
- [x] RED→GREEN-Prüfung von Spiegelung, Reset/Lücken, eigener/fremder Energie, Parametergrenze, unveränderten anderen Befehlen, höchstens einer Änderung, Erinnerung und Buchhaltung. Abgeschalteter Modus muss exakt originale Ausgabe/produktive Zustandsdaten liefern; Messzähler getrennt.
- [x] Unabhängiger Review plus Root-Abgleich; erst dann Aufnahme in `scripts/`/`tests/`. V14/ZIP-Hashes prüfen.
- [ ] Separaten begrenzten Leistungsvergleich festlegen, einschließlich frischer Karten, identischer V14-Konfiguration beider Seiten, Eingriffshäufigkeit und eindeutiger Auswahlbedingungen. Noch kein solcher Lauf und keine Abgabefreigabe.

## Review-Fokus

Kein zusätzlicher Core-Aufruf, native/kanonische Spiegelung, Parameterupdate vor Auswahl und remember nach Änderung, mutierbare öffentliche Positionskopien, SAP-Zählerdelta statt Doppelzählung. Ein geometrischer Vorteil ist kein Siegbeleg. Das unveränderte V14 bleibt bis zum unabhängig belegten besseren Kandidaten.

Technische Aufnahme am09.11.: [tatsächliche Prüfungen](../../../experiments/analysis/sap_leading_prototype_20261109/README.md), bytegleicher Code nach unabhängiger statischer Prüfung,44Repo-TestsPASS. Keine echten Modelle/Spiele, letzter Schritt weiterhin offen.
