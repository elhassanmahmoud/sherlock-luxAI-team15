"""Join 160 fixed true continuations to independently stored public original openings."""
from hashlib import sha256
import gzip
import json
from pathlib import Path

import numpy as np

from modell import observable, style

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ARCH = Path.home()/'Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/spaetort/train'
GAMES = STUDY/'folgewahl/train_spiele.jsonl.gz'
GAME_SHA = 'fbc358ca7eed53cbe17bc1c7c9bf136f9a63b92ed8c0d233956bcde9d2a4c96c'


def sha(p):return sha256(p.read_bytes()).hexdigest()


def save(path, value):
    data=json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n'
    if path.exists():assert json.loads(path.read_text())==json.loads(data)
    else:path.write_text(data)


def compact(path,rows):
    data=b''.join((json.dumps(r,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n').encode() for r in rows)
    if path.exists():assert gzip.decompress(path.read_bytes())==data
    else:path.write_bytes(gzip.compress(data,mtime=0))


def first(hits):
    turns=np.flatnonzero(hits)
    return int(turns[0]) if len(turns) else 101


def existing(z,team,cfg):
    foe=1-team
    score=z['team_points'][:,[team,foe]]
    delta=np.diff(score,axis=0,prepend=score[:1])
    live=z['units_mask'] & (z['energy']>=0)
    repeated=live[1:,foe]&live[:-1,foe]
    still=np.all(z['position'][1:,foe]==z['position'][:-1,foe],axis=2)
    oe=z['energy'][65:,team][live[65:,team]]
    ee=z['energy'][65:,foe][live[65:,foe]]
    order=z['commands'][65:,:,0][live[65:,team]]
    out=[*delta[:36].sum(0),*delta[36:71].sum(0),*delta[71:].sum(0),first(z['relic_nodes_mask'].any(1)),first(score[:,0]>0),
         live[:,foe].sum()/101,(repeated&still).sum()/max(1,repeated.sum()),oe.mean() if oe.size else 0,ee.mean() if ee.size else 0,
         z['sensor_mask'].any(0).mean(),z['known_points'][-1].sum(),cfg['unit_move_cost'],cfg['unit_sap_range'],
         live[65:,team].sum(1).mean(),live[65:,foe].sum(1).mean(),(~live[:,foe].any(1)).mean(),
         (order==0).sum()/max(1,len(order)),(order==5).sum()/max(1,len(order))]
    return [float(a) for a in out]


def extract():
    assert sha(GAMES)==GAME_SHA
    old=[json.loads(s) for s in gzip.decompress(GAMES.read_bytes()).splitlines()]
    selection=json.loads((STUDY/'spaetgebiet/ortsmodell/karten.json').read_text())
    assert len(old)==len({r['seed'] for r in old})==160 and len(selection['valid'])==48
    assert {r['seed'] for r in old}==set(selection['train']) and not set(selection['valid'])&set(selection['train'])
    out=[]
    for r in old:
        seed,team=r['seed'],r['team'];receipt=ARCH/f'{seed}-{team}.json';meta=json.loads(receipt.read_text())
        assert (meta['seed'],meta['team'],meta['opponent'],meta['split'],meta['steps'])==(seed,team,r['opponent'],'train',303)
        assert meta['cfg']['unit_sensor_range']==1 and r['base']['win']==meta['win']
        assert [m['points'][::1 if team==0 else -1] for m in r['base']['matches']]==meta['matches']
        assert (r['base']['prefix']==r['switch']['prefix'] and r['base']['matches'][0]==r['switch']['matches'][0]
                and r['eligible']==bool(r['base']['matches'][0]['win']))
        file=ARCH/meta['public'];assert file.name==f'{seed}-{team}.npz' and sha(file)==meta['public_sha']
        with np.load(file,allow_pickle=False) as data:
            z={k:data[k][:101] for k in ('units_mask','energy','position','team_points','relic_nodes_mask','commands','sensor_mask','known_points')}
        z['energy']=z['energy'].reshape(101,2,16)
        z['position']=z['position'].astype(np.int32)
        base=existing(z,team,meta['cfg'])
        assert len(base)==21 and np.allclose(base,r['base']['features'],atol=1e-10,rtol=0)
        live=z['units_mask'] & (z['energy']>=0)
        enemy=z['position'][:,1-team];own=z['position'][:,team];els=live[:,1-team];ols=live[:,team]
        time,uid=np.where(els);coords=enemy[time,uid]
        assert ((coords>=0)&(coords<24)).all() and z['sensor_mask'][time,coords[:,0],coords[:,1]].all()
        values,stats=style(own,enemy,ols,els)
        assert (values,stats)==style(23-own[:,:,::-1],23-enemy[:,:,::-1],ols,els)
        assert (values,stats)==style(own[:,::-1],enemy[:,::-1],ols[:,::-1],els[:,::-1])
        delta=r['switch']['win']-r['base']['win'];target=delta if delta>=0 else 2*delta
        assert r['experiments']==1+int(r['eligible']) and (r['eligible'] or delta==0)
        out.append(dict(seed=seed,team=team,opponent=r['opponent'],eligible=r['eligible'],observable=observable(stats),
            input=base,style=values,tracks=stats,target=target,delta=delta,original=r['base']['win'],switch=r['switch']['win'],
            old_pick=r['eligible'] and r['held_out_value']>=.35,public_sha=meta['public_sha'],receipt_sha=sha(receipt),m1_hash=r['base']['prefix']))
    assert sum(r['eligible'] for r in out)==115 and sum(r['old_pick'] for r in out)==6
    return out
