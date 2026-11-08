# Umsetzung des begrenzten Artillerievergleichs

Verbindliche Methode: [Spezifikation](../specs/2026-11-08-artillery-comparison.md), [ursprüngliche Artilleriestudie](../specs/2026-11-08-artillery-alignment.md) und [Größenvermerk](../../../experiments/analysis/artillery_alignment_20261108/operations/comparison-sizing.md). Kein Methodennachtrag aufgrund von Leistungsresultaten.

## 1. Sicheren Übergang herstellen

Alle vier trainierenden Arbeiter und den Supervisor vollständig beenden lassen; keine neuen Quellen, Tests oder Modelle während der Sperre. Noch auf Quelle02ce1b2 alle vier ursprünglichen Abschlussvalidatoren und die unabhängige Rohdatenprüfung ausführen. Rootbeleg bindet je Arm Receipt-SHA, env_steps193320 und learn_steps60000. Datenbericht `PASS_DATA_ONLY` bleibt als Datenprüfung erkennbar; Rootvalidator liefert tatsächliche Tensor-/Adam-/Reloadprüfung.

Historische Abnahme exklusiv unter `experiments/analysis/artillery_alignment_20261108/operations/historical_training_acceptance.json` speichern. Schema1, statusPASS, eligible_for_comparisonTrue, training_head, root, exakte source aus manifest.pins.source, protected, prepared, prepared_manifest_sha256, files, arms, totals, supervisor, paired_prefill, independent_audit und root_validation. Jede Datei-/Belegreferenz ist zusätzlich im vollständigen files-Inventar gebunden. Arm counts: actual_prefill_games40, actual_train_games400, actual_validation_games32, executions472, learn_steps60000, env_steps193320; totals:160/1600/128/1888/240000. Receipt plus alle neun Rohartefakte je Arm, alle vorbereiteten Starts und beide Paarfreigaben erhalten. Supervisorabschluss nach Cleanup binden. Fehlende Replaybuffer dürfen nicht aus der Prüfliste entfernt werden.

Erst nach dieser Abnahme Quellen wieder freigeben und Stagingdateien übernehmen. Tatsächlichen Abnahmehash in `ACCEPTANCE_SHA256` eintragen; vorliegendes `None` blockiert die Montage. Historische Validatoren bleiben unverändert.

Replaybuffer von ungefähr187MB je Arm werden nicht in Git aufgenommen. Modelle und kompakte Rohbelege werden versioniert. Eine vollständige Roh-Audit-Reproduktion in einem anderen Checkout oder bei Mahmoud erfordert zusätzlich die getrennte Übertragung aller originalen Buffer und deren Hashprüfung; ein Pull allein genügt nicht. Die lokale Pflichtbindung aller neun Artefakte bleibt uneingeschränkt bestehen. Keine Portabilität behaupten, solange diese Dateien dort fehlen.

## 2. Adapter und synthetische Tests prüfen

Neue Dateien sind `scripts/artillery_alignment_compare.py`, `scripts/artillery_alignment_eval.py` und `tests/test_artillery_alignment_compare.py`. Vorhandene geprüfte Helfer für Pfadrebasing, strikte Checkpoints, CSVs, Kartenbootstrap, LOCAL_SIX, Gates sowie Queue/Receipts/Guard/Cleanup wiederverwenden. Keine globale Umkonfiguration des Fog-Profils, keine Änderungen an Agent, Training, alten Vergleichsdateien oder gemeinsamen Gates.

Tests wurden vor der Stagingimplementierung vorbereitet. Wegen laufender Modelljobs wurde in der Stagingarbeit weder RED noch GREEN ausgeführt. Das ist keine bestandene TDD-Prüfung. Root führt nach Ende aller Modelljobs die geeigneten synthetischen Tests tatsächlich aus, dokumentiert Fehler/Behebungen und lässt Code/Methode unabhängig prüfen. Keine neuen Spiele als Werkzeugsmoke.

Prüffälle: echte Receiptform/False-Eligibility, noch ungepinnte Abnahme, fehlende Roh-/Vorlauf-/Start-/Paar-/Auditdateien, Config-/Hash-/Zählerabweichung, erlaubtes historisches Rebasing, exakt geordnete36+43+44-Netze und erneutes Laden, NaN/falsche Flag-/Mitgliederreihenfolge, Überschreibschutz, 440/600-Matrix, vier feste20er-Listen, Halbsieggrenzen, Rangfolge/CONTROL-Gleichstand/kein Nominierter, LOCAL_SIX und zehn Bestätigungsgates, Default-Remis, vollständige Receipts/Befehle/Quellen, unabhängige Auswahlabnahme, relative und absolute Analysepfade, STOP/AC/Quota/fremde Prozesse/maximal zwei Worker und unveränderte alte Profile.

## 3. Frische und Eingaben annehmen

Vier Listen exklusiv vorbereiten: selection_panel9800000–9800019, selection_direct9800100–9800119, confirmation_panel9801000–9801019, confirmation_direct9801100–9801119. Exakte Einzelzahlen stehen in der Spec. Keine Spiele vor erneuertem zielbezogenem Audit und ausdrücklicher Root-Abnahme der bekannten Suchgrenzen.

`experiments/analysis/artillery_comparison_20261108/operations/seed_acceptance.json` enthält schema_version1, statusPASS, profileartillery_alignment_20261108, cohorts mit exakt diesen vier Listen und audit:{path,sha256}. Repositoryrelative Referenzen. Root-Audit enthält statusPASS, no_observed_conflictsTrue, limitations als nichtleere Liste und raw_audit:{path,sha256}; zusätzliche Rohbelege gegebenenfalls vollständig als files:{path:sha256}. Tatsächlichen Seed-Abnahmehash in `SEED_ACCEPTANCE_SHA256` pinnen. Der Start bindet Root-Audit, Rohdatenbelege und alle vier Listen gemeinsam. StatusPASS bedeutet keine absolute Garantie über externe oder seedlose Altbestände.

Montage nach Trainingsabnahme: `python -B -m scripts.artillery_alignment_compare build`. Listen/erste Jobs exklusiv mit `prepare-plans` erstellen. Montage und Zulassung müssen vor Leistungsspielen unabhängig geprüft sein. Beide neuen Kandidaten bleiben Experimente, uniform38, V14-Inferenzkonfiguration, nur finale43/44-Q-Netze.

## 4. Auswahl und bedingte Bestätigung

Aktuellen geprüften Vergleichs-HEAD und alle Eingaben einfrieren. `scripts.artillery_alignment_eval start` braucht jobs, admission, neuen out, python, expected-head und frische usage-file. Eigener STOP unter `/private/tmp/sherlock-artillery-comparison-20261108/STOP` (kanonisch aus System-tmp). Maximal zwei Worker; keine Tests oder Audit-Pythondateien im Repository während dieser gemeinsamen Sperre. Alle vier Listen, Quellen, Modelle, Gegner, Spec, Plan und Größenvermerk bleiben bis zum endgültigen Ende gleich.

Auswahl elf Jobs×40=440 vollständig abschließen und `analyze` ausführen. Kein Statistikresultat vor vollständiger CSV-/Receipt-/Befehlsmatrix. ALIGNED−CONTROL zusätzlich beschreiben; keine Mechanismusbehauptung aus zwei Starts. Unabhängige Auswahlabnahme bindet statusPASS, profile, vollständigen summary_sha256 und denselben deterministischen nominee. Ohne Nominierten Welle beenden.

Nur mit akzeptiertem Nominierten `prepare-confirmation --selection-acceptance ...`: genau ein frischer Plan für15×40=600. Vor Bestätigungsstart gesamte Auswahl unverändert neu prüfen und binden; gleicher Quellen-HEAD wie Auswahl. Nach vollständigem Abschluss dieselben zehn Gates und unabhängige Nachrechnung. FAIL oder unklar: V14 bleibt, keine Zusatzkarten, kein Nachrücker und keine Wiederholung.

## 5. Abschluss und tatsächlicher Nachweis

Alle eigenen Modell-/Wachhalteprozesse beenden. Rohdaten, Quell-/Eingangs-/Receipt-Hashes, tatsächliche Prüfungen, Grenzen und Entscheidung erhalten. Erst nach Freigabe des Quellenstands Arbeitsstand und Experimentprotokoll aktualisieren. Kein Stärkenachweis aus Loss, technischen Checks oder Diagnosekarten. Eine Promotion erfolgt ausschließlich nach allen fachlichen Gates, unabhängiger Abnahme, Sicherung beider alten Gewichte, Kurs-/Lade-/Laufzeitprüfung und dokumentierter Reproduktion für Mahmoud.
