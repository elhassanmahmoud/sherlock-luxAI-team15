"""Check decisive historical seats independently of the interval/order enumeration."""
import csv
from collections import Counter
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from archiv import TAPES, save
from originale import HERE, STUDY


def historical():
    result=json.loads((HERE/'archiv/ergebnis.json').read_text())
    maps=json.loads((STUDY.parent/'v16_finalwoche_20261122/kartenparameter/ergebnis.json').read_text())['maps']
    small={m['seed'] for m in maps if m['unit_sensor_range'] in (1,2)}
    counts=Counter();seen=set()
    for _,(_,files) in result['source_tables'].items():
        totals={}
        for name,(filename,expected) in files.items():
            source=STUDY.parent/filename
            assert sha256(source.read_bytes()).hexdigest()==expected
            with source.open(newline='') as f:
                totals[name]={(int(r['seed']),int(r['side'][-1])):int(r['our_wins']) for r in csv.DictReader(f)
                               if r['opponent']=='solution92' and int(r['seed']) in small}
        assert totals['r3'].keys()==totals['v16'].keys()
        for key in totals['v16']:
            assert key not in seen;seen.add(key)
            scores={name:totals[name][key] for name in totals};whole={n:int(v>=2) for n,v in scores.items()}
            if whole['r3']==whole['v16']:continue
            counts['discordants']+=1
            seat=key[1];w={}
            for name in ('r3','v16'):
                receipt=json.loads((TAPES/f'{name}_{key[0]}_player_{seat}.json').read_text())
                with np.load(TAPES/receipt['filename'],allow_pickle=False) as z:
                    t=z['match_steps'];wins=z['team_wins'];bound=np.where(t==0)[0].tolist();assert bound==[0,101,202]
                    sums=wins[bound,seat].astype(int).tolist()+[scores[name]]
                w[name]=np.diff(sums).tolist()
                assert set(w[name])<={0,1}
            sig='r3_only' if whole['r3'] else 'v16_only'
            stratum='common_win' if w['v16'][0]==w['r3'][0]==1 else ('common_loss' if w['v16'][0]==w['r3'][0]==0 else 'different')
            counts[f'{stratum}/{sig}']+=1
            if stratum=='common_win' and sig=='r3_only':
                if w['r3'][1]>w['v16'][1]:counts['common_rescue_with_winning_m2']+=1
    common=result['low']['strata']['both_m1_win']
    assert len(seen)==result['low']['seats']
    assert [counts['common_win/r3_only'],counts['common_win/v16_only']]==[common['whole_rescues'][0],common['whole_lost'][0]]
    assert counts['common_rescue_with_winning_m2']==common['rescued_with_m2'][0]
    assert counts['discordants']==result['low']['discordant_all']
    return dict(low_seats=len(seen),counts=dict(counts))


def fresh():
    folder=HERE/'originalpruefung';result=json.loads((folder/'ergebnis.json').read_text())
    raw=[json.loads(s) for s in gzip.decompress((folder/'spiele.jsonl.gz').read_bytes()).splitlines()]
    by={(r['seed'],r['team'],r['id']):r for r in raw};assert len(raw)==len(by)==96
    totals={name:[0,0,0] for name in ('r3','v16')};common=0
    for seed,team,name in by:
        if name!='r3':continue
        pair=[by[seed,team,n] for n in ('r3','v16')]
        if min(r['matches'][0]['win'] for r in pair)!=1:continue
        common+=1
        for r in pair:totals[r['id']]=[a+m['win'] for a,m in zip(totals[r['id']],r['matches'],strict=True)]
    assert common==result['both_m1_win']['seats'] and all(totals[name]==result['both_m1_win']['by_policy'][name]['match_wins'] for name in totals)
    return dict(common_m1_seats=common,common_match_wins=totals,fresh_pass=sum(totals['r3'][1:])-sum(totals['v16'][1:])>=-2)


if __name__=='__main__':
    save(HERE/'nachrechnung.json',dict(historical=historical(),fresh=fresh()))
