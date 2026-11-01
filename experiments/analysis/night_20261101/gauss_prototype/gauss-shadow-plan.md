# Vorabentwurf: getrennte A-/G-Schattenprobe auf unverändertem V14

**Status: Entwurf, kein Job freigegeben oder gestartet.** Keine neuen Seedreservierungen und keine Gewichts-/Abgabeänderungen. Umsetzung/Start erst nach ausdrücklicher Rootentscheidung, ausschließlich wenn die derzeitige feste A/B/C-Auswahl **keinen Nominee** ergibt und die vollständige Probe noch in die Zeit-/Ressourcengrenzen passt. Nach einer gescheiterten Bestätigung eines nominierten Kandidaten ist dies **kein Nachrücken** und keine zweite Chance innerhalb derselben Studie. Ein eventueller späterer Stärkenvergleich braucht einen eigenen frischen Vorabplan.

## Zweck und feste Eingaben

Technisch prüfen, ob der begrenzte exakte Solver auf denselben öffentlichen Beobachtungen zusätzliche sichere 0/1-Information **gegenüber V14 und gegenüber A** liefert und was beide Inferenzarten kosten. Kein Gegenfaktum zur Spielstärke, da ausschließlich V14 handelt.

- Dieselben bereits für Diagnose verwendeten **40 Karten 830000–830039**, beide Seiten: genau **80 vollständige Spiele** gegen Solution_92. Diese Karten werden ausdrücklich nicht als neue unabhängige Stärkenbestätigung bezeichnet.
- V14-Referenz exakt SHA-256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`, 36 Netze, train=False, kein Lernen/Autosave. Existenz und Hash vor Start prüfen; kein zufälliger Ersatz.
- Lauf ausschließlich aus dem später von Root freigegebenen Followup-Checkout. Vor Start konkrete HEADs sowie Hashes aller runtimeabhängigen Agent-/Solver-/Diagnose-/Oracle-/Gegner-/Engine-Dateien, Interpreter und Gewichte einfrieren. Aktueller uncommitteter Prototyp ist noch keine eingefrorene Ausführungsidentität.
- Höchstens ein Probeprozess; erst starten, wenn dafür ein Modellworker frei ist und Netzbetrieb/Restzeit passen. Probe muss vollständig bis zur vorgesehenen Schlussreserve enden können. Keine parallele Vollsuite.

## Drei getrennte Beliefs, genau ein handelnder Agent

| Belief | Rolle | overlap_infer | gauss_infer |
|---|---|---:|---:|
| V | Original-Belief des tatsächlich handelnden V14 | false | false |
| A | unabhängige vollständige Kopie des zurückgesetzten V-Beliefs | true | false |
| G | zweite unabhängige vollständige Kopie desselben zurückgesetzten V-Beliefs | false | true |

Alle übrigen Eigenschaften/Schalter identisch. **Keine A+G-Kombination.** Nach jedem regulären `new_game` neu kopieren; eventuell mitkopierte instanzgebundene Diagnose-Observer entfernen. Die nachfolgende öffentlich bekannte Sensorreichweite identisch übertragen. Die beiden Shadows benutzen ihre eigene Recordhistorie, Markiermengen, Reset-/Attemptzustände und Cacheobjekte.

Ein frisches öffentliches obs verarbeitet der Observer in dieser festen Reihenfolge: `V.original_observe(obs)`, `A.observe(obs)`, `G.observe(obs)`. Das schafft parallele Erkenntnispfade, keine zusätzlichen handelnden Agenten. Keiner der Shadows schreibt in V oder den anderen Shadow. Keine zusätzlichen Zufallsziehungen. Die Aktion wird anschließend ausschließlich aus dem Originalagenten/V-Belief erzeugt. Kein Shadow-State gelangt in Zielwahl, Features, Maske, Reward oder Aktionen.

Bei idempotent erneut aufgerufenem Observer keine weitere logische Beobachtung zählen. Matchreset-Beobachtungen regulär an alle drei Beliefs reichen, aber nicht als Nichtreset-Informationsschritt zählen. G muss seine acht Versuche/Acht-Beobachtungen-Abstände und alle Matrix-/Operations-/Bitcaps unverändert einhalten.

## Wahrheit ausschließlich als nachgelagerter Validator

Erst nachdem **alle drei** Beliefs obs verarbeitet haben, die tatsächliche Karte mit der bestehenden `truth_maps(env.state)`-Diagnosefunktion lesen. Bei player_1 korrekt in den kanonischen Raum spiegeln. Wahrheit nur mit bereits abgeleiteten Punkt-/Nullfakten vergleichen, niemals ins Gedächtnis einspeisen. Das gilt sowohl für A als auch G und für neu auftauchende wie fortbestehende Zusatzfakten.

Jedes zusätzliche positive Feld muss wahr positiv, jedes zusätzliche Nullfeld wahr null sein. Direkte Point-/Dead- und Spiegelfaktkonflikte protokollieren. Bereits ein falscher Zusatzfakt verwirft den Prototyp technisch; Ausgabe mit Fehlerbeleg erhalten. Keine laufende Reparatur, keine Seedänderung und kein Fortsetzen unter verändertem Code. Ein vorzeitiger Abbruch ist als unvollständige Diagnose auszugeben.

## Vorab festgelegte Informationsmetriken

Alle Mengen getrennt für positive und Nullfakten berechnen:

- **A gegen V:** `A \ V`, außerdem `V \ A`.
- **G gegen V:** `G \ V`, außerdem `V \ G`.
- **G gegen A:** `G \ A`, außerdem `A \ G`.
- **Strenger inkrementeller G-Mehrwert:** `G \ (V ∪ A)`. Damit werden im G-gegen-A-Wert keine Fakten als neu bezeichnet, die V bereits kennt und A gerade nicht enthält.

Für jede Richtung: einzigartige (Matchindex,Tile)-Fakten pro Spiel, Fakt-Schritte, erste zusätzliche Beobachtung und Dauer bis V/A gegebenenfalls denselben Fakt kennen. Reale Vorlaufzeiten anhand gespeicherter Zeitpunktspuren berechnen; bei fehlendem Nachholzeitpunkt zensiert ausweisen, keine erfundene durchschnittliche Beschleunigung. Zahl Spiele **und Karten** mit Zusatzinformation getrennt berichten. Keine Annahme, dass einer der drei Beliefs stets eine Obermenge der anderen ist.

Neu gespeicherte faktbezogene Diagnosespur soll mindestens `(seed,side,match,obs_step,kind,tile,which_beliefs,truth)` tragen. So lassen sich die Zählung und die aufgezeichnete Wahrheitsprüfung unabhängig nachzählen; die frühere Probe speicherte hierfür nur Aggregatsummen. Diese Daten sind reine Ausgaben und dürfen nicht wieder als Agentinput verwendet werden.

## Kosten ohne verhaltensabhängigen Timeout

Für V, A und G jeweils Beobachtungsdauer pro frischem Nichtreset-Step separat messen, zusätzlich Kopier-/Setupzeit je Spiel. Pro Spiel und insgesamt Median, 95%-Quantil, Maximum und Gesamtzeit ausgeben; G−V, A−V und G−A aus denselben Beobachtungen deskriptiv vergleichen. Reihenfolge ist fest V/A/G, daher Cache-/Schedulingeffekte als Messgrenze nennen. Kein behaupteter harter Echtzeitbeweis und keine automatische Erhöhung der Solverbudgets.

Aus Gs bestehendem Zustandsübergang die tatsächlichen Attemptzuwächse je Match zählen, ebenso produktive Beobachtungen und unveränderte Caps bestätigen. Der aktuelle Helper gibt für „keine Fakten“, „zu groß“, „Widerspruch“ und „Budgetabbruch“ jeweils `{}` zurück. Ohne vorab separat geprüfte rein diagnostische Instrumentierung diese Gründe **nicht** auseinanderrechnen oder erraten. Der reine Mikrobenchmark und die deterministischen Strukturgrenzen bleiben eigene Belege; zusätzliche Kosten im echten Beobachtungsstrom sind hier der Prüfgegenstand.

## Vollständigkeit, Provenienz und Abnahme

Vor Start erwartete 80 Seed-/Seiten-Schlüssel festschreiben. Je Spiel speichern: normalen `play_game.steps`-Wert **303 Engine-Übergänge** separat von **300 frischen Nichtreset-Beobachtungen**, drei Matchreset-Beobachtungen, Ergebnis nur als Beleg des handelnden V14 sowie die obigen Informations-/Kostenfelder. Kein Vergleich von A-/G-Siegraten, da sie nicht handeln.

Nach Lauf Exitcode, exakte Schlüsselvollständigkeit, Duplikate, endliche/nichtnegative Kosten, alle Summen und Faktspuren, 303/300-Einheiten sowie sämtliche Vorher-/Nachher-Hashes unabhängig prüfen. Outputhash und Ausführungscommand im Root-Receipt archivieren. Bei Quellenbruch, fehlenden Schlüsseln, falschen Zusatzfakten oder Abbruch keine nachträgliche Auswahl schöner Teilmengen.

**Technische Auslegung:** Ohne strikten sicheren G-Mehrwert gegenüber `V ∪ A` den Gauß-Prototyp für diese Nacht verwerfen. Bei zusätzlicher Information ausschließlich „zusätzliche sichere Fakten beobachtet“ melden; Informationsverluste gegenüber A/V und Kosten ebenso offen ausweisen. Positive Diagnose ist keine Kandidatennominierung und kein Nachweis stärkerer Spielweise. Root beurteilt Vollständigkeit/Kosten separat und entscheidet erst danach, ob eine neue, eng getrennte, vorher frisch geplante Studie überhaupt sinnvoll und zeitlich möglich ist.
