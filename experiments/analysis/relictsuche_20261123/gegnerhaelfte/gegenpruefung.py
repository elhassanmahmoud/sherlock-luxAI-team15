"""Independently audit already enumerated V16-marked routes against the known original referee trajectories."""
from pathlib import Path
from hashlib import sha256
import base64,gzip,json,zlib
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv
from scripts.scoring import point_tile_map,match_points_after_step
from scripts.experiment import limit_threads

HERE=Path(__file__).resolve().parent


def run():
    limit_threads()
    with gzip.open(HERE/'markierungen.jsonl.gz','rt') as f:allrows=list(map(json.loads,f))
    with gzip.open(HERE.parent/'punktwissen/allgemein_partien.jsonl.gz','rt') as f:arch={(r['seed'],r['team']):r for r in map(json.loads,f) if r['version']=='v16' and r['opponent']=='solution92'}
    result=[];env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for i,r in enumerate(allrows):
            if not r['additional_offers']:continue
            team=r['team'];score_rows=[];real=[];ref=arch[r['seed'],team];data=np.frombuffer(zlib.decompress(base64.b64decode(ref['tape'])),np.int8).reshape(303,2,16,3)
            assert sha256(data.astype('<i4').tobytes()).hexdigest()==ref['digest']==r['archive_digest'];side=f'player_{team}';obs,_=env.reset(seed=r['seed']);offers=r['additional_offers']
            for t in range(101):
                before=obs[side];out=env.step({f'player_{tm}':data[t,tm].astype(np.int32) for tm in (0,1)});obs=out[0];st=out[4]['final_state'];grid=point_tile_map(st);alive=np.asarray(st.units_mask,bool)[team]&(np.asarray(st.units.energy)[team,:,0]>=0);pos=np.asarray(st.units.position)[team]
                individuals={}
                for uid in np.flatnonzero(alive):
                    x,y=map(int,pos[uid]);
                    if grid[x,y]:individuals.setdefault((x,y),[]).append(int(uid))
                score=match_points_after_step(before,obs[side],out[4]);assert int(score[team]-before['team_points'][team])==len(individuals)
                score_rows.append({p:l for p,l in individuals.items() if (sum(p)<23 if team else sum(p)>23)})
                for o in offers:
                    if o['t']==t:real.append(bool(grid[tuple(o['goal'])]))
            assert score[[team,1-team]].tolist()==ref['matches'][0]['points'];first=next((j for j,x in enumerate(score_rows) if x),None);assert first==r['first_away'] and len(real)==len(offers)
            for o,was_real in zip(offers,real):
                t,u=o['t'],o['uid'];g=tuple(o['goal']);actual=first is not None and t<=first<t+12 and score_rows[first].get(g)==[u]
                value=sum(x.get(g)==[u] for x in score_rows[first:t+12]) if actual else 0
                result.append(dict(seed=r['seed'],team=team,t=t,uid=u,goal=list(g),split='training' if i<36 else 'prüfung',real_point=was_real,natural_first=first,proposed_value=value))
    finally:env.close()
    (HERE/'wege_gegengeprueft.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print('Proposals',len(result),'true targets',sum(r['real_point'] for r in result),'positive value',sum(r['proposed_value']>0 for r in result))


if __name__=='__main__':run()
