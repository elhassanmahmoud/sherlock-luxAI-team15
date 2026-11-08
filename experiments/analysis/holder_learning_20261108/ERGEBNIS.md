# HOLD-Lernversuch abgeschlossen: V14 bleibt

08.11.2026. Der kleine Korrekturkopf wurde tatsächlich gelernt und auf vorher getrennten Karten geprüft. Er erhielt **keine Freigabe für den nächsten Spielvergleich**. Das beweist nicht, dass jeder Halteansatz wirkungslos ist; dieser feste Versuch liefert noch keinen belastbaren Vorteil.

## Was umgesetzt und gemessen wurde

Die ursprünglichen 36 V14-Netze blieben eingefroren. Ein zusätzlicher linearer Kopf nutzt 16 öffentliche Merkmale und sagt den Punktedifferenz-Vorteil eines einmaligen STAY-Vorschlags über zwölf Folgeschritte voraus. Maximal acht bewertete Gelegenheiten pro Spiel, zwölf Schritte Abstand auch nach Ablehnung. Die übrigen Regeln laufen normal weiter. Genau ein gewichteter Ridge-Fit, Faktor0,1 und feste Schwelle>1Punkt; kein Nachjustieren auf Validierungsdaten.

- Technischer neutraler Kopf: vier vollständige Ausführungen. Auf beiden Seiten je acht wirkliche Kopfaufrufe, vollständige Verläufe exakt wie V14.
- Training: 24 neue Karten, beide Seiten, Referenz+Sammler =96 Ausführungen.162 vollständige Paare auf20Karten:92 positive,50 negative,20 gleiche Label. Vier Karten lieferten keine geeignete Situation. Einmaliger Fit auf allen Labels; Normierung nur aus Training.
- Validierung: acht getrennte Karten, beide Seiten, Referenz+Sammler =32 Ausführungen.28 Paare auf sechs Karten. Der eingefrorene Kopf wählte14:10 positive und4 negative. Diese Alternativfortsetzungen sind keine14 vollständig gespielten Kandidatenpartien.

## Ergebnis und feste Entscheidung

Die ausgewählten Validierungslabels summieren sich auf+18Punkte. Der vorab definierte Kartenwert (halbe Summe je Karte über beide Seiten, inklusive Nullkarten) beträgt im Mittel+1,125; seine untere Bootstrap-Grenze beträgt−0,8765625. Dies ist ein Offline-Anhaltspunkt auf V14-Verläufen, kein nachgewiesener Gewinn einer wiederholt eingreifenden Policy.

Zwei von sechs Bedingungen verfehlt: nur28 statt mindestens32Paare und keine positive untere Bootstrap-Grenze. Die übrigen Mengen- und Mittelwertbedingungen bestehen. Deshalb **kein Refit, keine neue Schwelle, keine Zusatzkarten und kein vollständiger Stärkevergleich dieses Kopfes**. V14 und die abgegebene ZIP bleiben unverändert. Allgemeine100% gegenSolution sind weiterhin nicht belegt.

Der experimentelle Kopf bleibt unter `fit_v1/head.json` erhalten, SHA256 `0f61a4070020dab415ce02ae76f4c752533d4f97e58af7ece2bcffc09d4a8dc4`. Er ist kein freigegebener Abgabeagent.

## Tatsächlicher Aufwand und Prüfung

Dieser Lernversuch:132 vollständige Ausführungen/39996 echte Schritte,190 Alternativpaare,4560 primäre und1176 Wiederholungs-Simulationsschritte. Genau ein linearer Fit, keine neuen DQN-Netze oder RL-Updates. Die vorherige historische Einflussprobe ist separat dokumentiert und nicht in diese Daten gemischt.

Root:102 gezielte Werkzeugtests vor Spielstart. Unabhängige Reviews bestätigten Code, komplette Rohdaten, Passivität, Quelle und Kopf. Die unabhängige Nachrechnung reproduziert alle16 Merkmale, Normierung und Koeffizienten (maximale Abweichung4,22e−15) sowie Vorhersagen (2,22e−14). Validierungsbericht und feste Gateentscheidung unabhängig bis1e−12 bestätigt. Einzelbelege unter `operations/`.

Quellstand während aller Messungen und des Fits: `759c8fa1908184de04421ee9fb3547e55bf7663a`. Keine parallelen Tests, maximal ein Modellprozess. Beide V14-Dateien und Gruppe15.zip nach Abschluss erneut bytegleich; eigene Spiel-/Wachhalteprozesse beendet.

## Nächster Ansatz

Der autonome Auftrag geht weiter. Als getrennten Versuch prüfen wir die belegte Reward-Semantik: unbekannte Nebeltreffer werden bisher wie Fehlschüsse behandelt. Zunächst tatsächliche Herkunft/Trainingsnutzung prüfen, dann eine optionale neutrale Behandlung mit unveränderter Kontrolle vergleichen. Keine globale SAP0-Wiederholung, keine Änderung der V14-Abgabe aus einer bloßen Codekorrektur.
