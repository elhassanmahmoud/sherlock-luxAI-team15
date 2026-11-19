"""Auswertung der Zugbeispiele für die Abschlusspräsentation (19.11.2026, nur Messung).

Liest die Dateien `beispiele_<gegner>_<seed>.json` von zugbeispiel.py, prüft, dass jeder Zug nachgerechnet wurde,
zählt Schüsse nach Sicht und Treffern, schreibt `ergebnis.json` (Summen und die beiden Folienbeispiele) und
erzeugt die Karte des Schussbeispiels als SVG (`karte_schuss.svg`).

    python experiments/analysis/finale_20261119/auswertung.py DIR
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHUSS = dict(seed=4247, match=3, match_step=66, unit=11)
HALTER = dict(seed=4247, match=1, match_step=53, unit=2)
ACTIONS = ("stehen", "hoch", "rechts", "runter", "links", "schuss")


def pick(examples, kind, want):
    for e in examples:
        if e["kind"] == kind and all(e[k] == v for k, v in want.items() if k != "seed"):
            return e
    raise SystemExit(f"Beispiel nicht gefunden: {kind} {want}")


def svg_map(e: dict) -> str:
    """Ganze Karte 24x24 aus Sicht von Sherlock plus die echten Gegnerpositionen (Schiedsrichtersicht)."""
    W = H = 24
    s = 15  # Pixel je Feld
    pad = 18
    size_x, size_y = W * s + 2 * pad, H * s + 2 * pad
    vis, ast, pt = e["sensor_mask"], e["asteroid"], e["point_tiles"]
    ux, uy, tx, ty, rng = e["x"], e["y"], e["target_x"], e["target_y"], e["sap_range"]
    hit = {(h["x"], h["y"]) for h in e["hit_enemies"]}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size_x} {size_y}" width="{size_x}" '
           f'height="{size_y}" role="img" aria-label="Karte 4247, Match 3, Zug 66: Schuss ohne sichtbaren Gegner">']
    out.append(f'<rect x="0" y="0" width="{size_x}" height="{size_y}" fill="#F7F6F1"/>')
    for x in range(W):
        for y in range(H):
            fill = "#FFFFFF" if vis[x][y] else "#DCE3E0"
            if ast[x][y]:
                fill = "#7D8C89"
            out.append(f'<rect x="{pad + x * s}" y="{pad + y * s}" width="{s - 1}" height="{s - 1}" fill="{fill}"/>')
    for x in range(W):
        for y in range(H):
            if pt[x][y]:
                out.append(f'<rect x="{pad + x * s + 2}" y="{pad + y * s + 2}" width="{s - 5}" height="{s - 5}" '
                           f'fill="none" stroke="#00968A" stroke-width="2" rx="2"/>')
    for rx, ry in e["relics"]:
        cx, cy = pad + rx * s + s / 2 - 0.5, pad + ry * s + s / 2 - 0.5
        out.append(f'<path d="M{cx} {cy - 6} L{cx + 6} {cy} L{cx} {cy + 6} L{cx - 6} {cy} Z" fill="#142D35"/>')
    x0, y0 = max(0, ux - rng), max(0, uy - rng)
    x1, y1 = min(W - 1, ux + rng), min(H - 1, uy + rng)
    out.append(f'<rect x="{pad + x0 * s - 1}" y="{pad + y0 * s - 1}" width="{(x1 - x0 + 1) * s + 1}" '
               f'height="{(y1 - y0 + 1) * s + 1}" fill="none" stroke="#0F7774" stroke-width="1.5"/>')
    for ex, ey in e["true_enemies_after_move"]:
        cx, cy = pad + ex * s + s / 2 - 0.5, pad + ey * s + s / 2 - 0.5
        if (ex, ey) in hit:
            out.append(f'<circle cx="{cx}" cy="{cy}" r="5" fill="#B5452A" stroke="#F7F6F1" stroke-width="2"/>')
        else:
            out.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="none" stroke="#B5452A" stroke-width="1.6"/>')
    for ox, oy in e["own_units"]:
        if (ox, oy) == (ux, uy):
            continue
        cx, cy = pad + ox * s + s / 2 - 0.5, pad + oy * s + s / 2 - 0.5
        out.append(f'<circle cx="{cx}" cy="{cy}" r="4.5" fill="#00968A" stroke="#F7F6F1" stroke-width="2"/>')
    ucx, ucy = pad + ux * s + s / 2 - 0.5, pad + uy * s + s / 2 - 0.5
    tcx, tcy = pad + tx * s + s / 2 - 0.5, pad + ty * s + s / 2 - 0.5
    out.append(f'<line x1="{ucx}" y1="{ucy}" x2="{tcx}" y2="{tcy}" stroke="#B5452A" stroke-width="2" '
               f'stroke-linecap="round"/>')
    out.append(f'<circle cx="{tcx}" cy="{tcy}" r="10" fill="none" stroke="#B5452A" stroke-width="2"/>')
    out.append(f'<circle cx="{ucx}" cy="{ucy}" r="7" fill="#0F7774" stroke="#F7F6F1" stroke-width="2"/>')
    font = 'font-family="Helvetica Neue, Helvetica, Arial, sans-serif"'
    for v in range(0, W, 4):
        out.append(f'<text x="{pad + v * s + s / 2}" y="{pad - 5}" font-size="10" fill="#52646A" '
                   f'text-anchor="middle" {font}>{v}</text>')
        out.append(f'<text x="{pad - 5}" y="{pad + v * s + s / 2 + 3.5}" font-size="10" fill="#52646A" '
                   f'text-anchor="end" {font}>{v}</text>')
    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dir", type=Path)
    a = ap.parse_args()
    per_opp = defaultdict(lambda: dict(games=0, decisions=0, saps=0, holder_rule_decisive=0, stay_bias_decisive=0,
                                       blocked_best_moves=0, match_wins=[0, 0], game_wins=0))
    shots = defaultdict(lambda: defaultdict(Counter))
    reasons = defaultdict(Counter)
    chosen = {}
    for f in sorted(a.dir.glob("beispiele_*.json")):
        d = json.loads(f.read_text())
        s = d["summary"]
        c = s["checks"]
        if not (c["decisions"] == c["action_equal"] == c["logp_equal"] == s["decisions"]
                and c["saps"] == c["target_equal"] == s["saps"]):
            raise SystemExit(f"Nachrechnung nicht vollständig: {f}")
        o = per_opp[s["opponent"]]
        o["games"] += 1
        for k in ("decisions", "saps", "holder_rule_decisive", "stay_bias_decisive", "blocked_best_moves"):
            o[k] += s[k]
        w = s["match_wins_v16_opponent"]
        o["match_wins"][0] += w[0]
        o["match_wins"][1] += w[1]
        o["game_wins"] += int(w[0] > w[1])
        for cat, v in s["shots"].items():
            shots[s["opponent"]][cat].update(v)
        reasons[s["opponent"]].update(s["blocked_reasons"])
        if s["opponent"] == "kaggle3" and s["seed"] == SCHUSS["seed"]:
            chosen["schuss"] = pick(d["examples"], "schuss_ohne_sichtbaren_gegner", SCHUSS)
            chosen["halter"] = pick(d["examples"], "halter_regel_entscheidet", HALTER)
    if set(chosen) != {"schuss", "halter"}:
        raise SystemExit("Beispielspiel kaggle3 4247 fehlt")
    summary = {}
    for opp, o in per_opp.items():
        sh = {cat: dict(v) for cat, v in shots[opp].items()}
        summary[opp] = dict(o, shots=sh, blocked_reasons=dict(reasons[opp]))
    sch = chosen["schuss"]
    hal = chosen["halter"]
    slim_schuss = {k: v for k, v in sch.items() if k not in ("nebula", "asteroid", "sensor_mask", "point_tiles")}
    result = dict(
        source="experiments/analysis/finale_20261119/zugbeispiel.py, Abgabepaket SHA-256 0c59706b…6099, V16 als player_0",
        seeds="4242-4251", summary=summary,
        schuss_beispiel=slim_schuss,
        halter_beispiel=hal,
    )
    (HERE / "ergebnis.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
    (HERE / "karte_schuss.svg").write_text(svg_map(sch))
    k = summary["kaggle3"]
    blind = k["shots"]["unsichtbar"]
    print(json.dumps(dict(kaggle3_games=k["games"], saps=k["saps"], blind=blind, holder=hal["final"],
                          holder_without=hal["without_holder_rule"]), ensure_ascii=False))


if __name__ == "__main__":
    main()
