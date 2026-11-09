# Unabhängige Rangmittel-Ergebnisnachrechnung

**Tatsächlich einmal ausgeführt: PASS, Exit0, 219937 Prüfungen.** Alle120 abgeschlossenen Spiele,123 gebundene Rohdateihashes, die drei erfolgreichen Jobabschlüsse, Zulassung/Quelle/Config und originale Zusammenfassung stimmen überein. Keine Projektimporte, Modelle, Tensorloads, Spiele oder Tests; ausschließlich JSON/JSONL, Dateihashes und unabhängige NumPy-Bootstraprechnung.

- Gegen Solution: OFF39/40 und ON39/40, jeweils97,5% mit deskriptivem95%-Kartenbootstrapintervall[92,5;100]%. Gepaarter Kontrast0Prozentpunkte[0;0]. Dieses degenerierte Intervall beschreibt nur die20 beobachteten Kartencluster; es beweist keine allgemeine Gleichwertigkeit.
- Direkt ON gegen OFF:19Siege,0Remis,21Niederlagen;47,5%[25;70]%. Feste60%-Hürde verfehlt:2W+D=38 statt mindestens48. Keine Übernahme und keine nach diesem Screen qualifizierte Bestätigung; kein belegter Stärkezuwachs.
- Exposition auf allen20Panelkarten. ON gegen Solution:5597 Schritte mit geänderter legaler Netzpräferenz,9045 betroffene Einheitenvorschläge. Direkt:5018Schritte und7723Einheitenvorschläge. OFF jeweils0. Das sind Unterschiede der legalen Ensemblepräferenzen vor nachgelagerten Regeln, keine behaupteten Änderungen finaler Befehle.
- Expositions- und Solution-Gate erfüllt, Direktgate verfehlt. Bootstrap unverändert: ganze Karten mit beiden Seiten, gepaarter Panelkontrast,5000Ziehungen,PCG64Seed0,Perzentile2,5/97,5;20Kartencluster jeBlock, unadjustierte deskriptive Unsicherheit.

Die Ereignisprüfung bindet Schritt-/Einheitenzähler an gespeicherte tatsächliche Roh-/Rangmittel, legale Masken und eindeutig geordnete IDs. Sie zählt die kleinste legale Aktions-ID bei einem Maximum unabhängig nach. Keine36-Mitglieder-Rangrekonstruktion aus technischen Traces und kein neuer breiter Quellenaudit.

Separat bestätigt: beide V14-Gewichte und Gruppe15.zip bytegleich, tatsächlicher HEAD `32772fd971c1e65338b476438deda9f4aac9969b` weiterhin gleich zur Quellenaufnahme. Nur drei Datei-SHA-256-Prüfungen und aktueller Commit; keine Tensorarchive deserialisiert.

Tatsächlicher Aufruf:

`env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B /tmp/rank-mean-data-review/performance-data-check.py`

Belege: `execution.log`, `performance-data-review.json`, `protection-check.json`; unveränderte Vorbereitung in `preparation.json` und `adaptation.diff`.
