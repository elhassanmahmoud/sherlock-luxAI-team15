"""Offline-Vergleich von Zielwahlen fuer den Nebel-Sap auf den Ereignissen aus v12_fog_hits.py (31.10.2026).

Jede Regel bekommt je Ereignis dieselbe Information wie der Agent (Kandidaten, Zahl versteckter Gegner, letzte eigene
Beobachtung je Tile, geschaetzter Streufaktor) und waehlt ein Ziel oder keins. Bewertet wird mit der Wahrheit nach der
Bewegung: Schaden = Kosten x (Gegner auf dem Ziel + echter Streufaktor x Gegner auf den 8 Nachbarn). Dynamische Folgen
(Gegner weicht aus, Energie fehlt spaeter) fehlen; dafuer gibt es den Test auf Dev A.

    .venv/bin/python experiments/analysis/battle/v12_fog_eval.py EVENTS.csv
"""
import sys
from collections import Counter

import numpy as np
import pandas as pd


def parse(df):
    ev = []
    for r in df.itertuples(index=False):
        cand = []
        for c in r.cand.split(";"):
            xy, ao, ae = c.split(":")
            cx, cy = (int(v) for v in xy.split("-"))
            cand.append((cx, cy, int(ao), int(ae)))
        truth = Counter()
        if isinstance(r.truth, str) and r.truth:
            for t in r.truth.split(";"):
                tx, ty = (int(v) for v in t.split("-"))
                truth[(tx, ty)] += 1
        fired = None
        if isinstance(r.fired, str) and r.fired:
            fired = tuple(int(v) for v in r.fired.split("-"))
        ev.append(dict(r._asdict(), cand=cand, truth=truth, fired=fired))
    return ev


def choose(e, weight, drop_rule, min_frac=0.6, need_pt=True, reserve=30.0):
    """Wie rules.fog_sap (gleiche Kandidaten- und Zielreihenfolge), Gewichte und Streufaktor austauschbar."""
    if need_pt and not e["on_pt"]:
        return None
    if e["ene"] < e["cost"] + reserve:
        return None
    x, y, R, cost = e["x"], e["y"], e["R"], e["cost"]
    cand = e["cand"]
    w = np.array([weight(ao, ae) for _, _, ao, ae in cand], dtype=float)
    if w.sum() <= 0:
        return None
    p = np.minimum(1.0, e["hidden"] * w / w.sum())
    drop = drop_rule(e)
    cx = np.array([c[0] for c in cand])
    cy = np.array([c[1] for c in cand])
    targets = set()
    for tx, ty in zip(cx, cy):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                a, b = int(tx) + dx, int(ty) + dy
                if 0 <= a < 24 and 0 <= b < 24 and abs(a - x) <= R and abs(b - y) <= R:
                    targets.add((a, b))
    best, best_v = None, 0.0
    for a, b in targets:
        cheb = np.maximum(np.abs(cx - a), np.abs(cy - b))
        v = cost * float((p * ((cheb == 0) + drop * (cheb == 1))).sum())
        if v > best_v:
            best, best_v = (a, b), v
    if best is None or best_v < min_frac * cost:
        return None
    return best


def damage(e, t):
    if t is None:
        return 0.0, 0, 0
    a, b = t
    direct = e["truth"].get((a, b), 0)
    ring = sum(n for (tx, ty), n in e["truth"].items() if max(abs(tx - a), abs(ty - b)) == 1)
    return e["cost"] * (direct + e["drop"] * ring), direct, ring


UNIFORM = lambda ao, ae: 1.0                                                           # noqa: E731
D05 = lambda e: 0.5                                                                    # noqa: E731
DEST = lambda e: e["drop_est"] if e["drop_est"] >= 0 else 0.5                          # noqa: E731


def recency(occ=4.0, empty=0.25, horizon=1000):
    """Zuletzt besetzt gesehen -> occ, zuletzt leer gesehen -> empty, nie gesehen -> 1."""
    def w(ao, ae):
        if ao < ae and ao < horizon:
            return occ
        if ae < ao and ae < horizon:
            return empty
        return 1.0
    return w


def evaluate(ev, rules):
    games = len({(e["seed"], e["side"], e["opp"]) for e in ev})
    if not games:
        return pd.DataFrame()
    out = []
    for name, kw in rules.items():
        dmg = shots = direct = anyhit = cost = 0.0
        for e in ev:
            t = choose(e, **kw)
            if t is None:
                continue
            d, dh, rh = damage(e, t)
            shots += 1
            cost += e["cost"]
            dmg += d
            direct += dh > 0
            anyhit += (dh + rh) > 0
        out.append(dict(rule=name, shots_per_game=shots / games, direct_rate=direct / max(1, shots),
                        any_rate=anyhit / max(1, shots), dmg_per_shot=dmg / max(1, shots),
                        dmg_per_game=dmg / games, net_per_game=(dmg - cost) / games))
    return pd.DataFrame(out).set_index("rule")


if __name__ == "__main__":
    df = pd.read_csv(sys.argv[1])
    ev = parse(df)
    # Kontrolle: R0 muss die tatsaechliche Wahl wiedergeben
    same = sum(choose(e, UNIFORM, D05) == e["fired"] for e in ev)
    print(f"{len(ev)} Ereignisse, {sum(e['fired'] is not None for e in ev)} gefeuert; R0 = Agent in {same / len(ev):.4f}")
    rules = {
        "R0 jetzt (gleich, 0,5)": dict(weight=UNIFORM, drop_rule=D05),
        "R1 Schaetzung Streufaktor": dict(weight=UNIFORM, drop_rule=DEST),
        "R2 zuletzt gesehen 4/0,25": dict(weight=recency(), drop_rule=D05),
        "R2b zuletzt gesehen 8/0,1": dict(weight=recency(8, 0.1), drop_rule=D05),
        "R2c zuletzt gesehen 2/0,5": dict(weight=recency(2, 0.5), drop_rule=D05),
        "R3 = R2 + R1": dict(weight=recency(), drop_rule=DEST),
        "R3 jede Unit (fog_any)": dict(weight=recency(), drop_rule=DEST, need_pt=False),
        "R3 Reserve 0": dict(weight=recency(), drop_rule=DEST, reserve=0.0),
        "R3 Schwelle 0,4": dict(weight=recency(), drop_rule=DEST, min_frac=0.4),
        "R3 Schwelle 0,8": dict(weight=recency(), drop_rule=DEST, min_frac=0.8),
    }
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)
    print(evaluate(ev, rules).round(3))
    for drop in (0.25, 0.5, 1.0):
        sub = [e for e in ev if e["drop"] == drop]
        print(f"\nStreufaktor {drop}:")
        print(evaluate(sub, {k: rules[k] for k in ("R0 jetzt (gleich, 0,5)", "R1 Schaetzung Streufaktor",
                                                    "R2 zuletzt gesehen 4/0,25", "R3 = R2 + R1")}).round(3))
