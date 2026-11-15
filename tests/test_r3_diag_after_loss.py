"""Synthetic two-seat prefix, reset and exact panel-roster contracts without loading any weights."""
from collections import Counter
from unittest.mock import patch

from scripts.r3_diagonal import DiagonalAgent
from scripts.r3_diag_after_loss import AfterLossAgent
from scripts import r3_diag_after_loss_games as study


def test_public_first_match_is_the_only_latch():
    old, base=object(),object()
    with patch.object(DiagonalAgent,"_advise",return_value=old):
        for side in (0,1):
            for lose in (False,True):
                actor=AfterLossAgent.__new__(AfterLossAgent)
                actor.team_id=side
                with patch.object(DiagonalAgent,"_reset_episode_state"):
                    actor._reset_episode_state()
                actor.selective_counts=Counter()
                first=[0,0]; first[1-side if lose else side]=1
                for t in range(303):
                    wins=[0,0] if t<101 else (first if t<202 else [1,1])
                    got=actor._advise(t,{"team_wins":wins},base)
                    assert got is (base if lose and t>=101 else old)
                assert actor.selective_counts["fallback_calls"]==(202 if lose else 0)
                with patch.object(DiagonalAgent,"_reset_episode_state"):
                    actor._reset_episode_state()
                assert actor.first_match_lost is None


def test_phase_keys():
    assert len(set(study.jobs("diagnose","after_loss")))==11
    assert set(study.jobs("diagnose","diagonal"))==set(study.CONTROL)
    assert {k[2] for k in study.CONTROL}==set(study.SEATS)
    for stage,count in (("screen",224),("confirm",600),("solution",96)):
        assert sum(len(study.jobs(stage,k)) for k in study.layout(stage))==count
    assert set(study.layout("screen")["after_loss"][0]).isdisjoint(study.layout("confirm")["after_loss"][0])
    assert set(study.layout("confirm")["after_loss"][0]).isdisjoint(study.layout("confirm")["direct"][0])
