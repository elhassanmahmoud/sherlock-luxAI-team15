import numpy as np
import torch
from agents.sherlock.features import FEATURE_NAMES
from scripts.r3_trained_reflection import reflected_step,transposed_minibatch
from scripts.r3_trained_reflection_audit import gates


def test_transposed_training_rows_are_an_involution_and_sap_points_to_the_same_cell():
    board=torch.zeros((2,16,24,24),dtype=torch.int8)
    board[0,:,2,7]=torch.arange(1,17)
    feat=torch.arange(158,dtype=torch.float32).reshape(2,79)
    rows=dict(step=torch.tensor([0,1]),pos=torch.tensor([[2,7],[4,5]]),feats=feat,
              mask=torch.tensor([[1,1,0,1,0,1],[1,0,1,0,1,1]],dtype=torch.bool),
              act=torch.tensor([5,1]),base_act=torch.tensor([0,2]),rng=torch.tensor([5,5]),
              sap_label=torch.tensor([True,False]),sdx=torch.tensor([2,-1]),sdy=torch.tensor([-1,0]),
              tgt=torch.tensor([4*24+6,3*24+5]),distill_ok=torch.tensor([False,True]),
              movement_scores=torch.tensor([[2.,5,8,7,1],[1.,6,3,8,4]]))
    ids=np.arange(2)
    bm,r,j=transposed_minibatch(board,rows,ids)
    assert torch.equal(bm[0,:,7,2],board[0,:,2,7])
    assert r["pos"][0].tolist()==[7,2] and r["tgt"][0].item()==6*24+4
    assert r["sdx"].tolist()==[-1,0] and r["sdy"].tolist()==[2,-1]
    assert r["mask"][0].tolist()==[True,False,True,False,True,True]
    assert r["act"].tolist()==[5,4] and r["base_act"].tolist()==[0,3]
    assert r["movement_scores"][1].tolist()==[1,4,8,3,6]
    assert r["feats"][1,FEATURE_NAMES.index("u_allies")]==feat[1,FEATURE_NAMES.index("l_allies")]
    b2,r2,_=transposed_minibatch(bm,r,j)
    assert torch.equal(b2,board) and all(torch.equal(rows[k],v) for k,v in r2.items())


def test_orientation_balance_and_joint_holdout_gates():
    assert sum(reflected_step(k) for k in range(1024))==512
    for step in range(0,1024,16):
        assert sum(reflected_step(k) for k in range(step,step+16))==8
    o=dict(augmented_correct=5,diagonal_correct=5,control_correct=4)
    n=dict(augmented_correct=5,diagonal_correct=4,control_correct=4)
    assert all(gates(o,n).values())
    assert not all(gates(o,dict(n,control_correct=5)).values())
    assert not all(gates(dict(o,control_correct=6),n).values())
