# Sieben frühe Hinweise in 96 V16-Partien

Original-V16 gewann 94 von 96 Spielen gegen Solution, je 47 von 48 auf beiden Seiten. Der öffentliche Hinweis erkannte **beide verlorenen Spiele** rechtzeitig. Sie lagen auf verschiedenen Karten und Startseiten. Auf weiteren fünf Sitzen meldete er sich rechtzeitig, obwohl V16 das Spiel schon gewann. Das genügt gemäß der [Vorfestlegung](PLAN.md), um einen einzelnen Kundschafter auf denselben Entwicklungskarten zu testen.

| Messung auf 48 Karten | P0 | P1 | beide Sitze |
|---|---:|---:|---:|
| Ganze Spiele gewonnen | 47/48 | 47/48 | 94/96 |
| Zweites Match gewonnen | 45/48 | 46/48 | 91/96 |
| Verborgenes zweites Paar mit mindestens fünf nutzbaren Zügen | 11 | 11 | 22 |
| Rechtzeitiger öffentlicher Hinweis | 3 | 4 | 7 |
| Hinweis, für den Suchauftrag zu spät | 1 | 2 | 3 |
| Rechtzeitiger Hinweis bei Niederlage im zweiten Match | 1 | 1 | 2 |
| Fehlalarme auf echten Ein-Paar-Karten | 0/15 | 0/15 | 0/30 |

**Wie früh?** Auf 160343008/P0 überschritt die Summe der öffentlichen Punktzuwächse die Kapazität des ersten bekannten Reliktpaars in Zug 62, auf 160343014/P1 in Zug 60. In beiden Fällen hatte V16 das zweite Paar bei Ende von Match 2 immer noch nicht im Gedächtnis und verlor Match 2 und das Spiel. Der V16-Teil auf 160343026/P1 meldete bereits in Zug 50; dort sah das Team das Paar in Zug 70 auch auf seiner ursprünglichen Spielbahn. Über die sieben rechtzeitigen Sitze gab es 20 bis 40 Züge bis zur Sichtung oder bis zum letzten Spielzug. Es waren vier verschiedene Karten.

**Was der Hinweis verpasst.** 15 von 22 möglichen Gelegenheiten erhielten keine rechtzeitige Meldung. Alle 15 führten bei unverändertem V16 zu Siegen in Match 2 und im ganzen Spiel. Auf elf dieser Sitze waren in Zug 50 noch Kandidatenfelder offen. Das erklärt eine zu diesem Zeitpunkt fehlende Voraussetzung. Ob dieselben Felder den Hinweis noch später verhinderten, lässt sich anhand dieser Zählung nicht sagen. Für die beiden hier verlorenen Spiele bringt ein bloßes Lockern der Melderegel keinen zusätzlichen Treffer.

**Reichweite der Aussage.** Die 15 Karten mit nur einem aktiven Paar in Match 2 lieferten zusammen 1.018 tatsächlich prüffähige Teamzüge und keinen Fehlalarm. Die zwei Sitze pro Karte und aufeinanderfolgende Züge hängen voneinander ab. Die 7 von 22 Suchgelegenheiten betreffen rückblickend nachweisbar verborgene Paare, deren wahre Existenz die Entscheidung nie verwendet hat. Ob das Umleiten einer tatsächlichen Einheit diese Partien verbessert, misst erst der [Aktionsvergleich](AKTION.md).

[96 kompakte Einzelprotokolle, Teil A](beobachtung/worker_0.jsonl) · [Teil B](beobachtung/worker_1.jsonl) · [Auswertung mit Sitzen und Karten](beobachtung/ergebnis.json) · [Rechenumgebung](umgebung.json) · [Überlappungsprüfung beider Arbeitskopien](seedpruefung.json)

Der Startstand der Suche ist im Bericht zur Kartenüberlappung festgehalten. Nach Veröffentlichung dieser Studie können spätere Teamdokumente auf die reservierten Seeds verweisen. Das ist bei einer Wiederholung der Suche zu berücksichtigen.

Aus dem Projektordner mit aktivierter Kurs-Python-Umgebung:

```sh
d=experiments/analysis/v16_finalwoche_20261122/signalstudie
python "$d/auswerten.py"
```

Die beiden festen Spielhälften lassen sich in einer separaten Projektkopie mit anfangs leerem Ausgabeordner mit `"$d/lauf.sh" 0` und `"$d/lauf.sh" 1` reproduzieren. Bereits vollständig gesicherte Partien überspringt die Wiederaufnahme.
