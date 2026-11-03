# Sherlock: Abschluss 02./03.11.2026

**Kein nachweislich stärkerer Nachfolger. V14 bleibt unverändert die Abgabe.**
Die neue Planungsvariante P sah in der Auswahl gut aus, bestätigte ihren Vorteil
auf neuen Karten aber nicht. Das Ziel 100 % gegen Solution wurde nicht erreicht.

## Ergebnisse und Entscheidung

P verwendet dieselben 36 Netze wie V14. Eingeschaltet wurden ausschließlich
`point_pair_swap` und `art_move_guard`: Zieltausch zwischen eigenen Einheiten und
Schutz einer sinnvollen Bewegung vor einer später verworfenen Artillerieaktion.
Die separat nachtrainierten Netze wurden nicht eingesetzt.

| Frische Bestätigung | V14 | P | Unterschied / 95%-Intervall |
| --- | ---: | ---: | --- |
| Sechserpanel, je 3.600 Spiele | 80,14 % | 80,44 % | +0,31 pp [−0,86; +1,47] |
| Solution_92, je 600 Spiele | **578 Siege (96,33 %)** | 572 Siege (95,33 %) | −1,00 pp [−2,33; +0,17] |
| default, je 600 Spiele | 600 Siege | 600 Siege | 0,00 pp |
| P direkt gegen V14, 600 Spiele | — | 309 Siege / 291 Niederlagen | 51,50 % [48,17; 55,17] |

Keine Remis. Fünf von sieben festen Übernahmebedingungen verfehlt. Ein gesicherter
Gesamtvorteil ist nicht belegt; auch eine generelle Verschlechterung lässt sich
aus diesen Intervallen nicht ableiten. Gegen Solution liegt P numerisch zurück.
V14s 96,33 % sind eine neue Messung desselben Agenten auf anderen Karten, keine
Verbesserung gegenüber den historischen 95,4 %.

Die Auswahl auf 100 Karten hatte noch +2,67 pp im Panel und 118/200 direkte Siege
ergeben; gegen Solution beide 184/200. Dieser Vorteil wurde nicht repliziert.
Keine Übernahme, kein Nachrücken und kein zweiter Bestätigungsversuch. Die
bedingte PT2-Route war durch die P-Nomination endgültig ausgeschlossen.

## Tatsächliche Ausführungen

| Teil | Vollständige Spielausführungen | Ergebnis |
| --- | ---: | --- |
| Diagnose, Gauß-Shadow, P-Kompatibilität | 218 | 26 + 168 + 24 technische Spiele; Gauß praktisch zu selten wirksam |
| Erstes Trainingspaar | 1.632 | Je 120 Prefill + 600 Lernspiele + 96 bekannte Validierungen |
| P-Auswahl | 3.000 | 100 neue Karten 841000–841099, beide Seiten; P nominiert |
| P-Bestätigung | 9.000 | 300 Vergleichskarten 842000–842299 und 300 getrennte Direktkarten 843000–843299 |
| Zusätzliche V14-Technikprüfung | 9 | Acht Kurs-Runner-Spiele und ein aufgezeichnetes Spiel |
| **Gesamt** | **13.859** | Einschließlich wiederverwendeter Lern-/Diagnosekarten; keine 13.859 unabhängigen Testkarten |

Das Trainingspaar bestand aus Kontrolle und Anpassungsarm, beide mit V14-Netz 18
als Warmstart und frischem Optimierer/Replaybuffer. Beide änderten ihre Tensoren
und führten je 90.000 Lernupdates aus; Optimierer und Reload wurden unabhängig
geprüft. Die zweite Welle wurde mangels Netzstrom im festen Startfenster nie
begonnen. Der Vierarmpilot blieb unvollständig; seine Teilgewichte wurden nicht
zur Abgabe gemacht. [Endstände und Rohdaten](../experiments/analysis/continuation_20261102/training/first_wave/README.md).

Die ganze P-Studie lief unter Source 03e54e2 mit unverändertem Interpreter, Engine
und Gewichtssatz. Beide Startseiten und alle sechs Panelgegner wurden je Karte
zusammen resampelt: 5.000 Bootstrap-Ziehungen, PCG64 Seed 0. default blieb separat.
Das lokale Panel unterscheidet sich von Mahmouds historischer Liga.
[Daten, Einzelgegner, Gates](../experiments/analysis/continuation_20261102/performance/study_P_only_20261102/README.md).

Der unabhängige Auditor bestand 276 Prüfungen. Ein weiterer Reviewer rechnete
alle 9.000 CSV-Zeilen und Intervalle separat nach und prüfte 237 Belegdateien.
Beide bestätigen die Ablehnung. Ergebnisquoten wurden erst nach vollständigem
Phasenabschluss zur Wahl gelesen.

Der Mac war am 02.11. von 22:22:49 bis 23:35:47 Berlin im Clamshell-Ruhezustand,
mit kurzen Weckphasen. Beim P-Panel liegen dadurch rund 72,6 Minuten zwischen
Kalenderdauer und monotonem Rechentimer. Der unveränderte Lauf wurde fortgesetzt
und endete am 03.11. um 01:36:40 Berlin, vor dem festen Spielschluss 04:30.
Die Rechenzeit war somit unterbrochen. Die Schlafpause erklärt keinen entsprechend
langsameren Algorithmus.

## Unveränderte Abgabe technisch geprüft

Die lokal vorhandene `Gruppe15.zip` bleibt bestehen:

- Python 3.10.22, Torch 2.2.2 und NumPy 1.26.4: acht vollständige Kurs-Runner-Spiele,
  je 303 Schritte, Modelle korrekt geladen.
- Beide Ordnerpositionen funktionieren; `train=True` lässt das eingefrorene Paket
  und seine Gewichte unverändert. Diese API-Prüfungen sind keine weiteren Vollspiele.
- Ein unter Python 3.13 aufgezeichnetes Spiel wurde unter 3.10 nachgespielt:
  **0 abweichende Aktionen**, 303 Schritte und 606 Entscheidungen beider Spieler.
- Alle 36 Netze, Datentypen, Formen, Tensorbytes und sonstigen Checkpointfelder
  entsprechen V14. Im ZIP wird ausschließlich `cfg.frozen=True` ergänzt.
- 18 Einträge: 14 Laufzeitmodule, leere Initialisierung, eine Gewichtsdatei, YAML
  und LIESMICH. Keine internen Repo-Dokumente. Laufzeitquellen entsprechen Git 75af0c5;
  der Entwicklungsstand enthält zusätzliche ausgeschaltete Prototypen.

Der erste 3.10-Versuch scheiterte vor Spielen an einem fehlerhaften SciPy-Mac-Wheel.
Nur SciPy in der isolierten Umgebung wurde auf 1.14.1 ersetzt. Alle 59 anderen
Distributionen, Engine, gemeinsames Python 3.13, Gewichte und ZIP blieben gleich.
Anschließend bestand die tatsächliche Ausführung. Die Prüfung betrifft macOS arm64;
sie ist kein Windows-Test oder neuer Stärke-Benchmark unter 3.10. Aktionsmediane
je Spiel: 13,0–17,7 ms, Maximum 39,2 ms; eine unbekannte harte Kurs-Zeitgrenze wird
nicht zertifiziert. Begrenzte historische Startnachweise sind im Review benannt.
[Technikbelege und Umfang](../experiments/analysis/continuation_20261102/existing_v14_preflight/README.md).

| Geschützter Stand | SHA-256 |
| --- | --- |
| Beide aktiven V14-Dateien und V14-Sicherung | `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8` |
| Bestehende ZIP | `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6` |

Die ältere Sicherung `experiments/releases/20261020_old3_sym3` bleibt erhalten.
Kein Abgabetausch oder Moodle-Upload. Pfade: `Gruppe15.main.Agent_x` und für beide
Spieler `Gruppe15/agent.pth`.

## Git und nächste Schritte

Der Wächter erkannte Mahmouds Commits 56bcc55 und 35a9ebc. Nach Ende des P-Freeze
wurde der primäre Checkout verlustfrei aktualisiert. `zone_rescue` bleibt aus;
Entscheidungsäquivalenz bei ausgeschaltetem Flag ist quellenbasiert belegt, eine
Leistungsmessung des neuen Verhaltens fehlt. Der Server wurde nicht gestartet.
Vor öffentlichem Einsatz sind zwei belegte Ressourcenfehler zu beheben; siehe
[Commitreview](../experiments/analysis/continuation_20261102/performance/study_P_only_20261102/review/MM_commits_20261102_review.md).

Übertragene eigene Arbeit: Diagnose/Prototypen3152fed, Trainings-/P-only-Zulassung
bis03e54e2, [Entscheidungsablauf](ENTSCHEIDUNGSABLAUF_V14_P.md)8b66ddf,
unbenutzte Folgeroute3976b1d/ccdd92e, Auswahl668a157, Releasewerkzeugeef38993 und
Ablehnungsentscheidungdd2cbc2. Dieser Abschluss ergänzt Technikbelege und Bericht.
Gauß-Auswertung92648c1 bleibt auf ihrem Forschungsbranch; kein Merge in main/Abgabe.

1. V14 für die Abgabe behalten. Der spätere Zehn-Minuten-Vortrag sollte Zielzuweisung
   → 79 Merkmale → 36 Netze/6 Q-Werte → Masken → nachgelagerte Regeln zeigen.
   Folien und PDF wurden in dieser Fortsetzung nicht geändert.
2. Mahmouds zonenweise Rettung zunächst auf bereits verbrauchten Verlustspielen
   diagnostizieren: Findet sie neue Punktefelder, oder verschiebt sie nur Einheiten?
   Danach ein eigener vorab festgelegter Versuch auf neuen Karten.
3. Weitere Trainings an eine überprüfbare Ursache knüpfen. Teilgewichte und eine
   positive Auswahl allein rechtfertigen keine Übernahme.

Das begrenzte Programm ist geschlossen. Eigene Jobs und Nachtüberwachung werden
beim Abschluss beendet. Keine Resets eingelöst; die 30%-Reserve wurde eingehalten.
