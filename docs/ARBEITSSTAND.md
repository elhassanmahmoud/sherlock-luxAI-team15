# Gemeinsamer Arbeitsstand

Dieses Protokoll dient der Übergabe zwischen Mahmoud, Moayed, Claude Code und Codex. Neueste Einträge stehen oben. Gemeinsame Regeln und fachlicher Überblick: [CLAUDE.md](../CLAUDE.md). Messreihen und Entscheidungen über Agentenvarianten: [EXPERIMENT_PROTOKOLL.md](EXPERIMENT_PROTOKOLL.md).

Pro abgeschlossener Arbeit knapp festhalten: Datum und Bearbeiter, Änderung und Grund, tatsächlich ausgeführte Prüfungen, offene Punkte. Frühere Messergebnisse als solche kennzeichnen. Ein geplanter Schritt ist noch kein Auftrag zur Umsetzung. Änderungen werden für das andere Teammitglied erst nach Übertragung über Git und Aktualisierung seiner Arbeitskopie sichtbar; Chatverläufe gehören nicht automatisch dazu.

## 08.11.2026 – Fog-Vergleich abgeschlossen: positives Kontrollsignal, keine Freigabe

- Alle440 festen Partien / elf Jobs unabhängig vollständig bestätigt,280 Statistik-/Strukturgegenprüfungen PASS. CONTROL38: Solution38/40 stattV1437/40, Panel75/80 statt74, direkt28/40[50%;90%]. NEUTRAL38: Solution37/40, Panel73/80, direkt26/40[45%;85%]. Defaultalle40/40. KeineRemis.
- PaneldifferenzKontrolle+1,25pp[0;3,75], Neutral−1,25pp[−3,75;0]; N−C−2,5pp[−6,25;0]. Beide verfehlen vorab mindestens+2,5ppPanelgewinn. `nominee:null`, keineBestätigung/Erweiterung; V14/ZIP bleiben bytegleich. [Ergebnis mit Grenzen](../experiments/analysis/fog_comparison_20261108/ERGEBNIS.md).
- HistorischeAbnahmeunterc096e4fgesichert, eigeneProzesse/Wachhaltenbeendet, danach sichereIntegrationeigenerDokumentation. NächsterkleinerSchritt: vorhandeneReplaydaten offline auf tatsächlichenEinflussderNetze prüfen, höchstens10000Zeilen, keineweiterenSpiele/Trainingsupdates. NochkeinErgebnisdieserDiagnose.

## 08.11.2026 – Pfadfehler der Auswertungs-CLI behoben

- Nach vollständig beendeter Auswahl erkannte die Auswertung bei relativen Ergebnisordnern einen fehlenden Herkunftsbeleg: der Dateiinhalt stimmte, aber ein relativer Pfad wurde mit absoluten Schlüsseln verglichen. Derselbe unveränderte Auswertungscode erzeugte mit absoluten Argumenten das vollständige, unabhängig bestätigte Ergebnis noch unter dem ursprünglichen Freeze.
- Erst danach eng korrigiert: Herkunftspfad einmal kanonisch auflösen und überall gleich verwenden. Root: beide neuen CLI/API-Regressionen bestanden (3,69s). Keine Spielwiederholung, Modell-/Daten-/Gateänderung. Historische Resultate/Quellstand unverändert erhalten.

## 08.11.2026 – Fog-Auswahl tatsächlich gestartet

- Elf feste Jobs / 440 Spiele laufen, maximal zwei Worker. Supervisor79399, eigenes Wachhalten79418, erste V14-Referenzworker79431/79440. Netzstrom100%, echte erlaubte Kontingentnutzung93% beim Start. Keine fertigen Leistungsresultate behauptet.
- Studienworktree weiterhin `sherlock-student-20261104/sherlock-luxAI-team15`, Livezustand `experiments/analysis/fog_comparison_20261108/selection/state.json`. Quellen/HEAD `c096e4f0d1720900ee04d5acaa7faaef465fcded` bis Ende von Auswahl und eventueller Bestätigung unverändert. Keine parallelen Tests; keine zweite Instanz.
- Werkzeugreview PASS, Root45Tests PASS, tatsächliche Kandidatenmontage/Ladung/Zulassung sowie portable Gegenprüfung im primären Checkout PASS. Dieser Startvermerk verändert ausschließlich den primären Checkout. V14 und ZIP unverändert; Überwachung prüft GitHub, Ressourcen und die tatsächlichen Ergebnisse.

## 08.11.2026 – Zwei feste Fog-Ensembles gebaut, Vergleichswerkzeug geprüft

- CONTROL38 und NEUTRAL38 tatsächlich aus den 36 unveränderten V14-Netzen plus jeweils zwei festgelegten finalen Nachtrainingsnetzen gebaut. Gleiches Gewicht je Netz, ursprüngliche Inferenzkonfiguration; tatsächliches Laden und Tensorreihenfolge geprüft. Historische Trainingsabnahme und 55 benötigte Dateien gebunden.
- Root: 45 gezielte synthetische Tests bestanden (10,99s), reale reine Artefaktmontage und erneute Zulassungsprüfung bestanden. Vier feste Kartenlisten und elf Auswahljobs / 440 Spiele vorbereitet. Noch keine Leistungsspiele und kein belegter stärkerer Agent; V14 und ZIP unverändert.
- [Werkzeug-/Prüfbelege](../experiments/analysis/fog_comparison_20261108/operations/), [feste Regeln](superpowers/specs/2026-11-08-fog-comparison.md). Unabhängiger Schlussreview von Spezifikation, Code/Integration und Methode PASS; keine offenen Blocker. Der kommende Vergleich hält Quellen und HEAD über Auswahl **und gegebenenfalls Bestätigung** gleich; maximal zwei Worker, keine parallelen Tests. Keine zusätzlichen Karten oder nachrückenden Kandidaten bei negativem Ausgang.

## 08.11.2026 – Fog-Nachtraining vollständig geprüft; kleiner Ensemblevergleich folgt

- Vier feste Arme ab V14-Komponente 18: je 40 Vorlauf-, 400 Lern- und 32 Diagnosepartien. Tatsächlich 1.888 Spielausführungen und 240.000 neue Lernupdates. Beide Kontroll-/Neutral-Paare vor Gradienten identisch bis auf das geplante Reward-Signal.
- Unabhängiger finaler Tensor-/Daten-/Quellenaudit PASS; Root hat zusätzlich alle vier ursprünglichen Abschlussvalidatoren vor Aufhebung des Quellenstands `a3111c3` ausgeführt. Q/Target/Adam endlich und verändert, je 60.000 Updates, vollständige Rohdaten und Prüfsummen. Historische Abnahme gesichert; eigene Modell-/Wachhalteprozesse beendet.
- [Trainingsbericht](../experiments/analysis/fog_reward_20261108/TRAININGSERGEBNIS.md). V14 und ZIP unverändert; noch kein nachgewiesener Stärkegewinn. Replay-Puffer lokal, Modelle und nachvollziehbare Rohdaten versioniert.
- Nächster bereits vor Ergebnissen fixierter Vergleich: CONTROL38 und NEUTRAL38 mit exakt 36 ursprünglichen + zwei neuen Netzen. 440 Auswahlspiele; nur bei Qualifikation einmalig 1200 frische Bestätigungsspiele. Adapter in Umsetzung, noch keine Kandidaten/Leistungsspiele. Zwischenzeitliche eigene Dokumentation bis `8094c38` nach Ende des Freeze übernommen, keine neuen Mahmoud-Commits beobachtet.

## 08.11.2026, 13:07 Berlin – Fog-Nachtraining tatsächlich aktiv

- Studienkopie sherlock-student-20261104 auf eingefrorenem a3111c3. Supervisor50389, erstes Paar control41/neutral41 mit Kindern50415/50416; Paare42 folgen automatisch erst nach vollständiger technischer Abnahme von41. Maßgeblich experiments/analysis/fog_reward_20261108/training_v1/state.json. Keine zweite Instanz, keine Tests/Quellen-/HEAD-/Gewichtsänderungen in der aktiven Studienkopie.
- Vorlauf41 unabhängig bestanden: je40 vollständige Spiele/144264 Replay-Übergänge;615 explizite finale unbekannte Nebelschüsse, Rewardmasse184,5. Beide Trajektorien und Replay ohneReward gleich, Q/Target/Adam unverändert, null Vorlaufgradienten. Danach tatsächlich je14 Lernspiele/2100 Updates beobachtet. Keine bereits vollendeten400 Spiele oder höhere Siegquote behauptet.
- Maximal zwei Modellworker, AC100%, aktuelleKontingentprüfung freigegeben; Watcher überwacht GitHub/Quota. Dieser Startbericht verändert ausschließlich den primären Checkout, während der aktive Quellenstand eingefroren bleibt. V14/ZIP unverändert; Lauf-/Datenaudit und tatsächlicher Stärkevergleich bleiben offen.

## 08.11.2026 – Fog-Reward-Mechanik geprüft, Lernläufe folgen

- Explizite Herkunft finaler Fog-SAPs und optional neutrales Hit-Shaping umgesetzt; Schalter standardmäßig False. Numerische Trefferschätzung, Aktionen/Maske/Regeln und alte Fünf-Argument-Rewards erhalten. Trainingswerkzeug mit vier festen Armen, Herkunfts-/Replay-Audit und gemeinsamer Vorlaufprüfung vor Gradienten.
- Root:145 gezielte Tests bestanden (22,41s), ein echter Spieltest dort bewusst ausgeschlossen. Danach vier vollständige bekannte V14-Ausführungen (beide Seiten ×FlagFalse/True): alle1212 Schritte einschließlich beider Aktionen, Engine-/Beobachtungszustände und Punkte exakt mit alten Referenzen identisch. JeSeite69/91 finale unbekannte Schüsse explizit erkannt. Kein Lernen oder Leistungsvergleich in diesen vier Technikspielen.
- Unabhängiger Core-Review sowie integrierter Trainings-/Gesamtreview PASS, keine Blocker. Neue reale Reward-/Replay-/Lernzähler werden erst in den jetzt anstehenden Vorläufen und Trainings geprüft. Noch keine neue Spielstärke behauptet. Abgabe-Gewichte und ZIP bytegleich.

## 08.11.2026 – gezieltes Fog-Reward-Nachtraining vorbereitet

- Nächste getrennte Hypothese: finale Nebelschüsse mit unbekanntem Treffer werden bislang im Hit-Shaping wie eine Nulltrefferschätzung abgezogen. Optionaler Neutral-Term nur für explizit nachgewiesene finale Fog-Herkunft; bekannte Treffer/Miss-Schätzungen, Aktionen und Regeln bleiben gleich. Default False, noch in Implementierung.
- Fest vorab: V14-Komponente18, zwei Starts41/42, je Kontrolle/Neutral, vier Arme mit40 Vorlauf+400 Lernspielen und32 diagnostischen Validierungsausführungen. Insgesamt1888 geplante Ausführungen,240000 erwartete neue Lernupdates. Kein bereits gestarteter/bestandener Versuch. [Spec](superpowers/specs/2026-11-08-fog-reward.md), [Plan](superpowers/plans/2026-11-08-fog-reward.md), [Übergabe](../experiments/analysis/fog_reward_20261108/HANDOFF.md).
- Unabhängiger Kartencheck über acht Worktrees: keine beobachtete Verwendung/Reservierungsüberschneidung und keine Lesefehler. Grenzen:282 seedlose CSV,215 JSONL ohne numerischen Seed,778 uneindeutige Seed-Felder; externe/unprotokollierte Läufe unbekannt. [Vollständiger Audit](../experiments/analysis/fog_reward_20261108/operations/seed-audit.md).
- Getrennte Implementer für Agentenmechanik und Trainingswerkzeuge; unabhängiger Kartencheck und spätere Code-/Datenreviews. Maximal zwei Modellprozesse, keine parallelen Tests, Source-Freeze erst nach Werkzeugprüfung. V14/ZIP unverändert; vorherige HOLD-/Ensemblestudien geschlossen. Kein allgemeines SAP0 und kein erneuter Großvergleich.

## 08.11.2026 – HOLD-Kopf gelernt und getrennt geprüft: keine Freigabe

- Tatsächlich ein kleiner Kopf mit16 öffentlichen Merkmalen gelernt:162 vollständige Trainingspaare auf20 von24 festgelegten Karten. Beide Seiten,96 Referenz-/Sammelausführungen. Alle positiven/negativen/Null-Labels genutzt; Normierung nurTraining, einmaliger Ridge-Fit. V14-Netze unverändert.
- Getrennte Validierung auf acht Karten/32 Ausführungen:28 Paare,14 gewählte Eingriffe,10 positive und4 negative. Mittlerer Kartenwert+1,125, untere Bootstrap-Grenze−0,8765625. Zwei von sechs festen Bedingungen verfehlt (Menge und Unsicherheit). Keine Zusatzkarten, kein Refit, kein vollständiger Stärkevergleich oder Abgabeaustausch dieses Kopfes.
- Insgesamt132 vollständige Ausführungen einschließlich neutraler Technik,190 Paare und5736 zusätzliche Simulationsschritte; keine neuen DQN-/RL-Updates. Root102 Werkzeugtests vorher bestanden. Unabhängige Code-, Rohdaten-, Koeffizienten- und Validierungsaudits PASS; deren Leistungsentscheidung lautet FAIL. Quelle759c8fa bis zum Ende unverändert, eigene Prozesse beendet, Gewichte/ZIP bytegleich.
- [Vollständiger Bericht](../experiments/analysis/holder_learning_20261108/ERGEBNIS.md). Der Nutzer will autonome Weiterarbeit: nächster separater Ansatz ist die Herkunft/Behandlung unbekannter Fog-SAP-Treffer im Training. Noch kein neuer Trainingslauf dazu und keine Änderung am Produktionsagenten.

## 08.11.2026 – HOLD-Lernwerkzeuge geprüft

- Die 16 öffentlichen Merkmale, einmalige gewichtete Ridge-Anpassung und festen Validierungsregeln sind umgesetzt. Der optionale experimentelle Kopf darf höchstens acht Gelegenheiten pro Spiel bewerten; abgelehnte Eingriffe starten ebenfalls die zwölf Schritte Wartezeit. Der Produktionsagent und V14 bleiben unverändert.
- Root hat alle 102 gezielten Tests bestanden (2,88 Sekunden). Unabhängiger Integrationsreview PASS, keine Blocker. Alte Probeprüfungen bleiben erhalten. Reale neutrale Spielprüfung und Datensammlung stehen noch aus; kein bereits trainierter Kopf behauptet.
- Nächste Reihenfolge: vier bekannte technische Spiele mit tatsächlich aufgerufenem neutralem Kopf; dann feste Trainingsdaten, genau ein Fit, Kopf einfrieren, erst danach getrennte Validierungsdaten. Quellen während der Läufe unverändert; keine parallelen Tests. [Werkzeugbelege](../experiments/analysis/holder_learning_20261108/operations/).

## 08.11.2026 – kleiner HOLD-Lernversuch vor neuen Daten festgelegt

- Nach bestandener Einflussprobe eigener [Lernplan](superpowers/plans/2026-11-08-holder-learning.md):24Trainingskarten6500000–6500023 und8Validierungskarten6501000–6501007, beideSeiten, höchstens512Paare. Je Referenz+Sammler zusammen128volleAusführungen; keine frischen Leistungsspiele. Noch nicht gestartet.
- 16öffentliche Merkmale, genau eine gewichtete Ridge-Regression mit festem Faktor0,1, Vorhersageschwelle strikt>1Punkt. Normierung nurTraining; Kopf vor ersterValidierung einfrieren. Höchstens8bewertete Gelegenheiten proSpiel,12Schritte Abstand auch nachAblehnung. Validierung prüft Nutzen aufgetrenntenKarten, anschließend nur beiPASS ein eigener vollständigerSpielvergleich. KeineNachoptimierung aufValidation.
- Seed-Audit über8Worktrees: keine beobachtete Verbrauchs-/Metadatenüberschneidung, keineLesefehler. Lücken transparent:282seedloseCSV,83seedloseJSONL und598nichtnumerische/uneindeutigeSeed-Feldwerte. KeineGarantie überunprotokollierte/externeRuns. [Belege](../experiments/analysis/holder_learning_20261108/operations/seed-audit.md).
- ZweiSubagents implementieren getrennt Lernarithmetik und experimentellePolicy/Datenerfassung. Noch kein neuerKopf/Trainingslabel. V14/ZIP unverändert; main/primärerCheckout zuletzt8e462f6, keine neuen Mahmoud-Commits.

## 08.11.2026 – HOLD-Einflussprobe vollständig: 28 hilfreiche und21 schädliche Eingriffe

- Fester Block vollständig:24Spielausführungen auf zwölf bekannten Schlüsseln,55Paare über je zwölf Schritte. Positive Labels28 in10Spielen, negative21, null6; Mittel+0,418Team-Punkte, Spannweite−27 bis+42. Vorab-Machbarkeit bestanden, keine nachgewiesene stärkere Policy. Bekannte ausgewählte Spiele, keine neue Leistungsvalidierung.
- Technischer Smoke separat4Ausführungen/2Paare. Insgesamt28 vollständige Ausführungen und1680 zusätzliche Simulationsschritte, null Lernupdates. Referenz/Sammler, Baselinezweig/Livezukunft und Wiederholungen exakt; unabhängiger Audit70990 Datenprüfungen PASS. Quellen/HEAD01d4279 während Läufen eingefroren, eigene Modell-/Wachhalteprozesse beendet.
- V14 und ZIP unverändert. [Ergebnis mit Grenzen](../experiments/analysis/decision_learning_20261108/HOLD_DIAGNOSE.md). Nun separater kleiner Lernversuch auf24Trainings-/8Validierungskarten; Merkmale, Eingriffshäufigkeit und Freigaberegeln vor neuen Labels fixieren. Keine Probeverlängerung oder Übernahme aus den bekannten Fällen.

## 08.11.2026 – HOLD-Diagnosewerkzeug geprüft, echte Probe folgt

- Isolierte Diagnosewerkzeuge umgesetzt; Produktionsagent, Gewichte und ZIP unverändert. Zustandskopien erhalten Solution-Global/Node-Aliase und restaurieren globale Zufallszustände. Einmaliger STAY-Vorschlag durchläuft normale Regeln; ganze Teamfolgen über zwölf Schritte werden gemessen.
- Root:26 gezielte synthetische Tests bestanden (2,08s). Unabhängiger Code-/Methodenreview PASS, keine Blocker. Das ist noch kein Laufzeit-/Stärkenachweis; erst vier technische Spielausführungen (zwei bekannte Karten/Seiten jeweils Referenz+Sammler), dann bei Passivität die feste24-Ausführungen-Diagnose. Maximal96 Paare plus separat gezählte Wiederholungsprüfung. Keine parallelen Tests nach Start.
- Zusätzliche unabhängige historische Analyse: Niedrige Halterenergie nach SAP ist nicht allein durch eigene Schusskosten erklärt; unbekannte Nebeltreffer werden im Reward als Miss behandelt. Beides getrennte Forschungshinweise, keine bereits bewiesenen Verbesserungen. [Belege](../experiments/analysis/decision_learning_20261108/).

## 08.11.2026 – neuer Auftrag: gezieltes Entscheidungslernen vorbereitet

- Moayed hat nach dem Ensemble-Abschluss ausdrücklich weitere autonome Verbesserung beauftragt, auch über den nächsten Prototyp hinaus. Die abgeschlossenen Studien bleiben geschlossen; neue Hypothese und separate Belege. V14 und ZIP unverändert.
- Historische Detailprüfung: 277 Halterabzüge, davon268 mit sichtbarem Gegner in erweiterter SAP-Nähe; die übrigen neun von negativen Energiefeldern. Ein konservativer „sicher halten“-Filter trifft null Fälle. Keine Fehlentscheidung allein aus Abzug/Vakanz ableiten.
- Neuer [Plan](superpowers/plans/2026-11-08-holder-rollout-probe.md): eingefrorenes V14, gleiche Situation einmal normal und einmal mit einmaligem STAY-Vorschlag, vollständige Regeln/Teamfolgen, zwölf Folgeschritte. Höchstens96 Paare aus zwölf bekannten Spielen; noch keine Spiele gestartet. Vorab Machbarkeitsfilter, danach nur bei tatsächlichem Einfluss separates Lernen auf anderen Karten.
- Gezielte Tests und unabhängiger Review vor Modellläufen; Source-Freeze und maximal zwei Prozesse bleiben. Nutzer erlaubt restliches Kontingent, Resets ausschließlich durch ihn. [Übergabe](../experiments/analysis/decision_learning_20261108/HANDOFF.md).

## 08.11.2026 – Ensemble-Welle abgeschlossen: V14 bleibt

- Vollständige unabhängige REPLACE36-Validierung: **3200 Spiele, 15 Jobs**, keine Remis/Ausfälle. Solution REPLACE36 **193/200**, V14 **194/200**; Sechserpanel **930/1200 statt962/1200**, Δ −2,67 pp [−6,25; +0,92]. Direkt **206/400 =51,5 % [44,5;58,5]**; default beide200/200. Sechs von zehn festen Übernahmebedingungen verfehlt, kein bestätigter Gesamtgewinn, keine Übernahme. [Abschlussbericht](ENSEMBLE_ABSCHLUSS_20261108.md).
- Unabhängiger Audit PASS: alle3200 Rohzeilen,317 Quellen,129 gebundene Eingaben,85 alte Nachweise;262 Kennwerte bis1e-12 reproduziert. Root-Werkzeugtests zuvor228+43 bestanden. Source-Freeze f9e1195 eingehalten, alle eigenen Prozesse/Wachhalten beendet; danach eigenen Dokumentationsstand46e0fcf sicher übernommen. Keine neuen Mahmoud-Commits beim Abschlussabgleich.
- Insgesamt4760 vollständige Vergleichsspiele einschließlich1560 Vorauswahl; unbekannte interne Ausführungen des früheren großen Abbruchs separat. Kein Nachschlag, Nachrücker oder automatischer weiterer Versuch. Neue Modelle bleiben experimentell. V14-Gewichte und ZIP unverändert, Sicherungen erhalten. Remote-Abgleich-Automation pausiert. Veröffentlichung des fertigen Ergebnisstands folgt in diesem Commit; kein Stärkenachweis durch bloßes Trainieren behauptet.

## 08.11.2026, 06:20 Berlin – begrenzter REPLACE36-Frischdatenvergleich läuft

- Tatsächlich gestartet unter Quellstand `f9e1195bb65b6587206685971b3ce11e604666db`:15 Jobs/3200 Spiele, maximal zwei Spielprozesse. Controller78722, eigener Wachhalteprozess78738. [Startbeleg](../experiments/analysis/replacement_validation_20261108/started.json). Noch kein Ergebnis oder neuer Stärkegewinn behauptet.
- Maßgeblich: Studienkopie `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15`, `experiments/analysis/replacement_validation_20261108/validation/state.json`. Keine zweite Instanz, keine parallelen Tests, keine Änderungen an Quellen/HEAD/Modellen bis zum vollständigen Ende. Diese Startnotiz ändert nur den primären Checkout.
- Frischer Ressourcencheck und Eingabebindung bestanden; AC100%, Kontingentnutzung erlaubt. Unabhängiger Beobachter hält Nutzungsbeleg aktuell, prüft Prozesse und GitHub. Einmaliger fester Umfang, kein Nachschlag bei negativem/unklarem Ergebnis. V14 und ZIP unverändert.

## 08.11.2026 – Werkzeug für begrenzten Frischdatenvergleich geprüft

- Separates Werkzeug `replacement_validation.py` in `e5b6345`; bestehende Auswahl, Nomination und Auswertungsregeln bleiben unverändert. Exakte REPLACE36-/V14-Dateien, Herkunft, Karten, Quellen, Prozessbesitz und vollständige Rohdaten vor Auswertung gebunden. Keine automatische Übernahme.
- **Tatsächlich geprüft:** Root hat 228 Tests plus 43 Untertests erneut ausgeführt; bestanden. Unabhängiger Code-/Schema-Review PASS ohne offene Befunde. Prüfungen verwenden synthetische Daten und sind keine gespielten Leistungspartien. [Prüfbelege](../experiments/analysis/replacement_validation_20261108/).
- Begrenzter Umfang unverändert: 200 Spiele je Modell/Gegner und 400 direkte Duelle, zusammen3200; deutlich weniger als frühere große Bestätigungen. Höchstens zwei Spielprozesse. Kein Nachlegen bei unklarem Ergebnis. Noch nicht gestartet; frischer Ressourcen-/Quellencheck nach Veröffentlichung erforderlich. V14 und ZIP unverändert, origin/main beim Abgleich06fecb5, keine neuen Mahmoud-Commits.

## 08.11.2026 – getrennte Validierung der Austauschhypothese vorbereitet

- Die kompakte Auswahl bleibt abgeschlossen mit `nominee:null`. Ein unabhängiger Methodenreview bewertet einen einmaligen Frischdatentest des exakt bestehenden REPLACE36 unter dem autonomen Auftrag als sinnvoll, wenn Entstehung aus den Diagnoseergebnissen und statistische Grenzen ausdrücklich benannt werden.
- [Separater Vorabplan](superpowers/plans/2026-11-08-replacement-validation.md): nur V14 gegen REPLACE36, 100 frische Karten für sieben Gegner, 200 separate Direktkarten, beide Seiten, genau15 Jobs/3200 Spiele. Unveränderte sieben ursprüngliche Ensemble-Gates und drei Zusatzbedingungen. Kein Nachschlag, Nachrücker, Modelltraining oder automatischer weiterer Versuch bei negativem/unklarem Ausgang. Zusammen mit Auswahl1560 maximal4760 vollständige Leistungsspiele; unbekannte Ausführungen des früheren Abbruchs separat.
- Origin-Beleg bindet die exakten beiden Modelle und sämtliche abgeschlossenen Entdeckungsdaten an Prüfsummen. Frühere Ergebnisse werden nicht gepoolt. Neue Karten2000000–2000099 und2100000–2100199 in acht lokalen Arbeitskopien ohne dokumentierte Überschneidung/Lesefehler. Werkzeuge werden separat umgesetzt, damit die alten Auswahlregeln unverändert bleiben. Noch kein Start oder Ergebnis dieser neuen Validierung.

## 08.11.2026 – kompakte Auswahl vollständig; kein nominierter Nachfolger

- Alle39 Jobs/1560 Spiele vollständig, unabhängig gegen Rohdaten/Prüfsummen nachgerechnet. Sechserpanel V14 185/240; A39 202, B39 193, ALL42 205, REPLACE36 202. Solution V14 38/40, A39/B39/REPLACE36 39/40, ALL42 40/40; default überall40/40. Direkt A39/ALL42 je18/40, B39 14/40, REPLACE36 28/40.
- A39/B39/ALL42 verfehlen direkt mindestens50%; REPLACE36 bleibt gemäß Vorabplan nur Diagnose. `nominee:null` bleibt unverändert, keine kompakte Bestätigung. ALL42s40/40 sind keine allgemeine100%-Garantie; Auswahl klein und explorativ. [Vollständige Einordnung](ENSEMBLE_AUSWAHL_20261108.md).
- Unabhängiger Audit bestätigt alle39Jobs,1560 Zeilen und sämtlichen Bootstrap-/Gatewerte bis1e-12. Source-Freeze2146494 eingehalten; alle eigenen Prozesse inklusiveWachhalten beendet. V14/ZIP unverändert. Danach sichere Übernahme des eigenen Dokumentationscommits57f896e.
- Root folgt dem unabhängigen Methodenreview: separate prospektive Validierung genau des diagnostisch interessanten REPLACE36, maximal3200 neue Spiele, unveränderteGates, keine Modelländerung/Nachrücker/Nachschläge. Keine Umdeutung als alteNomination; Ergebnis motiviertneueHypothese. Folgetest noch inVorbereitung, Gesamtausführungen des gestoppten Großstarts zusätzlich unbekannt. Nach diesem begrenzten Folgetest kein automatischer weitererVersuch.

## 08.11.2026, 04:57 Berlin – kompakte Auswahl läuft

- Tatsächlich gestartet: 39 Jobs / 1560 Spiele, Profil `compact20261108`, maximal zwei Spielprozesse. Supervisor PID52177 mit eigenem Wachhalteprozess PID52193; erste Kinder 52218/52224. Startmoment: V14 gegen Solution und sol92_sq, noch kein vollständiger Ergebnisblock. Keine Stärkebehauptung.
- Aktiver Studienworktree: `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15`. Verbindlicher Live-Stand `experiments/analysis/ensemble_diversity_20261108_compact/selection/state.json`, [Startbeleg](../experiments/analysis/ensemble_diversity_20261108_compact/started.json). Keine zweite Instanz starten. Frühere große Auswahl ist bewusst beendet und getrennt.
- **Source-Freeze:** `2146494ee12ce288b48ae69bde119198cf8316b9` durch Auswahl und eventuelle Bestätigung unverändert. Keine Tests/pytest parallel, keine Quellen-/HEAD-/Modelländerung in der Studienkopie. Diese Startdokumentation verändert ausschließlich den primären Checkout. Remote-Überwachung prüft neue Commits, integriert erst nach Ende des gesamten Vergleichs.
- Kontingentfreigabe: restliche Nutzung erlaubt, laufender Nachweis strikt aktuell, kein automatischer Reset. Netzstrom100% beim Start. Eine unabhängige Überwachung prüft Quota/Prozesszustand/GitHub; alle Modell-/Abgabehashes bleiben geschützt. Nach vollständiger Auswahl nur einen nach festen Gates qualifizierten Kandidaten auf maximal3200 frischen Bestätigungsspielen prüfen; bei keinem Kandidaten diese Welle beenden.

## 08.11.2026 – Codex: Nutzer reduziert Vergleichsumfang vor Ergebnisprüfung

- Der erste große Auswahlcontroller wurde tatsächlich gestartet (Quellstand `f797627`, PID46618), anschließend auf Moayeds ausdrücklichen Wunsch nach weniger Testspielen kontrolliert beendet. Zwei Referenzjobs waren aktiv; keine vollständigen Ergebnis-CSV gespeichert, keine Ergebniswerte betrachtet. Tatsächlich intern berechnete Partien lassen sich daraus nicht exakt zählen. Alle eigenen Prozesse beendet; alte Daten/Reservierungen bleiben erhalten, ursprüngliche Kartenblöcke werden nicht wiederverwendet.
- Neuer vorab fester kompakter Umfang: 20 Karten für fünf Rollen gegen sieben Gegner plus vier direkte V14-Vergleiche =1560 Auswahlspiele. Nur ein qualifizierter Kandidat: 100 neue Karten gegen sieben Gegner und 200 separate Direktkarten =3200 Bestätigungsspiele. Jeweils beide Seiten, maximal4760. Entspricht dem Gesamtumfang der früheren Netzstudie, mit anderer Kartenverteilung und geringerer Solution-Präzision. Kein nachträgliches Nachlegen bis Signifikanz.
- Gleiche Modelle, Gegner, Rangfolge und Übernahmegates. Ein unklarer Ausgang qualifiziert keinen Nachfolger; V14 bleibt. [Neuer kompakter Plan](superpowers/plans/2026-11-08-ensemble-compact.md). Werkzeugänderung `f903de9` unabhängig geprüft (PASS). Root: 123 Tests plus 43 Untertests in 9,44 Sekunden bestanden; echter vorbereiteter Plan validiert. Seedprüfung über acht Arbeitskopien ohne dokumentierte Überschneidung oder Lesefehler. Noch keine kompakten Leistungsspiele gestartet; Start erst nach Veröffentlichung und erneutem Ressourcencheck.

## 08.11.2026 – Codex: Kontingentfreigabe und Fortsetzung des Ensemblevergleichs

- Moayed hat ausdrücklich die Nutzung des gesamten restlichen Kontingents freigegeben; die 30-%-Reserve gilt für diesen Auftrag nicht mehr. Einen gegebenenfalls nötigen Reset übernimmt er selbst. Keine Reset-Einlösung durch Codex.
- Sechs fertige Netze und A39/B39/ALL42/REPLACE36 aus `c624b09` bleiben unverändert. Null Auswahl-/Bestätigungsspiele zum Beginn dieser Fortsetzung; kein Stärkegewinn behauptet. Keine Wiederholung fertiger Trainings.
- Der Vergleichscontroller erhält eine explizite Kontingentobergrenze (Standard65, dieser Lauf100), mit unveränderten Prüfungen für bekannte, aktuelle und erlaubte Nutzung. Quellen-/Modellbindung, höchstens zwei Spielprozesse und sämtliche statistischen Gates bleiben bestehen. [Enger Umsetzungs-/Fortsetzungsplan](superpowers/plans/2026-11-08-ensemble-budget-resume.md).
- Startvorbereitung: Repository/Remote beide `c624b09`, keine neuen Mahmoud-Commits, keine aktiven Modellprozesse, Netzstrom100%. Umsetzung `9c103a1` geprüft: Root107Tests plus43Untertests bestanden (11,04s), unabhängigerReview ohne substantielleBefunde. AlleKandidatenhashes erneutidentisch. TatsächlicherStart folgt erst nach diesemCommit/Abgleich; dieseZeilen behaupten keinen laufendenVergleich.

## 07./08.11.2026 – Codex: sechs neue Netze fertig; größere Ensembles vorbereitet

- Neuer Versuch r1 vollständig: sechs × 3000 Lernspiele, insgesamt 19.488 Ausführungen einschließlich Vorlauf/Validierung und 2.700.000 Updates. Alle sechs Endstände unabhängig technisch geprüft; Rohpläne, endliche veränderte Q/Target/Adam, 24 Validierungsgrenzen, Konfiguration und Prüfsummen bestanden. Keine parallelen Tests während Training; alle eigenen Rechen-/Wachhalteprozesse beendet.
- A39/B39/ALL42 sowie diagnostisches REPLACE36 aus exakt den vorab festgelegten Mitgliedern gebaut und wieder geladen. Neue Endcheckpoints und Kandidaten für Mahmoud unter `experiments/candidates/ensemble_diversity_20261107/`; Rohdaten/Receipts versioniert, große Replay-Puffer lokal. [Abschluss und Grenzen](ENSEMBLE_TRAINING_20261107.md), [unabhängiger Audit](../experiments/analysis/ensemble_diversity_20261107/operations/final_training_audit.md).
- **Noch kein neuer Stärkegewinn belegt.** Null Auswahl-/Bestätigungsspiele. Bei 64 % Kontingentverbrauch gesicherter Zwischenstand wegen bisheriger 30-%-Reserve; Rückfrage zur Reserve unbeantwortet, kein Reset. Die festen 7800 Auswahlspiele erst nach ausreichender Ressourcenfreigabe starten; bei Nominierung einmalige 23.200-Spiele-Bestätigung. Keine Wiederholung fertiger Trainings, keine Übernahme anhand bekannter Zwischenvalidierung.
- Remote nach Trainingsende geprüft; keine neuen Mahmoud-Commits gegenüber `73119c7`. Studienkopie am sicheren Übergang auf diesen Dokumentationsstand aktualisiert, historische Trainingspins bleiben `6ad3452`. Wiederkehrender Remote-Abgleich pausiert. V14 und ZIP in beiden Checkouts bytegleich; keine Abgabeänderung. Veröffentlichung erfolgt als zusammenhängender geprüfter Trainings-/Artefaktstand; abschließender Kontingentstand 64 %.

## 07.11.2026 – Codex: geprüfter Versuch r1 tatsächlich gestartet

- Supervisor 27750 gestartet; anfängliche Kinder A0/B0 27767/27773, eigener Wachhalteprozess 27756. Maßgeblich ist **`experiments/analysis/ensemble_diversity_20261107/training_run_r1/state.json`** in der Studienkopie. Der ältere Pfad `training_run/state.json` beschreibt ausschließlich den unterbrochenen Versuch. Keine zweite Instanz starten.
- Studie bleibt auf `6ad34527673e29f0e50e2dacc917e5ded59f0343` eingefroren. Neue Runs heißen `experiments/runs/20261107_diversity_r1_<ARM>`; Vorbereitung `20261107_diversity_r1_prepared`. Gleichheit aller sechs initialen Tensoren, Konfigurationen, Eltern, Zufallsstarts und vollständigen Spielpläne vor Start geprüft. [Prüfnachweis](../experiments/analysis/ensemble_diversity_20261107/operations/retry_initial_equality.json), [Startmomentaufnahme](../experiments/analysis/ensemble_diversity_20261107/operations/retry_started.json).
- Netzstrom erkannt, zuletzt 99 % Akku; Kontingent beim Start 57 % verbraucht. Maximal zwei Modellläufe, Kontingentreserve unverändert. Keine parallelen Tests. Alle Review-Korrekturen und Werkzeuge vor diesem Start geprüft und veröffentlicht (`4ff93d9`, `6ad3452`).
- Alte Teilstände und Rohprotokolle unverändert erhalten; r1 ist ein neuer Versuch, keine exakte Fortsetzung und kein Stärkeergebnis. V14 und ZIP bytegleich. Remote-Abgleich auf r1-Pfad aktualisiert; neue Commits während des Freeze zunächst nur prüfen.

## 07.11.2026 – Codex: fester Ensemblevergleich technisch vorbereitet

- Neue Werkzeuge bauen ausschließlich A39/B39/ALL42/REPLACE36 aus sechs vollständig geprüften Endständen, prüfen die exakte Netzreihenfolge und V14-Konfiguration und erlauben keine Nutzung der unterbrochenen Teilstände. Alte V14-Dateien bleiben schreibgeschützt.
- Der Vergleichscontroller führt die festen 39 Auswahljobs mit höchstens zwei Spielprozessen aus, bindet Karten, Gegner, Modelle, Quellen und Ausgaben über Prüfsummen und verweigert unvollständige Ergebnisse. Kontingentnachweis muss aktuell sein; bei mindestens 65 % Verbrauch Stopp. Die Bestätigung wird erst nach erneut errechneter, identischer Auswahlentscheidung freigegeben. Kein automatisches Nachrücken oder Neustarten.
- Auswertung trennt echte Siege/Remis/Niederlagen vom Score mit halbem Remispunkt, nutzt ganze Karten für den gepaarten Bootstrap und die vorher festgelegten Gates. Alle Auswahlrollen müssen vollständig sein, auch REPLACE36; dieser diagnostische Kandidat darf nicht nominiert werden.
- **Tatsächlich geprüft:** 287 Tests plus 16 Untertests vor den Review-Korrekturen; danach Root-Prüfung mit 138 gezielten Tests plus 16 Untertests bestanden. Enthalten sind synthetische vollständige 7800-/23200-Zeilen-Datensätze; diese sind **keine gespielten Partien**. Unabhängiger Review und enger Nachreview haben beide Befunde als behoben bewertet. [Review](../experiments/analysis/ensemble_diversity_20261107/operations/comparison_review.md), [Korrekturtests](../experiments/analysis/ensemble_diversity_20261107/operations/comparison_fix1.md).
- Noch keine neuen vollständigen Modelle, Kandidaten oder Leistungsdaten. Nächster Schritt ist der separat dokumentierte frische Trainingsversuch; anschließend vollständige Lernabnahme und Vergleich.

## 07.11.2026 – Codex: Trainingsunterbrechung aufgeklärt und sicherer Neuanlauf vorbereitet

- **Tatsächlicher Abbruch um 14:14 UTC / 15:14 Berlin:** Codex hatte leichte Werkzeugtests im primären Checkout parallel erlaubt. Die vorhandene Prozessüberwachung blockiert jedoch auch `pytest` und stoppte deshalb beide eigenen Trainings. Das war ein Koordinationsfehler, kein Fehler von Mahmoud und kein Verlust der V14-Abgabe. Die neue gemeinsame Arbeitsregel trennt Tests und Modellläufe zeitlich.
- A0 endete nach 1906 Lernspielen/285.900 Updates, B0 nach 2178/326.700; zusammen zusätzlich 240 Vorlauf- und 160 Validierungsausführungen. **4484 tatsächliche Ausführungen**, darunter 4084 Lernspiele; beide Teilstände lokal gespeichert und ausdrücklich nicht nominierbar. Alte Run-Verzeichnisse und Startreservierung bleiben erhalten. Keine Leistungs-Auswahl oder Bestätigung gestartet.
- Alle damaligen eigenen Prozesse inklusive Wachhalteprozess nachweislich beendet. Ein zusätzlicher Fehler beim Prüfen bereits endender Prozessgruppen wurde protokolliert; die genaue ursprüngliche Ursache der Berechtigungsfehlermeldung ist nicht reproduziert. Konservative Behandlung mit unabhängiger Prozessprüfung und Regressionstests ergänzt; bestehende Fremdprozess-Sperre bleibt bestehen.
- Gespeichert wurden Gewichte, Optimierer und Zähler, aber kein vollständiger Replay-/Zufallszustand. Daher keine Behauptung eines exakten Fortsetzens. **Explizit geprüfter neuer Versuch** mit identischen Eltern, Startzuständen, Karten, Zufallsstarts, Gegnerplänen, 3000 Lernspielen und Endstandsregel vorbereitet: neue Namen `20261107_diversity_r1_<ARM>` und neues vorbereitetes Verzeichnis. Keine Auswahl anhand der alten Zwischenwerte. Kein automatischer Neustart; alte Ausgaben werden nicht überschrieben.
- Prüfung: ursprünglicher Root-Gesamtlauf 287 Tests plus 16 Untertests bestanden; nach Review-Korrektur weitere 138 gezielte Tests plus 16 Untertests bestanden (8,54 Sekunden). Unabhängiger Review hat die Bestätigungsbindung an den tatsächlich errechneten Auswahlkandidaten und die Prozessbeendigung geprüft; beide Befunde behoben und erneut abgenommen. [Unterbrechungsnachweis](../experiments/analysis/ensemble_diversity_20261107/operations/interruption_20261107_1414.json).
- **Noch offen:** tatsächlicher Neuanlauf nach Commit/Abgleich, sechs vollständige Modelle, Auswahl und gegebenenfalls Bestätigung. V14 und ZIP unverändert; keine neue Stärke behauptet.

## 07.11.2026 – Codex: erster Lernmeilenstein geprüft, Vergleich präzisiert

- Unabhängige technische Momentprüfung nach B0s erstem 1000-Spiele-Meilenstein: 150.000 Updates, geänderte Gewichte/Adam-Zustände, 300.000 Replay-Einträge; Validierung mit exakter V14-Konfiguration und unverändertem Lern-/Zufallszustand. Alle geprüften Rohzeilen entsprechen Karten, Seiten und Gegnerplan; protokollierte Verluste endlich. A0 läuft ebenfalls weiter. Noch keine vollständigen Endmodelle oder Aussage über neue Ensemble-Stärke.
- Netzstrom inzwischen vom Gerät erkannt. Beide Modellprozesse laufen weiter; Studienquellen und HEAD bleiben bei `b683bc7` eingefroren. Dieser Bericht verändert ausschließlich den primären Checkout, nicht den Trainingslauf.
- Anschlussreview bestätigt 39 geplante Jobs mit 7800 Auswahlspielen; bisher null gestartet. Alte Vergleichs-CLI-Voreinstellungen passen nicht zum lokalen Sechserpanel, daher vorhandene Statistikfunktionen mit den ausdrücklich festgelegten Parametern wiederverwenden.
- Vor Leistungsdaten präzisiert: Score zählt ein Remis halb; zusätzlich echte Siege/Remis/Niederlagen berichten. Bestehende Gates bleiben erhalten, zusätzlich echte Solution-Siegquote mindestens Baseline und echte default-Siegquote mindestens 99 % in Auswahl und Bestätigung. [Protokoll](superpowers/plans/2026-11-07-ensemble-comparison.md), [Review und Audit](../experiments/analysis/ensemble_diversity_20261107/operations/).
- Offen: sechs vollständige Trainingsabschlüsse, unabhängige Endprüfung, feste Ensemble-Auswahl und gegebenenfalls einzige frische Bestätigung. V14 und abgegebene ZIP bleiben unverändert.

## 07.11.2026 – Codex: neue sechsarmige Trainingswelle gestartet

- **Tatsächlicher Start:** Der einmalige Supervisor läuft im Studienworktree `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15` auf eingefrorenem Quellstand `b683bc7123fb159a294b8bbe3fa2a392477e80a6`. Eigentümer-PID 6274; erste Kinder A0/B0 6291/6297. Keine zweite Kopie starten. Momentaufnahme nach Start: 38/42 Vorlaufspiele, noch keine Lernupdates; daraus folgt noch kein Stärkeergebnis.
- Verbindlicher Live-Stand: `experiments/analysis/ensemble_diversity_20261107/training_run/state.json` in der Studienkopie; Einzelstände `experiments/runs/20261107_diversity_<ARM>/progress.json`. Zwei Arme aktiv, A1/B1/A2/B2 folgen automatisch. Geplant 18.000 Lern-, 720 Vorlauf- und 768 Validierungsausführungen. Keine automatische Auswertung/Übernahme durch den Supervisor; die feste Vergleichsphase folgt erst nach unabhängig geprüften vollständigen Endständen.
- Einmaliger Abbruch: `python -m scripts.ensemble_diversity_supervisor stop` in der Studienkopie setzt `/tmp/sherlock-diversity-20261107/STOP`. Laufende Spiele werden zu Ende geführt, Zwischenstände gesichert, Teilstände bleiben nicht nominierbar. Kein automatischer Neustart. Unter 35 % Akku keine neuen Kinder, bei höchstens 25 % ohne Netzstrom geordneter Stopp. Wachhalteprozess wird vom Supervisor besessen und am Ende beendet. Nutzer kündigt Anschluss an; zuletzt tatsächlicher Akkubetrieb 56 %.
- Vorbereitung veröffentlicht: `cda52d9` (Werkzeuge/Design/Tests), `b683bc7` (24 echte Smoke-Ausführungen und Abnahme). Root: 142 gezielte Tests bestanden; Smoke je 300 tatsächliche Updates, erfolgreiches Wiederladen, keine Änderung an V14/ZIP. Produktive Endstände sind noch nicht vorhanden.
- Remote-Überwachung und Kontingentkontrolle aktiv, bisher letzter Verbrauch 47 %. Früher beauftragter dreistündlicher Repo-Abgleich wieder aktiviert. Bis Trainingsende keine Änderungen an Quellen/HEAD der Studienkopie; neue Remote-Commits zunächst nur prüfen. Dieser Startbericht wird ausschließlich im primären Checkout ergänzt und erst nach Source-Freeze in die Studienkopie übernommen.


## 07.11.2026 – Codex: neue Ensemble-Studie nach der Präsentation vorbereitet

- Moayed beauftragt erneut autonome Trainings und Verbesserungen, Schwerpunkt mehr Netze, ohne feste Uhrzeit. Historischer Präsentations-/Trainingsstopp aufgehoben; mindestens 30 % Kontingentreserve bleibt erhalten.
- Remote und beide lokalen Arbeitskopien zu Beginn auf `a9b5202`; keine laufenden Modellprozesse. Bestehenden isolierten Worktree auf `improvement/ensemble-diversity-20261107` wiederverwendet; fünf historische unversionierte Run-Verzeichnisse erhalten.
- FO42-/FT18-Misserfolge geprüft; neue Welle statt Wiederholung: drei V14-Netzfamilien × zwei Gegnermischungen, sechs neue Endstände mit je 3000 Lernspielen. Feste Kandidaten A39/B39/ALL42; REPLACE36 rein diagnostisch. [Design](superpowers/specs/2026-11-07-ensemble-diversity.md), [Plan](superpowers/plans/2026-11-07-ensemble-diversity.md).
- Tatsächlich geprüft: 88 bestehende gezielte pytest-Tests bestanden; Seedprüfung in acht lokalen Worktrees ohne aufgezeichnete Überschneidung (externe/seedlose Läufe nicht abgedeckt). Zwei unabhängige Analysen zu Training und Evidenz; neue Trainingswerkzeuge noch in Umsetzung. Noch kein neues Training oder Stärkeergebnis.
- Werkzeugstand `cda52d9`: Root hat 142 gezielte Tests bestanden gesehen; unabhängiger Review-Befund zum Validierungsabbruch korrigiert und regressionsgeprüft. Zwei echte Smoke-Läufe mit insgesamt 24 Ausführungen abgeschlossen, je 300 Updates, geänderte Gewichte und erfolgreiches Wiederladen; ausdrücklich kein Stärkenachweis. V14-/ZIP-Hashes erneut unverändert. Sechs lange Lernarme als nächster Schritt vorbereitet.
- Referenz V14 (36 Netze), bestehende Sicherungen und abgegebene ZIP bleiben unverändert. Offene Punkte: Werkzeugtests/Review, reale Smoke-Läufe, Netzstromprüfung, neue Trainingswelle, vorab festzulegende Leistungsvergleiche. Startkontingent 44 % verbraucht; Mac zunächst 62 % Akku, Nutzer kündigt Netzteil an.

## 05.11.2026 – Codex: Mahmouds aktuelle Battle-Präsentation lokal übernommen

- Auf Moayeds Bitte die drei neuen Präsentationscommits `0d54780`, `506e074`, `6955a51` geprüft und beide lokalen Arbeitskopien ohne Überschreiben eigener Dateien auf `6955a51` vorgezogen. Nur Präsentation/Dokumentation betroffen; Agentenquellen, Gewichte und ZIP vor/nach per Prüfsumme unverändert. PDF und zugehörige Stichpunkte in beiden Arbeitskopien identisch.
- **Vergleich zur zuvor geübten Fassung `a33d71a`:** PDF-Seiten 1–8 textgleich; HTML-Folien 1–8 und Moayeds Sprechtexte 1–4 unverändert. Neue Folie 9 gehört Mahmoud. Moayeds alte Schlussfolie 9 ist jetzt Folie 10 und inhaltlich um Besonderheiten und Erkenntnisse erweitert. Reservefolien nur von 10–12 auf 11–13 umnummeriert. Folie 6 erhält zusätzliche Spielzahlen im Sprechtext; Folie 8 einen gekürzten Sprechtext und neue Übergabe.
- **Aktueller Plan:** Moayed 1–4 und 10 (4:55), Mahmoud 5–9 (5:45), zehn Hauptfolien plus drei Reserven; 10:40 korrekt addiert, weiterhin keine gemessene Probe. Neue PDF-Seiten 9/10 gerendert und visuell geprüft. Unabhängiger Vergleich von Inhalten, Rollen, Zeiten und neuen Zahlen mit den genannten Berichten. Präsentation und Stichpunkte selbst unverändert übernommen; keine neuen Spiele oder Trainings.
- **Für die Erklärungen/Probe präzisieren:** 165.000 bezeichnet das Trainingsbudget der Herkunftsläufe einschließlich Nachtraining, nicht einen gesicherten exakten Auswahlzeitpunkt jedes ursprünglichen Checkpoints. Über 1,3 Millionen Spiele ist die historische Projektzählung vom 01.11., spätere Studien kommen hinzu. Das Beispiel +1,8/−0,35 pp auf Folie 10 betrifft die Regelkombination `v19cr` und den Mittelwert über sechs Gegner, keine isolierte Regel oder allein Solution_92. „Schüsse auf unsichtbare Gegner“ heißt Schüsse auf vermutete besetzte Punktefelder, keine sichere Kenntnis des Aufenthaltsorts.
- **Übergabe:** Moayeds Erklärungen für 1–4 können unverändert bleiben; Schlussfolie 10 neu durchgehen. Alte Abschnitte im Prüfbericht historisch gekennzeichnet. Der JSON-Prüfnachweis mit Datum 04.11. gehört zur alten zwölfseitigen Fassung; er ist kein Nachweis für die neue PDF. Offen bleibt die gemeinsame Probe mit Uhr.

## 05.11.2026, 15:47 Berlin – Claude Code: Schlussfolie mit „Besonders“ und „Gelernt“

- **Grund:** Mahmouds Punkte „was Sherlock besonders macht“ waren nur indirekt enthalten; die Erkenntnisfolie der Präsentationen vom 16./23.10. war bei der Kürzung entfallen. Das Bewertungsschema (Kursfolie 11) liegt weiter nicht vor.
- **Änderung:** Folie 10 „Im Battle“ (Moayed) behält Kernsatz, Ergebnis und „Fragen?“; die drei Wiederholungspunkte sind durch zwei Spalten ersetzt: **Das macht Sherlock besonders** (Punktefelder aus dem Punktestand erschließen, 36 Netze mit Maske/Regeln, Schüsse auf unsichtbare Gegner) und **Was wir gelernt haben** (Netze und Regeln ergänzen sich, nur neue Karten zählen mit `v19cr` +1,81 auf Dev A / −0,35 pp frisch, mehr Netze oder Training nicht automatisch besser). Sprechtext Folie 10 0:45 → 1:05; Plan Moayed 4:55, Mahmoud 5:45, gesamt 10:40 (keine gemessene Probe; Kürzungshinweis im Text). Stichpunkte, README, CLAUDE.md und Prüfprotokoll angeglichen.
- **Prüfungen:** Beispielzahlen gegen die Arbeitsstand-Einträge vom 01.11. (15:22, 17:29) abgeglichen. PDF neu gerendert, 13 Seiten; Seite 10 visuell geprüft, übrige Seiten textgleich mit der vorherigen Fassung. Nur Präsentation/Dokumentation, keine Spiele.
- **Offen:** Moayed muss die geänderte Folie 10 und seinen neuen Sprechtext kennen. Gemeinsame Probe mit Uhr.

## 05.11.2026, 15:32 Berlin – Claude Code: Spielzahlen im Sprechtext zu Folie 6

- Auf Mahmouds Auftrag spricht Folie 6 jetzt zusätzlich die Projektgröße aus: 165.000 Trainingsspiele in den 36 Abgabenetzen und über 1,3 Millionen Spiele im ganzen Projekt, etwa zur Hälfte Training und Tests. Quelle ist die README-Zählung vom 01.11. (640.104 Training, 65.824 Zwischenprüfungen, 644.419 Bewertung, zusammen 1.350.347), nicht neu gezählt; spätere Studien kommen hinzu. Folie selbst unverändert. Planzeit Folie 6 1:10 → 1:15, Mahmoud 5:45, gesamt 10:20 (keine gemessene Probe). Stichpunkte, README, CLAUDE.md und Prüfprotokoll angeglichen; nur Dokumentation, keine Spiele.

## 05.11.2026, 15:13 Berlin – Claude Code: Battle-Folie „Neu seit letzter Woche“ ergänzt

- **Grund:** Die Aufgabenstellung verlangt neben Funktionsweise und Training ausdrücklich „kurz die neuesten Entwicklungen der letzten Woche“. Die Kürzung vom 04.11. hatte die Versionsübersicht entfernt; V13 und die Prüfungen vom 02.–04.11. kamen nicht mehr vor, V11/V12/V14 nur ohne Hinweis, dass sie neu sind. Mahmoud hat die Ergänzung beauftragt und betont, dass der Professor eine genaue Erklärung von Ablauf, Entscheidungsprozess und Netznutzung erwartet.
- **Änderung:** Neue Hauptfolie 9 (Mahmoud, 0:40) im bestehenden Design: V11–V14 je mit Datum, Änderung, **Schritt im Ablauf** (Bezug zu Folie 2) und Solution_92 vorher → nachher aus dem jeweiligen gepaarten Übernahmevergleich; Kasten zu den Prüfungen 02.–04.11. (A2 38/40 wie V14, direkt 14/40; V14 bleibt). „Im Battle“ jetzt Folie 10, Reserve 11–13. Folie 8 im Sprechtext von 1:40 auf 1:25 gekürzt (Detail zu seitlichen Zügen als Nachfragehinweis). Neue Planzeit Moayed 1–4 und 10 4:35, Mahmoud 5–9 5:40, gesamt 10:15. HTML, PDF, Stichpunkte, Prüfprotokoll, README und CLAUDE.md angeglichen.
- **Prüfungen:** Alle Zahlen der Folie gegen die Übernahmeberichte V11–V14 und den Aktionsschüler-Bericht abgeglichen; Schritt-Zuordnung gegen `config.py`/`main.py` (`art_splash`, `sap_still_splash`, `fog_sap`, `splash_min_drop`, `est_censor`, `neb_cross`, `cand_rescue` mit `obey_target`). PDF mit Headless-Chrome gerendert: 13 Seiten, 960 × 540 pt; neue Seite 9 visuell geprüft (erste Fassung hatte eine Überlappung von Fußnote und Kasten, behoben und erneut geprüft). Text der Seiten 1–8 identisch mit der vorherigen PDF, Seiten 10–13 identisch mit alten 9–12 bis auf die Seitennummer. Neue PDF SHA-256 siehe Commit. Keine Spiele, kein Training, keine Änderung an Agent, Gewichten oder ZIP.
- **Offen:** Moayed über die neue Folie und die geänderte Aufteilung informieren (er hatte die Kürzung gewünscht). Gemeinsame Probe mit Uhr; 10:15 ist ein Planwert. Bewertungsschema Kursfolie 11 liegt nicht im Repo und wurde nicht Punkt für Punkt geprüft.

## 04.11.2026, abends – Codex: Schlussprüfung vor der Vortragsprobe

- Auf Moayeds Bitte aktuelle zwölfseitige PDF (neun Hauptfolien), visuelle Darstellungen und Sprechtexte nochmals zusammen auf Vollständigkeit, Verständlichkeit und Professorfeedback geprüft. PDF/HTML/Stichpunkte in Arbeitskopie und primärem Checkout per Prüfsumme identisch mit der zuletzt freigegebenen Fassung. Unabhängiger pädagogischer Gegenreview ergänzt; keine wesentliche Inhaltslücke und kein zwingender weiterer Folienumbau festgestellt. Präsentation und Stichpunkte unverändert.
- Professorfeedback auf den Folien erfüllt: programmierte Ziele vor der Wegkorrektur (3/8), 79 Merkmale und sechs Q-Werte (4/5), Vorbereitung und Anwendung der Maske sowie nachgelagerte Regeln (2/7/8). Ensembleherkunft, Unterschied der Gewichte, Mittelwert statt Stimmen und mögliche gemeinsame Fehler sind enthalten; Training und Schritt-/Matchbelohnung auf 6. Hauptteil bleibt auf den Agenten konzentriert.
- **Schwerpunkte beim Üben:** Netzoutput (sechs Bewertungen) vom endgültigen Agentenbefehl unterscheiden. Auf Folie 7 ausdrücklich sagen: Spätere Regeln können die **gewählte Aktion** ändern; ihr Blindschuss hat eigene Prüfungen. Auf Folie 4 mit Energie 200/400→0,5, Zielrichtung und Nachbarfeld erklären, statt alle Tabellenzeilen aufzuzählen. Moayed behält 1–4 und 9, Mahmoud 5–8.
- **Noch offen:** Tatsächliche freie Erklärung und Zeitmessung in der gemeinsamen Probe; 9:50 ist weiter ein Planwert. Dichte Folien 2/4/8 beim Sprechen schrittweise zeigen; kleine Zusatzangaben nicht vorlesen. Die Lesbarkeit am konkreten Beamer wurde nicht getestet. Keine neuen Modelle, Spiele oder Gewichts-/ZIP-Änderungen.

## 04.11.2026, abends – Codex: Battle-Präsentation auf den Agenten konzentriert

- **Auftrag:** Weniger Folien und eine anschauliche Erklärung des tatsächlich abgegebenen Sherlock; Versionschronik und Fortschrittsübersichten aus dem Hauptteil entfernen. [PDF](../Sherlock_Battle_06-11-2026.pdf), [HTML](presentation/Sherlock_Battle_06-11-2026.html) und [Stichpunkte](../Sherlock_Stichpunkte_06-11-2026.md) jetzt **neun Hauptfolien + drei Reserven**, ursprüngliches Design erhalten. Neue Nummerierung bei weiter leichterem Teil für Moayed: **Moayed 1–4 und 9 (4:35), Mahmoud 5–8 (5:15)**; Plan 9:50, noch keine gemessene gemeinsame Probe.
- **Agentenerklärung:** Entscheidungsfluss zeigt programmierte Zielzuweisung vor Netzauswahl und Wegkorrektur. Eigene Folie mit sieben Merkmalsgruppen (10+4+20+5+30+6+4 = 79). Ensemblefolie erklärt gleiche Architektur, unterschiedliche Gewichte, 18 Grundnetze + 18 verwandte Nachtrainingspartner, Nutzen/Grenzen des Mittelns und ein reales Zahlenbeispiel. Regelkorrekturen enthalten eine schematische Hinderniskarte und Blindschuss → Overkill in tatsächlicher Reihenfolge. Maske begrenzt die Netzauswahl; spätere Regeln haben eigene Prüfungen. Training/Reward und ein eingeordnetes historisches Ergebnis bleiben enthalten; keine Versionschronik.
- **Fachprüfung:** Arbeit auf Netzherkunft, Stichpunkte und unabhängigen Gegenreview verteilt. Alle 36 Tensor-Hashes zusätzlich von Root nachgerechnet: 36 verschiedene Gewichtsstände, identische Bauart, je 152.967 Parameter. Herkunftsketten mit je 5.500 zusätzlichen Spielen bestätigt; keine 36 unabhängigen Neustarts behauptet. Fünf kleine Reviewbefunde korrigiert und nachgeprüft, keine offenen Sachbefunde. [Netznachweis](presentation/source/ENSEMBLE_BATTLE_0611_20261104.json), [Erklärung und Review](presentation/PRUEFUNG_BATTLE_0611_20261104.md).
- **Artefaktprüfung:** Alle zwölf Seiten gerendert und visuell kontrolliert; Textüberlagerungen im ersten Entwurf behoben und betroffene Seiten erneut angesehen. 960×540 pt, fortlaufende Nummern, keine Seitenüberläufe oder Inhalts-/Fußnotenüberlappungen. Rollen/Zeiten, 22 lokale Links der Stichpunkte und Diff geprüft. Schematische Weglängen unabhängig nachgerechnet: 7→8 bei hoch, 7→6 bei runter; Ziel unverändert. [Prüfnachweis](presentation/source/PRUEFUNG_BATTLE_0611_20261104.json).
- **Umfang und Übergabe:** README und CLAUDE folgen der neuen Gliederung; alte Prüfeinträge ausdrücklich historisch. 39 vorhandene Quell-/Gewichts-/ZIP-Prüfsummen in beiden Arbeitskopien unverändert, fremde unversionierte Dateien erhalten. Keine Inferenz, Spiele oder Trainings gestartet; kein Abgabeaustausch oder ZIP-Neubau. Remote beim sicheren Abgleich unverändert auf `87ec206`. Nächster Schritt ist, die neuen Sprechtexte gemeinsam durchzugehen und mit Uhr zu üben; Detailreserven nur bei Rückfragen zeigen.

## 04.11.2026, abends – Codex: Battle-Folien korrigiert, Rollen bestätigt

- Moayed beauftragt die Umsetzung der Präsentationsprüfung und bestätigt: **Moayed 1–5 und 12–13, Mahmoud 6–11**. [PDF](../Sherlock_Battle_06-11-2026.pdf), [HTML](presentation/Sherlock_Battle_06-11-2026.html) und [Stichpunkte](../Sherlock_Stichpunkte_06-11-2026.md) aktualisiert. Bestehendes Design, 13 Hauptfolien und vier Reservefolien erhalten; Planzeit 9:50 (Moayed 4:25 / Mahmoud 5:25), keine gemessene Probe.
- Tatsächlichen Ablauf Vorbereitung → Q-Mittel → maskierte Auswahl → Regelkette klargestellt. Blindschüsse und Overkill-Schutz korrekt erklärt; Q-Werte nicht als Sicherheit, Gedächtnis beim Matchwechsel präzisiert, Nachtraining den V10-Regeln zugeordnet. V12-Diagnose von allgemeinen V14-Aussagen getrennt, beide verfehlten V14-Hürden in der Reserve/FAQ genannt. Erkenntnisfolie auf drei einfache Aussagen verkürzt und abgeschlossene Versuche vom 02.–04.11. ergänzt. V14 bleibt Abgabe; Upload laut Teammitteilung bereits erfolgt, nicht selbst in Moodle eingesehen.
- Geprüft: alle 17 Seiten gerendert und visuell kontrolliert, letzte Layout-/Textkorrekturen erneut angesehen; 960 × 540 pt, kein Text außerhalb der Seiten und alle Bilder geladen. Unabhängiger fachlicher Gegenreview von HTML und Stichpunkten ohne offene Befunde; Rollen-/Zeit-, lokale Link- und Diff-Prüfung. Keine Programmtests oder Leistungsspiele nötig/gestartet. README, CLAUDE und [Prüfnotiz](presentation/PRUEFUNG_BATTLE_0611_20261104.md) angeglichen.
- Agent, Gewichte und vorhandene ZIP nicht verändert; Quelle und Abgabe zusätzlich per Vorher-/Nachher-Prüfsummen abgesichert. Fremde unversionierte Dateien erhalten. **Nächster Schritt:** Moayeds Folien erklären und zweimal mit Uhr proben. Training bleibt beendet.

## 04.11.2026, abends – Codex: Training beendet, Battle-Präsentation geprüft

- Moayed beendet die Trainingsarbeit ausdrücklich; laut seiner Mitteilung hat Mahmoud Sherlock bereits abgegeben. Moodle-Upload nicht selbst eingesehen. Keine neuen Trainings, Spiele oder Agenten-/Gewichts-/ZIP-Änderungen. GitHub-Abgleich vor der Prüfung unverändert auf `36a68ab`; keine erfassten aktiven Trainings-/Auswertungsprozesse gefunden.
- Battle-PDF, HTML-Quelle und Stichpunkte vom 01.11. geprüft, alle 17 PDF-Seiten gerendert und visuell angesehen; unabhängige Reviews zu tatsächlichem Entscheidungsablauf und Vortragsaufteilung. Design beibehalten, 13 Hauptfolien plus vier Reservefolien. [Befunde und Vorschlag](presentation/PRUEFUNG_BATTLE_0611_20261104.md).
- Relevante Korrekturen: Regeln können selbst Sap auslösen; Maskenwirkung von späteren Regeln unterscheiden; Q-Werte nicht als Sicherheit bezeichnen; Nachtraining unter V10- statt „allen heutigen“ Regeln; V12-Diagnoseanteile nicht als allgemeine V14-Werte; zwei verfehlte V14-Hürden in der Reserve vollständig benennen. Jüngste abgeschlossene Studien fehlen im Vortrag; keine davon ist neue Abgabe.
- Aufteilungsvorschlag: Moayed 1–5 und 12–13 (4:25), Mahmoud 6–11 (5:25), zusammen 9:50 Planzeit mit zwei Übergaben. Folien 11/12 und zugehörigen Sprechtext kürzen; Reserve 14–17 nur auf Nachfrage. Noch nicht vom Team bestätigt, PDF und bisherige Stichpunkte in diesem Prüfschritt unverändert. Offen: gezielte Folienkorrektur, Aufteilung abstimmen und Probe.

## 04.11.2026, 21:40 Berlin – Codex: A2-Lehreranker geprüft, V14 bleibt

- **Ergebnis:** Lehrerbeispiele verbessern beide RL-Kontrollen, aber kein neuer Agent ist gegenüber A2/V14 nachweislich besser. Solution auf denselben neuen Karten: V14 40/40, A2 39/40, ANCHOR25/26 je 36/40. Panel Anker 96/120 und 88/120 statt Kontrollen 81/120 und 75/120; direkt V14 nur 14/40 und 12/40. Beide verfehlen die vorab festgelegte Auswahl. Kein weiterer Versuch, keine Bestätigung, kein Abgabewechsel. [Bericht](A2_LEHRERANKER_20261104.md).
- **Umgesetzt:** drei getrennte Werkzeuge für Retention, passive Niederlagentraces und RL mit Lehreranker. A2 bleibt ein einzelnes 79→512→512-Dueling-Netz; Originalagent, Belohnungen und Spielregeln nicht verändert. Zwei Starts 25/26 jeweils ohne/mit 0,1 × maskiertem Lehrer-Aktionsverlust im selben TD-Optimierungsschritt. Alle vier Endstände gespeichert, keine Auswahl nach bekannter Validierung.
- **Tatsächlicher Umfang:** 24 bekannte Trace-Ausführungen + 928 Vorlauf-/Lern-/Validierungsspiele + 920 frische Diagnosepartien = 1.872 Studienausführungen. 96.000 Updates; beide Anker mit jeweils 6.144.000 ausschließlich erlaubten Lehrerziehungen und 24.000 aktiven Zusatzgradienten. Technische Tests/Vorfälle separat, nicht in diese Studienzahl mischen.
- **Befunde:** Frühere Entdeckung garantiert kein Halten der Punkte. Bei einem konkret untersuchten Abgang bevorzugte auch V14s Netzmittel LEFT; bloße Lehrerbindung behebt nicht jede Lehrerschwäche. Der Anker erhält Lehrerpräferenzen besser (78,77/80,94 % statt 73,20/77,37 %), bleibt aber unter A2 vor RL (86,70 %). Panelgewinne gegenüber Kontrolle +12,50 pp [2,50; 23,33] und +10,83 pp [0,83; 20,83]; explorativ, keine allgemeine Methodenfreigabe.
- **Prüfung:** vollständige Suite 1.307 Tests + 126 Untertests. Unabhängiger Lern-/Datenaudit, beide Retentionsprüfungen, 236 numerische Gegenprüfungen. Alle elf Diagnosejobs Exit 0, 303 Schritte/v2, keine fehlenden Zeilen oder abgefangenen Spielfehler. 266 Quellen und 153 Eingaben während der Diagnose unverändert. Modelle/Ergebnisdateien und Transparenz über technische Fehlstarts unter [Studienbelege](../experiments/analysis/a2_anchor_20261104/README.md).
- **Abgabe:** beide V14-Dateien SHA256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`, bestehende ZIP `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`. Kein ZIP-Neubau oder Moodle-Upload. Neue vier Modellkopien ausschließlich unter `experiments/candidates/a2_anchor_20261104/`; Replay-Puffer lokal im Studienworktree erhalten. Fünf fremde unversionierte Dateien erhalten.
- **Übergabe:** für die Abgabe V14 behalten. Später gezielt Punktehalten, Energie und Lernen aus tatsächlich ausgeführten Aktionen untersuchen; das sind offene Vorschläge. **Abschlussreview bestanden und veröffentlicht:** alle acht Plan-/Werkzeug-/Daten-/Dokumentationscommits bis `d2780ac` auf GitHub `main`; primärer lokaler Checkout identisch. 300 ursprüngliche Daten-/Modelldateien im committed Git-Baum bytegleich geprüft. Alle 19 eigenen Jobgruppen und der Controller beendet; eigener Wachhalteprozess beendet, beide Automationen bleiben pausiert. Konto zuletzt 35 % verbraucht (65 % verbleibend), kein Reset. [Verifizierter Publikationsabschluss](../experiments/analysis/a2_anchor_20261104/operations/published.json); dessen Dokumentationscommit folgt auf den dort bestätigten Upload. Keine bereits abgeschlossenen Läufe erneut starten.

## 04.11.2026, 17:35 Berlin – Codex: Aktionsschüler vollständig geprüft, V14 bleibt

- **Ergebnis:** A2 (ein Netz) gewinnt auf denselben frischen Karten gegen Solution 38/40 statt Ausgangsnetz S30 16/40; V14 ebenfalls 38/40. Panel A2 94/120 statt V14 98/120, Δ −3,33 pp [−10,83; +4,17]; direkt gegen V14 14/40 [15; 55 %]. Fortschritt gegenüber S30, kein nachgewiesener V14-Ersatz. [Bericht](AKTIONSSCHUELER_20261104.md).
- **Umgesetzt und ausgeführt:** echte aktuelle Merkmale/Masken/finale Aktionen sammeln, aktionsbezogene Destillation plus Wertkalibrierung, zwei Sammel-/Lernrunden, anschließend vier gepaarte RL-Arme mit Seeds 27/28 und nur `w_sap_hit=0.3` gegenüber `0` als Unterschied innerhalb eines Paares. Je Arm 40 Vorlauf + 160 Lernspiele + 32 bekannte Validierung, 24.000 Updates. Zwei vor Ergebnissen festgelegte Zweierensembles. Keine neuen Spielregeln und kein Default-Patch am Agenten.
- **Reward-/Ensemble-Befund:** SAP0-Panelunterschiede −2,50 pp [−11,67; +6,67] und −1,67 pp [−12,50; +10,83], kein gesicherter Vorteil. Alle vier RL-Endnetze und beide Ensembles im beobachteten Panel unter A2; keine nachträgliche Mischungsauswahl. Das beweist keine grundsätzliche Grenze von Einzelnetzen, RL oder Ensembles.
- **Prüfung:** 136 gezielte Tests bestanden. Unabhängige Prüfung aller 425.102 Sammelzeilen, beider Fits und vier echten RL-Endstände. Alle 1.400 Diagnosepartien vollständig/eindeutig, 303 Schritte/v2; separate Gegenprüfung von 288 Zahlen/Intervallen bestanden. 91 Quellen und 33 Eingaben unverändert, null abgefangene Fehler, alle 17 Jobs Exit 0. Quellstand `96b524b`; ursprüngliche erste Sammlung unter `280a297`.
- **Gesamtumfang:** 2.452 Ausführungen = 4 technische + 120 Sammlung + 928 RL/Vorlauf/Validierung + 1.400 Diagnose; 18.340 neue überwachte Updates und 96.000 RL-Updates. 20 neue Panelkarten 866000–866019 und 20 getrennte Direktkarten 866100–866119; zwei Trainingsstarts, explorative Intervalle, keine Bestätigungsfreigabe.
- **Übergabe:** [Datensätze, Rohdaten und unabhängige Prüfungen](../experiments/analysis/action_student_20261104/README.md), acht bytegleiche experimentelle Modellkopien unter `experiments/candidates/action_student_20261104/`. Originale Replay-Puffer und frühere unversionierte Versuche bleiben lokal im Studienworktree. Drei neue/erweiterte Werkzeuge sind dokumentiert; alte seedlose RL-Manifeste bewusst nicht umschreiben.
- **Abgabe geschützt:** beide V14-Dateien weiterhin SHA256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; ZIP `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`. Kein Gewichtswechsel, ZIP-Neubau oder Moodle-Upload. Modelljobs seit 17:33:47 Berlin abgeschlossen; keine neuen Experimente. Finaler unabhängiger Review bestanden. Daten und experimentelle Modelle unter `b97682e` committed; alle 236 ursprünglichen Archiv-/Kandidatendateien im Git-Index bytegleich geprüft, Commit-Baum identisch. **Veröffentlicht:** alle sieben Plan-/Werkzeug-/Daten-/Dokumentationscommits bis `85ecda0` auf GitHub `main`, primärer lokaler Checkout identisch. Neue fremde Remote-Commits gab es beim sicheren Abgleich nicht. Alle eigenen Modell-, Überwachungs- und Wachhalteprozesse bestätigt beendet; beide Sherlock-Automationen bleiben pausiert. Fünf fremde unversionierte Dateien bytegleich erhalten; Studienworktree wegen einzigartiger Replay-Puffer behalten. [Abschlussnachweis](../experiments/analysis/action_student_20261104/operations/closed.json); dessen Dokumentationscommit folgt auf den dort verifizierten Upload.

## 04.11.2026 – Codex: Einzelnetz und Reward-Abtrag geprüft, V14 bleibt

- **Ergebnis:** Auf 20 neuen Karten/600 Diagnosepartien gewinnt V14 gegen Solution 36/40, S3 0/40, S30 18/40, CONTROL30 16/40 und SAP0_30 22/40. Keine Übernahme, keine Bestätigung oder nachträgliche Kandidatenwahl. Die alte Netzanzahl-/FO42-Studie bleibt getrennt. [Vollständiger Bericht](SCHUELERNETZ_REWARD_20261104.md).
- **Tatsächlich gelernt:** ein 512-breites Einzelnetz mit 3 sowie einem vor Spielresultaten zusätzlich festgelegten 30-Epochen-Lauf; 1.407/14.070 überwachte Updates. Danach zwei identische S30-Starts mit/ohne geschätzten SAP-Shapingterm, je 40 Vorlauf + 160 Lernspiele + 32 bekannte Validierung, jeweils 24.000 RL-Updates. Zusammen 1.064 neue Spielausführungen, zusätzlich historische Zustandsdaten, keine fehlenden Spiele.
- **Reward-Befund:** SAP0 im Panel +6,67 pp gegenüber Kontrolle, 95-%-Intervall [−0,83; +14,17], also ungesichert; gegenüber V14 −27,50 pp [−35,00; −18,33]. Nur ein Trainingsstart, 20 Testkarten, mehrere explorative Vergleiche. Keine Übertragung der SAP-Änderung auf V14.
- **Prüfungen:** 50 gezielte Tests gemeinsam bestanden; S3/S30 unabhängig über sämtliche 600.000 historischen Zeilen geprüft; beide RL-Arme 94/94 Nachweisprüfungen; alle 600 Diagnosezeilen eindeutig, 303 Schritte/v2, unveränderte Quellen/Modelle. Separates Berichtswerkzeug stimmt bei allen 54 Ergebnis-/Intervallwerten überein. Eine Veröffentlichungsreihenfolge im neuen Werkzeug wurde nach Abschluss der eingefrorenen Trainings korrigiert und mit Regression geprüft; ursprüngliche Daten erhalten.
- **Dateien für Mahmoud:** neue Werkzeuge `scripts/student_distill.py`, `scripts/student_reward_train.py`; vier ausdrücklich experimentelle Checkpoints unter `experiments/candidates/student_reward_20261104/`; [vollständige Belege](../experiments/analysis/student_reward_20261104/README.md). Alte Replaydaten und neue Lernpuffer liegen lokal in der Studienarbeitskopie, nicht automatisch in Git.
- **Abgabe:** beide V14-Dateien weiterhin SHA256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; vorhandene ZIP `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`. Kein Agenten- oder Default-Config-Patch, kein Moodle-Upload. Quellstände: S3 `221ccf4`, S30 `9d0120d`, RL `5b9f883`, Diagnose/veröffentlichtes Werkzeug `cdb6e85`. Betriebsabschluss separat unter `experiments/analysis/student_reward_20261104/operations_closed.json`.
- **Veröffentlichung und Abschluss:** Geprüfte Werkzeuge, Daten und Dokumentation bis `a4addad` auf GitHub `main`; primäre lokale Arbeitskopie auf demselben Stand, geschützte Gewichte/ZIP erneut bytegleich geprüft. Eigene Trainings-, Auswertungs-, Überwachungs- und Wachhalteprozesse beendet, beide Sherlock-Automationen pausiert. Studienarbeitskopie für lokale Replay-Puffer behalten; fremde ungesicherte Dateien erhalten. Abschlussbeleg wird separat versioniert.
- **Nächster sinnvoller Schritt nach der Abgabe:** Schülerdaten mit Aktionsmasken und aktionsbezogene Lernziele prüfen; SAP-Hypothese allenfalls in mehreren Trainingsstarts weiterverfolgen. Diese Vorschläge sind nicht bereits implementiert und keine Aufforderung, erledigte Läufe erneut zu starten.

## 04.11.2026 – Codex: Einzelnetz-/42-Netz-Bestätigung abgeschlossen, V14 bleibt

- Einzige Bestätigung um **11:13:00 Berlin** vollständig beendet: 3.840 Spiele, alle fünf Aufgaben Exit 0. Unabhängiger Auditor und zusätzlicher Abschlussabgleich bestätigen sämtliche Schlüssel, 303 Schritte/Punktezählung v2, Ergebniszahlen, Intervalle, Quellen und Gewichte. **Datenintegrität bestanden; Leistungsfreigabe nicht bestanden.** [Abschlussbericht](ABSCHLUSSBERICHT_20261104_NETZE.md), [Rohdaten und Abnahme](../experiments/analysis/network_breadth_20261104/confirmation/README.md).
- **FO42 verfehlt drei von sieben Gates:** Panel Δ +0,104 pp [−3,646; +3,750] mit 773/960 statt V14 772/960; gegen Solution 771/800 statt 762/800, Δ +1,125 pp [−0,375; +2,750]; direkt 180/320 = 56,25 % [48,75; 63,75]. default beide 160/160. Panel-Mindestgewinn, untere Panelgrenze und untere Direktduellgrenze verfehlt. Numerischer Solution-Vorteil genügt nicht; keine zweite Bestätigung, kein Nachrücken, keine Übernahme.
- Neue Studie insgesamt **4.804 Ausführungen = 44 bekannte technische + 920 Auswahl + 3.840 Bestätigung**, auf 580 frischen unterschiedlichen Karten und zwei bekannten technischen Karten. Bestätigung mit 80 Panel/default-, 400 Solution- und 160 separaten Direktkarten; zusätzliche Solution-Karten nur in der Solution-Analyse. Quellenstand `bed06df`, derselbe Freeze über beide Leistungsphasen. Der kleinere Umfang wurde vor frischen Ergebnissen festgelegt.
- SOLO28 bleibt ein schwacher geprüfter Einzelnetz-Kandidat, keine Aussage über alle möglichen Einzelnetze. **Null neu trainierte Netze in dieser Studie**; zwei tatsächliche Lernarme mit je 1.200 Spielen gehören zum vorherigen Programm. Die vorgeschlagene [Einzelnetz-Destillation](../experiments/analysis/network_breadth_20261104/confirmation_review/single_distillation_feasibility.md) wurde nicht implementiert oder gestartet: Vollständiger frischer Vergleich plus Training und Abnahme passt nicht mehr in das heutige Zeitfenster mit Abschlussreserve.
- Aktive V14-Rohgewichte in beiden Arbeitskopien und bestehende ZIP bytegleich; [Abschlussnachweis](../experiments/analysis/network_breadth_20261104/confirmation_review/final_root_checks.json). Heute nur Hash-/Inhaltskontrolle des früher unter Python 3.13/3.10 geprüften Pakets, kein FO42-Bau und keine neue Laufzeitprüfung. Vorhandene historische Einträge und fremde Dateien erhalten.
- [Betriebsabschluss um 11:22 Uhr Berlin](../experiments/analysis/network_breadth_20261104/confirmation_review/closure_checks.json): alle fünf erfassten eigenen Prozesse beendet, beide Automationen pausiert, Experiment-HEAD `bed06df` unverändert. Frischer Remote-Abgleich vor Abschlusscommit ohne fremde neue Commits (`origin/main` zu diesem Zeitpunkt `17c1c65`). Kontingent nach natürlicher Erneuerung 2 % verbraucht, kein Reset genutzt; Akku 35 %, kein Netzstrom. Keine weiteren Leistungsversuche oder Moodle-Übertragung ausgeführt.

## 04.11.2026, 09:00 Berlin – Codex: FO42 in die einzige Bestätigung übernommen

- Alle 920 Auswahlspiele vollständig beendet (08:22:38–08:54:56), fünf Jobs mit Exit 0. Die unabhängige Auswertung bestätigt Rohdaten, Schlüssel, 303 Schritte/Punktezählung v2, Quellen, Gewichte und alle Statistikwerte. [Archiv und Einordnung](../experiments/analysis/network_breadth_20261104/selection/README.md).
- SOLO28 scheitert: Panel 137/240 statt 190/240, Solution 31/40 statt 35/40, direkt 16/40. FO42 besteht die vier Auswahlbedingungen: Panel 193/240 (+1,25 pp, Intervall −5,42 bis +7,51), Solution 39/40, default 40/40, direkt 20/40. Nur 20 unabhängige Karten; noch kein gesicherter Vorteil und keine Gewichtsfreigabe.
- Vor Bestätigung erneut alle sieben lokalen Arbeitskopien geprüft: 10.377 Dateien, sämtliche ursprünglichen Dateien bytegleich, neue tatsächliche Daten ausschließlich die 920 Auswahl- und 44 Pilotspiele. Kein beobachteter Verbrauch der zurückgehaltenen Bestätigungskarten; ursprüngliche Grenzen bei seedlosen und externen Versuchen gelten weiter.
- Die einzige FO42-Bestätigung läuft seit 09:00:13 im Worktree `sherlock-november-followup`, HEAD `bed06df`, Freeze `c01a9f05…32e13`, Eigentümer 93363, anfängliche Prozessgruppe 93389. Zustand: `experiments/analysis/network_breadth_20261104/confirmation/state.json`. Genau 3.840 Spiele: 80 Panel/default-Karten, insgesamt 400 Solution-Karten, 160 separate Direktkarten. Zwei Rechenworker; frisches Startkontingent 61 % verbraucht. Quellen und Gewichte bleiben unverändert; unabhängiger Startreview bestanden.
- Dieser Commit archiviert nur abgeschlossene Auswahl und Startnachweise im primären Checkout. Kein Aktualisieren des eingefrorenen Experiment-HEAD, kein Nachrücken von SOLO28, keine neue Abgabe. Aktive V14-Dateien und vorhandene ZIP unverändert. Ein neu trainiertes kompaktes Netz wäre ein gesondertes Projekt: Replay-Merkmale sind vorhanden, ein geprüftes Verfahren zur Verdichtung des Ensembles fehlt; in dieser Studie wurde nicht neu trainiert.

## 04.11.2026, 08:18 Berlin – Codex: technischer Pilot bestanden, Zeitumfang vor Ergebnissen korrigiert

- SOLO28 und FO42 tatsächlich gebaut und unabhängig durch exakten Vergleich aller Tensoren in ihrer Reihenfolge geprüft: ein Netz beziehungsweise 42 unterschiedliche Netze, identische rohe V14-Konfiguration. Kein neues Training und kein Stärkegewinn damit behauptet. Vier aktive Gewichtsdateien in beiden Arbeitskopien und die bestehende ZIP bytegleich.
- Einmaliger Pilot mit 44 bekannten Spielen auf 500720/500721 vollständig, Exit0, Quellen und Gewichte vor/nach identisch. Die maximale Direkt-Wandzeit von4,50655s/Spiel erhöht beide Zeitklassen konservativ. Der ursprüngliche 5.720-Spiele-Umfang ist nicht zugelassen: prognostiziertes Ende inklusive Reserven15:10 statt spätestens14:30Berlin. Noch keine frischen Spiele/Ergebnisauswahl gestartet.
- [Vorabplan](superpowers/plans/2026-11-04-network-breadth.md) deshalb vor Ergebnissen geändert: unveränderte920 Auswahlspiele; gegebenenfalls3.840 Bestätigungsspiele mit80 Panel/default-Karten,400 Solution-Karten und160 Direktkarten. Original3598bb8 und Zulassungsfehler bleiben erhalten. Alle sieben Gates und Sicherheitsreserven unverändert; breitere Panelunsicherheit ausdrücklich dokumentieren. Aktualisierte Schedule-Tests und unabhängiger Auswerter müssen vor Start bestehen. Keine Wiederholung des Piloten zur Verbesserung der Zeitmessung.

## 04.11.2026 – Codex: erneuter Auftrag bis 16 Uhr, neue Einzelnetz-/42-Netz-Studie

- Moayed beauftragt nach dem abgeschlossenen Morgenlauf ausdrücklich weitere Versuche bis 16 Uhr, auch ein starkes Einzelnetz und größere Ensembles. [Neuer Vorabplan](superpowers/plans/2026-11-04-network-breadth.md): genau SOLO28 (V14-Mitglied28, historische Validierung16/16 gegen Solution) und FO42 (V14 + sechs weitere FO-Netze). Eine reine Wiederholung von FT3 würde Netze duplizieren; die gewählte FO-Ergänzung enthält tatsächlich sechs andere Tensorzustände. Vollständige FT5/FTRL/League-Familien sind lokal nicht vorhanden. Historische Validierung ist kein neuer Stärkenbeleg.
- Read-only Inventur und unabhängiger Protokollreview abgeschlossen; keine neuen Spiele gestartet. Vorgesehen sind 44 technische Pilotspiele auf bekannten Karten, 920 neue Auswahlspiele und höchstens eine Bestätigung mit 4.800 Spielen. Vorab feste Karten861/862/863, alle sieben Freigabebedingungen unverändert. Wegen der Zeitgrenze 400 Solution-Karten, aber 120 Panel/default- und160 Direktkarten; breitere Unsicherheit ausdrücklich darstellen. Kein Pooling mit der abgeschlossenen Studie.
- Netzstrom100%, Kontingent zu Beginn52% verbraucht; höchstens zwei schwere Prozesse. Neue Überwachung unter `/tmp/sherlock-breadth-20261104/watch/`, keine alten Prozesse neu gestartet. Vorhandener Worktree `sherlock-november-followup` nach tatsächlichem Ende des alten Source-Freeze auf Branch `improvement/network-breadth-20261104` ab6393859 weiterverwendet. Alte Daten unverändert, alte Quelle7c906e1 weiter im Git verfügbar. Neue Quellen werden vor der Leistungsmessung eingefroren; native Erstellung einer weiteren Arbeitskopie war wegen der App-Unterordnergrenze nicht verfügbar. Primärer Checkout und Abgabe bleiben geschützt.

## 04.11.2026 – Codex: finale Leistungsstudie abgeschlossen, V14 bleibt

- Einzige Bestätigung am 04.11. um **06:29:21 Berlin** vollständig beendet: 12.000 Spiele, alle drei Aufgaben Exit 0, Eigentümer und Kinder beendet. Unveränderter offizieller Auswerter und unabhängiger externer Auditor stimmen über sämtliche Daten, Quellen, Intervalle und sieben Gates überein. [Originaldaten und Review](../experiments/analysis/final_battle_20261103/performance_confirmation/README.md).
- **FT18 nicht zur Übernahme qualifiziert:** Panel Δ −0,9167 pp [−2,8130; +0,9583], Solution 755/800 statt V14 761/800; vier von sieben Hürden verfehlt. Direkter Vorteil 453/800 = 56,625 % [51,75; 61,375] reicht allein nicht. Kein Nachrücken/zweiter Versuch, keine behauptete allgemeine Verschlechterung. FT18 enthält vorhandene Netze 18–35, keine Gewichte des neuen Rettungsnachtrainings.
- Insgesamt 20.800 Leistungsspiele, 2.832 Trainings-/Validierungsausführungen und zwei technische Kontrollspiele abgeschlossen. Die neuen Trainingsendgewichte und alle Kandidaten bleiben Experimente. V14 und bestehende ZIP unverändert; daher keine unnötige neue Verpackung, Modellprüfung oder zusätzliche Spiele. Bestehende konkrete Python-3.10-/Paketprüfung gilt für dieselben per Hash erneut bestätigten Bytes. [Bericht und Abgabeinformationen](MORGENBERICHT_20261104.md).
- Laufquelle bleibt zur Reproduktion im vorhandenen Worktree auf `7c906e1`; Hauptcheckout erhält Abschlussdokumentation und Daten. **Datencommit `9c29b75` auf `main` gepusht**, 28 Originalbelege direkt aus dem committed Git-Archiv bytegleich bestätigt; gemeinsame Dokumentation folgt als eigener Commit. Remote-Abgleich ohne neue fremde Commits. Eigene Remote-/Wachhalteprozesse um 06:35:43 Berlin beendet, beide Automationen pausiert; [Nachweis](../experiments/analysis/final_battle_20261103/closure/runtime.json). Keine abgeschlossenen Experimente erneut starten. Für die Präsentation den beibehaltenen V14 mit 36 Netzen erklären; die vorbereiteten Quellen für den Entscheidungsablauf sind verlinkt. Kein Moodle-Upload ausgeführt, fremde Dateien erhalten.

## 03.11.2026 – Codex: begrenzte Nachanalyse des Rettungstrainings

- [Diagnose für Mahmoud](RESCUE_NACHTRAINING_DIAGNOSE_20261103.md) nur aus abgeschlossenen Trainings-/Auswahldaten und statischem Code; keine Modelle/Spiele/Tests gestartet und keine Bestätigungsdaten gelesen. Root hat zentrale Verlust-, Aktionszähler- und Validierungswerte unabhängig nachgerechnet.
- Kein konkreter Fehlstart, numerischer Zusammenbruch oder Konfigurationsfehler gefunden. Rettungshelfer änderten im Lernteil 2.001-mal eine Zwischenaktion in 66/1.200 Spielen; das sind rund 0,04655 % bezogen auf den internen Entscheidungszähler. Kleine bekannte Einzelnetz-Validierung begünstigt R, der frische Ensemble-Screen dagegen C. Diese Belege erklären die Ursache noch nicht.
- Q-Abstände/Ensemble-Beiträge wurden nicht gemessen; eine unpassende Q-Skalierung bleibt eine Hypothese. Die Notiz trennt Messungen, verbleibende Trainings-/Inferenzunterschiede und zwei spätere Prüfungen. Keine nachträgliche Kandidatenänderung, kein Nachrücken und kein neuer Leistungsversuch. FT18-Bestätigung läuft unverändert; V14 bleibt aktuelle Abgabe.

## 03.11.2026 – Codex: Originalprüfsummen im Git-Archiv abgesichert

- Die FT18-Bestätigung läuft unverändert weiter. Nach dem Upload der Auswahl unter `6c4f953` wurde beim Vergleich der tatsächlichen Git-Dateiinhalte eine automatische CRLF→LF-Umwandlung bei allen 13 CSVs festgestellt (`core.autocrlf=input`). Zahlen und Auswertung waren unverändert, die ursprünglichen Datei-Prüfsummen ließen sich im heruntergeladenen Archiv dadurch jedoch nicht direkt bestätigen.
- Eng begrenzte `.gitattributes` nur für CSVs der aktuellen Studie ergänzt und die originalen CSV-Bytes erneut versioniert. Zunächst alle 49 ursprünglichen Nachweisdateien direkt aus dem Git-Index gegen ihre Original-Manifeste geprüft: bytegleich, alle SHA-256 stimmen. Nach Aufnahme der Fehlernachweise bestätigte ein unabhängiger Review alle 51 Dateien; dessen eigener Bericht ist zusätzlich archiviert. Globale Git-Einstellungen, historische Daten und eingefrorene laufende Studienkopie nicht geändert.

## 03.11.2026, 23:36 Berlin – Codex: FT18 ausgewählt, einzige frische Bestätigung gestartet

- [Vollständige Auswahl](../experiments/analysis/final_battle_20261103/performance_selection/README.md): **8.800 Spiele**, alle 13 Aufgaben Exit 0, Quelle/Eingaben unverändert. Unabhängiger vollständiger Abgleich aller Schlüssel, Werte, Bootstrapintervalle, Gates und Nominierung bestanden. Eine fehlende Gegnerbezeichnung im externen Prüfer wurde korrigiert; alte Fehlerausgabe erhalten, keine Änderung an Studie, Statistik oder Grenzen. Korrigierter Prüfer: 20 kleine synthetische Prüfungen grün.
- **FT18 nominiert:** nur die bereits nachtrainierten Netze 18–35 aus V14, keine heute neu trainierten Netze. Panel 81,67 statt 80,73 % (**+0,94 pp [−3,23; +4,90]**), Solution 152/160 statt 150/160, default 160/160, direkt 98/160 = 61,25 %. Alle Auswahlgates erfüllt; Panelintervall enthält null, somit noch kein bestätigter Stärkegewinn. Z36 ebenfalls zugelassen, nach fester Panelrangfolge hinter FT18. PAIR18/PAIR24/C36/R36 nicht zugelassen; R36 −2,71 pp im Panel und 143/160 gegen Solution. Keine allgemeine Aussage gegen jede Form von Rettungsnachtraining aus diesem einzelnen gepaarten Start.
- Die einzige **12.000-Spiele-Bestätigung läuft seit 23:36:00 Berlin**: V14/FT18 je 5.600 Spiele auf 852000–852399, zusätzlich 800 direkt auf separaten 853000–853399. Wiederholte lokale Seedprüfung aller sieben Worktrees ohne Verbrauchskonflikt; zwei Worker, Netzstrom 100 %, Kontingent 42 % verbraucht. [Startnachweise](../experiments/analysis/final_battle_20261103/confirmation_start/README.md).
- Eigentümer 70650, Status im eingefrorenen Worktree unter `experiments/analysis/final_battle_20261103/performance/confirmation/state.json`; HEAD weiter `7c906e1`, derselbe Freeze wie in der Auswahl. **Nicht doppelt starten, Quellen/HEAD/Gewichte nicht ändern.** Keine Zwischenquoten zur Entscheidung; nach Abschluss alle sieben Gates und technische Abnahme. Keine zweite Bestätigung mit Z36 oder anderer Variante bei Fehlschlag.
- Aktive V14-Dateien und bisherige ZIP weiter unverändert. Vollständige Auswahlrohdaten, beide Prüferfassungen und Herkunftsnachweise für Mahmoud bytegleich archiviert. Dieser Commit ändert ausschließlich den separaten Hauptcheckout.

## 03.11.2026, 18:18 Berlin – Codex: vollständiger Kandidatenvergleich gestartet

- Alle sechs Kandidaten nach vollständigem Training tatsächlich zugelassen: 14.812 unabhängige Prüfungen bestanden, geordnete Tensoren und Konfigurationen exakt, Endnetze korrekt an Index 18 ersetzt. [Kandidaten- und Startnachweise](../experiments/analysis/final_battle_20261103/selection_start/README.md).
- Seit 18:18:26 läuft die feste Auswahl mit **8.800 Spielen** auf 80 neuen Karten 851000–851079, jeweils beide Seiten: V14 und sechs Kandidaten gegen das lokale Sechserpanel plus default, zusätzlich sechs Direktblöcke gegen V14. C36 ist nur Kontrolle und kann nicht nominiert werden. Höchstens ein Kandidat erhält danach eine unabhängige Bestätigung mit 12.000 Spielen.
- Startabnahme bestanden: Quelle/Interpreter/Eingaben, 13 Aufgaben, zwei Rechenworker mit je einem Thread, unveränderte aktive Gewichte/ZIP und Gesamtzeitreserve geprüft. Tatsächliche Ergebnisdateien und Gewinnquoten noch nicht ausgewertet. Keine neue Stärke oder Freigabe behauptet.
- Lauf ausschließlich im eingefrorenen Worktree `sherlock-november-followup`, HEAD `7c906e1`; Eigentümer 59605, Status `experiments/analysis/final_battle_20261103/performance/selection/state.json`. Quelle und Eingaben bleiben auch zwischen Auswahl und Bestätigung unverändert. Kein zweiter Start. Primärer Hauptcheckout erhält nur diese Dokumentation; GitHub-/Kontingentwächter bleiben aktiv.

## 03.11.2026, 18:13 Berlin – Codex: festes Nachtraining vollständig und unabhängig akzeptiert

- Beide echten Läufe erfolgreich beendet, Exit 0, keine aktiven Trainingskinder. Dauer rund 74 Minuten 51 Sekunden. Je Arm **120 Vorlaufspiele, 1.200 Lernspiele, 96 bekannte Validierungsspiele, 180.000 Lernupdates und 459.960 kumulierte Umgebungsschritte**. Insgesamt 2.832 Trainings-/Validierungsausführungen plus die zwei vorangegangenen technischen Spiele; keine entsprechende Anzahl unabhängiger Testkarten.
- [Unabhängige Enddaten-Abnahme](../experiments/analysis/final_battle_20261103/completed_training/training_final_review.md) bestanden: tatsächliche Rohfolgen, endgültige Aktionen im Replay, gespeicherte und neu geladene Gewichte, Adam-Zustände, Rollen und unveränderte Quellen/Eingaben bestätigt. Beide Endnetze sind endlich und unterscheiden sich von der Quelle und voneinander. Kontrolle ohne Rettungseingriffe; Behandlungsarm in der Lernphase mit 15.737 rettungsberechtigten Einheitenschritten und 2.001 Änderungen durch Rettungshelfer. Letzteres sind Zwischenkorrekturen; nachfolgende Regeln können die Aktion weiter ändern.
- Alle drei bekannten Zwischenvalidierungen ließen den Lernzustand unverändert. Verwendet werden die festen Endstände, keine Auswahl des besten Zwischencheckpoints. Dieser einzelne gepaarte Start belegt eine korrekte Durchführung, noch keine allgemeine Überlegenheit der Methode oder bessere Gewinnrate des Ensembles.
- [Archiv mit Endgewichten und Nachweisen](../experiments/analysis/final_battle_20261103/completed_training/README.md) für Mahmoud: 34 Originaldateien, rund 11 MB komprimiert, jeder Inhalt nach dem Verpacken bytegleich gegengeprüft. Replay-Puffer und nicht ausgewählte Zwischengewichte bleiben lokal erhalten. Aktive V14-Dateien und bisherige ZIP bleiben unverändert.
- Die sechs festgelegten Kandidaten wurden gebaut: PAIR18, PAIR24, FT18, Z36, C36 und R36. Tatsächliche Kandidatenabnahme und anschließender vollständiger Leistungsblock sind der nächste Schritt. Kein Gewinner ausgewählt, keine neuen Leistungskarten benutzt und keine Freigabe zum Austausch der Abgabe. Performance-Quelle bleibt der geprüfte Commit `7c906e1`; dieser Übergabecommit ändert nur den separaten Hauptcheckout.

## 03.11.2026, 16:57 Berlin – Codex: beide echten Rettungs-Trainingsläufe gestartet

- Der vollständige Vorbereitungsstand wurde in getrennten Commits auf `main` übertragen: `7eb105c` Dokumentation/Plan, `f2688ea` Testisolation, `2050645` gepaartes Rettungstraining, `7c906e1` feste Kandidaten und Leistungsstudie. Lokaler Hauptcheckout aktualisiert; fremde unversionierte Dateien erhalten. Beide aktiven V14-Dateien und bisherige ZIP bytegleich.
- Zwei technische Spiele auf der schon bekannten Karte 500720 (beide Seiten) bestanden: jeweils 303 echte Aktions-/Update-Aufrufe, endgültige Aktionen korrekt im Replay, keine Lernupdates und keine geänderten Gewichte. Sie sind keine Stärkeauswertung und prüften selbst keinen aktiven Rettungseingriff. [Startbelege und unabhängige Abnahme](../experiments/analysis/final_battle_20261103/training_start/training_start_review.md).
- Das feste Paar läuft seit 16:57:39 im getrennten Worktree `sherlock-november-followup`, Source-Freeze **7c906e16943ff7217afe1eae392834439cc76634**. Eigentümerprozess 55001, Kinder 55028/55033; aktueller Zustand dort unter `experiments/analysis/final_battle_20261103/training/state.json`. Keine zweite Ausführung starten. Schon in der echten Prefill-Phase wurden Rettungseingriffe nur im Behandlungsarm nachgewiesen. Beide haben danach die 120 Vorlaufspiele und erste 32 bekannte Validierungen abgeschlossen und führen echte Lernupdates aus. Endstände und Leistungsvergleiche sind noch offen.
- Unabhängiger Startreview bestätigt gleiche Anfangsnetze/Adam/RNG, genau einen Konfigurationsunterschied, unveränderte Quellen/Eingaben, zwei Rechenprozesse mit je einem Thread und ausreichende Gesamtzeitreserve. Startkontingent 33 % verbraucht; Akkuwächter aktiv, Moayed kündigt rechtzeitigen Netzanschluss an. GitHub-Beobachter läuft; neue fremde Commits werden separat geprüft.
- **Dieser Dokumentationscommit wird ausschließlich im Hauptcheckout erstellt.** HEAD, Quellcode, Plan und Interpreter des laufenden Trainings bleiben eingefroren. Keine Übernahme neuer Gewichte, kein abgeschlossener Trainingserfolg und keine bessere Gewinnrate mit diesem Startbericht behauptet.

## 03.11.2026 – Codex: finaler Vergleich technisch vorbereitet und vollständig geprüft

- Neuer Trainingsschalter `rescue_in_training`, standardmäßig aus: Die bereits vorhandene Kandidatenrettung darf gezielt auch beim Lernen greifen. V14-Inferenz und aktive Gewichte bleiben unverändert. Zwei feste Läufe ab demselben V14-Netz 18, je 120 Prefill-, 1.200 Lern- und 96 bekannte Validierungsspiele; nur der Rettungsschalter unterscheidet die Rollen. Tatsächliche Endgewichte, Lernupdates, unveränderte Validierung und endgültige Aktionen im Replay werden geprüft. Noch kein tatsächlicher Trainingsstart oder Stärkegewinn mit diesem Eintrag behauptet.
- Fester Kandidatenbau: PAIR18, PAIR24, FT18, Z36 sowie nach vollständiger Trainingsabnahme C36/R36. C36 ist nur die Kontrolle. [Plan](superpowers/plans/2026-11-03-final-battle.md), [Prüfbelege](../experiments/analysis/final_battle_20261103/preflight/README.md): vollständige Auswahl mit 8.800 Spielen, bei technischer Nichtzulassung beider Trainingsarme vor Ergebnissen 6.240; höchstens eine Bestätigung mit 12.000 Spielen. Quelle und Eingaben bleiben über beide Phasen identisch. Keine automatische Übernahme und keine weiteren Kandidaten nach einem Fehlschlag.
- Reviews für Laufzeitänderung, Trainingsnachweise, Kandidatenbau und beide Steuerprogramme bestanden. Zwei begrenzte Befunde vor Start behoben: unvollständige Trainingsnachweise konnten akzeptiert werden; ein früher Startabbruch brauchte eine einmalige Reservierung am vorbereiteten Trainingspaar. Kein Leistungsbefund daraus abgeleitet.
- **Gesamte lokale Testsuite tatsächlich bestanden: 1.075 Tests und 126 Untertests, 201,60 s.** Der erste Gesamtlauf hatte 11 Fehler und 1.064 bestandene Tests: ausschließlich weitere prozessglobale Importprüfungen in historischen Archivtests. Diese laufen nun mit demselben Testinhalt in isolierten Unterprozessen. 110 fokussierte Tests und die elf ursprünglichen Fälle mit absichtlich vorab geladenem Torch bestanden ebenfalls; echter verbotener Import wird weiterhin abgewiesen. Historische Auswertungsprogramme, Resultate und Fristen wurden dafür nicht geändert.
- Quellengestützter [Entscheidungsablauf](../experiments/analysis/final_battle_20261103/preflight/decision_flow_sources.md) für spätere Flowcharts und [Abgabeweg](../experiments/analysis/final_battle_20261103/preflight/release_route.md) vorbereitet. Alte P-spezifische Freigabeprogramme passen nicht zu diesen Kandidaten; eine etwaige neue ZIP wird zunächst separat gebaut und geprüft. Finale Folien und tatsächliche Abgabeentscheidung folgen erst nach der Studie.
- Nächster Schritt: geprüften Stand übertragen, zwei echte technische Kontrollspiele auf bereits bekannten Karten, danach das feste Trainingspaar und die vorab festgelegten Vergleiche. Maximal zwei schwere Prozesse; unter 35 % Akku keine neue Phase, bei 25 % eigene Läufe stoppen; Kontingentreserve und Abschluss bis 04.11., 16 Uhr gelten weiter. Hashprüfung bestätigt beide V14-Dateien in beiden Arbeitskopien und die bisherige ZIP unverändert.

## 03.11.2026 – Codex: finaler Verbesserungsdurchlauf bis 04.11., 16 Uhr autorisiert

- Moayed beauftragt erneute eigenständige Verbesserung einschließlich weniger Netze, tatsächlichem Nachtraining, Subagents, Remote-Abgleich und anschließender geprüfter Battle-ZIP. Abgabe laut Screenshot04.11.23:59; Vortrag06.11. zehn Minuten, Fokus eigener Agent/Training/Neues, Spiel/DQN-Grundlagen bekannt voraussetzen. Bestehende30%-Kontingentreserve bleibt.
- [Vorabplan](superpowers/plans/2026-11-03-final-battle.md): feste kompakte18/24-Netz-Kandidaten, zonenweise Rettung, ein gepaartes1200-Spiele-Nachtraining ab V14-Netz18. Rettung wirkt bisher nur in der Inferenz; neuer Default-aus-Trainingsschalter soll genau diesen Unterschied prüfen. Höchstens ein Kandidat aus vollständigem Screen, eine frische Bestätigung, feste Mindestgewinne und unabhängige technische Abnahme. Noch keine neuen Leistungsresultate und noch kein Trainingsstart.
- Eigene Arbeit im vorhandenen Worktree `sherlock-november-followup`, Branch `improvement/final-battle-20261103`; historischeGauß- und03e-Performancezweige erhalten. Maximalzwei Rechenprozesse, Quellenfreeze über gesamte Vergleichsstudie, keine Integration zwischen Auswahl und Bestätigung. Gemeinsame Gegnergewichte lokal vorhanden; aktiveV14-Dateien erneut perHash bestätigt. Remote zuBeginnunverändert06a6b84. Wachhalter/10-Minuten-Fetchwächter angelegt, dreiStunden-Koordination und einmaliger16-Uhr-Abschluss reaktiviert; keine Modellprozesse doppelt gestartet.
- README-Befunde behoben: abgeschlosseneP-Studie, tatsächlich nachgelagerteSAP-Regeln, zweiV14-Ausnahmegates, ehrlicherTeststatus/100%-Grenzen, Servervorbehalte/cloudflared, lokalezweiWorker und konkreteFrist. Importisolationstest in sauberemUnterprozess repariert: ursprünglicherFehler mitGeometrietest reproduziert, danach2Testsgrün; gesamterVertrag7Tests+5Untertestsgrün. UnabhängigerReadinessreviewPASS. Vollsuite folgt nach Fertigstellung der aktuellen Implementierungen, keine behaupteteGesamtabnahme.

## 03.11.2026 – Codex: kritische README-Prüfung, noch keine inhaltliche Überarbeitung

- Auftrag Moayed: prüfen, ob die README aktuell und richtig ist. Remote frisch abgerufen; lokaler `main` und `origin/main` beide `06a6b842863e490241a942f8730a5feb5662e702`. Zwei unabhängige Teilreviews für Fachangaben und Nutzung; Root hat wesentliche Befunde an Quellen und Belegen geprüft. README, Agent, Gewichte, ZIP und historische Ergebnisdateien nicht geändert; dieser Eintrag hält nur den Prüfbefund fest.
- Korrekturbedarf: Kopfzeile beschreibt die abgeschlossene P-Studie noch als auf AC wartend; Abschluss/9.000-Spiele-Ablehnung vom 03.11. fehlt. Aussagen, dass ausschließlich das Netz über SAP bzw. die Aktionsart entscheidet (README Zeilen 196/402), widersprechen aktiven nachgelagerten V14-Regeln. Beim V14-Ausnahmeentscheid fehlen die zwei verfehlten Hürden als solche: nicht nur Panel +1 pp, auch untere Direktduellgrenze >50 %. „100 % sind nicht erreichbar“ ist durch die Versuche nicht bewiesen; korrekt sind bisher nicht erreicht und keine Garantie auf unbekannten Karten.
- Nutzung: öffentliches `sherlock_server --tunnel` wird ohne die zwei noch offenen Ressourcenbefunde empfohlen; zusätzliche Voraussetzung `cloudflared` fehlt in der Installation und ist hier nicht installiert. Bewertungsbeispiel `--workers 8` passt nicht zur lokalen Grenze von zwei Evaluationsprozessen. Uploadfrist präzisieren auf 04.11.2026, 23:59. Aktuelle geprüfte ZIP von historischem Übernahmebericht unterscheiden; datierte Gesamtzahlen sind historische Zählstände, keine neue Gesamtzählung durchgeführt.
- Teststatus: README nennt historische grüne Stände, ohne den im Eintrag vom 02.11. dokumentierten Gesamtsuitenfehler zu erwähnen. Tatsächlich ausgeführt, jeweils `python -B -m pytest -q -p no:cacheprovider`: `test_no_training_model_or_environment_module_was_imported` allein bestanden (1 Test, 8 Untertests); zusammen mit `tests/test_geometry.py::test_spawn_corners_swap` Exit 1 (2 Tests bestanden, 4 Unterfälle fehlgeschlagen, 4 bestanden). Ursache quellenbasiert: Prüfung des globalen `sys.modules` statt isolierter Imports. Keine vollständige Suite, Modelle, Spiele oder Server gestartet; keine Testkorrektur vorgenommen.
- Bestätigt: alle 38 lokalen Markdown-Dateilinks vorhanden, dokumentierte CLI-Schalter und Battle-Klassen-/Gewichtspfade passen. 36 Netze, 79 Merkmale/6 Aktionen und historische V14-Bestätigung 95,4 % Solution /87,6 % Sechserpanel stimmen. Neue lokale Messung 578/600 ist derselbe V14 auf anderen Karten, kein Leistungsfortschritt. Frische Hashprüfung: beide aktiven Dateien weiterhin `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`, bestehende ZIP weiterhin `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`. Fremde unversionierte Dateien erhalten. Nur dieser Dokumentationseintrag neu; kein Commit/Push im Prüfauftrag.

## 03.11.2026 – Codex: Abschluss und zusätzliche V14-Prüfung bestanden

- [Morgenbericht](MORGENBERICHT_20261103.md): Kein nachweislich stärkerer Nachfolger, V14 bleibt. Insgesamt 13.859 ausdrücklich protokollierte Spielausführungen einschließlich Training und wiederverwendeter Technikkarten; keine entsprechende Anzahl unabhängiger Tests. P verfehlt fünf Bestätigungsgates. Keine weitere Variante oder Bestätigung gestartet.
- Die unveränderte Abgabe besteht nun auch die zusätzliche [3.10-Technikprüfung](../experiments/analysis/continuation_20261102/existing_v14_preflight/README.md): acht vollständige Kurs-Runner-Spiele, zwei ZIP-Ablageorte, eingefrorenes `train=True` und ein 303-Schritte-Replay mit null abweichenden Aktionen. Neun neue Vollspiele insgesamt; Replay und API-Smoke erzeugen keine weiteren. Alle 36 Tensorzustände und anderen Checkpointfelder entsprechen V14, nur das Paket ergänzt `frozen=True`. ZIP und beide aktiven Dateien blieben bytegleich.
- Nur das fehlerhafte SciPy-Wheel in der isolierten 3.10-Umgebung wurde ersetzt. Erfolgreiche tatsächliche Ausführung und unabhängiger Review PASS; historische Grenzen der Startnachweise, macOS-Umfang und unbekannte harte Zeitgrenze sind benannt. Keine P-Freigabe oder Windows-Zertifizierung daraus ableiten.
- Primärer Checkout enthält Mahmouds 56bcc55/35a9ebc und unsere Daten/Dokumentation; die historische Performancekopie bleibt absichtlich auf03e. `zone_rescue` aus/unvermessen, Server nicht gestartet, zwei konkrete Ressourcenfehler im Commitreview vermerkt. Ältere Sicherungen, fremde lokale Dateien und die Präsentation wurden erhalten. Eigene Überwachung wird beim finalen Git-Abschluss beendet, beide Nachtaufträge deaktiviert; keine Resets, mindestens30 % Kontingent erhalten.

## 03.11.2026 – Codex: P nicht bestätigt, V14 bleibt; Remote-Stand übernommen

- Die [9.000-Spiele-Bestätigung](../experiments/analysis/continuation_20261102/performance/study_P_only_20261102/README.md) verfehlt fünf von sieben Gates. Panel Δ +0,306 pp [−0,861; +1,472]; Solution P 572/600 gegen V14 578/600; direkt P 309/600 = 51,5 % [48,167; 55,167]; default beide 600/600. Der Auswahlvorteil wurde nicht repliziert. Kein Stärkezuwachs nachgewiesen, keine 100%-Quote und auch keine gesicherte generelle Verschlechterung behauptet.
- Root-Auswertung, unabhängiger Auditor mit 276 Prüfungen und zweiter Datenreview mit eigener CSV-/Bootstrap-Gegenrechnung sowie 237 Dateihashes stimmen überein. Source03e und Mastere173 blieben über beide Phasen gleich. Freeze nach vollständiger Abnahme und Ende der Modelljobs geschlossen; die Performancekopie bleibt zur historischen Reproduktion auf03e. Keine P-Freigabeprüfung oder Übernahme, kein Nachrücken, keine zweite Bestätigung und kein PT2.
- Der Mac schlief am02.11. von22:22:49 bis23:35:47 Berlin mit kurzen Weckphasen. Beim P-Panel beträgt die Kalender-/Monotoniedifferenz4.353,7 Sekunden. Der absolute Abschluss um01:36:40 Berlin lag innerhalb der Frist. Quellen und Rechenzustand blieben erhalten; die Kalenderdifferenz bedeutet keinen entsprechend langsameren Algorithmus.
- Danach origin/main35a9ebc ohne Verlust lokaler Arbeit übernommen. `zone_rescue` bleibt ausgeschaltet und ohne Leistungsmessung. Der [Commitreview](../experiments/analysis/continuation_20261102/performance/study_P_only_20261102/review/MM_commits_20261102_review.md) belegt Entscheidungsäquivalenz bei ausgeschaltetem Flag, auch mit P-Flags. Das ist keine Stärkeabnahme. Server/Tunnel wurden nicht gestartet. Vor öffentlichem Einsatz sind zwei belegte Ressourcenfehler zu beheben: parallele Konstruktionen umgehen das Sitzungslimit; ungeprüfte Env-Dimensionen können große Arrays anlegen.
- Aktive Gewichte weiterhin `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`, bestehende ZIP `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`. Zusätzliche technische 3.10-Prüfung noch in Arbeit: erster Versuch scheiterte vor Spielen am SciPy-Mac-Binärpaket; nur die isolierte Umgebung wurde repariert. Agent und gemeinsames Python3.13 bleiben unverändert. Endgültiger Morgenbericht nach technischer Schlussprüfung.

## 02.11.2026, 22:33 Berlin – Claude Code mit Mahmoud: Fernspiel-Server und `zone_rescue` (Default aus)

- **Fernspiel-Server** (`scripts/sherlock_server.py`, Stellvertreter `scripts/sherlock_remote_stub.py`): Ein externer Agent kann im unveränderten Kurs-Runner gegen Sherlock spielen, ohne Code oder Gewichte zu erhalten. Der Server lädt genau `Gruppe15.zip` in einen temporären Ordner und beantwortet jeden Schritt mit Sherlocks Aktionen; der Gegner bekommt nur `Sherlock_Fernspiel.zip` (Ordner `Sherlock15`: Weiterleitung, Adresse, Schlüssel; nur numpy und Standardbibliothek). Nur JSON, Schlüssel im Header, Größen- und Sitzungsgrenzen (8), Fehler ohne Traceback an den Client; schreibt keine Gewichte. `--tunnel` öffnet eine cloudflared-Adresse und hält den Mac wach. Schlüssel `.fernspiel_token` und Kollegen-Zip sind gitignored. Der Server speichert keine Spielergebnisse.
- **Prüfungen:** 8 neue Tests (`tests/test_sherlock_remote.py`: verlustfreie Übertragung inklusive Datentypen, falscher Schlüssel, zu große Anfrage, Wiederholung nach Netzfehler, verdrängte Sitzung, Zip-Inhalt). Zwei ganze Spiele gegen default, Sherlock einmal als player_0 und einmal als player_1: Aktionen über den Server mit lokalem Sherlock verglichen, 0 von 303 Schritten abweichend. Nachgestellter Fremdrechner mit Kurs-Runner (`run_agents`, train=False und train=True), dazu ein Spiel über die öffentliche Adresse: ohne Fehler, Name im Replay.
- **`zone_rescue`** (config.py/main.py, Default aus, nicht in V14): `cand_rescue` je Relic-Zone. Units mit einem Kandidaten-Ziel in der 5×5-Zone eines seit `rescue_after` Schritten bekannten Relics ohne bewiesenes Punkte-Tile testen gezielt, auch wenn anderswo schon Punkte-Tiles bekannt sind (`cand_rescue` greift nur ohne jedes bekannte Punkte-Tile, im 2./3. Match also kaum). Ein Test. **Noch keine Leistungsmessung.** Arbeitskopie (inklusive Moayeds Default-aus-Schalter) gegen Battle-Zip-Code auf zwei Spielen gegen Solution_92, beide Seiten: 0 von 303 Schritten abweichend.
- **Tests:** `tests/` 846 bestanden. 7 Unterfälle von `tests/test_targeting_adapt_backup_contract.py::test_no_training_model_or_environment_module_was_imported` schlagen nur in der Gesamtsuite fehl, weil frühere Tests torch/agents laden (z. B. `test_geometry.py` davor reicht); einzeln bestanden. Nicht durch diese Änderung verursacht, offen für Moayed.
- Abgabe V14 und beide Gewichte-Dateien unverändert (`98a07350…d3d8`).

## 02.11.2026, 19:30 Berlin – Codex: bedingte Abgabeprüfung offline vorbereitet

- [Eng begrenzte Releasewerkzeuge](../experiments/analysis/continuation_20261102/release_tools/README.md) für den Fall einer vollständig bestandenen P-Bestätigung vorbereitet und unabhängig geprüft. Root: 19 synthetische Installation-/Rollbacktests und16 synthetische Paket-/Tensorprotokolltests bestanden, keine tatsächlichen Modelle oder neuen Spiele darin. Beide Reviews PASS; diese Abnahme ist keine reale Freigabe oder Installation.
- Ein enger Metadatenfehler im Paketprüfer wurde vor echter Modellprüfung behoben: Rohes V14/P speichert `frozen` nicht, der effektive WertFalse stammt aus dem Configstandard; im ZIP muss ausdrücklichTrue stehen. Gegenbeleg und Nachprüfung erhalten, Entscheidungsablauf präzisiert. Aktuelles P und die laufenden Messungen unverändert.
- Getrennte Python3.10.22-Umgebung mit Torch2.2.2/NumPy1.26.4 außerhalb des Repos vorbereitet; bisher nur Paketmetadaten und quellenidentische Kurskonfiguration geprüft, keine Agentenausführung. Gemeinsames3.13 unverändert. Tatsächlicher Kurs-/Paket-/Replaycheck erst nach Ende aller Evaluationsworker und bestandener Bestätigung. Vorbereitung, Warnungen und Herkunft sind dokumentiert.
- Einzige9.000-Spiele-Bestätigung weiterhin auf identischem03e-Source-Freeze; nur Status gelesen, keine laufenden Ergebnisquoten. Primärer main aktuell, Performancekopie bewusst eingefroren. Kontingent22 %verbraucht/78 %frei; V14 und ZIP unverändert.

## 02.11.2026, 19:03 Berlin – Codex: P nominiert, einzige frische Bestätigung gestartet

- Vollständige [P-Auswahl mit 3.000 Spielen](../experiments/analysis/continuation_20261102/performance/study_P_only_20261102/README.md) unabhängig akzeptiert: 137 Prüfungen ohne Abweichung. Sechserpanel 78,33 → 81,00 %, Δ +2,67 pp [+0,42; +5,00]; Solution beide184/200, default beide200/200. P direkt gegen V14 118/200, 59 % [53;65]. Alle vier Auswahlgates erfüllt. Kein behaupteter Solution-Fortschritt und noch keine Übernahmefreigabe; anderes Karten-/Gegnerpanel als Mahmouds historische Liga.
- Einzige Bestätigung seit19:03:10Berlin: 4.200baseline+4.200P auf842000–842299,600direkt auf843000–843299, Gesamt9.000. Tatsächliche Startprüfung unabhängig PASS; AC95 %, Quota20 %verbraucht. Performance-Freeze bleibt03e54e2 und Mastere1731478… über beide Phasen, keine Integration dort. Owner25997, laufende Kinder aus `confirmation/state.json`; keine Doppelstarts. Root liest neue Ergebnisquoten erst nach Gesamtabschluss.
- Rohdaten/Logs/Status/Summary/Auditor und Startprüfung bytegleich archiviert. Die bedingte PT2-Route ist wegenP-Nomination endgültig INELIGIBLE, auch bei späterem Fehlschlag. Kein Backup-Training begonnen, keine Modelle dafür geladen. Vorbereitete externe Dateien bleiben unbenutzt; kein zweiter Bestätigungsversuch zulässig.
- Aktive V14-Gewichte98a07350…d3d8 und ZIP88dfbe32…9dff9d6 weiter unverändert. Nächster Schritt: vollständiger unabhängiger Bestätigungs-/Datencheck; nur bei allen Gates technische Paket-/Kurs-/Reproduktionsprüfung und gesicherte Übernahme.

## 02.11.2026, 18:55 Berlin – Codex: getrennte PT2-Steuerung offline geprüft

- [Controller, Statistik und Anleitung](../experiments/analysis/backup_adaptation_20261102/README.md) für die bereits vor Ergebnislektüre festgelegte bedingte Route vorbereitet. Keine Aktivierung, keine zusätzlichen Spiele oder Modelle. Die laufende P-Auswahl bleibt auf Source03e54e2 unverändert; beide Panelblöcke sind abgeschlossen, das Direktduell läuft noch. Ergebnisquoten werden erst nach vollständigem Phasenabschluss gelesen.
- Root: 26 synthetische Tests bestanden (5,69 s); unabhängiger [Code-/Spec-Review PASS](../experiments/analysis/backup_adaptation_20261102/review/backup_study_final_review.md). Historischer P-Archivnachweis, neue Zweiarm-Abnahme, feste Karten/Gates, übernommene Laufzeitraten, exklusive einmalige Bestätigungsreservierung und Prozessschutz geprüft. Keine tatsächliche Trainings- oder Leistungsabnahme damit behauptet.
- Eintritt weiterhin nur nach vollständiger unabhängig akzeptierter P-Auswahl ohne Nominee, geschlossenem altem Freeze und vollständiger Zeit-/AC-/Quota-/Freshnessprüfung. Bei P-Nomination bleibt dieselbe eingefrorene P-Studie für die Bestätigung maßgeblich; die neue Route wird dann nicht verwendet. Die aktuelle V14-Abgabe und ZIP bleiben bytegleich.

## 02.11.2026 – Codex: separate Forschungsroute nur für eine verworfene P-Auswahl vorbereitet

- Vor Lektüre vollständiger frischer P-Ergebnisse eine begrenzte Folgeroute geplant: [PT2-Plan](superpowers/plans/2026-11-02-conditional-backup-adaptation.md). Nur nach vollständiger unabhängiger ACCEPTED-P-Auswahl **ohne Nominee**, niemals nach begonnener P-Bestätigung oder unvollständiger Auswahl. Genau eine begonnene unabhängige Bestätigung im ganzen Nachtpfad; keine Ergänzung des aktuellen P-Masters.
- Zwei neue adaptierte Starts30/31 aus V14-Komponenten18/19, je120Vorlauf+600Training+96bekannteVal, nur Endstände; keine alten Teilwellengewichte und keine Kontrollen oder Kausalbehauptung. Neue Auswahl50bisher unbenutzte844er-Karten/1.500Spiele, Bestätigung unverändert300+300Karten/9.000Spiele auf842/843, sofern die P-Bestätigung diese niemals benutzt hat. Freshness, AC, Quota und vollständiger Zeitfit inklusive20minSetup/Audit+60minAbschluss bis05:30 bleiben zwingend. Bei bisherigen Floors ab19:15 nur etwa8minZusatzpuffer; keine Startzusage.
- Benannter Backup-Trainingswrapper ist offline vorbereitet: nur Modultext, Protokoll, Variantenname und zwei ARMS-Konstanten geändert, sämtliche18Funktionskörper zur geprüften Vorlage identisch. Sieben reine AST-/NumPy-Tests grün, unabhängiger Review PASS; keine Torch-/Agent-/Env-Imports, keine Spiele oder Trainings. Geerbte Vierarm-Hilfetexte sind als kleiner Dokumentationsrest vermerkt, tatsächliche Zuordnung/Metadaten enthalten nur zwei Arme. Eligibility und tatsächlicher Lade-/Enddatencheck erfolgen außerhalb des Helpers vor einem möglichen Start.
- Getrennte Studienwerkzeuge werden noch ausschließlich in der primären Arbeitskopie geprüft; keine aktuelle Aktivierung. Der laufende Vergleich in der Performancekopie bleibt exakt auf Source03e54e2 und zwei Evaluationsprozessen. Bisher wurden nur Jobstatus und Laufzeiten, keine frischen Ergebnisquoten zur Variantenwahl gelesen.

## 02.11.2026, 17:29 Berlin – Codex: frische P-only-Auswahl läuft, Entscheidungsablauf dokumentiert

- Der Mac meldet seit16:12:57UTC tatsächlich AC und lädt. Nach erneuter Quotenprüfung (17%verbraucht/83%frei), vollständiger Zeitprojektion und unabhängiger Prüfung der tatsächlichen Modelle/Argumente/Quellen wurde die Auswahl am **17:16:14Berlin** gestartet. Zwei schwere Evaluationsworker, keine parallelen Trainings.
- Gemeinsamer Source-Freeze der Performancekopie bleibt **03e54e267242ff642c126313fe5f512ed9d959ac**, Master-SHA `e1731478088ec7bdaa2b63a51a6ae60f0c7ecedc4522fbedfbcfbb0f1517ba03`. Laufbasis: `experiments/analysis/continuation_20261102/performance/study_P_only_20261102/`; Status unter `selection/state.json`, später ggf. `confirmation/state.json`. Genau baseline/P; erster Job misst die Referenz. Noch keine vollständigen frischen Ergebnisse und keine neue Stärkequote.
- Auswahl3.000Spiele auf100Karten, beide Seiten; nur bei vollständiger Datenabnahme und allen Auswahlbedingungen folgt einmalige Bestätigung9.000Spiele auf300Vergleichs- und300getrenntenDirektkarten. **Auch zwischen Auswahl und Bestätigung HEAD/Quellen/Gewichte der Performancekopie nicht ändern**: identischer Master gilt über beide Phasen. Neue Commits dort erst nach Gesamtabschluss bzw. wenn die Auswahl keinen Nominee ergibt übernehmen. Primärer Checkout darf getrennte Dokumentationscommits erhalten.
- Fachliche Dokumentation für Mahmoud: [Entscheidungsablauf V14/P](ENTSCHEIDUNGSABLAUF_V14_P.md), unabhängig quellengeprüft. Enthält Mermaid, Pseudocode,79Features/36×6Q-Werte, heuristische Zielwahl, NN-Maske und sieben nachgelagerte Regelstufen. Präzisiert beide neuen Eingriffspunkte, Fog-SAP-Ausnahme, fehlenden zweitenArgmax nachVeto und verschiedene Lern-/Battle-Gates. Keine Präsentationsdatei geändert.
- Unabhängiger vollständiger Daten-/Statistikauditor außerhalb der eingefrorenen Kopie vorbereitet, tatsächliche CSVs noch nicht gelesen. Sechs zusätzliche synthetische PCG64-/Perzentil-Gegenprüfungen bestanden; keine echten Spiele darin. Eigene Prozesse/Guards und bestehende Sicherheitsautomationen auf den aktuellen Freeze hingewiesen. Abgabe V14 und Sicherungen unverändert.

## 02.11.2026, 17:06 Berlin – Codex: tatsächliche P-Datei technisch zugelassen, Leistungstest wartet auf AC

- Experimentdatei P gebaut: `experiments/ensembles/20261102_targeting_P_only/P.pth` in der Performancekopie, SHA-256 `dbb15222848b9ce8530080e128fa9ca66309c9900e98f50de5cce1d73e5b7f5a`. Sie enthält alle 36 ursprünglichen V14-Netze und nur die neuen Configwerte `point_pair_swap=true`/`art_move_guard=true`. Die teilweise nachtrainierten Netze werden nicht verwendet. P ist kein freigegebener Ersatz der Abgabe.
- Tatsächlicher `Agent_x`-Konstruktor lädt exakt alle 36 geordneten Tensorzustände, 79 Merkmale/6 Aktionen, epsilon0; Lernen und automatisches Speichern aus. Keine Forward-Calls, Lernupdates oder Spiele durch diese Ladeprüfung. Alle geschützten Gewichte unverändert. [Ladebeleg](../experiments/analysis/continuation_20261102/performance/review/P_actual_load_preflight.json).
- Unabhängige zweite Dateiprüfung: 20 Prüfungen ohne Fehler, sämtliche Checkpointinhalte mit V14 identisch außer den zwei Configschaltern, Manifest ohne Trainingsauditbehauptung, Ladebeleg und Schutzdateien stimmen. [Abnahme](../experiments/analysis/continuation_20261102/performance/review/P_candidate_admission_audit.md). Das ist technische Zulassung, kein Stärkenachweis.
- Trainings-Freeze nach Ende des 19er-Startfensters kontrolliert geschlossen; Performancekopie am sicheren Übergang verlustfrei auf main92cc7d9 gebracht. Alte Pilotverzeichnisse und Endstände bleiben erhalten. Noch kein reales841/842/843er-Spiel. Nutzer meldet, sobald das Netzteil angeschlossen ist; längere Auswahl erst bei nachgewiesenem AC und ausreichender Gesamtzeit.
- Nächster gemeinsamer Freeze wird Auswahl und mögliche Bestätigung mit genau baseline/P und festen3.000/9.000Spielen binden. Keine späterePT-Ergänzung, keine Übernahme ohne die festgelegten Gates. Zeitfenster siehe Leistungsprotokoll; P-only-Auswahl initial spätestens19:24Berlin, ggf. früher bei langsamerem Durchsatz.

## 02.11.2026, 16:47 Berlin – Codex: P-only vor frischen Daten fest gewählt

- ZweiteWelle wurde bis zum festenStartlimit15:44:54UTC mangelsAC nicht gestartet. Keine19erRunverzeichnisse/-Trainer. Vierarmpilot daher **unvollständig**, ersteZweiArme unabhängig akzeptiert. Ursprüngliche2hFrist nicht verlängert; Source-Freeze8e4720c bis Abschluss unverändert und allegepinntenQuellen/Gewichte exakt nachgeprüft. [Abschlussbeleg](../experiments/analysis/continuation_20261102/performance/review/training_freeze_close.json).
- Datenblind **P-only** gewählt, bevor ein reales841/842/843er-Spiel stattfand: [fixierteEntscheidung](../experiments/analysis/continuation_20261102/performance/route_decision.json). NurzweiPlanungsflags,36Originalnetze. Weder teilweise trainierteGewichte noch späterePT-Ergänzung. Auswahl3.000Spiele/100Karten, Bestätigungweiter9.000Spiele/300Karten, gleicheGates. NeueLangeJobs bleiben bei29%ohneAC blockiert; vorbereiten/prüfen ist möglich.
- Beide abgeschlossenenTeilwellen-Endstände undRohdaten unter [training/first_wave](../experiments/analysis/continuation_20261102/training/first_wave/README.md) gesichert:1.632tatsächlicheSpiele. JSONLverlustfreimitgzip, jederOriginal-/Archivhash inprovenance.json; Endgewichte bytegleich. ReplayBuffer je187MB und nichtverwendeteZwischenbeste bleiben lokal. DieseEndgewichte sind ausschließlichForschung undkeineAbgabe/Nominees.
- Performancekopie darf nun am sicherenPhasenübergang den aktuellenWerkzeug-/Dokumentationsstand übernehmen; vorbereitete altePilotverzeichnisse erhalten, nicht unter verändertemHEAD fortsetzen. NächsterSchritt: P-Datei ausV14 bilden, tatsächliche36Tensoren/Config/Ladevorgang prüfen, gemeinsamenP-onlyFreeze aufbauen; frische Auswahl erstbeiAC und ausreichenderGesamtzeit starten. Kein stärkererNachfolger behauptet, aktuelleAbgabeV14weiterbytegleich.

## 02.11.2026, 16:41 Berlin – Codex: erste Teilwelle unabhängig akzeptiert, P-only-Fallback vorbereitet

- [Unabhängiger Teilbericht](../experiments/analysis/continuation_20261102/performance/review/first_wave_independent_audit.md): **ACCEPTED_FIRST_WAVE_ONLY**,1.762Prüfungen/0Fehler. Zwei tatsächliche vollständige Arme, je720Rollouts/96Val/600CSV,90.000Updates,278.160Env-Schritte, echteTensor-/Adam-/Reloadbelege und strikteValisolation. Keine Agentenkonstruktion,Forward-Calls,Gradienten oder Spiele durch den Auditor. Das ist keine Vierarm- oder Stärkeabnahme.
- Eine zu strenge Auditannahme wurde vor einem Vierarm-Audit sauber eingegrenzt: Vorladeprüfung benutzteglobalSeed28, echte finetune-Initialisierung planmäßig4228; tatsächliche Partner stimmen überein. BestehenderDefaultAgent setzt zwischenEpisoden globalNumPy zurück. Vergleich kompletter globalerRNG über diese Konstruktion wäre falsch; innerhalb jeder Validierung bleibt exakte eigene/globaleRNG-Erhaltung zwingend und wurde bestanden. Details/Patchhinweis im Teilbericht; alter Vierarm-Audit noch nicht ausgeführt.
- ZweiteWelle noch ohneAC bei30%Akku vorgemerkt, spätester zulässigerStart15:44:54UTC, keineFristverlängerung und keine doppeltenArme. Danach keinPT aus einem unvollständigenPilot. Beide Abgabegewichte unverändert.
- Bereits im Protokoll erlaubten **P-only-Fallback** konkret implementiert und unabhängig geprüft: vor ersten841er-Daten kann Root bei fehlenderPT-Zulassung ausschließlichP fixieren. Auswahl3.000 statt4.600Spiele, dieselben100Karten/Gegner/Gates; Bestätigung unverändert9.000Spiele/300Karten, derselbeFreeze. Kein späteresPT-Hinzufügen. P verwendet alle36Originalnetze, nurzweiConfigflags; keinTrainingaudit behauptet. Die Route ist hiermit noch nicht gewählt.
- 49 fokussierte synthetische Tests nach Übertragung in die primäre Arbeitskopie bestanden, keineSkips (22Driver+16Stats+11Builder). Finaler unabhängigerCode-/Spec-Review PASS. OriginaleTools und deren historischeReviewnachweise erhalten; Source-Freeze der Performancekopie weiter8e4720c, dortkeineHEAD-/Quellenänderung. [Werkzeuge/Review](../experiments/analysis/continuation_20261102/performance/README.md). Kein reales841/842/843er-Spiel, kein neuesStärkeergebnis.

## 02.11.2026, 16:22 Berlin – Codex: erstes Trainingspaar abgeschlossen, feste Leistungsstudie vorbereitet

- Erste Welle `20261102_target_control18`/`20261102_target_adapt18` vollständig: je120Prefill+600Lernspiele+96bekannteValidierungen, zusammen1.632 tatsächliche Spiele. Beide Startnetze exakt V14-Komponente18; am Ende je90.000 reale Lernupdates und278.160Env-Schritte, q verändert, gespeicherter Endstand erfolgreich erneut geladen, keine Counterabweichung. Dies ist noch **kein Stärkenachweis**.
- Äußerer Abschlusscheck fragte ein im erfolgreichen Armrecord fehlendes Summenfeld ab; daher dessen Status `incomplete` mit `KeyError: actual_rollout_games`, obwohl beide Kinder mitExit0 und allen720/96/600Rohzeilen fertig waren. Originalskript/-Receipt unverändert erhalten, Fehler minimal reproduziert. Ein unabhängig geprüfter neuer Übergangs-Guard zählt120+600undRohdaten, wiederholt keinen Arm und bewahrt alteSource-Pins/Originaldeadline16:35UTC.
- Zweites Paar Index19 wartet bei33%Akku auf AC. Geprüfter einmaliger Power-Warter startet ausschließlich den zweiten Guard, falls AC spätestens15:44:54UTC bereitsteht; kein zweiter unabhängiger Trainer. Ohne alle vier vollständigen, unabhängig abgenommenen Arme gibt es **keinPT**. Endgültigen aktuellen Zustand unter `/tmp/sherlock-continue-20261102/` sowie im ignorierten SDD-Journal der Performancekopie lesen.
- Leistungsprotokoll vor sämtlichen neuen841er-Ergebnissen fixiert: [P/PT-Auswahl und Bestätigung](superpowers/plans/2026-11-02-targeting-performance.md), Werkzeuge [performance](../experiments/analysis/continuation_20261102/performance/README.md). MaximalP/PT, genau36Netze, Auswahl4.600Spiele/100Karten, danach maximal ein Nominee und9.000frischeBestätigungsspiele/300Karten, unveränderte strenge Gates, kein Nachrücken. Bisher **kein** reales841/842/843er-Spiel.
- Vorhandener `par_eval` unterstützt default bereits: gemeinsamerSiebenervergleich mitzweiWorkern, Default als separate Kennzahl. Ein unnötiger neuer serieller Adapter wurde vor frischen Daten entfernt. Laufzeitklassen gemeinsamerVergleich2,22/Direkt3,0Wallsekunden proSpiel plus beobachteterglobalerVerlangsamung,20%Reserve+60minSchluss. Keine erneuteDivisiondurch2. Methodik und finalerCode unabhängig abgenommen.
- 40 fokussierte rein synthetische Werkzeugtests nach Übertragung grün, **keineSkips**:19Driver+15Stats+6Builder. Vollständige4.600/9.000-Dateipipelines, Bootstrap/Schwellen, Sperren, eigeneProzesse, Alias-/Receipt-/Sourcebindung; keine echtenModelle/Spiele in diesen40Tests. Übertragungscheck fand zweiTestfixture-Pfade unter `/tmp` vorausgesetzt; Fixture jetzt im echtenSystem-Tempordner, Quellroot aus Umgebung/Arbeitsordner statt persönlichemMac-Pfad. Laufzeitcode bytegleich zum finalen unabhängigen Review.
- Performancekopie bleibt für mögliche zweite Welle auf **8e4720c** eingefroren: dort wederHEAD noch getrackteDateien ändern. Nur primäre Arbeitskopie auf separatem Dokumentations-/Werkzeugzweig ergänzt; deren neue Commits erst nach Ende der Trainingsphase in die Performancekopie übernehmen. Beide aktuellen Abgabe-Dateien, V14-Sicherung und alteSicherung bleiben unverändert. Mindestens30%Kontingent, keinReset; aktuell85%frei. Insgesamt bisher218früheretechnische+1.632Trainings/Vorbereitungs/Val-Spiele=**1.850**abgeschlosseneSpielausführungen dieserFortsetzung.


## 02.11.2026, 15:26 Berlin – Codex: P technisch geprüft, kontrolliertes Nachtraining vorbereitet

- Zwei Default-off-Prototypen in main: `point_pair_swap` tauscht höchstens ein streng besseres Paar eigener bekannter Punktziele vor der Merkmalsbildung; `art_move_guard` verdrängt einen Zug nicht durch schon als überflüssig erkannten Artillerie-Sap. Aktive V14-Config lässt beide aus, alle Gewichte unverändert.
- Code unabhängig geprüft, 792 Tests + 14 Untertests; 24 bekannte technische Spiele unabhängig abgenommen. Zwölf Default-off-Streams bytegleich zu V14, aktive Einzelzähler Artillerie 9 / Zieltausch 28. Das sind Funktionsnachweise, keine Siegverbesserung. [Datenabnahme](../experiments/analysis/continuation_20261102/prototype_technical_audit.md).
- Gaußstudie beendet: 168 Spiele / 84 identische Quellenpaare, 751 Tests + 14 Untertests, 1.318.342 unabhängige Datenprüfungen. Technisch bestanden, praktisch nur zwei positive Weltfelder für einen Schritt in einem Spiel; feste Hürde verfehlt. Bleibt außerhalb von main/Abgabe auf [separatem Branch](https://github.com/elhassanmahmoud/sherlock-luxAI-team15/blob/improvement/gauss-admission-20261102/experiments/analysis/gauss_admission_20261102/RESULTS.md). Keine aktiven Gaußspiele oder Stärkequoten.
- Gewählte nächste Route [P/PT-Anpassungspilot](superpowers/plans/2026-11-02-targeting-adaptation.md): vier feste Arme aus V14-Komponenten18/19, gleiche Trainingskarten/Seiten/Gegner je Paar, alte gegen neue Planung, unveränderter Reward. Je Arm120Prefill+600Training+96bekannteVal, nur Endstand; danach höchstens P und PT (genau zwei von36Netzen ersetzt) als frische Leistungskandidaten. Noch keine neuen841/842/843er-Auswahl-/Bestätigungszahlen.
- Wrapper `scripts/targeting_adapt.py` unabhängig geprüft; 42 fokussierte Tests und gemeinsame Vollsuite 834 Tests + 14 Untertests bestanden. Reale Extraktion/Ladeprüfung und Start folgen; **bei diesem Eintrag noch kein Trainingsspiel dieses Piloten ausgeführt**. Source/HEAD/Protokoll und Eingabegewichte werden für beide Wellen eingefroren; bitte in dieser Zeit keine parallele Integration in die Performancekopie. Remoteabruf läuft weiter, Integration an Phasengrenzen. Mindestens30%Kontingent erhalten, Akku35/25-Grenzen beachten.
- Primärer Checkout nach Ende der Gaußreferenzprüfung verlustfrei aktualisiert; fremde config2/reward2/DS_Store/altesAwakeJSON unverändert. Aktuelle V14-/Baseline-SHA weiter `98a07350…d3d8`; 218 tatsächliche Spielausführungen dieser Fortsetzung bisher, sämtlich technische Diagnose/Shadow/Smoke, noch keine Übernahme.

## 02.11.2026, 14:03 Berlin – Codex: unveränderten V14 passiv diagnostiziert, zwei enge Ansatzpunkte

- Externes Werkzeug `scripts/targeting_probe.py`, 42 fokussierte Tests nach einer Provenienzkorrektur grün; vorheriger gemeinsamer Volltest 728 Tests + 14 Untertests. Unabhängiger Code-/Fixreview sauber. Agentenlogik und Gewichte unverändert.
- 24 finale Nachspiele (12 feste verbrauchte Schlüssel × beobachtet/unbeobachtet) plus zwei frühere Integrationsspiele = **26 tatsächliche Spiele**. Alle zwölf Paare reproduzieren native Aktionshashes beider Teams, Punkte v2/Siege und 303 Schritte sowie die alte Auswahlbasis. Vollständige Quellen-/Gewichts-/Planidentität über den Lauf unverändert; 584.037 unabhängige Rohdatenprüfungen ohne Fehler. [Befund und Grenzen](../experiments/analysis/continuation_20261102/targeting_audit.md).
- **H1:** 16 beobachtete Bewegung→Artillerie→Overkill→STAY-Fälle, davon nur drei verhinderte erste Fortschritte zu bekannten eigenen Punkten (zwei in den alten verlorenen Matches). Eine frühe Ablehnung des bereits als überflüssig erkannten Artillerie-Saps kann die normale Bewegungskette erhalten; noch nicht umgesetzt oder als stärker bestätigt.
- **H2:** 141 erlaubte Zwei-Eigentümer-Tauschgelegenheiten bei exakt denselben eigenen gewählten Punktzielen, 91 Frames/82 Episoden in beiden Gruppen. Kürzere BFS-Summe ist noch kein tatsächlicher Punkte-/Sieggewinn. Pauschale Heimpriorität bleibt unbegründet: potenzielle Versorger unzugewiesener Felder hatten in dieser Diagnose andere eigene Punktziele.
- Nächster Schritt sind default-off Prototypen und frische Vergleiche; keine neue Abgabe. Gauß-Admissionwerkzeug auf getrenntem Branch in Prüfung, noch keine echten Gaußspiele. Primärer Checkout bleibt vorübergehend auf `384dad2` als explizite Referenz für diese technische Prüfung; Remote und Performancezweig dürfen die fertige Diagnosedokumentation schon enthalten. Nach sicherem Übergang lokal aktualisieren.

## 02.11.2026, 13:22 Berlin – Codex mit Moayed: gezielte Fortsetzung bis 03.11., 06:00

- Neuer autonomer Auftrag nach dem abgeschlossenen Nachtbericht. Frischer Remote-Abgleich: main/origin/main `3a7e782`, keine neuen Mahmoud-Commits. V14 und alle Sicherungen unverändert; keine neuen Stärke- oder Trainingsergebnisse.
- [Plan](superpowers/plans/2026-11-02-targeting-continuation.md), [Design](superpowers/specs/2026-11-02-targeting-continuation-design.md), [Trace-Schema](superpowers/plans/2026-11-02-targeting-trace-schema.md). Zuerst unveränderte V14-Entscheidungen beobachten: Zielvergabe, Netz/Masken, Endaktionen und Energie unterscheiden; freie bekannte Felder sind allein kein Fehlernachweis. Pauschale Heimprioritäten/Reserven/Sticky-Ziele wegen früherer negativer Befunde nicht wiederholen.
- Separat prüfbarer Gauß-Prototyp weiterhin außerhalb der Abgabe; echte Agenten-/Shadow-Zulassung noch offen. Training nur mit begründeter Fragestellung, nicht erneut ein beliebiges 37. Netz nach einer gescheiterten Bestätigung nachschieben.
- Reserviert nach Audit: Diagnose 840000–840039, Auswahl 841000–841099, Bestätigung 842000–842299, direkt 843000–843299, Technik 844000–844099. Konkrete Kandidaten/Umfänge werden vor neuen Leistungsresultaten fixiert. Zuerst 12 verbrauchte Verlust-/Kontrollschlüssel, jeweils beobachtet/unbeobachtet (maximal 24 Nachspiele), qualitative Diagnose ohne neue Stärkeaussage. [Audit/Designreview/Schlüssel](../experiments/analysis/continuation_20261102/).
- Eigene isolierte Arbeitskopie `sherlock-v10-mechanics`, Branch `improvement/targeting-20261102`; Remote-Watch ruft nur ab, keine Integration während eingefrorener Studien. Fremde lokale Dateien bleiben erhalten. Maximal zwei schwere Worker, mindestens 30 % Codex-Kontingent erhalten, kein Reset. Nutzer erlaubt ausdrücklich Akkuarbeit und schließt später an: unter 35 % keine neue lange Phase, bei 25 % eigene schwere Jobs sichern/beenden. Schlussreserve vor 06:00; Präsentation unverändert.

## 02.11.2026, 03:56 Berlin – Codex mit Moayed: November-Nacht bestätigt keinen V14-Nachfolger

- **Entscheidung:** V14 `v14_rescue` bleibt unverändert. Beide aktiven Gewichte und die Sicherung `experiments/releases/20261101_v14_baseline/` haben SHA-256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`. Kein Abgabetausch und kein nachrückender Kandidat. [Entscheidung und Intervalle](../experiments/analysis/night_20261101/DECISION.md), [Morgenbericht](MORGENBERICHT_20261102.md).
- **Tatsächliches Training:** je 600 Nachtrainingsspiele + 120 Prefill + 96 bekannte Validierungen in zwei Armen, zusammen 1.632 Spiele; gleicher V14-Start aus Netzindex 18, frischer Optimierer/Buffer, 90.000 Lernupdates je Arm. Einziger Unterschied: Entdeckungsreward 0,5 gegen 2,0. Start-/Endgewichte, reale Configs und Lernfortschritt unabhängig geprüft; kein Training ab Null, keine Wahl eines besten Zwischenstands.
- **Auswahl:** 3.100 vollständige Spiele, 50 neue Karten, einzig `control` nominiert (+4,83 pp im lokalen Panel, Solution 95/100 statt 94/100, direkt 62/100). OVERLAP und DISCOVERY haben die Auswahlbedingungen verfehlt. Der höhere einzelne Solution-Wert von DISCOVERY (96/100) rechtfertigt wegen des schlechteren Panels/Direktduells keine Übernahme.
- **Frische Bestätigung:** 6.000 Spiele; V14 und CONTROL auf 200 Karten gegen sechs Gegner + default, dazu 200 getrennte Direktkarten. Panel Δ −0,167 pp [−2,375; +2,000]; Solution 384/400 statt 382/400, Δ +0,50 pp [−1,25; +2,50]; direkt 201/400 = 50,25 % [43,50; 57,00]; default beide 400/400. Vier festgelegte Gates verfehlt. Der Auswahlvorteil wurde nicht repliziert; auch kein gesicherter Schaden belegt.
- **Methodik:** neues lokales Panel (Solution, Quadrat-Solution, V3, V7, V10, V13), andere Zusammensetzung als Mahmouds historische Liga. Vor Ergebnislektüre aus gemessenen Laufzeiten 200 statt 300 Bestätigungskarten festgelegt; numerische Gates unverändert. Kein nachträglicher Teilmengenbericht. Laufzeitquellen/HEAD `aa06601` und alle Gewichte blieben zwischen Auswahl und Bestätigung gleich; vollständige Schlüssel, 303 Schritte, Punktezählung v2, Hashes und Karten-Bootstraps separat exakt nachgerechnet.
- **Technik/Abgabe:** 694 Tests + 14 Untertests bestanden (119,95 s), acht vollständige Kurs-Runner-Spiele bestanden. Paketfilter lässt nur gültige Python-Modulnamen zu und entfernt dadurch lokale `config 2.py`/`reward 2.py`-Kopien aus dem Paket. Primäre Arbeitskopie ohne Verlust der fremden unversionierten Dateien auf den geprüften Stand gebracht. Neue lokale `Gruppe15.zip`: 22.228.404 Bytes, SHA-256 `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`; beide Ablageorte und eingefrorenes `train=True` geprüft. 36 Netze und sonstige Checkpointinhalte unverändert, nur die verpackte Config setzt `frozen=True`. Interne Repo-Dokumente gehören nicht ins Laufzeitpaket.
- **Getrennter Prototyp:** begrenzte Gauß-Inferenz auf Followup-Branch (`929b11f`), Default aus, 37 reine Tests/Review/Mikrobenchmark; keine tatsächliche Agenten-/Shadow-Abnahme und keine Stärkenzulassung. Nicht in main oder Abgabe übernommen. Nach der gescheiterten Bestätigung kein weiterer Stärkekandidat dieser Nacht.
- **Zusatzdiagnose abgeschlossen:** zwölf Nachspiele auf sechs bereits verbrauchten V14-Solution-Verlustschlüsseln, zwei Werkzeuge nacheinander mit einem Worker. Originalpunktetotale/Matchsiege im CSV und finale Siege im JSON reproduziert; Quellen, Engine und Gewichte unverändert. [Befund und Grenzen](../experiments/analysis/night_20261101/remaining_solution_losses/findings.md): erster Punkt in 10/12 verlorenen Matches nicht später, aber späte Belegung in 12/12 geringer. Bekannte freie Felder ohne Ziel, noch ungeklärte Zonen und Energie-/Halterverluste bleiben konkurrierende Erklärungen. Kein Kausalnachweis, keine neue Regellogik/Gewichtsänderung; fehlende Schritt-/Endpunktefelder im Mechanismusformat werden nicht als überprüft ausgegeben. Insgesamt 10.842 explizit protokollierte Spiele dieser Nacht, einschließlich Training/Prefill/Validierung und technischer Nachspiele. Code/Daten sind mit `c905c63` und `139057f` auf main übertragen; die zusätzliche Diagnose und dieser Abschlussstand werden als Dokumentation ergänzt. Der Gauß-Prototyp bleibt getrennt auf `improvement/november-followup-20261101` bis `307b1ed`, ohne Merge oder Battle-Freigabe. Die Quellenmemo [zur Zielmetrik](../experiments/analysis/night_20261101/targeting_metric_notes.md) präzisiert die nächste Messfrage; frühere pauschale Heimprioritätsversuche nicht blind wiederholen. Eigene Modellläufe und Remote-Watcher beendet, Nachtaufträge deaktiviert. Folien/PDF unverändert; die spätere Vorbereitung soll Zielzuweisung, Netzeingang/-ausgang, Masken und Regelüberschreibungen klar als Ablauf zeigen. Abgabe laut Moodle Mittwoch, 04.11., 23:59; Vortrag Freitag, 06.11., zehn Minuten.

## 01.11.2026, 21:00 Berlin – Codex mit Moayed: neue Verbesserungsnacht bis 02.11., 06:00

- Moayed autorisiert erneute selbstständige Weiterarbeit, tatsächlichen Trainingspilot, Subagents und Remote-Überwachung. Aktueller Ausgang nach Remote-Abgleich **V14** (`93a2ddd`), Gewichte `98a07350…d3d8`; V14-Teamentscheidung bleibt erhalten. Präsentation erst auf späteren Auftrag bearbeiten; Prof-Feedback zur Reihenfolge Zielzuweisung/Netz/Maske/Regelüberschreibung für die spätere Erklärung beachten.
- **Eigene Arbeitskopie:** `sherlock-v10-mechanics`, neuer Branch `improvement/november-battle-20261101`; der alte Ordnername bezeichnet keinen V10-Ausgang. Hauptcheckout auf Mahmouds aktuellem Stand, fremde lokale Duplikate unverändert erhalten. Lokale Gegnersnapshots `league_nets6` und `threat6` fehlen: kein Auswerten mit stillschweigend zufälligem Ersatz.
- [Vorab festgelegter Nachtplan](superpowers/plans/2026-11-01-night-improvement.md), [Design](superpowers/specs/2026-11-01-night-improvement-design.md): sichere Überlappungsschlüsse aus Beobachtungen prüfen; begrenzter kontrollierter Trainingspilot mit Entdeckungsreward 0,5 gegen 2,0. Kein blindes Wiederholen der wirkungslosen Runde 6. **Noch keine neuen Trainings-/Leistungsresultate.**
- Neues lokales Sechserpanel Solution, Quadrat-Solution, V3, V7, V10, V13; ausdrücklich anderes Panel als Mahmouds historische sechs Gegner. Eigene Nachtbestätigung mit **300 statt 800 Karten**, um vollständig in die Frist zu passen; entsprechend geringere statistische Präzision, gleiche Mindestgröße +1 pp, zusätzliche konservative Solution-Bedingung. Keine Ausnahme ohne Nachweis.
- Seedreservierung: Diagnose 830000–830039, Auswahl 831000–831049, Bestätigung 832000–832299, direkt 833000–833299, Technikreserve 834000–834099. Training 294200–294499, Prefill 295000–295059. Audits ohne Überschneidung archiviert unter `experiments/analysis/night_20261101/`; nicht parallel belegen.
- Technischer Ausgang auf Moayeds Rechner: **628 Tests + 14 Untertests bestanden**, 129,51 s, ohne laufende Modelljobs. Netzbetrieb bestätigt. Höchstens zwei Rechenworker, keine Quell-/Gewichtswechsel während Messreihen. Remote-Watch führt nur Fetch aus, Integration an Phasengrenzen. Mindestens 30 % Codex-Kontingent erhalten.
- Abgabe laut Moodle-Screenshot bestätigt: **Mittwoch 04.11., 23:59**, Battle-Präsentation Freitag 06.11., zehn Minuten. `Gruppe15.zip` liegt bisher nur auf Mahmouds Rechner; lokaler sauberer Neubau aus getrenntem Checkout folgt samt Prüfung. Interne Doku bleibt im Repo, gehört nicht ins Laufzeitpaket.

## 01.11.2026, 18:48 Berlin – Claude Code mit Mahmoud: Präsentation 06.11. auf V14 umgestellt

- **Auftrag Mahmoud:** „mach die folien fertig“ und „readme anpassen immer“.
- **Folien** (`Sherlock_Battle_06-11-2026.pdf` im Projektordner, 17 Seiten; Quelle `docs/presentation/Sherlock_Battle_06-11-2026.html`; alle geänderten Seiten als Bild geprüft):
  - Folien 1, 2, 10: 95 % statt 94 %.
  - Folie 3: Schrittzeit „meist 5 ms, höchstens 12 ms“ (Kurs-Runner-Prüfung V14).
  - Folie 10: Diagramm bis V14 (`docs/presentation/source/fortschritt_0611.py`: 46,7 → 78,3 → 83,5 → 90,3 → 94,1 → 94,4 → 95,4 %) und vierte Phase „gezielte Korrekturen“. V13 ohne Balken, weil es nur auf Nebel-Karten gemessen wurde.
  - Folie 11: „Neu seit letzter Woche: V11 bis V14“ als Tabelle mit Solution_92 und Mittel über 6 Gegner, jeweils gegen die Vorgängerversion.
  - Folie 12: vier Erkenntnisse. Neu sind „Fehler suchen bringt mehr als weitertrainieren“ (Runde 6: nichts), „Nur neue Karten zählen“ (Regel +1,8 auf Entwicklungskarten, −0,35 neu; V14 als Teamentscheidung) und „Was noch fehlt, ist Information“ (Orakel 96,5 statt 85 % bei Sichtweite 1).
  - Folie 13: Replay-Hinweis auf die Kandidaten-Rettung.
  - Reservefolie 14: Ergebnisse der letzten Prüfungen.
  - Reservefolie 16: Lage der Relics (6er-Raster) und Punktefeld-Wahrscheinlichkeit.
  - Neue Reservefolie 17: Orakel-Test, Tabelle nach Sichtweite.
- **Stichpunkte** (`Sherlock_Stichpunkte_06-11-2026.md`):
  - Sprechtext zu den Folien 1–3 und 10–13.
  - Zeitplan 9:50 (Moayed 5:20, Mahmoud 4:30), Upload-Hinweis auf die V14-Zip.
  - Neue Rückfragen: warum V14 trotz Hürde, Orakel-Test, warum nicht weitertrainieren, die +1,8-Regel.
  - Belege ergänzt.
- **README:** Links zu PDF, Quelle und Stichpunkten mit Stand V14; Termine mit Upload-Hinweis.
- **Offen für das Team:**
  - Moayed prüft seine Folien 1–5, 10, 12 und 13; beide proben zweimal mit Uhr.
  - Mahmoud lädt bis Mittwochnacht `Gruppe15.zip` (V14, 01.11., 17:51) hoch.

## 01.11.2026, 17:56 Berlin – Claude Code mit Mahmoud: **V14 `v14_rescue` ist die neue Abgabe** (Teamentscheidung)

- **Entscheidung:** Mahmoud hat um 17:51 ausdrücklich zugestimmt („ja lets go“), `cand_rescue` trotz der knapp verfehlten Hürde zu übernehmen. Empfehlung von Claude Code: Der Gewinn ist klein, aber in zwei unabhängigen Messungen belegt.
  - Dev A: +0,50 pp [+0,14; +0,94].
  - Frische Karten 820000–820799: +0,86 pp [+0,48; +1,28], alle 6 Gegner im Plus, Solution_92 95,44 statt 94,94 %, direkt 50,6 %.
  - Vorher hatte das Übernahmeskript die Übernahme ohne bestandenes Gate verweigert. Ein erster Versuch mit Mahmouds Antwort „wie du willst“ wurde vom System als nicht ausdrücklich genug blockiert. Danach kam das ausdrückliche Ja.
- **Werkzeug:** `scripts/release_candidate.py --team-decision` (Commit `95a9627`, Test): Die Übernahme ohne bestandenes Gate verlangt eine schriftliche Begründung; sie steht mit `gate_passed: false` im Manifest `experiments/releases/20261101_v14_rescue.json`.
- **Übernahme** (17:51): V13 bytegleich gesichert in `experiments/releases/20261101_v13_neb/`; beide Abgabe-Dateien jetzt SHA-256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8` (Quelle `experiments/ensembles/battle_v18r.pth`).
- **Prüfungen:**
  - Kurs-Runner 8 Spiele bestanden (act Median 4,7–5,7 ms, max 11,6 ms).
  - `Gruppe15.zip` neu gebaut (17:51, 22,2 MB, SHA-256 `50c188b1…`), „Check ok“ an beiden Orten. `Gruppe15/agent.pth` hat dieselben Tensoren und dieselbe Config plus `frozen=True`; alle 15 Python-Dateien sind bytegleich.
  - 3 Spiele (800000, 800004, 4242) unter Python 3.10.15 mit torch 2.14.1/numpy 2.2.6 und torch 2.2.2/numpy 1.26.4 nachgespielt: 0 abweichende Aktionen.
  - Testsuite 632 bestanden.
- **Doku:** [Übernahmebericht](../experiments/analysis/release_20261101_v14/RELEASE.md); CLAUDE.md und README auf V14, README-Zahlen neu gezählt (1.350.347 Spiele).
- Die V13-Zip vom Vormittag liegt als Kopie im Scratchpad und lässt sich aus der Sicherung jederzeit neu bauen.
- **Abgabe: V14 `v14_rescue`.** Upload `Gruppe15.zip` bis Mittwoch, 04.11., nachts (Mahmoud lädt einmal am Ende hoch).

## 01.11.2026, 17:29 Berlin – Claude Code (autonom): `v19cr` auf frischen Karten durchgefallen (−0,35 statt +1,81 auf Dev A); V13 bleibt

- **Battle-Bestätigung `v19cr`** (15:22–17:28, 822000–823399, Code `49a82ec`): **nicht bestanden.**
  - Mittel 6 −0,35 pp [−1,30; +0,59], Solution_92 −0,50, direkt gegen V13 50,6 % [46,5; 54,9].
  - Je Gegner: V3 −2,00, `league_nets6` −1,62, Solution_92 −0,50, V7 +0,50, `sol92_sq` +0,50, `threat6` +1,00.
- **Einordnung:**
  - Auf Dev A waren es +1,81. `cand_post` wurde dort entwickelt, die Probe lief auf denselben Spielen, und der beste von vier Kandidaten wurde gewählt. Diese Auswahl hat den Wert nach oben verzerrt.
  - `cand_rescue` allein (`v18r`, frische Karten 820000–820799) brachte +0,86 mit allen 6 Gegnern im Plus. Die neuen Schalter haben auf frischen Karten also eher geschadet.
  - Die vorab festgelegte Bestätigung hat damit genau ihren Zweck erfüllt: Eine auf den Entwicklungskarten scheinbar bessere, in Wahrheit nicht bessere Version wurde nicht übernommen.
- **Lehre für weitere Kandidaten:** Was auf Dev A entwickelt wurde, vor der Battle-Bestätigung auf einem eigenen, unbenutzten Entwicklungsblock prüfen.
- **Stand `cand_rescue`:** zwei unabhängige Messungen positiv.
  - Dev A +0,50 [+0,14; +0,94], frisch +0,86 [+0,48; +1,28], kein Gegner schlechter, direkt 50,6 %.
  - Die Hürde +1 pp ist verfehlt. Eine Übernahme wäre nur als ausdrückliche Teamentscheidung möglich (Mahmoud gefragt).
- Abgabe unverändert **V13 `v13_neb`**, `Gruppe15.zip` vom 01.11., 10:46.

## 01.11.2026, 15:22 Berlin – Claude Code (autonom): Screen: `v19cr` +1,81 pp zugelassen, Battle-Bestätigung läuft

- **Screen** (13:59–15:21, Code `9a34ffa`, Dev A gepaart gegen V13):
  - **`v19cr`** = V13 + `cand_post=15` + `spawn_proof` + `cand_rescue` (`rescue_after=30`): Mittel 6 **+1,81 pp [+0,25; +3,42]**, Solution_92 +2,17, direkt 51,7 % → zugelassen, gewählt.
  - Je Gegner bei `v19cr`: V7 +3,67, `league_nets6` +3,00, Solution_92 +2,17, V3 +1,67, `sol92_sq` +0,33, `threat6` ±0.
  - `v19c` +1,22 (zugelassen); `v19s` −0,28 und `v19sr` +0,22 (nicht zugelassen).
  - Der Gewinn kommt also von `cand_post` (wahrscheinliche Punkte-Felder zuerst testen), nicht vom Spawn-Beweis.
- **Battle-Bestätigung `v19cr`** gegen V13 läuft seit 15:22 auf 822000–822799, direkt 823000–823399 (`GG_*`, 14 Prozesse, Code `49a82ec`). Ende etwa 17:45.
  - Besteht `v19cr`, folgt die Übernahme als **V14** mit `release_candidate.py`, neuer Zip, Tests und Nachspielen unter Python 3.10.
  - Sonst bleibt V13.
- Abgabe unverändert **V13 `v13_neb`**.

## 01.11.2026, 13:59 Berlin – Claude Code (autonom): `v18r` knapp nicht bestanden (+0,86 statt +1,0); Screen von vier `v19`-Kandidaten läuft

- **Battle-Bestätigung `v18r`** (V13 + `cand_rescue`, 11:33–13:56, Code `961a93a`, 820000–821399): **nicht bestanden.**
  - Mittel 6 +0,86 pp [+0,48; +1,28], Solution_92 +0,50 [+0,12; +0,88], default 100 %, direkt gegen V13 50,6 % [49,25; 52,0].
  - Verfehlt: Δ ≥ +1 pp und untere Grenze direkt > 50 %.
  - Alle 6 Gegner wurden besser (+0,5 bis +1,3 pp). `cand_rescue` wirkt also nachweislich, allein aber unter der Hürde. V13 bleibt.
  - Wie vorgesehen lief die ganze Reihe mit demselben Code: Die neuen Schalter lagen bis zum Ende in der Arbeitskopie im Scratchpad.
- **Verworfen: Wachposten `relic_watch`** (nur Arbeitskopie, nicht versioniert): Das erste Relic war damit später bekannt (Median 12 statt 9 Schritte), Siege gegen Solution_92 bei Sichtweite 1 87,5 statt 85,4 % (Rauschen).
- **Schalter `cand_post` + `spawn_proof` versioniert** (Commit `9a34ffa`):
  - Volle Testsuite 631 bestanden.
  - 32 V13-Spiele mit dem neuen Code identisch zu `D_v15cx.csv`.
- **Screen läuft seit 13:59** (`REF=v15cx WORKERS=14 bash scripts/battle_v15.sh admit v19c v19cr v19s v19sr`, Nachträge 12:17 und 13:20). Ende etwa 15:30–15:45.
  - `D_v19c.csv`, `D_v19cr.csv` und `D_v19c_rl.csv` wurden vorher aus der Arbeitskopie gerechnet. Ihr Code ist dateigleich mit `9a34ffa` (per `cmp` geprüft), die Ergebnisse sind deterministisch. Das Skript überspringt vorhandene Dateien.
  - Vorab bekannt aus diesen Dateien: Solution_92 +2,2 pp, `sol92_sq` +0,2/+0,3 (`v19c`/`v19cr`).
- **Danach:** Der zugelassene Kandidat mit dem höchsten Mittel bekommt die Battle-Bestätigung auf 822000–822799, direkt 823000–823399 (~2,5 Stunden). Besteht er, folgt die Übernahme als V14 heute Abend.
- Abgabe unverändert **V13 `v13_neb`**.

## 01.11.2026, 12:19 Berlin – Claude Code (autonom): neue Schalter `cand_post` + `spawn_proof`, Probe gegen Solution_92 +2,9 pp; `v19c`/`v19cr` vorab festgelegt

- **Auftrag Mahmoud (11:4x):** weiter trainieren und neue Regeln coden, Folien erst am Ende; Ziel Platz 1 im Kurs.
- **Verluste gegen `league_nets6`** (Energiebilanz `scripts/mechanism_probe.py`, Dev A, je 120 verlorene/gewonnene Spiele von V13):
  - In verlorenen Spielen ist das Sap-Duell ausgeglichen: Sap-Kills 10,0 zu 10,5 je Match, in gewonnenen 14,1 zu 9,8.
  - 47 % der verlorenen Spiele haben Streufaktor 0,25 (sonst ein Drittel). Das ist die bekannte Schwäche, keine neue Regel daraus.
- **Spur „Units punkten, bevor sie das Relic sehen“** (Sichtweite 1, 268 Paare):
  - In 67 % der Fälle steht eine Unit vorher schon auf einem Punkte-Feld, im Mittel 6,5 Schritte früher. Mit Nebel am Relic hat das nichts zu tun.
  - Bewiesene Punkte-Tiles ohne bekanntes Relic gibt es aber fast nie (3 % der Spiele, nur Match 2/3). Eine Suchregel dafür lohnt nicht.
- **Neue Schalter** (Standard aus, Tests in `tests/test_relic_prior.py`, 9 Tests):
  - `cand_post`: Kandidaten mit höherer Punkte-Wahrscheinlichkeit zuerst testen. Ein Tile in 1/2/3/4+ Relic-Zonen ist zu 20/34/49/57 % ein Punkte-Tile (1.500 Karten); offene Gleichungen geben rest/n.
  - `spawn_proof`: Im 2./3. Match beweist ein Punkt, den keine bekannte Zone erklärt, dass das neue Paar gespawnt ist (alle früheren Paare bekannt). Die Inferenz darf dann vor Schritt 50 schließen.
- **Entwicklungsprobe** V13 + `cand_post=15` + `spawn_proof` (Dev A, nur Auswahl, kein Gate):
  - gegen Solution_92 auf 221 Karten (442 Spiele) **95,7 statt 92,8 %**: Sichtweite 1 91,7 statt 85,4 %, Sichtweite 2 95,5 statt 94,2 %, Sichtweite 3/4 100 statt 98,6 %; 21 Spiele neu gewonnen, 8 neu verloren;
  - gegen V7 bei Sichtweite 1 unverändert 76,4 % (je 12 gewonnen und verloren).
- **Plan-Nachtrag 12:17** (Commit `f24a96e`): Kandidaten `v19c` (V13 + beide Schalter) und `v19cr` (+ `cand_rescue`, `rescue_after=30`). Screen nach dem Ende der `v18r`-Bestätigung, danach genau eine Battle-Bestätigung auf 822000–822799, direkt 823000–823399 (vorher geprüft: unbenutzt).
- **Code und laufende Messung (offen dokumentiert):**
  - Die beiden Schalter standen von etwa 11:40 bis 12:18 unversioniert im Hauptordner, während die `v18r`-Bestätigung lief.
  - Ihr erster Teil (V13 auf 820000–820799) hatte den Code beim Start um 11:33 geladen. Die weiteren Teile starten erst später.
  - Um 12:18 wurde der Hauptordner auf den Code beim Start (`961a93a`) zurückgesetzt. Die neuen Schalter liegen bis zum Ende der Messung in einer Arbeitskopie im Scratchpad.
  - Die Messreihe läuft also vollständig mit demselben Code.
- **Läuft:**
  - `v18r`-Bestätigung (12 Prozesse, Ende etwa 14:20);
  - aus der Arbeitskopie die Screen-Dateien `D_v19c.csv`/`D_v19cr.csv` (Solution_92, `sol92_sq`) mit 3 Prozessen. Die Ergebnisse sind deterministisch und kommen nach dem Commit der Schalter in den Hauptordner.
- Abgabe unverändert **V13 `v13_neb`**.

## 01.11.2026, 11:35 Berlin – Claude Code (autonom): Relic-Gitter gefunden, `relic_prior` ohne klaren Gewinn; Gate-Rundung behoben; Bestätigung `v18r` läuft

- **Warum Sherlock bei Sichtweite 1 Information fehlt** (Dev A, V13 gegen Solution_92, nur Diagnose, Skripte im Scratchpad):
  - Relics findet Sherlock dort nicht langsamer als Solution_92. Paar 0: erster eigener Punkt im Mittel 10,3 Schritte nach dem Spawn, Solution_92 13,2.
  - Langsam ist das Erschließen einer Zone: Bis alle Punkte-Tiles bewiesen sind, dauert es 30–40 Schritte, bei jeder Sichtweite. Die Units testen etwa ein Kandidaten-Feld pro Schritt; die Laufwege begrenzen das.
  - Im 2. und 3. Match ist die Inferenz die ersten ~45 Schritte gesperrt (Spawnfenster). Unbewiesene Punkte-Tiles häufen sich bis Schritt 40–50 auf etwa 2 an.
  - Bei Sichtweite 1 entscheidet dieses Tempo enge Spiele. Mit den wahren Punkte-Tiles gewinnt V13 alle drei Matches häufiger (Match 1/2/3: 92 → 97, 78 → 83, 76 → 84 %).
- **Relic-Gitter:** Die Engine setzt Relics auf die höchsten Werte eines Perlin-Rauschens (Zellen zu 6 Tiles). Auf 10.000 Karten liegen 96,8 % aller Relics auf Streifen mit x%6 oder y%6 in {2, 3}, 30 % in 2×2-Kernen und keine bei x%6 und y%6 in {0, 5}. Spätere Paare liegen meist direkt neben früheren (Paar 1 zu 64 % höchstens 2 Felder entfernt).
- **Neuer Schalter `relic_prior`** (Standard aus, Commit `961a93a`, 5 Tests): Erkundungsziele nach dieser Verteilung.
  - Probe gegen Solution_92: Sichtweite 1 +0,7, 2 +0,6, 3/4 −4,8 pp. Die Relics werden kaum schneller gefunden.
  - Damit kein Kandidat. V13 spielt mit dem neuen Code nachweislich gleich (16 Spiele identisch zu `D_v15cx.csv`).
- **Gate-Rundung behoben** (Commit `e6d4624`): `scripts/league_gates.py` vergleicht mit Toleranz 1e-9, neuer Test. `scripts/battle_v15.sh` = `battle_v14.sh` mit derselben Toleranz in der Zulassung und wählbarem Bestätigungsblock. Die vier früheren Battle-Entscheidungen (`v11h`, V12, `v13r0`, `v17a`) bleiben gleich.
- **Läuft seit 11:33:** Battle-Bestätigung `v18r` (V13 + `cand_rescue`, `rescue_after=30`) gegen V13 auf 820000–820799, direkt 821000–821399, wie im Plan-Nachtrag 07:15 festgelegt. 12 Prozesse, Ende etwa 14:15.
  - Keine der 1.166 CSVs enthält diese Seeds.
  - Erwartung ehrlich: Der Screen zeigte +0,50 pp; die Hürde liegt bei +1 pp. Bestehen ist unwahrscheinlich, aber die Rechner wären sonst ungenutzt.
- **Tests:** Vor dem Start der Bestätigung (11:31) 626 bestanden; der neue Gate-Test läuft einzeln grün. Ein voller Lauf während der Messung (11:34): 596 bestanden, 31 Tests in `tests/test_early_curriculum_study.py` brechen ab mit „Another model job is active; resource admission refused“. Das ist die Schutzschaltung der Studie gegen parallele Modelljobs, ausgelöst durch die laufende Bestätigung, kein Codefehler. Nach dem Ende der Messung wird der volle Lauf wiederholt.
- Abgabe unverändert **V13 `v13_neb`**.

## 01.11.2026, 10:55 Berlin – Claude Code (autonom): `v17a` nicht bestanden, **V13 `v13_neb` ist die neue Abgabe**; Orakel: bei Sichtweite 1 fehlt Information

- **Battle-Bestätigung `v17a`** (813200–813999, direkt 814000–814399, Code `518f289`, 07:56–10:40): **nicht bestanden.**
  - Mittel 6 87,75 statt 87,34 % (Δ +0,41 pp [−0,68; +1,52]), Solution_92 95,19 % (Δ +1,31 [+0,19; +2,50]), default 99,88 %, direkt gegen V12 53,75 % [49,0; 58,75] aus 800 Spielen.
  - Verfehlt: Mittel 6 ≥ +1 pp, untere Grenze > 0, direkt untere Grenze > 50 %.
  - Nachträglich nach Kartenparametern getrennt (nur Beschreibung): 115 Karten mit Nebelabzug 25 +3,26 pp [−0,29; +6,74], übrige 685 Karten −0,07 pp [−1,24; +1,08]. Die 12 nachtrainierten Netze brachten also nichts Messbares; der Gewinn kam aus der Nebel-Korrektur.
- **Übernahme V13 `v13_neb`** (10:46) nach Plan, Nachtrag 04:45: Die Nebel-Bestätigung zählt, weil `v17a` durchfiel. Quelle `experiments/ensembles/battle_v15cx.pth` = V12-Netze (alle Tensoren identisch) + `est_censor` + `neb_cross`.
  - **Vorher Prüfskript korrigiert** (Commit `a5d6dd6`): `gate_passed` las das gemischte Gate-Log falsch. `v15cx` wurde nicht erkannt, und `v17a` hätte fälschlich als bestanden gegolten. Jetzt zählt nur die Urteilszeile derselben Art. Auf allen alten Gate-Logs gibt es dieselben Antworten außer diesen zwei Fällen. 2 neue Tests.
  - `scripts/release_candidate.py`: V12 bytegleich gesichert in `experiments/releases/20261101_v12_fog/`. Beide Abgabe-Dateien jetzt SHA-256 `6d00b6c52366a613eed3b7b5b6f9c3c088802716a85c30fe192c46c57bdd8e62`. Kurs-Runner 8 Spiele bestanden, `act` im Median 5,4–6,7 ms, höchstens 10,3 ms.
  - `Gruppe15.zip` neu gebaut (10:46, 22,2 MB, SHA-256 `dad66c4d…`), „Check ok“ unter `agents/` und in der Projektwurzel. `Gruppe15/agent.pth` (SHA-256 `93451fb0…`) hat dieselben Tensoren und dieselbe Config wie die Abgabe, nur zusätzlich `frozen=True`. Alle 15 Python-Dateien sind bytegleich. Die V12-Zip vom 31.10. liegt als Kopie im Scratchpad und lässt sich jederzeit neu bauen.
  - 3 Spiele mit der Zip aufgezeichnet: 800000 (Nebelabzug 25), 800004 (Sichtweite 1), 4242. Unter Python 3.10.15 mit torch 2.14.1/numpy 2.2.6 und mit torch 2.2.2/numpy 1.26.4 nachgespielt: **0 abweichende Aktionen**.
  - Testsuite vor und nach der Installation: 621 bestanden, 14 Untertests.
  - [Übernahmebericht](../experiments/analysis/release_20261101_v13/RELEASE.md). CLAUDE.md und README stehen auf V13; die Zahlen im README sind neu gezählt (1.287.629 Spiele, davon 640.104 Trainingsspiele).
- **Orakel-Diagnose `v18r`** (Dev A, alle 6 Gegner, `O_v18r_full.csv`, nur Diagnose, kein Gate): Mit den wahren Relics und Punkte-Tiles Mittel 6 91,0 statt 86,5 % (+4,53 pp [+2,42; +6,67]), Solution_92 97,5 statt 94,5 %.
  - Nach Sichtweite, alle 6 Gegner: 1: +8,9, 2: +1,0, 3: +5,1, 4: +3,3 pp.
  - Gegen Solution_92: Sichtweite 1 **96,5 statt 85,4 %**, Sichtweite 2–4 −0,7 bis +1,3 pp. Die Schwäche bei Sichtweite 1 gegen Solution_92 ist also fast ganz eine Informationslücke.
  - Aufgeteilt auf den 72 Karten mit Sichtweite 1 (je 144 Spiele, Skript im Scratchpad):
    - gegen Solution_92: normal 85,4 %, nur Relics 90,3 %, nur Punkte-Tiles um schon bekannte Relics 94,4 %, beides 96,5 %;
    - gegen V7: 77,8 / 90,3 / 87,5 / 88,9 %.
  - Am Spielende kennt Sherlock fast gleich viele Punkte-Tiles (15,6 statt 17,0). Es fehlt also vor allem Tempo.
- **Nächste Schritte:**
  - Herausfinden, warum Sherlock bei Sichtweite 1 die Punkte-Tiles langsamer erschließt. Daraus eine Regel bauen und vor der Messung im Plan festlegen.
  - `cand_rescue` (zugelassen, +0,50 pp) möglichst nicht allein bestätigen: Bei erwarteten +0,5 pp ist die Hürde von +1 pp kaum erreichbar. Besser zusammen mit einer Sichtweite-1-Regel auf 820000–820799. Dafür braucht es einen Plan-Nachtrag vor der Messung.
  - Nachtraining Runde 7 (`scripts/pipeline_battle_ft7.sh`, nicht gestartet, nicht versioniert) zurückgestellt: Runde 6 brachte auf Karten ohne Nebelabzug 25 nichts.
- Abgabe: **V13 `v13_neb`**.

## 01.11.2026, 09:10 Berlin – Claude Code (autonom): Nebel-Bestätigung bestanden, `cand_rescue` zugelassen (Rundungsfehler im Skript)

- **Gezielte Nebel-Bestätigung `v15cx`** (Nachtrag 04:45, `scripts/battle_neb25.sh`, Code `eeaaddb`, 04:27–09:04): **alle 7 Hürden bestanden.**
  - 300 frische Karten mit Nebelabzug 25: Mittel 6 87,17 statt 84,78 % (Δ +2,39 pp [+0,31; +4,36]), Solution_92 +0,83, default 100 %, direkt gegen V12 56,0 % [50,8; 61,3].
  - Je Gegner: `league_nets6` +10,3 [+4,0; +16,3], V7 +3,2, V3 +1,8, `sol92_sq` −0,7, `threat6` −1,2.
  - 60 übrige Karten: 720 von 720 Ergebnissen gleich.
  - Zählt laut Plan nur, falls `v17a` die Battle-Bestätigung nicht besteht; dann wird V13 `v13_neb`. `v17a` enthält die Korrektur schon.
- **Screen `v18r`** (`cand_rescue` + `rescue_after=30` auf `v15cx`, Code `518f289`, 07:16–09:05):
  - Mittel 6 Δ **+0,50 pp [+0,14; +0,94]**, Solution_92 +0,17, direkt gegen `v15cx` **52,3 % [51,0; 53,7]**.
  - Exakt 18 Siege mehr in 3.600 Spielen (Δ = 1/200 = +0,50 pp). Die Regel verlangt Δ ≥ +0,5 pp, also **zugelassen**.
  - `battle_v14.sh` meldete trotzdem „nicht zugelassen“: In Gleitkomma ergab sich 0,004999999999999999 statt 0,005. Das Skript läuft gerade für `v17a` und wird deshalb erst danach korrigiert, mit Test.
  - Je Gegner: Solution_92 +1, `sol92_sq` +1, V3 +4, V7 +10, `league_nets6` ±0, `threat6` +2 Siege; 26 Ergebnisse verändert.
  - Battle-Bestätigung wie vorab festgelegt nach der Entscheidung über `v17a`, auf 820000–820799, direkt 821000–821399, gegen die dann aktuelle Abgabe.
- **Läuft:**
  - Battle-Bestätigung `v17a` (seit 07:56, 12 Prozesse).
  - Orakel-Diagnose ohne Gate (`scripts/oracle_probe.py`, 3 Prozesse): `v18r` mit den wahren Relics und Punkte-Tiles auf Dev A gegen die 6 Gegner, gepaart gegen `D_v18r*.csv`. Sie zeigt, wie viel Information noch fehlt; bei V10 waren es +4 bis +6 pp.
- Abgabe unverändert **V12**.

## 01.11.2026, 08:00 Berlin – Claude Code (autonom): `v17a` zugelassen, Battle-Bestätigung läuft; `cand_rescue` als `v18r` im Screen

- **Screen Runde 6** (`REF=v12 WORKERS=12 bash scripts/battle_v14.sh admit v17a v17b`, Code `59da48b`, 06:44–07:56), Dev A gepaart gegen V12:
  - **`v17a`** (48 Netze, Config V12 + Nebel-Korrektur): Mittel 6 **+1,22 pp** [−0,64; +3,17], Solution_92 ±0, **direkt gegen V12 60,3 %** [55,0; 66,0] → **zugelassen**. Je Gegner: V7 +8,0 [+3,0; +13,0], `league_nets6` +2,0, `threat6` ±0, V3 −1,3, `sol92_sq` −1,3, Solution_92 ±0.
  - `v17b` (36 Netze): +0,69 [−1,33; +2,75], Solution_92 −0,83, direkt 56,0 % → ebenfalls zugelassen, aber niedrigeres Mittel.
- **Battle-Bestätigung `v17a`** läuft seit 07:56 (`REF=v12 WORKERS=12 bash scripts/battle_v14.sh confirm v17a`, Code `518f289`): 813200–813999 gegen die 6 Gegner und default, direkt 814000–814399. Die Karten waren vorher in keiner der 1.157 CSVs mit Seed-Spalte; die einzigen Suchtreffer waren Trainingskarten 313000–314749. Hürden `league_gates battle`. Ende etwa 11:30–12:00, weil parallel noch zwei Messungen laufen.
- **Gleichstand-Probe** (verbrauchte Karten 812000–812149, V12 gegen Solution_92, 300 Spiele, Endstand je Match; Skript nur im Scratchpad):
  - Bei Punktgleichstand gewinnt laut Engine das Team mit mehr Gesamtenergie. Das entschied nur 8 von 900 Matches (0,9 %), alle für V12.
  - Die vorbereitete Regel `tie_save` (Energie sparen bei drohendem Gleichstand) kommt deshalb nicht in den Hauptstand. Sie liegt nur in einer Arbeitskopie im Scratchpad, mit 3 Tests.
- **Wichtiger Befund dieser Probe:**
  - V12 verliert Match 2 und 3 dreimal so oft wie Match 1 (16,7/15,7 statt 5,7 %).
  - 102 von 114 verlorenen Matches gehen mit mehr als 10 Punkten Rückstand verloren.
  - 14 Matches mit weniger als 20 % der Gegnerpunkte stecken in 13 der 21 verlorenen Spiele.
  - Ursachen: der Nebel-Fehler (812049, 812081) und Kandidaten, die nicht getestet werden. Auf 812121 sind die Relics seit Match 1 bekannt, aber über 140 Schritte bleibt kein Punkte-Tile bekannt. Die Units pendeln auf Energiefeldern im Nebel, ihr Ziel-Kandidat wechselt jeden Schritt; Match 2 endet 0:202. Auf 812036 dasselbe Muster bei Sichtweite 1.
- **`cand_rescue` als Kandidat `v18r`** ([Plan-Nachtrag 07:15](superpowers/plans/2026-10-29-battle-push.md)):
  - `v18r` = `v15cx` + `cand_rescue` + `rescue_after=30`, SHA-256 `98a07350…`, Netze bytegleich mit V12.
  - Diagnose ohne Gate (9 verbrauchte, gezielt gewählte Karten, 18 Spiele): V12 10/18, `v15cx` 12/18, `v18r` 14/18.
  - Screen gegen `v15cx` läuft seit 07:16 mit 4 Prozessen. Bisher Solution_92 94,5 %, `sol92_sq` 91,0 %.
- **Gezielte Nebel-Bestätigung** (seit 04:27) läuft weiter. Sie zählt nur, wenn `v17a` die Battle-Bestätigung nicht besteht.
- Den Zeitstempel des Plan-Nachtrags zu `v18r` habe ich von 07:20 auf 07:15 korrigiert (Commit um 07:16).
- Abgabe unverändert **V12**.

## 01.11.2026, 06:45 Berlin – Claude Code (autonom): Nachtraining Runde 6 fertig, Screen von `v17a`/`v17b` läuft

- **Training** (`scripts/pipeline_battle_ft6.sh`, Code `e3cd0fc`, 04:23–06:43): 12 Netze (s16–s27) je 2.000 Spiele, zusammen **24.000 Trainingsspiele** plus 1.920 Validierungsspiele, alle Läufe mit exit 0. `--keep-final`: Jedes Netz ist der Endstand nach 2.000 Spielen.
  - Einzelnetz-Validierung (je 16 Spiele, nur grobe Richtung): gegen Solution_92 im Mittel 77,1 % vor und 77,1 % nach dem Training, gegen default 95,8 % → 94,8 %. Einzelne Netze schwanken stark (s22 50 → 75 %, s24 44 → 38 %, s20 88 → 69 %).
  - Läufe: `experiments/runs/20261101_ft6_v12_s16` bis `_s27` (Gewichte und Buffer gitignored), Log `experiments/pipeline_battle_ft6.log`.
- **Kandidaten** (gitignored, Config = V12 + `est_censor` + `neb_cross`, sonst identisch):
  - `battle_ft6_12.pth`, die 12 neuen Netze, SHA-256 `9a705547…`.
  - `battle_v17a.pth`, V12-Netze + 12 neue = 48 Netze, `0f860b0b…`.
  - `battle_v17b.pth`, V10-Netze + ft3 s10–s15 + 12 neue = 36 Netze, `a8fa16c8…`.
- **Läuft:** `REF=v12 WORKERS=12 bash scripts/battle_v14.sh admit v17a v17b` (Start 06:44, Code `59da48b`), Zulassung wie bisher. Parallel weiter die gezielte Nebel-Bestätigung mit 3 Prozessen: V12 auf den Abzug-25-Karten ist fertig (Solution_92 94,2 %, `league_nets6` 65,7 %), jetzt läuft `v15cx`.
- Abgabe unverändert **V12**.

## 01.11.2026, 04:25 Berlin – Claude Code (autonom): `no_strand` ohne Gewinn; Nachtraining unter den V12-Regeln gestartet

- **Screen** (`REF=v12 WORKERS=12 bash scripts/battle_v14.sh admit v16s v16all`, Code `c9fe79b`, 03:28–04:19), Dev A gepaart gegen V12:
  - `v16s` (`no_strand`): Mittel 6 Δ −0,28 pp [−1,50; +0,92], direkt 50,8 %.
  - `v16all` (alle drei Schalter): Mittel 6 Δ −0,06 [−1,33; +1,22], direkt 51,0 %.
  - Beide **nicht zugelassen**. Gegen `league_nets6` −3,0 bzw. −3,7, gegen V3, V7 und Solution_92 +0,7 bis +1,7. 280 von 3.600 Ergebnissen ändern sich, ohne klares Muster. `no_strand` bleibt im Code (aus), wird aber nicht weiter verfolgt.
- **Weitere Spur** (verbrauchte Karte 812618 gegen `league_nets6`, Bewegung 5, Sicht 1, Spielbild):
  - Beide Seiten haben Units mit 0 Energie; `league_nets6` erobert die Punkte-Tiles um unser Relic.
  - Ein einzelner Fehler ist das nicht, sondern ein Zusammenspiel vieler Entscheidungen der Netze.
- **Deshalb Nachtraining** ([Plan-Nachtrag 01.11., 04:25](superpowers/plans/2026-10-29-battle-push.md)):
  - Die Netze haben die V11/V12-Regeln nie im Training gesehen; V11 entstand aus genau so einem Nachtraining (R +4,66 pp).
  - `scripts/pipeline_battle_ft6.sh`, neue Variante `full_rules_v12` (V12-Config + Nebel-Korrekturen, alle Regeln im Training).
  - 12 der V12-Netze je 2.000 Spiele, 12 parallel, Kartenversatz 4000.
  - Gegner: Solution_92-Varianten 60 %, Pool aus V10, old3, V11 und V12 30 %, rush und default je 5 %.
  - Danach die Kandidaten `v17a` (48 Netze) und `v17b` (36 Netze, die 12 neuen ersetzen ihre Vorgänger), Screen wie bisher.
  - Ende des Trainings etwa 07:30–08:00.
- Abgabe unverändert **V12**.
- **Nachtrag 04:50:** gezielte Bestätigung der Nebel-Korrektur vorab festgelegt ([Plan-Nachtrag 04:45](superpowers/plans/2026-10-29-battle-push.md)).
  - Karten: die ersten 300 frischen Karten mit Abzug 25 aus 816000–819999 und 60 übrige Karten als Gleichheitsprobe.
  - Hürden: auf den Abzug-25-Karten Mittel 6 ≥ +1 pp mit unterer Grenze > 0; auf den übrigen Karten ≥ 98 % gleiche Ergebnisse.
  - Läuft seit 04:28 mit 3 Prozessen **parallel** zum Training. Laut Plan sollte sie erst nach Runde 6 laufen; vorgezogen habe ich sie, weil 3 Kerne frei waren.
  - An der Entscheidung ändert das nichts: Besteht `v17a`/`v17b` die Battle-Bestätigung, zählt `v17`, und die Abgabe enthält die Korrektur ohnehin. Nur sonst entscheidet dieser Test.

## 01.11.2026, 03:30 Berlin – Claude Code (autonom): Nebel-Korrektur knapp nicht zugelassen (auf Nebel-25-Karten +2,7 pp); neue Regel `no_strand`, Screen läuft

- **Screen** (`REF=v12 WORKERS=12 bash scripts/battle_v14.sh admit v15c v15cx`, Code `2e4eee7`, 02:24–03:21), Dev A gepaart gegen V12:
  - `v15c` (`est_censor`): Mittel 6 Δ +0,08 pp [−0,36; +0,53], direkt 49,8 % → nicht zugelassen.
  - `v15cx` (+ `neb_cross`): Mittel 6 Δ **+0,42** [−0,36; +1,28], Solution_92 +0,33, direkt 51,5 % → **knapp nicht zugelassen** (Hürde +0,5).
  - Die Wirkung liegt fast ganz auf Karten mit Nebelabzug 25: dort 88,39 statt 85,71 % (**+2,68 pp**, 672 Spiele; 84 der 87 veränderten Ergebnisse). Auf den übrigen fünf Sechsteln der Karten ändert sich praktisch nichts.
- **Zweiter Befund** (verbrauchte Karte 812256, Bewegungskosten 4, Sicht 1, Spielbild und Verlauf):
  - Units auf dem Weg zur Relic-Ecke bleiben 3–5 Felder davor mit 0 Energie liegen, auf Feldern ohne Energiegewinn, bis zum Matchende.
  - Das Gedächtnis findet die Relics deshalb nie, zeitweise haben 11 von 15 Units kein Ziel.
  - Match 2 endet 1:297.
- **Neue Regel `no_strand`** (Standard aus): kein Zug mit der letzten Zugenergie auf ein Feld ohne Energiegewinn, außer auf Punkte- und Kandidaten-Tiles. Stattdessen sammelt die Unit Energie.
  - 3 Tests in `tests/test_no_strand.py`, **ganze Suite 618 bestanden**. Ein Lauf direkt nach `par_eval` meldete wieder nur die Ressourcensperre von `test_early_curriculum_study`; der Lauf danach war grün.
  - V12 mit dem neuen Code: 16 Spiele identisch.
- **Rauchtest** (gezielt ausgewählte, verbrauchte Niederlagen, 8 Spiele gegen Solution_92, kein Gate): V12 2/8, `no_strand` 3/8, alle drei Korrekturen 6/8; 812256 von 6:909 zu 544:294.
- **Kandidaten:** `battle_v16s.pth` (`no_strand`, SHA-256 `591d05c5…`) und `battle_v16all.pth` (`est_censor` + `neb_cross` + `no_strand`, `b3903e06…`). Vorab festgelegt im [Plan-Nachtrag 01.11., 03:25](superpowers/plans/2026-10-29-battle-push.md).
- **Läuft:** `REF=v12 WORKERS=12 bash scripts/battle_v14.sh admit v16s v16all`, Ende etwa 04:30. Abgabe unverändert **V12**.

## 01.11.2026, 02:25 Berlin – Claude Code (autonom, Auftrag Mahmoud): Fehler in der Nebel-Schätzung gefunden und behoben (Schalter), Screen gegen V12 startet

- **Auftrag Mahmoud (gegen 1 Uhr):** „codiere doch einfach neue Regeln und teste diese … alles was geht“, Ziel Platz 1 gegen alle Agenten im Kurs, „hast alle Genehmigungen“. Die Absprache „keine Regeltests mehr vor dem Battle“ ist damit aufgehoben.
- **Suche** (nur verbrauchte Karten, nichts für Gates):
  - V12 nach versteckten Parametern auf 808000–808799 und 812000–812799, 19.200 Spiele.
  - Verlorene und gewonnene Spiele mit Wahrheit nachgemessen (`scripts/par_losses`, gegen `league_nets6`, V7 und Solution_92).
  - Probe für einen exakten Löser der Punkte-Gleichungen: Er bringt nichts, nach der Propagation bleiben kaum offene Gleichungen.
  - Abstimmung der 36 Netze: Die Q-Werte beider Hälften sind gleich groß, kein Problem.
- **Gefundener Fehler:** Ein Spielbild von 812584 zeigte das Problem (Nebelabzug 25, Bewegungskosten 5; V12 verliert gegen Solution_92 beide Seiten, 272:1112 und 259:1074).
  - Die Schätzung des Nebelabzugs (`param_est`) kippt in Match 1 bei Schritt 33 von 25 auf 0. Die Nebel-Meidung ist danach für das ganze Spiel aus.
  - Grund: Die Engine kappt die Energie bei 0. Eine Unit mit 0 Energie auf einem Nebel-Tile ohne Feldenergie zeigt „Verlust 0“, und jeder Schritt zählt als neuer Beleg für Abzug 0.
  - In Match 2 standen 3 von 4 verfolgten Units mit 0 Energie im Nebel fest (16:629 Punkte).
- **Neue Schalter** (Standard aus):
  - `est_censor`: Beobachtungen mit Energie 0 zählen in der Schätzung nicht.
  - `neb_cross`: Nebel nur mit Energie für die ganze Durchquerung betreten, statt pauschal mit 2 × Abzug.
  - 6 neue Tests in `tests/test_nebula_fix.py`, darunter die Nachstellung des Fehlers.
  - **Ganze Suite 615 bestanden.** Ein erster Lauf direkt nach der Gleichheitsprüfung meldete Fehler in `test_early_curriculum_study`, weil dessen Ressourcensperre noch Prozesse sah; der Lauf danach war grün.
  - V12 mit dem neuen Code (Schalter aus): 16 Spiele auf 812000–812003 in allen 20 Kennzahlen identisch.
- **Rauchtest** 812584 (verbraucht, kein Gate): Mit beiden Schaltern gewinnt V12 beide Seiten, 994:342 und 825:337.
- **Kandidaten:** `battle_v15c.pth` (`est_censor`, SHA-256 `16a5c53a…`) und `battle_v15cx.pth` (beide Schalter, `6d00b6c5…`); sonst bytegleich mit V12. Vorab festgelegt im [Plan-Nachtrag 01.11., 02:20](superpowers/plans/2026-10-29-battle-push.md).
- **Startet jetzt:** `REF=v12 WORKERS=12 bash scripts/battle_v14.sh admit v15c v15cx`. Wird ein Kandidat zugelassen, folgt genau eine Battle-Bestätigung auf 813200–814399.
- Abgabe bis dahin unverändert **V12**.

## 01.11.2026, 00:46 Berlin – Claude Code mit Mahmoud: `end_sap` nicht zugelassen, V12 bleibt die Battle-Abgabe; Ende der Regeltests

- **Screen** (`REF=v12 WORKERS=12 bash scripts/battle_v14.sh admit v14e10 v14e20`, Code `2924b53`, 23:54–00:44), Dev A 800000–800299 gepaart gegen V12, je Gegner 600 Spiele, direkt gegen V12 600 Spiele:
  - **`v14e10`** (`end_sap` 10): Mittel 6 86,67 statt 85,56 % (**Δ +1,11 pp [+0,22; +2,00]**), Solution_92 −0,33, **direkt gegen V12 45,7 % [40,8; 50,5]** → nicht zugelassen (Hürde direkt ≥ 50 %). Je Gegner: `league_nets6` +3,00 [−0,33; +6,33], `threat6` ±0, V3 −0,67, V7 +4,33 [+1,67; +7,33], `sol92_sq` +0,33, Solution_92 −0,33.
  - **`v14e20`** (`end_sap` 20): Mittel 6 +0,14 [−1,03; +1,31], Solution_92 −0,33, direkt 54,0 % [48,7; 59,3] → nicht zugelassen.
  - Gegen die 6 Gegner gibt es 4 bis 11 Saps je Spiel mehr. Der Gegner macht 1 bis 11 Punkte je Spiel weniger, die eigenen Punkte ändern sich um −10 bis +3. Direkt gegen V12 hat `v14e10` gleich viele Punkte (1.026 : 1.024 je Spiel), gewinnt aber weniger Matches (863 : 937).
- **Entscheidung laut Plan: V12 bleibt die Abgabe.** Keine Battle-Bestätigung, 813200–814399 bleiben unbenutzt. Wie mit Mahmoud vereinbart, werden vor dem Battle keine weiteren Regeln getestet.
- **Code:** `end_sap` bleibt im Hauptstand, Standard aus. Die Upload-Datei `Gruppe15.zip` von 31.10., 20:07 enthält den Code davor; V12 spielt mit beiden identisch (16 Spiele, Eintrag 23:54). Sie bleibt die Upload-Datei.
- **Daten:** `experiments/compare/battle/D_v14e10*.csv`, `D_v14e20*.csv`, Protokoll `experiments/battle_dev.log`. README („Grenzen“), Plan und Experiment-Protokoll nachgetragen.
- **Nachtrag 00:50, README neu gezählt** (gleiche Befehle wie am 31.10., 22:15):
  - Bewertungsspiele 516.025, zusammen **1.196.033 Spiele**.
  - Rechenzeit Bewertung 608 Prozess-Stunden, insgesamt rund 1.170.
  - 20.090 Karten; 156 Einstellungen; 609 Tests; 408 Commits; 141 Arbeitsstand-Einträge.
  - Die Zählregel für gleiche Zeilen ist jetzt genau beschrieben, in README und `count_games.py`: Zeilen, die in allen Spalten einschließlich `secs` gleich sind, zählen einmal. Das trifft auch verschiedene Läufe mit genau gleichem Spielverlauf, zum Beispiel 360 Zeilen von `v13r0` heute Nacht, die mit V12 übereinstimmen. Die Zahl ist also eine untere Grenze.

## 31.10.2026, 23:54 Berlin – Claude Code mit Mahmoud: Regel `end_sap` (Restenergie am Matchende) im Hauptstand, Screen gegen V12 läuft

- **Neu** (Standard aus, [Plan-Nachtrag 22:05](superpowers/plans/2026-10-29-battle-push.md)): Schalter `end_sap` (Zahl der letzten Schritte eines Matches) und `end_sap_hold` (1,0) in `config.py`, Methode `_end_sap` in `main.py` direkt nach `idle_sap`.
  - In den letzten `end_sap` Schritten schießen Units auf sichtbare Gegner in Reichweite: zuerst auf Gegner auf bekannten Punkte-Tiles, dann auf unbewegte, dann auf alle übrigen, jeweils den mit der geringsten Restenergie nach den schon geplanten Saps.
  - Halter behalten eine Sap-Kosten Energie, außer im letzten Schritt. Units, die ein Punkte- oder Kandidaten-Tile noch rechtzeitig erreichen, laufen weiter.
- **Grund:** Die Engine entfernt am Matchende alle Units. Im Mittel verfallen dabei etwa 1.100 Energie je Match ungenutzt (Probe im Eintrag 21:50).
- **Prüfungen:**
  - 5 neue Tests (`tests/test_end_sap.py`), **ganze Suite 609 bestanden** (+14 Untertests).
  - V12 mit dem neuen Code (Schalter aus): 16 Spiele auf 812000–812003 gegen Solution_92 und `league_nets6` (schon verbraucht) in allen 20 Kennzahlen außer der Laufzeit identisch mit der Battle-Bestätigung.
- **Kandidaten** (`scripts/set_cfg`; Netze und alle übrigen Felder identisch mit V12, nur `end_sap` gesetzt): `experiments/ensembles/battle_v14e10.pth` (10 Schritte, SHA-256 `57d50b21…`) und `battle_v14e20.pth` (20 Schritte, `16600f07…`).
- **Basis V12**, weil `v13r0` nicht bestanden hat (Eintrag 23:50).
- **Läuft seit 23:54** (Code `2924b53`): `REF=v12 WORKERS=12 bash scripts/battle_v14.sh admit v14e10 v14e20`. Dev A wird gepaart gegen die vorhandenen `D_v12*.csv` ausgewertet, dazu kommen 600 Spiele direkt gegen V12. Ende etwa 1:00. Wird ein Kandidat zugelassen, folgt genau eine Battle-Bestätigung auf 813200–814399.
- Abgabe unverändert **V12**.

## 31.10.2026, 23:50 Berlin – Claude Code mit Mahmoud: `v13r0` in der Battle-Bestätigung nicht bestanden, V12 bleibt

- **Lauf:** `WORKERS=12 bash scripts/battle_v13.sh confirm v13r0` (Code `294942d`, 21:41–23:46). V12 und `v13r0` auf 812000–812799 gegen die 6 Gegner und default, je Gegner 1.600 Spiele; direkt gegen V12 auf 812800–813199, 800 Spiele. Hürden `scripts/league_gates.py battle`.
- **Ergebnis:**
  - Mittel über 6 Gegner 86,96 statt 86,51 % (**Δ +0,45 pp [−0,24; +1,10]**): Hürde +1,0 pp und untere Grenze > 0 verfehlt.
  - Solution_92 94,25 statt 95,00 % (**Δ −0,75 [−1,69; +0,19]**): Hürde −0,5 verfehlt.
  - default 99,94 % (±0); direkt gegen V12 **59,4 % [56,5; 62,3]** aus 800 Spielen (bestanden).
  - Je Gegner: `league_nets6` +1,50 [−0,50; +3,50], `threat6` −0,25 [−1,75; +1,25], V3 +0,62, V7 +1,00, `sol92_sq` +0,56, Solution_92 −0,75.
- **Entscheidung: nicht bestanden, V12 bleibt Abgabe.** Abgabe-Dateien unverändert (`b258dc99…`), Upload-Datei weiter `Gruppe15.zip` von 20:07. `v13r0` gewinnt zwar direkt gegen V12, verbessert die übrigen Gegner aber kaum. Laut Plan wird an der Nebel-Sap-Menge vor dem Battle nicht weiter gedreht.
- **Daten:** `experiments/compare/battle/GD_V12_conf.csv`, `GD_v13r0_conf.csv`, `GD_v13r0_confdir.csv`, Hürdenprotokoll `experiments/pipeline_battle_gate.log`. README („Grenzen“), Plan und Experiment-Protokoll nachgetragen.
- **Nächster Schritt laut Plan-Nachtrag 22:05:** Test der Regel `end_sap` mit **V12 als Basis**.

## 31.10.2026, 22:10 Berlin – Claude Code mit Mahmoud: README und Entscheidungsdokument auf den aktuellen Stand

- **Auftrag Mahmoud:** die md-Dateien auf GitHub an den jetzigen Stand anpassen, die README „perfekt“ machen.
- **`README.md`** neu gegliedert, vorher Stand 22.10. (`all18_v3`): „Auf einen Blick“, Fortschritt gegen Solution_92 von V3 bis V12 (jeweils mit dem Vorgänger auf denselben Karten), Ergebnisse von V12 je Gegner und nach Sichtweite, Entscheidungsablauf mit 36 Netzen und den Regeln der Abgabe, Training, Testverfahren, Projektstruktur, Nutzung, Battle-Abgabe mit Absturzschutz und `--half`-Rückfall, Grenzen. Die historischen Ergebnisse (Review 16.10., Ablation 10.10.) stehen in einem eigenen Abschnitt.
- **Prüfungen:** alle Zahlen gegen Übernahmeberichte, CLAUDE.md, Arbeitsstand, Entscheidungsmessung und die gespeicherten Configs abgeglichen, dabei zwei eigene Formulierungen korrigiert (`sap_still` gilt nur für Halter-Saps; Nebel-Meidung erst ab geschätztem Abzug 25). Alle relativen Links und Anker automatisch geprüft, keine Fehler.
- **`Sherlock_Entscheidungsprozess.md`:** Nachtrag V12 mit den neu gemessenen Anteilen; ein Satz, der in den Kasten des V11-Nachtrags gerutscht war, steht wieder davor.
- Datierte Berichte und Pläne bleiben als Verlauf unverändert. Besteht die laufende Bestätigung von `v13r0`, werden README („Auf einen Blick“, Fortschritt, Grenzen) und CLAUDE.md nachgezogen.
- **Nachtrag 22:15, Wunsch Mahmoud: Anzahl der Spiele** (README-Abschnitt „Umfang: Spiele und Training“, neues Skript `experiments/analysis/count_games.py`, zählt nur gespeicherte Dateien): Training 616.104 Spiele in 251 Läufen (112 neue DQN-Netze 337.904, 129 Nachtrainings 233.600, Prof-DQN 9.000, 7 PPO-Läufe 35.600), Zwischenprüfungen im Training 63.904, Bewertung 484.827 (8.549 doppelt gespeicherte Zeilen nicht gezählt), zusammen **1.164.835 Spiele**. Alle gezählten Dateien sind versioniert (244/244 `train.csv`, 7/7 `ppo.csv`, 696/696 Ergebnisdateien). Auf Wunsch („einfach alles sagen, was es gibt“) heißt der Abschnitt jetzt „Zahlen und Fakten“ und nennt zusätzlich Rechenzeit (DQN 532, PPO 29, Bewertung 574 Prozess-Stunden), 18.890 verschiedene Karten, 25 Gegner, Parameter (36 × 152.967 = 5,5 Mio.), 154 Einstellungen (91 Schalter, 33 in V12 an), Codeumfang, 7 Abgabe-Stände, 403 Commits (Mahmoud 299, Moayed 104), 138 Arbeitsstand-Einträge und 23 Testpläne.

## 31.10.2026, 21:50 Berlin – Claude Code mit Mahmoud: `v13r0` (Nebel-Sap ohne Energiereserve) zugelassen, Battle-Bestätigung läuft; Ursachensuche bei Streufaktor 0,25; neue Regel `end_sap` in Arbeit

- **Screen** (`WORKERS=12 bash scripts/battle_v13.sh admit v13r0 v13r15 v13any`, Code `98f687d`, 20:19–21:40), Dev A gepaart gegen V12:
  - **`v13r0`** (`fog_reserve` 0 statt 30): Mittel 6 86,50 statt 85,56 % (**Δ +0,94 pp** [−0,08; +1,97]), Solution_92 +0,17, **direkt gegen V12 58,5 % [55,0; 61,8]** aus 600 Spielen → **zugelassen**. Je Gegner: `league6` +2,67, `threat6` +1,33, V3 −0,67, V7 +1,33, `sol92_sq` +0,83, Solution_92 +0,17.
  - `v13r15` (Reserve 15): Δ +0,08 [−0,83; +1,00], Solution_92 +2,17 [+0,33; +4,17], direkt 53,5 % → nicht zugelassen.
  - `v13any` (`fog_any`): Δ +0,39 [−0,69; +1,50], V7 +3,67 [+0,33; +7,00], `league6` −3,00, direkt 49,2 % → nicht zugelassen.
  - Deutung: Mehr Nebel-Saps derselben Schützen (Halter) helfen, mehr Schützen (jede stehende Unit) nicht.
- **Läuft seit 21:42:** `WORKERS=12 bash scripts/battle_v13.sh confirm v13r0` (V12 und `v13r0` auf 812000–812799 gegen die 6 Gegner und default, direkt 812800–813199, Hürden `league_gates battle`). Vorher geprüft: Keine der 1.357 CSVs unter `experiments/` enthält Seeds 812000–813199. Ende etwa 0:10. Bis dahin bleibt die Abgabe **V12**, am Agenten-Code ändert sich nichts.
- **Ursachensuche „V12 gegen `league_nets6` bei Streufaktor 0,25“** (nur Messung, `scripts/mechanism_probe.py` auf den V12-Spielen von Dev A, `experiments/analysis/battle/M_V12_league6_d025.json`/`_d05.json`):
  - Befund in den 9.600 Spielen der V12-Bestätigung: gegen `league_nets6` bei 0,25 nur 65,5 %, bei 0,5/1,0 81,1/86,2 % (Dev A 61,5/75,8/81,9 %). Bei allen anderen Gegnern liegen die Streufaktoren höchstens 5 Punkte auseinander.
  - Mechanismus: Bei 0,5 hält unser Streuschaden (926 statt 507 je Match) die Energie des Gegners niedrig, er sappt nur 21,8 statt 29,5 Mal je Match. Bei 0,25 ist das Schussduell ausgeglichen: Schaden je Sap 41,6 bei 40 Kosten, Abschüsse je Sap 0,32 auf beiden Seiten. Verlorene Matches sind verlorene Schussduelle.
  - Alle naheliegenden Regeln für 0,25 wurden früher schon getestet und schadeten: aggressivere Artillerie −6,5 bei 0,25, `idle_sap` −9,5, Ausweichen gegen RL-Gegner −1 bis −3, `sap_still_all`, `energy_pref`. Daraus folgt keine neue Regel.
- **Neuer Hebel: Restenergie am Matchende** (Probe `experiments/analysis/battle/v12_end_probe.py`, V12 auf Dev A 800000–800029, beide Seiten, gegen `league_nets6` und Solution_92, 120 Spiele, Daten `v12_end_*.csv.gz`): Die Engine entfernt am Matchende alle Units (`luxai_s3/env.py`), Restenergie zählt nur bei Punktgleichstand. Bei Schritt 99 haben unsere Units im Mittel etwa 1.100 Energie je Match (Median 850–920). In den letzten 10 Schritten gibt es 14–20 Unit-Schritte je Match mit Energie und sichtbarem Gegner in Reichweite ohne Sap; im letzten Schritt schießen nur 25 % der möglichen. Verlorene Matches gegen `league_nets6` gehen zu 14–21 % mit höchstens 5 Punkten verloren; 1.123 der 1.240 Niederlagen der V12-Bestätigung endeten 1:2.
- **Neue Regel `end_sap`** (Standard aus), gebaut in einer Arbeitskopie, nicht im Projektordner, weil die Bestätigung läuft: In den letzten `end_sap` Schritten schießen Units auf sichtbare Gegner, zuerst auf Halter, jeweils den mit der geringsten Restenergie nach den geplanten Saps. Eigene Halter behalten eine Sap-Kosten Energie (außer im letzten Schritt), Units, die ein Punkte-Tile noch rechtzeitig erreichen, laufen weiter. 5 neue Tests bestehen. Probe auf 16 Spielen: gegen Solution_92 +4 Saps und −3 Gegnerpunkte je Spiel. Übernahme in den Hauptstand und ein Test erst nach der Bestätigung.

## 31.10.2026, 20:25 Berlin – Claude Code mit Mahmoud: V12 gegen schwächere Gegner, Rückfall-Zip geprüft, Test „öfter im Nebel schießen“ läuft

- **V12 gegen schwächere Gegner** (nur Information, Dev A 800000–800299, je Gegner 600 Spiele, `experiments/compare/battle/D_v12_weak.csv`): DQN-Beispiel der Kursvorlage, Rush-Bot und Zufallsspieler je **600/600**, `sol92_sqweak` 90,2 % (V11 87,7 %, V10 79,2 %, Eintrag 30.10., 13:45). Damit ist der offene Punkt aus dem V12-Übernahmebericht erledigt.
- **Rückfall-Zip `--half`** für den Fall, dass Moodle 22 MB ablehnt (nur im Scratchpad gebaut, nicht im Projektordner): 10,7 MB, „Check ok“ in beiden Ordnerlagen. Die 3 mit der Zip von 17:07 aufgezeichneten Spiele nachgespielt: **1 abweichende Aktion von 1.818** (Karte 4242, Schritt 294), gleich unter Python 3.14.6 und Python 3.10.15 mit torch 2.2.2/numpy 1.26.4. Bei Bedarf baut `python -m scripts.build_submission --battle --half` sie unter demselben Namen `Gruppe15.zip` (ersetzt dann die volle Fassung).
- **Läuft seit 20:19:** `WORKERS=12 bash scripts/battle_v13.sh admit v13r0 v13r15 v13any` (Code `98f687d`, [Plan-Nachtrag 20:10](superpowers/plans/2026-10-29-battle-push.md)): Nebel-Sap mit Reserve 0 bzw. 15 statt 30 und für jede stehende Unit. Ende etwa 21:40. Abgabe unverändert **V12**, Upload-Datei `Gruppe15.zip` von 20:07.

## 31.10.2026, 20:10 Berlin – Claude Code mit Mahmoud: Absturzschutz für die Battle-Abgabe, `Gruppe15.zip` neu gebaut (spielt identisch)

- **Grund:** Der Kurs-Runner (`lux/runner.py`, Zeile 178) ruft `act()` und bei `train=True` auch `update()` ohne Fehlerbehandlung auf. Ein einziger unerwarteter Fehler in Sherlock würde das Battle-Spiel abbrechen. In unseren Testspielen ist das nie passiert, aber im Battle gibt es keinen zweiten Versuch.
- **Änderung** (`agents/sherlock/main.py`): Nur mit `cfg.frozen` fangen `act()` und `update()` Fehler ab; `frozen` setzt allein `build_submission --battle` in der Zip. Die Units bleiben dann einen Schritt stehen, die erste Meldung samt Traceback geht einmal nach stderr, `caught_errors` zählt mit. Im nächsten Schritt spielt der Agent normal weiter. Ohne `frozen` (Training, alle Messungen, die installierten Abgabe-Gewichte) werden Fehler wie bisher weitergereicht.
- **Prüfungen:**
  - 3 neue Tests in `tests/test_crash_guard.py`: Eingefroren stehen alle Units, es gibt eine Meldung, und der Zähler steht nach 2× `act` und 1× `update` auf 3. Nach einem einmaligen Fehler kommt wieder der normale Nebel-Sap. Ohne `frozen` kommt der Fehler durch. Gegenprobe mit dem alten Code: alle 3 scheitern. **Ganze Suite: 604 bestanden**, 14 Untertests.
  - `Gruppe15.zip` neu gebaut (20:07, 22,2 MB), „Check ok“ in beiden Ordnerlagen, auch mit `train=True` eingefroren. `Gruppe15/agent.pth` ist bytegleich mit der Zip von 17:07 (SHA-256 `17477a98…`), alle 15 Python-Dateien sind bytegleich mit `agents/sherlock/`.
  - **Spielt identisch:** 3 ganze Spiele mit der alten Zip von 17:07 aufgezeichnet und mit der neuen Zip nachgespielt. Karten: 800004 mit Sicht 1, 4242, 800009 mit Sicht 2 und Streufaktor 0,25; je 303 Schritte, Sherlock gegen Sherlock wie im Kurs-Runner mit `train=True`. Geprüft in der Projektumgebung (Python 3.14.6) und unter Python 3.10.15 mit torch 2.14.1/numpy 2.2.6 sowie torch 2.2.2/numpy 1.26.4: jeweils **0 abweichende Aktionen**.
- **Abgabe:** Gewichte unverändert V12 (`b258dc99…`). **Hochzuladen ist die neue `Gruppe15.zip` von 20:07.** Die Zip von 17:07 spielt gleich, hat den Schutz aber nicht.

## 31.10.2026, 20:05 Berlin – Claude Code mit Mahmoud: bessere Zielwahl für den Nebel-Sap bringt im Spiel nichts, V12 bleibt

- **Screen** (`WORKERS=12 bash scripts/battle_v13.sh admit v13p v13pd`, Code `5a5510f`, 18:50–19:59), Dev A 800000–800299, je Gegner 600 Spiele, gepaart gegen V12 auf denselben Karten:
  - `v13p`: Mittel über 6 Gegner 85,64 statt 85,56 % (Δ +0,08 pp [−0,53; +0,69]), Solution_92 +1,00 [−0,33; +2,33], direkt gegen V12 50,7 % [48,0; 53,3] aus 600 Spielen → **nicht zugelassen**.
  - `v13pd`: Mittel 85,64 % (Δ +0,08 [−0,72; +0,89]), Solution_92 +1,67 [+0,33; +3,17], direkt 50,2 % [47,2; 53,0] → **nicht zugelassen**.
  - Je Gegner (Δ pp, `v13p` / `v13pd`): Solution_92 +1,00 / +1,67, `sol92_sq` +0,83 / +0,50, V3 −1,00 / −2,00, V7 ±0 / +1,33, `league_nets6` −0,33 / −1,00, `threat6` ±0 / ±0.
- **Aufschlüsselung** (`PYTHONPATH=. .venv/bin/python experiments/analysis/battle/v13_by_param.py dev NAME`, neu): Das Ergebnis ändert sich nur in 103 bzw. 153 von 3.600 Spielen. Nach Sichtweite 1–4 liegen alle Δ zwischen −0,8 und +0,8 pp. Nach Streufaktor 0,25 / 0,5 / 1,0: −0,5 / +0,5 / +0,2 (`v13p`) und −0,7 / +0,6 / +0,3 (`v13pd`). Punkte je Spiel praktisch gleich.
- **Deutung:** Die bessere Trefferquote aus der Offline-Auswertung (34 → 41 % direkte Treffer) entscheidet kaum ein Spiel. Der Gewinn von V12 kam offenbar daher, dass im Nebel überhaupt geschossen wird, nicht von der Wahl zwischen den versteckten Feldern. Der Solution_92-Wert von `v13pd` ist nach der vorab festgelegten Regel kein Übernahmegrund: V3 und `league_nets6` verlieren im Gegenzug, das Mittel bleibt flach.
- **Folgen:** Keine Battle-Bestätigung, die Karten **812000–813199 bleiben unbenutzt**. Abgabe unverändert **V12** (`b258dc99…`), `Gruppe15.zip` vom 31.10., 17:07 unverändert. Die Schalter `fog_prior`/`fog_drop_est` bleiben im Code (Standard aus, getestet).
- Daten: `experiments/compare/battle/D_v12*.csv`, `D_v13p*.csv`, `D_v13pd*.csv`; Log `experiments/battle_dev.log`.
- **Nächster Schritt:** Absicherung gegen Abstürze im Battle. Der Kurs-Runner fängt Fehler in `act()` nicht ab; ein einziger unerwarteter Fehler würde das Spiel abbrechen.

## 31.10.2026, 18:55 Berlin – Claude Code mit Mahmoud: bessere Zielwahl für den Nebel-Sap fertig, Testlauf gegen V12 startet

- **Vorgeschichte:** Zwischen 17:40 und 17:51 haben zwei Claude-Sitzungen gleichzeitig an derselben Idee in `agents/sherlock/` geschrieben. Die eine hat ihre Zeilen wieder entfernt, die andere verlor um 17:51 den Zugriff auf den Ordner. Mahmoud hat beide Sitzungen geschlossen. Übrig war der unfertige Stand `fog_prior`/`fog_drop_est`. Ich habe ihn vollständig durchgesehen und mit der Offline-Auswertung abgeglichen.
- **Offline-Befund** (V12 auf Dev A gegen Solution_92, `sol92_sq`, `league_nets6`: 1.800 Spiele, 21.170 Nebel-Saps; Rohdaten `experiments/analysis/battle/v12_fog_hits_devA.csv.gz`, Auswertung `v12_fog_eval_devA.txt`, selbst nachgerechnet): direkte Treffer V12 34,1 %, mit Gewichten nach der letzten eigenen Beobachtung 40,6 %, Schaden je Sap 40,0 → 44,9, netto je Spiel +13 → +68. Mit sicher geschätztem Streufaktor netto +100.
- **Fehler behoben:** `belief.enemy_seen_at`/`empty_seen_at` speichern den Schritt im Match, wurden beim Matchwechsel aber nicht zurückgesetzt. Ein Gegner aus Schritt 95 des vorigen Matches hätte frischer gewirkt als eine leere Beobachtung aus Schritt 10. Jetzt in `reset_match`; die Offline-Auswertung rechnet ebenfalls je Match.
- **Prüfungen:** 3 neue Tests (`tests/test_fog_sap.py`: Zielwahl mit/ohne Gewicht, Buchführung für beide Seiten inkl. Zurücksetzen, Weitergabe des Streufaktors), **601 Tests bestanden**. V12 mit dem neuen Code (Schalter aus): 16 Spiele auf 808000–808003 (schon verbraucht) in allen Kennzahlen identisch mit der Battle-Bestätigung.
- **Kandidaten** (Netze bytegleich mit V12): `v13p` = V12 + `fog_prior`, `v13pd` = zusätzlich `fog_drop_est` (`experiments/ensembles/battle_v13p.pth`/`battle_v13pd.pth`).
- **[Plan-Nachtrag 18:50](superpowers/plans/2026-10-29-battle-push.md)** vor jeder Messung: Screen auf Dev A gegen V12 (Zulassung Mittel 6 ≥ +0,5 pp, direkt ≥ 50 %, Solution_92 ≥ −1,0 pp), dann genau eine Battle-Bestätigung auf den frischen Karten **812000–813199** mit den unveränderten Hürden. Neues Skript `scripts/battle_v13.sh` (Referenz V12, Auswertungsteil an den vorhandenen `v11fog`-Daten gegengeprüft: gleiche Zahlen wie im Eintrag 15:10).
- **Läuft:** `WORKERS=12 bash scripts/battle_v13.sh admit v13p v13pd`, etwa 1 Stunde. Abgabe unverändert **V12** (`b258dc99…`), `Gruppe15.zip` von 17:07 unverändert.

## 31.10.2026, 17:20 Berlin – Claude Code mit Mahmoud: Präsentation 06.11. auf V12 umgestellt

- **Entscheidungsstatistik für V12 neu gemessen** (`python -m scripts.decision_trace`, dieselben 10 Diagnosespiele 690000–690004, `experiments/analysis/decision_trace_20261031_v12.json`): 36.204 Entscheidungen; wie die Netze 91,2 % (V11 92,3), Regeln ändern 8,3 % (7,5). Mehr Eingriffe kommen vor allem von `pt_sap` (1,3 statt 0,5 %) und `art_sap` (0,6 statt 0,35 %), weil 4 der 5 Karten den Streufaktor 0,5 haben. Der Nebel-Sap greift hier nur bei 0,1 %, denn diese Karten haben Sichtweite 2–4. `decision_trace.py` zählt `fog_sap` jetzt als eigene Regel; die 4 Tests in `tests/test_decision_trace.py` bestehen.
- **Folien** (`docs/presentation/Sherlock_Battle_06-11-2026.html`, PDF im Projektordner neu gebaut, 16 Seiten; Seiten 9 und 11–14 als Bild geprüft):
  - Folie 9: 91 % statt 92 %, Regelanteile neu, Hinweis auf den Nebel-Sap.
  - Folie 11 heißt jetzt „Neu seit letzter Woche: V11 und V12“. Links V11 kurz, rechts V12 mit Tabelle nach Sichtweite (V11 → V12: 77,2 → 85,6 / 79,7 → 86,4 / 82,8 → 88,1 / 84,7 → 88,2 %, Mittel über 6 Gegner). Unten das Ergebnis der Battle-Bestätigung.
  - Folie 12: Punkt 2 nennt V12 (+5,9 Punkte durch Fehlersuche), Punkt 3 nennt die bestandene Hürde.
  - Folie 13: Replay-Hinweis auf Schüsse bei kleiner Sicht.
  - Reservefolie 14: Ergebnis der letzten Prüfung.
- **Stichpunkte** (`Sherlock_Stichpunkte_06-11-2026.md`): Sprechtext zu Folien 9, 11, 12 und 13 neu. Zeitplan 9:40 (Mahmoud 4:30, Folie 11 1:10). Neue Rückfragen: warum die 50-%-Regel jetzt in V12 ist, woher Sherlock unsichtbare Gegner kennt, was der Fehler war. Belege für V12 ergänzt. Der Moodle-Text ist unverändert.
- **Offen für das Team:** Moayed prüft die Folien 1–5, 10, 12 und 13. Zweimal mit Uhr proben. Mahmoud lädt am 04.11. `Gruppe15.zip` hoch (Stand 31.10., 17:07, V12).

## 31.10.2026, 17:15 Berlin – Claude Code mit Mahmoud: **V12 bestanden und als Abgabe übernommen**

- **Battle-Bestätigung V12** (`BLOCK=3 WORKERS=14 bash scripts/battle_confirm.sh v12`, Code `96a4833`, 15:08–17:06), Karten 808000–808799, je Gegner 1.600 Spiele, gepaart gegen V11:
  - **Mittel über die 6 Gegner 87,08 statt 81,19 % (Δ +5,90 pp [+4,75; +7,08])**, Hürde +1,0;
  - **Solution_92 94,38 statt 93,00 %** (Δ +1,38 [+0,06; +2,75]);
  - default 99,88 % (±0);
  - **direkt gegen V11 61,0 % [57,75; 64,38]** aus 800 Spielen auf 808800–809199.
  - `GATE Battle-Bestaetigung: BESTANDEN` in `experiments/pipeline_battle_gate.log`.
- **Je Gegner** (V11 → V12): `sol92_sq` 85,1 → 89,3, V3 83,4 → 88,9, V7 70,6 → 79,8, `league_nets6` 66,4 → 77,3, `threat6` 88,8 → 93,0. Jeder Gegner ist mit unterer Grenze > 0 besser.
- **Nach Sichtweite** (Mittel 6): 1 +8,4, 2 +6,7, 3 +5,2, 4 +3,5 pp. Nach Streufaktor 0,25 / 0,5 / 1,0: +1,8 / +8,8 / +7,1. Umkämpfte Relics nahe der Mittellinie +9,3, sonst +2,0. V12 sappt 101,5 statt 83,8 Mal je Spiel.
- **Übernahme** nach Plan-Nachtrag 14:40 und der Freigabe vom 20.10. mit `scripts/release_candidate.py` (Probelauf, dann echt, 17:07):
  - V11 bytegleich gesichert in `experiments/releases/20261031_v11_mix36c_as/` (Manifest, Wiederherstellungsanleitung).
  - Beide Abgabe-Dateien jetzt SHA-256 `b258dc9927a7094f3d4b83bf4de251b03c3ccc57d69a1da23080c27e806c924b`, Manifest `experiments/releases/20261031_v12_fog.json`.
  - Kurs-Runner: 8 Spiele bestanden, `act` im Median 5,5 ms, höchstens 8,7 ms.
- **Prüfungen danach:**
  - Testsuite: 598 bestanden, 14 Untertests.
  - `Gruppe15.zip` neu gebaut (17:07, 22,2 MB, „Check ok“ in beiden Ordnerlagen, auch mit `train=True` eingefroren). `Gruppe15/agent.pth` hat dieselben Tensoren und dieselbe Config wie die Abgabe, nur `frozen=True`. Alle 15 Python-Dateien sind bytegleich mit `agents/sherlock/`.
  - Nachspielen unter Python 3.10 (torch 2.14.1/numpy 2.2.6 und torch 2.2.2/numpy 1.26.4): Karten 800004 (Sicht 1) und 4242, **0 abweichende Aktionen**. In diesen Spielen gab es 20 bzw. 4 Saps auf Felder außerhalb des Sensors.
- [Übernahmebericht](../experiments/analysis/release_20261031_v12/RELEASE.md). CLAUDE.md „Aktuelle Abgabe“ ist aktualisiert.
- **Seeds:** 808000–809199 sind jetzt verbraucht. Unbenutzt sind noch 809200–809599 und 810000–810399.
- **Offen:** Folien 11, 12 und 14, Sprechtext und Rückfragen auf V12 bringen (folgt im nächsten Eintrag). Upload am 04.11.: `Gruppe15.zip` wie gehabt; die Zip vom 30.10. ist überholt.

## 31.10.2026, 15:10 Berlin – Claude Code mit Mahmoud: Nebel-Sap `fog_v2` auf Dev A klar besser, V12 in der letzten Prüfung

- **Screen `v11fog`** (V11 + `fog_sap` + `fog_v2`, Dev A gepaart gegen V11, 14:37–15:07): **Mittel über 6 Gegner 84,61 statt 81,83 % (Δ +2,78 pp [+1,25; +4,36])**, **direkt gegen V11 57,8 % [54,3; 61,5]** aus 600 Spielen.
  - Je Gegner (Δ pp): Solution_92 ±0 [−2,0; +2,0], `sol92_sq` +5,00 [+2,50; +7,67], V3 +1,67, V7 +2,00, `league_nets6` +4,33 [0,00; +8,67], `threat6` +3,67 [+0,67; +6,67].
  - Nach Sensorreichweite: 1 +3,0 [−0,7; +6,7], **2 +7,0 [+3,4; +11,5]**, 3 +1,5, 4 −0,6. Die Wirkung liegt also wie erwartet bei schlechter Sicht.
  - Nach Plan-Nachtrag 14:40 aufgenommen (≥ +0,5 pp, direkt ≥ 50 %, Solution_92 ≥ −1,0 pp). Die alte Hürde (+1,0 und 52 %) wäre ebenfalls erfüllt.
- **V12** = `v11h` + `fog_sap` + `fog_v2`: `experiments/ensembles/battle_v12.pth`, SHA-256 `b258dc99…`. Die Netze sind bytegleich mit V11, die Config weicht nur in diesen vier Schaltern ab. Kurzprobe mit 8 Spielen fehlerfrei.
- Block 808000–809199 vorher geprüft: keine der 669 CSVs unter `experiments/compare/` enthält diese Seeds.
- **Läuft seit 15:08:** `BLOCK=3 WORKERS=14 bash scripts/battle_confirm.sh v12` (V11 und V12 auf 808000–808799 gegen 6 Gegner und default, direkt 808800–809199). Ende etwa 17:15, Hürden wie die Battle-Bestätigung vom 30.10. Bis dahin bleibt die Abgabe **V11**.

## 31.10.2026, 14:40 Berlin – Claude Code mit Mahmoud: letzter Anlauf V12, Schwachstelle Sicht 1, Fehler im Nebel-Sap behoben (`fog_v2`)

- **Auftrag Mahmoud (14:20):** Sherlock so stark wie möglich machen. Mehr Netztraining bringt nach Runde 4 nichts Messbares, deshalb gezielt an der größten Schwachstelle.
- **Stärke V11 zum Vergleich** (Dev A, 600 Spiele je Gegner): DQN der Kursvorlage 100 %, Rush-Bot 100 %, default 99,7 %, Solution_92 94 %. Nur unsere älteren Sherlock-Versionen holen Spiele (68–87 %).
- **Schwachstelle Sicht 1** (Daten der verbrauchten Battle-Bestätigung, je Gegner 1.600 Spiele):
  - V11 gegen Solution_92 87,9 % statt 94,9–97,0 % bei Sicht 3/4, gegen V3 72,4 % statt 88,7–88,8 %;
  - V11 sappt dort nur 53 statt 89–100 Mal je Spiel.
  - Funktionsprobe auf 4 Karten (`experiments/analysis/battle/v11_fog_probe.py`): 97 % der gegnerischen Halter-Schritte sind unsichtbar. Je Spiel stehen 28–343 Mal unsichtbare Halter in Sap-Reichweite einer Unit mit genug Energie, dort sappt V11 nie.
- **Fehler in der alten Regel `fog_sap`:** Mit `use_symmetry` zählt das Spiegelbild des Sensors als gesehen. Die gegnerischen Punkte-Tiles sind das Spiegelbild unserer, fielen deshalb aus den Kandidaten, und die Regel schoss kaum. Das erklärt die Nullergebnisse vom 20.–22.10.
- **Neu: Schalter `fog_v2`** (Standard aus): echte Sicht, Kandidaten in beiden Hälften ohne eigene Unit, kein Nebel-Sap bei sichtbarem Ziel.
  - Prüfungen: 3 neue Tests (`tests/test_fog_sap.py`), alle 594 Tests bestanden, 6 V11-Spiele identisch zum Stand der Battle-Bestätigung.
  - Mit `fog_v2` sappen die Halter auf denselben Karten in 7–33 % dieser Gelegenheiten.
- **[Plan-Nachtrag 14:40](superpowers/plans/2026-10-29-battle-push.md)** (vor jeder Messung festgelegt):
  - Screen `battle_v11fog` (V11 + `fog_sap` + `fog_v2`, SHA-256 `64eb1620…`) auf Dev A gegen V11.
  - Aufnahme in V12 bei Mittel über 6 Gegner ≥ +0,5 pp, direkt ≥ 50 % und Solution_92 ≥ −1,0 pp.
  - V12 = `v11h` + Nebel-Regel, einmalige Prüfung auf 808000–809199 mit den Hürden der Battle-Bestätigung, spätester Start 03.11., 12:00.
- **Läuft:** `WORKERS=12 bash scripts/battle_admit.sh v11fog`, etwa 1 Stunde. Abgabe unverändert **V11**.

## 31.10.2026, 01:05 Berlin – Claude Code mit Mahmoud: Battle-Bestätigung `v11h` knapp nicht bestanden, **V11 bleibt**

- **Ergebnis** (`scripts/battle_confirm.sh v11h`, Code `e3195de`, 23:01–01:02): Karten 810400–811199, je Gegner 1.600 Spiele, gepaart gegen V11. **Mittel über die 6 Gegner 81,74 statt 80,79 % (Δ +0,95 pp [+0,33; +1,57])**. Die Hürde lag bei +1,0 pp und ist damit um 0,05 pp verfehlt. Alle übrigen Bedingungen sind erfüllt:
  - untere Grenze > 0;
  - Solution_92 93,25 % (Δ +0,06 [−0,44; +0,56]);
  - default 99,69 % (±0);
  - **direkt gegen V11 55,0 % [52,25; 57,63]** aus 800 Spielen auf 811200–811599.
  - `GATE Battle-Bestaetigung: NICHT BESTANDEN` in `experiments/pipeline_battle_gate.log`.
- **Je Gegner** (Δ in pp): Solution_92 +0,06, `sol92_sq` +0,38, V3 +1,00, V7 +1,38, `league_nets6` +2,12 [+0,12; +4,25], `threat6` +0,75, default ±0. Kein Gegner ist schlechter.
- **Nach Streufaktor** (Kartenparameter neu in `experiments/analysis/battle_params_20261030/map_params_810400.csv`):
  - 0,25: +0,03, direkt 50,4 %;
  - **0,5: +2,81 [+0,95; +4,67], direkt 64,2 % [56,9; 71,5]**;
  - 1,0: +0,03, direkt 50,0 %.
  - Die Halbstreuung wirkt also genau dort, wo sie es auf Dev A tat, und sonst ändert sich nichts. Weil nur ein Drittel der Karten den Streufaktor 0,5 hat, bleibt im Gesamtmittel knapp +1 pp.
- **Entscheidung nach Nachtrag 23:01:** V11 bleibt, kein weiterer Versuch auf diesem Block. `scripts/release_candidate.py` würde `v11h` ohnehin abweisen. Eine Übernahme wäre nur als ausdrückliche Teamentscheidung gegen die vorab festgelegte Hürde möglich; Claude Code übernimmt nicht selbstständig.
- **Seeds:** 810400–811599 sind jetzt verbraucht. Unbenutzt sind noch 810000–810399 und Runde 3 (808000–809599).
- **Daten:** `experiments/compare/battle/GB_V11_conf.csv`, `GB_v11h_conf.csv`, `GB_v11h_confdir.csv`.
- **Abgabe unverändert V11** (`2ab463e9…`, beide Dateien um 01:05 geprüft), `Gruppe15.zip` vom 30.10., 13:38 unverändert.
- **Präsentation (01:09):** Das Ergebnis steht auf Folie 11 (unten), Folie 12 (Punkt 3: zwei knapp verfehlte Hürden, beide nicht übernommen) und Reservefolie 14 (Hürde der Battle-Prüfung). Stichpunkte: Sprechtext zu Folie 11/12, neue Rückfrage „Warum nehmt ihr die Regel für 50 % nicht?“, Beleg. `Sherlock_Battle_06-11-2026.pdf` ist neu gebaut (16 Seiten); die Seiten 11, 12 und 14 habe ich als Bild geprüft.
- **Upload 04.11.:** Der Text steht in `Sherlock_Stichpunkte_06-11-2026.md` unter „Für Moodle“. `Gruppe15.zip` habe ich um 01:08 geprüft: `Gruppe15/agent.pth` hat dieselben 36 Netze (Tensoren identisch) und dieselbe Config wie die Abgabe, nur `frozen=True`, wie es `build_submission --battle` vorsieht.
- Weitere Agent-Experimente sind nach Mahmouds Auftrag („nur das Wichtigste“) nicht geplant.

## 30.10.2026, 23:01 Berlin – Claude Code mit Mahmoud: weiter nach der Pause; `v11h` (Halbstreuung mit Sicherheitsprüfung) zugelassen, Battle-Bestätigung auf frischen Karten läuft

- Auftrag Mahmoud (22:09): nur noch das Wichtigste, was weiterbringt. Deshalb **entfällt Runde 5** (Runde 4 brachte im Ensemble nichts), ebenso `V11_dropest` und `V11_rescue`. Die alten Zeilen der Warteschlange sind als erledigt markiert, der Poller läuft nicht.
- **Zulassung `v11e` fertig** (Dev A, gepaart gegen V11): Mittel über 6 Gegner +0,89 pp, direkt gegen V11 54,0 % → nicht zugelassen. Je Streufaktor: Ausweichen (0,25) im Mittel ±0 und direkt 47,4 %, Halbstreuung (0,5) +2,6 und direkt 64,6 %. Das Ausweichen fällt deshalb weg.
- **`V11_halfsafe`** = V11 + `splash_min_drop=0.5` + `splash_safe_below=1.0` (Dev A gegen V11, alle 6 Gegner und direkt): Solution_92 +0,33, `sol92_sq` +2,17 [+0,67; +3,83], V3 +0,67, V7 −0,67, `league_nets6` +4,00 [+0,33; +7,67], `threat6` ±0; **Mittel 6 +1,08 pp [−0,08; +2,39]**, **direkt 55,5 % [52,8; 58,3]**. Bei Streufaktor 0,5 +3,5 (`league_nets6` +13,1, `sol92_sq` +6,1), direkt 65,7 %. Ohne Sicherheitsprüfung (Messung vom Nachmittag) +0,78, Solution_92 −0,50.
- **Neu:** `python -m scripts.league_gates battle` (Mittel über die 6 Screen-Gegner statt R, sonst dieselben Bedingungen wie die Bestätigung; neuer Test, 10 Gate-/Screen-Tests bestanden), `scripts/battle_confirm.sh`, Runde 4 in `scripts/pipeline_battle_gate.sh` gesperrt. [Plan-Nachtrag 23:01](superpowers/plans/2026-10-29-battle-push.md): `v11h` geht statt in Runde 3 in eine Battle-Bestätigung auf 810400–811599. Vorher geprüft: Keine der 657 CSVs unter `experiments/compare/` enthält diese Seeds.
- Bündel `experiments/ensembles/battle_v11h.pth` (SHA-256 `13c73cce…`, V11-Netze, Config V11 + die beiden Schalter) und `battle_v11f.pth` (`v11e` + Sicherheitsprüfung, wird nicht geprüft).
- **Läuft:** `WORKERS=14 bash scripts/battle_confirm.sh v11h`, etwa 2 Stunden, Ergebnis in `experiments/pipeline_battle_gate.log`. Bis dahin bleibt die Abgabe **V11**.

## 30.10.2026, 20:48 Berlin – Claude Code mit Mahmoud: **Pause** (Akku leer, Mac soll abkühlen) – Stand gesichert, Weitermachen erst auf Mahmouds Zeichen

**Um 20:46 auf Mahmouds Wunsch gestoppt:** Training Runde 5, Zulassungstest `v11e`, Warteschlange (`scripts/battle_queue.sh`) und `caffeinate`. Es läuft nichts mehr.

- **Runde 5 (abgebrochen):** Nur die erste Welle lief (s10–s15, je 1.425–1.450 von 2.000 Spielen, Ordner `experiments/runs/20261030_ft5_v10_s10`–`s15`; dort `weights/agent.pth` vom letzten Zwischenstand, `val.csv` bis 1.000 Spiele). s16–s27 sind nicht gestartet, `battle_ft5_18`/`mix36e_as`/`mix54e_as` gibt es nicht. Zum Weitermachen: die sechs angefangenen Ordner zur Seite legen oder löschen (sie haben keinen Status „done“), dann `bash scripts/pipeline_battle_ft5.sh` neu starten. Alternativ Runde 5 auslassen, denn Runde 4 brachte im Ensemble nichts.
- **Zulassung `v11e` (abgebrochen):** fertig ist nur der Teil gegen Solution_92/`sol92_sq` (`experiments/compare/battle/D_v11e.csv`, 1.200 Spiele): **`sol92_sq` +2,33 pp [+0,83; +4,00]**, Solution_92 ±0 gegen V11. Es fehlen die RL-Gegner und das Direktduell. `WORKERS=14 bash scripts/battle_admit.sh v11e` überspringt den fertigen Teil und macht den Rest.
- **Offene Warteschlange** (`experiments/battle_queue.txt` hinter `battle_admit.sh v11e`): `V11_halfsafe` (Halbstreuung mit Sicherheitsprüfung, `splash_min_drop=0.5 splash_safe_below=1.0`), `V11_dropest`, `V11_rescue`. Die Zeile für `V11_halfsafe` zeigt noch auf die Arbeitskopie im Scratchpad. Der Code ist jetzt im Hauptstand, deshalb dort `REF=V11 bash scripts/battle_dev.sh V11_halfsafe …` verwenden. Neustart der Schlange: `bash scripts/battle_queue.sh`.
- **Neu im Hauptstand** (Standard aus): `splash_safe_below` (Artillerie behält bei Halbstreuung die Sicherheitsprüfung, gegen die −1,5 pp gegen Solution_92 bei Streufaktor 0,5). Test in `tests/test_art_splash.py`, Regeltests 99 bestanden.
- **Messung Trefferquote des Gegnermodells** (je 16 Spiele, `experiments/analysis/battle/v11_pred_probe.csv`): Solution_92 70 %, V7 68 %, `sol92_sq` 65 %, `league6` 58 %, `sol92_weak` 51 %. Das Modell trifft also auch gegen RL-Gegner oft. `dodge_distrust=0.35` wird dort kaum abschalten, `v11e` dürfte sich gegen RL-Gegner wie `v11b` verhalten.
- **Messung Schussgelegenheiten** (`v11_fire_probe_sq.csv`, 48 Spiele gegen `sol92_sq`): Einheiten mit Energie ≥ Sap-Kosten und sichtbarem Gegner in Reichweite schießen nur in 10–21 % der Fälle. Halter schießen in 22–35 % ihrer Gelegenheiten, Nicht-Halter fast nie (bei 0,5 in 1,6 %).
- Analyseskripte gesichert unter `experiments/analysis/battle/v11_*.py`. Aufruf: `PYTHONPATH=$PWD:$PWD/experiments/analysis/battle .venv/bin/python -m v11_fire_probe …`.
- **Nächste Schritte, wenn es weitergeht:** (1) Zulassung `v11e` fertig rechnen; (2) `V11_halfsafe` messen und daraus ggf. `v11f` bilden (Ausweichen bei 0,25 + Halbstreuung mit Sicherheit + ggf. `splash_dodge`); (3) über Runde 5 entscheiden; (4) zugelassene Kandidaten in Runde 3 (808000–809599) bzw. Runde 4 (810000–811599) gegen V11.
- Abgabe unverändert **V11** (`2ab463e9…`). Mac: `caffeinate` ist aus, vor langen Läufen wieder starten (`caffeinate -i -s -t 540000 &`).

## 30.10.2026, 20:30 Berlin – Claude Code mit Mahmoud: `v11b` knapp nicht zugelassen, Ursache gefunden, `v11e` mit Schutzschaltung in der Zulassung

- **Zulassung `v11b`** (Dev A gepaart gegen V11, `scripts/battle_admit.sh`): Mittel über 6 Gegner 82,69 statt 81,83 % (**+0,86 pp** [−0,31; +2,11], Hürde +1,0), direkt gegen V11 **54,3 %** (Hürde 52 %) → **nicht zugelassen**. Je Gegner: Solution_92 ±0, `sol92_sq` +2,5, V3 ±0, V7 +0,7, `league6` +3,7, `threat6` −1,7. Direkt gegen V10 74,3 % (V11 67,7 %).
- **Nach Streufaktor** (gegen V11): bei **0,5** (Halbstreuung) +2,6 im Mittel, `league6` +11,1, V7 +4,0, `sol92_sq` +3,0, direkt gegen V11 64,6 %. Bei **0,25** (Ausweichen) gegen die Solution_92-Familie +4,2 / +1,6, gegen die RL-Gegner aber −1 bis −3 (V3 −1,0, V7 −2,1, `threat6` −3,1), direkt 48,4 %. Das Modell sagt die Schüsse von RL-Agents falsch voraus, die Einheiten weichen umsonst aus. Bei 1,0 keine Änderung.
- **Neu im Hauptstand** (Commit `c967cf4`, Standard aus, 32 V11-Spiele identisch):
  - **`dodge_distrust`**: Das Gegnermodell gilt zunächst. Es wird für den Rest des Spiels abgeschaltet, wenn nach mindestens 6 stehen gebliebenen vorhergesagten Zielen weniger als dieser Anteil direkt getroffen wurde. Das gilt auch für das Streu-Ausweichen.
  - **`splash_dodge`**: Bei sicher geschätztem Streufaktor ≥ 0,5 treten Einheiten neben einem vorhergesagten Ziel aus dem Streuschaden und laufen nicht zurück hinein, solange die Gefahr besteht. Diagnose: In verlorenen Matches ist der Streuschaden auf uns dreimal so groß wie der direkte Schaden (bei 1,0: 2.016 zu 651).
  - 4 neue Tests, Regeltests 98 bestanden.
- **Bündel `v11e`** = `v11b` + `dodge_distrust=0.35` (`experiments/ensembles/battle_v11e.pth`, SHA-256 `49eaf3ea…`) ersetzt `v11c` (Köder) in der Zulassung, denn der Köder würde gegen RL-Gegner noch öfter umsonst ausweichen. Vorher läuft der Test `splash_dodge` gegen Solution_92/`sol92_sq`.
- Abgabe unverändert **V11**.

## 30.10.2026, 19:21 Berlin – Claude Code mit Mahmoud: Neue Regeln auf V11 getestet, Bündel `v11b` geht in die Zulassung

Alle Werte auf Dev A (800000–800299, je Gegner 600 Spiele), gepaart gegen die V11-Spiele derselben Karten; nur Entwicklung.

| Variante (V11 + …) | `sol92_sq` | Solution_92 | Bemerkung |
|---|---|---|---|
| `stage_attack` | +0,33 [+0,00; +0,83] | ±0 | greift kaum |
| `art_safe_cheb` | +0,83 [−0,83; +2,50] | +0,33 | n. s. |
| `dodge_auto` + **`dodge_shape`** (neu) | +1,00 [−0,33; +2,50] | +0,83 [−0,33; +2,17] | Gewinn bei Streufaktor 0,25 (+4,2 / +1,6), bei 0,5 −1,5 / ±0 |
| dasselbe mit `dodge_mode=always` | +1,33 [−1,00; +3,50] | +0,33 | ähnlich, mehr Streuung |
| dasselbe mit `dodge_verify` | +0,17 | +0,33 | zu vorsichtig |
| **dasselbe nur bei Streufaktor 0,25** (`dodge_auto_max=0.25`) | **+1,33 [+0,50; +2,50]** | +0,50 [−0,33; +1,33] | nur 15 von 1.200 Spielen ändern sich, alle auf 0,25-Karten |

- **`dodge_shape`** (Commit `a912b9f`, Standard aus): Das Gegnermodell für das Ausweichen sagt die Ziele für Raute und Quadrat voraus. Wird eine Einheit getroffen, die nur eine der beiden Formen als Ziel hatte und stehen blieb, zählt das für diese Form; das Quadrat gilt, sobald es mehr Treffer hat. Auch die Köder-Reichweite (`dodge_bait`) folgt dem Modell. 5 neue Tests, darunter eine Gegenprobe, dass der Ködertest die alte Manhattan-Reichweite erkennt.
- **`splash_min_drop`** (Commit `a912b9f`, Standard 1,0 = V11): R auch bei sicher geschätztem Streufaktor 0,5. Auf Dev A (Messung vom Nachmittag) Mittel über 6 Gegner +0,8 pp [−0,2; +1,9], nach Streufaktor: 0,25 −0,4, **0,5 +2,6** (`sol92_sq` +3,0, Solution_92 −1,5, V7 +4,0, `league6`/`threat6` zusammen +4,5), 1,0 +0,1.
- Mit beiden Schaltern aus spielt der neue Code 48 V11-Spiele identisch nach (Ergebnis, Punkte, Saps, bekannte Felder, Einheitenschritte). Regeltests 94 bestanden.
- **Bündel `v11b`** = V11-Netze und -Config + `dodge_auto` + `dodge_shape` + `dodge_auto_max=0.25` + `splash_min_drop=0.5` (`experiments/ensembles/battle_v11b.pth`, SHA-256 `a185232d…`, Netze bytegleich mit V11). Die beiden Teile wirken auf getrennten Karten (0,25 bzw. 0,5). In der Warteschlange: Zulassung nach Plan-Nachtrag 18:31 (`scripts/battle_admit.sh v11b`: 6 Gegner + direkt gegen V11). Erwartung aus den Einzelwerten etwa +1 pp im Mittel, also knapp an der Zulassungshürde. Für die Auswahlhürde von Runde 3 (R +1,5 pp gegen V11) reicht das allein vermutlich nicht.
- Weitere Tests in der Warteschlange: Köder bei 0,25 (`dodge_bait`), `sap_dropoff_est`, `dodge_auto` ohne Formerkennung, `holder_guard`, `cand_rescue`, `window_infer`, `relic_scout=1`.
- **Keine Ursache gefunden in der Punktefeld-Inferenz:** In einem nachgemessenen Verlustspiel gibt es an allen Messpunkten 0–1 offene Gleichungen, eine exakte Lösung würde nichts zusätzlich finden. Die fehlenden Felder wurden nie betreten.
- Abgabe unverändert **V11**.

## 30.10.2026, 18:36 Berlin – Claude Code mit Mahmoud: Runde 4 ohne Zulassung, Verlustanalyse V11, Runde 5 und neue Regeltests laufen

- **Runde 4 der Hauptlinie fertig** (14:21–17:05, 18 Netze je +2.000 Spiele, `ft4_18`). Einzelnetze in der Validierung gegen Solution_92 (je 16 Spiele, Mittel über 18 Netze): Ende Runde 2 77,8 %, Runde 3 81,2 %, Runde 4 83,0 %.
- **Zulassung zu Runde 3 (Dev A, gepaart gegen V11): keiner zugelassen.**

| Kandidat | Sol92 | `sol92_sq` | V3 | V7 | `league6` | `threat6` | Mittel 6 | Δ gegen V11 | direkt gegen V11 |
|---|---|---|---|---|---|---|---|---|---|
| V11 (`mix36c_as`) | 93,8 | 84,8 | 85,7 | 74,0 | 65,0 | 87,7 | 81,8 | – | – |
| `mix36d_as` (V10 + ft4_18 + R) | 92,8 | 84,3 | 87,3 | 75,3 | 68,0 | 88,0 | 82,6 | +0,81 [−1,14; +2,81] | 48,3 % |
| `mix54d_as` (V10 + ft3_18 + ft4_18 + R) | 91,5 | 84,5 | 80,0 | 75,7 | 69,0 | 86,7 | 81,2 | −0,61 [−2,64; +1,47] | 57,7 % |

- **Warum V11 noch verliert** (Dev-A-Spiele mit dem wahren Spielzustand nachgemessen, `experiments/analysis/battle/L_V11_*`, `M_V11_*`, Auswertung `v11_loss_matches.py`/`v11_loss_mechanisms.py`): Gegen `sol92_sq` gehen 91 verlorene Spiele fast immer in Match 2 und 3 verloren (Match 1 gewinnen wir dort zu 77 %). Diese Matches haben mehr Punktefelder (19–22 statt 15–17 in gewonnenen Spielen). Wir kennen am Matchende 83–84 % davon (gewonnen 96–98 %), verlieren 16–17 statt 9 Einheiten durch Energieverlust, und der Gegner feuert doppelt so oft (37–40 statt 20 Saps, Streuschaden auf uns 1.300 statt 550). Gegen `league_nets6` sind die Matches knapp (Punkte 392:441 bzw. 461:515), dort fehlen nur kleine Vorteile.
- Einzelbilder verlorener Spiele (800207, 800196, 800061) zeigen dasselbe Muster: ein umkämpfter Relic-Haufen nahe der Mittellinie, der Gegner kommt mit mehr Einheiten an und schießt unsere einzeln ab. Einmal (800061) fanden wir ein neues Relic-Paar in Match 2 gar nicht.
- **Relic-Lage** (aus dem Spielcode `luxai_s3/state.py`, 6.200 Karten): Relics sind die höchsten Werte eines Perlin-Rauschens. 59 % der neuen Paare liegen höchstens 1 Feld, 69 % höchstens 2 Felder neben einem früheren Relic oder dessen Spiegelbild. Auf Dev A übersieht V11 nahe neue Paare in 7,4 %, ferne in 17,2 % der Fälle.
- **Runde 5 der Hauptlinie läuft seit 18:31** (`scripts/pipeline_battle_ft5.sh`, Plan-Nachtrag 18:31): `ft4_18` je +2.000 Spiele, 6 parallel, Kandidaten danach `mix36e_as` und `mix54e_as`.
- **Entwicklung auf V11** (`REF=V11 bash scripts/battle_dev.sh`, Dev A gepaart gegen V11): `stage_attack` `sol92_sq` +0,33 [+0,00; +0,83], Solution_92 ±0. Es folgen `art_safe_cheb`, `dodge_auto`, `holder_guard`, `cand_rescue`, `window_infer`, `relic_scout=1` und der neue Schalter **`dodge_shape`** (in der getrennten Arbeitskopie, noch nicht im Hauptstand): Das Gegnermodell für das Ausweichen erkennt im Spiel, ob der Gegner in der Raute (Solution_92) oder im ganzen Quadrat (`sol92_sq`) schießt. 4 neue Tests bestanden, 88 bestehende Regeltests ebenfalls.
- **Neuer frischer Block für eine Runde 4** festgelegt: 810000–811599 (Plan-Nachtrag 18:31).
- Abgabe unverändert **V11** (`2ab463e9…`).

## 30.10.2026, 14:25 Berlin – Claude Code mit Mahmoud: Was V11 noch schwer fällt, Runde 4 des Nachtrainings läuft, Runde 3 gegen V11 vorbereitet

- **Wo V11 noch verliert** (Bestätigungsspiele gegen Solution_92/`sol92_sq`, 89,1 % auf 800 Karten): Sichtweite 1/2/3/4 84,6/87,3/90,2/94,4 %; umkämpfte Relics nahe der Mittellinie etwa 84 statt 94–95 %; Sap-Reichweite 6–7 86 statt 92,5 % bei Reichweite 3; 2–3 Relic-Paare 86–87 statt 93,5 %. Bei Sichtweite 1 und 2 Paaren nur 75,5 %. In 40 nachgespielten Spielen mit Sichtweite 1 kennt V11 in verlorenen Spielen im 3. Match nur etwa 84 % der Punktefelder, in gewonnenen fast alle. Die früher getestete Erkundung `relic_scout` war genau bei Sichtweite 1 schädlich, deshalb gibt es dafür keinen schnellen Ansatz.
- **Gegen RL-Gegner (Dev A):** `league_nets6` 65 % (bei Streufaktor 0,25 nur 55 %), V7 74 %, V3 85,7 %, `threat6` 87,7 %.
- **Versuche ohne Übernahme** (Dev A, gepaart gegen V11 auf denselben Karten): R auch bei Streufaktor 0,5 (`splash_min_drop=0.5`, nur in der getrennten Arbeitskopie) **+0,8 pp [−0,2; +1,9]**, bei 0,5 +2,6 [−0,8; +5,9]. Das ist nicht sicher besser und reicht nicht für die Hürde. Nicht im Hauptstand.
- **Runde 4 der Hauptlinie** läuft seit 14:21 (`scripts/pipeline_battle_ft4.sh`, Plan-Nachtrag 30.10., 14:21): die 18 `ft3`-Netze je weitere 2.000 Spiele mit V11 im Gegner-Pool, 18 parallel, Ende etwa 20–21 Uhr. Ein Probelauf (2 Spiele gegen den Pool-Gegner V11) lief fehlerfrei.
- **Runde 3 vorab festgelegt** (Nachtrag 14:21): Referenz V11 (feste Kopie `experiments/releases/20261030_v11_baseline/`, bytegleich mit der Abgabe). Kandidaten `mix36d_as` (V10 + ft4_18 + R) und `mix54d_as` (V10 + ft3_18 + ft4_18 + R). Zugelassen wird, wer auf Dev A im Mittel über 6 Gegner mindestens +1,0 pp über V11 liegt und direkt gegen V11 mindestens 52 % gewinnt. Danach Auswahl 808000–808399 und Bestätigung 808400–809599 mit unveränderten Hürden. `scripts/pipeline_battle_r3.sh` läuft und startet das automatisch nach dem Ende der Runde 4.
- **Werkzeuge** (Commit `bfdbd59`): `league_gates --direct-opponent`, `pipeline_battle_gate.sh` mit `REF`/`REFNAME` (Standard V10, für die Runden 1–2 unverändert). Tests für Gates, Screen-Tabelle, Entscheidungsdiagnose und Regeln: 16 bestanden.
- Abgabe unverändert **V11** (`2ab463e9…`).

## 30.10.2026, 13:55 Berlin – Claude Code mit Mahmoud: Präsentation 06.11. auf V11 umgestellt

- `Sherlock_Battle_06-11-2026.pdf` (Projektordner, 16 Seiten) und die Quelle `docs/presentation/Sherlock_Battle_06-11-2026.html` sind umgestellt. Geändert sind die Folien 1–4 und 6–14 sowie Folie 16: 36 statt 18 Netze, 94 statt 90 %, Schrittzeit 8,8 ms (Kurs-Runner-Prüfung nach der Installation).
- **Folie 11 neu:** Nachtraining und Mischen, verlorene Spiele nach dem verdeckten Streuschaden sortiert (V10 gegen V11 auf denselben 800 Bestätigungskarten gegen Solution_92: 25 % 91,4 → 94,5; 50 % 91,0 → 95,4; 100 % 86,7 → 92,5), die neuen Regeln und das Bestätigungsergebnis.
- **Folie 12:** Punkt 2 heißt jetzt „Erst Fehler suchen, dann passend trainieren“ (78 → 90 → 94 %). Punkt 3 nimmt als Beispiel die knapp gescheiterte Mischung (+1,8 statt +2).
- **Folie 10:** neues Diagramm `docs/presentation/folie_0611_fortschritt.png` (Skript `docs/presentation/source/fortschritt_0611.py`) mit V11 bei 94,1 %.
- **Entscheidungsstatistik für V11 neu gemessen** (`python -m scripts.decision_trace`, dieselben 10 Diagnosespiele 690000–690004 wie am 26.10., `experiments/analysis/decision_trace_20261030_v11.json`): 36.209 Entscheidungen; wie die Netze 92,3 % (V10 92,4), Regeln ändern 7,5 % (7,3), alle 36 Netze einig 30,7 % (alle 18: 31,9), Lieblingsaktion verboten 22,3 % (20,4), Mittelwert und Mehrheit verschieden 5,9 % (7,7). Die Beispiele auf den Folien 6 und 7 stammen aus diesen Spielen. Der Asteroid unter dem Maskenbeispiel ist im Spielzustand nachgeprüft (Spiel 690000, Schritt 114, Feld (0,13)). `decision_trace.py` wählt Beispiele jetzt mit Schwellen, die zur Ensemblegröße passen; Test ergänzt.
- `Sherlock_Stichpunkte_06-11-2026.md`: Sprechtexte angepasst, neue Rückfrage „Wie schätzt Sherlock den Streuschaden?“, Belege ergänzt. `Sherlock_Entscheidungsprozess.md` hat einen Nachtrag zu V11 bekommen.
- Prüfung: alle geänderten Seiten als Bild angesehen. Einen zu langen Punkt auf Folie 7 gekürzt.
- **Offen:** Moayed bitte seine Folien 1–5, 10, 12 und 13 gegenlesen (Zahlen und Punkt 2 auf Folie 12 geändert). Zweimal mit Uhr proben, Folie 11 hat etwa 1:05 Sprechtext.

## 30.10.2026, 13:45 Berlin – Claude Code mit Mahmoud: Bestätigung bestanden, **V11 `v11_mix36c_as` ist die neue Abgabe**

- **Bestätigung Runde 2** (806000–806799, je Gegner 1.600 Spiele; direkt 807000–807399, 800 Spiele; Ende 13:33): R **91,2 statt 86,6 % (Δ +4,66 pp [+3,45; +5,88])**, Solution_92 **94,1 statt 89,6 % (+4,50 [+2,88; +6,25])**, `sol92_sq` 84,1 statt 79,1, `sol92_weak` 93,8 statt 91,5, `old3_sym3` 92,9 statt 86,1, default 100 % (+0,06), **direkt gegen V10 59,5 % [54,5; 64,25]**. Alle Hürden erfüllt, „GATE Bestaetigung: BESTANDEN“.
- **Übernahme** mit `scripts/release_candidate.py` (Freigabe vom 20.10.) um 13:36. Neue Dateien `agents/sherlock/weights/agent_p0.pth`/`agent_p1.pth` SHA-256 `2ab463e9…cd2e0`. V10 liegt bytegleich mit Wiederherstellungsanleitung in `experiments/releases/20261030_v10_V8st/`, Manifest `experiments/releases/20261030_v11_mix36c_as.json`. [Übernahmebericht](../experiments/analysis/release_20261030_v11/RELEASE.md).
- **V11** besteht aus 36 Netzen: den 18 V10-Netzen und denselben 18 nach 5.500 Spielen Nachtraining unter allen V10-Regeln. Dazu kommen die Regeln `art_splash` und `sap_still_splash`. Beide greifen nur, wenn der Sap-Streufaktor sicher auf 1,0 geschätzt ist.
- **Prüfungen nach der Installation:** unveränderter Kurs-Runner 8 Spiele bestanden, `act` im Median 5,4 ms, höchstens 8,8 ms. Gesamte Testsuite ohne laufende Jobs: 576 bestanden plus 14 Untertests. `Gruppe15.zip` neu gebaut, 22,2 MB, „Check ok“ in beiden Ordnerlagen. Unter Python 3.10 (torch 2.14/numpy 2.2 sowie torch 2.2/numpy 1.26) gibt es 0 abweichende Aktionen in einem aufgezeichneten Spiel. Bei einer Moodle-Größengrenze baut `python -m scripts.build_submission --battle --half` eine 10,7-MB-Fassung. Auch sie hatte 0 Abweichungen, gemessen in den Hürden wurde aber die volle Fassung.
- **Zusatzmessungen** (Dev A, nur Information): DQN-Beispiel des Profs und Rush-Bot je 100 % (V10 ebenso), `sol92_sqweak` 87,7 statt 79,2 %.
- **Offen:**
  - Präsentation auf V11 umstellen: Folien 1, 4, 7–13 (18 → 36 Netze, 90 → 94 %) sowie Folie 11 „Neu seit letzter Woche“ mit Nachtraining, Mischung, Analyse der Verlustspiele und den neuen Regeln. Moayeds Folien 1–5, 10, 12–13 ändern sich mit, bitte gegenlesen.
  - Upload von `Gruppe15.zip` durch Mahmoud erst am Ende (04.11.). Vorher die Moodle-Größengrenze klären.
  - Runde 3 (808000–809599) nur mit einem eigenen Plan-Nachtrag. Referenz wäre jetzt V11.

## 30.10.2026, 11:55 Berlin – Claude Code mit Mahmoud: Auswahl Runde 2 wählt `mix36c_as`, Bestätigung läuft

- **Auswahl Runde 2** (805000–805199, je Gegner 400 Spiele, gepaart gegen V10; direkt 805200–805399, 400 Spiele; Log `experiments/pipeline_battle_gate.log`):

| Kandidat | R (Δ pp) | Solution_92 | `sol92_sq` | `sol92_weak` | `old3_sym3` | default | direkt | Hürden |
|---|---|---|---|---|---|---|---|---|
| V10 (Referenz) | 89,62 % | 90,75 | 83,25 | 92,5 | 92,0 | 100 | – | – |
| **`mix36c_as`** | **+2,19 [−0,25; +4,69]** | 96,0 (+5,25 [+1,75; +9,00]) | 85,0 | 95,75 | 90,5 | 100 | 65,5 % [59,0; 72,0] | **bestanden → gewählt** |
| `mix48_as` | +1,31 [−1,06; +3,69] | 95,25 (+4,50) | 82,75 | 94,75 | 91,0 | 100 | 65,75 % | R < +1,5 |
| `mixrl54_as` | +1,38 [−1,19; +3,88] | 94,5 (+3,75) | 82,75 | 94,75 | 92,0 | 99,5 | 66,0 % | R < +1,5 |

- Gegen `old3_sym3` liegt `mix36c_as` auf diesen 200 Karten 1,5 pp unter V10. Auf Dev B lag V10 + R dort bei +0,7, `mix36` auf Dev A bei −3,3. Das ist im Rahmen der Streuung, wird aber in der Bestätigung mitgemessen.
- **Bestätigung `mix36c_as` läuft seit 11:49** (806000–806799, je Gegner 1.600 Spiele; direkt 807000–807399, 800 Spiele). Ergebnis gegen 14 Uhr. Hürden: R Δ ≥ +2 pp mit unterer Grenze > 0, Solution_92 Δ ≥ −0,5 mit unterer Grenze > −2,5, default ≥ 99 % und Δ ≥ −1, direkt untere Grenze > 50 %.
- Der Gate-Log nennt je Schritt den aktuellen Commit (`fb60655`, `46232fc`, `e8904d2`). Dazwischen kamen nur Dokumentation und Messdaten dazu. `git diff fb60655 e8904d2 -- agents/ scripts/league_gates.py scripts/par_eval.py scripts/pipeline_battle_gate.sh` ist leer.
- **Dev-A-Screen von `mix36c_as`** (12:12, gepaart gegen `mix36c` auf denselben Karten, nur Entwicklung): Mittel über 6 Gegner **81,8 statt 77,8 % (+4,0 [+2,6; +5,4])**, gegen V10 +9,7 [+7,3; +12,0]; direkt gegen V10 67,7 % [62,3; 72,7]. R hilft gegen RL-Gegner mehr als gegen Solution_92: V7 +7,3 [+4,0; +10,7], `league_nets6` +6,0 [+2,7; +9,7], V3 +4,3, `threat6` +2,0, `sol92_sq` +3,3, Solution_92 +1,2. Nach Streufaktor: 0,25 ±0, 0,5 −0,2 [−0,5; 0,0], **1,0 +11,7 [+8,1; +15,2]**. Die RL-Gegner waren an der Entdeckung der Regel nicht beteiligt (sie stammt aus Dev-A-Spielen gegen Solution_92/`sol92_sq`).
- **Vorabprüfung des Kandidaten** (ohne Installation, Dateien im Arbeitsordner): Der unveränderte Kurs-Runner besteht 8 Spiele, ein Schritt dauert im Median 10 ms (max. 22 ms unter Last). Testweise gebaute Battle-Zips mit `mix36c_as`: 22,2 MB, mit `--half` 10,7 MB, beide „Check ok“. Unter Python 3.10 mit torch 2.14/numpy 2.2 und mit torch 2.2/numpy 1.26 gibt es in einem ganzen aufgezeichneten Spiel 0 abweichende Aktionen.
- Abgabe unverändert V10 (`03cf8bdc…`).

## 30.10.2026, 10:40 Berlin – Claude Code mit Mahmoud: Runde 2 läuft mit `mix36c_as`, `mix48_as`, `mixrl54_as`; Linie 4 fertig

- **Screens fertig** (10:28). Zulassung nach dem Nachtrag 04:09 (mechanisch, `python -m scripts.screen_table --admit`): `mix36c`, `mix48`, `mixrl54`.

| Kandidat (Dev A) | Solution_92 | `sol92_sq` | V3 | V7 | `league_nets6` | `threat6` | Mittel 6 | direkt V10 |
|---|---|---|---|---|---|---|---|---|
| V10 | 89,3 | 77,8 | 72,2 | 60,2 | 52,0 | 81,3 | 72,1 | – |
| `mix36b` (Maßstab) | 90,7 | 80,8 | 80,7 | 63,7 | 59,0 | 82,3 | 76,2 | 59,5 |
| **`mix36c`** | 92,7 | 81,5 | 81,3 | 66,7 | 59,0 | 85,7 | **77,8** | 61,7 |
| **`mix48`** | 90,5 | 82,0 | 78,0 | 66,0 | 61,0 | 85,3 | **77,1** | 63,7 |
| **`mixrl54`** | 89,7 | 80,3 | 77,7 | 63,7 | 64,3 | 82,0 | **76,3** | 62,3 |
| `mix30v8` | 93,5 | 81,5 | 79,3 | 66,3 | 57,3 | 82,7 | 76,8 | 55,7 |
| `mixrl36` | 91,2 | 80,2 | 78,7 | 62,0 | 59,0 | 85,3 | 76,1 | 59,3 |

- **Code im Hauptstand:** `art_splash` und `sap_still_splash` (Commit `f34f9c4`, Standard aus). Tests: 488 bestanden plus 14 Untertests, ohne die Studientests mit Ressourcensperre.
- **Kandidaten** (Nachtrag 10:35): die drei zugelassenen Mischungen mit eingebranntem R, Netze bitgleich. `mix36c_as` `2ab463e9…`, `mix48_as` `088b0280…`, `mixrl54_as` `e0970b37…`. Kurztest: Die Datei lädt R (`art_splash`, `sap_still_splash` an, 36 Netze), 2 Spiele gegen Solution_92 laufen fehlerfrei.
- **Runde 2 gestartet um 10:32** (`WORKERS=9 bash scripts/pipeline_battle_round.sh 2 mix36c_as mix48_as mixrl54_as`, Code `fb60655`, Log `experiments/pipeline_battle_gate.log`): Auswahl 805000–805399 je Kandidat, Wahl höchstens eines, Bestätigung 806000–807399.
- **Linie 4 fertig** (10:23): 12 Netze je 1.500 Spiele, `battle_ftold12` SHA-256 `82e2806e3de57a7a`, `mix30old` gebaut. Validierung gegen Solution_92 (je 16 Spiele, nur Hinweis): 70,3 % am Start, 78,1 % nach 1.500 Spielen. Laufdaten im Repo (`70806a8`). Der `mix30old`-Screen läuft seit 10:23. Seine ersten Teile liefen noch mit dem alten Code, die späteren laufen mit `f34f9c4`. Mit ausgeschalteten Schaltern spielen beide gleich (Gleichheitsprüfung 09:45).
- Kopfzeile von `scripts/pipeline_battle_ftv8.sh` nach dessen Ende korrigiert (01:50 statt 02:10).
- Abgabe unverändert V10 (`03cf8bdc…`).

## 30.10.2026, 09:45 Berlin – Claude Code mit Mahmoud: Regelsatz R (`art_splash` + `sap_still_splash`) besteht beide Gegenproben und geht in die Runde-2-Kandidaten

Nach dem Plan-Nachtrag 30.10., 08:13 (Commit `288f17a`, vor den folgenden Ergebnissen). Alles auf Dev B (801000–801299), gepaart, Code aus der getrennten Arbeitskopie:

| Lauf | gegen | Δ (pp) |
|---|---|---|
| `art_splash` + `art_low_off` | `art_splash` allein, Solution_92/`sol92_sq` | ±0,0 [−0,8; +0,8] → `art_low_off` entfällt |
| `art_splash` + `sap_still_splash` | `art_splash` allein | **+0,7 [+0,1; +1,3]**, bei Streufaktor 1,0 +2,7 [+0,3; +5,5] → kommt dazu (Regel: ≥ +0,5) |
| V10 + R | V10, Solution_92/`sol92_sq` | **+1,4 [+0,6; +2,3]** (Solution_92 +1,0, `sol92_sq` +1,8; Streufaktor 1,0 +5,8 [+2,7; +9,2]; umkämpfte Karten +2,7 [+1,3; +4,2]) |
| Gegenprobe 1: V10 + R | V10, übriges Panel | `sol92_weak` +0,5, `old3_sym3` +0,7, default ±0,0 → hält (keiner unter −1) |
| Gegenprobe 2: `mix36` + `art_splash` | `mix36`, Solution_92/`sol92_sq` | +0,5 [+0,0; +1,1] → hält (nicht darunter) |

- Bei Streufaktor 0,25 und 0,5 ändert R in keinem der 2.270 betroffenen Dev-B-Spiele das Ergebnis. Die Regeln greifen nur bei sicher geschätztem 1,0.
- **Gleichheitsprüfung:** Mit ausgeschalteten Schaltern liefert der neue Code auf 48 Dev-A-Spielen (800000–800011, Solution_92 und `sol92_sq`) in allen Kennzahlen dieselben Werte wie die V10-Basis `B_V10_dev800.csv`.
- Screens: `mix30v8` Mittel 76,8 %, direkt nur 55,7 % (< 59,5 %) → nicht zugelassen. `mixrl54` 76,3 % / 62,3 % → zugelassen. Zugelassen sind damit bisher `mix36c` und `mixrl54`; `mix48` läuft noch (bis etwa 10:45).
- **Ablauf bis Runde 2:** Nach dem `mix48`-Screen kommt der Code in den Hauptstand. Danach werden die zugelassenen Mischungen mit eingebranntem R gebaut (`battle_<name>_as.pth`) und Runde 2 gestartet. Der `mix30old`-Screen der Linie 4 startet gegen 10:30 und läuft dann teils mit dem neuen Code; laut Gleichheitsprüfung spielt der mit ausgeschalteten Schaltern genau wie der alte.
- Abgabe unverändert V10 (`03cf8bdc…`).

## 30.10.2026, 07:55 Berlin – Claude Code mit Mahmoud: Wo V10 verliert, neue Regel `art_splash` auf Dev B bestätigt, `mix36c` für Runde 2 zugelassen

- **v8-Linie fertig** (06:47): 12 Netze je 1.500 Spiele, `battle_ftv8_12` SHA-256 `515760dd885b8282`; `mix30v8` und `mix48` gebaut, ihre Screens laufen. Validierung gegen Solution_92 (je 16 Spiele, nur Hinweis): Mittel der 12 Netze 76,6 % am Start, 81,2 % nach 1.500 Spielen. Laufdaten im Repo (Commit `9d66897`). **Linie 4** läuft seit 06:47 sauber (12 Prozesse, keine Fehler, um 07:01 bei Spiel 75 von 1.500).
- **Screen `mix36c`** (Dev A, gepaart gegen V10): Mittel über 6 Gegner 77,8 statt 72,1 % (Δ +5,67 [+3,14; +8,11]); Solution_92 +3,33 [+0,33; +6,33], `sol92_sq` +3,67 [+0,33; +7,17], `league_nets6` 59,0 % (+7,0), `threat6` 85,7 % (+4,3), V3 +9,2, V7 +6,5; direkt gegen V10 61,7 % [56,0; 67,0]. Beide Werte liegen über `mix36b` (76,2 % / 59,5 %), also ist `mix36c` nach der Regel von 04:09 zugelassen. `mixrl36` (76,1 % / 59,3 %) liegt knapp darunter und ist nicht zugelassen. `mixrl54`, `mix30v8` und `mix48` laufen noch.
- **Wo V10 verliert** (keine neuen Spiele): 5.200 Spiele V10 gegen Solution_92 und `sol92_sq` (Dev A, Auswahl und Bestätigung Runde 1, zusammen 1.300 Karten), verknüpft mit den versteckten Spielparametern und der Relic-Lage jeder Karte aus `env.reset`. Skripte und Daten liegen unter `experiments/analysis/battle_params_20261030/`.

| Merkmal der Karte | Siegquote V10 |
|---|---|
| Sap-Streufaktor 0,25 / 0,5 / 1,0 (versteckt) | 89,1 / 84,5 / 78,9 % |
| Sap-Reichweite 3 / 4 / 5 / 6 / 7 | 91,7 / 87,7 / 79,8 / 82,2 / 79,3 % |
| Relic höchstens 5 Felder von der Mittellinie x + y = 23 (658 Karten, gleich weit von beiden Starts) / sonst | 76,4 / 92,1 % |
| Bewegungskosten 1 / 5 | 79,0 / 88,6 % |
| Sichtweite 1 / 2 / 3 / 4 | 81,4 / 81,5 / 84,3 / 89,8 % |
| Relic-Paare 1 / 2 / 3 | 90,7 / 81,2 / 80,4 % |

  Umkämpfte Karte mit starkem Sap (Streufaktor 1,0 oder Reichweite ≥ 5): 73 %. Keines von beiden: 97 %.
- **40 dieser Spiele nachgespielt** (gegen Solution_92 auf umkämpften Karten mit starkem Sap, je 20 verloren und gewonnen, Wahrheit aus dem Env-Zustand, `contested_probe.py`). Verlorene Spiele kippen in Match 2 und 3: Match 1 gewinnen wir dort noch in 60 %, Match 2 und 3 nur in 10 und 15 %. Je Match verlieren wir 16,6 und 15,9 Einheiten, der Gegner 11,8 und 12,0. Wir besetzen im Mittel 2,0 und 2,8 Punktefelder, der Gegner 3,2 und 4,1.
- **Frühere Dev-A-Tests nach Streufaktor neu ausgewertet** (keine neuen Spiele, gepaart gegen V10, Solution_92 und `sol92_sq`): aggressivere Artillerie (`art_safe=false` + `art_min_hits=2`) bei Streufaktor 0,25 / 0,5 / 1,0 **−6,5 [−10,9; −2,3] / −0,8 / +6,0 [+2,4; +9,5]** pp, insgesamt −0,2. Ihre Wirkung kehrt sich also mit dem Streufaktor um. Er steht nicht in `env_cfg`, `param_est` schätzt ihn aber aus den Energieverläufen der eigenen Einheiten. Nach Sichtweite, Bewegungskosten und Reichweite zeigt keiner der früheren Tests ein solches Muster.
- **Neue Regel `art_splash`** (Standard aus): Ist der Streufaktor laut `param_est` sicher 1,0, sappt die Artillerie schon ab 2 Treffern und auch in gegnerischer Reichweite, sonst wie V10. **Dev B** (801000–801299, von dieser Analyse unberührt, 1.200 Spiele gepaart gegen V10): **+0,8 pp [+0,2; +1,3]** (87,9 statt 87,2 %); Solution_92 +0,7 [−0,2; +1,5], `sol92_sq` +0,8 [+0,2; +1,7]. Bei Streufaktor 1,0 **+3,1 [+1,0; +5,5]**, bei 0,25 und 0,5 genau 0: Die Regel hat dort in 908 Spielen nie eingegriffen, es gab also keine falsche Schätzung „1,0“.
- **Wann die Schätzung sicher ist** (20 Spiele auf Dev-B-Karten mit Streufaktor 1,0): 4-mal in Match 1, 9-mal in Match 2, einmal in Match 3, 6-mal nie. Die Regel wirkt also vor allem in Match 2 und 3, wo die Spiele kippen. Ein Entwurf, der zusätzlich den Streuschaden eigener Saps an Gegnern auswertet, war nur in 4 von 48 Spielen früher sicher und wurde verworfen. Nebenbefund aus diesen 48 Spielen: Auch der heutige Schätzer ist in 3 Spielen zeitweise sicher falsch (zweimal 0,25 statt 0,5, einmal 0,5 statt 1,0), aber nie fälschlich 1,0. V10 nutzt die Streufaktor-Schätzung nicht.
- **Entwickelt in einer getrennten Arbeitskopie** (Basis `9d66897`), damit die laufenden Screens im Hauptstand unverändert bleiben. Patch `experiments/analysis/battle_params_20261030/art_splash.patch`, Tests `tests/test_art_splash.py` (89 Regeltests grün). Mit ausgeschalteten Schaltern ändert der Patch nichts am Verhalten: Er liest nur zusätzliche Schalter. Die Messungen auf Dev B liefen aus der Arbeitskopie (`DB_artsplash.csv`).
- **Laufen auf Dev B:** `art_low_off` (keine Artillerie, solange der Streufaktor sicher 0,25 ist), `sap_still_splash` (bei sicher 1,0 dürfen Halter auch ziehende Gegner sappen; die Engine bewegt vor dem Sap, ein Schritt neben dem Zieltile bekommt den vollen Schaden) und `art_splash` gegen den Rest des Panels (`sol92_weak`, `old3_sym3`, default).
- **Nächste Schritte:** Code nach dem Ende der Screens und vor Runde 2 in den Hauptstand übernehmen. Ob die Runde-2-Kandidaten mit eingebranntem `art_splash` laufen, legt ein Plan-Nachtrag fest, bevor auf 805000–807399 gemessen wird.
- Abgabe unverändert V10 (`03cf8bdc…`).

## 30.10.2026, 05:35 Berlin – Claude Code mit Mahmoud: Bestätigung von `mix36b` nicht bestanden, Abgabe bleibt V10

- **Bestätigung Runde 1** (803000–803799, je Gegner 1.600 Spiele; direkt 804000–804399, 800 Spiele; Ende 05:32, Log `experiments/pipeline_battle_gate.log`): R 88,7 statt 86,9 %, **Δ +1,77 pp [+0,64; +2,95]**. Die Hürde verlangt Δ ≥ +2 pp, deshalb **nicht bestanden**. Alle übrigen Hürden sind erfüllt: untere Grenze > 0, Solution_92 Δ +0,38 [−1,19; +2,00], default 99,9 % (Δ +0,06), direkt gegen V10 56,6 % [51,75; 61,5].

| Gegner (gepaart, 800 Karten) | V10 | `mix36b` | Δ (pp) |
|---|---|---|---|
| Solution_92 | 90,6 | 90,9 | +0,38 [−1,19; +2,00] |
| `sol92_sq` | 77,6 | 82,1 | +4,44 [+2,44; +6,50] |
| `sol92_weak` | 90,9 | 91,1 | +0,25 [−1,31; +1,75] |
| `old3_sym3` | 88,6 | 90,6 | +2,00 [−0,38; +4,50] |
| default | 99,8 | 99,9 | +0,06 |

- Einordnung: In der Auswahl lag `mix36b` bei +2,88. Dass der gewählte Kandidat auf frischen Karten schwächer abschneidet, war zu erwarten (der beste von vier Kandidaten wird überschätzt). Der Vorteil ist echt, aber kleiner als die vorab verlangte Mindestgröße, und er entsteht vor allem gegen `sol92_sq`. Gegen Solution_92 selbst ist kein Unterschied messbar.
- **Folgen laut Plan-Nachtrag 30.10., 04:09:** Referenz in Runde 2 bleibt V10. `mix36b` wird nicht auf neuen Karten wiederholt. Die für eine `mix36b`-Referenz vorgesehenen Änderungen (`--direct-opponent` in `league_gates.py`, `REF`/`REFNAME` im Gate-Skript) entfallen. `pipeline_battle_gate.sh` deckt Runde 2 mit V10 als Referenz schon ab (805000–807399).
- **Dev-A-Screen, nur Information** (300 Karten, gepaart gegen V10; `python -m scripts.screen_table`): Gegen den zurückgehaltenen RL-Gegner `league_nets6` gewinnen `mix36` und `mix36b` je **59,0 % statt 52,0 %** (V10). Mittel über die 6 Gegner: V10 72,1, `mix36` 76,9 (Δ +4,78 [+2,14; +7,33]), `mix36b` 76,2 (Δ +4,06 [+1,75; +6,39]). Gegen RL-Gegner bringen die Mischungen also mehr als gegen die Solution_92-Familie, die das Gate-Panel prägt. Das ist eine Beobachtung auf Entwicklungskarten, kein Nachweis.
- **Wo `mix36b` auf den frischen Karten gewinnt** (Bestätigungsdaten, keine neuen Spiele; Relic-Zahl einer Karte = größte Zahl gefundener Relics über alle 20 Spiele beider Agenten auf ihr): Gegen `sol92_sq` auf Karten mit 6 Relics **+8,3 pp [+4,0; +12,5]** (236 Karten), mit 4 Relics +3,5 [0,0; +7,2], mit 2 Relics +2,4 [−0,6; +5,4]. Gegen Solution_92 kein klares Muster (4 Relics −2,4 [−5,9; +0,7]). Die Häufung auf 4-Relic-Karten aus Dev A wiederholt sich also auch hier nicht; das Nachtraining hilft vor allem auf Karten mit vielen Relics gegen `sol92_sq`. Auf 68 Karten mit ungerader Zahl (ein Relic nie gefunden) gewinnt V10 deutlich seltener (74–79 %).
- **Gewichtung in den Mischungen geprüft** (20.000 Zustände aus dem Replay-Buffer von `20261029_ft_v10_s10`, keine Spiele): Die Spanne der erlaubten Q-Werte ist bei V10-Netzen (Mittel 1,18) und nachtrainierten Netzen (ft2 1,06, ft3 1,01, ftrl 1,08) ähnlich. Die Mischung wählt in 92,8 % der Zustände dieselbe Aktion wie V10 und in 91,6 % dieselbe wie ft2_18 allein; keine Hälfte überstimmt die andere. Eine Normierung der Q-Werte vor dem Mitteln lohnt sich deshalb nicht.
- **Werkzeuge für die nächsten Runden** (Commit `6bb2314`): `python -m scripts.screen_table --admit NAMEN` wendet die Zulassungsregel vom 04:09 mechanisch an (bricht ab, solange ein Screen oder Direktduell fehlt). `scripts/pipeline_battle_round.sh RUNDE NAME…` macht Auswahl je Kandidat, Wahl und Bestätigung; die Wahl wird nur aus Log-Zeilen nach dem eigenen Aufruf gelesen, damit kein altes `AUSWAHL:` greift. `pipeline_battle_gate.sh` kennt jetzt Runde 3 im Reserveblock (808000–809599), zu benutzen erst nach einem Plan-Nachtrag. Tests: `test_screen_table.py` und `test_league_gates.py` 8 bestanden; `bash -n` und die Argumentprüfungen beider Skripte ausprobiert.
- **Linie 4 „Altnetze“ vorbereitet** (Plan-Nachtrag 05:45, vor jedem Screen von `mix36c`, `mixrl54`, `mix30v8`, `mix48`): 12 nie abgegebene, nicht zurückgehaltene Quellnetze (6 × `full_rules_v6`, 6 × `full_rules_fo`) unter allen V10-Regeln wie die v8-Linie, je 1.500 Spiele, Seeds 0–9, 28, 29, Kartenversatz 0. `scripts/pipeline_battle_ftold.sh` läuft seit 05:47 und wartet auf das Ende der v8-Linie (gegen 07:05). Danach `battle_ftold12`, `mix30old` (V10 + ftold12) und ihr Dev-A-Screen. Rauchtest mit je 2 Spielen für `v6_s27` (Seed 0) und `fo_s35` (Seed 29): 300.000 Transitions geladen, V10-Regeln an, Trainingskarten 200000–200001 bzw. 490000–490001, Status `done`; Rauchtest-Ordner gelöscht.
- Abgabe unverändert V10 (`03cf8bdc…`).
- **Offen:** Screens von `mix36b` (Direktduell), `mixrl36`, `mixrl54`, `mix36c`, `mix30v8`, `mix48` bis etwa 10:30. Danach Zulassung zu Runde 2 nach den Regeln vom 04:09, Auswahl 805000–805399, Bestätigung 806000–807399. Linie 4 bis etwa 11:00, Screen danach. Folie 11 auf die Battle-Woche umstellen, sobald Runde 2 entschieden ist.

## 30.10.2026, 03:24 Berlin – Claude Code mit Mahmoud: Runde 3 fertig, v8-Linie und Morgen-Screen gestartet, `mix36c` als weiterer Screen-Kandidat

- **Runde 3 des Nachtrainings** ist um 03:15 fertig (18 Netze je +2.000 Spiele, Kartenversatz 2000): `battle_ft3_18`, SHA-256 `c556cd6cb0161708`, wie in Runde 1/2 aus den Endständen. Laufdaten (Manifest, Log, Trainings- und Validierungskurven) und `experiments/pipeline_battle_ft3.log` jetzt im Repo.
- **v8-Linie** um 03:16 automatisch gestartet: 12 Trainingsprozesse laufen, Pool-Gegner werden geladen, erste Validierung geschrieben. Der **Morgen-Screen** startete ebenfalls um 03:16 (zuerst V10 gegen die zurückgehaltenen Gegner).
- **Neuer Screen-Kandidat `mix36c`** = V10 + `ft3_18` mit V10-Config (SHA-256 `e8b0de223fee12f3`), festgelegt im Plan-Nachtrag 30.10., 03:23, vor jeder Messung mit `ft3_18`. Der Screen steht in der Entwicklungs-Warteschlange (`experiments/battle_queue.txt`) und läuft erst nach dem Nachtablauf, damit die Bestätigung nicht gebremst wird.
- Der Rechner ist voll ausgelastet (32 Rechenprozesse auf 15 Kernen). Das Ergebnis der Bestätigung von `mix36b` kommt deshalb eher gegen 06:00–07:00 als gegen 05:00. Die V10-Hälfte der Bestätigung (8.000 Spiele) war um 02:59 fertig.
- Abgabe unverändert V10 (`03cf8bdc…`).

## 30.10.2026, 01:50 Berlin – Claude Code mit Mahmoud: Auswahl Runde 1 wählt `mix36b`, Bestätigung läuft; dritte Trainingslinie vorbereitet

- **Auswahl Runde 1** (802000–802399, je Gegner 400 Spiele, direkt 400 Spiele auf 802200–802399; Hürden `scripts/league_gates.py`, Log `experiments/pipeline_battle_gate.log`):

| Kandidat | R (Δ zu V10) | Solution_92 | `sol92_sq` | `sol92_weak` | `old3_sym3` | default | direkt gegen V10 | Ergebnis |
|---|---|---|---|---|---|---|---|---|
| V10 (Referenz) | 88,5 % | 89,5 | 81,2 | 92,0 | 91,2 | 99,5 | – | – |
| `mix36` (V10 + ft18) | 89,9 (+1,44 [−0,62; +3,50]) | 94,8 | 82,3 | 92,5 | 90,2 | 99,8 | 58,5 [52,0; 65,0] | R-Hürde um 0,06 pp verfehlt |
| `ft2_18` (Runde 2 allein) | 90,0 (+1,50 [−0,69; +3,69]) | 90,0 | 85,3 | 91,7 | 93,0 | 99,5 | 63,5 [57,0; 70,0] | bestanden |
| **`mix36b`** (V10 + ft2_18) | **91,4 (+2,88 [+0,69; +5,06])** | 93,5 | 85,3 | 95,5 | 91,2 | 99,5 | 55,5 [48,5; 62,5] | **bestanden, gewählt** |
| `mix54` (V10 + ft18 + ft2_18) | 90,6 (+2,12 [+0,19; +4,00]) | 91,5 | 84,5 | 92,7 | 93,8 | 100 | 65,0 [58,5; 71,5] | bestanden |

  Gewählt wird nach der Regel der Kandidat mit dem größten R unter den bestandenen. Gegen Solution_92 liegt `mix36b` bei +4,0 pp [+0,75; +7,50]. Direkt gegen V10 sind Mischungen mit den V10-Netzen näher an 50 % als `ft2_18` oder `mix54`, weil sie V10 ähnlicher spielen.
- Die Code-Kennung im Log wechselt nach `mix36` von `cc8dba4` auf `1de55a8` (Commits während des Laufs). `git diff cc8dba4 1de55a8` für `agents/`, `lux/`, `par_eval`, `common` und `league_gates` ist leer; spielrelevant also derselbe Code.
- **Bestätigung `mix36b`** (803000–804399: 8.000 Spiele V10, 8.000 `mix36b`, 800 direkt) läuft seit 01:43, Ergebnis gegen 05:00. Die Abgabe bleibt V10, bis sie bestanden ist und die Übernahme mit `scripts/release_candidate.py` dokumentiert ist.
- **Wo die Gewinne entstehen** (Auswertung vorhandener Dev-A-Daten, keine neuen Spiele): Auf Karten mit 4 gefundenen Relics bringt das Orakel mit wahren Relics und Punktefeldern +11,5 / +8,9 pp (`sol92_sq` / Solution_92), nur Punktefelder +6,7 / +6,7, nur Relics +4,7 / +4,2. Auf Karten mit 2 Relics bringt das Orakel etwa nichts. `mix36` holt seinen Vorsprung an derselben Stelle: +9,6 / +6,8 auf 4-Relic-Karten, 0 auf 2-Relic-Karten. Die bisher getesteten Regeln für dieses Problem (`opp_point_infer`, `relic_scout`) brachten nichts; die nachtrainierten Netze schon. **Gegenprobe auf den Auswahlkarten** (802000–802199, `mix36b` gegen V10, Mittel über die 4 Panel-Gegner): 2 Relics +1,9, 4 Relics +1,6, 6 Relics +6,3 pp (je 58–65 Karten). Die Häufung auf 4-Relic-Karten wiederholt sich dort nicht; belastbar ist nur, dass das Nachtraining auf Karten mit mehreren Relic-Paaren eher mehr bringt.
- **Runde 4 der Hauptlinie entfällt** (Runde 2 ohne Zusatznutzen, Runde 3 mit flachen Trainingskurven). Stattdessen **dritte Trainingslinie „v8-Linie“** (Plan-Nachtrag 30.10., 01:50; `scripts/pipeline_battle_ftv8.sh`): die 12 Netze `full_rules_v8` vom 22.10. unter allen V10-Regeln, je 1.500 Spiele, Seeds 10–21, Kartenversatz 3000 (Bereich der gestrichenen Runde 4), Gegnermix der geplanten Runde 4. Startet automatisch nach Ende von Runde 3, 12 parallel. Danach `mix30v8` (V10 + ftv8_12) und `mix48` (V10 + ft2_18 + ftv8_12) im Dev-A-Screen; zusätzlich `mix36b` als Vergleich. Maßstab für Runde 2 ist jetzt `mix36b` statt `mix36` (festgelegt vor allen diesen Screens).
- Prüfungen: `bash -n`; Rauchtest `finetune` mit dem Init-Lauf `20261022_full_rules_v8_s70_sol70` und genau diesen Argumenten über 2 Spiele: lädt 300.000 Transitions, V10-Regeln an (`sap_still`, `reach_assign`), Trainingskarten 303000–303001, Status `done`. Der Rauchtest-Ordner wurde danach gelöscht. Der Kopfkommentar des laufenden Skripts nennt noch „02:10“ statt 01:50 (laufende Skripte werden nicht bearbeitet; Korrektur nach Ende). Die Startgrenze von `finetune` (Seed ≤ 29) erlaubt keine Seeds 30–41, deshalb Seeds 10–21 mit eigenem Kartenversatz.
- **Läuft Sherlock beim Prof?** Laut README der Kursvorlage nutzt er Windows mit Python 3.10+ und installiert Pakete ohne Versionsangabe. Neues Skript `scripts/xversion_replay.py`: `record` spielt mit der Battle-Zip ein echtes Spiel wie der Kurs-Runner mit `train=True` (Sherlock gegen Sherlock, beide Seiten) und zeichnet Beobachtungen und Aktionen auf. `replay` spielt dieselben Beobachtungen in einer anderen Umgebung nach und zählt abweichende Aktionen. Geprüft mit einer `mix36b`-Zip (nur Scratchpad, 22,2 MB, Prüfung von `build_submission --battle` bestanden) auf den Karten 4242 und 7311: **0 abweichende Aktionen in 303 Schritten** unter Python 3.10.15 mit torch 2.14.1/numpy 2.2.6 und mit torch 2.2.2/numpy 1.26.4 (eigene venvs im Scratchpad, Python-Build von python-build-standalone mit geprüfter SHA-256). Ebenso die `--half`-Zip (10,7 MB) mit torch 2.2.2. Der Agenten-Code nutzt keine plattformabhängigen Module und öffnet keine Textdateien. Windows selbst konnte ich nicht testen.
- Abgabe unverändert V10 (`03cf8bdc…`).
- **Offen:** Ergebnis der Bestätigung (gegen 05:00). Morgen-Screen (V10/`mix36` gegen die zurückgehaltenen Gegner, `mixrl36`, `mixrl54`). v8-Linie bis etwa 07:30, danach ihre Screens. Nachtrag mit höchstens 3 Kandidaten für Runde 2 vor deren Start.

## 29.10.2026, 23:55 Berlin – Claude Code mit Mahmoud: Runde 2 fertig, Auswahl Runde 1 läuft, Morgen-Screen mit zurückgehaltenen RL-Gegnern vorbereitet

- **Runde 2 vollständig** (18 Netze, je 2.000 Spiele, Ende 23:29), Ensemble `battle_ft2_18` (`0a05d938…`). Der Nachtablauf hat `mix36b` (V10 + ft2_18, 24,0 MB) und `mix54` (V10 + ft18 + ft2_18, 35,1 MB) gebaut und um 23:30 die **Auswahl Runde 1** gestartet. V10-Referenz auf 802000–802199 (je Gegner 400 Spiele): Solution_92 89,5 %, `sol92_sq` 81,2 %, `sol92_weak` 92,0 %, `old3_sym3` 91,2 %, default 99,5 %, also R 88,5 %. Tempo etwa 98 Spiele/min mit 8 Workern neben 12 Trainingsprozessen. Die Auswahl ist voraussichtlich gegen 02:00 fertig, danach folgt die Bestätigung des gewählten Kandidaten.
- **Trainingsverlauf der Einzelnetze** (ε = 0,05; erstes / mittleres / letztes Drittel der Spiele):
  - RL-Liga (6 von 18 Netzen fertig): Solution_92 59 / 64 / 67 %, `sol92_sq` 45 / 49 / 50 %, eigene Abgaben im Pool 29 / 34 / 35 %, `battle_mix36` 15 / 13 / 17 %.
  - Runde 3 (6 von 18 fertig): Solution_92 71 / 69 / 70 %, `sol92_sq` 56 / 59 / 54 %, Pool 46 / 51 / 47 %. Kein weiterer Anstieg gegenüber Runde 2 (Solution_92 66 / 67 / 66 %).
- **Neu, nur Entwicklung:** `scripts/battle_screen.sh` und `scripts/pipeline_battle_morning.sh` (Plan-Nachtrag 29.10., 23:55). Der Screen misst zusätzlich gegen zwei **zurückgehaltene RL-Gegner, gegen die nie trainiert wurde**: `league_nets6` (6 Netze vom 26.10., V10-Regeln) und `threat6` (6 Gefahr-Netze, V3-Regeln). Er startet automatisch nach Ende von Runde 3 mit V10 und `mix36`. Nach Ende der RL-Liga folgen `mixrl36` (V10 + ftrl18) und `mixrl54` (V10 + ft18 + ftrl18).
- Prüfungen: Auswertungscode des Screens auf vorhandenen Dev-A-Daten durchgelaufen (umbenannte Kopie im Scratchpad). Rauchtest V10 gegen beide zurückgehaltenen Gegner auf Karte 999990: beide laden mit 6 Netzen, 4/4 Spiele ohne Fehler. `bash -n` für beide Skripte.
- **Dateigröße, Vorsorge (noch nicht benutzt):** `python -m scripts.build_submission --battle --half` speichert die Netzgewichte als float16 und lässt den Optimierer-Zustand weg. Der Agent rechnet weiter in float32; `load_state_dict` wandelt beim Laden um, der Agenten-Code ist unverändert. Messung auf 50.000 Zuständen aus dem Replay-Buffer von `20261029_ft_v10_s10`: Die beste erlaubte Aktion ändert sich in 0,008 % der Fälle (`mix36`) bzw. 0,006 % (`mix54`), größte Q-Abweichung 0,007. `mix36` als Battle-Zip: **10,7 statt etwa 22 MB**. Kursprüfung in beiden Ordnerlagen bestanden, auch eingefroren mit `train=True` (nur Scratchpad). Standard bleibt ohne `--half`. Nur nutzen, wenn Moodle die Dateigröße begrenzt.
- **Auffälligkeit für die Fehlersuche** (vorhandene Dev-A-Daten, V10): Siegquote nach Zahl der gefundenen Relics (2 / 4 / 6): `sol92_sq` 87,0 / 69,9 / 77,8 %, Solution_92 92,7 / 84,1 / 92,4 %, V7 68,3 / 60,0 / 48,6 %. Gegen die Solution_92-Familie verliert V10 also vor allem auf Karten mit 4 Relics.
- Tests: ganze Suite 487 bestanden (ohne `test_early_curriculum_study`, Ressourcensperre), darunter 1 neuer Test für `--half`.
- Abgabe unverändert V10 (`03cf8bdc…`).
- **Offen:** Ergebnis von Auswahl und Bestätigung. Moodle-Dateigrenze klären (36 Netze ≈ 22 MB Zip, 54 Netze ≈ 33 MB, mit `--half` etwa die Hälfte).

## 29.10.2026, 21:05 Berlin – Claude Code mit Mahmoud: Runde 2 ohne Zusatznutzen, zweite Trainingslinie „RL-Liga“ gestartet

- **Runde 2 auf denselben 6 Netzen** (Dev A, gepaart): `ft2_6` gegen `ft6` (Runde 1) `sol92_sq` 79,8 statt 82,2 % (−2,3 [−5,8; +1,0]), Solution_92 89,0 statt 89,2 % (−0,2 [−3,2; +2,8]); gegen V10 +2,0 / −0,3. Weitere 2.000 Spiele derselben Art verbessern das Ensemble also nicht messbar, obwohl die Trainingskurven der Einzelnetze steigen.
- Deshalb **zweite Trainingslinie** (`scripts/pipeline_battle_ftrl.sh`, Plan-Nachtrag 21:00): dieselben 18 V3-Quellnetze wie Runde 1, je 1.500 Spiele, Kartenversatz 4000. **Die Hälfte der Spiele läuft gegen eigene RL-Abgaben** (V10, `old3_sym3`, `battle_mix36`, V3, V7), der Rest gegen Solution_92 0,20, `sol92_sq` 0,20, `sol92_weak` 0,05 und default 0,05. Ziel: vielfältigere Netze, und mehr Stärke gegen Agenten aus Netz und Regeln, wie sie andere Teams haben dürften. Seit 20:56 laufen 6 Netze, Ensemble `battle_ftrl18` voraussichtlich gegen 06:00.
- Erster Start um 20:55 abgebrochen: Kartenversatz 5000 verletzt die Schutzregel in `finetune` (`map_offset + games/2 <= 5000`, Grenze zu den Auffüllkarten). Es wurden keine Läufe angelegt. Log `experiments/pipeline_battle_ftrl_fehlstart.log`.
- Runde 4 startet nicht mehr automatisch. Die Entscheidung fällt nach der Auswahl Runde 1, die zeigt, ob `ft2_18` mehr bringt als Runde 1. Runde 3 läuft weiter.

## 29.10.2026, 19:45 Berlin – Claude Code mit Mahmoud: Gegenprobe Dev B für mix36, Runde 4 vorbereitet

- **`mix36` auf Dev B** (801000–801299, ganzes Panel, je Gegner 600 Spiele, gepaart gegen V10): `sol92_sq` 84,8 % (V10 83,2 %, +1,7 [−1,2; +4,7]), Solution_92 92,7 % (91,2 %, +1,5 [−1,0; +3,8]), `sol92_weak` 92,3 % (±0), `old3_sym3` 92,7 % (91,7 %, +1,0 [−2,7; +5,0]), default 100 %. Die Schwäche gegen `old3_sym3` auf Dev A (−3,3) bestätigt sich nicht. Der Vorsprung gegen `sol92_sq` ist kleiner als auf Dev A (+5,2). Gesamtbild beider Blöcke: R etwa +1,3 pp. Für die Bestätigungshürde (+2 pp) reicht das voraussichtlich nicht; deshalb weiteres Nachtraining.
- Trainingskurven (Einzelnetz, ε = 0,05): gegen Solution_92 61 → 72 %, `sol92_weak` 64 → 74 %, `sol92_sq` 48 → 52–56 %; gegen den Pool aus eigenen Ensembles bleibt es bei etwa 41–48 % ohne Anstieg. **Runde 4** (`scripts/pipeline_battle_ftn.sh 4 …`, startet automatisch nach dem Ende von Runde 2) deshalb mit mehr und vielfältigeren RL-Gegnern: Mix Solution_92 0,30, `sol92_sq` 0,25, `sol92_weak` 0,10, **Pool 0,25** (V10, `old3_sym3`, `battle_mix36`, **V3- und V7-Abgabe**), RushBot 0,05, default 0,05.
- **RL-Gegner und Direktduell** (Dev A, 4 Worker, nur Einschätzung, keine Auswahl; `par_eval --first 300000 --n 300`, Ausgaben `B_V10_rl.csv`, `D_mix36_rl.csv`, `D_mix36_direct.csv`): gegen die frühere Abgabe **V3** `mix36` 75,7 % statt 72,2 % (+3,5 [−2,7; +9,3]), gegen **V7** 66,7 % statt 60,2 % (+6,5 [−0,5; +13,2]); **direkt gegen V10 58,0 % [52,7; 63,7]** aus 600 Spielen. Gegen RL-Agenten mit ähnlicher Spielweise ist der Gewinn also größer als gegen die Solution_92-Familie.
- Upload: Mahmoud lädt **nur einmal am Ende** hoch (04.11., nach allem Training), keine Zwischenstände. Bis dahin ist `Gruppe15.zip` nur ein lokaler Prüfstand.
- Auslastung: 12 Trainings- und 8 Messprozesse auf 15 Kernen (5 Leistungs-, 10 Effizienzkerne). Training 115 statt 92 Spiele/min, Messung 86 statt 105 Spiele/min. Insgesamt etwa gleich, die Überbelegung kostet also nichts.

## 29.10.2026, 19:15 Berlin – Claude Code mit Mahmoud: 18 nachtrainierte Netze gemessen, Nachtablauf geplant, Battle-Abgabe gegen train=True abgesichert

- **Erste Nachtrainingsrunde fertig** (alle 18 Netze, je 1.500 Spiele). Dev A, alle mit V10-Config:

| Ensemble | `sol92_sq` | Solution_92 | `sol92_weak` | `old3_sym3` | default |
|---|---|---|---|---|---|
| V10 (Basis) | 77,8 % | 89,3 % | 89,5 % | 89,3 % | 99,8 % |
| `ft18` (nur nachtrainiert) | 77,7 (−0,2 [−4,0; +3,7]) | 90,3 (+1,0 [−2,0; +4,0]) | – | – | – |
| **`mix36`** (V10 + ft18, 36 Netze) | **83,0 (+5,2 [+1,7; +8,7])** | 90,8 (+1,5 [−1,5; +4,5]) | 92,0 (+2,5 [−0,2; +5,3]) | **86,0 (−3,3 [−7,7; +1,0])** | 100 (+0,2) |

  `mix36` ist auf Dev A die beste Mischung (R ≈ 88,0 statt 86,5 %), aber gegen unsere alte Abgabe `old3_sym3` schlechter. Ob das Zufall ist, prüft der laufende Dev-B-Lauf (ganzes Panel, zweiter von höchstens sechs Dev-B-Läufen). `relic_scout=2` −2,2 / −2,2 pp (Auswertung von Hand nachgetragen, weil das Messskript während des Laufs geändert worden war; die Spiele selbst waren vollständig).
- **Nachtablauf vorab festgelegt** (Plan-Nachtrag 29.10., 19:00, `scripts/pipeline_battle_night.sh` in der Warteschlange): Nach Runde 2 werden `mix36b` (V10 + ft2_18) und `mix54` (V10 + ft18 + ft2_18) gebaut. Danach läuft die Auswahl Runde 1 (802000–802399) für `mix36`, `ft2_18`, `mix36b` und `mix54`, anschließend die Bestätigung (803000–804399) nur für den gewählten Kandidaten. Die Abgabe ändert der Ablauf nicht.
- **Runde 3 des Nachtrainings** (`scripts/pipeline_battle_ft3.sh`, +2.000 Spiele je Netz, Kartenversatz 2000, Pool zusätzlich mit `battle_mix36`) läuft seit 18:51 für die Netze, deren Runde 2 fertig ist. Die übrigen Netze starten jeweils nach ihrer Runde 2. Der Nachtablauf startet Runde 3 nicht ein zweites Mal.
- **Risiko im Battle gefunden und behoben:** `lux/runner.py` erzeugt Agenten ohne `train`-Argument, und `run_agents` hat den Standard `train=True`. Mit `train=True` spielte Sherlock mit nur einem Netz, ohne die meisten Regeln und mit ε = 0,05. Außerdem überschriebe er seine `.pth` (Speichern vor Spiel 0 und am Spielende). Neuer Schalter `frozen` (Standard aus): Damit bleibt der Agent auch bei `train=True` im Spielmodus (alle Netze, alle Regeln, kein ε), lernt nicht und schreibt ohne ausdrücklichen Pfad nichts. `scripts.build_submission --battle` setzt `frozen` nur in der verpackten `.pth`; Gewichte und alle übrigen Einträge bleiben gleich. Die Prüfung der Zip simuliert jetzt zusätzlich den Runner mit `train=True` (ohne `set_to_eval_mode`, mit `save_agent()` und `update(terminated=True)`) und verlangt eine unveränderte Datei.
- Neu gebaut: `Gruppe15.zip` mit V10 (18 Netze, eingefroren), 11,9 MB, SHA-256 `b975fcd1…`, darin `agent.pth` `32daeda2…`. Die Abgabe-Dateien unter `agents/sherlock/weights/` sind unverändert (`03cf8bdc…`). Prüfung in der frischen Kursvorlage (Ordner unter `agents/` und in der Wurzel, je beide Seiten): bestanden.
- Prüfungen: ganze Testsuite 486 bestanden, darunter 2 neue zu `frozen`. Ausgenommen ist `test_early_curriculum_study`: Seine Ressourcensperre verweigert, solange Training läuft. Dabei aufgefallen und behoben: Die heutige `relic_scout`-Zeile in `features.make_context` las `agent.training` auch bei ausgeschaltetem Schalter. Mit echten Agenten änderte das nichts, aber 3 Tests in `test_active_targets` scheiterten an ihrem Test-Agenten ohne dieses Attribut. 4 V10-Spiele auf Dev A sind in allen Kennzahlen identisch mit der Basis. Rauchtest mit 5 statt 3 Matches pro Spiel (Env-Parameter nur im Testprozess): 4/4 Siege gegen Solution_92, Matches 19:1, kein Absturz.
- **Offen:** Dev-B-Ergebnis `mix36`. Für die 36- und 54-Netze-Kandidaten (Zip ≈ 22 bzw. 33 MB) die Moodle-Grenze für die Dateigröße prüfen (Mahmoud). Nach dem Nachtablauf Übernahme nur bei bestandener Bestätigung.

## 29.10.2026, 16:30 Berlin – Claude Code mit Mahmoud: Nachtraining wirkt, zweite Runde gestartet

- **Sauberer Trainingsvergleich auf Dev A** (gleiche 6 Netze, beide mit exakt der V10-Config, `scripts/build_ensemble.py --cfg-from`): vorher (`battle_orig6`) `sol92_sq` 77,5 %, Solution_92 86,0 %; **nach 1.500 Nachtrainingsspielen (`battle_ft6`) 82,2 % / 89,2 %**, gepaart **+4,7 pp [+1,0; +8,5]** und **+3,2 pp [0,0; +6,7]**. Schon diese 6 Netze liegen gegen Solution_92 gleichauf mit dem 18-Netz-V10 und gegen `sol92_sq` +4,3 pp [+0,7; +8,2] darüber. Erstmals bringt Training wieder messbar etwas: Die V3-Netze waren nie unter den späteren V10-Regeln und dem korrigierten Gedächtnis trainiert worden.
- Trainingskurven (ε = 0,05, je 500 Spiele) steigen am Ende noch: Solution_92 im Mittel 60 → 64 → 66 %, `sol92_sq` 48 → 51 → 53 %. Deshalb **zweite Runde** (`scripts/pipeline_battle_ft2.sh`): +2.000 Spiele je Netz ab dem Endstand der ersten Runde (Gewichte und Buffer), neue Trainingskarten (`finetune --map-offset 1000`), gleiche Gegnermischung. s10–s15 laufen seit 16:16, die übrigen starten jeweils nach ihrer ersten Runde; Ensemble `battle_ft2_18` voraussichtlich nachts.
- Erste Runde: Wellen 2/3 laufen, `battle_ft18` und `battle_mix36` (V10 + ft18) werden danach automatisch auf Dev A gemessen. V10-Basis auf **Dev B** (801000–801299, ganzes Panel) für die Gegenprobe in der Warteschlange.
- Regeln ohne Gewinn (Dev A, `sol92_sq` / Solution_92): `active_targets` −0,5 / +0,2, `mobile_seen` +0,3 / −0,3, `art_safe=false` +0,8 / −1,0, mit `art_min_hits=2` 0,0 / −0,5, `opp_point_infer` +0,5 / −1,0, `relic_scout=1` −1,3 / −1,0. Teil-Orakel: nur Relics +3,7 [+0,8; +6,5] / +1,0, nur Punktefelder +2,5 / +1,3. Relic-Entdeckung (60 Spiele): Verzögerung im Mittel 10 Schritte, in Match 2 drei von 40 neuen Paaren nie gefunden.
- Plan für 30.10. früh: bestes Ensemble (ft18, ft2_18, mix36) mit vollem Panel auf Dev A und Dev B prüfen, danach Auswahl Runde 1 (802000–802399) und bei Erfolg Bestätigung (803000–804399).

## 29.10.2026, 15:00 Berlin – Claude Code mit Mahmoud: erste Entwicklungsergebnisse der Battle-Vorbereitung

Alle Werte auf Dev A (800000–800299, je Gegner 600 Spiele), gepaart gegen die V10-Basis; nur Entwicklung, keine Übernahmeentscheidung.

| Variante | `sol92_sq` | Solution_92 |
|---|---|---|
| `opp_infer` | +0,3 [−1,8; +2,5] | −1,5 [−3,3; +0,3] |
| `contest_sap` | +1,2 [−1,3; +3,8] | −0,2 [−2,2; +2,0] |
| beide | +1,8 [−0,7; +4,5] | −1,8 [−4,3; +0,5] |
| **`home_reserve`** | **−24,0** [−28,7; −19,3] | **−23,8** [−28,3; −19,2] |
| Orakel: wahre Relics und Punktefelder | **+6,3** [+2,7; +10,0] | **+4,0** [+0,8; +7,2] |

- **`home_reserve` ist ein klarer Fehlschlag** und bleibt aus. Die Diagnose aus einem Einzelspiel (Einheiten laufen in die besetzte Festung) war nicht verallgemeinerbar: Punktefelder der Gegnerhälfte sind oft noch frei, dort holen wir viele Punkte (gewonnene Matches: mehr Einheiten auf dem Weg dorthin als verlorene). Die Tests `hrs`/`hrat` mit diesem Schalter wurden abgebrochen.
- **Orakel** (`scripts/oracle_probe.py`): Perfektes Wissen ist 4–6 pp wert. Teil-Orakel (nur Relics bzw. nur Punktefelder) laufen.
- **Gedächtnis gegen Wahrheit** (`scripts/belief_truth_check.py`, 60 Spiele, 18.000 Schritte): V10 hat nie falsche Punktefelder, aber in 553 Schritten echte Punktefelder als tot markiert. Ursache: Ein in Match 2 neu gespawntes Relic-Paar wird nicht gefunden (800004: 38–44 % der Punktefelder bekannt). Neue Schalter, alle Standard aus und getestet: `opp_point_infer` (Gleichungen aus dem Punktgewinn des Gegners, wenn jedes mögliche Punktefeld sichtbar ist; 299 Anwendungen ohne falsches Feld) und `relic_scout` (überzählige Einheiten suchen in Match 2/3 bis Schritt 60 das fehlende Paar).
- Weitere Einzelspiele: Gegnerfestung auf einem gemeinsamen Haufen (800180, 81:908 Punkte), unsere Einheiten treffen einzeln ein und schießen nicht zurück (`art_safe` verhindert Artillerie innerhalb gegnerischer Reichweite); Pendeln vor einem Haufen ohne bekanntes Punktefeld, weil `collision_guard` jeden Gegner für beweglich hält (800051).
- Warteschlange `scripts/battle_queue.sh` (`experiments/battle_queue.txt`): `active_targets`, `mobile_seen`, `art_safe=false` (±`art_min_hits=2`), `cand_rescue`, Teil-Orakel, `opp_point_infer`, `relic_scout` 1/2, sauberer Trainingsvergleich 6 Netze vor/nach dem Nachtraining.

## 29.10.2026, 14:30 Berlin – Claude Code mit Mahmoud: Battle-Vorbereitung gestartet (läuft bis 04.11.)

- **Auftrag Mahmoud:** bis 04.11. Sherlock „perfekt trainieren“ und vieles ausprobieren, damit wir die Agents der anderen Teams schlagen. [Plan mit Testkarten und Hürden](superpowers/plans/2026-10-29-battle-push.md) vor den Messungen festgelegt (Commit `b02ef7b`). Übernahme nur über `scripts/league_gates.py` auf frischen Karten, sonst bleibt V10.
- **Basis V10 auf Dev A** (800000–800299, beide Seiten, je 600 Spiele): default 99,8 %, Solution_92 89,3 %, `sol92_weak` 89,5 %, `old3_sym3` 89,3 %, **`sol92_sq` 77,8 %**. Datei `experiments/compare/battle/B_V10_dev800.csv`.
- **Niederlagen-Analyse** (`scripts/par_losses.py`, `scripts/mechanism_probe.py --opponent/--games`, 521 nachgespielte Spiele): In verlorenen Matches 2/3 feuert der Gegner etwa doppelt so viele Saps (40 statt 18 je Match, Streuschaden 1.269), wir verlieren 16,5 statt 9 Einheiten durch Energie, stehen auf weniger Punktefeldern (390 statt 550 Einheiten-Schritte) und kennen nur ~80 % der Punktefelder (gewonnen ~95 %). Gegner stehen viermal so oft auf Punktefeldern unserer Hälfte.
- **Fehler gefunden (800070, Match 3):** Kennt der Belief mehr Punktefelder als wir Einheiten haben, schickt die Zielzuweisung die übrigen Einheiten zu Punktefeldern der Gegnerhälfte, auch 25 Felder weit in die besetzte Festung. Sie sterben und laufen nach dem Respawn erneut los. Neue Schalter (Standard aus, Commit `2525d7b`): `home_reserve` (Reserve im Ring mit Abstand 2 um die eigenen Punktefelder) und `reserve_sap` (Reserve schießt wie ein Halter). Mit ausgeschalteten Schaltern 80 V10-Spiele in allen Kennzahlen identisch mit der Basis.
- **Nachtraining der 18 V3-Netze** unter allen V10-Regeln gegen gemischte Gegner (`scripts/pipeline_battle_ft.sh`, 6 parallel, je 1.500 Spiele) läuft seit 13:25. Erste Validierung der ersten 6 Netze nach 500 Spielen (je 16 Spiele, nur Hinweis): Solution_92 im Mittel 71 → 77 %, Matches 61 → 70 %.
- Entwicklungstests auf Dev A (`scripts/battle_dev.sh`, Log `experiments/battle_dev.log`): `opp_infer` ohne Gewinn (`sol92_sq` +0,3, Solution_92 −1,5 pp, n. s.). In der Warteschlange: `contest_sap`, beide zusammen, Orakel-Obergrenze (`scripts/oracle_probe.py`: wahre Punktefelder ins Gedächtnis), `home_reserve`, `+reserve_sap`, `active_targets`, `home_reserve+active_targets`.
- Für später vorbereitet: `scripts/pipeline_battle_gate.sh` (Auswahl, Wahl, Bestätigung je Runde; Log kompatibel mit `scripts/release_candidate.py`).
- Prüfungen: neue Tests `tests/test_finetune.py` (2), `tests/test_par_losses.py` (1), `tests/test_battle_rules.py` (4) grün; gesamte Suite 535 bestanden. Nur `tests/test_early_curriculum_study.py` schlägt fehl, und zwar ausschließlich an der eigenen Ressourcensperre („Another model job is active“, 81×), solange Training läuft. Abgabe-Gewichte unverändert `03cf8bdc…8c67`.
- Der Mac bleibt per `caffeinate` bis 04.11. wach; Laptop offen und am Netzteil lassen.

## 29.10.2026, 13:40 Berlin – Claude Code mit Mahmoud: Entwurf Präsentation Battle Session 06.11.

- Auftrag aus der Prof-Mail: 10 Minuten für die Kommilitonen, wie Sherlock funktioniert und trainiert wurde, dazu die Entwicklungen der letzten Woche; Bewertungsschema Kursfolie 11. Das Prof-Feedback vom 23.10. (Action Masking, Entscheidungsablauf, Rolle der 18 Netze) ist eingearbeitet.
- `Sherlock_Battle_06-11-2026.pdf` (Projektordner): 13 Vortragsfolien + 3 Reserve im Design vom 23.10. Quelle `docs/presentation/Sherlock_Battle_06-11-2026.html`, zusammengesetzt aus den geprüften Folien „Entscheidungsablauf“ (26.10.) und vom 23.10. Neu: Titel/Kernaussage, Agenda, Gedächtnis (aus der Reserve nach vorn), „Von 47 % auf 90 %“, „Neu seit letzter Woche“ (Liga-Training, Robustheitstabelle, Ladefehler), Erkenntnisse, Fazit mit Hinweisen fürs Replay.
- `Sherlock_Stichpunkte_06-11-2026.md` (Projektordner): Sprechtext je Folie, Vorschlag Moayed 5:10 (Folien 1–5, 10, 12–13), Mahmoud 4:20 (6–9, 11), zusammen 9:30; Rückfragen, Text für Moodle, Belege.
- Prüfungen: alle 16 Seiten als Bild angesehen, Umbrüche korrigiert. Zahlen aus Arbeitsstand 22./26.10., Übernahmeberichten V7/V10, `v10_mechanics_20261022/RESULTS.md` und `Sherlock_Entscheidungsprozess.md` übernommen. Keine neuen Spiele.
- Offen: Moayed prüft Aufteilung und Folien; Folie 11 vor dem 06.11. auf den neuesten Stand bringen; zweimal mit Uhr proben.

## 29.10.2026, 13:10 Berlin – Claude Code mit Mahmoud: Battle-Abgabe `Gruppe15.zip` gebaut und in der Original-Vorlage geprüft

- **Auftrag (Prof-Mail, von Mahmoud weitergegeben):** Agent bis Mittwoch Nacht auf Moodle (vermutlich 04.11.), der Prof bringt ihn am Donnerstag auf seinem Laptop zum Laufen. Gezippter Ordner mit Gruppennamen, Pfad zur Agent-Klasse, Pfad zu den Gewichten, dazu 10 Minuten Vortrag für die Battle Session.
- **Gefundenes Risiko:** Der Kurs-Runner legt `agents/` in den Suchpfad, der Gewichte-Pfad ist aber relativ zum Arbeitsverzeichnis. Liegt `Gruppe15/` unter `agents/` und der Prof übergibt `Gruppe15/agent.pth`, fand `Agent_x` die Datei nicht und spielte **still untrainiert mit Standard-Config** (nur eine Konsolenzeile).
- **Änderungen:**
  - `agents/sherlock/main.py`: `resolve_weights` nimmt bei fehlendem Pfad die gleichnamige `.pth` direkt neben `main.py`; vorhandene Pfade bleiben unverändert, im Repo liegen dort keine `.pth`. Zusätzlich `Agent = Agent_x`, weil das Beispiel des Profs `Gruppe21.main.Agent` lautet. Spielverhalten unverändert.
  - `scripts/build_submission.py --battle`: baut `Gruppe15.zip` im Projektordner mit `Gruppe15/` (Quellcode, `agent.pth`, `agents.yaml`, `LIESMICH.txt` mit Pfaden und Paths.csv-Zeile). Gleiche Gewichte für beide Seiten stehen einmal als `agent.pth` darin, sonst `agent_0.pth`/`agent_1.pth`. Die Prüfung entpackt in eine nachgebaute Vorlage (mit `agents/__init__.py`, das alle Unterpakete importiert) einmal unter `agents/` und einmal in der Wurzel. `dist/agent.zip` wie bisher.
  - `.gitignore`: `/Gruppe*.zip`. Neue Tests `tests/test_battle_submission.py` (7).
- **Für Moodle:** Datei `Gruppe15.zip` (11,9 MB), Agent-Klasse `Gruppe15.main.Agent_x`, Gewichte `Gruppe15/agent.pth` für Player 0 und Player 1. Enthaltene `agent.pth` = Abgabe V10, SHA-256 `03cf8bdc…8c67`.
- **Prüfungen:** gesamte Testsuite **559 bestanden** (+14 Untertests). `--battle`-Prüfung in beiden Ordnerlagen: 18 Netze, `env_steps=909000`, „Check ok“. Kopie der Original-Vorlage `~/Documents/AnwendKiLux` (nur im Scratchpad, Original unverändert), Zip nach `agents/`, Paths.csv-Zeile `15;Gruppe15.main.Agent_x;Gruppe15/agent.pth;Gruppe15/agent.pth`, unveränderter Runner mit `train=False`: 15 vs 2, 2 vs 15, 15 vs 1, 3 vs 15 je 2 Spiele, alle 8 mit 303 Schritten ohne Fehler, Sherlock gewann 7 (eine Niederlage 1:2 gegen Solution_92); reiner Funktionstest, keine Leistungsmessung. Agent-Code parst mit Python 3.9; Checkpoint lädt mit `weights_only=True` (nur Tensoren und einfache Werte). Abgabe-Gewichte vorher und nachher `03cf8bdc…8c67`.
- **Offen:** Hochladen und Pfade an den Prof schicken (Mahmoud/Moayed). Deadline-Datum im Team bestätigen. Wird bis dahin ein Kandidat nach den Gates übernommen, Zip mit `python -m scripts.build_submission --battle` neu bauen. Nicht getestet: Windows und CUDA (der Agent nutzt CUDA automatisch, falls vorhanden).

## 26.10.2026, 21:50 Berlin – Claude Code mit Mahmoud: Gegner-Liga abgeschlossen, kein Kandidat, V10 bleibt

- Die Studie lief vollständig nach dem [festen Plan](superpowers/plans/2026-10-26-league.md), der Code blieb durchgehend auf `6f5cde7`. Training: 6 × 4.000 Spiele `full_rules_v10` (Starts 73–78), 6 ok, 0 Fehler. Laufzeit 12:44–21:27 einschließlich der Zeit, in der der Laptop zugeklappt war; die Prozesse waren dann nur angehalten. Zeitangaben (`secs`, Laufdauer) enthalten deshalb Pausen.
- Trainingsverlauf der einzelnen Netze (ε = 0,05; Siege in den Spielen 1.000–1.999 / 2.000–2.999 / ab 3.000): Solution_92 57 / 60 / 62 %, `sol92_sq` 45 / 47 / 44 %, Pool V10 12 / 14 / 14 %, Pool V7 16 / 17 / 20 %, default 98–99 %, RushBot 100 %. Validierung nach 4.000 Spielen (16 Spiele je Netz): Solution_92 0,50–0,81, default 1,0.
- **Auswahl** auf 700000–700199 (200 Karten, beide Seiten). V10-Referenz: Solution_92 88,75 %, `sol92_sq` 80,75 %, `sol92_weak` 91,75 %, `old3_sym3` 89,5 %, default 100 %, R 87,69 %.
  - **L24** (V10 + 6 neue): R 88,50 %, Δ **+0,81 pp [−1,44; +3,12]** → Hürde +1,5 pp verfehlt. Je Gegner: Solution_92 +0,75 [−2,75; +4,25], `sol92_sq` +1,75 [−1,75; +5,25], `sol92_weak` −1,75 [−4,75; +1,25], `old3_sym3` +2,5 [−2,0; +7,0], default 100 %. Direkt gegen V10 52,5 % [45,5; 59,5] aus 400 Spielen.
  - **L6** (nur die 6 neuen): R 85,44 %, Δ −2,25 [−5,44; +0,75]; Solution_92 88,0 % (−0,75 [−5,0; +3,25]), `sol92_weak` −5,5 [−9,5; −1,75], default 99,5 %, direkt 40,0 % [33,5; 47,0] → R- und Direkthürde verfehlt.
- **Ergebnis nach Plan: kein Kandidat, Studie beendet, V10 bleibt Abgabe.** Abgabe-Dateien vorher und nachher `03cf8bdc…8c67`. Bestätigungsblock 701000–701799 und Direktblock 702000–702399 für Kandidaten unbenutzt. Auf 701000–701799 lief nur die V10-Referenz (je 1.600 Spiele: Solution_92 90,2 %, `sol92_sq` 78,9 %, `sol92_weak` 90,5 %, `old3_sym3` 89,9 %, default 100 %). Reserve 703000–703999 unbenutzt.
- Einordnung: Das Training gegen die gemischte Liga hat die Netze nicht messbar robuster gemacht. Die 6 neuen Netze allein liegen gegen Solution_92 fast gleichauf mit den 18 V3-Netzen, sind aber gegen `sol92_weak` und im Direktduell schwächer. Zusammen mit dem 22.10.: Zusätzliche DQN-Netze heben V10 nicht über das Plateau von rund 90 %. Schwächster Gegner bleibt `sol92_sq` mit 79–81 %.
- Daten im Repo: `experiments/pipeline_league.log`, `experiments/batch_20261026_league.log`, `experiments/compare/league/*.csv`, Logs, CSVs und Manifeste der 6 Läufe. Nur lokal (gitignored): Netzgewichte und die Ensembles `experiments/ensembles/league_mix24.pth` (`e3cc8c64…`) und `league_nets6.pth` (`357c3daa…`).
- Prüfungen: Pipeline mit Exit 0, alle Messdateien ohne ausgeschlossene Karten, Hürden mit `scripts/league_gates.py`, Werte je Gegner mit `compare_report.compare_results` nachgerechnet. Kein neuer Code.
- Offen, noch nicht begonnen: Vorschlag für den nächsten Schritt sind die Niederlagen von V10 gegen `sol92_sq` gezielt zu untersuchen, wie beim Weg von V3 zu V10.

## 26.10.2026, 12:45 Berlin – Claude Code mit Mahmoud: Gegner-Liga-Training gestartet (abgeschlossen, Ergebnis 21:50)

- Auftrag Mahmoud („ja los beginn“): weiter trainieren, damit Sherlock gegen die Agents der anderen Teams robuster wird. [Fester Plan mit Hürden](superpowers/plans/2026-10-26-league.md), Ablauf `bash scripts/pipeline_league.sh`, Log `experiments/pipeline_league.log`.
- Neu und getestet:
  - Gegnerplan `league` (`scripts/protocol.py`, `--opponent-plan league`).
  - Frühe Prüfung fehlender Pool-Dateien. Vorher spielte ein fehlender Checkpoint still untrainiert. Bei gleichen Dateinamen heißen Pool-Gegner nach ihrem Ordner, Pfad und SHA-256 stehen im Manifest.
  - Variante `full_rules_v10` und Schalter `rules_in_training_all`: `sap_still` und Nebel-Meidung jetzt auch im Training.
  - Prüfskript `scripts/league_gates.py`.
  - Tests `tests/test_league.py` (9) und `tests/test_league_gates.py` (6). Die zwei Trainings-Regeltests sind ohne die Änderung rot und mit ihr grün.
- Prüfungen: gesamte Testsuite **552 bestanden** (+14 Untertests). V10-Spielverhalten unverändert: Die 10 Diagnosespiele 690000–690004 lieferten mit dem neuen Code bitgleich dieselbe Auswertung (36.258 Entscheidungen samt Beispiel-Q-Werten). Probelauf mit je einem Trainingsspiel gegen `sol92_sq`, RushBot, V10-Pool und Solution_92 (Karten 495000–495003, nur Scratchpad). Panel-Messung, Direktduell und Prüfskript auf 2 Karten durchlaufen (nur Scratchpad).
- Läuft: Training (6 Prozesse) und parallel mit niedriger Priorität die V10-Referenz auf den Blöcken 700000–700199 und 701000–701799. Code bleibt bis Studienende eingefroren. Abgabe unverändert V10 `03cf8bdc…8c67`.

## 26.10.2026 Berlin – Claude Code mit Mahmoud: Review-Feedback, Erklärung des Entscheidungsablaufs

- **Feedback des Profs aus der Review (laut Mahmoud):** beim nächsten Mal genau erklären, (1) was Action Masking ist, (2) wie der Entscheidungsprozess abläuft (wer was bekommt und was liefert) und (3) wie die 18 Netze auf die Spiele verteilt werden. Außerdem weiter trainieren; bald folgen Kämpfe gegen die Agents der anderen Teams, dafür muss Sherlock stärker werden.
- Neu `Sherlock_Entscheidungsprozess.md` (Projektordner): Kurzfassung zum Sprechen, Antworten auf die drei Fragen, Ablauf eines Steps mit Dateien/Funktionen, 79 Merkmale, Netz und Ensemble, Maske (Training und Spiel), Regeln mit Häufigkeit, vier echte Entscheidungen mit Q-Werten, Training der drei Netzgruppen, mögliche Rückfragen. Kernpunkt zu (3): Die Netze werden **nicht** auf Spiele verteilt; alle 18 bewerten jede Unit in jedem Step, gemittelt wird je Aktion.
- Neu `scripts/decision_trace.py` (reine Diagnose, Gewichte nur gelesen) und `tests/test_decision_trace.py`. Messung `experiments/analysis/decision_trace_20261026.json`: 10 Diagnosespiele gegen Solution_92 (Karten 690000–690004 × beide Seiten, **kein Leistungsnachweis**), 36.258 Unit-Entscheidungen. Im Mittel 4,3 von 6 Aktionen erlaubt; die Lieblingsaktion des Ensembles war in 20,4 % verboten (Sap ohne Ziel 9,8 %, Züge 10,6 %); alle 18 Netze einig in 31,9 %, im Mittel 13,4 von 18; Mittelwert ≠ Mehrheitswahl in 7,7 %; **Netzwahl unverändert in 92,4 %**, Regeln ändern 7,3 % (vor allem `scripted_explore` 4,3 %, weiche Nebel-Meidung 1,2 %, `sap_no_overkill` 0,9 %, `path_fix` 0,6 %, `pt_sap` 0,5 %).
- Prüfungen: **gesamte Testsuite 537 bestanden** (+14 Untertests, darunter 3 neue); Messung zweimal (Entwurf und Repo-Skript) mit identischen Zahlen; Abgabe-Gewichte vorher und nachher `03cf8bdc…8c67`. Alle Zahlen der Erklärung gegen Code, Checkpoint (`cfg`, `ensemble_sources`), Laufmanifeste `20261019_full_rules_*` (Gegnerzählung aus `train.csv`) und Übernahmeberichte abgeglichen. Kein Training.
- Folien dazu: `Sherlock_Entscheidungsablauf_Folien.pdf` (Projektordner, 6 Folien + 1 Reserve im Design vom 23.10.), Quelle `docs/presentation/Sherlock_Entscheidungsablauf.html`. Sprechtext je Folie (zusammen etwa 3:30) in `Sherlock_Entscheidungsprozess.md`. Alle Seiten als Bild geprüft, Zahlen aus der Messung oben. Vorschlag: in den nächsten Hauptfoliensatz übernehmen, dort statt der Pseudocode-Folie „Sherlock heute“.
- Auf Mahmouds Wunsch („push alles“) außerdem nachgereicht: die lokalen Vorschaubilder `docs/presentation/bild_0611_*.png` vom 22.10. sowie Logs, CSVs und Manifeste der Läufe und Entwicklungsmessungen vom 22.10. Gewichte und Buffer bleiben per `.gitignore` lokal. Bewusst nicht übertragen: `.DS_Store` und die Dateien der laufenden Liga-Studie (folgen mit ihrem Ergebnis).
- Weiteres Training läuft, siehe Eintrag 12:45 oben.

## 22.10.2026, 17:40 Berlin – Codex mit Moayed: V10-Korrekturen abgeschlossen, V10 bleibt aktiv

- **Abschluss vor der Review auf Moayeds Wunsch.** Die bereits zugelassene Bestätigung wurde beendet; keine neuen Trainings, Direktduelle oder weiteren Gegnerblöcke. Alle eigenen Spielprozesse sind beendet. Keine Verbesserung als bestätigt ausgegeben, keine Abgabe ersetzt. [Vollständiger Bericht für Mahmoud](../experiments/analysis/v10_mechanics_20261022/RESULTS.md), [Reproduktion und Belege](../experiments/analysis/v10_mechanics_20261022/README.md).
- Zwei Fehler separat korrigiert und technisch geprüft: mögliche Energie-Erholung eines beschossenen Gegners (`sap_overkill_recovery`, Commit `75e71c0`) und veraltete Sichtmasken bei erkannter Terrain-Drift (`nebula_infer_drift_safe`, `9e5206b`). Beide bleiben **standardmäßig aus**. Regeln und Gedächtnis wurden als Versuchsoption erweitert; keine Netze neu trainiert.
- **8.800 Vergleichsspiele vollständig ausgewertet.** Auswahl: 200 Karten × beide Seiten, vier Varianten gegen Solution (1.600 Spiele), anschließend V10 und Energie-Korrektur gegen default (800). Nur Energie-Korrektur nominiert: 367/400 statt 363/400 gegen Solution, je 400/400 gegen default. Karten-Korrektur 359/400, Kombination 362/400; keine nachträgliche Kandidatenänderung.
- **Unabhängige Bestätigung auf 800 neuen Karten, beide Seiten:** je Variante 1.600 Spiele gegen Solution und 1.600 gegen default, zusammen 6.400. Solution: V10 **1.448/1.600 = 90,50 %**, Energie-Korrektur **1.437/1.600 = 89,8125 %**; Δ **−0,6875 pp**, gepaarter 95-%-Bereich **[−1,50; +0,125] pp**. Geforderter Gewinn nicht bestätigt; auch keine statistisch gesicherte Verschlechterung. Default jeweils **1.599/1.600 = 99,9375 %**. Somit keine qualifizierte neue Version, Ziel 100 % gegen Solution nicht erreicht.
- Unabhängige Datenprüfung bestätigt alle 6.400 geplanten Zeilen, Quellen-/Gewichtsbindung, Spielabschlüsse und Statistik. Bootstrap: 5.000 Ziehungen ganzer Karten, beide Seiten zusammen; Auswahl und Bestätigung getrennt. Alle Leistungsspiele unter eingefrorenem Commit `de2e95d`, 128 Quellen-/Umgebungsdateien und unveränderten Gewichten. Abschlussbegrenzung vor den Ergebnissen des Bestätigungskandidaten dokumentiert; Direkt-/Robustheitsblöcke wurden **nicht ausgeführt**, nicht als gescheitert gezählt.
- Technische Prüfungen: **527 Tests + 14 Untertests** vor den Messungen; acht Kompatibilitätsspiele mit identischen Aktionen und Nicht-Zeitmetriken bei ausgeschalteten Schaltern; acht Kurs-Runner-Spiele mit beiden Schaltern an; temporäres Paket „Check ok“; alle 264 Tensoren identisch. Nach Integration von Mahmouds Demo-/Präsentations-Commits bis `11c62f5`: **7 zusätzliche Demo-Integrationstests bestanden**. Präsentation und Stichpunkte für den 23.10. sind lokal aktuell und wurden in diesem Abschluss nicht verändert.
- Aktive V10-Dateien und Sicherung `experiments/releases/20261022_v10_baseline/` unverändert, SHA-256 **`03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67`**. Die abgeschalteten Korrekturen verändern das vorgeführte V10-Verhalten nicht. Fremde lokale ungesicherte Dateien bleiben erhalten.
- **Für später, kein laufender Auftrag:** Kämpfe um gemeinsame Relic-Haufen gezielt untersuchen; Mahmouds `tactics.py`-Entwurf ist durch diese Arbeit nicht validiert. Keine weitere Studie vor der Review begonnen. Seeds 610100–610299 und 611000–611799 sind verbraucht; reservierte Direkt-/Robustheitsblöcke 612000–612399 und 613000–613099 wurden von dieser Studie nicht benutzt.

## 22.10.2026, 16:20 Berlin – Claude Code mit Mahmoud: Demo-Seite statt Dialogfenster

- Auf Mahmouds Wunsch die App „Sherlock Demo“ übersichtlicher gestaltet. Ein Doppelklick startet `scripts/demo_server.py` (nur 127.0.0.1:8615) und öffnet die Demo-Seite `scripts/demo_page.html` im Design der Folien. Dort Gegner (Solution_92, default, Prof-DQN) und Seite (Spieler 1 blau, startet oben links; Spieler 2 rot, unten rechts) wählen. Jedes Spiel läuft als eigener Prozess über `scripts.play_and_view` (unveränderter Kurs-Runner, `train=False`).
- Ergebnisleiste mit Sieger je Match, eingebetteter Lux-Viewer (an die Fenstergröße angepasst, Karte und Steuerung ohne Scrollen sichtbar), „Nochmal“, Verlauf aus `replays/demo_verlauf.jsonl` (gitignored), „Demo beenden“; sonst endet der Server nach zwei Stunden ohne Anfrage. Startet die Seite nicht, bietet die App das bisherige Spiel mit Dialogfenstern an. Eigenes App-Symbol; Bau mit `sh scripts/build_demo_app.sh`.
- `scripts.play_and_view`: neu `--json` und Sieger je Match; die bisherige Ausgabe bleibt gleich.
- Prüfungen: `tests/test_demo_server.py` (4) und `tests/test_play_and_view.py` (3) bestanden; **gesamte Testsuite 534 bestanden** (+14 Untertests). Echtes Spiel über die Schnittstelle (7 s). In Chrome durchgeklickt: Auswahl, Spiel starten, Ergebnis mit Viewer, Abspielen, „Nochmal“, Verlauf, „Demo beenden“; keine Konsolenfehler. Startlogik der App per `osascript` auf Ersatzport geprüft (Start in 1 s, zweiter Start nutzt laufenden Server). Dabei behoben: Der erste Startbefehl hielt `do shell script` bis zum Serverende fest. Gewichte unverändert `03cf8bdc…8c67`.
- Hinweis: Der erste Start der neu gebauten App fragt wieder nach Zugriff auf „Dokumente“.

## 22.10.2026, 15:50 Berlin – Claude Code mit Mahmoud: Demo per Doppelklick

- Neu `scripts/sherlock_demo.applescript`, gebaut als `Sherlock Demo.app` im Projektordner (seit 22.10., 15:55 mit im Repo; nach Änderungen am Quelltext neu bauen mit `osacompile -o "Sherlock Demo.app" scripts/sherlock_demo.applescript`). Doppelklick → Gegner wählen (default, Prof-DQN, Solution_92) → `scripts.play_and_view` läuft → Replay öffnet sich im Browser, Ergebnisfenster mit „Nochmal“.
- Prüfungen: Kompilieren ohne Fehler; Ordnersuche, Aufruf und Auswertung der App ohne Dialoge per `osascript` getestet (App im Projektordner, App auf dem Schreibtisch mit Standardpfad, Quelltext in `scripts/`), drei Spiele gegen Solution_92, Prof-DQN und default jeweils 3:0 gewonnen. Die Dialoge selbst nicht automatisch geklickt; beim ersten Start fragt macOS nach Zugriff auf „Dokumente“. **Mahmoud hat die App per Doppelklick erfolgreich ausprobiert.** Gewichte unverändert.

## 22.10.2026, 15:45 Berlin – Claude Code mit Mahmoud: Live-Demo mit automatischer Visualisierung

- Neu `scripts/play_and_view.py`: spielt ein Spiel über den unveränderten Kurs-Runner (`run_agents`, `train=False`), verpackt das Replay wie `luxai-s3 --output replay.html` in eine HTML-Datei mit dem offiziellen Viewer (s3vis.lux-ai.org, braucht Internet), gibt das Matchergebnis aus und öffnet die Datei im Browser. Optionen `--gegner default|solution|dqn`, `--seite 1`, `--no-open`. Ausgaben nur unter `replays/` (gitignored).
- Prüfungen: `tests/test_play_and_view.py` 2 bestanden; zwei echte Spiele (gegen Solution_92 als player_0, gegen default als player_1), beide 3:0 gewonnen; erzeugte HTML-Datei in Headless-Chrome mit geladenem Viewer kontrolliert; Abgabe-Gewichte unverändert `03cf8bdc…8c67`. README und Stichpunkte (Abschnitt „Live-Demo“) ergänzt.

## 22.10.2026, 15:25 Berlin – Claude Code mit Mahmoud: Präsentation für den 23.10.

- Laut Mahmoud ist die Präsentation am **23.10.** In `CLAUDE.md` steht für die Zwischenpräsentation der 06.11.; Termin bitte im Team bestätigen. Folien und Stichpunkte tragen deshalb das Datum 23.10.
- Folien `Sherlock_Review_23-10-2026.pdf` (Projektordner, 13 Vortragsfolien + 2 Reservefolien im Design vom 16.10.), Quelle `docs/presentation/Sherlock_Review_23-10-2026.html` mit Bildern `docs/presentation/folie_2310_*.png` und Diagrammskript `docs/presentation/source/fortschritt_2310.py`. Stichpunkte zum Üben `Sherlock_Stichpunkte_23-10-2026.md` (Vorschlag: Moayed Folien 1–4, 8–10 und 13 = 5:10, Mahmoud 5–7 und 11–12 = 4:30). Plan und Belege: `docs/presentation/VORTRAGSPLAN_2310.md`.
- Kernaussage gegenüber dem Entwurf vom Morgen korrigiert: 47 → 78 % kam aus Regeln, Neutraining mit aktiven Regeln und `reward_fix` sowie 18 statt 6 Netzen (Arbeitsstand 19./20.10.); 78 → 90 % kam aus der Fehlersuche mit denselben 18 Netzen. Danach brachten CNN/PPO, Gefahrmerkmale und weitere Netze keinen Gewinn.
- Prüfungen: alle 15 Seiten als Bild kontrolliert. Zahlen gegen Übernahmeberichte, Nachtbericht, Arbeitsstand, Checkpoint (79 Merkmale, 18 Netze, Mittelwert der Q-Werte) und Engine-Parameter (Sap-Kosten 30–50, Reichweite 3–7, Drift alle 7–40 Schritte) abgeglichen. Für ein mögliches Battle: unveränderter Kurs-Runner mit installierter V10 auf `main` `de2e95d` **8 Spiele bestanden** (`act` höchstens 11,4 ms), `scripts.build_submission` „Check ok“ (Zip nur in einem temporären Ordner). Gewichte unverändert `03cf8bdc…8c67`. Kein Training, keine neuen Messspiele.
- Offen: Moayed prüft seine Folien und probt mit Uhr. Keine PowerPoint-Fassung; präsentiert wird das PDF. Nur lokal bei Mahmoud, nicht übertragen: vierteilige Vorversionen `docs/presentation/bild_0611_*.png`.

## 22.10.2026, 13:54 Berlin – Codex mit Moayed: V10-Mechanikkorrekturen vorbereitet, Abgabe bleibt V10

- Auftrag: lokales Repo aktualisieren, zwei im Review reproduzierte Fehler korrigieren und gegen V10 messen. `main` zunächst auf `c78732f`, danach Mahmouds reinen Ergebniscommit `bb7e84b` übernommen (12 neue Netze ohne belegten Gewinn). Fremde unversionierte Dateien erhalten.
- Zwei getrennte, standardmäßig ausgeschaltete Schalter: `sap_overkill_recovery` berücksichtigt maximale mögliche Feld-Erholung vor dem Absagen weiterer Saps; `nebula_infer_drift_safe` unterbindet zeitlich falsche Nebel-Inferenz bei erkannter Terrain-Drift. Nicht erkannte Drift und bewegte Ziele bleiben dokumentierte Grenzen. Keine Netzparameter geändert.
- V10 bytegleich unter `experiments/releases/20261022_v10_baseline/` gesichert; beide aktiven Gewichte weiterhin `03cf8bdc…8c67`. Neue Schalter bleiben aus, bis ein Kandidat alle vorab definierten Bedingungen erfüllt.
- Technische Prüfung: Regressionen zunächst rot, anschließend grün; vollständige Suite **527 Tests + 14 Untertests bestanden**; unabhängiges Code-Review ohne blockierende Befunde. Original und neuer Code mit Schaltern aus: je vier Spiele, **1.212 Schritte**, sämtliche Aktionen beider Spieler und sämtliche Nicht-Zeit-Metriken identisch.
- [Fester Vergleichsplan](superpowers/plans/2026-10-22-v10-mechanics.md): vier Varianten auf 200 Auswahlkarten 610100–610299, höchstens ein Kandidat. Nur bei bestandener Auswahl: 800 frische Bestätigungskarten 611000–611799, 400 Direktkarten 612000–612399 und 100 Robustheitskarten 613000–613099. Diese Blöcke sind reserviert; nicht parallel verwenden. Höchstens zwei Worker, unveränderter Code über die gesamte Messung. **Noch kein Leistungsnachweis und keine Übernahme.**
- Prüfbelege und später Rohdaten: `experiments/analysis/v10_mechanics_20261022/`. Der vorhandene `tactics.py`-Entwurf ist durch diese Arbeit nicht validiert oder eingebunden; vor Nutzung sind seine Engine-Abweichungen separat zu prüfen.

## 22.10.2026, 13:50 Berlin – Claude Code mit Mahmoud: 12 neue Netze, kein Gewinn gegenüber V10

- Zweite Trainingsreihe `full_rules_v8` (Starts 60–62/90–92, je 3000 Spiele) abgeschlossen; damit 12 Netze unter V8-Bedingungen. Entwicklung (V10-Config): **18 alte + 12 neue (`v10mix30`) 79,2/95,8 % → geschätzt 90,3 % (= V10)**, nur die 12 neuen (`v10nets12`) 76,5/95,2 % → 89,1 % (6 neue: 86,8 %). Mit V8-Config `v8mix24b` siehe `experiments/pipeline_v8nets_b.log`.
- Schluss: Weder kleine Regeln (Plateau 90–91 %) noch zusätzliche Netze verbessern V10 klar. **V10 bleibt Abgabe.** Für einen weiteren Sprung bräuchte es einen größeren Ansatz für die Kämpfe um gemeinsame Relic-Haufen (z. B. Planung mit dem geprüften Ein-Schritt-Simulator `agents/sherlock/tactics.py`).
- Für die Präsentation am 06.11. lokal erzeugt, nicht gepusht: `docs/presentation/bild_0611_*.png` (Vorher/Nachher zu Kartenfehler, Sackgasse, Mehrfach-Saps; Fortschrittsbalken), Verweise im lokalen `VORTRAGSPLAN_0611_ENTWURF.md`.

## 22.10.2026, 12:15 Berlin – Claude Code mit Mahmoud: Plateau um 90–91 % gegen Solution_92

- Auf V10 gemessen (Entwicklung, geschätzt gesamt; V10 90,3 %): `cand_rescue` mit `rescue_after=30` **91,0 %** (bester Einzelschalter, rettet 0-Punkte-Spiele), V10 + 6 neue Netze 90,8 %, beides zusammen 91,0 % (nicht additiv), `dodge` mit Köder 90,5 %, `stage_attack` (gemeinsam in die Schusszone) 90,3 %, `sap_kill_safe` 90,1 %, `art_still` 90,0 %, `sap_reserve_k=0.5` 89,0 %. Kein Bündel liegt um +2 pp vor V10 → **kein Prüflauf, V10 bleibt**.
- Verbleibende Niederlagen sind vor allem Kämpfe: ein gemeinsamer Relic-Haufen, Solution_92 kommt mit mehr Units zuerst an, unsere Units werden einzeln abgeschossen (z. B. 361038). Pro Verlustspiel ~27 Tode durch Saps.
- Läuft: 6 weitere Netze (`pipeline_v8nets_b.sh`, Ende ~13:45), danach Ensembles aus 18 alten + 12 neuen bzw. 12 neuen Netzen.

## 22.10.2026, 11:25 Berlin – Claude Code mit Mahmoud: Robustheit von V10, nächste Kandidaten

- **Robustheit gegen andere Spielweisen** (neue Gegner in `scripts/style_opponents.py`, je 100 frische Karten 509220–509319, nur Information): Prof-DQN, Zufall, RushBot je **100 %**, Solution_92 mit Ziel „schwächster Gegner“ 90,5 %, alte Abgabe `old3_sym3` 89 %, CNN-PPO `cnn3_ppo0050` 88 %, **Solution_92 mit Sap im ganzen Quadrat 74,5 %** (Original auf denselben Karten 89 %). V3 fällt gegen die Quadrat-Variante gleich stark (78 → 62,5 %): dieser Gegner ist stärker, keine V10-spezifische Lücke. Auf 509420–509619 V10 gegen die Quadrat-Variante 83,5 %. `art_safe_cheb` (Artillerie-Sicherheit im Quadrat) ohne Gewinn.
- **`cand_rescue` mit `rescue_after=30`** (Kandidaten gezielt testen, nur wenn ein Relic seit ≥ 30 Steps bekannt ist und noch kein Punkte-Tile): rettet die 0-Punkte-Spiele 361050/361255, Entwicklung 78,8/97,0 % (geschätzt 91,0 %, V10 90,3 %). Ohne Verzögerung schlechter (78,9/94,9 %).
- Neue Netze allein (`v10nets6`, 6 Netze mit V10-Config) 73,6/93,3 % (geschätzt 86,8 %); gemischt mit den 18 alten (`v10mix24`) 79,2/96,4 % (90,8 %). Weitere 6 Netze trainieren seit 11:22 (`scripts/pipeline_v8nets_b.sh`); Bündel V10 + neue Netze + `cand_rescue` läuft (`D22_v10mix24cr`).
- Ein Nachfolger wird erst gegen V10 geprüft, wenn ein Bündel in der Entwicklung klar vorn liegt (die Gates verlangen +2 pp auf 800 frischen Karten).

## 22.10.2026, 10:40 Berlin – Claude Code (autonom): Training ausgewertet, Testsuite mit V10 sauber

- **Gesamte Testsuite ohne laufende Jobs: 495 bestanden** (V10 installiert, `03cf8bdc…8c67`). Damit ist der offene Prüfpunkt der V10-Übernahme erledigt.
- 6 Netze unter V8-Bedingungen trainiert (`full_rules_v8`, `rules_in_training`, Starts 70–72/80–82, je 3000 Spiele). Entwicklung gemischt mit den 18 V3-Netzen: `v8mix24` 75,3/96,4 % (V8 73,0/97,6, gesamt gleich), **`v10mix24` 79,2/96,4 % (geschätzt 90,8 %, V10 90,3 %)**, also +0,45 pp und damit unter der üblichen Schwelle von +0,5. Kein neuer Prüflauf. V10 bleibt.

## 22.10.2026, 09:50 Berlin – Claude Code (autonom): V10-Feinschliff ohne Gewinn, Training läuft

- Auf V10 ohne Gewinn: `art_still` (Artillerie nur auf stehende Ziele) 77,7/96,0 % (−0,3), `sap_reserve_k=0.5` 76,5/94,9 % (−1,5). V10 bleibt unverändert.
- Training `full_rules_v8` (6 Netze unter V8-Bedingungen) bei ~2000/3000 Spielen, Ende gegen 10:25. Danach automatisch: `v8mix24` (V8-Config) und `v10mix24` (V10-Config, 18 V3-Netze + 6 neue) auf den Entwicklungs-Sets (`experiments/pipeline_v8nets.log`, `experiments/dev_v10mix24.log`). Ein Nachfolger würde nur über einen neuen, vorab festgelegten Plan gegen V10 geprüft.
- Vortragsentwurf `docs/presentation/VORTRAGSPLAN_0611_ENTWURF.md` lokal auf V10 aktualisiert (Kernaussage „von 47 % auf 90 %“), **nicht gepusht**, wartet auf Mahmouds OK.

## 22.10.2026, 09:25 Berlin – Claude Code (autonom): **V10 als Abgabe übernommen – 90,3 % gegen Solution_92**

- **V10 (`v10_V8st`) = V8 + `sap_still`** hat alle vorab festgelegten Gates gegen V7 bestanden ([Plan](superpowers/plans/2026-10-22-v10.md), [Übernahmebericht](../experiments/analysis/release_20261022_v10/RELEASE.md)): frisch auf 800 Karten 507420–508219 **Solution_92 90,3 % statt 82,8 % (Δ +7,5 [+5,4; +9,6])**, default 99,75 % (Δ −0,2), **direkt gegen V7 58,1 % [53,1; 62,75] aus 800 Spielen**.
- Übernahme per `scripts/release_candidate.py`: V7 bytegleich gesichert (`experiments/releases/20261022_v7_Bsnpd/`, SHA-256 `c394acba…95e6`), V10 installiert (`03cf8bdc…8c67`), **Kurs-Runner unverändert: 8 Spiele bestanden** (`act` max. 11,3 ms).
- Testsuite nach der Installation: 463 bestanden, 31 Studientests von der Schutzsperre abgewiesen (Training `full_rules_v8` lief). Wiederholung ohne Jobs folgt nach Trainingsende.
- Damit erledigt: V8-Teamentscheidung (V10 enthält V8). Ziel ≥ 90 % gegen Solution_92 auf frischen Karten erreicht.

## 22.10.2026, 08:30 Berlin – Claude Code (autonom): V10 in Prüfung gegen V7

- Auf V8 nachgemessen: **`sap_still`** (Halter-Saps nur auf stehende Gegner) **77,9/96,4 % → geschätzt ≈ 90,3 %** gegen Solution_92 (V8 89,5); `art_min_hits=4` 72,1/96,9 (schlechter).
- **[V10-Plan](superpowers/plans/2026-10-22-v10.md)** vorab festgelegt: V10 = V8 + `sap_still` (`experiments/ensembles/v10_V8st.pth`, SHA-256 `03cf8bdc…8c67`), gegen **V7** auf den unbenutzten V9-Blöcken: Auswahl 507220–507419, frisch 507420–508219 (800 Karten), direkt 508220–508619 (800 Spiele). Läuft seit 08:24 (`experiments/pipeline_v10.log`).
- Abgabe-Pruefung `agent.zip` mit V7 lokal gebaut: „Check ok“ (Import über den Kurs-Runner-Lader, Pflichtmethoden, beide Seiten, ein Aktionsschritt). `agents/sherlock/tactics.py` als Entwurf committet (nicht eingebunden).
- Training `full_rules_v8` läuft (6 Netze, ~10:15 fertig, danach Messung `v8mix24`).

## 22.10.2026, 08:00 Berlin – Claude Code (autonom): kein V9, Bericht der Nacht

- **Zusammenfassung der Nacht für Mahmoud/Moayed: [Nachtbericht V7/V8](NACHT_V7_V8_20261022.md)** (Änderungen in einfacher Sprache, Zahlen, Entscheidungsvorlage V8 mit Übernahmeweg).
- [V9-Plan](superpowers/plans/2026-10-22-v9.md): `mobile_seen` (−0,2), `obey_target` (−0,8) und `neb_cand`+`idle_approach` (−0,8, Fix für den Nebel-Relic-Fall 361050) verbessern V8 nicht → kein V9-Ablauf, Blöcke 507220–508619 unbenutzt. Kleine Regeländerungen um V8 liegen alle zwischen −2 und +0,2 pp: V8 ist für diesen Ansatz ein Plateau.
- Info-Duelle **nur für die Teamentscheidung** (kein Gate, nach dem V8-Gate erhoben): **V8 gegen V7 59,9 % [55,0; 64,75] aus 800 Spielen**, V8 gegen V3 75,0 % [69,0; 81,0] aus 400 Spielen (`scripts/info_duels_v8.sh`). Empfehlung im [Nachtbericht](NACHT_V7_V8_20261022.md): V8 übernehmen, als bewusste Teamentscheidung.
- Training läuft: 6 Netze unter V8-Bedingungen (`full_rules_v8`, `rules_in_training`), danach Messung `v8mix24` gegen V8 (`scripts/pipeline_v8nets.sh`).
- Abgabe: **V7** (`c394acba…95e6`).

## 22.10.2026, 07:30 Berlin – Claude Code (autonom): V8 knapp nicht übernommen, Testsuite sauber

- **V8** ([Plan und Ergebnis](superpowers/plans/2026-10-22-v8.md)), frisch auf 800 Karten 506220–507019: **Solution_92 89,1 % statt 84,6 % bei V7 (Δ +4,5 [+2,6; +6,4])**, default 100 %. **Direkt gegen V7 56,5 % [49,5; 63,5]** → die vorab festgelegte Hürde „untere Grenze > 50 %“ um 0,5 pp verfehlt → **V7 bleibt Abgabe**. V8 = V7 + `reach_assign` + `sap_no_overkill` + `safe_moves` + `collision_guard`, Checkpoint `experiments/ensembles/v8_Bsnpdroc.pth` (lokal, SHA-256 `13023d74…d60c`, gitignored; bauen mit `python -m scripts.set_cfg experiments/ensembles/v7_Bsnpd.pth <ziel> reach_assign=true sap_no_overkill=true safe_moves=true collision_guard=true`). **Entscheidungsvorlage für Mahmoud/Moayed**: gegen Solution_92 und default nachweislich besser, im direkten Vergleich gegen V7 nicht nachweislich.
- **Gesamte Testsuite ohne laufende Messung: 491 bestanden** (07:25, V7 installiert). Damit ist der offene Prüfpunkt der V7-Übernahme erledigt.
- Nach V8 gemessen, ohne Gewinn: `window_infer_all` (72,0/97,3), `dodge` lethal (73,6/97,5, +0,1), `far_opp=6` (69,8/96,0).

## 22.10.2026, 06:45 Berlin – Claude Code (autonom): V8 in Bestätigung gegen V7

- **V8 = V7 + `reach_assign` + `sap_no_overkill` + `safe_moves` + `collision_guard`** (18 V3-Netze bitgleich; [Plan mit Nachtrag](superpowers/plans/2026-10-22-v8.md)). Entwicklung 73,0/97,6 % → geschätzt **≈ 89,5 %** gegen Solution_92.
- **Auswahlblock 506020–506219: V8 85,75 % gegen V7 78,0 % (Δ +7,75 [+3,5; +12,2])**, default 100 % → Hürde (+1 pp) bestanden. Läuft: frisch 506220–507019 (800 Karten) + direkt 507020–507219 (`experiments/pipeline_v8.log`).
- Ohne Gewinn (nicht in V8): `sap_still` +0,40, `safe_moves` allein +0,45, `explore_quota=1` −4,25, `sap_still_all` (schadet), `holder_guard` +0,2.
- Neu, Default aus: `window_infer`/`window_infer_all` (Punkte-Inferenz im Relic-Spawnfenster von Match 2/3). Prüfung gegen die Wahrheit: keine falschen Punkte-Tiles, etwas mehr bekannte, aber auch etwas mehr fälschlich tote. Entwicklungsmessung läuft (`D22_V8w`), danach `dodge` lethal und `far_opp=6` auf V8.
- V8-Verlustanalyse (Karten, die V8 beidseitig verliert, 54 von 330 schweren): Match 2 fast immer verloren; pro Match 15–16 eigene Tode gegen 13 bei Solution_92, die meisten durch Saps auf stehende Halter mit wenig Energie; ~2 eigene echte Punkte-Tiles pro Step bleiben ungetestete Kandidaten.

## 22.10.2026, 06:05 Berlin – Claude Code (autonom): nächste Verbesserungen für V8

- Entwicklungsmessungen auf V7 + `reach_assign` (63,6/94,9 %, geschätzt ≈ 84,6 %): `unstack`, `sap_reserve_k=1`, `sym_map` (Spiegelung der Karte im Gedächtnis), `sap_relevant` ohne Gewinn. **`sap_no_overkill`** (keine Saps auf Gegner, die schon durch geplante Saps desselben Steps sterben) **68,5/96,0 % → geschätzt ≈ 86,9 %**. Befund dahinter: Halter feuerten zu dritt auf einen Gegner mit 21 Energie; unsere Halter haben zu wenig Energie und sterben dann an Kollisionen (im Mittel 41 gegen 102 Energie) und Void.
- Kollisionstode genauer (Verlustspiele, je Spiel): 5,5 Gegner zieht auf unsere stehende Unit, 3,4 beide ziehen auf dasselbe Tile, 1,5 wir ziehen auf einen stärkeren Gegner; Gegner fast immer vorher sichtbar. Neue Schalter `collision_guard`, `sap_still` (Default aus, Tests grün, 42 in `tests/test_rules_2110.py`); Messungen laufen (`D22_Bsnpdr{q,m,c}`, `D22_Bsnpdros`).
- Erkenntnis Spielregeln: neue Relic-Paare spawnen in Match 2/3 je bei Step 0–49 (`relic_spawn_schedule`). In Match 3 kennen wir ~2,7 echte eigene Punkte-Tiles nicht (37 % ungesehene Relics, 38 % ungetestete freie Kandidaten, 15 % Kandidaten im Nebel); Test `explore_quota=1` läuft.
- [V8-Plan](superpowers/plans/2026-10-22-v8.md) vorab festgelegt: Referenz V7, 800 frische Karten, Δ ≥ +2 pp mit unterer Grenze > 0, direkt gegen V7.
- Training: die 6 Netze mit V6-Regeln helfen gemischt nicht (`v6mix24` 53,9/93,9), allein schwach (`v6nets6` 52,0/88,4); weiteres Training gestoppt zugunsten der Regel-/Gedächtnis-Messungen.

## 22.10.2026, 05:35 Berlin – Claude Code (autonom): **V7 als Abgabe übernommen**

- **V7 (`v7_Bsnpd`) hat alle vorab festgelegten Gates bestanden** ([Plan](superpowers/plans/2026-10-22-v7.md), [Übernahmebericht](../experiments/analysis/release_20261022_v7/RELEASE.md)): frisch 505420–505819 Solution_92 **83,5 % statt 76,5 % (Δ +7,0 pp [+4,0; +10,0])**, default 99,75 % (Δ 0), **direkt gegen V3 68,0 % [61,5; 74,25]**.
- Übernahme per `scripts/release_candidate.py`: V3 bytegleich gesichert (`experiments/releases/20261022_all18_v3/`, SHA-256 `aac1c910…d935`, Wiederherstellung im README dort), V7 in `agent_p0.pth`/`agent_p1.pth` (SHA-256 `c394acba…95e6`), **Kurs-Runner unverändert: 8 Spiele bestanden** (beide Seiten, default + Solution_92, `act` max. 10,5 ms).
- Testsuite nach der Installation: 452 bestanden; 31 Studientests (`tests/test_early_curriculum_study.py`) von der Schutzsperre „Another model job is active“ abgewiesen, weil gleichzeitig eine Entwicklungsmessung lief (wie am 21.10.). Wiederholung ohne laufende Messung folgt.
- `scripts/v5_gates.py`: Mindest-Δ über `MIN_DELTA` einstellbar (Default 0,05 unverändert, V6-Entscheidung damit reproduziert); Meldung „vs Referenz“ statt „vs V3“.
- Weiter: `reach_assign` (Zielzuweisung nach BFS-Weglänge) auf V7 in der Entwicklung 63,6/94,9 % (geschätzt ≈ 84,6 %); `unstack` ohne Zusatznutzen (63,8/94,6); `sap_reserve_k=1` läuft. Nächster Kandidat V8 wird vorab gegen **V7 als neue Referenz** festgelegt.

## 22.10.2026, 05:05 Berlin – Claude Code (autonom): V7 in Bestätigung, weitere Ursachen gefunden

- **Kartenkorrekturen gemessen** (`dev_hard330`/`dev_easy330`, Solution_92; V3 27,0/100 %): Bs 48,0/97,6; + `nebula_infer` 50,6/96,3; + `path_fix` 57,4/93,9; + `drift_track` **58,3/95,1** → geschätzt gesamt ≈ 82,9 % (Bs 81,2 %, V3 75,9 %).
- **V7 = Bs + die drei Korrekturen** ([Plan, vorab](superpowers/plans/2026-10-22-v7.md)): Auswahlblock 505220–505419 **82,25 % statt 78,0 % (Δ +4,25 [+0,3; +8,3])**, default 100 % → Hürde bestanden. Frische Bestätigung 505420–505819 + direkt 505820–506019 läuft (`experiments/pipeline_v7.log`). Bei bestandenen Gates Übernahme per `scripts/release_candidate.py`.
- PPO `cnn3b`: Stände 50/100/150 alle unter V3 (bester 72,0 % gegen 76,7 %) → beendet, Bestätigungsblöcke unbenutzt.
- 6 Netze mit V6-Regeln trainiert (Starts 27–29/37–39): gemischt mit den 18 V3-Netzen (`v6mix24`, gleiche Regeln wie Bs) `dev_hard330` **53,9 % statt 48,0 %**; leichte Karten laufen.
- **Neue Diagnosen** auf Karten, die V7 noch beidseitig verliert: Zielzuweisung schickt Units zu Punkte-Tiles unter Asteroiden (unerreichbar) → `reach_assign` (BFS-Weglänge, unerreichbare Ziele zuletzt); gestapelte Units warten → `unstack`; unsere Halter haben 60–84 statt 82–115 Energie, wir sappen 2–3× so oft wie Solution_92, 70 % der Toten auf Punkte-Tiles, 74 % mit weniger Energie als ein Sap kostet (Kollision, Void, direkter Sap) → `sap_reserve_k` (Regel-Saps nur mit Reserve). Alle Default aus, Tests grün (37 in `tests/test_rules_2110.py`). Messungen laufen (`D22_Bsnpdr*`, `D22_Bsnpdru*`, danach `D22_Bsnpdrk*`).
- Training: 6 Netze `full_rules_v7` (V6-Regeln + Nebel-Inferenz + Drift im Gedächtnis). Erster Start scheiterte an der Schutzprüfung (Starts ≥ 50 lägen über 500000); `protocol.train_seed` nutzt für Starts ≥ 50 jetzt das bisher unbenutzte Blockende ab Index 5000 (Test ergänzt), Neustart 04:59 (`experiments/pipeline_v7nets.log`).
- Abgabe weiterhin **V3** (`aac1c910…d935`).

## 22.10.2026, 04:30 Berlin – Claude Code (autonom): V6 knapp unter der Hürde, zwei Kartenfehler gefunden

- **V6 = Bs** frisch 504220–504619: Solution_92 81,6 % statt 77,75 % (Δ +3,88 pp [+1,5; +6,25]), default 100 %, direkt gegen V3 67,5 % [62,25; 72,75]. Nur die Mindestgröße +5 pp verfehlt → **V3 bleibt**. Bs erfüllt die allgemeine Regel der Spezifikation vom 20.10.; Übernahme wäre eine Teamentscheidung.
- PPO `cnn3b` Stand 50: 72,0 % gegen V3 76,7 % (−4,8). Stände 100/150 laufen automatisch (`scripts/pipeline_cnn3b_eval.sh`, Log `experiments/pipeline_cnn3b.log`).
- **Verlustanalyse** (40 Karten, die Bs auf beiden Seiten verliert): Match 1 meist gewonnen, Match 2/3 verloren. (1) Die Gedächtniskarte veraltet durch Drift: im Mittel ~20 falsche und ~20 fehlende Asteroiden, 18 % der bekannten Tiles falsch. Units sitzen hinter vermeintlichen Asteroiden fest (360014: ganzes Match 3 mit 0 Energie am Spawn). (2) Greedy-Falle: Netz läuft nach Luftlinie in Sackgassen an Asteroidenwänden und pendelt (360581).
- Neu, Default aus, Tests grün (`tests/test_rules_2110.py`, 33): `nebula_infer` (unsichtbar in Sensorreichweite ⇒ Nebel), `path_fix` (BFS-Schritt statt Sackgasse), `drift_track` (Drift erkennen, ganze Karte rollen: 210/210 Drifts in 6 Spielen erkannt, falsche Tiles 78,6 → 13,5 pro Step). Grobcheck auf den 8 schlimmsten Karten (ausgewählt, nur Hinweis): 0/16 → 2/16 Siege, deutlich mehr Punkte.
- **Läuft** (Ergebnisse `experiments/compare/regeln/D22_{Bsn,Bsnp,Bsnpd}_*`, Vergleich mit `D22_Bs_*`): Bs + `nebula_infer` / + `path_fix` / + `drift_track` auf `dev_hard330`/`dev_easy330`. Training `full_rules_v6` (6 Netze, Auswertung automatisch, `experiments/pipeline_v6nets.log`).
- **Offen:** Entwicklungsergebnisse auswerten. Den besten Kandidaten (vermutlich Bs + Kartenfixes) vorab mit neuem, noch nicht reserviertem Auswahl- und Bestätigungsblock festlegen und prüfen. `agents/sherlock/tactics.py` (Ein-Schritt-Simulator, gegen die Engine geprüft) ist ein Entwurf, nicht eingebunden. Abgabe weiterhin V3 (`aac1c910…d935`).

## 22.10.2026, 03:20 Berlin – Claude Code mit Mahmoud (autonom über Nacht): V5-B knapp unter der Hürde, V6 in Bestätigung

Auftrag des Users: selbstständig weiterarbeiten bis Nachmittag, Ziel ≥ 90 % gegen Solution_92, ganze CPU nutzen; Übernahme nur über vorab festgelegte Tests.

- **V5-B** (`art_sap` 3 + `nebula_avoid` Sperre 25, 18 V3-Netze bitgleich; [Plan/Ergebnis](superpowers/plans/2026-10-22-v5-combination.md)): frisch 503420–503619 Solution_92 **75,75 % statt 71,0 %, Δ +4,75 pp [+1,0; +8,25]**, default 99,75 %, **direkt gegen V3 62,0 % [56,5; 67,25]**, Kurs-Runner bestanden. Hürde Δ ≥ +5 pp um 0,25 pp verfehlt → **nicht übernommen**, Hürde nicht nachträglich geändert. Entscheidungsvorlage für Mahmoud/Moayed.
- **Training auf schweren Karten** (6 Netze, 660 Karten mit V3-Niederlage): `hard6` 70,5 % (−6,2 gegen V3, −4,3 gegen Kontrolle), `hard24` +2,5 → kein Gewinn.
- Große Entwicklungs-Sets `dev_hard330`/`dev_easy330`: Bs (V5-B mit **weicher** Nebel-Meidung, `nebula_avoid_mode=soft`) ≈ +5,3 gesamt, beste einfache Variante. Ohne Gewinn bzw. schädlich: `stack_guard` (blockiert Wege, leichte Karten 79 %), `relic_search` (leicht −5), `sap_dropoff_est`, `art_surplus`, `fog_sap` bei Sicht ≤ 2. Neu: `dodge_verify` (Online-Prüfung des Solution_92-Modells), `dodge_auto_max`, `dodge_bait`.
- **V6 = Bs** läuft nach [vorab festgelegtem Plan](superpowers/plans/2026-10-22-v6.md): Auswahl 504020–504219 (V3 dort 77,0 %), dann 400 frische Karten 504220–504619 + direkt 504620–504819 (`scripts/pipeline_v6.sh`, Log `experiments/pipeline_v6.log`).
- Training läuft: 6 Netze `full_rules_v6` (Regeln von Bs schon im Training), Starts 27–29/37–39, Auswertung automatisch (`scripts/pipeline_v6nets.sh`). PPO `cnn3b` fast fertig; Prüfung der Stände 50/100/150 folgt laut Plan.
- Abgabe weiterhin **V3** (`aac1c910…d935`).

## 22.10.2026, 00:45 Berlin – Claude Code mit Mahmoud: versteckte Parameter, Entwicklungs-Sets, V5-Kandidaten in Auswahl

**Kartenanalyse** (`experiments/analysis/hard_map_training_20261021/map_features*.{py,csv}`, wahre Startzustände der 2000 gescreenten Karten, reine Analyse): V3 gegen Solution_92 nach verstecktem Parameter – Sap-Streufaktor 0,25/0,5/1,0: **65,9/76,3/85,4 %**; Nebelabzug 25: 65,5 % (sonst ~78 %); Bewegungskosten 1/5: 69,1/84,4 %; ≥ 14 Punkte-Tiles nahe der Diagonale: 54,7 %.

**Schnellere Entwicklung:** deterministische Spiele → feste Entwicklungs-Sets aus der Kartensuche ohne V3-Neumessung: `dev_hard150` (V3 25,0 %), `dev_easy60` (100 %), `dev_neb25_100` (64,5 %), `dev_neb5_60` (71,7 %); `scripts/par_eval.py --seed-list`, Skript `dev_eval.sh`. Kennzahl für das Gesamtbild: 0,33·Δhard + 0,67·Δeasy (Anteil schwerer Karten 660/2000).

**Ergebnisse (alle Schalter aus in der Abgabe):** hard150/easy60 gegen Solution_92 – `art_sap` 3: 37,7/98,3 (≈ +3,0 gesamt); `dodge` always: 35,0/97,5 (≈ +1,6); beides 38,7/96,7 (≈ +2,3); `art_sap` nur bei Rückstand (`tactics_when_behind`): 33,0/100 (≈ +2,6); neues `sap_kill_safe` (korrigiert `sap_kill_first`, das schon tote Gegner mit Energie < 0 bevorzugte): 33,3/98,3; mit `art_sap` 37,3/97,5. `nebula_avoid` (neue Online-Schätzung, Schwelle 25): Nebel-25-Karten 69,5 % statt 64,5 %; mit Schwelle 5 auf Nebel-5-Karten −16,7 pp → Schwelle 25.

**Online-Parameterschätzung** `agents/sherlock/param_est.py` (aus eigenen Energieverläufen, nur Beobachtungen): Nebelabzug 60/60 richtig ab Schritt 202; Streufaktor nach Filtern für wanderndes Energiefeld und fehlende Schützen **0 Fehlschätzungen in 60 Spielen**, sicher bekannt bei Schritt 101/202/300 in 25/41/47 von 60 Spielen (sonst Annahme 0,5). `dodge_auto`: Ausweichen nur bei geschätztem Streufaktor ≤ 0,5 (Entwicklung: always bei 0,25/0,5/1,0: +5,9/+2,5/−2,2).

**V5-Auswahl läuft** nach [vorab festgelegtem Plan](superpowers/plans/2026-10-22-v5-combination.md) (Kandidaten B–E, je hard150/easy60), danach Zufallsblock 503820–504019 und einmalige frische Bestätigung. Training auf schweren Karten (Lauf `_hard`) bei ~2000/3000 Spielen, Auswertung automatisch. Keine Abgabeänderung ohne Rücksprache.

## 21.10.2026, 22:50 Berlin – Claude Code mit Mahmoud: Solution_92-Modell, Ausweichen, Training auf schweren Karten läuft

Ziel des Users jetzt: 99–100 % gegen Solution_92 und Platz 1 im Kursturnier. Neu (alle Schalter aus, Abgabe unverändert):
- `agents/sherlock/opp_model.py`: sagt aus unserer Sicht voraus, wen Solution_92 sappt (stehendes Schiff auf Punkte-Tile, Energie ≥ Sap-Kosten, Ziel = unsere höchste sichtbare Unit-ID in Manhattan-Reichweite, aus seinem Code). Gemessen in 20 Spielen (500720–500729): 97,2 % der Saps sichtbarer Schützen vorhergesagt, Ziel zu 98,5 % richtig; 38 % Fehlalarme (nur ziehende Schiffe), 25 % der Saps kommen von unsichtbaren Schützen.
- `dodge` (`dodge_mode` lethal/always): vorhergesagte Ziele weichen aus. Entwicklungskarten gegen V3 85,0 %: lethal −0,8 [−3,3; +1,7], always +1,7 [−1,7; +5,0]. Mechanismus wirkt (direkter Gegnerschaden Match 3 −41 %), Siegquote kaum.
- Sichtprüfung verlorener Spiele (`scripts/render_snapshots.py`): drei Fehlerbilder – Wettlauf um nähere Haufen verloren, neues Relic-Paar in Match 2/3 nicht gesucht, überzählige Units ungenutzt.
- **Training mit Schwerpunkt auf schweren Karten** ([Plan, vorab](superpowers/plans/2026-10-21-hard-map-training.md)): Kartensuche V3 gegen Solution_92 auf 2000 neuen Trainingskarten 360000–361999 (4000 Spiele, V3 76,0 %); 660 Karten mit mindestens einer verlorenen Seite (300 beide verloren) → `hard_seeds.json`. Neue Option `scripts.experiment --seed-file`: Solution_92-Spiele laufen auf diesen Karten. 6 Läufe `20261021_full_rules_v3_s40`–`s45_hard` (je 3000 Spiele) gestartet 22:44; Auswertung automatisch (`scripts/pipeline_hard.sh`) auf neuem Auswahlblock 503820–504019. PPO `cnn3b` läuft mit niedrigster Priorität weiter.

Tests: 376 bestanden + 14 Untertests (ohne die 88 prozessgesperrten Studientests, die bei laufenden Spielen absichtlich verweigern).

## 21.10.2026, 21:55 Berlin – Claude Code mit Mahmoud: Gefahr-Merkmale ohne Gewinn, PPO läuft weiter

Die 6 Läufe `20261021_full_rules_v3_threat_s40`–`s45_sol70` (je 3000 Spiele, 18.000 insgesamt, je ~116 min, alle fehlerfrei) wurden nach dem [vorab festgelegten Plan](superpowers/plans/2026-10-21-threat-features.md) ausgewertet (`scripts/pipeline_threat.sh`, Log `experiments/pipeline_threat.log`). Auswahlblock 503220–503419, 200 Karten, beide Seiten, je 400 Spiele: V3 Solution_92 76,7 %, default 98,8 %; Kontrolle `v3nets6` 73,3 % (Δ −3,5 [−8,7; +1,5]); `threat6` 72,8 % (Δ −4,0 [−9,5; +1,3]); `mix24` = `threat6` + 18 V3-Netze 78,2 % (**Δ +1,5 [−2,8; +5,8]**), default 99,0 %. Methodenfrage `threat6` gegen Kontrolle: **−0,5 [−6,0; +4,8]** – kein messbarer Effekt der Gefahr-Merkmale. Vorab-Regel (+3 pp vor V3) verfehlt: Versuch beendet, **frische Blöcke 503420–503819 unbenutzt**, keine Abgabeänderung. Hashes `threat6` `7a26f21b…8d53`, `mix24` `ace788eb…8034` (lokal, gitignored).

Vorab festgelegter Nachtrag `mix24_art3` (`mix24` + `art_sap`, 3 Treffer) auf demselben Auswahlblock: 78,2 % (Δ +1,5 [−3,0; +6,0]), default 99,3 % → ebenfalls beendet, frische Blöcke weiter unbenutzt.

PPO `cnn3b` läuft weiter (Iteration 50 von 150, Trainings-WR gegen Solution_92 bisher flach ~0,71–0,73); Prüfung der Stände 50/100/letzter erst nach Laufende auf 503220–503419 laut Plan. Gesamte Testsuite nach Trainingsende **459 bestanden + 14 Untertests** (offener Punkt vom 19:33-Eintrag erledigt, inklusive Moayeds Ensemble-Korrektur `b359bd6`).

## 21.10.2026, 21:17 Berlin – Codex: V4-Programm ausgewertet, V3 bleibt Abgabe

[Abschlussbericht für den 22.10.](MORGENBERICHT_20261022.md). **Kein qualifizierter stärkerer V4.** Paar-Koordinator, Zielpilot, begrenzte CNN-Fortsetzung und Artillerie-Bestätigung ergeben zusammen **3.336 neue Spiele: 240 Training und 3.096 Auswertungs-/Kontroll-/Kursprüfspiele**. Historische Referenzen und frühere Nachtversuche nicht erneut mitgezählt. Der letzte Kandidat gewinnt frisch gegen Solution **301/400 statt V3 292/400**, Δ +2,25 Prozentpunkte, gepaartes 95%-Kartenintervall [−0,25; +4,75]. Beide Solution-Übernahmegates verfehlt; default jeweils 399/400. Kein direkter frischer Folgetest, kein zusätzlicher Trainingslauf, kein Gewichtswechsel.

[Artillerie-Archiv mit allen 2.208 Spielen](../experiments/analysis/art_sap_confirm_20261021/README.md): unabhängige Abschlussprüfung vollständig, Root-Nachrechnung und erneuter Audit erfolgreich. Originalzustand zum Auditzeitpunkt erhalten; danach `completed_negative`. Alle 83 Quell-/Runtime-, fünf Eingabe- und acht Schutzdatei-Hashes unverändert. Experimentdaten und Kandidat in main; erfolgloser Koordinationscode bleibt auf `improvement/v4-joint-20261021`.

Abgabe unverändert `all18_v3` (`aac1c910…8d935`), alte Sechser-Sicherung unverändert (`3788fb72…d158`). Artillerie-Karten 523000–523199 jetzt verbraucht; 523200–523399 und der finale 100%-Audit wurden in diesem Programm nicht gespielt. Die [unabhängige Abschlussentscheidung](../experiments/analysis/art_sap_confirm_20261021/next_step_review.md) empfiehlt keine weitere unbegründete Variantenrunde. Nächste neue Evidenz sind Mahmouds bereits gestartete 101-Merkmal-DQN-/PPO-Läufe unter ihrem festen Plan und den reservierten Karten 503220–503819. Diese Trainings nicht duplizieren.

Der begrenzte Auftrag wird nach Veröffentlichung vorzeitig abgeschlossen; das Ziel einer deutlich stärkeren V4-Version bleibt offen. Mindestens 30 % Nutzerkontingent erhalten, kein Reset. Tatsächliche Abschlussprozesse, Remote-Stand und Restkontingent stehen im Abschlussbericht.


## 21.10.2026, 20:43 Berlin – Codex: Artillerie-Kandidat in frischer Bestätigung

Vorgeschaltete Prüfung abgeschlossen: 480 Reproduktionsspiele stimmen für V3 und `art_sap=True, art_min_hits=3` in sämtlichen 23 Nichtzeitfeldern mit den historischen Referenzen überein. Solution **108/120 statt 102/120** (Δ+5 pp, gepaartes Kartenintervall [+0,833;+10]); default beide 120/120. Direkt auf denselben Entwicklungskarten **80 Siege/40 Niederlagen gegen V3** (66,67%, Kartenintervall [58,33;75]%). Unabhängiger Datenreview der 600 Vergleichsspiele bestanden. Zusätzlich acht Kursprüfspiele bestanden: exakte Ladung aller 18 Netze, frisches Belief, 303 Schritte; größte p95-Aktionszeit 2,326 ms, Maximum 10,946 ms. Der Kurscheck prüft Aktionsformat, keine vollständige semantische Legalitätsgarantie.

Die unveränderten 18 V3-Netze im Versuchskandidaten wurden rekursiv und nach Laden geprüft; unabhängiger Bytevergleich aller 264 Tensor-Speicherblöcke ebenfalls identisch. Kandidat SHA `e392f20c60d51817591ee4c0061bc8150e7ec8aa312b42e704004538ead45497`. Die zwei gespeicherten Configänderungen sind die einzige Veränderung gegenüber V3. **Noch keine Freigabe als stärkere Abgabe.**

Jetzt fester Vergleich auf 200 neuen Karten 523000–523199, beide Seiten, beide Gegner, jeweils V3/Kandidat = 1.600 Spiele. Erst nach vollständiger Auswertung aller vorher festgelegten Gates gegebenenfalls 400 direkte Spiele auf 523200–523399. Finaler Seed-Abgleich: 2.109 zugängliche CSV-Dateien mit Seedspalte, 1.485.640 Zeilen, kein Treffer im reservierten Bereich. Mahmouds 503220–503819 bleiben frei für seine Studie. Arbeitszweig `improvement/v4-joint-20261021`, eingefroren auf `9c1efc7`; aktuelle Daten dort unter `experiments/analysis/art_sap_confirm_20261021/`. main erhält den fertigen Bericht erst nach Abschluss.

Neue ausdrückliche Budgetgrenze von Moayed: mindestens 30 % Codex-Kontingent übriglassen. Root beginnt Abschluss bei 35 % Rest; kein Reset. Bei letzter Kontrolle 79 % Rest. Beide aktiven Automationen übernehmen diese Grenze. Die Frist 22.10. um 06:00 Berlin gilt nur, sofern die Budgetgrenze nicht früher greift. V3 und alte Sicherung bleiben unverändert.


## 21.10.2026, 20:30 Berlin – Codex: gemeinsame Integration geprüft

Mahmouds Artillerie-/Gefahrmerkmale und die Korrektur der Ensemble-Dimensionen sind im Arbeitszweig zusammengeführt. Der erste Gesamtlauf zeigte 14 überholte Testfixtures (517 bestanden): Frühablehnung beschädigter Checkpoints, fehlende Breitenangaben in inerten Curriculum-Mocks und ein Zielpilot-Mock ohne Eingabedimension. Nur die Testverträge angepasst; Produktionsprüfung nicht abgeschwächt. Unabhängiger Review der Korrektur und Fixtures ohne offene Blocker.

Root-Gesamtlauf im V4-Arbeitszweig: **531 Tests und 14 Untertests bestanden in 82,52 s**. Die Tests des Zielpiloten gehören ausschließlich zum Arbeitszweig; main erhält Werkzeugkorrektur und gemeinsame Testfixtures. [Review](ENSEMBLE_DIMENSIONEN_REVIEW_20261021.md). Kein Trainings-/Agentenverhaltenswechsel und keine Gewichtsänderung durch die Fixture-Korrektur. Nächster Schritt: festgeschriebene Artillerie-Reproduktion, noch keine Stärkeverbesserung belegt.


## 21.10.2026, 20:23 Berlin – Codex: ältere Ensemble-Testdaten an strikte Ladeprüfung angepasst

Nach Roots Integrationslauf zwei Testverträge korrigiert: Der Kandidatenrunner-Test verlangt jetzt die frühe Ausnahme bei falscher Eingabebreite und prüft weiterhin unabhängig Tensor-/Config-/Architekturabweichungen. Die inerten Curriculum-Prüfnetze erhalten einen Tensor mit der deklarierten Eingabebreite; sämtliche Herkunfts- und Gate-Prüfungen bleiben bestehen. **2 gezielt reproduzierte Fehler vor der Anpassung, danach 98 Tests aus beiden betroffenen Dateien bestanden** (44,30 s). [Nachweis](ENSEMBLE_DIMENSIONEN_20261021.md). Nur Tests und Dokumentation geändert, Rechenplatz freigegeben; erneute vollständige Integrationsprüfung durch Root offen.

## 21.10.2026, 20:15 Berlin – Codex: Ensemble-Dimensionen gegen stillen Netzverlust abgesichert

[Korrektur und Prüfnachweis](ENSEMBLE_DIMENSIONEN_20261021.md): Beim Erweitern eines gespeicherten homogenen Ensembles blieb bisher eine zu kurze Dimensionsliste bestehen; der Loader ließ dadurch Netze aus. Der Builder schreibt jetzt immer alle Dimensionen. Gemeinsame Prüfung von Listenlänge, ganzzahligen positiven Grenzen und tatsächlichen Tensorbreiten weist fehlerhafte Checkpoints ab. Fehlende/`None`/leere Altformat-Metadaten und gültige 101/79-Ensembles bleiben unterstützt.

TDD auf isoliertem Zweig: **23 Fehler/5 bestanden vor der Korrektur**, danach **28 neue Tests bestanden**; abschließend **32 fokussierte Tests bestanden** inklusive bestehender Persistenz- und Mischensemble-Prüfung. Rechenplatz erst nach Freigabe benutzt, anschließend freigegeben. Keine Aktionsregel-, Trainingscode- oder Gewichtsänderung. Vollständige Testsuite und unabhängiger Review des zusammengeführten Stands durch Root noch offen; kein Push aus diesem Arbeitszweig.



## 21.10.2026, 20:16 Berlin – Codex: CNN-Fortsetzung beendet, Artillerie-Prüfung vorbereitet

[724 neue registrierte Spiele, Rohdaten und unabhängiger Abschlussreview](../experiments/analysis/cnn3_sol90_s20_20261021/README.md): 240 Trainingsspiele ab Original-PPO60 in 38:50 Minuten, 240 Original-Referenzspiele, vier V3-Kontrollen und 240 Endstand-Spiele. Auf den bekannten 60 Karten gewinnt der einzige finale CNN-Kandidat gegen Solution **89/120**, Original-PPO60 **96/120**, V3 **102/120**; default alle120/120. Gegenüber V3 Δ−10,83 pp, gepaartes95%-Kartenintervall[−20;−2,5]. Vorgegebene Solution-Gates verfehlt; dieser Kandidat ist beendet. Keine frischen Tests, keine Zwischenstand-Auswahl und keine Übernahme. Alle V3-/Sicherungshashes unverändert.

Root-Tensor-/Ladeprüfung und unabhängige CSV-/Hash-/Statistikprüfung bestanden. Quellen während des Versuchs eingefroren auf `47388d4`; 30 von32 Policy-Tensoren geändert, Architektur und effektive Konfiguration erhalten. Neuer kleiner Minibatch und frischer Adam erlauben keine isolierte Aussage über den Gegner-Mix. Die Spielzahlen werden nicht mit den parallel auf Mahmouds Rechner laufenden Trainings vermischt.

Mahmouds Commits `f540da4` bis `baef7a8` gelesen und nach Ende der eigenen Modelljobs ins lokale main übernommen. [Unabhängiger Code-/Datenreview und separater Vorabplan](superpowers/plans/2026-10-21-art-sap-confirmation.md) für genau den bereits ausgewählten Artillerie-Schalter3: historisch108/120 statt102/120, aber sieben Varianten auf bekannten Karten und fehlende vollständige Run-Manifeste. Deshalb zuerst vollständige Reproduktion mit exakt18 unveränderten V3-Netzen, dann direkte/Kursprüfung und nur bei bestandenen Gates frische Karten. Noch keine eigenen Artillerie-Spiele. Mahmouds503220–503819 bleiben für seine Studien reserviert, Root523000–523399 ist noch unbenutzt.

Separater Werkzeugfehler beim Wiederaufbau gespeicherter homogener Ensembles gefunden: veraltete `ensemble_dims` können beim Laden zusätzliche Netze unterschlagen. Gezielte Reproduktion/Korrektur in eigenem Zweig; unabhängiger Review und endgültige gemeinsame Integrationssuite stehen noch aus. Die Artillerie-Kopie verwendet diesen Builder nicht. Nachtauftrag läuft weiter bis spätestens22.10.06Berlin; spätestens05:15 Abschlussreserve. Aktuelle Abgabe bleibt V3.


## 21.10.2026, 19:33 Berlin – Claude Code mit Mahmoud: Festungs-Diagnose, zwei Trainings laufen

**Diagnose** ([Mechanismus-Probe](../experiments/analysis/mechanism_probe_20261021/README.md), neues Messwerkzeug `scripts/mechanism_probe.py`, reine Messung, V3 unverändert, Entwicklungskarten 500720–500779): Verlorene Matches 3 liegen auf Karten mit vielen Punkte-Tiles. In den deutlichsten Niederlagen kippt das Sap-Verhältnis in Match 3 (z. B. 500753: 6 : 68 Saps, 23 : 4 Tote): Solution_92 sitzt mit vielen Units auf einem umkämpften Relic-Haufen („Festung“) und sappt alles in **Manhattan**-Reichweite; unsere wiedergeborenen Units laufen einzeln hinein. Die Engine erlaubt Saps im ganzen Quadrat.

**Neue Schalter, alle Default aus, Abgabe unverändert:** `art_sap` (Sap aus Manhattan-sicherer Position bei ≥ n Treffern) und `siege` (Festungsziele aus der Ferne belagern, `rules.SiegePlan`). Auswahl auf Entwicklungskarten gegen V3 (85,0 %): `art_sap` 2/3/4 Treffer +2,5/+5,0 [+0,8; +10,0]/−0,8; Nachbarvarianten ±1 → nicht robust, kein Kandidat. `siege` **−17,5** [−25,8; −10,0] → verworfen (Units geben umkämpfte Tiles auf). Default jeweils 120/120.

**Training (läuft, noch keine Ergebnisse):** (1) PPO `cnn3b`: Start `cnn3/ppo_0060`, 150 Iterationen × 80 Spiele, Gegner 80 % Solution_92 / 15 % V3 / 5 % default, Seed 5, Trainingskarten 250000+ (`experiments/ppo/cnn3b/`), auf Mahmouds Rechner mit dem damaligen `ppo_train` vor `14469f2` gestartet; unabhängig von Codex' begrenztem 10-Iterationen-Lauf `cnn3_sol90_s20` auf Moayeds Rechner. (2) Neuer Schalter `threat_feats` (+22 Netzeingaben: je Tile sapfähige Gegner in Manhattan-/Quadrat-Reichweite, Gegnerenergie auf/neben dem Tile, bester Sap, besetzte Punkte-Tiles), Variante `full_rules_v3_threat` = `full_rules_v3` + Gefahr-Merkmale: 6 Läufe `20261021_full_rules_v3_threat_s40`–`s45_sol70`, je 3000 Spiele, 70 % Solution_92 – gleiche Starts/Einstellungen wie die Kontrolle `v3nets6` vom 20.10. Alte Checkpoints/Abgabe laden unverändert (79 Eingaben).

**Auswertung vorab festgelegt:** [Plan](superpowers/plans/2026-10-21-threat-features.md) mit Auswahl auf 503220–503419, Bestätigung 503420–503619 und direktem Vergleich 503620–503819, Abnahmeregeln wie V4-Strategie. Dazu `build_ensemble --mixed`: V3-Netze (79 Eingaben) und Gefahr-Netze (101) in einem Ensemble, alte Netze bekommen die ersten 79 Merkmale (`ensemble_dims`). Kurs-Runner-Prüfung und `train.py --resume` akzeptieren Gefahr-Checkpoints. Tests zu `92ece27` (während die Trainings liefen): 400 bestanden + 14 Untertests; die 31 Tests in `tests/test_early_curriculum_study.py` verweigern absichtlich, solange `scripts.experiment`-Prozesse laufen (Prozessprüfung „Another model job is active“), Datei unverändert – Wiederholung nach Trainingsende steht aus.

**Seeds reserviert (Mahmoud):** 503220–503419 Auswahl unter PPO-/Threat-Ständen, 503420–503619 einmalige frische Bestätigung genau eines vorher gewählten Kandidaten, 503620–503819 Reserve. Vor Nutzung in 524 CSVs ohne Treffer geprüft.

**Prüfungen:** gesamte Testsuite 422 Tests + 14 Untertests bestanden (davon 13 neu in `tests/test_rules_2110.py`), Trainings-Probelauf mit 101 Eingaben gespeichert/geladen. Abgabe-Hash unverändert.

## 21.10.2026, 19:28 Berlin – Codex: begrenztes CNN3-Training läuft

Die geprüfte PPO-Zufallsbindung ist als `14469f2` in main veröffentlicht: 489 Tests plus 14 Untertests im Arbeitszweig, danach acht fokussierte Tests im Hauptcheckout. Vorabplan und unabhängige Reviews unter [CNN3-Fortsetzung](superpowers/plans/2026-10-21-cnn3-bounded-continuation.md). Die V3-Abgabe bleibt unverändert.

240 neue Referenzspiele auf 60 bekannten Karten 500720–500779: Original-PPO60 gewinnt **96/120 gegen Solution_92** und **120/120 gegen default**. V3-Referenz **102/120 bzw. 120/120**; vier neue Kontrollspiele reproduzieren alle 23 gespeicherten Nichtzeitfelder. Keine frischen Bestätigungskarten verwendet.

Der einzige geplante Trainer läuft seit etwa 19:28 Berlin: 240 Spiele, 10 Iterationen, Startseed 20, letzter Originalstand PPO60, festes Gegnerprogramm mit 211 Solution- und 29 Default-Spielen. Das sind geplante Trainingszahlen, noch kein abgeschlossenes Ergebnis. Endstand allein wird ausgewertet; keine Auswahl eines günstigen Zwischenstands. Maximal 90 Minuten Training, Quellen- und Gewichtskontrolle, Speicher- und Fehlerüberwachung. Bei negativem Entwicklungsgate keine weitere Verlängerung dieses Kandidaten.

Aktive Arbeitskopie auf Moayeds Rechner: `/Users/moayedshawesh/Desktop/KI/sherlock-v4-joint`, eingefrorener Commit `47388d4`. Livezustand dort unter `experiments/analysis/cnn3_sol90_s20_20261021/execution_state.json`; kein zweites Training oder paralleler Modelltest auf dem 8-GB-Mac. main darf getrennt aktualisiert werden; der aktive Versuch übernimmt neue Quellen erst nach Abschluss. Der Remote-Wächter meldet Mahmouds neue Commits. Späteste Gesamtfrist 22.10.2026 06:00 Berlin, Abschlussreserve ab 05:15.

## 21.10.2026, 19:16 Berlin – Codex: Zielpilot beendet, CNN3-Folgeversuch vorbereitet

[Acht Spiele und unabhängiger Datenreview](../experiments/analysis/v4_target_pilot_20261021/README.md): Kontroll- und Wiederholungsverläufe identisch, aber in 32 festen Situationen keine geeignete Zielalternative. Festes Gate verfehlt; kein Zielbewerter, keine frischen Tests, keine Änderung an V3. Daraus folgt keine allgemeine Wirkungslosigkeit von Zielzuweisung. Zusammen mit dem Paar-Koordinator 404 neue Spiele; weiterhin kein qualifizierter V4.

Mahmouds Commit `718a298` in Haupt- und Arbeitskopie am sicheren Phasenübergang integriert. Originale CNN3-Gewichte per Hash geprüft. [Separater begrenzter Fortsetzungsplan](superpowers/plans/2026-10-21-cnn3-bounded-continuation.md): nach technischer Prüfung einmal 240 PPO-Trainingsspiele ab PPO60, 90-Minuten-Grenze und feste Entwicklungsgates. Noch nicht gestartet. Vorher wird eine reproduzierte Lücke geschlossen: gleicher Spielseed bindet bisher den Torch-Zufall der PPO-Aktionswahl nicht; auch der Lernprozess setzt ihn nicht. Eine kleine Korrektur samt unabhängigem Review läuft. Keine Architektur- oder Rewardänderung und keine Gewichtsübernahme.

## 21.10.2026, 19:10 Berlin – Claude Code mit Mahmoud: CNN3-Originalgewichte geteilt

Auf Codex' offene Bitte (Morgenbericht): Original-Checkpoints des Laufs `cnn3` (`scripts/pipeline_cnn3.sh`, 20.10.) liegen jetzt versioniert in `experiments/candidates/`: `cnn3_bc.pth` (Start nach BC, SHA-256 `1879c991…f62a2`), `cnn3_ppo0050.pth` (auf Val 720 bester Stand, frisch 502020–502219 getestet; `5c16f62d…617b3`) und `cnn3_ppo0060.pth` (letzter Stand; `0efe4d39…0fb0bef`). Volle Hashes, Ergebnisse und Lehrer (`all18_fo10.pth`, identisch mit `experiments/ensembles/all18_fo10.pth`) in [Kandidaten-README](../experiments/candidates/README.md). `bash scripts/install_candidates.sh` kopiert sie nach `experiments/ppo/cnn3/` und prüft die Hashes; lokal ausgeführt, alle OK. Config/Architektur stecken im Checkpoint (`cfg`, `arch`, `feature_dim` 79). Lehrerdaten `bc_data.npz` (4,9 GB) bleiben lokal bei Mahmoud. Keine Code-, Gewichts- oder Abgabeänderung; Abgabe weiter `all18_v3` (Hash geprüft).

## 21.10.2026, 18:53 Berlin – Codex: erster gemeinsamer V4-Zug ohne Stärkegewinn

[396 neue Spiele, vollständige Daten und unabhängige Prüfung](../experiments/analysis/v4_joint_pairs_v1_20261021/README.md). Auf 60 bekannten Karten 500720–500779 gewinnt der Koordinationskandidat gegen Solution_92 **101/120 statt V3 102/120**, Δ −0,83 pp, gepaartes Kartenintervall [−2,5; 0]. Default beide120/120. Direkt gegen V3 62Siege/58Niederlagen, Resultat51,67%, Intervall[50;54,17]%. Vorgegebenes Solution-Gate verfehlt; keine frischen Bestätigungsspiele, kein Gewichtswechsel.

48 fokussierte Tests, insgesamt457 Tests plus14 Untertests, unabhängiger Codereview, acht Kurs-Runner-Spiele und Hashkontrollen bestanden. Die technische Umsetzung und der Kandidat bleiben auf `improvement/v4-joint-20261021`; main erhält Ergebnisse und Übergabe. Die 18 Netze entsprechen exakt V3. Quellen waren während sämtlicher Versuche eingefroren.

Die passive Folgeprüfung reproduziert vier Entwicklungsverläufe. In120 abgetasteten Situationen erlauben alle legalen Bewegungen sieben mögliche Belegungsgewinne, die zwei besten Netzvorschläge noch zwei und die15%-Bewertungsgrenze keinen. Das erklärt die geringe Aktivierung dieser Stichprobe; kein Beweis, dass Lockerung sinnvoll wäre. Kandidat beendet. Nächste eigenständige Machbarkeitsfrage: Kann eine Zielwahl anhand von Erreichbarkeit/Energie/Bedrohung die tatsächlich ausgeführte V3-Aktion verändern? Erst bei nachgewiesenem Einfluss und korrekter Simulator-Isolation ist ein kleiner gelernter Zielbewerter sinnvoll. User hat eigenständige Folgearbeit bis22.10.06Berlin autorisiert; Root schreibt den separaten Versuch vor neuen Daten fest.


## 21.10.2026, ab 18:25 Berlin – Codex: V4-Koordination wird umgesetzt

Moayed hat die selbstständige Umsetzung samt Subagents und Tests bis **22.10.2026 spätestens 06:00 Berlin** beauftragt. [Fester Implementierungs- und Versuchsplan](superpowers/plans/2026-10-21-v4-joint-prototype.md), Arbeitszweig `improvement/v4-joint-20261021` in eigener Arbeitskopie. Implementer baut einen standardmäßig deaktivierten, nur bei Auswertung aktiven Paar-Koordinator; unabhängiges Review folgt. Root prüft Daten, integriert und führt Tests aus; ein eigener Remote-Wächter meldet neue Commits, ohne Quellen zu verändern.

V3-Gewichte und alte Sicherung zu Beginn per Hash unverändert. Keine aktiven Modelljobs aus früheren Versuchen, keine Wiederaufnahme der abgebrochenen Curriculumstudie. 523000–523399 als neuer Bestätigungsbereich vorgeprüft (520 Seed-CSVs ohne Treffer), Nutzung nur nach erneutem Remote-Abgleich und bestandenem Entwicklungsgate. Zunächst neue Entwicklungs- und direkte V3-Spiele, keine bestätigte Verbesserung und noch kein neuer trainierter Kandidat. Deadline-Auftrag und Repo-Abgleich auf den neuen Zeitraum aktualisiert. Nächste Berichte unterscheiden tatsächliche Umsetzung, laufende Versuche und abgeschlossene Ergebnisse.

## 21.10.2026 – Codex: neue V4-Strategie nach ausbleibendem Zusatzgewinn

Auf Moayeds erneuten Planungswunsch: [V4-Strategie](V4_STRATEGIE_20261021.md). Zwei unabhängige, ausschließlich lesende Reviews prüfen Entscheidungsarchitektur und Lernwege. Priorität ist eine kleine gemeinsame Auswahl von V3-Aktionsvorschlägen für interagierende Schiffe; zunächst Bewegung/STAY, keine neue Trainingsserie. Erst ein positiver Entwicklungsvergleich rechtfertigt eine Bestätigung auf neuen Karten oder einen kleinen lernenden Bewerter. Ziel bleibt 100 % auf einem vorher festgelegten Testsatz, ohne Garantie für alle Karten. Bereits vorhandene, nicht qualifizierte V4-Dateien bleiben getrennt.

Begründung aus Code und vorhandenen Daten: eindeutige strategische Ziele werden bereits verteilt, die tatsächlichen Aktionen aber weitgehend pro Einheit gewählt. Das ist eine neue Hypothese, noch kein nachgewiesener Engpass. CNN/PPO übernehmen ebenfalls die sechs Aktionsklassen und lösen die gemeinsame Planung nicht automatisch. Vorhandene Verlusttraces enthalten nicht alle legalen Modellinputs; keine versteckten Zustandsdaten für Lernmerkmale benutzen.

Nur Strategie und Übergabe geändert; Quellenstellen, historische Zahlen und relative Links geprüft. Kein Agentencode, keine Gewichte, keine neuen Spiele oder Trainings in dieser Planung. Letzter aktiver Versuch bleibt der abgeschlossene Gegnerenergie-Vergleich unten. Die zwischenzeitlichen automatischen Git-Abgleiche waren keine kontinuierliche Entwicklungsarbeit; dieser Stillstand wurde Moayed ausdrücklich mitgeteilt. Nächster konkreter Liefergegenstand: begrenzter Koordinationsprototyp samt vollständigem Vergleich. Die bisherige V3 bleibt Abgabe.






## 21.10.2026, 14:53 Berlin – Codex: direkter Gegnerenergie-Vergleich abgeschlossen

[480 vollständige Vergleichsspiele und unabhängiger Audit](../experiments/analysis/enemy_tie_energy_20261021/README.md). V3 mit `enemy_tie_energy=True` gewinnt gegen Solution_92 **105/120 statt 102/120**; Differenz +2,5 Prozentpunkte, gepaartes 95%-Kartenintervall **[−2,5; +8,33]**. Default jeweils 120/120. Positiver Punktschätzer, aber kein vorab geforderter Vorteilsnachweis: Variante beendet, keine frischen oder direkten Folgespiele, kein Austausch der Abgabe.

Vorher 439 Tests und 14 Untertests sowie acht Kurs-Runner-Spiele bestanden; sämtliche 18 Netze und alle übrigen Checkpointfelder identisch mit V3, nur gespeicherter Schalter verändert. Die 240 V3-Referenzspiele reproduzieren alle Nichtzeitfelder. Root und unabhängiger Reviewer bestätigen vollständige Schlüssel, Rechnung, Quellen- und Gewichtsidentität.

Implementierung und nicht qualifizierter Kandidat bleiben auf `improvement/enemy-tie-20261021`, Ergebniscommit **694eda3**. main erhält ausschließlich Rohdaten/Prüfungen und diesen Bericht; die nicht belegte Funktionsänderung wird nicht in den Abgabe-Agenten übernommen. Nächste begrenzte Diagnose ist die bereits offene Konsistenzfrage von PPO-Aktionswahl und gespeicherten Kartenebenen, zunächst ohne Spiele oder Optimizer-Schritte. Keine neue breite Trainingsreihe.

## 21.10.2026, 14:39 Berlin – Codex: Ressourcen neu priorisiert, Curriculum unvollständig beendet

Moe kritisiert den langen Aufwand ohne zusätzlichen Stärkegewinn. Root hat die weitere Priorität nach einer unabhängigen, begrenzten Ressourcenprüfung geändert: Die laufende Curriculumstudie wird **unvollständig beendet**, der bereits vorbereitete direkte V3-Gegnermerkmale-Vergleich vorgezogen. Noch etwa zweieinhalb Stunden wären allein bis zur Grundauswertung angefallen. [Begründung, tatsächliche Spielzahlen und vollständiges Abbrucharchiv](../experiments/analysis/continuous_20261021/curriculum_progress/cancellation/README.md).

Der negative erste Start war bereits bekannt. Deshalb ausdrücklich keine vorgeplante statistische Ablehnung und keine Aussage, dass die vollständige Methode widerlegt sei. Ursprüngliche Gates/Seeds werden nicht umgeschrieben; keine historischen Kontrollen ersetzt, kein Teilcheckpoint ausgewählt. Zwei erneut trainierte Kontrollen reproduzierten sämtliche 3.000 historischen Trainingszeilen außerhalb der Laufzeit exakt ([Beleg](../experiments/analysis/continuous_20261021/curriculum_progress/historical_control_reproduction_s47_s48.json)). Das belegt Reproduzierbarkeit, ist aber kein neuer Stärkegewinn.

Kontrollierter SIGTERM nur an den nach PID/Kommando überprüften eigenen Supervisor; seine registrierte Trainingsgruppe ist beendet, State `active=null`, geschützte Gewichte unverändert. Der alte State bleibt als Original erhalten; `train_48_early` ist unvollständig und darf nicht durch manuelle Statusänderung fortgesetzt werden. Drei vollständige Trainingsarme plus 750 Spiele des vierten: insgesamt 9.750 Trainingsspiele, 544 Zwischenvalidierungen und 480 finale Testspiele. Keine s49-Läufe.

Nächster Schritt: getrennten Gegnerenergie-Zweig mit main abgleichen, einmal passende Modellintegration prüfen, Quellen/Gewichte einfrieren und 480 vorab festgelegte Entwicklungsspiele ausführen. Keine neue Trainingsreihe. Eigene Wachhaltung bleibt für diese aktive Folgearbeit bestehen.

## 21.10.2026, 13:39 Berlin – Codex: erstes Curriculum-Paar vollständig ausgewertet

[Archiv und Prüfungen](../experiments/analysis/continuous_20261021/curriculum_progress/s47/README.md):6.000 Trainings-,320 Zwischenvalidierungs- und480 finale Testspiele fertig. Früher Gegnerkontakt s47 gegen Solution_92 **62/120 statt86/120** der Kontrolle, Δ−20pp, gepaartes95%-Kartenintervall[−32,5;−7,5]. Default119/120 statt120/120. Die beiden Einzelnetze werden miteinander verglichen, nicht mit der18-Netz-Abgabe.

Unabhängiger Subagent prüfte Daten/Initialidentität/Gegnerplan/Hashbindungen ohne Modellimporte; Root reproduzierte Resultate und Kartenintervalle separat und kontrollierte alle Archivkopien. Laufquellen und Gewichte unverändert. Rohdateien, Prüfbericht und abgeschlossene Phasen archiviert; `.pth`-Laufkopien nur lokal gemäß bestehender Git-Regel, Buffer in der eingefrorenen Arbeitskopie.

Die feste Studie läuft mit s48Kontrolle weiter, anschließend s48früh und s49beide. Ein einzelner negativer Start beendet den vorher festgelegten Vergleich nicht. Keine geänderten Gates, keine nachträgliche Best-Seed-Auswahl und kein Abgabeersatz.

## 21.10.2026, 12:58 Berlin – Codex: Folgeversuch vorab operativ geprüft

Der [unabhängige Operationsreview](../experiments/analysis/continuous_20261021/representation_probe/protocol_review.md) prüft den vorbereiteten Gegnerenergie-Vergleich. Ein Ressourcenfehler wurde vor jedem neuen Spiel korrigiert: Zwei Stunden passen nicht zur festgelegten konservativen Zeitrechnung. Historische Maximaldauer6,43Sekunden ergibt mit Sicherheitsfaktor und Reserve20.833Sekunden für alle möglichen2.480Spiele. Die interne Obergrenze beträgt deshalb jetzt sechs Stunden; Seeds, Spielzahlen und statistische Gates bleiben unverändert. Root hat die drei historischen Laufzeitmaxima und Dateihashes separat bestätigt.

Weitere Ausführungshinweise sind dokumentiert: absoluter gemeinsamer Pythonpfad, tatsächlich gespeicherter Configschalter, vollständige CSV-Prüfung und separate Direktanalyse für522200–522399. Kein neuer Supervisor, keine zusätzlichen Modelle/Spiele gestartet. Laufende Curriculumquellen bleiben eingefroren; dieser Folgeversuch beginnt erst danach.

## 21.10.2026, 12:38 Berlin – Codex: erster Trainingsarm vollständig geprüft

Kontrolle s47 fertig: 3.000 Trainings- und160 Zwischenvalidierungsspiele, Trainingsprozess3186,54Sekunden, anschließender Tensorcheck3,21Sekunden, beide Returncodes0. Alle gespeicherten Q-/Target-Tensoren endlich; geschützte Gewichte unverändert. [Technischer Phasennachweis](../experiments/analysis/continuous_20261021/curriculum_progress/s47_control_training.json).

Der frühe Gegnerarm s47 läuft. Root hat seine tatsächliche Anfangsidentität mit der Kontrolle verglichen: vollständig gleich, einschließlich Netzen, Optimizer, leerem Replay und Zufallszuständen. Auch sämtliche Nichtzeitfelder der32 Startvalidierungen und der ersten100 Trainingsspiele sind exakt gleich; erst danach beginnt der geplante Gegnerunterschied. Die finalen240-Spiele-Auswertungen beider Arme und der vollständige Vergleich aller drei Starts stehen noch aus. Keine Stärke-/Übernahmeentscheidung aus diesem Zwischenstand.

## 21.10.2026 – Codex: Gegnerenergie-Tiebreak auf getrenntem Zweig geprüft

Commit `1b3f6a7` auf `improvement/enemy-tie-20261021`: acht Produktionszeilen ergänzen den ausgeschalteten Schalter und seine Auswahl. [Umsetzung](../experiments/analysis/continuous_20261021/representation_probe/implementation.md), [unabhängiger Review](../experiments/analysis/continuous_20261021/representation_probe/code_review.md) ohne wichtigen Befund. 34 leichte Tests bestanden; im selben Prozess keine Torch-/JAX-/Engineimporte. Root hat die505 Bewegungen und beiden Konvergenzereignisse separat aus Rohaktionen reproduziert ([Zählprüfung](../experiments/analysis/continuous_20261021/representation_probe/root_counts.json)).

Code noch nicht in main integriert: vollständige Modellintegration und tatsächliche Spiele warten auf das Ende der laufenden Curriculumstudie. Danach einmal passende Integrationstests, Quellenfreeze und der festgelegte Einzelvergleich. Kein Wirksamkeitsnachweis und keine Gewichtsänderung. Der Zweig erlaubt Mahmoud/Claude bereits die Vorbereitung nachzulesen; keine parallelen Modelljobs auf diesem Rechner starten.

## 21.10.2026 – Codex: ein separater Gegnermerkmal-Versuch vorbereitet

Der [Repräsentationscheck](../experiments/analysis/continuous_20261021/representation_probe/README.md) bestätigt eine konkrete Informationslücke: nur einer von mehreren gleich nahen sichtbaren Gegnern wird einzeln beschrieben. Zwei nominelle Konvergenzen in den fest ausgewählten84Übergängen zeigen den Kontext, keine Kausalität oder Verbesserung. Root lässt deshalb genau eine standardmäßig ausgeschaltete Auswahlvariante vorbereiten: bei gleicher Entfernung höhere Gegnerenergie bevorzugen.

[Vergleich und Gates vorab festgelegt](superpowers/plans/2026-10-21-enemy-tie-energy.md). Neue reservierte Karten522000–522399, keine Kollision im vorliegenden CSV-Bestand. Umsetzung in separater Arbeitskopie; während der laufenden Curriculumstudie nur leichte Tests/Review, keine zusätzlichen Modelljobs. Gewichte und Curriculum bleiben unverändert. Diese zusätzliche Vorbereitung ist keine bisher ausgeführte Evaluation oder Übernahme.

## 21.10.2026, 11:44 Berlin – Codex: neue Trainingsstudie läuft

Der freigegebene Vergleich `20261021_early_contact_v1` ist tatsächlich gestartet: 21.10.2026 11:44:34 Europe/Berlin, feste Studienfrist 23:44:34 desselben Tages. Eingefrorener Commit **`a5d2e61b0e8654bad64e31c29447ada1e439174d`** in `sherlock-counterplay`; Supervisor 63520, erster Trainer 63533. Zustand und Joblogs liegen dort unter `experiments/analysis/early_curriculum_20261021_early_contact_v1/`. Prozessnummern sind nur die lokale Momentaufnahme, vor jedem Eingriff erneut mit Kommando/Ownership prüfen.

Unabhängiger [Anlaufcheck](../experiments/analysis/continuous_20261021/planning/curriculum_start_audit.md): tatsächliche Initialidentität, CLI, Konfiguration, Gegnerplan, 32 Startvalidierungs- und erste 225 vollständige Trainingszeilen geprüft; keine technischen Auffälligkeiten. Das ist keine Stärkeprüfung.

Aktuell beginnt Kontrolle s47; erst danach früher Gegnerkontakt s47 und die vollständigen Paarprüfungen, anschließend Starts48/49. Geplant sind18.000 Trainingsspiele plus960 Zwischenvalidierungs- und1.440 finale Einzelnetzauswertungsspiele; weiterführende Ensemble-/Frisch-/Direktprüfungen sind bedingt. Aus einem laufenden Training lässt sich noch keine Verbesserung ableiten.

Den eingefrorenen Arbeitszweig, seine Pythonquellen, Pläne, Gewichte und die benutzte Venv nicht verändern. Hauptcheckout und Remote dürfen separat abgeglichen werden; fremde Änderungen werden während des Source-Freeze nicht in den Versuch übernommen. Alte Deadlines06/09 gelten nicht mehr, der Benutzer hat kontinuierliche Arbeit ohne feste Enduhrzeit beauftragt. Der konkrete Versuch behält trotzdem seine vorab festgelegte Ressourcenfrist. V3-Abgabe und Sicherungen bleiben unverändert.

## 21.10.2026 – Codex: Curriculumstudie vollständig geprüft und zum Start bereit

Alle vier Umsetzungsschritte inklusive unabhängiger Nach- und Integrationsprüfung fertig. Statistikauswertung `a5ce6d8`, bedingte Bestätigung `9c5c06d`, periodische Prüfung erzeugter Eingaben `2da04b3`. Vollsuite vor der engen letzten Korrektur: 406 Tests plus 14 Teilprüfungen; danach 88 betroffene Tests. [Nachweise und Grenzen](../experiments/analysis/continuous_20261021/planning/README_CURRICULUM.md).

Nächster tatsächlicher Schritt: sechs frische Läufe (Starts 47–49, je Kontrolle/früher Gegnerkontakt, je 3.000 Spiele), feste Zwischenvalidierungen und abschließende Vergleiche. Genau eine fachliche Änderung: 100 Solution-Spiele früher, Gesamtgegnerzahlen gleich. Keine Auswahl des besten Zwischenstands. Ein 21-Netze-Kandidat entsteht nur nach positivem Methodengate; neue Karten und direkte V3-Prüfung erst nach ihren vorgeschalteten Gates.

Studien-ID `20261021_early_contact_v1`, Quellenfreeze nach dieser Dokumentation in der separaten Arbeitskopie `sherlock-counterplay`. Der Runner setzt die feste 12-Stunden-Frist beim wirklichen Start. Hauptrepo kann getrennt aktuell gehalten werden. Noch kein stärkerer Agent aus dieser Studie nachgewiesen; V3 und alte Sicherung unverändert, Bestätigungskarten unbenutzt. Keine Agenten-/Reward-/Architekturänderung.

## 21.10.2026 – Codex: lokale Wiederbesetzung als begrenzte Diagnose

Der [Folgecheck](../experiments/analysis/continuous_20261021/loss_observation/locality_followup/README.md) betrachtet ausschließlich die vier größten späten Belegungslücken in vorhandenen Traces. Weit entfernte oder gegnerisch besetzte bekannte Punkte erklären, warum der globale freie-Felder-Zähler sofortige Chancen überschätzt. Konkrete Sequenzen zeigen negative Energie, Maskenverluste und längere erneute Anreise; die verursachenden Schadensquellen und mögliche bessere Aktionen sind damit nicht isoliert.

Keine neuen Spiele, kein Agentenpatch. Root prüfte feste Auswahl, Quellenhashes, Fenster und Partitionen; die Arbeitshypothese bleibt ausdrücklich begrenzt. Vorhandene Energiepuffer-/Zuweisungsvarianten nicht blind wiederholen. Das getrennt festgelegte Curriculumtraining und seine Gates bleiben unverändert.

## 21.10.2026 – Codex: Studienrunner geprüft, statistische Auswertung folgt

Der exklusive Studienrunner (`4332d6b`, korrigiert in `0ec929e`) ist unabhängig freigegeben: sechs neue Läufe, feste Reihenfolge, tatsächliche Anfangsidentitäten, vollständige Trainings-/Validierungs-/Auswertungsdateien und eine ursprüngliche Zwölfstundenfrist. Ein globaler Lock für unsere Studien verhindert konkurrierende Modelljobs über Arbeitskopien hinweg; fremde manuell gestartete Werkzeuge werden zusätzlich per Prozessprüfung erkannt, aber nicht durch diesen Lock gesteuert.

Der Review fand zunächst fehlende Spaltenprüfungen, eine Lücke bei der Prozesssperre und vererbte Signalsperren. Alle drei sind korrigiert und nachgeprüft; 62 gezielte Tests bestanden. [Erster Review](../experiments/analysis/continuous_20261021/planning/curriculum_runner_initial_review.md), [Freigabe der Korrektur](../experiments/analysis/continuous_20261021/planning/curriculum_runner_fixed_review.md).

Noch keine neuen Trainingsspiele: Als nächstes werden die festgelegten statistischen Gates und bedingten Ensembleprüfungen umgesetzt. Vorbereitung der technischen Abgabeprüfung ist dokumentiert; sie ist keine bereits durchgeführte Übernahmeprüfung. V3 und die bestehende alte Sicherung bleiben unverändert.

## 21.10.2026 – Codex: Trainingsvergleich, Eingaben unabhängig geprüft

Der frühe Gegnerplan und die isolierten Zwischenmessungen sind implementiert (`bc7d3b1`) und unabhängig freigegeben. 267 Tests plus 14 Teilprüfungen bestanden. Standardaufrufe behalten ihr bisheriges Verhalten. Neue Studienaufrufe zeichnen die vollständige Gegnerfolge, die tatsächliche Anfangsidentität der Learner und rohe Zwischenvalidierungsspiele auf; die Validierung erhält den relevanten Lern- und Zufallszustand.

Noch kein neues Langtraining gestartet: Der exklusive Studienrunner, seine vollständigen Ergebnisprüfungen und die festgelegten statistischen Gates werden als nächste getrennte Schritte umgesetzt und geprüft. Die abgeschlossene Verlustdiagnose liegt mit Rohdaten unter `experiments/analysis/continuous_20261021/loss_observation/`. Aktuelle V3-Abgabe und alte Sicherung bleiben unverändert. Remote vor Veröffentlichung abgeglichen; keine neuen fremden Commits gefunden.

## 21.10.2026 – Codex: Verlustdiagnose abgeschlossen, kein neuer Regelpatch

[Archiv und Ergebnis](../experiments/analysis/continuous_20261021/loss_observation/README.md) der 20 fest ausgewählten Partien vollständig: 6060 Übergänge, 60 Matchabschlüsse und 240 zeitlich ausgerichtete Schnappschüsse. Alle 460 nichtzeitlichen Referenzwerte identisch; Root prüfte 41 ursprüngliche Dateihashes sowie Matchsiege und die zentralen Belegungswerte unabhängig nach. Die ergebnisgeschichtete Stichprobe ist keine neue Siegquotenmessung.

Matchsiege 16/20, 6/20, 3/20; alle 13 verlorenen Spiele verlieren Match 2 und 3. Dort sind spät viele Punktefelder bekannt, aber weniger produktiv besetzt als beim Gegner. Das unterscheidet Anreise, Zuweisung, Energie und Gegnerdruck noch nicht kausal. Kein erneuter pauschaler Reserve-/Zuweisungspatch. Die falsche Sap-Kollisionsannahme ist auch im engen echten Engine-Test widerlegt: gleiche Kollisionsmasken bei STAY/SAP, unterschiedliche Restenergie. Fünf enge beobachtete Eintrittskontexte behalten unmittelbar das produktive Feld. Kostenindikatoren bleiben deskriptiv.

Nächster Schritt ist deshalb der getrennt vorab festgelegte Curriculumvergleich, bei unveränderter Agentenlogik. Seine erste Werkzeugänderung ist implementiert und wird unabhängig geprüft; vollständiger Studienrunner und Gates folgen, noch kein neues Langtraining gestartet. V3 und Sicherung unverändert.

## 21.10.2026 – Codex: Diagnosewerkzeug geprüft, erste Ursache widerlegt

Observer `4503dba` und Korrektur `525060f` sind in main veröffentlicht. Tests: 231 plus 14 Teilprüfungen bestanden; nach unabhängig gefundenem Koordinatenfehler der Aufzeichnung neun fokussierte Tests bestanden, Review freigegeben. Anschließend genau 20 vorab ausgewählte Partien unveränderter V3 aufgenommen: 6060 Übergänge, alle 460 nichtzeitlichen Referenzwerte und 41 Ergebnisdatei-Hashes geprüft. Das ist Reproduktion, keine Verbesserung; fachliche Auswertung und Rohdatenarchiv folgen.

**Wichtige Korrektur zum ursprünglichen Solution-Review:** Der behauptete unmittelbare Kollisionsnachteil durch Sapkosten war falsch. Die installierte Engine speichert die Energie nach Bewegung, aber vor Sap (`env.py:293`) und nutzt diese gespeicherte Energie zur Kollisionsaggregation (`:462`). Ein Sap ändert daher nicht den Gewinner derselben Kollision. [Ursprünglicher Review mit vorangestellter Rücknahme](../experiments/analysis/continuous_20261021/planning/sherlock-solution-counterplay-20261021.md). Kein Agentenpatch daraus. Eine weitere kurze Engineprüfung wird separat dokumentiert; der Fehler betraf eine Hypothese, nicht Sherlocks ausgeführte Aktionen oder Gewichte.

Lokaler Git-Abruf war durch eine ungültig benannte Zusatzreferenz `refs/remotes/origin/main 2` blockiert. Ihr Inhalt zeigte auf den vorhandenen Commit b008252. Die Datei wurde unverändert außerhalb des Referenzbaums unter `.git/codex-ref-backups/20261021-main-2.txt` gesichert; anschließend Abruf, Fast-forward und Push erfolgreich. Ursache der Zusatzdatei nicht behauptet; keine Projektdateien oder fremden ungesicherten Änderungen entfernt.

## 21.10.2026 – Codex: neuer autonomer Verbesserungsauftrag

Moayed hat nach dem Abschluss um 09:00 erneut kontinuierliche Arbeit ohne feste Enduhrzeit freigegeben: gezielte Niederlagenanalyse, Gegenstrategien, Training, unabhängige Bestätigung und geprüfte Pushes. [Aktueller Plan](superpowers/plans/2026-10-21-continuous-improvement.md). Die vorigen Abschlussnotizen bleiben historische Belege. V3 bleibt zunächst Abgabe; bisherige Sicherung bleibt erhalten.

Remote-Vorprüfung: b008252 lokal/remote identisch, keine laufenden Modelljobs. Drei unabhängige Agenten prüfen Verlustdaten, Solution-Code und Remote/Seedkollisionen. Neuer finaler Auditblock 520000–520999 reserviert; 511000–511399 bleibt Curriculumreservierung. Der Drei-Stunden-Abgleich ist reaktiviert, andere alte Abschlussautomationen bleiben pausiert. Arbeitskopie für neue Quellen: ../sherlock-counterplay, Branch improvement/counterplay-20261021. Noch keine neue Trainings- oder Stärkeaussage.

## 21.10.2026, 09:00 – Codex: Auftrag bis 09:00 abgeschlossen

Morgenbericht `07dbe71` und konkretisierter Curriculumplan `34fc59f` sind gepusht. Beim letzten Abruf vor dem Abschlusscommit stimmen lokales `main` und `origin/main` überein; keine neuen fremden Commits. Die abschließende Dokumentation einschließlich dieser Zeile wird in einem eigenen Abschlusscommit veröffentlicht; dessen Identität ist in der Git-Historie nachvollziehbar.

[Abschlussprüfung](../experiments/analysis/autonomous_20261020/closing_checks_20261021.json): V3-Dateien und alte Sicherung weiter mit den erwarteten Hashes; keine Python-/Gewichtsänderungen seit `6ab3109`. Eigene Trainings und Auswertungen sind beendet, alle delegierten Prüfaufträge abgeschlossen. Der eigene bis 09:00 befristete Wachhalteprozess ist beendet. Alle drei Nacht-Automationen sind deaktiviert (Status PAUSED); kein automatischer weiterer Studienstart. Fremde ungesicherte Dateien und lokale Trainingsgewichte/Buffer bleiben erhalten.

Ergebnis und Grenzen: [Morgenbericht](MORGENBERICHT_20261021.md). V3 bleibt Abgabe; zusätzliche Trainingsversuche und V4-Bestätigung ergaben keinen weiteren qualifizierten Ersatz. Der [nächste Plan](superpowers/plans/2026-10-21-early-opponent-curriculum.md) ist geprüft, aber nicht implementiert oder gestartet. Die Fortsetzung benötigt ein neues ausreichendes Arbeitszeitfenster; dieser Abschluss startet keine Hintergrundjobs.

## 21.10.2026, 08:49 – Codex: nächste einzelne Studie verbindlich geplant, nicht gestartet

Der Morgenbericht wurde als `07dbe71` erfolgreich nach `origin/main` gepusht. Danach den [Curriculumplan](superpowers/plans/2026-10-21-early-opponent-curriculum.md) konkretisiert und unabhängig prüfen lassen: drei neue Paare mit bekannten Starts 47–49, gleiche Gegnergesamtzahlen, feste Zwischenmessungen und getrennte Methoden-/Ensemblegates. Neu reserviert 511000–511199 (bedingte Gegnerbestätigung), 511200–511399 (bedingter Direktvergleich); 507 versionierte CSVs mit 358.716 Zeilen ohne Kollision, jüngster Remote-Abgleich ohne neue fremde Commits. Vor einem späteren Start nochmals prüfen.

Planreview korrigiert: Audits eindeutig an Studien-ID/State binden, tatsächliche Initialidentität vor Validierung erfassen, Zwischenvalidierung samt RNG isolieren und Rohschlüssel sichern, exklusive Ausgaben und atomare Phasengrenzen testen. Die heutigen Werkzeuge unterstützen die neuen Optionen noch nicht. Keine Implementierung, kein weiterer Modelllauf und keine Verlängerung des Auftrags über 09:00. [Prüfbelege](../experiments/analysis/autonomous_20261020/early_curriculum_planning/README.md).

## 21.10.2026, 08:43 – Codex: Morgenbericht und gemeinsame Orientierung geprüft

[Morgenbericht](MORGENBERICHT_20261021.md) mit Ergebnisgrafik, Spielzahlen, Grenzen, Abgabe/Sicherung und tatsächlich gepushten Arbeitsschritten erstellt. V3 bleibt installiert; zusätzliche 18.800 Trainingsspiele und der unabhängige 2.400-Spiele-V4-Vergleich liefern keinen weiteren qualifizierten Ersatz. Bericht, Grafikwerte, Quelllaufbudget und nächste Schritte unabhängig geprüft. Zwei sprachliche Übertreibungen, ein relativer Link und veraltete nächste Schritte korrigiert. Historische Erstpräsi-Läufe (`full`/`full_sym`) ausdrücklich von den heutigen 66.000 V3-Quelllaufspielen getrennt; teilweise gleiche Karten bedeuten keine identischen Trainingsläufe.

README, CLAUDE, Experiment-Einstieg und Hauptplan auf den Stand vom 21.10. gebracht. Künftiger Curriculumversuch bislang nur Entwurf; genaue Umsetzung und Studie werden separat geplant. Keine neuen Modellversuche während des Abschlusses. Das Nutzungslimit unterbrach die aktive Koordination nachts; bereits gestartete Programme liefen unabhängig fertig. Der Bericht behauptet keine durchgängige LLM-Arbeit.

Prüfung: Quellen und Gewichte seit dem vollständig getesteten Stand `6ab3109` unverändert; damalige Suite 223 Tests plus 14 Subtests bestanden. Für diesen reinen Dokumentationsschritt Dateilinks, Format, Grafik und Archivhashes geprüft, keine zusätzlichen Modelltests nötig. Aktuelle V3-Dateien und alte Sechser-Sicherung stimmen mit ihren dokumentierten SHA-256 überein. Remote-Beobachter und Root bestätigten vor diesem Berichtscommit lokales `main` = `origin/main` auf `5dda0a3`, ohne neue Mahmoud-Commits. Eigene Trainings-/Evaluationsprozesse sind beendet; Wachhaltung bis 09:00 und Abschlussautomationen werden beim tatsächlichen Abschluss separat geprüft. Fremde ungesicherte Dateien bleiben unangetastet.

## 21.10.2026, 08:27 – Codex: Aktionsfluss von V3 passiv geprüft

[20 Beobachtungsspiele](../experiments/analysis/autonomous_20261020/v3_action_source_observation/README.md), bekannte Karten 500720–500729, beide Seiten gegen Solution_92. Alle 23 nichtzeitlichen Spielkennzahlen exakt gegen zwei vorhandene Referenzen reproduziert. Keine Agenten-, Gewichts- oder Aktionsänderung; lediglich Methoden-Ein-/Ausgänge beobachtet. 13 Tests vor Start; danach Root und unabhängiger Review: Quellen-/Input-/Gewichtshashes identisch, komplette Aktionsketten und Nenner nachgerechnet.

70.200 aktive Unitentscheidungen, davon 8.320 mit nur einer legalen Aktionsklasse und 61.880 mit mindestens zwei. Bei Wahlmöglichkeit blieb die maskierte Greedyklasse **56.352/61.880 = 91,07 %** bis zur Ausgabe erhalten. 3.702 Änderungen durch Erkundung, 1.826 durch späte Nachbearbeitung; keine Änderung durch die allgemeine Regel und keine Rückänderung in dieser Stichprobe. Negative Energieslots und Matchstart-No-ops separat gezählt. Das zeigt Entscheidungsfluss, **keinen kausalen Netzbeitrag oder Stärkenachweis**; Features/Masken/Sap-Zielwahl sind bereits regelgestützt. Individuelle Masken/Energien wurden zur Laufzeit geprüft, nicht nachträglich aus Aggregaten rekonstruiert. Lauf vollständig um 08:21:17 beendet; V3 und alte Sicherung bleiben unverändert.

## 21.10.2026, 08:09 – Codex: nächste Trainingsfrage vorbereitet, keine Agentenänderung

[Übergabe für Mahmoud](NAECHSTER_TRAININGSVERSUCH_20261021.md): langsame Exploration blieb auf allen drei Starts schwächer; geringere Trainingsresultate auch nach gemeinsam erreichtem Epsilonminimum, keine allgemeine Aussage gegen Exploration. Deskriptive Phasenmittel über 18.000 Logzeilen unabhängig mit Stdlib reproduziert; fehlende anfängliche Losswerte gezählt und ausgeschlossen. Gleiche Gegnergesamtzahlen in beiden Armen. Q-Margen und Beobachtungen liefern Hypothesen, keine isolierte kausale Erklärung.

Priorisierter späterer Versuch: 100 frühere Solution_92-Spiele gegen 100 spätere tauschen, sonst ursprünglicher schneller Epsilon-Abfall und gleiche 1.426/1.574 Gegnerzahlen. Gegnerfolge rechnerisch geprüft, **noch nicht implementiert oder trainiert**. Vor Start feste Zwischenmessungen, Seedreservierungen, Tests und vollständigen Studienplan ergänzen. Rund 5,2 Stunden reine Trainingszeit plus Auswertung einplanen. Keine weiteren gleichartigen Netze, langsamen Decays oder Kombinationen von Inferenzschaltern ohne neue belastbare Hypothese. CNN3-Fortsetzung benötigt zunächst die lokal fehlenden Originalcheckpoints. Installierte V3, Sicherung und Pythonquellen unverändert. Ergänzend alle 18 V3-Quelllaufmanifeste und 66.000 lückenlose Trainingslogzeilen geprüft: sechs × 3.000 plus zwölf × 4.000 Spiele; verschiedene Reward-/Gegnerkonfigurationen. Das ist ein dokumentiertes Quelllaufbudget, nicht die gesamte Projektentwicklung; individuelle Quellgewichte fehlen lokal, daher kein neuer Tensor-Herkunftsnachweis.

## 21.10.2026, 08:06 – Codex: unabhängige V4-Bestätigung beendet, V3 bleibt Abgabe

Alle vorab festgelegten **2.400 Spiele** abgeschlossen (07:35–08:04 Berlin), Quellenstand `6ab3109`. Neue Karten 510400–510799 direkt V4 gegen V3: **408/800 = 51,0 %**, Karten-KI **[48,125; 54,0] %**. Neue Karten 510800–510999, beide Seiten: Solution_92 V3 **311/400**, V4 **313/400**, Δ **+0,5 pp**, gepaartes Karten-KI **[−3,0; +4,0]**; default beide **400/400**. Keine Remis. Beide geforderten Vorteilsnachweise fehlen: **keine Übernahme und keine Erweiterung der Stichprobe**. Alte V4-Ergebnisse nicht gepoolt. Das beweist keine Gleichwertigkeit, rechtfertigt unter den vorherigen Regeln aber keinen Austausch.

[Ergebnisse, Rohdaten, Audits und historische Werkzeuge](../experiments/compare/autonomous_20261020/v4_independent_20261021/README.md). Root und unabhängiger Subagent bestätigen alle Spielschlüssel, vollständige Kurslänge, Punktezählversion 2, Resultatkonsistenz, unveränderte Quellen/Inputs/HEAD und unabhängig nachgerechnete 5.000 Kartenbootstrapziehungen (Seed 0). Die vorherige vollständige Suite bestand: 223 Tests plus 14 Subtests. Keine Pythonquellen seitdem geändert. Aktuelle Abgabe bleibt `all18_v3`, beide SHA-256 `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`; alte Sechser-Sicherung unverändert. Die zusätzliche technische Übernahmeprüfung wurde mangels qualifizierten Kandidaten nicht gestartet. Nun Archivierung, Übergabe und Abschluss bis 09:00; keine neuen langen Trainings.

## 21.10.2026, 07:31 – Codex: Diagnose abgeschlossen, Arbeit bis 09:00 verlängert

Moayed hat die autonome Arbeit bis 09:00 verlängert. Nach der Nutzungslimit-Unterbrechung liefen die bereits gestarteten Programme selbstständig fertig; aktive LLM-Reviews und Pushes wurden erst nach Wiederaufnahme abgeschlossen. Die 40 Beobachtungsspiele reproduzieren sämtliche nichtzeitlichen Referenzwerte. [Punktfeld-Review](../experiments/analysis/autonomous_20261020/post_exploration_point_flow/point-flow-final-review.md): unerreichbare nahe Ziele betreffen 6,20%/7,62% freier bekannter eigener Feld-Schritte bei V3/V4; unter dem vorher gesetzten 10%-Arbeitsfilter. Null enge Stillstandssegmente. Kein Zuweisungspatch. Blockierte Fernziele nicht nachträglich zum Bestehen des Gates hinzurechnen. Bereits besetzte Asteroidenfelder können weiter punkten; ein späterer Filter müsste aktuelle direkte Sicht und Belegung beachten.

Als einmaligen nächsten Schritt V4 gegenüber V3 auf neuen Karten prüfen: [vorab veröffentlichter Plan](superpowers/plans/2026-10-21-v4-independent-confirmation.md). Reserviert 510400–510799 für 800 direkte Spiele und 510800–510999 für 1600 gepaarte Gegner-Spiele. Alte Daten werden nicht gepoolt, keine ergebnisabhängige Stichprobenverlängerung. Übernahme nur bei allen festgelegten Gates und technischen Prüfungen. Bisherige Abgabe und Sicherung unverändert. Dies ist eine Planung, noch kein Testergebnis.

## 21.10.2026, 07:27 – Codex: Exploration vollständig, kein Kandidat zur Übernahme

Die vorab festgelegten Starts47–49 wurden jeweils mit Kontrolle (Epsilon-Abfall60000 Schritte) und langsamem Abfall454500 vollständig trainiert: **18000 Trainingsspiele,1440 Einzelnetz-Auswertungen,1200 Ensemble-Auswertungen**. Gleiches Curriculum und gleiche Anfangstensoren je Paar; kein Start und kein Trainingshorizont nach Ergebnissen ausgewählt. [Aggregation](../experiments/analysis/autonomous_20261020/exploration_aggregate.md): langsamer Abfall gegen Solution_92 im Mittel48,06% statt61,11%, **Δ−13,06pp**, Karten-KI[−19,17;−6,94]; default93,89% statt97,78%, Δ−3,89pp. **0/3 Starts positiv**, Methodengate verfehlt.

Feste Ensembles ohne Auswahl einzelner Netze: auf500720–500779 gegen Solution_92 V3-Referenz85%, control3 75%, slow3 66,67%, V3+control3 85%, V3+slow3 81,67%; default Referenz/beide21-Netz-Ensembles100%, beide3er98,33%. V3+control3 Δ0pp (KI[−7,5;+7,5]), V3+slow3 Δ−3,33pp (KI[−10;+3,33]): **kein Entwicklungskandidat**, deshalb keine frische/direkte Bestätigung und keine Übernahme. Der frische Block510200–510399 blieb unbenutzt. Q-Margen-Diagnose und Bauprovenienz gespeichert, keine nachträgliche Umgewichtung.

Alle Paaraudits und Prozessphasen erfolgreich. Vor Archivierung unabhängig alle CSV-Zeilen/Schlüssel/Initialidentitäten, Hashes und5000/Seed0-Kartenintervalle nachgerechnet; sechs train.csv plus sechs val.csv byteerhalten, ebenso alle elf Evaluations-CSVs. Keine Modelle beim Archivcheck geladen; endliche Q-/Target-Tensoren sind bereits separat auditierte Befunde. Karten-KI gilt bedingt auf diese drei Starts, nicht als allgemeine Trainingsunsicherheit. [Historische Werkzeuge und Prüfbeleg](../experiments/analysis/autonomous_20261020/historical_exploration_tools_20261021/README.md) als bytegleiche Textsnapshots archiviert; absolute Pfade, alte Fristen und Hashes sind keine allgemeine Wiederstartanleitung. Gewichte/Buffer bleiben ignoriert, installierte V3 und Sicherung unverändert. Separate Punktfeld-Diagnose wird noch ausgewertet und ist nicht Teil dieses Abschlusses.

## 20.10.2026, 23:09 – Codex: Explorationspaar 47 vollständig geprüft, Restfolge unverändert

Beide frischen Einzelnetze mit Seed 47 jeweils 3.000 Spiele trainiert, danach je 240 vollständige Auswertungsspiele auf bekannten Karten 500720–500779. Einziger Konfigurationsunterschied: Epsilon-Abfall 60000 gegen 454500 Schritte. Default Kontrolle 120/120, langsamer Abfall 112/120 (Δ −6,67 pp, Karten-KI [−13,33; −1,67]); Solution_92 86/120 gegen 57/120 (Δ −24,17 pp, KI [−35,00; −13,33]). [Technischer Audit und Grenzen](../experiments/analysis/autonomous_20261020/exploration_pair_audit_s47.md).

**Tatsächlich geprüft:** vollständige 6.000 Trainings- und 480 Evaluationszeilen, identische Anfangstensoren/RNG und Gegnerfolge, exakter Configdiff, endliche gelernte Q-/Target-Tensoren, Quellen-/Plan-/Gewichtsidentität; unabhängig nachgerechnete CSV-Schlüssel und Kartenintervalle. Ein negativer Start ist kein Methodenurteil über die drei vorab festgelegten Starts. Keine Änderung der Trainingslänge, keine Best-Seed-Auswahl und kein Austausch der Abgabe. Rohdaten, Manifeste, Identitäten und Audit versioniert; lokale Modelle und Replay Buffer bleiben ignoriert. CSV-Rohbytes werden je Run über `.gitattributes` erhalten.

Mahmouds sieben ausschließlich Daten/Dokumentation enthaltende Commits bis `146c1f8` per Fast-forward übernommen; keine Python-, Plan- oder Gewichtsänderung. Anschließend ist die unveränderte, zeitgeprüfte Folge für 48/49, Audits, Aggregation und feste Ensemble-/Bestätigungsgates vorgesehen. Der nächste Lauf ist zum Zeitpunkt dieses Eintrags noch nicht gestartet. Währenddessen bleiben HEAD, Pythonquellen, Präregistrierungsplan und Abgabegewichte eingefroren; vorbereitete Helfer bleiben außerhalb des Repositorys.

## 20.10.2026, 22:25 – Claude Code mit Mahmoud: CNN `cnn3` (Nachahmung + PPO) und Plan für 21.10.

**`cnn3`** (`scripts/pipeline_cnn3.sh`, Log `experiments/pipeline_cnn3.log`): 1200 Lehrerspiele von `all18_fo10` (4,27 Mio. Unit-Schritte, Lehrer 74 % vs Solution_92 in der Datensammlung), BC 6 Epochen (48 Kanäle × 4 Blöcke, Trefferquote 88,4 %), PPO 60 Iterationen. Val 720 vs Solution_92 (gespeicherte Lehrer-Config, ohne `pt_sap`): BC 74,0 %, PPO 10/20/30/40/50/60 = 78,0 / 74,5 / 77,0 / 74,5 / **83,5** / 78,5 %; default immer 100 %. **Frische Karten 502 020–502 219** (vorab reserviert, bester Val-Stand `ppo_0050` gegen den Lehrer): `cnn3/ppo_0050` 99,5 % / 73,0 %, `all18_fo10` 99,5 % / 73,25 % (−0,25, KI [−5,0; +4,5]) → **das CNN erreicht das Lehrer-Niveau, nicht mehr**; der Val-Spitzenwert war Auswahlglück. `cnn3/ppo_0050` + `far_cand`/`pt_sap`/`opp_infer`: Val 81,0 % (−2,5). Auf demselben frischen Block **`all18_v4` 99,25 % / 76,25 %** (+3,0 vs `all18_fo10`, KI [−2,2; +8,3]; +3,25 vs CNN). PPO-Checkpoints liegen gitignored unter `experiments/ppo/cnn3/`.

**Vorher/nachher auf denselben Karten 501 620–501 819** (200 Karten, beide Seiten; Block war schon Bestätigungsblock für `far_opp`, daher nur Illustration): Solution_92 `all18` 296/400 (74,0 %) → `all18_fo10` 320/400 (80,0 %) → **`all18_v4` 324/400 (81,0 %)**, V4 gegen `all18` +7,0 (KI [+1,8; +12,2]); default jeweils 400/400 (`G_v4_1620.csv`).

**Stand heute Abend:** beste bestätigte Variante `all18_v4` (Solution_92 auf frischen Blöcken 80,4 % / 400 Karten und 76,25 % / 200 Karten; default 98,5–99,25 %; gegen alte Abgabe 106/120). Abgabe ist laut Codex `all18_v3`. Mehr oder neu trainierte DQN-Netze (`fo6`, `all24fo`, `v3nets6`, `all24v3`) und PPO-Weitertraining brachten heute nichts.

**Diagnose Relics auf der Diagonale** (`all18_v4` vs Solution_92, die 33 Karten mit ungerader Relic-Zahl aus 502 820–503 219, beide Seiten, Ground Truth): Zone um das Diagonal-Relic ≈ 10 Punkte-Tiles (4,5 je Hälfte + 1,1 auf der Diagonale). Besetzt bei Step 30/50/75/95: wir 1,0 / 1,9 / 3,7 / 3,2, Solution_92 1,3 / 2,2 / 1,8 / 2,4. Eigener Teil (4,5 Tiles): wir 1,0 / 1,4 / 2,2 / 2,0, Gegner dort 0,0 / 0,4 / 0,5 / 0,6 → rund 2 eigene Tiles der Mittelzone bleiben frei; früh ist Solution_92 schneller. Freie eigene Tiles der Zone je Schnappschuss (Step 40–90): 2,7, davon 1,5 bekannt, 1,05 noch Kandidat, 0,5 mit Gegner, 0,3 Asteroid; 2,35 sind einer Unit zugewiesen, die meist noch weit weg ist (≥ 4 Felder: 1,7) und läuft (75–85 % Bewegung) → kein Fehler, sondern Wegzeit; kein schneller Hebel erkennbar.

**Letzter Test 20.10.:** `pt_walk` + `pt_walk_own` (BFS-Weg zu eigenen Punkte-Tiles) auf `all18_v4`, Val 720 gegen 84,5 %: ab Match 1 −1,5, ab Match 2 −3,0 → bleibt aus. Arbeit für heute beendet (Mahmoud: „heute nur noch kurze Sachen, Rest morgen“); keine Prozesse laufen.

**Plan 21.10. (Mahmoud/Claude):**
1. Schwachstelle Relics auf der Diagonale / umkämpfte Mittelzone (V4 dort 67 %) gezielt diagnostizieren.
2. Große Karten im 3. Match: Besetzung der eigenen Hälfte (Solution_92 ~8 von 10, wir ~5–6).
3. Modellauswahl für PPO auf einem eigenen, größeren Validierungsblock statt Val 720 (100 Karten sind für die Auswahl zu verrauscht; Val 720 ist stark wiederverwendet).
4. Mit Moayed abstimmen, ob `all18_v4` die Abgabe ersetzen soll (Solution_92 +2,4 auf 400 Karten, alte Abgabe 106 vs 96/120, direkt gegen V3 unentschieden).

**Seeds:** Val 502 020–502 219 (cnn3), 502 620–502 819 (v3nets), 502 820–503 219 (V4) verbraucht; Moayed 502 420–502 619. Nächster freier Index für Mahmoud: 3220.

## 20.10.2026, 21:50 – Claude Code mit Mahmoud: Netze mit V3-Regeln im Training – kein Gewinn

`scripts/pipeline_v3nets.sh`: 6 × `full_rules_v3` (`pt_sap`, `far_cand`, `far_opp=10`, `keep_dead_fast` schon im Training; je 3000 Spiele, 70 % Solution_92, 128 min; Läufe `20261020_full_rules_v3_s40`–`s45_sol70`). Val 720 gegen `all18_v3` (83,0 %): `v3nets6` (nur die 6 neuen Netze) 75,5 % (−7,5, KI [−14,0; −1,0]), `all24v3` (18 + 6, V3-Schalter) 81,5 % (−1,5). **Frische Karten 502 620–502 819** (200 Karten, je 400 Spiele): `all18_v3` default 99,75 %, Solution_92 71,0 %; `v3nets6` 100 % / 70,0 % (−1,0, KI [−5,2; +3,5]); `all24v3` 100 % / **71,0 % (±0, KI [−4,3; +4,8])** → mehr bzw. neu trainierte DQN-Netze bringen nichts; die Gewinne heute kamen ausschließlich aus Regeln. Log: `experiments/pipeline_v3nets.log`.

**V4 gegen alte Abgabe** (für Moayeds Übernahmeregel, gleiche 60 Entwicklungskarten 500 720–500 779, beide Seiten, Gegner `self:experiments/releases/20261020_old3_sym3/agent_p0.pth`): **`all18_v4` 106/120 (88,3 %)**; Codex hatte für `all18_v3` dort 96/120 (80,0 %) gemessen (`U_v4_vs_old_720.csv`). **Relics auf der Diagonale:** ungerade `relics_found` (66 von 800 Spielen auf 502 820–503 219) heißt, ein Relic liegt auf der Spiegelachse (eigenes Spiegelbild); diese Karten gewinnt V4 nur zu 67 % (sonst 82 %) – umkämpfte Mittelzone, kein Belief-Fehler.

## 20.10.2026, 21:14 – Codex: kontrollierter Explorationsvergleich vorbereitet

Nach negativem Reward-Pilot eine getrennte, begründete Trainingsfrage: Der bisherige Epsilon-Abfall endet schon im 199. Spiel, während das 3.000er-Curriculum Solution_92 erst nach 750 Default-Spielen einführt. Neue Variante `full_rules_v3_slowexplore` ändert ausschließlich `eps_decay_steps` von 60000 auf 454500 (= 1500 Spiele). Alle experimentellen Reward-/Inferenzschalter bleiben aus. Dies verändert auch den Anteil geführter Aktionen und Regeln im Greedy-Zweig; kein isolierter Test uniformen Zufalls. [Diagnose](../experiments/analysis/autonomous_20261020/TRAINING_DIAGNOSIS.md), [vorab festgelegter Plan](superpowers/plans/2026-10-20-exploration-replication.md).

Geplant: drei frische gepaarte Starts 47–49, jeweils 3000 Spiele pro Arm; Karten 470000–471499, 480000–481499, 490000–491499. Alle sechs finalen Netze vergleichen, keine Zwischencheckpoint-/Best-Seed-Auswahl. Neue Bestätigung 510200–510399 reserviert; 510000–510199 bleiben unbenutzt. Methodenurteil und konkrete Ensembleauswahl getrennt; feste Vergleichsregeln im Plan.

**Tatsächlich geprüft:** zunächst erwartete Fehler wegen fehlender Variante, danach **16 Tests plus zehn Untertests bestanden**, acht Runner-Selbsttests und unabhängige Quellenreviews. Vier vollständige Rauchtestspiele mit echter Optimiereraktivität, endlichen Q-/Target-Tensoren und null gezählten ungültigen Aktionen. Keine Aussage zur Spielstärke aus diesem Rauchtest. Abgabe und Sicherung bytegleich. Maximal ein Trainer bzw. zwei Evaluationsworker; Quellen pro Paar eingefroren. Laufzeit wird vor jedem Paar zugelassen, spätestens 06:00 Ende; kein späterer Wechsel der Trainingslänge nach Resultaten.

## 20.10.2026, 21:11 – Codex: zweite Inferenzrunde ohne belastbaren Gewinner

720 vollständige Spiele auf bekannten Karten 500720–500779: V3, ausschließlich `active_targets`, ausschließlich `sap_geometry`, je 60 Karten × beide Seiten × zwei Gegner. Referenz reproduziert alle 240 nichtzeitlichen Kennzahlen des früheren V3-Laufs exakt. Alle Daten-/Quellen-/Gewichtsprüfungen bestanden. Default jeweils 120/120; Solution_92 V3 102/120, active 104/120, sap 103/120. Gepaarte Kartenintervalle: active +1,67 pp [−2,50; +5,83], sap +0,83 pp [−2,50; +5,00]. **Keine Variante erfüllt die vorab gesetzte Auswahlregel**, keine frische Bestätigung oder Übernahme gestartet. Schalter bleiben aus, Abgabe/Sicherung unverändert. [Bericht](../experiments/analysis/autonomous_20261020/inference_development2_analysis.md), Rohdaten und Auswertung archiviert. 510000–510199 wurden nicht benutzt.

## 20.10.2026, 20:58 – Codex: Mahmouds aktuelle Änderungen integriert

Remote bis `7ae858f` zusammengeführt: `sap_kill_first=False`, `energy_pref=0.0`, zugehörige Tests und die negativen Ergebnisse bleiben erhalten. Gemeinsamen Protokollkonflikt durch Erhalt beider Einträge gelöst. **217 Tests plus vier Untertests bestanden (43,74 s)**; Abgabe und Sicherung unverändert. Das ähnlich gute Gesamtergebnis beider Spielseiten in Mahmouds Notiz ist ein Plausibilitätscheck, allein kein Beweis, dass jeder Spiegelungsfehler ausgeschlossen ist. Vor der nächsten Variantenbewertung wird V3 auf allen 240 Entwicklungsspielen neu reproduziert.

## 20.10.2026, 20:56 – Codex: tatsächlicher Reward-Pilot verworfen

Zwei frische Einzelnetze mit identischen Anfangstensoren und identischer Karten-/Gegnerfolge jeweils **400 Spiele trainiert**, danach jeweils 240 feste Auswertungsspiele. Einziger Unterschied: `terminal_death_potential`. Vollständiger Audit bestanden: Quellen/HEAD unverändert, gleiche Initialisierung, vollständige Spielschlüssel, endliche gelernte Tensoren und geschützte Abgabe/Sicherung. Details: [Pilotbericht](../experiments/analysis/autonomous_20261020/reward_pilot_analysis.md).

Kontrolle gegen default 120/120, Korrektur 106/120; gegen Solution_92 43/120 statt 15/120. Differenz Korrektur minus Kontrolle **−23,33 Prozentpunkte**, gepaartes Kartenintervall [−34,17; −13,33]. Beide vorab festgelegten Schadensgrenzen verletzt: **keine große Reward-Replikation starten**, Schalter bleibt aus, Abgabe V3 bleibt unverändert. Ein Trainingsstart und bekannte Entwicklungskarten erlauben keine allgemeine Aussage über jede Trainingslänge; der konkrete Pilot reicht aber zum Stoppen dieses Versuchs. Kein Nutzen allein aus der mathematischen Motivation ableiten.

Der vor Auswertung geschriebene bedingte Replikationsplan bleibt als Historie erhalten (SHA im Audit). Rohdaten/Manifeste und Initial-/Finalidentitäten versioniert; lokale experimentelle Checkpoints und Replay Buffer bleiben in ihren getrennten Run-Verzeichnissen. Das tatsächlich ausgeführte Audit-Skript ist unverändert als `tools/source_snapshots/reward_pilot_analysis_original.py` archiviert: historischer Rechnerpfad und exakte damalige HEAD-Prüfung, kein universeller Wiederausführungsbefehl auf aktuellem main. Nächster Schritt: zwei separat vorab festgelegte Inferenzvarianten prüfen, parallel Ursachenanalyse des Reward-Rückschritts.

## 20.10.2026, 20:36 – Codex: Integration geprüft, Trainingsstart vorbereitet

Mahmouds `d41d1bf` normal gemergt (`05db41d`); seine deaktivierte Erkundungsquote und alle gemeinsamen Notizen erhalten. Danach **215 Tests plus vier Untertests bestanden (36,34 s)**. 24 kurze Spiele: V3 und die zwei einzeln aktivierten Inferenzvarianten auf je zwei Entwicklungskarten, beiden Seiten/Gegnern. V3 reproduziert alle acht bisherigen Spielzeilen außer Laufzeit. Varianten nur auf Lauffähigkeit geprüft, kein Stärkeurteil. Abgabe V3 und alte Sicherung bytegleich.

Audit: `experiments/analysis/autonomous_20261020/pretraining_checks.json`, Rohdaten `pretraining_*_smoke.csv`. Separater Reward-Pilot bereit für tatsächlichen Start: zwei frische Einzelnetze, je 400 Spiele, einziger Unterschied Terminal-Potentialkorrektur. Alle drei Flags standardmäßig aus; der Reward-Pilot aktiviert ausschließlich seinen Reward-Schalter im zweiten Arm. Während seines Laufs bleibt der lokale Code einschließlich HEAD eingefroren; Remote-Beobachter meldet weiterhin neue Commits, Integration erst danach.

**Reservierung für danach:** Eigene Inferenzvarianten einzeln auf bekannten 500720–500779 prüfen; vorab festgelegte Auswahlregeln im Plan. 510000–510199 für höchstens einen Gewinner zur frischen Bestätigung reserviert. Mahmouds Trainings-/Bestätigungsblöcke werden nicht mitbenutzt.

## 20.10.2026 abends – Codex: aktive Zielbesitzer als getrennte Testvariante

In der rein beobachtenden V3-Diagnose wurden 425 unbesetzte eigene Punktefelder in 38/40 Spielen einer Einheit mit negativer Energie zugeordnet; die Schattenzuweisung übergab sie einer lebenden Einheit. 139 dieser wiederholten Situationen hatten eine lebende Einheit in Manhattan-Distanz höchstens zwei mit Bewegungsenergie. Insgesamt änderten sich 2.729 Zielzuweisungen lebender Einheiten über 699 Schritte. Das sind Häufigkeiten, keine unabhängigen Ereignisse oder nachgewiesenen verlorenen Punkte.

Neuer Schalter `active_targets=False`: Nur für die Zielzuweisung werden Einheiten mit negativer Energie herausgefiltert. Null Energie bleibt zulässig. Belegung, `first_on_tile`, sonstige Merkmale und Lebenszykluserkennung bleiben unverändert. **Prüfung:** zwölf Tests plus vier Seiten-/Koordinaten-Untertests bestanden, zuvor erwartete RED-Fehler. Rohdiagnose, Vergleich sämtlicher nichtzeitlicher Spielkennzahlen und portables Diagnosewerkzeug sind separat dokumentiert. Spielstärkeprüfung folgt; keine Gewichte geändert.

## 20.10.2026 abends – Codex: Sap-Geometrie als getrennte Testvariante

40 reine Beobachtungsspiele mit V3 auf 500720–500739 (Solution_92, beide Seiten) reproduzieren sämtliche vorhandenen Kennzahlen außer Laufzeit. In 218 von 4.168 geeigneten ausgeführten Sap-Angriffen, verteilt über 32/40 Spiele, liefert ein freies Zielfeld einen höheren bestehenden Energiescore. Das ist ein beobachteter Ansatzpunkt, keine Messung tatsächlichen Schadens oder gewonnener Spiele.

Neuer Schalter `sap_geometry=False`: Nur wenn ein bisheriges legales Sap-Ziel vorhanden ist, werden zusätzliche freie Zentren geprüft. Ausschließlich ein strikt besserer Score ersetzt das alte Ziel; alte Gleichstände bleiben erhalten. Bei sichtbaren Gegnern mit negativer Energie bleibt der alte Pfad. Keine Änderung der Aktionsverfügbarkeit; neue leere Zentren erhalten keinen Gegner-auf-Punktefeld-Bonus.

**Prüfung:** 12 gezielte Tests, zuerst vier erwartete Fehler, danach alle bestanden. Abgedeckt sind Cluster, Kartenrand/Reichweite, Spiegelung, Gleichstände, fehlende Ziele, negative Energie und Punktefeld-Priorität. Die Variante ist ausgeschaltet und noch nicht auf Spielstärke geprüft; keine Gewichte geändert.

## 20.10.2026 abends – Codex: kontrollierter Reward-Pilot vorbereitet

Beim bereits erkannten Tod einer Einheit fehlte im potenzialbasierten Shaping der Abschluss `-w_shape * phi(s)`. Der neue Schalter `terminal_death_potential` ergänzt nur diesen Term, ohne die Lebenszyklus-/Done-Erkennung zu verändern. Standardmäßig aus: alte Checkpoints und laufende Trainings behalten ihre bisherige Belohnung. `full_rules_v3_terminal` unterscheidet sich genau in diesem Flag von `full_rules_v3`; vorhandene Basis-Overrides werden nicht verändert.

**Prüfung:** Neue Reward-/Registry-Tests zunächst 10 erwartete Fehler, nach Umsetzung zusammen mit bestehenden Reward-Tests **32 bestanden**. Tests umfassen entfernte Einheiten, Wiederauftauchen, gleichzeitiges Matchende, ausgeschaltetes Shaping, vollständige diskontierte Übergangsfolgen und Config-Kompatibilität. Das ist eine Konsistenzkorrektur, noch kein belegter Spielstärkegewinn.

**Trainingsplan:** Je 400 Spiele aus identischen Anfangsgewichten (Seed 46, Karten 460000–460199), anschließend ausschließlich finale Checkpoints auf bekannten Entwicklungskarten vergleichen. Keine Wiederaufnahme alter Replay Buffer; keine Zwischencheckpoint-Auswahl. Der geprüfte Ablauf `experiments/analysis/autonomous_20261020/tools/reward_pilot.py` dokumentiert Start-/Endgewichte, Config, Quellcode und Ergebnisse, schützt V3/Sicherung und beendet eigene Prozesse spätestens um 06:00 Berlin. Vor dem tatsächlichen Start noch Gesamttests und kurze Reproduktion nach Integration der getrennten Diagnosevarianten. Noch kein Trainingsergebnis.

## 20.10.2026, 20:35 – Claude Code mit Mahmoud: Relic-Suche im 2./3. Match (`explore_quota`) verworfen

**Diagnose** (`all18_v3`, Val 720–759): In 13 von 57 verlorenen Matches haben wir mindestens ein Relic nie gefunden (davon 6, in denen Solution_92 alle fand). Ursache: In Match 2/3 gibt es mehr bekannte Ziele als Units, dann bekommt keine Unit ein Erkundungsziel.

**Neuer Schalter `explore_quota`** (+ `explore_until=75`, Default aus, Test in `tests/test_rules_1910.py`): solange das Relic-Paar des Matches fehlen kann, suchen so viele Units (nicht auf Punkte-Tiles, zuerst ohne Ziel/mit Gegnerziel) lange nicht gesehene Tiles der eigenen Hälfte ab. Val 720 gegen `all18_v4` (84,5 %): Quote 1 **−8,0 (KI [−14,0; −2,0])**, Quote 2 **−9,5** → bleibt aus. Units vom Punktesammeln abzuziehen kostet mehr, als gefundene Relics bringen.

**`sap_kill_first`** (Sap-Ziel bevorzugt Gegner, die der Treffer zerstört): Val 720 **−8,0 (KI [−14,5; −1,5])** gegen `all18_v4` → aus; die bisherige Wahl (größte getroffene Gegnerenergie) ist besser.

**`energy_pref`** (Punkte-Tiles mit hoher Feldenergie bevorzugen) 2 / 5: −1,5 / −3,5 → aus. **Seitenvergleich** über 3600 Spiele gegen Solution_92 (7 Messreihen): player_0 77,2 %, player_1 77,3 % – kein Spiegelungsfehler.

Hinweis an Moayed/Codex: Moayeds V4-Direktvergleich gelesen; V3 bleibt Abgabe. Zielvergabe-/Sap-Geometrie-Diagnose und Reward-Trainingspilot sind bei Codex – Claude startet dazu nichts Paralleles.

## 20.10.2026, 20:25 – Codex: V4-Direktvergleich abgeschlossen, V3 bleibt Abgabe

V4 enthält exakt dieselben 18 Netze wie V3; nur `contest_sap` und `opp_infer` sind zusätzlich aktiv. Mahmouds positive Bestätigung gegen Solution_92 bleibt gültig. Das vorab zusätzlich festgelegte direkte Gate ist jedoch **unklar**: V4 gewinnt gegen V3 **61/120 Spiele** auf 60 bekannten Entwicklungskarten 500720–500779, beide Seiten; Kartenbootstrap 95 % [43,33; 58,33] % bei 5.000 Wiederholungen. Die untere Grenze liegt nicht über 50 %. Deshalb keine automatische Übernahme, keine Behauptung, V4 sei schlechter. V3 bleibt die feste Ausgangsbasis für die nächsten eigenen Versuche.

Rohdaten: `experiments/compare/autonomous_20261020/v4_vs_v3.csv`; Identitätsprüfung und Auswertung: `experiments/analysis/autonomous_20261020/v4_identity.json` und `v4_direct_gate.json`. Weitere V4-Kurs-/Reproduktionsprüfungen werden erst bei einer erneuten begründeten Übernahmeentscheidung benötigt. Keine Gewichtsdatei geändert. Als Nächstes: rein beobachtende Diagnose von Zielvergabe/Sap-Geometrie und kontrollierter Reward-Trainingspilot.

## 20.10.2026, 20:20 – Claude Code mit Mahmoud: neuer Kandidat `all18_v4` bestätigt (Hinweis an Moayed/Codex)

**Mahmoud/Claude arbeiten weiter, heute bis 0:00 Uhr**, morgen geht es weiter (die Notiz „Mahmoud/Claude arbeitet derzeit nicht weiter“ ist überholt). Moayeds Reservierungen 502 420–502 619 werden nicht benutzt.

**`all18_v4`** = `all18_v3` + `contest_sap` + `opp_infer` (Config im Checkpoint, `experiments/candidates/all18_v4.pth`, SHA-256 `3465225733bbbfbf05adc577f7af5f76cb2d886ff2ed895498434fac979ededd`, in `scripts/install_candidates.sh`). **Bestätigung auf 400 frischen Karten 502 820–503 219** (Kombination vorab festgelegt, nur Solution_92, je 800 Spiele, gleiche Karten/Seiten): `all18_v3` 78,0 %, **`all18_v4` 80,4 % (+2,4, KI [+0,1; +4,6])**. Default auf 502 820–502 919: v4 197/200, v3 198/200 (−0,5 pp; beide Niederlagen-Karten ohne gefundenes Relic). 3 Karten × 2 Seiten: gespeicherte Config identisch mit `--set`. Laut Moayeds Abnahmeregel (positiver Bereich gegen Solution_92, default höchstens −2 pp) wäre **v4 der bessere Kandidat für eine Übernahme als v3**; eine eigene Bestätigung gegen die alte Abgabe auf Moayeds Block fehlt noch. Abgabe-Gewichte von Claude **nicht** verändert (Mahmoud hat noch nicht „ja, einsetzen“ gesagt).

**Läuft bei Mahmoud:** `pipeline_cnn3.sh` (Messung auf 502 020–502 219), `pipeline_v3nets.sh` (502 620–502 819). Beide enden vor 0:00.

## 20.10.2026 abends – Codex: V3 gegen bisherige Abgabe bestätigt

**Messung:** Auf vorab reservierten 200 neuen Karten 502420–502619 gewinnt `all18_v3` gegen Solution_92 **313/400 (78,25 %)**, die bisherige Abgabe `old3_sym3` **170/400 (42,5 %)**. Gepaarte Differenz +35,75 Prozentpunkte, 95%-Kartenbootstrap [29,00; 42,25]. Default 400/400 gegen 382/400. Direkter Vergleich auf 60 bekannten Entwicklungskarten: V3 96/120, Intervall [70; 90] %. Alle vorab festgelegten Stärkekriterien bestanden und unabhängig nachgerechnet. [Bericht, Quellen und Grenzen](../experiments/analysis/autonomous_20261020/RELEASE.md).

**Einordnung:** Bestätigung von Mahmouds bereits vorhandenem Kandidaten; kein neues Training und kein Gewinn durch die vier verworfenen Codex-Varianten. 1.728 Spielausführungen im Übernahmebatch einschließlich acht Reproduktionsspielen; zusätzliche technische Reproduktion umfasst 16 bereits ausgewertete Spiele.

**Integration und Prüfung:** Remote bis `3a4f32f` normal gemergt; Messcode `14d239f` bleibt in der Historie. Beide Checkpoints einschließlich sämtlicher Netzparameter und effektiver Config geprüft; `cand_boost=0`, `contest_sap=False`, `pt_walk=False`. Alle Kennzahlen außer Zeit der 16 Schlussprüfspiele identisch. Gesamte Testsuite **169 bestanden (46,44 s)**. Sicherung und beide bisherigen Abgabedateien weiterhin bytegleich; Installation und anschließende Kursprüfung stehen als eigener Schritt an.

**Anschließende Übernahme:** Beide Abgabedateien durch den geprüften V3-Kandidaten ersetzt, SHA-256 jeweils `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`. Danach acht Kurs-Runner-Spiele bestanden, beide Seiten/Gegner, je 303 Schritte, explizit verifizierte 18 Netze und frisches Belief. Maximale gemessene Entscheidungszeit 39,82 ms, keine Aussage zu einem unbekannten Turnierlimit. Manifest: `experiments/releases/20261020_all18_v3.json`. Alte Sicherung unverändert. Nach Installation zusätzlich 41 Lade-/Runner-/Gewichtsschutztests bestanden (22,05 s). README und gemeinsamer Überblick beschreiben nun V3; Präsentationsdateien bleiben historisch.

**Datenintegrität:** Git hatte wegen `core.autocrlf=input` die CSV-Zeilenenden beim Einchecken normalisiert. Eine ordnerlokale `.gitattributes` erhält jetzt die exakten Messbytes, damit Audit-Hashes auch nach einem Clone stimmen. Alle elf CSVs im Arbeitsordner gegen ihre zuvor eingecheckten Fassungen geprüft: identische geparste Daten, nur Zeilenenden geändert.

**Weitere Arbeit:** Moayed verlangt ausdrücklich auch neues Training und laufende Koordination mit Subagents. Ein Agent beobachtet neue Remote-Commits, ohne selbst zu mergen. Geplant sind ein kontrollierter Reward-Trainingsvergleich und getrennte Tests zur Zielvergabe sowie Sap-Geometrie; noch nicht als Verbesserungen bestätigt. Mahmouds zusätzliche Reservierungen 502620–502819 und 502820–503219 beachten. Kein zweites CNN3-/V3nets-Training starten.

## 20.10.2026 – Codex mit Moayed: selbstständiger Prüf- und Verbesserungszyklus

**Auftrag:** Moayed hat die selbstständige Planung, Umsetzung, Prüfung und das Pushen freigegeben, einschließlich längerer lokaler Läufe. Laut Moayed arbeitet Mahmoud/Claude derzeit nicht weiter. Abgabe-Gewichte bleiben ausdrücklich unverändert. [Plan und Fortschritt](superpowers/plans/2026-10-20-autonomous-improvement.md), [Auswahlregeln und Grenzen](superpowers/specs/2026-10-20-autonomous-improvement-design.md). Moayed hat den Zeitraum anschließend bis **21.10., 06:00 Berlin / 04:00 UTC** verlängert und einen Morgenüberblick beauftragt. Seit 19:39 verlangt Moayed fortlaufende aktive Arbeit ohne Intervallsteuerung; Automation daher nur noch für den Morgenbericht um 06:00, danach deaktivieren. Weitere begründete Arbeit nach dem ersten Zyklus ist autorisiert; ab 05:30 Abschluss priorisieren.

**Neue Freigabe und Sicherung (20.10., nach Start des Zyklus):** Moayed erlaubt jetzt ausdrücklich, die Abgabe durch einen nach den Tests nachweislich besseren Kandidaten zu ersetzen. Das frühere Änderungsverbot oben ist damit für eine geprüfte Übernahme aufgehoben. Beide bisherigen Dateien sind unter `experiments/releases/20261020_old3_sym3/` mit Manifest und Rückweg bytegleich gesichert; Hash jeweils `3788fb72…d158`. Noch kein Austausch erfolgt. Spec und Plan enthalten zusätzlich einen gepaarten Vergleich mit der alten Abgabe auf dem vorab reservierten frischen Kartenblock, Kursprüfung und Rückfall bei Fehlern. Der Trainings-Überschreibschutz bleibt aktiv.

**Commit-Präferenz:** Moayed wünscht dauerhaft mehrere fachlich zusammengehörige, geprüfte Commits an abgeschlossenen Arbeitsschritten. In gemeinsamer Anleitung und Plan festgehalten. Sicherung und Übernahmeregeln bilden einen eigenen Meilenstein; eine tatsächliche Übernahme bekommt später einen separaten geprüften Commit.

**Aktualisierung:** `1cadc18` übernommen, `all18_v3` installiert und als Referenz gewählt. Vorhandene Tests: 153 bestanden. Acht Entwicklungsspiele von V3 stimmen in allen Kennzahlen außer Zeit mit `M_fo10_ptsap_fc_720.csv` überein. Kein neues Training; die im Protokoll erwähnte CNN3-Pipeline wird nicht dupliziert.

**Kursbetrieb:** Neues `scripts/check_candidate_runner.py` prüft Kandidaten mit dem unveränderten Kurs-Runner in einem temporären Arbeitsverzeichnis. Acht Spiele auf Seeds 500720/500721, zwei pro Seite/Gegner; Gewichte kopiert, Original-Paths.csv unverändert. Gemessen werden Entscheidungszeiten, frisches Belief bei neuer Instanz und das Aktionsformat. Der Gegner Solution_92 wird wie im Kurs-Runner nicht zusätzlich zwischen Spielen zurückgesetzt. Die Prüfung ist kein Siegquoten-Benchmark und zertifiziert kein unbekanntes Zeitlimit.

**Review:** Unabhängige Prüfung des neuen Prüfwerkzeugs fand einen möglichen falschen Erfolg bei still abgewiesenem Checkpoint. Behoben: Architektur, Config und sämtliche geladenen Netzparameter werden jetzt gegen den Checkpoint verglichen; Regressionstest erst fehlgeschlagen, danach bestanden. Keine Agentenänderung. Bewertung strategischer Stärke, vollständiger Spiellegalität und unbekannter Kurs-Zeitlimits bleiben außerhalb dieser Integrationsprüfung.

**Abschlussprüfung:** 163 Tests bestanden. Erneute acht Kurs-Runner-Spiele mit explizit geprüfter Checkpoint-Identität erfolgreich; [Bericht](../experiments/analysis/autonomous_20261020/runner_verified.json). Abgabe- und Kandidatenhashes unverändert.

**Remote-Abgleich:** Commits `790997a` und `96bbf6f` übernommen. Gesamte Testsuite: **167 bestanden in 129,41 s** mit begrenzten numerischen Threads. Ein vorheriger Lauf wurde während JAX-Kompilierung nach 88 erfolgreichen Tests abgebrochen und vollständig wiederholt; er zählt nicht als bestandene Suite. Kein Agentencode durch Codex geändert.

**Entwicklungsmessung abgeschlossen:** 1.200 Spiele mit unverändertem Code `975b3aa`: V3 102/120 gegen Solution_92, Reserve30 101/120, Reserve60 96/120, far6 101/120, far14 100/120; gegen default alle 120/120. Alle 240 Zeilen je Variante und Seitenpaare/Punktzählversion geprüft. Keine Variante übertrifft V3, daher keine Änderung aus dieser Suche. Unsicherheitsintervalle und Quellen: `experiments/analysis/autonomous_20261020/development_report.json`. Die Abgabeübernahme wird stattdessen ausschließlich für V3 geprüft.

**Nächster Schritt / Reservierung:** Entwicklungsmessung auf 500720–500779: Referenz V3, Sap-Energiereserve 30/60 und `far_opp` 6/14, vier einzelne Varianten. Auswahl anhand mittlerem `result`, eindeutiger Gewinner, default höchstens −2 Prozentpunkte. **502420–502619 für die Bestätigung genau eines Herausforderers reserviert**; nicht für andere Versuche benutzen. 502020–502219 bleiben Mahmouds CNN3-Block. Neue CSVs und Status unter `experiments/compare/autonomous_20261020/` bzw. `experiments/analysis/autonomous_20261020/`.

## 20.10.2026 spätabends – Claude Code mit Mahmoud: `pt_sap` + `far_cand`, neuer Kandidat `all18_v3`

**Diagnosen** (Val 720–779, `all18_fo10` vs Solution_92, Skripte im Arbeitsverlauf): Matchsiege 90 / 75 / 57 %; 42 von 109 verlorenen Matches mit mehr als 200 Punkten Rückstand. Bekannte eigene Punkte-Tiles in Match 2/3 (Step 40–95): 4,9 besetzt, 1,2 frei (davon 0,39 mit Gegner darauf, Rest meist von einer Unit angesteuert). Zielwechsel: 15–24 % aller Unit-Schritte, altes Ziel meist noch gültig. **Sap-Gelegenheiten:** steht eine Unit auf einem eigenen Punkte-Tile und hat ein Sap-Ziel, wählt das Netz nur in 9–12 % Sap, sonst meist „stehen“ (Solution_92 sappt in dieser Lage immer, `harvest()`).

**Neue Schalter (Default aus, Tests in `tests/test_rules_1910.py`):**
- `sticky` (Kostenabzug für das bisherige Ziel): Val 720 **−6,0 / −8,5 pp** (Stärke 3 / 6) → aus.
- `far_cand`: entfernte Kandidaten der Gegnerhälfte (mit `far_opp`) hinter die eigenen Kandidaten: Val 720 82,0 % (+1,5, n. s.).
- `pt_sap` (+ `pt_sap_reserve`): Unit auf eigenem Punkte-Tile sappt statt zu stehen, wenn ein Ziel in Reichweite ist: Val 720 81,0 % (+0,5, n. s.).
- `pt_sap` + `far_cand`: Val 720 83,0 % (+2,5, n. s.). **Bestätigung auf frischen Karten 502 220–502 419** (200 Karten, 400 Spiele/Gegner, Kombination vorab festgelegt): default 100 % → 100 %, **Solution_92 71,75 → 78,5 % (+6,75, KI [+1,8; +12,0])**.

**Weitere Versuche auf Basis `all18_v3`** (Val 720, Referenz `O_v3_720` 83,0 %; alle Schalter bleiben aus): `sap_pt_first` (Sap-Ziel bevorzugt Gegner auf Punkte-Tiles) ±0; `pt_hold` −2,0; `idle_sap` (jede stehende Unit sappt, Reserve 30) **−9,5**; `pt_sap_reserve` 25 / 60: −0,5 / −4,5; `fog_sap` (Reserve 0 / 30) −1,0 / −1,5; `pt_sap_zone` (auch gestapelt / Kandidaten-Tiles) ±0. CNN `cnn2/ppo_0040` mit `far_opp`, `far_cand`, `pt_sap` (in `PPOAgent` jetzt nur im Eval-Modus aktiv): 81,0 % (+1,0 n. s.). Diagnose `all18_v3` (Val 720–789): Matchsiege 91 / 81 / 69 % (vorher 90 / 75 / 57 %), Saps in Match 3 37,6 statt 19,4 je Spiel; Todesfälle je Spiel wir 56, Solution_92 66, überwiegend stehende Units (Kollision 14, wenig Energie 18, sonst 19, Sap 5).

**Später getestet (Val 720 gegen `O_v3_720` 83,0 %, alle aus):** `safe_moves` (kein Zug auf Tile mit gleich starkem sichtbaren Gegner) −1,0; `ram` −1,5; `cand_boost` 10 / 30 (eigene Kandidaten auf einer Stufe mit Gegner-Punkte-Tiles) −2,5 / −3,0. **Diagnose fehlende eigene Punkte-Tiles** (`all18_v3`, Val 720–759): Match 3 Step 60/90 fehlen 1,54 / 1,24 von 8,2 – davon ungetestete Kandidaten 1,00 / 0,82, Relic unbekannt 0,49 / 0,36, fälschlich tot nur 0,04. Solution_92 kennt in Match 3 ohne neues Relic 97 % seiner Tiles, wir 84 %. Relic-Funde: gleich schnell wie Solution_92 (Match 3 neues Relic Median Step 37 vs 41), aber in 17 % vs 12 % der 3. Matches nicht alle Relics gefunden.

**Noch später (Val 720 gegen 83,0 %):** `stale_all` −0,5; `opp_infer` +1,5; neuer Schalter `contest_sap` (steht auf dem Ziel-Tile ein Gegner, den die Unit per Kollision nicht schlägt, sappt sie dieses Tile aus der Entfernung) +1,5; `contest_sap` + `opp_infer` +1,5 (alle n. s.). Bestätigung der vorab festgelegten Kombination `all18_v3` + `contest_sap` + `opp_infer` läuft auf **400 frischen Karten 502 820–503 219** (nur gegen Solution_92, je 800 Spiele).

**Neuer Kandidat `all18_v3`** = `all18_fo10` + `pt_sap` + `far_cand` in der Config (`experiments/candidates/all18_v3.pth`, SHA-256 `aac1c910…d935`, auch in `scripts/install_candidates.sh` und im Manifest); 3 Karten × 2 Seiten × 2 Gegner identisch mit `--set`. Keine neue Abgabe.

**Läuft:** `scripts/pipeline_cnn3.sh` (BC von `all18_fo10`: 1200 Lehrerspiele, 4,27 Mio. Unit-Schritte, Lehrer-WR 74 % vs Solution_92; danach PPO 60 Iterationen; Messung auf Val 720 und frischen Karten 502 020–502 219).

**Prüfungen:** 153 Tests bestanden (neu: `far_cand`, 2 × `pt_sap`). Val-Seeds: 502 020–502 219 für cnn3 reserviert, 502 220–502 419 verbraucht; **502 420–502 619 sind für Moayeds Bestätigungslauf exklusiv reserviert** (sein Plan `docs/superpowers/plans/2026-10-20-autonomous-improvement.md`), nächster freier Index für Mahmoud 2620. Abgabe-Gewichte unverändert (`3788fb72…d158`).

## 20.10.2026 – Codex mit Moayed: lokale Umgebung und all18_fo10-Funktionstest

**Auftrag und Einrichtung:** Auf Moayeds Mac (M3, 8 GB, arm64) eine eigene `.venv` im Projekt angelegt, `requirements.txt` installiert und ausschließlich in dieser Umgebung die Kursregel auf drei Matches gesetzt. Ausgangsstand `5ec86ae`. Python 3.13.13, PyTorch 2.14.1, LuxAI-S3 0.2.1, NumPy 2.5.4, JAX/JAXlib 0.12.0. Vollständige Paketversionen, Befehl und Prüfsummen: [Umgebungsnachweis](../experiments/analysis/local_moe_environment_20261020.json). `.venv` bleibt lokal und gitignored; weder System-Python noch Agentenquellen geändert.

**Prüfung:** `pip check` ohne Konflikte; `scripts.set_match_count --check` bestätigt drei Matches. `scripts.par_eval` mit `all18_fo10`, `--first 720 --n 2 --workers 2`: Seeds 500720/500721, beide Seiten, default und Solution_92, insgesamt acht Spiele. Ergebnis: default 4/4 Siege, Solution_92 2/4 Siege. [Lokale Messdaten](../experiments/compare/local_moe_all18_fo10_20261020.csv) stimmen in allen erfassten Feldern außer `secs` mit den zugehörigen Zeilen von `F_a18_fo10_720.csv` überein (numerische Vergleichstoleranz 1e-9). Vom Evaluator gemessene Laufzeit 32 Sekunden; erste Python-/Bibliotheksinitialisierung kommt zusätzlich hinzu. Kein neuer Leistungsvergleich auf unbekannten Karten, keine neuen Seeds verbraucht.

**Synchronisierung während der Arbeit:** Mahmouds neuer Commit `2524f0c` (standardmäßig ausgeschalteter `sticky`-Schalter, CNN3-Pipeline) vor dem Hochladen übernommen. Dieselben acht Spiele anschließend erneut ausgeführt: alle Kennzahlen außer Laufzeit weiterhin identisch, Evaluator-Laufzeit 11 Sekunden. Beide Abgabe-Dateien und der Kandidat auch danach unverändert. Insgesamt 16 Spielausführungen auf denselben zwei bekannten Karten; keine unabhängige zusätzliche Stichprobe.

**Schutz und Grenzen:** Kein Training, keine Codeänderungen, keine vollständige Testsuite und kein zusätzlicher Kurs-Runner-Test. Beide Abgabe-Dateien vor/nach dem Test SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`; Kandidat `all18_fo10` unverändert `b2b7ffcc506d71a4657bb8990a71c0b25c4535f0f41564054ff687a1fa7b4607`. Die Python-/JAX-Versionen weichen von Mahmouds Trainingsmanifest ab; auf diesen acht Spielen wurden dennoch identische Kennzahlen reproduziert. Das ist keine Garantie für sämtliche Trainings- und Auswertungspfade.

**Weiterarbeiten:** Befehle im Projekt mit `.venv/bin/python` ausführen oder die Umgebung mit `source .venv/bin/activate` aktivieren. Die vier geteilten Kandidaten sind bereits an den Originalpfaden installiert. Für einen erneuten Test einen neuen CSV-Ausgabepfad wählen. Umfangreichere Runner-Prüfung und Auswahl des nächsten Verbesserungsversuchs bleiben offen; Nachttraining ist möglich, wurde aber noch nicht gestartet.

## 20.10.2026 abends – Claude Code mit Mahmoud: Pipeline-Ergebnisse und PPO-Prüfpunkt

**Ausgangslage:** Moayeds Review `d0db18c` per Fast-Forward übernommen; danach Pipeline-Ergebnisse geprüft (Punkt 1 der Arbeitsliste). Mac war 09:58–16:54 zugeklappt im Akkubetrieb (Clamshell Sleep), die Trainings pausierten in dieser Zeit.

**Pipeline `pipeline_2010.sh`** (Log `experiments/pipeline_2010.log`):
- PPO `cnn2c` (ab `cnn2/ppo_0040`, `w_opp_points=1`, nur Reward geändert, kein Pool): Val 720 Iteration 10/20/30/40 = 78,0 / 78,0 / 75,0 / 77,0 % gegen 80,0 % am Start → kein Gewinn.
- `fo6` (6 Netze `full_rules_fo`, `far_opp=10` schon im Training, je 4000 Spiele mit 70 % Solution_92): Val 720 77,0 % (−3,5 vs `all18_fo10`, n. s.).
- `all24fo` (`all18` + `fo6`, `far_opp=10`): Val 720 78,0 % (−2,5, n. s.).
- **Frische Karten 501 820–502 019** (200 Karten, 400 Spiele/Gegner, vorab in der Pipeline festgelegt): default alle 100 %; Solution_92 `all18_fo10` 74,75 %, `fo6` 75,75 % (+1,0, KI [−3,7; +5,5]), `all24fo` 77,5 % (+2,75, KI [−1,0; +6,5]) → **kein belegter Unterschied, `all18_fo10` bleibt Referenz.** `all18_fo10` auf zwei frischen Blöcken: 80,0 % und 74,75 %; die Kartenblöcke streuen deutlich.
- Weitere Val-Tests: `all18_fo10` + `ram` 80,0 % (−0,5).

**PPO-Prüfpunkt aus dem Review** (int8-Kartenebenen im Update): 2 Spiele mit `cnn2/ppo_0040` gegen Solution_92 (Seeds 123 401/123 402, Trainingsbereich), 7183 Unit-Schritte, gleiches Netz: Ratio neu/alt im Mittel 1,00005, mittlere Abweichung |r−1| 0,0015, Maximum 0,10, kein Schritt jenseits der Clip-Grenze 0,15. Die Rundung erklärt den späteren Leistungsabfall also nicht; Ebenen liegen in [−0,3; 1,0], kein int8-Überlauf.

**Kandidaten-Manifest** `experiments/candidates_20261020.json`: SHA-256, Quellnetze (mit SHA-256), abweichende Config, Bauschritte und Ergebnisse für `all18_fo10` (SHA-256 `b2b7ffcc…4607`, 18 Netze) und `all24fo` (`e9ff09a6…8b03`, 24 Netze). Auf Wunsch von Moayed (über Mahmoud) liegen die Gewichte jetzt **versioniert in `experiments/candidates/`** (`all18_fo10.pth`, `all24fo.pth`, `cnn2_ppo0040.pth`, SHA-256 identisch mit den Originalen, README mit Ergebnissen und Befehl); Ausnahme in `.gitignore` vermerkt. Keine neue Abgabe. Kurs-Runner-Test `all18_fo10` (isolierte Kopie, 15 vs 2, 2 Spiele als player_0) ohne Fehler; der ausführlichere Runner-Test aus dem Review (beide Seiten, Laufzeit pro Zug) steht noch aus.

**Seeds:** Val bis 502 019 verbraucht, nächster freier Index 2020. Abgabe-Gewichte unverändert (`3788fb72…d158`).

## 20.10.2026 – Codex mit Moayed: Review-Erkenntnisse und nächste Schritte dokumentiert

**Auftrag:** Erkenntnisse aus der Prüfung von Mahmouds Commits und Vorschläge für die weitere Arbeit gemeinsam zugänglich machen. Ausschließlich Dokumentation; keine Änderungen an Agent, Gewichten, Training oder Runner. Laut Moayed erhielt die erste Präsentation die Note **1,3**.

**Übergabe:** Neuer [Review und priorisierte Arbeitsliste](REVIEW_NAECHSTE_SCHRITTE_20261020.md), geprüft gegen `2ed46e4`. Enthält nachgezählte Benchmark-Ergebnisse, Antworten auf die Prof-Fragen zu Reward/DQN/PPO/CNN und 18.000 Spielen sowie konkrete Prüfkriterien. Reihenfolge: aktuelle Pipeline-Ergebnisse prüfen und Kandidaten reproduzierbar sichern; Kurs-Runner prüfen; Match-3-Zielwahl verbessern; breiter mit zurückgehaltenen Karten bewerten; PPO-Konsistenz und Reward-Beiträge untersuchen. Vorschläge sind noch keine Umsetzung oder Freigabe für Agentenänderungen.

**Wichtige Abgrenzungen:** `all18_fo10` ist ein experimenteller Kandidat, keine neue installierte Abgabe. Seine Gewichte und die PPO-Checkpoints sind gitignored und müssen separat zwischen den Arbeitsumgebungen verfügbar gemacht werden. Die neue Pipeline `pipeline_2010.sh` reserviert bereits Karten 501820–502019; keine doppelten Versuche oder widersprüchlichen Seed-Zuweisungen starten. Historische Karten 900000–900029 sind kein unberührter Testsatz. Das CNN ist beobachtet ähnlich erfolgreich wie `all18`, aber weder als überlegen noch statistisch gleichwertig belegt. Reward-Strafe und Gegner-Pool wurden gemeinsam verändert und lassen sich daraus nicht einzeln bewerten.

**Prüfungen:** Verlinkte Ergebnis-CSVs nachgezählt, vollständige Seitenpaare/eindeutige Schlüssel und Punktemessversion geprüft; Dokumentlinks und Git-Diff geprüft. Keine neuen Spiele oder Trainings, keine Anwendungstests. Der Dokumentationscommit verändert ausschließlich Markdown-Dateien. Beide Abgabe-Dateien behalten SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`. Ausgangs-Arbeitskopie mit ihrem älteren Agentenstand nicht umgeschaltet; die Dokumentation wurde auf dem aktuellen GitHub-Stand in einer separaten Arbeitskopie erstellt.

**Offen für Mahmoud:** Zuerst aktuelle Pipeline-Ergebnisse und Verfügbarkeit der Kandidatengewichte prüfen, dann einen der vorgeschlagenen Versuche gemeinsam auswählen. Die Arbeitsliste enthält auch einen noch ungemessenen PPO-Prüfpunkt: unterschiedliche Rundung der Kartenebenen bei Rollout und Update. Keine der vorgeschlagenen Codeänderungen wurde hier umgesetzt.

## 20.10.2026 – Claude Code mit Mahmoud: Nacht-Ergebnisse, PPO-Stände, CNN-Ensemble

**Nacht Teil 2** (`scripts/overnight_2010.sh`, Log `experiments/overnight_2010.log`): 6 weitere `full_rules`-Netze mit 70 % Solution_92 (`*_s18`–`*_s23_sol70`, je 4000 Spiele, 138 min). 24er-Ensemble `all24` gegen `all18` auf frischen Karten 501 220–501 419: default beide 100 %, Solution_92 71,5 vs 72,0 % (−0,5, KI [−4,8; +3,7]) → **mehr Netze bringen nichts mehr**.

**PPO `cnn2`** (200 Iterationen ab BC, lr 1e-4, eigener Critic-Kopf), Val 720–819 vs Solution_92 (BC 73,0 %): Iteration 30 und 40 je **80,0 %**, 50 77,5 %, 60 72,5 %, 70 69,5 %, 100 70,0 %, 150 67,5 %, 200 68,0 % – PPO verbessert zuerst und verschlechtert sich danach (Entropie 0,38 → 0,12). Bestätigung auf frischen Karten 501 420–501 619 (200 Karten, 400 Spiele/Gegner): **`ppo_0040` default 100 %, Solution_92 72,8 %; `ppo_0030` 99,8 % / 72,8 %; `all18` 99,8 % / 71,0 %** (Δ +1,8, KI [−3,7; +7,2]) → ein einzelnes CNN nach 40 PPO-Iterationen ist so stark wie das 18er-DQN-Ensemble, aber nicht nachweisbar besser.

**`all18` auf allen frischen Karten** (501 020–501 619, 600 Karten, je 1200 Spiele): default 99,9 %, Solution_92 72,4 %.

**Neu: CNN-Policy-Ensemble** (`PPOAgent.extra_nets`, `scripts/build_cnn_ensemble.py`, Tests `tests/test_cnn_ensemble.py`): mittelt im Eval-Modus die log-Wahrscheinlichkeiten. Ensembles aus Ständen desselben Laufs (3, 5, 7 Netze) auf Val 720: 76,0 / 78,0 / 76,5 % gegen 80,0 % für `ppo_0040` allein → Stände eines Laufs sind zu ähnlich; Ensemble braucht unabhängige Läufe.

**Diagnose Match 3** (60 Karten × 2 Seiten, Ground Truth, Skripte `diag_m3`, `diag_m3b`, `diag_know3` im Arbeitsverlauf): Matchsiege 88 / 69 / 49 %. Verlorene 3. Matches sind Karten mit vielen Punkte-Tiles (10,1 je Hälfte, gewonnene 5,6). Dort besetzt Solution_92 bei Step 50 7,5 der 10 Tiles seiner Hälfte, wir 5,3 der 10 unserer Hälfte, obwohl 15 Units leben: 5,7 Units sind auf dem Weg zu Punkte-Tiles der Gegnerhälfte (im Mittel 18 Felder entfernt, nur 0,2 dort angekommen), 1,8 eigene Punkte-Tiles sind noch ungetestete Kandidaten, 0,9 außerhalb jeder Kandidatenzone. Wissen über die eigene Hälfte (alle Karten, Match 3 Step 50): wir 6,1, Solution_92 6,6 von 7,9 Tiles, beide ohne Fehler.

**PPO `cnn2b`** (ab `cnn2/ppo_0040`, lr 3e-5, Entropie 0,01, `--seed 1`, 80 Iterationen; `cnn2b/ppo_0040.pth` ist Iteration 40 dieses Laufs, nicht der Startpunkt): alle 16 Stände auf Val 720 zwischen 74,0 und 78,5 % gegen 80,0 % am Start → **Weitertrainieren mit PPO bringt nichts mehr.**

**Neuer Schalter `far_opp`** (Antwort auf die Match-3-Diagnose): Punkte-Tiles der Gegnerhälfte, die weiter als `far_opp` Felder von der Unit entfernt sind, rangieren in der Zielzuweisung hinter den Kandidaten-Tiles (`features.assign_targets`, Tests in `tests/test_rules_1910.py`). Val 720: `all18` + `far_opp=10` **80,5 % statt 76,5 %** (+4,0, KI [−1,0; +9,5]); CNN `ppo_0040` + `far_opp` 10 / 6: +0,5 / −0,5 pp. **Vorab festgelegte Bestätigung `far_opp=10` auf frischen Karten 501 620–501 819** (200 Karten, 400 Spiele/Gegner): default 100 % → 100 %, **Solution_92 74,0 → 80,0 % (+6,0, KI [+2,2; +9,8])**. Kandidat **`experiments/ensembles/all18_fo10.pth`** (gitignored) = `all18_kdf` + `far_opp=10` in der Config; 5 Karten × 2 Seiten × 2 Gegner identisch mit `--set`. `par_eval --set` wirkt jetzt auch auf CNN-Checkpoints.

**Läuft:** PPO `cnn2c` ab `cnn2/ppo_0040` mit Reward-Strafe für Gegnerpunkte (`w_opp_points=1`), 40 Iterationen.

**Prüfungen:** 148 Tests bestanden. Val-Seeds bis 501 819 verbraucht, nächster freier Index 1820. Abgabe-Gewichte unverändert.

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

**Weitere Ergebnisse 19.10. abends:** „Scharfschützen“-Regel (Ziele auf gegnerischen Punkte-Tiles durch Tiles ersetzen, die Solution_92 wegen seiner Manhattan-Reichweitenprüfung nicht beschießt): **22 % statt 74 %** – viele „gegnerische“ Punkte-Tiles liegen direkt an der Mittellinie und sind wertvoll; Code wieder entfernt. PPO `cnn1` bei Iteration 80 angehalten (Rechner überlastet, 285 s/Iteration): Iteration 50 63,0 %, 80 60,5 % vs Solution_92 (BC 58 %), default jeweils 100 % – kein belegter Fortschritt durch PPO.

**Spätere Tests 19.10.:** Kurs-Runner setzt die Klassenvariablen von Solution_92 (`Global`) zwischen Spielen nicht zurück; Nachstellung in einem Prozess (45 Spiele je Variante, Seeds 700 000+): rules6_kdf 71 % mit Zurücksetzen, 73 % ohne → kein nennenswerter Effekt. Neue Regel `ram` (auf Nachbar-Tile mit schwächerem Gegner fahren, Kollision zerstört ihn): Val 720–819 +2,5 pp (n. s.), neue Karten 920–1019 −3,5 pp (n. s.) → aus. `cand_quota=2` mit rules6: −4,5 pp → aus. Fehlende eigene Punkte-Tiles bei Step 95 in Match 3 (je Spiel): 0,62 ungetestete Kandidaten, 0,25 Relic unbekannt, 0,18 unter Asteroid, 0,08 fälschlich leer (`keep_dead_fast`). **Bester bestätigter Stand `rules6_kdf` auf neuen Karten 920–1019: default 98,5 %, Solution_92 70,0 %.** Val-Seeds jetzt bis 500 1019 verbraucht.

**Spät am 19.10.:** `opp_infer` (Null-Tiles aus dem Gegner-Punktgewinn) und `stale_all` (veraltete Erkundung in jedem Match, solange das Paar fehlt): +0,5 / +1,5 pp (n. s.), 0 falsche Punkte-Tiles. **Orakel-Diagnose** (echte Punkte-Tiles eingespeist, 40 Karten × 2 Seiten): 75,0 % vs 77,5 % ohne Orakel, Match 3 51 % vs 56 % → **Wissen ist nicht mehr der Engpass**, sondern das Besetzen (Match 3, Step 20–60: 3,8 Units auf Punkte-Tiles, 3,9 unterwegs zu gegnerischen Punkte-Tiles, 2,6 erkunden). `pt_walk` für alle Ziele −10 pp, ab Match 2 −6,5 pp, nur eigene Hälfte (`pt_walk_own`) +2,5 pp (n. s.). **CNN `cnn2`** (BC vom Lehrer rules6, 48 Kanäle × 4 Blöcke, 8 Epochen, 85,7 % Übereinstimmung): **default 100 %, Solution_92 73,0 %** (Val 720–819) – ein einzelnes CNN auf Lehrer-Niveau (+15 pp vs `cnn1`, KI [+7,5; +23]). Um 21:46 Notfall-Ruhezustand wegen Überhitzung (Deckel zu, Volllast), Prozesse liefen nach dem Aufwachen weiter.

**Nacht-Pipeline** `scripts/overnight_1910.sh` (Log `experiments/overnight_1910.log`): wartet auf die Trainings, baut `sol70_6`, `rules12`, `opp6`, `all18`, misst sie auf Val 720–819 gegen `N_r6_kdf_720` (rules6 + alle Regeln) und startet PPO für `cnn2` (200 Iterationen).

**Ergebnisse der Nacht-Pipeline (Val 720–819, alle mit denselben Regel-Schaltern wie `rules6_kdf`, Referenz 99,0 % / 74,0 %):** `sol70_6` (6 Netze, 70 % Solution_92 im Training) 98,5 % / 76,0 % (+2,0 n. s.); `rules12` (rules6 + sol70) 99,5 % / 75,5 %; `opp6` (Gegner-Punkte-Strafe `w_opp_points=1` + Pool) 100 % / **68,0 % (−6,0, KI [−14; +2])** → Gegner-Strafe und Pool helfen nicht; **`all18`** (alle 18 Netze) **100 % / 76,5 %** (+2,5 n. s.). CNN `cnn2` BC allein 100 % / 73,0 %. DQN `all18` + `cnn2`-Policy gemischt: Temperatur 0,2 −1,0 pp, 0,5 −3,0 pp (n. s.) → Mischung bringt nichts.

**Bestätigung auf frischen Karten 501 020–501 219 (200 Karten × 2 Seiten, `W_*_1020.csv`):** `rules6_kdf` default 98,8 %, Solution_92 67,2 %; **`all18` default 100 % (400/400), Solution_92 74,3 % → +7,0 pp, KI [+2,5; +11,7]** – erste signifikante Verbesserung seit `rules6`. Kandidat **`experiments/ensembles/all18_kdf.pth`** (gitignored) = `all18` mit `keep_dead_fast` in der gespeicherten Config; auf 10 Karten × 2 Seiten × 2 Gegner identische Ergebnisse wie mit `--set` (40/40). Kurs-Runner-Test für `all18_kdf` steht noch aus. PPO `cnn2` läuft (Rollout-WR vs Solution_92 schwankt 0,4–0,9 bei 34 Spielen je Iteration, kein klarer Trend bis Iteration 25); um 23:31 kurzer Ruhezustand, weil `caffeinate` an das Pipeline-Skript gebunden war – jetzt an den PPO-Prozess gebunden. Nichts davon ersetzt die Abgabe.

**Arbeitsweise:** Mahmoud möchte, dass gute Stände direkt auf `main` committet und gepusht werden (keine Pull Requests/Feature-Branches). Achtung: Der Projektordner wird synchronisiert; ein Branch-Wechsel erzeugte Kopien „… 2.csv“, die in `989cc3c` entfernt wurden.

**Werkzeuge:** `scripts/par_eval.py` (100 Karten × 2 Seiten × 2 Gegner in ~50 s, `--set` Schalter, PPO-Checkpoints automatisch erkannt), `analyze_losses.py --set`. Tests: 143 bestanden (neu `tests/test_rules_1910.py`).

**Seeds:** Val 500 660–501 219 verbraucht (Diagnose 660–719, Tuning 720–819, Bestätigung 820–919, 920–1019 und 1020–1219); nächster freier Val-Index 1220. Trainingsseeds PPO 100 000+. Test-Seeds 900 000+ nicht angefasst.

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
