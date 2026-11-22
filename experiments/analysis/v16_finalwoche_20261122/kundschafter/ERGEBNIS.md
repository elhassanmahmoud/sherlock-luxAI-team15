# Früher Kundschafter auf 16 frischen Karten

**V16 bleibt die Referenz.** Der Kundschafter drehte in der [technischen Vorprüfung](TECHNIK.md) zwei bekannte Niederlagen. Auf dem unabhängigen Panel gewannen aber **beide Versionen alle 32 Spiele gegen Solution**. Im direkten Vergleich verlor der Kundschafter 15:17. Damit verfehlte er zwei der drei vorab festgelegten Bedingungen für einen weiteren Bestätigungstest.

| Gegner | Spielsiege Kundschafter / V16 | Matchsiege Kundschafter / V16 | Sitze mit tatsächlich veränderten Befehlen | Ergebnis bei diesen Eingriffen |
|---|---|---|---|---|
| Solution_92 | 32 / 32 von je 32 | 94 / 93 von je 96 | 8 auf 6 Karten | beide 8/8; kein gewonnener oder verlorener zusätzlicher Spielsitz |
| Kaggle-Dritter | 4 / 2 von je 32 | 18 / 14 von je 96 | 12 auf 6 Karten | 4/12 gegenüber 2/12; zwei gewonnene, null verlorene bisherige Siege |
| Direkt gegen V16 | 15:17 | 46:50 | 10 auf 5 Karten | 4:6; ohne geänderten Befehl 11:11 |

Gegen Kaggle lagen **beide zusätzlichen Siege auf derselben Karte**, 94651000, je einer pro Startseite. Die beiden Siege belegen damit einen Effekt auf dieser Karte. Beim Vorzeichenvergleich der Kartenpaare ergibt sich für den Unterschied bei ganzen Kaggle-Spielen zweiseitig p = 1,0. Bei nur einer Karte mit verändertem Gesamtsaldo kann die Probe einen allgemeinen Vorteil nicht belegen. Die 32 Siege gegen Solution zählen 16 Karten mit zwei Startplätzen. V16 gewann auf diesen Karten schon zuvor alle Spiele.

**Nach Seiten.** Gegen Solution gewann der Scout 16/16 auf jeder Seite und griff auf Player 0 dreimal, auf Player 1 fünfmal ein. Gegen Kaggle war das Ergebnis auf jeder Seite 2/16 gegenüber V16 mit 1/16, bei jeweils sechs Eingriffen. Im direkten Duell holte er 8/16 auf Player 0 und 7/16 auf Player 1 (je fünf Eingriffe, davon je zwei Siege). Jeder tatsächlich geänderte Befehl gehörte zur einen ausgewählten Einheit und war durch die echte Aktionsmaske erlaubt. Alle 44 äußeren Gegnerpartien ohne geänderten Befehl stimmten mit ihrer Baseline bei Matchsiegen und beiden Punktsummen überein.

## Warum das technische Signal nicht wiederkam

Gegen beide äußeren Gegner änderte sich auf keiner frischen Karte der Zug, in dem das zweite Paar erstmals beobachtet wurde. Auch gegen Kaggle ging der Gewinn auf Karte 94651000 daher nicht auf eine frühere Sichtung zurück.

Eine **nachträgliche Prüfung der Karteninitialisierung** klärt den scheinbaren Widerspruch: Auf fünf der 16 Karten erschien während Match 2 überhaupt kein zweites Reliktpaar. **Sieben der acht Eingriffe gegen Solution** lagen auf genau diesen fünf Karten. Auf den übrigen elf Karten sah bereits V16 das zweite Paar auf allen 22 Solution-Sitzen; der Kundschafter griff dort nur einmal ein. Der Kaggle-Doppelsieg fiel auf eine der fünf Ein-Paar-Karten und muss durch den veränderten Spielverlauf erklärt werden. Versteckte Kartenmerkmale wurden erst nach Abschluss aller Spiele gelesen. Sie dürfen im Agenten oder zur Vorabauswahl einer für ihn günstigen Karte nicht verwendet werden.

## Nächste überprüfbare Idee

**Nachträglich formulierte Hypothese.** Ein stärkerer Anlass zum Suchen wäre der Nachweis, dass die bisher bekannte Reliktumgebung den öffentlich beobachteten Punktgewinn des Gegners nicht erklären kann. Im [bereits aufgezeichneten Verlauf](../solution/frueh/WISSENSSPRUNG.md) kennt V16 auf 7261020/P0 nur das seit Beginn von Match 2 bekannte, gespiegelte erste Reliktpaar. In seiner vollständig geklärten bekannten Zone gibt es zehn bestätigte Punktefelder und null offene Kandidaten. Von Zug 52 auf Zug 53 steigt Solutions öffentlicher **Matchpunktestand von 281 auf 292**, also um elf. Selbst wenn Solution alle zehn bekannten Punktefelder gleichzeitig besetzt hält, können diese in einem Zug nur zehn Punkte bringen. Da das erste Paar allein keine Punkte außerhalb seiner beiden 5×5-Zonen erzeugt, deutet der elfte Punkt auf ein zusätzliches, noch nicht entdecktes Punktegebiet. Die Überlegung setzt voraus, dass bisherige Beweise des alten Gebiets korrekt sind. Neue Freischaltungen können frühere Nullfelder wirksam machen und damit genau diesen Überschuss erklären.

[Der Offline-Test](oeffentlicher_hinweis.py) verlangt auf beiden Seiten der zeitlich ausgerichteten Beobachtung dasselbe alte, schon zu Matchbeginn bekannte Paar, null offene Kandidaten und eine unveränderte Menge bestätigter Punktefelder. Er vergleicht nur benachbarte Schritte desselben Matches für Zug 50–100. Ein Zurücksetzen der Matchpunkte wird dadurch nicht als Zuwachs gewertet. Obergrenze ist die **Gesamtzahl** aller bereits bestätigten Felder, unabhängig davon, auf welchen Feldern ein Gegner sichtbar ist. Die Daten der Engine-Kartenprüfung gehen nicht in diesen Test ein.

| Öffentlicher V16-Verlauf | Auswertbare Züge | Züge mit Überschuss | Erstes Signal |
|---|---:|---:|---|
| 7261020, Player 0 | 45 | 13 | Zug 53, 11 > 10; die spätere Sichtung war in Zug 95 |
| 7267071, Player 0 | 51 | 0 | Keines, obwohl R3 im eigenen Verlauf später ein zweites Paar sichtete |

**Unterschied zum vorhandenen `Belief._check_spawn_proof`.** Der vorhandene, bei den zwei geladenen Paketen inaktive Schalter prüft den **eigenen** Punktzuwachs gegen die Anzahl eigener besetzter, bestätigter oder im bekannten Reliktgebiet noch möglicher Felder. Er kann bislang verdeckten Spawn für die frühere Inferenz vor Zug 50 nachweisen. Der hier offline betrachtete Vorschlag nutzt **gegnerischen** Punktzuwachs, benötigt dessen Einheitenpositionen nicht und soll höchstens einen Suchauftrag **nach** dem Spawnfenster auslösen. Er verrät dem Agenten keine Zielkoordinate und nie anhand von Engine-Parametern, dass auf einer Karte nur ein Paar existiert. Ob das Signal auf unabhängigen Karten häufig, früh und präzise genug ist, bleibt offen. Eine Trefferzahl unter mehreren aufeinanderfolgenden Zügen ist keine Anzahl unabhängiger Fälle. [Öffentliche Auswertung samt beiden R3-Gegenverläufen](oeffentlicher_hinweis.json)


## Vollständigkeit und Grenzen

Das Panel war vor dem ersten Technikspiel fixiert: Seeds 94651000–94651015, beide Startseiten. 128 gepaarte Partien gegen die externen Gegner und 32 direkte Duelle, insgesamt 48.480 echte Spielzüge. Geprüft wurden alle 160 unterschiedlichen Kombinationen, 303 Schritte und drei Matchausgänge pro Spiel, konsistente Ergebnisse bei unverändertem Verhalten sowie die Identität von Abgabe, Kandidat und Regelplan. Die [Rohdaten](frisch.json) haben SHA-256 `d0ae225883014cd598d375edd613b1a1c5a0fad9dbaeba332e831eadb454b0ae`.

Die Messung wurde bei drei gesicherten Sitzzeilen vor dem ersten direkten Duell für eine zusätzliche passive Kontrolle des direkten Gegners und des entfernten Suchziels unterbrochen. Bei der Fortsetzung wurden die drei vollständigen Ergebnisse übernommen und die gerade unvollständige Partie neu gespielt. In 95 überwachten Kandidatenpartien trat der in [der Technikprüfung](TECHNIK.md) beschriebene Fernziel-Sonderfall keinmal auf. Für genau eine aktive Kandidatenpartie (94651000, Player 0, Solution) fehlt dieser Zähler. Der veröffentlichte Agent und die Gewichte wurden in diesem Versuch nicht ausgetauscht.

[Ergebnisse auswerten](auswerten.py) · [Spielvergleich reproduzieren](spielen.py) · [Kartenprüfung ohne weitere Spiele](kartenpruefung.py) · [Kartenparameter nach dem Test](kartenpruefung.json) · [Vorabplan](PLAN.md)

```sh
pfad=experiments/analysis/v16_finalwoche_20261122/kundschafter
python "$pfad/auswerten.py" "$pfad/frisch.json"
# In der Projekt-Pythonumgebung, Ausgabe an einen neuen Pfad:
python "$pfad/spielen.py" frisch --out /tmp/sherlock-scout-frisch-erneut.json
```
