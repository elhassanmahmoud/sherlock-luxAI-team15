# Erster V4-Koordinationsprototyp: kein qualifizierter Vorteil

21.10.2026. Kandidat `v4_joint_pairs_v1_20261021`, Quellenstand
`e84b9928f20d24fcfe18d1ccf1d1db5a59cf78f5`. Alle 18 gelernten V3-Netze
unverändert; nur der experimentelle Schalter `joint_moves=True` aktiviert
eine begrenzte gemeinsame Bewegungswahl für nahe Schiffspaare.
[Vorab festgelegter Plan](../../../docs/superpowers/plans/2026-10-21-v4-joint-prototype.md).

## Vollständiger Entwicklungsvergleich

60 bereits bekannte Karten 500720–500779, immer beide Seiten. Remis zählen
beim Gegnervergleich nicht als Sieg; es gab keine Remis.

| Vergleich | Kandidat | V3 | Differenz / gepaartes 95%-Kartenintervall |
|---|---:|---:|---|
| Gegen Solution_92 | 101/120 (84,17 %) | 102/120 (85 %) | −0,83 pp [−2,5; 0] |
| Gegen Default | 120/120 | 120/120 | 0 pp [0; 0] |
| Direkt gegen V3 | 62 Siege, 58 Niederlagen | — | mittleres Resultat 51,67 %, Intervall [50; 54,17] % |

Das vorab geforderte Solution-Entwicklungsgate von mindestens 108/120 Siegen
ist verfehlt. **Keine frische Bestätigung, keine Gewichtsübernahme.** Der
kleine direkte Vorsprung ist kein belastbarer allgemeiner Stärkegewinn.
Dieser Versuch bewertet genau die festgelegte Paarvariante, nicht jede
mögliche Form gemeinsamer Planung.

Auswertung: ganze Kartenpaare, 5.000 Bootstrap-Ziehungen mit NumPy
`default_rng(0)`, 2,5-/97,5-Perzentile. Bekannte Entwicklungskarten und feste
Agenten; kein Intervall über neue Trainingsstarts und keine Korrektur für
historische Modellauswahl. Das Nullintervall bei 120/120 bedeutet nicht,
dass die wahre allgemeine Siegquote sicher 100 % wäre.

## Tatsächlicher Umfang und technische Prüfung

- 240 neue Spiele gegen Solution/Default und 120 neue direkte V3-Spiele.
- 16 zusätzliche Kontrollspiele mit abgeschaltetem Schalter reproduzieren
  368 Nichtzeitfelder der vorhandenen V3-Referenz ohne Abweichung.
- Acht Spiele über den unveränderten Kurs-Runner bestanden; maximale
  Aktionsdauer 5,239 ms, höchstes spielweises 95%-Perzentil 2,343 ms.
- Acht gesonderte Aktivierungsbeobachtungen auf 500720–500723, beide Seiten
  gegen Solution: 2.400 Aufrufe, null geänderte Einheitenentscheidungen.
  Das beschreibt diese acht Spiele, nicht alle 360 Vergleichsspiele.
- Insgesamt **392 neu gespielte vollständige Spiele**, kein Training.
  240 passende historische V3-Referenzspiele wurden kontrolliert wiederverwendet.
- 48 fokussierte Tests, insgesamt 457 Tests und 14 Untertests bestanden;
  unabhängiger Implementierungsreview ohne blockierende Befunde.
- Hashkontrolle aller eingefrorenen Quellen und beider aktuellen
  Abgabe-Dateien sowie der alten Sicherung vor und nach jedem Job.

Aktuelle V3-Dateien bleiben SHA-256
`aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`.
Experimenteller Kandidat:
`8301c9fdae44a511c91d21946f4ac66536260e6836358fbc300726b801ae8acc`.
Die alte Sechser-Sicherung bleibt unverändert.

## Nachvollziehbarkeit

- `results.json` und `analyze.py`: vollständige Schlüssel-/Hashprüfung,
  Siegzahlen, Kartenintervalle und feste Gateentscheidung.
- `state.json`: Befehle, Eingabehashes, Prozesszuordnung, Zeitpunkte und
  Rückgabecodes. Absolute Pfade dokumentieren den damaligen Mac-Aufbau.
- `development_opponents.csv`, `development_direct.csv`: neue Rohspiele.
- V3-Referenz: `../enemy_tie_energy_20261021/development_v3.csv`;
  `reference_source_comparison.json` erklärt die deaktivierten Codeunterschiede,
  `baseline_reproduction.json` die tatsächlich wiederholte Teilmenge.
- `candidate_identity.json`, `course_runner.json`, `activation_probe.json`
  sowie Implementierungs-/Reviewberichte dokumentieren die technische Prüfung.

## Passive Folgeprüfung: Vorschläge sind stark eingeschränkt

Vier zusätzliche Spiele auf 500724–500725, beide Seiten gegen Solution,
bringen den gesamten neuen Umfang auf **396 Spiele**. Alle Nichtzeitfelder
reproduzieren die entsprechenden vier Entwicklungszeilen; der Beobachter
verändert keine Aktionen. `funnel_probe.json`/`.py.txt` dokumentieren die
genaue Diagnose. `results.json` nennt weiterhin die 392 Spiele der zuvor
abgeschlossenen Vergleichs-/Technikphase.

Von 1.200 Koordinationsaufrufen wurden 120 gleichmäßig abgetastet; 34 hatten
noch keine bekannten Punktefelder. In sieben Stichproben hätte irgendeine
legale Paarbewegung die nominale Belegung erhöht. Nach Beschränkung auf
die zwei höchstbewerteten Bewegungen blieben zwei, nach der zusätzlichen
15%-Q-Regret-Grenze null. Spätere Gegner-/Überlappungsfilter konnten daran
nichts mehr ändern. Insgesamt griff die echte Koordination einmal ein,
außerhalb der Stichproben. Keine Abweichung zwischen letzter Diagnosestufe
und tatsächlicher Helper-Entscheidung festgestellt.

Dies erklärt die geringe Aktivierung in dieser kleinen Stichprobe; es
beweist weder die Ursache sämtlicher Niederlagen noch, dass weniger strenge
Filter besser wären. Der festgelegte Kandidat bleibt beendet. Als separater
Machbarkeitsschritt wird geprüft, ob eine gelernte strategische Zielwahl
die tatsächlichen V3-Aktionen überhaupt beeinflussen könnte.
