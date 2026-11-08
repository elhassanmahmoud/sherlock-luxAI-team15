# Task1/2 – externe Textvorbereitung, ungeprüfte Implementierung

08.11.2026. Grundlage: `/tmp/sampled-target-PREPARATION_APPROVAL.md` und die korrigierten Spec-/Planentwürfe. Ausschließlich zwei neue Quelldateien unter `/tmp/sampled-target-staging/` vorbereitet; kein Studienrunner, Supervisor, neuer Seed oder Repositoryeingriff.

- `scripts/sampled_target_agent.py` (573 Zeilen): enge `SampledTargetAgent`-/`SuccessorReplay`-Unterklassen. Die native `_act`-Kette bleibt geerbt; `_act_est` und `_update` umschließen jeweils genau einen Parent-Aufruf. Keine Kopie der Reward-/Updatekette. Lokaler Learner mit gemeinsamen DDQN-/Sampled-Targetformeln und deskriptiver Telemetrie.
- `tests/test_sampled_target_agent.py` (473 Zeilen): zuerst geschrieben, danach Implementierung und gezielte Ergänzungen. Synthetische Prüfungen für bestätigte Befehle, gemischte Terminalbatches, Core-Grenzen/Respawn-Limit, No-op ohne frischen Cache, nativen/kanonischen Abgleich, SAP außerhalb Netzmaske, Zählerzeitpunkt, echten Parent-Updatepfad, Ring-/Save-/Load-Verträge und numerische Control-Parität vorgesehen.

Die Replayfreigabe ist für beide Modi gleich: nach Bindung im Folge-act erst am Beginn seines bestätigenden update; terminale neue Batches nach Parent-update. Nichtterminale Labels bleiben verpflichtend. Die Erweiterung beurteilt weder biologische Lebensidentität noch Enginewirkung. Laufzeitereignisse für spätere gestreamte Provenienz werden über einen optionalen `event_sink` bereitgestellt; der Logwriter gehört erst zu Task3.

Die engen Funktionen `save_pilot_bundle(agent, directory, metadata)` und `load_pilot_bundle(agent, directory, expected)` sind ebenfalls vorbereitet. `expected` verlangt `arm`, `bootstrap_mode` und **extern gebundenes `state_sha256`**; der State bindet Gewichts-/Bufferhashes, ohne Selbsthash-Zirkel. Direkte spätere Legacy-Loads sind gesperrt. Reload ist nur Artefaktinspektion, kein Resume; RNG-Fingerprints werden dokumentiert, aber keine Fortsetzung des historischen RNG-Zustands zugesichert. Die ursprüngliche V14-Initialisierung bleibt beim geerbten Konstruktor-Loader und braucht weiterhin den separaten Task3-Initialaudit.

## Tatsächlich geprüft und noch offen

Nur lesende Quellen-/Textprüfung, Dateigrößen und SHA-256 erfasst. **Null Python-Aufrufe, Imports, NumPy-/Torch-Ausführungen, Syntaxkompilierungen, pytest-Aufrufe, Forward-Pässe, Modelle oder Spiele. Sämtliche Tests sind UNRUN; weder RED noch GREEN wurde beobachtet. Keine Funktions- oder Integrationsbehauptung.**

Offen: unabhängiger statischer Review; danach erst bei gesonderter Root-Zulassung nach Ende des Leistungsfreeze Syntax-/Importprüfung und tatsächliche synthetische Testausführung, einschließlich möglicher Fixture-/Schnittstellenkorrekturen. Bundle-Reload, Control-Parität, Speicherverbrauch und tatsächliche Core-Lifecycle-Verträglichkeit sind nicht zur Laufzeit verifiziert. Task3/4, Studienaufnahme, frische Bindungen und Training bleiben außerhalb dieser Vorbereitung.

## Eingefrorene Fassung für den statischen Review

- `scripts/sampled_target_agent.py`: `fd0e94a695f4e06b4fedfe43c27d37e91b31a97e9b2458405958fd9427217391`
- `tests/test_sampled_target_agent.py`: `52014754a8f3ab50566c26af7502ffc6ae18dbcebe03b56065b150a7c6133f89`

Diese Dateien werden bis zur Rückmeldung nicht weiter verändert.
