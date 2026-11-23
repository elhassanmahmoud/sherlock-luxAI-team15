"""Replay already measured forced training cases to explain when V16 resumed control. No new maps or training."""
import argparse
from collections import Counter
import gzip
import json

import numpy as np

from anfahrt import HERE,MIRROR,STEPS,bits,encoded,is_set,stationary,threat_col,worlds
from gegenfahrten import check,common,start
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors

def reason(actor,o,row,path,expect):
    if not path:return ['Wegende']
    uid=row['uid'];target=row['target'];pol=actor.pol;pub=actor.pub;team=actor.team;points=bits(pol['point']);pos=np.asarray(o['units']['position'])[team,uid];start=int(pos[0]*24+pos[1]);nxt=path[0];flags=[]
    if not o['units_mask'][team,uid] or o['units']['energy'][team,uid].item()<max(30,4*int(actor.base.env_cfg['unit_move_cost'])):flags.append('Einheit/Energyreserve')
    if start==target:flags.append('Ankunft')
    if is_set(points,target):flags.append('V16 bestätigt Ziel inzwischen')
    if not is_set(bits(pol['visible']),target):flags.append('Ziel außer Sicht')
    if target in pub['occupied']:flags.append('Ziel bereits selbst besetzt')
    if target in pol['enemy']:flags.append('Ziel sichtbar gegnerisch besetzt')
    if target in {x for u,x in pol['dest'].items() if u!=uid}:flags.append('Anderes Schiff plant Ziel')
    if expect is not None and start!=expect:flags.append('Vorherigen Schritt nicht erreicht')
    old=int(actor.raw[uid,0]);original=int(STEPS[start,old]) if old<=4 and start>=0 else -1;cert=worlds(actor.ev.positive)|points;parked=stationary(pol)
    if old==5:flags.append('SAP-Auftrag')
    fz=actor.base._imitation.last_fz
    if fz is not None:
        ctx,ids,features,mask,*_=fz;idx=np.flatnonzero(np.asarray(ids)==uid)
        if len(idx):
            i=idx.item();assigned=ctx['assigned'].get(uid)
            if assigned is not None:
                x,y=map(int,assigned);goal=24*(23-y)+23-x if team else 24*x+y
                if is_set(cert,goal):flags.append('V16 teilt einen gesicherten Punkt zu')
            if features[i,threat_col()]>0:flags.append('Sichtbare Gefahr')
            dirs=np.flatnonzero(STEPS[start]==nxt) if start>=0 else []
            if len(dirs)!=1 or not mask[i,MIRROR[int(dirs[0])] if team else int(dirs[0])]:flags.append('Nächster Schritt nicht legal')
        else:flags.append('V16 gibt keinen freien Befehl')
    if start>=0 and is_set(cert,start) and not (start!=row['start'] and any(i!=uid for i in parked.get(start,[]))):flags.append('Selbst auf gesichertem Punkt')
    if original>=0 and original!=target and is_set(cert,original) and not (original==start and any(i!=uid for i in parked.get(start,[]))):flags.append('Originalbefehl bedient anderen Punkt')
    if old==0 and start>=0 and pub['gain']>0 and not is_set(worlds(actor.ev.negative),start) and not any(i!=uid for i in parked.get(start,[])):flags.append('Möglicher alleiniger aktueller Halter')
    if nxt in {x for u,x in pol['dest'].items() if u!=uid} and not (is_set(cert,nxt) and any(i!=uid for i in parked.get(nxt,[]))):flags.append('Zwischenfeld reserviert')
    if not is_set(bits(pol['known_passable']),nxt) or nxt in pol['enemy']:flags.append('Zwischenfeld gesperrt')
    if nxt!=target and is_set(cert,nxt) and not any(i!=uid for i in parked.get(nxt,[])):flags.append('Zwischenfeld würde Punkteaufgabe übernehmen')
    return flags or ['Freigabebedingung nicht erfüllt, nicht weiter auflösbar']

def main(n,split):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads();archive=HERE/f'{split}_{n}.jsonl.gz';games=[r for line in gzip.decompress(archive.read_bytes()).splitlines() if (r:=json.loads(line))['force']];out=[];env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for g in games:
            baseline=g['force'];seed,team,op=baseline['seed'],baseline['team'],baseline['opponent'];our,other,a,b,obs=start(env,seed,team,op,'force');cut=None;arr=[];credits=[]
            for t in range(baseline['steps_checked']):
                was=a.active;before=a.path.copy();expect=a.expect;o=obs[our];cmd=a.act(step=t,obs=o);opp=b.act(t,obs[other])
                if was and not a.active and cut is None:cut={'step':t,'flags':reason(a,o,a.selected,before,expect)}
                obs,*_=env.step({our:cmd,other:opp})
                if a.selected:
                    state=env.state;pos=np.asarray(state.units.position)[team];live=np.asarray(state.units_mask)[team]&(np.asarray(state.units.energy)[team,:,0]>=0);target=a.selected['target'];at=(pos[:,0]*24+pos[:,1]==target)&live
                    arr.append(bool(at[a.selected['uid']]));credits.append(bool(at.any()))
            require_no_agent_errors(a.base,b);check(a.selected==baseline['selection'] and a.events==baseline['events'] and arr==[z['arrival'] for z in baseline['after']] and credits==[z['credit'] for z in baseline['after']],'Recorded and replayed trip differ')
            out.append({'seed':seed,'team':team,'opponent':op,'arrived':any(arr),'stop':cut});print(seed,cut,flush=True)
    finally:env.close()
    report={'archive_sha':common.sha(archive),'script_sha':common.sha(HERE/'abbruch.py'),'cases':out,'flags_on_nonarrival':dict(Counter(y for r in out if not r['arrived'] and r['stop'] for y in r['stop']['flags']))}
    common.write_once(HERE/f'abbruch_{split}_{n}.json',report)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('n',type=int);p.add_argument('--split',default='train');q=p.parse_args();main(q.n,q.split)
