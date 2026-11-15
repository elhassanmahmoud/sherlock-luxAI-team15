from pathlib import Path

import pandas as pd
import pytest

from experiments.analysis.umbau_20261115.tools import gates


def panel(candidate):
    external = ["kaggle3","solution92","default"]
    opponents = external + (["self:agents/sherlock/weights/agent_p0.pth"] if candidate else [])
    return pd.DataFrame([
        {"opponent": opp, "seed": seed, "side": side, "steps": 303,
         "result": float(k), "our_wins": 1+k, "opp_wins": 2-k, "our_points": 10, "opp_points": 8}
        for opp in opponents for seed in range(7158000,7158400)
        for k,side in enumerate(("player_0","player_1"))])


@pytest.mark.parametrize("broken", ["duplicate-seat","missing-seat","same-card-missing-in-both",
    "wrong-range","wrong-opponent","other-checkpoint","incomplete-steps","bad-matches","result-disagrees"])
def test_invalid_schedules_never_reach_bootstrap(tmp_path, monkeypatch, broken):
    ref, cand = panel(False), panel(True)
    if broken == "duplicate-seat":
        cand.loc[0, "side"] = cand.loc[1, "side"]
    elif broken == "missing-seat":
        cand = cand.drop(2)
    elif broken == "same-card-missing-in-both":
        ref, cand = (d[d.seed != 7158010] for d in (ref, cand))
    elif broken == "wrong-range":
        cand.loc[cand.seed == 7158000, "seed"] = 7157999
    elif broken == "wrong-opponent":
        ref.loc[ref.opponent == "kaggle3", "opponent"] = "kaggle3-alternative"
    elif broken == "other-checkpoint":
        cand.loc[cand.opponent.str.startswith("self:"), "opponent"] = "self:experiments/some/agent_p0.pth"
    elif broken == "incomplete-steps":
        ref.loc[0, "steps"] = 302
    elif broken == "bad-matches":
        cand.loc[0, "our_wins"] = 0
    else:
        cand.loc[0, "result"] = 1
    paths = [tmp_path / n for n in ("ref.csv","cand.csv")]
    for d,p in zip((ref,cand),paths):
        d.to_csv(p,index=False)
    def unexpected_bootstrap(*args):
        pytest.fail("A malformed panel reached the first bootstrap")
    monkeypatch.setattr(gates,"boot_mean",unexpected_bootstrap)
    with pytest.raises(ValueError):
        gates.main(*paths)


def test_intact_roster_both_v14_filenames_and_unchanged_statistics(tmp_path,monkeypatch,capsys):
    ref,cand = panel(False),panel(True)
    sel = cand.opponent.str.startswith("self:") & (cand.side == "player_1")
    cand.loc[sel,"opponent"] = "self:agents/sherlock/weights/agent_p1.pth"
    # Give the candidate one further game win on each Kaggle map.
    wins = (cand.opponent == "kaggle3") & (cand.side == "player_0")
    cand.loc[wins,["our_wins","opp_wins","result"]] = [2,1,1.]
    paths = [tmp_path/n for n in ("ref.csv","cand.csv")]
    for d,p in zip((ref,cand),paths):
        d.sample(frac=1,random_state=7).to_csv(p,index=False)
    calls = []
    def bootstrap(values,rng):
        calls.append((len(values),float(values.mean()),id(rng)))
        return values.mean(), values.mean()
    monkeypatch.setattr(gates,"boot_mean",bootstrap)
    gates.main(*paths)
    assert [n for n,_,_ in calls] == [400]*4
    assert [avg for _,avg,_ in calls] == pytest.approx([.5,1/6,0.,.5])
    assert len({rng_id for _,_,rng_id in calls}) == 1
    assert "1: ja, 2: ja, 3: nein, 4: nein" in capsys.readouterr().out
