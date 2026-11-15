from collections import Counter

import numpy as np
import pytest
import torch

from scripts import imitate, temporal_movement_agreement as audit
from scripts.selective_agreement import count_agreement


def test_near_is_chebyshev_three_inclusive_single_current_enemy_on_confirmed_tile():
    boards = torch.zeros((2,17,24,24), dtype=torch.int8)
    for x,y in ((0,0),(12,12),(20,20)):
        boards[:,0,x,y] = 127
        boards[:,10,x,y] = 32
        boards[1,16,x,y] = 95  # Previously occupied by several is allowed.
    boards[1,10,12,12] = 64  # Two enemies now.
    boards[1,0,20,20] = 0    # Unconfirmed tile.
    rows = dict(pos=torch.tensor([[0,0],[3,3],[4,0],[12,12],[20,20],[23,23]]),
                step=torch.tensor([0,1,1,1,1,1]))
    assert audit.near_rows(boards,rows).tolist() == [False,True,False,False,False,False]


def test_shared_clock_clears_between_archived_games_gaps_and_matches():
    frames = np.array([1,2,4,100,102,103])
    current = np.zeros((6,16,24,24), np.int8)
    current[:,10,2,4] = [32,64,95,127,32,64]
    previous = audit.archived_boards(dict(planes=current,global_step=frames))
    assert previous[:,16,2,4].tolist() == [0,32,0,0,0,32]
    assert torch.equal(previous[:,:16],torch.from_numpy(current))
    bad = current.copy()
    bad[2,10,4,5] = 1
    with pytest.raises(ValueError,match="occupancy code"):
        audit.archived_boards(dict(planes=bad,global_step=frames))


def test_paired_counts_only_use_model_inputs_and_leave_base_saps_alone():
    class Fixed:
        def __init__(self, channels): self.channels = channels
        def forward_all(self, maps, step, pos, features):
            assert maps.shape == (2,self.channels,24,24)
            # The first unit in frame 1 only moves if the model receives its previous board.
            action = torch.ones(len(pos),dtype=torch.long)
            if self.channels == 17:
                action[(pos[:,0] == 3) & (maps[step,16,0,0] > 0)] = 2
            action[pos[:,0] == 4] = 5  # A proposed shot must never override a stay.
            logits = torch.full((len(pos),6),-10.)
            logits[torch.arange(len(pos)),action] = 10.
            logits[pos[:,0] == 7] = 0.  # Uncertain, leave V14's command.
            return logits,None,None
    maps = torch.zeros((2,17,24,24),dtype=torch.int8)
    maps[1,16,0,0] = 32
    rows = dict(step=torch.tensor([0,1,1,1,1]), pos=torch.tensor([[1,0],[3,0],[4,0],[6,0],[7,0]]),
                feats=torch.zeros((5,79)), mask=torch.ones((5,6),dtype=torch.bool),
                act=torch.tensor([1,2,5,1,3]), base_act=torch.tensor([0,0,0,5,3]))
    near = torch.tensor([False,True,True,False,False])
    r2 = count_agreement([Fixed(16)],maps[:,:16],rows,near=near)
    r4 = count_agreement([Fixed(17)],maps,rows,near=near)
    assert (r2["all"]["changed"],r4["all"]["changed"]) == (2,2)
    assert (r2["near"]["rows"],r2["near"]["helped"],r4["near"]["helped"]) == (2,0,1)
    assert r4["all"]["helped"] == 2 and r4["all"]["hurt"] == 0
    rows["act"].fill_(4)
    alternate = count_agreement([Fixed(17)],maps,rows,near=near)
    assert alternate["all"]["changed"] == r4["all"]["changed"]
    assert alternate["all"]["helped"] == 0


def test_freeze_uses_count_ratio_without_rounding_and_separate_original_group():
    def counts(net, hurt): return Counter(helped=hurt+net,hurt=hurt)
    game = dict(r2=dict(all=counts(10,10),near=counts(4,2)),
                r4=dict(all=counts(10,11),near=counts(5,1)))
    mixed = audit.combine([game])
    assert audit.selection_gate(mixed)["pass_offline"]
    for group,key,value in (("all","hurt",12),("near","net",4),("all","net",9)):
        changed = {m:{g:v.copy() for g,v in by.items()} for m,by in mixed.items()}
        changed["r4"][group][key] = value
        assert not audit.selection_gate(changed)["pass_offline"]
    mixed["r2"]["all"]["hurt"],mixed["r4"]["all"]["hurt"] = 0,1
    assert not audit.selection_gate(mixed)["pass_offline"]


def test_t0_failure_stops_before_optimizer(monkeypatch):
    from agents.sherlock.imitation_net import ImitationNet
    net = ImitationNet(79,ch=4,blocks=1,hidden=8)
    original = imitate.add_previous_enemy_input
    def corrupt(net):
        original(net)
        with torch.no_grad(): net.pi.bias.add_(1)
    monkeypatch.setattr(imitate,"add_previous_enemy_input",corrupt)
    with pytest.raises(AssertionError):
        imitate.verify_initial_history_outputs(net)


def test_checkpoints_bind_holdout_pairs_and_original_r2_checksum(tmp_path):
    inputs = {}
    for name,plan in (("original",audit.make_plan(7271000,32,7271032,8)),
                      ("mixed",audit.make_plan(7272000,120,7272200,24))):
        inputs[name] = {split:[dict(seed=seed,side=side,sha256="c"*64,protocol="p"*64)
                                for seed,side in keys] for split,keys in plan.items()}
    arch = dict(feat_dim=79,n_actions=6,in_ch=16,ch=32,blocks=3,hidden=128,detach_value=True,sap_head=True)
    base = dict(kind="imitation",arch=arch,epochs=5,sap_own_tile=True,
                selective_training=dict(parent_sha256="b"*64,inputs=inputs))
    parity = dict(device="cpu",rtol=1e-5,atol=1e-6,max_abs_by_head=[0.,0.,0.])
    r2,r4 = tmp_path/"r2.pth",tmp_path/"r4.pth"
    def save_pair():
        torch.save(base,r2)
        candidate = dict(**base["selective_training"],previous_enemy_r2_sha256=audit.collect.file_sha(r2),
                         initial_parity=parity)
        torch.save({**base,"arch":{**arch,"in_ch":17},"kind":audit.HISTORY_KIND,"selective_training":candidate},r4)
    save_pair()
    assert audit.paired_inputs(r2,r4)[0] == inputs
    torch.save({**base,"unrelated_source":True},r2)
    with pytest.raises(ValueError,match="another R2"):
        audit.paired_inputs(r2,r4)
    inputs["mixed"]["val"][1] = inputs["mixed"]["val"][0]
    save_pair()
    with pytest.raises(ValueError,match="duplicate mixed/val"):
        audit.paired_inputs(r2,r4)
