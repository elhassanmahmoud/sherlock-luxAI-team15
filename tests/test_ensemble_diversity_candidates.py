"""Candidate assembly uses only complete admitted arms; no games are played."""
import copy
import importlib
import json

import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet


@pytest.fixture
def case(tmp_path, monkeypatch):
    b = importlib.import_module('scripts.ensemble_diversity_candidates')
    monkeypatch.setattr(b, 'ROOT', tmp_path)
    cfg = AgentConfig().to_dict()
    cfg.update(cand_rescue=True, rescue_after=30)
    template = QNet(79, 6, hidden=256, dueling=True).state_dict()
    states = [{k: torch.full_like(v, (i+1)/100) for k,v in template.items()} for i in range(42)]
    src = tmp_path/'experiments/releases/20261101_v14_baseline/agent_p0.pth'
    src.parent.mkdir(parents=True)
    torch.save(dict(q=states[0],ensemble=states[1:36],ensemble_dims=[79]*35,cfg=cfg,
                    feature_dim=79,n_actions=6),src)
    monkeypatch.setattr(b,'SOURCE_SHA',b.file_sha256(src))
    receipts={}; entries={}; jobs={}
    for i,a in enumerate(b.ARMS):
        run=tmp_path/f'experiments/runs/retry_{a}';(run/'weights').mkdir(parents=True)
        torch.save(dict(q=states[36+i],cfg=b.training_config(cfg),feature_dim=79,n_actions=6),run/'weights/agent.pth')
        r=dict(arm=a,config=b.training_config(cfg),initial_tensor_sha256=b.tensor_sha256(states[b.PARENTS[a]]),
               pins={'git_commit':'a'*40})
        rp=run/'final_receipt.json';rp.write_text(json.dumps(r));receipts[str(rp)]=r
        entries[a]=dict(path=str(rp),sha256=b.file_sha256(rp),final_checkpoint_sha256=b.file_sha256(run/'weights/agent.pth'))
        jobs[a]={'returncode':0}
    monkeypatch.setattr(b,'validate_arm',lambda path,arm: copy.deepcopy(receipts[str(path)]))
    st=tmp_path/'training_state.json';st.write_text(json.dumps(dict(status='complete',active=[],queue=[],
                   expected_head='a'*40,jobs=jobs,receipts=entries)))
    out=tmp_path/'experiments/candidates/ensemble_diversity_20261107'
    return b,src,st,out,states,receipts


def test_rosters_raw_config_and_source_bytes_survive(case):
    b,src,st,out,states,_=case;before=src.read_bytes();m=b.build(src,st,out)
    expected={'A39':list(range(36))+[36,38,40], 'B39':list(range(36))+[37,39,41],
              'ALL42':list(range(42)), 'REPLACE36':[i for i in range(36) if i not in (0,6,12,18,24,30)]+list(range(36,42))}
    for role,indices in expected.items():
        cp=torch.load(out/f'{role}.pth',weights_only=True)
        assert [b.tensor_sha256(x) for x in [cp['q'],*cp['ensemble']]]==[b.tensor_sha256(states[i]) for i in indices]
        assert cp['cfg']==torch.load(src,weights_only=True)['cfg']
        assert 'opt' not in cp and cp['learn_steps']==0 and cp['env_steps']==60000
        assert m['roles'][role]['sha256']==b.file_sha256(out/f'{role}.pth')
    assert src.read_bytes()==before and m['status']=='admitted'
    assert m['non_nominable']==['V14','REPLACE36']
    with pytest.raises(FileExistsError):b.build(src,st,out)


@pytest.mark.parametrize('bad',['partial','missing_arm','exit','receipt_hash','parent','source_head','config','duplicate','nan'])
def test_bad_training_never_creates_candidates(case,bad):
    b,src,st,out,states,receipts=case;s=json.loads(st.read_text());r=s['receipts']['A0'];rp=r['path']
    if bad=='partial':s['status']='failed'
    elif bad=='missing_arm':s['receipts'].pop('B2')
    elif bad=='exit':s['jobs']['A0']['returncode']=1
    elif bad=='receipt_hash':r['sha256']='0'*64
    elif bad=='parent':receipts[rp]['initial_tensor_sha256']='0'*64
    elif bad=='source_head':receipts[rp]['pins']['git_commit']='b'*40
    elif bad=='config':receipts[rp]['config']['lr']=1
    else:
        cp_path=__import__('pathlib').Path(rp).parent/'weights/agent.pth';cp=torch.load(cp_path,weights_only=True)
        if bad=='duplicate':cp['q']=states[0]
        else:cp['q']['adv.2.bias'][0]=float('nan')
        torch.save(cp,cp_path);r['final_checkpoint_sha256']=b.file_sha256(cp_path)
    st.write_text(json.dumps(s))
    with pytest.raises(ValueError):b.build(src,st,out)
    assert not out.exists()
