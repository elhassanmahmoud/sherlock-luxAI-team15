# Gezielte Feldtests: früher verwertbares Punktewissen

**Status 11.11.2026: nach der Planungsrunde zur bedingten Umsetzung freigegeben.** Aktuellen tatsächlichen Stand im [Arbeitsstand](../../ARBEITSSTAND.md) lesen. Die vorab festgelegten Bedingungen bleiben unverändert; V14 und ZIP bis zum nachgewiesenen Vorteil erhalten. [Umsetzungsplan](../plans/2026-11-11-information-probing.md).

## Entscheidung und Begründung

Als Nächstes eine einzige koordinierte Informationsprobe untersuchen: maximal zwei nicht produktiv haltende Einheiten verändern gemeinsam ihre Bewegung, damit das nächste öffentliche Punktesignal ein unbekanntes Feld eindeutig bestimmen kann. Zuerst die Gelegenheit in vorhandenen Aufzeichnungen nachweisen, erst danach einen ausführbaren Kandidaten bauen. Keine weitere Ensemble-, Reward- oder Schussvariantenserie.

Beispiel: Aus der bisherigen Besetzung folgt `A + B = 1`. Besetzt eine spätere Situation nur B (alle anderen Punktbeiträge sind bekannt), verrät das echte neue Punktesignal B und damit A. Das Wissen wird nicht vorausgesetzt oder erfunden. Ob die geplante Besetzung tatsächlich zustande kommt und ob der Informationsgewinn den Bewegungsaufwand rechtfertigt, ist gerade die offene Frage.

### Was die bisherigen Ergebnisse tatsächlich sagen

| Befund | Konsequenz für den nächsten Versuch |
|---|---|
| Residualnetze R61/R62: Solution 35/40 bzw. 38/40 gegenüber V14 40/40; direkt 14/40 bzw. 10/40 | Neue Bewertungen sind nicht automatisch bessere finale Entscheidungen. Kein erneutes Nachtraining derselben Korrekturen. |
| Matchausgang-Pilot: 43 wirksame Eingriffe, ein positiver und ein negativer Matchflip | Einzelne zweitbeste Aktionen liefern bisher keine ausreichende Lernbasis. |
| Halter-Schussverzicht: 46 Paare, zwei gerettete und ein zusätzlich verlorenes ganzes Spiel, aber Matchsiegsumme −2 und Punktedifferenzsumme −914 | Schussverzicht ist nicht als generelle Verbesserung belegt. Studie geschlossen. |
| Frühere Orakel-Diagnose auf **v18r, einem V14-Vorläufer**: bei Sichtweite 1 auf 72 Karten/144 Spielen gegen Solution 85,4 % ohne Orakel, 94,4 % mit bekanntgegebenen Punktefeldern um bekannte Relics | Rechtzeitiges Punktewissen ist ein plausibler Hebel. Das ist weder eine Messung des aktuellen V14 noch ein praktisch erreichter Gewinn. |
| `OVERLAP`, `cand_post`-Folgevarianten und Kandidaten-Rettung waren bereits untersucht | Mehr abgeleitete Fakten, schnellere Zielwahl oder ein gerettetes Einzelspiel genügen nicht. Der neue Mechanismus muss tatsächliche frühere Information und anschließend Spielerfolg nachweisen. |

Quellen: [Residualbericht](../../../experiments/analysis/residual_ensemble_20261110/ERGEBNIS.md), [Matchpilot](../../../experiments/analysis/match_outcome_probe_20261110/ERGEBNIS.md), [Schussverzicht](../../../experiments/analysis/holder_sap_causality_20261111/ERGEBNIS.md), [Experimentprotokoll, Orakel und frühere Erkundung](../../EXPERIMENT_PROTOKOLL.md).

### Was daran neu ist

`Belief._add_differences` kann Teilmengengleichungen bereits lösen; `subset_infer` ist in V14 aktiv. `assign_targets` weist Ziele anhand der vorhandenen Prioritäten und Wege zu. Der neue Versuch soll bewusst eine **gemeinsame Besetzung mit Informationswert** erzeugen. Er ersetzt weder den bestehenden Belief-Solver noch bloß eine Entfernungsgewichtung. Seine Abgrenzung muss im Code-Review bestätigt werden; findet sich eine bereits gleichartige abgeschlossene Policy, nicht erneut ausführen.

## A – Gelegenheit ohne neue Spiele prüfen

Feste Eingabe: `experiments/analysis/continuation_20261102/targeting/manifest.json`, SHA256 `90324b008945da4a054a0559a108ee0023cf572d754b20af844160dfe4ebc435`. Zwölf vorhandene vollständige öffentliche Traces:

- Verlustschlüssel: 831006/p1, 831029/p0, 831042/p0 und p1, 831043/p0 und p1.
- Kontrollschlüssel: 831000, 831001, 831002, jeweils p0 und p1.

Diese Karten sind bekannt und dienen ausschließlich der Machbarkeit. Manifest, CSV, Quellen-/Konfigurationsherkunft und tatsächliche Modellbytes vor Verarbeitung binden. Historische absolute Pfade durch nachgewiesene identische Dateien ersetzen; fehlende neue inaktive Config-Felder ausdrücklich abgleichen, nicht still ignorieren.

**Öffentliche Daten:** `public`, `units`, native Aktionen und chronologische Punktstände. Die `posthoc`-Sektion und spätere Frames dürfen weder Feldauswahl noch Voraussetzungen beeinflussen. Vollständige Belief-Records fehlen im Archiv: aus dem öffentlichen Präfix rekonstruieren, fehlende Beweise als nicht prüfbar zählen.

Für ein stabiles Match gilt: der aktuelle Punktzuwachs entspricht den **aktuell beobachteten** verschiedenen eigenen besetzten Feldern mit Energie mindestens null. Nicht die Positionen vor dem letzten Zug verwenden. Stapel zählen einmal. Bekannte Punkte abziehen, bekannte Nullfelder entfernen; Rest ergibt eine Gleichung über die verbleibenden Felder. Gleiche symmetrische Felder nicht zu einer Variablen mit falscher Vielfachheit zusammenziehen. `candidate == False` bedeutet nicht automatisch bekanntes Nullfeld. Widersprüche oder Matchwechsel verwerfen die entsprechenden Gleichungen/Nullannahmen; keine Reparatur mit versteckter Wahrheit. Bei fehlenden öffentlichen Daten keine Gelegenheit behaupten.

**Fester Suchraum:** nur erstes Match, Matchschritte 50–80 einschließlich, erste geeignete Gelegenheit pro Spiel. Der private Probespeicher sammelt eigene Gleichungen und Nullannahmen ausschließlich aus Beobachtungen ab Matchschritt 50. Frühere Gleichungen/Nullannahmen nicht übernehmen: Ein Relic-Spawn kann sie ungültig machen, ohne dass sofort ein Widerspruch sichtbar wird. Maximal 400 jüngste gültige Gleichungen. Es wird nur geprüft, ob das unten beschriebene Verfahren anhand des damaligen Wissens eine zulässige, zusätzliche Informationsprobe hätte vorschlagen können; dies beweist noch keine realisierte Information oder Stärke.

**Gate A:** mindestens sechs der zwölf Spielschlüssel auf mindestens drei verschiedenen Karten mit vollständig öffentlichem, nachvollziehbarem Beweis; mindestens ein Verlust- und ein Kontrollschlüssel. Andernfalls schließen: keine Engine, kein erweitertes Zeitfenster, keine Ersatzkarten, kein Training.

## B – Ein eng begrenzter ausführbarer Prototyp

Nur nach Gate A. Originale 36 Netze, Gewichte, Features, Belief-Inferenz und nachgelagerte Regeln bleiben gleich. Experimentelle Unterklasse nutzt den vorhandenen `_policy_greedy`-Hook **nach maskierter Netzwahl und vor der vollständigen Regelkette**. Kein neuer Standardpfad, keine zusätzliche Netzrechnung oder Belief-Aktualisierung. Der heutige Live-`ctx` enthält keine `sensor_mask`: Die Unterklasse übernimmt diese aus der tatsächlichen aktuellen Beobachtung, kanonisiert sie für beide Seiten und reicht sie nur an die Probe weiter. Den Basispfad genau einmal aufrufen. Nicht `belief._vis_now` verwenden, weil dort durch Symmetrie ergänzte Sicht enthalten ist; das Archiv hat die echte Sicht separat gespeichert.

1. Bis zu vier aktive Nicht-Halter mit maskiertem Netzvorschlag STAY oder MOVE auswählen, sortiert nach Entfernung zum nächsten unbekannten Kandidatenfeld, dann UID. Eine eigene aktuell produktiv besetzte Position darf durch den Eingriff nicht aufgegeben werden. Ausgangsaktionen für die Projektion sind die legalen maskierten Netzvorschläge aller Einheiten; unveränderte SAP-Einheiten bleiben für die Belegungsprojektion am aktuellen Ort und sind keine Eingriffskandidaten.
2. Höchstens zwei dieser Einheiten auf eine andere maskenerlaubte STAY-/MOVE-Aktion setzen. Höchstens 113 gemeinsame Belegungsentwürfe einschließlich Original (16 Einzel- und 96 Paaralternativen). Keine SAP-Änderung.
3. Für jede veränderte Einheit: Ursprung und Ziel sichtbar, passierbar, kein sichtbarer Nebel; Energie mindestens zweimal Bewegungskosten, kein sichtbarer Gegner im Chebyshev-Abstand bis `sap_range + 1` zu Ursprung oder Ziel. Fehlende Kosten/Sichtinformationen schließen aus. Das ist eine konservative öffentliche Voraussetzung, keine Garantie gegen unsichtbare Gegner.
4. Geplante unbekannte Belegung mit einer normalisierten früheren Gleichung vergleichen. Nur wenn die Mengen sich um genau ein bisher unbekanntes Kandidatenfeld x unterscheiden, ist x nach dem nächsten echten Punktsignal eindeutig ableitbar. Bekannte Beiträge müssen in beiden Gleichungen korrekt verrechnet sein. Die unveränderte Belegungsprojektion darf x nicht bereits genauso isolieren.
5. Deterministische Wahl: kleinste Zahl geänderter Einheiten, dann kleinste zusätzliche Manhattan-Distanz zu deren bereits zugewiesenen Zielen, dann x/UID/Aktionsreihenfolge. Keine nachträgliche Schwellen- oder Kartenauswahl anhand Resultaten.
6. Maximal **ein Probeversuch pro ganzem Spiel**, ausschließlich im Fenster aus A. Auch eine von nachgelagerten Regeln aufgehobene Probe verbraucht den Versuch. Aktionsregeln dürfen weiterhin übersteuern. Eigener Speicher enthält nur öffentlich hergeleitete Gleichungen; niemals erwartetes Punktewissen in Belief injizieren.

Der Regelablauf bleibt sichtbar: Beobachtung → Belief/79 Merkmale → 36 Netze → Maske/Argmax → **optionaler gemeinsamer Feldtest** → bestehende Regeln → finale Aktionen → tatsächlicher Punktzuwachs. Geplanter, final emittierter und tatsächlich ausgeführter Eingriff sowie reales neues Wissen werden getrennt gezählt.

### Kleiner vollständiger Vergleich auf den zwölf bekannten Schlüsseln

Je Schlüssel originale V14-Referenz, experimentelle Unterklasse AUS und dieselbe Unterklasse AN: 36 vollständige Partien. Zwei zusätzliche AN-Wiederholungen auf 831006/p1 und 831000/p0, insgesamt **38 Partien / höchstens 11.514 Engine-Schritte**, null Gradienten. Die acht Ausführungen dieser beiden Technikschlüssel zuerst separat abnehmen; erst dann die übrigen 30. Frische Originalstarts, keine kopierten Engine-/Solution-Zustände. AUS muss die originale Referenz frame- und aktionsgleich reproduzieren; AN muss vor seinem Eingriff gleich sein.

**Gate B:** keine technischen Fehler/illegalen Aktionen/falschen Fakten; exakte Wiederholbarkeit; mindestens sechs Spiele auf drei Karten mit wirklicher Aktionsänderung; in mindestens vier Spielen auf drei Karten x durch echte öffentliche Daten mindestens drei Schritte früher bestimmt als AUS. Wird x in AUS bis zum ersten Matchende nicht bestimmt, den Vorsprung als rechtszensierte Untergrenze ausweisen. Punkt und Nicht-Punkt zählen als Information; Spiegelduplikate nicht doppelt zählen. Ganze Spielsiege AN ≥ AUS und Summe eigener Matchsiege AN ≥ AUS. Sämtliche Gelegenheiten, Informationsvorsprünge und Erfolgs-/Matchsummen ausschließlich auf den zwölf eindeutigen AN/AUS-Paaren berechnen; die zwei zusätzlichen AN-Ausführungen prüfen nur Reproduzierbarkeit. Kein einzelnes positives Beispiel genügt. Bei Verfehlung schließen. Diese kleine bekannte Stichprobe belegt noch keine allgemeine Verbesserung.

## C – Frische Auswahl, nur bei tatsächlichem Bestehen von B

Ein Kandidat, eine eingefrorene Konfiguration, keine weitere Suche. Vor Ausführung Karten gegen vorhandene Manifeste/CSVs/Trainingsarchive prüfen, genaue Reichweite dieser Prüfung dokumentieren; Seed-Kollision oder unbekannte Herkunft stoppen die Aufnahme. Identische Seeds allein sind bei anderer Engine-/Parametrisierung kein vollständiger Kartenidentitätsbeweis.

- Solution: 20 neue Karten, beide Seiten, je Kandidat und V14 = 80 Partien; reserviert 11210000–11210019.
- Direkt gegen V14: 20 andere neue Karten, beide Seiten = 40 Partien; reserviert 11210100–11210119.

**120 Partien.** Nominierung nur bei mindestens gleich vielen Solution-Siegen wie V14 und mindestens 24/40 direkten Siegen, ohne Fehler. Ein 40/40-Gleichstand gegen Solution ist kein belegter Solution-Gewinn. Die Seedbereiche sind Vorschläge, noch nicht vollständig als unbenutzt zertifiziert; vor Ausführung prüfen, bei Kollision keine stillen Ersatzbereiche.

## D – Unabhängige Bestätigung und mögliche Übernahme

Nur bei C; weiterhin genau derselbe eingefrorene Kandidat, keine Nachjustierung. Solution auf 100 neuen Karten/beiden Seiten für beide Agenten = 400 Partien (11211000–11211099); direkt auf 100 anderen/beiden Seiten = 200 (11211100–11211199); default auf 20 anderen/beiden Seiten für beide = 80 (11211200–11211219). **680 Partien**; gleiche Herkunftsprüfung wie C.

Vor Aufnahme finalen Vergleichsvertrag mit Quellen-/Modellhashes, Engine/Solution-Versionen und diesen Hürden speichern:

- Direkt mindestens 55 %; untere Grenze des 95-%-Kartenclusterintervalls über 50 %.
- Solution beobachtete Siegdifferenz mindestens null und untere Grenze des gepaarten 95-%-Kartenclusterintervalls mindestens −2 Prozentpunkte; Summe eigener Matchsiege nicht niedriger. Dies ist eine begrenzte Nichtunterlegenheitsbedingung, kein Nachweis eines Solution-Zuwachses. Nur eine untere Grenze über null erlaubt diesen Zuwachs zu behaupten.
- Default mindestens 39/40, höchstens ein Sieg weniger als V14.
- Intervalle aus 10.000 Ziehungen ganzer Karten mit beiden Seiten, RNG-Seed 20261111. Keine Behandlung der beiden Seiten als unabhängige Stichproben. Falls alle Kartenkontraste identisch sind und der Bootstrap degeneriert, keine scheinbar exakte Sicherheit behaupten und keine Übernahme allein auf dieser Grundlage; Ergebnis dann unter diesen Gates unzureichend. Kein automatisches Aufstocken.
- Aktuelle Engine entscheidet ganze Spiele anhand `team_wins`; echte Unentschieden gegebenenfalls vorab als 0,5 werten und separat zählen. Keine Punktesumme anstelle der Spielwertung. Sämtliche Fehler/Abbrüche offen erfassen, keine Ersatzspiele.
- Separat Kurs-Interface, CPU-Laufzeit und exportierte ZIP prüfen. Erst nach bestandenen statistischen und technischen Hürden alten Agenten/ZIP sichern und neuen Code übernehmen; Originalgewichte müssen für diese Policy nicht verändert werden.

Maximal **838 Vergleichspartien** über B/C/D, aber vor der ersten Entscheidung **null**, vor dem ersten Leistungs-Screen **38**. Jede spätere Phase entfällt bei negativem Gate. Kein Training in diesem Plan; kein unbefristetes Weiterprobieren. Ein neu benötigter technischer Kurslauf wird vor seiner Aufnahme separat konkret gezählt, nicht als unsichtbarer Teil der Vergleichszahl ausgegeben.

## Durchführung und Grenzen

- Bestehende Studien bleiben geschlossen. Während jeder realen Phase Quellen/HEAD/Modelle einfrieren; neue Mahmoud-Commits nur lesen und am sicheren Übergang integrieren. Ein Modellworker, keine Tests parallel zu Modellläufen. Keine automatischen Neustarts.
- Mindestens 5 % Kontingent erhalten; ab 92 % Verbrauch keine neue Phase beginnen, spätestens bei 95 % kontrolliert stoppen. Vor jeder Phase aktuelle tatsächliche Quota prüfen; unbekannte Quota erlaubt keine umfangreiche Aufnahme. Keine Resets durch Codex.
- Root setzt inline um. Ein gezielter unabhängiger Review für Gleichungs-/Aktionslogik und ein Datenreview vor einer Stärkeaussage sind sinnvoll; keine dauerhaften unbeschäftigten Subagents.
- Die Diagnose macht diesen Ansatz plausibel, nicht bewiesen. Der einmalige Feldtest kann zu selten sein, von Regeln aufgehoben werden, zu viel Positionierung kosten oder Information zu spät liefern. Dann wird er geschlossen. Auch 100 % auf endlich vielen Testkarten garantieren keine universellen 100 % gegen Solution.
