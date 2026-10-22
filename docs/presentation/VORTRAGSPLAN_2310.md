# Sherlock: Vortragsplan für die Präsentation am 23.10.2026

Ursprünglich als Entwurf für den 06.11. geschrieben (Claude Code, Stand 22.10.2026, 09:30). Laut Mahmoud
(22.10., nachmittags) ist die Präsentation am 23.10.; Folien und Stichpunkte tragen deshalb dieses Datum.
Maßgeblich sind die fertigen Folien und die Stichpunkte (Abschnitt unten). Die Abschnitte „Kernaussage“,
„Folien, Zeiten, Aufteilung“ und „Inhalte je Folie“ sind die ursprüngliche Planung mit Belegen.

## Stand 22.10., nachmittags: Folien fertig

- Folien: `Sherlock_Review_23-10-2026.pdf` im Projektordner (13 Vortragsfolien + 2 Reserve, Design vom
  16.10.), Quelle `docs/presentation/Sherlock_Review_23-10-2026.html`, Bilder `docs/presentation/folie_2310_*.png`.
  Kartenbilder mit `scripts/render_snapshots.py` erzeugt (Kopfzeile abgeschnitten), Diagramm mit
  `docs/presentation/source/fortschritt_2310.py` aus den Werten der Übernahmeberichte.
- Stichpunkte zum Üben mit Aufteilung und Zeiten: `Sherlock_Stichpunkte_23-10-2026.md` im Projektordner
  (Moayed 5:10, Mahmoud 4:30, zusammen 9:40). Diese Datei ersetzt die Folienliste unten.
- **Kernaussage korrigiert:** Der Sprung 47 → 78 % kam auch aus Training (Neutraining mit aktiven Regeln
  und `reward_fix`, 18 statt 6 Netze) und Regel-Schaltern (Arbeitsstand 19./20.10.). Erst ab V3 brachte
  Training nichts mehr, 78 → 90 % kam aus der Fehlersuche. Neue Kernaussage: „Von 47 % auf 90 % gegen
  Solution_92: Regeln und Training brachten uns auf 78 %, die Fehlersuche gegen den wahren Spielzustand auf 90 %.“

## Rahmen laut Kursfolien

- Folie 10: Battle-Session – zwei Teams stellen je **10 Minuten** vor, danach spielen die Agenten
  drei Spiele à drei Matches gegeneinander (Replay in doppelter Geschwindigkeit).
- Folie 9 (Inhalte): Algorithmus/Pseudocode, Netzarchitektur, RL-Verfahren, Trainingskonfiguration,
  Feature Engineering, Trainingsablauf (Spielzahl, Gegner), ausgewählte Spiele, Beobachtungen/
  Hypothesen/Erkenntnisse, nächste Schritte.
- Folie 11 (Bewertung): klare Kernaussage, logische Reihenfolge, verständliche Erklärungen,
  freies Sprechen, Folien, Originalität.
- Folie 51: Abgabe `agent.zip` (erst 27.11.), Agent muss für das Battle schon laufen.

## Kernaussage (Vorschlag)

**„Von 47 % auf 90 % gegen Solution_92 – nicht durch mehr Training, sondern weil wir jede
Niederlage mit dem wahren Spielzustand verglichen und die Fehler unseres Agenten behoben haben.“**

Roter Faden: Prof-Fragen vom 16.10. → Training und CNN/PPO (seine Empfehlung) ehrlich bewertet →
die Wende: Verlustspiele gegen die Wahrheit prüfen → drei Fehlerklassen → Ergebnis auf frischen
Karten → was nicht half → Plan bis 27.11.

## Folien, Zeiten, Aufteilung (10:00)

| Folie | Thema | Person | Dauer |
|---|---|---|---|
| 1 | Titel + Kernaussage | Moayed | 0:20 |
| 2 | Rückblick 16.10. und Prof-Fragen | Moayed | 0:50 |
| 3 | Sherlock auf einen Blick: Netze + Gedächtnis + Regeln | Moayed | 1:00 |
| 4 | Training und CNN + PPO: was es gebracht hat | Mahmoud | 1:30 |
| 5 | Die Wende: Niederlagen gegen die Wahrheit prüfen | Mahmoud | 1:00 |
| 6 | Fehler 1: Die Karte im Gedächtnis war veraltet | Mahmoud | 1:10 |
| 7 | Fehler 2: Wege und Ziele | Moayed | 1:00 |
| 8 | Fehler 3: Energie und Kollisionen | Moayed | 1:00 |
| 9 | Ergebnis auf frischen Karten | Moayed | 0:50 |
| 10 | Was nicht geholfen hat + nächste Schritte | Mahmoud | 0:50 |
| 11 | Fazit | Moayed | 0:20 |

Moayed 5:20, Mahmoud 4:30 (zusammen 9:50). Reserve (ausgeblendet): Statistik/Bootstrap und
Gates, Engine-Regeln (Sap, Kollision, Void, Drift), Merkmalsliste, Trainingsparameter.

## Inhalte je Folie (mit Belegen)

**2 Rückblick.** 16.10.: Abgabe `old3_sym3`, 28/60 gegen Solution_92 (46,7 %). Fragen: (1) „Wie 47 %
nach 18.000 Spielen?“ (2) „Belohnung jeden Schritt?“ Empfehlung: PPO + CNN.

**3 Auf einen Blick.** 18 DQN-Netze (Ensemble), Belief/Gedächtnis mit Spiegelsymmetrie,
Zielzuweisung, Aktionsmaske, Regeln für Sap und Wege. Pseudocode aus `agents/sherlock/main.py` (Kopf).
Netz vs. Regel: gleiche Leitplanken ohne Netz 3 % statt 38 % gegen Solution_92 → das Netz trägt.

**4 Training/CNN/PPO.** 66.000 Trainingsspiele für die 18 Netze. CNN-Policy (16 Kartenebenen, Conv +
ResBlocks) mit Nachahmung des Ensembles, dann PPO: erreicht den Lehrer (73,0 % vs 73,25 %), langer
PPO-Lauf `cnn3b` (150 Iterationen) bester Stand 72,0 % gegen V3 76,7 % → kein Gewinn. Gefahr-Merkmale
(22 neue Eingänge, 6 Netze) 72,8 % vs Kontrolle 73,3 % → kein Gewinn. Weitere Netze mit neuen Regeln:
gemischt nicht besser. Quellen: `docs/superpowers/plans/2026-10-21-threat-features.md`, Arbeitsstand
22.10. Ehrliche Botschaft: mehr Training war nicht der Engpass.

**5 Die Wende.** Werkzeuge: `scripts/mechanism_probe.py` (Energiebilanz je Match aus dem wahren
Zustand), Todesursachen, Gedächtnis gegen Wahrheit, Einzelbilder (`scripts/render_snapshots.py`).
Entwicklungs-Sets aus 2.000 neuen Karten (schwer/leicht nach V3-Ergebnis), Kennzahl sagte die frischen
Ergebnisse auf ±1 pp voraus.

**6 Fehler 1: Karte.** Asteroiden und Nebel driften; Nebel ist bei kleiner Sicht unsichtbar → das
Gedächtnis hielt weggedriftete Asteroiden fest (18 % der bekannten Tiles falsch). Bild: 360014, Units
mit 0 Energie am Spawn eingesperrt. Lösung: Nebel-Inferenz, Drift erkennen (210/210 Drifts), falsche
Tiles 78,6 → 13,5 pro Step. Quelle: `docs/NACHT_V7_V8_20261022.md`.

**7 Fehler 2: Wege und Ziele.** Netz läuft nach Luftlinie in Sackgassen und pendelt (Bild 360581);
Zielzuweisung schickt Units zu Punkte-Tiles unter Asteroiden (360051). Lösung: kürzester Weg (BFS) bei
Sackgassen, Zuweisung nach Weglänge.

**8 Fehler 3: Energie und Kollisionen.** Drei Halter schießen gleichzeitig auf einen Gegner mit 21
Energie (Bild 360019); unsere Halter haben danach zu wenig Energie und sterben bei Kollisionen (41
gegen 102 Energie). Lösung: kein Schuss auf sicher tote Ziele, keine Züge in Kollisionen mit stärkeren
Gegnern; Halter schießen nur noch auf stehende Gegner (`sap_still`).

**9 Ergebnis (frische Karten, beide Seiten, gepaarter Karten-Bootstrap).**
16.10. `old3_sym3` 46,7 % → V3 (20.10.) 78,25 % → V7 (22.10. früh) 83,5 % (+7,0 [+4,0; +10,0] gegen
V3, direkt 68 %) → **V10 (Abgabe seit 22.10., 09:21) 90,3 %** auf 800 frischen Karten (+7,5 [+5,4; +9,6]
gegen V7), gegen default 99,75 %, direkt gegen V7 58 %. Balkendiagramm. Quellen:
`experiments/analysis/release_20261022_v7/RELEASE.md`, `experiments/analysis/release_20261022_v10/RELEASE.md`.

**10 Nicht geholfen + nächste Schritte.** Ohne Gewinn: Gefahr-Merkmale, PPO-Fortsetzung, Training auf
schweren Karten (−6 pp), Späher (−4 pp), viele kleine Regeln (±0,5). Methode: jede Idee vorab festgelegt
und auf neuen Karten geprüft. Nächste Schritte bis 27.11.: Robustheit gegen andere Gegner (nicht nur
Solution_92), Turnier-Tests, `agent.zip`.

## Bilder

- Fehler 1 (Folie 7): `folie_2310_karte_vorher.png` (V6 `Bs`, Karte 360014, Match 3: Units mit 0 Energie
  am Spawn, Schritt 90 112:717) und `folie_2310_karte_nachher.png` (V10: 541:488).
- Fehler 2 (Folie 8): `folie_2310_weg_vorher.png` und `folie_2310_weg_nachher.png` (Karte 360581).
- Fehler 3 (Folie 9): `folie_2310_energie_vorher.png` (Karte 360019, drei Saps auf einen Gegner mit 21 Energie).
- Ergebnis (Folie 10): `folie_2310_fortschritt.png` (Balken 46,7 → 78,25 → 83,5 → 90,3 %).
- Vierteilige Vorversionen (`bild_0611_*.png`) liegen nur lokal bei Mahmoud und sind nicht übertragen.

## Offen

1. Moayed: Aufteilung und eigene Folien vor dem Vortrag prüfen und einmal mit Uhr proben.
2. Termin: In `CLAUDE.md` steht für die Zwischenpräsentation der 06.11., laut Mahmoud ist sie am 23.10.
   Im Team bestätigen.
3. Erledigt: V10 ist seit 22.10., 09:21 die Abgabe. Bilder gewählt: 360014, 360581, 360019.
4. Keine PowerPoint-Fassung. Präsentiert wird das PDF; die Sprechernotizen stehen in den Stichpunkten.
