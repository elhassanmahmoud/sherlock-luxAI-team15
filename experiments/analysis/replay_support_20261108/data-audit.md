# Unabhängiger Datenabschluss: Replay-Abdeckung

**PASS — 41.002 Prüfungen, 1,713 Sekunden, Exit 0.**

Eigenständiger Auditor `/tmp/replay-support-data-audit.py`; Ergebnis `/tmp/replay-support-data-audit.json`. Kein Import oder erneuter Lauf von `support.py`, keine Modelle, Forward-Pässe, Spiele oder Tests. Nur gespeicherte NumPy-Zahlen; ein Thread, vier Puffer nacheinander mit 8192-Zeilen-Streams. Repository unverändert.

| Arm | Gewinner im passenden aktuellen s beobachtet | Gewinner dort nicht beobachtet | Kein s-Treffer / unbekannt |
|---|---:|---:|---:|
| control41 | 1959 | 541 | 0 |
| neutral41 | 1992 | 508 | 0 |
| control42 | 2010 | 490 | 0 |
| neutral42 | 2020 | 480 | 0 |
| Gesamt | 7981 | 2019 | 0 |

Alle 10.000 Berichtszeilen und sämtliche Einzelwerte vollständig unabhängig rekonstruiert: Arm-/Mitgliedszuordnung 36/38/37/39, Originalindex, Featurehash, legaler Q-Gewinner, Abstand zum zweitbesten legalen Wert, sechs Aktionshäufigkeiten, Treffer-/Gewinnerzähler, bedingter Anteil und Kategorie. Für die Histogramme wurden **alle 1.200.000 aktuellen s-Zeilen** der vier Originalpuffer erneut gestreamt und ausschließlich die tatsächlichen Aktionen ihrer jeweiligen aktuellen Zeile gezählt. Kein a[i+1]-Link und keine nachgebildete Folgeaktion.

Bank-ns, next_mask und done wurden an jedem der 10.000 gespeicherten Originalindizes gegengeprüft. Alle 10.000 Bankübergänge sind nichtterminal; null terminale Bankzeilen. Puffer-, Bank-, Q-Ausgabe- und Metadatenhashes stimmen vor und nach der Nachrechnung. Root-Freigabe, freigegebene Skript-/Spec-/Bindingbytes sowie die Berichtsbindungen stimmen. Alle vier Armzusammenfassungen und Gesamtzählungen stimmen exakt.

Grenzen: Es wurden gespeicherte Endnetz-Q-Werte geprüft, keine historischen Online-/Targetwerte oder Netz-Forward-Pässe. Bytegleiche 79 Merkmale belegen keinen identischen vollständigen Belief-/Regelzustand. Die Zeilen sind korreliert, aus einem endlichen teilweise überschriebenen Replay und rein deskriptiv. Die 2019 nicht beobachteten Gewinner beweisen weder Unmöglichkeit noch falsche Q-Werte oder einen Stärkeverlust; die 7981 beobachteten Gewinner beweisen keine Aktionsqualität. Keine TD-, Kausal- oder Stärkeaussage. Der ursprüngliche Sampler-RNG bzw. historische Trainingsablauf wurde nicht erneut ausgeführt.
