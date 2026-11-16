"""Small archive/roster and native-random checks for the separate 80-game comparison."""
import hashlib

import pytest

from scripts import v15_ft18_random as study


def fake_rows():
    return {k: {"opponent":k[0],"seed":k[1],"side":k[2],"result":0,"game_win":0,
                "our_wins":0,"opp_wins":3,"our_points":0,"opp_points":5,"steps":303,"point_counting_version":2,
                "opponent_source":"scripts.common.RandomAgent" if k[0]=="random" else "historical_ft18_18_35",
                "random_stream_sha256":hashlib.sha256(b"fixture").hexdigest() if k[0]=="random" else None}
            for k in study.KEYS}


def test_schedules_and_paired_match_denominators():
    v14=fake_rows()
    v15=fake_rows()
    assert len(v14)==40 and set(study.MAPS["ft18"]).isdisjoint(study.MAPS["random"])
    key=("ft18",7170064,"player_0")
    v15[key].update(result=1,game_win=1,our_wins=2,opp_wins=1)
    for k,row in v15.items():
        study.validate_row(row,k)
    ft=study.compare_scores(v14,v15,"ft18")
    assert ft["games"]["total"]==24 and ft["matches"]["total"]==72
    assert ft["games"]["delta"]==pytest.approx(1/24) and ft["matches"]["delta"]==pytest.approx(2/72)
    assert ft["gained"]==[(7170064,"player_0")] and not ft["lost"]
    r=study.compare_scores(v14,v15,"random")
    assert r["games"]["total"]==16 and r["matches"]["total"]==48
    v15["random",7170076,"player_1"]["random_stream_sha256"]="1"*64
    with pytest.raises(ValueError,match="Random opponent differed"):
        study.compare_scores(v14,v15,"random")


def test_native_random_is_checked_without_a_second_actor_call():
    from scripts.common import make_opponent
    rival=make_opponent("random","player_1")
    monitor=study.RandomStream(rival)
    for t in range(3):
        assert rival.act(t,{}).shape==(16,3)
    assert monitor.calls==3
    with pytest.raises(ValueError,match="stream"):
        rival.act(4,{})
