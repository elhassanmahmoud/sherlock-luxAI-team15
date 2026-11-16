# Rekonstruktion der vier abweichenden Starts

Die zwölf Spiele vergleichen den ursprünglichen R3, Mahmouds V15 und die zuletzt untersuchte Einzelübergabe auf denselben vier Kombinationen aus Karte und Startseite. V15 hatte diese vier Spiele gegen Solution gewonnen und die Einzelübergabe verloren. P0 und P1 derselben Karte zählen als getrennte Starts. Die Originalreferenzen wurden über die archivierten Spieltabellen und ihre Prüfsummen identifiziert.

[Alle zwölf Zugfolgen](roh/) enthalten je 303 Schritte. Unsere Perspektive steht in den Punktzahlen und gewerteten Feldern jeweils an erster, Solution an zweiter Stelle. Um den 101 Schritte langen Matchzyklus nachzuvollziehen, ist die Matchnummer `step // 101 + 1`, die Zugnummer `step % 101`.

- `own` und `visible` enthalten die vor dem Zug öffentlich beobachteten eigenen bzw. gegnerischen aktiven Einheiten als Kennung, Weltkoordinaten x und y sowie Energie. `next_own` und `next_visible` sind die nächste öffentliche Beobachtung. `confirmed` und `known_asteroids` kommen aus dem jeweils tatsächlich spielenden Gedächtnis, beim Hybrid aus seinem V14-Zweig.
- `own_orders` und `opp_orders` sind die tatsächlich gespielten Weltbefehle, `r3_orders` und `v15_orders` die Vorschläge auf derselben Beobachtung. Beim Einzelübergabe-Agenten wurden die beiden tatsächlich schon berechneten Empfehlungen abgegriffen. Auf nativen Elternverläufen erhielt ein getrennter zweiter Berater dieselbe Beobachtung und die tatsächlich gespielte Aktion als Rückmeldung. Sein Aufruf bewahrt die Zufallszustände des laufenden Spiels.
- `before` und `after` sind der offizielle Schrittstand einschließlich der letzten Gutschrift vor einem Matchreset. `scored_fields` enthält für jedes Team die Weltfelder, die bei diesem Schritt tatsächlich jeweils einen Punkt einbrachten. Diese Koordinaten wurden ausschließlich **nach** dem Zug aus dem finalen Enginezustand für die Diagnose ausgelesen. Jeder Zuwachs ist gegen die Differenz im Spielstand geprüft. Die Agenten erhalten nur die reguläre Beobachtung.

Die zwölf Endergebnisse stimmen in Siegen, Matches, beiden Punktsummen und Schrittzahl mit ihren archivierten Referenzen überein. Die sechs früher vollständig gespeicherten Elternpartien auf 7158020 (P0/P1) und 7158030 (P1) reproduzierten zusätzlich alle ursprünglichen Beobachtungen und beide Aktionsströme. Die vier Elternempfehlungs- beziehungsweise Spielmatrizen je Zug dürfen für das nachträgliche Betrachten zusammen eingesehen werden. Für eine Live-Regel sind gegnerische Befehle, echte gegnerische Punktfelder und der nächste Zustand unbekannt.

## Punkte in der Umgebung von V15s Schüssen

Auf V15s eigenen vier Verläufen erfüllten 61 seiner Schüsse in 49 Zügen den untersuchten Filter für einen vom R3-Vorschlag abweichenden Schuss. In acht dieser 61 Fälle war vor dem Schuss ein lebender Gegner höchstens ein Feld in Chebyshev-Distanz vom Ziel entfernt. Für die folgende Auswertung zählen überlappende 3×3-Schussbereiche eines Zugs zusammen nur einmal.

In diesen Bereichen erzielte Solution beim vorigen Zug insgesamt 93 Punkte, beim Schusszug 54. In 24 der 49 Züge fiel mindestens ein vorher gewertetes gegnerisches Feld weg. In vier Zügen kam ein neues hinzu. In 17 Zügen lagen in den Bereichen vorher wie nachher null gegnerische Feldpunkte. Das sind beobachtete Belegungen in zwei aufeinanderfolgenden Zuständen. Zeitgleich spielten beide Teams ihre übrigen Befehle. [Zählung, einzelne Schüsse und Aufschlüsselung nach Match](schussumgebung.json).

Ein Beispiel ist 7158020/P0 in Match eins, Zug 55. V15 ließ Einheit 2 auf das bestätigte Feld (17,17) schießen. R3 empfahl derselben Einheit auf dieser Stellung zu warten. Solution hatte im vorigen Zug auf (17,17) gepunktet und bekam im Schusszug in diesem 3×3-Bereich keinen Punkt.

## Nachrechnen

Mit dem Projekt-Python aus diesem Ordner aufrufen:

```sh
"$PY" -B pruefen.py
"$PY" -B schussumgebung.py
"$PY" -B aufnehmen.py --runtime "$LAUFZEIT" --out "$NEUER_ORDNER"
```

Der letzte Aufruf benötigt die rekonstruierte [historische Laufzeit](../../r3_v15_blend_20261116/REPRODUKTION.md) und schreibt einen neuen Satz Daten mit maximal zwei lokalen Modellprozessen.

Die separate [Ein-Zug-Gegenprobe auf den nativen V15-Stellungen](v15_gegenprobe/ERGEBNIS.md) misst die direkte Wirkung dieser Schüsse beim selben Gegenzug.
