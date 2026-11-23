# Welche Wirkung hatte die erste gelernte Suchrichtung?

**Auf einer von zehn vorab ausgewählten Karten ließ sich die gelernte Bewegung mit einer ähnlich aussichtsreichen sicheren Gegenrichtung vergleichen.** Auf deren beiden Sitzen gewann V16 eins von zwei Spielen. Ein einziger Schritt in die gelernte Richtung gewann ebenfalls eins, die Gegenrichtung gewann beide. Alle sechs Partien sahen das erste Relikt in Zug 49 und erhielten ihre erste Gutschrift in Zug 48. Die Bedingungen zum Öffnen neuer Karten wurden verfehlt. [Vorabplan](PLAN.md) · [Bilanz](bilanz.json)

## Welche Fälle sich vergleichen ließen

Untersucht wurden die sieben Verlustkarten aus den beiden Punktwissen-Prüfungen sowie die drei V16-Verlustkarten des gemeinsamen Orts- und Flottensuchers aus dessen erster Serie. Beide Sitzseiten waren festgelegt, insgesamt elf ursprüngliche Niederlagen und neun Siege. Für alle 20 Sitze wiederholte die veröffentlichte V16 die archivierte vollständige Weltbefehlsfolge beider Teams, die drei Matchstände, erste Sicht, Gutschrift und den Gesamtausgang. Die erste tatsächlich abweichende Bewegung des ursprünglichen Suchers wurde für jeden Sitz anhand seines archivierten Verlaufs abgeglichen. [Sitzprotokoll](sitzprotokoll.csv)

| Karten, jeweils beide Sitze | Früheste Suchentscheidung | Ergebnis der Richtungspaarung |
|---|---|---|
| 162640213 | Zug 23, Schiff 2 | Beide Sitze zugelassen |
| 162860075, 164050032 | Der gemeinsame Sucher spielte alle Originalbefehle | Vier Sitze ohne Eingriff |
| 162640018 | Sichere Alternativen mit zu abweichender Sicht oder mit anderem Nebel und anderer Energie | Zwei Sitze ausgeschlossen |
| 162640022, 162640027, 162860060 | Die alternativen Ziele unterschieden sich zu stark in Sicht und Energie | Sechs Sitze ausgeschlossen |
| 162640186, 164050141 | Jede Gegenrichtung überschritt mindestens den Energieabstand | Vier Sitze ausgeschlossen |
| 164050036 | Die Alternativen unterschieden sich entweder im Nebelstatus oder in Energie und Sicht | Zwei Sitze ausgeschlossen |

Die Eignung wurde am ersten abweichenden Befehl aus der öffentlichen Beobachtung bestimmt. Vor dem Eingriff stimmten die vollständigen öffentlichen Beobachtungen beider Teams, alle früheren Weltbefehle und sämtliche V16-Vorschläge überein. Im Entscheidungszug blieben auch der gesamte Gegnerzug und die anderen 15 eigenen Befehle identisch. Danach veränderte die äußere Steuerung keinen weiteren V16-Vorschlag. Inklusive der 20 V16-Kontrollen wurden 24 vollständige Partien mit je 303 Zügen überprüft. [Tatsächliche Spielverläufe](partien.jsonl.gz) · [Prüfsummen und Quellen](manifest.json)

## Was auf Karte 162640213 geschah

Schiff 2 sollte auf beiden Sitzen in Zug 23 ursprünglich stehenbleiben. In einheitlicher Kartenorientierung führte der gelernte Schritt auf das Feld (3, 7), die Gegenrichtung auf (4, 8). Beide Ziele waren passierbar und nebelfrei. Ihre öffentlich geschätzten Feldenergien lagen bei 8 und 7. Nach Abzug der übrigen projizierten Flotte versprach der erste Schritt ein neues Feld, der zweite keines. Die tatsächlichen Sichtmasken bestätigten den unmittelbaren Unterschied. Auf jedem Sitz sah das Team direkt danach sieben neue Felder in der gelernten Richtung und sechs in der Gegenrichtung. Acht Züge nach dem Eingriff hatte das gesamte Team in diesen Zweigen 37 bzw. 47 neue Felder gesehen. Die Flotte mit unverändertem V16-Befehl erreichte 46. [Messungen pro Partie](sitzprotokoll.csv)

| Sitz | Befehl in Zug 23 | Match 1 | Match 2 | Match 3 | Ganzes Spiel |
|---|---|---:|---:|---:|---|
| P0 | Original | 157–100 | 488–590 | 850–839 | Sieg |
| P0 | Gelernt | 198–132 | 478–601 | 585–795 | Niederlage |
| P0 | Gegenrichtung | 181–154 | 523–559 | 837–694 | Sieg |
| P1 | Original | 144–142 | 524–564 | 632–717 | Niederlage |
| P1 | Gelernt | 186–106 | 676–618 | 735–809 | Sieg |
| P1 | Gegenrichtung | 201–98 | 629–558 | 686–683 | Sieg |

Auf P1 retteten beide Bewegungen das Spiel bereits durch den Sieg in Match 2. Auf P0 entschied Match 3. Nach Match 2 kannte V16 auf P0 in der Gegenrichtung 16 positive Felder, in der gelernten Richtung zehn. Dasselbe frühe Relikt und dieselbe erste Gutschrift waren somit mit unterschiedlichen späteren Wissensständen und Siegern vereinbar. Die Folgezüge entstanden durch jede jeweilige V16-Fortsetzung mit dem tatsächlich ausgeführten Zug im Gedächtnis. Der Einfluss eines einzelnen späteren Wissensfelds auf den Sieg wurde nicht isoliert.

Zwei gespiegelte Sitze derselben ausgewählten Karte tragen keine übertragbare Aussage zur besten Himmelsrichtung. Der einzelne gelernte Zug zeigt hier auf P1, dass bereits eine frühe Abweichung die spätere Partie drehen kann. Die ebenso sichere Gegenrichtung rettete diesen Sitz ebenfalls. Für die sieben weiteren Karten mit einer abweichenden Bewegung ohne passende Gegenrichtung lässt sich Richtungseinfluss unter den festgelegten Bedingungen nicht trennen. Für eine unabhängige Ursachenstichprobe waren mindestens acht geeignete Sitze auf mindestens vier Karten sowie ein Vorteil des gelernten Einzelzugs bei den Gesamtsiegen und bei Sicht oder Gutschrift verlangt. Keines dieser Kriterien wurde erreicht.

Ein technischer Erststart endete nach dem ersten Originalspiel vor dem Speichern der Auswertung, weil die abschließende Fehlerprüfung mit drei statt zwei Spielern aufgerufen wurde. Der korrigierte Lauf prüfte die beiden Agentenpaare getrennt und spielte diesen Sitz vollständig neu. Seine 24 gespeicherten Spiele bilden die ausgewertete Serie. [Spielsteuerung](spieler.py) · [Prüflauf](spielen.py) · [Auswertung](auswerten.py)
