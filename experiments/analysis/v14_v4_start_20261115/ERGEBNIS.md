# Die öffentliche Sichtweite reicht für eine Startwahl zwischen V14 und v4 nicht aus

V14 und der **gemischte v4-Hybrid** spielten auf drei disjunkten Kartenblöcken beide Sitze gegen Solution und den nativen Kaggle-Dritten. Eine Regel, die vor Aktion 0 einen Agenten für das gesamte Spiel bestimmt, kann genau anhand der zugehörigen vollständig gespielten Partie ausgewertet werden. Auf Dev A wurde die Regel **V14 bei Sichtweite 3 oder 4, sonst v4** ausgewählt. Ihr einziger zusätzlicher Sieg gegenüber v4 auf Dev A wiederholte sich auf Dev B nicht.

| Block | V14-Karten | Solution: Regel / v4 / V14 | Kaggle: Regel / v4 / V14 | Extern: Regel / v4 / V14 | Regel minus v4, 95 % in pp | Regel minus V14, 95 % in pp |
|---|---:|---:|---:|---:|---:|---:|
| Dev A, 100 Karten, Auswahl | 45 | 195 / 194 / 188 | 10 / 10 / 8 | 205 / 204 / 196 | +0,25 [0,00; +0,75] | +2,25 [−0,25; +5,00] |
| Dev B, 100 Karten | 47 | 188 / 190 / 185 | 2 / 4 / 0 | 190 / 194 / 185 | −1,00 [−2,75; +0,25] | +1,25 [−0,50; +3,25] |
| Historische 400 Karten | 181 | 769 / 764 / 767 | 12 / 12 / 12 | 781 / 776 / 779 | +0,31 [−0,25; +0,94] | +0,13 [−1,13; +1,31] |

Jede Karte zählt vier externe Partien. Auf dem 400er-Block fallen gegenüber v4 alle elf hinzugewonnenen und alle sechs verlorenen Spiele bei Solution an. Gegen Kaggle bleiben die 800 Spielausgänge gegenüber v4 einzeln identisch. Auf Dev B verliert die Regel gegenüber v4 je zwei Siege pro Gegner. Dev A diente allein der Regelwahl. Die 400er-Paarungen und Dev B waren für die vorliegende Regelwahl gesperrt, ihre vorher veröffentlichten Resultate und die frühere Auswahl des v4-Elternagenten waren bekannt. Die 400 Karten waren außerdem bereits Gegenstand einer früheren Schussreichweitendiagnose.

**Günstigste nachträgliche Wahl.** Wer für jede ganze Karte die vier abschließenden Ergebnisse beider Agenten kennt und den besseren Agenten für beide Gegner und Sitze wählt, erreicht 211/400 auf Dev A, 199/400 auf Dev B und 815/1600 auf dem 400er-Block. Die noch freiere Wahl je Gegner und Sitz liefert 211, 200 und 817. Dies sind Obergrenzen mit Kenntnis der Ausgänge.

## Regelwahl und Datenherkunft

Vier vor dem ersten Befehl mitgeteilte Größen wurden betrachtet: Bewegungskosten, SAP-Kosten, SAP-Reichweite und Sichtweite. Für jede Größe weist eine Regel der unteren oder oberen Hälfte ihres vorgegebenen Wertebereichs V14 zu und verwendet sonst v4. Es gibt acht Regeln und die zwei konstanten Agenten. Die Auswahl maximiert auf Dev A die Vollspielsiege gegen beide Gegner zusammen. Bei Gleichstand haben konstante Agenten Vorrang, übrige Gleichstände werden per fester Reihenfolge aufgelöst. Erst nach Schreiben von [selection.json](selection.json) wurden die festgelegten Entscheidungen auf den beiden anderen Panels bewertet. Die Intervalle resampeln 10.000-mal ganze Karten, einschließlich beider Sitze und beider Gegner, mit NumPy PCG64 und Startwert 2711. Die vollständigen Zahlen pro Gegner, gewonnene und verlorene Sitze, Matchsiege und Datei-Prüfsummen stehen in [comparison.json](comparison.json).

V4 ist durchgängig Mahmouds gemischte Version mit demselben Schüler, Stay-Bias 1,5, Entstapeln und Kampfradius fünf. Für Dev A gehört **v14_ref_devA.csv** zur veröffentlichten v4-Gegenüberstellung. Die ältere v14_devA.csv weicht bei allen 200 Kaggle-Punktepaaren, 188 Matchsummen und sechs Spielausgängen ab. Bei Solution stimmen alle 200 Endstände überein. Das Werkzeug verwendet die registrierte Referenz und liest von beiden Eltern ausschließlich vollständige, eindeutige Karten-Sitz-Gegner-Schlüssel mit 303 Zügen und drei Matches. Dev A beginnt bei 7150000, Dev B bei 7151000, der 400er-Block bei 7158000. Für R3 liegt Dev A vollständig nur gegen Solution vor. Der neue gemeinsame 400er-Lauf hatte zum Zeitpunkt dieser Auswertung noch keine versiegelte R3-Gesamtdatei. [V4-Zuweisung und Dev B](../umbau_20261115/V4_ZUWEISUNG.md) · [Vorab registrierte 400er-Konfiguration](../../../docs/superpowers/plans/2026-11-15-umbau-imitation.md) · [Prüfsumme der Dev-A-Referenz](../../../scripts/r3_deva_solution.py) · [Bestätigung des v4-Elternagenten](../umbau_20261115/confirm/ERGEBNIS.md)

**Kontrolle der öffentlichen Felder.** Das Werkzeug liest die Wertebereiche aus der installierten `luxai_s3/params.py` und führt nur die Aufteilung der JAX-Zufallsschlüssel und die vier öffentlichen Ziehungen des ursprünglichen Wrappers aus. Es benutzt weder Gym noch Kartenaufbau oder Agenten. Auf allen 6.200 Karten in der separat durchgeführten früheren Erhebung stimmten alle vier Ganzzahlen mit ihren gespeicherten Werten überein, also 24.800/24.800 Werte. Der Parametervergleich, alle beteiligten SHA-256 und die JAX-Version stehen in [selection.json](selection.json). [Historische Parametertabelle](../battle_params_20261030/map_params.csv) · [Ursprüngliche Aufzeichnung](../battle_params_20261030/map_params.py)

Die ältere FT18-Auswertung nutzte denselben eng begrenzten Regelraum bei einem anderen Ensemble. Die frühere Diagonaldiagnose wählte V14 für SAP-Reichweite höchstens fünf ausdrücklich anhand von V14-Kaggle-Siegen auf den 400 Karten. Bei Anwendung dieser älteren Regel auf das Elternpaar V14/v4 ergeben sich 201 statt 204 v4-Siege auf Dev A, 189 statt 194 auf Dev B und 787 statt 776 auf den bereits für jene Auswahl benutzten 400 Karten. Selbst dort umfasst das gepaarte Intervall gegenüber v4 null (−0,44 bis +1,88 pp). Dieser Befund begründet keinen neuen Spielversuch. [Früherer FT18-Selektor](../late_ft18_20261115/public_selector/ERGEBNIS.md) · [Frühere SAP-Auswahl](../diagonal_after_loss_20261115/PLAN.md) · [Separate Nachrechnung](earlier_sap.json)

## Nachrechnen

Mit der Projektumgebung aus dem Projektstamm ausführen. `OUT` muss ein leeres Verzeichnis sein. Die Auswahl bindet den Messcode, die Quelltabellen für Dev A und die Parameterprüfung an SHA-256. Alle drei Ergebnisdateien können byteweise mit den hier hinterlegten Dateien verglichen werden.

```sh
OUT=$(mktemp -d)
STUDY=experiments/analysis/v14_v4_start_20261115
.venv/bin/python -B "$STUDY/route.py" "$PWD" choose --out "$OUT"
.venv/bin/python -B "$STUDY/route.py" "$PWD" evaluate --out "$OUT"
.venv/bin/python -B "$STUDY/previous_rule.py" "$PWD" --out "$OUT"
for f in selection.json comparison.json earlier_sap.json; do cmp "$STUDY/$f" "$OUT/$f"; done
```
