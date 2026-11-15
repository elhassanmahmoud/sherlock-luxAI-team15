# Kurskandidat mit zwei Ansichten

Das separate Kandidatenarchiv lässt sich aus dem geprüften Standard-R3-Paket und dem festen Spiegelungsmodul bauen. Es nutzt dieselben 36 V14-Netze und denselben R3-Schüler. Der Builder ersetzt den Loader und ergänzt die ursprüngliche Klasse `DiagonalAgent` aus `aa5cd60354014ac33ddc4d6b1013e1842ba27aa7`. Alle übrigen ZIP-Einträge einschließlich der Gewichtsdatei sind bytegleich. Importpfad für den Kurs ist `agents.sherlock.main.Agent_x`. Beide Sitze laden `agents/sherlock/weights/agent.pth`.

In der ersten Ansicht wertet der Schüler die bereits für seinen Sitz ausgerichteten Eingangsdaten aus. Für die zweite vertauscht er die Kartenachsen, die beiden Einheitskoordinaten und die zugehörigen der 79 Merkmalspositionen. Nach der Rückabbildung der Richtungen mittelt er beide Aktionsbewertungen **vor** der Legalitätsmaske und der 70-%-Schwelle. V14 behält seine Schüsse einschließlich Zielversatz. Eine angenommene Bewegung rechnet der bestehende Berater für Spieler 1 in Weltkoordinaten zurück.

## Bauen und auf beiden Sitzen prüfen

Im Projektordner ausführen. `PYTHON` ist der Interpreter der Projektumgebung. `BASE` ist der Pfad zum geprüften Standard-R3-Archiv. Der ursprüngliche [R3-Builder](../../../../scripts/build_r3_course_candidate.py) kann dieses Paket aus den gespeicherten Git-Objekten neu erzeugen. Der neue Paketbau liest Gewichte ausschließlich als Bytes. Erst der Prüfaufruf lädt Agenten und spielt zwei Partien.

```sh
PYTHON=.venv/bin/python
BASE=experiments/analysis/movement_soft_20261115/candidate_package/r3-final-candidate.zip
OUT=$(mktemp -d)
mkdir "$OUT/research"
git archive 0105658188b2ec5eaf5c3a4b0ef477be9a1412f8 agents scripts lux | tar -x -C "$OUT/research"
git show aa5cd60354014ac33ddc4d6b1013e1842ba27aa7:scripts/r3_diagonal.py > "$OUT/research/scripts/r3_diagonal.py"
git show bd202fb26c5b6e919007760c62eb5830a1439191:experiments/candidates/movement_dagger_20261115/r3_soft.pth > "$OUT/r3.pth"
"$PYTHON" scripts/build_r3_diagonal_course_candidate.py --base "$BASE" --out "$OUT/r3-diagonal-course-candidate.zip"
"$PYTHON" -I scripts/check_r3_course_parity.py --diagonal --zip "$OUT/r3-diagonal-course-candidate.zip" \
    --research "$OUT/research" --v14 "$OUT/research/agents/sherlock/weights/agent_p0.pth" \
    --r3 "$OUT/r3.pth" --out "$OUT/diagonal-course-parity.json"
```

Die unabhängige Referenz lädt den Forschungsagenten aus dem rekonstruierten Quellstand. Der Kursagent läuft in einem anderen Prozess mit gesperrten Forschungsimporten. Auf der bekannten Karte 7271000 werden alle 303 Weltbefehlsmatrizen, Beraterzähler und alle Kurs-Updates pro Sitz geprüft. Beide Sitze müssen Schüsse mit echtem Zielversatz enthalten. Mindestens eine der beiden vollständigen Aktionsfolgen muss sich vom bereits protokollierten Standard-R3 unterscheiden. Das Protokoll benennt die betroffenen Sitze. Eine Stärkeaussage kommt aus der vorab festgelegten unabhängigen Bestätigung.

| Artefakt | SHA-256 |
| --- | --- |
| Standard-R3-ZIP | `8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d` |
| Diagonal-Kandidaten-ZIP | `feaf20aa7058ad856634cd8a5a2daf56bfc6da4f6be296cff6d98fc55eefac25` |
| Gemeinsame Kurs-Gewichtsdatei | `d20814949d4460c523ac718acf74e282ef5cdf4e3b743b4713d6aac95795d554` |
| Forschungsstand (Python-Quellen samt Diagonalmodul) | `2ede35c0e544c06b079b7ef7eaf7d1c0f56dd0c92f33347c172f30f48245c736` |
