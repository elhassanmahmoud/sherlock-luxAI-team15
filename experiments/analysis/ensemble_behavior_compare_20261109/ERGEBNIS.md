# BEHAVIOR38: Vergleich abgeschlossen, V14 bleibt

## Ergebnis

Alle 200 vorab festgelegten Spiele unter Quelle `16fae8afd42dc6b9c721be4fe46a7595375e8628` abgeschlossen. Keine Wiederholung, Unterbrechung, Ersatzspiele oder Zwischenwahl.

| Vergleich | Siege | Remis | Niederlagen |
|---|---:|---:|---:|
| V14 gegen Solution | 39 | 0 | 1 |
| CONTROL38 gegen Solution | 40 | 0 | 0 |
| BEHAVIOR38 gegen Solution | 40 | 0 | 0 |
| BEHAVIOR38 gegen V14 | 16 | 0 | 24 |
| BEHAVIOR38 gegen CONTROL38 | 12 | 0 | 28 |

Jede Reihe umfasst 20 feste Karten, beide Startseiten: Solution 9990000–9990019, direkt gegen V14 9990100–9990119, direkt gegen Kontrolle 9990200–9990219. Gleiche ursprüngliche Inferenzkonfiguration; CONTROL38 ist die historisch akzeptierte Kopie mit zwei klassisch nachtrainierten Netzen. BEHAVIOR38 hängt an die ursprünglichen 36 exakt beide neuen Endnetze an. Diese wurden bei der Aktionsauswahl gemeinsam mit 35 eingefrorenen Netzen trainiert, mit eigenem unverändertem DDQN und Reward. Kein Umbau des Abgabeagenten.

Die beiden Solution-Bedingungen sind erfüllt, beide Direktbedingungen (je mindestens 24 tatsächliche Siege von 40) verfehlt. **Kein nominierter Nachfolger und kein belegter Gesamtvorteil. V14 und die bestehende ZIP bleiben unverändert.** Keine Bestätigung oder Verlängerung dieser Variante. Die 40/40 auf 20 Karten sind keine allgemeine 100-Prozent-Quote. Die gleich erfolgreiche Kontrolle erlaubt auch keine isolierte positive Aussage zum neuen Trainingsverfahren.

## Unsicherheit und Grenzen

Deskriptive 95%-Intervalle aus 5000 Ganzkarten-Bootstrapziehungen, PCG64-Seed 0; jede Karte umfasst beide Seiten. Solution-Differenz zu V14 +2,5 Prozentpunkte [0; +7,5], zur Kontrolle 0 [0; 0]. Letzteres ist bei identischen beobachteten Ergebnissen degeneriert und bedeutet nicht null wahre Unsicherheit. Direkt gegen V14 40 Prozent [20; 60], gegen Kontrolle 30 Prozent [10; 50]. Breite Intervalle; keine universelle Verschlechterung bewiesen.

Historische Kontrollen sind keine frischen unabhängigen Trainingswiederholungen. Zwei feste ON-Starts, wiederholte projektweite Auswahl und keine Multiplizitätskorrektur. Karten wurden einmalig vorab geprüft; alle 884 intervenierenden eigenen Ausführungen überschneiden die reservierten Karten nicht. Grenzen des ursprünglichen lokalen Scans (undokumentierte/externe/formelbasierte Nutzungen) bleiben bestehen.

## Tatsächliche Prüfung und Übergabe

109 gezielte synthetische Werkzeugtests bestanden. Tatsächliche Nullspiel-Montage und Original-Agenten-Lader mit Batchgrößen 1/8/16 bestanden; unabhängiger Tensor-/Reihenfolge-/Configaudit. Die drei Evalkopien enthalten exakt 36/38/38 Mitglieder; Abgabe bytegleich.

Alle 200 tatsächlichen CSV-Zeilen, Karten/Seiten, vollständige 303-Schritt-Spiele mit Punktezählung v2, Ergebnisarithmetik, vier Bedingungen und sämtliche Intervalle unabhängig nachgerechnet (10.595 Prüfungen). Root hat die originale Analyse unter unveränderter Quelle exakt reproduziert und Quelle, Eingaben, Schutzdateien sowie Ende sämtlicher eigener Prozesse/Wachhalter geprüft. Root-Abschluss `operations/completion.json`, SHA `6a89f00b8dc819637b7ccb702f6bb0219f570638581bd7f01008971ffa1c1cff`; erst danach Quellenfreeze gelöst.

Rohdaten und Originalsummary: `performance_v1/`. Kandidat: `technical_v1/behavior.pth`, SHA `caddf31310f7fc4f21fe089bb15c129f55d4c8bcddde789e7731f96c82e36858`. Modelle/Resultate bleiben als Experimente erhalten. Einschließlich zugehörigem Training: 1084 Ausführungen (4 Technik, 80 Vorlauf, 800 Lernen, 200 Vergleich), 120000 Updates; Montage null Spiele. Andere historische Studien hier nicht erneut gezählt.

Nächster Schritt wird getrennt behandelt: kleiner Offlinecheck tatsächlicher archivierter Vorlauf-Rewards bei frühem Punktzuwachs vor bestätigten Punktefeldern. Noch keine neue Belohnungsvariante oder Trainingsfreigabe aus diesem Befund ableiten. Kein Wiederholen geschlossener Studien.
