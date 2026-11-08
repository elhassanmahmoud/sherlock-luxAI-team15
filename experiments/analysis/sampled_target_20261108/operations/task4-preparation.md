# Sampled-Target Task 4 – externe Textvorbereitung

**Status: UNRUN.** Nur Textdateien geschrieben und statisch gelesen. Kein Python, Import, Syntaxcompile, Test, Modellladen, Spiel oder Repoeingriff. Die Dateien sind ausdrücklich keine Trainings- oder Leistungsfreigabe. Historische Trainingsabnahme und deren tatsächlicher SHA liegen noch nicht vor; `ACCEPTANCE_SHA256=None` blockiert Build/Start.

Maßgeblich sind die festgelegte Sampled-Target-Spec/Plan und `/tmp/sampled-target-task4-handoff.md`. Task 3, produktiver Agent, historische Studien und V14 bleiben unangetastet. Vier finale **Einzelnetze** werden in getrennten Dateien ausschließlich für Inferenz kopiert; kein Ensemble, V14-Vergleich oder V14-Ersatz.

## Dateien / Schnittstellen

- `scripts/sampled_target_compare.py`: `historical_acceptance(root)`, `build_inference_copies(root=...)`, `validate_admission(path,root=...)`, `performance_plan(admission)`, `validate_plan(plan,root,admission)`, `prepare_plans(root=...)`, `validate_performance(panels,direct)`.
- `scripts/sampled_target_eval.py`: `validate_job_csv`, `build_state`, `validate_receipt`, `analyze`, `run_supervisor`. Wiederverwendet `par_eval`, den bestehenden vollständigen CSV-Reader, Statistikhelfer und Owned-Queue/Cleanup. Zwei lokale Controller-Callbacks (`guard`, CSV-Prüfung für die neuen expliziten self-Pfade) werden nur während des Controllerprozesses eingesetzt und im finally zurückgesetzt. Keine Agent-/RNG-/Factoryänderung, keine Änderung des historischen Supervisors oder alter Profile.
- `tests/test_sampled_target_performance.py`: synthetische Prüfung von Ganzzahlgrenzen, vollständiger Matrix, Kartenbootstrap, Plan, historischen Hash-/Abnahmebindungen, Inferenzkopien und tatsächlichen Primär-/self-Ladewegen mit winzigem synthetischem Checkpoint. **Alle Tests ungestartet.**

## Feste 400 Spiele

Rollen `control45`, `sampled45`, `control46`, `sampled46`. Jede Rolle gegen `solution92` und `sol92_sq`, je20 Karten9930000–9930019×beide Seiten: acht Jobs×40=320. Je Start ein direktes Duell Sampled gegen die zugehörige **Inferenzkopie** Control auf9930100–9930119×beide Seiten: zwei Jobs×40=80. Zehn Jobs, maximal zwei gleichzeitig, jeder `par_eval --workers 1`, keine Overrides, keine Nachspiele.

Inferenzkopien: `experiments/candidates/sampled_target_20261108/{role}.pth`. Jede Kopie erhält exakt die gebundene V14-Quellconfig mit ausschließlich `frozen=False`; jedes nicht-Config-Element einschließlich sämtlicher Tensoren, Target, Adam und Metadaten bleibt nach typisiertem Hash unverändert. Die ursprünglichen Trainingscheckpoints bleiben erhalten. Copy/Reloadprüfung braucht keine Netzinstanz oder Forwards. Der synthetische Integrationstest lädt später einen kleinen Checkpoint über `par_eval.build_cfg`+produktiven `Agent_x` und `common.make_opponent('self',...)`; beide tatsächlichen Configs müssen identisch sein.

Plan: `experiments/analysis/sampled_target_performance_20261108/plans/{panel.json,direct.json,jobs.json}`. Planverzeichnis und Inferenzordner werden nur einmal exklusiv erzeugt. Ein unvollständiger Versuch wird nicht automatisch wiederholt.

## Vorgeschlagene historische Root-Abnahme

Root erzeugt diese Datei **erst nach** beendetem Trainingssupervisor/Wachhalter, allen originalen finalen Validatoren und unabhängiger vollständiger Datenprüfung, noch unter der Trainingsquelle:

`experiments/analysis/sampled_target_20261108/operations/historical_training_acceptance.json`

Die tatsächlichen Bytes werden danach durch Root als `ACCEPTANCE_SHA256` gepinnt. Kein Hash wird aus einem ungeprüften späteren State abgeleitet. Der alte `training_head` bleibt historisch; der spätere Leistungs-HEAD wird separat aufgenommen. Die historischen Originalvalidatoren werden nach einem HEAD-Wechsel nicht erneut als gültige zeitgenössische Trainingsprüfung dargestellt.

Minimaler vorgeschlagener Vertrag (Werte in spitzen Klammern sind **Schemahinweise, keine erfundenen Ergebnisse**):

```text
schema_version: 1
status: PASS
profile: sampled_target_20261108
eligible_for_performance: true
root: <absoluter damaliger Repo-Pfad>
training_head: <damaliger tatsächlicher 40-Hex-HEAD>
source: <vollständige damalige SourceIdentity mit head/files/runtime>
protected: {<absolute geschützte Pfade>: <SHA256>}
prepared: <absoluter Studien-Prepared-Pfad>
prepared_manifest_sha256: <SHA256>
totals:
  technical_games: 4
  prefill_games: 160
  train_games: 640
  training_executions: 800
  updates: 96000
supervisor: {path: <absoluter Endstate>, sha256: <SHA256>}
seed_acceptance: {path: <absolute Abnahme der sechs Kohorten>, sha256: <SHA256>}
technical_acceptance: {path: <Root-Abnahme der vier Technikspiele>, sha256: <SHA256>}
original_validation: {path: <Originalvalidator-Ergebnis>, sha256: <SHA256>}
independent_audit: {path: <unabhängige Datenabnahme>, sha256: <SHA256>}
paired_prefill:
  "45": {path: <absolutes Gate>, sha256: <SHA256>}
  "46": {path: <absolutes Gate>, sha256: <SHA256>}
arms:
  <jede der vier Rollen>:
    receipt_path: <absolutes final_receipt.json>
    receipt_sha256: <SHA256>
    checkpoint_path: <absolutes final/agent.pth>
    checkpoint_sha256: <SHA256>
files: {<alle referenzierten absoluten Input-/Beleg-/Rohdateipfade>: <SHA256>}
```

`files` muss sämtliche finalen Receiptartefakte (derzeit14 je Arm), Receipts, Vorlaufgates, Preparedmanifest/Launchmarker/initial.pth, ursprüngliche Inputs sowie die referenzierten Review-/Seed-/Technik-/Original-/unabhängigen Belege binden. Die JSON/Markdown-Prüfbelege vor der Abnahme unter dem Repo archivieren; `historical_path` rebasiert Repoartefakte und die bereits bekannte primäre geschützte Kopie, akzeptiert keine frei wechselnden externen `/tmp`-Belege. Die Seed-Abnahme enthält weiterhin alle sechs festgelegten Listen und verweist auf Rawscan sowie nichtleere Grenzen; weder die bekannten technischen4242-Spiele noch seedlose/externe Daten werden als garantiert frisch ausgegeben.

`original_validation` wird so erwartet:

```text
status: PASS
training_head: <gleicher historischer HEAD>
validator: scripts.sampled_target_study.validate_final_receipt
arms:
  <jede Rolle>: {status: PASS, receipt_sha256: <genauer Receipt-SHA>,
                games: 200, updates: 24000, env_steps: 120600}
```

`independent_audit` kann ein schmaler Root-Wrapper um tatsächliche unabhängige Berichte sein; der Wrapper und die zugrundeliegenden Berichte müssen alle in `files` stehen. Erwartet: `status: PASS`, `training_head` und `receipt_sha256: {jede Rolle: genauer Receipt-SHA}`. Zusätzliche Felder sind erlaubt. Das ist keine Erlaubnis, einen fehlenden oder gescheiterten Audit mit PASS zu versehen.

`technical_acceptance` ist die ursprüngliche Root-Abnahme mit `status: PASS`, `profile`, `games: 4` und den vier tatsächlich gebundenen Receipts. Der technische Endstate, tatsächliche Belege und Auditberichte werden in der historischen Gesamtinventur erhalten. Erst diese vollständig gebundenen Istwerte dürfen den Trustanker ersetzen.

## Gates und Interpretation

Score=(Siege+0,5×Remis)/Spiele; strikte Siege separat. Ganzzahl `half_wins=2×Siege+Remis`. Je Start muss der Sampled-Panelgewinn positiv sein; Summe beider Panelgewinne mindestens16 Halb-Siege (= mittlerer Panelgewinn≥5 Prozentpunkte). Direkt je Start mindestens40 Halb-Siege (=50 Prozent), zusammen strikt mehr als80. Exakte Grenztests sind als Text vorhanden.

Pro Start und Gegner sowie für Panel/Direktduell vollständige20 Kartencluster; Bootstrap5000, PCG64 seed0,95-Prozent-Perzentile. Das beschreibende Mittel über beide Starts zieht dieselben Karten gemeinsam über Starts, Seiten und Gegner. Zwei feste Starts belegen keinen Effekt über eine Trainingspopulation. Unadjustierte Intervalle, keine Leistungs-/Promotionsgarantie. Bestehen ist nur ein Methodenhinweis; Verfehlen oder Unklarheit erzeugt keinen Nachschlag und keinen weiteren automatischen Versuch.

## Späterer Aufruf, ausdrücklich noch nicht ausgeführt

Nach Root-Review, Freigabe gezielter synthetischer Tests, historischer Trainingsabnahme und Installation außerhalb eines aktiven Freeze:

```sh
python -B -m pytest -q tests/test_sampled_target_performance.py
python -B -m scripts.sampled_target_compare build
python -B -m scripts.sampled_target_compare prepare-plans
python -B -m scripts.sampled_target_eval start --jobs <jobs.json> --admission <admission.json> --out <neues Ergebnisverzeichnis> --python <Interpreter> --expected-head <Leistungs-HEAD> --usage-file <frischer Kontingentbeleg>
python -B -m scripts.sampled_target_eval analyze --jobs <jobs.json> --results <Ergebnisverzeichnis> --out <neues Bericht.json>
```

Der letzte Aufruf akzeptiert nur den abgeschlossenen400-Spiel-Block mit exakt zehn CSVs/Receipts, tatsächlichen Befehlen und vollständigen Modell-/Quellen-/Inputbindungen. Vor echten Läufen müssen die vorbereiteten Tests tatsächlich ausgeführt und eventuelle Befunde behoben werden. Dieser Bericht behauptet weder Syntaxgültigkeit noch PASS.
