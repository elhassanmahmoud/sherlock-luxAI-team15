# Einmaliger begrenzter Repräsentationscheck – 21.10.2026

**Informationsverlust bestätigt; zwei nominelle Konvergenzen auf zwei der drei festgelegten Karten.** Damit greift der vorab festgelegte Abbruch wegen eines reinen Ein-Karten-Befunds nicht. Der Prüfauftrag endet trotzdem hier. Dies erlaubt höchstens eine spätere Repräsentationsdiskussion: kein statistischer Gate-Erfolg, kein Agentenpatch, keine Freigabe für weitere Spiele oder Training.

## Isoliertes tatsächliches Feature-Fixture

Aus `features.py` wurden per AST ausschließlich `build_features`, `_nearest`, `_names` und ihre Featurekonstanten ausgeführt; aus `geometry.py` nur Richtungsarrays und `mirror_positions`. Keine Paketinitialisierung, Agenten-, Torch-, JAX-, Modell- oder Engineimporte.

Das Fixture verwendet die dokumentierten eigenen UID7-Daten (19,10), E125, und sichtbaren Gegner UID4 (20,9), E89 sowie UID7 (19,8), E150 aus 510930/p1/M2/t78. **Der übrige vollständige Kontext ist kontrolliert synthetisch und konstant**, unter anderem leere Zielklassen/Zuordnung, gleichförmige Karten, festgelegte Zähler und nur die fokale eigene Unit. Es rekonstruiert weder den fehlenden realen Featurevektor noch reale Zielzuweisungen oder Terrain.

- Nur Energie der nicht ausgewählten gegnerischen UID7 **150→50**: alle **79 Features exakt identisch**.
- Gegenkontrolle: nur Energie der ausgewählten UID4 **89→50**: genau **Index72 `enemy_energy_rel`** ändert sich, 0,345214→0,635149.
- Beide Prüfungen separat im Welt- und gespiegelten kanonischen Raum erfolgreich. UID4 bleibt bei Manhattan-Abstand2 für beide Gegner ausgewählt. Die Vektoren verschiedener Orientierungen müssen untereinander nicht identisch sein.

Die Quelleninspektion bestätigt: `make_context` bildet Gegner über aufsteigende `np.where(enemy_mask)`-Slotnummern, filtert ungültige Positionen, **aber keine negative Gegnerenergie** (`features.py:299–333`). Spiegelung verändert keine UID-Reihenfolge. `build_features` wählt mit `np.argmin` im Gleichstand den ersten Gegner (`:455–469`). Der Observer behält sichtbare negative Gegner ebenfalls bei und schreibt Positionen/Aktionen im Weltraum. Die Fensterklassifikation hat deshalb negative Gegner bei der nächsten-Auswahl ausdrücklich nicht entfernt. Im zusätzlichen Ereignis ist UID11 mit E−27 sichtbar, Abstand4; die ausgewählte UID10 hat E3, Abstand2.

## Ausschließlich die vorab festen 84 Übergänge

Lokale Schritte65…85 inklusive, je21 Übergänge. Nenner: alle bei t maskierten eigenen Slots mit E≥0 und final ausgegebener kardinaler Bewegung1…4. Abgleich gegen Rohaktionen/Truth bestätigt, dass keine solche Bewegung wegen fehlendem Entscheidungseintrag ausgelassen wurde. Insgesamt817 aufgezeichnete Unitentscheidungen, darunter505 Nennerbewegungen; keine zusätzlichen Karten oder Fenster.

Konvergenz bedeutet hier **nominelle Bewegung**: eigener Start plus ausgegebene Richtung stimmt mit dem Start eines bei t sichtbaren Gegners plus dessen nachträglich aufgezeichneter kardinaler Bewegungsrichtung überein. STAY/SAP-Gegner sind keine gleichzeitig eintreffenden Bewegungen. Negative Gegner wären im nominellen Zähler erhalten geblieben; Energie/Budget und Folgemasken stehen getrennt im JSON. Die beiden gefundenen Gegner sind nichtnegativ und beide Parteien können jeweils die nominellen Bewegungskosten bezahlen.

| Fester Fall | E≥0 eigene Bewegungen | nominelle Konvergenzen | konvergierender Gegner nicht nächstes Feature |
|---|---:|---:|---:|
| 510858/p1/M2 | 93 | 1 | 1 |
| 510858/p0/M2 | 120 | 0 | 0 |
| 510847/p0/M3 | 131 | 0 | 0 |
| 510930/p1/M2 | 161 | 1 | 1 |
| Gesamt | **505** | **2** | **2** |

Die beiden Paare sind zugleich zwei unterschiedliche eigene Bewegungsentscheidungen:

| Fall/t | eigene Bewegung | sichtbarer konvergierender Gegner | nominelles Ziel | ausgewählter nächster Gegner | tatsächliche Folgemasken eigen/Gegner |
|---|---|---|---|---|---|
| 510858/p1/M2/t68 (global169) | UID12 (15,18), E88, hoch | UID12 (14,17), E243, rechts | (15,17) | UID10 (13,18), E3; Distanz2 statt ebenfalls2 | aus/an |
| 510930/p1/M2/t78 (global179) | UID7 (19,10), E125, hoch | UID7 (19,8), E150, runter | (19,9) | UID4 (20,9), E89; Distanz2 statt ebenfalls2 | aus/an |

Die extern gespeicherten Folgepositionen beider Slots stimmen jeweils mit dem nominellen Ziel überein. **Eine gespeicherte Position oder Restenergie bei Maske aus ist keine lebende Unit.** Folgemasken sind keine Lebenszyklus-/Schadensattribution. Terrain, Drittunits, simultane Effekte und Spawn können nominale Konvergenzen und Slotfolgen beeinflussen; es wurde kein Kollisionsausgang isoliert oder gegnerischer Zug zum Entscheidungszeitpunkt vorausgesetzt.

## Schluss und Grenzen

Der kontrollierte Informationsverlust ist direkt gezeigt, und sein geometrischer Kontext tritt zusätzlich zum bekannten Fall auf Karte510858 auf. Das belegt weder die Ursache der Netzentscheidung noch eine bessere mögliche Aktion oder den Anteil am Spielverlust. Die vier Fenster stammen aus nach Ergebnis ausgewählten Extremfällen: **2/505 ist ein begrenzter Archivzähler, keine allgemeine Häufigkeit oder Wirksamkeitsschätzung.** Ein umfassenderes Gegnerbild kann trotz zusätzlicher Information ohne Nutzen bleiben. Die Zweikartenregel war nur eine Aufwandsschwelle.

Keine Featureänderung, keine Regeln, keine neue Instrumentierung, keine Tests/Spiele/Modelle und keine laufenden Studienresultate. Nur dieser Prüfauftrag wurde ausgeführt; er ist abgeschlossen.

## Nachweis und Reproduktion

- Ausführbares Skript: `/tmp/sherlock-representation-probe-20261021.py`
- Kompaktes Aggregat samt zwei Einzelereignissen, Fixturewerten, Rohdatei-/Quellenhashes: `/tmp/sherlock-representation-probe-20261021.json`
- Ausführung: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python /tmp/sherlock-representation-probe-20261021.py` (nur Stdlib/NumPy; Rechenzeit unter1 Sekunde).
- HEAD vor/nach: `a5d2e61b0e8654bad64e31c29447ada1e439174d`. SHA-256 von `features.py`, `geometry.py`, `main.py` und Observer vor/nach identisch; die zwei vorab angegebenen Feature-/Mainhashes stimmen. Alle vier gelesenen Rohdateihashes vor/nach identisch.
- Zeitaufwand unter30 Minuten. Alle Ausgaben ausschließlich `/tmp`; keine Repository-, HEAD- oder Gewichtsänderung. Das laufende Curriculumtraining wurde weder gelesen noch beeinflusst.
