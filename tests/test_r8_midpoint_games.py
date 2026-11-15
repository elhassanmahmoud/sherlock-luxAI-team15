"""Synthetic policy-threshold and keyset regressions; no game or model required."""
from types import SimpleNamespace

import pytest

from scripts import r8_midpoint_games as study


def test_rosters():
    phases = []
    for stage,n in (("screen",224),("confirm",600)):
        layouts = study.blocks(stage)
        jobs = {(arm, opp, seed, seat) for arm,(seeds,foes) in layouts.items()
                for seed in seeds for opp in foes for seat in study.SEATS}
        assert len(jobs) == n
        phases.append({row[2] for row in jobs})
    assert phases[0] == set(range(7170230,7170246))
    assert phases[1] == set(range(7170300,7170360)) | set(range(7170400,7170460))
    assert phases[0].isdisjoint(phases[1])
    assert "r3" not in study.blocks("confirm")


@pytest.mark.parametrize("kaggle,solution,baseline,passes", [
    (1,1,True,False), (2,1,True,True), (3,0,True,False), (2,1,False,False)])
def test_r3_gates_preserve_v14_gates(kaggle,solution,baseline,passes):
    seeds = range(2)
    def run_counts(wins):
        games = {(opp,seed,side): {"result": int(2*seed+i < wins[opp])}
                 for opp in study.OPPONENTS for seed in seeds for i,side in enumerate(study.SEATS)}
        return SimpleNamespace(games=games,hashes={})
    ref = run_counts({"kaggle3":1,"solution92":1})
    candidate = run_counts({"kaggle3":kaggle,"solution92":solution})
    result = {"gates":{"remaining_v14_gates":baseline}}
    study.add_screen_gates(result,ref,candidate,seeds)
    assert result["game_gates_pass"] is passes


def test_false_or_modified_selection_rejected(tmp_path,monkeypatch):
    dst = tmp_path/"screen"
    dst.mkdir()
    (dst/"assessment.json").write_text('{"game_gates_pass":true, "key":1}')
    for passed,key in ((False,1),(True,2)):
        monkeypatch.setattr(study,"report",lambda *args: {"game_gates_pass":passed,"key":key})
        with pytest.raises(ValueError,match="224-game"):
            study.qualified_selection(None,tmp_path)
