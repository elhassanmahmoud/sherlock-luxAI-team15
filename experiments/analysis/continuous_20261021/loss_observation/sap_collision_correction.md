# Erratum: Sapkosten ändern hier nicht die Kollisionsentscheidung desselben Schritts

**Meine frühere H1-Begründung war falsch und wird zurückgezogen.** Betroffen ist `/tmp/sherlock-solution-counterplay-20261021.md` (SHA256 `b4a04c53c5dce71ff1229d3e4ac418512a18a8581e067569ba7ea6867a0dfd4a`), insbesondere die behauptete Umkehr des Kollisionsgewinners im Beispiel 100 gegen 90 Energie. Dieser Korrekturtext ersetzt jene Aussage; der historische Bericht wurde nicht still überschrieben.

## Fehler und richtige Datenabhängigkeit

In der tatsächlich installierten Engine unter `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/lib/python3.13/site-packages/luxai_s3/env.py` wird in **Zeile293** `original_unit_energy = state.units.energy` festgehalten: **nach Bewegung, vor Sap**. In **Zeilen459–462** erhält der Aufbau der aggregierten Energie-/Voidkarten genau dieses Array. Die Kollisionsprüfung **486–499** verwendet diese aggregierten Energiekarten.

Ich hatte aus der textlichen Reihenfolge „Sapblock vor Kollisionsblock“ fälschlich auf eine Energiegrundlage nach Sap geschlossen und die tatsächliche Datenquelle im `lax.scan` übersehen. Richtig ist: Bei unveränderten Bewegungen/Positionen und identischem Ausgangszustand bleibt die Energiegrundlage der unmittelbaren Kollision beim Wechsel STAY↔SAP gleich. Sap verändert die gespeicherte Restenergie, nicht diesen Kollisionsvergleich.

Die früheren drei Source-AST-Fixtures prüften Teile von Solution_92, das vierte lediglich meine isolierte Arithmetik. **Keines prüfte die Engine.** Sie waren daher kein Beleg für den behaupteten Kollisionsflip.

## Tatsächlich ausgeführter enger Engine-Test

Am21.10.2026 mit vorhandener `.venv/bin/python -B`, ohne neue Abhängigkeiten. Direkt `LuxAIS3Env.reset_env` und zweimal `step_env` verwendet; **kein Agent/Modell/Training, keine vollständigen Spiele**, kein Torch- oder `agents`-Import.

- Ein gemeinsamer, unveränderter `EnvState`, derselbe Schritt-Key `jax.random.key(123)` und dieselben `EnvParams` für beide Zweige.
- Initialzustand aus `reset_env(jax.random.key(0),params)`; nur je UID0 maskiert, Positionen (10,10)/(11,10), Energien100/90. Gelände leer; Energieknotenmasken deaktiviert; `steps=match_steps=7`, sodass in diesem Schritt kein Spawn/Matchreset eintritt.
- Parameter: Bewegungskosten1, Sapkosten40, Sapreichweite5, Splashfaktor0,5; übrige Parameter unverändert `EnvParams`.
- Gegner in beiden Zweigen Aktion `[4,0,0]`, also links auf (10,10). Eigene Aktion entweder `[0,0,0]` oder `[5,1,0]`, Sap auf die alte Gegnerposition (11,10).
- Die echte Energie-Feldfunktion erzeugt trotz deaktivierter Knoten ein Feld von +2; dieser gleiche spätere Zuschlag ist in den Endwerten enthalten.

| Tatsächliches Ergebnis nach einem Schritt | STAY | SAP |
|---|---:|---:|
| Eigene UID0 überlebt | ja | ja |
| Gegnerische UID0 überlebt | nein | nein |
| Beide gespeicherten UID0-Positionen | (10,10) | (10,10) |
| Eigene Restenergie einschließlich Feld | 102 | 62 |
| Gegnerische gespeicherte Energie, Slot bereits entfernt | 89 | 69 |
| Kollisionsgrundlage eigener/Gegnerenergie | 100 / 89 | 100 / 89 |

**Assertions bestanden:** komplette 2×16-Unitmasken beider Zweige identisch; nur eigene UID0 aktiv; beide UID0-Positionsarrays identisch; eigene Energiedifferenz exakt40; ursprünglicher Eingabezustand enthält weiterhin100/90. Prozess Exit0. Ein JAX-FutureWarning zur int32→int16-Konvertierung im synthetischen Aufbau trat auf; keine Exception oder fehlgeschlagene Assertion.

## Konsequenz

Der behauptete unmittelbare H1-Mechanismus ist widerlegt. **Kein Kollisionsveto, keine Reserveänderung und kein Training werden durch dieses Beispiel gerechtfertigt.** Vorhandene Beobachtungsdaten dürfen STAY→SAP, Energie und folgende Verluste weiterhin beschreiben; sie dürfen daraus aber nicht den zurückgezogenen unmittelbaren Kollisionsmechanismus ableiten. Eine etwaige spätere Energiewirkung wäre eine andere, hier nicht untersuchte Frage und wird nicht als Ersatzhypothese behauptet.

Keine Repositorydatei, Gewichte oder Gitdaten geändert. Dieses Erratum und der enge Engine-Test sind der gesamte Prüfumfang.
