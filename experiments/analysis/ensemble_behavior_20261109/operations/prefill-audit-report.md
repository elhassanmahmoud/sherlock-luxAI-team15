# Unabhängiger Vorlaufaudit: beide ursprünglichen ON-Worker

**PASS.** Beide tatsächlichen 40er-Vorläufe unter Quelle `71090f760788bdcec8d7158bc5aab4fd47d406cc` einmal unabhängig geprüft. Exit 0, stderr leer, **1.084 Checks, 494 Hashbindungen und 489 eindeutige gehashte Dateien**. Keine Projektimporte, Agent-/Modellkonstruktion, Forwards, Tests, Spiele, Quelländerungen oder Freigabe. Ausschließlich die zwei eigenen gespeicherten Vorlaufcheckpoints wurden nach bestätigter gemeinsamer Wartephase als CPU-Daten deserialisiert.

| Arm | Spiele | Tatsächliche Replayzeilen | Envschritte | Lernupdates | Nichtnull-Outcomes (+/−) |
|---|---:|---:|---:|---:|---:|
| on48 | 40 | 141.704 | 72.120 | 0 | 1772 (1519/253) |
| on49 | 40 | 141.514 | 72.120 | 0 | 1729 (1433/296) |

Beide ursprünglichen Worker **54962/54967**, mit Gruppen/Elternbindung an Owner **54950**, waren vor und nach Prüfung tatsächlich lebend und wartend. Owner running, beide aktiven Rollen und null offene Returncodes, `awaiting_root_release=true`, beide korrekten waiting-Marker und identische Readiness-/Vorlaufhashes; keine Release-Datei. Das beschreibt den Auditzeitpunkt, erteilt selbst keinen Release.

Die tatsächlichen 40 JSONL-Zeilen stimmen jeweils vollständig mit der gespeicherten Proof-Chronologie überein. Gesamten 440er-Plan je Start eigenständig mit PCG64/Seed48 beziehungsweise49 regeneriert; Vorlaufkeys exakt, vollständige 303/v2-Spiele, Zähler/Nullverluste, Match-/Punktresultate und originale Live-Auditbedingungen konsistent. Keine ON-/OFF- oder startübergreifende Trajektoriengleichheit verlangt.

**Tatsächliche Checkpoints:** q und Target endlich Float32, 79 Eingaben/6 Aktionen, q und Target direkt bitgleich; ihre eigenständig berechneten Tensorhashes entsprechen exakt der akzeptierten Originalinitialisierung `43e2c214143f4354aaaa9b8db945941f2d6b8d04f09d9792d4eec6e3d17c45b6`. Gespeicherter Adam tatsächlich leer und mit akzeptiertem Initialhash `e792320c12ea2f52219d0b177d630df0bfe99e53787969098c6fb67510a1012e`, lr=5e-5. Vollständige Kontrollconfig, Start-/Quell-/40-Spiele-Metadaten, `ensemble=[]`, env_steps=72120 und learn_steps=0 korrekt. Keine alten Tensorarchive erneut geladen.

**Tatsächliche Replays:** sämtliche s/a/r/ns/done/mask-Arrays mit exakten Dtypes/Dimensionen und endlichen Werten geprüft; Actions, Terminals und Folgemasken gültig. Alle gespeicherten r sind bitexakt die Float32-Quantisierung der ursprünglichen Kontrollformel aus dem archivierten Rewardstream. Eigenständig für jedes der 40 Spiele die vollständigen geordneten UID-/Feature-/finalen Replayaction-/Folgefeature-/Terminal-/Masken-Digests sowie Gegenformeldigests rekonstruiert; alle Stimmen. Gesamt-Replay-/Rewardhashes und die Outcome-Zähler ebenfalls selbst berechnet. Maximaler Rest der originalen Gegenformelrelation 18×Outcome **3,553×10⁻¹⁵**, innerhalb der vorab bestehenden Toleranz; dies ist eine Formelkonsistenzprüfung, kein neuer Rewardkontrast zwischen den beiden ON-Starts.

**Mechanismus:** je Arm 12.120 Handlungsaufrufe, 12.000 Q-Aufrufe und 432.000 Mitgliedsforwards. Quellenreihenfolge mit aktuellem Mitglied18, alle 35 aufgezeichneten eingefrorenen Identitäten und kumulative Übergangszähler konsistent zur akzeptierten Technik. Geänderte legale Präferenzen: 27.616 bei on48 und 29.355 bei on49. Je drei gespeicherte reale Mittelungsbeispiele unabhängig nachgerechnet; maximale Mittelwertabweichung 4,636×10⁻⁷ beziehungsweise 3,113×10⁻⁷, jeweils innerhalb derselben vorab begründeten Float32-Summations-/Divisionsgrenze wie im Technikcheck. Setup-RNGhashes vor/nach gleich und passend zur akzeptierten Technik; Python-/NumPy-/privaten PCG64-Initialzustand erneut selbst aus dem jeweiligen Start rekonstruiert.

Admission, technische Rootannahme/Receipt sowie Source-/Input-/Interpreter-/Schutzbindungen bestanden. Vorlaufhashes blieben während des Audits unverändert. Keine geschlossenen Studien erneut breit geprüft.

**Grenzen:** Originalformel- und Policyprovenienz lassen sich ohne vollständige Kontexte/native Rohaktionen nicht unabhängig neu simulieren. Die tatsächlichen gespeicherten Streams und alle Abschnittsdigests sind geprüft; eingefrorene35-Rohtensoren wurden nicht separat gespeichert, daher bleiben deren Identitäten gebundene Livehashbelege. Torch-Setup-RNG und historische vollständige Bibliotheks-/RNGzustände sind ebenfalls nicht aus Rohsnapshots wiedergewonnen. Das bestätigt Vorlaufkonsistenz, keinen Lernabschluss oder Stärkezuwachs.

SHA256:

- Trainingadmission: `be82efd30f0b7eb7beab40ac47a98dbba6c25f7ddf9f0cbfe376e3d773c2f24d`
- on48 prefill.json: `ee8fce7f3215e048e780dbca71e510774ae197eb2f2f8d846cfedf436d15bc6a`
- on49 prefill.json: `bd3bee8a1ea8f13e47ccd91acae8a58ceaea0cde16c72caa962c84dbfad17720`
- `results.json`: `f5ceea097f18cd4abff7464d092ecc9ee90c21b1a55c1c8f2800f47828215b1e`
- `check.py`: `6406efc4d39e331d824c8dc8c956dcb9e1acfbfa1047daa4d654c04f4730ae3e`
- `bindings.json`: `2b28689d204e68bdd42cb560bf0f9f2462496ea0b70a47796ff26f7747f59b49`
- `run.log`: `84f0ef9bf379a7bc28a4a6699414afb17d2771f2aac32c5abc1921a8de3b3dab`
