import csv,hashlib,itertools,json,re
from pathlib import Path
root=Path.cwd();arc=root/'experiments/analysis/action_student_20261104';d=arc/'diagnostic';tmp=Path('/tmp/sherlock-action-student-20261104')
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=read(d/'diagnostic_review.json');s=read(d/'state.json');p=read(arc/'preflight/diagnostic_protocol.json');c=read(d/'root_crosscheck.json')
assert s['status']=='complete' and s['completed']==17 and not s['running'] and s['pins_after_equal']
assert sha(arc/'preflight/diagnostic_protocol.json')==s['protocol_sha256']
assert sha(arc/'preflight/run_diagnostic.py')==s['controller_sha256']
assert sha(arc/'preflight/audit_final.py')==a['auditor_sha256']
assert sha(d/'diagnostic_review.json')==c['independent_audit_sha256'] and sha(d/'state.json')==c['controller_state_sha256']
rows={};total=0
for job in s['jobs']:
 assert job['status']=='completed' and job['returncode']==0
 group=job['kind'];role=job['role'];path=d/group/(role+'.csv');h=sha(path)
 assert h==job['csv_sha256']==a['source_csv_sha256'][f'{group}/{role}.csv']
 guard=read(d/'guards'/(job['name']+'.json'));assert guard['status']=='completed' and guard['returncode']==0
 rr=list(csv.DictReader(path.open()));rows[group,role]=rr;total+=len(rr)
 seeds=p['panel_seeds'] if group=='panel' else p['direct_seeds'];opps=p['opponents'] if group=='panel' else [p['direct_opponent']]
 keys=[(int(r['seed']),r['side'],r['opponent']) for r in rr]
 assert len(keys)==len(set(keys)) and set(keys)==set(itertools.product(seeds,['player_0','player_1'],opps))
 for r in rr:
  assert int(r['steps'])==303 and int(r['point_counting_version'])==2
  ours,other=int(r['our_wins']),int(r['opp_wins']);result=1. if ours>other else 0. if ours<other else .5
  assert float(r['result'])==result and int(r['game_win'])==int(result==1)
 def wdl(x):return [sum(float(r['result'])==v for r in x) for v in (1.,.5,0.)]
 summary=a['summaries'][role]['pooled_three_opponent_panel'] if group=='panel' else a['direct_against_V14'][role]
 assert wdl(rr)==[summary[k] for k in ('wins','draws','losses')]
 if group=='panel':
  for o in opps:
   q=a['summaries'][role]['by_opponent'][o];assert wdl([r for r in rr if r['opponent']==o])==[q[k] for k in ('wins','draws','losses')]
assert total==1400
# Verify the stated zero-difference degeneracy from actual paired card results.
for seed in p['panel_seeds']:
 def sol(role):return sum(float(r['result']) for r in rows['panel',role] if int(r['seed'])==seed and r['opponent']=='solution92')/2
 assert sol('A2')==sol('V14')
# Validate links in newly authored report and archive/candidate overview.
links=0
for f in (root/'docs/AKTIONSSCHUELER_20261104.md',arc/'README.md',root/'experiments/candidates/action_student_20261104/README.md'):
 for target in re.findall(r'\]\(([^)]+)\)',f.read_text()):
  if '://' in target or target.startswith('#'):continue
  destination=(f.parent/target.split('#')[0]).resolve();assert destination.exists(),(f,target);links+=1
result=dict(status='passed',jobs=17,games=total,exact_csv_hashes=17,whole_key_sets_and_303_v2=True,outcome_wdl_agrees=True,paired_A2_V14_Solution_zero_all20=True,protocol_controller_audit_state_hash_chain=True,local_links=links,model_work=False,new_games=False)
(tmp/'final_static_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
