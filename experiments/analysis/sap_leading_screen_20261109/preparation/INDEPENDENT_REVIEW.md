# Unabhängiger statischer Review: SAP-Vorhalte-Screen

**Ergebnis: PASS im statischen Prüfungsumfang; keine blockierenden Findings.** Datum: 09.11.2026. Reviewer: `sampled_admission_review`. Kein Modell-/Spielstart, kein eigener Testlauf, keine Repositoryänderung durch diesen Review. Der tatsächliche Vier-Spiel-Integrationsnachweis und sämtliche 120 Leistungsdaten bleiben offen. Dieser Bericht ist keine Start-, Stärke- oder Übernahmefreigabe.

## Gegenstand und genaue Versionen

Worker (alle 469 Zeilen), vollständige Testdatei, README und ergänzender Launcher (alle 87 Zeilen) wurden gelesen. Maßstab waren der ursprüngliche Entwurf, der inzwischen konkretisierte Repo-Plan, der aufgenommene Prototyp und die tatsächlich aufgerufenen Core-/Historik-/Prozesshelfer. Beobachteter Repo-HEAD: `2ddf64b33b12744619fa6e57188b7f2c45ecc8c5`; die neue Aufnahme war während dieses Reviews noch uncommitted. Keine Behauptung eines damaligen unveränderlichen Gesamt-Checkouts.

| Gegenstand | SHA-256 |
|---|---|
| `/tmp/sap-leading-screen/scripts/sap_leading_eval.py` | `e434dfcd81a159e3f0921c9c11011768fdb3910e4aaf79f5f58eeb071059226d` |
| `/tmp/sap-leading-screen/tests/test_sap_leading_screen.py` | `d365cc0846ce24857a63905427d8b8cdbb4fdad64c38fc93fd71a182796a15b3` |
| `/tmp/sap-leading-screen/run_owned.py` | `0565b53366ad907b642846f6594a56a94f9cd772c5a455ba36f58b20d835d529` |
| `/tmp/sap-leading-screen/README.md`, einschließlich Launcherergänzung | `e3c9b50355aaa3c9424dbeaa34619986e2d13c41c32165b5e88a732b8c68bd10` |
| `/tmp/sap-leading-screen-plan.md` | `4e127072161d05ffe14e26c45737306d7c336a212521bd8c89fba4654d4aa08f` |
| `docs/superpowers/plans/2026-11-09-sap-leading-screen.md` | `a1fd1a824d7ccc4c07aacc99df780526561dd88ee2bf0831606e90cabd02a38a` |
| `scripts/sap_leading_agent.py` | `3b4b779f25f32af9f523b69b169a68eea78b862ce89ede77a3138ef2db26c2eb` |

Die inzwischen installierten `scripts/sap_leading_eval.py`, `tests/test_sap_leading_screen.py` und `scripts/sap_leading_owner.py` wurden abschließend gehasht: bytegleich zu den entsprechenden drei externen geprüften Dateien. Beim tatsächlichen Aufnahmedokument ist der installierte Launcherpfad zu binden; dessen `__file__`-Prüfung akzeptiert keinen bloßen alten `/tmp`-Pin.

## Fachlicher und technischer Abgleich

- **Rollen und Ladeweg:** Beide Rollen sowie der direkte OFF-Gegner verwenden `make_agent`, denselben fest gepinnten V14-Checkpoint, `build_cfg(..., ['frozen=false'])` und dieselbe vollständige Config. Die tatsächliche Instanz wird auf Eval/Epsilon 0, Lernen/Autosave aus, 35 Zusatznetze plus Hauptnetz, 79 Merkmale/6 Aktionen und keine CNN-Erweiterung geprüft. Solution92 wird über den vorhandenen Klassenstatus-Reset geladen. `common.play_game(..., False)` ruft kein Update auf; `new_game` setzt Spieler/Belief/Estimator und die Lead-Zähler zurück. Der direkte Gegner läuft nicht über die implizite Self-Play-Config.
- **Historisches OFF:** Feste Reihenfolge OFF auf 831006/player_1 und 831000/player_0, dann ON auf denselben Schlüsseln. Beide Historikinputs werden vor der ersten Modellkonstruktion gebunden. Manifeststruktur, `native_actions`, 303 Frames, gemeinsame Aktionshashbytes und `matches={match_idx, points, cumulative_wins}` entsprechen dem echten `targeting_probe._play`-Produzenten. `RecordedEnv` benutzt dieselbe v2-Punkterekonstruktion und denselben Matchabschluss. Historische Config und aktueller gebundener Configbeleg unterscheiden sich ausschließlich durch sechs inzwischen hinzugekommene False-Defaults (`art_move_guard`, `art_splash_in_training`, `fog_unknown_reward_neutral`, `point_pair_swap`, `rescue_in_training`, `zone_rescue`). Das ist kein Ersatz für die noch ausstehende exakte OFF-Reproduktion; jeder spätere Aktions-/Punkte-/Matchunterschied bricht ab.
- **Hookintegration:** Der Wrapper ruft den originalen gebundenen `act` genau einmal; die Klassenhülle zählt genau einen eigenen originalen `_act` und lässt andere Instanzen direkt passieren. Der echte `_act_est`-Ablauf bleibt observe → Unterklassen-`_act` → remember. Die gebundene V14-Config aktiviert diesen Estimatorpfad. `ParamEstimator.remember` speichert eine Kopie der nativen Aktionen, einschließlich Matchreset; darauf passt `_prev['act']`. Der zusätzlich abgefragte `dropoff` liest lediglich den Posterior. Keine zusätzliche Entscheidung, kein weiterer Forward und kein zusätzlicher observe-/remember-Aufruf in der Hülle.
- **Öffentliche Auswahl und Buchhaltung:** Separate kopierte Vorgeschichte, aktueller öffentlicher Kontext/Sensor, kardinaler voriger Schritt, Energie-/Sicht-/Passierbarkeits-/Reichweitenbedingungen, sichere Parameterwahl und kleinste geeignete UID werden unabhängig vom Prototyp-`_candidate` rekonstruiert. Die Spiegelung benutzt den tatsächlichen `belief.mirrored`-Zustand und die inverse involutive Deltaabbildung; `remember` bleibt nativ. Bei Matchstep 0 wird kein alter Kontext verwendet, die eigene Auditvorgeschichte wird `None`. Der nach Core-Rückgabe gespeicherte Buchhaltungszustand wird mit dem Zustand nach originalem remember verglichen: nur gewählte Hitanzahl, passendes `sap_hits_est`-Delta und Entfernen dieser UID aus unknown sind erlaubt; andere Aktionen/Klassen und Pending-/Feature-/Maskenfelder bleiben gleich. Die neue Hitanzahl wird gegen alle sichtbaren Gegner im 3×3-Feld geprüft. Änderungen müssen den tatsächlichen eingereichten Befehlen und dem kumulativen Lead-Änderungszähler entsprechen. Andere Lead-Diagnosezähler werden erhalten; nicht jeder Ausschlusszähler wird hier separat numerisch rekonstruiert.
- **Technikabschluss und Messung:** Genau vier vollständige Technikzeilen, beide OFF-Reproduktionen und mindestens ein wirklicher ON-Eingriff sind erforderlich. Null Exposition führt zu keinem Ersatzspiel. Technik archiviert sämtliche Hookframes, Performance tatsächliche Änderungsframes. Frische Instanzen pro Spiel verhindern Übertrag von Episodenzustand. Fehler werden bei `frozen=False` weitergegeben; vollständige Laufabschlüsse verlangen 303 Frames, drei Resetframes, drei Matches und null abgefangene Fehler beider Agenten.
- **Matrix und Statistik:** Exakt drei Jobs mit je 40 eindeutigen Schlüsseln; Panel 9940000–9940019, Direkt 9940100–9940119, jeweils Seiten 0/1. Resultat folgt Matchsiegen; Unentschieden zählen halb. Die Gates sind exakt mindestens fünf exponierte ON-Panelkarten, ON-Solution-Score ≥ OFF und `2W+D >= 48` direkt. Der Bootstrap mittelt beide Seiten je Karte und resampelt ganze Karten; der Panelkontrast wird vorher gepaart. Bestehender Helfer: 5000 Ziehungen, `default_rng(0)`/PCG64, 2,5-/97,5-Perzentile. Die Intervalle werden nicht zu nachträglichen Gates. Ergebnis bleibt deskriptiv, `promotion=False`.
- **Bindung und Wiederholungsschutz:** Getrennte gehashte Root-Aufnahme pro Phase; reale Quelle/HEAD, Pläne, Interpreter/Engine, Config, Gewichte/ZIP und Inputs. Performance verlangt denselben technischen Quellen-/Configstand, vier erfolgreiche Technikbelege samt Rohdateien und eine begrenzte Seed-Abnahme samt Belegen. Exklusive Phasenverzeichnisse und globale Job-Startreservierungen, kein Resume/Overwrite. Abschlussreceipts binden alle Rohdateien. Analyse verlangt vollständig beendeten Owner-State, genaue drei Jobs/Exitcodes, tatsächliche Befehle/Receipthashes, genau 41 Rohdateien je Job und Übereinstimmung von Spielzeilen und Änderungsereignissen; einmalige Summaryausgabe.
- **Ressourcen und Launcher:** Nur eine ausdrücklich aufgenommene Phase; Technik ein Worker, Performance zwei Panelworker und anschließend Direkt allein. Bestehende gemeinsame Rechensperre und Prozessgruppenhelfer, exakte Eltern-/PID-/PGID-/Befehlsbindung einschließlich macOS-Launcherbehandlung. Erste Panel-Registrierung erfolgt vor Modellbeginn. Bestehender Fog-Guard prüft aktuelle tatsächliche Quota, AC, STOP, Quellen/Inputs und fremde Modell-/Testprozesse; vor jedem Spiel und Abschluss erzwungen, sonst spätestens nach zehn Sekunden beim nächsten Agentaufruf, STOP bei jedem Aufruf. Numerische Threads werden auf eins begrenzt. Parent prüft ebenfalls fortlaufend; Cleanup signalisiert nur registrierte eigene Gruppen. Kein Retry, keine Analyse-/Phasenverkettung und kein eigener Wachhalter.

## Tatsächliche Prüfevidenz und Grenzen

Gelesen wurden die vollständigen synthetischen Tests und ursprünglichen RED-Logs; `GREEN.log` enthält **37 passed in 2.13s**, SHA `483b1f9778476c61b674ee2f524d6dfac816c110c24878ec102e1b363411efd1`. Die Tests sperren QNet-Konstruktion und `torch.load`. Kein eigener Testlauf durch den Reviewer.

Root hat nach bytegleicher Aufnahme tatsächlich **37 Repo-Tests PASS in 2,38s** durchgeführt. Gelesener Beleg: `experiments/analysis/sap_leading_screen_20261109/preparation/ROOT_INTEGRATION.json`, SHA `b9d509e0fc62fc99a3052ee0691fa32a261b252add9c24da486d910bce4f85a7`. Dieser bindet die drei aktuellen Quellhashes und dokumentiert außerdem ausschließlich eine `compile()`-Syntaxprüfung des Launchers. Der Launcher wurde noch nicht ausgeführt; die 37 Tests sind kein Ausführungsnachweis für ihn.

Dieser Review bestand aus Lesen, Dateihashes und kleiner Standardbibliotheksauswertung der zwei historischen Manifestzeilen/Configdifferenzen sowie erster Trace-Schemazeilen. Keine Projekt-/Torchimporte, Modelle, Tensorloads, Forwards, Tests, Spiele oder vollständige Archivanalyse. Die echte Engine-/OS-/Ressourcenintegration, OFF-Passivität, tatsächliche ON-Exposition und Ergebnisdaten sind damit ausdrücklich nicht bewiesen. Fehlender Netzstrom bleibt eine reale Startbedingung; dieser Bericht ändert daran nichts. Aus einem später positiven Screen folgt nur ein separater Folgeentwurf.

## Geprüfte Anschlussquellen und Historikpins

Folgende Hashes fixieren die konkret herangezogenen Schnittstellen; keine Behauptung einer vollständigen unabhängigen Prüfung jeder Datei:

```text
108ea9cb072bbdba0987d91873a7001cedda420b965da96cd9e9090e7c1d33bc  agents/sherlock/main.py
c98eae7b8afba125bc7df3b2e8371b3c00a89ead149d3058a1dbc448affd8419  agents/sherlock/param_est.py
081ffbbfa6b50b8d01b1a2875250ec7c66aa8275a56bb44bc478808df099c9fa  agents/sherlock/geometry.py
3f1a17515a588145c145999fe60293553473414900a3b2b77076ed4c2223d7a1  scripts/common.py
f525506d5268600e00c180d2a1fc4c9cc6bfb02ff2d63c6dcc7a8da33bf58a61  scripts/par_eval.py
f22d4b6c44ddef0ef0f0cc04f358451c559328391328047a3a25d8bac87becee  scripts/targeting_probe.py
963ba7785483f1b707e589d3023011f1a869ef65cd4fc064d0b0b44df309aaa0  scripts/scoring.py
47b2884f11c2f8fbc4bb41742c39d3db74a7c010abadea3bf481f8917fb3e22a  scripts/league_gates.py
c43355f08fc71a07242e087ce67ec1d2aac2a7d0951fb1150754c60a642eea72  scripts/compare_report.py
0c045ccf8dc7b4e4e269b11e6a254aeb617121416702df55abdc9e6ace7aba06  scripts/fog_reward_supervisor.py
62a317f634da7db8f1945ccc8a7f69224d87de72751e074e9300144a35926252  scripts/early_curriculum_study.py
1b35745c175f5adca714e9762768c9ca81224a5ee456abad1dea64132e9fdb76  scripts/final_training_supervisor.py
2028d15f07ab292bfcef92209c341a782e445b3abc4bd46193d06708540b3c24  scripts/ensemble_diversity_supervisor.py
18ae1b9fac25854a9cc90adfc2b4b2044867a936a2ad4080e8867e9e439486db  scripts/ensemble_diversity_eval_supervisor.py
00b316de7233cbfdfd07f33751d49a9f1711a93db643aa3a5e6352c337170405  scripts/experiment.py
90324b008945da4a054a0559a108ee0023cf572d754b20af844160dfe4ebc435  experiments/analysis/continuation_20261102/targeting/manifest.json
f5b81f554ad4d52f70bcb3a04008a1463c3887594cfd6be246dfe2556de97d08  experiments/analysis/continuation_20261102/targeting/831006_player_1.jsonl.gz
2f03777deb7c9449dd7572389c4720191d22bdf4c10b5b2b275a1c177edb293b  experiments/analysis/continuation_20261102/targeting/831000_player_0.jsonl.gz
72ec8ea499661c6e7f37d95293aa82ea02da38bc4b48c39e92050fb55af0203e  experiments/runs/20261108_sampled_target_prepared/manifest.json
```
