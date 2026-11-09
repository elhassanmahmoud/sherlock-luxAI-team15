# Matchsiege stärker gewichten: fester Lernvergleich

## Frage und Abgrenzung

Ein öffentlich bestätigter produktiver Halterschritt liefert dem heutigen Reward +1, der Matchausgang einmalig +2 oder −2 je vorhandener Einheit. Vier der fünf Niederlagen aus dem aktuellen V14-Vergleich hatten höhere Gesamtpunkte; daraus folgt keine bewiesene Rewardursache. Der [Quellencheck](../../../experiments/analysis/candidate_progress_20261109/operations/match-objective-coverage.md) fand keinen isolierten ausgeführten Vergleich einer höheren `w_match`-Gewichtung. Geschlossene No-Shaping-, Gegnerpunkte-, Terminalpotential-, SAP0-, Fog- und Reserveversuche werden nicht wiederholt.

Dieser Versuch ändert genau `w_match` von 2 auf **20**. Der Faktor zehn soll das seltene Matchsignal deutlicher gegenüber wiederholter Feldbelegung gewichten. Er ist eine vorab feste Hypothese, kein optimierter Wert. Alle dichten Rewards, Match-/Tod-Terminals und Regeln bleiben zwischen den Armen identisch. Kein neuer Spielendbonus, kein Reward-Clipping und kein Punktevorsprung-Potential. Insbesondere endet Replay an jeder Matchgrenze; ein erst am Spielende gegebener Bonus würde frühere Matches nicht automatisch erreichen.

## Vier feste Lernarme

- Zwei Starts 48 und 49, jeweils Kontrolle (`w_match=2`) und Matcharm (`w_match=20`). Kein Gewinnerstart wird ausgewählt.
- Jeder Arm beginnt aus dem exakt gleichen ursprünglichen V14-Mitglied 18 (nullbasiert), mit 79 Eingaben, sechs Aktionen und ursprünglicher Architektur. Keine Ensemblemitglieder im Lerner; alle ursprünglichen Tensoren unverändert kopieren. Frischer Adam, `target_q=q`, leerer Replay, `env_steps=60000`, `learn_steps=0`, Lernrate 0,00005. Herkunft des historischen Trainingsrewards dieses Mitglieds nicht aus dem Inferenzconfig ableiten.
- Normalisiertes V14-Config, gemeinsam `frozen=False`, `rules_in_training=True`, `rules_in_training_all=True`, `rescue_in_training=True`. `cand_stall_rescue=False`, `fog_unknown_reward_neutral=False`, `art_splash_in_training=False`, keine Gefahrmerkmale oder anderen neuen Versuchsregeln. Alle übrigen Werte gleich. Epsilon ist der vorhandene Endwert 0,05.
- Je Arm genau **40 Vorlaufspiele ohne Gradienten und danach 400 Lernspiele**. Zusammen 160 Vorlauf- und 1.600 Lernspiele. Je Paar gleiche feste Gegnerfolge aus Seed 48 beziehungsweise 49: Solution 0,6, Square-Solution 0,2, default 0,1, rush 0,1. Seiten alternieren. Nach Gradientenbeginn dürfen Trajektorien auseinanderlaufen; keine künstliche Replaygleichheit verlangen.
- Karten Start 48: Lernen 9960000–9960199, Vorlauf 9960300–9960319, jeweils beide Seiten. Start 49: Lernen 9961000–9961199, Vorlauf 9961300–9961319, jeweils beide Seiten. Vor Aufnahme einmaliger begrenzter lokaler Konfliktcheck mit dokumentierten Grenzen.
- Nur vollständiger Endstand, keine Zwischencheckpointwahl oder zusätzliche interne Validierungsspiele. Bei Unterbrechung Zwischenstand eindeutig als unvollständig sichern, kein automatischer Neustart/Weiterlauf. Keine Schreibzugriffe auf Abgabegewichte oder ZIP.

## Mechanismus vor Gradienten prüfen

1. Vorhandene Trainer-/Supervisorhilfen möglichst eng wiederverwenden. Keine allgemeine neue Trainingsplattform. Gezielte synthetische Tests und unabhängiger Review vor echten Modellen; bestehende Rewardfunktion unverändert verwenden.
2. Genau vier bekannte Technikspiele: beide Rollen mit Start 48 auf 9946007/player_0 und 831006/player_1, Trainingsaktionspfad, Lernen abgeschaltet. Initiale Gewichte, Aktionen, Beobachtungen und Nicht-Reward-Replayfelder müssen paarweise identisch bleiben. Der analytische Rewardkontrast je eingelegtem Übergang ist `18 × (Δeigene Matchsiege − Δgegnerische Matchsiege)`; ohne Matchausgang null. Beide unveränderten Originalformeln auf demselben Livekontext unabhängig nachrechnen: am Replay-Push muss der verwendete Originalwert exakt stimmen, im Replay seine exakte Float32-Darstellung. Beim Subtrahieren gespeicherter Werte nur den aus diesen konkreten Quantisierungsfehlern und der Float64-Arithmetik begründeten Rundungsrest zulassen, keine unmögliche bitgenaue 18-Differenz fordern. Reale Exposition des Matchterms nachweisen, keine Ersatzspiele. Die technischen Resultate dienen keinem Stärkevergleich.
3. Erst nach tatsächlicher Technikabnahme Paar 48 getrennt aufnehmen. Vorlaufbarriere: beide Originalworker warten ohne Gradienten, Root prüft tatsächliche Replays und Rewardkontrast, dann explizite Freigabe. Nach vollständiger Prüfung von Paar 48 Paar 49 separat aufnehmen und dieselbe Barriere prüfen. Keine automatische Phasenverkettung oder Wiederholung.
4. Am Ende tatsächliche vollständige Spielzahlen, Gradienten-/Adamupdates, endliche Gewichte/Losswerte, geänderte Lerngewichte, unveränderte Inferenz-V14-Dateien sowie Quellen-/Eingabeidentität prüfen. Replay und Rewardkontrast so speichern, dass sie unabhängig nachrechenbar sind. Große Roharchive verlustfrei komprimieren; keine unnötigen doppelten Binärarchive veröffentlichen.

Numerische Vorabgrenze: Float64-Formelkontrast mit `abs_tol=1e-10`, `rel_tol=1e-12`; Replaywerte jeweils exakt gegen die Float32-Konvertierung der Originalformel. Der Kontrast gespeicherter Werte darf zusätzlich nur deren konkret nachgerechnete Quantisierungsabweichung enthalten. Toleranzen nicht anhand realer Ergebnisse lockern.

## Vorab festgelegter anschließender Vergleich

Nach vollständiger Trainingsabnahme separate Aufnahme und Werkzeuge, keine automatische Auswertung. Exakt eine Kontroll- und eine Matchgewicht-Ensemblevariante: ursprüngliche 36 V14-Mitglieder in derselben Reihenfolge plus beide jeweiligen Endnetze (Starts 48 und 49), insgesamt **38**. Keine Auswahl, Mischung, Temperaturanpassung, Rangmittel oder nachträgliche Umgewichtung. Inferenzconfig des ursprünglichen V14, neue Frührettung aus, nur `frozen=False` für kontrollierte Messungen. Der Trainingsreward ist im Evalmodus kein Aktionsschalter.

Die unterschiedlichen Trainingsziele können auch die Größenordnung der Q-Werte verändern. Gleiche Architektur garantiert keine kalibrierten Werteskalen. Das unveränderte arithmetische Mittel der 38 Netze ist deshalb eine zu prüfende Heuristik, keine theoretisch zugesicherte Verbesserung; Modellzahlkontrolle und reale Vergleiche sind notwendig.

- V14, CONTROL38 und MATCH38 jeweils gegen Solution auf 9970000–9970019, beide Seiten: 120 Spiele.
- MATCH38 direkt gegen V14 auf 9970100–9970119 und gegen CONTROL38 auf 9970200–9970219, beide Seiten: 80 Spiele.
- Insgesamt **200 Leistungsspiele**. Tatsächliche MATCH38-Siege gegen Solution mindestens so viele wie beide Referenzen; direkt mindestens 24 tatsächliche Siege je 40 gegen beide Referenzen. Unentschieden sind keine Siege. Ganze Karten mit beiden Seiten gemeinsam resampeln, 5.000 PCG64-Seed-0-Ziehungen, deskriptive 95%-Scoreintervalle; keine Korrektur für die vielen Projektversuche.
- Fehlschlag schließt diese feste Variante ohne Schwellen-/Rewardnachjustierung oder Nachschlag. Bestehen erlaubt nur eine separat festgelegte frische Bestätigung, keinen sofortigen V14-Ersatz. Übernahme erst nach belegtem Vorteil, Sicherung, Reproduktion und Kursprüfung.

## Betrieb und Übergabe

Profil `match_weight_20261109`. Maximal zwei Modellworker, keine parallelen Tests, feste Quelle/HEAD und Eingaben während jeder aufgenommenen Phase. Akkubetrieb vom Nutzer ausdrücklich erlaubt. Vor neuen Modellläufen echtes frisches Kontingent prüfen; Restnutzung erlaubt, Resets ausschließlich durch Nutzer. Bei tatsächlichen 100 Prozent sicher abschließen und Automation pausieren.

Codex koordiniert getrennte Schreibbereiche, prüft echte Ergebnisse, dokumentiert für Mahmoud und committet/pusht sinnvolle abgeschlossene Einheiten. Hauptkopie am sicheren Übergang aktualisieren, Mahmouds neue Commits beachten, fremde Dateien erhalten. Kandidatenrettung und alle älteren abgeschlossenen Studien bleiben geschlossen. V14/ZIP bis zur qualifizierten Übernahme unverändert.
