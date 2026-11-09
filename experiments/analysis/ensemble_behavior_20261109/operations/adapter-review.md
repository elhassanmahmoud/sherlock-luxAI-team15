# Vorläufiger statischer Adapterreview

**Ein konkreter Blocker offen; Root hat ihn angenommen und die enge Korrektur mit Negativtest beauftragt.** Nur `rng_identity`, `BehaviorEnsemble` und zugehörige vorhandene Adaptertests geprüft. Kein Urteil zum noch unfertigen Runner oder Owner, keine eigenen Tests oder Modelle.

## Doppelinstallation auf demselben Agenten

`BehaviorEnsemble.__enter__` prüft nur `self.entered`. Zwei unterschiedliche Adapter A und B können deshalb auf demselben Agenten verschachtelt installiert werden. B speichert A._act als Originalaufruf. Beim nächsten Handeln registrieren beide ihren Forward-Hook; beide lokalen active/last-Prüfungen bestehen. Ein Hook erhält dann bereits den Ensemblemittelwert des anderen als vermeintlichen Lernoutput an Position 18 und mittelt erneut. Damit sind genau 36 unverfälschte, einmalige Beiträge nicht mehr garantiert.

Erforderliche enge Korrektur: Doppelinstallation instanzlokal am Agenten verweigern und ursprünglichen Agentzustand sauber wiederherstellen. Kleiner Negativtest mit zwei verschiedenen Adapterinstanzen, unverändertem ersten Adapter nach Zurückweisung und anschließendem normalem Cleanup. Keine globale Sperre oder weitere Architektur nötig. Root und motion_impl unmittelbar informiert. Bis zur stabilen Korrektur kein abschließendes Adapter-PASS.

## Übriger gelesener Vertrag

Für den vorgesehenen einfachen Kontext ist die Umsetzung nachvollziehbar: ursprünglicher q-Output wird an Originalposition 18 eingesetzt; die anderen 35 Module werden je einmal auf demselben Eingabetensor ausgewertet. Geordneter Stack und Mittelwert, kein zusätzliches Originalmitglied 18. Separate neue Module mit kopierten Statewerten, eval, ohne Gradienten und ohne Adamzugehörigkeit; q/Target/Optimizer werden nicht ersetzt. CPU, Form/Dtype/Finitheit, ursprüngliche Mitglieder und Optimizerparameter werden geprüft.

Installation erhält Torch-RNG per fork_rng und vergleicht Python-/NumPy-/Torch-/privaten Agent-RNG sowie Lernidentitäten. Temporärer q-Hook ist nur im ursprünglichen `_act_est`-Aufruf aktiv und wird bei normaler Rückkehr sowie Fehler innerhalb dieses Aufrufs im finally entfernt. Matchstart/leere Units benötigen keinen Forward. OFF ruft den gespeicherten Originalaufruf direkt auf, ohne weitere Netze oder Hook. Roh-Q, Mittelwert, Mitgliederwerte und tatsächliche Cachemasken werden vor der mutierenden Core-Numpy-Maskierung kopiert; keine zweite `_decide`- oder Q-Abfrage als Observer.

Die vorhandenen synthetischen Tests prüfen Forwardanzahl/Reihenfolge, aktuellen statt kopierten Lernoutput, unveränderte rohe NumPy-Belege, Setup-RNG und Optimizerparameter, OFF, leere/reset-Fälle, Fehlercleanup und ungültige Mitglieder. Der Lernvergleich ruft das tatsächliche originale `_learn` auf gleichem kleinem Replay mit passenden privaten RNGs auf, einschließlich Adam und sofortiger Targetkopie, und verlangt identische q-/Target-/Optimizerzustände sowie unveränderte eingefrorene Netze. Das ist passend für die aktuelle Linear/ReLU-Architektur; keine zusätzliche Lernimplementierung im Test. Die gemeldeten 14 grünen synthetischen Tests wurden hier nicht erneut ausgeführt oder anhand eines nicht bereitgestellten Logs eigenständig bestätigt.

## Geprüfte Bytefassung und spätere Begrenzung

- `scripts/ensemble_behavior_study.py`, Präfix vor `def validate_release`, 127 Zeilen: SHA256 `e57e94a2bfd9faaa25373c924902942cd683bc7cbb88defa60744fbd0d66d1e7`.
- Ganze Study-Datei zum Lesezeitpunkt, nur Identifikation des laufenden Arbeitsstands: `70a169a64d85c004296092d213e34c99318edd43efca811c01b07fad044a9e95`.
- `tests/test_ensemble_behavior_study.py`, Präfix vor `def test_joint_release`, 150 Zeilen: `a84b0efdc400c8703348ad5fe7e4240114274233f64dd0fa867b5a7107f7368c`.
- Ganze Testdatei zum Lesezeitpunkt: `a1e55b3146769cd6ced6b12072028935a654d0ff282830bc691bfee2f5b2439c`.

Später nur die stabile Adapterkorrektur und den zugehörigen Negativfall abgleichen; kein erneuter vollständiger Adapterreview ohne weiteren Anlass. Runner-/Historien-/Barrierenabnahme ist separat ausstehend. Der von Root separat gemeldete historische technische Hashlink gehört nicht zu diesem Adapterreview.
