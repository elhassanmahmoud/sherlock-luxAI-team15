# Wer die ersten 40 Züge steuert

Der Versuch verwendet die veröffentlichten R3- und V16-Kurspakete. Bei einer aus der Kursumgebung bekannten Sichtweite von höchstens zwei Feldern spielt R3 von der Aufbaurunde bis einschließlich Zug 40 des ersten Matches. V16 verarbeitet in dieser Zeit dieselben regulären Beobachtungen der eigenen Mannschaft. Vor dem nächsten Zug werden seine gespeicherten Aktionsrichtungen auf die tatsächlich gespielten R3-Befehle berichtigt. Bei Spieler 1 erfolgt die Rückübersetzung in V16s kanonische Richtungen. Der etwaige Parameterschätzer erhält die Weltbefehle. Die fünf Merkmale der letzten Bewegung liest V16 aus beobachteten Positionsänderungen. Ein erfolgloser befohlener Schritt zählt daher als beobachteter Stillstand. Nach Zug 40 erhält V16 die volle Kontrolle für den Rest aller drei Matches. Bei größerer Sicht wird R3 für die Partie gar nicht geladen.

Die Standardnamen beider Pakete lauten intern `sherlock`. Für diesen Versuch wird V16 über den ursprünglichen Kurslader geladen. Python registriert das unveränderte R3-Paket in einem eigenen Modulraum. Beide Pakete verwenden getrennte Agenteninstanzen und eigene Gedächtnisse. Der R3-Weltbefehl einschließlich eines eventuellen Schussziels wird als ganzes 16×3-Array übernommen.

## Prüfung an echten Zügen

| Sicht und Sitz | Frühphase gegen gespeichertes Original-R3 | Abweichende Züge gegenüber V16 in der Frühphase | Spätere Befehle identisch zum mitgeführten Original-V16 |
|---|---:|---:|---:|
| 1, P0, Karte 7261004 | 41/41 | 26 | 262/262 |
| 2, P1, Karte 7261005 | 41/41 | 26 | 262/262 |
| 3, P0, Karte 7261000 | V16 ab Beginn | – | 303/303 |
| 3, P1, Karte 7261000 | V16 ab Beginn | – | 303/303 |

Alle vier Technikpartien liefen regulär gegen Solution_92. In der Frühphase wurden die Befehle mit der früher gespeicherten Originalpartie auf demselben Sitz und Seed verglichen. Ein zweiter, separat geladener Original-V16 erhielt dieselben Beobachtungen. Für die ersten 41 Schritte folgte er anhand des Archivbefehls der tatsächlichen Handlungshistorie. Für alle späteren Zugentscheidungen wurden die Arrays des Prototyps mit seinen Entscheidungen verglichen. Die beiden Kanonisierungspfade für P1 wurden separat umgesetzt. Der jeweils erste Zähler umfasst einen neutralen Aufbauzug und 40 spielbare Züge. Auf den Karten mit kurzer Sicht erfolgte die Übergabe bei Zug 41. [Prüfung P0](technik_0.json) · [Prüfung P1](technik_1.json).

**Wann sah Sherlock erstmals ein Relikt?** Nachträglich wurden die tatsächlich sichtbaren Reliktpositionen in den archivierten Originalpartien der beiden Techniksitze gezählt. Auf Karte 7261005 (P1, Reichweite 2) sah R3 in Zug 30 das Relikt auf (21, 15). Das reine V16 sah dieselbe Position erstmals in Zug 33. Auf Karte 7261004 (P0, Reichweite 1) sah bis zur Übergabe in Zug 41 keiner der beiden ein Relikt. In den unvermischten Archivpartien sah V16 sein erstes Relikt in Zug 56 und R3 in Zug 58. Diese beiden späteren Zeitpunkte gehören zu den unabhängigen Originalverläufen. Als Beleg für den Zeitpunkt der ersten Sichtung des gemischten Agenten nach Zug 40 dienen sie nicht. Es sind zwei Technikbeispiele, keine Erfolgsvoraussetzung. [Originalbeobachtungen und Prüfsummen](reliktsichtung.json).

## Aufwand und Wiederholung

Die beiden bestehenden ZIPs belegen zusammen **37.060.540 Bytes**, davon **27.591.024 Bytes für R3** zusätzlich zu **9.469.516 Bytes für V16**. Die entpackten Gewichtsdateien zusammen haben **47.177.776 Bytes**. Das sind die gemessenen Größen der Originaldateien. Eine integrierte, gegebenenfalls komprimierte Kursabgabe wurde für diesen Vergleich nicht gebaut. [Pakete und Prüfsummen](herkunft.json).

Für eine Wiederholung im Stamm des Studien-Repositories mit der eingerichteten Lux-Umgebung die vier Thread-Variablen sowie `PYTHONHASHSEED` wie unten setzen. Die beiden mit `0` und `1` bezeichneten Spuren erhalten beim Spielen disjunkte Aufträge. Nach vollständigem Abschluss kann der gespeicherte Rohdatensatz ohne erneute Spiele ausgewertet werden.

```sh
d=experiments/analysis/v16_finalwoche_20261122/fruehuebergabe
py=/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONHASHSEED=0

# Öffentliche Kartenauswahl reproduzieren
"$py" "$d/spielen.py" karten

# Ergebnisse aus vollständigem Archiv prüfen
"$py" "$d/auswertung.py" auswahl "$d/auswahl_partien.jsonl.gz"
```

Die gesicherte Kartenliste enthält die ersten 40 aufsteigenden passenden Seeds von 160362001 bis 160362073. 22 Karten haben Sichtweite eins, 18 Sichtweite zwei. Vor jedem Spiel mit diesem Panel wird der tatsächliche öffentliche Parameter vom Kurs-Runner erneut mit der Liste abgeglichen. [Versuchsplan](PLAN.md) · [Feste Kartenliste](karten.json).
