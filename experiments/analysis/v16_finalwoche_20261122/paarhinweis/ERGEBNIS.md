# Ein zweites Reliktpaar an den öffentlichen Punkten erkennen

Auf beiden untersuchten V16-Karten war ein zusätzliches Punktegebiet aus der **Summe der gleichzeitig erzielten Punkte beider Teams** ableitbar, bevor V16 es selbst gesehen hatte. Auf Karte 7267071 blieb der frühere Test, der nur den Gegner betrachtete, während des gesamten zweiten Matches stumm. In Zug 70 erzielten Sherlock und Solution dort zusammen 14 Punkte. Die bekannte Reliktumgebung erlaubte höchstens zwölf. Die noch unbekannte Position des Relikts lässt sich aus dieser Zahl allein nicht bestimmen.

| Bestehende öffentliche Partie, Match 2, Player 0 | Erster Summenhinweis ab Zug 50 | Bisheriger Nur-Gegner-Hinweis | Zugschritte mit Summenhinweis / auswertbare Schritte |
|---|---|---|---:|
| V16, 7261020 | Zug 50: **5 + 10 > 10** | Zug 53 | 45 / 45 |
| V16, 7267071 | Zug 70: **5 + 9 > 12** | keiner | 31 / 51 |
| R3, 7261020 | Zug 50: 5 + 11 > 10 | Zug 50 | 22 / 22 |
| R3, 7267071 | Zug 50: 6 + 7 > 12 | keiner | 11 / 11 |

Bei V16 stiegen die beobachteten Matchstände von Zug 49 auf 50 auf der ersten Karte von (120, 251) auf (125, 261), auf der zweiten von Zug 69 auf 70 von (224, 276) auf (229, 285). Spätere direkte Zweitpaar-Sichtung von V16: Zug 95 auf der ersten Karte und keine im zweiten Match auf der zweiten. R3s Sichtungen (Zug 72 bzw. 61) stammen aus R3s eigenen Spielverläufen.

## Herleitung aus der Kurs-Engine

1. **Zusammenstoß.** Nach Bewegung und Schüssen berechnet die Engine die Besetzung und die Energie beider Stapel am jeweiligen Feld. Sind beide Teams vertreten, überlebt ein Team nur, wenn seine Gesamtenergie dort **strikt größer** ist als die des anderen. Die Auswertungen für beide Seiten verwenden dieselben vor dem ersten Entfernen berechneten Karten. Bei Gleichstand werden beide Stapel entfernt. Dadurch kann nach der Kollision höchstens ein Team ein normales Feld werten. Quelle: `luxai_s3/env.py`, Funktionen `compute_unit_counts_map` und `step_env`, Zeilen 43–69 und 426–500.

2. **Energie und Nachwuchs.** Anschließend ändern Energiefeld und Umgebungsschaden Energie, aber weder Positionen noch Überlebensmasken der ausgeschiedenen Einheiten. Nur die nachfolgende Erzeugung einer neuen Einheit kann vor der Wertung eine neue teamübergreifende Doppelbesetzung erzeugen. Player 0 spawnt ausschließlich auf (0, 0), Player 1 auf (23, 23). Steht auf einer solchen Ecke bereits eine überlebende gegnerische Einheit und ist die Ecke ein Punktefeld, können beide Teams dort im selben Zug punkten. Deshalb wird je möglicher Punkte-Startecke ein zusätzlicher Punkt zugelassen, selbst in Zügen ohne Spawn. Sensorberechnung und Terrain-/Energiedrift nach dem Spawn verschieben keine Einheit mehr. Quelle: `env.py`, Zeilen 500–693.

3. **Zählung.** Die Engine zählt erneut die maskierten Einheiten mit nichtnegativer Energie, reduziert pro Team jede Position auf „mindestens eine“ und summiert die tatsächlich freigeschalteten Punktefelder. Mehrere eigene Schiffe derselben Seite bringen damit keinen Mehrpunkt, Reliktüberlappungen werden einmal gezählt. Die Generatorfunktion `gen_state` erzeugt die Feldmasken innerhalb der Kartengrenzen aus den beiden lokalen 5×5-Mustern eines Paars. Jede neue Paaraktivierung kann zu den nutzbaren Feldern hinzufügen. Quelle: `env.py`, Zeilen 695–707, sowie `luxai_s3/state.py`, Zeilen 182–225 und 343–350.

Unter der Hypothese „nur das bereits bekannte erste Paar ist aktiv“ sei **P** die Menge seiner bestätigten **und noch ungeklärten** möglichen Punktefelder. Bei korrektem Gedächtnis gilt für einen Zug:

```text
ΔPunkte eigenes Team + ΔPunkte Gegner
    ≤ Anzahl verschiedener Felder in P
      + Anzahl der Starterecken in P.
```

Beispiel für die Eckkorrektur: Wenn zwei mögliche Punktefelder existieren und eines davon die eigene Starterecke ist, kann der gemeinsame Gewinn bis zu drei betragen. Erst vier Punkte würden die Hypothese ausschließen. Ein Unterschreiten der Schranke liefert keinerlei Aussage darüber, ob ein weiteres Paar existiert.

## Welche Daten in den Test eingehen

Das Skript liest nur beobachtete Teamstände und das tatsächlich aufgebaute Gedächtnis der zwei Spielerpakete, jeweils auf deren eigener Partie. Beide Beobachtungen (Zug (t-1) und (t)) müssen zum selben Match gehören und direkte Nachbarn sein. Es zählt die Differenz der **Matchpunkte**, keine Matchsiege und keine Differenz über einen Reset. Die letzte zum Folgematch zurückgesetzte Anzeige wird ausgelassen. Beide Zeitpunkte müssen dieselbe bekannte Reliktpaarung wie bei Beginn von Match 2, unveränderte bestätigte Felder sowie null offene Kandidaten aufweisen. Die Bestätigungsmenge wird nach Koordinaten dedupliziert. Bei den ersten hier ausgewiesenen Überschreitungen war keine Starterecke enthalten. In Situationen mit offenen Kandidaten darf man deren Beitrag oder eine mögliche unentschiedene Ecke keinesfalls unterschlagen. Der verwendete Beobachtungsdatensatz speichert dafür nur die Anzahl offener Kandidaten; er wird konservativ nur bei vollständig geklärtem Gebiet ausgewertet.

Der ältere `_check_spawn_proof` verwendet die **eigenen** besetzten potenziell punktenden Felder und den **eigenen** Zuwachs. Der frühere [Nur-Gegner-Test](../kundschafter/oeffentlicher_hinweis.py) nutzt eine globale Obergrenze nur für den Gegenzuwachs. Diese Auswertung fügt erstmals die über beide Teams geteilte Gesamtkapazität hinzu.

## Aussage für einen neuen Suchauftrag

Eine getrennte [Kontrolle auf drei archivierten Demokarten](archivkontrolle/ERGEBNIS.md) ergab auf der einzigen Karte ohne zweites Paar keinen Fehlalarm. Auf den beiden anderen Karten war das zusätzliche Paar bereits vor Zug 50 bekannt. Wie oft das Signal bei einem spielenden V16 früh genug kommt, bleibt offen.

Der Beleg gilt für **zwei nach dem Ausgang ausgewählte Problemkarten**, jeweils aus zwei verschiedenen Spielverläufen. 45 Überschreitungen auf derselben Karte sind kein Befund auf 45 unabhängigen Karten. Sobald ein Gedächtnis Felder fälschlich ausschließt oder eine Reliktzone falsch rekonstruiert, kann auch das Summensignal falsch auslösen. Die Engineprüfung belegt die geometrische Schranke, nicht die Unfehlbarkeit des Agentengedächtnisses.

Vor einer Änderung sollten die öffentliche Bedingung, Öffnungszeit und Auswertung eingefroren werden. Dann auf unabhängigen, vorab gezogenen Karten für gewöhnliches V16 prüfen, wann ein Signal vor der eigenen Sichtung erscheint, ob es auf Ein-Paar-Karten fälschlich feuert und ob noch genug Matchzüge sowie eine geeignete Einheit zur Verfügung stehen. Versteckte Spawnpläne dienen allenfalls der externen Bewertung nach dem Spiel und dürfen weder die Stichprobe nach Ergebnis sortieren noch den Agenten steuern. Erst ein solcher Blindtest kann einen begrenzten Kundschafter **nach** Auftreten eines gültigen öffentlichen Signals rechtfertigen. Hier wurde weder eine Aktion verändert noch ein weiteres Spiel oder Training gestartet.

[Auswertung](ergebnis.json) · [Code und Eck-Grenzfälle](obergrenze.py) · [Öffentliche Ursprungsdatei](../solution/frueh/wissenssprung.json.gz)

```sh
python experiments/analysis/v16_finalwoche_20261122/paarhinweis/obergrenze.py
```

Das Skript lädt keinen Agenten und startet keine Simulation. Es prüft Version und SHA-256 von `env.py`, `state.py` und des Beobachtungsarchivs. Referenz ist die installierte Kursumgebung `luxai-s3==0.2.1`.
