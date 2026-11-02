# Bedingter Anpassungspilot: P und PT

02.11.2026 · **Route nach vollständiger Gaußdatenabnahme von Root gewählt; Umsetzung/Prüfung des Wrappers vor Lauf.** Grundlage: Performance-Code `3152fed`, neue Prototyp-Spec/-Plan vom 02.11. sowie bestehende Trainingspfade. Keine Modelle, Spiele, Extraktion oder Implementierung für diesen Entwurf ausgeführt.

## Eintritt und feste Fragestellung

Nur starten, wenn Root die **vollständige** Gauß-Admission abgenommen und die praktische Route verworfen hat: mindestens 20 strikte neue positive Fakten gegenüber V∪A, mindestens 5 Spiele/3 Karten und mindestens 100 zusätzliche positive Fakt-Schritte sind gemeinsam nötig. Ein günstiger Zwischenstand oder bloß technisch erfolgreicher Solver reicht nicht. Keine Mischung von Gauß und diesem Pilot.

Außerdem müssen die ausstehenden Vollsuite-/bekannten Default-off-/aktivierten Mechanismusprüfungen des Planungsprototyps bestanden und dessen tatsächlicher Runtime-Stand eingefroren sein. Unabhängiges Code-Review liegt vor; es ersetzt diese offenen Prüfungen nicht.

**P = V14 + point_pair_swap + art_move_guard**, ansonsten unveränderte V14-Inferenz. **PT = P mit genau zwei ersetzten Komponenten 18/19**. Forschungsfrage: Hilft Anpassung an die neue Planungs-/Aktionsverteilung gegenüber identischem Nachtraining unter alter Planung? Kein neuer Reward, keine Architektur-, Gegner-, Ensemblegrößen- oder Hyperparametersuche.

## Vier Arme und Kartenherkunft

Indexierung ausdrücklich `[q, *ensemble]`, also q=0; 18/19 werden vor Ergebnissen fest gewählt.

| Komponente / Runseed | Kontrolle: Rollout/Prefill | Anpassung: Rollout/Prefill | Trainingskarten inkl. | Prefillkarten inkl. |
|---|---|---|---|---|
| 18 / 28 | beide P-Flags false | beide P-Flags true | 484200–484499 | 485000–485059 |
| 19 / 29 | beide P-Flags false | beide P-Flags true | 494200–494499 | 495000–495059 |

Formel aus `finetune.py:51,206–223`: Training 200000 + 10000×Runseed + 4200 + g//2, Prefill 200000 + 10000×Runseed + 5000 + g//2; Seiten P0/P1 abwechselnd. Je Paar identische Karten, Seiten und vorab festgelegte Gegnerfolge. Feste Mix-Gewichte: Solution92 .6, Quadrat .2, default .1, rush .1; kein Pool/Snapshot. Die gezogene Folge mit RNG-Seed Runseed+4200 (4228/4229) einschließlich Prefill protokollieren und armweise vergleichen; Gewichte bedeuten keine exakt erzwungenen Anteilszahlen.

**Herkunftsgrenze:** Der zentrale `seed_audit.json` belegt 840000–844999, nicht diese Lernblöcke. Der ältere `training_design.md` fand in vorhandenen CSV/Manifesten keinen Treffer, zertifiziert aber keine universelle Frische. `ARBEITSSTAND.md:870` nennt ausdrücklich frühere Scratchpad-Spiele auf **495000–495003**; diese Prefillkarten sind bereits bekannt. Seeds 28/29 wurden früher mit anderem Offset trainiert (`:709`). Lern-/Prefillkarten dürfen bekannt sein und werden nicht als heutiger unabhängiger Test ausgegeben. Keine eigenständige Offsetänderung. 841000–841099, 842000–842299 und 843000–843299 bleiben unangetastete Auswahl-/Bestätigungs-/Direktblöcke; unmittelbar vor Leistung weiterhin zentraler Herkunfts-/Remoteabgleich, keine unsichtbaren Fremdläufe unterstellen.

## Identischer echter Anfang, frischer Lernzustand

Vor Jobs einen kleinen geprüften Wrapper festlegen; **`night_train_pilot.run_arm` unverändert ist ungeeignet** (Seed 9, alte Rewardarme). Vorhandene Extraktions-/Hashlogik darf wiederverwendet werden, keine stillen V12-Configüberschreibungen.

- V14-Quelldatei SHA `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`, 36 Netze, 79 Merkmale/6 Aktionen. Alle 36 geordneten Tensorhashes vorab binden; nur Komponenten 18/19 entnehmen. Je Komponente beide Arme tensoridentisch initialisieren, einschließlich `target_q=q`; kein zufälliges Ersatznetz tolerieren.
- Neue einmalige Init-/Runverzeichnisse. Init enthält nur ein q/target, leeres ensemble, keinen `opt` und keine Replaydatei. Am **wirklich geladenen** Lerner beweisen: genau ein Netz, exakte q/target-Hashgleichheit zur gewählten Quelle, frischer Adam ohne Momentzustände/Steps, Replay size=pos=0, learn_steps=0, keine alte Verlusthistorie. Beide Seiten teilen dasselbe kanonische Lernerobjekt.
- Effektive komplette Config vorab speichern und nach Konstruktion vergleichen: Quelle plus frozen=false, lr=1e-4, w_discovery=.5, w_explore=.3, beide bisherigen Trainings-Regelgates true; einzige Behandlung sind die zwei P-Flags. Epsilon-Endwert .05, env_steps genau 60000 bei eps_decay_steps=60000, learn_enabled=true, Autosave aus. Keine Reward-Differenz zwischen Armen.

## Ablauf, tatsächliche Regeln und Zählung

Je Arm **120 Prefillspiele ohne Updates**, danach **600 Lernspiele**, nur Endcheckpoint. Prefill ist **lernlos mit epsilon .05**, keine deterministische eingefrorene Aktionspolicy. Nach Prefill q/target und Adam unverändert, learn_steps=0, Replay über learn_start=5000; unterschiedliche Trajektorien/Replayinhalte sind die beabsichtigte Behandlung. Vor Spiel 1/300/600 Lerncounter und Tensorhashes sichern.

Je Arm 3 bekannte Validierungen nach 0/300/600: 8 Karten 500000–500007 × 2 Seiten × default/Solution = 32 Spiele je Zeitpunkt, **96 insgesamt**. Für beide Arme gemeinsame finale **P-Inferenzconfig**, epsilon=0, Lernen aus; danach die jeweilige Rolloutconfig wiederherstellen. Diese Kurven sind Forschungsdiagnose, wählen weder Checkpoint, Komponente, Seed noch Kandidat.

Validation muss getrennten festen Eval-RNG verwenden und Lernzustand, Optimizer/Replay, Config, Rollout-RNG, Zähler und Episodezustand unverändert wiederherstellen. `finetune.py:177–197` verwendet bisher direkt `play_set`; der künftige schmale Wrapper braucht geprüfte Isolation (vorhandenes `experiment.run_validation(..., isolate=True)` als Grundlage), kein ungeprüfter unveränderter CLI-Start. Kein Einblick in Test-Seeds; `--keep-final --no-test`, n_val=8, val_every=300, ohne nachträgliche Wahl aus `weights_best`.

| Regelpfad | Training/Prefill | Gemeinsame P-Validierung / spätere Inferenz |
|---|---|---|
| point_pair_swap, art_move_guard | bei Anpassung aktiv durch rules_in_training; Kontrolle aus | beide aktiv |
| reach/path_fix/Overkill/Kollision | bestehendes rules_in_training gilt | bestehende Regeln aktiv |
| Parameterschätzung/Nebel und sap_still | bestehendes rules_in_training_all gilt | aktiv |
| art_splash-Absenkung | **trotz Flag eval-only**, `_artillery_ok` prüft explizit `not self.training` | abhängig von vorhandener Schätzung aktiv |
| sap_still_splash | kann auch im Training mit vorhandener Schätzung wirken | entsprechend Schätzung aktiv |
| cand_rescue | **eval-only aus**; nicht heimlich angleichen | bestehende Rescue-Bedingung aktiv |

Quellen: `main.py:255–269,301–306,386–393,451–465,708–725,1135–1147`. Folglich keine Behauptung vollständiger Gleichheit aller Trainings-/Inferenzregeln. P-Zähler im tatsächlichen Rollout speichern; eine korrekte Flagconfig garantiert nicht, dass ein seltenes Ereignis in jedem Arm vorkommt.

**Geplante Simulationen:** je Arm 120+600+96 = **816**, vier Arme **3264 = 480 Prefill + 2400 Training + 384 bekannte Val**. Technische Spiele und spätere Leistungsstudie separat zählen. Erwartung bei vollem Replay: 90000 Adamupdates je Arm und env_steps=278160 nach 720×303 Updates ab 60000; tatsächliche Werte/Resetkonvention gegen Logs prüfen, nicht aus Spieldateinamen ableiten.

## Endstand und Forschungsvergleich

Alle vier Arme müssen vollständig, endlich und mit tatsächlichen Updates abschließen: 600 eindeutige Lernzeilen, 120 Prefillbelege, 96 Valzeilen, korrekte Quellen/Keys/Config/Steps, keine NaNs/Fehler. Final-q muss vom Init abweichen; Zielnetz, Adam-Momente/-Steps und Lerncounter plausibel und endlich; nach Laden wieder tensor-/configgleich zum gespeicherten Endstand. Vorzeitiger/fehlender Arm liefert kein PT. Kein Nachladen des besten Valzustands.

P hält alle ursprünglichen 36 Tensoren. PT ersetzt **verbindlich beide** Positionen 18 und19 durch die adaptierten End-q; alle anderen 34 exakt gleich, Reihenfolge und 1/36-Gewichte unverändert, keine 37. Komponente. Die zwei Kontroll-Endnetze werden unter derselben P-Inferenz in den vorhandenen bekannten Validierungen gegen Anpassung verglichen; sie sind **kein weiterer Nominee**. Kein Entfernen eines schlechteren Starts, kein Seed-/Mischungsnachrücken. Zwei Starts sind keine allgemeine statistische Methodenbestätigung.

## Zulassung nach Zeit und Ressourcen

Zwei Wellen: zuerst Kontrolle/Anpassung Index18 parallel, dann Index19; maximal zwei Worker, keine parallele Vollsuite. Frühere zwei 816er-Arme benötigten 40:42 min; vier Arme daher etwa 82 min, mit 20 % Reserve etwa **98 min**, harte Pilotgrenze **2 h**. P kann langsamer sein: vor jeder Welle mit bisheriger kompletter Laufzeit neu zulassen, kein Siegquoten-Abbruch. Dateibruch/NaN/fehlende Updates/Deadline stoppt das aktive Paar kontrolliert; Zwischenstände nur als unvollständig archivieren.

Auf Akku unter 35 % keine lange Phase beginnen, bei 25 % eigene schwere Jobs kontrolliert beenden; AC hebt diese Akkuschwellen auf. Vor Pilot müssen auch technische Nachweise, Auswahl, einzige Bestätigung und mindestens 60 min Schlussreserve bis 05:30 Berlin passen; Nutzerende 03.11.06:00. Frühere konservative Gesamtprojektion einschließlich 100-Karten-Auswahl/300-Karten-Bestätigung: Training etwa 98 min, Auswahl 204 min, Bestätigung 400 min plus Schlussreserve. Aktuellen langsameren Durchsatz verwenden, keine automatische Zusage aus alten Zeiten. Vor 05:00 keine Phase beginnen, die nicht rechtzeitig vollständig endet.

Erst nach separatem veröffentlichtem Leistungsnachtrag maximal **P und PT** nominierbar; feste 841/842/843-Blöcke und unveränderte Übernahmegates, genau ein Nominee, keine Erweiterung nach Outcomes und kein Nachrücken nach fehlgeschlagener Bestätigung. Falls die vollständige Folge nicht mehr passt, vor frischen Leistungsdaten PT ganz auslassen oder den Pilot ausdrücklich nur als Forschung abschließen. **Root entscheidet erst nach Gaußdaten; dieser Entwurf startet nichts.**


## Root-Entscheidung nach abgeschlossenen technischen Daten

Gauß praktisch verworfen (2 Weltfelder/1 Spiel/1 Karte/2 positive Feld-Schritte),
bevor irgendeine neue841er-Leistungszahl gelesen wurde. P technisch abgenommen:
792Tests+14Untertests, unabhängig geprüfte24Spiele,12Default-off-Streams exakt.
Damit wird diese vorab bedingte Route P/PT gewählt. Gewichte bisher unverändert;
noch kein Trainingsspiel dieses Piloten gestartet.

Umsetzung nur in `scripts/targeting_adapt.py` und `tests/test_targeting_adapt.py`.
Vorhandene `finetune`-Schleife, Komponenten-/Tensorhashlogik und
`experiment.run_validation(...,isolate=True)` wiederverwenden. Keine Änderung
an Reward, Runner, Gegnern oder globaler Variantenregistrierung auf Festplatte.
Validierung: eigene/ globale RNG-Zustände und Rolloutflags sichern; fester
Eval-RNG-Seed20261102; beide P-Flags während der bekannten Val aktiv; vorhandene
Isolationsroutine bewahrt Lernen/Optimizer/Replay. Danach Rollenflags/RNG exakt
zurück, Episodenkontext frisch für die nächste Trainings-Env-Initialisierung.
Keinen vollständigen alten beendeten Belief-/Episodenkontext zu rekonstruieren
behaupten: die vorhandene Isolationsroutine setzt ihn bewusst neu zurück.
Rote Tests müssen insbesondere Rolle/Konfig-/RNG-Rückgabe auch bei Fehler prüfen.

Initiale und finale tatsächliche Lernerzustände,720Rolloutzeilen je Arm
(120Prefill/600Training) sowie96rohe Val-Spielzeilen und P-Zähler protokollieren.
Nur Endstand; interne weights_best-Verzeichnisse nie als Auswahlquelle verwenden.
Unerwartete Config-/Tensorabweichung, geladener Replay/Optimizer oder bestehende
Ausgabe vor dem ersten Spiel hart ablehnen. Alle vier Arme vollständig oder keinPT.

Vor Erststart Source/HEAD/Interpreter, Quell-/Initgewichte, Protokoll/Wrapper und
alle erwarteten Karten/Seiten/Gegnerpläne pinnen. Maximal zwei Worker, zwei Wellen,
120min Gesamtfrist ab erstem Arm. Remoteabruf weiter möglich, Integration erst
nach Ende des Freeze. Quelle darf nach Vormessung einer ganzen Welle nicht
geändert werden. Keine Laufentscheidung anhand Val-/Gewinnzwischenständen.
