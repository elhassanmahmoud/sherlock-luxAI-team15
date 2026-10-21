# Sherlock: Abschlussbericht für den 22. Oktober 2026

**Ergebnis: Der V4-Koordinationsprototyp ist gebaut und getestet. Ein nachweislich stärkerer V4 wurde in diesem Versuchsprogramm nicht erreicht. V3 bleibt unverändert die Abgabe.** Der Abschluss erfolgt bereits am Abend des 21. Oktober, weil die vorab begrenzten Versuche entschieden sind. Das ist ein Abschluss dieser Versuche, keine Erfüllung des weiterhin offenen Ziels einer deutlich höheren Siegquote.

## Was tatsächlich getestet wurde

| Versuch | Neue Spiele | Ergebnis gegen Solution_92 | Entscheidung |
|---|---:|---|---|
| Gemeinsame Bewegungswahl für Schiffspaare | 396 | Kandidat 101/120, V3 102/120; direkt 62/120 gegen V3 | Entwicklungsgate verfehlt |
| Einfluss alternativer Ziele | 8 | 32 festgelegte Situationen, keine geeignete Alternative; Kontrollverläufe identisch | Machbarkeit nicht nachgewiesen, kein Zielbewerter trainiert |
| Begrenzte CNN3-Fortsetzung ab Original-PPO60 | 724, davon 240 Training | Endstand 89/120, Original-PPO60 96/120, V3 102/120 | Entwicklungsgate verfehlt |
| Unabhängige Prüfung von Mahmouds Artillerie-Regel | 2.208 | Entwicklung 108/120 statt 102/120; frisch **301/400 statt 292/400** | Frische Übernahmekriterien verfehlt |
| **Summe dieses V4-Programms** | **3.336** | **240 Trainingsspiele und 3.096 Auswertungs-/Kontroll-/Kursprüfspiele** | kein Gewichtswechsel |

Die Summe zählt keine historischen Referenzen, keine Softwaretests und keine früheren Nachtversuche nochmals. Beim Koordinator enthalten die 396 Spiele auch Kontroll-, Kurs- und Aktivierungsprüfungen. Die 724 CNN-Spiele bestehen aus 240 Training, 240 Originalreferenz, vier V3-Kontrollen und 240 Endstand-Auswertungen. Artillerie: 480 Reproduktion, 120 direkter Entwicklungsvergleich, acht Kursprüfungen und 1.600 frische Gegnervergleiche.

## Was die Ergebnisse bedeuten

Der Paar-Koordinator zeigt gegen Solution **−0,83 Prozentpunkte**, gepaartes 95%-Kartenintervall **[−2,5; 0]**. Direkt gegen V3 beträgt das mittlere Resultat 51,67 %, Intervall [50; 54,17] %. In einer passiven Stichprobe gibt es zunächst sieben Möglichkeiten für bessere Punktefeldbelegung; nach den festen Alternativen- und Abweichungsgrenzen bleibt keine übrig. Das begründet die Ablehnung dieses konkreten Kandidaten, keine allgemeine Aussage gegen Koordination.

Der Zielpilot findet in seiner festgelegten Auswahl keine zulässige Alternative. Damit wurde nicht geprüft, wie gut eine tatsächlich verfügbare Alternative wäre. Die Auswahl nachträglich zu erweitern hätte den registrierten Versuch verändert; es wurde kein nutzloser Lernkopf auf leeren Vergleichsdaten trainiert.

Das CNN-Training lief **38:50 Minuten**, zehn Iterationen mit insgesamt 240 Spielen auf 120 unterschiedlichen Trainingskarten aus Teilblöcken 550024–550251. Gegner: 211-mal Solution, 29-mal default. Der finale Kandidat liegt gegenüber V3 um **10,83 Prozentpunkte zurück**, Intervall [−20; −2,5]. Default gewinnen alle drei verglichenen Stände 120/120. Der frische Optimizer und die kleinere Minibatch verhindern eine isolierte Aussage über den Gegner-Mix; das Ergebnis widerlegt PPO nicht grundsätzlich. Es wurden keine günstigen Zwischenstände nachträglich ausgewählt.

Am vielversprechendsten sah Mahmouds Artillerie-Schalter auf den bekannten 60 Entwicklungskarten 500720–500779 aus: **108/120 gegen Solution und 80/120 direkt gegen V3**. Die anschließende feste Prüfung auf **200 neuen Karten 523000–523199**, beide Seiten, ergab aber nur **+2,25 Prozentpunkte**, Intervall **[−0,25; +4,75]**. Ein kleiner Nutzen ist möglich, der geforderte Nachweis von mindestens +5 Prozentpunkten und einer strikt positiven unteren Grenze fehlt. Gegen default gewinnen Kandidat und V3 jeweils 399/400. Deshalb kein weiterer Direktvergleich auf frischen Karten, kein Auffüllen und keine Übernahme.

Die Intervalle ziehen ganze Kartenpaare einschließlich beider Seiten, 5.000 Bootstrap-Stichproben, Seed 0. Unterschiedliche Kartenblöcke werden nicht zusammengelegt. Eine höhere Zahl auf bekannten Karten ist kein Beleg für bessere Leistung auf neuen Karten.

## Was technisch verbessert und veröffentlicht wurde

- PPO-Spielabläufe und Trainingsinitialisierung binden den Torch-Zufall jetzt an die vorgesehenen Seeds. Das verbessert die Reproduzierbarkeit, behauptet aber keinen Stärkegewinn.
- Der Ensemble-Builder bewahrt die Eingabedimension jedes Netzes. Fehlerhafte Dimensionslisten werden früh abgewiesen; zusätzliche Netze können nicht mehr still beim Laden entfallen. Das ist auch für Mahmouds gemischte 79-/101-Merkmal-Ensembles wichtig.
- Der geprüfte gemeinsame Stand bestand im V4-Arbeitszweig **531 Tests plus 14 Untertests** in 82,52 Sekunden. Zusätzlich bestanden elf synthetische Prüfungen des Artillerie-Protokolls. Dies sind Softwaretests, keine zusätzlichen Spiele.
- Alle sechs Artillerie-Jobs wurden unabhängig anhand der Rohdaten geprüft. Root rechnete die Ergebnisse separat nach. Die acht Kursprüfspiele laden alle 18 Netze exakt und starten mit frischem Belief; größte p95-Aktionszeit 2,326 ms, absolutes Maximum 10,946 ms. Der Kurscheck prüft insbesondere Aktionsformat und Ladeverhalten, keine vollständige Garantie aller semantischen Spielregeln.

Der erfolglose Koordinationscode bleibt auf `improvement/v4-joint-20261021`. In `main` liegen die gemeinsam nutzbaren Werkzeugkorrekturen, geprüften Ergebnisse und die Dokumentation. Die Artillerie-Idee und die laufenden neuen Trainings stammen von Mahmoud. Der große bestätigte Sprung von der alten Abgabe zu V3 ist ebenfalls sein Modellfortschritt; diese Arbeit hat keinen weiteren bestätigten Sprung erzielt.

## Abgabe, Sicherung und Nachweise

- Aktuelle Abgabe: `agents/sherlock/weights/agent_p0.pth` und `agent_p1.pth`, jeweils SHA-256 `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`.
- Alte Sechser-Sicherung: `experiments/releases/20261020_old3_sym3/`, beide Dateien SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.
- Alle acht geschützten Dateien in Haupt- und V4-Arbeitskopie sind unverändert. Es wurde kein neues Abgabepaket freigegeben.
- Artillerie-Kandidat und Rohdaten sind geteilt. Der unterlegene CNN-Endstand bleibt lokal im Experimentverzeichnis, wie im CNN-Bericht angegeben; er ist kein neuer veröffentlichter Abgabekandidat.

Vollständige Daten, Quellenstände, Hashes, Prüfungen und Grenzen:
[Paar-Koordinator](../experiments/analysis/v4_joint_pairs_v1_20261021/README.md),
[Zielpilot](../experiments/analysis/v4_target_pilot_20261021/README.md),
[CNN-Fortsetzung](../experiments/analysis/cnn3_sol90_s20_20261021/README.md),
[Artillerie-Bestätigung](../experiments/analysis/art_sap_confirm_20261021/README.md).

## Nächster sinnvoller Schritt

Mahmouds bereits gestartete DQN-Läufe mit 101 Eingabemerkmalen, davon 22 neue Gefahrmerkmale und sein getrenntes PPO-Training liefern die nächste neue Evidenz. Diese Trainings wurden nicht doppelt auf Moayeds Mac gestartet. Wenn ihre eingefrorenen Ergebnisse vorliegen: Herkunft und Ladeverhalten prüfen, den [bestehenden Auswahl-/Bestätigungsplan](superpowers/plans/2026-10-21-threat-features.md) ausführen und nur den dort festgelegten Kandidaten zu frischen Tests zulassen. Die reservierten Karten 503220–503819 bleiben für diese Studie vorgesehen.

Ein zusätzlicher Read-only-Review historischer Kollisionen fand nur zwei verpasste nominelle Möglichkeiten unter den konservativen Bedingungen, davon eine gegen einen tatsächlich stehenbleibenden Gegner. Keine erfüllt vorher beobachtete Stationarität. Das reicht derzeit nicht als Begründung für einen weiteren Kampfregler. Die [unabhängige Entscheidung zum Abschluss](../experiments/analysis/art_sap_confirm_20261021/next_step_review.md) hält die Grenzen fest.

Die Artillerie-Karten 523000–523199 sind verbraucht. 523200–523399 und der optionale finale 100%-Audit 520000–520999 wurden in diesem Programm nicht gespielt. **100 % gegen Solution wurden nicht erreicht.** Auch ein späterer perfekter Testsatz wäre keine Garantie für alle möglichen Karten.

## Veröffentlichung und Abschlusskontrolle

Wesentliche tatsächlich gepushte Commits in `main`:

| Commit | Inhalt |
|---|---|
| `8d13a38` | geprüfte Ergebnisse des Paar-Koordinators |
| `db7210f` | Zielpilot und negatives Machbarkeitsgate |
| `14469f2` | reproduzierbarer PPO-Zufall |
| `ec6e069` | abgeschlossene CNN-Fortsetzung mit Rohdaten und Review |
| `8f4353a` | Artillerie-Vorabplan |
| `b359bd6` | Korrektur der Ensemble-Dimensionen |
| `2b9c62c` | angepasste Testverträge für die strikte Ladeprüfung |
| `dea348f` | geprüfte Artillerie-Werkzeuge und Experimentkandidat |
| `9888f81` | vollständige negative Artillerie-Bestätigung |

Auf dem Arbeitszweig sind insbesondere Implementierung `b73523f`, Ergebnisarchiv `a1cd85b`, eingefrorene Artillerie-Basis `9c1efc7` und Abschluss `479d2dc` veröffentlicht. Dieser Bericht und die gemeinsame Übergabe folgen im abschließenden Dokumentationscommit. Keine unqualifizierte Koordinationslogik wurde in main aktiviert.

Letzter abgeschlossener Remote-Watch-Abgleich: **21.10.2026 um 21:17:54 Berlin**, erfolgreich. Seit `4cb6e37` waren nur eigene veröffentlichte Änderungen hinzugekommen; keine weiteren Ergebnisse von Mahmoud. Eigener Wächter PID 81327 und eigene Wachhaltung PID 46418 sind nach Prüfung ihres jeweiligen Kommandos beendet. Beide aktiven Sherlock-Automationen sind auf **PAUSED** gesetzt. Es laufen keine eigenen Modelljobs und keine offenen Experimente dieses Programms. Der Morgenauftrag ist mit diesem vorgezogenen Bericht erledigt, er startet um 06:00 keine neue Runde.

Kontingentkontrolle beim Abschluss: **26 % verbraucht, 74 % übrig** im vom Konto gemeldeten Fenster. Die verlangte Reserve von mindestens 30 % bleibt erhalten; kein Reset eingelöst. Dies ist kein budgetbedingter Abbruch, sondern der Abschluss der vollständig ausgewerteten, begrenzten Versuche. Die unabhängigen Reviews sind beendet. Lokale Arbeitskopien und abgelehnte Versuchskandidaten bleiben zur Nachvollziehbarkeit erhalten; fremde unversionierte Dateien wurden nicht angerührt.
