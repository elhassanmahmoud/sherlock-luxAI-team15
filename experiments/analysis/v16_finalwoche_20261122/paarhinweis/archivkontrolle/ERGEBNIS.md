# Ein unabhängiges Spiel mit nur einem Reliktpaar

Auf **einer** zusätzlichen Ein-Paar-Karte löste die Summenschranke unter beiden öffentlichen Sichtweisen in Match 2 **keinen Fehlalarm** aus. Die weiteren beiden Karten hatten je ein zweites Paar, das beide Teams vor dem frühesten Prüfzeitpunkt in Zug 50 bereits kannten. Damit bleibt offen, wie häufig Sherlock auf neuen Karten ein verborgenes Paar rechtzeitig erkennen kann.

| Demokarte und aufgezeichnete Gegner | Zweites Paar erstmals aktiv | Zweites Paar bekannt, P0 / P1 | Prüffähige Züge, P0 / P1 | Hinweise, P0 / P1 |
|---|---:|---:|---:|---:|
| 7171000 · V15 gegen V14 | keines in Match 2 | – / – | 51 / 30 | 0 / 0 |
| 7171001 · V15 gegen Solution_92 | 15 | 24 / 22 | 0 / 0 | 0 / 0 |
| 7171002 · V15 gegen Kaggle | 40 | 40 / 40 | 0 / 0 | 0 / 0 |

Die 81 prüffähigen Kombinationen aus Team und Zug beschreiben dieselbe Karte und dieselbe Partie. Auf 7171001 hatte zudem keines der Teams zu Beginn von Match 2 beide Positionen des ersten Paares im Gedächtnis. Auf 7171002 kannten beide Teams das zweite Paar bereits in seinem ersten aktiven Zug. Diese Daten liefern keine Schätzung der Sensitivität, der Fehlalarmquote auf anderen Karten oder der Siegquote einer neuen Strategie.

## Daten und Kontrolle

Die [vorab getroffene Auswahl](AUSWAHL.md) enthält alle drei für eine frühere Präsentation reservierten Karten. Ihre Seeds liegen außerhalb der beiden Entwicklungskarten und der 200 Bestätigungskarten. Die gespeicherten Entscheidungen stammen von den in der Tabelle genannten Agenten. Das Gedächtnis stammt aus dem originalen V16-Release samt den am geladenen Agenten protokollierten Einstellungen. Für jedes Team wurden die ersten 202 öffentlichen Beobachtungen verarbeitet, also insgesamt 1.212 Teambeobachtungen. Unsichtbare gegnerische Schiffe, Kartenfelder und Relikte wurden vor der Übergabe an das Gedächtnis maskiert. Erst nach der Auswertung aller Perspektiven wurden die tatsächlich aktivierten Paare in den vollständigen Zuständen nachgeschlagen.

Für drei Zeitpunkte jeder Karte (globale Schritte 0, 149 und 201) wurden beide rekonstruierten Sichtweisen feldweise mit der Originalfunktion der Kurs-Engine verglichen, einschließlich Energiestand, Sicht, Reliktmaske und beider öffentlicher Punktestände. Die Eingabedateien sind durch die ursprünglichen Empfangsbelege und Prüfsummen identifiziert. Alle Daten stammen aus archivierten Spielen.

## Reproduktion

Vom Repo-Hauptverzeichnis mit der vorhandenen Kurs-Python-Umgebung ausführen:

```sh
ordner=experiments/analysis/v16_finalwoche_20261122/paarhinweis/archivkontrolle
python "$ordner/pruefen.py"
python "$ordner/sichtpruefung.py"
```

Die erste Prüfung erzeugt [die kompakte Ergebnistabelle](ergebnis.json). Die zweite vergleicht die öffentliche Sicht an 18 Stellen. Eine spätere positive Prüfung benötigt zuvor abgegrenzte Spiele, in denen das zweite Paar auch ab Zug 50 noch verborgen bleibt. Ob diese Situation häufig genug auftritt, ist eine eigene Frage.
