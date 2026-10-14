"""Paired seed clusters, matching cohorts and invalid input at report boundary."""
import sys

import numpy as np
import pandas as pd
import pytest

from scripts import compare_report as report


def results(values, seeds=None, opponent="default"):
    seeds = range(len(values)) if seeds is None else seeds
    return pd.DataFrame([
        dict(opponent=opponent, seed=seed, side=f"player_{side}", result=value)
        for seed, pair in zip(seeds, values) for side, value in enumerate(pair)
    ])


def test_cli_keeps_opposite_side_differences_together(tmp_path, monkeypatch, capsys):
    candidate, reference = tmp_path / "candidate.csv", tmp_path / "reference.csv"
    results([(1, 0), (1, 0)]).to_csv(candidate, index=False)
    results([(0, 1), (0, 1)]).to_csv(reference, index=False)
    monkeypatch.setattr(sys, "argv", ["compare_report", "--ref", str(reference), str(candidate)])
    report.main()
    out = capsys.readouterr().out
    # Every map has exactly zero average difference. Bootstrapping whole
    # maps can NEVER produce a nonzero interval, unlike independent sides.
    assert "[+0.000; +0.000]" in out
    assert "Karten" in out and "Spiele" in out


def test_cluster_interval_against_exact_two_map_distribution():
    candidate = results([(0, 0), (1, 1)])
    reference = results([(1, 1), (0, 0)])
    row = report.compare_results(candidate, reference)[0]
    # Four equiprobable resamples: [-1,-1], [-1,+1], [+1,-1], [+1,+1].
    assert row["delta"] == 0
    assert (row["low"], row["high"]) == (-1, 1)
    assert row["maps"] == 2 and row["games"] == 4


def test_wr_and_delta_use_same_shared_maps_and_report_exclusions():
    candidate = results([(1, 1), (0, 0), (1, 1)], seeds=[0, 1, 2])
    reference = results([(0, 0), (0, 0), (1, 1)], seeds=[0, 1, 3])
    row = report.compare_results(candidate, reference)[0]
    assert row["maps"] == 2 and row["games"] == 4
    assert row["winrate"] == .5 and row["ref_winrate"] == 0 and row["delta"] == .5
    assert row["excluded_candidate"] == 1 and row["excluded_reference"] == 1


def test_pairing_is_by_seed_side_and_opponent_not_row_order():
    a = results([(1, 0), (.5, 1), (0, 1)])
    b = results([(0, .5), (1, 0), (1, 1)])
    expected = report.compare_results(a, b)
    assert report.compare_results(a.sample(frac=1, random_state=2),
                                  b.sample(frac=1, random_state=7)) == expected
    combined = pd.concat([a.assign(opponent="solution92"), a])
    refs = pd.concat([b, b.assign(opponent="solution92")])
    both = report.compare_results(combined, refs)
    assert both[0] == expected[0]
    assert both[1] == {**expected[0], "opponent": "solution92"}


def test_single_shared_map_does_not_claim_estimated_uncertainty():
    row = report.compare_results(results([(1, 0)]), results([(0, 0)]))[0]
    assert row["delta"] == .5
    assert row["low"] is None and row["high"] is None


@pytest.mark.parametrize("bad", ["duplicate", "missing_side", "invalid_side", "nan", "infinite", "bad_result", "missing_column", "empty", "bad_seed"])
@pytest.mark.parametrize("which", ["candidate", "reference"])
def test_invalid_inputs_are_rejected(bad, which):
    good = results([(1, 0), (0, 1)])
    damaged = good.copy()
    if bad == "duplicate":
        damaged = pd.concat([damaged, damaged.iloc[:1]])
    elif bad == "missing_side":
        damaged = damaged.iloc[1:]
    elif bad == "invalid_side":
        damaged.loc[0, "side"] = "player_2"
    elif bad in ("nan", "infinite", "bad_result"):
        damaged["result"] = damaged["result"].astype(float)
        damaged.loc[0, "result"] = {"nan": np.nan, "infinite": np.inf, "bad_result": .7}[bad]
    elif bad == "missing_column":
        damaged = damaged.drop(columns="result")
    elif bad == "empty":
        damaged = damaged.iloc[:0]
    elif bad == "bad_seed":
        damaged["seed"] = -1
    a, b = (damaged, good) if which == "candidate" else (good, damaged)
    with pytest.raises(ValueError):
        report.compare_results(a, b)


@pytest.mark.parametrize("mismatch", ["seeds", "opponent"])
def test_no_shared_games_are_rejected(mismatch):
    a, b = results([(1, 0)]), results([(1, 0)])
    if mismatch == "seeds":
        b["seed"] = 99
    else:
        b["opponent"] = "solution92"
    with pytest.raises(ValueError):
        report.compare_results(a, b)


def test_cli_rejects_invalid_csv_before_printing_partial_results(tmp_path, monkeypatch, capsys):
    good, bad = tmp_path / "good.csv", tmp_path / "bad.csv"
    results([(1, 0), (0, 1)]).to_csv(good, index=False)
    results([(1, 0)]).iloc[:1].to_csv(bad, index=False)
    monkeypatch.setattr(sys, "argv", ["compare_report", "--ref", str(good), str(good), str(bad)])
    with pytest.raises(SystemExit) as error:
        report.main()
    assert error.value.code == 2
    output = capsys.readouterr()
    assert not output.out
    assert "bad.csv" in output.err
