# R3 und Mahmouds Hybrid auf denselben Solution-Karten

Der unabhängige R3-Vergleich ist abgeschlossen. Die 119 von 120 Siegen auf dessen Karten und die 194 von 200 Siegen von Mahmouds v3-Hybrid auf Dev A lassen sich wegen der verschiedenen Karten nicht direkt vergleichen. Für die gemeinsame Entwicklungsarbeit soll derselbe eingefrorene R3 die vollständigen 100 Dev-A-Karten 7150000 bis 7150099 auf beiden Seiten gegen Solution spielen. Die schon veröffentlichten 188/200 von V14 und 194/200 des v3-Hybrids sind die Referenzen. Die Karten waren dem Team für andere Kandidaten bekannt. Dieses Ergebnis wird als Entwicklungsvergleich gekennzeichnet und ändert die abgeschlossene unabhängige Freigabeentscheidung nicht.

1. Acht V14-Partien auf den ersten vier Karten reproduzieren. Matchsiege und -niederlagen, Punkte beider Seiten, Spielschritte und Sieger müssen pro Sitz exakt mit der veröffentlichten V14-Tabelle übereinstimmen. Bei Abweichungen zuerst die Ursache klären.
2. Den R3-Bewegungsberater der unabhängigen Bestätigung mit festem Checkpoint und identischen Quellen gegen Solution auf allen 200 Spielschlüsseln laufen lassen. Der vollständige v3-Schüler wird anhand von Mahmouds veröffentlichten Partiezeilen einbezogen. Die ursprünglichen Gewichte dieses Schülers liegen hier nicht vor.
3. Siegzahlen, gewonnene Einzelmatches und wechselseitig gedrehte Spiele für R3 gegenüber beiden Referenzen ausweisen. Das gepaarte 95-%-Intervall wird über ganze Karten gezogen, jeweils mit beiden Sitzen, 10.000 Ziehungen mit Startwert 2711. Berichten, in welchen konkreten Partien jeweils die andere Strategie gewinnt. Ein Ergebnis nach Auswahl des richtigen Agenten anhand des bekannten Siegers wäre nur eine theoretische Obergrenze.

Vor Beginn festgelegte Dateien aus [Mahmouds Auswertung](../kaggle3_20261115/) und ihre SHA-256-Werte:

| Datei | SHA-256 |
|---|---|
| seeds_devA.json | 18f39c9d86a6809a4ac6008bf43143ea29bb86fd17709d35984ac6b9615acb8d |
| v14_ref_devA.csv | 589ebf326adbb2535bd0079b603d914a47b7b2987b2bdf8dd83ba9c2bcefb25f |
| student_hyb_v3_points.csv | 0ef267b05fddf6816485d696e0794ba6b28cd13e056585db3d6e39dde5444e64 |
| R3-Schüler | 99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9 |

Mahmoud hat die v4-Ergebnisse vor dem ersten R3-Lauf auf Dev A veröffentlicht. Wir berichten zusätzlich den gemischten v4-Hybrid auf denselben vollständigen 200 Solution-Schlüsseln. Seine gemessene Quote ist 194/200. Das erfordert keine zusätzlichen Spiele. Quelle ist `student_hyb_v4_mixed.csv` mit SHA-256 `dab8ad9200433eb46b311992ef940e8110aeaf520ef4b1995b81b7403b80381c`. Die bestehende Auswertung gegenüber V14 und v3 bleibt erhalten. [v4-Daten](../kaggle3_20261115/student_hyb_v4_mixed.csv).
