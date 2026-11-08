# HOLD-Einflussprobe: Lernen ist prüfenswert, V14 bleibt

08.11.2026, Quelle01d42794bd798ac6c90831d4ac20358187f3ea1a. Zwölf bereits bekannte, historisch nach Verlust/Kontrolle ausgewählte Spiele gegen Solution92, jeweils ein Referenz- und ein identischer Sammellauf. Keine frische Leistungsprüfung.

## Ergebnis

55 geeignete Situationen, alle mit veränderter erster Teamaktion. Ein einmaliger STAY-Vorschlag vor den normalen Regeln ergab über zwölf Folgeschritte gegenüber V14:28 positive,21 negative und6 gleiche Team-Punktedifferenzen. Positive Fälle in10Spielen; Mittel+0,418, Median+1, Spannweite−27 bis+42. Summe+23 ist keine zusätzliche echte Spielpunktzahl: Fortsetzungen sind getrennte, teils abhängige Alternativwelten. Keine pauschale Halteregel ableiten.

Vorab-Machbarkeitsfilter (>=24 veränderte Aktionen,>=6 positive in>=3Spielen) bestanden. Das belegt beeinflussbare Situationen, nicht ihre Vorhersagbarkeit und keine höhere Siegquote. Nächster freigegebener Schritt: auf getrennten Karten eine kleine öffentliche Entscheidungshilfe lernen und nur bei eigener Validierung frisch als vollständige Policy vergleichen.

## Umfang und Prüfung

- Hauptdiagnose24 vollständige Ausführungen/7272 echte Schritte;55Paare mit1320 zusätzlichen primären Simulationsschritten und264 Wiederholungs-/Reihenfolgeschritten.
- Vorher technischer Smoke4Ausführungen/1212Schritte,2Paare,48primäre+48zusätzliche Prüfschritte. Beides separat, zusammen28vollständige Ausführungen und1680zusätzliche Simulationsschritte. Keine Trainingsupdates.
- Referenz/Sammler und Baselinebranch/Livezukunft exakt identisch. Beide Seiten, Branchreihenfolge, Wiederholungen und alle Quellen-/Gewichtshashes geprüft. Root26gezielte Werkzeugtests vor Spielstart bestanden.
- Unabhängiger Datenreview PASS,70990 reine Daten-/Hash-/Arithmetikprüfungen, keine zusätzlichen Modellspiele. Siehe operations/runtime-audit.md/json für Grenzen (gespeicherte Zustandsdigests statt vollständiger Zustandsarrays; Wiederholungen durch Laufzeitassertionen belegt).

V14-Rohgewichte und Gruppe15.zip unverändert. Keine Produktionseinführung. Rohdaten unter technical_smoke_v1/ und diagnostic_v1/ vollständig erhalten; diese Diagnose nicht wiederholen/verlängern. Neue Lernstudie erhält eigenes vorab festes Protokoll.
