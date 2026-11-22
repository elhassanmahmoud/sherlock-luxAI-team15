from pathlib import Path
import argparse
from collections import Counter
import gzip
import json
import numpy as np
from spielvergleich import DIGEST, HERE, keys, sha


def records(folder):
    if folder.is_dir():
        for item in sorted(folder.glob('*.json')):
            yield json.loads(item.read_text())
    else:
        with gzip.open(folder,'rt') as f:
            yield from (json.loads(line) for line in f)


def evaluate(phase,folder):
    expected=set(keys(phase)); raw={}
    approval=HERE/('diagnose_ergebnis.json' if phase=='auswahl' else 'auswahl_ergebnis.json')
    binding={p.name:sha(p) for p in (HERE/'regel.py',HERE/'PLAN.md',HERE/'spielvergleich.py',approval)}
    for r in records(folder):
        k=(r['seed'],r['team'],r['opponent'],r['arm'])
        if (r['release']!=DIGEST or r['binding']!=binding or k in raw or k not in expected or r['steps']!=303 or r['our_wins']+r['opp_wins']!=3 or
                r['game_win']!=int(r['our_wins']>=2) or min(r['our_points'],r['opp_points'])<0):raise ValueError(k)
        raw[k]=r
    if set(raw)!=expected or len({json.dumps(r['binding'],sort_keys=True) for r in raw.values()})!=1:raise ValueError('Incomplete panel')
    summaries={}; contrasts={}; paired_unchanged=0
    scores=('our_wins','opp_wins','our_points','opp_points','game_win')
    seeds=sorted({k[0] for k in raw}); rng=np.random.default_rng(221124)
    sample=rng.integers(0,len(seeds),(20000,len(seeds)))
    for opp in ('solution92','kaggle3','v16'):
        summaries[opp]={}
        for arm in (('kandidat',) if opp=='v16' else ('original','kandidat')):
            panel=[r for k,r in raw.items() if k[2:]==(opp,arm)]
            summaries[opp][arm]=dict(games=len(panel),wins=sum(r['game_win'] for r in panel),
                    matches=sum(r['our_wins'] for r in panel),changed=sum(bool(r['interventions']) for r in panel),
                    wins_with_intervention=sum(r['game_win'] for r in panel if r['interventions']),
                    interventions=sum(len(r['interventions']) for r in panel),
                    seats={str(t):{'games':sum(r['team']==t for r in panel),
                                    'wins':sum(r['game_win'] for r in panel if r['team']==t)} for t in (0,1)})
        if opp=='v16':continue
        net=[]; discordance=Counter()
        for seed in seeds:
            d=[]
            for side in (0,1):
                a,b=(raw[seed,side,opp,arm] for arm in ('kandidat','original'))
                if not a['interventions']:
                    if any(a[k]!=b[k] for k in scores):raise ValueError('No command changed but endgame differs')
                    paired_unchanged+=1
                def share(r):
                    total=r['our_points']+r['opp_points']
                    return r['our_points']/total if total else .5
                d.append(share(a)-share(b));discordance[f"{a['game_win']}:{b['game_win']}"]+=1
            net.append(np.mean(d))
        values=np.array(net)
        contrasts[opp]=dict(paired_seats=dict(discordance),mean_share_delta=float(values.mean()),
                             share_delta_ci95=np.percentile(values[sample].mean(axis=1),[2.5,97.5],method='linear').tolist())
    d=summaries
    gates={opp:d[opp]['kandidat']['wins']>=d[opp]['original']['wins'] for opp in ('solution92','kaggle3')}
    if phase=='auswahl':
        gates['kaggle_two_additional_matches']=d['kaggle3']['kandidat']['matches']-d['kaggle3']['original']['matches']>=2
        gates['direct']=d['v16']['kandidat']['wins']>=21
    else:
        gates['kaggle_share']=contrasts['kaggle3']['mean_share_delta']>=.01
        gates['positive_ci']=contrasts['kaggle3']['share_delta_ci95'][0]>0
        gates['direct']=d['v16']['kandidat']['wins']>=50
    return dict(phase=phase,totals=summaries,paired=contrasts,identical_external_seats_without_intervention=paired_unchanged,
                gates=gates,passed=all(gates.values()))


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('phase',choices=('auswahl','bestaetigung'));ap.add_argument('folder',type=Path)
    ap.add_argument('--archiv',type=Path)
    a=ap.parse_args()
    report=evaluate(a.phase,a.folder)
    if a.archiv is not None:
        raw=''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in records(a.folder)).encode()
        payload=gzip.compress(raw,mtime=0)
        if a.archiv.exists() and a.archiv.read_bytes()!=payload:
            raise ValueError('A different archive already exists')
        a.archiv.write_bytes(payload)
        if evaluate(a.phase,a.archiv)!=report:raise ValueError('Archive readback differs')
    print(json.dumps(report,indent=2))
