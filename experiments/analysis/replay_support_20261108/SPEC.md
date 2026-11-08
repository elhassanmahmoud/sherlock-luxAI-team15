# Exakte Replay-Abdeckung vorhandener Endnetz-Gewinner

**Status: nur vorbereitet.** Keine realen NPZ-Inhalte wurden geöffnet oder analysiert; vorhandene Bytes wurden inventarisiert/gehasht und JSON-/Quellmetadaten gelesen. Die echte Analyse wartet auf unabhängige statische Prüfung und gesonderte Root-Freigabe.

## Feste Frage und Umfang

Für maximal10000 bereits gespeicherte Bank-ns-Zeilen: Welchen legalen Gewinner nennt genau das zugehörige eigene Endnetz in den vorhandenen gespeicherten Q-Ausgaben? Wie oft findet sich dieselbe bytegenaue79-Merkmalsfolge als aktuelles `s` im selben ursprünglichen Replay, und welche tatsächlich ausgeführten `a` sind an diesen Treffern gespeichert? Keine weitere Rolle, kein Ensemblevergleich, keine neue Stichprobe, keine Aktions-/Netzauswahl.

Vier Arme werden strikt getrennt ausgewertet; Gesamtsummen sind rein deskriptiv. Bankreihenfolge und Mitgliedsreihenfolge sind verschieden und historisch eindeutig gebunden:

| Arm | Bank-Index | Eigenes Endnetz in member_q | Zugehöriger Puffer |
|---|---:|---:|---|
| control41 | 0 | 36 | `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/runs/20261108_fog_reward_control41/weights/agent.buffer.npz` |
| neutral41 | 1 | 38 | `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/runs/20261108_fog_reward_neutral41/weights/agent.buffer.npz` |
| control42 | 2 | 37 | `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/runs/20261108_fog_reward_control42/weights/agent.buffer.npz` |
| neutral42 | 3 | 39 | `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/runs/20261108_fog_reward_neutral42/weights/agent.buffer.npz` |

## Exakte Inputs und Herkunft

| Input | SHA-256 | Bytes |
|---|---|---|
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/fog_influence_20261108/run_v1/bank.npz` | `e64df568ab55b9ba4ab915b061d3dd8449786f8bb6d9accdf65bea263e988774` | 3311006 |
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/fog_influence_20261108/run_v1/outputs.npz` | `f1b607f11b8089d8869aa3754ac540e7846f279a3ac5546be31e0892f13f6c68` | 10904506 |
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/runs/20261108_fog_reward_control41/weights/agent.buffer.npz` | `20c66ad7461aafff93e1fab8b9df760cb0d4adcbd008da9230ad18192d5decb6` | 196201440 |
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/runs/20261108_fog_reward_neutral41/weights/agent.buffer.npz` | `685924fb456a4e0795a737325e58bc05762a12bbd7f8ddb565961678aa92d118` | 196201440 |
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/runs/20261108_fog_reward_control42/weights/agent.buffer.npz` | `1b967416ca2432929722099c3d88e30e732ca36a27b9384cd325502b11f520ba` | 196201440 |
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/runs/20261108_fog_reward_neutral42/weights/agent.buffer.npz` | `501ba751f93693d778e7a65ec48e17de08d7cf57560677af16dabea9fdc3ad15` | 196201440 |
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/fog_influence_20261108/run_v1/summary.json` | `a0571fd3e07c982d5650554f22a715d10f0328028133d7f37bc22ba02e66ede9` | 158855 |
| `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/fog_influence_20261108/run_v1/bank_manifest.json` | `7c42bc89b4a6840f54ec51466da673d7375b5465554ce656f97d11c13754f66b` | 4892 |

Insgesamt799,185,019 gespeicherte Inputbytes. Die vier Puffer sind je300000 Zeilen groß; die ursprüngliche Bank enthält je2500 Zeilen. Die aktuelle Artilleriestudie und ihre Puffer werden nicht gelesen.

Historischer Einfluss-Quellstand `f6f8b8ad2feecb680a3cd06a0eab2669d5d7b4d7`, `scripts/fog_influence.py` SHA-256 `be6da3adccc23c5d4fd7a0f20e62a1a9c62b602e67c1629be8e3ea4ed7fa80e0`. Das Git-Blob stimmt mit dem gespeicherten Quellhash überein. Die Literale ARMS, NEW_MEMBERS und LIMIT wurden per AST geprüft, ohne Codeimport/-ausführung. Bankmanifest und Zusammenfassung stimmen exakt überein. Laufzeitprüfung bindet zusätzlich gespeicherte member_labels/ordered_member_hashes und row_indices/arm_indices in outputs.npz an Bank und ursprünglichen Puffer.

## Terminalvertrag: keine stillschweigende Filterung

Der historische Sampler wählt ausdrücklich `(done==0) & mask.any`. Daher müssen ALLE Bankzeilen am tatsächlich referenzierten Original-Pufferindex nichtterminal sein. Der Runner liest jedes entsprechende originale `done`, prüft0/1 und verlangt0. Ein Terminalwert ist ein Provenienz-/Zuordnungsfehler: gesamter Lauf unvollständig stoppen, keine kleinere Hauptmenge, keine Ersatzzeilen. Bericht führt `terminal_bank_rows` (erwartet0) und `nonterminal_bank_rows` separat. Aktuelle-s-Abdeckung benutzt dagegen alle tatsächlich gespeicherten a-Zeilen dieses Puffers, auch wenn deren Übergang anschließend terminal ist.

## Datenvertrag und Rechenweg

1. Root-Freigabe und alle Eingabehashes prüfen. NumPy erst danach für gespeicherte Zahlen importieren; keine Projektmodule, Torch, Modelle oder Forward-Pässe. Numerische Threadzahlen1; ein niedrig priorisierter Prozess.
2. Bank: ns=(10000,79), float32; mask=(10000,6), bool und jeZeile mindestens eine erlaubte Klasse; ursprüngliche Indizes int64, Armindizes uint8. Gespeicherte member_q=(40,10000,6), endlich float32. Labels/Hashes und Zeilenidentitäten exakt prüfen. Nur die jeweils zugehörige eigene Endnetzspalte wird zur Gewinnerbestimmung genutzt; die anderen gespeicherten Netz-/Ensemblewerte werden nicht analysiert.
3. Pro Arm alle2500 Bank-ns und next_mask bytegenau gegen ns/mask an den Original-Pufferindizes prüfen; done wie oben. Keine Neusammlung oder Q-abhängige Auswahl.
4. Gewinner unter vorhandener Bankmaske bestimmen; exakt gleiche Werte wählen die erste Aktionsklasse wie argmax. Q-Abstand zum zweiten legalen Wert rein deskriptiv protokollieren, bei nur einer legalen Klasse null. Keine nachträgliche Schwelle.
5. Ein Dictionary nur für die maximal2500 gesuchten Feature-Bytefolgen dieses Arms aufbauen. Originales aktuelles s in4096-Zeilen-Blöcken streamen; nur exakt passende Bytes erhalten sechs a-Zähler. Keine Näherung, Rundung oder Normalisierung; +0/-0 bleiben byteverschieden. Mehrfache Bankzeilen bleiben getrennte berichtete Zeilen, erzeugen aber keine mehrfach gezählten Originalübergänge im Histogramm.
6. Drei disjunkte Kategorien: kein aktueller s-Treffer → unbekannt; mindestens ein s-Treffer und Gewinner mindestens einmal ausgeführt → beobachtet; s-Treffer, aber Gewinner nicht unter deren a → in diesem endlichen Puffer nicht beobachtet. Kein s-Treffer wird NICHT als Nullabdeckung interpretiert.

## Vorab feste Ausgaben

`run_v1/rows.jsonl`: Arm, Bankzeile, Originalindex, Mitgliedsindex, Feature-Bytehash, maskierter Endnetz-Gewinner, legaler Q-Abstand, alle sechs tatsächlichen a-Zähler, Zahl exakter s-Treffer, Gewinnerzähler und bedingter empirischer Anteil (null bei fehlendem s-Treffer).

`run_v1/summary.json`: alle vier Arme einzeln, feste Nenner, Terminal-/Nichtterminalnenner, Zahl verschiedener Feature-Bytefolgen, drei Kategorieanzahlen, Treffermultiplizität, deskriptive Gesamtsummen, Integritätsnachweise und Laufzeit. `incomplete.json` bei Fehler/Timeout; Teilzahlen sind kein abgeschlossenes Ergebnis. Keine IID-Intervalle oder Signifikanzentscheidung.

## Harte Interpretationsgrenzen

`mask[i]` gehört zum Folgezustand `ns[i]`; `a[i]` gehört zu aktuellem `s[i]`. Es gibt kein next_actual_action und keine Unit-/Spielverkettung. Weder a[i] noch a[i+1] wird als Folgeaktion ausgegeben. Die genutzten Q-Zahlen sind Endnetzbewertungen, keine historischen Online-/Target-Q-Werte; historische TD-Fehler, Bellman-Bias und projizierte Targetlabels sind damit nicht rekonstruierbar. Off-policyDQN ist wegen abweichender Verhaltens-/Zielpolicy nicht mathematisch fehlerhaft.

Gleiche79 Merkmale beweisen keinen gleichen vollständigen Belief, Parameterposterior, Regelzustand oder Gegnerkontext. Seltene/fehlende Aktion in einem endlichen, teilweise überschriebenen Replay beweist weder Unmöglichkeit noch falschen Q-Wert. Häufige Aktion beweist keine Qualität. Die vier historischen Arme und korrelierten Zeilen erlauben keine allgemeine Kausal-/Stärkeaussage. Kein Training, Kandidatenwechsel oder Eingriff in die laufende Studie folgt automatisch.

## Ressourcen und Freigabe

Puffer nacheinander; s/ns als NPY-Streams direkt aus NPZ,4096 Zeilen/Block. Kein gleichzeitiges Laden der vier196MB-Puffer; nur kleine Bank, gespeicherte Q-Matrix, ein Aktionsvektor und kleiner Suchindex im Speicher. Dateien/Hashlesen sind lineare I/O. Harter120s-Alarm einschließlich NumPyimport/Hashprüfung und zusätzlich monotone Checkpoints; Nice+10 und numerische Threads1. Kein automatischer Retry/Resume.

Root erstellt nach statischer Prüfung ausschließlich unter diesem /tmp-Verzeichnis ROOT_APPROVAL.json: `approved:true`, `allow_numpy_saved_arrays_only:true`, `sha256` für support.py, SPEC.md und bindings.json. Bis dahin kein run_v1. Danach höchstens einmal `<bestehende .venv/bin/python> -B /tmp/replay-support-diagnosis-20261108/support.py run`. Jede Änderung entwertet die gebundene Freigabe.

Tatsächlich vorbereitet: Hash-/Metadatenprüfung bestanden und22 winzige synthetische Selbstchecks bestanden, NumPy2.5.4, Threads1. Diese Selbstchecks öffnen ausschließlich temporäre selbst erzeugte Zwei-Zeilen-NPZs und löschen sie anschließend; null reale NPZs, keine pytest-/Modellprozesse. Sie prüfen u.a. Zuordnung36/38/37/39, unbekannte Treffer, doppelte Suchzeilen, Vorzeichen-Nullbytes, Masken/Ties, getrennte Arme, Streaming/Dtype und zwingenden Abbruch bei terminaler Bankprovenienz.
