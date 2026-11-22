# Wie R3 in Match 2 das zweite Reliktpaar entdeckt

Auf den zwei Karten mit der größten [frühen Wissenslücke](ERGEBNIS.md) spielt R3 eine Einheit in Sichtweite eines weiteren Relikts. Neue eigene Punktebeobachtungen in dessen Umgebung bestätigen zusätzliche Felder. Beide Originalagenten verwenden in diesen Spielen dieselben 18 wirksamen Einstellungen ihres Kartenwissens. Die paarweise identischen Anfangszahlen laufen erst auseinander, als die Agenten verschiedene Orte beobachten.

| Karte, Match 2, Player 0 | Was R3 erstmals sieht | Was V16 sieht | Bestätigte Felder zu Beginn von Match 3 |
|---|---|---|---|
| 7261020 | Zug 72, zweites Reliktpaar durch Sichtung bei (3, 6); Zug 74 erster neuer Feldbeweis | Zug 95, Sichtung desselben Relikts und erster neuer Feldbeweis | R3 22, V16 12 |
| 7267071 | Zug 61, zweites Reliktpaar durch Sichtung bei (4, 14); gleichzeitig erster neuer Feldbeweis | Das Paar taucht im gesamten zweiten Match in keiner öffentlichen Beobachtung von V16 auf | R3 22, V16 12 |

### Karte 7261020

Beide Agenten beginnen Match 2 mit zehn bestätigten Punkten und einem bekannten Reliktpaar. In R3s Zug 71 steht Einheit 14 auf (3, 5) mit 155 Energie. Nach ihrem Schritt nach unten steht sie in Zug 72 auf (3, 6) mit 151 Energie. Das Relikt bei (3, 6) wird sichtbar, sein Spiegelpartner wird ins Gedächtnis eingetragen. In den jetzt bekannten Reliktzonen bleiben 42 Kandidaten offen. Auf seiner eigenen Partie kennt V16 in Zug 72 weiterhin nur das erste Paar.

R3s Einheit 14 zieht weiter auf (4, 6), Einheit 15 auf (5, 6). Aus dem öffentlichen Punktezuwachs nach Abzug der bekannten Felder ergibt sich in Zug 73 für diese beiden Positionen zusammen **ein Punkt**. In Zug 74 ergibt sich für (5, 6) allein **null**. Das beweist (4, 6); die Symmetrie bestätigt zugleich (17, 19). Der erste Beweis entsteht damit, obwohl im Moment des Beweises keine der beiden Einheiten mehr auf (4, 6) steht. Spätere Beweise in Zug 82, 89, 93 und 96 bringen den Zähler auf 22. V16 sieht das neue Relikt erstmals in Zug 95, während seine Einheit 14 mit 291 Energie auf (3, 5) steht. Für (3, 5) ergibt sich der eindeutige Rest von einem Punkt. Mit dessen Spiegelfeld kennt V16 nun zwölf.

### Karte 7267071

Beide Agenten starten mit zwölf bestätigten Feldern. R3s Einheit 15 zieht von (1, 13) mit 41 Energie in Zug 60 nach (2, 13) mit 43 Energie in Zug 61. Das Relikt bei (4, 14) wird in R3s Beobachtung sichtbar. Der eigene Punktestand steigt um sieben; nach Berücksichtigung der bereits bekannten Felder bleibt **ein Punkt für genau ein Feld**, (2, 13). R3 bestätigt dieses und dessen Spiegelposition (10, 21). Weitere öffentliche Beobachtungen in Zug 69, 78 und 100 bringen die Gesamtzahl auf 22. V16 erhält auf seiner eigenen Partie in Match 2 keine Sichtung dieses zweiten Paars und macht keinen neuen Feldbeweis. Sein öffentlicher Punktezuwachs in Zug 61 ist vier.

### Konkreter Versuch

Bei Zug 50 hatte V16 auf beiden Karten nur ein bekanntes Reliktpaar und keinerlei ungeprüfte Felder mehr in dessen Umgebung. Gleichzeitig standen zehn beziehungsweise zwölf eigene Einheiten mit mehr als 20 Energie außerhalb bestätigter Punktefelder. Dieser Filter beschreibt den beobachteten Zustand, die Schwelle 20 dient nur der Zählung. Andere Aufgaben, Schüsse und unbekannte Gefahren können eine Einheit weiterhin binden.

Für einen kleinen Vergleich bietet sich **ein einzelner zeitlich begrenzter Suchauftrag** an. Wenn in Match 2 nach dem Spawnfenster erst ein Paar bekannt ist und dessen Umfeld bereits ausgewertet ist, könnte eine geeignete freie Einheit noch ungesehene Gebiete erkunden. Nur öffentliche Informationen als Auslöser und Ziel verwenden; die versteckte Position des zweiten Relikts steht im Spiel nicht zur Verfügung. Suchdauer vorab begrenzen, damit auf Karten ohne zweites Paar möglichst wenige Züge verloren gehen. Zuerst frühere Sichtung, neue Feldbeweise und tatsächliche Mehrpunkte messen. Ein separater Vergleich mit der Originalversion muss anschließend zeigen, ob mehr ganze Spiele gewonnen werden. Die zwei ausgesuchten Karten belegen den Mechanismus; sie belegen keine allgemeine Erfolgsaussicht einer bestimmten Suchroute.

### Rückprüfung

Die vier Originalpartien reproduzierten alle archivierten Endpunkte und Einzelmatchergebnisse. Erfasst wurden ausschließlich die öffentlichen Beobachtungen des Player 0, seine echten Befehle, der Wissensstand nach der Beobachtung sowie die tatsächlich ausgelösten Rechenschritte beim Bestätigen neuer Punktefelder. Jede neu bestätigte Koordinate wurde im zweiten Match und am Übergang zum dritten Match genau einem direkten Beweis oder dessen Symmetriepartner zugeordnet. Der direkte Vergleich der 18 wirksamen Einstellungen umfasste unter anderem Symmetrie, die frühe Schlussfolgerung, den Filter auf Reliktzonen, Teilmengen-Schlüsse und die deaktivierten gegnerischen Punktbeweise. Positionsangaben gelten im Weltkoordinatensystem, Punktegleichungen betreffen eigene Einheiten der jeweiligen Partie.

[Messskript](wissenssprung.py) · [Alle zeitlich aufgelösten Beobachtungen und auslösenden Gleichungen](wissenssprung.json.gz)

```sh
python experiments/analysis/v16_finalwoche_20261122/solution/frueh/wissenssprung.py
```
