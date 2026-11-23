# Beide Kurspakete auf derselben gespielten Vorgeschichte

Der V16-Schüler und das ursprüngliche R3-Paket werden aus ihren veröffentlichten ZIP-Dateien in getrennte Python-Modulräume geladen. V16 trägt die SHA-256 `0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099`, R3 die SHA-256 `8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d`. R3 sieht ab Zug null dieselben öffentlichen Beobachtungen wie V16. Nach seinem Vorschlag erhält es die gespielte Weltbefehlsmatrix. Bei Abweichungen werden die gespeicherte kanonische Aktion, Schussmerker und Trefferindikatoren anhand der gegenwärtig sichtbaren Gegnereinheiten korrigiert. Der aktive R3-Parameterschätzer erhält die wirklich gespielten Befehle. [Öffentlicher Adapter](berater.py) · [Isoliertes Laden beider Originale](../../v16_finalwoche_20261122/fruehuebergabe/staffel.py)

| Prüfung auf echten Aufzeichnungen | Umfang | Ergebnis |
|---|---:|---|
| Original-R3 auf eigener öffentlicher Spur | 160 Züge je Sitzseite | 320 identische Teampläne |
| R3 auf einer von Original-V16 gespielten Spur | 160 Züge je Sitzseite | Gleicher Folgevorschlag wie beim unabhängigen Ersetzen der Rückgabe innerhalb der nativen Aktion. Auf 261 Zügen unterschieden sich gespielte und vorgeschlagene Befehle. |
| Unveränderte V16-Steuerung mit mitlaufendem R3 bei Sicht eins | 160 Züge je Sitzseite | Alle 5.120 Einzelbefehle identisch zu den Archivbefehlen |
| Öffentliche Zulassung und Schutzregeln | 17 konstruierte Fälle je Sitzseite | Beide Positivkontrollen und alle 32 gesperrten Fälle korrekt |

Die beiden echten Sicht-1-Spuren enthielten eine zugelassene Empfehlung auf P0 bei M2-Zug 19 und auf P1 bei M2-Zug 29. Die unabhängige Referenz für R3 ersetzte die native Rückgabe **vor** dem ursprünglichen Speichern des Aktionsinputs. Sie rekonstruierte die kanonische Richtung separat und verglich den nächsten R3-Befehl, alle gespeicherten Einheitenbefehle, Schussmerker und die öffentlich erschlossene Punktekarte. [R3-Nachrechnung](technik.json) · [V16-Schattenvergleich](schatten.json) · [Schutzregeln](schutzpruefung.json)

Beim ersten Anlauf der Gegenfortsetzungen erwartete die zusätzliche Monitorprüfung fälschlich auch beim reinen V16-Schüler immer einen befüllten Parameterspeicher. Das Kurs-Speicherverfahren schreibt dort nur in einen bereits bestehenden Eintrag. Die Prüfung kontrolliert nun den optional vorhandenen V16-Eintrag und immer den aktiven R3-Eintrag sowie den kanonischen V16-Einzelbefehl. Die eine bereits vollständig geschriebene Zeile des ersten Anlaufs wurde ohne Ergebnisöffnung beiseitegelegt. Die Auswertung verwendet ausschließlich den zweiten, wieder am Anfang gestarteten Lauf mit neuer Quellenkennung. Der Agentenadapter blieb bytegleich. [Monitor und Quellenbindung](gegenrunde.py)

## Nachvollziehen

Mit der Projektumgebung gelten `PYTHONHASHSEED=0` sowie jeweils `1` für `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS` und `MKL_NUM_THREADS`. Im Studienordner lesen `archiv.py` die historischen Tabellen und `originalpruefung.py` die 96 vollständig erzeugten Spielzeilen. `nachrechnung.py` prüft die entscheidenden historischen und frischen Gruppen unabhängig nach. Die beiden Erhebungsprozesse für neue vollständige Originalspiele sind `originale.py r3` und `originale.py v16`.

Für die Gegenfortsetzungen bilden `gegenrunde.py 0` und `gegenrunde.py 1` zwei feste Arbeitslisten. Bei einer Unterbrechung wird jede vollständig geschriebene Zeile anhand ihrer Quellenkennung übernommen. `gegenpruefung.py` wertet erst nach Vorliegen aller 128 Zeilen aus, `gegencheck.py` prüft Entscheidungen und Kartenkontraste erneut in den gespeicherten Rohfenstern. Nur wenn alle vorab registrierten Kriterien bestanden sind, erlauben `pilot.py 0` und `pilot.py 1` ganze Spiele des Kandidaten im frischen 32-Karten-Panel.
