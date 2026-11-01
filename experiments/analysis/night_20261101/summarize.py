"""Summarize only complete, hash-verified preregistered night phases."""
import hashlib,json,sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]; D=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.compare_report import compare_results
from scripts.league_gates import panel_delta,direct_result,EPS
from run_jobs import validate_output


def counts(frame,opponent):
    r=frame.loc[frame.opponent==opponent,'result']
    return dict(games=len(r),wins=int((r==1).sum()),draws=int((r==.5).sum()),losses=int((r==0).sum()))


def main():
    phase=sys.argv[1]
    if phase not in ('selection','confirmation'):raise ValueError(phase)
    target=D/f'{phase}_summary.json'
    if target.exists():raise FileExistsError(target)
    state=json.loads((D/f'{phase}_state.json').read_text())
    assert state['status']=='complete'
    spec=state['phase'];panel=tuple(spec['panel']);ref_opp=spec['direct_opponent']
    assert len(panel)==6 and len(set(panel))==6
    original=Path(spec['manifest_path'])
    assert hashlib.sha256(original.read_bytes()).hexdigest()==state['phase_sha256']
    frames={};csv_hashes={}
    for job in state['jobs']:
        args=job['command'];path=Path(args[args.index('--out')+1])
        assert job['exit_code']==0 and hashlib.sha256(path.read_bytes()).hexdigest()==job['output_sha256']
        validate_output(path,args)
        frames[job['name']]=pd.read_csv(path);csv_hashes[path.name]=job['output_sha256']
    assert len(frames)==len(spec['jobs'])
    baseline=frames['baseline'];results={};chosen=None
    names=spec['candidates'] if phase=='selection' else [spec['candidate']]
    for name in names:
        cand=frames[name];direct=frames[name+'_direct']
        comparisons={r['opponent']:r for r in compare_results(cand,baseline)}
        p=panel_delta(cand,baseline,panel=panel);d=direct_result(direct,ref_opp)
        sol=comparisons['solution92'];default=comparisons['default']
        if phase=='selection':
            gates=dict(panel_delta=p['delta']>=.005-EPS,solution=sol['delta']>=-EPS,
                       default=default['winrate']>=.99-EPS,direct=d['winrate']>=.5-EPS)
        else:
            gates=dict(panel_delta=p['delta']>=.01-EPS,panel_lower=p['low']>EPS,
                solution_delta=sol['delta']>=-EPS,solution_lower=sol['low']>=-.01-EPS,
                default=default['winrate']>=.99-EPS,default_delta=default['delta']>=-.01-EPS,
                direct_lower=d['low']>.5+EPS)
        entry=dict(panel=p,direct=d,opponents=comparisons,gates={k:bool(v) for k,v in gates.items()},
                   counts={o:dict(baseline=counts(baseline,o),candidate=counts(cand,o)) for o in (*panel,'default')})
        entry['passed']=all(entry['gates'].values());results[name]=entry
        if phase=='selection' and entry['passed']:
            if chosen is None or p['delta']>results[chosen]['panel']['delta']+EPS:chosen=name
    summary=dict(phase=phase,panel=panel,source_state=str(D/f'{phase}_state.json'),csv_sha256=csv_hashes,
                 candidates=results,nominee=chosen if phase=='selection' else spec['candidate'],
                 promotion_qualified=(results[spec['candidate']]['passed'] if phase=='confirmation' else False),
                 completed_games=sum(len(x) for x in frames.values()))
    with target.open('x') as f:json.dump(summary,f,indent=2)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
