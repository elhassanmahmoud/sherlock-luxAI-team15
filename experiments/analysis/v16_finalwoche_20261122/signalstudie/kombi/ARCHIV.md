# Welche bekannten Rettungen lassen sich verbinden?

Die Kombination behielt **drei von drei** geretteten Starts des Kundschafters aus dessen separater 200-Karten-Prüfung sowie **sechs von sieben** geretteten Mitte2-Starts aus der früheren, zur Hälfte nach Niederlagen ausgewählten Vorstudie. Auch der einzelne, separat gezählte Gewinn aus der ursprünglichen Scout-Entwicklung blieb erhalten. Der Mitte2-Berater änderte in jedem der elf Spiele genau einen Befehl, der Scout in sechs Spielen zusammen 21 Befehle. In den sechs Spielen mit beiden Eingriffsarten änderte der Berater jeweils früher einen Befehl. Alle elf Fälle sind vorbekannte Siegwechsel. Ihre Kombination ist keine Schätzung der allgemeinen Siegquote.

Die vier Zahlen je Zeile zählen die gewonnenen Einzelmatches der drei Matches eines ganzen Spiels. Ab zwei gewonnenen Einzelmatches gewinnt der Agent das Spiel.

| Karte / Sitz | Original-V16 | Nur Scout | Nur Mitte2 | Kombination |
|---|---:|---:|---:|---:|
| 7261398 / P1 | 1 | 2 | 2 | **1** |
| 7267009 / P1 | 1 | 1 | 3 | 3 |
| 7267106 / P0 | 1 | 1 | 2 | 2 |
| 7267165 / P0 | 1 | 1 | 2 | 2 |
| 7267225 / P0 | 1 | 1 | 3 | 3 |
| 7267291 / P0 | 1 | 1 | 2 | 2 |
| 7267344 / P0 | 1 | 2 | 2 | 2 |
| 160343014 / P1 · frühere Scout-Entwicklung | 1 | 2 | 2 | 2 |
| 160344002 / P0 · bisherige Scout-Prüfung | 1 | 2 | 3 | 3 |
| 160344002 / P1 · bisherige Scout-Prüfung | 1 | 3 | 3 | 3 |
| 160344183 / P0 · bisherige Scout-Prüfung | 1 | 3 | 1 | 3 |

Auf **7261398/P1** gewann jeder Helfer alleine 2:1. Gemeinsam wurde nach dem Beraterbefehl in Zug 35 ein anderer Suchverlauf angestoßen, mit vier Scoutänderungen in den Zügen 73, 76, 78 und 79. Die Kombination verlor 1:2. Auf **160344002** gewann Mitte2 alleine auf beiden Sitzen 3:0. Nach seiner frühen Umleitung in Zug 30 musste der Scout im kombinierten Verlauf keine Bewegung übernehmen. Auf **160344183/P0** reichte Mitte2 alleine nicht. Hier blieben nach seinem Eingriff in Zug 26 die fünf Suchbewegungen wirksam, die auch beim einzelnen Scout zu einem 3:0 führten. Das sind drei unterschiedliche Formen der Wechselwirkung.

Die 44 archivgesteuerten Wiederholungen decken sämtliche veröffentlichten ganzen Siegwechsel der betreffenden drei Vergleiche ab. Originalpunkte, Matchausgänge, die gespeicherten Scoutänderungen und Mitte2-Ereignisse wurden vor der Auswertung abgeglichen. [Gesamtergebnis einschließlich aller Züge](technik/ergebnis.json) · [Vorfestlegung](PLAN.md) · [Technische Einzelmodulprüfung](PARITAET.md)

**Vollständige Einzelmodulparität.** In vier zusätzlichen Kontrollwiedergaben auf P0 und P1 stimmten alle **1.212 vollständigen Mannschaftsbefehle** mit den unveränderten Einzelagenten überein. Die vor, zwischen und nach den Aufrufen gespeicherten Hashes der öffentlichen Beobachtung waren pro Zug identisch. Das bestätigt auch den gespiegelten P1-Fall. Die Teilspielstände und sämtliche echten Eingriffe der Einzelfassungen wurden ebenfalls aus den Archiven reproduziert. Die Schwelle für die getrennte Serie auf 80 neuen Karten ist erfüllt. [Kontrolle P0](technik/paritaet_0.json) · [Kontrolle P1](technik/paritaet_1.json)
