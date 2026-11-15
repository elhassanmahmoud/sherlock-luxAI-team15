"""Two synthetic seats only, without game/torch/model imports. Uses the historical SideRecord NPZ encoding."""
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS

import numpy as np

from scripts.optional_v4_dagger import PublicChecks, SET, check_npz


def check(team, folder):
    key = (7172000, f"player_{team}", "kaggle3")
    p = folder / f"{team}.npz"
    actor = NS(cfg=NS(imit_stay_bias=1.5, imit_unstack=True), training=False, sample=False, has_sap_head=True,
               extra_nets=[], autosave_on_terminate=False, team_id=team)
    audit=PublicChecks(actor)
    board_steps=[1,102,203]
    for t in range(303):
        energy=np.zeros((2,16,1),np.int16)
        mask=np.zeros((2,16),bool)
        label=np.zeros((16,3),int)
        fz=None
        if t in (*board_steps,0,101,202):
            mask[team,:3]=True
            energy[team,:3,0]=[0,60,-1]
            label[0,0]=1
            label[1]=[5,1,0]
            if t in board_steps:
                fz=({"ally_ene":energy[team,:,0]},[0,1,2])
        obs=dict(steps=t,match_steps=t%101,units={"energy":energy},units_mask=mask)
        audit.before(t,obs,fz,np.zeros((16,3),int),label)
        audit.feedback+=1
    rows=6
    meta=dict(seed=key[0],side=key[1],opponent=key[2],dagger=True,teacher_history="played_student_actions",
              row_filter="unit_energy>=0",steps=303,acknowledged=303,student_set=SET,source_protocol_sha256="fixture",
              student_wins=2,opp_wins=1,played_sha256=audit.commands.hexdigest(),teacher_sha256=audit.teacher.hexdigest(),
              canonical_teacher_sha256=audit.canonical.hexdigest(),live_masks=audit.alive_masks,rollout_seconds=4)
    feats=np.zeros((rows,79),np.float16)
    feats[:,0:2]=1/24
    feats[1::2,2]=60/400
    feats[:,7:9]=[30/50,3/7]
    a=dict(meta=json.dumps(meta),planes=np.zeros((3,16,24,24),np.int8),pos=np.ones((rows,2),np.int8),
           mstep=np.ones(rows,np.int16),step=np.repeat(np.arange(3,dtype=np.int32),2),feats=feats,
           uid=np.tile(np.array([0,1],np.int8),3),mask=np.ones((rows,6),bool),act=np.tile(np.array([2 if team else 1,5],np.int8),3),
           sdx=np.tile(np.array([0,0 if team else 1],np.int8),3),sdy=np.tile(np.array([0,-1 if team else 0],np.int8),3))
    np.savez_compressed(p,**a)
    r=check_npz(p,key,"fixture")
    assert (r["rows"],r["sap"],r["admitted"],r["legal_sap"],r["rows_by_match"])==(6,3,6,3,[2,2,2])
    for col,index,value in [("uid",0,2),("act",0,0),("mstep",0,2)]:
        bad={**a,col:a[col].copy()}
        bad[col][index]=value
        np.savez_compressed(p,**bad)
        try:check_npz(p,key,"fixture")
        except ValueError:pass
        else:raise AssertionError(f"Accepted corrupt {col}")


if __name__=="__main__":
    with TemporaryDirectory() as folder:
        for team in (0,1):
            check(team,Path(folder))
    print("Both synthetic seats, three restarts, six rejected mutations.")
