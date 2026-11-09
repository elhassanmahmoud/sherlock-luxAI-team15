# Unabhängige Nachrechnung: 120 SAP-Vorhalte-Spiele

**Datenprüfung PASS; vorab festgelegter Screen nicht bestanden.** 09.11.2026. Das zuvor vorbereitete unveränderte Prüfskript wurde erst nach Abschluss aller drei Jobs und der Root-Originalanalyse ausgeführt: Exit 0, **5.404 erfolgreiche Prüfungen**, 0,33 Sekunden. Keine neuen Spiele, Modelle, Forwards, Tensorloads, Projekthelperimports oder Tests.

| Vergleich | W/D/L | Score | Deskriptives 95%-Kartenbootstrapintervall |
|---|---:|---:|---:|
| OFF gegen Solution_92 | 39/0/1 | 97,5 % | 92,5–100 % |
| ON gegen Solution_92 | 40/0/0 | 100 % | 100–100 % |
| ON direkt gegen OFF | 18/0/22 | 45 % | 30–60 % |

Gepaarter Solution-Kontrast: **+2,5 Prozentpunkte**, Intervall **0 bis +7,5 Prozentpunkte**. Eigene Berechnung mit 5.000 Ganzkarten-Bootstrapziehungen, PCG64/Seed 0, beiden Seiten je Karte und gepaarten Panelrollen. Je Block nur 20 Kartencluster.

Alle drei Originalgates bestätigt: **14 exponierte Panelkarten** erfüllen mindestens fünf; ON-Solution 40/40 ≥ OFF 39/40; Direkt **2W+D = 36 < 48**, daher verfehlt. Die tatsächlichen Änderungsereignisse ergeben OFF-Panel 0, ON-Panel 917, Direkt-ON 430. Folglich `eligible_for_separate_design=false`, `promotion=false`: Dieser Screen schließt gemäß Plan ohne Nachschlag; V14 bleibt.

Das degenerierte ON-Intervall `[1,1]` entsteht, weil jede beobachtete Karte ausschließlich Siege enthält und der empirische Bootstrap nur diese Karten wiederzieht. Es ist **keine garantierte 100%-Siegquote**, kein allgemeiner Stärkenachweis und kein Nachweis fehlender Unsicherheit außerhalb dieser Stichprobe.

Geprüft wurden genau drei Rohdateien mit je 40 festen geordneten Spielschlüsseln, alle Spielausgänge aus Matchsiegen, vollständige Match-/Punktesummen, 303 Schritte und null abgefangene Fehler. Sämtliche Receipt-/Rohdateihashes, tatsächlichen Befehle, vollständiger Owner-State mit drei Exitcodes 0 und leerem `active`, Quellen-/Configgleichheit innerhalb der Aufnahme und Originalsummary stimmen. Alle gespeicherten Änderungsereignisse wurden gezählt und auf genau einen SAP-Offsetwechsel bei unveränderten übrigen Zeilen/Aktionsklassen geprüft. Kein erneuter umfassender Quellen- oder Technikframeaudit.

Messquelle: `4b11f8a5ec61c63756bdab00748dd6779a2f2e61`. Maschinenlesbarer Bericht mit vollständigen Eingangshashes: `/tmp/sap-leading-performance-data-review.json`, SHA-256 `68d308228e987efaf093af27344e0a63dd5e7307dadaa1d36f889d98f4f822a0`. Prüfer: `/tmp/sap-leading-performance-data-check.py`, unverändert SHA `dfb3d9d918e8f826126b1d1c1e8ab7975a0516fc70d0d33760b31a2a861e812e`.

Tatsächlicher Aufruf: `env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B /tmp/sap-leading-performance-data-check.py`.
