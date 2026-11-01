# Unabhängiger Review des begrenzten Gauß-Prototyps

Arbeitskopie `/Users/moayedshawesh/Desktop/KI/sherlock-november-followup`, bestätigter HEAD `f6c27ce`. Gelesen: vollständiger Reviewbrief/Spec und Plan in `gauss-review-brief.md`, Implementierungsbericht, Reviewdiff, aktuelle `exact_infer.py`, die geänderten Belief-/Configpfade sowie die neuen Tests. Keine Datei im Checkout verändert.

**Spec-Verdikt:** Der reine Solver und die Belief-Anbindung erfüllen den vereinbarten technischen Prototypen weitgehend. Keine blockierende mathematische oder zeitliche Unsoundness im vorgesehenen gültigen Beobachtungspfad gefunden. Eine präzise Minor-Grenze der Bitbudgetaussage ist unten dokumentiert. Die ausdrücklich von Root zurückgestellte Main-Flagübergabe ist kein unerlaubt fehlender Arbeitsschritt dieses Reviewpakets.

**Qualitäts-/Zulassungsverdikt:** Für den separaten technischen Prototyp reviewbar; noch kein zugelassener Agenten-/Stärkekandidat. Main-Wiring, zentraler Kompatibilitäts-/Paketcheck, CPU-Mikrobenchmark und zusätzlicher Shadow-Mehrwert gegenüber Subset+Overlap bleiben die bereits vorgegebenen Folgeschritte. Die laufende A/B/C-Auswahl bleibt davon unabhängig. Dieser Review behauptet weder stärkere Spielweise noch gemessene Aktionslatenz.

## Ein konkreter Minor-Befund: Bitlimit schützt Matrixwerte, nicht jedes rationale Zwischenprodukt

**[P3] `agents/sherlock/exact_infer.py:51`**

`check(row[j] - factor * matrix[rank][j])` validiert den fertig subtrahierten, normalisierten Fraction-Wert. Der separate Fraction-Wert von `factor * matrix[rank][j]` wird nicht geprüft. Das ist ein eigenständiges algebraisches Zwischenprodukt, nicht bloß ein internes GCD-/Integerdetail der Fraction-Implementierung. Die garantierte Aussage lautet somit: Eingabematrix und alle gespeicherten Matrixwerte haben höchstens MAX_BITS; eine strengere Aussage „jeder erzeugte rationale Zwischenwert bleibt unter MAX_BITS“ ist derzeit nicht implementiert.

Ein einziges erlaubtes reines Gegenbeispiel wurde in einem separaten Standardbibliotheksprozess ausgeführt (kein Testframework, Torch, Lux oder Spiel): MAX_BITS nur im geladenen Modul auf2 gesetzt und `_reduce` auf folgenden gültigen, erfüllbaren Koeffizienten angewandt:

```text
a +2b =2
2a+2b =2
```

Alle Eingabewerte haben höchstens2Bit. Beim Eliminieren entsteht das Fraction-Produkt2×2=4 mit3Bit; nach der Subtraktion2−4=−2 passt der gespeicherte Wert wieder in2Bit. Der Aufruf gibt korrekt `{a:0,b:1}` zurück. Ergebnis des Gegenchecks: `cap_bits=2, temporary_bits=3, result={0:0,1:1}`. Die Produktionskonstanten/Dateien wurden nicht geändert.

**Auswirkung/Einstufung:** Keine falschen Fakten und kein unbeschränktes Wachstum nachgewiesen. Produkte zweier bereits begrenzter Fraction-Werte sind weiterhin strukturell begrenzt; es gibt keinen Beleg, dass das reale256Bitlimit bei den zugelassenen kleinen ganzzahligen Beobachtungssystemen praktisch gerissen wird. Der Implementierungsbericht beschränkt seine Zusage bereits auf „Ausgangs-/gespeicherte Zwischenwerte“ und ist damit zutreffend. Der allgemeiner formulierte Specabschnitt muss dieselbe Einschränkung tragen, oder bei bewusst strenger Auslegung müsste das explizite Produkt vor der Subtraktion separat geprüft werden. **Keine große Fixschleife für Python-Fraction-interne Temporärintegers erforderlich.** Root kann die dokumentierte Matrixwertgrenze als Minor akzeptieren; ein genauerer Produktcheck wäre eine kleine spätere Präzisierung, keine Voraussetzung für den laufenden A/B/C-Versuch.

## Soundness und Vollständigkeitsgrenzen

- `exact_infer.py:17–67`: Rationale RREF ist korrekt aufgebaut. Jeder Pivot wird exakt normalisiert und aus allen anderen Zeilen entfernt. Nur fertige Zeilen mit genau einer nichtnull Variable und RHS exakt0/1 erzeugen Fakten. Freie Variablen werden nicht belegt; feste Fakten innerhalb rangdefizienter Systeme bleiben zulässig.
- Nullzeilen mit nichtnull RHS und feste Nichtbinärwerte verwerfen die gesamte Rückgabe. Die Facts werden erst nach vollständiger Reduktion zurückgegeben; ein späterer Widerspruch oder Budgetabbruch kann keine Teilmenge nach außen ausgeben.
- `exact_infer.py:80–98`: Bekannte Point-/Dead-Orbits werden zuerst normalisiert, ihr Konflikt wird abgefangen. Restkapazität, doppelte linke Seite mit anderem Rest und leere widersprüchliche Zeilen werden konservativ verworfen. Unverbundene ungültige Eingaben dürfen auch den ganzen Aufruf verwerfen; das kostet nur mögliche Fakten.
- `exact_infer.py:88–91`: Ein Set entfernt mehrfach besetzte **identische physische Tiles**, der Counter zählt danach die Symmetrieorbits. Zwei verschiedene spiegelbildliche physische Tiles werden dadurch korrekt zu Koeffizient2. Bekannte positive Orbits werden mit voller Multiplizität vom Rest abgezogen. Keine unzulässige Orbit-Set-Deduplizierung.
- Neue Faktvariablen sind kanonische Orbitrepräsentanten. Vorwissen wird in denselben Repräsentanten geprüft; unterschiedliche neue Werte desselben Orbits können nicht als zwei unabhängige Variablen entstehen. Die bestehenden `_mark_point`/`_mark_dead` übertragen Spiegelwissen. Im synchronen Beobachtungspfad ändert sich das Vorwissen während der reinen Solverfunktion nicht.
- Ein rational konsistentes, binär unmögliches System kann unerkannt bleiben. Das ist die ausdrücklich vereinbarte Unvollständigkeit. Sicherheit bleibt konditional auf gültigen Beobachtungsgleichungen und korrektem Vorwissen; keine SAT-/Orakelbehauptung.

## Deterministische Arbeitsgrenzen und Codequalität

- `exact_infer.py:85–87`: maximal400 Records; Rohrecords über16 physischen Einträgen werden vor Expansion ausgelassen. Die Belief-Pfade begrenzen ihren gespeicherten Recordbestand bereits auf400. Der Helper erzeugt keine große400×576Matrix.
- `exact_infer.py:99–124`: erst eindeutige normalisierte Zeilen, dann Variablen-/Zeileninzidenz, deterministisch kleinste berührte Variable und genau eine komplette Komponente. Bei41Zeilen oder25Variablen Abbruch der ganzen Komponente; kein günstiger Ausschnitt und keine alternative Komponente nach einem Abbruch.
- `exact_infer.py:38–51`: exakt höchstens4096 Pivotnormalisierungs-/Eliminations-**Zellupdates**, vor der nächsten Zelle geprüft. Ein Eliminationszellupdate enthält Multiplikation und Subtraktion; die Zahl ist keine Behauptung von4096 einzelnen Fraction-Operatoraufrufen. Graph-/Sortier-/Pivotarbeit ist zusätzlich vorhanden, durch die festen Strukturcaps aber begrenzt. Es gibt keine Wallclock-abhängige Entscheidung.
- `_Abort` zentralisiert Widerspruchs-/Budgetverwurf, die reine Funktion verändert ihre Eingaben nicht. Kleine getrennte Funktion ohne zusätzliche Abhängigkeiten ist für diesen Prototyp nachvollziehbar. Die Ausgabe `{}` unterscheidet momentan kein „keine Fakten“ von „Budgetabbruch“; eine spätere Shadow-Messung muss diese Fälle wie geplant extern erfassen oder gezielt instrumentieren. Das ist kein zusätzlicher heutiger Implementierungsauftrag.

## Zeitliche Gültigkeit und Default-off

- `belief.py:615–625`: Solver bleibt vollständig aus bei beiden Window-Schaltern und ohne `_stable`. Es wird kein Spawnfenster geöffnet und kein neuer Spawnbeweis eingeführt.
- `belief.py:233–246`: die bestehende Idempotenzprüfung steht vor dem neuen Beobachtungszähler. Reset-Beobachtungen zählen nicht mit.
- `belief.py:196–206`: Spiel-/Matchreset setzen Seen, Versuche und Abstand zurück; alte Gleichungen werden mit den bestehenden Resetregeln verworfen.
- `belief.py:475ff` sowie `805–817`: neue Relics und `_reopen_dead` leeren Seen-Signaturen, füllen aber weder die acht Versuche noch den Acht-Beobachtungen-Abstand auf. Es gibt keinen persistenten Matrixcache, der nach Wiederöffnung veralten könnte.
- `belief.py:623–637`: fehlgeschlagene/zu große tatsächliche Versuche verbrauchen Budget, höchstens8 pro Match. Rückgabe wird über bestehende Markiermethoden und anschließende bestehende Propagation übernommen; keine rekursive Gauß-Schließung.
- `config.py:83–85` und Belief-Konstruktor: Default false; der normale False-Pfad führt keine Elimination aus. Main-Wiring fehlt wie ausdrücklich beauftragt noch. Aktionsgleichheit eines fertig verdrahteten Agenten wurde durch diesen Review nicht behauptet.

## Prüfungen dieses Reviews

Keine unveränderten Tests erneut ausgeführt, keine Vollsuite, kein Torch-/Luximport, keine Modelle, Spiele, Seeds oder neuen Auswertungen. Die im Paket beschriebenen fokussierten Tests wurden gelesen, ihre grünen Zahlen nicht als eigene Läufe ausgegeben. Einziger Rechengegencheck war die oben beschriebene Zweizeilen-Fraction-Prüfung zum konkreten Bitgrenzenverdacht. Kein weiterer blockierender Befund gefunden.
