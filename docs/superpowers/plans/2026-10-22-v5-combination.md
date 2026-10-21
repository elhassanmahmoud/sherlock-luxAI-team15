# V5: Regeln der Nacht zu einem Kandidaten kombinieren (vorab festgelegt)

22.10.2026, ca. 00:20, Claude Code mit Mahmoud. Festgelegt, bevor irgendeine der unten
genannten Kombinationen gespielt wurde. Ziel des Users: 99–100 % gegen Solution_92.

## Ausgangslage (Entwicklung, keine Bestätigung)

Entwicklungs-Sets aus der Kartensuche (deterministische Spiele, V3-Werte aus
`H21_screen_v3_360000.csv`): `dev_hard150` (V3 25,0 %), `dev_easy60` (V3 100 %).

| Schalter | hard150 | easy60 |
|---|---|---|
| `art_sap` 3 Treffer | 37,7 % | 98,3 % |
| `dodge` always | 35,0 % | 97,5 % |
| `art_sap` 3 + `dodge` | 38,7 % | 96,7 % |
| `art_sap` 3, nur bei Rückstand | 33,0 % | 100 % |
| `nebula_avoid` (Schwelle 25) | 100 Karten mit Nebelabzug 25: 69,5 % statt 64,5 % | |

`sap_kill_safe` und `art_sap`+`sap_kill_safe` werden gerade gemessen und zählen mit.

## Kandidaten

Netze: V3 (18 Netze) oder – falls `hard24` die Auswahlregel seines eigenen Plans
(`2026-10-21-hard-map-training.md`) besteht – `hard24`. Regelpakete, jeweils zusätzlich zur
V3-Konfiguration:

- A: `art_sap` 3
- B: A + `nebula_avoid` (25)
- C: B + `sap_kill_safe` (nur falls `sap_kill_safe` allein auf hard150 nicht schlechter als V3 ist)
- D: B + `dodge` always

## Auswahl

1. Jede Kombination auf `dev_hard150` und `dev_easy60` gegen Solution_92.
2. Kennzahl: Δ_gesamt = 0,33 · Δ_hard150 + 0,67 · Δ_easy60 (Anteil schwerer Karten in der
   Kartensuche: 660/2000). Bester Kandidat nach dieser Kennzahl, bei Gleichstand der einfachere.
3. Zufälliger Kartenblock 503820–504019 (200 Karten, beide Seiten, default + Solution_92; dort
   V3 76,7 %): weiter nur bei ≥ +3 Prozentpunkten gegen Solution_92 und default ≥ 99 %.

## Bestätigung und Übernahme

Einmalig, genau ein Kandidat: 503420–503619 (Kandidat und V3, beide Gegner, je 800 Spiele) und
503620–503819 direkt gegen V3 (400 Spiele). Übernahme nur bei Solution_92 Δ ≥ +5 pp mit unterer
95%-Grenze > 0, default ≥ 99 % und Δ ≥ −1 pp, direkt untere Grenze > 0,5 (gepaarter
Karten-Bootstrap, 5000 Ziehungen, Seed 0). Vor einer Übernahme V3 sichern, Kurs-Runner-Prüfung,
Testsuite und Rücksprache mit Mahmoud und Moayed – die Gewichte ersetze ich nicht allein über Nacht.

## Nachtrag vor dem Spielen von E (22.10.2026, ca. 00:38)

Die Online-Schätzung des Sap-Streufaktors (`agents/sherlock/param_est.py`) ist jetzt verlässlich:
auf 500720–500749 (60 Spiele) **0 Fehlschätzungen**, sicher bekannt bei Schritt 101/202/300 in
25/41/47 von 60 Spielen (sonst Annahme 0,5); Nebelabzug 60/60 ab Schritt 202. Zusätzlicher
Kandidat **E: B + `dodge_auto` (dodge always nur bei geschätztem Streufaktor ≤ 0,5)**, gleiche
Auswahlregel wie A–D. Keine weiteren Kandidaten nach Sichtung der Ergebnisse.

## Ergebnis (22.10.2026, 01:57)

Auswahl auf hard150/easy60: B (`art_sap` 3 + `nebula_avoid` 25) bester Kandidat (≈ +5,8 gesamt;
A +3,1, C +4,3, D +4,5, E +4,8). Netze: `hard24` verfehlte seine eigene Hürde (+2,5) → V3-Netze.
Kandidatdatei `v5B_v3.pth` (SHA-256 `2c213ca8…cfd5`): 18 V3-Netze bitgleich, nur Schalter.

- Zufallsblock 503820–504019: Solution_92 80,5 % statt 76,75 % (Δ +3,75 [−0,3; +7,7]), default
  99,75 % → Auswahlhürde bestanden.
- Frische Bestätigung 503420–503619: **Solution_92 75,75 % statt V3 71,0 %, Δ +4,75 pp
  [+1,00; +8,25]**; default 99,75 % (Δ 0); **direkt gegen V3 62,0 % [56,5; 67,25]** (503620–503819).
- Kurs-Runner (8 Spiele): bestanden, Median 5 ms je Aktion.
- **Nicht bestanden: Δ ≥ +5 pp um 0,25 pp verfehlt** (alle anderen vier Kriterien erfüllt).
  Deshalb keine automatische Übernahme; die Hürde wird nicht nachträglich geändert.
  Entscheidungsvorlage für Mahmoud/Moayed: V5-B ist auf frischen Karten signifikant besser
  (untere Grenze > 0, direkt 62 %), erreicht aber nicht die vorab verlangte Mindestgröße.
  Die Blöcke 503420–503819 sind jetzt verbraucht.
