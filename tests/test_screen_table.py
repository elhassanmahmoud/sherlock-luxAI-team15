"""Dev-A-Screens nebeneinander (scripts/screen_table.py, 30.10.2026)."""
import pandas as pd
import pytest

from scripts import league_gates as G
from scripts import screen_table as S

RL = list(S.SIX)[2:4]
HOLD = list(S.SIX)[4:]


def write(path, opponents, value, n=4):
    pd.DataFrame([dict(opponent=o, seed=800000 + i, side=side, result=value)
                  for o in opponents for i in range(n) for side in ("player_0", "player_1")]).to_csv(path, index=False)


def screen_files(d, prefix, value, rl=None, hold=None):
    write(d / f"{prefix}.csv", ["solution92", "sol92_sq"], value)
    write(d / f"{prefix}_rl.csv", RL, value if rl is None else rl)
    write(d / f"{prefix}_hold.csv", HOLD, value if hold is None else hold)


def test_table_pairs_against_v10_and_base_and_marks_missing_screens(tmp_path):
    write(tmp_path / "B_V10_dev800.csv", ["solution92", "sol92_sq", "default"], 0.0)  # default nicht im Screen
    write(tmp_path / "B_V10_rl.csv", RL, 0.0)
    write(tmp_path / "B_V10_hold.csv", HOLD, 0.0)
    screen_files(tmp_path, "D_mix36b", 0.5)
    screen_files(tmp_path, "D_x", 1.0)
    write(tmp_path / "D_x_direct.csv", [G.V10_REF], 1.0)
    lines = S.table(["mix36b", "x", "fehlend"], d=tmp_path)
    rows = {ln.split(" | ")[0][2:]: ln.split(" | ")[1:] for ln in lines[2:]}
    assert rows["V10"][6:] == ["0.0", "–", "–", "– |"]
    assert rows["mix36b"][6:] == ["50.0", "+50.00 [+50.00; +50.00]", "–", "– |"]
    assert rows["x"] == ["100.0"] * 7 + ["+100.00 [+100.00; +100.00]", "+50.00 [+50.00; +50.00]",
                                         "100.0 [100.0; 100.0] |"]
    assert rows["fehlend"] == ["fehlt"] * 9 + ["fehlt |"]


def test_admission_needs_both_point_estimates_and_keeps_the_best_three(tmp_path):
    # (Sol92/sq, RL, zurueckgehalten) -> Mittel 6; Massstab mix36b: Mittel 0,5, direkt 0,5
    for name, parts, direct in [("mix36b", (0.5, 0.5, 0.5), 0.5), ("hoch", (1, 1, 0.5), 0.5),
                                ("gleich", (0.5, 0.5, 0.5), 0.5), ("schwach_direkt", (1, 1, 1), 0.0),
                                ("schwach_mittel", (0, 0.5, 0.5), 1.0), ("a", (1, 1, 1), 1.0),
                                ("b", (1, 0.5, 0.5), 1.0)]:
        screen_files(tmp_path, f"D_{name}", *parts)
        write(tmp_path / f"D_{name}_direct.csv", [G.V10_REF], direct)
    names = ["hoch", "gleich", "schwach_direkt", "schwach_mittel", "a", "b"]
    assert S.admitted(names, d=tmp_path) == ["a", "hoch", "b"]
    assert S.admitted(["gleich", "schwach_mittel"], d=tmp_path) == ["gleich"]
    with pytest.raises(SystemExit, match="unvollstaendig"):
        S.admitted(["hoch", "fehlend"], d=tmp_path)
