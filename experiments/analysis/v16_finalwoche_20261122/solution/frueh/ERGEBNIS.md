# Gegen Solution fehlen in zwei Fällen schon zu Beginn von Match 3 Informationen

In den sieben Einzelmatches, die R3 auf seinen vier allein gewonnenen Spielsitzen holte und V16 verlor, kannte R3 pro Zug durchschnittlich **13,05 bestätigte Punktefelder**, V16 **9,91**. **92,2 % dieses Abstands** entfielen auf das dritte Match zweier Karten, 7261020 und 7267071 (jeweils Player 0). Die Eröffnung dieser Matches begann mit unterschiedlichem Wissen aus den vorherigen Matches.

| Frühe Züge (1–70), sieben gepaarte Einzelmatches | V16 | R3 |
|---|---:|---:|
| Bestätigte Felder im eigenen Gedächtnis pro Zug | 9,91 | 13,05 |
| Tatsächlich von eigenen Einheiten besetzte Punktefelder pro Zug | 3,58 | 4,18 |
| Sichtbare, bestätigte und unbesetzte Felder pro Zug | 0,90 | 1,17 |
| Davon insgesamt in einem erlaubten Schritt von einer verlegbaren Einheit erreichbar | 66 | 74 |
| Davon mit dem passenden Befehl besetzt und sofort bepunktet | 47 (71 %) | 51 (69 %) |

Pro Spalte sind es 490 Matchzüge. Für die Besetzung zählt die Istposition vor der jeweiligen Entscheidung; die letzte Zeile misst den Erfolg nach dem Zug. Auf den sechs entgegengesetzt gekippten Matches kannten beide ungefähr gleich viele Felder (V16 16,72; R3 16,40). Dort gewann V16 trotz **87 von 173** direkt genutzten Gelegenheiten, R3 verlor bei **50 von 87**. Eine allgemeine Anweisung, immer das nächste freie Feld zu nehmen, lässt sich daraus nicht ableiten.

**Wann öffnet sich die Wissenslücke?** Auf 7261020 kannten beide in Zug 1–50 des zweiten Matches im Mittel 10 bestätigte Felder, auf 7267071 jeweils 12. In Zug 1–30 des dritten Matches lagen beide Karten bei V16 im Mittel bei 12 und bei R3 bei 22. Im gesamten Frühfenster von Match 3 waren es auf 7261020 12,00 gegen 22,00 und auf 7267071 12,00 gegen 22,31. Zusammengenommen machen diese zwei Matches 1.422 der 1.542 zusätzlichen bestätigten Feldzüge von R3 aus. Besetzungsunterschiede sind dadurch plausibel, aber der Vergleich verrät noch nicht, welche konkrete Bewegung, Sichtung eines Relikts oder einzelne logische Schlussfolgerung die zusätzlichen Felder erschlossen hat.

**Ein anderes Hindernis zeigt Karte 7267009, Match 2, Player 1.** V16 und R3 kannten hier gleich viele Punktefelder (12 je Zug). V16 hatte 40 Ziel-Feldzüge mit freiem Nachbarfeld und unmittelbar angrenzender verlegbarer Einheit. Bei 31 davon reichte deren Energie für die Bewegung nicht. V16 nutzte acht der neun übrigen Fälle, R3 sechs von acht. Alle 31 energiebedingt ausgeschlossenen Ziel-Feldzüge der sieben untersuchten V16-Verlustmatches stammen von dieser einen Karte. Auf allen sieben Karten-/Matchpaaren zusammen gab es für V16 außerdem elf durch Gelände ausgeschlossene Feldzüge, darüber hinaus keine Verwerfung einer bezahlbaren und passierbaren Bewegung durch die Aktionsmaske in der betrachteten Situation.

**Gezielter nächster Versuch.** Auf den beiden benannten Karten sollte man am Ende von Match 2 und beim Übergang zu Match 3 die erste weiterhin unbekannte Punktefeldgruppe verfolgen, die R3 beweist. Welche bisher nicht beobachtete oder nicht getestete Gruppe erreicht eine freie Einheit, was ist zum Entscheidungszeitpunkt schon öffentlich ableitbar und welcher Folgeschritt löst die Bestätigung aus? Wenn es in beiden Fällen denselben beobachtbaren Vorläufer gibt, ist das ein Kandidat für gezielte Lehrerbeispiele bei der Wegwahl freier Einheiten. Die Wirksamkeit muss sich auf unbenutzten Karten zeigen. Zwei Beispiele rechtfertigen noch keinen Eingriff in die Spielstrategie.

## Messung und Grenzen

Getrennte Wiedergabe der acht Spielsitze mit den zwei Originalpaketen, **alle 16 Endresultate und alle 48 Einzelmatchergebnisse** stimmten mit der [vorigen Reproduktion](../REPLAYS.md) überein. Pro Einzelmatch wurden Zug 1–70 ausgewertet; Zug 0 mit Figurenresten aus dem vorigen Match wurde ausgelassen. Beide Spieler laufen auf eigene Trajektorien, auch Solution reagiert jeweils auf den anderen Spielverlauf.

„Bestätigt“ bezeichnet die tatsächliche Menge `point_tiles` im entscheidenden Agenten nach Verarbeitung seiner Spielbeobachtung und vor Ausführung des Spielzugs. R3 und der V16-Schüler haben jeweils ihr eigenes Gedächtnis. Die Auswertung liest die tatsächlich genutzte Bewegungsmaske und übersetzt ihre Richtungen entsprechend der Startseite. Ein erreichbares Ziel muss bestätigt, sichtbar, von beiden Seiten unbesetzt und aus einem Nachbarfeld nach der tatsächlichen Maske erreichbar sein. Die lebende Nachbareinheit darf selbst kein als bestätigt bekanntes Feld räumen. Die Einheit kann dennoch eine andere strategische Aufgabe haben. Jeder zulässige Ziel-Feldzug zählt nur einmal, auch bei mehreren geeigneten Nachbarn. Eine Gelegenheit, die mehrere Runden offen bleibt, kann mehrfach zählen. Wege über zwei oder mehr Schritte, unsichtbare Ziele und Gegnerreaktionen auf hypothetische Aktionen werden nicht geschätzt.

Als unabhängige Rückprüfung wurden die im Gedächtnis bestätigten Felder mit dem vollständigen Zustand der Engine abgeglichen. In den sieben R3-Siegmatches waren alle gemessenen Bestätigungen aktuell echte Punktefelder. Bei V16 hatte in allen 66 tatsächlich möglichen Fällen mindestens eine geeignete Einheit auch rückblickend ein echtes Nichtpunktefeld als Startposition, bei R3 in 73 von 74. Der vollständige Enginezustand fließt nur in diese nachträgliche Prüfung und die tatsächliche Punktezählung ein. Die ausgewählten Karten gehören zur Ursachenanalyse und sollten nicht über eine neue Abgabe entscheiden.

[Messskript](messen.py) · [Messwerte je Match und Zeitabschnitt](daten.json) · [Gepaarte Summen](auswerten.py)

```sh
python experiments/analysis/v16_finalwoche_20261122/solution/frueh/messen.py
python experiments/analysis/v16_finalwoche_20261122/solution/frueh/auswerten.py
```
