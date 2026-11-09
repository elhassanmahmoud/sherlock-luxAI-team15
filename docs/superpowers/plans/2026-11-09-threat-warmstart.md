# V14-Warmstart mit öffentlichen Gefahrmerkmalen

Stand 09.11.2026. Moayed hat die autonome Fortsetzung einschließlich Training, Tests, Commit und Push beauftragt und Akkubetrieb ausdrücklich erlaubt. Kein erneuter geschlossener Versuch. Ausgangspunkt ist V14; ein besserer Nachfolger ist bislang nicht belegt.

## Entscheidung und Grenze

Nach den erfolglosen größeren Ensembles, Reward-/Folgeaktionsvarianten und drei kleinen Entscheidungsscreens wird genau eine Informationshypothese geprüft. Die vorhandenen 79 Merkmale enthalten bereits Gegnerinformationen; weitere 22 vorhandene öffentliche Gefahrmerkmale könnten räumliche Kampfsituationen besser unterscheiden. Kein Zugriff auf versteckte Zustände oder zukünftige Gegneraktionen. Historische V3-Threat-Trainings waren negativ; dieser kontrollierte Warmstart ist ebenfalls ergebnisoffen. Eine weitere SAP-Regel oder reine Ensembleumgewichtung wird jetzt nicht verfolgt.

## Gemeinsame Vorgaben

- Studienkopie und bestehender Arbeitszweig bleiben Arbeitsort. Produktiver Agent, Kursrunner, V14-Dateien und ZIP unverändert. Exakte geschützte Hashes aus den bisherigen Studien übernehmen.
- Ein festes V14-Mitglied, Index 18, ohne erneute Auswahl. Zwei gleich große Netze mit 101 Eingaben: `control` bekommt 22 Nullen, `threat` die bestehenden 22 öffentlichen Merkmale. Beide behalten den ursprünglichen 79er-Präfix. Gleiche Masken, Regeln, Belohnung, Optimierung, Gegner-, Karten- und Seitenpläne.
- Erste Schicht: ursprüngliche 79 Spalten exakt kopieren, neue 22 Spalten null. Alle übrigen Tensoren exakt übernehmen, Target gleich Q, Adam frisch, Replay leer, env_steps=60000 und learn_steps=0. Architektur 101→256→256, Dueling, sechs Aktionen. Kein impliziter Loader-Fallback. Mathematische Funktionserhaltung bedeutet keine garantierte bitweise Gleichheit mit einem 79er-GEMM; beide 101er-Arme müssen vor Gradienten jedoch exakt gleich entscheiden.
- V14-Konfiguration plus threat_feats=True, frozen=False, lr=0.00005, rules_in_training=True, rules_in_training_all=True, rescue_in_training=True. fog_unknown_reward_neutral=False und art_splash_in_training=False bleiben in beiden Armen gleich. Keine weitere Reward-, Target- oder Regelsuche.
- Ein gemeinsamer Start 47, epsilon=0.05; pro Arm genau 40 Vorlaufspiele ohne Gradienten und 400 Lernspiele, keine Zwischenvalidierung oder Bestcheckpointwahl. Mischung Solution 60 %, Quadrat-Solution 20 %, default 10 %, rush 10 %, vorab mit unabhängigem NumPy-Generator(47) vollständig festlegen. Seiten alternieren. Gleiche Karten für beide Arme; verschiedene Rollen dürfen nach Lernbeginn auseinanderlaufen.
- Feste Trainingskarten 9950000–9950199, Vorlauf 9950300–9950319. Diese Bereiche vor Start auf beobachtete frühere Nutzung prüfen, Lücken der Prüfung offenlegen. Bekannte Technikspiele 831006/player_1 und 831000/player_0 in beiden Armen: vier Ausführungen ohne Gradienten, kein Leistungsnachweis.
- Maximal zwei Modellworker, keine parallelen Tests. Frische echte Quota; bei tatsächlichen 100 % kontrolliert stoppen, kein Reset. Akku erlaubt. Prozessbesitz, STOP, unveränderte Quellen/HEAD/Eingaben und geschützte Dateien überwachen. Keine automatischen Wiederholungen, Ersatzspiele oder Phasenübergänge.

## Task 1: enger Lernprototyp

Eigene Dateien `scripts/threat_warmstart.py`, `scripts/threat_warmstart_owner.py` und gezielte Tests. Bestehende Spiel-, Quellen-, Prozess-, Quota- und Speicherhilfen wiederverwenden. Keine allgemeine neue Trainingsplattform. Eigener Agent-Adapter nullt ausschließlich die 22 Zusatzwerte der Kontrolle, einschließlich Cache und Folgezuständen. Echtmerkmalsarm verwendet den unveränderten bestehenden Featurepfad. Keine globalen Änderungen am produktiven Core.

Vor Gradienten tatsächliche aktuelle und nächste Replaymerkmale (101), Masken, finale Aktionslabels und öffentliche Merkmalswerte prüfen. Technische vier Spiele vergleichen native Aktionen und Ergebnisse der beiden 101er-Arme; beide Q/Target bleiben gleich initialisiert, kein Optimizerschritt. Technikdaten dienen nur der Funktion.

Danach zwei feste Lernworker. Nach jeweils 40 Vorlaufspielen gemeinsam anhalten: Q/Target/Optimizer unverändert, hinreichender Replay, beobachtete echte Zusatzmerkmale, gleiche ursprüngliche Merkmale/Aktionen/Rewards/Spielverläufe beider Arme. Die unterschiedlichen Zusatzmerkmale ausdrücklich aus dem Gleichheitsdigest ausschließen. Erst nach tatsächlicher Root-Abnahme die einmalige Freigabedatei für die 400 Lernspiele schreiben. Bei Widerspruch abbrechen, keine automatische Reparatur/Wiederholung.

Pro Spiel persistente Zeile mit Karte, Seite, Gegner, Ergebnis, Zählern, Verlust und Aktions-/Replayprüfung. Abschließend nur Endcheckpoint und Replay sichern; explizite Status-/Hashbelege. Kontrollspalten müssen null bleiben, Merkmalsarm muss nachweislich aus exponierten Zusatzmerkmalen lernen. Unterbrochene Arbeit ist kein vollständiger Kandidat.

## Task 2: unabhängige Abnahme und Ausführung

Gezielte synthetische Tests vor realen Modellen. Unabhängiger Code-/Methodenreview; Root liest finale Änderungen und Belege. Kartenprüfung, Quellen-Commit, geschützte Hashes und echte Quota separat aufnehmen. Technikphase zuerst, dann tatsächliche Abnahme vor Training. Originalprüfungen vor Quellenfreigabe ausführen; Rohdaten unabhängig nachrechnen. Keine wiederholten gleichen Tests ohne neue Änderung.

## Spätere Leistungsprüfung – noch nicht implementiert oder gestartet

Nach vollständig geprüftem Training genau Mitglied 18 ersetzen, übrige 35 erhalten. Beide Studienensembles haben dieselbe Reihenfolge, 101er-Hauptnetz und 35 originale 79er-Netze. Konfiguration für Inferenz wie V14 plus threat_feats=True; Kontrolle weiterhin Nulladapter. Reordering/Floating-Point-Grenzen ausdrücklich dokumentieren. Vor Performance einen getrennten festen Plan und technische Aufnahme erstellen.

Vorgesehener kompakter Screen: je 40 Solution-Spiele für V14, Kontrolle und Threat auf denselben 20 neuen Karten; je 40 direkte Threat-gegen-V14- und Threat-gegen-Kontrolle-Spiele auf getrennten neuen Karten, insgesamt höchstens 200. Keine Trainingskarten oder Technikspiele als unabhängiger Test zählen. Nominierung nur bei mindestens gleich gutem Solution-Ergebnis wie beide Referenzen und mindestens 24/40 in beiden direkten Blöcken. Keine Verlängerung bis zum gewünschten Ergebnis. Ein Screening-Erfolg erlaubt eine separat vorab festgelegte frische Bestätigung, noch keinen V14-Austausch. Bei unklarem Vorteil bleibt V14.

## Übergabe

Ergebnisse, auch negative und unvollständige, in `experiments/analysis/threat_warmstart_20261109/` und den gemeinsamen Arbeitsstand aufnehmen. Sinnvolle Implementierungs- und Ergebniscommits getrennt. Remote vor Push prüfen; fremde Änderungen und ungesicherte Dateien erhalten. Quellensperre nur am sicheren Phasenübergang lösen.
