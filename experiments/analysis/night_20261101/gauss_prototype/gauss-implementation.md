# Begrenzte exakte Inferenz – Umsetzung / RED / GREEN

Arbeitskopie ausschließlich `/Users/moayedshawesh/Desktop/KI/sherlock-november-followup`, Branch `improvement/november-followup-20261101`, Ausgang `f6c27ce`. Kein Commit dieses Agenten. Die laufende A/B/C-Auswahl im anderen Worktree wurde nicht verändert.

**Stand: technisch implementierter, fokussiert geprüfter Prototyp; kein zugelassener Stärkekandidat.** Unabhängiges Review ohne Blocker liegt vor und Main-Flagübergabe ist nach Rootfreigabe ergänzt. Tatsächliche Kosten in Agenten-/Shadow-Beobachtungsfolgen, echte Agentprüfung, Aktionskompatibilität und zusätzlicher Shadow-Mehrwert sind noch offen. Keine Spiele, Trainings, neuen Seeds, Torchmodelle, Luximporte oder Vollsuite gestartet.

## Eigentumsdateien

- Neu `agents/sherlock/exact_infer.py` (126 Zeilen): reine Funktion `exact_facts(records,touched,*,point=(),dead=(),mirror=None)` und private Fraction-RREF; Standardbibliothek ausschließlich Counter/Fraction.
- `agents/sherlock/belief.py`: opt-in `gauss_infer=False`, gleiche gültige eigene/gegnerische Gleichungspfade; nach bestehender Propagation maximal ein kleiner Solverversuch; Übernahme nur fertiger Fakten über bestehende `_mark_*` und Propagation.
- `agents/sherlock/config.py`: neuer Bool mit Default false / bestehendem Config-Roundtrip.
- Neu `tests/test_exact_inference.py` (251 Zeilen, 25 Testfälle einschließlich Parametrisierungen).
- `main.py` nach separater Rootfreigabe um genau die Konstruktorweitergabe `gauss_infer=self.cfg.gauss_infer` ergänzt. Ein echter Agenttest wurde weiterhin nicht ausgeführt.
- Paketfilter, Gewichte und alle anderen Dateien unverändert.

## Begrenzung und Semantik

Der Helper liest höchstens 400 Records mit je höchstens 16 physischen Tiles. Überlange Rohrecords werden vor Setexpansion ausgelassen. Normale Beobachtungen enthalten maximal 16 eindeutig besetzte physische Tiles; die Auslassung größerer abgeleiteter Aggregatzeilen ist eine konservative Einschränkung.

Bekannte positive/Nullwerte werden vor Matrixbau normalisiert. Symmetrieorbits verwenden `min(f,M(f))`, aber erhalten die Anzahl physischer Belegungen als Koeffizient: gleichzeitig f und M(f) besetzt bedeutet **2*x**, nicht x. Bekannte positive Werte werden mit voller Multiplizität abgezogen. Inputobjekte bleiben unverändert.

Die normalisierten Zeilen werden deterministisch sortiert und identische Gleichungen dedupliziert. Aus der kleinsten berührten Variablen wird genau eine vollständige verbundene Komponente gebildet. Bei mehr als 24 Variablen oder 40 verschiedenen Zeilen wird sie vollständig übersprungen; keine willkürliche Matrixtrunkierung und keine alternative Komponente nach einem Fehlschlag.

RREF verwendet ausschließlich Fraction. Jede Pivotnormalisierung und jede Eliminations-Zellaktualisierung zählt gegen **4096 Zelloperationen pro Versuch**; vor der nächsten Operation wird abgebrochen, wenn das Budget verbraucht ist. Zähler und Nenner jedes Ausgangs-/gespeicherten Zwischenwerts sind auf **256 Bit** begrenzt. Nach Abbruch gibt es keinerlei partiellen Rückgabefakten. Es gibt keinen Wallclock-Test im Produktionscode.

Reviewpräzisierung **P3** (`gauss-code-review.md`): Das separate temporäre Fraction-Produkt innerhalb `row[j] - factor * matrix[rank][j]` wird **nicht** vor der Subtraktion einzeln auf 256 Bit geprüft. Garantiert ist die Grenze für geprüfte/gespeicherte Matrixwerte, nicht für jeden erzeugten rationalen Zwischenwert. Ein Eliminations-Zellupdate enthält außerdem Multiplikation und Subtraktion; 4096 Zellupdates sind keine 4096 einzelnen Fraction-Operatoraufrufe. Root hat die dokumentierte Einschränkung akzeptiert; keine Produktivänderung hierzu.

Nur vollständige RREF-Zeilen mit einer einzigen nichtnull Variable und exakt festem Wert 0 oder 1 werden Fakten. Freie Variablen werden nie belegt oder gerundet. Eine Nullzeile mit nichtnull Rest, gleiche linke Seite mit widersprüchlichem Rest oder ein isolierter fester Nichtbinärwert verwirft die ganze Rückgabe. Konflikte vorhandener positiver/Nullwerte einschließlich Symmetrie werden vor dem Matrixbau abgefangen.

**Diese Widerspruchsprüfung ist rationale lineare Konsistenz plus Erkennung isolierter Nichtbinärwerte, kein allgemeiner binärer SAT-/Machbarkeitsnachweis.** Manche rational lösbaren, binär unmöglichen Systeme bleiben unerkannt. Die Sicherheit der neuen Aussagen gilt unter der bestehenden Voraussetzung gültiger Beobachtungsgleichungen und korrekten Vorwissens. Ungültige Eingangszeilen außerhalb der schließlich ausgewählten Komponente dürfen konservativ ebenfalls den ganzen Aufruf verwerfen; das kostet Schlüsse, erzeugt keine neuen Behauptungen.

## Beobachtungs-/Matchbudget

- Frische Nichtreset-Beobachtungen zählen einmal; idempotente zweite `observe`-Aufrufe zählen nicht.
- Maximal acht tatsächliche Versuche pro Match, mindestens acht gezählte Beobachtungen Abstand. Fehlgeschlagene oder zu große Komponenten kosten ebenfalls ihren Versuch.
- Nur neue unterschiedliche Gleichungen; maximal 400 Seen-Signaturen. Kein Matrixcache über Beobachtungen.
- Spiel-/Matchreset setzen Budget und Abstand zurück.
- **`_reopen_dead` und neue Relics leeren nur Seen-Signaturen; sie füllen das Attemptbudget nicht auf und setzen den Mindestabstand nicht zurück.**
- `_stable` bleibt unverändert. Bei `window_infer` oder `window_infer_all` ist Gauß vollständig deaktiviert. Kein neuer Spawn-Beweis, kein Orakelinput.
- Nach Übernahme nur vorhandene Propagation; keine rekursive Gauß-Abschlussschleife.

## RED vor Produktivcode

Interpreter `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python`, cwd Followup-Worktree:

```text
python -B -m pytest -q tests/test_exact_inference.py \
  -k 'five_tile_fact_is_new_beyond_subset_and_overlap or config_and_constructor_default_off'
3 failed, 19 deselected in 4.41s
```

Erwartete echte Assertionfehler: beide erfüllbaren Fünf-Feld-Varianten beweisen e=0/e=1 im bisherigen Subset+Overlap-Code nicht; fehlender Configschalter wird nicht übernommen. Kein Import-/Setupfehler. Log `/tmp/sherlock-night-20261101/gauss-red.log`.

## GREEN und gezielte Nachherprüfung

Erster kompletter Exact-Lauf: **22 passed in 3.82s**, Log `gauss-green.log`. Danach reine zusätzliche Grenz-/Symmetrieprüfungen ergänzt. Eine Kostenregression setzte zunächst fälschlich unsortierte private Matrixreihenfolge und sortierte Helperreihenfolge gleich (1 failed, 36 passed in 4.05s). Der tatsächliche 4096-Abbruch war im privaten Pfad korrekt; der sortierte Helper löste dieselbe Matrix billiger. Testannahme korrigiert, keine Produktivänderung dafür.

Abschließend frisch ausgeführt:

```text
python -B -m pytest -q tests/test_exact_inference.py tests/test_belief.py
37 passed in 3.28s
```

Log `/tmp/sherlock-night-20261101/gauss-focused.log`. `git diff --check` ohne Befund. Vollsuite bewusst nicht ausgeführt: Root hat parallele Modelljobs und eine zentrale spätere Verifikation vorgegeben.

Nach der separat freigegebenen Main-Weitergabe: `ast.parse` für Main/Belief/Config/Exact (vier Dateien, keine Projekt-/Modellimports) erfolgreich; derselbe bestehende reine Testaufruf erneut **37 passed in 3.90s**, Log `/tmp/sherlock-night-20261101/gauss-wiring-pure.log`. Das bestätigt Syntax und den reinen Unterbau, keine echte Agentinitialisierung oder Aktionsgleichheit.

## Was konkret geprüft wurde

- Fünf-Feld-Mehrwert e=0/e=1 gegenüber Subset+Overlap; alle 24 Reihenfolgen des reinen Gleichungssystems in beiden Varianten.
- Sämtliche binär kompatiblen Systeme aus drei verschiedenen Teilmengen eines Drei-Variablen-Universums, unabhängig gegen alle acht binären Belegungen. Kein Produktionsschritt berechnet die erwarteten Werte.
- Zusätzlich sämtliche kompatiblen Systeme aus zwei verschiedenen physischen Teilmengen von vier Tiles mit zwei Spiegelorbits; unabhängige vollständige Zwei-Bit-Belegungen prüfen die Multiplizitäten.
- Freie Variablen, leere/disjunkte Komponenten, deterministische Wahl nur einer Komponente, unveränderte Eingaben und Deduplizierung.
- Koeffizient 2 für doppelt besetzte Spiegeltilepaare, Spiegelachse, Abzug bekannter positiver Multiplizität und vorhandene Spiegel-Faktübernahme im echten Belief.
- Negative/zu große Reste, gleiche linke Seite mit verschiedenem Rest, rational eindeutige 1/2-Werte zusammen mit einem sonst positiven Fakt: keinerlei Teilfakten.
- 25-Variablen-/41-Zeilen-Komponenten vollständig übersprungen; übergroße Rohrecords nicht expandiert; Record 401 nicht verwendet.
- Gezielte Operations-/Bitbudgetabbrüche und ein echter dichter 24-Variablen-Grenzfall, der die unveränderte 4096-Grenze im privaten Eliminationspfad erreicht. Kein Realzeitbenchmark daraus abgeleitet.
- Fresh-/Reset-Zählung, Spawn-/Window-Sperren, acht Versuche trotz wiederholtem `_reopen_dead`, Mindestabstand, Match-/Spielreset und Seen-Invalidierung durch Relics ohne Budgetauffüllung.

## Erlaubter reiner Fraction-Mikrobenchmark

Nach Stabilmeldung des Diffs auf ausdrückliche Rootfreigabe ein kleiner Lauf ausschließlich des Helpers. Er wurde während der von Root mit zwei Evaluationsworkern gemeldeten laufenden Auswahl durchgeführt. Kein Modell und keine Engine importiert. Insgesamt **1,005 CPU-Sekunden / 1,007 Wallclock-Sekunden**, 162 Wiederholungen je Fall; jede Rückgabe gegen die vorab bekannte Lösung geprüft.

| Fall | Median ms | Maximum ms |
|---|---:|---:|
| Fünf-Feld-Gegenbeispiel | 0,079 | 0,218 |
| Dichte lösbare 24-Variablen-Komponente | 1,990 | 3,604 |
| 400 Rohrecords mit Deduplizierung auf diese Komponente | 4,013 | 4,752 |
| Abgelehnte 25-Variablen-Komponente | 0,073 | 0,132 |

Rohbeleg `/tmp/sherlock-night-20261101/gauss-microbenchmark.json`. Das sind wenige feste synthetische Eingaben unter der gemeldeten Hintergrundlast, **kein harter Echtzeitbeweis**, keine vollständige Worst-Case-Suche und kein Shadow-Nachweis. Produktionsentscheidungen hängen weiterhin ausschließlich von deterministischen Operations-/Bit-/Größengrenzen ab, niemals von den hier gemessenen Zeiten.

## Nächste Schritte ausschließlich durch Root

Zentraler echter Agent-/Paketcheck. Gegebenenfalls danach ausdrücklich freigegebener Shadow-Nachweis zusätzlicher sicherer Fakten **über Subset+Overlap hinaus** einschließlich tatsächlicher Agenten-/Beobachtungskosten. Ein Vorabentwurf liegt unter `/tmp/sherlock-night-20261101/gauss-shadow-plan.md`; er startet keinen Job und schafft selbst keine Messfreigabe. Ohne solchen Mehrwert oder bei nicht tragbaren Kosten verwerfen. Keine neue Stärkenmessung oder Übernahme durch diesen technischen Task autorisiert.
