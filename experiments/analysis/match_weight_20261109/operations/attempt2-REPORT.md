# Manuelle technische Ersatzaufnahme: enger Änderungsbeleg

Basis: a96ddebacc57d44945fe925f259ec72ddd58a02b. Geschrieben wurden ausschließlich scripts/match_weight_study.py und tests/test_match_weight_study.py.

output_dir akzeptiert ausschließlich ganzzahliges attempt 1 oder 2 (fehlend = 1) und den passenden stage_v1/stage_v2-Pfad. Für attempt 2 ist restart_reason=monitor_timestamp_format nötig sowie ein durch die Aufnahme gebundener interruption_closure. Der Beleg muss Profil und Status INCOMPLETE_MONITOR_TIMESTAMP_ERROR tragen, beide Originalprozesse beendet und ursprüngliche Bindungen gültig bestätigen sowie für control und match jeweils exakt 40 Vorlauf-, 75 Lernspiele und 11.250 Updates ausweisen. Der historische Quellstand wird nicht gegen den neuen HEAD neu aufgenommen. Diese Prüfung ist auch Teil der vorhandenen admission-Funktion, die output_dir bereits zwingend aufruft.

Keine Änderung an Agent, Reward, Config, Karten, Initialisierung, Replay, 400er-Lernschleife, manueller Vorlauffreigabe oder Phasenfolge. Keine automatische Wiederaufnahme. Kein Schreibzugriff auf v1-Artefakte; Tests prüfen einen erhaltenen v1-Sentinel und keinen durch die Pfadprüfung erzeugten v2-Ordner.

Tatsächliche Tests, primärer Projektinterpreter, -B, PYTHONDONTWRITEBYTECODE=1 und alle vier Threadvariablen=1:
- RED: pytest -q -p no:cacheprovider tests/test_match_weight_study.py -k attempt: 2 FAIL, 1 PASS, 22 deselected; fehlende v2-Unterstützung belegt.
- GREEN: pytest -q -p no:cacheprovider tests/test_match_weight_study.py: 25 PASS in 2,98 s. Nur diese betroffene Datei, keine komplette alte 41er-Kombination.
- git diff --check für beide Scope-Dateien ohne Befund.

SHA256:
- Studie: a0ae96aac35f5e09787bfcce26802111d92e09f69242cfced4f49abd0f062b51
- Tests: d852125736abd04553189173572e4c7cf6021991d8afcd46f90035dc2c29e186
- red.log: 26a2f6d69a18c68c256502041f924e97ebfa661d3d9020578a1c9be8b02b45eb
- green.log: 06ff91dceb6d1f487bed208c6de025da6113ef6c8165dd74acd11a4a19d7a861

Keine echten Modelle/Spiele/Trainings und keine Commits ausgeführt. Quota-Watcheränderung und tatsächliche Aufnahme liegen bei Root.
