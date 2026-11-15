# Überträgt sich V15s Direktvorteil?

Auf 400 bekannten Karten gewann V15 direkt 730/800 gegen V14. Ein zweiter Lerngegner (ursprünglicher R3) verlor auf einem anderen Kartensatz 36/48 gegen V15. Gegen die ursprüngliche Solution gewann V15 in der unabhängigen Bestätigung dagegen 764/800, V14 767/800. Der neue Vergleich prüft, ob die Richtung des Vorteils auch gegen andere Spielweisen sichtbar wird. Er entscheidet keine Übernahme. [V15-Bestätigung](../V15_ENTSCHEIDUNG.md) · [R3-Duell](../../r3_v4_mixed_duel_20261115/ERGEBNIS.md)

## Karten und Gegner

Beide festen Agenten spielen **7170040 bis 7170063** auf beiden Sitzen gegen jeden Gegner. Das ergibt je Gegner und Agent 48 Spiele, je Agent 144 und zusammen 288 vollständige Partien. Die Nummern stammen aus dem im Nachtauftrag reservierten Robustheitsbereich. In den vorhandenen Ergebnistabellen und Partiezeilen des Hauptprojekts waren vor der Registrierung keine dieser Spielschlüssel zu finden.

| Gegner | Tatsächliche Spielweise |
| --- | --- |
| `sol92_sq` | Solution-Variante mit quadratischer Schussreichweite der sammelnden Einheiten, sonst die ursprüngliche Zielpriorität. |
| `rush` | Regelagent, der mit seinen Schiffen in die gegnerische Hälfte fährt und auf den schwächsten Gegner im Schussquadrat zielt. |
| `dqn` | Das Kursnetz aus Gruppe 3 mit 17 Eingaben und fünf Bewegungsaktionen. Spielt im Kurs-Evalmodus gierig mit ε = 0. |

Der allgemeine Parallel-Evaluator lässt den DQN-Gegner bei seiner Initialisierung auf ε = 0,1. Die neue Messung folgt dem Evalmodus des Kurs-Runners. In beiden Vergleichsarmen läuft der Gegner als originale DQN-Klasse des Kurses. Jede neu erzeugte DQN-Instanz muss die sechs Tensoren der mitgelieferten Datei nach Typ, Form und Bytes reproduzieren. Bei fehlenden Gewichten oder einem zufällig gestarteten Ersatznetz endet die Prüfung. Die beiden alternativen Gegner werden zusätzlich über ihre tatsächlichen Typen und bei Solution über deren Schalter geprüft. Ein Zufallsgegner würde weitere 96 vollständige Spiele kosten und bleibt aus diesem begrenzten Vergleich heraus.

## Vor dem ersten Spiel

Die beiden Abgabedateien von V14 sind bytegleich. Gespielt wird mit dem ursprünglichen Checkpoint und dem echten, zuvor geprüften V15-Hybrid, der beide Checkpoints enthält. Beim Laden kontrolliert der bestehende Kursprüfer alle aktiven Netze, den Modus und die Schalter. Die Agenten und Kursgegner stammen aus `b2bd67e43f213cd99669bf3eee759e3fdeb1c0f5`. Der strengere Messprüfer für mitgezählte Fehler in Unteragenten ist im Studien-Snapshot enthalten. Für die Reproduktion die Arbeitskopie von `scripts/par_eval.py` (SHA-256 `a2460e6663878c8993093e035881ba6132865e7aeeac7d976543e9147fd7a58f`) und `scripts/xversion_replay.py` (`7f0563d13bdc915c180271a2b1c6733bdab7145efc7152122e9dee09edad28b4`) über die gleichnamigen Dateien des historischen Quellstands legen. Zwischen den Armen müssen Quellstand, Lux-Engine, Laufzeitversionen, Hashes und Kartenplan übereinstimmen. Die äußere ZIP der Abgabe wird nicht benötigt.

| Eingabe | SHA-256 |
| --- | --- |
| V14 | `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8` |
| Separat für den Kurs geprüfter V15-Hybrid | `20f8af0dee4711b566cc83309111fceb32ee176aa86c7fd9398bf52c330a017e` |
| Ursprünglicher Prof-DQN aus `agents/DQN/agent.pth` | `2678d4e5409645ec16236545c5b84dbb32108a02d3140ea40aad1444089a4981` |

Aus dem eingefrorenen Arbeitsverzeichnis mit dem [Messwerkzeug](../../../../scripts/v15_style_panel.py). `PYTHON` bezeichnet die Projektumgebung, `V15` den absoluten Pfad zum geprüften `experiments/imitation/releases/v15_codex/weights/agent.pth`, `OUT` ein neues Ergebnisverzeichnis. Jeder Spielaufruf läuft mit einem Worker. Bereits angelegte Armergebnisse werden vor einem Wiederholungsstart erkannt.

```sh
"$PYTHON" -m scripts.v15_style_panel v14 --v15 "$V15" --out "$OUT"
"$PYTHON" -m scripts.v15_style_panel v15 --v15 "$V15" --out "$OUT"
"$PYTHON" -m scripts.v15_style_panel compare --v15 "$V15" --out "$OUT"
```

## Auswertung

Primär zählen die je Gegner gewonnenen ganzen Spiele. Zusätzlich erscheinen die 144 Einzelmatches je Agent und Gegner sowie die Sitze, auf denen das Ergebnis umschlägt. Für Spiel- und Matchsieganteile werden die Differenzen V15 minus V14 gebildet. Das bestehende Bootstrap-Verfahren zieht 4.000-mal 24 Karten mit beiden Sitzen (Startwert 2711) und liefert je Gegner das 95-%-Perzentilintervall. Die drei Vergleiche bleiben einzeln und ohne Korrektur für Mehrfachvergleiche sichtbar. Bei durchgehend gleichen Ergebnissen ergeben sich auch bei kleinen Stichproben rechnerisch manchmal Grenzen von [0, 0]. Dann lautet der Befund ausschließlich, dass auf diesen Karten kein Unterschied auftrat. Gleichstand am oberen Rand oder 48/48 sichern keine 100 % auf weiteren Karten. Die Resultate zum quadratischen Solution-Ableger sind keine weiteren Partien gegen die Original-Solution.
