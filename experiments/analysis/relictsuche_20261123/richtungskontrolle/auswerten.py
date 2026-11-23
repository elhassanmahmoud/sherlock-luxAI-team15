"""Summarize paired interventions, selected denominators, and each match from the verified archive."""
import csv
import gzip
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def horizon(row,step):
    k=row['knowledge']
    before=k[step]['coverage']-k[step]['novel']
    return dict(new1=k[step]['novel'],new8=k[step+7]['coverage']-before,
                new20=k[min(step+19,99)]['coverage']-before,
                known1=k[100]['known'],known2=k[201]['known'],known3=k[302]['known'])


def metrics(row):
    o={k:row[k] for k in ('win','sight','credit')}
    o.update({f'match{j+1}':m['win'] for j,m in enumerate(row['matches'])})
    o.update({f'margin{j+1}':m['points'][0]-m['points'][1] for j,m in enumerate(row['matches'])})
    o.update(horizon(row,row['decision']['step']))
    return o


def main():
    with gzip.open(HERE/'partien.jsonl.gz','rt') as f:rows=list(map(json.loads,f))
    keys={(r['seed'],r['team'],r['arm']):r for r in rows}
    assert len(keys)==len(rows)
    bases=[r for r in rows if r['arm']=='original'];assert len(bases)==20
    pairs=[];missing={};records=[];rejections={}
    for base in bases:
        s,t=base['seed'],base['team'];d=base['decision']
        if d is None or d['alternative'] is None:
            key=f'{s}_{t}'
            missing[key]='kein abweichender Scoutzug' if d is None else 'keine gleichwertige sichere Gegenrichtung'
            if d is not None:
                ref=d['views'][str(d['learned'])]
                fails={}
                for number,other in d['views'].items():
                    if int(number) in (d['original'],d['learned']):continue
                    issues=[]
                    if ref['fog']!=other['fog']:issues.append('Nebel')
                    if abs(ref['energy']-other['energy'])>2:issues.append('Energie')
                    if abs(ref['gain']-other['gain'])>1:issues.append('Sichtgewinn')
                    assert issues
                    fails[number]=issues
                rejections[key]=fails
            continue
        maps={a:keys[s,t,a] for a in ('original','gelernt','alternative')}
        pairs.append({a:metrics(r) for a,r in maps.items()}|{'seed':s,'team':t})
    assert len(rows)==20+2*len(pairs)
    indicators=list(metrics(next(r for r in rows if r['arm']=='gelernt'))) if pairs else []
    totals={a:{k:sum(p[a][k] for p in pairs) for k in indicators} for a in ('original','gelernt','alternative')}
    cards=sorted({p['seed'] for p in pairs});positive=sorted({p['seed'] for p in pairs if any((p['gelernt'][k]<p['alternative'][k] if k in ('sight','credit') else p['gelernt'][k]>p['alternative'][k]) for k in ('win','sight','credit'))})
    diff={k:(totals['gelernt'][k]-totals['alternative'][k]) for k in indicators}
    wins={f'{a}_vs_{b}':dict(won=sum(p[a]['win']>p[b]['win'] for p in pairs),lost=sum(p[a]['win']<p[b]['win'] for p in pairs),same=sum(p[a]['win']==p[b]['win'] for p in pairs)) for a,b in (('gelernt','original'),('alternative','original'),('gelernt','alternative'))}
    new_gate=len(pairs)>=8 and len(cards)>=4 and diff['win']>0 and (diff['sight']<0 or diff['credit']<0) and len(positive)>=2
    for r in rows:
        d=r['decision'];x=metrics(r) if d and d['alternative'] is not None else {}
        record=dict(seed=r['seed'],team=r['team'],arm=r['arm'],eligible=bool(d and d['alternative'] is not None),step=None if d is None else d['step'],uid=None if d is None else d['uid'],
                    learned=None if d is None else d['learned'],alternative=None if d is None else d['alternative'],estimated_learned=None if d is None else d['views'][str(d['learned'])]['gain'],
                    estimated_alternative=d['views'][str(d['alternative'])]['gain'] if d and d['alternative'] is not None else None,
                    digest=r['digest'],win=r['win'],sight=r['sight'],credit=r['credit'],**{f'match_{i+1}':'-'.join(map(str,m['points'])) for i,m in enumerate(r['matches'])})
        record.update({k:x.get(k) for k in ('new1','new8','new20','known1','known2','known3')});records.append(record)
    with (HERE/'sitzprotokoll.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    summary=dict(originals=len(bases),games=len(rows),original_losses=sum(1-r['win'] for r in bases),eligible=len(pairs),eligible_cards=cards,excluded=missing,
                 rejected_directions=rejections,eligible_original_losses=sum(1-p['original']['win'] for p in pairs),totals=totals,learned_minus_alternative=diff,paired_wins=wins,
                 gate_contributing_cards=positive,independent_gate=bool(new_gate),per_pair=pairs)
    (HERE/'bilanz.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='per_pair'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
