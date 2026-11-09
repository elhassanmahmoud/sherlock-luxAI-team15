# Isolierter Matchgewichtsvergleich

Vorab festgelegte Frage: Verbessert das bestehende Matchreward-Gewicht 20 statt 2 das Nachtraining eines ursprünglichen V14-Netzes? Andere Rewards und Regeln bleiben innerhalb jedes Paars gleich. Ein höheres Trainingsreward ist kein Ergebnisnachweis.

Der [Plan](../../../docs/superpowers/plans/2026-11-09-match-weight-training.md) bindet vier bekannte Technikspiele, zwei separat aufgenommene Startpaare 48/49 mit je 40 Vorlauf- und 400 Lernspielen pro Arm sowie einen späteren separaten Vergleich über 200 Spiele. Vor Gradienten wird anhand realer Replaydaten geprüft, dass ausschließlich das beabsichtigte Matchsignal abweicht. Keine automatische Phasenverkettung oder Auswahl von Zwischenständen.

## Stand

Versuch v1 unvollständig durch einen Fehler in der Laufüberwachung: Nach vier akzeptierten Technikspielen und je 40 Vorlauf- plus 75 Lernspielen wurde ein falsch formatierter Kontingentzeitstempel geschrieben. Beide Worker wurden an einer Spielgrenze beendet, je 11.250 tatsächliche Updates. Zusammen 234 Ausführungen und 22.500 Updates; keine Leistungsprüfung, keine Schlussfolgerung über die Rewardhypothese.

Originale v1-Dateien und unvollständige Gewichte bleiben unverändert erhalten. Die realen Vorläufe wurden zuvor unabhängig geprüft: je 142.110 Replayzeilen, ausschließlich erwartete Rewardunterschiede. Root schloss Quellen-/Eingabebindungen und Prozessende unter a96ddeb ab. V14 und ZIP unverändert.

Der geprüfte Kontingentschreiber erzeugt Zeitstempel nun automatisch im richtigen Format. 44 gezielte integrierte Tests sowie unabhängiger Recovery-Review bestanden. Laut ausdrücklichem Plananhang folgt genau eine manuell aufgenommene technische Ersatzrunde v2 mit frischen Originalgewichten, denselben festen Karten und unverändertem 40+400-Lernumfang. Noch keine v2-Spiele. Keine automatische Wiederaufnahme und keine Auswahl unvollständiger Gewichte.

## Belege und Grenzen

- `preparation/reward-rationale.md`: vorhandene Rewardfunktion und bereits abgeschlossene Alternativen.
- `preparation/seed-review.md` und `seed-acceptance.json`: begrenzter lokaler Kartencheck ohne beobachtete Konflikte; externe, undokumentierte und bestimmte Roharchive sind nicht abgedeckt.
- `preparation/source-config.json`: akzeptierte V14-Metadaten mit heutigen Standardwerten ergänzt; vor echten Spielen zusätzlich mit der tatsächlichen Quelldatei abgeglichen.
- `scripts.match_weight_owner`: genau eine explizite Phase, maximal zwei Modellworker, kein automatischer Neustart oder Lernstart.
- `scripts.match_weight_study`: unveränderter Originalreward und Original-DDQN-Lernschritt; instance-spezifische Beobachtung der tatsächlichen Replayeinträge, manuelle Freigabe nach Vorlaufprüfung.

Erst vollständige Ergebnisdateien und deren Prüfung erlauben einen Trainingsabschluss. Auch erfolgreiches Training beweist noch keine höhere Spielstärke. Der spätere feste Vergleich prüft Original-V14 gegen zwei 38er-Ensembles: die unveränderten 36 Netze plus beide jeweiligen Endnetze. Unterschiedliche Q-Werteskalen sind dabei eine offene empirische Frage.
