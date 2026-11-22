# Ein Kundschafter auf den zwei bekannten Karten

In den zwei ausgewählten Match-2-Diagnosefällen auf Player 0 genügte die Änderung von jeweils acht Befehlen eines einzigen Raumschiffs, um das ganze Spiel gegen Solution zu drehen. Das unberührte V16 spielte beide Male 1:2, die Variante gewann 2:1 und 3:0. Bei zwei weiteren Durchläufen auf dem umgekehrten Sitz blieb der jeweilige Spielsieger gleich. Von vier Sitzen gewann V16 einen, der Kundschafter drei. Auf den vier Vergleichssitzen sah jede Variante dasselbe Spiel unter denselben Einstellungen mit derselben Karteninitialisierung, aber ab ihrer ersten unterschiedlichen Aktion folgten eigenständige Spielverläufe.

| Karte und Sitz | Änderungen | Zweites Paar in Match 2, V16 → Scout | Bekannte Felder Anfang Match 3 | Matchsiege V16 → Scout | Punktesaldo V16 → Scout |
|---|---:|---|---|---|---|
| 7261020, Player 0 | 8 | Zug 95 → 81 | 12 → 20 | 1 → 2 | −234 → +10 |
| 7261020, Player 1 | 7 | nicht gesehen → Zug 81 | 10 → 12 | 1 → 1 | −458 → −269 |
| 7267071, Player 0 | 8 | nicht gesehen → Zug 70 | 12 → 24 | 1 → 3 | +168 → +576 |
| 7267071, Player 1 | 12 | Zug 77 → 66 | 20 → 24 | 3 → 3 | +388 → +361 |

Auf 7261020/Player 0 war der Suchauftrag schon beendet, als das zusätzliche Relikt in Zug 81 sichtbar wurde. In einem getrennten Kontrolllauf mit identischen acht geänderten Befehlen und identischem Endergebnis stand **Einheit 14** bei (2, 6) als einzige eigene Figur innerhalb der Sensorreichweite 1 zum Relikt (3, 6). Der Kundschafter war **Einheit 0**. Der Eingriff änderte den weiteren Teamverlauf, die direkte Sichtung übernahm eine andere Einheit. [Sensorbeleg](sichtbeleg.json) · [Reproduktion](sichtbeleg.py)

**Technische Prüfung.** Alle vier V16-Referenzen reproduzierten die archivierten Punktesummen und Matchsiege exakt; die acht Kombinationen aus zwei Karten, zwei Sitzen und zwei Agenten waren vollständig. Alle 35 tatsächlichen Änderungen über die vier Kandidatenpartien betrafen pro Spiel eine einzelne Einheit auf einem erlaubten Bewegungsschritt; jeder ersetzte Befehl war Bewegung oder Stillstand. P1 nutzte die gespiegelten Aktionsrichtungen. Diese nach bekannten Schwächen ausgesuchten Karten dürfen keine Auswahl der Abgabe entscheiden. Das Signal erfüllte die [vor dem ersten Spiel festgelegten Bedingungen](PLAN.md) für den getrennten Frischtest.

**Genaue Ausführung der Suchregel.** Die Suchrichtung schätzt bislang ungesehene Fläche in einem Manhattan-Radius, während die ungestörte Grundsicht der Engine in Quadraten berechnet wird. Für die Erfolgsmessung zählte nur die tatsächlich beobachtete zusätzliche Reliktpaarung. Ein Sonderfall des vorab beschriebenen Abbruchs wird im Prototyp enger behandelt: Steht die Einheit bereits auf einem neuen Punktefeld oder würde ihr ursprünglicher nächster Schritt eins besetzen, gibt sie den Auftrag frei. Wird hingegen nur das bisher ausgewählte entfernte Suchziel inzwischen als Punktefeld bestätigt, kann der Prototyp zu einem neuen Ziel wechseln. Der Code blieb für alle Spielresultate identisch. Für den unabhängigen Vergleich wird dieser Sonderfall zusätzlich passiv überwacht; die vier ursprünglichen technischen Kandidatenpartien haben diesen Zähler nicht. Jede spätere Bestätigung muss genau das getestete Verhalten festhalten oder eine geänderte Implementierung als neue Variante prüfen.

[Spiele und geänderte Befehle](technik.json) · [Auswertung](auswerten.py) · [Isolierter Prototyp](kandidat.py)

```sh
python experiments/analysis/v16_finalwoche_20261122/kundschafter/auswerten.py experiments/analysis/v16_finalwoche_20261122/kundschafter/technik.json
```
