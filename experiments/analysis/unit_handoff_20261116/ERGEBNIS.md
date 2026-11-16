# Übergabe von R3 an V15 pro Einheit

**Ein Vorteil gegenüber R3 gegen Solution ist auf diesen Karten nicht nachgewiesen. R3 bleibt für die Abgabe freigegeben.**

## Was die Replays hergaben

In fünf archivierten Partien mit unterschiedlichen Ergebnissen der Elternmischungen wurden 1.485 Stellungen mit bekannten Befehlen beider Eltern auf derselben Stellung geprüft. Es gab 88 einzeln mögliche V15-Bewegungen in 78 Stellungen. 79 dieser Übernahmen lassen sich im jeweiligen Teamzug gemeinsam ausführen. Nur sechs Einzeloptionen lagen im früheren Öffnungsfenster der Matches zwei und drei. Die Live-Auswahl wurde auf allen 1.485 Stellungen gegen die separat rekonstruierte Auswahl nach Einheit und Ziel überprüft. [Einzelfälle, doppelt gewählte Ziele und Grenzen der Projektion](replays/ERGEBNIS.md).

## Feste Spielregel

R3 plant den gesamten Teamzug. Eine Einheit erhält den V15-Bewegungsbefehl, wenn sie ein momentan von keiner sichtbaren Einheit besetztes bestätigtes Punktefeld zusätzlich erreichen kann. Alle aktuell selbst besetzten bestätigten Felder und alle von R3 eingeplanten Punktefelder müssen im projizierten Teamzug weiterhin abgedeckt sein. Felder werden pro Zug einmal reserviert. Energie, bekannte Asteroiden, Kartenrand und die Spiegelung für Spieler 1 werden berücksichtigt. In den Matches eins bis drei ist die Regel in den Zügen 1–99 aktiv. Die beiden Berater erhalten die tatsächlich gespielten Befehle. [Festlegung vor den Spielen](PLAN.md).

## Gegen die originale Solution

Auf 40 weiteren Karten spielte jeder Agent beide Startseiten. Die Regel gewann **80/80**, Original-R3 **80/80**. Die Differenz beträgt +0,00 Prozentpunkte (95-%-Kartenintervall +0,00 bis +0,00). Ganze Karten wurden 10.000-mal mit Zurücklegen gezogen, wobei beide Sitze einer Karte zusammenbleiben. Da auf keiner dieser Karten ein Spielausgang voneinander abweicht, liefern alle Bootstrap-Ziehungen dieselbe Differenz von null. Andere Karten können die beiden Versionen unterscheiden.

- Zusätzliche Siege (0): keine.
- Abgegebene Siege (0): keine.

## Zusätzlicher Vergleich auf historischen Karten

Nach dem Ergebnis von zweimal 80/80 auf neuen Sitzen wurde für dieselbe Regel ein fester früherer Kartenblock gewählt. Alle 80 Sitze der ersten 40 Karten der früheren 400-Karten-Reihe sind enthalten. Die archivierten nativen Referenzdateien wurden anhand ihrer SHA-256 und je Sitz geprüft. Der Kandidat gewann **76/80**, Original-R3 **76/80**, Original-V15 **80/80**. Gegenüber R3 gewann er ein zusätzliches Spiel und verlor einen früheren R3-Sieg. Das entspricht +0,00 Prozentpunkten (95-%-Kartenintervall -3,75 bis +3,75). Zusätzliche Siege: 7158030/P0. Abgegebene Siege: 7158016/P0. Die früheren Referenzwerte waren bekannt. Dieser nachgelagerte historische Vergleich ist separat von der neuen Kartenstichprobe zu lesen. [Festlegung](ZUSATZVERGLEICH.md) · [Kennzahlen](archiv.json) · [80 vollständige Zusatzpartien](archiv/games.jsonl).

## Direktduelle

| Gegner | Übergabe pro Einheit | Frühere Übergabe ab Match zwei | Frühere Mischung mit Kontaktroute |
|---|---:|---:|---:|
| R3 | 18/32 | 20/32 | 30/32 |
| V15 | 6/32 | 14/32 | 18/32 |

Alle drei Spalten nutzen dieselben 16 Duellkarten mit beiden Startseiten. Die Referenzspalten stammen aus den abgeschlossenen, nach Karten und Sitz zugeordneten Reihen. Original-R3 gewann auf diesen Karten 6/32 gegen V15. Gegen R3 lag die neue Regel gegenüber der früheren Mischung mit Kontaktroute bei −37,50 Prozentpunkten (95-%-Kartenintervall -62,50 bis -15,62), gegen V15 bei −37,50 Prozentpunkten (95-%-Kartenintervall -62,50 bis -12,50). Die direkte Siegquote gegen R3 beträgt 56,25 % (95-%-Kartenintervall 34,38 bis 75,00 %), gegen V15 sind es 18,75 % (0,00 bis 37,50 %).

## Erreichte die Einheit das Feld wirklich?

| Spielreihe | Spiele mit mindestens einer Übergabe | Übernommene Bewegungen | Beauftragte Einheit danach am Ziel | Züge mit allen geplanten Feldern und allen zusätzlichen Zielen tatsächlich besetzt / Züge mit Übergabe |
|---|---:|---:|---:|---:|
| Solution, weitere Karten | 80/80 | 679 | 672 | 634/656 |
| Direkt gegen R3 | 32/32 | 237 | 232 | 221/230 |
| Direkt gegen V15 | 32/32 | 218 | 212 | 196/214 |
| Fünf Diagnosesitze | 5/5 | 38 | 37 | 36/38 |

Die rechte Spalte vergleicht die Projektion vor der Aktion mit den lebenden eigenen Einheiten in der nächsten öffentlichen Beobachtung. Ein Zug kann mehrere Übergaben enthalten. Ein Kampf oder der gleichzeitige Gegenzug kann die tatsächliche Belegung ändern. Der Gegenverlauf zu einem einzelnen Alternativbefehl wurde nicht ausgespielt.

## Fünf vorab bekannte Diagnosesitze

| Karte / Sitz | Original-R3, gewonnene:verlorene Matches | Übergabe pro Einheit | Übernommene Bewegungen |
|---|---:|---:|---:|
| 7151043/P0 | 2:1 | 1:2 | 8 |
| 7151059/P1 | 1:2 | 2:1 | 3 |
| 7151068/P0 | 2:1 | 2:1 | 9 |
| 7151073/P0 | 1:2 | 2:1 | 8 |
| 7151094/P1 | 2:1 | 3:0 | 10 |

Diese fünf Partien wurden gezielt gewählt. Die neue Siegquote gegen Solution enthält ausschließlich die separaten 80 Sitze.

## Nachrechnen

Die 229 vollständig beendeten Spiele stehen in [spiele/games.jsonl](spiele/games.jsonl). Jede Partie umfasst 303 Schritte und drei Matchentscheidungen. Mit dem Projekt-Python aus dem Studienverzeichnis startet `python -B pruefe_replays.py` den Vergleich der beiden Auswahlverfahren, `python -B bericht.py` validiert die Dateien und berechnet die [Kennzahlen](auswertung.json) erneut. Für neue Spiele die [historische Laufzeit](../r3_v15_blend_20261116/REPRODUKTION.md) wiederherstellen und `python -B duelle.py --runtime LAUFZEIT --out NEUER_ORDNER` ausführen. Abgabe-SHA-256: `8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d`.

Den separaten Archivvergleich reproduzieren `duelle.py --archiv` mit denselben Laufzeit- und Ausgabeoptionen und `python -B archivergebnis.py`.
