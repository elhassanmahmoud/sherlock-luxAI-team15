"""Diagramme der Abschlusspräsentation als SVG erzeugen (19.11.2026).

    python docs/presentation/finale_2711/diagramme.py

Schreibt drei Dateien neben dieses Skript; die Folien (Sherlock_Finale_27-11-2026.html) binden sie als Bild ein.
Alle Werte stehen hier mit ihrer Quelle. Farben: Markierungen #00968A (Netz/positiv) und #B5452A (negativ) sind mit
dem Palettenprüfer des dataviz-Skills auf der Folienfarbe #F7F6F1 geprüft; Texte tragen nie die Datenfarbe.
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
FONT = 'font-family="Helvetica Neue, Helvetica, Arial, sans-serif"'
INK, MUTED, GRID, SURFACE = "#142D35", "#52646A", "#D5DDDA", "#F7F6F1"
TEAL, RUST, REF = "#00968A", "#B5452A", "#8A9A97"

# Siege gegen Solution_92, frisch gemessen bei der Übernahme der jeweiligen Abgabe (Übernahmeberichte):
# Review 28/60 (CLAUDE.md, Stand 14.10.), V3 313/400 (autonomous_20261020/RELEASE.md), V7 83,5 % (release_20261022_v7),
# V10 90,3 % (release_20261022_v10), V12 94,4 % (release_20261031_v12), V14 95,4 % (release_20261101_v14).
WEG = [("Review", "16.10.", 46.7), ("V3", "20.10.", 78.3), ("V7", "22.10.", 83.5), ("V10", "22.10.", 90.3),
       ("V12", "31.10.", 94.4), ("V14", "Battle", 95.4)]

# Reiner Schüler mit Stay-Bias 1,5 und Entstapeln gegen Solution_92 auf Dev A (7150000-7150099, beide Seiten,
# je 200 Spiele): v2 78 %, v3 89,5 % (umbau_20261115/README.md), v4 185/200, v5 190/200 (v5/ERGEBNIS.md),
# v7 196/200 (v7/ERGEBNIS.md); V14 auf denselben Karten 188/200.
DAGGER = [("nur Lehrer", "v2", 78.0), ("Runde 1", "v3", 89.5), ("Runde 2", "v4", 92.5), ("Runde 3", "v5", 95.0),
          ("Runde 4", "v7", 98.0)]
DAGGER_V14 = 94.0

# Dev H (devh_20261117/ERGEBNIS.md): Punkteanteil gegen Kaggle, gepaart gegen V16 (K), je 800 Spiele.
TAKTIK = [("alles gleichzeitig", -1.64), ("ohne Sicherheitsmasken", -0.71), ("Nebel-Schüsse", -0.67),
          ("gemeinsame Abschüsse", -0.67), ("Granaten mit Streuschaden", -0.66), ("Ausweichen", -0.43),
          ("Tanken", 0.21), ("Matchende-Sturm", 0.26), ("öfter schießen", 0.52)]


def text(x, y, s, size=15, fill=MUTED, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" {FONT}>{s}</text>')


def pct(v):
    return f"{round(v)} %"


def line_chart(points, lo, hi, ticks, w=560, h=330, ref=None, ref_label=None, label_idx=(0, -1)):
    left, right, top, bottom = 70, w - 30, 22, h - 58
    n = len(points)
    xs = [left + 44 + i * (right - left - 80) / (n - 1) for i in range(n)]

    def y(v):
        return bottom - (v - lo) / (hi - lo) * (bottom - top)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
           f'<rect width="{w}" height="{h}" fill="{SURFACE}"/>']
    for t in ticks:
        out.append(f'<line x1="{left}" x2="{right}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="{GRID}" stroke-width="1"/>')
        out.append(text(left - 10, y(t) + 5, f"{t} %", 14, MUTED, "end"))
    if ref is not None:
        out.append(f'<line x1="{left}" x2="{right}" y1="{y(ref):.1f}" y2="{y(ref):.1f}" stroke="{REF}" '
                   f'stroke-width="1.5"/>')
        out.append(text(left + 8, y(ref) - 8, ref_label, 14, MUTED, "start"))
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f} {y(v):.1f}" for i, (x, (_, _, v)) in enumerate(zip(xs, points)))
    out.append(f'<path d="{path}" fill="none" stroke="{TEAL}" stroke-width="2" stroke-linejoin="round" '
               f'stroke-linecap="round"/>')
    for x, (name, sub, v) in zip(xs, points):
        out.append(f'<circle cx="{x:.1f}" cy="{y(v):.1f}" r="5.5" fill="{TEAL}" stroke="{SURFACE}" stroke-width="2"/>')
        out.append(text(x, bottom + 26, name, 15, INK, "middle"))
        out.append(text(x, bottom + 45, sub, 13, MUTED, "middle"))
    for i in label_idx:
        x, (_, _, v) = xs[i], points[i]
        dy = 22 if i == 0 else -14
        out.append(text(x, y(v) + dy, pct(v), 17, INK, "middle", "bold"))
    out.append("</svg>")
    return "\n".join(out)


def diverging(rows, lo=-1.8, hi=0.8, w=580, row_h=31, label_w=222):
    top = 14
    h = top + len(rows) * row_h + 44
    left, right = label_w, w - 52
    k = (right - left) / (hi - lo)

    def x(v):
        return left + (v - lo) * k

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
           f'<rect width="{w}" height="{h}" fill="{SURFACE}"/>']
    base = top + len(rows) * row_h
    for t in (-1.5, -1.0, -0.5, 0.5):
        out.append(f'<line x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{top - 4}" y2="{base}" stroke="{GRID}" stroke-width="1"/>')
        out.append(text(x(t), base + 20, f"{t:+.1f}".replace(".", ","), 13, MUTED, "middle"))
    out.append(text(x(0), base + 20, "0", 13, MUTED, "middle"))
    out.append(text((left + right) / 2, base + 40, "Punkteanteil gegen Kaggle, Änderung in Prozentpunkten", 13,
                    MUTED, "middle"))
    bar = 16
    for i, (name, v) in enumerate(rows):
        cy = top + i * row_h + row_h / 2
        out.append(text(left - 12, cy + 5, name, 15, INK, "end", "bold" if i == 0 else "normal"))
        x0, x1 = sorted((x(0), x(v)))
        color = RUST if v < 0 else TEAL
        out.append(f'<rect x="{x0:.1f}" y="{cy - bar / 2:.1f}" width="{x1 - x0:.1f}" height="{bar}" rx="4" fill="{color}"/>')
        sq = x(0) - 4 if v < 0 else x(0)
        out.append(f'<rect x="{sq:.1f}" y="{cy - bar / 2:.1f}" width="4" height="{bar}" fill="{color}"/>')
        if i == 0:  # Wert passt mit Abstand in den Balken: weiß auf der Markierung
            out.append(text(x(v) + 10, cy + 5, "−1,64", 14, "#FFFFFF", "start", "bold"))
        if name == "öfter schießen":
            out.append(text(x(v) + 8, cy + 5, "+0,52", 15, INK, "start", "bold"))
    out.append(f'<line x1="{x(0):.1f}" x2="{x(0):.1f}" y1="{top - 6}" y2="{base}" stroke="{MUTED}" stroke-width="1.5"/>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    (HERE / "diagramm_weg.svg").write_text(line_chart(WEG, 40, 100, (40, 60, 80, 100)))
    (HERE / "diagramm_dagger.svg").write_text(line_chart(DAGGER, 70, 100, (70, 80, 90, 100), ref=DAGGER_V14,
                                                         ref_label="V14 auf denselben Karten: 94 %"))
    (HERE / "diagramm_taktiken.svg").write_text(diverging(TAKTIK))
    print("geschrieben: diagramm_weg.svg, diagramm_dagger.svg, diagramm_taktiken.svg")


if __name__ == "__main__":
    main()
