# Geführte Exploration: Pfadkorrektur offline geprüft

**08.11.2026 – Diagnose abgeschlossen und unabhängig geprüft. Der Ansatz erhält vorläufig niedrige Priorität; ein stärkerer Agent ist damit nicht nachgewiesen.**

Untersucht wurde, ob die vorhandene Pfadkorrektur `_path_fix` auch bei geführten Explorationszügen eingreifen könnte. Dieser Trainingszweig überspringt bisher die Korrektur des Greedy-Zweigs. Die Diagnose rekonstruiert ausschließlich mögliche Helper-Eingriffe auf alten Beobachtungen.

Die feste Datenbasis umfasst genau zwölf archivierte Ausführungen aus `continuation_20261102/diagnostic_keys.json`: sechs ausgewählte Niederlagen und die ersten sechs Siege, auf sieben Karten. Das ist keine repräsentative Trainingsstichprobe. Es wurden keine neuen Spiele, Netzberechnungen oder Lernupdates durchgeführt.

| Größe | Ergebnis |
|---|---:|
| Archivierte Frames, davon reguläre Entscheidungsframes | 3.636 / 3.600 |
| Unit-Entscheidungen | 41.937 |
| Historische `_path_fix`-Aufrufe exakt reproduziert | 22.258 |
| Rekonstruierbare deterministische geführte Züge | 22.125 |
| Hypothetische Änderungen durch den Helper | **343** |
| Betroffene Partie-Schritte / alte Ausführungen | 303 / 12 |

Die 343 Änderungen verteilen sich auf 144 bekannte Punktefelder, 90 Kandidatenziele und 109 Erkundungsziele. Sie entsprechen rund 1,55 % der rekonstruierten deterministischen geführten Züge. Für 19.090 zugewiesene Zielgelegenheiten gab es keinen solchen Zug; der zufällige Ersatz wurde nicht simuliert. [Originalergebnis](run_v1/summary.json)

Mit der theoretischen Zweigwahrscheinlichkeit `0,05 × 0,7 = 0,035` ergeben sich rechnerisch `343 × 0,035 = 12,005`, also **rund zwölf erwartete Helper-Eingriffe über sämtliche zwölf alten Partien**, wenn man deren beobachtete Zustände festhält. Das ist keine gemessene Trainingshäufigkeit. Spätere Regeln können Zwischenänderungen überschreiben; veränderte Entscheidungen würden zudem andere Verläufe erzeugen. Eine Zahl geänderter Endaktionen oder ein Nutzen bei Schäden und Siegen lässt sich daraus nicht ableiten.

Der unabhängige Audit bestand **69.683 Prüfungen**: sämtliche Golden- und Änderungszeilen, Zuordnungen, Summen und Hashbindungen wurden geprüft. Die ursprünglichen Archive und alle Frame-/Unit-Nenner wurden dabei nicht erneut vollständig rekonstruiert; für diese Vollständigkeit bleibt der geprüfte Originallauf maßgeblich. [Datenprüfung](data-audit.json)

**Entscheidung:** Die begrenzte theoretische Exposition rechtfertigt vorläufig niedrige Priorität. Keine Regeländerung oder zusätzliche Trainingsreihe folgt aus dieser Diagnose. Eine fehlende Lernwirkung oder grundsätzliche Unwirksamkeit ist damit ebenfalls nicht bewiesen; V14 bleibt unverändert.
