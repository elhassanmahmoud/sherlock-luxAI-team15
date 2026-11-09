# Unabhängiger Abschlussaudit: beide Ensemble-Verhaltensarme

**PASS.** Einmaliger tatsächlicher Endaudit des vollständigen gemeinsamen Trainings unter Quelle `71090f760788bdcec8d7158bc5aab4fd47d406cc`: Exit 0, leeres stderr, **11.298 Checks, 521 Hashbindungen und 501 eindeutige gehashte Dateien**. Der unveränderte vorbereitete Prüfer wurde erst nach vollständigem Ownerabschluss und wirklichem Ende beider Originalworker ausgeführt.

| Arm | Vorlauf + Lernen | Envschritte | Tatsächliche Adam-Schritte je Parameter | Finale Replayzeilen | Gesamt eingefügte Übergänge |
|---|---:|---:|---:|---:|---:|
| on48 | 40 + 400 | 193.320 | 60.000 | 300.000 | 1.570.353 |
| on49 | 40 + 400 | 193.320 | 60.000 | 300.000 | 1.571.694 |

Damit **880 vollständige Trainingsausführungen und 120.000 Updates**, zusätzlich zu den separat akzeptierten vier Technikspielen. Beide festen Starts ohne Auswahl erhalten. Kein Leistungsresultat, stärkerer Kandidat oder V14-Ersatz aus diesem Audit abgeleitet.

## Tatsächliche Daten und Tensoren

Alle 440 Original-JSONL-Zeilen je Arm unabhängig gegen den vollständigen mit PCG64/Seed48 beziehungsweise49 selbst regenerierten Gegner-/Karten-/Seitenplan geprüft. Rows stimmen vollständig mit den finalen Receipts überein, alle 303/v2, korrekte schrittweise Env-/Lernzähler und Resultat-/Punktarithmetik. Je Arm genau 400 endliche nichtnegative protokollierte Lernspiel-Lossmittel. Originale Live-Reward-/UID-/Finalaktionsaudits decken die gezählten Übergänge; ihre Digestfelder und kumulativen Mechanismuszähler sind konsistent.

Beide eigenen tatsächlichen `final.pth` als CPU-Daten gelesen, ohne Agentkonstruktion oder Forward: exakte zwölf Dueling-Parameter mit richtigen Shapes/Dtypes, alle q-/Targetwerte endlich, Konfiguration 79/6 und Kontrollreward unverändert, keine zusätzlichen Ensemblemitglieder im Einzelcheckpoint. q nach Lernen gegenüber dem Originalinitialhash verändert. Target ist am finalen Update 60.000 bitgleich zu q. Sämtliche zwölf tatsächlichen Adamzustände vorhanden, korrekte Parametermapping/Shapes, endliche Momente, nichtnegative zweite Momente und **jede gespeicherte Schrittzahl exakt 60.000**. Eigenständig berechnete q-/Target-/Optimizeridentitäten entsprechen den finalen Livebelegen.

Beide tatsächlichen finalen Replay-NPZs vollständig unabhängig gelesen: je 300.000 Zeilen mit s/ns=(300000,79), sechs Folgemasken, exakten Dtypes und endlichen Werten; Actions, Terminals und Masken gültig. Eigenständig berechneter vollständiger Arrayhash entspricht der jeweiligen Receipt. Ringgröße stimmt mit Kapazität und den gezählten gesamten Einfügungen überein. Die bereits akzeptierten Vorlaufarrays wurden nicht erneut deserialisiert oder vollständig nachgerechnet.

## Erhaltene Vorläufe, Freigabe und Mechanismus

Akzeptierte unabhängige Vorlaufresultate, Prüfer, Bericht, beide Proofs und gespeicherte Vorlaufdateien unverändert gehasht. Die ersten 40 tatsächlichen Zeilen je Arm sind exakt die akzeptierten Proof-Rows. Ursprüngliche waiting-Marker und der gemeinsame manuelle Rootrelease sind erhalten; Release und Rootreview binden genau beide ursprünglichen Proofhashes, beide Rollen/Starts, Quelle und Admission. Keine neue Release-Datei durch diesen Audit.

Je Arm 133.320 Handlungsaufrufe, 132.000 Netzaufrufe und 4.752.000 Mitgliedsforwards. Die aufgezeichneten 35 eingefrorenen Identitäten, vollständige Quellenreihenfolge einschließlich Mitglied18 und ursprüngliche Setup-RNGbelege stimmen mit der akzeptierten Vorlaufbasis überein. Finale Zähler stimmen mit sämtlichen Spielabschnitten überein. Geänderte legale Präferenzen: on48 357.444, on49 345.080; das sind Mechanismuszahlen, keine Stärkeindikatoren. Die schon unabhängig geprüften drei Vorlaufbeispiele je Arm blieben unverändert gespeichert.

## Quelle, Dateien und tatsächliches Prozessende

Admission, sämtliche deklarierte Source-/Input-/Interpreter-/Schutzdateien, beide finalen Receipts und deren vollständige Artefaktmaps geprüft; keine unvollständigen Kandidatenartefakte. V14 p0/p1 und ZIP unverändert. Source/HEAD, gemeinsamer Release und abgeschlossener Ownerstatus blieben während der Prüfung fest.

Vor der ersten Archivladung eigenständig nachgewiesen: Owner **54950**, Originalworker **54962/54967** und deren Prozessgruppen sowie Wachhalter **55150** tatsächlich beendet. Owner complete/active leer, beide ursprünglichen Returncodes 0 und beide originale Finalchecks PASS. Original-PIDs/-Gruppen nach dem Audit erneut abwesend. Prästartbeleg und tatsächliche Prozesssnapshots extern gespeichert.

## Grenzen

Die tatsächlichen finalen q-/Target-/Adamtensoren und finalen Ringarrays sind unabhängig wiedergewonnen. Einzelne 60.000 Batchverluste je Arm sind nicht separat archiviert; geprüft sind 400 endliche Spielmittel. Erfolgreicher unveränderter `play_one` verweigert abgefangene Fehler beider Spieler, die Rohzeilen enthalten aber keine separaten Fehlerzähler.

Nicht alle Trainings-UID-/Outcome-/Gegenformelstreams, Rohbeobachtungen und nativen Aktionen wurden archiviert. Deshalb lassen sich vollständige ursprüngliche Rewardprovenienz oder alle per-Spiel-Replaydigests nicht aus dem finalen Ring neu erzeugen. Eingefrorene35-Rohtensoren und vollständige historische RNG-/Bibliothekszustände fehlen ebenfalls; deren unveränderte Identitäten bleiben gebundene Livehashbelege. Kein breiter erneuter Audit geschlossener Studien, keine Modellkonstruktion, Inferenz, Tests, Spiele, Quelländerung, Freigabe oder Folgephase.

## SHA256

- Admission: `be82efd30f0b7eb7beab40ac47a98dbba6c25f7ddf9f0cbfe376e3d773c2f24d`
- Gemeinsamer Release: `eefa11400c04fce531e6c569f04fb6f408010bcafc6ba36229e10ab7fcab1689`
- on48 Receipt: `ab3429c4af89cc43a09470ef19f58aec0e142344c4a61db9c14dc6d0e87eb17e`
- on49 Receipt: `6e2e3a8c3a02690b997691376685d36c790a254a6e4636c065a7e73305ca78cc`
- on48 final.pth: `486b9b44e12be251213b00fd84b82964c7aa5a781bdf086da866da42eb95a3fd`
- on49 final.pth: `e0668fdcfbf70b9c85180e81af9d3bfd684b65d8aba048addee36bb58bdf27d3`
- `results.json`: `661795fd674acb51c68a65da71d143a871eff593234351b2ac90d871abc45bb9`
- `check.py`: `1fa844d713e1a00098d0e1d364f4ebd119dd9b018d0bf52e3e75c993833ca4d1`
- `bindings.json`: `27d2103c424bfaa4752d191f2ab010b148d67993e9ecf3f0275bfe1eab8075af`
- `run.log`: `708037e81b4cf1f1dc39d907b178e60775ff97a36a9820ee7e360e55b825b11e`
- `pre-execution.json`: `ad9f7fa4e90f84c8fbc056a7f5deeba3fae00bc2a9bf63fabc0973d82375de37`
