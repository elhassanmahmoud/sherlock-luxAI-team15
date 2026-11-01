# Fachliche Trainingsdaten-Abnahme vor B/C-Zulassung

**BESTANDEN.** Beide vorregistrierten Endnetze dürfen als B/C gemäß Nachtplan zur unabhängigen Auswahl verwendet werden. Dies ist die Abnahme der korrekten Durchführung und tatsächlicher Lernupdates, kein Nachweis höherer Battle-Stärke.

Prüfung am 2026-11-01T21:03:41.133146+00:00: 18,369 Einzelchecks, keine Fehler. Ausschließlich vorhandene Dateien gelesen, Checkpoints auf CPU geladen, ein Torch-Thread. Keine Spiele, Trainings, Testsuite, Repoquelländerungen oder Commits. Maschinenlesbarer Befund: `training-data-review.json` im selben Ordner; reproduzierender reiner Dateiprüfer: `verify_training_data.py`.

## Exakter gepaarter Versuch

- Supervisor vollständig, beide Prozess-Exits 0; gemeinsames Zeitfenster 2441.8 Sekunden =40 Minuten 41,8 Sekunden und damit unter zwei Stunden.
- HEAD und alle Quell-/Plan-/geschützten Gewichtsdateien stimmen unverändert mit dem Training-Freeze überein: `390de378c06dbde8bde0e11c68b2ba35b77bda48`.
- Init und beide Arm-Provenienzen sind korrekt gebunden. V14-Quellhash `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; tatsächliche Source-Komponente `ensemble[17]` (=Index18) ist tensorweise identisch mit dem Einzelnetz-Init. Init-q und Init-target stimmen exakt überein; initial kein Optimizer und keine Ensemble-Extras.
- Gemeinsamer Starttensorhash `3c79c58371bc67badf7962e84276d474bad3bff690d1ad465cb3977a45ddb309`. Ein vorhandenes Ensemble-Optimizerfeld wurde nicht als Komponentenzustand verwendet; frischer Adam ist ausdrücklich belegt.
- Beide tatsächlichen Configs unterscheiden sich **ausschließlich** in `w_discovery`: Kontrolle0,5, Discovery2,0. `w_explore=0,3`, lr1e-4, V14-/V12-Trainingsregeln, unveränderte eval-only-Rescue-Sperre, `overlap_infer=false`, `frozen=false` stimmen überein.
- Genau600 Trainingsspiele pro Arm, Seed9, Karten294200–294499 mit beiden Seiten, genau120 Prefillspiele, kein altes Replay, kein Pool/Snapshot, Endstandwahl und keine Testkarten. Die Manifestobergrenze294500 ist exklusiv.
- Mix .6 Solution/.2 Quadrat-Solution/.1 default/.1 rush korrekt. Die komplette tatsächliche Gegnerfolge beider Arme wurde unabhängig durch NumPy-RNG4209 reproduziert, nach exakt120 übersprungenen Prefillziehungen. Beide folgen ihr in allen600 Zeilen. Tatsächliche Häufigkeiten je Arm: Solution348, Quadrat128, default55, rush69. Das sind die korrekten Zufallsziehungen des vorab festgelegten Mixes, keine nachträgliche Quotenauswahl.

## Vollständige CSV-Prüfung

Beide `train.csv` haben exakt das erwartete vollständige Schema und600 eindeutige geordnete Zeilen. Alle Seeds, Seiten, Gegner,303 Steps und Punktezählungv2 stimmen. Matchsiege, Spielresultat, Punktergebnis und Punktsummen sind kohärent; sämtliche numerischen Werte, Losswerte und Zähler sind endlich. Rolling-Winrate und die vollständigen Env-/Lernzähler stimmen pro Zeile exakt mit ihrem Fortschritt. Keine günstige Teilmenge wurde verwendet.

Die beiden `val.csv` haben jeweils exakt sechs Aggregatzeilen:0/300/600 × default/Solution, je16 Spiele auf denselben acht bekannten Karten. Die Anfangsvalidierung nach dem Prefill ist in allen Aggregaten zwischen den Armen identisch. Sämtliche vorhandenen Analysewerte sind endlich und plausibel. Die Spalte `secs` ist im bestehenden Aggregatformat absichtlich leer; Laufzeiten werden aus vollständigen Manifeste-/Supervisorzeiten und Trainingszeilen abgenommen.

Training-Lossbereiche: Kontrolle 0.61405–0.78437, Discovery 0.62028–0.80686. Die Lossniveaus sind wegen der unterschiedlichen Rewards kein eigenständiger Stärkenvergleich.

Gesamtumfang:1200 neue Trainingsspiele +240 Prefillspiele +192 bekannte Validierungsspiele =**1632 tatsächlich simulierte Spiele**. Keine neue unabhängige Bewertungskarte durch diese Abnahme verbraucht.

## Endcheckpoint statt „bester nach0“ konkret bestätigt

In beiden tatsächlich gespeicherten Enddateien stehen **env_steps278160 und learn_steps90000**, exakt wie in ihrer600. Trainingszeile. Alle zwölf Adam-Parameterzustände sind vorhanden, haben je90000 Updates und endliche, tatsächlich nichtleere Gradientenmomente. Alle Q-/Target-/Optimizerwerte sind endlich; Architektur und Tensorformen entsprechen dem79-Feature-/6-Aktionen-Init.

Die End-Qs weichen vom unveränderten Start und voneinander ab. Q und Target sind jeweils identisch, wie beim letzten Update90000 und der Targetperiode500 zu erwarten ist. Die finalen Replay-Rewardarrays sind vollständig (300000 Transitions) und endlich.

Der separate `weights_best/agent.pth` enthält tatsächlich den Stand nach0 Trainingsspielen: learn_steps0, env_steps96360 nach dem Prefill und denselben Q-Hash wie der Init. **`weights/agent.pth` enthält dagegen die gelernten600er-Endnetze.** Die historische Abschlusszeile „bester Checkpoint nach0“ beschreibt die interne Val-Bestenliste und setzt `--keep-final` nicht außer Kraft.

| Arm | Enddatei-SHA256 | Q-/Target-Tensorhash |
|---|---|---|
| Kontrolle | `f30a40e103c6e5b5f8bb8f54984fafea5999f5c1873d21b0150e88186ca0212b` | `68b0adac2eea45ada0ef9aad10bf214a3d504f1d06f2d9dddd1584ff5438c2be` |
| Discovery | `8f8d150d6a4ba0b0e7ce139b6e90e229fed332366f9c9ca553a0239112388cc2` | `382706f2145c6b25857db35f7c01d821ec391aecff304ff515519e6b1a134a0b` |

Die neue Auswahl muss exakt diese Enddateien verwenden. Ihre Hashes stimmen zudem mit den vom Supervisor nach Abschluss aufgezeichneten Hashes überein.

## Aussagegrenze

Die bekannten acht Validierungskarten erlauben keine Aussage über neue Karten: Solution am Ende15/16 für Kontrolle und14/16 für Discovery ist weder ein Methodenbeweis noch ein Grund, einen Arm wegzulassen oder eine neue Rewardstärke anzupassen. Es bleibt ein einziger gepaarter Trainingsstart. B/C gehen wie vorregistriert beide mit dem V14-Ensemble und V14-Inferenzconfig in die unabhängige Auswahl; eine Übernahme braucht weiterhin das separate Bestätigungsgate.
