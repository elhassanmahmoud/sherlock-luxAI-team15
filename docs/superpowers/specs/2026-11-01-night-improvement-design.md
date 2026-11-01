# Sherlock: begrenzte Verbesserungsnacht vor dem Battle

Moayed autorisiert am 01.11. die selbstständige Weiterarbeit mit Subagents bis
02.11., 06:00 Berlin. Präsentation erst auf späteren Auftrag bearbeiten.

## Ausgang und Ziel

Ausgang ist Mahmouds V14 (`93a2ddd`, Gewichte `98a07350…d3d8`), nicht V10.
Ziel ist eine belegte Verbesserung in Richtung 100 % gegen Solution, mit
Robustheitsprüfung. Die explizite Teamentscheidung zur V14-Übernahme bleibt
historisch erhalten; weitere Ausnahmen sind hier nicht autorisiert.

## Ansätze und Entscheidung des Koordinators

1. Das letzte Nachtraining unverändert wiederholen: verworfen. Runde 6 brachte
   auf frischen Karten keinen gesicherten Gewinn; Einzelcheckpoints/Buffer fehlen.
2. Beobachtungsalgebra vervollständigen: bevorzugter Verhaltensversuch. Teilweise
   überlappende Gleichungen können sichere neue Fakten liefern. Nur logisch
   erzwungene Schlüsse, keine verborgenen Engine-Zustände oder Kartenprioren.
3. Begrenzter Trainingspilot mit stärkerem bestehendem Entdeckungsreward:
   passende Ergänzung zur Informationsdiagnose. Ein aus V14 extrahiertes Netz,
   gleicher Start, Karten und Gegner, Kontrolle gegen `w_discovery=2.0` statt 0.5.
   Kein allgemeiner Methodenbeweis aus einem Start, keine naive Ensemble-Fortsetzung.

Diese technischen Entscheidungen trifft Codex im Rahmen des ausdrücklich
delegierten Nachtauftrags. Kein neues Zustimmungsmenü erforderlich.

## Umsetzung und Grenzen

- Neue Inferenz standardmäßig aus, vorhandenes Verhalten mit ausgeschaltetem
  Schalter reproduzieren; Tests für Gleichungen, Symmetrie, Reset und Widersprüche.
- Trainieren ausschließlich in neuen Experimentordnern; ursprüngliche q-Tensoren
  nachweislich geladen, frischer Optimierer ausdrücklich dokumentiert,
  fehlende Dateien führen zum Abbruch. Gleiche Prefill-Policy und 600 Trainingsspiele
  je Arm, maximal zwei Stunden Trainingsbudget; Ende oder Abbruch ehrlich erfassen.
- V14 bleibt die Referenz. Ein Abgabetausch verlangt unabhängige Bestätigung,
  Sicherung, Kurs-Runner-/Paketprüfung und dokumentierte neue Prüfsummen.
- Mac M3/8 GB: maximal zwei Rechenworker, keine parallele Volltestsuite, lange
  Jobs nur am Netzteil, eigener Wachhalteprozess. Mindestens 30 % Kontingent
  erhalten, ab 65 % Verbrauch Schlussreserve, keine Resets.
- Remote-Watch führt ausschließlich Fetch aus. Keine Änderung eingefrorener
  Quellen, HEADs oder Gewichte; Mahmouds Änderungen erst am Phasenübergang integrieren.
- Abgabe nur Laufzeitcode, Gewichte, benötigte Hinweise/Abhängigkeiten/Lizenzen.
  Interne Repo-Doku wird nicht in die ZIP kopiert. Keine lokalen Dateiduplikate.

## Auswertung

Vor Spielbeginn frische Karten reservieren und festen Kandidatenplan schreiben.
Da `league_nets6` und `threat6` fehlen, heißt das lokal verfügbare Sechserpanel
aus Solution, Quadrat-Solution, V3, V7, V10 und V13 ausdrücklich ein neues Panel.
Seine Mittelwerte sind nicht mit Mahmouds ursprünglichem Sechsermittel identisch.
Neue Kandidaten und V14 spielen dieselben Karten von beiden Seiten.
Auswahl und unabhängige Bestätigung bleiben getrennt; keine Zwischenstands-
Nachjustierung auf dem Bestätigungsblock. Gepaarter Bootstrap ganzer Karten.

## Abschluss

Ab 05:00 Berlin keine neuen langen Jobs. Bis 06:00 kontrolliert beenden,
abgeschlossene Arbeit prüfen, nachvollziehbar committen/pushen und berichten.
Nicht qualifizierte Kandidaten bleiben Experimente. Keine unbewiesenen 100-%-Aussagen.
