# Ein zusätzlicher Solution-Sieg in der Entwicklung

Der signalgesteuerte Kundschafter gewann auf den 48 bereits beobachteten Entwicklungskarten **95 von 96** ganzen Spielen gegen Solution, Original-V16 **94 von 96**. Der Unterschied beträgt +1,04 Prozentpunkte. Ein beschreibendes 95-%-Bootstrapintervall mit 20.000 Ziehungen ganzer Karten (RNG 221123) reicht von 0,00 bis +3,13 Prozentpunkten. Er drehte einen bisherigen Verlust, gab keinen bisherigen Sieg ab und erreichte in der Summe genau dieselbe Zahl an Matchsiegen (272 von 288). Der gepaarte Punktesaldo stieg um 1.041 Punkte über 96 Spielsitzvergleiche. In 8 Sitzen auf 5 Karten änderte er insgesamt 29 Befehle. Viermal sah das Team das zweite Reliktpaar früher, nie später.

| Sitz | Siege V16 → Kandidat gegen Solution | Direkt gegen V16 |
|---|---:|---:|
| P0 | 47/48 → 47/48 | 23/48 |
| P1 | 47/48 → 48/48 | 25/48 |
| Zusammen | 94/96 → 95/96 | 48/96 |

Im **Direktduell** gab es exakt eine Karte, auf der der Kundschafter die V16-Befehle änderte, dort auf beiden Sitzen (24 Befehle, ein Sieg). Bei allen anderen 47 Karten waren beide Spieler in beiden Spielen Original-V16 bis zum letzten tatsächlich ausgeführten Befehl. Der Kandidat gewann 47 der 94 unveränderten Sitze und einen der zwei veränderten. Alle reinen V16-Spielverläufe lieferten je Karte auf beiden Sitzen dieselben drei Matchgewinner. Auf der aktiven Karte fehlt hingegen ein komplett unveränderter Spielverlauf als direkter Gegenversuch, weshalb die Ursache des jeweiligen direkten Spielsiegs offenbleibt. Der direkte Gesamtwert ist ein Gleichstand.

## Was die geänderten Bewegungen bewirkten

Die folgende Nachmessung verwendet die **wirklichen öffentlichen Sensorsichten des gesamten Teams**. „Neue Zellen“ zählt erstmals seit Zug 49 gesehene Kartenfelder während des Suchauftrags, einschließlich der Beobachtung nach dem letzten Suchschritt. „Punktefelder“ zählt das bestätigte V16-Wissen in Zug 0 von Match 3. Diese Größen beschreiben unterschiedliche Leistungen. Die acht geänderten Sitze wurden in 16 technischen Wiedergaben geprüft. Jedes Endergebnis, sämtliche Matchsieger, jede öffentliche Erstmeldung und jeder geänderte Befehl ließen sich exakt reproduzieren. Diese 16 Durchläufe erhöhen die Stichprobe nicht.

| Karte / Sitz | Suchdauer / andere Befehle | Neue Zellen V16 → Scout | Zweites Paar gesehen V16 → Scout | Punktefelder V16 → Scout | Matchsiege V16 → Scout |
|---|---:|---:|---:|---:|---:|
| 160343001 / P0 | 6 / 2 | 5 → 9 | nie → 98 | 10 → 10 | 3 → 3 |
| 160343001 / P1 | 5 / 1 | 4 → 21 | nie → 89 | 10 → 12 | 3 → 3 |
| 160343008 / P0 | 18 / 10 | 73 → 122 | nie → nie | 10 → 10 | 1 → 1 |
| 160343008 / P1 | 4 / 2 | 20 → 26 | nie → nie | 10 → 10 | 2 → 2 |
| 160343014 / P0 | 16 / 7 | 110 → 124 | nie → nie | 6 → 6 | 3 → 2 |
| 160343014 / P1 | 20 / 3 | 107 → 141 | nie → 85 | 6 → 10 | 1 → 2 |
| 160343026 / P1 | 5 / 3 | 40 → 54 | 70 → 55 | 6 → 8 | 3 → 3 |
| 160343033 / P1 | 2 / 1 | 27 → 35 | 78 → 78 | 8 → 11 | 3 → 3 |

Auf **160343008/P0** sah V16s Team während des Auftrags 15 neue Zellen, die das veränderte Team bis dahin gar nicht sah. Dafür sah das veränderte Team 64 andere Zellen, insgesamt 49 mehr. Trotz 18 Suchzügen und dieser zusätzlichen Sicht blieb das zweite Paar unentdeckt. Auf **160343014/P1** führte die veränderte Spielbahn zu 40 exklusiv gesehenen Zellen und ließ sechs der V16-Zellen aus. Das Team fand das Paar in Zug 85, also nach dem Ende des Suchauftrags in Zug 80. Die Messung belegt den veränderten Gesamtverlauf. Welches Schiff das Relikt zuletzt sichtbar machte, wurde in diesen 96 Spielen nicht ermittelt.

Die auf denselben bereits bekannten Karten erzielte Differenz genügt der vorab festgelegten Schwelle für eine getrennte Bestätigung. Die gewonnene Partie macht den Kandidaten noch nicht zum Nachfolger von V16. [Unabhängige Vorfestlegung](BESTAETIGUNG.md) · [Aktionsvergleich und Endergebnisse](aktion/ergebnis.json) · [Tatsächliche Sensorflächen mit Zell-IDs](aktion/feldkontrolle.jsonl) · [Definition der Sichtkontrolle](SICHTKONTROLLE.md)

Aus dem Repo mit der Kurs-Python-Umgebung lässt sich die Entwicklung aus den fertigen Rohdaten unabhängig auswerten:

```sh
d=experiments/analysis/v16_finalwoche_20261122/signalstudie
python "$d/aktionsbilanz.py"
```
