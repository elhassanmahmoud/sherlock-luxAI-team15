# Entscheidungslernen um eingefrorenes V14

## Auftrag und Ausgangslage

Moayed beauftragt am 08.11. ausdrücklich weitere autonome Verbesserung, auch nach dem nächsten Prototyp. Die abgeschlossenen Ensemble-Studien bleiben geschlossen; dies ist ein neuer Ansatz. Ziel ist bessere Spielleistung gegen V14 und Solution, keine Garantie einer allgemeinen 100-%-Quote. Kleine begrenzte Studien statt erneut tausender Vorversuche. Gewichte und abgegebene ZIP bleiben bis zu einem unabhängigen Übernahmenachweis unverändert.

Die historischen zwölf ausgewählten Spiele zeigen 277 vorgeschlagene/ausgeführte Abzüge einzelner Halter von eigenen Punktefeldern. Fast alle passieren unter sichtbarer Gegnerbedrohung, die übrigen verlassen negative Energiefelder. Eine einfache sichere Halteregel hat null Fälle. Abzüge sind daher keine bewiesenen Fehler. Wir untersuchen stattdessen den Energie-/Kampfkonflikt durch tatsächliche alternative Fortsetzungen.

## Erstes Experiment: Einflussprobe, kein Leistungstest

- Exakt zwölf bekannte Seed/Seiten-Schlüssel aus dem früheren targeting-Manifest, Gegner Solution92, originales V14. Historische Verlust-/Kontrollauswahl offen deklarieren; keine frischen Validierungsdaten.
- Pro Spiel höchstens acht Situationen: erste passende Situation, danach mindestens zwölf echte Schritte Abstand; höchstens ein UID je Schritt, erster passender UID in der unveränderten aufsteigenden Agentenschleife. Maximal 96 Paare.
- Nur Evaluation, legaler Move1..4, STAY legal, gültige Koordinaten, eigene Energie >=0, alleiniger nichtnegativer Halter eines bekannten Punktefeldes, zugewiesenes Ziel = aktuelles Feld, Ziel des Moves kein bekanntes Punktefeld, mindestens zwölf reguläre Aktionen bis zur Matchgrenze: Engine führt match_step100 noch aus, daher 1<=match_step<=89 für Horizont12; match_step0 ist Reset-only und ausgeschlossen. „Eigenes Punktefeld“ bedeutet selbst besetzt, keine zusätzliche Kartenhälften-Beschränkung. Grenzsemantik im Werkzeugtest nachweisen.
- Eingriff unmittelbar vor `_rule_override`, nach `scripted_explore`. HOLD ersetzt nur diesen Vorschlag durch STAY. Alle bestehenden Regeln einschließlich SAP und Folgen für andere Einheiten laufen normal weiter. An allen folgenden Schritten V14 unverändert.
- Zwei getrennte Fortsetzungen ab derselben Momentaufnahme vor BEIDEN act-Aufrufen: unverändertes V14 und einmaliger HOLD. Reihenfolge wie common.play_game. Horizont zwölf Schritte. Label = HOLD-Team-Punktedifferenz minus Baseline-Team-Punktedifferenz über den gesamten Horizont, vorhandene v2-Punktezählung verwenden.
- Vollständige Teamaktionen archivieren; identische erste Teamaktionen separat zählen. Änderungen an SAP und an späteren Einheiten sind zulässige Folgen und keine Einheiten-Einzelfallkausalität. Keine Filterung anhand künftiger Baselineaktionen, Gegneridentität oder versteckter Spielinformationen.
- Pro bekanntem Schlüssel ein uninstrumentiertes Referenzspiel und ein passives Sammelspiel: maximal 24 vollständige Ausführungen plus höchstens 2304 zusätzliche Simulationsschritte. Technische Wiederholungen separat zählen; keine Spielstärke daraus behaupten.
- Fortsetzung zum Lernen nur bei >=24 Fällen mit tatsächlich verschiedenen ersten Teamaktionen sowie >=6 positiven HOLD-Labels verteilt über >=3 Spiele. Dies ist ein vorab gesetzter Machbarkeitsfilter, kein statistischer Wirksamkeitsnachweis. Bei Nichterreichen keinen wirkungslosen Kopf trainieren; als getrennten nächsten Ansatz Energieverwendung beim Halter-SAP diagnostizieren.

## Isolation und Beweispflichten

Sherlock-Verhaltenszustand vollständig als gemeinsamer Objektgraph kopieren, nur eingefrorene stateless Torch-Q-Module teilen. Ausnahme im reinen Diagnoseagenten: ungenutzten Trainings-Replay-Puffer und Optimierer nach Laden auf None setzen; update/train/save im Werkzeug verboten. Damit werden nicht bei jedem Schritt190MB ungenutzte Trainingsdaten kopiert. Das unveränderte Agent_x-Referenzspiel und vollständige Passivität prüfen diese Optimierung. Solution-Objekt UND Global-Attributgraph zusammen kopieren, da Global.REWARD_RESULTS Nodes aus der gegnerischen Space referenziert. Branch-Global installieren, originale Referenzen und Attributinventar in finally restaurieren. Python-/NumPy-/Torch-CPU-Zufallszustände ebenfalls restaurieren. Keine resets/set_env_cfg/neue Gegner im Branch. Separater flacher Lux-Wrapper mit unveränderlichen JAX-state/key/params und geprüft reinem jax_env.step.

Kein Hook darf eine Closure auf Live-Agent/Sammler behalten. Kein Lernen oder Verändern geteilter Netze. Probe darf echte Fortsetzung nicht verändern: Referenz-/Sammelspiel identische Aktionen, Scores, Zustands-/Beobachtungshashes; Baselinebranch stimmt mit tatsächlich folgenden zwölf Schritten überein. Branchreihenfolge, Wiederholung, Exceptionrestauration, interne Node-/Belief-Aliase gezielt prüfen. Verdeckte Zustände dienen nur Simulatorfortsetzung/Prüfung, niemals späteren Merkmalen.

## Anschluss nach positivem Machbarkeitsfilter

Separate vorab dokumentierte 24 Trainings- und acht Validierungskarten, beide Seiten, feste Samplingregeln. Kleine gelernte Korrektur auf legalen öffentlichen Merkmalen (Q-Abstand, Energie, Feldenergie, beobachtete Bedrohung, Schritte, SAP-Gelegenheit) statt V14 zu imitieren. Normierung ausschließlich Training, fester Ridge-Ansatz und konservative Schwelle; keine Modell-/Schwellenjagd auf Testkarten. Fehlender/neutraler Kopf muss V14 exakt erhalten. Die konkreten Seedlisten, Datenobergrenze, Merkmale und Auswahlregeln werden vor neuen Labels festgelegt.

Danach kleine frische Vorauswahl gegen Solution, V14 und Kontrollen; ein eingefrorener Kandidat erhält genau eine begrenzte unabhängige Prüfung. Übernahme nur bei belegtem Vorteil inklusive Direktvergleich und ohne relevante Kontrollverschlechterung, reproduzierbarer Laufzeit/Kursschnittstelle und gesicherter alter Abgabe. Frühe Probe/Trainingslabels sind kein Übernahmenachweis. Genaues Leistungsprotokoll vor Leistungsergebnissen separat festlegen; negative Studien nicht nachträglich verlängern.

## Betrieb

Bestehender isolierter Worktree, eigener Zweig improvement/decision-learning-20261108. Maximal zwei Modellprozesse insgesamt, Probe sequenziell ein Prozess. Keine Tests parallel mit Modellspielen. Source-Freeze während einer Messreihe; Remote nur abrufen, sicher am Übergang integrieren. Restkontingent laut Nutzer freigegeben, keinen Reset einlösen. Netzstrom für lange Läufe, STOP und Quellen-/Gewichtshashes prüfen. Sinnvolle Commits und Dokumentation für Mahmoud, kein Austausch nach bloßen Lernfortschritten.

Methodischer Hintergrund: [Multiagent Rollout, Bertsekas](https://arxiv.org/abs/1910.00120). Dessen theoretische Garantien gelten nicht automatisch für unseren kurzen Horizont, partielle Beobachtung und einen approximierten Korrekturkopf.
