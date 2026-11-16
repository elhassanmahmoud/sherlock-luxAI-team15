# Wann unterscheiden sich R3 und V15 auf R3s zwölf Solution-Niederlagensitzen?

Auf **allen zwölf Sitzen** war der erste eigene Punkt in Match 2 bei R3 und V15 zum **gleichen Zug** öffentlich sichtbar. Bis Zug 25 hatte V15 dennoch auf **elf der zwölf Sitze** mehr eigene Punkte. Auf allen sieben Sitzen, an denen ein mit R3 verlorenes zweites Match mit V15 gewonnen wurde, besetzte V15 bis dahin bekannte Punktefelder über mehr Züge. Beide Versionen zusammengefasst über die zwölf Sitze gaben im selben frühen Zeitfenster jeweils nur **zwei** Schussbefehle ab.

Die Stichprobe umfasst alle R3-Niederlagen gegen Original-Solution im gemeinsamen 400-Karten-Vergleich. Es sind zwölf Sitze auf neun Karten. Drei Karten kommen mit beiden Sitzen vor. V15 gewann neun der zwölf vollständigen Spiele; auf 7158056/P1, 7158059/P0 und 7158234/P0 verloren beide. Beide Versionen spielten jeden Sitz neu bis zum letzten Schritt. **Alle 24 Partien** reproduzierten den archivierten Gewinner, beide Matchsiegsummen, beide vollständigen Punktesummen und 303 Schritte. [Sitzregister und Archivvergleich](../../movement_soft_20261115/shared_400/sitzvergleich/joined.csv) · [Alle neuen Endstände und Rohdatenhashes](summary.json)

## Die drei Matches

Summen über zwölf Sitze je Version; Schreibweise R3 → V15. Der erste Punkt ist der Median des ersten öffentlichen positiven Punktestands zu Beginn eines Zuges.

| Match | Gewonnene Matches | Erster eigener Punkt | Eigene Punkte nach Zug 25 | Eigene Endpunkte | Solution-Endpunkte | Eigene Schüsse | Züge mit sichtbarem Gegner in SAP-Reichweite |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 9 → 11 | 32,5 → 32 | 18 → 3 | 4.606 → 3.939 | 2.074 → 2.023 | 228 → 294 | 600 → 500 |
| 2 | 1 → 7 | 7 → 7 | 552 → 689 | 8.302 → 8.453 | 9.022 → 8.032 | 192 → 360 | 349 → 311 |
| 3 | 1 → 5 | 5 → 5 | 743 → 832 | 9.408 → 9.404 | 10.066 → 9.435 | 200 → 316 | 236 → 236 |

**Match 2.** Nach Zug 25 hatte V15 über alle Sitze 137 eigene Punkte mehr, während sich die gegnerische Summe um nur einen Punkt unterschied. Eigene Einheiten besetzten zwischen Zug 1 und 25 insgesamt 595 bestätigte Feld-Züge (R3 501). Nach Zug 50 lag Solutions Gesamtstand in den V15-Partien 51 Punkte niedriger, nach Zug 75 bereits 422 und am Matchende 990. Sieben ursprüngliche Matchniederlagen wurden zu Siegen, ein ursprünglicher Sieg wurde zur Niederlage. In diesen sieben neu gewonnenen Matches lagen V15s eigene Punkte jeweils nach Zug 25, 50, 75 und am Ende höher. Auf sechs dieser sieben Sitze erzielte Solution am Ende weniger Punkte.

**Match 3.** Vier ursprüngliche Niederlagen wurden zu Siegen. V15 hatte auf allen vier Sitzen nach Zug 25 mehr eigene Punkte. Solutions Punktestand nach Zug 50 war bei beiden Versionen auf allen vier Sitzen identisch; am Matchende lag er mit V15 in jedem der vier Spiele niedriger. Über alle zwölf Sitze erzielten die beiden eigenen Versionen am Ende fast gleich viele Punkte. Die größere Differenz lag bei Solution.

**Schussziel und Kontakt.** Von R3s 392 Schüssen in Match 2 und 3 zielten 290 auf die aktuelle Position eines öffentlich sichtbaren, aktiven Gegners. Bei V15 waren es 168 von 676. V15 schoss 237-mal auf ein bestätigtes Punktefeld, an dem im Umkreis eines Felds vor dem Zug kein aktiver sichtbarer Gegner stand; R3 tat dies 96-mal. Die öffentliche Vorzugslage verrät weder den Standort unsichtbarer Gegner noch individuelle Treffer oder den verursachten Punktausfall. Ein pauschaler Verweis auf häufigeren Kontakt passt ebenfalls nicht zur Zählung in der letzten Tabellenspalte. [Alle 72 Match-Verläufe als Kennzahlen](matches.csv)

**Eine Gegenprobe im selben Panel.** Auf 7158056/P1 hatten beide Versionen in Match 2 ab Zug 5 einen Punkt. R3 kam bis Zug 25 auf 61 bekannte Feld-Züge und 68 Punkte, V15 auf 17 und 57. R3 gewann das Match 825:800, V15 verlor 762:803. Auf 7158229/P1 war der erste Punkt bei beiden in Zug 7, R3 verlor 530:699, V15 gewann 546:421. V15 gab dort 45 Schüsse ab, R3 zwei. R3 und V15 hatten auf diesen Karten schon im ersten Match verschiedene Befehle ausgeführt. Spätere Kennzahlen vergleichen zwei tatsächlich gespielte Verläufe. Einzelne Bewegungen oder Schüsse lassen sich daraus nicht als Ursache identifizieren.

Die **frühe Belegung nach dem ersten Punkt** und **späteres Schießen auf bekannte Felder** lassen sich als getrennte Mechanismen untersuchen. Diese Aufzeichnung enthält ausschließlich R3-Niederlagen. Sie bestimmt weder die Verlustrate auf den 788 früheren R3-Siegen noch die erreichbare Spielquote eines Mischagenten.

## Messung und Reproduktion

`replay.py` wählt die zwölf Sitze aus beiden fest gepinnten Originaltabellen. Beide Arme verwenden ihre eingefrorenen Quellen, die unveränderte native Spielschleife mit eigenem Solution-Reset pro Sitz, feste RNG-Initialisierung und Evaluationsmodus. Der passive Beobachter liest die dem Agenten zugängliche Stellung nach seiner Entscheidung, beide tatsächlich eingereichten Weltbefehle sowie die folgenden öffentlichen Punkte und Matchsiege. Zum Matchreset ergänzt die originale Kurs-Punktezählung den letzten Zuwachs vor dem Nullsetzen; diese reine Messinformation erhielt kein Spieler. Bei V15 stammt die bestätigte Feldkarte aus der eigenen V14-Komponente, bei R3 aus derselben Art von V14-Gedächtnis. Je Zug zählt ein besetztes bestätigtes Feld einmal, auch bei mehreren eigenen Einheiten darauf. Die drei Startschritte mit alten Einheiten bleiben im Rohprotokoll und sind aus Kontakt-, Besetzungs- und Schusszahlen ausgeschlossen. Es gibt keinen Punktegleichstand in den 72 Matches.

Im Unterordner [roh](roh/) steht pro Partie eine gzip-komprimierte JSON-Datei mit allen 303 Zugpaaren, allen Weltbefehlen, eigenen Einheiten sowie öffentlich sichtbaren aktiven Gegnern (ID, Weltposition und Energie), bestätigten Feldern und Matchuhren. Die zwei Manifeste nennen die Quelldateien, Modell- und Tabellenhashes. Der Auswerter prüft die 24 Dateien, die 48 Aktionsstromhashes und jede Matchsumme gegen die Originalspielstände. Die alten Tabellen enthalten keine Aktionsstromhashes für einen Vergleich mit der historischen Trajektorie.

Aus dem Projekt lässt sich der vollständige Bericht **ohne Modelllauf** nachrechnen. `AUS` ist das Ziel für die neu berechneten CSV- und JSON-Zahlen; `PY` bezeichnet das Projekt-Python.

```sh
REPO="$(git rev-parse --show-toplevel)"
DIAG="$REPO/experiments/analysis/r3_v15_blend_20261116/diagnose"
"$PY" -B "$DIAG/auswerten.py" --repo "$REPO" --raw "$DIAG/roh" --out "$AUS"
```

Für neue Reproduktionen zwei voneinander getrennte Quellabzüge verwenden. R3 verwendet `0105658188b2ec5eaf5c3a4b0ef477be9a1412f8` mit den Dateien aus `agents`, `scripts`, `lux`; unter `experiments/opponents/kaggle3_lux3_048fn` liegt der vom alten 400er-Manifest ebenfalls geprüfte lokale Gegnerabzug. V15 verwendet das veröffentlichte gepackte Modell mit SHA-256 `20f8af0dee4711b566cc83309111fceb32ee176aa86c7fd9398bf52c330a017e`. Sein Quellabzug basiert auf `b2bd67e43f213cd99669bf3eee759e3fdeb1c0f5` mit `agents`, `scripts`, `lux` und `Paths.csv`; die drei Dateien `scripts/par_eval.py`, `scripts/xversion_replay.py`, `scripts/v15_style_panel.py` stammen aus `ed1aee4313e1f370eff317886f8ecd1364e427ae`. Der Loader prüft die geladenen Bestandteile und Mischschalter; das historische Vergleichsarchiv verweist auf einen separat serialisierten, tensoridentischen V15-Pack. [V15-Tensor- und Kursprüfung](../../umbau_20261115/py310/ERGEBNIS.md)

`R3_SRC` und `V15_SRC` geben diese beiden Abzüge an, `V15` die genannte Packdatei und `NEU` ein neues Messverzeichnis. Jede Zeile benötigt genau einen Worker.

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
"$PY" -B "$DIAG/replay.py" r3 --repo "$REPO" --source "$R3_SRC" --model "$REPO/experiments/candidates/movement_dagger_20261115/r3_soft.pth" --out "$NEU"
"$PY" -B "$DIAG/replay.py" v15 --repo "$REPO" --source "$V15_SRC" --model "$V15" --out "$NEU"
```
