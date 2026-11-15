# V15 mit Python 3.10

Der gepackte V15-Kandidat spielt die aufgezeichnete Partie mit beiden geprüften Python-3.10-Umgebungen exakt nach. Eine Partie auf Karte 7171093 lieferte 303 Schritte je Sitz, also **606 vollständige Aktionsmatrizen je Umgebung**. In den tatsächlichen Befehlen kamen auf Spieler 0 insgesamt 1.939 Bewegungen und 172 Schüsse vor, auf Spieler 1 insgesamt 1.861 Bewegungen und 179 Schüsse. Die drei Matches begannen jeweils bei Schritt 0, 101 und 202. Beide Ordnerpositionen der Battle-ZIP und der eingefrorene Aufruf mit `train=True` funktionierten. [Trajektorie](trajectory.json) · [Protokollauszüge](replays.json)

| Lauf | torch | numpy | Abweichende Matrizen |
| --- | --- | --- | --- |
| Python 3.13.13, ursprüngliche Umgebung | 2.14.1 | 2.5.4 | 0/606 |
| Python 3.10.15 | 2.14.1 | 2.2.6 | 0/606 |
| Python 3.10.15 | 2.2.2 | 1.26.4 | 0/606 |

## Inhalt des Kursmodells

Für beide Startseiten enthält das Paket dieselbe Datei `Gruppe15/agent.pth`, mit der Klasse `Gruppe15.main.Agent_x`. Für das separat gepackte Modell und anschließend noch einmal für das aus der ZIP gelesene Modell wurden die beiden eingebetteten Original-Checkpoints rekursiv verglichen. Alle Schlüssel und Werte, sämtliche Datentypen, Tensorformen und **524 Tensoren** stimmen überein. Davon stammen 480 Tensoren mit 23.862.900 Bytes aus dem gesamten V14-Checkpoint und 44 mit 2.796.324 Bytes aus Mahmouds Schüler-Checkpoint. Die Schalter sind `mixed`, Radius 5, Stay-Bias 1,5 und Entstapeln aktiviert. Die ZIP setzt im äußeren Agenten zusätzlich `frozen=True`. [Prüfsummen und Zählungen](contents.json)

Die beiden Originaldateien tragen die publizierten Hashes `98a07350…` und `0e8b280c…`. Das separat erzeugte gepackte Modell hat SHA-256 `20f8af0d…`, Mahmouds früherer Packvorgang `28933a3b…`. Die Packroutine schreibt neben den Gewichten auch die absoluten lokalen Quellpfade in die Datei. Für diese Prüfung wurden deshalb die Tensorbytes und Konfigurationen ausdrücklich mit beiden ursprünglichen Git-Objekten verglichen. Der Quellstand ist `b2bd67e`. Die konkrete getestete Kandidaten-ZIP ist 24.856.793 Bytes groß und hat SHA-256 `0e3af9db15bcfb1e2fd315ed9da5169e51b1f5f42561d52a15af32bb75ad64ee`.

`xversion_replay.py` gibt für diesen Hybrid „Netze 1“ aus. Der Zähler liest lediglich das leere Zusatznetz-Array der äußeren Kursklasse. Die geladenen Unteragenten sind **36 V14-Netze und ein CNN-Schüler**. Der Paketprüfer meldete diese Struktur auf beiden Sitzen. [Reproduktion](REPRODUKTION.md)

## Acht Spiele im Kurs-Runner

Unter Python 3.10.15 mit torch 2.14.1, numpy 2.2.6 und SciPy 1.14.1 absolvierte V15 **8 von 8 technischen Kursprüfungen**. Gegen Default und Solution spielte der Agent auf 7171094 und 7171095 jeweils einmal pro Sitz, mit 303 Aktionen pro Spiel. Der Prüfer bestätigte für jede Instanz frisches Kartengedächtnis und die geladenen 36 V14-Netze, den Schüler, den Mischmodus und die Schalter. Die 2.424 gemessenen Entscheidungen dauerten im Median je Partie 13,4–15,4 ms, im langsamsten Einzelzug 32,1 ms auf diesem Mac. Die Kurs-Zeitschranke ist unbekannt. [Acht Partieprotokolle und Versionen](runner.json)

Der erste Runner-Start scheiterte beim Import des standardmäßig gewählten SciPy-1.15.3-Wheels. Er hatte noch keine Partie begonnen. Das kompatible SciPy-1.14.1-Wheel lud denselben Kurscode und die ursprüngliche Paketdatei. Das neue Runner-Protokoll und die Vorbelegung der beiden Karten sind separat gebunden. Der statische Prüfer von `b2bd67e` kann intern abgefangene Fehler nur teilweise erkennen. In den tatsächlichen Spiel- und Replayprotokollen taucht keine Fehlermeldung des Agenten auf. Beide offiziellen Gewichtsdateien und die bisherige `Gruppe15.zip` hatten vor und nach der Prüfung dieselben Prüfsummen.

Damit liegt ein Kompatibilitätsnachweis für macOS 27.0.1 auf Apple Silicon vor. Die Siegquoten und die Übernahmeentscheidung stammen aus der unabhängigen [V15-Bestätigung](../V15_ENTSCHEIDUNG.md).

Die geprüfte Kandidaten-ZIP liegt in Moes Hauptcheckout unter `experiments/analysis/umbau_20261115/py310/Gruppe15_V15.zip`. Der geprüfte lokale Hybrid liegt unter `experiments/imitation/releases/v15_codex/weights/agent.pth`. Beide sind aus den im Repository verfügbaren Gewichtedateien wiederherstellbar.
