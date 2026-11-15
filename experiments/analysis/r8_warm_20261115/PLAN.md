# R3 mit eigenen Spielstellungen nachtrainieren

Beide Einzelnetze starten direkt mit R3 (`99b07775…`), frischem AdamW, konstanter Lernrate 0,0001 und Seed 2711. Nach genau 1.024 Updates wird der letzte Stand verglichen. Jeder Update enthält dieselben 128 Replay-Einheitszeilen aus 7272000–7272047. Dazu kommen 128 weitere Zeilen aus 7272048–7272095 für die Warmkontrolle oder aus 7287000–7287047 für R8. Die neue Sammlung mit `--raw-teacher` nutzt dieselben 48 Lern- und 24 Diagnosekarten wie die [Kontextstudie](../r3_context_selector_20261115/PLAN.md). Alle alten Daten stammen von R1, die neuen aus tatsächlichen R3-Spielen. Die Gegenüberstellung misst den gemeinsamen Effekt neuer Karten und der durch R3 besuchten Stellungen.

Pro Hälfte und Update entfallen 64 Entscheidungen auf jeden Sitz, 42 oder 43 auf jeden der drei Gegner. Die Restplätze wechseln mit jedem Update. Je Gegner und Sitz rotieren jeweils alle 16 Archive gleich oft in zufälliger Reihenfolge. Pro gewähltem Archiv werden 21 bzw. 22 aufeinanderfolgende zulässige Zeilen mit zufälligem Start und zyklischem Umbruch gezogen. Jede so betroffene Kartenansicht wird im Update nur einmal durch den CNN-Teil geschickt. Der Prüfnachweis enthält die benutzten Einheitszeilen als fortlaufenden SHA-256, die Zeilenzahlen je Archiv und die tatsächlichen Adam-Schritte. Die gemeinsamen Replay-Identitäten und Ziehungen müssen in beiden Armen exakt übereinstimmen.

Ziele wie bei R3: maskierte Kreuzentropie des endgültigen Lehrerbefehls (Gewicht 3 bei V14- oder Lehrer-SAP), halbe Kreuzentropie des legalen Schussziels und halbe KL der fünf legalen Bewegungswerte bei Temperatur 2 auf gültigen nativen Rohspuren. Im Spiel berät das resultierende Netz V14 wie beim ursprünglichen R3 mit 70-%-Schwelle für Bewegung oder Halten. Schuss und Zielfeld bleiben V14 überlassen. Der Kontextselektor wird hierbei nicht verwendet.

## Vorab festgelegte Auswertung

Auf den 24 neuen Diagnosekarten 7287100–7287123 muss R8 auf identischen gespeicherten Eingaben mehr endgültige Lehreraktionsklassen treffen als die Warmkontrolle und R3. Auf den 24 älteren Diagnosekarten 7272200–7272223 muss R8 mindestens R3 erreichen. Pro Karte (beide Sitze) zählen wir auch verlorene, zuvor richtige V14-Aktionen. Beim neuen Satz berichten wir R3s tatsächlich ausgeführte Befehle und Abweichungen zur aus den komprimierten Eingaben rekonstruierten R3-Entscheidung als separate Sensitivitätsanalyse. Diese Übereinstimmungen messen keine Spielsiegquote.

Nur nach bestandenem Archivvergleich sind 16 neue Karten (7288000–7288015) vorgesehen. R8, Warmkontrolle, R3 und V14 spielen auf beiden Sitzen gegen Solution und Kaggle, R8 zusätzlich direkt gegen V14. Das sind 288 ganze Spiele. Für die Nominierung muss R8 extern jeweils mehr Siege als R3 und die Warmkontrolle und wenigstens zwei zusätzliche Siege gegenüber V14 erzielen. Gegen Solution muss R8 mindestens V14 und R3 erreichen, direkt gegen V14 die Mehrheit. Unabhängige Bestätigung erst nach Nominierung auf 7288100–7288159 extern und 7288200–7288259 direkt (600 Spiele, V14 als Referenz). Für den Vorteil gegenüber V14 müssen die unteren 95-%-Grenzen extern über 0 und direkt über 50 % liegen, mit wenigstens V14s Zahl an Solution-Siegen. Jeweils 10.000 Ziehungen ganzer Karten mit beiden Sitzen und extern gemeinsam gezogenen Gegnern, PCG64/2711. Vor einer Änderung der Abgabe ist außerdem der Vergleich mit dem tatsächlichen aktuellen Turnierstand erforderlich.

## Nachrechnung

`R3` ist der feste Elterncheckpoint, `ALT` der historische Ordner `final_20261115_movement_dagger`, `NEU` der einmalig mit rohen Lehrerwerten aufgenommene Ordner `final_20261115_r3_context`. Der neue Ergebnisordner `ZIEL` liegt außerhalb der Abgabe. Beide Fits verwenden dasselbe Gerät. Der Archivvergleich läuft auf der CPU und reproduziert für alte Diagnosesitze die veröffentlichten R3-Zählungen.

```sh
python -B -u -m scripts.r8_warm control --parent "$R3" --old "$ALT" --new "$NEU" --out "$ZIEL"
python -B -u -m scripts.r8_warm r8 --parent "$R3" --old "$ALT" --new "$NEU" --out "$ZIEL"
python -B -u -m scripts.r8_warm_assess --parent "$R3" --models "$ZIEL" --old "$ALT" --new "$NEU" --out "$ZIEL/validation.json"
```
