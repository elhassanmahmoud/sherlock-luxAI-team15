# Gefahr-Merkmale (`threat_feats`) und PPO `cnn3b`: Auswertung vorab festgelegt

21.10.2026, Claude Code mit Mahmoud. Festgelegt, während beide Trainings laufen und bevor
irgendein Ergebnis der neuen Netze bekannt ist. Abnahmeregeln wie in der
[V4-Strategie](../../V4_STRATEGIE_20261021.md), damit alle Kandidaten dasselbe Maß haben.

## Hypothese

V3 verliert Match 3 oft gegen eine Solution_92-„Festung“ (viele Units auf einem
umkämpften Relic-Haufen, Sap auf alles in Manhattan-Reichweite;
[Diagnose](../../../experiments/analysis/mechanism_probe_20261021/README.md)). Feste Regeln
(`art_sap`, `siege`) brachten keinen robusten Gewinn. Die Netze kennen bisher nur den
nächsten Gegner und die Zahl der Gegner im Sap-Quadrat. Mit Gefahr-Merkmalen je Tile
(Manhattan- und Quadrat-Bedrohung durch sapfähige Gegner, Gegnerenergie auf/neben dem
Tile, bester Sap) kann das Netz lernen, wann es eine Festung betritt, wartet oder schießt.

## Läufe (gestartet 21.10. ab 19:28 Berlin, Mahmouds Rechner)

- `20261021_full_rules_v3_threat_s40`–`s45_sol70`: Variante `full_rules_v3_threat` =
  `full_rules_v3` + `threat_feats`, je 3000 Spiele, 70 % Solution_92, Starts 40–45.
  Kontrolle: `v3nets6` = dieselbe Variante ohne Gefahr-Merkmale, Starts 40–45 vom 20.10.
- PPO `cnn3b`: Start `cnn3/ppo_0060`, 150 Iterationen × 80 Spiele, Gegner 80 % Solution_92,
  15 % V3, 5 % default, Seed 5. Checkpoints alle 10 Iterationen.

## Auswahl (Block 503220–503419, 200 Karten, beide Seiten, default + Solution_92)

1. Nach Trainingsende ohne weitere Auswahl einzelner Netze bauen:
   `threat6` (die 6 neuen Netze, gespeicherte Trainings-Config) und `mix24`
   (`threat6` als Hauptnetz + 18 V3-Netze, `build_ensemble --mixed`, Config = V3-Schalter
   + `threat_feats`). Je 800 Spiele, dazu V3 und `v3nets6` auf denselben Karten.
2. Methodenfrage: `threat6` gegen `v3nets6` (gleiche Trainingsstarts) – zeigt, ob die
   Merkmale selbst helfen.
3. Genau ein Kandidat: der bessere von `threat6`/`mix24` nach Solution_92-Siegquote. Er geht
   nur weiter, wenn er auf dem Auswahlblock mindestens +3 Prozentpunkte vor V3 liegt und
   default ≥ 99 % erreicht. Sonst Ende dieses Versuchs, frische Karten bleiben unberührt.
4. PPO: erst nach Laufende (oder spätestens am 22.10. vormittags mit dem dann letzten
   gespeicherten Stand) höchstens drei vorher festgelegte Stände (Iteration 50, 100, letzte)
   auf demselben Auswahlblock. Gleiche +3-Regel; nur einer der beiden Wege (DQN oder PPO)
   darf den Bestätigungsblock benutzen, der jeweils bessere.

## Bestätigung (einmalig, frisch)

- 503420–503619 (200 Karten, beide Seiten): Kandidat und V3 gegen Solution_92 und default.
- 503620–503819 (200 Karten, beide Seiten): Kandidat direkt gegen V3 (400 Spiele).
- Gepaarter Karten-Bootstrap, 5000 Ziehungen, Seed 0 (`scripts.compare_report`).
- Übernahme nur wenn alle gelten: Solution_92 Δ ≥ +5 Prozentpunkte und untere 95%-Grenze
  > 0; default ≥ 99 % und Δ ≥ −1 Prozentpunkt; direkt mittleres Ergebnis mit unterer
  95%-Grenze > 0,5. Keine Erweiterung der Stichprobe nach Sichtung.
- Vor einer Übernahme: aktuelle V3 mit Hash unter `experiments/releases/` sichern (alte
  Sechser-Sicherung bleibt), Kurs-Runner-Prüfung, gesamte Testsuite, Mahmoud fragt Moayed.
  Ergebnis in jedem Fall in Arbeitsstand und Experimentprotokoll.

## Ergebnis (21.10.2026, 21:48 – nach der Festlegung oben ergänzt)

Auswahlblock 503220–503419, je 400 Spiele: V3 76,7 % gegen Solution_92 (default 98,8 %),
`v3nets6` 73,3 %, `threat6` 72,8 %, `mix24` 78,2 % (default 99,0 %). Gepaarter Karten-Bootstrap
gegen V3: `mix24` +1,5 [−2,8; +5,8], `threat6` −4,0 [−9,5; +1,3]; `threat6` gegen Kontrolle −0,5
[−6,0; +4,8]. Bester Kandidat `mix24` unter der +3-Regel → **beendet**, Bestätigungsblöcke nicht
benutzt. PPO-Teil (Schritt 4) steht noch aus.


## Nachtrag vor neuen Spielen (21.10.2026, 22:00): Kombination `mix24_art3`

Festgelegt, bevor der Kandidat gespielt hat. `mix24_art3` = `mix24` + `art_sap=true`,
`art_min_hits=3` (frisch bei Codex +2,25 pp auf 523000–523199). Nur auf dem bereits benutzten
Auswahlblock 503220–503419 (Auswahlverzerrung möglich, deshalb nur Vorauswahl). Weiter auf die
unbenutzten Bestätigungsblöcke 503420–503819 genau dann, wenn Solution_92 ≥ +3 pp vor V3
(76,7 %) und default ≥ 99 %; dort unverändert die Übernahme-Gates oben. Keine weiteren
Varianten oder Schwellen nach Sichtung.

Ergebnis Nachtrag (22:08): `mix24_art3` Solution_92 78,2 % (Δ +1,5 [−3,0; +6,0] gegen V3),
default 99,3 % → +3-Regel verfehlt, beendet. Bestätigungsblöcke 503420–503819 weiter unbenutzt.
