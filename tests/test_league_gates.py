"""Abnahmeregeln der Gegner-Liga (scripts/league_gates.py, 26.10.2026)."""
import pandas as pd
import pytest

from scripts import league_gates as G

OPPS = G.PANEL + ("default",)


def frame(results: dict[str, list[float]], opponents=OPPS) -> pd.DataFrame:
    """results[opponent] = Ergebnis je Karte (beide Seiten gleich)."""
    rows = [dict(opponent=o, seed=700000 + i, side=side, result=r)
            for o in opponents for i, r in enumerate(results[o]) for side in ("player_0", "player_1")]
    return pd.DataFrame(rows)


def direct(results: list[float], opponent=G.V10_REF) -> pd.DataFrame:
    return pd.DataFrame([dict(opponent=opponent, seed=702000 + i, side=side, result=r)
                         for i, r in enumerate(results) for side in ("player_0", "player_1")])


def base(n=10, value=1.0):
    return {o: [value] * n for o in OPPS}


def test_panel_delta_is_paired_mean_over_panel_and_sides():
    ref = base(value=0.5)
    cand = base(value=0.5)
    cand["sol92_sq"] = [1.0] * 10          # nur ein Panel-Gegner besser: +0,5 / 4 = +12,5 pp
    cand["default"] = [0.0] * 10           # default zaehlt nicht zu R
    p = G.panel_delta(frame(cand), frame(ref))
    assert p["maps"] == 10
    assert p["delta"] == pytest.approx(0.125)
    assert p["low"] == pytest.approx(0.125) and p["high"] == pytest.approx(0.125)


def test_panel_delta_uses_only_maps_complete_for_every_panel_opponent():
    ref, cand = frame(base()), frame(base())
    ref = ref[~((ref["opponent"] == "sol92_weak") & (ref["seed"] == 700003))]
    assert G.panel_delta(cand, ref)["maps"] == 9


def test_direct_result_rejects_other_opponent():
    with pytest.raises(ValueError):
        G.direct_result(direct([1.0] * 4, opponent="solution92"))
    d = G.direct_result(direct([1.0, 0.0, 1.0, 1.0]))
    assert d["winrate"] == 0.75 and d["games"] == 8


def test_selection_and_pick_choose_at_most_one_best_candidate():
    ref = frame(base(value=0.5) | {"default": [1.0] * 10})
    good = base(value=0.5) | {"default": [1.0] * 10, "sol92_sq": [1.0] * 10}       # R +12,5 pp
    better = base(value=0.5) | {"default": [1.0] * 10, "sol92_sq": [1.0] * 10, "sol92_weak": [1.0] * 10}
    worse_sol = better | {"solution92": [0.0] * 10}                                   # Solution_92 -50 pp
    res = {name: G.selection_checks(ref, frame(c), direct([1.0] * 6 + [0.0] * 4))
           for name, c in (("good", good), ("better", better), ("worse_sol", worse_sol))}
    assert res["good"]["passed"] and res["better"]["passed"]
    assert not res["worse_sol"]["passed"]
    assert G.pick(res) == "better"
    lost = G.selection_checks(ref, frame(better), direct([1.0] * 4 + [0.0] * 6))
    assert not lost["passed"] and G.pick({"x": lost}) is None


def test_confirm_needs_robust_gain_safe_solution92_and_direct_bound():
    n = 40
    ref = frame(base(n, 0.5) | {"default": [1.0] * n})
    cand = base(n, 0.5) | {"default": [1.0] * n, "sol92_sq": [1.0] * n}
    assert G.confirm_checks(ref, frame(cand), direct([1.0] * 30 + [0.0] * 10))["passed"]
    # Direktduell knapp ueber 50 %, aber untere Grenze darunter -> nicht bestanden
    r = G.confirm_checks(ref, frame(cand), direct([1.0] * 21 + [0.0] * 19))
    assert not r["passed"] and not r["checks"]["direkt untere 95%-Grenze > 50 %"]


def test_cli_select_reports_choice(tmp_path, capsys):
    ref, cand, d = tmp_path / "ref.csv", tmp_path / "cand.csv", tmp_path / "d.csv"
    frame(base(value=0.5) | {"default": [1.0] * 10}).to_csv(ref, index=False)
    frame(base(value=0.5) | {"default": [1.0] * 10, "sol92_sq": [1.0] * 10}).to_csv(cand, index=False)
    direct([1.0] * 6 + [0.0] * 4).to_csv(d, index=False)
    assert G.main(["select", str(ref), "L24", str(cand), str(d)]) == 0
    assert "AUSWAHL: L24" in capsys.readouterr().out


def test_direct_opponent_option_checks_against_another_reference(tmp_path, capsys):
    v11 = "self:experiments/releases/20261030_v11_baseline/agent_p0.pth"
    ref, cand, d = tmp_path / "ref.csv", tmp_path / "cand.csv", tmp_path / "d.csv"
    frame(base(value=0.5) | {"default": [1.0] * 10}).to_csv(ref, index=False)
    frame(base(value=0.5) | {"default": [1.0] * 10, "sol92_sq": [1.0] * 10}).to_csv(cand, index=False)
    direct([1.0] * 6 + [0.0] * 4, opponent=v11).to_csv(d, index=False)
    with pytest.raises(ValueError):  # ohne Option wird weiter gegen V10 verlangt
        G.main(["select", str(ref), "X", str(cand), str(d)])
    assert G.main(["select", str(ref), "X", str(cand), str(d), "--direct-opponent", v11]) == 0
    assert "AUSWAHL: X" in capsys.readouterr().out
