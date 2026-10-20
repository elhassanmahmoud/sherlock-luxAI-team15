# Sherlock nach dem ersten Review: Befunde und nächste Schritte

Stand: 20.10.2026 · Übergabe von Moayed/Codex an Mahmoud/Claude Code.
Geprüfter Repository-Stand: `2ed46e4` (einschließlich der neuen Auswertungspipeline).

## Auftrag und Grenzen

Laut Moayed wurde die erste Präsentation mit **1,3** bewertet. Die Rückfragen des
Professors betreffen Reward, DQN, PPO, CNN und die guten Ergebnisse gegen
Solution_92 nach den ursprünglich genannten 18.000 Trainingsspielen.

Diese Übergabe dokumentiert die Prüfung und priorisiert mögliche Arbeiten.
**Sie ist kein Auftrag, die Vorschläge bereits umzusetzen.** In diesem Schritt
werden ausschließlich Dokumente geändert. Agent, Trainingscode, Kurs-Runner
und Gewichte bleiben unverändert; es werden keine Trainings oder Spiele gestartet.
Eine neue Abgabe-Version benötigt weiterhin eine ausdrückliche Entscheidung.

## Was bereits vorhanden ist

- **Regeln und Reward-Korrekturen:** Relic-Filter, Teilmengen-Inferenz,
  gezieltere Erkundung sowie Korrekturen bei Energie, Einheiten-Identität und
  terminalem Potential. `full_rules` verbindet diese Änderungen mit neuem Training.
- **DQN-Ensembles:** `rules6`, `all18` und `all24` wurden untersucht. Die
  untersuchte Erweiterung auf 24 Netze brachte keinen belegten Vorteil.
- **CNN und PPO:** Kartenebenen aus dem Belief plus 79 Einheitenmerkmale;
  zuerst Nachahmung eines Lehrers, anschließend PPO. Das ist bereits
  implementiert und muss nicht noch einmal von Grund auf begonnen werden.
- **Match-3-Diagnose und `far_opp`:** Entfernte Punktefelder in der
  Gegnerhälfte werden bei der Zielzuweisung hinter Kandidatenfelder eingeordnet.
  `all18_fo10` ist der derzeit am besten bestätigte Kandidat im geprüften Stand.
- **Neue Versuche bereits vorbereitet:** `full_rules_fo` trainiert mit dieser
  Zielregel. Die [Pipeline vom 20.10.](../scripts/pipeline_2010.sh) wartet auf
  sechs entsprechende Läufe und PPO `cnn2c`, baut `fo6`/`all24fo` und wertet aus.
  Die Existenz des Skripts belegt weder einen laufenden Prozess noch erfolgreiche
  Ergebnisse. Zuerst Mahmouds neue Resultate abwarten bzw. prüfen.

Die Entwicklung und historischen Prüfungen stehen im
[Arbeitsstand](ARBEITSSTAND.md) und im [Experimentprotokoll](EXPERIMENT_PROTOKOLL.md).

## Nachgezählte Ergebnisse

Die folgenden Siege wurden aus den versionierten CSVs nachgezählt. Das sind
**keine neu ausgeführten Spiele**. Jede Zeile umfasst beide Seiten pro Karte und
Gegner. Die genannten Dateien verwenden `point_counting_version=2`.

| Vergleich / Quelle | Karten-Seeds | default | Solution_92 |
|---|---|---:|---:|
| [Ausgangsstand](../experiments/compare/regeln/A_base_820.csv) | 500820–500919 | 193/200 = 96,5 % | 94/200 = 47,0 % |
| [Verbesserte Regeln, bisherige Netze](../experiments/compare/regeln/F_best_820.csv) | gleiche Karten | 198/200 = 99,0 % | 122/200 = 61,0 % |
| [`rules6`, neu trainiert](../experiments/compare/regeln/M_rules6_820.csv) | gleiche Karten | 199/200 = 99,5 % | 138/200 = 69,0 % |
| [`rules6_kdf`](../experiments/compare/regeln/W_r6kdf_1020.csv) | 501020–501219 | 395/400 = 98,75 % | 269/400 = 67,25 % |
| [`all18`](../experiments/compare/regeln/W_all18_1020.csv) | gleiche Karten | 400/400 = 100 % | 297/400 = 74,25 % |
| [`all18`](../experiments/compare/regeln/Y_all18_1220.csv) | 501220–501419 | 400/400 = 100 % | 288/400 = 72,0 % |
| [`all24`](../experiments/compare/regeln/Y_all24_1220.csv) | gleiche Karten | 400/400 = 100 % | 286/400 = 71,5 % |
| [`all18`](../experiments/compare/regeln/Z_all18_1420.csv) | 501420–501619 | 399/400 = 99,75 % | 284/400 = 71,0 % |
| [CNN + PPO, `ppo_0040`](../experiments/compare/regeln/Z_ppo0040_1420.csv) | gleiche Karten | 400/400 = 100 % | 291/400 = 72,75 % |
| [`all18`](../experiments/compare/regeln/G_a18_1620.csv) | 501620–501819 | 400/400 = 100 % | 296/400 = 74,0 % |
| [`all18` + `far_opp=10`](../experiments/compare/regeln/G_a18_fo10_1620.csv) | gleiche Karten | 400/400 = 100 % | 320/400 = 80,0 % |

**Einordnung:** Der letzte Vergleich ergibt +6 Prozentpunkte gegen Solution_92.
Das im bisherigen Arbeitsstand berichtete Karten-Bootstrap-Intervall beträgt
[+2,2; +9,8] Prozentpunkte; es wurde bei dieser Dokumentationsarbeit nicht neu
berechnet. Beim CNN-Vergleich sind +1,75 Prozentpunkte beobachtet, das dort
berichtete Intervall [−3,7; +7,2] belegt keine Überlegenheit. Eine ähnliche
beobachtete Siegquote ist auch kein statistischer Nachweis von Gleichwertigkeit.
Prozentwerte verschiedener Kartenblöcke nicht als unmittelbaren Fortschritt vergleichen.

## Antworten auf die Rückfragen des Professors

### Bekommt Sherlock erst am Ende Reward?

Nein. [reward.py](../agents/sherlock/reward.py) berechnet Trainingsbelohnungen
pro Einheit und Schritt, unter anderem aus Punkten, Zielannäherung, Energie
und Stacking. Ein Match-Ergebnis liefert zusätzlich eine Belohnung bzw. Strafe.
Spielpunkte und Trainingsreward sind unterschiedliche Größen: Shaping soll
hilfreiches Verhalten vermitteln, ist aber selbst nicht die Turnierwertung.
Die genauen Gewichte und Schalter immer aus der Config des jeweiligen Laufs
angeben; alte Abgabe und neue Trainingsvarianten nicht vermischen.

### Warum schon gute Ergebnisse nach 18.000 Spielen?

Sherlock war bereits bei der ersten Präsentation ein **hybrider Agent**:
Belief, Symmetrie, Zielzuweisung, Aktionsmasken und Sap-Zielwahl reduzieren das,
was die Netze selbst lernen müssen. Dazu kommen dichte Reward-Signale,
Replay-Wiederverwendung und ein Ensemble.

18.000 bezeichnete sechs Basisläufe mit jeweils 3.000 Spielen, nicht den gesamten
heutigen Trainingsaufwand. Bei drei Matches mit etwa 100 Schritten entspricht
das grob 5,4 Millionen Umgebungsschritten, mit mehreren Einheitenentscheidungen
pro Schritt. Das ist weder die Zahl unterschiedlicher Karten noch die Zahl
unabhängiger Lernbeispiele. Ein Vergleich nur anhand „Spiele“ ist daher unvollständig.

Die [Netz-Ablation](../experiments/analysis/rules_vs_net_20261019_net.csv) erzielte
auf 60 Karten / 120 Spielen gegen Solution_92 45 Siege (37,5 %); die
[einfache Regelalternative](../experiments/analysis/rules_vs_net_20261019_rules.csv)
mit denselben umgebenden Regeln nur 4 (3,33 %). Das belegt den Nutzen der
gelernten Aktionswahl gegenüber **dieser** Alternative, nicht gegenüber jedem
möglichen Regelbot. Für den neuesten Kandidaten erneut prüfen, weil inzwischen
auch Regeln wie `scripted_explore` Netzentscheidungen übersteuern können.

### DQN, PPO und CNN: Welche Alternative ist das?

DQN und PPO sind Lernverfahren. Ein CNN ist eine Netzarchitektur zur Verarbeitung
räumlicher Informationen; auch DQN kann ein CNN verwenden. Im Projekt werden
derzeit ein DQN-Ensemble mit MLPs und eine CNN-Policy mit Nachahmungslernen/PPO
verglichen. Architektur, Lernverfahren, Lehrer und Trainingsbudget ändern sich
dabei gemeinsam: Der Vergleich allein isoliert keinen einzelnen Ursachenbeitrag.

## Priorisierte nächste Schritte

### 1. Kandidaten reproduzierbar sichern und im Kursbetrieb prüfen

- [ ] Neue Resultate der Pipeline vom 20.10. prüfen, bevor dieselben Versuche
  noch einmal gestartet werden. Referenz zunächst `all18_fo10` festhalten.
- [ ] Für jeden verglichenen Kandidaten Checkpoint-SHA-256, Herkunft der Netze,
  gespeicherte Config, zusätzliche Schalter, Git-Commit, Umgebung und Startbefehl
  in einem Manifest festhalten. CSV allein dokumentiert das noch nicht vollständig.
- [ ] Mahmoud und Moayed Zugriff auf die **identischen** Kandidatengewichte
  ermöglichen. `experiments/ensembles/` und PPO-Checkpoints sind gitignored;
  ein Git-Pull allein überträgt sie nicht. Ablage/Übertragung getrennt vereinbaren.
- [ ] Besten Kandidaten in einer isolierten Kopie durch den unveränderten
  Kurs-Runner testen: beide Seiten, mehrere aufeinanderfolgende Spiele,
  korrekter Belief-Reset, gültige Aktionen und Laufzeit pro Zug. Der dokumentierte
  ältere Runner-Test von `rules6_kdf` ersetzt diesen Test nicht.

**Erfolgskriterium:** Eine zweite Arbeitsumgebung kann denselben Kandidaten mit
derselben Konfiguration ausführen; Runner-Verhalten und Laufzeit sind protokolliert.
Die vorhandenen Abgabe-Gewichte werden dabei nicht überschrieben.

### 2. Match 3 gezielt verbessern: erreichbare Punkte statt langer Wege

Die bisherige Diagnose deutet auf zu lange Wege zu gegnerischen Punktefeldern,
während eigene Möglichkeiten ungenutzt bleiben. `far_opp=10` adressiert das
bereits erfolgreich. Nicht pauschal Gegnerhälfte oder Erkundung verbieten:
Mehrere frühere Varianten dieser Art waren schlechter.

- [ ] Zuerst die neuen `full_rules_fo`-Ergebnisse bewerten.
- [ ] Danach als einzelne Änderung Zielprioritäten anhand erreichbarer
  Punktegewinne untersuchen: tatsächliche Weglänge, Restzeit, Energie,
  sichtbare Bedrohung und bereits zugewiesene Einheiten.
- [ ] Neben Spielsiegen messen: Match-3-Siege, Zeitpunkt der Besetzung,
  besetzte unterschiedliche Punktefelder, Reisezeit und unnötige Zielwechsel.
- [ ] Gegen die feste Referenz auf denselben Karten und beiden Seiten vergleichen.

**Abgrenzung:** Eine bessere Bewertung von Zielen ist nicht identisch mit dem
bereits getesteten Erzwingen von BFS-Bewegungen (`pt_walk`), das oft schadete.
Der vorgeschlagene Nutzen ist noch unbewiesen. Orakel-Diagnosen grenzen Ursachen
ein, beweisen aber nicht allgemein, dass Wissen kein Engpass mehr sein kann.
Versteckter Spielzustand bleibt ausschließlich externes Diagnosematerial.

### 3. Breiter und ohne erneute Testauswahl bewerten

- [ ] Neben default/Solution_92 auch alten Sherlock, aktuelle Kandidaten und
  verfügbare weitere Gegner verwenden. Gegen den alten Sherlock gewann
  `rules6_kdf` im dokumentierten Test nur 60/100 Spiele.
- [ ] Entwicklungs-, Auswahl- und abschließende Testkarten getrennt festlegen.
  Karten 900000–900029 wurden historisch mehrfach verwendet und sind kein
  unberührter Testsatz, auch wenn spätere Läufe sie nicht erneut angefasst haben.
- [ ] Bis 501819 liegen Resultate vor; **501820–502019 sind bereits für die neue
  Pipeline vorgesehen**. Vor neuen Seed-Zuweisungen mit Mahmoud abgleichen.
- [ ] Konfidenzintervalle mit beiden Seiten als gemeinsamer Karteneinheit
  berechnen (`compare_report`); nicht nach jedem Tuning-Schritt den finalen
  Testsatz prüfen. Trainingsstarts und Budget mitberichten.

**Erfolgskriterium:** Fortschritt bleibt auf vorab zurückgehaltenen Karten sichtbar
und wird nicht nur durch Anpassung an Solution_92 oder einen Kartensatz erklärt.

### 4. PPO vor längerem Training technisch absichern

**Konkreter Prüfpunkt aus dem Code:** In
[ppo_agent.py](../agents/sherlock/ppo_agent.py) werden Aktionen und alte
Log-Wahrscheinlichkeiten mit ungerundeten Kartenebenen ermittelt. Der Recorder
speichert diese Ebenen als gerundete `int8`-Werte mit Faktor 127.
[ppo_train.py](../scripts/ppo_train.py) verwendet beim Update die zurückskalierten
Werte. Die Eingaben stimmen damit nicht exakt überein. Die praktische
Auswirkung wurde nicht gemessen; das ist keine nachgewiesene Erklärung für
die spätere Leistungseinbuße.

- [ ] Bei unverändertem Netz und derselben Aktionsmaske prüfen, ob alte und neu
  berechnete Log-Wahrscheinlichkeiten übereinstimmen und die PPO-Ratio vor dem
  ersten Update ungefähr 1 ist. Vorverarbeitung konsistent halten.
- [ ] Periodische Validierung und Auswahl des besten Checkpoints vorsehen;
  „letzter Checkpoint“ ist laut bisherigen Kurven nicht automatisch besser.
- [ ] KL-basierte Begrenzung der Updates und ggf. Lehrer-Regularisierung einzeln
  untersuchen. Sinkende Entropie ist eine Beobachtung, noch keine Ursachenanalyse.
- [ ] Bei weiterem Budget mehrere unabhängige Trainingsstarts vergleichen.
  Ein einzelnes CNN ist nicht automatisch schneller als 18 kleine MLPs:
  tatsächliche Laufzeit im vorgesehenen CPU-/Runner-Betrieb messen.

`cnn2` erreichte früh höhere Siegquoten und fiel später ab; `cnn2b` brachte auf
den verwendeten Auswahlkarten keinen Fortschritt. Das rechtfertigt gezielte
Stabilitätsprüfungen, nicht die allgemeine Aussage „PPO bringt nichts mehr“.

### 5. Reward und Lernbeitrag durch einzelne Änderungen erklären

- [ ] Reward-Komponenten einzeln protokollieren: Punkte, Zielannäherung,
  Energie/Stacking, Match-Ergebnis und ggf. Gegnerpunkte.
- [ ] Gegnerpunkte-Strafe und Gegner-Pool getrennt variieren. Bei
  `full_rules_opp` änderten sich beide; dessen Ergebnis isoliert keine der Ursachen.
- [ ] Für den aktuellen Kandidaten Netzbeitrag, Belief und zusätzliche Regeln
  mit gezielten Ablationen untersuchen; zuerst ohne Neutraining umschaltbare
  Effekte, getrennt davon Trainingseffekte.

**Erfolgskriterium:** Für die nächste Präsentation zeigen können, welche
Komponente unter welchen Bedingungen hilft, und wo nur eine Hypothese besteht.
Keine Serie vieler gleichzeitig veränderter Schalter ohne klare Vergleichsbasis.

## Quellen und Prüfgrenzen

- Repository-Code und oben verlinkte Messreihen zum Stand `2ed46e4`.
- [PPO-Dokumentation, inklusive KL-Abbruch](https://spinningup.openai.com/en/latest/algorithms/ppo.html).
- [Einordnung von On-/Off-Policy-Verfahren](https://spinningup.openai.com/en/latest/spinningup/rl_intro2.html).
- [DQN mit CNN im ursprünglichen Paper](https://arxiv.org/abs/1312.5602).
- Keine neuen Spiele, Trainings oder Anwendungstests in dieser Prüfung.
  Die im historischen Arbeitsstand genannten 148 Tests sind Mahmouds damaliger
  Prüfstand, keine hier erneut ausgeführte Testsuite.
- Die beiden versionierten Abgabe-Dateien bleiben unverändert; beide besitzen
  SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.
