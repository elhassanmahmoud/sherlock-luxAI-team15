# Ergebnis der frischen Bestätigung „reiner Schüler v9“ (17.11.2026)

**Kurz: Bestanden, alle fünf vorab festgelegten Bedingungen sind erfüllt.** Das Kurspaket des reinen Schülers v9
(SHA-256 `1579eb83…253f`) gewann auf 400 frischen Karten 789/800 Spiele gegen Solution (R3 787/800), **28/800 gegen
Kaggle** (R3 16/800) und **236 statt 90 von 2.400 Matches gegen Kaggle**. Gepaart gegen R3: Punkteanteil gegen Kaggle
**+4,02 [+3,10; +4,92]** Prozentpunkte, gewonnene Spiele gegen beide Gegner zusammen +0,88 [−0,31; +2,06]. Auch die
strengere Spielbedingung der ersten Bestätigung (Mittel mindestens 0, untere Grenze nicht unter −1,0) wäre erfüllt.
**Nach der Regel empfehlen wir Mahmoud und Moayed, R3 durch dieses Paket zu ersetzen.** Bis beide ausdrücklich
zustimmen, bleibt R3 die Abgabe. Vorher fehlt noch das Nachspielen unter Python 3.10.

## Was gelaufen ist

Vorab festgelegt im [Plan](BESTAETIGUNG_PLAN.md) (Regel Commit `d27683d` um 11:20, vor dem Ende von Dev E; Kandidat
Commit `2ed6068`, vor dem ersten Spiel). Karten 7260000–7260399, beide Seiten, bisher von niemandem benutzt.
Eingefrorene Quelle `ab34c54`, 10 Prozesse, von 12:36 bis 13:12 ([Skript](run_bestaetigung.sh),
[Protokoll](run_bestaetigung.log)). Gespielt wurden das unveränderte R3-Paket (`8aabdc73…a64d`) und das echte
Kurspaket des Kandidaten, beide als `r3zip:` geladen. Alle 3.400 Spiele liefen über 303 Schritte ohne abgefangenen
Fehler. Vorher bestand das Paket die Ladeprüfung des Kursrunners auf beiden Seiten und spielte auf 16 Dev-E-Spielen
genau wie die gemessene Variante.

## Ergebnisse

| | R3 | reiner Schüler v9 |
|---|---:|---:|
| gewonnene Spiele gegen Solution | 787/800 | **789/800** |
| gewonnene Spiele gegen Kaggle | 16/800 | **28/800** |
| gewonnene Matches gegen Kaggle | 90/2.400 | **236/2.400** |
| gewonnene Matches gegen Solution | 2.292/2.400 | **2.322/2.400** |
| Punkteanteil gegen Kaggle | 33,5 % | **38,5 %** |
| Punkteanteil gegen Solution | 67,9 % | **69,7 %** |
| direkt gegen R3 (7260000–7260099, nur Information) | – | 192/200 Spiele, 558/600 Matches |

**Regel** (gepaart nach Karte, 10.000 Ziehungen, Seed 2711, [Auswertung](analyze_bestaetigung.py)):

| Bedingung | verlangt | gemessen | erfüllt |
|---|---|---|---|
| 1. Punkteanteil gegen Kaggle | Mittel ≥ +2,0, untere Grenze > 0 | +4,02 [+3,10; +4,92] | ja |
| 2. Spiele gegen Solution und Kaggle zusammen | Mittel ≥ −0,5, untere Grenze ≥ −1,5 | +0,88 [−0,31; +2,06] | ja |
| 3. Spiele gegen Solution | Mittel ≥ −0,5 | +0,25 [−1,00; +1,62] | ja |
| 4. Matches je Spiel gegen Kaggle | Mittel > 0 | +0,182 [+0,128; +0,237] | ja |
| 5. Technik | keine Fehler, 303 Schritte | 3.400 Spiele fehlerfrei | ja |

Zusätzlich (nicht Teil der Regel): Spiele gegen Kaggle +1,50 [−0,50; +3,50] Prozentpunkte, Punkteanteil gegen
Solution +1,06 [+0,27; +1,84], Matches je Spiel gegen Solution +0,037 [+0,001; +0,075].

## Einordnung

- Der Kandidat ist **gegen Solution mindestens so gut wie R3** und **gegen Kaggle klar besser**: 2,6-mal so viele
  gewonnene Matches, fast doppelt so viele gewonnene Spiele, 5 Prozentpunkte mehr Punkteanteil. Das passt zu Dev E
  (+4,97 Punkteanteil, 22/400 gegen 2/400 Spiele).
- Die Toleranz in Bedingung 2 war für das Ergebnis nicht nötig: Auch nach der alten, strengeren Regel wäre der
  Kandidat bestanden.
- Der reine Schüler ist ein **vollständig gelerntes Netz** (Ensemble aus zwei Netzen, bis zu 19 Mio. nachgeahmte
  Entscheidungen des Kaggle-Dritten mit sechs DAgger-Runden). Nur zwei Spielschalter sind fest eingestellt
  (weniger Stehenbleiben, höchstens eine stehende Unit je Feld). Der Kaggle-Lehrer selbst ist nicht im Paket.
- Das direkte Duell (192/200) ist kein Beweis für Stärke gegen andere Gegner. Die Robustheit gegen sechs weitere
  Spielweisen wird getrennt geprüft ([Plan](../robust_p9_20261117/PLAN.md)).

## Was vor einem Wechsel noch fehlt

1. Ausdrückliches Ja von **Mahmoud und Moayed**.
2. Nachspielen des Pakets unter **Python 3.10** (`scripts/xversion_replay.py`); bei Mahmoud fehlt Python 3.10, siehe
   [Codex-Auftrag](../../../docs/AUFTRAG_CODEX_20261117.md).
3. Erst dann: Paket als neues Release ablegen und `dist/agent.zip` ersetzen, mit Sicherung von R3 und Rückweg.

## Dateien

- Rohdaten: `bestaetigung_r3.csv`, `bestaetigung_kandidat.csv`, `bestaetigung_direkt.csv` (je Spiel eine Zeile).
- Kurspaket: `experiments/candidates/deve_20261117/agent_p9_reiner_schueler.zip`, SHA-256
  `1579eb8338d1e9a98e52a96e0777633578e99e3d6e81365660f526852655253f`.
