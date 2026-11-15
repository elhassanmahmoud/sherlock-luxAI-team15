# Kurskandidat mit Rückkehr zu V14

Das separate Paket übernimmt die Zwei-Ansichten-Beratung in Match 1. Nach dem ersten öffentlich gemeldeten Matchsieg bleibt sie für diesen Spieler aktiv. Nach einer Niederlage beim Auftakt gibt der Berater ab Match 2 den bereits im selben Zug berechneten V14-Weltbefehl zurück. Der Schalter gilt bis zum nächsten Spiel. Die Klasse stammt unverändert aus `scripts/r3_diag_after_loss.py` im Forschungscommit `86f18fa1b3c968f2bbd98fefe5483ed4e9d113c5`.

Das Kandidatenarchiv verwendet denselben Kurseinstieg `agents.sherlock.main.Agent_x` und für beide Spieler `agents/sherlock/weights/agent.pth`. Nur der Klassenimport und die ergänzte Umschaltklasse unterscheiden sich vom geprüften Diagonalpaket. Alle anderen Einträge einschließlich der gemeinsamen Gewichtsdatei sind bytegleich.

| Datei | SHA-256 |
| --- | --- |
| Diagonales Eingangspaket | `feaf20aa7058ad856634cd8a5a2daf56bfc6da4f6be296cff6d98fc55eefac25` |
| Paket mit Rückfall nach Match 1 | `dafeefecd9d032ff64cd20ebc7f92f089d11680f34a1576957f4aa4a721eeaf9` |
| Gewichtsdatei im Paket | `d20814949d4460c523ac718acf74e282ef5cdf4e3b743b4713d6aac95795d554` |
| 13 bekannte Diagnosepartien als Referenz | `41ad3ab55abe1bc4602c3c87b335443dd8dbc66bb2461f1b838f00d8d0b7a6cf` |

## Bauen und prüfen

Aus dem vollständigen Projekt mit den vorhandenen Studienartefakten. Der Paketbau liest nur archivierte Bytes. Die gesonderte Prüfung startet zwei vollständige Kursspiele gegen Solution_92. Python ist der Interpreter der Spielumgebung.

```bash
PYTHON=.venv/bin/python
BASE=experiments/analysis/movement_reflection_20261115/course/r3-diagonal-course-candidate.zip
OUT=$(mktemp -d)
mkdir "$OUT/research"
git archive 0105658188b2ec5eaf5c3a4b0ef477be9a1412f8 agents scripts lux | tar -x -C "$OUT/research"
git show aa5cd60354014ac33ddc4d6b1013e1842ba27aa7:scripts/r3_diagonal.py > "$OUT/research/scripts/r3_diagonal.py"
git show d635551:scripts/r3_diagonal_games.py > "$OUT/research/scripts/r3_diagonal_games.py"
for name in r3_diag_after_loss r3_diag_after_loss_games; do
  git show "86f18fa1b3c968f2bbd98fefe5483ed4e9d113c5:scripts/$name.py" > "$OUT/research/scripts/$name.py"
done
git show bd202fb26c5b6e919007760c62eb5830a1439191:experiments/candidates/movement_dagger_20261115/r3_soft.pth > "$OUT/r3.pth"
"$PYTHON" scripts/build_r3_diagonal_course_candidate.py --after-loss --base "$BASE" --out "$OUT/r3-diagonal-nach-niederlage-kandidat.zip"
"$PYTHON" -I scripts/check_r3_course_parity.py --after-loss --zip "$OUT/r3-diagonal-nach-niederlage-kandidat.zip" \
  --research "$OUT/research" --v14 "$OUT/research/agents/sherlock/weights/agent_p0.pth" \
  --r3 "$OUT/r3.pth" --out "$OUT/kursparitaet-kandidat.json"
```

Der ursprüngliche Prüfer lädt Paket und Forschungscode in getrennten Prozessen. Für 7286100/P0 muss der Rückfallzähler an jedem Schritt null bleiben und der Berater in allen drei Matches Bewegungen ändern. Für 7286137/P1 muss er vor Match 2 null sein, anschließend in jedem Schritt um eins steigen und genau 202 erreichen. Im zweiten und dritten Match darf dann keine R3-Bewegung ausgeführt werden. Beide Agenten müssen für jeden der insgesamt 606 Schritte dieselbe Weltaktionsmatrix liefern. Alle Kurs-Updates und die Aktionsfolgen beider Spieler werden gegen die zuvor publizierten Partien geprüft. Dieser Lauf prüft die Umsetzung. Die Spielstärke folgt aus den separaten Vergleichen auf frischen Karten.

## Tatsächliche Prüfung auf dem M3

Die gepackte Kandidatenklasse und der Forschungsagent erzeugten auf beiden Sitzen je 303 identische Weltaktionsmatrizen. Der Kurs-Runner rief je 303 Updates auf. Auf 7286100 als Spieler 0 blieb der Berater für die ganze Partie aktiv. Auf 7286137 als Spieler 1 übernahm nach dem ersten verlorenen Match V14 an allen 202 folgenden Aufrufen. Die Aktionstrajektorien beider Spieler stimmen mit den vollständigen Diagnosepartien überein. [Prüfprotokoll](kursparitaet-kandidat.json).
