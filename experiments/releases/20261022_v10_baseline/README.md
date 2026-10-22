# Gesicherte V10-Abgabe

Bytegleiche Sicherung vor den zwei gezielten Mechanikkorrekturen vom 22.10.2026. Beide Dateien: SHA-256 `03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67`. Vollständiger ursprünglicher Agentencode: Commit `c78732f1cc0a7746268e644223692d146aa8f25e`. Die Netzparameter bleiben auch bei den Korrekturversuchen identisch.

Die neuen Schalter `sap_overkill_recovery` und `nebula_infer_drift_safe` sind standardmäßig aus; dieser Checkpoint aktiviert sie nicht. Damit bleibt V10 im neuen Code der Vergleichsstand. Keine Übernahme eines Kandidaten durch diese Sicherung.

Zur Wiederherstellung bei gestoppten Versuchen beide Dateien nach `agents/sherlock/weights/` kopieren, SHA-256 prüfen und `python -m scripts.check_candidate_runner` ausführen. Für eine vollständige historische Reproduktion den oben genannten Code-Commit in einem separaten Checkout verwenden.
