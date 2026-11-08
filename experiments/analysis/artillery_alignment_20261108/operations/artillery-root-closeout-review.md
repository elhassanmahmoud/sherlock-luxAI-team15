# Statischer Review des Root-Abschlusscollectors

**Ein eng begrenzter Blocker; sonst Schema und Reihenfolge passend.** Kein Python-/Modell-/Testlauf, keine Repositoryänderung.

## P2: Unabhängige PASS-Berichte sind nicht an die aktuell abgenommenen Artefaktbytes rückgebunden

`/tmp/artillery-root-closeout.py` prüft bei den beiden unabhängigen Berichten lediglich Status und Trainings-HEAD. Es prüft weder deren vorhandene `files`-Hashinventare gegen die jetzigen Bytes noch deren Manifest-/Quellen-/Protected-/Arm-Receiptbindungen gegen die jetzt validierten Daten. Später werden die Berichte selbst zwar gehasht und kopiert, das macht einen älteren PASS für andere Artefaktbytes jedoch nicht zu einer unabhängigen Abnahme der jetzigen Artefakte. Derselbe HEAD und Status allein reichen dafür nicht; insbesondere die unabhängige Replay-/Tensorprüfung muss genau die nun freigegebenen Dateien betreffen.

Minimaler Fix: Vor den Originalvalidatoren für beide Reports `prepared_manifest_sha256`, `source`, `protected` sowie vollständige vier Arm-Receiptbindungen mit dem vorhandenen Manifest/Zustand abgleichen und sämtliche vorhandenen `files`-Hashes gegen die echten Dateien prüfen. Die gespeicherten Reportbytes und ihre Datei-Inventare bis unmittelbar vor Schreiben der historischen Abnahme nochmals unverändert verlangen. Kein neues Framework erforderlich; beide Reports liefern diese Daten bereits (`PASS_DATA_ONLY` / `PASS_TENSORS_AND_REPLAY`, je `files`, `arms[arm].receipt_sha256`).

## Bestätigte Teile

- Explizites `--after-supervisor-exit`, Supervisor done mit leerer Queue/active und genau vier erfolgreichen Jobs/Receipts; Wake-Aufräumfeld und Prozessprüfung vor Modellimports.
- Richtige Statusnamen: `PASS_DATA_ONLY` und `PASS_TENSORS_AND_REPLAY`; richtiger Trainings-HEAD.
- Ursprüngliche `validate_final_receipt`-Aufrufe tatsächlich unter eingefrorener Quelle vorgesehen; Source/HEAD/Protected-Prüfungen davor und danach.
- `compare_prefill_proofs(control, aligned, seed)` korrekt verwendet; beide Paarbelege samt Datei-/Supervisorbindung werden exakt verglichen.
- Sämtliche neun tatsächlichen Receiptdateien plus jeweiliges Receipt sowie vorbereitete Manifeste/Startgewichte und Supervisorstart werden gebunden. Richtige Budgets 40+400+32, 472 pro Arm, 60000 Updates und env_steps193320; Gesamt1888/240000.
- Historische Abnahme passt zum vorgesehenen Vergleichsleser. JSON/MD-Belege werden erst nach Originalvalidierung ins Repo kopiert; kein Python während des Freeze. Python-Dictreferenz `files=files` enthält auch die danach über `ref(...)` ergänzten Belege, da dieselbe Instanz gebunden wird.
