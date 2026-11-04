"""Root cross-check after the independent auditor accepts all fixed games."""
import argparse,datetime,hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
import pandas as pd

root=Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
sys.path.insert(0,str(root))
from scripts.compare_report import compare_results
ap=argparse.ArgumentParser();ap.add_argument('--audit',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
assert not args.out.exists()
tmp=Path('/tmp/sherlock-action-student-20261104');protocol=json.loads((tmp/'diagnostic_protocol.json').read_text());diag=Path(protocol['output_directory'])
state=json.loads((diag/'state.json').read_text());audit=json.loads(args.audit.read_text())
assert state['status']=='complete' and state['completed']==17 and not state['running']
assert audit['integrity']=='complete' and audit['games']==1400
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==protocol['source_commit']
for p,h in protocol['source_sha256'].items():assert sha(root/p)==h,p
for p,h in protocol['inputs_sha256'].items():assert sha(p)==h,p
assert state['protocol_sha256']==sha(tmp/'diagnostic_protocol.json')
assert state['controller_sha256']==sha(tmp/'run_diagnostic.py')
assert datetime.datetime.fromisoformat(state['finished_utc'])<datetime.datetime.fromisoformat(protocol['deadline_utc'].replace('Z','+00:00'))
for job in state['jobs']:
    g=json.loads(Path(job['guard']).read_text())
    assert job['status']=='completed' and job['returncode']==0 and g['status']=='completed' and g['returncode']==0
    assert sha(job['csv'])==job['csv_sha256']
bad_logs=[]
for p in (diag/'guards').glob('*.log'):
    text=p.read_text()
    if 'Traceback (most recent call last)' in text or 'Fehler in ' in text:bad_logs.append(str(p))
assert not bad_logs,bad_logs
for rel,h in audit['source_csv_sha256'].items():assert sha(diag/rel)==h
panels={role:pd.read_csv(diag/'panel'/f'{role}.csv') for role in protocol['roles']}
pairs=[(r,'V14',audit['comparisons_against_V14'][r]) for r in protocol['roles']]
pairs.extend((f'SAP0{s}',f'CONTROL{s}',audit['reward_comparisons'][str(s)]) for s in (27,28))
pairs.append(('A2','S30',audit['A2_against_S30']))
for ens,items in audit['ensemble_against_constituents'].items():pairs.extend((ens,r,v) for r,v in items.items())
checks=0
def equal(a,b):
    global checks
    assert np.allclose(a,b,rtol=0,atol=1e-12),(a,b)
    checks+=1
comparisons=[]
for candidate,reference,expected in pairs:
    actual=compare_results(panels[candidate],panels[reference])
    for row in actual:
        e=expected['by_opponent'][row['opponent']]
        assert row['maps']==20 and row['games']==40 and row['excluded_candidate']==row['excluded_reference']==0
        equal(row['delta'],e['score_difference']);equal([row['low'],row['high']],e['percentile_95_ci'])
        equal(row['winrate'],audit['summaries'][candidate]['by_opponent'][row['opponent']]['draw_half_score'])
        equal(row['ref_winrate'],audit['summaries'][reference]['by_opponent'][row['opponent']]['draw_half_score'])
    a=panels[candidate].groupby('seed')['result'].mean().sort_index();b=panels[reference].groupby('seed')['result'].mean().sort_index()
    assert list(a.index)==list(b.index)==protocol['panel_seeds']
    delta=(a-b).to_numpy();bootstrap=np.random.default_rng(0).choice(delta,size=(5000,20)).mean(1)
    e=expected['pooled_three_opponent_panel'];equal(delta.mean(),e['score_difference']);equal(np.percentile(bootstrap,[2.5,97.5]),e['percentile_95_ci'])
    comparisons.append({'candidate':candidate,'reference':reference,'three_opponents_and_pooled_equal':True})
for role,expected in audit['direct_against_V14'].items():
    frame=pd.read_csv(diag/'direct'/f'{role}.csv');assert len(frame)==40 and frame['seed'].nunique()==20
    for metric,values in [('candidate_score',frame['result']),('candidate_win_fraction',(frame['result']==1).astype(float)),('V14_score',1-frame['result']),('V14_win_fraction',(frame['result']==0).astype(float))]:
        grouped=values.groupby(frame['seed']).mean().sort_index().to_numpy()
        bootstrap=np.random.default_rng(0).choice(grouped,size=(5000,20)).mean(1)
        equal(grouped.mean(),expected[metric]['estimate']);equal(np.percentile(bootstrap,[2.5,97.5]),expected[metric]['percentile_95_ci'])
    assert expected['wins']==int((frame['result']==1).sum()) and expected['draws']==int((frame['result']==.5).sum()) and expected['losses']==int((frame['result']==0).sum())
candidate_manifest=json.loads((root/'experiments/candidates/action_student_20261104/manifest.json').read_text())
for role,item in candidate_manifest['roles'].items():assert sha(root/item['archive_path'])==sha(root/item['original_path'])==item['sha256']
result={'status':'passed','completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':protocol['source_commit'],'source_files':len(protocol['source_sha256']),'pinned_inputs':len(protocol['inputs_sha256']),'jobs':17,'games':1400,'numeric_equalities':checks,'comparisons':comparisons,'direct_roles':8,'caught_exception_logs':bad_logs,'all_candidate_copies_equal':True,'all_protected_inputs_unchanged':True,'independent_audit_sha256':sha(args.audit),'controller_state_sha256':sha(diag/'state.json'),'limit':'Reuses existing compare_report for opponent intervals; independent explicit pooled/direct calculation. Does not rerun engine scoring or games.'}
args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
