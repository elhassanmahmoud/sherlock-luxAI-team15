# Verbindliche alte Kontrollreferenz für Ensemble-Verhalten

**Genau zwei akzeptierte Kontroll-Technikfälle identifiziert.** Ausschließlich gezielte JSON-Belege und Originalquellen gelesen; 15 kleine JSON-Dateien über ihre versiegelten Hashketten gebunden. Keine Tensor-/NPZ-Archive geöffnet, alten Trainingszeilen erneut geprüft oder Reproduktion ausgeführt. Die maschinenlesbare Referenz enthält alle exakten verschachtelten Vergleichswerte und Dateien: `/private/tmp/ensemble-behavior-golden-reference.json`.

## Fälle, Reihenfolge und Initialisierung

| Fall | Fester Key gegen Solution | Envschritte vorher → nachher | Lernupdates | Matchresultat | Punkte | Replayübergänge |
|---|---|---:|---:|---:|---:|---:|
| 0 | 9946007 / player_0 | 60000 → 60303 | 0 | 3:0, Sieg | 785:304 | 3489 |
| 1 | 831006 / player_1 | 60303 → 60606 | 0 | 1:2, Niederlage | 1252:1037 | 3421 |

Beide jeweils 303 Schritte, Punktzählung v2, `loss=null`, tatsächliches epsilon `0.050000000000000044`. Insbesondere gewinnt Fall 1 trotz höherer Gesamtpunktzahl nicht das Spiel. Die ursprünglichen `masked_final_actions` sind **16 und 65**, keine geforderte Null: Diese Diagnose zählt finale Regeln gegenüber der vorherigen Q-Maske und ist nicht mit einem abgefangenen Agentenfehler gleichzusetzen.

Originalchronologie aus `match_weight_study.run_worker`: Threads begrenzen; Originalmitglied 18 laden; **eine Env vor make_learner konstruieren**; frischen Kontrollagenten für Start 48 einmal erzeugen. Beide Fälle danach auf derselben Env und demselben Agenten in obiger Reihenfolge spielen. Agent, Replay, Zähler und privater RNG bleiben zwischen den beiden Fällen erhalten. Nicht pro Fall neu initialisieren. Ursprünglich wurde erst für den zweiten Arm MATCH20 ein neuer Agent auf derselben Env erzeugt; später entsprechend ein neuer ON-Agent für seine zwei Fälle.

`make_learner` ruft `seed_everything(start)` auf: Python `random.seed`, globales `np.random.seed`, `torch.manual_seed`. Agent-RNG ist separat `np.random.default_rng(start)`. Pro Spiel erzeugt `play_one` zuerst den Gegner. `play_game` ruft `new_game` auf, setzt Python/NumPy global auf den Spielseed, dann `env.reset(seed=seed)` und Envkonfiguration; je Schritt Handlung vor Update. `new_game` setzt Belief/Episodenstatus zurück, **nicht** Replay, q/Target/Adam, Zähler oder agent.rng. Kein manuelles zusätzliches Reseeding.

Für Start 49 ist nur die Initialprüfung ohne Spiel vorgesehen: gleiche ursprüngliche Gewichte, vollständige Kontrollconfig und frischer leerer Adam, aber eigener Startseed **49**. Keine Forderung, dass dessen privater RNG mit Start 48 identisch sei. Installation des Adapters muss die jeweils frisch rekonstruierte Basis-RNG-Rezeptur erhalten; historische RNG-Snapshots existieren nicht.

## Exakte OFF-Gleichheit

Die unveränderte Funktion `paired_row` vergleicht exakt diese zehn Felder, einschließlich aller verschachtelten Werte:

`key`, `native_sha256`, `trajectory_sha256`, `reward_audit`, `final_action_audit`, `our_wins`, `opp_wins`, `our_points`, `opp_points`, `result`.

Zusätzlich fachlich prüfen: `before`, `env_steps`, `learn_steps`, `initial`, `current`, epsilon, 303/v2, `loss=null`, konsistente `game_win`/`point_win`, Nulllernen und tatsächliche eigene Replay-/Kontrollrewardlabels. `reward_audit` umfasst unter anderem UID-/Nichtreward- und Gegenformeldigest, Übergangszahl und 303 Updates; `final_action_audit` enthält 303 Handlungs-/Updateaufrufe und den finalen Labeltranskript-Digest. Alle exakten Werte stehen im JSON; keine neue Toleranz für Digest-/Integergleichheit einführen.

Der native Digest bindet eingereichte Aktionen **beider Spieler**. Der Trajektoriendigest bindet pro Schritt `(obs, actions, next_obs, reward, terminated, truncated)`, nicht sämtliche Engine-Interna, Reset-info oder Step-info. Rohbeobachtungen wurden nicht archiviert; diese Hashes ermöglichen Vergleich, keine unabhängige Wiedergewinnung alter Beobachtungen.

**Nicht als Gleichheitsgate verwenden:** `secs`, Wallclock-/Guard-/Usage-/Powerdaten, PIDs/PGIDs, neuer HEAD, Admission, Profil, Ausgabepfade oder ganze JSON-/Archivcontainerbytes. Eigene Artefakte bekommen neue Bytehashbindungen; Rewardarray-Inhalte sind über die alten semantischen Arrayhashes und ursprüngliche Kontrollformel vergleichbar, ihre Pfade sind neu.

**Besondere Falle:** Die globale alte Receipt `final_replay_sha256=3b981f62945c66697317edab98b16a98a8dce292dbe89554d9046432fe795457` gehört zum zuletzt ausgeführten **MATCH20-Arm**, nicht zu Kontrolle. Nicht mit dem neuen OFF-Replay vergleichen. Die globale finale q/Target/Adam-Identität ist wegen Nullupdates zwar gemeinsam, beweist aber keine Gleichheit der Kontrollrewards. Maßgeblich sind die beiden alten Kontrollzeilen und ihre Kontroll-Rewardarraybelege. ON muss diese Trajektorien ausdrücklich nicht reproduzieren.

## Dateien und Bindung

Basisverzeichnis: `experiments/analysis/match_weight_20261109/` im angegebenen Checkout.

- `operations/training-completion.json`: `41cb8fa0689bb1a5b98bbd692e147fceb8471b5e72387b661b06e7484c244b94`; bindet beide Kontrollabschlüsse und Receipts. Diese Gesamtabnahme wiederverwenden.
- `technical_v2/technical/receipt.json`: `3e4de943b8dd74d1a674d6effeb18931bdcb87ebed57d08d523312f0b2ff285b`; erste zwei `games` sind Kontrolle, danach MATCH20.
- `operations/technical-v2-acceptance.json`: `97d30ecbd546871da07e1c43f2cfc7046ff54c64f8b9a6b62859a0fc3354d92d`; echte frühere Technikannahme.
- `technical_v2/technical/control-initial.json` und `pair48_v2/control/control-initial.json`: beide `a0657d10d13375aebb6797c6f203bd1b8ead937e962036363102e3406090b837`.
- `pair49_v2/control/control-initial.json`: `3ebb0f02dcd61d1ddd86bc8001eaad939f443c0927c75592f91c02953c569a39`.

Initial-q und Target sind bei beiden Starts `43e2c214143f4354aaaa9b8db945941f2d6b8d04f09d9792d4eec6e3d17c45b6`, leerer Adam `e792320c12ea2f52219d0b177d630df0bfe99e53787969098c6fb67510a1012e`. Vollständige Kontrollconfig ist in allen drei Initialbelegen gleich, einschließlich w_match=2, lr=5e-5 und Trainingsregeln. Initialidentitäten und Config stimmen mit den jeweiligen gebundenen Vorlaufbelegen überein. Das sind gelesene, historisch akzeptierte JSON-Identitäten; keine heute erneut geladenen Tensoren.

Die historische Quelle ist `207f504cf75920e4569ef3084b6cd916df76243c`. **Alle 406 alten Source-Dateibindungen** aus der versiegelten Gesamtabnahme, Interpreterbinary, pyvenv.cfg und Enginequellen müssen bei realer Neuaufnahme unverändert sein; neue Dateien/HEAD sind gesondert zulässig. Hier kein neuer breiter Runtimeaudit. Vollständige alte Torch-/NumPy-/JAX-Binärstände und RNG-Snapshots fehlen weiterhin. Gleicher Venvpfad oder zwei bekannte OFF-Reproduktionen beweisen keine vollständige historische Bibliotheksidentität.

JSON-Referenz SHA256: `6a9629d4997865b91e817f3044f1a8aade80d04895c5cd296219eb390a991239`. Keine Code-/Repoänderung, Tests, Modellladungen, Spiele oder Freigabe.
