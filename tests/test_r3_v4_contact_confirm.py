from types import SimpleNamespace

import pytest

from scripts.r3_v4_contact_confirm import DIRECT,EXTERNAL,canonical,panel,verify_row
from scripts.r3_v4_contact_confirm_assess import parents,primary,sealed_primary


def fixtures(phase, same_parents=False):
    rows={}
    for k in panel(phase):
        arm,opp,seed,seat=k
        won=arm=="contact" or same_parents and arm in ("r3","v4")
        rows[k]={"game":dict(game_win=int(won),our_wins=2 if won else 1,opp_wins=1 if won else 2,
                             our_points=5,opp_points=5,steps=303)}
    return rows


def test_exact_disjoint_whole_cards_and_sizes():
    assert not set(EXTERNAL)&set(DIRECT)
    for phase,expected in (("v14",600),("parents",480)):
        keys=set(panel(phase))
        a,b=set(panel(phase,0)),set(panel(phase,1))
        assert a.isdisjoint(b) and a|b==keys and len(keys)==expected
        assert {k[2] for k in a}.isdisjoint({k[2] for k in b})
    assert set(panel("v14")).isdisjoint(panel("parents"))


def test_direct_half_and_solution_regression_block_primary():
    rows=fixtures("v14")
    assert primary(rows)["v14_advantage_confirmed"]
    for (arm,opp,seed,seat),r in rows.items():
        if opp=="v14":
            r["game"]["game_win"]=int(seat=="player_0")
    assert not primary(rows)["primary_gates"]["direct_lower_bound_above_half"]
    for (arm,opp,seed,seat),r in rows.items():
        if opp=="solution92":
            r["game"]["game_win"]=int(arm=="v14")
    assert not primary(rows)["primary_gates"]["solution_at_least_v14"]


def test_equal_parent_intervals_do_not_cancel_v14_result():
    base=fixtures("v14")
    assert primary(base)["v14_advantage_confirmed"]
    r=parents(base|fixtures("parents",same_parents=True))
    assert not r["beats_both_parents_externally"]
    for p in ("r3","v4"):
        assert r["comparisons"][p]["combined"]["difference_ci95"]==[0.,0.]
    assert primary(base)["totals"]["contact"]["solution_target"]["both_wins"]==60


def test_any_changed_raw_game_is_rejected():
    k=panel("parents")[0]
    row=dict(zip(("arm","opponent","seed","side"),k),**fixtures("parents")[k],routing={},run_sha256="s")
    row["row_sha256"]=canonical(row)
    verify_row(row,k,"s")
    row["game"]["our_points"]+=1
    with pytest.raises(ValueError,match="payload"):
        verify_row(row,k,"s")
