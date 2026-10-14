# Gemeinsamer Arbeitsstand

Dieses Protokoll dient der Übergabe zwischen Mahmoud, Moayed, Claude Code und Codex. Neueste Einträge stehen oben. Gemeinsame Regeln und fachlicher Überblick: [CLAUDE.md](../CLAUDE.md). Messreihen und Entscheidungen über Agentenvarianten: [EXPERIMENT_PROTOKOLL.md](EXPERIMENT_PROTOKOLL.md).

Pro abgeschlossener Arbeit knapp festhalten: Datum und Bearbeiter, Änderung und Grund, tatsächlich ausgeführte Prüfungen, offene Punkte. Frühere Messergebnisse als solche kennzeichnen. Ein geplanter Schritt ist noch kein Auftrag zur Umsetzung. Änderungen werden für das andere Teammitglied erst nach Übertragung über Git und Aktualisierung seiner Arbeitskopie sichtbar; Chatverläufe gehören nicht automatisch dazu.

## 14.10.2026 – Codex mit Moayed: Statistik nach Karte korrigiert

**Auftrag:** `compare_report.py` korrigieren, Gewichte unverändert lassen, für Mahmoud/Claude Code dokumentieren und die geprüfte Änderung in `main` veröffentlichen. Ausgangspunkt `839dacc`, Arbeitszweig `fix/paired-seed-bootstrap`.

**Änderung:** Der gepaarte Bootstrap zieht jetzt ganze Karten mit ihren beiden Spielseiten. Kandidat und Referenz werden nach Gegner/Seed/Seite gepaart; anschließend wird die Seitendifferenz je Karte gemittelt. 5000 Bootstrap-Wiederholungen, Zufallsseed 0, 95-%-Perzentilintervall für die mittlere Differenz. Zeilen- und Kandidatenreihenfolge beeinflussen die Berechnung nicht. Die Anzeige trennt Karten von Spielen und zeigt WR beider Agenten sowie ihre Differenz auf derselben gemeinsamen Kartenmenge.

**Eingaben und Grenzen:** Doppelte Spielschlüssel, unvollständige Karten, fehlende/ungültige Ergebnisse und Vergleiche ohne gemeinsame Karten werden abgewiesen. Nicht gemeinsame Karten werden ausdrücklich als ausgeschlossen ausgewiesen. Bei nur einer gemeinsamen Karte wird kein KI geschätzt. Alle Dateien werden vor der Berichtsausgabe validiert, um irreführende Teilberichte zu vermeiden. CLI-Aufruf bleibt `python -m scripts.compare_report --ref REFERENZ.csv KANDIDAT.csv`; bewusst passende Test-/Validierungsdateien auswählen. Alte CSVs ohne Punktezählungs-Version bleiben für den Siegvergleich verwendbar, denn das Skript nutzt ausschließlich `result`.

**Prüfung:** Ein neuer CLI-Regressionstest zeigte den alten Fehler zunächst mit einem Intervall von [−1; +1], obwohl die mittlere Seitendifferenz auf jeder Karte null war. Nach der Korrektur [0; 0]. Insgesamt **26 neue Tests**, einschließlich exakt nachvollziehbarer Zwei-Karten-Verteilung, Zeilenreihenfolge, Gegnertrennung, gemeinsamer Vergleichsmenge, ungültiger Eingaben und Einzelkartenfall. Vollständige Testsuite: **131 bestanden in 30,15 Sekunden**. Unabhängiger Review: 26 fokussierte Tests erneut bestanden, keine offenen Befunde. Keine neuen Benchmarkspiele und kein neues Modelltraining; nur bestehende Tests mit temporären Trainingsdateien.

**Neu berechnete Resultate:** Drei vorhandene Vergleichspaare, je zwei Gegner, ohne Änderungen an den historischen Rohdaten: [Statistikprüfung mit Tabelle und Aufrufen](STATISTIK_20261014.md), [Ergebnisse und Quellprüfsummen](../experiments/analysis/paired_bootstrap_20261014.json). Wichtig für die Folien: `m1_early` Runde 1 gegen Solution_92 hat jetzt KI [0,00; +18,33] pp, also keinen allein dadurch belegten klaren Vorteil. Runde 2 bleibt bei +7,92 pp mit KI [+2,50; +13,75] pp. Die übrigen historischen Intervalle wurden nicht pauschal neu berechnet. Das aktuelle Abgabe-Ensemble bleibt `old3_sym3`.

**Gewichte:** Beide Abgabe-Dateien weiterhin SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`. Sie passen zum aktuellen Agenten und wurden zuvor auf beiden Seiten in 120 Spielen geprüft. Dass beide Dateien identisch sind, ist beim seitenübergreifenden Ensemble beabsichtigt. Die Statistikänderung erfordert keine Anpassung oder neues Training. Über eine spätere bessere Version entscheidet ein separater Entwicklungs-/Validierungsschritt, nicht eine nachträgliche Änderung dieser Zahlen.

**Übergabe:** Nach dem Upload `main` aktualisieren und diese Notiz lesen. README, CLAUDE.md, Experimentprotokoll und Präsentationscheckliste sind angepasst. Keine Änderungen an Agent, Reward, Kurs-Runner, bisherigen Rohdaten oder Gewichten. Die konkrete Veröffentlichung wird durch die Git-Historie und den abgeglichenen Remote-Stand bestätigt.

**Weiterhin offen:** Zeitliche Ausrichtung der Erkundungsdiagnose, Reward-/Einheiten-Übergänge, neuer zurückgehaltener Testsatz für November sowie Folien und Vortragsvorbereitung. Mehrfachvergleiche und Modellauswahl auf bekannten Karten werden durch den Karten-Bootstrap nicht korrigiert. `scripts/report.py` bleibt die separate Zwei-Ebenen-Auswertung für Trainingsstarts.

## 14.10.2026 – Codex mit Moayed: vollständige Punktezählung

**Auftrag:** Punktezählung korrigieren, aktuelle Gewichte unverändert lassen und die Änderung für Mahmoud/Claude Code dokumentieren. Ausgangspunkt `9edac5f`, Umsetzung auf `fix/complete-point-counting`; geprüfte Änderung zur gemeinsamen Nutzung in `main` übernehmen.

**Ursache und Änderung:** LuxAI S3 zählt im letzten Matchschritt noch Punkte, setzt den sichtbaren Stand aber im selben Schritt auf null. Die bisherige Addition der sichtbaren Maxima unterschlug diesen Zuwachs. `scripts/scoring.py` rekonstruiert ihn aus dem nach der Aktion gespeicherten `info["final_state"]`: belegte aktive Punktefelder je Team, nur lebende Einheiten mit Energie ≥ 0, gestapelte Einheiten zählen einmal. `scripts/common.py` summiert vollständige Zuwächse; `analyze_losses.py` und `analyze_timing.py` melden ebenfalls vollständige Matchpunkte. Agentencode, Beobachtungen für den Agenten, Trainingsbelohnungen und Kurs-Runner bleiben unverändert.

**Datenformat und historische Ergebnisse:** Neue CSV-Zeilen tragen `point_counting_version=2`, auch in Training und Validierung. Ohne diese Spalte handelt es sich um historische Version 1; deren Punkte, Punktedifferenzen und Punkt-Siegquoten bleiben unvollständig. Alte Rohdateien nicht überschreiben oder mit Version 2 mischen. In neuen Diagnosen bedeutet −1 bei `first_score`, `opp_first_score` und `first_score_step` „nie gepunktet“; 101 bezeichnet den ersten Punkt im letzten Schritt. Die Kennzeichnung der Sichtbarkeitszeiten ändert sich nicht. Details und Migrationshinweise im [Experimentprotokoll](EXPERIMENT_PROTOKOLL.md#messkorrektur-vom-14102026-vollständige-punkte).

**Tatsächliche Prüfungen:**

- Sechs Regressionstests reproduzierten die Unterzählung auf beiden Seiten in gemeinsamer Spielauswertung und beiden Diagnoseskripten. Referenz: dieselbe echte Engine, derselbe Zustand, dieselben Aktionen und Zufallszahlen; nur der Reset wurde für den Referenzschritt verschoben, um die Endpunkte direkt zu lesen. Beispiel Seed 900011 gegen default als player_0: **1866:58 statt 1830:57**.
- Neue Prüfungen decken außerdem Stacking, Energie null/negativ, tote Einheiten, inaktive Relics, Nullpunkte, reine Schluss-Schritt-Punkte, Replay-Wrapper, fehlenden Endzustand und CSV-Versionskennzeichnung ab. Ein unabhängiger Review fand die Mehrdeutigkeit von 101 als „nie“ und als letzter Schritt; durch −1 und vier zusätzliche Diagnosefälle behoben und erneut geprüft.
- Abschließend **105 Tests bestanden in 28,71 Sekunden**, davon **17 neue Tests**. Der unabhängige Review meldet keine offenen Befunde.
- Alle **120 historischen Benchmarkspiele** des unveränderten Sechser-Ensembles neu gespielt (106,66 Sekunden). Jede bisherige Nicht-Punkte-Kennzahl je Spiel stimmt überein, Laufzeiten ausgenommen. Siege weiterhin **60/60 gegen default**, **28/60 gegen Solution_92**. Neue vollständige Daten: [CSV](../experiments/compare/TEST_old3_sym3_points_v2.csv), [Prüfsummen, Versionen und Wiederholungsanleitung](../experiments/compare/TEST_old3_sym3_points_v2.json). Mittlere Gesamtpunkte je Spiel: 1076,25:120,47 bzw. 741,52:883,25. Keine neuen Karten zur Modellauswahl verwendet.
- Beide Abgabe-Gewichte behalten SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`. Keine Änderungen unter `agents/` oder `lux/`, an `main.py`, `Paths.csv` oder historischen Experimentdateien. Kein neues Modelltraining außerhalb der bestehenden Tests mit temporären Dateien.

**Veröffentlichungsstand:** Nach Moayeds lokaler Entsperrung funktioniert SSH wieder. Erneuter Abruf bestätigte, dass auf GitHub keine zusätzlichen Änderungen seit `9edac5f` vorlagen. Die geprüfte Korrektur `03c5e3a` wurde erfolgreich ohne erzwungenes Überschreiben nach `origin/main` hochgeladen. Die frühere SSH-/GitHub-App-Blockade ist für diesen Upload damit erledigt; die lokale SSH-Konfiguration wurde nicht geändert.

**Für Mahmoud:** Jetzt die eigene Arbeitskopie von `main` aktualisieren und diesen Eintrag mit Claude Code lesen. Neue Läufe erhalten die korrekte Zählung automatisch. Für die Präsentation können die neuen Benchmarkdaten verwendet werden; alte Punktevergleiche anderer Modelle müssen mit den jeweiligen Originalgewichten in neue Dateien neu gemessen werden. README und Präsentationscheckliste sind angepasst.

**Weiterhin offen:** Bootstrap nach Karte in `compare_report`, zeitliche Ausrichtung der Erkundungsdiagnose, Reward-/Einheiten-Übergänge sowie Folien und Vortragsvorbereitung. Diese Korrektur verbessert die Messung, nicht die Spielstärke, und hebt die übrigen Einschränkungen nicht auf.

## 14.10.2026 – Codex mit Moayed: Überschreibschutz in main übernommen

**Auftrag:** Den geprüften Überschreibschutz in `main` übernehmen, damit Mahmoud ihn direkt nutzen kann; aktuelle Gewichte unverändert lassen.

**Übernahme:** Nach erfolgreichem Abruf von GitHub gab es keine zusätzlichen Änderungen auf `origin/main`. Commit `2038efd` wurde ohne Konflikte per Fast-forward in das lokale `main` übernommen. Dieser gemeinsame Stand ist für die Veröffentlichung auf GitHub vorgesehen; die folgende Git-Historie dokumentiert die Übernahme.

**Prüfung auf main:** Alle **88 Tests bestanden in 21,04 Sekunden**. Agentencode, Kurs-Runner, `main.py` und `Paths.csv` stimmen weiterhin mit dem Stand vor der Schutzänderung überein. Beide Abgabe-Gewichte behalten SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.

**Für Mahmoud:** Nach dem Upload genügt es, die eigene Arbeitskopie von `main` zu aktualisieren; ein Wechsel auf den Entwicklungsbranch ist nicht mehr nötig. Die Anleitung steht in [README: Sicher trainieren und fortsetzen](../README.md#sicher-trainieren-und-fortsetzen). Die übrigen fachlichen Korrekturen bleiben offen und sind weiterhin nicht beauftragt.

## 14.10.2026 – Codex mit Moayed: Abgabe-Gewichte beim Weiterarbeiten schützen

**Auftrag und Umfang:** Überschreiben der aktuellen Abgabe-Gewichte verhindern; Lernverfahren und trainierte Gewichte erhalten. Arbeit auf `fix/protect-submission-weights`, ausgehend von `c831ab3`.

**Änderungen:**

- `scripts.train` erzeugt pro Aufruf einen neuen Run-Ordner unter `experiments/runs/`; alternativ `--output-dir` mit einem noch nicht vorhandenen Ordner. Laufprotokoll, beide Gewichte, Bestmodell und Self-Play-Schnappschüsse liegen gemeinsam dort, auch beim Abbruch.
- `--resume` braucht jetzt einen expliziten Einzelnetz-Checkpoint. Seine gespeicherte Konfiguration wird übernommen; die Quelldatei wird nicht geändert. Der Replay Buffer wird nicht geladen. Ensembles werden abgewiesen, statt still nur deren erstes Mitglied weiterzutrainieren.
- Gemeinsame Prüfung der Ausgabeziele gegen den Abgabe-Gewichteordner, einschließlich symbolischer Links und Hardlinks.
- Beim Prüfen der Speicherwege fiel zusätzlich auf: `build_submission --from-run` ersetzte bisher die Abgabe-Dateien, bei fehlender zweiter Datei sogar teilweise. Es verpackt die ausgewählten Run-Gewichte jetzt direkt. Eingabe-Checkpoints dürfen nicht als ZIP-Ausgabe überschrieben werden.
- README und CLAUDE.md beschreiben die neuen Aufrufe und die Grenzen des Schutzes. Agentencode und Kurs-Runner bleiben unverändert; deren direkte Speicheraufrufe sowie andere Skripte sind keine allgemein gesperrten Dateioperationen. Für Vorführungen `main.py` weiterhin mit `train=False` nutzen.

**Prüfung:**

- 62 bestehende Tests vor der Änderung bestanden. Die erste Gruppe von 16 Regressionstests schlug mit dem alten Code fehl und bestand nach der Korrektur. Der unabhängige Review deckte zusätzlich verschachtelte Hardlinks, Groß-/Kleinschreibungs-Aliase auf macOS und inkompatible Resume-Checkpoints auf; auch diese Fehler wurden erst reproduziert und dann behoben.
- Abschließend **88 Tests bestanden in 21,90 Sekunden**, davon **26 neue Schutztests**. Darunter echte Trainings-/Evaluationsspiele mit kleinem Einzelnetz in temporären Ordnern, Self-Play-/Bestmodell-Speicherung, Abbruch-/Fehler-Speicherung, fehlende oder inkompatible Checkpoints, Ensemble-Ablehnung und Paketbau. Der Reviewer prüfte die Korrekturen nochmals unabhängig; keine offenen blockierenden Befunde.
- Das Standardpaket und ein Paket mit `--from-run` wurden separat gebaut, entpackt und auf beiden Seiten mit dem echten Sechser-Ensemble geladen und auf einer Beobachtung ausgeführt. ZIP-Inhalte, verwendete Quellgewichte und Abgabe-Gewichte per SHA-256 verglichen; unverändert.
- Beide Abgabe-Dateien behalten SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`. Keine Änderungen unter `agents/` oder `lux/`, an `main.py` oder `Paths.csv`. Diff-Prüfung ohne Befund.

**Für Mahmoud:** Ursprünglich auf dem separaten Branch `fix/protect-submission-weights` bereitgestellt; inzwischen auf ausdrücklichen Auftrag in `main` übernommen, siehe neuesten Eintrag oben. Neue CLI-Beispiele stehen in [README: Sicher trainieren und fortsetzen](../README.md#sicher-trainieren-und-fortsetzen). Ein alter Aufruf mit bloßem `--resume` muss einen Dateipfad zu einem passenden Sherlock-Einzelnetz-Checkpoint mit Config erhalten. Das aktuelle Sechser-Ensemble bleibt für die Präsentation unverändert. Die Messfehler und Reward-/Einheiten-Probleme aus der ursprünglichen Prüfung sind durch diesen Speicherschutz nicht behoben. Ein längerer Trainingslauf wurde nicht gestartet.

## 14.10.2026 – Codex mit Moayed: SSH-Zugriff und Veröffentlichung

**Auftrag:** Vorbereitete Dokumentationsänderungen auf GitHub hochladen, damit Mahmoud sie in seiner Arbeitskopie mit Claude Code verwenden kann. Agent, Trainingsskripte und Gewichte weiterhin nicht verändern.

**Zugriff eingerichtet und geprüft:** GitHub akzeptiert Moayeds bereits vorhandenen RSA-Schlüssel für den Account `ShaweshMoayed`. Die lokale Git-Konfiguration dieses Repositorys wählt diesen Schlüssel ausdrücklich aus; keine neuen Schlüssel und keine globalen SSH-Einstellungen angelegt. Die lokale Schlüsselkonfiguration wird nicht mit Git übertragen und ist auf Mahmouds Rechner nicht erforderlich.

**Synchronisierung:** `git fetch origin` erfolgreich. Vor der Veröffentlichung stimmen lokales `main` und `origin/main` auf Commit `40f236c7b418a3c9da407cd3129a760a7b5678cd` überein; keine fremden Änderungen zusammenzuführen. Der Veröffentlichungsumfang besteht aus genau fünf Dokumentationsdateien: AGENTS.md, CLAUDE.md, README.md, diesem Arbeitsstand und der Review-Checkliste. Der konkrete Commit und sein Upload werden über die Git-Historie nachvollziehbar.

**Übergabe:** Nach dem Upload kann Mahmoud sein `main` aktualisieren und Claude Code den neuesten Eintrag dieses Arbeitsstands lesen lassen. Die frühere SSH-Blockade und die damalige Einschränkung auf rein lokale Dokumentation sind damit überholt. Die offenen fachlichen Aufgaben unten bleiben unverändert; ihre Umsetzung ist noch nicht beauftragt.

## 14.10.2026 – Codex mit Moayed: gemeinsame Dokumentation

**Freigegebener Umfang:** Gemeinsame Dokumentation einrichten, README und Review-Checkliste aktualisieren. Agentencode, Trainingsskripte und Gewichte bleiben unverändert. Weitergehende Fehlerbehebungen und Experimente sind noch nicht beauftragt.

**Änderungen und Grund:**

- AGENTS.md verweist für Codex auf die gemeinsame CLAUDE.md und dieses Übergabeprotokoll. CLAUDE.md enthält dieselbe Dokumentationsregel für Claude Code.
- README beschreibt den aktuellen Abgabe-Agenten `old3_sym3` (sechs Netze), trennt seine Ergebnisse vom historischen Einzelnetz-Batch und benennt bekannte Grenzen der Auswertung.
- Review-Checkliste trennt belegte Projektinhalte von noch zu prüfenden Folien und Vortragsvorbereitung.
- Erste Präsentation am 16.10.: ungefähr zehn Minuten Vortrag laut Moodle-Aufgabe „Submission 1“, Upload bis 08:00 Uhr. Laut Moayed sind die Slots 20 Minuten lang. Die Aufteilung der restlichen Zeit für Fragen/Puffer ist eine Vermutung; auch die genaue Vortragsdauer späterer Termine ist noch zu bestätigen.

**Prüfgrundlage und Nachweise:**

- Lokaler Ausgangsstand: Commit `40f236c7b418a3c9da407cd3129a760a7b5678cd`. Alle 587 versionierten Dateien waren vor dieser Änderung identisch mit der bereits geprüften Projekt-ZIP.
- Frühere technische Prüfung vom 14.10. in separater Kopie: 62 Tests bestanden, 120 Spiele des Abgabe-Ensembles reproduziert, Paket auf beiden Seiten geladen und über den Kurs-Runner gespielt. Das sind keine im Rahmen dieser Dokumentationsänderung neu ausgeführten Tests.
- Ausführlicher Prüfbericht und Rohbelege liegen bei Moayed lokal im benachbarten Ordner `Pruefung_2026-10-14/`; sie sind nicht Bestandteil dieses Repositorys. Die wichtigsten offenen Befunde stehen unten, damit die Übergabe nicht von diesem Ordner abhängt.
- Prüfung dieser Dokumentationsänderung: `git diff --check` ohne Befund; alle relativen Dateilinks der fünf bearbeiteten/neuen Dokumente auf vorhandene Ziele geprüft. Aktuelle Ergebniszahlen direkt mit der CSV (60/60 und 28/60) und Trainingsumfang mit allen 34 Manifesten (99.000 Spiele) abgeglichen. Alle 584 übrigen Originaldateien sind bytegleich mit der geprüften ZIP, einschließlich Agent, Skripten, Gewichten und Experimentdaten. Keine neuen Trainingsläufe oder Spieltests für diese reine Dokumentationsänderung ausgeführt.

**Offene Punkte, keine bereits umgesetzten Korrekturen:**

1. Präsentationsdatei erstellen/exportieren, Inhalte gegen die Checkliste prüfen, Slot/Buchung bestätigen, Replays im Viewer ansehen und auf etwa zehn Minuten proben. Frühere Notizen erwähnen einen externen Folienentwurf; dessen aktueller Export liegt nicht im Repository.
2. Historischer Befund: `scripts/train.py` überschrieb die Abgabe-Gewichte und trainierte bei Ensembles nur ein Mitglied. Für dieses Skript durch neue Run-Ordner und Ablehnung von Ensemble-Resume behoben; siehe neuesten Eintrag. Ein gemeinsames Ensemble-Training bleibt unimplementiert.
3. Historischer Befund: Der letzte Punktezuwachs vor dem Match-Reset fehlte. Für neue Messungen mit `point_counting_version=2` behoben; siehe neuen Eintrag oben. Historische Dateien ohne Versionsspalte bleiben unvollständig. Siegquoten aus `team_wins` sind nicht betroffen.
4. Historischer Befund: `scripts/compare_report.py` resampelte einzelne Spiele; durch den gepaarten Karten-Bootstrap am 14.10. behoben, siehe neuen Eintrag oben. Alte Intervalle nur nach Neuberechnung weiterverwenden. Alte Testkarten wurden mehrfach ausgewertet; für November einen neuen, bis zur finalen Entscheidung unangetasteten Testsatz festlegen. Bestehende historische Rohdaten nicht überschreiben.
5. Vor weiterem Training gezielt prüfen/korrigieren: wiederverwendete Einheiten-IDs bei Tod und Respawn, Punktebelohnung bei negativer Energie und terminales Potential beim Reward Shaping. Passende Regressionstests ergänzen.
6. `scripts/analyze_timing.py` vergleicht eigene Beobachtung vor dem Schritt mit gegnerischer Sicht danach. Genaue Zeitvergleiche benötigen denselben Beobachtungszeitpunkt.
7. `scripts/report.py` deckt den ursprünglichen Varianten-Batch ab, nicht automatisch alle späteren Ensemble-/Self-Play-Vergleiche. Historische Gewichte fehlen teilweise; neue Läufe sollten Modell-Hashes und Softwareversionen mitführen.
8. `m1_early` bleibt der dokumentierte Kandidat für nach dem Review. Aktuelle Abgabe bleibt `old3_sym3`.
9. Historischer Stand dieser ersten Prüfung: SSH-Zugriff scheiterte mit `Permission denied (publickey)`; Commit und Push waren noch nicht beauftragt. Durch den anschließenden Auftrag und die Schlüsselkonfiguration überholt, siehe neuesten Eintrag oben.
