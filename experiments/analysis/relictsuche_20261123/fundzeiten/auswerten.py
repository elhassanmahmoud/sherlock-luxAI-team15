"""Summarize only completed first-match sight panels, with paired, hash-verified Solution controls."""
import argparse
from hashlib import sha256
import gzip
import json
from pathlib import Path
from statistics import mean,median

import numpy as np

HERE=Path(__file__).resolve().parent
D=HERE.parent
OLDER=[('flotte40','Flottenblick, erste 40 Karten','flottenblick/ganzspiel/partien.jsonl.gz',40,('flotte',)),
       ('flotte120','Flottenblick, unabhängige 120 Karten','flottenblick/bestaetigung/partien.jsonl.gz',120,('flotte',)),
       ('gemeinsam48','Ort und Flotte, erste 48 Karten','ortundflotte/duelle_karten.jsonl.gz',48,('scout',)),
       ('suchwege40','Früher Vergleich dreier Suchwege','vergleich/discovery/partien.jsonl.gz',40,('route','wert','ziel'))]
LABELS={'reference':'V16','flotte':'Flottenblick','scout':'Ort und Flotte','ziel':'Ortsprior','route':'Routenlernen','wert':'Routenwert','ortundflotte':'Ort und Flotte'}


def require(b,msg):
    if not b:raise ValueError(msg)


def read_archive(p):
    with gzip.open(p,'rt') as f:return list(map(json.loads,f))


def measures(rows):
    times=[r['sight'] for r in rows];n=len(times)
    require(n and all(isinstance(x,int) and 0<=x<=101 for x in times),'Invalid sight record')
    return dict(n=n,by40=sum(t<=40 for t in times),by70=sum(t<=70 for t in times),missed=sum(t==101 for t in times),
                median=median([min(t,100) for t in times]),mean100=mean(min(t,100) for t in times),mean101=mean(times),
                wins=sum(r['win'] for r in rows),curve=[sum(t<=j for t in times) for j in range(101)])


def subset(rows):
    return measures(rows) if rows else None


def panel(key,title,path,allrows,arms):
    index={(r['seed'],r['team'],r['id'],r['opponent']):r for r in allrows}
    require(len(index)==len(allrows),'Duplicate seat')
    cards=sorted({r['seed'] for r in allrows});seats=[(s,t) for s in cards for t in (0,1)]
    groups=[('reference','solution92')]+[(name,opponent) for name in arms for opponent in ('solution92','v16')]
    require(set(index)=={(s,t,a,o) for s,t in seats for a,o in groups},'Missing whole games')
    for r in allrows:
        require(r['steps']==303 and len(r['matches'])==3 and r['win']==int(sum(x['win'] for x in r['matches'])>=2),'Unverified game row')
        if 'actions_checked' in r:
            require(r['actions_checked']==[303,303] and r['caught_errors']==[0,0], 'Invalid archived command or policy-error check')
    def group(name,opp):return [index[s,t,name,opp] for s,t in seats]
    refs=group('reference','solution92');require(all(not r['events'] for r in refs),'Reference marked as changed')
    values={'reference':{'solution92':measures(refs)}}
    for arm in arms:
        external=group(arm,'solution92');direct=group(arm,'v16')
        require(all(r['sensor']==a['sensor']==b['sensor'] for r,a,b in zip(refs,external,direct)), 'Sensor mismatch')
        active=[];inactive=[]
        for i,(r,a) in enumerate(zip(refs,external)):
            diff=r['action_hash']!=a['action_hash']
            require(diff==bool(a['events']),'Changed-command flag disagrees with the actual joint action hash')
            if not diff:require(all(r[k]==a[k] for k in ('sight','credit','matches','win')), 'Inactive trajectory differs')
            (active if diff else inactive).append(i)
        pair_subset=lambda series,ind:subset([series[i] for i in ind])
        by_map=np.array([min(x['sight'],100)-min(y['sight'],100) for x,y in zip(refs,external)]).reshape(len(cards),2).mean(1)
        draws=np.random.default_rng(231123).integers(0,len(cards),(20000,len(cards)))
        capped_ci=np.quantile(by_map[draws].mean(1),[.025,.975]).tolist()
        early=sum(a['sight']<r['sight'] for r,a in zip(refs,external));late=sum(a['sight']>r['sight'] for r,a in zip(refs,external))
        values[arm]=dict(solution92=measures(external),v16=measures(direct),active=len(active),inactive=len(inactive),
                         active_candidate=pair_subset(external,active),active_reference=pair_subset(refs,active),inactive_both=pair_subset(refs,inactive),
                         earlier=early,same=len(refs)-early-late,later=late,paired_mean100_gain=float(by_map.mean()),paired_mean100_ci95=capped_ci,
                         misses=[dict(seed=a['seed'],team=a['team'],original_sight=r['sight'],original_credit=r['credit'],candidate_credit=a['credit'],original_win=r['win'],candidate_win=a['win']) for r,a in zip(refs,external) if a['sight']==101],
                         inactive_direct=sum(not r['events'] for r in direct) if all(r.get('direct_marking',True) for r in direct) else None,
                         active_direct=subset([r for r in direct if r['events']]) if all(r.get('direct_marking',True) for r in direct) else None)
    return dict(key=key,title=title,path=str(path.relative_to(D)),sha256=sha256(path.read_bytes()).hexdigest(),cards=cards,games=len(allrows),values=values)


def verify_pilot(p):
    ref=p['values']['reference']['solution92'];g=p['values']['scout'];cand=g['solution92'];d=g['v16'];f=json.loads((D/'ortundflotte/duelle.json').read_text())
    rows=read_archive(D/p['path']);idx={(r['seed'],r['team'],r['id'],r['opponent']):r for r in rows}
    pairs=[(idx[s,t,'reference','solution92'],idx[s,t,'scout','solution92']) for s in p['cards'] for t in (0,1)]
    sums=[ref['wins'],cand['wins'],d['wins'],sum(r['sight']-n['sight'] for r,n in pairs),sum(r['credit']-n['credit'] for r,n in pairs)]
    require(len(p['cards'])==f['cards']==48 and len(rows)==f['games']==288 and sums==f['sums']==[93,95,51,68,143] and all(r['source']==f['source'] for r in rows),'Pilot verification failed')


def completed_general():
    # This reader is opt-in and opens only the final 960-game artifact after the official result is present.
    folder=D/'abschlusspruefung';result=json.loads((folder/'ergebnis.json').read_text())
    require(result['player']=='ortundflotte' and result['games']==960 and result['cards']==160,'General panel has not closed')
    path=folder/'partien.jsonl.gz';rows=read_archive(path)
    import base64,zlib
    require(len(rows)==960 and all(r['source']==result['source'] for r in rows),'Unverified general archive')
    check={}
    for r in rows:
        packed=np.frombuffer(zlib.decompress(base64.b64decode(r['tape'],validate=True)),np.int8).reshape(303,2,16,3)
        require(sha256(packed.astype('<i4').tobytes()).hexdigest()==r['digest'],'General world commands corrupt')
        key=tuple(r['key']);require(key not in check,'Duplicate general record');check[key]=(r,packed)
    require(sorted({s for s,t,a,o in check})==list(range(164300000,164300160)),'Wrong general cards')
    norm=[]
    for (s,t,arm,opp),(r,cmds) in check.items():
        active=False
        if arm=='ortundflotte' and opp=='solution92':
            ref,orig=check[s,t,'v16','solution92'];delta=np.flatnonzero(np.any(cmds!=orig,axis=(1,2,3)))
            if len(delta):
                move=delta[0];require(np.array_equal(cmds[move,1-t],orig[move,1-t]) and np.sum(np.any(cmds[move,t]!=orig[move,t],axis=1))==1,'First divergence not scout')
                active=True
            require(r['sensor']==1 or not active,'Intervention outside sight 1')
        norm.append(dict(**{k:r[k] for k in ('sight','credit','win','matches','sensor')},seed=s,team=t,id='reference' if arm=='v16' else arm,opponent=opp,
                         action_hash=r['digest'],events=[True] if active else [],direct_marking=False,steps=len(cmds)))
    alls=panel('allgemein160','Ort und Flotte, alle 160 ungefilterten Karten',path,norm,('ortundflotte',))
    sub=panel('allgemein_sicht1','Ort und Flotte, Sicht 1 im allgemeinen Vergleich',path,[v for v in norm if v['sensor']==1],('ortundflotte',))
    a=alls['values']['ortundflotte'];require([alls['values']['reference']['solution92']['wins'],a['solution92']['wins'],a['v16']['wins'],a['active']]==[result[k] for k in ('original','candidate','direct','changed_seats')] and 2*len(sub['cards'])==result['sight1'],'General result totals differ')
    return [alls,sub]


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--general',action='store_true');args=parser.parse_args()
    results=[]
    for key,label,src,n,arms in OLDER:
        p=D/src;rows=read_archive(p);require(all(r['sensor']==1 for r in rows),'Wrong sight range')
        r=panel(key,label,p,rows,arms);require(len(r['cards'])==n,'Wrong panel size');results.append(r)
    verify_pilot(results[2])
    seeds=[s for r in results for s in r['cards']];require(len(seeds)==len(set(seeds)),'Older whole-game panels overlap')
    if args.general:
        addons=completed_general();require(not set(seeds).intersection(addons[0]['cards']),'General cards overlap');results+=addons
    (HERE/('mit_gesamt.json' if args.general else 'historisch.json')).write_text(json.dumps(results,ensure_ascii=False,separators=(',',':'))+'\n')
    for r in results:
        print(r['key'],len(r['cards']),r['games'])
        for k,d in r['values'].items():
            for opp in ('solution92','v16'):
                if opp in d:
                    z=d[opp]; print(k,opp,z['n'],z['by40'],z['by70'],z['missed'],z['median'],round(z['mean100'],2),z['wins'])
            if 'active' in d:print('Paare',d['active'],d['inactive'],[round(d[z]['mean100'],2) if d[z] else None for z in ('active_reference','active_candidate','inactive_both')])


if __name__=='__main__':main()
