# V15 entscheidet drei ausgewählte Solution-Partien für Sherlock und zwei direkte Duelle gegen ihn

Der vorgeschlagene Wechsel endet als allgemeiner Turnieransatz. Die zwei vorab benannten Solution-Niederlagen von R3 wurden im Entscheidungsmatch zu Siegen. Den einen gefährdeten Solution-Sieg behielt Sherlock. Im Direktduell mit V15 verlor der Wechsel dagegen beide vorab geschützten Sitze auf derselben Karte. Damit ist die vereinbarte Schutzbedingung verfehlt. [Versuchsplan](PLAN.md) · [Ergebnis je Sitz](diagnosis/assessment.json)

R3 spielte jeweils die ersten beiden Matches. Nur nach einem eigenen Sieg und einer Niederlage übernahm V15 im dritten Match. Die folgende Tabelle enthält sämtliche sechs tatsächlich umgeschalteten Sitze. Die Punktpaare zeigen Sherlock und Gegner in dieser Reihenfolge.

| Gegner | Karte / Sitz | Punkte M3 mit R3 | Punkte M3 mit V15 | Geänderte Befehle aktiver Einheiten |
|---|---|---:|---:|---:|
| Solution, primärer Fall | 7150079 / P1 | 183 : 197 | **397 : 64** | 213 |
| Solution, primärer Fall | 7150096 / P0 | 667 : 753 | **747 : 668** | 235 |
| Solution, zusätzlicher bekannter Verlust | 7286137 / P1 | 1030 : 1044 | **1065 : 1053** | 128 |
| Solution, gefährdeter Sieg | 7287108 / P0 | 647 : 464 | **614 : 509** | 309 |
| V15, gefährdeter Sieg | 7170018 / P0 | 575 : 568 | **612 : 628** | 119 |
| V15, gefährdeter Sieg | 7170018 / P1 | 575 : 568 | **612 : 628** | 119 |

Alle 20 vollständigen Originaldateien, die Quellenbindung und die früheren Referenzausgänge wurden unabhängig geprüft. Auf allen zehn Sitzen stimmen die gespeicherten Hashes der ersten 202 tatsächlich ausgeführten Befehlsmatrizen für beide Spieler sowie beide Matchstände überein. Die vier Sitze ohne Auslöser behielten dieselben Befehle beider Spieler bis Zug 303. Im direkten Vergleich reproduzierte die Kontrolle auch beide archivierten 303er-Befehlsfolgen. Für 7287108 war vorab aus dem Trainingsarchiv nur die Matchfolge mit dem Spielsieg verfügbar; die beiden vollständigen Messläufe liefern die Punktestände. [Rohdaten und Quellenmanifest](diagnosis/protocol.json) · [Prüfsummen der 20 Partien](diagnosis/completed.json)

## Wie oft könnte der Wechsel gegen Solution überhaupt eintreten?

Sechs abgeschlossene Kartenblöcke mit dem ursprünglichen R3 enthalten 368 weitere Solution-Partien auf 184 verschiedenen Karten, jeweils mit beiden Sitzen. Keiner der zehn diagnostischen Sitzschlüssel kommt darin vor. Die Karten waren für die ursprünglichen Vergleiche im Voraus festgelegt; ihre Ergebnisse waren vor dieser rückblickenden Frage teilweise schon bekannt. Die Tabelle zählt gewonnene Einzelmatches von dreien. [Alle gemischten Sitzresultate und Quellprüfsummen](gelegenheiten.json)

| Erste Karte | Spiele | 0:3 | 1:2 | 2:1 | 3:0 |
|---:|---:|---:|---:|---:|---:|
| 7273000 | 32 | 0 | 1 | 5 | 26 |
| 7273100 | 120 | 0 | 1 | 11 | 108 |
| 7283000 | 120 | 0 | 0 | 17 | 103 |
| 7286000 | 32 | 0 | 1 | 4 | 27 |
| 7170230 | 32 | 0 | 1 | 4 | 27 |
| 7170260 | 32 | 0 | 0 | 1 | 31 |
| **Gesamt** | **368** | **0** | **4** | **42** | **322** |

R3 gewann 364/368. Bei seinen 322 Siegen mit 3:0 ist der Auslöser ausgeschlossen. Auf **7273148/P0** ist er nachgewiesen: R3 gewann M1 mit 315:17, verlor M2 mit 229:245 und anschließend M3 mit 343:398. Dies ist eine weitere tatsächliche Gelegenheit. Die übrigen 1:2-Niederlagen sind 7273002/P1, 7286015/P1 und 7170236/P0. Dort fehlt die Matchreihenfolge. Unter den 42 Siegen mit 2:1 ist auf 7273116/P1 die Folge Sieg–Sieg–Niederlage belegt; bis zu 41 bestehende Siege könnten gefährdet sein. Aus den vorhandenen Endständen lassen sich somit höchstens **vier Rettungen** ableiten. Für keinen dieser vier Sitze liegt bisher der Ausgang mit einer V15-Übernahme in M3 vor. [Frühere Matchverläufe](../movement_soft_20261115/restart_route/verzoegerung/dev)

Der frühere R3-Kontextdatensatz enthält auf 24 anderen Solution-Karten 43-mal drei Siege, viermal Sieg–Sieg–Niederlage und einmal Sieg–Niederlage–Sieg. Der einzige tatsächliche Auslöser war genau die bereits geprüfte Gefährdungskontrolle 7287108/P0. Als separate Momentaufnahme sind die ersten 32 vollständigen Karten des noch laufenden gemeinsamen 400er-Vergleichs registriert. Auf diesen 64 Sitzen entfielen 1/3/9/51 Spiele auf 0/1/2/3 Matchsiege. Für die gemischten Fälle fehlt die Reihenfolge; dieser unvollständige Vergleich ist in den 368 Spielen nicht enthalten. [Archivstatistik des W–L-Versuchs](registered.json) · [Separat gekennzeichneter 400er-Ausschnitt](gelegenheiten.json)
