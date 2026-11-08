# Fog-Reward: gezieltes Nachtraining von Sherlock

**Nachtraining technisch abgeschlossen und unabhängig geprüft; noch kein Spielstärkenachweis.** V14 und die abgegebene ZIP bleiben unverändert. Der Vergleich der festen Kandidaten wird separat durchgeführt.

## Was wir untersuchen

Sherlock kann aufgrund seiner Karteninformationen auch auf ein nicht sichtbares Ziel schießen. Für den vorhandenen Fog-SAP-Pfad wird als Trefferschätzung bisher die Zahl null gespeichert. Im Training führt das zu demselben Hit-Shaping-Abzug wie eine nichtpositive Trefferschätzung aus dem normalen Schussplaner. Der tatsächliche Treffer ist bei diesen Nebelschüssen jedoch unbekannt.

Das ist zunächst eine Hypothese über ein Lernsignal: Ein vorsichtiger Abzug für ungewisse Schüsse könnte durchaus sinnvoll sein. Wir behaupten deshalb weder einen bewiesenen Fehler in der Spielstärke noch einen schon erreichten Vorteil durch die Änderung.

Die neue Option lässt ausschließlich den Hit-Shaping-Term eines nachweislich final ausgeführten Fog-Schusses weg. Andere Reward-Anteile bleiben erhalten, einschließlich Punkte, Energie, Tod und Matchausgang. Andere SAP-Schätzungen behalten ihren bisherigen Bonus oder Abzug. Bei einem solchen unbekannten Schuss beträgt der Unterschied zum bisherigen Reward genau +0,3, sofern Shaping aktiv ist.

## Was unverändert bleibt

Aktionen, Zielwahl, Aktionsmaske und Regeln folgen demselben Ablauf. Die neue Herkunftsmarkierung wird erst für die tatsächlich ausgegebene Aktion festgehalten; spätere Zielersetzungen oder abgebrochene Schüsse übernehmen sie nicht. Die Option ist standardmäßig ausgeschaltet. Sie ist eine Trainingsoption und keine neue Regel, die während der Auswertung eine Aktion erzwingt.

Vier vollständige bekannte V14-Ausführungen auf beiden Spielseiten haben mit ausgeschalteter und eingeschalteter Option exakt dieselben 1.212 Schritte wie die alten Referenzen erzeugt: beide Agentenaktionen, Beobachtungen, Enginezustände und Punkte stimmen überein. Diese Inferenzprüfung prüft keine Lernupdates.

## Wie der Versuch aufgebaut ist

Alle vier Arme starten mit derselben Komponente 18 des ursprünglichen V14-Ensembles, demselben Q-/Target-Netz und einem frischen Optimierer und Replay-Speicher. Für die Zufallsstarts 41 und 42 gibt es jeweils eine Kontrolle und eine Neutral-Variante. Innerhalb eines Paares unterscheidet sich nur die neue Reward-Option.

Je Arm sind 40 Vorlaufspiele ohne Lernen, 400 Lernspiele sowie 16 anfängliche und 16 abschließende Diagnosepartien festgelegt. Die Gegnerverteilung beim Training wird mit 60 % Solution92, 20 % sol92_sq und jeweils 10 % default und rush gezogen. Die tatsächlich gezogenen Gegner stehen in den Rohdaten. Es wird ausschließlich der Endcheckpoint verwendet.

Vor den ersten Gradienten muss jedes Paar übereinstimmende vollständige Vorläufe nachweisen. Der Audit prüft dabei auch die Rewards, die tatsächlich in den Replay-Speicher gelangen. Der zweite Start verwendet andere festgelegte Trainingskarten. Diagnosepartien sind keine unabhängige Bestätigung einer höheren Spielstärke.

## Bereits belegte Ergebnisse

- 145 gezielte Werkzeug-/Agententests bestanden; unabhängige Code- und Integrationsreviews ohne Blocker.
- Beide Vorlaufpaare unabhängig geprüft. Start 41: je 40 Spiele, 144.264 Replay-Übergänge und 615 unbekannte finale SAPs. Start 42: je 40 Spiele, 143.087 Übergänge und 411 entsprechende SAPs.
- Die paarweise übereinstimmenden Vorläufe änderten weder Q-/Target-Parameter noch Optimierer und enthielten keine Lernupdates. Die zusätzlich wirksame Rewardmasse betrug bei Neutral 184,5 beziehungsweise 123,3; bei Kontrolle null.
- Alle vier Arme haben jeweils 400 Lernspiele, 32 Diagnosepartien und 60.000 Updates abgeschlossen. Insgesamt wurden 1.888 Spielausführungen einschließlich Vorlauf und Diagnose sowie 240.000 Lernupdates ausgeführt.
- Nach Ende aller Worker hat ein unabhängiger Audit die vier Start- und Endcheckpoint-Dateien tatsächlich geladen: Q, Target und Adam sind endlich, verändert und vollständig. Rohdaten, Reihenfolge, Reward-/Replay-Nachweise und die unveränderten Quellen bestanden die Prüfung.
- Zusätzlich hat Root alle vier ursprünglichen Abschlussvalidatoren noch unter dem eingefrorenen Trainingsstand `a3111c3` ausgeführt und eine historische, an Prüfsummen gebundene Abnahme gesichert. Erst danach wurden die zwischenzeitlichen Dokumentationscommits übernommen. Alle eigenen Trainings- und Wachhalteprozesse sind beendet.

## Wie wir Spielstärke anschließend prüfen

Nach vollständiger Abnahme werden zwei festgelegte Ensembles gebaut: die 36 ursprünglichen Netze plus beide Kontrollnetze sowie die 36 ursprünglichen Netze plus beide Neutral-Netze. Kein einzelner Trainingsstart wird nach seinem Ergebnis ausgewählt. Beide Ensembles verwenden die ursprüngliche V14-Inferenzkonfiguration.

Der vorab festgelegte Vergleich beginnt mit 440 Spielen: je 40 Spiele pro Modell und externem Gegner sowie je 40 direkte Duelle der Kandidaten gegen V14. Beide neuen Ensembles können sich nach denselben Regeln qualifizieren. Nur ein qualifizierter Kandidat erhält anschließend höchstens eine getrennte Bestätigung auf frischen Karten. Der Gesamtumfang ist auf 1.640 Leistungsspiele begrenzt; die bisherigen Freigaberegeln bleiben bestehen.

Ein Erfolg der Neutral-Variante gegen V14 würde den konkreten Agentenvergleich stützen. Ohne zusätzlichen frischen Vergleich mit der Kontrolle wäre damit noch kein allgemeiner kausaler Vorteil des Reward-Eingriffs bewiesen. Ebenso beweisen 40 oder 80 Siege ohne Niederlage keine allgemeine Siegquote von 100 %.

## Nachweise

Maßgeblich sind der abgeschlossene Laufzustand in `training_v1/state.json`, die vier Laufprotokolle und Endbelege unter `experiments/runs/20261108_fog_reward_*`, die unabhängigen Prüfberichte unter `operations/` und die vorab festgelegten Spezifikationen. Geschlossene frühere HOLD-, SAP0- und Ensemble-Versuche werden nicht nachträglich umgedeutet oder wiederholt.

Die ursprünglichen und finalen Gewichte, Rohprotokolle und Abnahmen sind versioniert. Die vier großen Replay-Puffer bleiben lokal und werden für den Inferenzvergleich nicht benötigt. Ihre historischen Prüfsummen bleiben im unabhängigen Audit erhalten. Die vollständige lokale Abnahme lässt sich deshalb aus einer frischen Git-Kopie ohne diese Puffer nicht in jedem Detail wiederholen; Modelle, Rohzeilen und die historische Prüfentscheidung sind jedoch nachvollziehbar.
