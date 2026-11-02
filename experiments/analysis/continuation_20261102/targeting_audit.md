# Unabhängiger Datenreview des V14-Zieltraces

02.11.2026 · **Technische Datenabnahme: PASS.** 584.037 unabhängig nachgerechnete Prüfungen, 0 Fehler. Keine neuen Spiele, Modellimporte oder Repositoryänderungen durch dieses Audit.

Die finale Diagnose lief 12:47:57–12:50:49 UTC auf HEAD `0c0dda642e9876141a705c2b8ed807a4f26ed870`. V14 blieb SHA `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`. **24 finale Spiele plus 2 frühere Integrationsspiele = 26 tatsächliche Spielausführungen.** Die früheren zwei werden nicht mit den finalen Traces vermischt. Der separate Vorladebeleg verzeichnet 36 exakt geladene Netze, 79 Merkmale/6 Aktionen, Evaluation/epsilon=0/kein Autosave und 0 Spiele/Forwards/Resets; seine Metadaten wurden geprüft, keine Tensoren erneut geladen.

## Was geprüft wurde

| Kriterium | Ergebnis |
|---|---|
| Vorab festgelegte Schlüssel | Exakt 12 seed/side-Schlüssel, je einmal unbeobachtet und beobachtet; alle 24 abgeschlossen. |
| Passivität und Ausgangsreproduktion | Alle zwölf Paare: gleiche vollständige native Aktions-SHA beider Teams, Konfiguration, Matchsiege, v2-Punktetotale und 303 Schritte. Zusätzlich Ergebnis/Siege/Punkte/v2/Schritte jeweils exakt zur alten `selection_baseline.csv`. |
| Rohtraces | Zwölf geprüfte gzip-Dateihashes, zusammen 3636 Frames = 3600 Entscheidungen + 36 Resets. Jede Step-/Matchfolge, Cache-Zeitangabe, Q-Argmax, Halterklasse, kanonische Endaktion, Freifeldmenge, BFS und alle zugelassenen Zweierpaare neu aus kopierten Rohfeldern berechnet. |
| Freeze | Guard vollständig, Exit 0, `inputs_unchanged=true`; finales Manifest SHA `90324b008945da4a054a0559a108ee0023cf572d754b20af844160dfe4ebc435`. Alle 208 gepinnten Datei-/Gewichtsidentitäten plus Python-Executable gegen aktuelle Dateien geprüft; Manifestquellen gegen deklarierten Git-Stand geprüft. |

Die SHA enthält auch gegnerische native Arrays samt Shape/Dtype. Diese Arrays sind nicht im Trace gespeichert: **Geprüft ist der Gleichstand der beiden vollständigen Streamhashes und deren Bindung ans Manifest, keine unabhängige Neuberechnung aus fehlenden Gegnerarrays.** Ebenso sind die einzelnen Netzausgaben nicht gespeichert; das Audit prüft das gespeicherte Ensemble-Q gegen Argmax/Masken, mittelt keine 36 Ausgaben erneut. Die quellseitige Beobachterprüfung ist eine getrennte Abnahme.

## Freie Felder: mehrere Hindernisse, kein pauschales Heimproblem

Gruppen umfassen jeweils **alle drei Matches** der sechs ausgewählten Verlustspiele (4 Karten) beziehungsweise sechs Kontrollspiele (3 Karten). Die Kontrollen sind genau die ersten sechs bekannten Siege in CSV-Reihenfolge, **keine repräsentative oder passend abgeglichene Kontrollstichprobe**.

Feld-Schritte; in Klammern Zahl unterschiedlicher Freiphasen, in denen die Bedingung mindestens einmal auftrat:

| Agentensichtig freie bekannte eigene Felder | Verlustspiele | Kontrollen |
|---|---:|---:|
| Insgesamt | 5008 (495) | 3384 (227) |
| Ohne Zielzuweisung | 1774 (131) | 1293 (105) |
| Nach Gedächtnis unpassierbar / kein lebender BFS-Weg | 967 (76) | 515 (48) |
| Nachträglich verdeckt gegnerisch besetzt | 127 (40) | 126 (18) |
| Kein beweglicher Nicht-Halter mit erlaubtem ersten Fortschritt | 984 (84) | 617 (68) |
| Ohne Ziel, aber mindestens ein solcher erster Fortschritt | 844 (77) | 773 (76) |

„Frei“ bedeutet keine eigene und keine **sichtbare** gegnerische Unit. Die Bedingungen überlappen; Phasen sind zusammenhängende Beobachtungen eines bekannten Punkts ohne eigene Unit, keine kausal verpassten Punkte. Jede Tabellenzeile betrifft alle sechs Spiele ihrer Gruppe. Alle freien Belief-Punkte waren nachträglich echte Punkte; tatsächliche Asteroiden kamen bei 978/507 Feld-Schritten vor und stimmen wegen Kartengedächtnis/Drift nicht immer mit dem Gedächtnisblock überein.

Die potenziell versorgenden Units der 844 Verlust-Feld-Schritte hatten durchweg konkurrierende **eigene bekannte Punktziele**; kein Fall enthielt eine potenziell versorgende Unit mit gegnerischem Ziel. Das zeigt keine freie Reserve: dieselbe Unit kann nicht mehrere Felder gleichzeitig bedienen. Eine globale Gegnerhälftenstrafe wird dadurch nicht begründet. Negative Zuweisungsinhaber erklären 21 Feld-Schritte in 21 Phasen/5 Spielen/3 Karten; unter Bewegungskosten liegende lebende Inhaber 30 in 8 Phasen/3 Spielen/3 Karten. Diese Teilbefunde tragen keine allgemeine Energie-Ausfilterung.

**Alter Nenner exakt reproduziert:** Nur die zwölf verlorenen Matches der alten sechs Spiele ergeben weiterhin **1681/4417 = 38,1 %**; 119 Phasen, sechs Spiele/vier Karten enthalten mindestens einen solchen unzugewiesenen Feld-Schritt. Auch 13.666 wahre eigene Punktfeld-Schritte und 2393/516 unbekannte Feld-Schritte bei bekanntem/unbekanntem Relic stimmen exakt mit der alten Aggregation. Zehn alte Matchgruppen-/Zählvergleiche sind exakt, einschließlich der sechs gewonnenen Matchanteile. 1774/5008 ist deshalb kein Widerspruch, sondern ein größerer Matchumfang.

## Q, Masken, Endaktion und Energie

Bei zugewiesenem eigenen bekannten Punkt in positiver BFS-Distanz gab es 3345/2004 Unit-Schritte mit legalem erstem Fortschritt. Maskiertes Q wählte Fortschritt in 2963/1879, die Endaktion in 3018/1917 Fällen. Ein maskierter Fortschritt ging durch spätere Regeln in 13/5 Fällen verloren; End-STAY trotz erlaubtem Fortschritt trat 63/27-mal auf. Diese Zahlen trennen Netzpräferenz und spätere Änderungen; sie belegen weder einen überwiegenden Regelengpass noch sicheren tatsächlichen Routenerfolg.

Nichtnegative Halter auf bekannten Punkten hatten **vor Aktion** in 3213/7747 (41,5 %) versus 2367/9314 (25,4 %) Unit-Schritten weniger als Sapkosten; 400/283 beobachtete niedrige Energieepisoden. Das sind erste lebende Halter je Feld, beide Hälften, keine unabhängig identifizierten Lebensläufe. Dies ersetzt die alte 40,9-%-Messung **nach Bewegungskosten/vor Sap** nicht. Energiephasenrekonstruktion ist in allen neuen Traces ausdrücklich `null`; daraus folgt keine Zuordnung des Energiedefizits zu eigenem Sap, Feindschaden, Void oder Feldenergie. Unbekannte Punkte bleiben getrennt: über ganze Verlustspiele 2987 Feld-Schritte nahe bekanntem Relic und 858 ohne bekanntes Relic bei 16.804 wahren eigenen Feld-Schritten.

## H1 und H2: beobachtet, Stärke offen

**H1, Bewegung → Artillerie → Overkill → End-STAY:** 16 nachgewiesene Unit-Schritte in 8 Frames, 15 zusammenhängenden Unit-/Ziel-Episoden, 5 Spielen/4 Karten. Davon 9 in Verlustspielen, 7 in Kontrollen. Alle 16 vorherigen Bewegungen waren nach tatsächlicher Maske legal. Nur **3** Fälle verloren legalen Fortschritt zu einem bereits bekannten eigenen Punkt (3 Freiphasen, 2 Spiele/2 Karten); davon liegen **2** in den zwölf alten verlorenen Matches. Die übrigen Fälle dürfen nicht als Ausfall eigener Punktversorgung ausgegeben werden.

Konkreter Fall: `831006/player_1`, Match 1, Beobachtung 62, Unit 11: Position `(17,4)`, Ziel `(17,5)`, Energie 109, BFS 1. Maskiertes Q und tatsächlich beobachteter Artillerie-Aufrufer wählen DOWN (3). Artillerie akzeptiert Sap, der spätere Overkill-Aufrufer sieht SAP (5) und storniert; Endaktion STAY. Dieses Match wurde gewonnen. Ein eng begrenzter Wiederherstellungspfad ist technisch motiviert; Häufigkeit und Beispiele beweisen keinen Sieggewinn oder dominanten Verlustgrund.

**H2, Zwei-Eigentümer-Gegenfaktum bei gleichem gewählten eigenen Zielset:** 141 Paar-Schritt-Gelegenheiten in **91 Frames, 82 zusammenhängenden Paar-/Ziel-Episoden**, allen 12 Spielen/7 Karten, mit Bezug zu 94 Freiphasen. Verlustspiele: 72 Gelegenheiten/42 Episoden; Kontrollen: 69/40. 137-mal sinkt die BFS-Summe um 2, viermal um 4. Wiederholte und überlappende Paare sind keine unabhängigen Verbesserungen; die aufsummierten 290 Distanzschritte sind kein realisierbarer Gesamtgewinn.

Beispiel: `831006/player_1`, Match 1, Beobachtung 77, Units 0/14 bei `(9,4)`/`(14,1)`, Energie 73/43. Tatsächliche eigene Ziele `(17,3)`/`(14,4)` ergeben BFS-Summe 12; reiner Eigentümertausch derselben Ziele 10. Beide Units sind bewegliche Nicht-Halter, alte und neue Wege im Gedächtnis erreichbar und besitzen erlaubte erste Schritte. Die tatsächlichen Endaktionen sind RIGHT/LEFT. Der Tausch wurde nicht ausgeführt; Energie einer ganzen Route, Folgeverhalten des Q-Netzes und Kampfwirkung sind nicht bewiesen.

**Abnahme gilt für technische Verwendbarkeit und diese deskriptiven Befunde.** H1/H2 sind reale enge Mechanismen, aber nicht spezifisch für Niederlagen und keine zugelassenen Stärkekandidaten. Keine Produktionsübernahme oder neue Leistungsstudie wurde durch dieses Audit ausgeführt.

[Core-Audit und Definitionen](targeting_independent_audit/targeting_audit.json) · [Episoden, sämtliche H1-/H2-Fälle und Vorlaufbelege](targeting_audit_details.json) · [Standardbibliothek-Auditskript](audit_targeting.py) · [Ergänzungsrechner](targeting_audit_details.py) · [Finales Rohmanifest](targeting/manifest.json)
