# Gemeinsamer Arbeitsstand

Dieses Protokoll dient der Übergabe zwischen Mahmoud, Moayed, Claude Code und Codex. Neueste Einträge stehen oben. Gemeinsame Regeln und fachlicher Überblick: [CLAUDE.md](../CLAUDE.md). Messreihen und Entscheidungen über Agentenvarianten: [EXPERIMENT_PROTOKOLL.md](EXPERIMENT_PROTOKOLL.md).

Pro abgeschlossener Arbeit knapp festhalten: Datum und Bearbeiter, Änderung und Grund, tatsächlich ausgeführte Prüfungen, offene Punkte. Frühere Messergebnisse als solche kennzeichnen. Ein geplanter Schritt ist noch kein Auftrag zur Umsetzung. Änderungen werden für das andere Teammitglied erst nach Übertragung über Git und Aktualisierung seiner Arbeitskopie sichtbar; Chatverläufe gehören nicht automatisch dazu.

## 19.10.2026 – Claude Code mit Mahmoud: Regeln, Reward-Korrekturen, CNN + PPO

**Auftrag:** Nach dem Review (lief laut Mahmoud gut) alles einbauen, was Regeln und Rewards hergeben, plus CNN/PPO (Empfehlung des Prof). Ziel bis 23.10.: default und Solution_92 möglichst immer schlagen. Commit/Push ausdrücklich erlaubt. Arbeitszweig `feat/regeln-rewards` (ab `b37aec3`, Präsi-Stand 15.10. vorher auf `docs/presentation-erkenntnisse` committet).

**Prof-Fragen beim Review und Antworten (belegt):** (1) „Warum 47 % nach 18 000 Spielen?“ – Der Agent ist hybrid: Gedächtnis, Zielzuweisung, Maske und Sap-Ziel sind Regeln, das Netz entscheidet laufen/stehen/sappen. Diagnose auf neuen Val-Karten 500 660–500 719 (`experiments/analysis/rules_vs_net_20261019*`): gleiche Regeln mit einfacher Regel statt Netz 95 % vs default (Netz 92 %), aber nur **3 % vs Solution_92 (Netz 38 %, Δ −34 pp, KI [−45; −23])**. (2) „Belohnung jeden Schritt?“ – Ja, pro Einheit und Schritt (`reward.py`), Matchsieg zusätzlich ±2.

**Ursachenanalyse gegen Solution_92** (Ground Truth, `scripts/analyze_losses.py --set`, Skript `diag_know` im Arbeitsverlauf): Solution_92 kennt die Punkte-Tiles viel früher (Match 1, Step 50: 2,6 vs 0,2). Grund: Es schließt Tiles aus, die von keinem *möglichen* Relic erreichbar sind. Danach bleibt Match 3 die Schwäche (mit allen Regeln Matchsiege 79 / 65 / 36 %).

**Neue Schalter (alle Default aus, alte Checkpoints unverändert):**

| Schalter | Wirkung | Ergebnis vs Solution_92 (100 Val-Karten, gepaart) |
|---|---|---|
| `relic_filter` | Belief ignoriert Units außerhalb jeder möglichen 5×5-Relic-Zone | **+11,0 pp** [+6,0; +16,0] |
| `subset_infer` | Differenzen von Teilmengen-Gleichungen, keine doppelten Gleichungen | +1,5 pp (n. s.), behalten |
| bestehende `explore_grid`, `scripted_explore`, `explore_stale=20` zusätzlich | Erkundung Match 1 | **+10,5 pp** [+2,5; +18,5] |
| `pt_walk`, `pt_hold` | BFS-Weg zu Punkte-Tiles, Punkte-Tile nicht verlassen | ±2 pp, aus |
| `home_penalty`, `home_last_only` | Gegnerhälfte meiden | −3 bis −15 pp, aus (Einheiten in der Gegnerhälfte stören Solution_92) |
| `smart_sap`, `fog_sap`, `fog_any` | abgestimmtes Sap / Sap in den Nebel | −3 bis +1,5 pp, aus |
| `keep_dead`, `cand_quota` | Null-Tiles über Matches merken / Kandidaten-Quote | −3 bis +1 pp, aus |
| `reward_fix` | 3 Reward-Fehler aus der Prüfung 14.10. behoben (ID-Wiederverwendung, negative Energie, terminales Potential) | nur Training |

**Bester Regelstand ohne neues Training** (`old3_sym3` + `early_inference relic_filter subset_infer explore_grid scripted_explore explore_stale=20`): Val 500 720–500 819: default 96,5 → 98,5 %, Solution_92 45,0 → 66,5 %. **Bestätigung auf neuen Karten 500 820–500 919:** default 96,5 → 99,0 % (+2,5 [0,0; +5,5]), **Solution_92 47,0 → 61,0 % (+14,0 [+4,0; +23,5])**.

**CNN + PPO (neu):** `agents/sherlock/cnn_model.py` (16 Kartenebenen 24×24 aus dem Belief → Conv + 3 ResBlocks → pro Unit lokales + globales Merkmal + 79er-Merkmale → Policy 6 Aktionen + Critic), `ppo_agent.py` (PPOAgent mit gleichen Leitplanken, Recorder mit GAE pro Unit-Trajektorie), `scripts/ppo_train.py` (`collect` Lehrer-Spiele, `bc` Nachahmung, `ppo`). Läufe unter `experiments/ppo/<run>/` (Gewichte/Rohdaten gitignored, Abgabe-Ordner gesperrt). Lauf `cnn1`: 800 Lehrer-Spiele (2,8 Mio. Unit-Schritte), BC 6 Epochen, 85 % Übereinstimmung. **BC-Policy allein: default 100 %, Solution_92 58 %** (Lehrer 66,5 %). PPO-Start mit gemeinsamem Critic verschob die Policy (KL 0,02 schon in der reinen Critic-Aufwärmphase) → abgebrochen, neu mit eigenem Critic-Kopf (`--detach-value`). Nach 10 Iterationen 61,5 % (+3,5 n. s.). DQN+CNN-Abstimmung (`cnn=` in `par_eval`): −2 bis −3,5 pp, n. s.

**Neu trainiert:** Variante `full_rules` (alle Regeln + `reward_fix`), 6 Starts × 3000 Spiele, `--no-test`, je 93 min. Ensemble **`rules6`** (`experiments/ensembles/rules6.pth`, gitignored) mit allen Regel-Schaltern: Val 720–819 **default 98,5 %, Solution_92 72,5 %**; neue Karten 820–919 **default 99,5 %, Solution_92 69,0 %** (gegenüber Ausgangsstand 47,0 %: +22,0 pp, KI [+12,0; +31,5]). 12er-Ensemble rules6 + old3_sym3: 68 % (schwächer). Zusätzlich `keep_dead_fast` (Null-Tiles wie Solution_92 über Matchgrenzen): 74,0 % (+1,5 n. s.), 0,02 falsche Punkte-Tiles pro Match 3. Kandidat **`rules6_kdf.pth`** = rules6 mit allen Schaltern in der gespeicherten Config; im Kurs-Runner (Kopie in temporärem Ordner, 15 vs 2) 2 Spiele fehlerfrei. Match-Siege rules6 vs Solution_92 (42 Karten): 85 / 71 / 49 % – Match 3 bleibt die Schwäche.

**Andere Gegner (50 Karten, beide Seiten):** Prof-DQN 100 %, alter Abgabe-Agent `old3_sym3` nur **60 %** (große Streuung, Punktedifferenz SD 607). Für fremde Teams ist Robustheit also nicht garantiert → Training mit Gegner-Pool (`--pool`, `--pool-frac`).

**Läuft/eingeplant (19.10. abends):** 6 × `full_rules` mit 70 % Solution_92, 4000 Spiele (`*_sol70`); PPO `cnn1` bis Iteration 150 (Iteration 50: 63 %); danach automatisch 6 × `full_rules_opp` (+ `keep_dead_fast`, Reward-Strafe `w_opp_points=1` für Gegner-Punkte, Gegner 60 % Solution_92 / 20 % Pool aus old3_sym3 + rules6 / 20 % default); CNN `cnn2` = BC vom Lehrer rules6 (800 Spiele, Lehrer-WR 65 % vs Solution_92 auf Trainingskarten), größeres Netz 48 Kanäle × 4 Blöcke.

**Arbeitsweise:** Mahmoud möchte, dass gute Stände direkt auf `main` committet und gepusht werden (keine Pull Requests/Feature-Branches). Achtung: Der Projektordner wird synchronisiert; ein Branch-Wechsel erzeugte Kopien „… 2.csv“, die in `989cc3c` entfernt wurden.

**Werkzeuge:** `scripts/par_eval.py` (100 Karten × 2 Seiten × 2 Gegner in ~50 s, `--set` Schalter, PPO-Checkpoints automatisch erkannt), `analyze_losses.py --set`. Tests: 143 bestanden (neu `tests/test_rules_1910.py`).

**Seeds:** Val 500 660–500 919 verbraucht (Diagnose 660–719, Tuning 720–819, Bestätigung 820–919). Trainingsseeds PPO 100 000+. Test-Seeds 900 000+ nicht angefasst.

**Abgabe-Gewichte unverändert** (`agents/sherlock/weights/`, SHA-256 `3788fb72…d158`). Neue Abgabe erst nach ausdrücklicher Entscheidung.

## 15.10.2026 – Claude Code mit Mahmoud: Erkenntnisfolie und Reservefolie zur Belohnung

**Auftrag:** Moayeds Foliensatz prüfen und das Nötige verbessern. Ausgangspunkt `ba1578f`, Arbeitszweig `docs/presentation-erkenntnisse`.

**Änderung und Grund:** Design, Reihenfolge und alle übrigen Folien unverändert. Folie 11 zeigte nur einen negativen Befund; jetzt steht dort der belegte Fortschritt: gegen Solution_92 von 12/60 (altes Einzelnetz `full_s0`) auf 28/60 Siege (aktuelles Ensemble), gleiche 30 Testkarten auf beiden Seiten. Dazu „Mehr Training half kaum“ und Match 1 als nächster Schritt; interner Name `m1_early` nur noch in den Notizen. Folie 3 „Punkten: unsichtbare Felder besetzen“ als Brücke zum Gedächtnis, Folie 5 Belief-Zeile konkret (Punktezuwachs → Punktefelder), Folie 6 „6 Netze (3 + 3 mit Symmetrie)“ statt `full`/`full_sym`. Neue ausgeblendete Reservefolie 15 „Belohnung im Training“ mit allen Reward-Signalen und Gewichten für Rückfragen. Notizen 3/6/11/15, `slides.json`, Vortragsplan, Checkliste, Quellen, Prüfvermerk, README und CLAUDE.md abgeglichen. Folie 11 jetzt 65 statt 55 Sekunden: Plan 11:10, Moayed 5:35, Mahmoud 5:35.

**Prüfung:** Zahlen gegen `TEST_full_s0.csv` und `TEST_old3_sym3_points_v2.csv` nachgezählt (51/60 und 12/60 bzw. 60/60 und 28/60, Seeds 900000–900029). `compare_report` gepaart nach Karte: Solution_92 +26,7 pp, KI [+13,3; +41,7]; default +15,0 pp, KI [+3,3; +28,3]; ohne Korrektur für Mehrfachvergleiche/Modellauswahl, Karten mehrfach genutzt. Reward-Gewichte gegen `config.py`, `reward.py` und die Manifeste `full_s0`/`full_sym_s0`, Ensemble-Zusammensetzung gegen `ensemble_sources` im Checkpoint. Paketprüfung des PPTX-Skills bestanden. **Erstmals in nativem Microsoft PowerPoint (Mac) geöffnet** und daraus die PDF exportiert, ohne Reparaturmeldung; alle 15 Seiten gerendert und angesehen, Abstände auf Folie 11 nachgebessert. Dunkle Seiten 1/12: Hintergrund 2 pt über den Rand gemalt, alle Randpixel bei 1400 px `#102D35`. 131 Tests bestanden (vor der Folienarbeit, Code unverändert). Agent, Gewichte (SHA-256 weiterhin `3788fb72…d158`), Runner und Messdaten unverändert; keine neuen Spiele oder Training.

**Nachtrag:** Auf Mahmouds Wunsch Stichpunkte zum Ablesen für alle Folien, Reservefolien und typische Fragen, dazu eine einfache Projekterklärung und ein Wörterbuch aller Fachbegriffe von Folien und Vortrag, als `Sherlock_Stichpunkte_16-10-2026.md` im Projektordner (nicht versioniert), abgeleitet aus Notizen und Vortragsplan; Zeiten summieren sich auf 335 + 335 Sekunden.

**Offen:** Moayed über die geänderten Folien 3/5/6/11/15 informieren; gemeinsame Probe mit Uhr; Upload bis 16.10., 08:00 Uhr. Die PDF liegt zusätzlich als Arbeitskopie im Projektordner (`Sherlock_Review_16-10-2026.pdf`, nicht versioniert, identisch mit `docs/presentation/`).

## 15.10.2026 – Codex mit Moayed: Agenda als zweite Folie

**Auftrag:** Eine Agenda wie in der bereitgestellten Referenz einfügen, als Orientierung für das Publikum. Reserveinhalte und interne Hinweise nicht in der Agenda aufführen. Ausgangspunkt `b3c7e3d`, Arbeitszweig `docs/presentation-agenda`.

**Änderung:** Neue Folie 2 „Agenda“ mit sechs Themenblöcken: Spielidee/Ziel, Agent/Merkmale, Architektur/Lernverfahren, Training/Auswertung, Ergebnisse/Spielbeispiel, Erkenntnisse/Ausblick. Einfache nummerierte Liste, ursprüngliche Sherlock-Farben und Typografie. Bestehende Folien inhaltlich erhalten und ab alter Folie 2 um eins weiter nummeriert. Zwölf Vortragsfolien plus zwei ausgeblendete Reservefolien 13/14; Vortrag endet nach Folie 12. Pseudocode jetzt auf Folien 4/7, Trainingstabellen auf Folie 8, Ergebnisdiagramm auf Folie 9.

**Zeit und Übergabe:** Moayed übernimmt die Agenda mit 20 Sekunden zusätzlich. Neuer Plan 11:00 Minuten (Moayed 5:35, Mahmoud 5:25), weiterhin höchstens zwölf. Vortragsplan, Notizen/JSON, Checkliste, README, CLAUDE und Quellen auf neue Nummern abgestimmt; gemeinsame Probe steht noch aus. Die Reservefolien wurden aus der Agenda ausgelassen, nicht aus dem Anhang gelöscht. Frühere Protokolle beziehen sich auf die damalige Nummerierung.

**Prüfung:** Paket-, Layout-, Schrift-, native Tabellen-/Diagrammprüfung erfolgreich. Neue Agenda visuell geprüft. Vorhandene Folienkörper und Notizen unverändert; beim Rendervergleich nur die neuen Seitenzahlen unterschiedlich. Tabellen, Diagramm, eingebettete Datentabelle und Bilder bytegleich; dunkle PDF-Seiten 1/12 randlos. Kein Test in nativem PowerPoint. Agent, Skripte, Messdaten und Gewichte unverändert; keine neuen Spiele oder Training. Beide Gewichtshashes weiterhin `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.

## 14.10.2026 – Codex mit Moayed: Trainingspseudocode und publikumsfertige Hauptfolien

**Auftrag:** Folie 6 als Pseudocode wie Folie 3 gestalten, Tabellen auf Folie 7 nochmals auf gleiche Größe prüfen und interne Vortragsinformationen von den Hauptfolien entfernen. Ausgangspunkt `a86ef79`, Arbeitszweig `docs/training-pseudocode-cleanup`.

**Änderung:** Folie 6 mit hellem Codekasten, Courier New, eingerücktem Lernupdate und fachlichem Kommentar. Dargestellt sind Batch 256, Auswahl durch Online-Netz, Bewertung durch Target-Netz, Terminalfall, Batch-Update und Target-Kopie alle 500 Updates. Folie 7: beide Tabellen weiterhin 556 × 300 px, jetzt auch gleiche Spaltenbreiten 170/386 px; Hinweis „Weitere Einstellungen: Reservefolie 12“ entfernt. Alle elf Hauptfolien auf weitere reine Vortragsanweisungen durchgesehen; keine weiteren gefunden. Fachliche Kontextangaben wie wiederverwendeter Benchmark und vollständige Replay-Ansicht bleiben erhalten.

**Prüfung:** Pseudocode mit `agents/sherlock/main.py::_learn` abgeglichen. Paket-, Layout-, Schrift-, Tabellen-/Diagrammprüfung erfolgreich. Folien 6/7 visuell geprüft. Außenmaße im PowerPoint exakt gleich; Außenkanten der Tabellen zusätzlich im PDF gemessen, Rundungsabweichung unter 0,1 pt. Elf übrige PDF-Seiten pixelidentisch; außer Folien 6/7 alle PowerPoint-Paketbestandteile bytegleich. Sprechernotizen und Zeitbudget 10:40 unverändert. Kein Test im nativen PowerPoint.

**Übergabe:** Aktuelle PowerPoint/PDF verwenden, Vortragsplan und gemeinsame Präsentationsregel in CLAUDE.md beachten. Mahmoud behält Folie 6 mit 75 Sekunden; die Notizen passen weiter zum Lernablauf. Interne Hinweise stehen ausschließlich in Notizen/Plan bzw. im separaten Anhang, nicht im sichtbaren Hauptteil. Agent und Gewichte unverändert, keine neuen Spiele oder Training; beide Gewichtshashes `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158` bestätigt.

## 14.10.2026 – Codex mit Moayed: gleich große Tabellen auf Folie 7

**Änderung:** Beide Tabellen auf Folie 7 auf dieselbe Breite und Höhe gebracht, oben und unten bündig ausgerichtet und Kopfzeilen vereinheitlicht. Zeilenhöhen an die unterschiedliche Zeilenanzahl angepasst, Schriftgröße beider Tabellen vereinheitlicht. Hinweis auf die Reservefolie darunter neu ausgerichtet. Inhalte, Notizen, Sprecheraufteilung und geplante 10:40 Minuten unverändert. Ausgangspunkt `c5d0a30`, Arbeitszweig `docs/equal-training-tables`.

**Prüfung und Übergabe:** Paket-, Layout-, Schrift-, Tabellen-/Diagrammprüfung erfolgreich. Folie 7 nach PDF-Export visuell auf gleiche Außenmaße und lesbare Umbrüche geprüft. Zwölf andere PDF-Seiten pixelidentisch; alle PowerPoint-Paketbestandteile außer Folie 7 bytegleich. Aktuelle PowerPoint/PDF verwenden. Kein Test in nativem PowerPoint, keine neuen Spiele oder Training. Agent und Gewichte unverändert; beide Gewichtshashes weiterhin `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.

## 14.10.2026 – Codex mit Moayed: Pseudocode und Trainingsparameter ergänzt

**Auftrag:** Pseudocode auf Folie 3 anhand der bereitgestellten Designreferenz ergänzen und Trainingsparameter auf Folie 7 sichtbar machen; bestehendes Design, 10–12 Minuten und unveränderte Gewichte erhalten. Ausgangspunkt `2108ea8`, Arbeitszweig `docs/pseudocode-training-slides`.

**Änderung:** Folie 3 zeigt links „Merken / Bewerten / Handeln“ und rechts den eingerückten Spielablauf in einem hellen Codekasten mit Courier New. Gestaltung nach Folie 4 aus `team20-presentation3.pdf`, Inhalte aus Sherlock. Pseudocode ausdrücklich für die Auswertung mit festen Gewichten; Match-Reset, Sap-Zielwahl, Aktionsformat und Stapelverarbeitung sind vereinfacht. Auf Folie 7 stehen Trainingsablauf und Parametertabelle nebeneinander: Lernrate/γ, Batch/Buffer, ε-Abnahme und Target-Kopie. Eine weitere Folie war nicht nötig. Notizen zu beiden Folien, Vortragsplan, Checkliste, README und Quellen gemeinsam aktualisiert.

**Prüfung:** Spielablauf mit `act`/`_decide` und Parameter mit allen sechs abgeschlossenen Basislauf-Manifesten abgeglichen. Paket-, Geometrie-, Schrift-, native Tabellen-/Diagrammprüfung einschließlich eingebetteter Datentabelle erfolgreich. Beide geänderten PDF-Seiten einzeln angesehen, enge Umbrüche nachgebessert. Elf übrige Seiten pixelidentisch zum zuvor geprüften Export. Im PowerPoint-Paket nur Folien 3/7 und deren Sprechernotizen verändert; sonstige Bestandteile bytegleich. Dunkle Seiten 1/11 randlos; Reservefolien 12/13 ausgeblendet. Kein Test in nativem PowerPoint.

**Übergabe an Mahmoud/Claude Code:** Aktuelle PowerPoint/PDF und Vortragsplan verwenden. Weiterhin elf Vortragsfolien, Ziel 10:40, maximal zwölf Minuten. Moayed behält 5:15 Minuten und erklärt auf Folie 3 den Grundablauf, ohne jede Codezeile vorzulesen; Mahmoud behält 5:25 und erklärt die Parameter auf Folie 7. Beide Notizen sind auf diese Aufteilung abgestimmt. Gemeinsame Zeitprobe und Kontrolle auf dem Vortragsrechner stehen noch aus.

**Unverändert:** Agent, Skripte, Runner, Messdaten und Gewichte. Keine neuen Spiele oder Training. Beide Abgabe-Gewichte anhand SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158` bestätigt.

## 14.10.2026 – Codex mit Moayed: Aufzählungen mit mittigen Strichen

**Auftrag:** Auf Folie 2 die Punkte durch mittige kurze Striche ersetzen und auf Folien 8/9/11 wieder passende Aufzählungen ergänzen. Ausgangspunkt `f480083`, Arbeitszweig `docs/dash-presentation-lists`.

**Änderung:** Acht Textfelder auf Folien 2/8/9/11 verwenden native Aufzählungszeichen „–“ in derselben Schrift wie der Text (Helvetica Neue). Hängender Einzug mit Abstand zum ersten Wort; Folgezeilen am Text ausgerichtet. Auf Folie 8 nur die beiden Ergebnisangaben als Liste, die kleine Benchmark-Anmerkung bleibt ohne Strich. Das konkrete Fazit auf Folie 11 bleibt inhaltlich erhalten. Keine Änderung an Sprechernotizen, Aufteilung oder Zeitbudget.

**Prüfung:** Paket-, Geometrie-, Schrift-, Tabellen-/Diagrammprüfung mit eingebetteter Datentabelle erfolgreich. Alle vier geänderten PDF-Seiten einzeln angesehen; Abstand nach erster Sichtprüfung vergrößert. Neun übrige Seiten pixelidentisch zum zuvor geprüften Export. Im PowerPoint-Paket ausschließlich acht Textkörper geändert, alle übrigen Bestandteile bytegleich. Dunkle Folien 1/11 weiterhin ohne weißen Rand. Kein Test in nativem PowerPoint.

**Übergabe:** Aktuelle PowerPoint/PDF verwenden; Vortragsplan und Notizen weiterhin gültig. Änderungen rein gestalterisch. Agent, Gewichte, Skripte und Messdaten unverändert; keine neuen Spiele oder Training. Beide Gewichte weiterhin SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.

## 14.10.2026 – Codex mit Moayed: konkretes Fazit ohne Aufzählungspunkte

**Auftrag:** Aufzählungszeichen auf Folien 8, 9 und 11 entfernen und die zu abstrakte Abschlussfolie verständlicher machen. Ausgangspunkt `8373e1a`, Arbeitszweig `docs/clarify-presentation-conclusion`.

**Änderung:** Auf Folien 8/9 die vorhandenen Texte ohne Listenzeichen und Einzüge gesetzt; auf Folie 11 ebenfalls keine Liste mehr. Abschluss enthält jetzt „Gedächtnis + sechs Netze“, die bekannten Benchmark-Ergebnisse (60/60 gegen default, 28/60 gegen Solution_92) und den nächsten Schritt: frühe Erkundung verbessern, neue Testkarten nutzen. Keine neuen Ergebnisbehauptungen. Sprechernotiz der Abschlussfolie in PowerPoint, Vortragsplan und JSON gemeinsam angepasst. Ursprüngliches Design und kurze Überschriften erhalten; Folie 2 behält ihre Aufzählungen.

**Prüfung:** Paket-, Geometrie-, Schrift-, native Tabellen-/Diagrammprüfung einschließlich eingebetteter Datentabelle erfolgreich. Folien 8/9/11 aus dem finalen PDF gerendert und visuell geprüft; die zehn übrigen Seiten sind pixelidentisch zum zuvor geprüften Export. Nur sieben Textkörper und die Sprechernotiz 11 im PowerPoint-Paket verändert, alle übrigen Bestandteile bytegleich. Dunkle Seiten 1/11 weiterhin randlos. Reservefolien 12/13 ausgeblendet, Zeitplan weiterhin 640 Sekunden. Kein Test in nativem PowerPoint.

**Übergabe:** Mahmoud und Claude Code verwenden die aktuelle PowerPoint/PDF und den synchronisierten Vortragsplan. Moayed schließt auf Folie 11 in etwa 25 Sekunden mit Ansatz, Ergebnis und nächstem Schritt ab und eröffnet die Fragen. Gemeinsame Probe bleibt offen. Agent, Skripte, Messdaten und Gewichte unverändert; keine neuen Spiele oder Training. Beide Gewichte anhand SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158` bestätigt.

## 14.10.2026 – Codex mit Moayed: kurze Überschriften und klare Aufzählungen

**Auftrag:** Satzartige Überschriften durch kurze Themenüberschriften ersetzen und fehlende Aufzählungspunkte ergänzen, insbesondere auf Folien 8/9. Ausgangspunkt `f4d0889`, Arbeitszweig `docs/concise-slide-headings`.

**Änderung:** Zwölf Themenüberschriften gekürzt, z. B. „Spielidee und Ziel“, „Netzarchitektur und Ensemble“, „Benchmark-Ergebnisse“ und „Spielbeispiel“. Titel „Sherlock“ bleibt erhalten. Neun Textfelder auf Folien 2, 8, 9 und 11 als echte bearbeitbare Aufzählungsabsätze formatiert, insgesamt 16 Listenpunkte. Aussage auf Folie 9 zu „Stehenbleiben kann sinnvoll sein“ gekürzt. Auf Folie 11 die drei bisherigen Abschlussaspekte untereinander gesetzt und die Textbox passend erweitert. Nummerierte Abläufe, Tabellen, Diagramm und Bildbeschriftungen erhalten. PowerPoint/PDF, Titel in `source/slides.json` und Vortragsplan gemeinsam aktualisiert.

**Prüfung:** Paket-, Geometrie-, Schrift-, Tabellen- und Diagrammprüfung einschließlich eingebetteter Diagramm-Datentabelle erfolgreich. Alle 13 PDF-Seiten einzeln angesehen. Export mit ursprünglicher Helvetica Neue, Randkorrektur für dunkle Seiten 1/11 erneut angewendet und Außenpixel geprüft. Paketvergleich bestätigt: Nur 21 gezielte Textkörper und Position/Höhe einer Textbox verändert; alle übrigen Elemente, Bilder, Tabellen, Diagrammdateien, eingebettete Datentabelle und Sprechernotizen unverändert. Reservefolien 12/13 weiterhin ausgeblendet. Kein Test im nativen PowerPoint. Zeitplan weiterhin 640 Sekunden (Moayed 315, Mahmoud 325).

**Übergabe:** Aktuelle PowerPoint/PDF und Vortragsplan verwenden; beide sprechen dieselben Folien wie zuvor. Fachliche Aussagen und geprüfte Zahlen unverändert. Agent, Gewichte, Runner, Skripte und Messdaten nicht geändert; keine neuen Spieltests oder Training. Beide Abgabe-Gewichte weiterhin SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.

## 14.10.2026 – Codex mit Moayed: weiße Kante auf dunklen Folien entfernt

**Auftrag und Änderung:** Weißen Rand auf den dunklen Folien entfernen. Im PDF-Export waren Beschnitt und Hintergrundmalfläche minimal kleiner als die vollständig gerasterte Seite. Auf Seiten 1 und 11 reichen beide jetzt einen Punkt über den Seitenrand; die unveränderten Seitenboxen begrenzen die Ausgabe. Die PowerPoint besitzt bereits einen vollflächigen Folienhintergrund und bleibt unverändert.

**Prüfung:** Beide korrigierten Seiten gerendert und angesehen; sämtliche Außenpixel bei 1400 Pixel Renderbreite haben Hintergrundfarbe `#102D35`. Text und Seitenmaße auf allen 13 Seiten unverändert, Inhaltsströme der übrigen elf PDF-Seiten identisch. PowerPoint und beide Gewichte anhand der bisherigen Prüfsummen unverändert bestätigt. PDF-Prüfsumme und Exporthinweis unter `presentation/source/` aktualisiert. Keine Änderung an Inhalten, Aufteilung, Agent oder Gewichten; keine neuen Spieltests nötig.

**Übergabe:** Aktuelle PDF verwenden. Bei künftigem Neu-Export die Kanten der dunklen Seiten erneut prüfen; die Änderung betrifft den PDF-Export, nicht den Vortragsinhalt.

## 14.10.2026 – Codex mit Moayed: ursprüngliches Design wieder verbindlich

**Auftrag:** Moayed bevorzugt die ursprüngliche Gestaltung. Inhalte nochmals prüfen und das Repository auf diese Fassung zurückstellen. Ausgangspunkt `802ed46`, Arbeitszweig `docs/restore-original-presentation`.

**Ergebnis:** Ausschließlich [ursprüngliche PowerPoint mit Notizen](presentation/Sherlock_Review_16-10-2026.pptx) und [PDF](presentation/Sherlock_Review_16-10-2026.pdf) als aktueller Foliensatz. Beide Dateien sind unverändert. Gamma-PowerPoint, Gamma-PDF, Gamma-Anleitung und Gamma-Notizen-JSON aus dem aktuellen Repository entfernt. README, CLAUDE.md, Checkliste und [Vortragsplan](presentation/VORTRAGSPLAN_1610.md) wieder auf elf Vortragsfolien plus zwei Reservefolien abgestimmt. Ziel 10:40 Minuten, maximal zwölf; Moayed 5:15, Mahmoud 5:25. Abschluss wieder auf Folie 11. Der frühere Gamma-Eintrag ist als abgelöst markiert, die Git-Historie bleibt erhalten. Die externe Gamma-Präsentation wurde nicht gelöscht.

**Inhaltsprüfung:** Gesamten PDF-Text und alle Sprechernotizen gelesen. 79 Merkmale, Netzarchitektur, Q-Mittelung/Aktionsmaske und Double-DQN-Lernziel mit Agentenquellen abgeglichen. Alle sechs abgeschlossenen Basislauf-Manifeste bestätigen jeweils 3000 Spiele sowie die genannten Trainingsparameter. Benchmark-CSV erneut ausgezählt: 60/60 Siege gegen default, 28/60 gegen Solution_92, je 30 Karten auf beiden Seiten. Replay-Metadaten und Zwischenstände bei Frames 23/61/90 stimmen mit den Bildnachweisen überein. Einschränkungen zu mehrfach genutzten Testkarten, früheren ausgewählten Checkpoints und späterem Kandidaten m1_early bleiben ausdrücklich erhalten. Kein fachlicher Korrekturbedarf an den Folien festgestellt.

**Dateiprüfung:** Ursprüngliche PowerPoint/PDF stimmen bytegenau mit den in `source/PRUEFUNG.json` dokumentierten Prüfsummen überein. PowerPoint-Paketprüfung ohne Befund; 13 Sprechernotizen vorhanden, Reservefolien 12/13 ausgeblendet. Titel- und Ergebnisfolie erneut aus der PDF gerendert und angesehen; die vollständige Sichtprüfung der unveränderten 13 Seiten ist im ursprünglichen Erstellungsvermerk dokumentiert. Zeitbudget, relative Links und Diff geprüft. Keine Ausführung im nativen PowerPoint, kein Training und keine neuen Spieltests.

**Für Mahmoud:** `main` aktualisieren und den wiederhergestellten Vortragsplan lesen. In der PDF nach Seite 11 enden; Seiten 12/13 nur bei Rückfragen zeigen. Noch gemeinsam mit Uhr proben, Darstellung/Notizen auf dem Vortragsrechner prüfen, Slot bestätigen und PDF bis 16.10.2026, 08:00 Uhr auf Moodle hochladen.

**Unverändert:** Agent, Gewichte, Skripte, Tests, Kurs-Runner und Messdaten. Beide Abgabe-Gewichte weiterhin SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.

## 14.10.2026 – Codex mit Moayed: Gamma-Entwurf (historisch, abgelöst)

Ein Gamma-Entwurf mit zehn Folien wurde in Commit `802ed46` erstellt. Moayed hat anschließend ausdrücklich das ursprüngliche Design gewählt. Die Gamma-Dateien und die zugehörige Bearbeitungsanleitung sind deshalb nicht mehr Bestandteil des aktuellen Repository-Stands. Der frühere Entwurf bleibt über die Git-Historie nachvollziehbar. Maßgeblich sind ausschließlich die ursprüngliche PowerPoint/PDF und der aktuelle Vortragsplan; die damalige Zehn-Folien-Aufteilung gilt nicht mehr.

## 14.10.2026 – Codex mit Moayed: neue Präsentation und gemeinsame Vortragsplanung

**Auftrag:** Es gibt laut Moayed keine verwendbare Präsentation. Für den ersten Review neu aufbauen, etwa zehn bis höchstens zwölf Minuten; Moayed erhält den leichter zugänglichen Teil. Aufteilung und Vorbereitung für Mahmoud/Claude Code dokumentieren. Agent und Gewichte bleiben unverändert. Ausgangspunkt `12e0c4d`, Arbeitszweig `docs/review-presentation`.

**Ergebnis:** [Bearbeitbare PowerPoint](presentation/Sherlock_Review_16-10-2026.pptx), [PDF](presentation/Sherlock_Review_16-10-2026.pdf) und [Vortragsplan mit Lernhilfe](presentation/VORTRAGSPLAN_1610.md). Elf Vortragsfolien plus zwei Reservefolien. Zielzeit **10:40**, Moayed **5:15** (Aufgabe, Überblick, Ergebnisse, Spielbeispiel, Abschluss), Mahmoud **5:25** (Merkmale, Netz, Double DQN, Training, nächste Schritte). Notizen auf jeder Folie, konkrete Übergaben, Kürzung auf zehn Minuten und Antworten auf typische Rückfragen. Zeitangaben sind Planwerte; eine menschliche Probe steht noch aus.

**Inhaltliche Abgrenzung:** Aktueller Agent bleibt `old3_sym3`. Architektur und Parameter mit Code und gespeicherter Konfiguration abgeglichen. 18.000 Trainingsspiele meint die sechs Basisläufe à 3000; gewählte Checkpoints können früher liegen. Siegquoten 60/60 und 28/60 aus den neuen Benchmarkdaten. Mehrfach verwendete Testkarten als Grenze benannt. Keine alten Konfidenzintervalle oder unzuverlässigen genauen Erkundungszeitvergleiche übernommen. `m1_early` bleibt späterer Kandidat. Zwei echte Viewer-Bilder desselben Spiels (Seed 900011, Frames 23 und 90) zeigen Zwischenstände 0:0 und 374:11; vollständige Zuschaueransicht, kein Agentenwissen. Eine Live-Demo ist nicht nötig.

**Tatsächliche Prüfung:**

- Alle 13 Folien erstellt und gerendert; sämtliche finalen PDF-Seiten einzeln auf Lesbarkeit, Umbrüche und Überlappungen angesehen. PowerPoint-Paket, Geometrie, Schriftzuweisung und Wiederimport geprüft; keine gemeldeten Befunde. Ergebnisdiagramm nativ mit eingebetteter Datentabelle, Tabellen und Texte bearbeitbar.
- PDF aus der finalisierten PowerPoint mit eingebetteter Helvetica Neue erzeugt; 13 Seiten. Reservefolien 12/13 in PowerPoint ausgeblendet; in der PDF nach Seite 11 enden. Notizen auf allen 13 Folien vorhanden. Kein Test im nativen Microsoft PowerPoint durchgeführt; vor Ort Darstellung und Notizenansicht prüfen.
- Zeitbudget rechnerisch geprüft: 315 + 325 = 640 Sekunden. Ergebnisse gegen CSV, Bildzwischenstände gegen Replay-Datei und Viewer, relative Dokumentlinks und Git-Diff geprüft. [Prüfvermerk mit Dateihashes](presentation/source/PRUEFUNG.json), [Quellen/Bildnachweise](presentation/source/QUELLEN.md) und [Notizen als JSON](presentation/source/slides.json) liegen bei.
- Keine neuen Spieltests und kein Training für diese reine Präsentationsarbeit. Agentenmodule, Skripte, Tests, Kurs-Runner und Experimentdaten unverändert. Beide Abgabe-Dateien behalten SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.

**Übergabe an Mahmoud:** Nach Veröffentlichung `main` aktualisieren. Mit Claude Code zuerst den Vortragsplan und diese Notiz lesen. PowerPoint ist die bearbeitbare Folienquelle; bei Änderungen PDF, Notizen/JSON und Plan gemeinsam abgleichen. README, CLAUDE.md und Review-Checkliste verweisen auf den neuen Foliensatz; frühere Hinweise auf einen externen 19-Folien-Entwurf sind historisch.

**Noch durch das Team zu erledigen:** Inhalt und Aufteilung gemeinsam bestätigen, zwei Proben mit Uhr, Slot/Buchung bestätigen, Dateien auf dem Vortragsrechner öffnen und PDF bis **16.10.2026, 08:00 Uhr** auf Moodle hochladen. Codex hat keinen Moodle-Upload vorgenommen. Die bestehenden offenen Mess-/Trainingsfragen bleiben Aufgaben für nach dem Review.

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
