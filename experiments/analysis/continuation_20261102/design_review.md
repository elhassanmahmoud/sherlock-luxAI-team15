# Unabhängiger Entwurfsreview: Fortsetzung und passiver Targeting-Trace

Gelesen: `docs/superpowers/specs/2026-11-02-targeting-continuation-design.md`, `docs/superpowers/plans/2026-11-02-targeting-continuation.md`, verbindlicher Nachtrag `2026-11-02-targeting-trace-schema.md` und die12fixen Schlüssel in `/tmp/sherlock-continue-20261102/diagnostic_keys.json`; zusätzlich tatsächlicher V14-Q-/Masken-/Regelpfad in main/features und die bereits geprüfte Quellenmemo zur38,1%-Metrik. Nur Lesen; keine Implementierung, Spiele, Modelle oder Tests.

**Verdikt: zur Umsetzung des externen passiven Traces geeignet, kein blockierender Entwurfsbefund.** Der Auftrag autorisiert zunächst genau die Diagnose und ihre Passivitätsprüfung. Er legt noch keinen Fix, Trainingsarm oder neuen Leistungskandidaten fest. Autonome Umsetzung kann nach dem vorgesehenen technischen Review fortgesetzt werden; es ist kein weiteres Nutzermenü erforderlich.

## Scope und negative Vorgeschichte

Die neue Studie ist sauber von der abgeschlossenen CONTROL-Niederlage getrennt. V14 bleibt Referenz und die alte Bestätigung wird weder gepoolt noch um eine zweite Chance erweitert. Neue Leistungsumfänge/Gewichte werden erst nach einem belegten Mechanismus vor ersten Leistungsdaten festgelegt. Root setzt maximal zwei Kandidaten, einen Nominee und unveränderte Bestätigungsgates fest; fehlende Slots im Leistungsnachtrag sind zum jetzigen Diagnosestadium kein Blocker.

Die38,1%-Quote wird korrekt als agentensichtige Feld-/Planmetrik behandelt. Die Spec vermeidet die bereits negativen pauschalen Heimprioritäts-,Reserve-,Sticky- undUnstack-Runden. Wahrheit dient ausschließlich der nachgelagerten Trennung versteckter Gegner/echter Versorgung, nicht einem Orakel-Agenten. Energiearmut wird nicht pauschal mit dauerhafter Unerreichbarkeit gleichgesetzt. Formaler neuer Trainingsaufbau ist vor dieser Diagnose nicht erforderlich.

## Provenienz und tatsächlich prüfbarer erster Umfang

Der Schlüssel-Nachtrag enthält genau sechs verbrauchte Verlustspiele und die ersten sechs Gewinnzeilen derselben bekannten Auswahlquelle. Das sind qualitative Kontrollen, keine gematchten oder repräsentativen Gruppen.12Schlüssel×traced/untraced ergibt genau24reale Spiele, sequenziell mit einem Worker. Damit bleibt der Auftrag klein, reproduzierbar und ohne neue Auswahl-/Holdoutkarten.

Die explizite Forderung nach vollständigem nativen Aktionsbytevergleich mit Shape/Dtype sowie Spielen/Matchsiegen/Punktetotalen/v2/303Steps schließt die wichtige Lücke eines bloßen Ergebnisvergleichs: Identische Siege allein würden Passivität nicht belegen. Originale Benchmarkzeilen sind zusätzlich ein Reproduktionsanker, ersetzen aber den frischen Aktionsvergleich nicht. Manifest und Outputs müssen diese Ebenen getrennt aufzeichnen.

## Plausible technische Umsetzung

Der tatsächliche Agent berechnet Qs per `torch.stack([q]+extra_q).mean(dim=0)` in float32, nimmt anschließend eine NumPy-Sicht und maskiert diese in-place. Die vorgeschriebenen kopierenden Forward-Hooks und exakt gleiche Mittelungsreihenfolge erfassen deshalb die benötigten Rohwerte ohne zusätzlichen Netzforward. Wrapper beobachten den vorhandenen Methodenaufruf einmal; insbesondere kein zweiter `_enemy_stationary`-Aufruf, keine RNG-Ziehung und kein erneutes Belief-Update. Die Fehler-/Kontextmanagerbereinigung ist ausdrücklich spezifiziert.

Spieler1-Kanonisierung, Reset-/fehlenderCache-Status, tatsächliche79Features, getrennte rohe/maskierte/finale Aktion, erlaubte erste BFS-Verkürzung und die Aufzeichnung unaufgelöster Inline-Regelübergänge sind sachlich angemessen. Sichtbare Besetzung allein erklärt nicht jede Maskensperre; der Nachtrag macht die reale Maske maßgeblich. Sensorbasierte Energiefrische wird zu Recht nicht aus symmetrisch erweitertem `last_seen` erfunden.

Das auf120Unitpaare jeStep begrenzte Zwei-Eigentümer-Gegenfaktum ist eng genug: gleiche zwei eigenen bekannten Ziele, nur bewegliche Nicht-Halter, alte und neue Pfade/erste Schritte zulässig, kleinere BFSSumme. Es ist eine lokale Kostenbeobachtung, kein globales Optimum und kein Eingriff in die Policy. Das angegebene Beispiel liefert tatsächlich5gegen3Wegschritte. Künftige Heim-/Energie-/Stickykosten müssen die Kostenvergleichszulassung deaktivieren, wie gefordert.

## Konkrete Implementierungskontrollen, keine Scope-Erweiterung

1. JSONL/Gzip proFrame streamen. Die vielen24×24Karten,79Features proUnit und Hookwerte nicht über alle12Spiele im RAM sammeln. Bei Methodenwrapping nur definierte relevante Argumente/Felder kopieren, nicht proHook rekursiv das komplette Agent-/Kontextobjekt. So bleiben M3/8GB und der vorgegebene kleine Trace praktisch beherrschbar.
2. Lebender Holder/Stacker und Legacy-`first_on_tile` getrennt erhalten: falls ein maskierter Eintrag negative Energie hat, darf dessen bloße Reihenfolge keinen bewegungsfähigen Nicht-Halter oder sole holder vortäuschen. Der Nachtrag fordert ausdrücklich nichtnegative Energie für Holder.
3. Native und kanonische Aktionen getrennt speichern; die Passivitäts-SHA aus den unveränderten nativen Bytes bilden. Kein vorheriges Casten, Spiegeln oder Überschreiben zur „Normalisierung“ der Gleichheit.
4. Die beobachteten Eventwrappers dürfen aus einem Artillerie-OK oder einer booleschen Overkillabfrage keine nie aufgezeichnete frühere Bewegung rekonstruieren. Fehlende Zwischenstände bleiben markierte Restdifferenz.
5. 303echte Übergänge und Reset-/Nichtresetzahlen getrennt zählen; Matchpunkte an den V2-Zeitpunkt binden, keine Nullsetzung am Matchreset als Endpunkte behandeln. Diese Ausgaben sind im neuen Auftrag bewusst gefordert und dürfen nicht aus der früheren begrenzten Mechanismusdatei übernommen werden.

Diese Punkte konkretisieren bereits verlangte Grenzen und verlangen weder einen neuen Supervisor noch Produktionsänderungen. Bei unvollständigen Daten oder Passivitätsabweichung keine kausale Interpretation und kein Training aus dem Trace ableiten.

## Ressourcen und weitere Entscheidung

Ein sequentialer24-Spiele-Trace ist viel kleiner als eine neue Stärkenstudie. Die aktualisierte Spec erlaubt Akkuarbeit ausdrücklich (Nutzer-Nachtrag13:17Berlin): unter35% keine neue lange Phase, bei25% eigene schwere Jobs sichern/beenden; AC hebt diese Akkugrenzen auf. Kein Warten auf Netzteil. MaximalzweiWorker und keine parallele Vollsuite bleiben gültig. Die reine Ausgangssuite694+14 muss ohne Änderung nicht wiederholt werden; nach neuem Werkzeug sind fokussierte rote/grüne Tests und der angekündigte zentrale Volltest richtig. Kein tatsächlicher Lauf wurde in diesem Review zugelassen oder gestartet.

Nach Diagnose kann Root evidenzabhängig einen minimalen Targetingpfad oder die neue separate Gauß-Admission wählen. Keine automatische Kombination beider und kein Training allein, weil noch Zeit verfügbar ist. Der unabhängige Trainingsentwurf im selben `/tmp`-Ordner bleibt ein Vorschlag unter dieser Mechanismusbedingung; der jetzt konkretisierte passive Trace hat Vorrang.
