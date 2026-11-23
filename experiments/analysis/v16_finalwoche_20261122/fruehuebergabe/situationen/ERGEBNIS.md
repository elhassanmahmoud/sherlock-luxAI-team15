# Vor der ersten abweichenden Bewegung

Eine frei sichtbare Erkundungsgelegenheit erklärte **eine der beiden** von der R3-Eröffnung geretteten Solution-Partien. Derselbe Auslöser trat aber auch auf beiden Sitzen einer Karte auf, auf der die R3-Eröffnung einen Kaggle-Sieg verlor. Das Kriterium trennt die gewünschten von den schädlichen Situationen zu diesem Zeitpunkt nicht verlässlich. Deshalb endet dieser Ansatz bei der Diagnose. Auf den reservierten neuen Karten wurden keine Spielversuche gestartet. [Vorab gebundene Frage und Prüfgrenzen](PLAN.md).

**Was war Sherlock schon bekannt?** Beim ersten unterschiedlichen Befehl in den beiden Solution-Rettungen und allen sechs verschlechterten Kaggle-Sitzen waren keine Gegner sichtbar, keine Relikte und keine Punktefelder bekannt. Alle lebenden eigenen Schiffe hatten genug Energie für eine Bewegung. Die Unterschiede traten bereits in Zug 4 bis 8 auf. Für jeden der beiden tatsächlichen Teambefehle wurde berechnet, wie viele bis dahin selbst ungesehene Felder nach einem Schritt geometrisch in Sensorreichweite lägen. Dieses Maß nutzt die damalige Spielersicht. Es enthält keine versteckte Gelände- oder Gegnerinformation und kann die wirkliche Sicht im nächsten Zug nur annähern.

| Späterer tatsächlicher Ausgang der kompletten R3-Eröffnung | Karte / Sitz | Zug | Eigene bewegungsfähige Schiffe | Bisher selbst gesehene Felder | Potenziell neue Sichtfelder V16 → R3 | Öffentlicher Auslöser |
|---|---|---:|---:|---:|---:|---|
| Solution-Sieg gewonnen | 160362065, P1 | 6 | 2 | 18 | 3 → 5 | Ja |
| Solution-Sieg gewonnen | 160362073, P1 | 4 | 2 | 12 | 3 → 3 | Nein |
| Kaggle-Sieg verloren | 160362049, P0/P1 | 6 | 2 | 15 | 5 → 5 | Nein |
| Kaggle-Sieg verloren | 160362057, P0/P1 | 5 | 2 | 11 | 7 → 4 | Nein |
| Kaggle-Sieg verloren | 160362066, P0/P1 | 8 | 3 | 23 | 3 → 4 | Ja |
| Kaggle-Sieg gewonnen | 160362030, P0/P1 | 6 | 2 | 29 | 1 → 5 | Nein, bereits zwei bekannte Reliktpositionen |

Die dargestellten Ergebnisse stammen aus dem vorherigen ganzen Vergleich. Sie folgen auf eine bis zu 40 Züge lange R3-Eröffnung und erlauben keine Zuschreibung an diesen einen Schritt. Gegen Kaggle brachte ein zusätzlicher potenzieller Sichtgewinn auf 160362066 zwei falsche Freigaben, die zweite Solution-Rettung 160362073 wäre bei identischem Umfang der potenziellen Sicht ausgeschlossen worden. Das ältere Vorwissen auf 160362030 schließt die vorab definierte *reine* Erkundungslage aus.

**Unabhängige Vorkontrolle.** Im getrennten V16-Archiv wurden 32 weitere vollständige Originalpartien auf 32 unterschiedlichen Karten wiederholt. Die Auswahl erfolgte vorab allein nach Kartennummer und öffentlichem Sensorparameter, mit beiden Startseiten und beiden Gegnern. In 17 Partien erfüllte die erste abweichende Empfehlung die Erkundungsbedingung, darunter acht bei Sicht eins und neun bei Sicht zwei. Der Auslöser ist also im normalen Spiel häufig genug messbar. Die Vorkontrolle hat seine Häufigkeit gemessen, aber keinen Gewinn einer neuen spielenden Variante.

**Prüfung.** Alle 42 Partien erreichten 303 Schritte und reproduzierten Original-Spielsieg, beide Match- und beide Punktesummen. Solange R3 und V16 dieselben Befehle gaben, folgten sie derselben echten Beobachtungs- und Handlungshistorie. Gemessen wurde erst die erste Abweichung, danach spielte das unveränderte Original-V16 zu Ende. Die 42 Einzeldatensätze sind zusammen **1.662 Bytes** komprimiert, SHA-256 `9927010e487bdd515fafc36c99fa241aa991217dab54840103cc04b0d4997917`. [Alle Beobachtungen und Befehle am ersten Unterschied](partien.jsonl.gz) · [Prüfergebnis und Häufigkeiten](ergebnis.json).
