# Übergabe an Mahmoud: Einzelnetz und SAP-Belohnung, 04.11.2026

## Ziel und belastbarer Stand

**Ergebnis: kein stärkerer Nachfolger; V14 bleibt unverändert die Abgabe.** Alle vier neuen Einzelnetz-Varianten lagen in diesem Vergleich deutlich hinter V14. Gegen Solution gewann V14 36/40 Spiele, S3 0/40, S30 18/40, CONTROL30 16/40 und SAP0_30 22/40. Das Entfernen des geschätzten SAP-Rewards ist eine unsichere positive Spur innerhalb dieses Schülerpaares, keine Empfehlung, V14 zu verändern. Insgesamt wurden 1.064 neue Spiele vollständig ausgeführt: 464 im RL-Versuch einschließlich Vorlauf/Validierung und 600 im frischen Diagnosevergleich. Die alten 600.000 Zustandszeilen zählen nicht als neue Spiele.

Ein einzelnes Schülernetz wurde tatsächlich trainiert und unabhängig technisch geprüft. Es bildet die Q-Bewertung des unveränderten V14-Ensembles mit 36 Netzen nach. Darauf baut ein isolierter Versuch zur SAP-Trainingsbelohnung auf. Diese kurze Studie untersucht Machbarkeit und eine Reward-Hypothese; sie ersetzt weder die sieben Freigabehürden noch die technische Paketabnahme. Eine Übernahme in die Abgabe ist nicht vorgesehen.

Die fünf vorab erfassten geschützten Gewichts- und ZIP-Dateien haben nachweislich unveränderte Hashes. Alte Sicherungen wurden nicht bearbeitet.

## Was das Einzelnetz ersetzt

`scripts/student_distill.py` lernt den arithmetischen Mittelwert der 36 rohen V14-Q-Vektoren. Der Schüler nutzt das vorhandene Dueling-MLP: 79 Eingaben, zwei Schichten mit jeweils 512 Einheiten, anschließend Wert- und Vorteilskopf mit jeweils 128 Einheiten und insgesamt sechs Q-Ausgaben. Das sind 435.847 Parameter.

Sherlocks bisherige Regeln und Belief-Zustände bleiben erhalten. Das Einzelnetz ersetzt die Q-Bewertung innerhalb dieses Agenten. Es ist kein vollständig durch ein Netz ersetzter, regelfreier Agent. Die Spielkonfiguration entspricht V14 bis auf `hidden=512`.

Die beiden historischen Replay-Dateien enthalten jeweils 300.000 Zustandszeilen. Je Datei dienen die ersten 240.000 dem Lernen und die letzten 60.000 der Diagnose: insgesamt 480.000 Lern- und 120.000 Diagnosezeilen. Verwendet wurden nur Zustände, keine alten skalaren Rewards. Alte Replay-Puffer werden nicht in das anschließende RL übernommen.

Die Teilmengen sind keine nachweislich unabhängigen Karten oder Episoden. 18 identische Merkmalszeilen kommen in beiden Teilmengen vor. Aktuelle Aktionsmasken fehlen; die Diagnose bewertet daher keine Übereinstimmung unter ausschließlich legalen Aktionen.

## Warum es S3 und S30 gibt

Der ursprüngliche Lauf S3 absolvierte drei vollständige Epochen in tatsächlich 17,9 Sekunden. Seine historischen Diagnosewerte motivierten vor dem ersten neuen Spiel einen ausdrücklich festgelegten Zusatzlauf mit genau 30 Epochen. S30 beginnt mit derselben Zufallsinitialisierung und nutzt denselben Lehrer, dieselben Daten sowie Adam mit Lernrate 0,0001 und Batchgröße 1024. Seine tatsächliche Laufzeit von ungefähr 72 Sekunden wurde erst nach diesem Lauf gemessen; sie war keine vorab bekannte Entscheidungsgrundlage.

Es gab keine Auswahl eines Zwischencheckpoints. S30 wurde vor den Spielresultaten verbindlich als Ausgangspunkt beider RL-Arme festgelegt. S3 bleibt als eigener Vergleich erhalten.

| Historische Diagnose | S3 | S30 |
|---|---:|---:|
| Vollständige Epochen | 3 | 30 |
| Adam-Updates | 1.407 | 14.070 |
| Besuche von Lernzeilen | 1.440.000 | 14.400.000 |
| Q-MSE control18 | 11,08040 | 2,97745 |
| Q-MSE adapt18 | 11,67298 | 3,11138 |
| Unmaskierte Argmax-Übereinstimmung control18 | 53,395 % | 68,0883 % |
| Unmaskierte Argmax-Übereinstimmung adapt18 | 54,715 % | 68,715 % |

Diese Werte wurden unabhängig aus allen 600.000 Zustandszeilen und dem direkten Mittelwert der 36 Lehrernetze nachgerechnet. Sie belegen bessere Nachbildung des Lehrers auf diesen historischen Daten, keine höhere Spielstärke oder Siegrate.

Beide Artefakte besitzen endliche, gegenüber der Initialisierung veränderte Gewichte. Der echte `Agent_x` lädt jeweils genau ein Netz mit identischen Parametern und Vorhersagen. Optimizer und Replay fehlen im Export. `env_steps=60000` ist ein gesetzter Startwert für den Explorationsplan des folgenden RL-Trainings, kein Nachweis von 60.000 tatsächlich ausgeführten Spielschritten. Die überwachten Lernupdates werden separat dokumentiert; `learn_steps=0` bedeutet hier nur, dass noch keine RL-Updates erfolgt sind. Im normalen Testbetrieb wird Exploration abgeschaltet.

## Die SAP-Hypothese und der festgelegte Vergleich

Das bestehende Shaping belohnt vermutete SAP-Treffer und bestraft vermutete Fehlschüsse. `w_sap_hit=0` entfernt beide Vorzeichen dieses Terms. Andere Rewards und SAP-Aktionen bleiben bestehen. Das Experiment beweist nicht, dass die ursprünglichen Trefferschätzungen falsch waren.

Beide RL-Arme starteten von S30 mit frischen Optimierern und leeren Puffern. Durchgeführt wurden je 40 Vorlauf- und 160 Lernspiele, Startwert 29, Exploration 0,05 und derselbe Gegnermix: 60 % Solution, 20 % sol92_sq, 10 % default und 10 % rush. Trainingskarten sind 493000–493079, Vorlaufkarten 495000–495019. Je 32 bekannte Validierungsspiele werden nur am Anfang und Ende verwendet. Die Karten 500000–500003 sind kein neuer Stärkenachweis; es gibt keine Wahl des besten Zwischenstands.

Die Reward-Instrumentierung berechnet das Gegensignal auf exakt denselben Übergängen, ohne Zufallsfolge oder Training zu beeinflussen.

Beide Arme sind abgeschlossen und bestanden die unabhängige technische Abnahme mit 94 von 94 Prüfungen. Je Arm wurden 24.000 Adam-Updates mit endlichen Zuständen und veränderten Q-Gewichten bestätigt. Zusammen sind das 48.000 RL-Updates und 464 RL-bezogene Spielausführungen: 80 Vorlauf-, 320 Lern- und 64 bekannte Validierungsspiele. Die 600.000 historischen Zustandszeilen sind keine neu gespielten Partien.

| Arm / Phase | SAP-Übergänge | SAP-Beitrag signiert | SAP-Beitrag absolut | Positiv → nichtpositiv |
|---|---:|---:|---:|---:|
| Kontrolle / Vorlauf | 3.108 | 898,2 | 1.240,2 | 337 |
| SAP0 / Vorlauf | 3.108 | 898,2 | 1.240,2 | 337 |
| Kontrolle / Lernen | 12.477 | 3.807,6 | 4.931,4 | 2.266 |
| SAP0 / Lernen | 9.527 | 2.799,9 | 3.890,7 | 1.205 |

Die Tabelle beschreibt jeweils den Unterschied zwischen ursprünglichem Reward und Reward ohne SAP-Term auf denselben Übergängen: in der Kontrolle hypothetisch, bei SAP0 tatsächlich entfernt. Der absolute Beitrag zählt Bonus und Fehlschussstrafe ohne gegenseitige Aufhebung; die letzte Spalte zählt positive Rewards, die ohne SAP-Term nichtpositiv wären. Im Vorlauf waren Aktionen und Merkmalszustände beider Arme identisch. SAP0 erhielt dort exakt 898,2 weniger Gesamtreward, entsprechend dem entfernten signierten Term. Später unterscheiden sich die Lernverläufe. Reward-Summen sind durch die Intervention verändert und deshalb kein Spielstärkenvergleich.

Der vorab erweiterte Diagnoseplan umfasst V14, S3, S30, CONTROL30 und SAP0_30 auf 20 reservierten Karten 864000–864019, jeweils beide Seiten gegen Solution, default und V13: insgesamt 600 Spiele. Alle 600 Spiele sind vollständig, mit 303 Schritten, eindeutigen Schlüsseln und Punktezählung v2. Die Auswertung erfolgt gepaart nach ganzen Karten. Daraus folgt keine Abgabefreigabe und keine zweite Auswahlrunde.

| Stand | Solution | Default | V13 | Alle drei Gegner |
|---|---:|---:|---:|---:|
| V14 | 36/40 | 40/40 | 23/40 | 99/120 (82.50 %) |
| S3 | 0/40 | 33/40 | 0/40 | 33/120 (27.50 %) |
| S30 | 18/40 | 40/40 | 4/40 | 62/120 (51.67 %) |
| CONTROL30 | 16/40 | 40/40 | 2/40 | 58/120 (48.33 %) |
| SAP0_30 | 22/40 | 40/40 | 4/40 | 66/120 (55.00 %) |

Es gab keine Unentschieden und keine ausgeschlossenen Spiele. **SAP0_30 gegenüber CONTROL30:** im Dreierpanel +6,67 Prozentpunkte, gepaartes 95-%-Bootstrapintervall [−0,83; +14,17]; gegen Solution +15,0 pp [0,0; +30,0]. Damit ist der Vorteil nicht abgesichert. **SAP0_30 gegenüber V14:** im Panel −27,50 pp [−35,00; −18,33]. Auch die anderen drei Schüler liegen im Panel unter V14; die vollständigen Intervalle stehen im [Datenbericht](../experiments/analysis/student_reward_20261104/diagnostic/diagnostic_review.md).

Die Stichprobe umfasst nur 20 Karten und einen Trainingsstart. 5.000 Bootstrapziehungen mit Seed 0 ziehen jeweils eine ganze Karte einschließlich beider Seiten und aller drei Gegner. Die Intervalle sind explorativ und nicht für mehrere Vergleiche korrigiert. Es gibt keine unabhängige Bestätigung oder Abgabefreigabe. V14s 90 % in dieser kleinen Stichprobe ersetzen nicht die historischen 95,4 % auf einem anderen, größeren Kartensatz; die unterschiedlichen Kartensätze dürfen nicht als Leistungsänderung interpretiert werden.

Der lokale Seed-Abgleich fand keine vorherige Nutzung von 864000–864019 in den lesbaren Seed-Feldern und Bereichen der acht untersuchten Arbeitskopien. Grenzen bei Dateien ohne Seed-Felder bleiben im [Vorabnachweis](../experiments/analysis/student_reward_20261104/preflight/freshness_adjudication.json) dokumentiert.


## Prüfung, Reproduktion und Übergabe

Die abschließende gemeinsame Prüfung des unveränderten Quellstands bestand mit **50 Tests in 9,94 Sekunden** (29 Distiller + 21 Reward). Zusätzlich wurden zu Beginn 35 passende Baseline-Tests ausgeführt. Die gesamte historische Testsuite wurde nicht erneut ausgeführt. Unabhängige Code-, Artefakt- und Datenreviews sowie der Abgleich von 54 Ergebnissen/Intervallgrenzen mit dem vorhandenen Berichtswerkzeug bestanden. Zusätzliche Distillationsmetadaten und spärliche Legacy-Konfigurationen wurden an den Integrationsgrenzen berücksichtigt. Ein Veröffentlichungsfehler konnte einen fertigen Laufbeleg sichtbar machen, bevor der Status auf abgeschlossen stand. Die ursprünglichen RL-Läufe wurden durch dokumentiertes kurzes Pausieren/Fortsetzen eines Workers zeitlich entzerrt und danach unabhängig vollständig abgenommen. Ihre Artefakte und Laufbelege bleiben unverändert.

Die anschließende Korrektur schreibt den Abschlussstatus vor Veröffentlichung des Laufbelegs. Ein deterministischer Regressionstest stellte den Fehler zunächst nach; anschließend bestanden alle 21 Reward-Tests. Die unabhängige Prüfung akzeptierte die Korrektur. Sie ändert keine Rewards, Modelle oder Trainingsparameter und erfordert keine Wiederholung des Trainings.

Die belegten Quellstände sind `221ccf4` für S3, `9d0120d` für S30 und `5b9f883` für das tatsächlich ausgeführte RL. Die Veröffentlichungskorrektur ist in `cdb6e85` enthalten; dieser anschließend eingefrorene Quellstand dient der Evaluation. Historische RL-Belege bleiben an ihre ursprünglichen Quellen gebunden. Die dauerhafte [Belegablage](../experiments/analysis/student_reward_20261104/README.md) enthält Eingabe-/Quellhashes, Originalbefehle, alle Rohdaten, Laufnachweise und Reviews. Die vier getesteten Checkpoints sind unter [experiments/candidates/student_reward_20261104](../experiments/candidates/student_reward_20261104/README.md) versioniert; sie sind ausdrücklich keine Abgaben. Original-Startbefehle liegen in `student/guard.json`, `student30/guard.json`, `rl/<arm>/guard.json` und `diagnostic/<rolle>_guard.json` innerhalb der Belegablage.

S3-SHA256: `0b465006b5eb6ec3dc9e2bdff19aec29eae44f557573e76e07e3af1e35a52a9b`.

S30-SHA256: `3104596d5527d644d0c3f2cfc98189ec166e6e8e4a1f0ae9a4166f27a934b11b`.

Für eine Wiederholung, vom Repository aus und mit neuen Ausgabeordnern, ist die Befehlsstruktur:

```sh
<PYTHON> -B -m scripts.student_distill --teacher agents/sherlock/weights/agent_p0.pth --buffers <CONTROL18_REPLAY> <ADAPT18_REPLAY> --out experiments/runs/<NEU_S3> --deadline-utc <ISO_UTC>
<PYTHON> -B -m scripts.student_distill --teacher agents/sherlock/weights/agent_p0.pth --buffers <CONTROL18_REPLAY> <ADAPT18_REPLAY> --out experiments/runs/<NEU_S30> --epochs 30 --deadline-utc <ISO_UTC>
<PYTHON> -B -m scripts.student_reward_train prepare --student experiments/runs/<NEU_S30>/weights/agent.pth --out experiments/runs/<NEU_RL>
<PYTHON> -B -m scripts.student_reward_train runarm --prepared experiments/runs/<NEU_RL> --arm control --deadline-utc <ISO_UTC>
<PYTHON> -B -m scripts.student_reward_train runarm --prepared experiments/runs/<NEU_RL> --arm sap0 --deadline-utc <ISO_UTC>
```

`<PYTHON>` bezeichnet die vorhandene Projekt-Umgebung; Replay-Platzhalter benötigen die beiden historischen lokalen Dateien. Für jeden Prozess ist ein CPU-Thread einzustellen. Die Originalbefehle und Hashes haben Vorrang vor dieser verkürzten Darstellung.

Die historischen Roh-Replays bleiben lokal. Für eine Wiederholung auf einem anderen Gerät werden dieselben beiden Dateien benötigt; Git enthält sie nicht automatisch. Es gelten höchstens zwei Modelljobs mit je einem CPU-Thread und festen Fristen.

Geprüfte Werkzeug-Commits: `221ccf4` (Destillation), `bd7c73c` (gepaartes RL), `9d0120d` (explizite Epochen), `5b9f883` (Legacy-Konfiguration), `cdb6e85` (Abschlussveröffentlichung). Hinzu kommen die getrennten Daten- und Dokumentationscommits. Für Mahmoud: lokale Arbeit zuerst sichern, danach `git fetch origin` und auf einer konfliktfreien `main`-Arbeitskopie `git pull --ff-only`. Keine experimentellen Gewichte über die Abgabe kopieren. Die vollständigen lokalen Trainingspuffer bleiben in Moayeds Studienarbeitskopie; deren Pfad ist in den Manifesten enthalten.

Zum erneuten Prüfen bereits verbrauchter Diagnosekarten kann `scripts.par_eval` mit einem gespeicherten Kandidaten und `experiments/analysis/student_reward_20261104/diagnostic/seeds.json` verwendet werden, immer mit neuer CSV und höchstens zwei Ein-Thread-Workern. Eine solche Wiederholung wäre eine Reproduktion, kein neuer unberührter Test.

**Empfohlene Fortsetzung nach der Abgabe:** Der Schüler müsste zuerst die entscheidungsrelevanten Bewertungen zuverlässiger übertragen. Dafür sind aktionsbezogene Lernziele und neu gesammelte Schülerzustände mit Aktionsmasken naheliegende, noch ungetestete Ansätze. Die bestehende Q-MSE enthält auch einen gemeinsamen Wertversatz aller Aktionen, der deren Reihenfolge nicht verändert; bessere Q-MSE allein hat hier nicht für Spielstärke gereicht. Mehrere unabhängige Trainingsstarts wären für die unsichere SAP-Hypothese nötig. Diese Änderungen sind nicht umgesetzt. Zusätzliche Merkmale, Prioritized Replay und weitere Reward-Terme bleiben getrennte spätere Versuche; vor der heutigen Abgabe wird daran nichts ungeprüft umgestellt.
