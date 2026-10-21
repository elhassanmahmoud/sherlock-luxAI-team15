# Unabhängiger Point-flow-Ergebnisreview — 21.10.2026

**Kein Patch empfohlen: Der streng ausgelegte, vorab genannte Nahbereichs-Befund (unerreichbar trotz Manhattan≤2) bleibt bei beiden Modellen unter 10% freier Feld-Schritte.** Blockierte Zielzuweisungen und Pendeltrajektorien sind konkret beobachtet, rechtfertigen unter diesem Arbeitsfilter aber keine jetzige Policyänderung.

## Datenprüfung

- Alle 40 Spiele vollständig: V3/V4 jeweils Karten 500720–500729 × beide Seiten × Solution_92, exakt 20 eindeutige Schlüssel. Beide Kinder `returncode=0`, Gesamtstate vollständig.
- Alle nichtzeitlichen Referenzfelder erneut unabhängig gegen `inference_development2/phase2_reference.csv` beziehungsweise `regeln/T_v4_720.csv` verglichen: numerisch absolut 1e−9, Text exakt. 303 Schritte und Punktezählversion 2 überall. Keine fehlenden Referenzfelder.
- Spielresultate und Summaries zwischen JSON und JSONL identisch. Alle gespeicherten Primärsummaries aus den Rohzeilen neu berechnet; keine doppelten `(match,step,tile)`-Schlüssel. Manhattan- und Differenzfelder intern konsistent.
- 104 gespeicherte Input-/Pythonquellen-/Interpreter-Hashes gegen aktuelle Bytes geprüft, null Abweichungen. Historische Start-/Endidentität gleich; Lauf-HEAD `8517f88594e0e909a7d631e197e98b1ed4ca9dcb`. Während der abschließenden Wiederholung wurde der reine Ergebnis-/Dokumentationscommit `ffcc39411841f37d3a96c2295466690ac643798f` erstellt; alle 104 geprüften Eingabedateien bleiben bytegleich. Modellgewichte nur gehasht, niemals geladen. Kein Torch/JAX, kein Spiel, kein Git-Schreibzugriff.
- State-SHA `90a3025c49b717fe8bfb4f77561cac12aee962450d8c7c5c70c65cf9f1b50543`. V3-Rohdaten `b28c6d4686cf4afda8e8c0641eb0c7cc17c181935317e4cc7a5d9e8679cef479`; V4 `afffb6a7e9c45f5865f683d98d633d69471e7fa3baf2c3e132ec66b42a871962`.

## Primärfenster und Nenner

Match 3, inklusive Match-Schritte 20–95, bekannte Punktefelder strikt in eigener Hälfte (`x+y<23`). Diagonale separat, je Modell 608 bekannte Feld-Schritte; unten nicht eingerechnet. Beide Seiten einer Karte zusammenfassen: nur zehn unabhängige Kartenpaare, keinesfalls Tausende unabhängiger Entscheidungen.

| Kennzahl | V3 | V4 |
|---|---:|---:|
| Bekannte eigene Feld-Schritte | 8.525 | 8.574 |
| Frei | 2.550 (29,91%) | 2.335 (27,23%) |
| Frei, lebend zugewiesen | 2.392 | 2.192 |
| Frei, negative ID / ohne Zuweisung | 119 / 39 | 106 / 37 |
| Lebende Zuweisung: Bewegung | 86,54% | 84,63% |
| BFS ≥6 / 3–5 / 0–2 / unerreichbar, lebende Zuweisung | 1.241 / 466 / 378 / 307 | 1.043 / 462 / 360 / 327 |
| BFS−Manhattan ≥4, Anteil aller freien Feld-Schritte | 115 (4,51%), 4 Karten | 58 (2,48%), 4 Karten |
| Enger Stay / Segment ≥3 | 0 / 0 | 0 / 0 |
| Frei, Ziel laut Belief blockiert | 270 (10,59%), 7 Karten | 290 (12,42%), 7 Karten |
| **Frei, blockiert UND lebend zugewiesen** | **261 (10,24%), 7 Karten / 13 Spiele** | **282 (12,08%), 6 Karten / 12 Spiele** |
| **Frei, blockiert UND lebend zugewiesen UND Manhattan≤2** | **147 (5,76%), 6 Karten / 12 Spiele** | **165 (7,07%), 6 Karten / 12 Spiele** |
| Alle unerreichbaren lebenden Nahzuweisungen (Manhattan≤2) | 158 (6,20%), 6 Karten | 178 (7,62%), 6 Karten |
| Energie unter Bewegungskosten | 211 (8,27%) | 248 (10,62%) |
| Zuweisungswechsel | 750 (29,41%) | 681 (29,16%) |

**Das enge Arbeitsgate ist verfehlt.** Blockierte lebende Nahzuweisungen betreffen zwar jeweils sechs Karten, aber nur 5,76%/7,07% der freien Feld-Schritte. Auch alle unerreichbaren Nahzuweisungen erreichen nur 6,20%/7,62%. Der allgemeine Umwegbefund bleibt ebenfalls unter 10%. Enger Stay hat keine Beobachtung.

Korrektur gegenüber meiner ersten Zwischenmeldung: Dort bezog ich die 10%-Schwelle auf blockierte Ziele sämtlicher Entfernungen (10,24%/12,08%). Das ist eine nachträgliche Erweiterung gegenüber der von Root verlangten strikten Nahbereichs-Auslegung und wird **nicht als bestandenes Gate** verwendet. Der Plan nennt unterschiedliche Mechanismen beispielhaft; sie nach Sichtung zu vereinigen wäre ebenfalls kein sauberer Ersatz. Niedrige Energie erfüllt den Filter nur bei V4 und ist kein Änderungsvorschlag. Zuweisungswechsel allein belegen keine Fehlentscheidung.

| Karte | V3 frei / blockiert+lebend | V4 frei / blockiert+lebend |
|---|---:|---:|
| 500720 | 205 / 16 | 203 / 16 |
| 500721 | 572 / 102 | 579 / 104 |
| 500722 | 596 / 16 | 281 / 0 |
| 500723 | 89 / 12 | 90 / 12 |
| 500724 | 414 / 88 | 433 / 104 |
| 500725 | 0 / 0 | 2 / 0 |
| 500726 | 96 / 0 | 113 / 0 |
| 500727 | 52 / 14 | 38 / 14 |
| 500728 | 394 / 13 | 489 / 32 |
| 500729 | 132 / 0 | 107 / 0 |

Die Verteilung ist konzentriert: Karten 721/724 liefern 190/261 beziehungsweise 208/282 der betroffenen Schritte. Median des Kartenpaar-Anteils: V3 7,80% (Karte ohne freien Nenner ausgeschlossen), V4 7,21%. Der gepoolte 10%-Filter darf nicht als typischer Effekt jeder Karte dargestellt werden.

## Konkrete Trajektorien

Alle Koordinaten kanonisch; Schritte innerhalb Match 3. Ziel/ID über die genannten Segmente unverändert, Ziel als blockiert gemessen, Energie jeweils für Bewegung ausreichend. Finale Aktionen sind die tatsächlich zurückgegebenen Aktionen.

- **500720, Seite 0 (auch Seite 1), V3 und V4, ID 5, Ziel (3,10):** Schritte 26–32 sieben aufeinanderfolgende Zuweisungen. Positionen `(1,9)→(2,9)→(2,10)→(2,11)→(2,10)→(2,11)→(2,10)`, Energie 73→63. Schritte 28–32 wiederholtes Pendeln neben dem unerreichbaren Ziel, statt enger Stay.
- **500721, Seite 0, V3, ID 15, Ziel (14,8):** Schritte 82–92 elf Zuweisungen. Nach Annäherung pendelt die Unit Schritte 86–92 zwischen `(13,7)` und `(13,8)`. Energie 51→17, also nicht energielos. Gegnerdruck kann beitragen; aus der Bewegung allein folgt keine sichere alternative beste Aktion.
- **500724, Seite 1, V4, ID 9, Ziel (7,14):** Schritte 53–62 zehn Zuweisungen, Energie 170→226. Positionen u.a. Schritte 55–58 `(7,12)↔(8,12)`, später `(7,13)↔(6,13)`. Auch hier Bewegung und Richtungswechsel statt Stay.
- Gegenbeispiel zur Überinterpretation: V3 Karte 500724, Seite 0, ID 7 nähert sich Schritte 39–45 demselben blockierten Ziel (10,12) von Manhattan 13 auf 7. Nicht jede blockierte Zuweisung ist bereits beobachtetes Pendeln oder verlorener Punkt.

Vollständige ausgewählte Segmente einschließlich Energie, Aktion, Bedrohungs-/Kartenwechselindikator stehen in der begleitenden JSON-Datei.

## Entscheidung: kein Patch in dieser Runde

Die Daten begründen eine konkrete Hypothese, aber das enge Häufigkeitsgate nicht. Deshalb weder BFS-Zuweisungsumbau noch pauschalen Bewegungszwang oder sofortigen Filterversuch starten. Die bestehende Policy bleibt unverändert.

Für eine spätere, ausdrücklich neu festgelegte Untersuchung wäre genau eine Hypothese übrig: Ein abschaltbarer Filter ausschließlich für **unbesetzte, laut Belief blockierte eigene bewiesene Punktziele**. Das wäre ein Zuweisungsfilter und keine Wiederholung des gescheiterten `pt_walk`-Versuchs. `point_coords()` liefert bislang alle bewiesenen Punkte unabhängig von `passable`; die Zielmatrix verwendet Manhattan. `belief.passable` bedeutet ausdrücklich „nach letztem Wissen kein Asteroid“ (`belief.py:544`), sichtbare Kartenteile werden wegen Drift laufend überschrieben (`belief.py:266`). Dies ist derzeit nur eine archivierte Hypothese, keine Implementierungs-/Laufempfehlung.

Sollte eine spätere Untersuchung separat beschlossen werden, sind bereits besetzte Ziele zu erhalten: Ein Asteroid kann unter eine Unit driften; die Diagnose begründet nicht, dort stehende Units wegzuschicken. Punktwissen müsste erhalten bleiben und ein wieder passierbares Ziel normal auswählbar werden. Insbesondere Ziel-Sichtbarkeit/Alter der Asteroideninformation und alternative erreichbare freie Ziele fehlen, um den tatsächlichen Nutzen vorher zu bestimmen.

## Grenzen

Beobachtungsdaten liefern keine kontrafaktischen Aktionen, keine optimale alternative Zuweisung und keine zusätzlichen gewinnbaren Punkte. Blockierte Felder können gegenwärtig selbst nicht besetzt werden; die mögliche Hypothese betrifft die gebundene Unit. Belief kann außerhalb Sicht veraltet sein, Asteroiden driften: frühe Anreise kann im Einzelfall nützlich sein. Rohdaten enthalten keine Ziel-Sichtbarkeitskarte und beweisen deshalb nicht für jeden Schritt eine aktuell sichtbare Blockade. `belief.last_seen==current` wäre kein sicherer Ersatz: last_seen wird auch über Symmetrie aktualisiert, tile_type nur über direkt sichtbare Sensorfelder (belief.py:268–280). Es gibt sogar 405/404 besetzte blockierte eigene Feld-Schritte im Primärfenster; Asteroiden unter besetzten Punktfeldern sind daher ausdrücklich vom etwaigen Filter auszunehmen. Target bestätigte zudem im Enginecode, dass die Punkteberechnung keine Tile-Typ-Prüfung enthält. Stale Belief ist bei einem Filter ein reales Risiko, keine durch den Häufigkeitsfilter gelöste Frage.

Bekannte Entwicklungskarten, nur Solution_92, zehn Kartenpaare und keine Auswahl nach Spielausgang. Statische BFS ignoriert Energie, Gegner und künftige Drift; enges Stay schließt Sap/Bedrohung aus. Die Hashprüfung bestätigt gespeicherte Dateien, rekonstruiert aber keine fehlende vollständige Beobachtungskarte. Kein Stärkebeweis und keine Empfehlung für weiteres Training aus diesem Befund.

Reproduzierbare reine Stdlib-Prüfung: `/tmp/point_flow_final_audit.py`; Kennzahlen: `/tmp/point-flow-final-review.json`. Quellen und Modelle unverändert.

## Archivierung

Die vollständigen Originaldateien bleiben im Diagnoseordner erhalten. Die zwei etwa 15-MiB-JSONL-Dateien wurden zusätzlich deterministisch mit gzip (mtime=0, leerer Originalname) komprimiert und beim Entpacken gegen ihre SHA256 geprüft. `historical_snapshots/` enthält bytegleiche Textkopien des damaligen Observers, Runtimehelfers, Fixtures und Plans sowie der unabhängigen Prüfroutine; keine neuen ausführbaren Repo-Pythonquellen. Diese Snapshots dokumentieren historische Zulassungsfristen/Pfade und sind kein unmittelbar erneut freigegebener Lauf. `archive_manifest.json` enthält Größe/SHA256 sämtlicher Diagnose- und Archivdateien außer sich selbst sowie die Herkunft der Snapshots. Der Review berechnet keine fehlenden Ziel-Sichtbarkeiten nach. Keine gemeinsamen Dokumente, Gewichte oder Gitstände wurden durch diesen Review geändert.
