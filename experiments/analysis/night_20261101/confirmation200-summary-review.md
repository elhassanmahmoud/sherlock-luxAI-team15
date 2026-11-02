# Review: externe 200-Karten-Bestätigungsauswertung

Gegenstand ist ausschließlich der Diff zwischen dem eingefrorenen `experiments/analysis/night_20261101/summarize.py` und `/tmp/sherlock-night-20261101/confirmation200-summary.py`, plus der vorab geschriebenen Zeitänderung. Keine Leistungsdaten gelesen, keine Auswertung, Tests, Spiele oder Modelljobs gestartet und keine Worktree-Datei verändert.

**Nach scoped Nachprüfung: kein verbleibender blockierender Anpassungsbefund.** Freigegebener geprüfter Tool-SHA:

`83430c9f2b8aadede9da807d88026c2416b07b89a5d2eccbac28ce8829216c4d`

Der zuerst gefundene Fehler `promotion_qualified` prüfte noch auf den nun unzulässigen Phasennamen `confirmation` und wäre immer false gewesen. Root hat ausschließlich diese Zeile auf den direkt geprüften `passed`-Wert korrigiert. Die neue Datei wurde erneut gegen das eingefrorene Original diffweise gelesen und ihr vollständiger SHA unabhängig bestätigt. Sie war laut Root zuvor noch nicht gepinnt oder ausgeführt.

## Bestätigte Anpassung

- Ausschließlich Phase `confirmation200`; eigene Ausgabe-/Journalnamen, vorhandene Ausgabe wird nicht überschrieben.
- Für alle drei Jobs exakt200Karten. Referenz/Kandidat nutzen832000–832199; Direktduell nutzt833000–833199. Der unveränderte vollständige CSV-Validator erzwingt beide Seiten und alle sieben Panel/default-Gegner bzw. genau die V14-Direktreferenz. Daraus folgen2800+2800+400=**6000Spiele**, keine Auswertung einer willkürlichen Teilmenge.
- Exaktes neues lokales Sechserpanel unverändert; default bleibt Sicherheitsgegner außerhalb des Panelmittels.
- Original-Phasenhash, Gleichheit eingebetteter/originaler Phase, genaue Jobnamen und tatsächliche Commands bleiben gebunden. Der neue Confirmationmanifest muss vor den ersten Spielen gepinnt werden.
- Zeitnachtrag ist an den festen SHA `3319dcfa8cec9b979945cd6fe9e12fb41d5a53e2ccf7d41885450eae158e2aaf` gebunden. Manifest muss diesen SHA und den tatsächlichen SHA des externen Zusammenfassungstools tragen.
- Selection-Freeze-SHA wird über den neuen Manifest gebunden; Confirmation- und Selection-Freeze müssen als vollständige JSON-Identitäten gleich sein. Der unabhängige Prüfer wird zusätzlich den bereits vor Auswahl fest gepinnten Selection-Freeze-SHA verlangen.
- Der Selection-Summary-SHA und sein einziger Nominee müssen exakt zum Confirmationmanifest passen. Keine neue Wahl und kein Nachrücken. Alle erwarteten Jobs sind baseline, genau dieser Kandidat und sein Direktjob.
- Sämtliche numerischen Bestätigungsgates sind byteinhaltlich unverändert: Paneldelta≥1pp und untereGrenze>0; Solutiondelta≥0 und untereGrenze≥−1pp; default≥99% und Delta≥−1pp; Direktuntergrenze>50%. EPS bleibt1e-9.
- Bootstrap bleibt identisch: ganze Karten einschließlich beider Seiten und bei Panel alle sechs Gegner,5000Ziehungen, RNG0,2,5/97,5Perzentile.200 statt300 unabhängige Karten schwächen die Präzision; keine stärkere Evidenzbehauptung.

Der Zeitnachtrag dokumentiert Erklärung und Zeitpunkt21:33:45UTC, als laut deklarierter Zustandsaufnahme nur der erste Baselinejob gestartet und noch kein Job fertig war. Die Aussage „keine Leistungsdaten gelesen“ stammt aus dieser vorab geschriebenen Erklärung und Roots Auftrag, nicht aus einer jetzigen Datenprüfung.

## Weiteres Vorgehen

Die unabhängige CSV-/NumPy-Bestätigungsprüfung wird außerhalb des Worktrees vorbereitet. Ihr späterer Pin-Schritt muss nach vollständig geprüfter Nominierung und **vor Existenz eines Confirmation-Journals/ersten Spiels** den tatsächlichen200erManifest, Selection-Summary, Nachtrag, Tool und Freeze binden. Jetzt wird kein Kandidat gesetzt und kein noch nicht existierender Confirmationmanifest vorgetäuscht. Ausführung des Audits erst nach vollständigen6000Spielen.

## Vorbereiteter unabhängiger Prüfer

`/tmp/sherlock-night-20261101/confirmation200-independent-audit.py` ist erstellt. Nur statisch syntaktisch geprüft; weder importiert/ausgeführt noch an einen Kandidaten oder einen noch nicht geschriebenen Manifest gebunden. Keine Bestätigungs-/Auswahlergebnisse gelesen.

Zwei ausdrücklich getrennte Schritte, beide mit demselben vorhandenen Python-Interpreter:

```sh
# ERST nach vollständiger, unabhängig geprüfter Auswahl und vor dem ersten Confirmation-Journal:
python -B /tmp/sherlock-night-20261101/confirmation200-independent-audit.py pin \
  --manifest /Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics/experiments/analysis/night_20261101/confirmation200_jobs.json \
  --selection-audit /tmp/sherlock-night-20261101/selection-independent-audit.json \
  --out /tmp/sherlock-night-20261101/confirmation200-audit-pin.json

# ERST nach vollständigen 6000Spielen und offizieller Zusammenfassung:
python -B /tmp/sherlock-night-20261101/confirmation200-independent-audit.py audit \
  --pin /tmp/sherlock-night-20261101/confirmation200-audit-pin.json \
  --out /tmp/sherlock-night-20261101/confirmation200-independent-audit.json \
  --compare-summary /Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics/experiments/analysis/night_20261101/confirmation200_summary.json
```

Pin verweigert Existenz eines Confirmation-Journals oder einer Ergebnisdatei. Er verlangt einen tatsächlich qualifizierten einzigen Nominee, Übereinstimmung des offiziellen und unabhängigen Selectionberichts, die gepinnten bisherigen Phasen-/Freeze-SHAs, den korrigierten Toolhash und den festen Nachtrag. Erst dann schreibt er den tatsächlichen Confirmationmanifest-SHA und seinen eigenen Auditorhash außerhalb des Worktrees.

Der spätere Audit prüft erneut alle Bindungen und unveränderte eingefrorene Quellen/Weights, genaue Commands, vollständig200Karten und beide Seiten pro Job, endliche und kohärente CSVs sowie6000Spiele. Er berechnet Kartenmittel, Bootstrap und sämtliche unveränderten Bestätigungsgates selbst mit NumPy; keine Repository-Statistik-/Torch-/Luximports. Der unabhängige Checker verlangt dieselbe komplette Weightinventarliste wie Selection, damit die deklarierte Freeze-Identität tatsächlich vergleichbar bleibt. Optionale offizielle Vergleichsprüfung gleicht Zahlen/Intervalle mit1e-12Toleranz und boolesche Entscheidung exakt ab. Kein automatischer Abgabetausch.
