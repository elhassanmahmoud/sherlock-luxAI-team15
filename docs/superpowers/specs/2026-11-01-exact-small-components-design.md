# Begrenzter exakter Gauß-Fallback – Lesedesign

Stand: Arbeitskopie `sherlock-v10-mechanics`, laufende Auswahl auf **aa06601**. Ausschließlich Quellen gelesen und dieses Kurzdesign unter `/tmp` geschrieben. Keine Implementierung, Tests, Rechenversuche, Spiele, Trainings, Quelleneingriffe oder Seedreservierungen. Der aktuelle A/B/C-Versuch bleibt unverändert.

**Empfehlung: als getrennten späteren Mechanismusversuch plausibel, nicht algebraisch verwerfen.** Exakte rationale Elimination kann beweisbar neue 0/1-Fakten liefern, die die bestehende Subset-/Overlap-Propagation nicht findet. Häufigkeit in echten Restniederlagen und Nutzen für Spielstärke sind vollkommen offen. Gegenüber dem kleinen Overlap-Pfad deutlich höhere CPU-/Komplexitätskosten; Umsetzung nur nach Rootentscheidung in getrennter Arbeitskopie und eigenem Vorabplan.

## 1. Konkretes, binär erfüllbares Gegenbeispiel

Fünf verschiedene offene Felder, keine davon Spiegelbilder der anderen, vier gültige Beobachtungsgleichungen desselben stabilen Matchabschnitts:

```text
(1) a + d + e = 2
(2) a + b     = 1
(3)     b + c = 1
(4)         c + d = 1

(1) - (2) + (3) - (4):  e = 1
```

Die Belegung `(a,b,c,d,e)=(1,0,1,0,1)` erfüllt sämtliche Gleichungen; es ist somit kein nur rational lösbares, in Wahrheit unmögliches Beispiel. Alle Lösungen haben e=1, während a frei bleiben kann: b=1−a, c=a, d=1−a. Ersetzt man ausschließlich den Rest in (1) durch 1, folgt ebenso sicher e=0, etwa mit Belegung (1,0,1,0,0).

**Warum der vorhandene Code stehen bleibt:**

- Keine Gleichung hat Rest 0 oder Rest=Mengengröße; `_propagate` findet keinen Startfakt (`agents/sherlock/belief.py:781–803`).
- Keine Feldmenge ist echte Teilmenge einer anderen; `_add_differences` erzeugt nichts (`:600–626`).
- (1) mit (2) oder (4) hat Exklusivmengen der Größen 2 und 1. Der Restunterschied ist 1 (bzw. 0 in der Nullvariante), erreicht also weder +2 noch −1. Die übrigen sich überschneidenden Paare haben gleiche Reste und je ein Exklusivfeld; disjunkte Paare liefern ebenfalls nichts. `_overlap_differences` erzeugt daher nichts (`:628–683`).
- Diese Aussage ist unabhängig von der Reihenfolge der vier Beobachtungen: sämtliche möglichen Paarvergleiche bleiben unergiebig.

Das ist ein **Code-/Algebragegenbeispiel, keine beobachtete neue Spielkarte**. Es belegt den möglichen zusätzlichen Schluss, nicht dessen tatsächliche Häufigkeit. Eine seltene Konstellation kann den Laufzeitaufwand wertlos machen.

## 2. Exakte Schlussregel, bewusst unvollständig

Aus gültigen normalisierten Records eine kleine rationale Matrix `C x = r` bilden und mit `fractions.Fraction` auf reduzierte Zeilenstufenform bringen. Nur wenn eine fertige RREF-Zeile **genau eine nichtnull Variable** enthält und diese damit exakt den Wert 0 oder 1 hat, darf dieser Wert als neuer Fakt zurückgegeben werden. Alternativ beschrieben: ein Pivot hängt von keiner freien Variable mehr ab. Keine Rundung, kein Schwellwert, keine Belegung freier Variablen und keine angenommene Unabhängigkeit.

Jede Elimination ist eine umkehrbare rationale Zeilenoperation. Alle binären Modelle der ursprünglichen gültigen Beobachtungen sind auch rationale Modelle. Ein in allen rationalen Lösungen festgelegtes x=0/1 gilt deshalb in allen binären Lösungen. Das Gegenbeispiel hat einen solchen festen Pivot trotz Unterbestimmtheit der restlichen Komponente.

**Wichtige Grenze:** Gauß ist keine vollständige binäre Inferenz. Beispielsweise kann `2x+y=1` mit binären Variablen x=0,y=1 erzwingen, ohne dass die rationale RREF einen der Werte festlegt. Das wird im Minimalversuch absichtlich nicht zusätzlich mit Branch-and-Bound, SAT, Integerprogrammierung oder Suchbelegungen gelöst.

## 3. Spiegelsymmetrie braucht Multiplizitäten

Bei aktivem `symmetry` können Variablen über die bekannte Involution M zusammengefasst werden: `rep(f)=min(f,M(f))`. Das darf **keine Set-Deduplizierung der Belegung** werden. Jedes ursprünglich eindeutig besetzte physische Tile zählt einmal; liegen f und M(f) gleichzeitig in einer Gleichung, hat ihre gemeinsame Variable den Koeffizienten **2**. Ein Tile auf der Spiegelachse bleibt Koeffizient 1. Stacking auf demselben physischen Tile zählt weiterhin nur einmal, wie in der bisherigen Beobachtungsgleichung.

Bekannte positive Variablen werden mit ihrer vollen Multiplizität vom Rest abgezogen, bekannte Nullvariablen nur entfernt. Beispiel: die Belegung `{f,M(f),g}` mit Gewinn 1 wird `2*x_rep(f)+x_rep(g)=1`, keinesfalls `x_rep(f)+x_rep(g)=1`. Neue Werte anschließend nur über bestehende `_mark_point`/`_mark_dead` übertragen; keine zweite eigene Karten-/Spiegellogik bauen.

Wenn Symmetrie aus ist, bleiben physische Tileindizes getrennte Variablen. Der sichere noch kleinere erste Entwurf könnte die Orbits ganz weglassen und nur vorhandene `_mark_*` verwenden; er verlöre Schlüsse und liefe früher in die Variablengrenze. Welche Variante umgesetzt wird, vor einem Versuch festlegen, nicht nach Zwischenresultaten wechseln.

## 4. Zeitliche Gültigkeit und Widersprüche

- Ausschließlich Records desselben unveränderten Punkte-Regimes verwenden. `_stable` (`belief.py:535–540`), Spawnfenster und Widerspruchserholung werden nicht geöffnet oder verkürzt. Kein zusätzliches `spawn_proof`, keine Orakel-/Engine-Wahrheit im Solver.
- Im kleinsten Entwurf Gauß bei eingeschaltetem `window_infer` oder `window_infer_all` vollständig deaktivieren. Die bestehenden Records tragen keine Herkunfts-/Epochentags; sonst könnten frühe Window-Records unbemerkt in eine spätere Eliminierung geraten. Das ist eine konservative Einschränkung, keine neue Gültigkeitsbehauptung für diese früheren Regeln. V14 nutzt sie ohnehin nicht.
- Matchreset und `_reopen_dead` löschen bereits Records. Sämtliche Gauß-Cache-/Aufrufzustände dort ebenfalls verwerfen. Beim Wiederöffnen alter Nullfelder durch neu entdeckte Relics jeden normalisierten Cache verwerfen; keine alten fertig gerechneten Matrizen weiterverwenden. Persistente positive Fakten behalten exakt die bestehenden Regeln.
- Vor Matrixbau jede Zeile gegen aktuelles Punkt-/Nullwissen normalisieren und Restkapazität prüfen. Gleiche linke Seite mit verschiedenem Rest, eine Nullzeile mit von null verschiedenem Rest oder ein exakt festgelegter Variablenwert außerhalb {0,1} macht die Komponente unverwendbar: **keine neuen Fakten dieser Komponente**. Nicht `_propagate` als Validator missbrauchen; dessen `<=0`/`>=len` akzeptiert selbst keine verlässliche Inkonsistenzdiagnose.
- Auch direkte/symmetrische Konflikte der gesamten fertig gesammelten neuen Fakten gegen vorhandenes Wissen und gegeneinander prüfen. Erst danach atomar übernehmen. Bei abgebrochener oder noch nicht vollständig reduzierter Matrix keine teilweise gesammelten Fakten herausgeben.
- Rationale Konsistenz beweist keine binäre Lösbarkeit. Es gibt keinen vollständigen Binär-Konsistenzcheck in diesem Entwurf. Sicherheit der Fakten ist konditional auf tatsächlich gültige Beobachtungen und korrektes bisheriges Wissen, genau wie bei Subset/Overlap. Ein Shadow-Wahrheitscheck ist deshalb weiterhin Pflicht vor einem Kandidaten, aber seine Wahrheit darf niemals Solverinput sein.

## 5. Harte, deterministische Größen- und Arbeitsgrenzen

Vorschlag für den ersten technischen Pilot, vor jeglicher Stärkenmessung unveränderlich festzulegen:

| Grenze | Vorschlag / Verhalten |
|---|---|
| Gesamter eingelesener Recordbestand | höchstens vorhandene 400 Records; keine Matrix 400×576 |
| Eingaberecord | höchstens 16 physische Tiles; größere abgeleitete Aggregatzeilen konservativ auslassen |
| Komponentenbau | Variablen↔Record-Inzidenz, höchstens 400×16 Einträge; nur die von der neuen Gleichung berührte Komponente |
| Matrix | höchstens 24 Orbit-/Tilevariablen und 40 verschiedene gültige Gleichungen |
| Überschreitung | ganze betreffende Komponente überspringen; kein ergebnisabhängig gewählter 24er-/40er-Ausschnitt |
| Aufwand pro Aufruf | höchstens 4096 rationale Zelloperationen, danach kompletter ergebnisloser Abbruch |
| Bruchgröße | Zähler und Nenner höchstens 256 Bit; bei Überschreitung kompletter ergebnisloser Abbruch |
| Aufrufrate | neue unterschiedliche gültige Gleichung, mindestens 8 Beobachtungsschritte Abstand, höchstens 8 Versuche je Match |
| Auswahl bei mehreren berührten Komponenten | maximal eine, vorab deterministische Reihenfolge (z. B. kleinste Repräsentanten-ID) |
| Zusatzabschluss | keine Gauß-Rekursion auf gerade bewiesenen Fakten; nur vorhandene Propagation danach |

Bei 24 Pivots, 40 Zeilen und 25 einschließlich RHS Spalten könnte ungebremste dichte RREF ungefähr 24.000 Zellenupdates benötigen. Die zusätzliche Operationsgrenze ist deshalb wesentlich: 24/40 allein ist kein plausibles kleines Laufzeitbudget für Python-Fraction. Deterministisch zählen auch Pivotnormalisierungen als Zelloperationen; Produkt/Division/subtraktive Aktualisierung müssen vor weiterer Arbeit budgetiert sein. Für den ganzen Match ergeben sich maximal 32.768 zugelassene Zelloperationen, zuzüglich begrenztem Komponentenbau und Index-/Pivotarbeit. Der GCD-/Integeraufwand wird zusätzlich durch die Bitgrenze beschränkt. Das ist eine strukturelle CPU-Grenze, **keine hier gemessene Millisekundengarantie**.

Ein Wallclock-Timeout pro Aktion wäre zwar schnell eingebaut, würde aber die Fakten und damit Aktionen unter unterschiedlicher Rechnerlast verändern. Das verletzt die gewünschte Wiederholbarkeit. Deshalb deterministische Arbeits-/Bit-/Aufrufgrenzen im produktiven Kandidaten; tatsächliche Maximalzeiten später getrennt messen und Kandidaten verwerfen, falls sie nicht in den vorhandenen Laufzeitrahmen passen. Keine adaptive Budgeterhöhung nach Ergebnissen.

Wenn Komponenten aus dem vollständigen gewählten Recordbestand zu groß werden, nicht heimlich nur die ersten 40 passenden Gleichungen als vermeintlich vollständige Komponente ausgeben. Ein ausdrücklich vorab definierter Record-Teilbestand liefert zwar logisch weiterhin nur Folgerungen aus wahren Teilgleichungen, erschwert aber Inkonsistenz-/Reichweitenaussagen; der erste Entwurf sollte größere Komponenten schlicht auslassen.

## 6. Minimaler Folgeauftrag, nur falls Root ihn neu freigibt

1. In getrennter Arbeitskopie eine reine kleine Elimination mit den obigen festen Caps entwerfen, Default aus. Das Fünf-Feld-Beispiel in beiden Restvarianten sowie unabhängige erschöpfende binäre Miniuniversen, Symmetriekoeffizient 2, Rangmangel, Widersprüche, Reset und Budgetabbruch prüfen. Dies ist hier nur ein Prüfentwurf; nichts davon wurde ausgeführt.
2. Zuerst Shadow auf einem vorab festgelegten vorhandenen Diagnosetrace: zusätzliche **0/1-Fakten gegenüber Subset+Overlap**, ihre Vorlaufzeit, falsche Fakten, ausgelassene/abgebrochene Komponenten und tatsächliche maximale CPU-Zeit. Fehlen über Overlap hinaus zusätzliche nützliche Fakten oder reißen die Kosten den Rahmen, Ansatz sofort verwerfen.
3. Erst bei ausreichendem Mechanismussignal und Restzeit eigener frischer Vorabplan für genau einen Kandidaten, getrennte Auswahl/Bestätigung. Keinen gescheiterten A/B/C-Bestätigungsblock wiederverwenden und kein Nachrücken in dessen Nominierungsregel. Dieser Bericht reserviert nichts und schafft selbst keine Messfreigabe.

**Fazit für Root:** Der zusätzliche mathematische Mehrwert ist mit einem sehr kleinen erfüllbaren Gegenbeispiel belegt. Praktische Häufigkeit, Laufzeit und Gewinn bleiben unbekannt. Begrenzte Gauß-Elimination ist deshalb eine plausible Reserve, aber kein begründeter sofortiger Ersatz für den laufenden Versuch und keine Rechtfertigung für einen großen Solver vor dem Battle.
