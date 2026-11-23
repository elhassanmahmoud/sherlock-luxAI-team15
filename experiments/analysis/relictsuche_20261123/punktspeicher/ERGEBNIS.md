# Öffentliche Punktebeweise auf 40 neuen Sicht-1-Karten

**Auf 12 von 40 neuen Karten konnte Sherlock ein tatsächliches Punktefeld früher sicher erkennen als V16. Auf fünf dieser Karten hatte ein freies Schiff einen sichtbaren, freien Zielpunkt in höchstens vier Zügen in Reichweite.** Auf einer dieser fünf Karten verdankte es die Gelegenheit ausschließlich dem über die Matchgrenze bewahrten Beweis. Die Messung beobachtete die unveränderten Befehle von V16 gegen die originale Solution. Sie misst erreichbare Ziele. Ob eine geänderte Fahrt zusätzliche Punkte oder Siege bringt, müssen aktive Duelle zeigen.

## Frische Karten auf beiden Sitzen

Die ersten 40 Sicht-1-Karten ab Seed 162300000 ergaben 80 vollständige Partien. Ein Spiegelpaar zählt pro Karte einmal, selbst wenn beide Startseiten es beweisen. Ein Paarzug ist eine Beobachtung auf einem Sitz, zu der die Eigenschaft für ein Paar gilt. Wiederholte Paarzüge können also denselben offenen Befund betreffen.

| Beobachtete Situation | Karten von 40 | Sitze von 80 | Spiegelpaare je Karte gezählt | Paarzüge M1 / M2 / M3 |
|---|---:|---:|---:|---:|
| Sicheres aktives Feld, das V16 noch nicht kennt | 12 | 14 | 14 | 42 / 161 / 181 |
| Sichtbares freies Ziel über höchstens vier Schritte erreichbar | 5 | 5 | 5 | 4 / 32 / 7 |
| Dasselbe Ziel mit einem abweichenden Schritt erreichbar | 3 | 3 | 3 | 0 / 7 / 6 |
| Vorteil gegenüber dem identischen Beweiser mit Löschung am Matchende | 2 | 2 | 2 | 0 / 59 / 63 |
| Davon Ziel in höchstens vier Schritten erreichbar | 1 | 1 | 1 | 0 / 27 / 0 |
| Mit dem öffentlichen Beweis zugleich als falsch leer widerlegt | 1 | 1 | 1 | 0 / 0 / 2 |
| Laut Schiedsrichter zu diesem Zeitpunkt fälschlich von V16 als leer markiert | 17 | 31 | 63 | 0 / 1.026 / 689 |

Der Vorsprung betraf sechs P0- und acht P1-Sitze, zusammen 16 Sitz-Paare. V16 bestätigte alle 16 später. Der Vorsprung betrug 2 bis 65 Züge, der Median lag bei 16,5 Zügen. In 15 Fällen waren es mindestens drei Züge. Auf fünf Sitzen war ein alternativer Weg möglich, davon einer auf P0 und vier auf P1. Für jeden gezählten Weg stand ein Schiff mit ausreichender Anfangsenergie und einem legalen, abweichenden ersten Schritt bereit. Ziel und Weg wurden anhand der öffentlich bekannten passierbaren Felder geprüft. Spätere Gegnerzüge und Geländedrift können die Ankunft beeinflussen. [Zählung je Karte, Sitz und Match](frisch/ergebnis.json) · [Wege und Beweiszeitpunkte](frisch/beweise.jsonl.gz)

**Was genau die Matchgrenze beitrug.** Auf `162300044/P1` bewies die eigene Gutschrift das Spiegelpaar `(15,2)` und `(21,8)` mit der letzten Beobachtung im ersten Match. V16 bestätigte es erst bei Zug 59 im zweiten Match. Das vorangegangene Wissen eröffnete 27 Paarzüge mit einem Weg von höchstens vier Schritten, davon sieben mit einem direkten Schritt. Bei Zug 24 im zweiten Match stand Schiff 1 auf `(20,8)` neben dem freien Zielfeld `(21,8)`. Auf `162300029/P1` blieb der frühere Beweis über die ersten 63 Beobachtungen von Match 3 verfügbar. Hier fand sich kein freier Weg bis vier Schritte. Zusammen ergeben sich 122 zusätzliche Paarzüge durch das Speichern. Für alle 122 war das jeweilige Feld bereits im unmittelbar vorherigen Match sicher bewiesen. [Festgelegter Vergleich mit Löschung](GEGENPROBE.md) · [Gesamte öffentliche Spielverläufe](frisch/beobachtungen.jsonl.gz)

**Wie oft ein falsches Leerurteil widerlegbar war.** Im frischen Panel führte V16 auf 17 Karten mindestens ein tatsächlich aktives Spiegelpaar als leer. Der Speicher konnte dies auf `162300168/P0` für das Paar `(5,2)` und `(21,18)` öffentlich beweisen, bei Zug 39 und 40 im dritten Match. Ein freies Schiff hätte dieses Paar zu diesen Zeitpunkten unter den festgelegten Bedingungen nicht in vier Schritten erreicht. V16 führte während der 80 Spiele kein tatsächlich inaktives Feld als positiv. Diese Vergleiche mit der verdeckten Spielmaske dienten erst der Prüfung nach der öffentlichen Ableitung. [Unabhängige Rechnung](frisch/gegenrechnung.json)

## Die zwei bekannten Verlustkarten

Auf `161620068` ließ sich das strittige Spiegelpaar `(3,2)` und `(21,20)` auf beiden Sitzen bei **Zug 25 im zweiten Match** aus zwei öffentlichen Gutschriften beweisen. Bei Zug 21 zählte die frühere Belegung sechs Punkte, bei Zug 25 die aktuelle Belegung fünf. Zieht man die gemeinsamen Teile beider Belegungen ab, ergibt sich für Sitz 0

`x(3,2) − x(0,0) − x(6,7) ≥ 1`.

Für Sitz 1 steht zusätzlich `−x(2,3)` links. Alle Werte sind null oder eins. Damit muss `x(3,2)` auf beiden Sitzen eins sein. V16 bestätigte den Punkt auf P0 bis Spielende nie und auf P1 erst bei Zug 83 im dritten Match. Der öffentliche Beweis widerlegte die aktuelle Leermarkierung während je 117 Paarzügen. Beide Sitze gemeinsam hatten 252 Paarzüge mit diesem falschen Leerurteil, darunter 234 ab dem Beweis.

Ein direkter Alternativschritt auf dieses strittige Paar stand auf keinem der beiden Sitze zur Verfügung. Wege von zwei bis vier Zügen gab es auf P0 bei 13 und auf P1 bei 29 Beobachtungen im zweiten Match. So hätte P0-Schiff 0 bei Zug 34 von `(3,4)` über `(3,3)` nach `(3,2)` fahren können. P1-Schiff 7 hatte bei Zug 38 den Weg von `(19,20)` über `(20,20)` nach `(21,20)`. Die primäre Entdeckung gelang bereits innerhalb desselben Matches. Das Speichern ersparte im dritten Match auf beiden Sitzen jeweils weitere 15 Beobachtungen bis zur erneuten Herleitung. In diesem zusätzlichen Zeitraum erfüllte kein Weg die Vier-Schritt-Bedingung. [Beweise und originale Aktionsprüfsummen](archiv/beweise.jsonl.gz) · [Frühere Zuordnung der gegnerischen Punkte](../fruehepunkte/ERGEBNIS.md)

Auf `161620111/P1` erkannte der Speicher das Paar `(3,3)` und `(20,20)` bei Zug 44 im dritten Match, 50 Züge vor V16. Bei Zug 47 hätte Schiff 13 von `(20,19)` unmittelbar auf `(20,20)` fahren können. Auf P0 erbrachte diese Karte keinen früheren Beweis. Alle vier nachgespielten Archivpartien reproduzierten die früheren Aktionsprüfsummen und sämtliche Matchstände. Die beiden Karten waren anhand bekannter Niederlagen ausgewählt und gehen getrennt von den 40 neuen Karten in den Bericht ein. [Archivzählung](archiv/ergebnis.json) · [Archivnachrechnung](archiv/gegenrechnung.json)

## Korrektheit und frühere Arbeiten

Die unabhängige ganzzahlige Nachrechnung widerlegte für alle **627 positiven Erstbeweise** die Annahme, das jeweilige Spiegelpaar könne null sein. Sie verarbeitete 33 Archiv- und 594 Frischbeweise. Der Abgleich aller 25.452 Beobachtungen mit der echten, zum jeweiligen Zug aktiven Wertungsmaske fand keinen falschen positiven Beweis und kein falsches temporäres Nullfeld. Geprüft wurden 78.959 positive und 794.737 negative Paarzustände im Hauptspeicher sowie 25.200 tatsächliche öffentliche Gutschriften. Die Matchanfänge lieferten keine Wertungsgleichung. Eine unabhängige Wegsuche reproduzierte alle Reichweiten. In kleinen synthetischen Welten deckte die vollständige Aufzählung 9.600 reguläre Beobachtungen ab, darunter gestapelte Einheiten, beide Spiegelendpunkte und die Aktivierung neuer Punkte. [Aufzählung](kleinwelten.json) · [Öffentliche Beweisregeln](PLAN.md) · [Reproduktion und Datenschema](AUSFUEHRUNG.md)

Die Frühsuche vom 22.11. fand auf 46 Archivplätzen vier Sitz-Paare mit mindestens drei Zügen Vorsprung. Sie betrachtete die ersten 50 Züge und jeweils zwölf frühere Beobachtungen. Die frühere Gauß-Studie mit V14 fand auf 168 Vollspielen ein früher erkanntes positives Spiegelpaar für einen Zug. Der jetzige Versuch verfolgt mit V16 dieselben bewiesenen positiven Felder über alle drei Matches und prüft ihren Vorteil zusätzlich gegen eine identische Rechnung mit Löschung am Matchende. [Frühsuche](../../v16_finalwoche_20261122/fruehbeweis/ERGEBNIS.md) · [Gauß-Studie vom 02.11.](https://github.com/elhassanmahmoud/sherlock-luxAI-team15/blob/92648c13ee390f1a88647fe6fc8b241e852d6452/experiments/analysis/gauss_admission_20261102/RESULTS.md)
