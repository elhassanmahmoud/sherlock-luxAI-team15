# Öffentliche SAP-Bewegungsfolgen: begrenzter Archivplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Ohne neue Spiele prüfen, ob Vorhalten gegen bewegte Gegner in vorhandenen Aufzeichnungen überhaupt untersuchenswerte Gelegenheiten bietet.

**Architecture:** Ein separates, nur lesendes Python-Analysewerkzeug verarbeitet genau die zwölf im historischen Targeting-Manifest gebundenen öffentlichen Traces. Keine Änderung von Agent, Training, Replay, Gewichten oder Aktionswahl. Ausgabe enthält alle Gelegenheiten und Ausschlüsse, Quellenhashes sowie eine beschränkte geometrische Diagnose.

**Tech Stack:** Python-Standardbibliothek, gzip/JSON; keine Modell- oder Projektimporte.

**Spec:** Dieser enge Plan enthält die vollständige Diagnosedefinition. Frühere Datenverfügbarkeitsprüfung liegt als Beleg bei der Diagnose; Hypothese wurde vor neuer Häufigkeitszählung festgelegt. Bestehender autonomer Auftrag; Auswahl dieser Fragestellung durch Codex, nicht als gesonderte Nutzerentscheidung ausgeben.

## Grenzen

- Genau zwölf bestehende Traces aus `experiments/analysis/continuation_20261102/targeting/manifest.json`, SHA256 `90324b008945da4a054a0559a108ee0023cf572d754b20af844160dfe4ebc435`. Historische Niederlagen und Gewinnkontrollen, keine repräsentative Stichprobe.
- Null neue Spiele, Tensorloads oder Lernupdates. Keine Suche nach neuen Karten/Parametern nach Ansicht der Daten.
- Auswahl ausschließlich aus `key`, `public` und `units` der bis dahin vorliegenden Frames. Kein `posthoc` oder verborgenes Enginewissen.
- Finale kanonische Aktion verwenden, nicht den vorgelagerten `sap_target`-Vorschlag. Position+SAP-Offset ergibt das Zielzentrum.
- Eindeutiger sichtbarer Gegner am bisherigen Zentrum; gleiche sichtbare UID im unmittelbar vorherigen Frame desselben Matches, genau ein kardinaler Schritt, nichtnegative beobachtete Energien und aktuelle Energie mindestens öffentliche Bewegungskosten. Das bleibt ein Kontinuitätsheuristik, kein Beweis derselben Lebensinstanz.
- Eigene finale SAP-Energie mindestens öffentliche SAP-Kosten; altes Ziel legal. Alle finalen SAPs trotzdem im ursprünglichen Nenner behalten.
- Neues Zentrum ist aktuelle Position plus beobachtete letzte Bewegung: innerhalb Karte, aktuell sichtbar/passierbar und in Chebyshev-SAP-Reichweite der eigenen Einheit. Eigene finale Aktion bleibt SAP; keine anderen Einheiten oder Entscheidungen werden verändert.
- Folgelabel nur bei direkt anschließendem Entscheidungsframe desselben Matches und erneut sichtbarer UID; fehlende Beobachtung bleibt unbekannt. Weiterlaufen, Abbiegen, Stehen und sonstige Bewegung getrennt zählen; Nenner und Sichtbarkeitsverzerrung berichten.
- Bei beobachteter Folgeposition nur idealisierte Geometrie des einzelnen Ziels vergleichen: Zentrum=1, benachbart=f, sonst0; vorab feste f=0/0,25/0,5/1. Kein archivierter öffentlicher Streufaktor, keine tatsächliche Schadens- oder Stärkebehauptung. Andere Ziele und Reaktionen sind damit nicht bewertet.

## Schritte

- [ ] Implementierung außerhalb der produktiven Agentendateien; kleine synthetische Fälle für Richtung, Spiegelungsfreiheit/kanonische Position, Grenzen, Sichtbarkeit, fehlende Folgeposition und Mehrfach-SAP auf dieselbe Gegner-/Schrittkombination.
- [ ] Root prüft Auswahl, Achsenordnung und Nenner anhand Recorderquelle; unabhängiger Code-/Definitionsreview vor Vollausführung.
- [ ] Einmalige vollständige Archivzählung; alle Datei-SHAs und Ereignisse speichern, existierenden Output nicht überschreiben. Pro Spiel/Gruppe sowie insgesamt zählen; Ereignisse pro schießender Unit und eindeutige Gegner/Frame-Fälle separat.
- [ ] Ergebnis gegen Ereignistabelle prüfen, Grenzen festhalten und sinnvollen nächsten Schritt entscheiden. Nur bei konkretem Signal wäre eine getrennte kausale Spielprüfung zu entwerfen; keine automatische Freigabe aus idealisierter Geometrie. Versionieren und für Mahmoud dokumentieren.

## Review-Fokus

Achsen [x,y], Match-/Resetgrenzen und UID-Wiederverwendung, Reihenfolge öffentliche Beobachtung → Auswahl → Folgelabel, fehlende Gegner nicht als STAY/Tod erfinden, mehrfach gezählte gleichzeitige Schüsse. Vorherige negative HOLD-, Geometrie- und Koordinationsstudien werden nicht nachträglich umgedeutet.
