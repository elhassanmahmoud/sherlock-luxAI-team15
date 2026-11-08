# Folgeaktions-Pilot: kein belegter Vorteil, V14 bleibt

Stand 08.11.2026. Alle 400 festgelegten Leistungsspiele sind vollständig und unabhängig geprüft. **Der neue Lernansatz erfüllt vier von sechs Auswahlbedingungen nicht.** Die Studie ist geschlossen; keine Verlängerung, Auswahl eines anderen Zwischenstands oder Übernahme in V14.

## Was tatsächlich gelernt wurde

Vier einzelne Netze wurden aus derselben V14-Komponente 18 nachtrainiert: zwei Kontrollnetze mit Double-DQN und zwei mit einem SARSA-artigen Replay-Ziel aus der tatsächlich übergebenen Folgeaktion. Je Paar gleiche Startbedingungen und Karten-/Gegnerfolge. Alle Regeln und Belohnungen waren innerhalb der Paare gleich. Insgesamt 160 Vorlauf- und 640 Lernspiele, 96.000 Lernupdates; vier bekannte Technikspiele separat. [Vollständiger Trainingsbericht](../sampled_target_20261108/TRAININGSERGEBNIS.md).

Es handelt sich um historische Folgeaktionen aus dem Replay, nicht um streng on-policy SARSA. Eine technisch korrekte Umsetzung beweist keinen Spielstärkegewinn.

## Vollständige Ergebnisse

„Kontrolle“ bezeichnet das entsprechend nachtrainierte Einzelnetz, **nicht V14s Ensemble**. Keine Remis oder ausgeschlossenen Spiele.

| Trainingsstart | Gegner / Vergleich | Folgeaktionsnetz | Kontrolle |
|---|---|---:|---:|
| 45 | Solution92 | 37/40 | 35/40 |
| 45 | sol92_sq | 32/40 | 32/40 |
| 45 | beide Gegner zusammen | 69/80 | 67/80 |
| 45 | direkt gegeneinander | 20/40 | 20/40 |
| 46 | Solution92 | 35/40 | 34/40 |
| 46 | sol92_sq | 32/40 | 34/40 |
| 46 | beide Gegner zusammen | 67/80 | 68/80 |
| 46 | direkt gegeneinander | 14/40 | 26/40 |

Die beiden Gegner verwenden dieselben 20 Karten (9930000–9930019), jeweils beide Seiten; die Direktduelle 20 getrennte Karten (9930100–9930119). Insgesamt 320 Gegnervergleiche und 80 Direktspiele, nicht 400 verschiedene Karten.

Mittlerer Panelunterschied über die zwei festen Starts: **+0,625 Prozentpunkte**, deskriptives 95-%-Intervall **−8,125 bis +11,875**. Direkt zusammen **34/80 = 42,5 %**, Intervall **30 bis 55 %**. Für jedes Intervall werden ganze Karten mit beiden Seiten und gegebenenfalls Gegnern/Starts gemeinsam gezogen: 5.000 Bootstrapziehungen, PCG64-Seed 0. Nur 20 Kartencluster je Kohorte; die zwei festen Trainingsstarts bilden keine Trainingspopulation ab. Die Intervalle sind nicht für Mehrfachvergleiche korrigiert.

Vorab verlangt waren positive Panelgewinne in beiden Starts, im Mittel mindestens fünf Prozentpunkte, sowie direkte Scores je mindestens 50 % und zusammen über 50 %. Nur der positive Panelgewinn und die direkte 50-%-Quote bei Start 45 bestehen. Kein belastbarer Methodenvorteil; daraus folgt auch kein allgemeiner Beweis, dass Folgeaktionslernen schlechter wäre. **Kein V14-Leistungsvergleich und kein Fortschritt zu allgemein 100 % gegen Solution nachgewiesen.**

## Prüfungen und Herkunft

- Leistung unter eingefrorener Quelle `153d2af974d7fa4ce1a9dbc318b1cb2dade5be2b`; alle zehn Jobs Exit 0. Historische Trainingsquelle `945e1938a1fb1fcc87eeaf10b58138a409266581` separat gebunden.
- [Originalauswertung](performance_v1/summary.json), SHA-256 `e39e2b7dd7c04398393668c60d65e81aa1b9a91ff3c68096a25c5ad55b4e5c25`.
- [Unabhängiger Audit](performance_v1/independent_audit.json), SHA-256 `44b1ad404e0603ef89adab5558ad157d89c2bfe3eddd3aa9bf567cc9102ff756`: sämtliche 400 CSV-Zeilen, Befehle, Modellkopien, Berechnungen und sechs Gates geprüft. PASS bezieht sich auf Datenqualität und Nachrechnung, nicht auf Spielstärke.
- [Root-Abschluss](performance_v1/closure.json): 547 Datei-/Eingabebindungen unverändert, alle zwölf eigenen Prozess-/Gruppen-IDs beendet. Erst danach Quellenfreeze freigegeben und zurückgestellte Dokumentation übernommen.
- Die Originalanalyse wurde zunächst bei relativer Übergabe des Provenienzpfads gesperrt; der absolute Aufruf bestand mit unverändertem Originalcode. Keine Ergebnisdatei wurde überschrieben und keine Daten angepasst. Für eine Reproduktion absolute Pfade verwenden. Der erste Root-Abschlussentwurf verglich zusätzlich Metadaten mit reinen Statistiken; nach Begrenzung auf dieselben Schlüssel waren sämtliche Statistikwerte exakt gleich.
- V14-Gewichte beider Seiten unverändert: `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`. ZIP unverändert: `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`.

## Übergabe und nächster Ansatz

Modelle, Rohdaten und Berichte bleiben erhalten. Die großen historischen Replay-NPZs sind weiterhin lokal, mit [Dateiindex und Hashes](../sampled_target_20261108/operations/local-replay-files.json); ein Git-Pull allein reicht für den vollständigen historischen Lernaudit auf einem anderen Rechner nicht aus.

Dieser Pilot wird nicht verlängert. Separat wird zunächst ohne neue Spiele geprüft, ob die zwölf bestehenden öffentlichen Targeting-Traces überhaupt sinnvolle Gelegenheiten für ein Vorhalten auf bewegte Gegner zeigen. Ein Netz entscheidet derzeit zwischen sechs Aktionsarten; die konkrete SAP-Zielkoordinate stammt aus Helfern. Mehr Netze allein erweitern diese Aktionsausgabe nicht. Ob eine Bewegungsprognose hilft, ist noch offen; ihre Geometrie, fehlende Folgebeobachtungen und die Wirkung auf andere Ziele müssen vor jedem neuen Training geklärt werden. Keine neue Agentenregel oder Übernahme aus diesem Vorschlag.
