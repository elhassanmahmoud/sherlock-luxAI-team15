import json
import pytest
from scripts import r3_v4_mixed_duel as duel


def test_early_reproductions_include_wins_losses_both_sides():
    expected={}
    for arm,(win,loss) in duel.SELECTION.items():
        rows={(s,p):dict(result=int(s==win),points=123,opp_points=100,wins=2 if s==win else 1,
                         losses=1 if s==win else 2,steps=303) for s in (win,loss) for p in duel.SEATS}
        expected.update(duel.selection(rows,arm))
    check=[dict(arm=arm,seed=s,side=p,opponent="historical_v14",updates={p:303},**r)
           for (arm,s,p),r in expected.items()]
    assert len(check)==8 and duel.check_replays(check,expected)==[]
    check[6]["opp_points"]+=1
    assert len(duel.check_replays(check,expected))==1
    with pytest.raises(ValueError):
        duel.check_replays(check[:-1],expected)


def test_card_interval_keeps_opposing_seats_together(tmp_path):
    path=tmp_path/"games.jsonl"
    with path.open("w") as f:
        for s in duel.MAPS:
            for side in duel.SEATS:
                a=int(side=="player_0")
                matches=[dict(winner="player_0",world_points=[3,1]) for _ in range(3)]
                row=dict(arm="r3",opponent="v4",seed=s,side=side,steps=303,result=a,wins=3*a,losses=3*(1-a),
                         points=9 if a else 3,opp_points=3 if a else 9,matches=matches,updates=dict.fromkeys(duel.SEATS,303))
                f.write(json.dumps(row)+"\n")
    report=duel.assessment(path)
    assert report["r3_wins"]==24 and report["paired_card_ci95"]==[.5,.5]
    assert report["map_two_one_zero"]==[0,24,0]
