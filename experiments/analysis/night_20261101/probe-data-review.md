# Daten- und Mechanismusabnahme der Overlap-Schattenprobe

**Urteil: Technische Zulassung von Kandidat A: JA.** Die Probe erfüllt die vorab festgelegte Voraussetzung zusätzlicher sicherer Information. Sie belegt keine Verbesserung der Spielstärke und erlaubt noch keine Abgabeübernahme.

Prüfung rein lesend in `/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics`. Keine Spiele, Tests, Trainings, Torch-/Lux-Importe oder Sourceänderungen gestartet; nur Python-Standardbibliothek für Dateihashes und Nachzählung verwendet. Ausgabe dieses Berichts ausschließlich unter `/tmp`.

## Vollständigkeit und Nachzählung

Grundgesamtheit gemäß Nachtplan: Seeds **830000–830039**, jeweils `player_0` und `player_1`, Gegner Solution_92. Nachzählung der tatsächlichen `rows`:

| Prüfung | Befund |
|---|---:|
| Erwartete / vorhandene / eindeutige Schlüssel | 80 / 80 / 80 |
| Fehlende / unerwartete / doppelte Schlüssel | 0 / 0 / 0 |
| Einheitliche Zeilenschemata | 1 |
| Zeilen mit `steps=300` | 80 |
| Zusätzliche positive Fakten | 51 |
| Zusätzliche Null-Fakten | 200 |
| Spiele mit zusätzlichen Fakten | 9 / 80 (11,25 %) |
| Zusätzliche positive / Null-Fakt-Schritte | 409 / 1911 |
| Aufgezeichnete falsche zusätzliche Fakten | 0 |
| JSON-Spielzeilen identisch mit Log-Spielzeilen | 80 / 80 |
| Nicht endliche Zahlen | 0 |

Die Summen im JSON stimmen mit der unabhängigen Summe seiner Einzelzeilen überein. Das Log enthält genau die 80 identischen Spielzeilen und eine zusätzliche erwartete Ladezeile für das eingefrorene V14-Ensemble mit 36 Netzen; keine Fehler-/Abbruchzeilen.

Die neun betroffenen Schlüssel sind 830003 beide Seiten, 830006/player_1, 830010/player_1, 830016/player_1, 830028 beide Seiten und 830031 beide Seiten. Das sind sechs Karten, nicht neun unabhängige Karten.

## Richtige Einheiten

`steps=300` sind **beobachtete frische Nichtreset-Schritte**, nicht die Zahl der Engine-Übergänge des vollständigen Spiels. `probe_overlap.py:44–52` zählt nur frische Beobachtungen und überspringt `match_steps==0`; `play_game` läuft unabhängig davon bis `done` (`scripts/common.py:126–151`). Die 303 Engine-Schritte der regulären Auswertung dürfen deshalb nicht als Erwartungswert dieser speziellen Diagnose-Spalte verwendet werden.

`extra_*_facts` zählt pro Spiel die Vereinigungsmenge **(Matchindex, flacher Tileindex)**, die irgendwann im Shadow zusätzlich gegenüber dem handelnden V14 bekannt ist (`probe_overlap.py:55–60`). Das sind weder 51 verschiedene Kartenpositionen über die gesamte Probe noch 51 zusätzlich besetzte Punktefelder. Derselbe Tile in mehreren Matches zählt mehrfach; bewiesene Spiegelfelder sind eigenständige Tile-Fakten. `extra_*_steps` zählt dagegen die Anzahl zusätzlicher Fakten je Beobachtung aufsummiert und ist deshalb höher. Diese Einheiten sind für die Mechanismusvoraussetzung geeignet und dürfen nicht zu Punkten oder Gewinnprozenten umbenannt werden.

## Wahrheit und Aktionsisolation

Der geprüfte Quellpfad ist `experiments/analysis/night_20261101/probe_overlap.py`:

1. Die Referenzgewichte sind fest auf V14-SHA `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8` geprüft; der Agent wird mit `train=False` geladen und Autosave ausgeschaltet (`:23–29`).
2. Nach jedem regulären `new_game` wird dessen zurückgesetzter Belief vollständig kopiert. Die kopierte instanzgebundene `observe`-Übersteuerung wird entfernt; ausschließlich die Kopie erhält `overlap_infer=True` (`:36–42`). `main.py:153–160` bestätigt, dass die Originalmethode denselben Original-Belief zurücksetzt und die Seite setzt, statt ihn heimlich auszutauschen.
3. Der Observer ruft zuerst `original_observe(obs)` auf, dann `shadow.observe(obs)` mit derselben öffentlichen Beobachtung. Lediglich die öffentlich bekannte Sensorreichweite wird vom Original zum Shadow übertragen (`:43–50`). Die Schattenfakten werden danach durch Set-Differenz gelesen; sie werden nicht in den Original-Belief zurückgeschrieben (`:55–60`).
4. Erst nach beiden Observe-Aufrufen wird Engine-Wahrheit gelesen (`:61–66`). Sie wird ausschließlich für `bad_p`/`bad_d` genutzt. Weder echte Relics noch echte Punkt-/Nullkarten gelangen in Features, Ziele, Rewards oder eine Aktion. `truth_maps` nutzt dieselbe Punktbedingung wie die Engine: Gewicht > 0 und Gewicht ≤ Zahl aktivierter Relic-Paare (`scripts/oracle_probe.py:25–31`; eingefrorene Engine `env.py:696–707`). Bei player_1 wird die Wahrheitskarte in denselben kanonischen Raum gespiegelt.
5. Der tatsächliche Aktionspfad bleibt `agent.act` → `self.belief` → Kontext/Features des Original-Beliefs (`scripts/common.py:131–136`, `main.py:300–316`). Er liest den Shadow aus dem Diagnosezustand nicht. In `play_game(...,train=False)` wird auch kein Agent-Update ausgeführt (`common.py:138`). Die Shadow-Operationen sind deterministische Belief-Berechnungen und nehmen keine Zufallsziehungen vor.

Damit ist anhand des eingefrorenen Codes **keine Aktionskontamination durch Orakel- oder Schattenwissen vorhanden**. Es gibt hier keine separate Aktion-für-Aktion-Aufzeichnung gegen einen Lauf ohne Observer; die Isolation ist eine Code-/Datenflussprüfung, keine neue Aktionsreplikation. Das ist für diese Schatten-Mechanismusprüfung ausreichend. Die separate allgemeine Flag-aus-Kompatibilität bleibt eine eigene technische Prüfung.

Die Wahrheit wird für jede zusätzliche Klassifikation geprüft, solange sie zusätzlich gegenüber dem Original ist. Nicht nur erstmals auftauchende, sondern auch fortbestehende zusätzliche Fakten fließen in den Check ein. Alle gespeicherten `bad`-Listen sind leer. Es sind keine vollständigen (Match,Tile,Wahrheit)-Rohtraces gespeichert; daher lässt sich aus dem JSON allein keine zweite unabhängige Wahrheitssimulation jeder einzelnen Feldklassifikation durchführen. Das Urteil stützt sich hier auf den geprüften Validator und dessen vollständig erhaltene Ausgaben, nicht auf eine unzutreffend behauptete Neu-Simulation.

## Hashes, Freeze und Root-Receipt

Das Root-Receipt `probe_receipt.json` nennt den direkten Aufruf des eingefrorenen Probeskripts mit `--out probe_full.json`, Exitcode 0 und `source_unchanged=true`. Ohne `--first`/`--n` gelten die im ebenfalls eingefrorenen Skript sichtbaren Defaults 830000/40 (`:12–15`), welche die tatsächlichen Schlüssel exakt abdecken.

Der unabhängig neu berechnete SHA-256 von `probe_full.json` lautet:

```text
5e0f002c9b3617841d91265b8adce214ab2a1d65c473636d2d874e9e83abeeb4
```

Er stimmt exakt mit `probe_receipt.json.output_sha256` überein. Zusätzlich wurden **insgesamt 195 Eingabedateien** aus `probe_freeze.json` anhand ihres erwarteten SHA-256 erneut gelesen, einschließlich Quell-/Test-/Plan-/Engine-Dateien, drei Gewichtsdateien und ausführbarem Interpreter: **0 fehlend, 0 verändert**. Die drei Gewichtsdateien sind jeweils die erwartete V14-Datei. Das Probe-Skript selbst, `scripts/common.py`, `scripts/oracle_probe.py`, die Agent-Dateien und die Engine-Quelldateien sind im Freeze enthalten.

Der Freeze nennt HEAD `73613710ccf7f7fb76900cadb2ada678f6a514af`; zum Reviewzeitpunkt ist HEAD `390de378c06dbde8bde0e11c68b2ba35b77bda48`. Das ist ein nachträglicher Commitstand bei unveränderten eingefrorenen Dateiinhalten und widerspricht dem Receipt zur Laufzeit nicht. Der neue HEAD wird nicht rückwirkend als Ausführungsversion ausgegeben. Das Receipt ist ein Root-Ausführungsbeleg mit Vorher/Nachher-Aussage; die unabhängige Reviewprüfung bestätigt den jetzigen Bytezustand und die Outputbindung. Ein kryptografisch signiertes vollständiges Prozess-Audit behauptet sie nicht.

## Grenze des Urteils

Die Probe zeigt auf dem festen vollständigen Diagnosesatz echte zusätzliche Information ohne aufgezeichnete falsche Zusatzfakten und erfüllt damit Aufgabe 5 des Nachtplans für A. Der Informationsgewinn ist auf 9/80 Spiele konzentriert; seine Breite oder sein Einfluss auf Entscheidungen ist damit nicht bewiesen. Die Summen erlauben auch keinen Schluss über Sichtweite 1 allein, weil die Probe keine entsprechenden Parametergruppen ausgibt.

Gesamte gemessene Shadow-Beobachtungszeit 1,361 s über 24.000 gezählte Beobachtungen; einzelner Maximalwert 60,57 ms. Diese instrumentierte Zeit enthält Scheduling-/Messschwankungen und ist kein nachgewiesenes Aktionszeitlimit des Kandidaten.

**A darf technisch in die vorab geplante Auswahl aufgenommen werden.** Für Stärke, Nominierung oder Übernahme gelten anschließend unverändert die unabhängigen Auswahl-/Bestätigungsbedingungen. Keine neuen Kandidatenkombinationen oder Gates aus diesem Review ableiten.
