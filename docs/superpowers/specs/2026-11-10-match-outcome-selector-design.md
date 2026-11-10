# V14 durch gelernte Matchentscheidungen ergänzen – Designvorschlag

**Spätere Freigabe 10.11.:** Moayed hat Umsetzung und selbstständige bedingte Fortsetzung beauftragt. Die folgenden ursprünglichen Planungsgrenzen bleiben als Verlauf erhalten; der jüngste Arbeitsstand beschreibt die tatsächliche Phase. Noch keine automatische Leistungsfreigabe oder Übernahme.

## Technische Reparaturfestlegung nach tatsächlichem Abbruch, 10.11.

Der erste Snapshot-Durchlauf ist wegen nachgewiesener Baseline-Abweichung technisch geschlossen:19 vollständige und1 teilweise Ausführung, insgesamt10.203 Engine-Schritte, kein Stärke-/Lernzielbefund. Set-Kopien können die Reihenfolge gegnerischer Gleichstandsentscheidungen ändern; die konkrete gegnerinterne Ursache des realen Fehlerschritts ist mangels internem Zustandsdump nicht vollständig bewiesen. [Fehlerbeleg und Grenzen](../../../experiments/analysis/match_outcome_probe_20261110/SNAPSHOT_FEHLER.md).

Unter der ausdrücklichen autonomen Umsetzungsfreigabe ersetzt Root die ungeeignete Kopiertechnik einmalig durch **Rekonstruktion vom Spielanfang**. Das ist eine transparent vergrößerte technische Messung, kein automatischer Neustart, Ersatz verlorener Spiele oder neuer Kandidatenversuch. Alte Dateien bleiben erhalten und werden nicht mit neuen Labels vermischt. Karten, Auswahlregel, Eingriffsstelle, Matchziel und Gates B/C ändern sich nicht.

- Neue Dateien/Outputs getrennt: `scripts/match_outcome_replay.py`, neue `prefix_technical/` und `prefix_remaining/` unter derselben Studie. Originaler Sammler bleibt als historischer Fehlerstand erhalten, nicht weiter ausführen.
- Pro16Schlüssel ein vollständiger Stock-V14-Referenzlauf und ein vollständiger passiver Sammler,303Schritte jeweils. Beide gesamten Verläufe müssen gleich sein; der Sammler zeichnet öffentliche Gelegenheiten auf, ohne Snapshots/Branchspiele einzuschieben.
- Jede der maximal48Alternativen erhält neue Agenten, zurückgesetzte Solution-Globals und RNGs, denselben Seed. Jeden Schritt vor dem Eingriff exakt mit dem Baselineverlauf vergleichen; danach bis Ende des aktuellen Matches, niemals zusätzlich das nächste Match. Der Baselineast ist der entsprechende Abschnitt des bereits vollständig reproduzierten Referenzlaufs. **Keine Objektkopie und keine Gegneränderung.**
- Erste vorhandene Alternative je Karte einmal unabhängig vom Anfang wiederholen, exakt gleicher vollständiger Verlauf; maximal8Wiederholungen. Ein abweichender Frame wird vor Abbruch gespeichert.
- Neue feste Obergrenze:32Referenz-/Sammelläufe +48Alternativläufe +8Wiederholungsläufe = höchstens88 gestartete Ausführungen; **21.816 Engine-Schritte** =32×303 +16×(101+202+303)+8×303. Prefixläufe bis Match1/2 sind Teilpartien, bis Match3 vollständige Partien. Tatsächliche vollständige/teilweise Läufe und alle Schritte getrennt berichten; diese Last nicht als nur32Spiele ausgeben.
- Technik zuerst auf `11011007/player_0` (tatsächlicher Fehler) und `11011017/player_0` (Kontrolle), dann übrige14Schlüssel derselben acht Karten. Die vier vollständigen Technikreferenzen sind in32enthalten; ihre Alternativ-/Wiederholungsläufe in48/8. Nach vollständiger tatsächlicher Prüfung ausdrückliche Root-Aufnahme der restlichen Phase, gleiche eingefrorene Quelle.
- Bei erneutem Integritätsfehler den Reparaturversuch ebenfalls stoppen und ehrlich dokumentieren, keine automatische weitere Reparaturrunde. Keine Gradienten oder Übernahme. Laufende neue Phase bindet alte technische Rohdateien der neuen Prefix-Phase, nicht die fehlerhaften Snapshotlabels.

Diese datierte Festlegung ersetzt ausschließlich Kopiermechanik, technische Reihenfolge und Ausführungsobergrenzen der ursprünglichen PhaseA unten. Die5-%-Reserve, unveränderte V14-/ZIP-Hashes und bedingte spätere Lern-/Leistungsprüfung bleiben bestehen.

**Status: nur vorgeschlagen, nicht umgesetzt oder gestartet.** Nutzerauftrag vom 10.11.: schwächere Kandidaten analysieren und den nächsten sinnvollen Plan entwickeln, mindestens 5 % Kontingent erhalten. [Befund](../../../experiments/analysis/residual_postmortem_20261110/ERGEBNIS.md).

## Entscheidung und Hypothese

V14s 36 Netze, Gewichte und Regeln bleiben Grundlage. Statt erneut lokale DDQN-Werte zu korrigieren, prüfen wir, ob eine eng begrenzte Alternative **nach allen Regeln** einen tatsächlichen Matchausgang verbessert. Erst dann lernen wir die Auswahl aus öffentlichen Zustandsmerkmalen. Ein solcher Entscheider darf V14 ablehnen, aber kein verstecktes Simulatorwissen verwenden.

Das ist eine Hypothese, keine zugesagte Verbesserung. Geprüft wird zunächst nur der zweitbeste legale Netzausgang bei knappen Bewertungen im mittleren Matchabschnitt. Ein negativer Pilot widerlegt weder jede andere Alternative noch jede Form des Entscheidungslernens.

## Warum dieser Versuch und keine neue Rewardwelle?

- Die neuen Residualnetze ändern etwa jeden achten untersuchten Rohvorschlag, ohne bessere Spielresultate zu erzielen.
- Punkte über das ganze Spiel und geformte Einheitenbelohnungen sind nicht dasselbe wie Matchgewinne. Alte Reward-/Folgeaktions-/Ensembleversuche werden nicht wiederholt.
- Eine zwölf Schritte lange HOLD-Fortsetzung ist bereits untersucht. Neu sind die breitere Aktionsart und das tatsächliche Matchendlabel. Nur den alten HOLD-Horizont zu erhöhen und denselben Kopf erneut zu trainieren wäre nicht der vorgeschlagene Versuch.
- Ein gezieltes finales SAP-Veto ist eine mögliche spätere Alternative, aber durch die aktuellen Residualverluste nicht kausal begründet. Wir implementieren nicht beide Richtungen gleichzeitig.

## Phase A: kleiner Einfluss- und Lernzielpilot

**Karten:** bekannte Entwicklungskarten `11011000, 11011001, 11011002, 11011004, 11011007, 11011011, 11011013, 11011017`, beide Seiten gegen Solution. Die Auswahl enthält bekannte Verluste und Kontrollen; ausdrücklich keine frische Leistungsbewertung.

**Ausführungen:** je Schlüssel ein unveränderter Referenzlauf und ein passiv instrumentierter V14-Lauf. Maximal 32 vollständige Ausführungen, keine Gradienten. Die ersten vier sind `11011017/player_0` und `11011000/player_0`, jeweils Referenz/Instrumentierung; vor den übrigen 28 ihre tatsächliche technische Gleichheit prüfen. Nicht separat weitere Technikspiele hinzufügen.

**Eine Gelegenheit pro Match:** Am ersten Schritt im Bereich 40–70, an dem mindestens eine aktive Einheit zwei endliche legale Q-Werte hat, unter den aktuellen Einheiten den kleinsten Abstand zwischen Rang 1 und 2 wählen. Gleichstände nach UID, Aktionsrang nach kleiner Aktionsnummer auflösen, kompatibel zu V14s Argmax. Keine Suche über zukünftige Schritte, kein weiteres Q-Regret-Filter. In der Praxis wird der Schritt häufig 40 sein. Keine Gelegenheit = Nullfall, keine Ersatzkarte.

**Ein Eingriff:** Baseline-Vorschlag unverändert versus genau zweitbester legaler Rohvorschlag dieser Einheit. Die normale vollständige Regelkette verarbeitet beide, inklusive SAP-Ziel/Schadensplanung und Koordination weiterer Einheiten. Anschließend bis Matchende normaler V14, kein weiterer Eingriff im Branch. Gesamte erste Teamaktion samt SAP-Offsets vergleichen; bei identischer Aktion dürfen sich Fortsetzungen nicht unterscheiden. Unwirksame Alternativen bleiben im Datensatz, kein Nachrücken zu Rang 3 oder einer anderen Einheit.

**Snapshot:** vor beiden `act`-Aufrufen, kompletter Agent-/Gegner-/Gedächtnis-/RNG-Zustand mit Aliasidentität; unveränderliche Modellmodule dürfen nach Prüfung geteilt werden. Gegen Solution vorhandene `holder_rollout`-Mechanik wiederverwenden. Keine Ableitung aus gespeicherten alten Zustandsdigests: Diese sind keine fortsetzbaren Snapshots. Beim späteren V14-Gegner dessen eingefrorenen Modulgraph ebenfalls korrekt behandeln.

**Label:** tatsächliche Änderung des gewonnenen aktuellen Matches, `delta_win ∈ {-1, 0, +1}`. Ausgang direkt nach Engine-Abschluss einschließlich Punkte-, Energie- oder Zufallsentscheidung erfassen. Das initiale Punktkonto gehört zum Matchausgang. Gesamte Teamenergie und Entscheidungsgrund nur in externer Diagnose; Gegnerenergie/Future/Seed nie in Eingabefeatures. Zeitfenster endet nach dem finalen Schritt, ohne nächste Matchaktion. Kein weiteres Match im Branch.

**Zielgrenze:** Das Label erfasst keine späteren Vorteile oder Nachteile durch verändertes Gedächtnis und Erkundungswissen. Ein gewonnener aktueller Matchflip kann mit einem schlechteren Gesamtspiel einhergehen; umgekehrt können aktuelle Nachteile spätere Vorteile verdecken. Deshalb bleibt die Prüfung vollständiger Spiele mit derselben wiederholt angewendeten Policy zwingend.

**Begleitdiagnose:** dieselben Branches liefern Punktdifferenz nach 12 Schritten, Matchendpunkte, terminale Energien, Matchausgang und H12-/End-Signalwechsel. Ein früher positiver Punktwert ist kein positiver Sieg. Gleicher Randomzustand ist eine gepaarte Simulation, keine Garantie, dass ein Ergebnis in jeder verborgenen Welt gleich ausfällt.

**Feste Rechenobergrenze:** 16 Sammelspiele × maximal 3 Matches = 48 Paare; zwei Branches × höchstens 61 Schritte = maximal 5.856 zusätzliche Hauptschritte. Je erster vorhandener Gelegenheit pro Karte einmal umgekehrte Wiederholung beider Branches: maximal 976 weitere technische Schritte. Keine automatischen Wiederholungen nach Fehlern, keine neuen Karten wegen geringer Ausbeute. Nur ein Modellworker; keine Tests parallel zu Spielen.

**Gate A – technische Integrität:** Referenz und passiver Sammler identisch, Baselinebranch entspricht dem tatsächlichen anschließenden Referenzverlauf, Reihenfolgen-/Wiederholungsprüfung bestanden, keine abgefangenen Agentenfehler, keine Quellen-/Gewichtsänderung, vollständige Schlüssel und Endzustände. Bei Verstoß stoppen und Fehler benennen; keine Ergebnisinterpretation aus ungültigen Paaren.

**Gate B – hinreichender Einfluss:** mindestens 24 Paare, deren erste vollständige Teamaktion zwischen Baseline und Alternative verschieden ist, verteilt über mindestens 6 Karten. Bei Verfehlung ist diese Vorschlagsauswahl zu selten wirksam; daraus kein allgemeines Urteil über Matchlernen ableiten.

**Gate C – Lernziel vorhanden:** mindestens 3 positive Matchflips auf 3 verschiedenen Karten. Alle negativen Flips und Nullfälle ebenfalls berichten. Kein positiver Durchschnitt über alle unselektierten Alternativen verlangt: Ein späterer Selektor soll schädliche Alternativen erkennen. Diese praktischen Mindestmengen sind keine Signifikanzschwellen und reichen allein noch nicht zum Trainieren eines zuverlässigen Modells.

Nach vollständiger Auswertung endet Phase A. Bei verfehltem Gate keine automatische Verlängerung, kein neues Netz, keine Übernahme. Auch bei bestandenen Gates gibt es erst einen Nachweis nutzbarer Alternativen unter vollständigem Simulatorzustand, keinen besseren Agenten.

## Bedingter Weg zu einem Kandidaten

Vor neuen Daten in Phase B ein kurzes ergänzendes Protokoll festschreiben: feste, getrennte Lern-/Validierungskarten gegen Solution und V14, feste Datenobergrenze, öffentliche Merkmalsliste, kleines Modell und Abnahmekriterien. Der Pilot darf Lern-/Entwicklungsdaten liefern, aber keine frische Validierung sein. Erst seine tatsächlich gemessene Ereignisrate bestimmt, ob eine begrenzte Sammlung sinnvoll ist; hier keine unbegründete Modellgröße oder ausreichend große Trainingsmenge behaupten.

Der geplante Kopf schätzt die **erwartete Matchausgangsdifferenz** einer Alternative, einschließlich ihres Schadensrisikos. Er lernt weder nur positive Beispiele noch V14s Q-Werte. Eingaben: öffentliche aktuelle Einheiten-/Matchmerkmale und Kandidatenbeschreibung; keine Seeds, zukünftigen Endwerte, Gegnerinternas oder unsichtbaren Zustände. Kleiner regulierter Kopf vor einem weiteren großen Netz. Schwelle strikt positiv, vor Validierung fixieren; Nullkopf bleibt bei V14.

Auch eine abgelehnte Alternative verbraucht die einzige Gelegenheit dieses Matches. Sonst unterschieden sich Lern-/Prüfpolicy. Ganze Karten trennen; Karten ohne Eingriff mitzählen. Einzelne positive Gegenfakten dürfen nicht zu einem vermeintlich erreichbaren Spielgewinn aufaddiert werden. Frühere Eingriffe verändern spätere Zustände: vollständige Spiele sind deshalb unverzichtbar.

**Kompakte Leistungsauswahl als Zielrahmen:** ein eingefrorener Kandidat, zunächst 40 Spiele direkt gegen V14 und je 40 gegen Solution für Kandidat und V14, beide Seiten; bei erkennbarem Erfolg kleiner Gegner-/Defaultkontrollblock. Mindestens 24 direkte Siege und keine beobachtete Solution-Verschlechterung als Vorauswahl, ausdrücklich noch kein Beweis. Danach genau eine vorab begrenzte neue Bestätigung mit Kartenintervallen und Schutz gegen Rückschritte; genaue Zahl/Gates vor deren erstem Ergebnis festlegen, keine wiederholte Wahl bis zum erwünschten Resultat. Keine erneuten Tausenderwellen ohne begründeten Präzisionsbedarf.

V14 erst ersetzen, wenn die vollständige Policy auf getrennten Karten den Vorteil bestätigt und die Kursprüfung besteht. Auch dann lässt sich keine allgemeine 100-Prozent-Garantie gegen Solution geben. Sicherung/Hashes und Wiederherstellung vor Austausch dokumentieren.

## Unveränderliche Schutzbedingungen

- Beide V14-Gewichte: SHA256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`.
- Bestehende ZIP: SHA256 `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`.
- Aktueller Auftrag nur Analyse/Plan. Keine neuen Spiele, Trainings, Agentenänderungen oder Automationsaktivierung dadurch autorisiert.
- Mindestens 5 % Kontingent erhalten. Ab 92 % Verbrauch keine neue Phase beginnen und sichern; spätestens 95 % stoppen. Frische Quota vor tatsächlichem Modellstart, keine Resets. Fremde Arbeit erhalten, Remote vor sicherem Phasenübergang abgleichen.
