"""Abnahmeregeln der Gegner-Liga pruefen (docs/superpowers/plans/2026-10-26-league.md).

    python -m scripts.league_gates select REF.csv NAME KAND.csv DIREKT.csv [NAME KAND.csv DIREKT.csv ...]
    python -m scripts.league_gates confirm REF.csv KAND.csv DIREKT.csv
    python -m scripts.league_gates battle REF.csv KAND.csv DIREKT.csv   (30.10.2026: Mittel ueber BATTLE_SIX statt R)
    ... [--direct-opponent self:PFAD]   (30.10.2026: Direktduell gegen eine andere Referenz als V10)

Robustheitsmittel R = mittlere Siegquote gegen die PANEL-Gegner; nur Karten, auf denen Referenz
und Kandidat jeden Panel-Gegner von beiden Seiten gespielt haben. Gepaarter Karten-Bootstrap wie
scripts.compare_report (5000 Ziehungen, Seed 0, 95-%-Perzentile). Exit-Code 0 = bestanden
(select: ein Kandidat gewaehlt), 1 = nicht bestanden.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from scripts.compare_report import BOOTSTRAP_SAMPLES, KEY, compare_results, validated_results

OLD3 = "self:experiments/releases/20261020_old3_sym3/agent_p0.pth"
V10_REF = "self:experiments/releases/20261022_v10_baseline/agent_p0.pth"
PANEL = ("solution92", "sol92_sq", "sol92_weak", OLD3)

# Auswahl (200 Karten): Punktschaetzungen, hoechstens ein Kandidat
SEL_PANEL_DELTA = 0.015
SEL_SOL92_DELTA = -0.010
SEL_DEFAULT = 0.99
SEL_DIRECT = 0.50
# Bestaetigung (800 frische Karten, 400 frische Direktkarten)
CONF_PANEL_DELTA = 0.02
CONF_SOL92_DELTA = -0.005
CONF_SOL92_LOW = -0.025
CONF_DEFAULT = 0.99
CONF_DEFAULT_DELTA = -0.01
CONF_DIRECT_LOW = 0.50
# Battle-Bestaetigung (Plan battle-push, Nachtrag 30.10.2026, 23:01): wie die Bestaetigung, aber Mittel ueber die
# 6 Gegner des Dev-A-Screens (Solution_92-Familie und vier RL-Agents) statt R, Hoehe +1 pp
BATTLE_SIX = ("solution92", "sol92_sq", "self:experiments/releases/20261022_all18_v3/agent_p0.pth",
              "self:experiments/releases/20261022_v7_Bsnpd/agent_p0.pth",
              "self:experiments/ensembles/league_nets6.pth", "self:experiments/ensembles/threat6.pth")
BATTLE_DELTA = 0.01


def _bootstrap(values: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(0)
    samples = rng.choice(values, size=(BOOTSTRAP_SAMPLES, len(values)), replace=True).mean(axis=1)
    low, high = np.percentile(samples, [2.5, 97.5])
    return float(low), float(high)


def panel_delta(candidate: pd.DataFrame, reference: pd.DataFrame, panel=PANEL) -> dict:
    """R von Kandidat und Referenz auf gemeinsamen vollstaendigen Karten, gepaarte Differenz."""
    cand = validated_results(candidate, "Kandidat")
    ref = validated_results(reference, "Referenz")
    cand, ref = cand[cand["opponent"].isin(panel)], ref[ref["opponent"].isin(panel)]
    paired = cand.merge(ref, on=KEY, suffixes=("_c", "_r"), validate="one_to_one")
    complete = paired.groupby("seed")["opponent"].size().eq(2 * len(panel))
    paired = paired[paired["seed"].isin(complete[complete].index)]
    if paired.empty:
        raise ValueError("keine gemeinsame Karte mit allen Panel-Gegnern")
    maps = paired.groupby("seed")[["result_c", "result_r"]].mean()
    diff = (maps["result_c"] - maps["result_r"]).to_numpy()
    low, high = _bootstrap(diff)
    return dict(maps=len(maps), winrate=float(maps["result_c"].mean()),
                ref_winrate=float(maps["result_r"].mean()), delta=float(diff.mean()), low=low, high=high)


def direct_result(direct: pd.DataFrame, opponent: str = V10_REF) -> dict:
    """Siegquote im Direktduell gegen die Referenz, Karten-Bootstrap (beide Seiten je Karte)."""
    d = validated_results(direct, "Direkt")
    if set(d["opponent"]) != {opponent}:
        raise ValueError(f"Direktduell muss genau gegen {opponent} laufen, nicht {sorted(set(d['opponent']))}")
    maps = d.groupby("seed")["result"].mean().to_numpy()
    low, high = _bootstrap(maps)
    return dict(maps=len(maps), games=len(d), winrate=float(maps.mean()), low=low, high=high)


def _by_opponent(candidate: pd.DataFrame, reference: pd.DataFrame) -> dict:
    return {r["opponent"]: r for r in compare_results(candidate, reference)}


def selection_checks(reference: pd.DataFrame, candidate: pd.DataFrame, direct: pd.DataFrame,
                     direct_opponent: str = V10_REF) -> dict:
    p = panel_delta(candidate, reference)
    rows = _by_opponent(candidate, reference)
    d = direct_result(direct, direct_opponent)
    checks = {
        f"R Δ >= +{SEL_PANEL_DELTA * 100:.1f} pp": p["delta"] >= SEL_PANEL_DELTA,
        f"Solution_92 Δ >= {SEL_SOL92_DELTA * 100:+.1f} pp": rows["solution92"]["delta"] >= SEL_SOL92_DELTA,
        f"default >= {SEL_DEFAULT:.0%}": rows["default"]["winrate"] >= SEL_DEFAULT,
        f"direkt >= {SEL_DIRECT:.0%}": d["winrate"] >= SEL_DIRECT,
    }
    return dict(panel=p, solution92=rows["solution92"], default=rows["default"], direct=d, checks=checks,
                passed=all(checks.values()))


def confirm_checks(reference: pd.DataFrame, candidate: pd.DataFrame, direct: pd.DataFrame,
                   direct_opponent: str = V10_REF, panel=PANEL, min_delta: float = CONF_PANEL_DELTA,
                   label: str = "R") -> dict:
    p = panel_delta(candidate, reference, panel)
    rows = _by_opponent(candidate, reference)
    sol, dfl = rows["solution92"], rows["default"]
    d = direct_result(direct, direct_opponent)
    checks = {
        f"{label} Δ >= +{min_delta * 100:.0f} pp": p["delta"] >= min_delta,
        f"{label} untere 95%-Grenze > 0": p["low"] > 0,
        f"Solution_92 Δ >= {CONF_SOL92_DELTA * 100:+.1f} pp": sol["delta"] >= CONF_SOL92_DELTA,
        f"Solution_92 untere 95%-Grenze > {CONF_SOL92_LOW * 100:+.1f} pp": sol["low"] > CONF_SOL92_LOW,
        f"default >= {CONF_DEFAULT:.0%}": dfl["winrate"] >= CONF_DEFAULT,
        f"default Δ >= {CONF_DEFAULT_DELTA * 100:+.0f} pp": dfl["delta"] >= CONF_DEFAULT_DELTA,
        "direkt untere 95%-Grenze > 50 %": d["low"] > CONF_DIRECT_LOW,
    }
    return dict(panel=p, solution92=sol, default=dfl, direct=d, checks=checks, passed=all(checks.values()))


def pick(results: dict[str, dict]) -> str | None:
    """Hoechstens einen Kandidaten waehlen: groesstes R-Δ unter den bestandenen, dann direkt."""
    ok = [(r["panel"]["delta"], r["direct"]["winrate"], name) for name, r in results.items() if r["passed"]]
    return max(ok)[2] if ok else None


def _report(name: str, r: dict, label: str = "R") -> None:
    p, s, dfl, d = r["panel"], r["solution92"], r["default"], r["direct"]
    print(f"{name}: {label} {p['winrate']:.4f} vs {p['ref_winrate']:.4f} (Δ {p['delta'] * 100:+.2f} pp "
          f"[{p['low'] * 100:+.2f}; {p['high'] * 100:+.2f}], {p['maps']} Karten); Solution_92 "
          f"{s['winrate']:.4f} (Δ {s['delta'] * 100:+.2f} [{s['low'] * 100:+.2f}; {s['high'] * 100:+.2f}]); "
          f"default {dfl['winrate']:.4f} (Δ {dfl['delta'] * 100:+.2f}); direkt {d['winrate']:.4f} "
          f"[{d['low']:.4f}; {d['high']:.4f}] aus {d['games']} Spielen")
    for k, v in r["checks"].items():
        print(f"  {'OK  ' if v else 'FAIL'} {k}")


def main(argv: list[str]) -> int:
    argv, opp = list(argv), V10_REF
    if "--direct-opponent" in argv:
        i = argv.index("--direct-opponent")
        opp = argv[i + 1]
        del argv[i:i + 2]
    mode, ref = argv[0], pd.read_csv(argv[1])
    if mode == "select":
        rest = argv[2:]
        if not rest or len(rest) % 3:
            raise SystemExit("select REF NAME KAND DIREKT [NAME KAND DIREKT ...]")
        results = {}
        for i in range(0, len(rest), 3):
            name, cand, direct = rest[i], pd.read_csv(rest[i + 1]), pd.read_csv(rest[i + 2])
            results[name] = selection_checks(ref, cand, direct, opp)
            _report(name, results[name])
        chosen = pick(results)
        print(f"AUSWAHL: {chosen or 'keine'}")
        return 0 if chosen else 1
    if mode == "confirm":
        r = confirm_checks(ref, pd.read_csv(argv[2]), pd.read_csv(argv[3]), opp)
        _report("Bestaetigung", r)
        print("GATE Bestaetigung:", "BESTANDEN" if r["passed"] else "NICHT BESTANDEN")
        return 0 if r["passed"] else 1
    if mode == "battle":
        r = confirm_checks(ref, pd.read_csv(argv[2]), pd.read_csv(argv[3]), opp, BATTLE_SIX, BATTLE_DELTA, "Mittel 6")
        _report("Battle-Bestaetigung", r, "Mittel 6")
        print("GATE Battle-Bestaetigung:", "BESTANDEN" if r["passed"] else "NICHT BESTANDEN")
        return 0 if r["passed"] else 1
    raise SystemExit(f"unbekannter Modus {mode}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
