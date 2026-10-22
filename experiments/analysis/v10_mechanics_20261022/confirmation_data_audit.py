import csv,hashlib,json,math,os,subprocess
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
ROOT=Path('/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics');D=ROOT/'experiments/analysis/v10_mechanics_20261022'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda n:json.loads((D/n).read_text())
summary=load('confirmation_summary.json');state=load('confirmation_state.json');jobs=load('confirmation_jobs.json');freeze=load('source_freeze.json');admission=load('confirmation_admission.json');closing=load('closing_scope_20261022.json')
errors=[]
def ck(v,label):
 if not v:errors.append(label)
FIELDS='seed side opponent result game_win point_win our_wins opp_wins our_points opp_points point_counting_version wait_frac invalid_frac greedy_masked_frac sap_attempts sap_hits stack_frac relics_found relics_seen known_point_tiles belief_contradictions unit_steps steps secs'.split()
SIDES=('player_0','player_1');OPP=('default','solution92');SEEDS=range(611000,611800)
expected={(o,s,p) for o in OPP for s in SEEDS for p in SIDES}
counts={};byarm={};csvhash={};identity={}
for arm in ('baseline','recovery'):
 path=D/f'confirmation_{arm}.csv';before=sha(path)
 with path.open(newline='') as f:
  reader=csv.DictReader(f);ck(reader.fieldnames==FIELDS,arm+': schema');rows=list(reader)
 indexed={}
 for i,row in enumerate(rows):
  label=f'{arm}:{i}';ck(set(row)==set(FIELDS),label+': row fields')
  nums={k:float(v) for k,v in row.items() if k not in ('opponent','side')}
  ck(all(math.isfinite(v) for v in nums.values()),label+': finite')
  integer_fields=('seed','steps','our_wins','opp_wins','our_points','opp_points','point_counting_version','sap_attempts','sap_hits','relics_found','relics_seen','known_point_tiles','belief_contradictions','unit_steps')
  ck(all(nums[k].is_integer() and nums[k]>=0 for k in integer_fields),label+': count')
  ck(nums['steps']==303 and nums['point_counting_version']==2,label+': course/version')
  ck(nums['our_wins']+nums['opp_wins']<=3,label+': match wins')
  result=1 if nums['our_wins']>nums['opp_wins'] else 0 if nums['our_wins']<nums['opp_wins'] else .5
  ck(nums['result']==result and nums['game_win']==int(result==1),label+': result coherence')
  point=1 if nums['our_points']>nums['opp_points'] else 0 if nums['our_points']<nums['opp_points'] else .5
  ck(nums['point_win']==point,label+': points coherence')
  ck(all(0<=nums[k]<=1 for k in ('wait_frac','invalid_frac','greedy_masked_frac','stack_frac')) and nums['secs']>=0,label+': fractional metric')
  key=(row['opponent'],int(nums['seed']),row['side']);ck(key in expected and key not in indexed,label+': unique planned key');indexed[key]=int(2*result)
 ck(len(rows)==3200 and len(indexed)==3200 and set(indexed)==expected,arm+': exact key set')
 ck(sha(path)==before,arm+': unchanged while reading');csvhash[path.name]=before;byarm[arm]=indexed
 counts[arm]=len(rows)
 identity[arm]=dict(csv_sha256=before,csv_size=path.stat().st_size,csv_mtime_utc=datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat())
results={}
for opp in OPP:
 units={arm:[byarm[arm][(opp,s,p)] for s in SEEDS for p in SIDES] for arm in byarm}
 totals={arm:dict(wins=u.count(2),draws=u.count(1),losses=u.count(0),half_score_units=sum(u),score=sum(u)/3200) for arm,u in units.items()}
 # Independent paired resampling of integer totals per map; both sides stay together.
 ref=np.array(units['baseline'],dtype=np.int16).reshape(800,2).sum(axis=1,dtype=np.int16)
 cand=np.array(units['recovery'],dtype=np.int16).reshape(800,2).sum(axis=1,dtype=np.int16)
 differences=cand-ref;delta_units=int(differences.sum());sampled=np.random.default_rng(0).choice(differences,size=(5000,800),replace=True).sum(axis=1)/3200
 ci=[float(v) for v in np.percentile(sampled,[2.5,97.5])]
 passed=(totals['recovery']['half_score_units']>=3168 and delta_units>=-32) if opp=='default' else (delta_units>=64 and ci[0]>0)
 result=dict(maps=800,games_per_arm=1600,baseline=totals['baseline'],recovery=totals['recovery'],delta_units=delta_units,denominator=3200,delta=delta_units/3200,ci95=ci,gate_passed=bool(passed))
 ck(summary['opponents'][opp]==result,opp+': summary mismatch');results[opp]=result
ck(summary['phase']=='confirmation' and summary['nominee']=='recovery' and summary['files']==csvhash and summary['all_phase_gates_passed']==all(r['gate_passed'] for r in results.values()),'Summary overall mismatch')
source=freeze['source'];reference=ROOT/'experiments/releases/20261022_v10_baseline/agent_p0.pth'
expected_jobs={'name':'confirmation','jobs':[]}
for arm in ('baseline','recovery'):
 args=['--weights',str(reference),'--first','111000','--n','800','--workers','2','--opponents','default,solution92','--set','sap_overkill_recovery='+('true' if arm=='recovery' else 'false'),'--set','nebula_infer_drift_safe=false','--out',str(D/f'confirmation_{arm}.csv')]
 expected_jobs['jobs'].append({'name':arm,'args':args})
ck(jobs==expected_jobs and state['phase']==expected_jobs,'Manifest/phase mismatch')
ck(state['phase_sha256']==sha(D/'confirmation_jobs.json') and state['status']=='complete' and len(state['jobs'])==2,'Phase hash/completion')
for expected_job,record in zip(expected_jobs['jobs'],state['jobs']):
 arm=expected_job['name'];ck(record['name']==arm and record['exit_code']==0 and record['command']==[source['python'],'-B','-m','scripts.par_eval',*expected_job['args']],'Command/exit binding '+arm)
 ck(record['output_sha256']==csvhash[f'confirmation_{arm}.csv'],'Output hash binding '+arm)
 ck(record['started_at']<record['finished_at'],'Job timestamp '+arm)
ck(state['started_at']<=state['jobs'][0]['started_at']<state['jobs'][0]['finished_at']<state['jobs'][1]['started_at']<state['jobs'][1]['finished_at']<=state['finished_at']<summary['audited_at'],'Phase timestamp sequence')
ck(admission['admitted_at']<state['started_at'] and admission['nominee']=='recovery','Admission sequence/nominee')
for n,h in admission['inputs'].items():ck(sha(D/n)==h,'Admission binding '+n)
ck(closing['admitted_phase_to_complete']=='confirmation' and closing['new_experiment_phases_allowed'] is False and closing['candidate_results_seen'] is False and closing['source_freeze_unchanged'] is True,'Closing scope flags')
ck(state['jobs'][1]['started_at']<closing['recorded_at']<state['jobs'][1]['finished_at'],'Closing timestamp candidate completion order')
ck(closing['recorded_at']<identity['recovery']['csv_mtime_utc'],'Closing timestamp vs final CSV write')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();ck(head==source['head'],'HEAD changed')
changed=[]
for p,h in {**source['files'],**freeze['weights']}.items():
 if not Path(p).exists() or sha(p)!=h:changed.append(p)
ck(not changed,'Frozen file hashes changed')
py=Path(source['python']);ck(str(py.resolve())==source['executable'] and sha(py)==source['executable_sha256'],'Interpreter changed')
names=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard','--','*.py'],cwd=ROOT).split(b'\0');paths={ROOT/os.fsdecode(n) for n in names if n}
for n in ('scripts','agents','lux'):paths.update((ROOT/n).rglob('*.py'))
plan=ROOT/'docs/superpowers/plans/2026-10-22-v10-mechanics.md';paths.add(plan)
for n in ('requirements.txt','pyproject.toml'):
 if (ROOT/n).is_file():paths.add(ROOT/n)
venv=py.parent.parent
if (venv/'pyvenv.cfg').is_file():paths.add(venv/'pyvenv.cfg')
for engine in (venv/'lib').glob('python*/site-packages/luxai_s3'):paths.update(engine.rglob('*.py'))
ck(set(map(str,paths))==set(source['files']),'Source inventory changed')
ck(set(freeze['weights'].values())=={'03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67'},'Unexpected weight identity')
ck(subprocess.check_output(['git','show','HEAD:docs/superpowers/plans/2026-10-22-v10-mechanics.md'],cwd=ROOT)==plan.read_bytes(),'Plan not committed unchanged')
no_later_artifacts=[str(p.name) for p in D.iterdir() if p.is_file() and any(x in p.name for x in ('direct_', 'robustness_', 'stronger_'))]
ck(not no_later_artifacts,'Unexpected later phase artifacts: '+str(no_later_artifacts))
report=dict(checked_at=datetime.now(timezone.utc).isoformat(),errors=errors,verdict='valid_confirmation_no_qualifying_improvement',total_games=sum(counts.values()),results=results,csv_identity=identity,source_head=head,frozen_source_files=len(source['files']),frozen_weights=len(freeze['weights']),frozen_changes=changed,source_inventory_equal=set(map(str,paths))==set(source['files']),source_freeze_sha256=sha(D/'source_freeze.json'),confirmation_jobs_sha256=sha(D/'confirmation_jobs.json'),confirmation_state_sha256=sha(D/'confirmation_state.json'),confirmation_summary_sha256=sha(D/'confirmation_summary.json'),closing_scope_sha256=sha(D/'closing_scope_20261022.json'),closing_recorded_at=closing['recorded_at'],candidate_finished_at=state['jobs'][1]['finished_at'],direct_robustness='not run; closing scope prohibited new phases; not failed gates',later_phase_artifacts=no_later_artifacts,decision='Keep installed V10 unchanged. No promotion; Solution confirmation gates fail independently of closing scope.')
Path('/tmp/sherlock-v10-fixes-20261022/confirmation-data-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
