# Sampled-Target-Pilot – Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Nach Root-Methodenprüfung `superpowers:subagent-driven-development` oder `superpowers:executing-plans` verwenden. Checkboxen beschreiben die Prüfanforderungen; tatsächliche Ausführung siehe Status unten.

**Goal:** Einen isolierten40+160-Paarvergleich des bestehenden Double-DQN-Targets gegen tatsächliche Folgeaktionslabels vorbereiten, ohne produktiven V14-Core zu verändern.

**Architecture:** Experimentlokale Agent-/Replay-Unterklasse. Unveränderte Parent-Aktions-/Reward-/Updatekette; lokale Übernahme nur der kurzen `_learn`-Methode. Ein enges Studienwerkzeug und Supervisoradapter nutzen bestehende Freeze-/Prozess-/Vergleichshilfen.

**Tech Stack:** Bestehendes Python, NumPy, Torch und pytest; keine neue Abhängigkeit. Task1/2 sind im Studiencheckout installiert und synthetisch geprüft; Task3/4 und reale Läufe sind offen.

**Spec:** [Feste Methode](../specs/2026-11-08-sampled-target.md).

## Globale Grenzen

- Der Artillerie-Freeze ist nach historischer Abnahme aufgehoben. Neue Modellläufe erst nach integrierter technischer und methodischer Freigabe. „Freigabe“ ist Root-Methodenprüfung innerhalb vorhandener Autonomie, keine neue Nutzerfrage.
- Vier finale Einzelnetze, zwei feste Startpaare; je40 Vorlauf+160 Lernspiele,24.000 Updates. Insgesamt800 Ausführungen plus400 feste Leistungsspiele, keine Zwischenvalidierung; zusätzlich genau vier separat gezählte technische Integrationsspiele auf bekannter Karte4242 vor Studienstart. Kein Ensemble oder Nachschlag.
- Gleiche verzögerte Replayfreigabe in beiden Armen; genau ein echtes act je Env-Schritt. Label ist der bestätigte an env.step übergebene Befehl, keine garantierte Enginewirkung. Bindung ausschließlich innerhalb Core-definierter Unit-Episoden; keine neue Survivalheuristik. Fehlende Folgeaktionslabels sind Fehler, kein Masken-/Argmaxfallback.
- Maximal zwei Modellworker, Threads1; keine parallelen Tests. Startpaare nacheinander, je Paar Vorlaufgate vor Gradienten.
- Keine Änderungen an `agents/sherlock/*`, bestehenden Studien oder Abgabegewichten/ZIP. Sechs exakte Kohorten und Starts45/46 sind vor neuen Daten in der Spec festgelegt. Frischeaudit und tatsächliche Inputbindung bleiben vor dem Studienstart erforderlich.

## Reviewfokus

1. `act` ohne erfolgreiches folgendes env.step/update: kein Commit und kein speicherbarer Schein-Nachfolger → Task1.
2. Gemischte Batches und vom Core erkannte Terminal-/Matchgrenzen: genaue Bindung/Originalreihenfolge; nicht erkannte Respawns bleiben geerbte Einschränkung. No-op ohne frischen Cache muss leer schließen → Task1.
3. Finale Fog-SAP-Klasse außerhalb Netzmaske sowie native Spiegelung/SAP-Fallback: echte Klasse erhalten, widersprüchliche Ausgabe stoppen → Task1/2.
4. Alter oder partieller Buffer / getrennte falsche Gewichtsdatei: vor Mutation ablehnen, niemals Labels migrieren → Task2.
5. Bestehender Aktionsaudit erwartet sofortige Writes; alte Helper für Initialisierung haben abweichende Lernraten/Gates: nur passende primitives wiederverwenden, neue Bedingungen selbst prüfen → Task3.

## Geplanter Dateiumfang

- `scripts/sampled_target_agent.py`: `SuccessorReplay`, `SampledTargetAgent`, lokale Capture-/Commit-Audits, versionierte Replay-Persistenz; ein fokussiertes Modul, kein allgemeiner Hookbaukasten.
- `scripts/sampled_target_study.py`: feste Rezeptur, lokale kanonische `PilotLearners`, prepare/worker/prefill-/finale Prüfungen, Endmodellzulassung und400-Spiel-Plan/Auswertung. Bestehenden Play-Loop und Modellarchitektur importieren.
- `scripts/sampled_target_supervisor.py`: schmaler Adapter für vorhandene Source-/Quota-/OwnedProcess-Hilfen, genau zwei Starts und zwei Rollen; keine Änderung historischer Supervisoren.
- `tests/test_sampled_target_agent.py`, `tests/test_sampled_target_study.py`: nachstehende gezielte Prüfungen.
- Erst nach Root-Entscheidung: akzeptierte Spec/Plan im Repo und projekttypischer Abschlussvermerk. Diese Entwürfe sind keine Aufforderung, die laufenden Projektdateien jetzt zu ändern.

## Task1 – Korrekte Folgeaktionsbindung ohne Core-Duplikation

**Interfaces:** `SampledTargetAgent(..., bootstrap_mode='double_dqn')`; `bind_episode(meta: dict) -> None`; `assert_boundary() -> None`. `SuccessorReplay(capacity,obs_dim)` mit `begin_capture(source_rows,meta)`, dem originalkompatiblen `push(s,a,r,ns,done,next_mask)`, `finish_capture(next_context: dict | None)` (`None` bei leerer Capture), `attach_successor(frame)` und `commit_confirmed(action,frame_key)`. Meta/Frame sind lokale feste Datensätze mit den Specfeldern, keine frei erweiterbare Plattform.

- [ ] Tests `test_submitted_successor_commits_only_after_update`, `test_one_parent_act_and_update`, `test_mixed_batch_preserves_uid_order`: synthetische Mehr-Unit-Schrittfolgen; vor bestätigendem update bleibt size unverändert; danach jede ursprüngliche Zeile genau einmal und in Reihenfolge; keine zusätzliche act-/decide-Ausführung/RNG-Ziehung. `test_submitted_command_kept_without_engine_effect`: erfolgreiches env.step/update mit unverändertem Zustand darf den eingereichten Befehl als Label behalten; keine behauptete Wirkung prüfen.
- [ ] Tests `test_terminal_successor_action_still_labels_previous`, `test_core_detected_terminal_and_match_reset_do_not_link`, `test_core_unrecognized_adjacent_respawn_keeps_core_done`, `test_missing_or_repeated_successor_aborts`, `test_reset_with_pending_aborts`: Szenarien und Terminal-Sentinels exakt nach unverändertem Core; keine zusätzliche Todes-/Energieheuristik, kein Drop oder Ersatzlabel. Der Respawn-Gegenfall dokumentiert ausdrücklich die Begrenzung statt Lebensidentität zu behaupten. Vor Implementierung als gezielte Fehler nachweisen.
- [ ] Tests `test_noop_closes_empty_capture_without_fresh_cache` und `test_empty_uid_capture_needs_no_context`: Matchstep0 mit `_prev_ctx=None`, fehlendem oder veraltetem `_cache`; vollständiges act/update-Paar und null Übergänge, `finish_capture(None)`, kein Cachezugriff als Nachfolger und kein zusätzliches `_decide`. Ein nichtterminaler Pendingübergang ohne tatsächlichen Nachfolger bleibt dagegen ein Fehler.
- [ ] Unterklasse mit Lifecyclefeldern vor `super().__init__` initialisieren; den einmalig geladenen Base-Agent und seine Module behalten, leeren Basisbuffer vor Allokation des Zusatzbuffers freigeben. `_act_est`/`_update` umschließen; `_act`, `_decide`, Reward und Parent-Updatebody nicht kopieren.
- [ ] Neues `push` prüft Source-Reihenfolge gegen die vorher gesicherten `_prev_feats/_prev_actions` und puffert Kopien. Parent darf nur fertigen Ring samplen. Der vorherige Batch wird am Beginn des bestätigenden update committet; vollständig terminaler neuer Batch erst nach Parent-update. `next_action_env_steps` beim Eintritt in Folge-`_act_est` sichern und unverändert übernehmen, bevor der bestätigende Parent-update inkrementiert. `test_successor_counter_is_pre_update_value`: vor act/Parent-update60001, im bestätigenden Lernupdate60002 und Labelalter1; zweiter Fall vor act60002, kein Lernen bei60003, nächster Lernupdate60004 und Alter2. Gespeicherter Zeitstempel bleibt jeweils60001/60002; obs.steps und learn_steps nicht als Ersatz verwenden.
- [ ] Native Aktions-/UID-Prüfung aus dem bisherigen action_audit in den lokalen Lifecycle integrieren, dessen unmittelbare pos+=Anzahl-Annahme ersetzen. Tests `test_canonical_mirror_and_sap_target`, `test_sap_without_target_mismatch_aborts`, `test_actual_action_outside_mask_kept`, `test_update_action_differs_aborts`. Match-/Game-/Schritt-/Feature-/Maskenabweichung muss vor Commit scheitern.
- [ ] Nur die Task1-Tests ausführen; erwartetes Ergebnis alle PASS. Unabhängig prüfen, dass keine Core-Aktions-/Updatekopie oder globaler Monkeypatch entstanden ist.

## Task2 – Gemeinsamer Lerner und strikte Persistenz

**Interfaces:** `SuccessorReplay.sample_with_successor(batch_size,rng)` liefert dieselben sechs Basisarrays plus Folgeaktion/Metadaten aus **einem** Indexzug; `save(path)`/`load(path)` implementieren Schema1. `SampledTargetAgent._learn()` verwendet Modus und prüft Integrität; `save_pilot_bundle(directory,metadata)`/`load_pilot_bundle(directory,expected)` im Studienmodul binden Gewichte/Replay/State gemeinsam.

- [ ] Formeltests mit kleinen festen Arrays/Tensornetzen: Kontrolle entspricht maskiertem DDQN, Sampled folgt gespeicherter Klasse, terminales Target=r, unzulässige Labels abort, außerhalb-Maske-Folgeaktion wird direkt gathered. Kein sentinel−1-Indexzug; gleiche Labels ergeben numerisch gleiche Targets/Parameterupdates beider Modi.
- [ ] Die aktuelle36-Zeilen-`_learn`-Logik lokal übernehmen; nur Auswahl des Next-Index bedingt ändern. Kontrollpfad gegen produktiven `_learn` mit identischen **bereits committeten** Batches/RNG vergleichen: Parameter/Adam/Target/learn_steps/Loss und RNG nach einem Update sowie an Target-Sync-Grenze gleich. Mit echter Replayfreigabe ist keine Gleichheit zum historischen sofortigen Puffer zu behaupten.
- [ ] Telemetrie beider Formeln innerhalb eines Updates aus demselben Batch und denselben Online-/Targetausgaben, ohne zusätzlichen Samplingzug. Nach unterschiedlichen Gradienten keine Gleichheit der Puffer/Transitionen zwischen Armen voraussetzen. Labelalter=`env_steps` beim Lernen minus gespeicherten Folge-act-Zähler, nur nichtterminal; Test des Zeitbezugs aus Task1 übernehmen. Nur deskriptive Index-/Targetdifferenz und Maskenmitgliedschaft, kein rekonstruierter Regelgrund. Nichtendliche Q/Targets/Verluste/Gradienten führen zum Fehler.
- [ ] Tests `test_ring_wrap_keeps_all_columns_aligned`, `test_save_load_chronological_schema`, `test_pending_save_rejected`, `test_legacy_or_partial_buffer_rejected_before_mutation`, `test_bundle_wrong_mode_hash_arm_rejected`. Alte sechs-Array-Puffer nicht importieren. Load ausschließlich in leeren Zustand; logische Chronologie statt Gleichheit alter physischer Ringslots prüfen.
- [ ] Gewichte mit Base-Saveformat erhalten, Mode/Schemazustand in verpflichtendem `pilot_state.json`; State bindet Gewichts-/Bufferhash, Abschlussreceipt bindet auch den Statehash. Kein Selbsthash-Zirkel. Bundle nur an sauberer Spielgrenze schreiben und nach vollständiger Reloadprüfung als fertig markieren. Kein Studien-Resume implementieren.
- [ ] Task1/2-Tests gemeinsam ausführen; alle PASS und numerische Control-Parität unabhängig prüfen. Coredateien müssen weiterhin unverändert sein. Diese kleine bewusste Learnerduplikation ist erlaubt; Bedarf an `_act`-/`_update`-Duplikation an Root zurückgeben, nicht ausweiten.

## Task3 – Feste Paarstudie, Machbarkeitsgate und Belege

**Interfaces:** `prepare(source,out,seed_bindings) -> manifest`; `run_arm(prepared,arm,name,supervisor_state) -> receipt`; `validate_prefill_pair(control,sampled) -> gate`; `validate_final_receipt(path) -> dict`. `PilotLearners` bietet `.agents`, `.paths`, `.unique()` und geerbte kanonische Methoden, konstruiert aber direkt die lokale Agentklasse ohne Änderung der globalen Variantenfactory.

- [ ] Reine synthetische Plantests: vier Rollen, exakt40+160 pro Arm, Paarfolgen identisch, beide Seiten je Karte, getrennte Vorlauf/Train/Panel/Direktbereiche, kein unbekannter/zusätzlicher Seed, kein fertig vorbereiteter Plan ohne geprüfte Seedbindung. Konfiguration genau der Spec, Mode nur im separaten Pilotmanifest.
- [ ] Initialisierung und Rezeptur nach vorhandener artillery/fog-Vorbereitung übernehmen: Komponente18, lr5e-5, autosave_on_terminate=False, fresh Adam, env_steps60000, target=q, empty replay, kein Ensemble. Nur passende Hash-/State-/Freeze-Funktionen wiederverwenden; ältere `_prove_initial` mit lr1e-4 und alter Action-Audit sind keine passenden unveränderten Validatoren.
- [ ] `common.play_game` unverändert benutzen; vor Aufruf episode_id setzen, nach Aufruf `assert_boundary` und Übergangszähler prüfen. Den vollständigen, gestreamten provenance.jsonl.gz-Vertrag der Spec umsetzen; Initial-/Prefill-/Endbelege enthalten Zusatzschema, Mode, vollständige Pending-/Commit-Zähler und Original-zu-Folgeaktion-Provenienz. Training darf ausschließlich nach passendem Paarreceipt fortfahren.
- [ ] Nach40 Vorlaufspielen deterministisch alle fertigen Zeilen in256er-Blöcken read-only auf beiden Targetformeln prüfen; keine RNG/Optimizeränderung. Paargate: komplette identische Prefills, unveränderte Startzustände, keine Missinglabels sowie mindestens ein Index- und ein Wertunterschied. Gatefehler beendet den Pilot; keine Schwellen-/Kartennachwahl.
- [ ] Synthetische Gate-/Receipt-Tests: fehlende/doppelte Übergänge, nichtleerer Pendingzustand, ungleiche Prefills, Nullintervention, veränderte Quellen/Gewichte, fehlende Updates, zusätzliche Spiele oder unvollständige160-Lernspielserie werden abgewiesen. Genau24.000 Updates pro Arm und insgesamt60000+200*303 Env-Schritte nachweisen; Match-Noops erklären303 statt300.
- [ ] Supervisoradapter führt ein Startpaar mit zwei Workern durch Vorlauf/Gate/Training, danach das zweite. Gleiche bestehende Strom-/Kontingent-/Fremdprozess-/Freezeprüfungen; signalbedingter Stop an Spielgrenze, bei Crash unvollständiges Receipt. Kein automatischer Restart. Tests verwenden Fake-Prozesse/Dateien, keine Spiele.
- [ ] Alle gezielten Task3-Tests sowie vorhandene tatsächlich berührte Helperprüfungen ausführen, unabhängig statisch abnehmen. Noch keine Modelle/Spiele starten, bevor Root integrierte technische und methodische Freigabe erteilt.

## Task4 – Exakte400-Spiel-Prüfung und Abschluss

**Interfaces:** `performance_plan(prepared,final_receipts,seed_bindings) -> jobs`; `validate_performance(jobs,rows) -> report` im Studienmodul. Vorhandene `par_eval`-Worker/CSV-Prüfungen verwenden, mit ausschließlich vier finalen Einzelnetzen. Pro Netz eine Inferenzkopie mit identischen Tensoren und derselben gebundenen V14-Config (`frozen=False` als einzige Änderung zur Quellconfig); sowohl `--weights` als auch gegnerische `self:`-Pfade verwenden diese Kopien. `--set` allein würde nur eine Direktduellseite verändern und ist hier kein zulässiger Ersatz.

- [ ] Synthetischer Plantest:8 Paneljobs×40 Spiele +2 Direktjobs×40=400; vollständige `(role,opponent,seed,side)`-Schlüssel, kein V14/Ensemble/zusätzlicher Kandidat. Panelkarten für alle Rollen/Gegner gleich, Direktkarten getrennt. Replaymodus wird nicht zur Inferenz benötigt.
- [ ] Inferenzkopien mit erhaltenen Trainingscheckpoints erstellen und sämtliche Tensorhashes gegen den jeweiligen Finalstand prüfen; nur Config-Metadaten wie oben ersetzen. `test_direct_both_sides_load_same_bound_inference_config`: Agent über `--weights` und Gegner über `make_opponent('self',...)` laden, beide tatsächlich erhaltenen Configs müssen exakt gleich dem gebundenen Inferenzconfig sein. Falschen self:-Pfad zum Trainingscheckpoint ablehnen. Keine neuen Parameter, Zwischenversionen oder Spiele für diese Ladeprüfung.
- [ ] Synthetische Ergebnistests für beide strikt positive Paneldeltas, Mittel>=.05, beide direkte Scores>=.5 und gemeinsamer Score>.5; Remis=.5. Unvollständige, doppelte oder unbekannte CSV-Zeilen ablehnen. Alle Werte je Start/ganzer Karte berichten; keine Interpretation kleinerem Loss als bessere Stärke.
- [ ] Nach abgeschlossenen Tests unabhängiger Methoden-/Codeaudit gegen Spec und unveränderten Core. Danach erst Root-Entscheidung: tatsächlicher negativer Artillerieabschluss, freie Rechenplätze, Seed-Audit/Reservierung, vollständige Inputhashes und neuer Freeze. Ohne diese Bindungen bleibt der Entwurf nicht startbar.
- [ ] Nach einer eventuell später autorisierten Ausführung: unabhängiger Enddaten-/Auswertungsaudit, Abschluss mit allen Negativ-/Nullresultaten; keine Übernahme-/Nachschlagsautomatik. Erst dann Arbeitsstand/Experimentprotokoll und tatsächliche Prüfungen dokumentieren.

## Entwurfsprüfung und Übergabe

Specanforderungen sind Tasks1–4 zugeordnet: Core-definierte Episode/eingereichter Folgebefehl/No-op/Zählerzeitpunkt→1; Targets/alte Puffer/Save/Load→2; Paarvergleich/Freigabe/Reset-/Commitnachweis→3; identische Inferenzconfig beider Duellseiten/400-Spiele-Gates und Datenlimits→4. Präzisierungen aus dem unabhängigen Entwurfsreview eingearbeitet; keine neue Survivaländerung oder Hypothese. Dieser historische Entwurfsreview führte keine Tests aus; der aktuelle tatsächliche Root-Testnachweis folgt im Statusabschnitt. Numerische Starts/Kohorten sind jetzt in der Spec festgelegt; ihre Frische und tatsächlichen Datei-/Quellenhashes müssen noch vor dem Start gebunden werden.

## Tatsächlicher Stand und enger technischer Zusatz (08.11.)

Task1/2: Agent-/Replaymodul nach unabhängigem statischem Fixreview installiert; Root hat `python -B -m pytest -q tests/test_sampled_target_agent.py` tatsächlich ausgeführt:53 PASS in2,71 Sekunden. Keine produktive Coredatei oder Abgabe geändert. Noch keine echten Spielausführungen/Trainingsupdates dieses Piloten. Frühere externe Textberichte mit UNRUN bleiben historische Belege vor dieser Ausführung.

Task3 erhält vor der Frischstudie den in der Spec exakt festgelegten Vier-Spiel-Integrationsschritt: beide Modi×beide Seiten, bekannte Karte4242, default, keine Gradienten. Ein lokaler `technical`-Einstieg verwendet dieselbe Initialisierung/Spielschleife/Eventprotokollierung wie der echte Worker. Prüft identische Vorläufe pro Seite, Nullupdates und geschlossene Captures; keine Leistungsentscheidung. 4 technische+800 Lern/Vorlauf+400 Leistungsausführungen getrennt berichten. Technischer Fehler stoppt die Aufnahme vor frischen Karten; keine automatische Wiederholung.

Task3/4 bleiben in Umsetzung zu vergeben. Der aktuelle Text ist eine feste Methode mit noch offenen Aufnahmebedingungen; keine erfolgreiche reale Laufzeit oder Trainingsfreigabe behaupten.
