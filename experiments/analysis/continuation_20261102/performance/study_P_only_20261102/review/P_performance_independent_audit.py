"""Independent P-only phase audit, never imports project/statistics/model code.

Preparation/import reads no study data. Run only after root explicitly authorizes
an entire completed phase. CSV parsing uses stdlib. NumPy is loaded only for the
specified PCG64(seed0) resampling, not any project/league gate implementation.
"""
from pathlib import Path
from datetime import datetime
from decimal import Decimal, InvalidOperation
from collections import Counter
import argparse, csv, hashlib, json, math, os, re, subprocess

ROOT=Path('/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics')
STUDY=ROOT/'experiments/analysis/continuation_20261102/performance/study_P_only_20261102'
OUTDIR=Path('/tmp/sherlock-continue-20261102')
HEAD='03e54e267242ff642c126313fe5f512ed9d959ac'
V14='98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
P_SHA='dbb15222848b9ce8530080e128fa9ca66309c9900e98f50de5cce1d73e5b7f5a'
PANEL=('solution92','sol92_sq',
 'self:experiments/releases/20261022_all18_v3/agent_p0.pth',
 'self:experiments/releases/20261022_v7_Bsnpd/agent_p0.pth',
 'self:experiments/releases/20261022_v10_baseline/agent_p0.pth',
 'self:experiments/releases/20261101_v13_neb/agent_p0.pth')
DIRECT='self:experiments/releases/20261101_v14_baseline/agent_p0.pth'
SIDES=('player_0','player_1')
FIELDS=('seed','side','opponent','result','game_win','point_win','our_wins','opp_wins',
 'our_points','opp_points','point_counting_version','wait_frac','invalid_frac',
 'greedy_masked_frac','sap_attempts','sap_hits','stack_frac','relics_found',
 'relics_seen','known_point_tiles','belief_contradictions','unit_steps','steps','secs')
INTEGER_FIELDS=('seed','game_win','our_wins','opp_wins','our_points','opp_points',
 'point_counting_version','sap_attempts','sap_hits','relics_found','relics_seen',
 'known_point_tiles','belief_contradictions','unit_steps','steps')
EPS=1e-9
NP=None


def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def percentile(sorted_values,percentage):
 index=(len(sorted_values)-1)*percentage/100
 lo=math.floor(index);hi=math.ceil(index)
 return sorted_values[lo]+(index-lo)*(sorted_values[hi]-sorted_values[lo])


def interval(values):
 # A fresh seeded stream for each requested statistic, sorted-map order.
 values=NP.asarray(values,dtype=NP.float64)
 generator=NP.random.Generator(NP.random.PCG64(0))
 indices=generator.integers(0,len(values),size=(5000,len(values)))
 samples=NP.mean(values[indices],axis=1)
 ordered=sorted(map(float,samples))
 return percentile(ordered,2.5),percentile(ordered,97.5)


def wdl(rows):
 results=[r['result'] for r in rows]
 return dict(games=len(rows),wins=results.count(1.),draws=results.count(.5),losses=results.count(0.))


def game_details(rows):
 result=wdl(rows)
 result.update(score_sum=sum(r['result'] for r in rows),
  score_rate=sum(r['result'] for r in rows)/len(rows),
  pure_win_rate=sum(r['result']==1 for r in rows)/len(rows),
  our_match_wins=sum(r['our_wins'] for r in rows),opp_match_wins=sum(r['opp_wins'] for r in rows),
  our_points=sum(r['our_points'] for r in rows),opp_points=sum(r['opp_points'] for r in rows))
 return result


def rule_checks(phase,panel,solution,default,direct):
 if phase=='selection':
  return dict(panel_delta=panel['delta']>=.005-EPS,solution_delta=solution['delta']>=-EPS,
              default=default['winrate']>=.99-EPS,direct=direct['winrate']>=.5-EPS)
 return dict(panel_delta=panel['delta']>=.01-EPS,panel_lower=panel['low']>EPS,
  solution_delta=solution['delta']>=-EPS,solution_lower=solution['low']>=-.01-EPS,
  default=default['winrate']>=.99-EPS,default_delta=default['delta']>=-.01-EPS,
  direct_lower=direct['low']>.5+EPS)


class Auditor:
 def __init__(self):
  self.checks=[];self.evidence={};self.computed={}
 def require(self,name,condition,detail=None):
  self.checks.append(dict(name=name,passed=bool(condition),**({'detail':detail} if detail is not None else {})))
  if not condition:raise ValueError(name+(': '+str(detail) if detail is not None else ''))
 def pin(self,path):
  path=Path(path).resolve(strict=True);self.evidence[str(path)]=sha(path);return path
 def read(self,path):return json.loads(self.pin(path).read_text())
 def git(self,*args):return subprocess.check_output(['git','-C',str(ROOT),*args])
 def freeze(self,plan,state):
  masterpath=Path(plan['study_freeze_path']).resolve(strict=True)
  self.require('master_path_fixed',masterpath==(STUDY/'study_freeze.json').resolve())
  self.require('phase_plan_master_sha',sha(masterpath)==plan['study_freeze_sha256']==state['study_freeze_sha256'])
  m=self.read(masterpath);identity=m['identity'];src=identity['source']
  self.require('frozen_only_baseline_P',set(m['weights'])=={'baseline','P'})
  self.require('frozen_source_HEAD',m['expected_head']==src['head']==HEAD==self.git('rev-parse','HEAD').decode().strip())
  self.require('tracked_checkout_clean',not self.git('status','--porcelain','--untracked-files=no').strip())
  self.require('identity_before_after_complete',state['source_before']==state['source_after']==identity)
  self.require('same_fixed_driver',m['driver']==identity['driver'] and sha(m['driver']['path'])==m['driver']['sha256'])
  self.require('fixed_interpreter',src['python']==m['python'] and str(Path(m['python']).resolve())==src['executable'] and sha(m['python'])==src['executable_sha256'])
  self.require('all_frozen_weight_hashes',m['frozen_weights']==identity['weights'] and all(Path(p).is_file() and sha(p)==h for p,h in m['frozen_weights'].items()))
  self.require('actual_baseline_P_hashes',sha(m['weights']['baseline'])==V14 and sha(m['weights']['P'])==P_SHA)
  self.require('all_frozen_file_hashes',all(Path(p).is_file() and sha(p)==h for p,h in src['files'].items()))
  names=self.git('ls-files','-z','--cached','--others','--exclude-standard','--','*.py').split(b'\0')
  paths={ROOT/os.fsdecode(n) for n in names if n}
  for name in ('scripts','agents','lux'):paths.update((ROOT/name).rglob('*.py'))
  paths.update(map(Path,m['protocols']))
  for name in ('requirements.txt','pyproject.toml'):
   if (ROOT/name).is_file():paths.add(ROOT/name)
  venv=Path(m['python']).parent.parent
  if (venv/'pyvenv.cfg').is_file():paths.add(venv/'pyvenv.cfg')
  for engine in (venv/'lib').glob('python*/site-packages/luxai_s3'):paths.update(engine.rglob('*.py'))
  self.require('frozen_source_inventory_complete',set(map(str,paths))==set(src['files']))
  self.require('protocols_in_freeze',all(str(p) in src['files'] for p in m['protocols']))
  self.evidence.update(src['files']);self.evidence.update(m['frozen_weights'])
  route=self.read(ROOT/'experiments/analysis/continuation_20261102/performance/route_decision.json')
  self.require('P_only_predeclared_no_late_PT',route['route']=='P_only' and route['candidates']==['P'] and route['fresh_real_games_before_choice']==0 and route['late_PT_forbidden'] is True and route['trained_replacements_used'] is False and route['gates_and_map_counts_unchanged'] is True and route['selection_maps']==100 and route['confirmation_maps']==300 and route['direct_maps']==300)
  self.require('route_fixed_before_selection',datetime.fromisoformat(route['chosen_utc'])<datetime.fromisoformat(self.read(STUDY/'selection/state.json')['started_at']))
  return m
 def planned_jobs(self,m,phase,out):
  n,first=(100,841000) if phase=='selection' else (300,842000)
  result=[]
  for role in ('baseline','P'):
   flag='false' if role=='baseline' else 'true'
   result.append(dict(name=f'{role}_panel',role=role,engine='par_eval',timing_class='combined_panel',weights=m['weights'][role],first_seed=first,n_maps=n,opponents=[*PANEL,'default'],overrides=[f'point_pair_swap={flag}',f'art_move_guard={flag}'],workers=2,games=14*n,out=str(out/f'{role}_panel.csv'),log=str(out/f'{role}_panel.log'),root=str(ROOT)))
   if role=='P':result.append(dict(name='P_direct',role='P',engine='par_eval',timing_class='direct',weights=m['weights']['P'],first_seed=841000 if phase=='selection' else 843000,n_maps=n,opponents=[DIRECT],overrides=['point_pair_swap=true','art_move_guard=true'],workers=2,games=2*n,out=str(out/'P_direct.csv'),log=str(out/'P_direct.log'),root=str(ROOT)))
  return result
 def command(self,job,python):
  return [python,'-B','-m','scripts.par_eval','--weights',job['weights'],'--first',str(job['first_seed']-500000),'--n',str(job['n_maps']),'--opponents',','.join(job['opponents']),'--workers','2','--out',job['out'],*(x for flag in job['overrides'] for x in ('--set',flag))]
 def csv(self,job):
  path=self.pin(job['out'])
  with path.open(newline='') as stream:
   reader=csv.DictReader(stream);self.require(job['name']+'_exact_schema',tuple(reader.fieldnames or ())==FIELDS)
   raw=list(reader)
  expected={(seed,side,opp) for seed in range(job['first_seed'],job['first_seed']+job['n_maps']) for side in SIDES for opp in job['opponents']}
  parsed=[];seen=set()
  for line,row in enumerate(raw,2):
   label=f'{job["name"]}:row{line}'
   if None in row or any(v in (None,'') for v in row.values()):raise ValueError(label+' missing values')
   nums={k:float(v) for k,v in row.items() if k not in ('side','opponent')}
   if not all(math.isfinite(v) for v in nums.values()):raise ValueError(label+' nonfinite metric')
   for key in INTEGER_FIELDS:
    value=Decimal(row[key])
    if not value.is_finite() or value!=value.to_integral_value() or value<0:raise ValueError(label+' invalid integer '+key)
    nums[key]=int(value)
   key=nums['seed'],row['side'],row['opponent']
   if key not in expected or key in seen:raise ValueError(label+' unexpected/duplicate key '+str(key))
   seen.add(key)
   if nums['steps']!=303 or nums['point_counting_version']!=2 or nums['secs']<0:raise ValueError(label+' invalid runtime/course/v2')
   if not all(0<=nums[k]<=1 for k in ('wait_frac','invalid_frac','greedy_masked_frac','stack_frac')):raise ValueError(label+' invalid fraction')
   a,b=nums['our_wins'],nums['opp_wins'];result=1. if a>b else .5 if a==b else 0.
   if a+b>3 or nums['result']!=result or nums['game_win']!=int(a>b):raise ValueError(label+' inconsistent wins/result')
   a,b=nums['our_points'],nums['opp_points'];point=1. if a>b else .5 if a==b else 0.
   if nums['point_win']!=point:raise ValueError(label+' inconsistent point outcome')
   parsed.append(dict(nums,side=row['side'],opponent=row['opponent']))
  self.require(job['name']+'_all_exact_keys_and_count',seen==expected and len(parsed)==job['games'])
  return parsed
 def audit(self,phase,summary_path):
  out=STUDY/phase;state_path=out/'state.json'
  # Inspect complete status before opening any result CSV or outcome summary.
  state=self.read(state_path)
  self.require(phase+'_full_phase_complete_before_outcomes',state['phase']==phase and state['status']=='complete')
  plan_path=out/'plan.json';plan=self.read(plan_path)
  self.require(phase+'_plan_binding',Path(state['plan_path']).resolve()==plan_path.resolve() and sha(plan_path)==state['plan_sha256'] and plan['phase']==phase and plan['schema_version']==1)
  master=self.freeze(plan,state);n=100 if phase=='selection' else 300
  self.require(phase+'_nominee_plan',plan['candidate'] is None if phase=='selection' else plan['candidate']=='P')
  self.require(phase+'_fixed_job_plan',plan['jobs']==self.planned_jobs(master,phase,out))
  expected_total=3000 if phase=='selection' else 9000
  self.require(phase+'_job_receipt_counts',len(state['jobs'])==3 and state['completed_games']==expected_total and sum(j['games'] for j in plan['jobs'])==expected_total)
  self.require(phase+'_deadline_reserve',plan['deadline_utc']=='2026-11-03T04:30:00+00:00' and plan['reserve_seconds']==3600 and plan['initial_seconds_per_game']=={'combined_panel':2.22,'direct':3.0} and plan['future_confirmation_games']==({'combined_panel':8400,'direct':600} if phase=='selection' else {'combined_panel':0,'direct':0}))
  self.require(phase+'_completed_before_hard_game_deadline',datetime.fromisoformat(state['finished_at']).timestamp()<datetime.fromisoformat(plan['deadline_utc']).timestamp()-3600)
  if phase=='confirmation':
   self.require('confirmation_original_selection_paths',Path(plan['selection_state_path']).resolve()==(STUDY/'selection/state.json').resolve())
   self.require('confirmation_selection_hash_bindings',sha(plan['selection_state_path'])==plan['selection_state_sha256'] and sha(plan['selection_summary_path'])==plan['selection_summary_sha256'])
   selection=self.audit('selection',Path(plan['selection_summary_path']))
   self.require('confirmation_only_independently_qualified_P',selection['nominee']=='P' and selection['passed'])
   self.require('confirmation_prior_complete_observed_rates',plan['prior_observed_seconds_per_game']==selection['observed_seconds_per_game'])
  else:
   self.require('selection_no_consumed_outcomes',plan['prior_observed_seconds_per_game']=={'combined_panel':[],'direct':[]} and not any(k.startswith('selection_') for k in plan))
  frames={};csv_hashes={};observed={key:list(values) for key,values in plan['prior_observed_seconds_per_game'].items()}
  previous_finished=None
  for job,record in zip(plan['jobs'],state['jobs']):
   cmd=self.command(job,master['python']);target=Path(job['out'])
   self.require(job['name']+'_done_process_record',record['name']==job['name'] and record['out']==job['out'] and record['log']==job['log'] and record['timing_class']==job['timing_class'] and record['status']=='complete' and record['exit_code']==0 and record['actual_games']==job['games'])
   self.require(job['name']+'_exact_actual_command',record['command']==cmd and record['launch_command'][:3]==[master['python'],'-B','-c'] and record['launch_command'][4:]==cmd and bool(re.fullmatch(r'import os, signal, sys; signal.pthread_sigmask\(signal.SIG_SETMASK, \[[0-9, ]*\]\); os.execvpe\(sys.argv\[1\], sys.argv\[1:\], os.environ\)',record['launch_command'][3])))
   self.require(job['name']+'_owned_single_process_group',record['pid']==record['pgid'] and record['pid']>0 and record['owner_pid']>0)
   start=datetime.fromisoformat(record['started_at']);finish=datetime.fromisoformat(record['finished_at'])
   self.require(job['name']+'_sequential_finite_walltime',finish>=start and (previous_finished is None or start>=previous_finished) and math.isfinite(record['wall_seconds']) and record['wall_seconds']>0)
   previous_finished=finish
   self.require(job['name']+'_recorded_csv_sha',sha(target)==record['output_sha256'])
   frames[job['name']]=self.csv(job);csv_hashes[str(target)]=sha(target)
   observed[job['timing_class']].append(record['wall_seconds']/record['actual_games'])
  self.require(phase+'_all_rate_observations_preserved',state['observed_seconds_per_game']==observed)
  prior={k:list(v) for k,v in observed.items()}
  last=plan['jobs'][-1];prior[last['timing_class']].pop()
  initial={'combined_panel':2.22,'direct':3.0}
  maxima={k:max(v,default=0.) for k,v in prior.items()}
  slowdown=max(1.,*(maxima[k]/initial[k] for k in initial))
  effective={k:max(maxima[k],initial[k]*slowdown) for k in initial}
  remaining={k:plan['future_confirmation_games'][k]+(last['games'] if last['timing_class']==k else 0) for k in initial}
  projected=1.2*sum(remaining[k]*effective[k] for k in initial)
  projection=state['projection']
  self.require(phase+'_projection_complete_fixed_remaining_quantities',projection['remaining_games']==remaining and projection['initial_wall_seconds_per_game']==initial and projection['closing_reserve_seconds']==3600)
  self.require(phase+'_projection_unmodified_cost_classes',abs(projection['global_slowdown_factor']-slowdown)<1e-12 and all(abs(projection['effective_wall_seconds_per_game'][k]-effective[k])<1e-12 for k in initial) and abs(projection['seconds_plus_twenty_percent']-projected)<1e-6)
  self.require(phase+'_projection_time_admission',datetime.fromisoformat(projection['checked_at']).timestamp()+projected+3600<datetime.fromisoformat(plan['deadline_utc']).timestamp()+1.)
  baseline=frames['baseline_panel'];candidate=frames['P_panel'];direct_rows=frames['P_direct']
  bindex={(r['seed'],r['side'],r['opponent']):r for r in baseline};cindex={(r['seed'],r['side'],r['opponent']):r for r in candidate}
  seeds=list(range(841000 if phase=='selection' else 842000,(841000 if phase=='selection' else 842000)+n))
  def paired(opponents):
   b=[sum(bindex[s,side,o]['result'] for side in SIDES for o in opponents)/(2*len(opponents)) for s in seeds]
   c=[sum(cindex[s,side,o]['result'] for side in SIDES for o in opponents)/(2*len(opponents)) for s in seeds]
   diff=[x-y for x,y in zip(c,b)];low,high=interval(diff)
   return dict(maps=n,games=n*2*len(opponents),winrate=sum(c)/n,ref_winrate=sum(b)/n,delta=sum(diff)/n,low=low,high=high)
  opponents={o:dict(paired((o,)),opponent=o,excluded_candidate=0,excluded_reference=0) for o in (*PANEL,'default')}
  panel=paired(PANEL)
  dseeds=sorted({r['seed'] for r in direct_rows});dindex={(r['seed'],r['side']):r for r in direct_rows}
  direct_values=[sum(dindex[s,side]['result'] for side in SIDES)/2 for s in dseeds]
  dlo,dhi=interval(direct_values);rate=sum(direct_values)/n
  direct=dict(maps=n,games=2*n,winrate=rate,low=dlo,high=dhi,**{k:v for k,v in wdl(direct_rows).items() if k!='games'})
  checks=rule_checks(phase,panel,opponents['solution92'],opponents['default'],direct);passed=all(checks.values())
  nominee=('P' if passed else None) if phase=='selection' else 'P'
  counts={o:{'baseline':wdl([r for r in baseline if r['opponent']==o]),'candidate':wdl([r for r in candidate if r['opponent']==o])} for o in (*PANEL,'default')}
  result=dict(phase=phase,status='complete',observed_seconds_per_game=observed,nominee=nominee,promotion_qualified=phase=='confirmation' and passed,passed=passed,gates=checks,panel=panel,opponents=opponents,direct=direct,counts=counts,completed_games=expected_total,csv_sha256=csv_hashes,plan_sha256=sha(plan_path),state_sha256=sha(state_path),study_freeze_sha256=plan['study_freeze_sha256'],bootstrap_samples=5000,bootstrap_rng_seed=0,bootstrap_rng='NumPy PCG64; independent index resampling and own linear percentile interpolation',bootstrap_cluster='whole map; paired sides and all six panel opponents jointly',tie_rule='P-only roster: one eligible candidate or none; no PT/no runner-up',direct_delta_from_half=rate-.5,direct_delta_from_half_ci=[dlo-.5,dhi-.5],diagnostic_details={'panel':{'baseline':game_details([r for r in baseline if r['opponent'] in PANEL]),'candidate':game_details([r for r in candidate if r['opponent'] in PANEL])},'opponents':{o:{'baseline':game_details([r for r in baseline if r['opponent']==o]),'candidate':game_details([r for r in candidate if r['opponent']==o])} for o in (*PANEL,'default')}})
  self.computed[phase]=result
  root=self.read(summary_path)
  self.require(phase+'_root_summary_metadata',root['status']=='complete' and root['phase']==phase and root['nominee']==nominee and root['promotion_qualified']==result['promotion_qualified'] and root['completed_games']==expected_total and set(root['candidates'])=={'P'} and root['bootstrap_samples']==5000 and root['bootstrap_rng_seed']==0)
  self.require(phase+'_root_summary_provenance',root['plan_sha256']==result['plan_sha256'] and root['state_sha256']==result['state_sha256'] and root['study_freeze_sha256']==result['study_freeze_sha256'] and root['csv_sha256']==csv_hashes)
  cand=root['candidates']['P']
  self.require(phase+'_root_gates_nomination_no_runnerup',cand['gates']==checks and cand['passed']==passed)
  self.require(phase+'_root_WDL_counts',cand['counts']==counts)
  for label,ours,theirs in [('panel',panel,cand['panel']),('direct',direct,cand['direct']),*[(o,opponents[o],cand['opponents'][o]) for o in (*PANEL,'default')]]:
   for key,value in ours.items():
    if label=='panel' and key=='games':continue  # Root's panel wire schema omits games; independently counted above.
    self.require(phase+'_root_'+label+'_'+key,key in theirs and (abs(value-theirs[key])<=1e-12 if isinstance(value,(int,float)) else value==theirs[key]),dict(independent=value,root=theirs.get(key)))
  return result


def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--phase',choices=('selection','confirmation'),required=True)
 ap.add_argument('--root-summary',type=Path,required=True)
 ap.add_argument('--output-prefix',type=Path)
 args=ap.parse_args()
 prefix=args.output_prefix or OUTDIR/f'P_{args.phase}_independent_audit'
 if prefix.parent.resolve()!=OUTDIR.resolve():raise SystemExit('Audit outputs must remain in the designated /tmp directory')
 auditor=Auditor();error=None;result=None
 try:
  # Fail closed before even importing NumPy or inspecting outcome files.
  status=json.loads((STUDY/args.phase/'state.json').read_text())
  if status.get('status')!='complete':raise ValueError('Phase incomplete: no result CSV/summary was opened')
  global NP
  import numpy as np
  NP=np
  result=auditor.audit(args.phase,args.root_summary)
  auditor.require('all_bound_inputs_unchanged_after_audit',all(Path(p).is_file() and sha(p)==h for p,h in auditor.evidence.items()))
 except Exception as exc:error=f'{type(exc).__name__}: {exc}'
 verdict='ACCEPTED' if error is None else 'REJECTED'
 output=dict(verdict=verdict,scope='Independent complete-phase data/statistics/gate audit; no project imports or model/game/training calls',phase=args.phase,error=error,checks_total=len(auditor.checks),failed=[c for c in auditor.checks if not c['passed']],results=auditor.computed,evidence_sha256=auditor.evidence,checks=auditor.checks,limits=['Stored CSV outcomes and process/source/hash receipts are audited; no raw action stream or fresh model execution is reconstructed.','Whole-map paired percentile intervals describe the fixed panel, not Mahmoud historical league; default remains separate.','Data acceptance does not itself authorize release replacement. A failed confirmation admits no runner-up, retry or enlarged sample.'])
 prefix.with_suffix('.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
 lines=['# Independent P-only '+args.phase+' audit','',f'**{verdict}** — {len(auditor.checks)} checks; '+(error or 'no discrepancies.'),'']
 if result:
  lines += [f"Completed games: {result['completed_games']}; nominee: {result['nominee']}; promotion qualified: {result['promotion_qualified']}.",f"Panel delta {result['panel']['delta']*100:+.6f} pp [{result['panel']['low']*100:+.6f}; {result['panel']['high']*100:+.6f}].",f"Direct {result['direct']['wins']}/{result['direct']['draws']}/{result['direct']['losses']}; score {result['direct']['winrate']*100:.6f}% [{result['direct']['low']*100:.6f}; {result['direct']['high']*100:.6f}].",'', 'Opponent counts, rates, paired deltas/intervals, exact gates and provenance are in the companion JSON.']
 lines += ['', 'No Root statistics/league function, Torch/model, Agent, game or update was invoked. Same-map sides and all six panel opponents were resampled together; 5000 PCG64(seed0) samples, own2.5/97.5 linear percentiles.']
 prefix.with_suffix('.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps(dict(verdict=verdict,phase=args.phase,error=error,checks_total=len(auditor.checks),nominee=result['nominee'] if result else None,promotion_qualified=result['promotion_qualified'] if result else None),indent=2))

if __name__=='__main__':main()
