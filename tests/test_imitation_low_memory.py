from types import SimpleNamespace

import numpy as np
import torch

from scripts import imitate
from scripts.imitation_storage import store_partition


def archive(path, seed):
    rng = np.random.default_rng(seed)
    frames, width, height = 21, 5, 5
    n = frames * 2
    feats = rng.normal(0, .1, (n,79)).astype(np.float16)
    feats[:,2], feats[:,7], feats[:,8] = .5, .6, 3/7
    feats[::11,2] = 0   # A cheap-energy label where a SAP may not be admitted.
    act = np.arange(n, dtype=np.int8) % 6
    dx = np.zeros(n,np.int8)
    dx[5] = 12           # Outside the board; other shots land on their own tile.
    np.savez_compressed(path,planes=rng.integers(-70,70,(frames,16,width,height),dtype=np.int8),
                        step=np.repeat(np.arange(frames,dtype=np.int32),2), pos=np.full((n,2),2,np.int8),
                        feats=feats,mask=np.ones((n,6),bool),act=act,sdx=dx,sdy=np.zeros(n,np.int8))


def test_low_memory_keeps_seed_groups_order_and_exact_labels(tmp_path):
    source = tmp_path/'games'
    source.mkdir()
    for seed in range(4):
        for side in (0,1):
            archive(source/f'g{seed}_player_{side}_kaggle3.npz',seed+side)
    parts = imitate.partition_files([source],.25,4)
    train, val, nt, nv = imitate.load_data([source],.25,4)
    assert (nt,nv) == (6,2)
    assert {p.name.split('_')[0] for p in parts['val']}.isdisjoint(p.name.split('_')[0] for p in parts['train'])
    for group, (expected,rows) in (('train',train),('val',val)):
        board, stored = store_partition(parts[group], tmp_path/group, imitate.prepare_labels)
        assert isinstance(board,np.memmap) and all(isinstance(v,np.memmap) for v in stored.values())
        np.testing.assert_array_equal(board,expected)
        ordinary = {k:torch.from_numpy(v.copy()) for k,v in rows.items()}
        imitate.prepare_labels(ordinary, *board.shape[-2:])
        assert set(ordinary) == set(stored)
        for k in stored:
            np.testing.assert_array_equal(stored[k],ordinary[k].numpy(),err_msg=k)
        assert 0 < stored['sap_label'].sum() < (stored['act'] == 5).sum()


def test_same_cpu_training_streamed_and_ordinary(tmp_path, monkeypatch):
    source=tmp_path/'games'
    source.mkdir()
    for s in range(4):
        archive(source/f'g{s}_player_0_v14.npz',s)
    monkeypatch.setattr(imitate,'v14_cfg',lambda: SimpleNamespace(to_dict=lambda:{}))
    state, threads = np.random.get_state(), torch.get_num_threads()
    metrics = []
    try:
        torch.set_num_threads(1)
        for low in (False, True):
            np.random.seed(4421)  # Ordinary, nonselective trainer uses global NumPy for shuffle.
            a=SimpleNamespace(data=[str(source)],out=str(tmp_path/f'{low}.pth'),epochs=2,mb=16,
                              ch=4,blocks=1,hidden=12,val_frac=.25,seed=4,device='cpu',lr=.0003,
                              sap_weight=.5,low_memory=low)
            imitate.cmd_train(a)
            lines=(tmp_path/f'{low}.log').read_text().splitlines()
            metrics.append([line.rsplit(' | ',1)[0] for line in lines if line.startswith('Epoche ')])
    finally:
        np.random.set_state(state)
        torch.set_num_threads(threads)
    ckpts=[torch.load(tmp_path/f'{v}.pth',map_location='cpu',weights_only=True) for v in (False,True)]
    assert all(ck['kind']=='imitation' and ck['sap_own_tile'] for ck in ckpts)
    assert len(metrics[0]) == 2 and metrics[0] == metrics[1]
    for name, weights in ckpts[0]['policy'].items():
        torch.testing.assert_close(ckpts[1]['policy'][name],weights,rtol=0,atol=0)
    assert not list(tmp_path.glob('.imitation-data-*'))
