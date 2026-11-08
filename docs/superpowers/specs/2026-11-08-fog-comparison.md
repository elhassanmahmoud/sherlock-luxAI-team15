# Begrenzter Vergleich der Fog-Nachtrainingsnetze

Vor neuen Leistungsdaten festgelegt, während die getrennte Trainingsstudie aufa3111c3 läuft. Der Nutzer will einen tatsächlich stärkeren Agenten und ausdrücklich weniger Testspiele. Keine100%-Garantie. Es werden keine neuen Regeln/Netzarchitekturen/Komponenten aus Ergebnissen ausgesucht.

## Zulassung und feste Modelle

Erst nachdem alle vier Fog-Arme und beide Vorlaufpaare vollständig unabhängig akzeptiert sind. Vor jeder Änderung des eingefrorenen Trainings-HEAD/source muss die tatsächliche `validate_final_receipt`-Prüfung samt unabhängigem Tensor-/Rohdatenaudit eine historische Abnahme erzeugen. Sie bindet Quelle, vier Endcheckpoints, Receipts, alle Eingangsdaten und Abschlussnachweise an Hashes. Spätere Vergleichswerkzeuge prüfen diese historischen Bindungen und die Modelle; sie umgehen oder schwächen nicht den aktiven Trainingsvalidator, der bewusst aktuellenHEAD=a311 verlangt.

- V14: unverändertes Archiv `experiments/releases/20261101_v14_baseline/agent_p0.pth`, Hash98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8; aktiveP0/P1 undZIP bleiben ebenfalls gebunden.
- CONTROL38: exakt36 Originalkomponenten in ursprünglicher Reihenfolge, danach finale control41/control42.
- NEUTRAL38: exakt36 Originalkomponenten, danach finale neutral41/neutral42.
- Jeder Beitrag gleich gewichtet. Beide Kandidaten mit ursprünglicher V14-Inferenzkonfiguration, neues TrainingsrewardflagFalse. Keine Auswahl einzelner Netze/Checkpoints. Einbauen ausschließlich in neue Experimentdateien; Mitgliedertensor-Hashes, Reihenfolge, Config, Speicher-/Ladekontrolle dokumentieren.

## Einmalige Vorauswahl:440 Spiele

Alle dreiModelle gegen Solution92,sol92_sq,default auf denselben20Karten7700000–7700019, beideSeiten:360Spiele. CONTROL38 undNEUTRAL38 zusätzlich direkt gegen exaktesV14 auf20anderenKarten7700100–7700119:80Spiele. ElfJobs, je40Partien. FrischeKarten vor Verwendung über lokaleWorktrees auditieren; keine ungeprüfte Umnummerierung bei Überschneidungen. Kein Spielstart vor Werkzeug-/Datenabnahme.

Zweierpanel bedeutet gleichgewichteteSolution92+sol92_sq; default separat. BeideKandidaten sind nominierbar, mit denselben vorab festgelegten Bedingungen gegenüberV14:

1. Panel-Spielscore mindestens+2,5Prozentpunkte (mindestens zwei volle zusätzliche Score-Siege auf80).
2. Solution-Spielscore und strikteSiege nichtniedriger alsV14.
3. default40/40strikteSiege.
4. Direktspielscore mindestens50Prozent.

Genau einen qualifizierten Kandidaten wählen: höchsterPanel-Spielscore, dannmeisteSolution-Siege, dannhöchsterDirektspielscore, bei vollständigemGleichstand CONTROL38. AlleSchwellen/Rangfolgen mit ganzzahligenHalbsieg-Zählern umsetzen, um Gleitkomma-Grenzfehler auszuschließen. Kein qualifizierter Kandidat: beenden, keinNachschlag/Nachrücker/Refit. N−C imPanel zusätzlich vorab geplante gepaarteMechanikanalyse, ohne allgemeine kausaleBehauptung aus zweiTrainingsstarts.

## Höchstens eine frische Bestätigung:1200 Spiele

Nur wenn vollständige, unabhängig geprüfteVorauswahl genaueinenNominierten liefert. Nominierter+V14 gegen das etablierte `LOCAL_SIX` unddefault auf40frischenKarten7701000–7701039, beideSeiten:1120Spiele. Dazu nurNominierter direkt gegenV14 auf40separatenKarten7701100–7701139:80Spiele. FünfzehnJobs, insgesamt1200; mitVorauswahl maximal1640Leistungsspiele. VierKartenlisten getrennt undvorher auditieren. Trainings-/Technikspiele bleiben separatgezählt.

LOCAL_SIX: solution92,sol92_sq,V3(`experiments/releases/20261022_all18_v3/agent_p0.pth`),V7(`experiments/releases/20261022_v7_Bsnpd/agent_p0.pth`),V10(`experiments/releases/20261022_v10_baseline/agent_p0.pth`),V13(`experiments/releases/20261101_v13_neb/agent_p0.pth`). AlleGegner-Hashes wie im bestehenden lokalenVergleich prüfen.

Bestehende siebenFreigabegates unverändert: SechserpanelΔ≥+1pp unduntere95%-Grenze>0; Solution-ScoreΔ≥−0,5pp unduntereGrenze>−2,5pp; defaultScore≥99% undΔ≥−1pp; direkteuntereGrenze>50%. Dazu dreiSchutzbedingungen: Solution-Score undstrikteSiege nichtniedriger, defaultstrikteSiegrate≥99%. Bei80defaultSpielen verlangt99% genau80Siege. Kein stillesUmschreiben desSechserpanels zumZweierpanel. AlleGates müssen bestehen, danach erst unabhängigePrüfung/Kursreproduktion/Sicherung vor möglichemAustausch. BeiFAIL/unklar keinzweiterKandidat, keinezweiteBestätigung oderZusatzkarten.

## Statistik, Integrität und Grenzen

Spielscore=(Siege+0,5×Remis)/Spiele; strikteSiege separat. Exaktvollständige Schlüssel(opponent,seed,side) erzwingen. PaareganzerKarten mitbeidenSeiten/allenPanelgegnern gemeinsambootstrappen,5000Züge,PCG64-RNG0,95%-Perzentile. KeineMischung derPhasen oderaltenDaten. Zwanzig/VierzigKarten könnenkleineVorteile übersehen; unadjustierte/teilweise degenerierteBootstrapintervalle sind keineGarantie simultanerDeckung oderallgemeiner100%. NeueNEUTRAL-Bestätigung gegenV14 beweist ohnefrischenCONTROL-Vergleich nichtden isoliertenRewardeffekt; CONTROL-Erfolg wäreNutzen desNachtrainings.

Quellen/HEAD/Pläne/Modelle/Gegner/Seeds/Inputs währendjeder gesamtenPhase einfrieren. MaximalzweiModellworker, keineparallelenTests, AC/frischeechteQuota<100/STOP/Prozessbesitz prüfen. KeinautomatischerRetry oderTeilresultat-Reuse. HistorischeStudien/Profile unverändert. RohCSV undausgeführteKommandos perReceipt binden. Watcher beachtetMahmoud-Commits; Integration nuramsicherenPhasenübergang.
