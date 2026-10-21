# Mechanismus-Probe V3 gegen Solution_92 (21.10.2026, Claude Code mit Mahmoud)

Reine Messung: `scripts/mechanism_probe.py` spielt die unveränderte Abgabe `all18_v3`
(SHA-256 `aac1c910…d935`) gegen Solution_92 und baut jeden Engine-Schritt aus dem wahren
Zustand nach (Bewegung → Sap direkt/3×3 → Kollision → Void → Energiefeld, Logik aus
`luxai_s3/env.py`). Gezählt wird je Team und Match: Saps, Sap-Schaden, Void, Tode nach
Ursache, Units auf Punkte-Tiles, gestapelte Units und (nur eigene Seite) was jede Unit
laut Zielzuweisung tut. Bekannte Entwicklungskarten 500720–500779, beide Seiten, 120 Spiele
(V3 102/120 Siege, gleich der Referenz `enemy_tie_energy_20261021/development_v3.csv`).
`productive` (Punkt-Tile-Schritte) ist eine Näherung der Matchpunkte (±5 %).

`scripts/mechanism_report.py X.json` druckt die Tabellen, `scripts/render_snapshots.py`
zeichnet Spielfeld-Schnappschüsse.

## Befund: Festung in Match 3

Verlorene Matches 3 (42/120) liegen auf Karten mit vielen Punkte-Tiles (eigene Hälfte
im Mittel 10,75 statt 6,6 in gewonnenen). Pro Step im Mittel: 4,3 eigene Units allein auf
Punkte-Tiles, 0,5 gestapelt, 2,75 unterwegs zu eigenen Punkte-Tiles (Ø 8,5 Felder),
1,8 unterwegs zu Punkte-Tiles der Gegnerhälfte (Ø 18,6 Felder), 1,35 testen Kandidaten;
2,5 von 10,75 eigenen Punkte-Tiles unbekannt. Solution_92 hält 5,8 Tiles seiner und 0,6
unserer Hälfte.

In den deutlichsten Niederlagen kippt das Sap-Verhältnis in Match 3 vollständig:

| Karte, Seite | Saps wir : Gegner | Sap-Schaden wir : Gegner | Tote wir : Gegner |
|---|---|---|---|
| 500753 p0 | 6 : 68 | 443 : 5433 | 23 : 4 |
| 500732 p0 | 12 : 57 | 855 : 1976 | 20 : 4 |
| 500776 p1 | 9 : 43 | 360 : 2415 | 22 : 11 |

Match 1/2 derselben Spiele: wir sappen mehr als Solution_92. Bilder
`festung_500753_m3_*.png`: alle Relics in einem Haufen an der Diagonale, Solution_92 sitzt
mit ~13 Units darauf, unsere wiedergeborenen Units laufen einzeln aus der Ecke nach und
sterben. Solution_92 sappt von seinem Punkte-Tile jede sichtbare Unit mit
Manhattan-Abstand ≤ Reichweite (Ziel = aktuelle Position), die Engine erlaubt dagegen das
ganze Quadrat (Chebyshev).

## Daraus abgeleitete Versuche (Entwicklungskarten, nur Auswahl, keine Bestätigung)

Referenz V3 Solution_92 102/120 = 85,0 %, default 120/120. Gepaarter Karten-Bootstrap
(`scripts.compare_report`, 5000 Ziehungen, Seed 0). Rohdaten
`experiments/compare/regeln/A21_*_720.csv`.

| Schalter (Default aus) | Solution_92 | Δ [95-%-KI] |
|---|---|---|
| `art_sap` (Sap ≥ 2 Treffer aus Manhattan-sicherer Position) | 87,5 % | +2,5 [−1,7; +6,7] |
| `art_sap`, `art_min_hits=3` | 90,0 % | +5,0 [+0,8; +10,0] |
| `art_sap`, `art_min_hits=4` | 84,2 % | −0,8 [−3,3; +1,7] |
| `art_sap`, 3 Treffer, `art_safe=false` | 85,8 % | +0,8 [−3,3; +5,0] |
| `art_sap`, 3 Treffer, `art_reserve=20` | 85,8 % | +0,8 [−3,3; +5,0] |
| `siege` (Festungsziel → Schussposition, Sap auch in den Nebel) | 67,5 % | **−17,5** [−25,8; −10,0] |
| `siege` + `art_sap` 3 | 70,8 % | −14,2 [−23,3; −5,8] |

Default überall 120/120. `art_sap` 3 löst nur rund zwei zusätzliche Saps je Match aus
(`probe_art3_720.json`); die Nachbarvarianten liegen bei −1 bis +1 → der Wert +5 ist
vermutlich zum Teil Auswahlglück, kein Kandidat ohne frische Bestätigung. `siege` senkt
die Punkt-Tile-Schritte in allen drei Matches (Match 3: 442 → 390, `probe_siege_720.json`),
die Units warten an Schusspositionen und geben umkämpfte Tiles auf → verworfen.

Folgeversuch: Netze bekommen Gefahr-Merkmale (`threat_feats`, Manhattan- und
Quadrat-Bedrohung je Tile), siehe Arbeitsstand.
