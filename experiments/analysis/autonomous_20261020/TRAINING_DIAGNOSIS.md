# Trainingsdiagnose und Prüfung eines langsameren Epsilon-Abfalls

Stand: 20.10.2026. Quellenreview und stdlib-Auswertung vorhandener CSV/JSON; keine Modelle geladen, keine Spiele oder Trainings gestartet. Das Memo ist ein Diagnose-/Designvorschlag, keine Änderung des laufenden Versuchs.

## Gemessener Reward-Pilot und Grenzen

Der Hauptagent meldet nach striktem Abschlussaudit für den 400-Spiele-Piloten, Seed 46: Control Default **100,00 %**, Solution92 **35,83 %**; terminale Korrektur Default **88,33 %**, Solution92 **12,50 %**. Das vorab festgelegte Gate lautet `stop_and_investigate`; die Reward-Replikation 47–49 wird nicht gestartet. Diese Evalwerte stammen aus dem Abschlussaudit des Hauptagenten. Der folgende Explorations-/Rewardreview erklärt den Unterschied nicht kausal.

Unabhängig gelesen wurden je 400 Zeilen aus:

- `experiments/runs/20261020_full_rules_v3_s46_terminal_control/train.csv`
- `experiments/runs/20261020_full_rules_v3_terminal_s46_terminal_fix/train.csv`
- deren `initial_identity.json` mit effektiver Konfiguration.

Beide Arme hatten denselben Epsilonverlauf und dieselbe Gegnerfolge. Nach 100 Spielen: 30.300 Env-Schritte, Epsilon 0,5203. Erstes Solution92-Spiel: Index 102 (103. Spiel), Start-Epsilon 0,510655. Nach 198 Spielen: 59.994 Schritte, Epsilon 0,0501; im 199. Spiel wird 0,05 erreicht und bleibt konstant. Von 206 Solution92-Spielen hatten 66 einen protokollierten End-Epsilonwert über 0,05, die übrigen 140 lagen danach. Beide Trainings endeten mit 121.200 Env-Schritten und 59.792 Lernschritten. End-Loss: Control 1,18348, Fix 1,14568. Der kleinere Loss ist kein Stärkenbeleg.

## Exploration: belegte Mechanik

`agents/sherlock/main.py`, `epsilon` (Zeilen 184–189), berechnet linear

`epsilon = 1 − 0,95 × min(env_steps / eps_decay_steps, 1)`.

`update` erhöht `env_steps` pro Env-Schritt. Die Kurse haben 303 Schritte pro Spiel. `AgentConfig` setzt `eps_decay_steps=60000`, `guided_prob=0.7`, `eps_end=0.05`. Im Epsilonzweig von `act` sind 70 % der Entscheidungen zielgerichtet (`_guided_action`), 30 % uniform unter legalen Aktionen. `_guided_action` geht zum zugewiesenen Ziel und fällt bei fehlendem Schritt selbst auf Zufall zurück. Am Epsilonminimum sind daher 1,5 % der Unitentscheidungen im explizit uniformen Zweig und 3,5 % im guided-Zweig. Dies sind Zweigwahrscheinlichkeiten, keine gemessenen endgültigen Aktionshäufigkeiten: Fallbacks und spätere Regeln verändern die Aktionen.

`_explore_action` und `_rule_override` werden im Greedyzweig ausgeführt; nachgelagerte Regeln wie `pt_sap` wirken zusätzlich. Ein Epsilonvergleich verändert deshalb auch die Mischung aus Q-Policy und heuristischer Verhaltenssteuerung, nicht lediglich die Menge uniformen Zufalls.

`scripts/protocol.py`, `train_opponent`, verwendet 25 % reine Default-Aufwärmphase, danach deterministisch `sol92_frac=.7` pro Kartenpaar. Bei 3.000 Spielen liegen alle Solution92-Spiele nach 750 Default-Spielen; bei 2.000 nach 500. Mit 60.000 Decay-Schritten sind somit sämtliche Solution92-Spiele dieser längeren Läufe bereits am Epsilonminimum. Ob 5 % ausreichend sind, ist durch diese Quellen nicht beantwortet. Der identische Verlauf beider Pilotarme erklärt ihren Leistungsunterschied nicht allein.

## Terminaler Reward: lokale Größenordnung und Lebensgrenzen

`agents/sherlock/reward.py`, `_phi` (42–51), definiert `phi = −10 × ManhattanDist / (W+H)`; ohne zugewiesenes Ziel oder bei negativer Position gilt 0. Für gültige Position und Ziel auf 24×24 liegt die geometrische Distanz zwischen 0 und 46, somit `phi` zwischen −9,58333 und 0. Dies ist eine Zustandsgrenze, keine im Pilot gemessene Distanzverteilung.

Die Pilotparameter waren `w_shape=w_death=0.5`, `gamma=.99`, `active_targets=False`. Der neue Todeszweig (`reward.py:141–146`) addiert `−w_shape × phi`, also **+5d/48**. Tod plus Korrektur, ohne weitere Rewardterme:

| Distanz d | Tod + Korrektur |
|---:|---:|
| 0 | −0,50000 |
| 5 | +0,02083 |
| 10 | +0,54167 |
| 20 | +1,58333 |
| 46 | +4,29167 |

Ab Distanz 5 überwiegt der positive Endterm lokal die Todesstrafe. Team-, Match- und Sap-Terme kommen hinzu. Das beweist weder absichtliche Selbstschädigung noch die Ursache des gemessenen Leistungsabfalls.

`surviving` (`reward.py:71–85`) prüft Masken-ID und Ortswechsel bis höchstens ein Feld, nicht Energie. Die Engine entfernt negative Units erst am Anfang des folgenden Steps (`luxai_s3/env.py:230–234`); Kollisionen können die Maske dagegen im aktuellen Step entfernen (487–499). Bei negativem Zwischenzustand bleibt mit `active_targets=False` ein Ziel/Potential möglich. Nach erkannter Entfernung erzeugt `main.py:update` Nullfeatures, STAY-only Folgemaske und `done=True`; das DQN-Ziel hat dann keinen Bootstrap. Die Korrektur kann deshalb auf den letzten erzwungenen STAY-Übergang der bereits negativen Unit fallen.

Am Matchende gilt für Überlebende bereits `phi_next=0`, `done=True`. Der anschließende `match_step=0`-Reset produziert absichtlich keinen Lernübergang (`main.py:221–226`), also keinen zweiten Endterm. Unveränderte Grenzen: Rebirth derselben ID in höchstens einem Feld Abstand bleibt unentdeckt; externe Midmatch-Trunkierung setzt `done`, ohne überall terminales Potential zu erzwingen.

Algebraisch gilt bei konsistenten Lebensgrenzen und terminalem Potential 0:

`Σ[t=0..T−1] gamma^t × w × (gamma×phi[t+1]−phi[t]) = −w×phi[0]`.

Der positive Endterm hebt frühere Potentialanteile auf. Im alten Todeszweig fehlt der letzte Shapingterm; übrig bleibt zusätzlich `w×gamma^(T−1)×phi[T−1] ≤ 0`, eine implizite distanzabhängige Todesstrafe. Die Korrektur entfernt diese. Endliche Daten, Funktionsapproximation, partielle Unitfeatures und heuristische Lebensgrenzen erlauben daraus keine Garantie unveränderter gelernter Stärke. Hypothese: diese zusätzliche Strafe bzw. ihre Skala half unter kurzem Training. Die vorhandenen CSVs enthalten keine Todes-/Potentialzerlegung; Häufigkeiten und Beträge bleiben ungemessen.

Ein späterer Beobachter könnte Distanz/Potential bei erkanntem Tod, Korrekturquantile, negative Zwischenzustände, forced-STAY, Maskenentfernung vs. ID-Rebirth und einzelne Rewardterme zählen. Er wäre als eigener Versuch vorab zu planen und dürfte keine versteckten Engineinformationen in Agententscheidungen einspeisen.

## Kritischer Review: 60.000 gegen 454.500 Decay-Schritte

Das vorgeschlagene neue Experiment ist in sich sinnvoll abgegrenzt: frische Paare 47, 48, 49, je 3.000 Spiele, gleiche Initialtensoren und RNG-Startzustände, identisches Curriculum; nur `eps_decay_steps` unterscheidet sich. `terminal_death_potential=False` in beiden Armen, ebenso `active_targets=False` und `sap_geometry=False`. Der Kontrollarm bleibt die bestehende vollständige V3-Konfiguration. Dies ist eine neue Frage zur Verhaltenspolicy, kein Reparaturversuch innerhalb des gescheiterten Reward-Piloten.

454.500 = 1.500 × 303. Daher endet der langsame Abfall exakt nach 1.500 Spielen. Bei Start der gemischten Phase nach 750 Spielen beträgt Epsilon **0,525** statt 0,05. Das erste tatsächliche Solution92-Spiel liegt bei Index **752**, Start-Epsilon **0,5237333**. Bei Spielindex 1.000 gilt 0,3666667; ab Index 1.500 wieder 0,05. Der deterministische 3.000er-Plan enthält **1.574 Solution92-Spiele**, davon **524** vor Index 1.500. Diese Zahlen wurden rein mit der dokumentierten Schedulingformel berechnet, nicht durch Spiele gemessen.

Die Änderung verschiebt Exploration tatsächlich in die Gegnerphase, erhöht sie aber auch während der gesamten Default-Aufwärmphase. Ein späterer Effekt lässt sich deshalb dem verlängerten Gesamtabfall zurechnen, nicht speziell einem Exploration-Neustart bei Solution92. Bei Beginn der Mischphase beträgt die explizite Uniform-Zweigwahrscheinlichkeit 15,75 % statt 1,5 %; der guided-Anteil beträgt 36,75 % statt 3,5 %. Mehr guided-Bewegung kann helfen, mehr Uniformität kann kurzfristig schaden. Welche Komponente wirkt, trennt dieser erste Versuch bewusst nicht.

Für einen interpretierbaren Versuch sind vor Start festzuhalten:

- Exakte Kontrollkonfiguration aus einer freigegebenen Referenz; Configdiff ausschließlich `eps_decay_steps`. Keine gleichzeitig geänderte Reward-, Ziel- oder Sap-Logik. Nach einem Merge Referenz erneut prüfen.
- Identische frische Anfangstensoren pro Paar; Seedbereiche 470000–471499, 480000–481499, 490000–491499 auf belegte Remote-/Lokalkollisionen prüfen. Gleiche RNG-Startzustände bedeuten nach Verhaltensdivergenz keine identischen Zufallsaktionen.
- Alle sechs finalen Läufe auswerten, keine Zwischencheckpoint-/Best-Seed-Auswahl. Greedy-Inferenz nutzt Epsilon 0; die Evaluationsbedingungen bleiben gleich. Je Start die gepaarte Differenz berichten; ein Kartenbootstrap allein misst nicht die Initialisierungsstreuung.
- Vor Resultaten eine Entwicklungsregel und separaten Bestätigungsblock festlegen; bereits reservierte/betrachtete Karten nicht als frisch ausgeben. Die alte Reward-Entscheidungsregel nicht stillschweigend auf den neuen Versuch übertragen.
- 18.000 Trainingsspiele plus Auswertung und mindestens eine Stunde Abschlussreserve müssen realistisch passen. Langsamere Exploration kann die Laufzeit ändern; aus dem 400er-Piloten lässt sie sich nicht verlässlich übernehmen. Kein nachträglicher Horizonwechsel oder Abbruch nach günstigen Zwischenergebnissen. Reicht die Zeit nicht, den vollständigen Versuch vertagen oder vor irgendeinem Start ein einheitliches neues Design beschließen.

Bewertung: **begründete neue kontrollierte Hypothese**, kein belegter Verbesserungsansatz. Der lange Abfall ist groß genug, um die fragliche Explorationsverteilung deutlich zu verändern. Er beantwortet zunächst, ob diese Gesamtkonfiguration bei gleicher Trainingsmenge robuster lernt; er isoliert weder reine Zufallsexploration noch deren Zeitpunkt vollständig.

## Deskriptive Begleitmetriken der abgeschlossenen Pilot-Evaluation

Je Arm/Gegner 120 Spiele (60 Karten, beide Seiten). Angegeben sind **ungewichtete arithmetische Mittel der Spielzeilen**, bei Anteilen also Mittel der individuellen Spielanteile, keine gepoolten Unit-Step-Raten. Werte mit voller Python-Float-Repräsentation; ausschließlich deskriptiv, kein zusätzlicher Auswahltest und kein Kausalnachweis.

| Gegner | Arm | wait_frac | stack_frac | known_point_tiles | unit_steps | sap_attempts |
|---|---|---:|---:|---:|---:|---:|
| default | control | 0.3892826006664977 | 0.23269071261729887 | 13.566666666666666 | 3739.65 | 36.65833333333333 |
| default | fix | 0.529124966711662 | 0.23505684822675724 | 12.941666666666666 | 3736.175 | 29.183333333333334 |
| solution92 | control | 0.3533349322799172 | 0.24022372080245347 | 13.125 | 3598.4666666666667 | 96.68333333333334 |
| solution92 | fix | 0.5463068473520669 | 0.3024445540550867 | 11.066666666666666 | 3663.15 | 66.65833333333333 |

Kennzahlendefinitionen: `scripts/common.py:121–127` ruft `StepTracker.record` **vor** der Engine-Auflösung auf. `scripts/metrics.py:54–78,88–96` zählt alle eigenen maskierten Unit-Slots ohne Energieausschluss: `unit_steps` zählt deren Entscheidungsgelegenheiten; `wait_frac` ist der Anteil ausgegebener Aktion 0, `stack_frac` der Anteil auf einem aktuell mehrfach von eigenen Units belegten Feld (jedes Stackmitglied zählt), `sap_attempts` die Anzahl ausgegebener Aktion 5, auch vor Legalitäts-/Trefferprüfung. Negative Zwischenzustände und Match-Start-Reste können in diese Zählungen eingehen. Ein Sap bleibt räumlich stehen, zählt aber nicht als `wait`; mehr `wait_frac` ist daher kein unmittelbarer Anteil physischer Bewegungslosigkeit.

`known_point_tiles` ist `belief.point_tiles.sum()` bei `Agent_x.episode_stats` am Spielende (`agents/sherlock/main.py:156–162`, übernommen in `scripts/common.py:160–162`). Es ist die Anzahl im Belief bekannter Punktefelder, nicht gehaltene Felder oder erzielte Punkte.

Beim Fix begleiten gegen Solution92 mehr ausgegebene STAY-Aktionen, mehr Stacking, weniger bekannte Punktefelder und weniger Sap-Versuche den Leistungsabfall. Die mittleren Unit-Steps sind dort sogar höher. Damit lässt sich aus diesen Aggregaten weder mehr Sterben noch eine durch terminalen Reward verursachte Wartepolitik beweisen; Todes-/Rewardereignisse fehlen weiterhin.

Gelesene CSV-SHA-256:

- `experiments/compare/autonomous_20261020/pilot_terminal_control.csv`: `4bfba3c122c5446f900c7a7ac035f0a2cc2a1a648eacc482c5892c6db8e0e1b8`
- `experiments/compare/autonomous_20261020/pilot_terminal_fix.csv`: `5940f6f50d9d71a06d850c60c34dc15503fbda6140788f4b5cd9d90d4a0fc585`
