"""Check team totals twice and classify the signed point margin of every official match."""
import csv,gzip,json
from collections import Counter
from pathlib import Path
import numpy as np
from zuordnen import ARCH,HERE,WORK,select,sha


def group(d1,d23,ours,other):
    if ours==other:return 'Punktgleichstand'
    if d1>0 and d23>0:return 'beide'
    if d1>0:return 'erste'
    if d23>0:return 'spätere'
    raise ValueError('A lost points match has no unfavorable group')


def main():
    pairs=select();rows=[];flat=[]
    for a,b in pairs:
        for game in (a,b):
            s,t,arm,opp=game['key'];r=json.loads((WORK/f'{s}_{t}_{arm}.json').read_bytes());assert r['digest']==game['digest'] and r['referee']==game['matches']
            pts=np.array(r['points']).sum(3);assert pts.shape==(3,2,3);gains=np.array(r['gains']).reshape(3,101,2).sum(1)
            assert np.array_equal(gains,pts.sum(2)) and gains.tolist()==[m['points'] for m in game['matches']];rows.append(r)
            for i,m in enumerate(r['referee']):
                own,foe=pts[i].tolist();d1=foe[0]-own[0];late=sum(foe[1:])-sum(own[1:]);assert d1+late==m['points'][1]-m['points'][0]
                assert all(own[j]==foe[j]==0 for j in range(r['active_groups'][i],3))
                winner=bool(m['win']);category='gewonnen' if winner else group(d1,late,*m['points'])
                flat.append(dict(seed=s,sitz=t,spieler=arm,match=i+1,sieg=int(winner),aktiv=r['active_groups'][i],
                                 eigene_1=own[0],eigene_2=own[1],eigene_3=own[2],gegner_1=foe[0],gegner_2=foe[1],gegner_3=foe[2],
                                 nachteil_erste=d1,nachteil_spaet=late,eigene_gesamt=sum(own),gegner_gesamt=sum(foe),verlustgruppe=category))
    assert len(flat)==66 and len(rows)==22
    with (HERE/'matches.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
    stats={}
    for arm in ('v16','ortundflotte'):
        z=[x for x in flat if x['spieler']==arm];lost=[x for x in z if not x['sieg']];rarm=[r for r in rows if r['phase']==arm]
        stats[arm]=dict(lost=len(lost),won_first=sum(x['sieg'] for x in z if x['match']==1),lost_by_match=[sum(x['match']==j for x in lost) for j in (1,2,3)],
            classification=dict(Counter(x['verlustgruppe'] for x in lost)),dominant=dict(Counter('erste' if x['nachteil_erste']>x['nachteil_spaet'] else 'spätere' if x['nachteil_erste']<x['nachteil_spaet'] else 'gleich' for x in lost if x['eigene_gesamt']<x['gegner_gesamt'])),
            both_dominant=dict(Counter('erste' if x['nachteil_erste']>x['nachteil_spaet'] else 'spätere' if x['nachteil_erste']<x['nachteil_spaet'] else 'gleich' for x in lost if x['verlustgruppe']=='beide')),
            only_one_active_matches=sum(x['aktiv']==1 for x in z),only_one_paying_matches=sum(x['eigene_2']+x['eigene_3']+x['gegner_2']+x['gegner_3']==0 and x['eigene_gesamt']+x['gegner_gesamt']>0 for x in z),
            only_one_active_lost=sum(x['aktiv']==1 for x in lost),only_one_paying_lost=sum(x['eigene_2']+x['eigene_3']+x['gegner_2']+x['gegner_3']==0 and x['eigene_gesamt']+x['gegner_gesamt']>0 for x in lost),
            active_groups_per_seat=dict(Counter(max(r['active_groups']) for r in rarm)),only_first_paying_seats=sum(not any(x['eigene_2']+x['eigene_3']+x['gegner_2']+x['gegner_3'] for x in z if (x['seed'],x['sitz'])==(r['seed'],r['team'])) for r in rarm),
            no_later_score_cards=sorted({r['seed'] for r in rarm if not any(x['eigene_2']+x['eigene_3']+x['gegner_2']+x['gegner_3'] for x in z if (x['seed'],x['sitz'])==(r['seed'],r['team']))}),
            both_deficits=sum(x['verlustgruppe']=='beide' for x in lost),sums_lost={k:sum(x[k] for x in lost) for k in ('eigene_1','eigene_2','eigene_3','gegner_1','gegner_2','gegner_3')})
    cnt=sum(not r['identical_tape_reused'] for r in rows);assert len({r['digest'] for r in rows})==cnt
    summary=dict(archive=sha(ARCH),common_loss_seats=len(pairs),maps=sorted({r['seed'] for r in rows}),
                 identical_complete_commands=22-cnt,distinct_replays=cnt,by_policy=stats)
    (HERE/'bilanz.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');raw=b''.join(json.dumps(r,separators=(',',':')).encode()+b'\n' for r in rows);(HERE/'rekonstruktionen.jsonl.gz').write_bytes(gzip.compress(raw,mtime=0));print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':main()
