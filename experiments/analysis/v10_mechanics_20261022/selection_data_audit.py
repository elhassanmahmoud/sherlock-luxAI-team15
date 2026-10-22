import csv,hashlib,json,math,os,subprocess
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
root=Path('/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics')
d=root/'experiments/analysis/v10_mechanics_20261022'
fields='seed side opponent result game_win point_win our_wins opp_wins our_points opp_points point_counting_version wait_frac invalid_frac greedy_masked_frac sap_attempts sap_hits stack_frac relics_found relics_seen known_point_tiles belief_contradictions unit_steps steps secs'.split()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
errors=[]
def check(c,m):
 if not c:errors.append(m)
summary=json.loads((d/'selection_summary.json').read_text())
freeze=json.loads((d/'source_freeze.json').read_text())
jobs=json.loads((d/'selection_jobs.json').read_text())
state=json.loads((d/'selection_state.json').read_text())
defaults=json.loads((d/'selection_default_jobs.json').read_text())
defstate=json.loads((d/'selection_default_state.json').read_text())
expected={(s,side,'solution92') for s in range(610100,610300) for side in ('player_0','player_1')}
variants={}; maps={}
for name in ('baseline','recovery','drift','combined'):
 p=d/f'selection_{name}_sol.csv';before=sha(p)
 with p.open(newline='') as f:
  reader=csv.DictReader(f);check(reader.fieldnames==fields,name+': CSV schema differs');rows=list(reader)
 actual=[];by_seed={s:0 for s in range(610100,610300)};wins=draws=losses=units=0
 for i,r in enumerate(rows):
  tag=f'{name} row {i}'
  check(set(r)==set(fields),tag+': fields');check(all(v not in ('',None) for v in r.values()),tag+': missing value')
  n={k:float(v) for k,v in r.items() if k not in ('side','opponent')}
  check(all(math.isfinite(v) for v in n.values()),tag+': nonfinite')
  for k in ('seed','steps','our_wins','opp_wins','our_points','opp_points','point_counting_version','unit_steps'):
   check(n[k].is_integer() and n[k]>=0,tag+': invalid '+k)
  check(n['steps']==303 and n['point_counting_version']==2,tag+': course/version')
  check(n['our_wins']+n['opp_wins']<=3,tag+': match wins total')
  result=1 if n['our_wins']>n['opp_wins'] else 0 if n['our_wins']<n['opp_wins'] else .5
  check(n['result']==result and n['game_win']==int(result==1),tag+': result incoherent')
  point=1 if n['our_points']>n['opp_points'] else 0 if n['our_points']<n['opp_points'] else .5
  check(n['point_win']==point,tag+': points incoherent')
  for k in ('wait_frac','invalid_frac','greedy_masked_frac','stack_frac'):
   check(0<=n[k]<=1,tag+': bad fraction '+k)
  check(n['secs']>=0,tag+': negative duration')
  key=(int(n['seed']),r['side'],r['opponent']);actual.append(key)
  check(key in expected,tag+': unexpected key')
  u=int(2*result);units+=u;by_seed[key[0]]+=u
  wins+=result==1;draws+=result==.5;losses+=result==0
 check(len(rows)==400 and len(set(actual))==400 and set(actual)==expected,name+': expected keys failure')
 check(sha(p)==before,name+': changed during read')
 variants[name]=dict(games=len(rows),maps=len(by_seed),wins=int(wins),draws=int(draws),losses=int(losses),half_score_units=units,score_rate=units/800,sha256=before)
 maps[name]=np.array([by_seed[s] for s in sorted(by_seed)],dtype=np.int64)
 for k,v in variants[name].items():check(summary['variants'][name].get(k)==v,name+': summary mismatch '+k)
for name in ('recovery','drift','combined'):
 delta=maps[name]-maps['baseline'];rng=np.random.default_rng(0)
 # Each integer map value is the sum of twice the result on the TWO sides.
 samples=rng.choice(delta,size=(5000,200),replace=True).sum(axis=1)/800
 lo,hi=np.percentile(samples,[2.5,97.5]);diff=int(delta.sum())
 variants[name].update(delta_units=diff,delta=diff/800,low=float(lo),high=float(hi))
 expected_comparison=dict(opponent='solution92',maps=200,games=400,winrate=variants[name]['score_rate'],ref_winrate=variants['baseline']['score_rate'],delta=diff/800,low=float(lo),high=float(hi),excluded_candidate=0,excluded_reference=0)
 check(summary['variants'][name]['comparison']==expected_comparison,name+': comparison mismatch')
rank={'combined':3,'recovery':2,'drift':1}
eligible=[n for n in rank if variants[n]['delta_units']>=8]
nominee=max(eligible,key=lambda n:(variants[n]['delta_units'],rank[n])) if eligible else None
check(nominee=='recovery' and summary['nominee']==nominee,'Nominee mismatch')
check(summary['status']=='selection_solution_complete' and summary['requires_default_guard'] is True,'Summary status mismatch')
ref=root/'experiments/releases/20261022_v10_baseline/agent_p0.pth'
flags={'baseline':('false','false'),'recovery':('true','false'),'drift':('false','true'),'combined':('true','true')}
def expected_args(name,opp,suffix):
 a,b=flags[name]
 return ['--weights',str(ref),'--first','110100','--n','200','--workers','2','--opponents',opp,'--set',f'sap_overkill_recovery={a}','--set',f'nebula_infer_drift_safe={b}','--out',str(d/f'selection_{name}_{suffix}.csv')]
check(jobs=={'name':'selection','jobs':[{'name':n,'args':expected_args(n,'solution92','sol')} for n in flags]},'Selection jobs differ from intended commands')
check(defaults=={'name':'selection_default','jobs':[{'name':n,'args':expected_args(n,'default','default')} for n in ('baseline',nominee)]},'Default jobs differ from intended commands')
check(state['phase']==jobs and state['phase_sha256']==sha(d/'selection_jobs.json'),'Selection state input binding')
check(defstate['phase']==defaults and defstate['phase_sha256']==sha(d/'selection_default_jobs.json'),'Default state input binding')
check(state['status']=='complete' and len(state['jobs'])==4,'Selection completion state')
for rec in state['jobs']:
 name=rec['name'];check(rec['exit_code']==0 and rec['output_sha256']==variants[name]['sha256'],name+': state output binding')
 check(rec['command']==[freeze['source']['python'],'-B','-m','scripts.par_eval',*expected_args(name,'solution92','sol')],name+': recorded command mismatch')
check(defstate['started_at']>state['finished_at'],'Default started before selection completion')
source=freeze['source'];head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip();check(head==source['head'],'HEAD differs from freeze')
changed=[]
for p,h in {**source['files'],**freeze['weights']}.items():
 if not Path(p).exists() or sha(p)!=h:changed.append(p)
check(not changed,'Frozen files changed: '+str(changed))
python=Path(source['python']);check(str(python.resolve())==source['executable'] and sha(python)==source['executable_sha256'],'Python executable differs')
names=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard','--','*.py'],cwd=root).split(b'\0')
paths={root/os.fsdecode(n) for n in names if n}
for name in ('scripts','agents','lux'):paths.update((root/name).rglob('*.py'))
plan=root/'docs/superpowers/plans/2026-10-22-v10-mechanics.md';paths.add(plan)
for name in ('requirements.txt','pyproject.toml'):
 if (root/name).is_file():paths.add(root/name)
venv=python.parent.parent
if (venv/'pyvenv.cfg').is_file():paths.add(venv/'pyvenv.cfg')
for engine in (venv/'lib').glob('python*/site-packages/luxai_s3'):paths.update(engine.rglob('*.py'))
check(set(map(str,paths))==set(source['files']),'Frozen source inventory differs')
check(set(freeze['weights'].values())=={'03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67'},'Frozen weights SHA differs from V10')
committed=subprocess.check_output(['git','show','HEAD:docs/superpowers/plans/2026-10-22-v10-mechanics.md'],cwd=root)
check(committed==plan.read_bytes(),'Plan differs from committed HEAD')
commit_time=int(subprocess.check_output(['git','log','-1','--format=%ct','--',str(plan.relative_to(root))],cwd=root,text=True))
check(commit_time<datetime.fromisoformat(state['started_at']).timestamp(),'Plan not committed before selection start')
report={'reviewed_at':datetime.now(timezone.utc).isoformat(),'errors':errors,'variants':variants,'nominee':nominee,'source_head':head,'frozen_file_count':len(source['files']),'weight_file_count':len(freeze['weights']),'changed_files':changed,'source_inventory_equal':set(map(str,paths))==set(source['files']),'default_jobs_valid':True,'source_freeze_sha256':sha(d/'source_freeze.json'),'selection_summary_sha256':sha(d/'selection_summary.json'),'selection_default_jobs_sha256':sha(d/'selection_default_jobs.json'),'selection_jobs_sha256':sha(d/'selection_jobs.json')}
Path('/tmp/sherlock-v10-fixes-20261022/selection-data-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
