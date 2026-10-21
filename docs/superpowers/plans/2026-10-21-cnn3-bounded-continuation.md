# Begrenzte CNN3-Fortsetzung nach den V4-Koordinationspiloten

Vor neuen Trainings-/Vergleichsspielen festgelegt am 21.10.2026. User autorisiert eigenständige Folgearbeit und Training bis 22.10.2026 06:00 Berlin. Root entscheidet Gates, ein Implementer korrigiert ausschließlich die fehlende Torch-Seeding-Bindung, unabhängiger Reviewer prüft Code und Messdaten. Keine Änderung an V3 oder seiner Sicherung.

## Anlass und Reichweite

Der Paar-Koordinator verfehlte das Entwicklungsgate. Der getrennte Zielpilot lieferte keine geeigneten Alternativen; kein Zielbewerter wird daraus trainiert. Mahmoud hat inzwischen die originalen CNN3-Checkpoints bereitgestellt. Historische CNN3-Ergebnisse sind schwankend und kein Beleg eines Vorteils gegenüber V3. Deshalb genau **ein kleiner Fortsetzungsversuch**, keine erneute große Parameter-/Checkpoint-Suche.

Hypothese: Weitere PPO-Erfahrung hauptsächlich gegen Solution_92 könnte einen nützlichen Kandidaten liefern. Ausgangspunkt ist der **letzte** Originalstand PPO60, nicht der historisch auf Validierung beste PPO50. Quelle `experiments/candidates/cnn3_ppo0060.pth`, SHA-256 `0efe4d39c8b2c8e56d4877e208b6064fc3766b9c486f83c6f82407cf11fb0bef`. Nur der endgültige Stand nach zehn Iterationen ist Kandidat. Da kein paralleler Kontrolltrainer geplant ist, wäre selbst ein Gewinn kein isolierter kausaler Nachweis für den Gegner-Mix.

## Technische Vorbedingungen

- Fehlendes Torch-Seeding in `play_recorded` und `cmd_ppo` durch reproduzierenden Test bestätigen und minimal korrigieren. Pro Spiel Torch-Seed `2 * game_seed + side_id`; Lernprozess `args.seed` vor Netz-/Critic-Aufbau und Minibatch-Zufall. Python-/NumPy-Semantik bleibt gleich. Keine Garantie für bitweise Identität auf verschiedener Hardware.
- Fokussierte Tests und unabhängiger Review, anschließend einmal passende Integrationssuite. Ein vollständiger kurzer echter Rollout wird innerhalb der registrierten Trainingsmenge geprüft; keine zusätzlichen versteckten Lernspiele.
- Neuer exklusiver Run-Ordner `experiments/ppo/cnn3_sol90_s20_20261021`; Original nach `start.pth` bytegleich kopieren, `teacher.json` mit ursprünglicher Herkunft erhalten. Teacher-Datei per Hash verfügbar machen, obwohl Teacher-Wahrscheinlichkeit null ist. Keine vorhandenen Logs/Checkpoints überschreiben.
- Warmstart: Policy/Critic aus PPO60; **frischer Adam-Optimizer**, keine genaue Wiederaufnahme des alten Optimizer-/RNG-Zustands. Architektur, Reward und gespeicherte Agent-Konfiguration unverändert. Kein nachträgliches Hinzufügen bereits erfolgloser V3-Regeln.

## Festes Training

`python -m scripts.ppo_train ppo --run cnn3_sol90_s20_20261021 --start start.pth --seed 20 --iters 10 --games 24 --workers 1 --lr 1e-4 --epochs 3 --mb 256 --clip .15 --ent .003 --vf .5 --sol92 .9 --default .1 --teacher 0 --detach-value --vf-warmup 0 --save-every 10`

240 Spiele, 120 unterschiedliche Karten, beide Seiten je Karte. Gegner werden mit dem bestehenden Mixer gezogen, nicht auf exakt 90/10-Anzahlen erzwungen. Kartenformel `150000 + 20*20000 + iteration*24 + game_index//2`, Iterationen1–10, Index0–23: Teilblöcke innerhalb **550024–550251**. Keine Treffer unter523 vorhandenen Seed-CSVs vor Plananlage; vor Start erneut Remote prüfen und Seedliste archivieren. Historisches Training nutzte andere Batch-/Workerzahlen. Minibatch 256 statt 4096 erhöht bei gleichen Daten die Anzahl der Optimizer-Schritte deutlich; es ist eine feste, ressourcenbedingte Änderung der Optimierung. Ein Worker begrenzt die Speichernutzung. Diese Unterschiede verhindern eine isolierte kausale Zuschreibung an den Gegner-Mix.

Ein Trainingsprozess, keine parallelen Spiel-/Modelljobs. Threadlimits1. **Maximal90 Minuten**, zusätzlich absolute interne Deadline22.10.03:15UTC (45Minuten Abschlussreserve vor04UTC). Nach erster abgeschlossener Iteration lineare Laufzeitprojektion inklusive 20% Reserve; falls zehn Iterationen nicht innerhalb90Minuten oder Restbudget passen, kontrolliert abbrechen. Auch bei nichtendlichen Losses/Tensoren, Fehlern, Hashänderungen oder anhaltendem Speicherdruck stoppen. `wr_teacher=nan` bei keinem Teacher-Spiel ist erwartete fehlende Kennzahl, kein numerischer Fehler. Keine Teilcheckpoint-Auswahl, kein automatischer Wiederanlauf eines abgebrochenen Trainings. Bei Abbruch kann die nächste angefangene Rollout-Runde bereits zusätzliche Spiele enthalten: bestätigte vollständige Iterationen und die höchstens 24 unvollständig belegten Spiele der nächsten Runde getrennt berichten. Die CSV zählt erst nach einem vollständigen PPO-Update.

## Evaluation und feste Entscheidung

Quellen/HEAD/Runtime, Original-, V3- und Sicherungs-Hashes vor Start einfrieren und während Jobs prüfen. Zunächst OriginalPPO60 gegen default und Solution_92 auf60 **bekannten** Entwicklungskarten500720–500779×beide Seiten =240Spiele. Das dient Referenz und technischer Prüfung, nicht einer nachträglichen Wahl des Trainingsstarts. Der Pilot bleibt bewusst klein trotz schwächerer historischer CNN3-Werte.

Nach komplettem, technisch gültigem Training den einzigen finalen Kandidaten auf denselben240Spielen prüfen. V3-Referenz102/120Solution und120/120default aus dem bereits auditierten Vergleich darf nur nach Hash-/Quellenabgleich und vier reproduzierten V3-Kontrollspielen (500720–500721, beide Seiten, Solution) verwendet werden. Sämtliche Nichtzeitfelder dieser Kontrollen müssen exakt übereinstimmen; sonst die vollständigen240V3-Referenzspiele neu ausführen und die Abweichung vor jeder Stärkeentscheidung klären.

Entwicklungsgate: Kandidat **≥108/120 echte Siege gegen Solution**, strikt mehr Siege als PPO60 auf denselben120Spielen, **120/120 gegen default**. Bei Scheitern beendet dieser Kandidat den Versuch ohne Direkt-/Frischtests. Bei Erfolg120Direktspiele gegen unveränderten V3 auf denselben60Karten, Resultatmittel≥0,5; acht Kurs-Runner-Spiele, p95 Aktionszeit ≤50ms/max ≤250ms und valide Pflichtschnittstelle. Der bestehende DQN-Prüf-/Paketweg ist dafür ungeeignet: erst bei bestandenem Stärke-Gate einen minimalen, unabhängig geprüften PPO-Ladeadapter hinzufügen und damit den echten Kurs-Runner prüfen. Keine Messung eines versehentlich frisch initialisierten DQN als PPO-Kandidat ausgeben. Ein reines PPO-Modell darf nur nach geprüftem geeigneten Verpackungs-/Ladeweg promoted werden; keine PPO-Datei blind in einen DQN-Lader installieren.

Auswertung: vollständige eindeutige Gegner/Karte/Seite-Schlüssel, `point_counting_version=2`, endliche gültige Resultate. Echte Siege primär gegen feste Gegner, Remis separat; direkt Resultat0/0,5/1. Gepaarter Bootstrap ganzer Karten einschließlich beider Seiten,5000Ziehungen,NumPyGeneratorSeed0,95%-Perzentile. Entwicklungswerte sind bekannte Auswahldaten, keine unabhängige Bestätigung.

Nur bei vollständigem Entwicklungsgate gelten unverändert die [V4-Frischgates](2026-10-21-v4-joint-prototype.md): reservierte523000–523199, Kandidat undV3 je800Gegnerspiele;523200–523399,400Direktspiele. SolutionΔ≥5pp und95%-Untergrenze>0;default≥99%undΔ≥−1pp; direkte95%-Untergrenze>0,5. Vor Nutzung neuer Karten wieder Remote/Seedreservierung und Zeitbudget prüfen. Keine Datennachlieferung bei Grenzergebnis. Finaler100%-Audit520000–520999 nur nach Qualifikation und ausreichender Zeit; kein universelles100%-Versprechen.

## Abschluss

Unabhängiger Datenreview, Root-Reproduktion, sinnvolle separate Commits für Seedfix und Trainingsergebnisse; main erhält geprüfte Werkzeuge/Übergabe, unqualifizierte Modelle bleiben Experimente. Alte6-Netz-Sicherung erhalten; vor einer qualifizierten Ablösung auch aktuellenV3 separat sichern. Tatsächliche Spiele, Zeiten, Tensoränderungen, Unsicherheiten und gepushte Commits dokumentieren. Bei negativem Pilot nicht blind verlängern oder weitere Startpunkte probieren; begrenztes Programm sauber abschließen oder ausschließlich einen konkret belegten neuen Fehler untersuchen. Spätestens22.10.06Berlin eigene Jobs beendet und Morgenbericht fertig.

Vor Ausführung korrigiert nach unabhängigem Review: kurzer `--run`-Name, weil der Trainer das Verzeichnis `experiments/ppo` selbst voranstellt; Ressourcenänderung am Minibatch als zusätzliche Optimierungsänderung benannt; DQN-only-Paketweg als bedingter technischer Folgeauftrag festgehalten. Noch keine neuen Trainings- oder Vergleichsdaten bei diesen Präzisierungen.
