# Findet der Kaggle-Lehrer das erste Relikt früher?

Auf acht vorab ausgewählten neuen Karten mit der kleinsten Sensorreichweite (**1**) gewannen Original-V16 und der Kaggle-Dritte gegen die originale Solution jeweils **15 von 16 ersten Matches**. Die beiden verloren auf unterschiedlichen Karten. Die Eröffnung des Lehrers brachte ihm auf sechs Startseiten frühere Sicht auf ein Relikt, auf sieben sah V16 es früher. Dreimal sahen beide es im selben Zug.

| Beobachtung | Lehrer früher | Gleichzeitig | V16 früher | Median V16 | Median Lehrer |
|---|---:|---:|---:|---:|---:|
| Erste direkte Reliktsicht | 6 | 3 | 7 | Zug 45 | Zug 52 |
| Erster eigener Punkt | 5 | 2 | 9 | Zug 45,5 | Zug 53 |

Der Lehrer hatte nach Zug 70 auf **7/16** Startseiten die bessere Punktedifferenz, am Matchende noch auf **5/16**. Unter den 16 gepaarten Vergleichen beträgt der Median der Differenz Lehrer minus V16 zu diesen Zeitpunkten −6,5 bzw. −44,5 Punkte. Auf 14 Startseiten gewannen beide.

**Zwei Partien zeigen, wann sich der Suchweg auszahlte.**

| Karte / Sitz | V16: erste Sicht, erste Gutschrift | Lehrer: erste Sicht, erste Gutschrift | V16 gegen Solution | Lehrer gegen Solution |
|---|---|---|---:|---:|
| 160394018 / P1 | Keine Sicht, keine Gutschrift | Zug 76, Zug 73 | 0:2 | **32:6** |
| 160394013 / P1 | Zug 38, Zug 39 | Zug 70, Zug 62 | **189:40** | 38:82 |

Auf Karte 018 hatte V16 nach Zug 70 noch **0:0**, der Lehrer auf seinem eigenen Spielverlauf **0:6**. Eine Rettung, die ausschließlich auf einen bestehenden Rückstand in Zug 70 reagiert, würde diese V16-Partie verpassen. Umgekehrt funktionierte V16s eigener früher Suchweg auf 013 gut. Für ein Nachtraining wäre damit das **Ausbleiben jeglicher Sicht und eigener Gutschrift über viele Züge** ein plausibler Anlass, gezielt unterschiedliche Suchbewegungen zu vergleichen. Die vorliegenden Spiele begründen keine allgemeine Übernahme der Lehrer-Eröffnung. Ob eine einzelne im V16-Verlauf ausgetauschte Entscheidung hilft, lässt sich erst mit einem solchen Gegenversuch prüfen.

## Suchfläche und tatsächliche Nähe

Die beiden Ausnahmen wurden nach Sichtung der Ergebnisse als vier Zusatzreplays ausgewählt. In Zug 70 hatte die später erfolgreiche Mannschaft auf beiden Karten **weniger** unterschiedliche Felder gesehen. Großflächigeres Erkunden allein erklärt die Siege nicht.

| Karte / P1 | Agent | Gesehene Felder bis Zug 50 / 70 | Kleinster Abstand in Zug 50 / 70 |
|---|---|---:|---:|
| 160394013 | V16 | 239 / 306 | 1 / 1 |
| 160394013 | Kaggle-Lehrer | 229 / 320 | 6 / 2 |
| 160394018 | V16 | 225 / 330 | 8 / 8 |
| 160394018 | Kaggle-Lehrer | 194 / 289 | 9 / 8 |

Auf 013 stand mindestens eine V16-Einheit in Zug 50 bereits unmittelbar neben einem echten Relikt, nachdem V16 es in Zug 38 gesehen hatte. Auf 018 hatten beide Teams in Zug 70 noch acht Felder Abstand. Der Lehrer bekam sechs Züge später Sicht und V16 während des gesamten ersten Matches keine. Die zwei Messzeitpunkte erlauben auf 018 keine genauere Zuschreibung an die Zielwahl eines bestimmten Schiffes. Sie legen nahe, Suchrichtungen und tatsächliche Sichtgewinne bis zur ersten Entdeckung zu messen, wenn man neue Eröffnungen beurteilt.

Gesehene Felder sind die Vereinigung der eigenen öffentlichen Sensormasken bis einschließlich der jeweiligen Beobachtung auf 576 möglichen Feldern. Der Abstand ist die kleinste Manhattan-Distanz eines eigenen lebenden Schiffes zu einem der beiden echten ersten Relikte. Nur die rückblickende Diagnose kennt diese Koordinaten. Das Maß berücksichtigt weder Hindernisse noch Nebel. Erstes Relikt, erste Gutschrift, 70er-Stand, Endpunkte und Sieger der vier Wiederholungen stimmen mit den 32 Originaleröffnungen überein. Die Wiederholungen gingen nicht in die Siegzahl ein. [Koordinaten und Messwerte](suchweg.json) · [Reproduktion](suchweg.py)

## Prüfung und Aussagegrenze

Aus den aufsteigenden Seeds ab 160394000 wurden allein anhand der öffentlichen Reichweite die ersten acht Karten gewählt (Endziffern 000, 006, 009, 010, 011, 013, 016, 018). Auf jeder Karte wurden beide Startseiten und beide Agenten in getrennten Spielen gegen Solution geprüft. Die Reichweite wurde an jedem tatsächlichen Kurs-Reset kontrolliert. Für das untersuchte Fenster wurden 32 verschiedene Eröffnungen mit jeweils 101 Entscheidungen gezählt. Beide Fehlerzähler waren unauffällig. Die Sicht wird aus der öffentlichen Reliktanzeige vor dem Befehl gelesen, jeder Punkt nach dem ausgeführten Zug, einschließlich der letzten Wertung beim Matchwechsel. V16 verpasste auf einem Sitz sowohl Relikt als auch Gutschrift, der Lehrer auf keinem. Die Rangfolge behandelt ein ausgebliebenes Ereignis als Zug 101. Der benutzte Lehrer stammt aus der im Projekt eingefrorenen Version 0.4.8_fn. Auf allen acht Karten war die Sensorreichweite niedrig. Der Versuch misst erste Matches gegen Solution, keine kompletten Spiele, und isoliert den Effekt einer einzelnen Entscheidung nicht.

[Vor dem Start festgelegter Plan](PLAN.md) · [Alle Kennzahlen](ergebnis.json) · [Einzelwerte A](teil_0.jsonl) · [Einzelwerte B](teil_1.jsonl) · [Die ursprünglichen drei Niederlagen und sieben Kontrollsiege](../signalstudie/kombi/auftakt/ERGEBNIS.md)

Für eine unabhängige Wiederholung mit der Kurs-Python-Umgebung im Repo-Stamm:

```sh
d=experiments/analysis/v16_finalwoche_20261122/eroeffnung_lehrer
out=$(mktemp -d)
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONHASHSEED=0
python "$d/eroeffnung.py" 0 --out "$out"
python "$d/eroeffnung.py" 1 --out "$out"
python "$d/auswertung.py" --out "$out"
```
