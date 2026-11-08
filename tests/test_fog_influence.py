"""Small synthetic replay/math checks; no games or real model-bank execution."""
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from scripts import fog_influence as I


def replay(path,n=12):
    ns=np.arange(n*79,dtype=np.float32).reshape(n,79)
    mask=np.ones((n,6),bool);done=np.zeros(n,np.float32)
    done[0]=1;mask[1]=False
    np.savez(path,s=-ns,ns=ns,mask=mask,done=done)
    return ns,mask,done


def test_fixed_sampling_uses_ns_next_mask_and_no_replacement(tmp_path):
    path=tmp_path/'buffer.npz';ns,mask,done=replay(path,2602)
    selected=I.sample_buffer(path,I.digest(path),np.random.default_rng(0))
    expected=np.random.default_rng(0).choice(np.arange(2,2602),2500,replace=False)
    assert np.array_equal(selected['indices'],expected)
    assert np.array_equal(selected['ns'],ns[expected]) and np.array_equal(selected['mask'],mask[expected])
    assert len(set(selected['indices']))==2500 and selected['eligible_rows']==2600


def test_sequential_rng_and_unique_pool(tmp_path):
    paths=[]
    for arm in I.ARMS:
        path=tmp_path/f'{arm}.npz';replay(path);paths.append(path)
    bank,metadata=I.sample_bank({a:dict(path=p,sha256=I.digest(p)) for a,p in zip(I.ARMS,paths)})
    assert len(bank['ns'])==40 and metadata['unique_ns_mask_rows']==10
    assert metadata['sampled_rows']==40
    rng=np.random.default_rng(0)
    for index,arm in enumerate(I.ARMS):
        expected=rng.choice(np.arange(2,12),10,replace=False)
        assert np.array_equal(bank['row_indices'][bank['arm_indices']==index],expected)


def test_changed_buffer_hash_rejected(tmp_path):
    path=tmp_path/'buffer.npz';replay(path);old=I.digest(path);path.write_bytes(b'tampered')
    with pytest.raises(ValueError): I.sample_buffer(path,old,np.random.default_rng(0))


@pytest.mark.parametrize('damage',['nan','bad_mask','bad_done','wrong_width'])
def test_bad_replay_inputs_fail_closed(tmp_path,damage):
    path=tmp_path/'buffer.npz';ns,mask,done=replay(path)
    if damage=='nan': ns[2,0]=np.nan
    elif damage=='bad_mask': mask=mask.astype(np.float32)
    elif damage=='bad_done': done[2]=np.nan
    else: ns=ns[:,:78]
    np.savez(path,ns=ns,mask=mask,done=done)
    with pytest.raises(ValueError): I.sample_buffer(path,I.digest(path),np.random.default_rng(0))


def test_legal_argmax_matches_minus1e9_and_rejects_illegal_winner():
    q=np.array([[3,100,2,1,0,4],[0,1,2,3,4,5]],np.float32)
    mask=np.array([[1,0,1,0,0,1],[0,0,0,1,0,0]],bool)
    assert I.legal_argmax(q,mask).tolist()==[5,3]
    with pytest.raises(ValueError): I.legal_argmax(q,np.zeros_like(mask))
    with pytest.raises(ValueError): I.legal_argmax(np.full_like(q,-2e9),mask)


def test_pair_mean_and_fixed_v14_runnerup_margin_even_without_change():
    members=torch.zeros((40,3,6),dtype=torch.float32)
    members[:36,:,0]=2;members[:36,:,1]=1
    members[36:38,:,0]=2;members[36:38,:,1]=3
    members[38:,:,0]=2;members[38:,:,1]=1
    mask=np.ones((3,6),bool);mask[2]=[1,0,0,0,0,0]
    means=I.ensemble_means(members)
    np.testing.assert_allclose(means['CONTROL38'][:,1].numpy(),np.full(3,42/38),rtol=1e-6)
    summary=I.summarize(members,mask,np.array([0,1,3],np.uint8))
    control=summary['candidates']['CONTROL38']
    assert control['proposal_changes']['changed']==0
    assert control['v14_fixed_margin_change']['count']==2
    assert control['v14_fixed_margin_change']['mean']==pytest.approx(-4/38)
    assert control['pair_minus_base_at_v14_winner']['mean']==0
    assert control['pair_minus_base_all_q']['max']==2
    assert summary['members'][0]['legal_action_gap']['count']==2


def test_independent_mean_reproduction_tolerance_and_nonfinite():
    members=torch.arange(40*2*6,dtype=torch.float32).reshape(40,2,6)/100
    expected=I.ensemble_means(members)['CONTROL38']
    assert I.check_reproduction(expected,expected.clone())['passed']
    with pytest.raises(ValueError): I.check_reproduction(expected,expected+.01)
    with pytest.raises(ValueError): I.check_reproduction(expected,torch.full_like(expected,float('nan')))


def test_bank_is_exclusive_and_hash_bound_before_outputs(tmp_path):
    bank=dict(ns=np.zeros((2,79),np.float32),mask=np.ones((2,6),bool),
              row_indices=np.array([2,3]),arm_indices=np.array([0,1],np.uint8))
    out=tmp_path/'fresh';out.mkdir()
    proof=I.persist_bank(out,bank,dict(sampled_rows=2),['a'*64]*40)
    assert I.digest(out/'bank.npz')==proof['bank_sha256']
    assert json.loads((out/'bank_manifest.json').read_text())['ordered_member_hashes']==['a'*64]*40
    with pytest.raises(FileExistsError): I.persist_bank(out,bank,{},[])
