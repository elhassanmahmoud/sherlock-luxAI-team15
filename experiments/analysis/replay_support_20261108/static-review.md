# Statischer Review: Replay-Abdeckung gespeicherter Endnetz-Gewinner

Ergebnis: **Spec PASS / Quality PASS, keine Blocker.** Dies ist eine statische Prüfung; die reale Analyse ist noch nicht ausgeführt oder datenmäßig abgenommen.

Geprüfte Dateien: `/tmp/replay-support-diagnosis-20261108/SPEC.md`, `support.py`, `bindings.json`, `READY.json`, `selfcheck.json`; zusätzlich den archivierten Sampler-/Ausgabeaufbau in `scripts/fog_influence.py` lesend nachvollzogen. Keine Python-, NumPy-, Torch-, pytest-, Modell- oder Spielausführung, keine Repositoryänderung.

## Geprüfte Verträge

- Zuordnung korrekt: Bankreihenfolge control41/neutral41/control42/neutral42 und zugehörige Mitgliedsspalten **36/38/37/39**. Die historischen Konstanten werden per AST/hashgebundenem Git-Blob geprüft; gespeicherte Labels und alle Mitgliedshashes werden erneut verglichen.
- Fest genau 10000 vorhandene Zeilen, 2500 pro Arm. Pufferpfade und Hashes sind armweise korrekt gebunden. Originalindizes müssen eindeutig und innerhalb des jeweiligen 300000-Zeilen-Puffers liegen. Die gespeicherten Q-Zeilen besitzen dieselben Bankindizes/Armkennungen.
- Jede Bank-ns-Zeile und ihre next_mask werden bytegenau am referenzierten Originalindex gegengeprüft. Der historische Sampler verlangt `(done == 0) & mask.any`; der Runner verlangt daher für jede Bankzeile originales done=0. Terminalwerte oder ungültige Flags führen zum Abbruch, nicht zu Filterung oder Ersatz.
- Gewinner werden ausschließlich aus der passenden eigenen Endnetzspalte unter der gespeicherten Maske gewählt. Gleichstände verwenden die erste legale Klasse. Alle sechs Q-Werte müssen endlich sein; leere Masken sind ausgeschlossen. Kein anderer Netz-/Ensemblevergleich und keine Q-abhängige Stichprobenauswahl.
- Coverage verwendet exakt bytegleiche aktuelle `s`-Zeilen im eigenen Replay und deren dort gespeicherte `a`. Aktion und aktuelle Zeile werden innerhalb desselben Streamblocks/Originalindexes verbunden. Es gibt keine Zuordnung von `a[i]` oder `a[i+1]` als tatsächliche Folgeaktion für `ns[i]`.
- Fehlender s-Treffer bleibt ausdrücklich UNKNOWN. Bei vorhandenen Treffern sind beobachteter bzw. nicht beobachteter Gewinner disjunkt. Doppelte Suchzeilen verdoppeln keine ursprünglichen Histogrammzählungen; wiederholte Bankzeilen bleiben beschreibend erhalten. Aktuelle s-Zeilen dürfen Übergänge mit anschließendem terminalem Zustand sein.
- 79-Merkmalsgleichheit wird nicht mit vollständiger Belief-/Regel-/Spielzustandsgleichheit verwechselt. Endnetz-Q ist nicht historisches Online-/Target-Q; keine TD-Fehler-, Qualitäts-, Kausal- oder Stärkeaussage. Unbeobachtet im endlichen Replay bedeutet weder unmöglich noch fehlerhaft.
- Ein kleiner Suchindex pro Arm, 4096-Zeilen-NPY-Streams und sequentielle Pufferverarbeitung begrenzen den Speicher. Keine Projekt-/Modellimporte. Exakte Root-Freigabe vor echter Analyse; exklusiver Ausgabepfad, 120-Sekunden-Alarm plus Zeitprüfungen, Nice+10, numerische Threads=1, kein Retry/Resume. Eingabehashes werden vor und nach der Analyse geprüft.

## Geprüfte Byteversionen

- support.py: `e1dc7a4a2e72a159e6477e00c7f024d172db0116702c115b76dbe31e14b9cdbb`
- SPEC.md: `e56e3213bebd15d6cb20278e9529ddc92eba54b27e27f1ec5cf6e710d567d83a`
- bindings.json: `4aafc5c1e160f06cdfb73d5d3ae0a82f0f64ee44761bb98d479d72cbfff4afe1`
- selfcheck.json: `e3dc2c22565d2308f39e135eaf74383bde16d416f03d60639d8351651d3d6154`

Der vorhandene Bericht meldet 22 synthetische Selbstchecks; diese wurden in diesem Review bewusst nicht wiederholt. Reale NPZ-Inhalte, berechnete Häufigkeiten und erfolgreiche Laufzeit bleiben ausstehende Tatsachen und werden hier nicht behauptet.
