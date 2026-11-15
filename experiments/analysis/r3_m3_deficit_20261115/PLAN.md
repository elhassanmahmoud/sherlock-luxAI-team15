# Öffentlicher Rückstand im Entscheidungsmatch

Wir prüfen, wann Sherlock in einem offenen dritten Match einen Wechsel zu V15 überhaupt erwägen könnte. Der ursprüngliche Wechsel zu Beginn von Match 3 rettete auf 184 historischen Solution-Karten zwei ganze Partien und kostete zwei andere. Für die zwei weiteren Niederlagen half die frühe Übernahme ebenfalls nicht. Die vorgesehene Alternative beobachtet zusätzlich die aktuelle Partie im dritten Match.

**Vorab festgelegter Auslöser.** Bei öffentlichem Matchstand 1:1 liest der eigene Spieler ab einschließlich Matchschritt 50 vor jeder Aktion seinen aktuellen Punktestand und den des Gegners. Sobald die eigenen Punkte strikt niedriger sind, wird in dieser Partie genau einmal ein Auslöser vermerkt. Gleichstand löst nichts aus. Schritt 100 ist die letzte ausführbare Aktion, der danach ermittelte finale Punkte- und Siegerstand ist kein Auslöser. Beide möglichen Reihenfolgen der ersten beiden Matchsiege zählen. Zur Entscheidung stehen ausschließlich Matchstand, Matchschritt und öffentlicher Punktestand zur Verfügung.

Die Diagnose spielt alle drei Matches mit den archivierten Originalbefehlen beider Seiten zu Ende. Es werden keine Modelle oder Gegner geladen und keine Befehle geändert. Eingabe ist das bereits veröffentlichte [Archiv mit 61 Partien](../r3_v4_wl_20261115/solution_scope/partien.tar.gz). Von 368 ursprünglichen Sitzresultaten waren 322 schon nach zwei Matchsiegen entschieden. Unter den 46 reproduzierten knappen Kontrollen bleiben genau 17 mit 1:1 nach Match 2. Darunter befinden sich alle vier R3-Niederlagen und 13 ursprüngliche Siege. Die beiden neu verlorenen Spiele des früheren V15-Wechsels werden einzeln gekennzeichnet.

Der Prüfer gleicht alle 303 Befehlspaare, die drei vollständigen Matchpunktestände, die drei offiziellen Matchsieger, die Gesamtscores und den ursprünglichen Spielsieger ab. Jeder Fall enthält den ersten Auslösezeitpunkt und die beiden öffentlichen Punktestände. Die kumulative Zählung an jedem Auslösezeitpunkt einer Niederlage zeigt, wie viele geschützte Siege bis einschließlich desselben Schritts bereits betroffen gewesen wären. Nachträgliche Optimierungen von Schritt oder Schwelle sind nicht Teil der Studie.

**Bedingung für eine getrennte Folgeprüfung.** Nur wenn mindestens eine der vier ursprünglichen Niederlagen den Auslöser tatsächlich erreicht, kommt ein kausaler Versuch in Betracht. Dann wird auf genau sämtlichen ausgelösten Sitzen einschließlich aller geschützten Siege jeweils einmal der geänderte Agent gespielt. Die nicht ausgelösten Sitze folgen nachweislich allen Originalbefehlen. Ein eigenständiger Vergleich auf neuen Karten kommt nur bei positivem Nettozuwachs der ganzen Spiele im Archiv in Betracht. Die neuen Karten werden vor dessen Beginn festgelegt.

Die Schwelle wurde nach Einsicht in einzelne frühere Dev-A-Zeitreihen und die ausgewählte Karte 7286137 festgelegt. Die Auswertung auf den 17 historisch bekannten Sitzen ist eine Entwicklungsdiagnose. Ein Treffer zeigt eine Gelegenheit, eine Niederlage zu beeinflussen. Erst ein späteres gepaartes Duell mit tatsächlich anderen Befehlen könnte einen geretteten Spielsieg belegen.

```sh
python -m scripts.r3_m3_deficit_replay --project . --out /tmp/sherlock-m3-result.json
```
