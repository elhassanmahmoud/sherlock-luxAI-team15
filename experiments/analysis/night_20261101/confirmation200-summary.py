"""200-map time amendment; unchanged predeclared strength gates and frozen game inputs."""
import hashlib,json,sys
from pathlib import Path
import pandas as pd
ROOT=Path('/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics'); D=ROOT/'experiments/analysis/night_20261101'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(D))
from scripts.compare_report import compare_results
from scripts.league_gates import panel_delta,direct_result,EPS
from run_jobs import validate_output

PANEL=('solution92','sol92_sq',
       'self:experiments/releases/20261022_all18_v3/agent_p0.pth',
       'self:experiments/releases/20261022_v7_Bsnpd/agent_p0.pth',
       'self:experiments/releases/20261022_v10_baseline/agent_p0.pth',
       'self:experiments/releases/20261101_v13_neb/agent_p0.pth')
REFERENCE='self:experiments/releases/20261101_v14_baseline/agent_p0.pth'

def counts(frame,opponent):
    r=frame.loc[frame.opponent==opponent,'result']
    return dict(games=len(r),wins=int((r==1).sum()),draws=int((r==.5).sum()),losses=int((r==0).sum()))


def main():
    phase=sys.argv[1]
    if phase != 'confirmation200':raise ValueError(phase)
    target=D/f'{phase}_summary.json'
    if target.exists():raise FileExistsError(target)
    state=json.loads((D/f'{phase}_state.json').read_text())
    assert state['status']=='complete'
    spec=state['phase'];panel=tuple(spec['panel']);ref_opp=spec['direct_opponent']
    assert spec['name']==phase
    amendment=D/'confirmation_time_addendum.json'
    expected_amendment='3319dcfa8cec9b979945cd6fe9e12fb41d5a53e2ccf7d41885450eae158e2aaf'
    assert hashlib.sha256(amendment.read_bytes()).hexdigest()==expected_amendment
    assert spec['time_addendum_sha256']==expected_amendment
    assert spec['summary_tool_sha256']==hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    selection_freeze=D/'selection_freeze.json'
    assert spec['selection_freeze_sha256']==hashlib.sha256(selection_freeze.read_bytes()).hexdigest()
    assert json.loads((D/f'{phase}_freeze.json').read_text())==json.loads(selection_freeze.read_text()), 'Selection/confirmation frozen inputs differ'

    assert panel==PANEL and ref_opp==REFERENCE
    original=Path(spec['manifest_path'])
    assert hashlib.sha256(original.read_bytes()).hexdigest()==state['phase_sha256']
    assert spec==json.loads(original.read_text()), 'Journal differs from preregistered phase'
    if phase=='selection':
        assert spec['candidates']==[n for n in ('overlap','control','discovery') if n in spec['candidates']]
    else:
        selection=D/'selection_summary.json'
        assert hashlib.sha256(selection.read_bytes()).hexdigest()==spec['selection_sha256']
        assert json.loads(selection.read_text())['nominee']==spec['candidate']
    expected_names=['baseline']
    for name in (spec['candidates'] if phase=='selection' else [spec['candidate']]):
        expected_names += [name,name+'_direct']
    assert [j['name'] for j in spec['jobs']]==expected_names
    assert [j['name'] for j in state['jobs']]==expected_names
    frames={};csv_hashes={}
    for job,planned in zip(state['jobs'],spec['jobs']):
        args=job['command'];path=Path(args[args.index('--out')+1])
        assert args[1:]==['-B','-m','scripts.par_eval',*planned['args']], 'Actual command differs from planned job'
        direct=job['name'].endswith('_direct')
        assert int(args[args.index('--n')+1])==(50 if phase=='selection' else 200)
        expected_first=331000 if phase=='selection' else (333000 if direct else 332000)
        assert int(args[args.index('--first')+1])==expected_first
        assert args[args.index('--opponents')+1]==(REFERENCE if direct else ','.join((*PANEL,'default')))
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
                 promotion_qualified=results[spec['candidate']]['passed'],
                 completed_games=sum(len(x) for x in frames.values()))
    with target.open('x') as f:json.dump(summary,f,indent=2)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
