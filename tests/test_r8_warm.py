from collections import Counter

import numpy as np

from scripts.r8_warm import HalfBatch, ROTATION, SIDES
from scripts.r8_warm_assess import gates


def test_realized_128_rows_are_balanced_repeatable_and_cover_each_archive():
    records = [dict(opponent=opponent, side=side) for _ in range(16) for opponent in ROTATION for side in SIDES]
    pools = [100*j+np.arange(j%17+22) for j in range(len(records))]
    a,b = [HalfBatch(records,pools,2711) for _ in range(2)]
    hits=Counter()
    for k in range(16):
        chosen=a.draw(k)
        np.testing.assert_array_equal(chosen,b.draw(k))
        assert len(chosen)==len(set(chosen))==128
        maps=chosen//100
        hits.update(set(maps))
        by_side=Counter(records[j]["side"] for j in maps)
        by_opp=Counter(records[j]["opponent"] for j in maps)
        assert sorted(by_side.values())==[64,64]
        assert sorted(by_opp.values())==[42,43,43]
        assert all(int(i) in pools[int(i//100)] for i in chosen)
    assert len(hits)==96 and set(hits.values())=={1}
    assert a.summary()==b.summary()


def test_fixed_gates_ignore_observed_sensitivity_and_reject_tied_new_control():
    old=dict(r8_correct=4,r3_correct=4)
    new=dict(r8_correct=5,r3_correct=4,control_correct=4,actual_r3_correct=7)
    assert all(gates(old,new).values())
    assert not all(gates(old,{**new,"control_correct":5}).values())
    assert not all(gates(old,{**new,"r3_correct":5}).values())
    assert not all(gates({**old,"r8_correct":3},new).values())


def test_batch_shares_frames_and_keeps_frame_to_unit_mapping():
    import torch
    from scripts.r8_warm import loss_for

    class Probe(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.logits=torch.nn.Parameter(torch.zeros(6))

        def forward_all(self,frames,inv,pos,feats):
            assert len(frames)==2 and inv.tolist()==[1,0,1]
            assert torch.allclose(frames[:,0,0,0],torch.tensor([3.,7.])/127.)
            return self.logits.expand(3,6),None,torch.zeros(2,24,24)

    b=torch.zeros((5,16,24,24),dtype=torch.int8)
    b[1]=3
    b[4]=7
    r=dict(step=torch.tensor([4,1,4]),pos=torch.tensor([[5,5]]*3),feats=torch.zeros(3,79),
           mask=torch.ones(3,6,dtype=torch.bool),act=torch.tensor([0,5,1]),base_act=torch.tensor([0,5,0]),
           sap_label=torch.tensor([False,True,False]),rng=torch.tensor([2,2,2]),tgt=torch.tensor([125,125,125]),
           distill_ok=torch.tensor([True,False,True]),movement_scores=torch.zeros((3,5)))
    net=Probe()
    loss,unique,soft,shots=loss_for(net,b,r,np.arange(3),"cpu")
    assert (unique,soft,shots)==(2,2,1)
    assert torch.isfinite(loss)
    loss.backward()
    assert torch.isfinite(net.logits.grad).all() and net.logits.grad.abs().sum()>0
