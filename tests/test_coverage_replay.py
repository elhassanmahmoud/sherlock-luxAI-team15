import numpy as np

from scripts.coverage_replay import commands_world, gated_classes, known_coverage


def test_player_one_world_commands_keep_base_sap_target():
    rows=np.array([[geo,dx,dy] for geo,dx,dy in [(2,0,0),(5,-1,2)]],int)
    world=commands_world(rows,np.array([3,15]),1)
    assert world[3].tolist()==[1,0,0] and world[15].tolist()==[5,-2,1]
    assert not world[0].any()


def test_threshold_sap_veto_and_distinct_occupied_fields():
    base=np.array([0,0,0,5]); raw=np.array([1,2,5,1])
    result=gated_classes(base,raw,np.array([.69,.70,.95,.99]))
    assert result.tolist()==[0,2,0,5]
    known=np.zeros((24,24),bool);known[4,4]=known[5,4]=True
    assert known_coverage(np.array([[4,4],[4,4],[4,4],[8,8]]),result,known)=={(4,4),(5,4)}


def test_inference_uses_separate_boards_all_six_classes_and_payable_sap():
    import torch
    from scripts.coverage_replay_inference import predict

    class Fixed:
        def __init__(self):
            self.batches=[]
        def forward_all(self,board,groups,pos,feats):
            self.batches.append((board.shape,groups.tolist()))
            logits=torch.tensor([[0.,8.,0.,0.,0.,12.]]).repeat(len(pos),1)
            return logits,None,None

    a=dict(planes=np.zeros((2,16,24,24),np.int8),step=np.array([0,0,1]),pos=np.zeros((3,2),np.int8),
           feats=np.zeros((3,79),np.float16),mask=np.ones((3,6),bool))
    a["feats"][:,7]=.60  # 30 energy per shot
    a["feats"][:,2]=np.array([29,30,40])/400
    a["mask"][:,5]=False  # live head rebuilds the SAP column from actual available energy
    net=Fixed()
    raw,conf=predict([net],a)
    assert raw.tolist()==[1,5,5] and (conf>.7).all()
    assert net.batches==[((1,16,24,24),[0,0]),((1,16,24,24),[0])]
