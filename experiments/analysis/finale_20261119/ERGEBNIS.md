# Echte Züge von Sherlock V16 für die Abschlusspräsentation (19.11.2026, nur Messung)

**Kurz:** Das unveränderte Abgabepaket (`experiments/releases/20261117_sherlock_v16/agent.zip`, SHA-256 `0c59706b…6099`)
spielte als player_0 je 10 Spiele gegen den Kaggle-Dritten und gegen Solution_92 (Karten 4242–4251). Jeder Zug wurde
mitgeschrieben und gegen den echten Befehl des Pakets geprüft. **Gegen den Kaggle-Dritten gingen 286 von 1.438 Schüssen
auf Felder ohne sichtbaren Gegner; 234 davon (82 %) trafen mindestens eine Kaggle-Einheit.** Das Beispiel für Folie 7
und das Halter-Beispiel für Folie 8 stammen aus diesen Spielen. Es wurde nichts ausgewählt oder übernommen; die
Abgabe ist unverändert.

## Was gemessen wurde

[zugbeispiel.py](zugbeispiel.py) lädt das Paket wie in den Bestätigungen (`scripts/r3_package.py`) und hängt sich an
vier Funktionen des geladenen Pakets (Eingaben, beide Netze, Halter-Zeilen, Entstapeln), ohne ihre Rückgabe zu ändern.
Für jede eigene Einheit und jeden Zug werden die Wahrscheinlichkeiten beider Netze vor und nach der Maske, Stay-Bias
und Halter-Regel, die Aktion vor und nach dem Entstapeln, der gesendete Befehl und bei Schüssen das Ziel festgehalten.
Treffer zählt die Engine-Nachrechnung aus [diagnose.py](../r3_kaggle_20261117/diagnose.py) (Bewegung vor dem Schuss,
direktes Ziel und die acht Nachbarfelder). [auswertung.py](auswertung.py) prüft alle Spiele und schreibt
[ergebnis.json](ergebnis.json) und die Karte [karte_schuss.svg](karte_schuss.svg).

**Prüfungen, alle bestanden:** In allen 20 Spielen stimmen die nachgerechneten Wahrscheinlichkeiten nach Stay-Bias
(Abweichung höchstens 10⁻⁴), die Aktion jeder Einheit (70.576 von 70.576 Entscheidungen) und jedes Schussziel
(2.139 von 2.139) mit dem Paket überein. Zwei Läufe derselben Karte ergaben dieselbe Zusammenfassung.

## Ergebnisse

| | gegen Kaggle-Dritten | gegen Solution_92 |
|---|---:|---:|
| Spiele (Matches) gewonnen | 1 von 10 (5 von 30) | 10 von 10 (29 von 30) |
| Einheitsentscheidungen | 33.539 | 37.037 |
| Schüsse | 1.438 | 701 |
| … mit sichtbarem Gegner im 3×3 um das Ziel: getroffen | 1.085 von 1.139 (95 %) | 462 von 493 (94 %) |
| … nächster sichtbarer Gegner genau 2 Felder vom Ziel: getroffen | 12 von 13 | 21 von 33 |
| … ohne sichtbaren Gegner (keiner näher als 3 Felder): getroffen | **234 von 286 (82 %)**, 114 direkt | 97 von 175 (55 %), 35 direkt |
| beste Aktion ohne Maske war gesperrt | 3.107 | 1.225 |
| Halter-Regel änderte die Aktion | 302 | 231 |
| Stay-Bias änderte die Aktion (sonst stehen) | 627 | 484 |

Gründe für gesperrte beste Aktionen gegen Kaggle: zu wenig Energie für einen Schuss 1.442, Asteroid 812, zu wenig
Energie für eine Bewegung 479, Kartenrand 190, stärkerer Gegner oder Nebel 184 (grobe Zuordnung nur zur Beschreibung).

## Die beiden Folienbeispiele

**Schuss ohne sichtbaren Gegner (Folie 7):** Karte 4247, Match 3, Matchschritt 66. Einheit 11 steht bei (10, 6) mit 32
Energie (Schusskosten 31, Reichweite 7). Sherlock sieht in diesem Zug keinen einzigen Gegner. Nach Maske und Stay-Bias:
schießen 88,4 %, stehen 8,7 %, rechts 2,5 %. Die gemeinsame Zielkarte beider Netze gibt Feld (17, 13) innerhalb der
Reichweite fast 100 %. Das Feld ist für Sherlock nicht sichtbar und laut Gedächtnis ein Punktefeld neben dem
gegnerischen Relikt (18, 14). Nach der Bewegung standen dort eine Kaggle-Einheit (direkter Treffer) und drei auf
Nachbarfeldern (16, 14), (17, 14), (18, 12) (Streuschaden). Die Karte zeigt die Schiedsrichtersicht; Sherlock selbst
sah nur die hellen Felder.

**Halter-Regel (Folie 8):** Karte 4247, Match 1, Matchschritt 53. Einheit 2 hält das Punktefeld (8, 3) mit 85 Energie.
Nach der Maske kombiniert: stehen 65,4 %, rechts 34,4 %. Mit Stay-Bias auch für diese Einheit wären es stehen 41,1 %
und rechts 58,6 %, sie hätte das Feld verlassen. Mit der Halter-Regel bleibt sie stehen.

## Grenzen

- 10 Spiele je Gegner, nur player_0. Die Zahlen beschreiben die Spielweise, sie sind keine Siegquote.
- „Ohne sichtbaren Gegner“ heißt: kein für Sherlock sichtbarer Gegner höchstens zwei Felder vom Ziel; ein Gegner,
  der zwei Felder entfernt war, hätte mit einem Zug in den Trefferbereich laufen können und zählt deshalb nicht.
- Die Gründe für gesperrte Aktionen sind eine grobe Zuordnung; die Prüfung der Aktionen hängt nicht davon ab.

Erneut erzeugen:

```sh
for s in $(seq 4242 4251); do
  python experiments/analysis/finale_20261119/zugbeispiel.py --seed $s --opponent kaggle3 --out DIR
  python experiments/analysis/finale_20261119/zugbeispiel.py --seed $s --opponent solution92 --out DIR
done
python experiments/analysis/finale_20261119/auswertung.py DIR
```
