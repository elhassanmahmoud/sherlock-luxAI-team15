import numpy as np
import pytest

from agents.sherlock import own_command as oc
from agents.sherlock import geometry as geo


@pytest.mark.parametrize("team", [0, 1])
def test_previous_issued_canonical_command_and_continuity(team):
    # Actual reported course frames include missing UID 1 at step 9. Both UID 0 positions after gap are outside spawn.
    frame = np.array([7,7,8,8,9,10,10,12,100,102,103,104,105,106])
    uid = np.array([0,1,0,1,0,0,1,0,0,0,0,0,0,0])
    pos = np.array([(2,2),(3,3),(3,2),(3,3),(3,2),(4,2),(3,3),(4,2),
                    (4,2),(7,7),(0,0),(1,0),(1,0),(5,5)])
    issued = np.array([2,5,2,5,2,0,0,1,5,1,2,0,0,3])
    steps, board = np.unique(frame, return_inverse=True)
    archive = dict(global_step=steps, step=board, mstep=frame % 101, uid=uid, pos=pos,
                   base_act=np.zeros(len(uid), int), played_act=issued, act=np.full(len(uid), 4))
    features = oc.archive_features(archive)
    assert [row.argmax() if row.any() else -1 for row in features] == [-1,-1,2,5,2,2,-1,-1,-1,-1,-1,-1,0,-1]
    # The source action was emitted in world coordinates, independently mirrored for seat 1.
    state = oc.PlayedCommands()
    for s in steps:
        idx = np.flatnonzero(frame == s)
        np.testing.assert_array_equal(state.features(s, s%101, uid[idx], pos[idx]), features[idx])
        native = np.zeros((16, 3), int)
        for row in idx:
            a = issued[row]
            native[uid[row],0] = geo.mirror_dir(a) if team and a != geo.SAP else a
        state.record(s, s%101, uid[idx],pos[idx],native,bool(team))
    archive.pop("played_act")
    archive["base_act"] = issued
    archive["act"][:] = 5
    np.testing.assert_array_equal(oc.archive_features(archive), features)


def test_input_widening_preserves_rng_and_existing_parameters_and_receives_gradients():
    import torch
    from agents.sherlock.imitation_net import ImitationNet
    from scripts.own_command_study import widen_and_check
    torch.manual_seed(2711)
    net = ImitationNet(feat_dim=79,ch=8,blocks=1,hidden=32)
    old = {k: v.clone() for k,v in net.state_dict().items()}
    rng = torch.get_rng_state()
    record = widen_and_check(net)
    assert len(record["max_abs_by_head"]) == 3 and torch.equal(rng, torch.get_rng_state())
    for k,v in net.state_dict().items():
        if k == "unit.0.weight":
            assert torch.equal(v[:, :79], old[k]) and not v[:, 79:].count_nonzero()
        else:
            assert torch.equal(v, old[k])
    x = torch.zeros(1,85)
    x[0,82] = 1
    net.unit[0](x).sum().backward()
    assert torch.all(net.unit[0].weight.grad[:,82] == 1)


@pytest.mark.parametrize("seat", [0,1])
def test_movement_adviser_records_final_return_value(monkeypatch,seat):
    from types import SimpleNamespace
    from agents.sherlock.main import Agent_x
    from scripts.selective_advice_agent import SelectiveAdviceAgent
    actor = object.__new__(SelectiveAdviceAgent)
    actor.own_command_input = True
    actor.belief = SimpleNamespace(mirrored=bool(seat))
    actor.played_commands = oc.PlayedCommands()
    actor._prev_ctx = dict(ally_ids=[0,1], ally_ene=np.array([40,-1]), ally_pos=np.array([(3,3),(5,5)]))
    base = np.zeros((16,3),int)
    played = base.copy()
    played[:2,0] = geo.UP if seat else geo.RIGHT
    monkeypatch.setattr(Agent_x,"_act",lambda self,step,obs: base)
    monkeypatch.setattr(actor,"_advise",lambda step,obs,proposal: played)
    obs = dict(steps=11, match_steps=11)
    assert actor._act(11,obs) is played
    bits = actor.played_commands.features(12,12,[0,1],np.array([(4,3),(5,5)]))
    assert bits[0].tolist() == [0,0,1,0,0,0] and not bits[1].any()
    actor._prev_ctx = None
    actor._act(101,dict(steps=101,match_steps=0))
    assert not actor.played_commands.features(102,1,[0],np.array([(4,3)])).any()


def test_paired_screen_counts_only_true_previous_command_rows(tmp_path):
    from types import SimpleNamespace
    import torch
    from scripts.selective_agreement import measure
    path = tmp_path / "example.npz"
    # Only observation #2 has a preceding live row in the same match and outside spawn.
    np.savez(path, planes=np.zeros((3,16,24,24),np.int8), global_step=[7,8,10], mstep=np.array([7,8,10]),
             step=np.arange(3), uid=np.zeros(3,int), pos=np.array([[2,2],[3,2],[4,2]]),
             feats=np.zeros((3,79),np.float16), mask=np.ones((3,6),bool), act=np.array([2,2,0]),
             sdx=np.zeros(3,int), sdy=np.zeros(3,int), base_act=np.zeros(3,int), played_act=np.array([2,2,2]))
    def always_right(planes,step,pos,features):
        scores = torch.zeros(len(pos),6)
        scores[:,2] = 10.
        return scores, None, None
    heads = [SimpleNamespace(arch={"feat_dim":79},forward_all=always_right)]
    counts = measure(heads,path,with_history_scope=True)
    assert (counts["rows"],counts["helped"],counts["hurt"]) == (3,2,1)
    assert (counts["history_rows"],counts["history_helped"],counts["history_hurt"]) == (1,1,0)


@pytest.mark.parametrize("net,known,hurt,criteria", [
    (20, 13, 11, (True, True, True)),    # Global tie is sufficient when known-history net improves.
    (21, 11, 10, (False, True, True)),   # Overall gain cannot compensate a loss on known histories.
    (19, 13, 10, (True, False, True)),
    (21, 13, 12, (True, True, False)),
    (21, 12, 10, (False, True, True)),   # Known-history tie fails the strictly-positive requirement.
])
def test_three_preregistered_own_command_gates(net,known,hurt,criteria):
    from scripts.own_command_study import offline_gate
    control = dict(net=20,history_net=12,hurt=10)
    candidate = dict(net=net,history_net=known,hurt=hurt)
    checks = offline_gate({"r2":control,"own_command":candidate})
    assert tuple(checks.values()) == criteria
