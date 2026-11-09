# Isolierter Matchgewichtsvergleich

Vorab festgelegte Frage: Verbessert das bestehende Matchreward-Gewicht 20 statt 2 das Nachtraining eines ursprünglichen V14-Netzes? Andere Rewards und Regeln bleiben innerhalb jedes Paars gleich. Ein höheres Trainingsreward ist kein Ergebnisnachweis.

Der [Plan](../../../docs/superpowers/plans/2026-11-09-match-weight-training.md) bindet vier bekannte Technikspiele, zwei separat aufgenommene Startpaare 48/49 mit je 40 Vorlauf- und 400 Lernspielen pro Arm sowie einen späteren separaten Vergleich über 200 Spiele. Vor Gradienten wird anhand realer Replaydaten geprüft, dass ausschließlich das beabsichtigte Matchsignal abweicht. Keine automatische Phasenverkettung oder Auswahl von Zwischenständen.

## Stand

Technische Vorbereitung vollständig: 41 gezielte synthetische Tests und unabhängiger Code-/Methodenreview bestanden; Root hat Code, Metadaten und Kartenbelege geprüft. Noch keine tatsächlichen Spiele oder Trainingsupdates dieses Versuchs. V14 und Abgabe-ZIP bleiben unverändert.

## Belege und Grenzen

- `preparation/reward-rationale.md`: vorhandene Rewardfunktion und bereits abgeschlossene Alternativen.
- `preparation/seed-review.md` und `seed-acceptance.json`: begrenzter lokaler Kartencheck ohne beobachtete Konflikte; externe, undokumentierte und bestimmte Roharchive sind nicht abgedeckt.
- `preparation/source-config.json`: akzeptierte V14-Metadaten mit heutigen Standardwerten ergänzt; vor echten Spielen zusätzlich mit der tatsächlichen Quelldatei abgeglichen.
- `scripts.match_weight_owner`: genau eine explizite Phase, maximal zwei Modellworker, kein automatischer Neustart oder Lernstart.
- `scripts.match_weight_study`: unveränderter Originalreward und Original-DDQN-Lernschritt; instance-spezifische Beobachtung der tatsächlichen Replayeinträge, manuelle Freigabe nach Vorlaufprüfung.

Erst vollständige Ergebnisdateien und deren Prüfung erlauben einen Trainingsabschluss. Auch erfolgreiches Training beweist noch keine höhere Spielstärke. Der spätere feste Vergleich prüft Original-V14 gegen zwei 38er-Ensembles: die unveränderten 36 Netze plus beide jeweiligen Endnetze. Unterschiedliche Q-Werteskalen sind dabei eine offene empirische Frage.
