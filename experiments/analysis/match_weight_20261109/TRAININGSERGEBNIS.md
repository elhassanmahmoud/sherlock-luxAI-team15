# Matchgewicht: Training abgeschlossen, Spielstärke noch offen

Vier neue Einzelnetze sind vollständig trainiert und geprüft. Zwei verwenden das bisherige Matchreward-Gewicht 2, zwei das feste höhere Gewicht 20. Ein Matchausgang wirkt damit stärker im Lernziel; alle übrigen Rewards und Trainingsregeln bleiben innerhalb der Paare gleich. **Das ist noch kein belegter stärkerer Sherlock. V14 und die Abgabe-ZIP bleiben unverändert.**

## Tatsächlich ausgeführt

| Start | Arm | Vorlauf | Lernspiele | Adam-Updates | Endmodell |
|---|---|---:|---:|---:|---|
| 48 | Kontrolle, Gewicht 2 | 40 | 400 | 60.000 | [control 48](pair48_v2/control/final.pth) |
| 48 | Match, Gewicht 20 | 40 | 400 | 60.000 | [match 48](pair48_v2/match/final.pth) |
| 49 | Kontrolle, Gewicht 2 | 40 | 400 | 60.000 | [control 49](pair49_v2/control/final.pth) |
| 49 | Match, Gewicht 20 | 40 | 400 | 60.000 | [match 49](pair49_v2/match/final.pth) |

Die akzeptierte Ersatzrunde v2 umfasst vier bekannte Technikspiele, 160 Vorlauf- und 1.600 Lernspiele: **1.764 Spielausführungen und 240.000 Updates**. Jedes Endmodell stammt ausschließlich vom vollständigen Endstand; keine Zwischencheckpointwahl. Fester Mix aus Solution, Square-Solution, default und rush, zwei unabhängige Zufallsstarts. Die genauen Karten, Folgen, Modelle und Hashes stehen in den Aufnahmen und Receipts.

## Nachweis des tatsächlichen Lernens

Vor jedem Paar wurden die realen Vorlaufreplays geprüft: Start 48 enthält je 142.110 Übergänge, Start 49 je 142.731. Zustände, finale Aktionen, Folgefeatures, Terminals und Masken waren zwischen den Rollen bitgleich; ausschließlich der vorgesehene Matchreward unterschied sich. Je Arm waren 1.757 beziehungsweise 1.768 Übergänge dem Matchsignal ausgesetzt. Der Gegenformelkontrast beträgt 18 mal die Matchsiegedifferenz, mit vorab festgelegter Rundungsprüfung und exakter Float32-Replaydarstellung.

Danach wurden die ursprünglichen wartenden Worker separat durch Root freigegeben. Beide Paare endeten vollständig. Originale Supervisorvalidatoren, unabhängige Rohdaten-/Tensor-/Adam-/Replayprüfung und Root-Prüfung der Quellen-, Datei- und Prozessbindungen bestanden. Endgewichte und Optimizerzustände sind endlich, die Lerngewichte haben sich verändert, alle Adam-Schritte entsprechen 60.000. Die eingefrorene Trainingsquelle ist `207f504cf75920e4569ef3084b6cd916df76243c`.

[Gesamtabnahme](operations/training-completion.json), [Paar 48](operations/pair48-v2-closure.json), [Paar 49](operations/pair49-v2-closure.json), [ursprünglicher Plan](../../../docs/superpowers/plans/2026-11-09-match-weight-training.md).

## Unterbrechung offen mitzählen

Versuch v1 wurde wegen eines falsch formatierten Zeitstempels in unserer Kontingentüberwachung kontrolliert abgebrochen, nicht wegen eines schlechten Leistungsresultats. Er umfasst zusätzlich vier Technikspiele, 80 Vorlauf- und 150 Lernspiele sowie 22.500 Updates. Die unvollständigen Modelle werden nicht verwendet. Alle ursprünglichen Daten bleiben erhalten. Der Kontingentschreiber wurde korrigiert; die eine ausdrücklich dokumentierte Ersatzrunde begann frisch aus den ursprünglichen Gewichten.

**Gesamte Rechenarbeit einschließlich v1: 1.998 Ausführungen und 262.500 Updates.** Diese Mehrarbeit ist kein zusätzlicher Stärkenachweis.

## Nächster festgelegter Schritt

Separater Vergleich: Original-V14 mit 36 Netzen, CONTROL38 und MATCH38 mit jeweils den ursprünglichen 36 plus den beiden passenden neuen Endnetzen. Gleiche ursprüngliche Inferenzkonfiguration, keine Übernahme der Trainingsregeln oder des Trainingsrewards in die Spielentscheidung. Zunächst tatsächliche Loader-/Zusammensetzungsprüfung ohne neue Spiele, danach separat die vorab festen 200 Leistungsspiele gegen Solution und direkt.

Der Vergleich ist hier **noch nicht gestartet**. Geänderte Q-Skalen bei stärkerem Reward sind eine offene empirische Frage; kleinerer Loss oder mehr Trainingssiege beweisen keinen Vorteil. Eine Nominierung würde erst eine weitere getrennte Bestätigung erlauben. Keine automatische Übernahme und keine Verlängerung bis zu einem gewünschten Ergebnis.
