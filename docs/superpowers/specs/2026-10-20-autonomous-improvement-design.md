# Selbstständige Verbesserung von Sherlock

## Auftrag

Moayed hat am 20.10. ausdrücklich beauftragt, den neuesten Stand zu prüfen,
einen Plan zu entwickeln und ihn anschließend selbstständig abzuarbeiten,
zu testen und geprüfte Änderungen zu pushen. Mahmoud/Claude arbeitet laut
Moayed derzeit nicht weiter. Rückfragen zu gewöhnlichen Umsetzungsschritten
sind nicht erforderlich. Diese Anweisung ersetzt die sonst üblichen einzelnen
Planfreigaben; Ergebnisse und Entscheidungen müssen nachvollziehbar bleiben.

## Ziel und Ausgangspunkt

Mehr Siege auf bisher nicht zur Auswahl verwendeten Karten und gegen
verschiedene Gegner, bei zuverlässigem Kursbetrieb. Kein Versprechen einer
bestimmten Siegquote. Ausgangspunkt `1cadc18`: Referenz `all18_v3`, ältere
Referenz `all18_fo10`, CNN2-PPO als weiterer vorhandener Ansatz.
Mahmouds CNN3-Pipeline wird laut Protokoll noch ausgeführt; Prozessstatus
auf seinem Rechner unbekannt. Kein doppeltes CNN3-/BC-Training starten.

## Verbindliche Grenzen

- Neue ausdrückliche Freigabe vom 20.10.: Abgabe-Dateien
  `agents/sherlock/weights/agent_p0.pth` und `agent_p1.pth` dürfen nach
  bestandener Übernahmeprüfung unten ersetzt werden. Bis dahin unverändert.
  Beide bisherigen SHA-256:
  `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.
  Vorab geprüfte, versionierte Sicherung:
  `experiments/releases/20261020_old3_sym3/`. Diese bleibt unverändert.
- Vorhandene Kandidaten nicht überschreiben; neue Ergebnisse in neue Dateien.
- Kurs-Runner `lux/runner.py` unverändert lassen.
- Keine versteckten Umgebungsinformationen als Agentenfeatures oder Reward.
- Keine zusätzlichen kostenpflichtigen Dienste oder Cloud-Trainings buchen.
- M3 / 8 GB: maximal zwei Evaluationsprozesse; höchstens ein Training
  gleichzeitig, keine parallele große Testsuite während eines Trainings.
- Moayed hat den Arbeitszeitraum ausdrücklich bis **21.10.2026, 04:00 UTC /
  06:00 Berlin** verlängert. Ab 05:30 Berlin nur noch rechtzeitig abschließbare
  Prüfungen starten. Um 06:00 Arbeiten kontrolliert abschließen und Morgenbericht
  im Chat und Repo liefern. Die frühere Grenze 23:15 UTC ist aufgehoben.
- Nur getestete Änderungen pushen; vor jedem Push GitHub abgleichen.
  Direkte kleine Commits auf `main` sind vom Team autorisiert.
- Lokale Dateien anderer Arbeiten, insbesondere `.DS_Store`, erhalten.

## Vorgehen

1. Vollständige vorhandene Testsuite, reproduzierbarer Kandidatentest und
   Kurs-Runner auf beiden Seiten mit wiederholten Spielen.
2. Begrenzte Entwicklungsmessung mit unveränderten Netzen:
   `all18_v3` plus vier vorab festgelegte Einzelvariationen:
   `pt_sap_reserve=30`, `pt_sap_reserve=60`, `far_opp=6`, `far_opp=14`.
   Die Fragen sind ausreichende Energie nach Sap und bessere Reichweite
   der Zielpriorisierung. Keine blind wachsende Parametersuche.
3. Auswahl nur auf bereits verwendeten Entwicklungskarten 500720–500779
   (60 Karten, beide Seiten, default und Solution_92). Referenz frisch
   mit identischem Code auswerten. Auswahlmetrik ist der Mittelwert von
   `result` (Sieg 1, Remis 0,5, Niederlage 0), wie in `compare_report`;
   reine Siegzahlen zusätzlich berichten. Genau ein eindeutiger bester
   Kandidat muss die Referenz übertreffen; Gleichstand bedeutet keine Änderung.
   Varianten mit mehr als zwei Prozentpunkten Verlust gegen default ausschließen.
4. Höchstens einen ausgewählten Herausforderer auf neuen Karten prüfen:
   **502420–502619**, beide Seiten, beide Gegner; dieser Block ist hiermit
   für diese Bestätigung reserviert. Den Block nicht zur erneuten Auswahl
   unter mehreren Konfigurationen verwenden. Auch negatives Resultat behalten.
5. Zusätzlich Referenz und Herausforderer auf Entwicklungskarten gegen die
   alte Abgabe prüfen. Kein neuer Kandidat bei klarer Verschlechterung
   der Robustheit. Größere Stichprobe als eigener Folgeschritt, falls unklar.
6. Ein neuer Kandidat wird nur gespeichert, wenn die Bestätigung einen
   positiven gepaarten 95%-Karten-Bootstrap-Bereich gegen Solution_92 ergibt,
   default nicht um mehr als zwei Prozentpunkte sinkt und kein technischer
   Fehler vorliegt. Das ist eine pragmatische Auswahlregel, kein Beweis gegen
   unbekannte Gegner und kein Ersatz für spätere unabhängige Turniertests.
7. Falls keine Variante bestätigt wird: Referenz behalten, Gründe
   dokumentieren. Kein langes Training allein zur Auslastung des Rechners.
   Neuer Trainingsplan erst aus konkretem Befund; vorhandenes CNN3-Ergebnis
   gegebenenfalls prüfen, wenn es veröffentlicht wird.

## Abnahme und Übergabe

Prüfungen, Seeds, Config, Checkpoint-Hash, Codeversion und Grenzen speichern.
Runner-Bericht enthält Seiten/Gegner, wiederholte Spiele, gültiges Aktionsformat,
Initialisierung des Gedächtnisses und gemessene Entscheidungszeiten.
Kein unbekanntes Kurs-Zeitlimit erfinden; Zeiten berichten, Grenzwert offen benennen.
Entwicklungs- und Bestätigungsergebnisse getrennt halten. Ältere Ergebnisse
bleiben mit ihrem damaligen Stand gültig.

## Übernahme in die Abgabe – ergänzende Freigabe vom 20.10.

Die Auswahl unter den vier Varianten bleibt unverändert. Falls keine davon
bestätigt wird, kommt ausschließlich die vorab festgelegte Referenz `all18_v3`
als möglicher Ersatz der alten Abgabe infrage. Keine neue Parametersuche.

Die alte Abgabe zusätzlich auf denselben frischen Seeds 502420–502619 gegen
default/Solution_92 auswerten. Für die Übernahme muss der ausgewählte Stand
gegenüber der alten Abgabe einen positiven gepaarten 95%-Karten-Bootstrap-Bereich
gegen Solution_92 erreichen, darf gegen default höchstens zwei Prozentpunkte
verlieren und muss die Kursprüfung auf beiden Seiten bestehen. Wenn die vier
Varianten keinen Herausforderer liefern, V3 und alte Abgabe trotzdem auf
diesem Block vergleichen. Ein direkter Vergleich gegen die gesicherte alte
Abgabe auf 60 Entwicklungskarten ergänzt diese Prüfung; bei klarer Schwäche
oder technischen Fehlern nicht übernehmen.

Ein neuer experimenteller Herausforderer muss zusätzlich die ursprünglichen
Kriterien gegenüber V3 erfüllen. Diese Zusatzprüfung ist vor Sichtung des
Bestätigungsblocks festgelegt. Falls Zeit oder Beleg fehlen, alte Abgabe
behalten und offenen Schritt dokumentieren.

Vor dem Austausch Sicherung anhand Manifest prüfen. Nach dem Austausch
beide Abgabedateien gegen den gewählten Kandidaten prüfen, Kursprüfung und
betroffene Tests ausführen. Bei Fehlern gesicherte Dateien wiederherstellen.
Übernahme als eigenen Commit mit Ergebnisbericht, Herkunft, alten/neuen Hashes
und Rückweg dokumentieren. Trainings-Überschreibschutz nicht lockern.

## Verlängerung bis 06:00 – Auftrag vom 20.10.

Nach dem ersten begrenzten Zyklus weitere sachlich begründete Diagnose-,
Verbesserungs- und Trainingsschritte selbstständig bearbeiten. Vor jedem neuen
Versuch Hypothese, Vergleichsstand, Auswahlregel und Karten schriftlich festlegen.
Keine Bestätigungsdaten als neue Entwicklungsdaten benutzen und anschließend
auf denselben Karten Erfolg behaupten. Neue remote Ergebnisse vor eigener
Trainingsplanung prüfen; Mahmouds CNN3-/V3-Netz-Pipelines nicht duplizieren.
Weitere Bestätigungsblöcke erst nach Abgleich mit Remote eindeutig reservieren.

Wenn keine sinnvollen Schritte mehr offen sind, keine künstlichen Läufe starten;
Bericht vorbereiten. Die automatische Fortsetzung bleibt für den Morgenbericht
um 06:00 eingerichtet und wird danach deaktiviert. Bericht enthält vollständige
Spielzahlen/Gegner/Karten, gescheiterte Ansätze, belegte Änderungen mit Unsicherheit,
Abgabestand, Sicherung, tatsächlich gepushte Commits und offene Arbeit.
