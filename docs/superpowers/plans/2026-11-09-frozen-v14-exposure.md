# Frozen-V14-Exposition – Umsetzung

> Ausführung mit Subagents und unabhängiger Task-Review; Root koordiniert tatsächliche Phasen. Quelle der Anforderungen: zugehörige Spec.

**Goal:** Zwei feste Ensemble-Verhaltenslerner bei identischem Reward gegen eine feste Solution/V14-Mischung trainieren und später begrenzt mit V14/BEHAVIOR38 vergleichen.
**Architecture:** Neue schmale Studien-/Ownerdateien, unveränderte bestehende Lern-, Reward-, Behavior-, Replay-, Statistik- und Prozesshilfen importieren. Keine produktive Quelle umschreiben und kein generisches Framework bauen.
**Spec:** docs/superpowers/specs/2026-11-09-frozen-v14-exposure.md

## Global Constraints

Vier Technikspiele, zwei40er-Vorläufe, gemeinsame manuelle Root-Barriere, zwei400er-Lernläufe, Endstände; spätere200er-Auswahl separat. Starts48/49 und alle ursprünglichen Rolloutkarten/Seiten/Solutionpositionen erhalten, nur ursprüngliche Nicht-Solutiongegner durch hashgebundenen V14 ersetzen. Weder Reward noch eigene Behavior-/DDQN-Mechanik ändern. Original V14/ZIP bleiben. Maximal2Worker/keine Tests parallel/echteQuota/kein Retry/Resume/automatische Folgephase.

## Review Focus

Gegner muss tatsächlich das richtige36er-Modell auf der Gegenseite sein; kein eigener Behavior-Hook oder Training am Gegner. Eigen-/Gegnerinitialisierung darf globale/Agent-RNG nicht verschieben. Frische Gegnerinstanz je V14-Spiel mit Seed0; normales new_game und neue env_cfg, Gegenseite korrekt. Reale Gegner-Ausnahmen dürfen nicht verschluckt werden. Öffentliche Beobachtungen und eigene Replaylabels bleiben identisch im alten Solutionpfad. Historische Belege prüfen, keine alten Admission-Aufrufe gegen neuen HEAD. Exklusive Ausgaben und echte Prozessenden vor Folgephasen.

## Task 1 – Werkzeuge, Verträge, Quellen

Create scripts/frozen_v14_exposure.py, scripts/frozen_v14_exposure_owner.py, tests/test_frozen_v14_exposure.py. Reuse BehaviorEnsemble, make_learner, reward_audit, action_audit, TraceEnv, replay serialization, state hashes, original stock opponent loader and lifecycle helpers. Kleine eigene play_one-Variante darf nur die explizite Gegnerwahl/Belege ergänzen. Keine globalen Modulpatches zur Profilfälschung. Gegnerkopie an ursprüngliche Montage/accepted receipt und original36-Tensorhashfolge binden; beide tatsächlichen historischen ON-Finals/Trainingsclosure als Kontrollprovenienz binden.

- [ ] Zuerst sinnvolle synthetische Tests: ursprüngliche Solutionpositionen/Karten/Seiten unverändert, Nicht-Solutionersatz genau; falscher Modellhash/Config/Seite/36erIdentität abgelehnt, Learning/Save am Gegner verboten, RNG/Memoryresetvertrag; historische Datenbindungen; Barrieren/Outputkollisionen/Stop/Prozessgruppen/defekte Counts. Keine echten Archive/Modelle/Simulatoren in Tests. Vorhandene passende Hilfertests nur soweit nötig.
- [ ] Minimaler Adapter/Worker/Owner, tatsächliche Red/Green-Nachweise. Status/Profile `frozen_v14_exposure_20261109`, Rollen e48/e49; Checkpoints behalten originale cfg/q/target/opt und metadaten `exposure` mit Profil/Status/Rolle/Start/Quelle/Spiele/Komponente18/Gegnerhash. Release-/Admission-/Receipt-Vertrag vor Root-Aufnahme knapp dokumentieren.
- [ ] Unabhängiger Review, Root-Byte-/Logprüfung, Kartenprüfung, sinnvolle Quellenpublikation/Primaryabgleich.

## Task 2 – Tatsächliche Technik und zwei Lernarme

- [ ] Root baut exklusive technische Aufnahme (Originalruntime/Inputs/Schutz/Quellenhashes), genau vier bekannte Spiele. Tatsächliche beiden alten ON-Verläufe reproduzieren; neuen eingefrorenen Gegner und echte Teilhabe belegen. Unabhängige Prüfung, Root-Abnahme erst nach Originalprozessende.
- [ ] Separate Trainingsaufnahme, genau zwei Worker. Beide40er-Vorläufe tatsächlich gemeinsam unabhängig prüfen; tatsächlicher unveränderter Gegner, eigene q/Target/Adam und gespeicherte Daten. Manuelle Rootfreigabe der Originalworker.
- [ ] Je400 Lernspiele vollständig, finale tatsächliche Tensor-/Adam-/Replay-/Gegner-/Updateprüfung; keinen Zwischencheckpoint auswählen. Abbruch ehrlich archivieren, keine automatische Ersatzrunde. Root-Abschluss vor Freeze-Lösung, dann Ergebnisse/Modelle veröffentlichen.

## Task 3 – Separat fester Vergleich

Erst danach neuer enger Vergleichsadapter aus bestehenden Montage/Loader/CSV/Statistik/Lifecyclehilfen, eigene Spec/Details aus bereits hier fixierten200Karten/Gates unverändert konkretisieren. Neue Modelle nicht vorab auswählen. Echte Nullspiel-Montage annehmen, Performance separat aufnehmen, alle tatsächlichen200Zeilen und Intervalle unabhängig/Root prüfen. Negative Variante endgültig schließen, positives Ergebnis nur nominieren. Keine automatische frische Bestätigung oder Promotion. Anschließend autonome neue Entscheidung anhand echter Daten.
