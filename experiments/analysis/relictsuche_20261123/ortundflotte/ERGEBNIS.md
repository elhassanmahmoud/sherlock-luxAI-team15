# Welcher Suchweg ergänzt die übrige Flotte?

## 288 vollständige Spiele bei geringer Sicht

Auf 48 frischen Karten mit beiden Startseiten gewann die gemeinsame Suche **95/96 gegen Solution**, Original-V16 auf denselben Sitzen **93/96**. Direkt gegen V16 gewann der Kandidat **51/96** (53,13 %, nach Karten gezogenes 95-%-Intervall 40,63 bis 65,63 %). Das erste Relikt wurde gegen Solution im Mittel **0,71 Züge früher** sichtbar (Intervall −1,82 bis +4,04), der erste eigene Punkt kam 1,49 Züge früher (−1,24 bis +4,86). Das ist ein bestandener Auswahltest. Die eigens festgelegte Prüfung auf 160 weiteren Karten aller Sichtweiten läuft. [Rohdaten](duelle_karten.jsonl.gz) · [Unverändertes Ergebnis und Auswahlbedingungen](duelle.json) · [Vorher festgelegte unabhängige Prüfung](../abschlusspruefung/PLAN.md)

Die Richtung rettete zwei ganze Spiele, beide auf Startseite 1. Auf beiden gewann V16 schon Match 1. Auf Karte 164050036 änderte die Route genau einen Befehl von Schiff 0. Das erste Relikt erschien zwei Züge früher in Sherlocks Sicht und Match 2 kippte von 223:287 auf 282:237. Auf Karte 164050141 änderte der Sucher zwei Befehle desselben Schiffs. Die erste Sicht kam sechs Züge später, der **erste Punkt 19 Züge früher**. Match 2 kippte von 183:197 auf 294:266. Der einzige verbliebene Solution-Verlust hatte ein Relikt schon in Zug 12 und wurde vom Sucher vollständig wie bei V16 gespielt. Daraus folgt auch, weshalb wir Sichtzeit, Punkte und Gesamtgewinner einzeln messen.

## Wie die Richtung gelernt wurde

Wir haben die auf 49.152 Karten gelernte Häufigkeit der ersten Reliktposition mit der trainierten Acht-Zug-Vorhersage für die übrigen Schiffe kombiniert. Auf 480 Entwicklungskarten mit 1.788 angebotenen Suchsituationen erzielte die volle Ortsgewichtung die höchste mittlere Vorverlegung im kurzen Vergleich. Sie wurde vor Öffnung der getrennten 160 Karten festgehalten.

Auf diesen Karten lagen 681 verwertbare Situationen vor. Der neue Bewerter änderte auf 123 Karten mindestens eine Wegwahl. Auf zwölf Karten rückte die Sicht im Mittel der dort untersuchten Situationen vor, auf sechs trat sie später ein. Über alle 160 Karten ergaben sich 0,081 Züge frühere Sicht im Acht-Zug-Fenster (95-%-Kartenintervall +0,017 bis +0,167). Der Schiedsrichter prüfte hierzu am tatsächlichen ersten Reliktpaar, wann die angebotene Position des freien Schiffs und die aufgezeichnete Sensorleistung der übrigen Flotte die echte Sichtschwelle überschritten hätten. Außerhalb des kurzen Fensters gibt dieser Vergleich keine Fundzeit an. Im vollständigen Spiel können die anderen Schiffe auf einen geänderten Befehl reagieren.

Für Mahmoud ist der wesentliche Unterschied zur älteren Flottensuche, dass zwei unerkundete Orte jetzt verschieden bewertet werden können, auch wenn an beiden die gleiche Wahrscheinlichkeit besteht, dass die übrige Flotte vorbeikommt. [Trainingskarten](train.json) · [Getrennte Vorauswahl](valid.json) · [Suchregel und Spielplan](PLAN.md)

Die ersten beiden technischen Vergleichssitze ließen in der ursprünglichen Flottensuche keinen Eingriff zu. Für den aktiven Technikvergleich wurden deshalb zwei bereits archivierte Sitze mit mindestens drei ausgeführten Suchbewegungen verwendet.

Auf den beiden aktiven technischen Sitzen spielte die neue Implementierung mit ausgeschalteter Ortsgewichtung alle 303 Befehle genauso wie das archivierte Original der Flottensuche. Mit der gelernten Gewichtung rückte die erste Sicht hier von Zug 73 auf 71 gegen Solution und von 41 auf 40 direkt gegen V16 vor. Die zwei bekannten Verläufe dienen der Funktionsprüfung. [Echte Befehle, Zeitpunkte und Matchstände](technik.json)
