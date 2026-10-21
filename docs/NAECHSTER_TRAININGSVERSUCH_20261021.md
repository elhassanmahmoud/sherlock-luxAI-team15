# Übergabe an Mahmoud: Trainingsbefunde und nächster sinnvoller Versuch

**Stand: 21.10.2026. Studienentwurf, noch nicht implementiert oder gestartet.** Die abgeschlossenen Versuche rechtfertigen weder eine weitere langsame Exploration noch zusätzliche Netze ohne neue Hypothese. Priorität für später hat ein kontrollierter, begrenzter Tausch im Gegnercurriculum. Die unabhängige V4-Bestätigung wurde separat ausgewertet und rechtfertigt ebenfalls keinen Austausch der V3-Abgabe.

## 1. Was gemessen wurde

Drei gepaarte Starts 47–49 mit jeweils 3.000 Spielen pro Arm: identische Anfangstensoren, gleiche Karten, Gegner und V3-Konfiguration; einziger Unterschied war der Epsilon-Abfall **60.000 gegen 454.500 Schritte**. Insgesamt **18.000 Trainingsspiele**, verteilt auf sechs Einzelnetze, und **5,20 Stunden reine Trainingszeit**.

| Abschließende Greedy-Auswertung | Kontrolle | Langsame Exploration |
|---|---:|---:|
| Solution_92, Mittel über drei Starts | 61,11 % | 48,06 % |
| Default | 97,78 % | 93,89 % |

Die Sol-Differenz beträgt **−13,06 Prozentpunkte**, Kartenbootstrap-Intervall **[−19,17; −6,94]**. Alle drei Starts waren negativ: −24,17/−7,50/−7,50 Prozentpunkte. Das vorab festgelegte Methodengate wurde verfehlt. Das Intervall beschreibt Kartenunsicherheit bei diesen drei festen Starts, keine allgemeine Trainingsunsicherheit.

Auch die festen Ensembles brachten keinen qualifizierten Kandidaten: Gegen Sol erreichten V3 **85 %**, die drei neuen Kontrollnetze **75 %**, die drei langsamen **66,67 %**, V3+Kontrollnetze **85 %** und V3+langsame Netze **81,67 %**. Keine Best-Seed-Auswahl oder nachträgliche Umgewichtung.

## 2. Was den Rückstand erklären könnte — und was nicht bewiesen ist

Alle Arme spielten exakt **1.426-mal gegen Default und 1.574-mal gegen Solution_92**. Zu wenig nomineller Gegnerkontakt erklärt den Unterschied also nicht.

Die Kontrolle erreicht Epsilon 0,05 im 199. Spiel; Solution_92 beginnt erst bei Index 752. Der langsame Arm startet dort noch mit Epsilon **0,524** und erreicht das Minimum erst nach 1.500 Spielen. Exploration bedeutet hier zu 70 % geführte Zielbewegung und zu 30 % expliziten Zufall. Außerdem laufen einige Regeln nur im Greedy-Zweig. Der Versuch änderte deshalb mehr als reine Zufallshäufigkeit.

In der ersten Mischphase, Spiele 750–1499, betrugen die **Trainingsresultate gegen Sol 37,09 % gegenüber 8,52 %**; Über beide Gegner gemittelt waren es 85,40 gegenüber 61,63 Sap-Versuche je Spiel. Nach Erreichen des gemeinsamen Minimums blieb ein Rückstand: 40,70 gegenüber 32,19 %. Die finale Greedy-Auswertung zeigt beim langsamen Arm weniger bekannte Punktefelder, weniger Sap-Versuche und mehr Stacking. Ein insgesamt höherer STAY-Anteil wurde nicht beobachtet; er war in der finalen Auswertung geringer.

**Plausible Hypothese:** Die verlängerte Exploration erzeugte eine ungünstigere frühe Verhaltens- und Erfahrungsverteilung. Das beweist weder eine bestimmte Replay-Ursache noch fehlende Kampfkompetenz. Unsere Zwischenvalidierung war ausgeschaltet; aus Trainingsresultaten allein lässt sich die damalige Greedy-Stärke nicht rekonstruieren.

Die vorhandene Q-Diagnose zeigt ähnliche legale Q-Spannen und zentrierte Streuungen; sie prüft keine möglichen gemeinsamen Verschiebungen aller absoluten Q-Werte. Langsame Netze haben kleinere mediane Aktionsabstände und weniger Übereinstimmung mit V3. Diese Stichprobe stammt jedoch nur aus Kontrollbuffer 47 und berücksichtigt keine späteren Regelüberschreibungen: beschreibender Befund, kein Stärkenmaß.

## Vergleichsbasis und Rückfrage des Professors

Die heutigen 18 V3-Quellläufe sind mit **66.000 abgeschlossenen Trainingsspielen** dokumentiert: sechs Läufe à 3.000 (`rules6`), sechs à 4.000 (`sol70`) und sechs à 4.000 (`opp` mit Gegnerpool). Alle 18 Manifeste und die lückenlosen CSV-Spielindices wurden geprüft. [Herkunftsprüfung](../experiments/analysis/autonomous_20261020/training_followup_20261021/v3_training_lineage_audit.json). Das ist die Summe der dokumentierten Quelllaufbudgets, weder die gesamte Projektentwicklung noch ein neues Nachttraining. Die individuellen Quellcheckpoints liegen hier nicht vor; ihre exakte Auswahlzeit und Tensorherkunft wurden bei dieser reinen Logprüfung nicht erneut verifiziert. Der Zusammenhang mit V3 folgt dem bereitgestellten Kandidatenmanifest.

Die frühere Präsiangabe von 18.000 Basislauf-Spielen und die neuen 18.000 Explorationsspiele sind davon getrennte Mengen. Ein einzelnes neues 3.000er-Netz gegen ein bestehendes 18er-Ensemble ist kein isolierter Lernalgorithmusvergleich.

Auch der Trainingsreward ist innerhalb des Ensembles verschieden: Die sechs `opp`-Läufe haben zusätzlich `w_opp_points=1.0`; das heutige gespeicherte Inferenzconfig beschreibt nicht den Trainingsreward sämtlicher Quellnetze. Reward gibt es pro Einheit und Schritt sowie an Matchgrenzen. Punktbelohnung nutzt bekannte Feldbelegung, Sap-Reward eine heuristische Trefferabschätzung – keinen Zugriff auf verborgene echte Felder oder gemessenen Schaden. Die frühere Matchgrenzenkorrektur `reward_fix` ist vom neuen, negativ getesteten `terminal_death_potential` getrennt.

Noch offen ist der isolierte zusätzliche Nutzen der Netze unter den heutigen V3-Regeln. Die alte Netzablation bezog sich auf `old3_sym3`. Beobachtete Aktionsüberschreibungen können diesen Vergleich vorbereiten, beweisen aber weder den kausalen Netzbeitrag noch, dass Regeln ohne Netze genauso gut spielen würden.

## 3. Genau eine priorisierte spätere Studie

**Hypothese:** Begrenzter früher Kontakt mit Solution_92 hilft während der ursprünglichen Exploration, ohne die Default-Aufwärmphase insgesamt durch lange hohe Exploration zu verändern.

Fester Vergleich bei unverändertem schnellen Epsilon-Abfall und gleicher V3-Konfiguration:

- Kontrolle: bisheriges Curriculum mit `sol92_frac=0.7` und `pool_frac=0`, 3.000 Spiele. Der allgemeine Protokollstandard ohne diese Parameter wäre ein anderer 50%-Mix.
- Versuch: Spielindices **100–199** gegen Solution_92 statt Default. Dafür die ersten **50 ursprünglichen Sol-Kartenpaare nach dem Warmup**, zwischen Indices 752 und 893, gegen Default spielen. Gesamtzahlen bleiben exakt gleich; ab Index 894 ist die Gegnerfolge wieder identisch.
- Drei frische gepaarte Initialisierungen, beispielsweise erneut die festgelegten Starts 47–49. Keine alten Gewichte oder Buffer fortsetzen. Diese wären bekannte Trainingsstarts, keine neue unabhängige Startpopulation.
- Kleine, feste Greedy-Zwischenmessungen nur zur Diagnose; alle finalen Netze auswerten, keine Zwischencheckpoint-Auswahl. Vorab festes Methodengate: Sol-Mittel mindestens +3 Prozentpunkte, mindestens zwei positive Starts, Defaultverlust höchstens 2 Prozentpunkte. Erst danach getrennte frische Bestätigung.

Der Gegnerlabeltausch wurde rein rechnerisch geprüft. Er ist eine neue Curriculum-Hypothese, kein bewiesener Verbesserungsansatz. Er verändert auch die Zuordnung von Karten und Gegnern. Dafür später mehrere Stunden plus Auswertung reservieren, nicht kurzfristig vor einer Abgabe starten.

## 4. Was wir nicht wiederholen sollten

Mahmouds sechs neuen V3-Netze 40–45 hatten die V3-Regeln bereits im Training. Auf frischen Karten: V3 **71 %**, neue sechs **70 %**, V3+sechs **71 %** gegen Sol. Einfach mehr gleichartige Netze ist derzeit nicht begründet.

Auch `active_targets` und `sap_geometry` jetzt nicht kombinieren: Alle drei positiven Sap-Spieländerungen liegen bereits bei Active-Gewinnen; die Verluste betreffen unterschiedliche Karten. Technisch getrennte Eingriffe sind kein Nachweis positiver Synergie.

**Alternative nach Beschaffung der Originalgewichte:** CNN3 reproduzierte auf frischen Karten ungefähr den Lehrer: **73,0 % gegen 73,25 %**, Intervall der Differenz [−5,0; +4,5]. Lokal fehlen die CNN3-Checkpoints. Zuerst Originalgewichte, Hash und Konfiguration übertragen und reproduzieren; keine kostspielige Neuerstellung aus Logs. Die bisherigen Vergleiche isolieren weder CNN gegen Unitfeatures noch PPO gegen DQN bei gleichem Budget.

## Belegbare Repositoryquellen

- `experiments/analysis/autonomous_20261020/exploration_aggregate.json`, `exploration_pair_audit_s47.json` bis `s49.json`, `exploration_qmargin_diagnostic.json`.
- Die sechs Explorationsläufe unter `experiments/runs/`: `train.csv`, `val.csv`, `manifest.json`.
- `experiments/compare/autonomous_20261020/exploration_ensemble_development/state.json` und `inference_development2/phase2_*.csv`.
- `scripts/protocol.py`, `agents/sherlock/main.py:255–299`.
- `docs/ARBEITSSTAND.md`, Einträge 20.10.2026, 21:50/22:25; `experiments/compare/regeln/R3_{v3,v3nets6,all24v3}_2620.csv`.

Nur vorhandene Ergebnisse ausgewertet. Keine neuen Modelle, Spiele, Trainings oder Quellenänderungen für diese Übergabe.

## Vor einem tatsächlichen Start noch festzulegen

Der Versuch passt in das vorhandene Trainingsprotokoll; Agent, Reward, Netze und Belief müssten dafür nicht geändert werden. Ein explizit gewählter Gegnerplan, Protokolltests und eine im Manifest gespeicherte Gegnerfolge würden genügen. Die Gegnerfolge wurde jetzt rechnerisch geprüft: genau 200 geänderte Spielpositionen, gleiche Gesamtzahlen und ab Index 894 unverändert. [Prüfbeleg](../experiments/analysis/autonomous_20261020/training_followup_20261021/proposed_schedule_audit.json).

Die bestehende Validierung ist periodisch. Für kleinen Umfang wären Messungen bei 0/750/1500/2250/3000 mit acht bekannten Entwicklungskarten möglich; eine genaue Zusatzmessung bei 200 benötigt einen separaten Änderungsschritt. Vor dem Studienstart entscheiden und festhalten, keine Auswahl nach Zwischenständen. Seedbereiche für Entwicklung und unabhängige Bestätigung noch verbindlich reservieren. Starts 50 oder höher nicht in die bestehende Trainings-Seedformel einsetzen: Sie würden in den Validierungsbereich ab 500000 geraten.

Den alten Explorations-Supervisor nicht unverändert wiederverwenden: Dort wird gerade ein Epsilon-Unterschied geprüft, hier müssen beide Agentenkonfigurationen exakt identisch sein. Ausgabeverzeichnisse dürfen vor dem Start nicht existieren; ein Trainer oder höchstens zwei Evaluationsworker insgesamt. Kein automatischer Lauf auf den historischen Testkarten 900000–900029 (`--no-test`). Vor Umsetzung konkrete Tests für Gegnerzahlen, vollständige Seitenpaare, deterministische Folge und unveränderte Standardkonfiguration vorsehen. Ein vollständiger Studienplan muss außerdem Abbruchzeit, Methodengate, frische Bestätigung und Übernahmeprüfung festlegen.

Dies ist ein priorisierter Entwurf für eine nächste Arbeitssitzung, keine vorgetäuschte bereits implementierte Verbesserung. Sechs Trainingsläufe benötigten gemessen rund 5,2 Stunden, zuzüglich Zwischenmessungen, Auswertung und Reserve.
