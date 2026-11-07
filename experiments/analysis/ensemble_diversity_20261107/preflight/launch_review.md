# Unabhängiger Startreview, 07.11.2026

## Umfang und Methode

Gezielter statischer Review von `scripts/ensemble_diversity_train.py`, `scripts/ensemble_diversity_supervisor.py` und deren neuen Tests gegen Design, Umsetzungsplan und vorab festgelegten Ensemblevergleich. Zusätzlich die tatsächlich wiederverwendeten Pfade in `finetune.py`, `final_rescue_train.py`, `targeting_adapt.py`, `experiment.py`, den gemeinsamen Prozess-/Quellschutz und die einschlägigen Agenten-Regelbedingungen gelesen. Keine Codeänderungen, neuen Spiele, Trainings, Testläufe oder Git-Operationen durch diesen Reviewer. Das ist keine Bestätigung echter Trainingsresultate.

## Wesentlicher Befund

**Vor Start zu beheben: SIGTERM während Validierung wird erst nach dem ganzen Block beachtet.** Im geprüften Snapshot prüft `run_arm.validate` den Stopp vor und nach `validate_v14`; die darunterliegende Validierung führt aber alle 32 Spiele ohne weitere Stoppabfrage aus. Ein SIGTERM während des ersten Spiels stoppt daher nicht vor dem nächsten Spiel. Überschreitet der Restblock die 180 Sekunden Schonfrist des Supervisors, folgt SIGKILL statt kontrollierter Sicherung. Der existierende Unterbrechungstest deckt nur Vorlauf-/Trainingsspiele ab.

Root hat den Befund angenommen und eine lokale Korrektur mit Regressionstest beauftragt. **Korrektur und Testergebnis sind in diesem Review noch nicht verifiziert.** Die Startfreigabe setzt deren Prüfung durch Root voraus; dieser Eintrag behauptet keinen abgeschlossenen Fix.

## Übrige geprüfte Eigenschaften

- Drei fest zugeordnete Eltern, sechs getrennte Zufallsstarts, jeweils einzelnes Online-/Target-Netz mit identischen Starttensoren; tatsächlicher leerer Replay und frischer Adam werden vor dem ersten Spiel geprüft.
- Die Trainingskonfiguration aktiviert die drei vorgesehenen Trainingsschalter bei Lernrate 0,00005. Die weiterhin inaktive Trainingswirkung von `art_splash` wird ausdrücklich dokumentiert. Validierung wechselt zur normalisierten V14-Konfiguration und nutzt den vorhandenen Lern-/Replay-/RNG-Schutz mit Wiederherstellung auch im Fehlerfall.
- Jede Vorlauf-/Lernpartie wird gegen festen Seed, Seite, Gegner und Lernmodus geprüft. Die sechs Produktionsbereiche sind getrennt; Smoke verwendet getrennte Karten. Gespeicherte Aktionen werden mit tatsächlicher Ausgabe und Replay-Schreibvorgang abgeglichen.
- Vollständigkeit verlangt 120 Vorlauf-, 3000 Lern-, 128 Validierungsspiele und 450000 Updates. Der Endnachweis bindet gespeicherte Gewichte, Spielprotokolle und Audit per Hash; zusätzlich wird der gespeicherte Endzustand gegen den tatsächlichen Lerner geprüft und neu geladen. Smoke und unterbrochene Läufe bleiben nicht nominierbar.
- Der Supervisor reserviert einen einmaligen Start, feste neue Run-Namen, zwei Plätze und gemeinsame Ressourcensperren. Er prüft fremde Prozesse, eingefrorene Quellen/HEAD/Interpreter, vorbereitete Eingaben, beide V14-Gewichte und ZIP wiederholt. Fehler stoppen verbleibende eigene Prozesse; keine automatischen Wiederholungen.

Keine weiteren materiellen Startblocker im gelesenen Snapshot gefunden. Die leichte Supervisor-Receiptprüfung ersetzt ausdrücklich nicht den nachgelagerten unabhängigen Tensor-/Rohdatenaudit vor Kandidatenbau. Der Root-Operator muss weiterhin Kontingent und Remote-Abgleich überwachen; diese Aufgaben werden nicht vom Supervisor automatisiert. Echte Smoke-Prüfungen, finale Quellfestlegung und ein erfolgreicher Langlauf sind außerhalb dieses statischen Reviews.

## Root-Abnahme der Korrektur

Vor dem echten Smoke geprüft: Stoppabfrage vor jedem Validierungsspiel, vorherige abgeschlossene Zeile bleibt erhalten, Hooks/Config in finally wiederhergestellt. Zwei Regressionsfälle wurden vor der Korrektur rot beobachtet; Root hat anschließend 142 gezielte Tests (inklusive neuer und gemeinsam genutzter Werkzeuge) selbst erfolgreich ausgeführt, 50,74 s, Exit 0. Kein offener materieller Startblocker; reale Smoke-Läufe weiterhin separat erforderlich.
