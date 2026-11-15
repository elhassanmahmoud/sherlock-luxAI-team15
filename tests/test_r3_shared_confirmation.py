import pytest

from scripts import r3_shared_confirmation as study


def fixed_replay():
    return {(o,s,p):(1,2,1,100,200,303) for s in study.MAPS[:4] for p in study.SEATS for o in study.OPPONENTS}


def test_reproduction_checks_both_opponents_seats_and_exact_final_points():
    prior = fixed_replay()
    study.replay_gate(prior, dict(prior))
    changed = dict(prior)
    key = ("kaggle3",7158003,"player_1")
    changed[key] = (1,2,1,100,201,303)
    diagnosis = study.replay_diagnosis(prior, changed)
    assert diagnosis["solution92"] == {"games":8,"identical":8,"differences":[]}
    assert diagnosis["kaggle3"]["identical"] == 7
    assert diagnosis["kaggle3"]["differences"][0]["local"]["opp_points"] == 201
    with pytest.raises(ValueError, match="V14 mismatch"):
        study.replay_gate(prior, changed)
    del changed[key]
    with pytest.raises(ValueError, match="16 reproduction"):
        study.replay_gate(prior, changed)


def test_same_map_both_opponents_stay_together_for_interval():
    base = {}
    r3 = {}
    for seed in range(4):
        for seat in study.SEATS:
            k=("kaggle3",seed,seat)
            s=("solution92",seed,seat)
            win=(1,2,1,0,0,303)
            loss=(0,1,2,0,0,303)
            base[k],r3[k]=((win,loss) if seed<2 else (loss,win))
            base[s],r3[s]=r3[k],base[k]
    result=study.paired(base,r3,range(4))
    assert result["external"]["ci95"]==[0.,0.]
    assert result["external"]["match_ci95"]==[0.,0.]
    for d in result["by_opponent"].values():
        assert len(d["gained"])==len(d["lost"])==4
        assert d["ci95"][0]<0<d["ci95"][1]
