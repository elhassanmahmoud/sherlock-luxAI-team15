# Unabhängiger enger Leistungsaudit – Textentwurf

**TEXT PREPARATION / UNRUN.** Keine Imports, Syntaxcompile, Tests, Tensorloads, Forwards, Datenanalysen oder Spiele ausgeführt. Die laufenden Trainingsdaten wurden nicht gelesen. Der bereits vorbereitete Trainingsauditor bleibt unverändert und hat Vorrang. Beide Audits dürfen jeweils erst nach vollständigem Ende aller zugehörigen Modellworker, Supervisor und Wachhalter und einer ausdrücklichen Root-Anweisung tatsächlich laufen. Der Endstate ist kein unabhängiger OS-Prozessnachweis; diesen Abschluss prüft Root separat.

## Umfang und eingefrorene Entwurfsbezüge

Genau zehn CSVs mit je40 vollständigen Spielen: vier finale Einzelnetze je gegen Solution_92 und sol92_sq auf9930000–9930019/beide Seiten, dazu je Start45/46 Sampled gegen die zugehörige Control-Inferenzkopie auf9930100–9930119/beide Seiten. Insgesamt400 Spiele. Keine V14-Leistungsmessung, neue Modelle, Ausweitung oder Promotion.

- Auditor `/tmp/sampled-target-performance-audit.py`,479 Zeilen, SHA256 `9a5feb220537cc75abdb72dbeb6fe76f9e10239e0eb357ec9436ec67b744e692`.
- Unabhängiger bereits früher verfasster Hashsupport `/tmp/sampled-target-technical-audit.py`, SHA256 `384a0467a64e5b23a8e81cb5134321c79c0cad78c39a55e5411b3b324c14a408`. Er wird vor Import gehasht, sein Hauptprogramm nicht ausgeführt. Kein Projekt-/Studien-/Statistikhelper wird importiert.
- Gesicherter externer Compare-Entwurf `/tmp/sampled-target-performance-compare-interface-draft.py`, SHA256 `ea5b853ed7981ebe87d684210c98f7ee1bac8ea383e9f30fd2a744496703a9ea`.
- Gesicherter externer Eval-Entwurf `/tmp/sampled-target-performance-eval-interface-draft.py`, SHA256 `96e72e72652f9f9b4644480f468ba812705b9b812bcd2963f46ce98ef1fbe1f5`.
- Fachlicher Maßstab: `docs/superpowers/specs/2026-11-08-sampled-target.md`; Task4-Schnittstelle aus `/tmp/sampled-target-performance-staging/README.md` und den beiden externen Entwürfen. Historischer Trainings-HEAD bleibt `945e1938a1fb1fcc87eeaf10b58138a409266581`.

Die Entwurfshashes sind **keine** späteren Leistungsquellen-Pins: Bereits die Einsetzung des tatsächlichen historischen Abnahmehashs ändert Compare. Vor Ausführung verlangt der Auditor deshalb den dann von Root unabhängig geprüften vollständigen Leistungs-HEAD und die tatsächlichen beiden Datei-SHAs als explizite CLI-Pins. Eventuelle Schemaänderungen nach Task4-Review müssen vorher textlich abgeglichen werden. Es existieren hier noch keine echten Leistungsresultate oder Zahlen.

## Prüfschritte

1. Extern gepinnten Endstate prüfen: Statuscomplete,400 erwartete und abgeschlossene Spiele, genau zehn erfolgreich beendete Jobs, leere active/queue und abgeschlossener Wachhalter. Erst danach NumPy/Torch für eigene Statistik und sichere Tensorcontainerprüfung importieren.
2. Quelleninventar einschließlich Engine/Interpreter neu aus Dateien und Gitliste abgleichen; tatsächlicher HEAD und beide Root-geprüften Task4-Codehashes müssen stimmen. Vollständige Inputs sowie V14 und ZIP erneut hashen. Keine Projektimports.
3. Historische Trainingsaufnahme gegen ihren expliziten Root-Pin lesen. Die800 Studienausführungen, vier Technikspiele, ursprünglichen Validatoren, unabhängigen Trainingsaudit, alle vier finalen Receipts samt14Artefakten und beide Vorlaufgates erhalten. Hier wird deren historische vollständige Abnahme gebunden, nicht nach dem HEAD-Wechsel als erneut ausgeführter Trainingsaudit dargestellt.
4. Alle vier Inferenzkopien direkt mit `torch.load(weights_only=True, map_location="cpu")` als Container lesen. Die Config entspricht exakt der gemeinsamen V14-Quellconfig mit ausschließlich frozen=False. Sämtliche Nicht-Config-Inhalte müssen typisiert bitidentisch zum jeweiligen finalen Trainingscheckpoint sein. Einzelnetz, Zähler, endliche Q-/Targettensoren und vollständige Rollen-/Dateihashes prüfen. Keine Netzinstanz und keine Forwardrechnung.
5. Plan elementweise gegen acht Paneljobs und zwei Direktjobs rekonstruieren. Feste Kartenlisten und self-Controlpfade, workers1 und keinerlei Overrides. Tatsächliche Receiptbefehle, Quellen, Primär-/Gegnergewichte, Seeddateien und CSV-Hashes müssen passen. Exakt zehn CSV- und zehn Receiptdateien zulassen. Historische PID-/Prozessgruppen-/Owner- und Zeitbindungen sowie maximal zwei überlappende Jobintervalle prüfen; keine nachträgliche Prozesssimulation.
6. Jede der400 Zeilen unabhängig mit `csv.DictReader` lesen. Exaktes24-Felder-Schema, keine fehlenden/zusätzlichen Werte oder doppelten Schlüssel, endliche Zahlen, gültige Ganzzahlen/Fraktionen,303Schritte, Zählversion2. Game-/Pointscore aus aufgezeichneten Match-/Punktzahlen neu ableiten. Vollständige Gegner×Karte×Seite-Matrix ohne Ausschluss verlangen.
7. Eigene Statistik aus ganzzahligen Halb-Siegen: `half_wins=2*wins+draws`, Score=half_wins/(2*games), strikte Siege separat. Sechs exakte Integergates: jeder Panelgewinn>0, Summe beider Gewinne≥16; Direkt jeweils≥40 Halb-Siege und zusammen>80. Diese Gates entscheiden nur das vorab definierte Methodensignal.
8. Pro Start beide Gegner separat, gesamtes Panel und Direktduell berichten. Jeweils20 vollständige Kartencluster; ein Kartenindex zieht beide Seiten und beim Panel beide Gegner gemeinsam.5000Resamples mit ausdrücklich `Generator(PCG64(0))`, pro Intervall neu initialisiert. Eigene lineare2,5-/97,5-Perzentile. Das deskriptive Mittel über Starts45/46 mittelt zuerst dieselbe Karte über beide Starts und zieht anschließend Karten gemeinsam. Keine zufälligen Trainingsstarts oder IID-Spielzeilen vortäuschen.
9. Alle strukturellen/ganzzahligen Werte des vorhandenen Originalsummary exakt, Gleitkommazahlen mit relativer und absoluter Toleranz1e-12 vergleichen. Dessen Eingabehashmap muss exakt dieselben Dateien binden. Sämtliche verwendeten Dateien vor der Ausgabe nochmals hashen. Nur eine neue Ergebnisdatei exklusiv schreiben, bei Fehler Exit1/`AUDIT BLOCKED`, kein PASS-Bericht.

Der Adapter ist absichtlich auf den ursprünglichen Studiencheckout begrenzt (`accepted.root == state.root`). Für die bereits bekannte primäre Schutzkopie ist lediglich die im Task4-Code vorhandene Zuordnung auf dieselbe relative Repositorydatei umgesetzt; beide vorhandenen tatsächlichen Schutzdateien werden zusätzlich gehasht. Keine beliebigen externen historischen Dateien oder automatische Worktree-Rebasierung. Die Aufnahme-/Rohdateninventur kann große Replaydateien erneut hashen, ohne sie als Arrays zu laden.

## Spätere Ausführung – ausdrücklich noch nicht gestartet

```text
<gebundener Interpreter> -B /tmp/sampled-target-performance-audit.py
  --state <absoluter vollständig beendeter Leistungs-state.json>
  --state-sha256 <Root-geprüfter Endstate-SHA>
  --summary <absoluter Originalsummary-Pfad>
  --summary-sha256 <Root-geprüfter Originalsummary-SHA>
  --acceptance-sha256 <Root-gepinnter historischer Trainingsabnahme-SHA>
  --expected-head <vollständiger eingefrorener Leistungs-HEAD>
  --compare-sha256 <tatsächlicher geprüfter sampled_target_compare.py-SHA>
  --eval-sha256 <tatsächlicher geprüfter sampled_target_eval.py-SHA>
  --support /tmp/sampled-target-technical-audit.py
  --out <neue unabhängige JSON-Datei>
```

## Ergebnisvertrag und Grenzen

Bei tatsächlicher erfolgreicher Ausführung enthält der Bericht `status: PASS`, Profil, Trainings-/Leistungs-HEAD, komplette SourceIdentity, beide historischen/aktuellen Quellenbezüge, alle400Spiele/10Jobs, eigene Statistiken einschließlich sechs Gates, Modelle, Originalsummary-SHA, tatsächliche Befehle und vollständige `input_sha256`-Inventur. `promoted` und `eligible` bleibenfalse. **PASS bedeutet vollständige gebundene Daten und reproduzierte Berechnungen; `independent_statistics.passed` kannfalse sein.**

Nur20Kartencluster je Kohorte; unadjustierte Intervalle, zwei feste Starts und keine Aussage über eine Trainingspopulation. Archivierte CSV-Arithmetik und Hash-/Ausführungsketten werden geprüft; ungespeicherte Spieltrajektorien und tatsächliche Runtimeconfigs werden nicht erneut ausgeführt. Die separate synthetische Prüfung der produktiven Ladewege bleibt eigene Evidenz. Keine kausale Stärkeaussage, kein Vergleich gegenV14, keine Freigabe zur Abgabe, Verlängerung oder nächsten Studie. Grenzen des damaligen Seedscans hinsichtlich externer/seedloser Daten bleiben bestehen.

Statische Erstellung und Dateihashes sind die einzigen bisher tatsächlich durchgeführten Prüfungen dieses neuen Auditors. Keine Syntaxgültigkeit oder bestandenen Lauf behaupten.
