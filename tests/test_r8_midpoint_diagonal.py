from scripts.r8_midpoint_diagonal import MIDPOINT,MidpointDiagonalAgent
from scripts.r8_midpoint_diagonal_audit import gates,rename
from scripts import r8_midpoint_diagonal as policy
import pytest


def group(dual,diagonal,single):
    return dict(dual_correct=dual,diagonal_correct=diagonal,single_correct=single)


def test_strictness_applies_across_holdouts_and_pooled_midpoint():
    assert all(gates(group(15,15,16),group(12,11,11)).values())
    assert not all(gates(group(15,15,15),group(12,12,12)).values())
    assert not all(gates(group(15,16,14),group(12,11,11)).values())
    assert not all(gates(group(15,15,18),group(12,11,12)).values())


def test_keeps_paired_gain_loss_roles_well_defined():
    raw=dict(rows=11,r3_correct=6,control_correct=7,r8_correct=8,r8_gained_over_r3=3,r8_lost_from_r3=1,
             r8_gained_over_control=2,r8_lost_from_control=1,actual_r3_correct=4)
    result=rename(raw)
    assert result["dual_correct"]==8 and result["dual_gained_over_single"]==2
    assert result["played_original_parent_correct"]==4
    with pytest.raises(ValueError): rename(dict(raw,r8_gained_over_control=3))


def test_frozen_single_checkpoint_and_identical_two_view_policy(monkeypatch,tmp_path):
    class Fake:
        arch={"feat_dim":79,"in_ch":16}
    original=Fake()
    def start(self,*args,**kwargs):
        self.members=[original]
        self.sap_own_tile=True
    monkeypatch.setattr(policy.SelectiveAdviceAgent,"__init__",start)
    monkeypatch.setattr(policy,"digest",lambda _:MIDPOINT)
    agent=MidpointDiagonalAgent(advice_path=tmp_path/"midpoint.pth")
    assert len(agent.members)==1 and isinstance(agent.members[0],policy.TwoViews) and agent.members[0].net is original
    with pytest.raises(ValueError): MidpointDiagonalAgent(advice_path=tmp_path/"midpoint.pth",mode="combat")
