# Verkürzt V14 nach dem Matchwechsel den Weg zum ersten bestätigten Punktefeld?

Auf 7273148/P0 gewann V14 Match 2 mit 263:244, R3 verlor 229:245. Beide kannten bereits acht Punktefelder. V14 punktete in Zug 20, R3 erst in Zug 40. Bis Zug 39 veränderte R3 63 Bewegungsbefehle und bewegte dabei keinen von V14 gehaltenen Halter von seinem Feld. Die sechs [reproduzierten Spielverläufe](../solution_diagnostic/BEFUND.md) begründen eine engere Frage zur Anfahrt.

## Eingriff

Grundlage ist der publizierte R3 mit 0,70-Bewegungsschwelle im eingefrorenen Forschungsstand `0105658`. Geprüft wird nach V14s eigenen Schlussregeln und R3s Zielauswahl auf derselben öffentlichen Beobachtung. Match 2 und 3 sind vom ersten regulären Zug bis vor dem ersten eigenen öffentlich sichtbaren Matchpunkt zugelassen, einschließlich der Aktion, mit der dieser erste Punkt entstehen könnte. Pro lebender Einheit muss V14 ihr aktuell ein konkretes, bestätigtes, passierbares Punktefeld zugewiesen haben. Maßgeblich ist `ctx["assigned"][uid]`, in den kanonischen Koordinaten des jeweiligen Sitzes.

V14 muss eine legale Bewegung (1–4) vorschlagen, R3 ein anderes legales Warten oder Bewegen (0–4), das die unveränderte R3-Policy auch wirklich einreichen würde. Die Weglänge stammt aus V14s Vier-Nachbar-BFS auf `ctx["passable"]` mit dem echten Ziel dieser Einheit. Ein separater Cache lässt den V14-Cache in beiden Armen unberührt. Nur wenn alle drei Distanzen bestimmt sind und `Distanz(V14-Endfeld) < Distanz(Ursprung) <= Distanz(R3-Endfeld)` gilt, wird der R3-Befehl auf V14 zurückgesetzt. Mehrere passende Einheiten dürfen im selben Zug eingreifen. Nach diesem Filter durchläuft der gesamte Plan einmal V14/R3s reguläre Legalitätsprüfung, Aktionsbuchhaltung und Erinnerung im Parameterschätzer. Schussbefehle werden in beiden Richtungen ausgeschlossen; für UIDs ohne passende Gelegenheit bleibt der normale R3-Befehl bestehen.

## Abgrenzung zu früheren Versuchen

Mahmouds [points-Hybrid](../../umbau_20261115/README.md) verwendet den ganzen Schüler und gibt jeder Einheit mit bestätigtem Punkteziel V14s Kontrolle. Die [R2-Deckungsregel](../../coverage_restore_20261115/PLAN.md) reagiert darauf, dass ein ganzes Team ein bereits eingeplantes Punktefeld freigeben würde. Die [FT18-Regel](../../late_ft18_20261115/PLAN.md) tauscht ab Match 2 die Bewegungspräferenz von Netzen; sie prüft kein solches Ziel. Die [Halteranalyse](../../holder_oscillation_20261109/analysis/REPORT.md) und die frühere [passive Solution-Diagnose](../../solution_passive_20261115/ERGEBNIS.md) beobachten bekannte Verläufe. In den geprüften Plänen und Studienprogrammen fand sich kein durchgespielter Versuch mit diesem R3, dem Nullpunktfenster und einer strikten Verkürzung des zugewiesenen Weges.

## 12 feste Schlüssel und 24 Spiele

Gegner ist die native Solution_92. Jeder Schlüssel wird auf demselben Seed und Sitz mit normalem R3 sowie mit dem gefilterten R3 gespielt. Drei Gruppen sind vor dem Lauf festgelegt.

| Gruppe | Karten und R3-Sitze |
|---|---|
| Einzige im Vergleich zu V14 neu verlorene Partie | 7273148/P0 |
| Fünf durch R3 gerettete Partien | 7273116/P1, 7273131/P0, 7273141/P1, 7273149/P1, 7273152/P1 |
| Sechs Gegenpositionen | jeweils die andere Seite aller sechs Karten |

Alle zwölf Original-R3-Kontrollen müssen die vollständigen historischen Ergebnisfelder einschließlich Punkte, Matchsiege und R3-Eingriffe reproduzieren. Die Originaldateien, Engine, Gegner, R3- und V14-Gewichte werden gegen die versiegelte Bestätigung geprüft. Die Kontrollklasse protokolliert nominal mögliche Rücknahmen ohne Anwendungswirkung. Der Eingriffsarm zählt die tatsächlich eingereichten Rücknahmen auf seinem eigenen Verlauf. Für jeden Fall werden Schritt, Sitz, UID, Weltziel, Distanzen und beide Weltbefehle festgehalten. Die native Aktionsbuchhaltung läuft genau einmal mit dem endgültigen Befehl.

Erfasst werden beide vollständigen Weltaktionsströme, Match- und Spielausgänge und je Match der erste eigene Punkt. Im ersten Match und bis unmittelbar vor dem ersten Eingriff müssen die eingereichten Aktionen beider Spieler vollständig übereinstimmen. Am ersten Eingriff müssen sich genau die registrierten UIDs unterscheiden, der Gegner muss auf seiner noch identischen Ausgangslage denselben Befehl abgeben. Paare ohne Eingriff müssen über alle 303 Schritte übereinstimmen. Die Arrays `original` und `restart` liegen mit Achsen (Schritt, Weltteam, UID, Befehlskomponente) im jeweiligen NPZ; Dateihash und Präfixhash stehen in der zugehörigen JSON.

Als Reparatur auf diesen bekannten zwölf Schlüsseln zählt eine zurückgewonnene Partie 7273148/P0 bei Erhalt der fünf Rettungen und sechs Siege auf den Gegensitzen. Matchsiege, erste Punkte und Anzahl tatsächlicher Eingriffe werden auch bei einem negativen Ergebnis berichtet. Die Schlüsselauswahl erfolgte anhand früherer Ergebnisse; sie liefert keine allgemeine Siegquote. Es folgt daraus keine automatische Übernahme oder weitere Kartenserie.

### Reproduktion

Auf einer Archivkopie von `0105658` mit dem Studienpatch und derselben Lux-Engine wie im Bestätigungslauf. `CONF` zeigt auf die ursprünglichen externen Verzeichnisse `confirmation/v14` und `confirmation/r3` über ihren gemeinsamen Ordner `confirmation`. `R3` ist das publizierte `r3_soft.pth`. Ein expliziter Aufruf startet einen Worker und legt ein neues Ergebnisverzeichnis an.

```sh
python -m scripts.r3_restart_study --confirmation "$CONF" --r3 "$R3" --out NEW_RESULTS
```
