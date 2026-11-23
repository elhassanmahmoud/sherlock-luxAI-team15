"""Distinguish original public V16 positive cells from the stronger separate score proof in the same diagnostic."""
import argparse,gzip,json
from types import SimpleNamespace
import numpy as np
import kontakt
from kontakt import s
from modell import fit,predict


def run(lane):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    rows=kontakt.select();s.limit_threads();env=LuxAIS3GymEnv(numpy_output=True);folder=s.WORK/'markierung'
    sign=''.join(s.sha(s.HERE/f) for f in ('markierung.py','kontakt.py','lernen.py','KONTAKTPLAN.md','V16_MARKIERUNG.md'))+s.sha(s.ARCH)
    original=kontakt.choices
    try:
        for i in range(lane,60,2):
            r=rows[i];p=folder/f'{i:02d}.json';extra=[]
            if p.exists():
                assert json.loads(p.read_bytes())['source']==sign;continue
            def flagged(agent,o,a,t,view,proof):
                canon=np.asarray(agent._imitation.belief.point_tiles,bool);physical=canon[::-1,::-1].T if agent.team_id else canon
                ids=np.flatnonzero(physical);pairs={min(int(k),(23-int(k%24))*24+23-int(k//24)) for k in ids}
                public=SimpleNamespace(positive=proof.positive|sum(1<<k for k in pairs))
                if public.positive and view is not None:
                    candidate=s.offer(agent,o,a,t,True,public)
                    if candidate is not None:extra.append(candidate)
                return original(agent,o,a,t,view,public)
            kontakt.choices=flagged
            try:data=kontakt.replay(env,r,sign)
            finally:kontakt.choices=original
            data['additional_offers']=extra;s.write_once(p,data);print(i,bool(data['event']),len(extra),flush=True)
    finally:env.close()


def evaluate():
    rows=[json.loads((s.WORK/'markierung'/f'{i:02d}.json').read_bytes()) for i in range(60)]
    orig=[json.loads((s.WORK/'natuerlich'/f'{i:02d}.json').read_bytes()) for i in range(60)]
    for a,b in zip(rows,orig):assert (a['seed'],a['team'],a['first_view'],a['first_away'],a['archive_digest'])==(b['seed'],b['team'],b['first_view'],b['first_away'],b['archive_digest'])
    groups=rows[:36],rows[36:];events=[[r['event'] for r in group if r['event']] for group in groups]
    (x,y),(xx,yy)=[(np.array([v['x'] for v in es],float).reshape(-1,len(kontakt.NAMES)),np.array([v['y'] for v in es],float)) for es in events]
    models={};scores={};loss={};ci=None
    if len(x) and len(xx):
        for n,c in [('constant',[]),('time_sensor',[0,1]),('model',list(range(len(kontakt.NAMES))))]:
            m=fit(x,y,np.ones(len(y)),c);pr=predict(m,xx);models[n]=m;loss[n]=(pr-yy)**2;scores[n]=dict(mse=float(loss[n].mean()),mae=float(abs(pr-yy).mean()),mean=float(pr.mean()))
        b=min(('constant','time_sensor'),key=lambda n:scores[n]['mse']);d=loss[b]-loss['model'];draw=np.random.default_rng(231123).integers(0,len(d),(20000,len(d)));ci=np.quantile(d[draw].mean(1),[.025,.975]).tolist()
    summary=dict(maps=[36,24],natural=[sum(r['first_away'] is not None for r in rr) for rr in groups],supported=[len(y),len(yy)],mean_value=[float(v.mean()) if len(v) else None for v in (y,yy)],
                 additional_offer_cards=[sum(bool(r['additional_offers']) for r in rr) for rr in groups],additional_offers=[sum(len(r['additional_offers']) for r in rr) for rr in groups],
                 models=models,holdout=scores,better_mse_ci95=ci,accepted=bool(ci and ci[0]>0 and len(y)>=8 and len(yy)>=8),features=kontakt.NAMES,source=rows[0]['source'])
    (s.HERE/'markierungsmodell.json').write_text(json.dumps(summary,indent=2)+'\n');(s.HERE/'markierungen.jsonl.gz').write_bytes(gzip.compress(b''.join(json.dumps(r,separators=(',',':')).encode()+b'\n' for r in rows),mtime=0));print({k:v for k,v in summary.items() if k not in ('models','features','source')})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('0','1','fit'));args=p.parse_args();evaluate() if args.mode=='fit' else run(int(args.mode))
