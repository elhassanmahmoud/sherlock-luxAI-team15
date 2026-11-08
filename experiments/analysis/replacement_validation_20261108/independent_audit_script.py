import csv, hashlib, json, math, subprocess, time
from pathlib import Path
import numpy as np
R=Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
B=R/'experiments/analysis/replacement_validation_20261108'; D=B/'validation'
HEAD='f9e1195bb65b6587206685971b3ce11e604666db'
ORIGIN='e63c06d87745120b7c7e46d4fc8dec264e178377c548cd0cd23a6c3dda85d02e'
MODELS={'V14':'98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8','REPLACE36':'5ce350a86d4ed90b319af298e64b98e7f725ed253f5df89d504e98a73a54db6b'}
PATHS={'V14':'experiments/releases/20261101_v14_baseline/agent_p0.pth','REPLACE36':'experiments/candidates/ensemble_diversity_20261107/REPLACE36.pth'}
OPPS=['solution92','sol92_sq','self:experiments/releases/20261022_all18_v3/agent_p0.pth','self:experiments/releases/20261022_v7_Bsnpd/agent_p0.pth','self:experiments/releases/20261022_v10_baseline/agent_p0.pth','self:experiments/releases/20261101_v13_neb/agent_p0.pth','default']
FIELDS='seed side opponent result game_win point_win our_wins opp_wins our_points opp_points point_counting_version wait_frac invalid_frac greedy_masked_frac sap_attempts sap_hits stack_frac relics_found relics_seen known_point_tiles belief_contradictions unit_steps steps secs'.split()
def read(p): return json.loads(Path(p).read_text())
def digest(p):
 with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def check(ok, msg):
 if not ok: raise ValueError(msg)
def hashes(values):
 for p,h in values.items(): check(digest(p)==h,'hash '+str(p))
s=read(D/'state.json')
check(s['status']=='complete' and s['completed_games']==3200 and not s['active'] and not s['queue'],'not complete')
# No outputs, heavy imports, or model loads precede complete-state prerequisite.
pids={s['owner_pid'],s['wake']['pid']}|{x['pid'] for x in s['jobs'].values()}
ps=subprocess.run(['ps','-axo','pid=,command='],text=True,capture_output=True,check=True).stdout
active=[line.strip() for line in ps.splitlines() if line.split() and int(line.split()[0]) in pids]
check(not active,'owned processes still alive: '+repr(active))
check(s['wake'].get('returncode') is not None,'wake cleanup not recorded')
p=read(B/'validation_plan/jobs.json'); f=read(D/'provenance.json'); l=read(B/'validation_launch.json'); o=read(B/'origin.json')
check(subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==HEAD,'HEAD changed')
check(s['source']==f['source_identity']==l['source_identity'] and s['expected_head']==HEAD==s['source']['head'],'source identity')
check(s['provenance']==f and s['python']==s['source']['python'],'provenance binding')
hashes(s['source']['files']); check(digest(s['source']['executable'])==s['source']['executable_sha256'],'python executable')
hashes(s['inputs']); hashes(s['protected'])
check(s['protected']=={str(R/'agents/sherlock/weights/agent_p0.pth'):MODELS['V14'],str(R/'agents/sherlock/weights/agent_p1.pth'):MODELS['V14'],str(R/'Gruppe15.zip'):'88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6'},'protected expected')
check(digest(B/'origin.json')==ORIGIN==s['origin_sha256']==f['origin_sha256'],'origin hash')
check(o['kind']=='outcome_motivated_separate_validation' and o['prior_selection_nominee'] is None and o['prior_diagnostic_role']=='REPLACE36' and o['not_compact_protocol_confirmation'] is True and o['new_games_cap']==3200 and o['no_successor_or_topup'] is True,'origin boundary')
hashes({str(R/k):v for k,v in o['prior_files_sha256'].items()})
prior=read(R/'experiments/analysis/ensemble_diversity_20261108_compact/selection/summary.json')
check(prior['nominee'] is None and prior['status']=='complete' and prior['results']['REPLACE36']['nominable'] is False,'prior closed')
check(s['model_sha256']==f['model_sha256']==MODELS,'model hash identities')
check(o['fixed_models']=={r:{'path':path,'sha256':MODELS[r]} for r,path in PATHS.items()},'fixed models')
for role,path in PATHS.items(): check(digest(R/path)==MODELS[role],'actual model '+role)
check(p['roles']==PATHS and p['total_games']==3200 and len(p['jobs'])==15 and p['max_simultaneous_model_processes']==2,'plan basic')
for obj in (p,s,l,f): check(obj['profile']=='replacement20261108','profile')
check(p['nominee'] is s['nominee'] is None and p['phase']==s['phase']==l['phase']=='confirmation','phase')
check(p['protocol']=='docs/superpowers/plans/2026-11-08-replacement-validation.md','protocol')
check(s['opponent_sha256']==p['opponent_sha256'],'opponent hash bindings'); hashes({str(R/k):v for k,v in p['opponent_sha256'].items()})
a=read(B/'admission.json'); check(a['status']=='admitted' and a['roles']==o['fixed_models'] and digest(B/'admission.json')==s['admission_sha256'],'admission')
expected={f'{role}_panel_{i}':(role,'panel',opp) for role in PATHS for i,opp in enumerate(OPPS)}
expected['REPLACE36_direct']=('REPLACE36','direct','self:'+PATHS['V14'])
check(set(expected)==set(s['jobs'])==set(s['receipts'])==set(s['job_plan']),'complete jobs')
check({x.stem for x in D.glob('*.csv')}==set(expected),'CSV files')
check({x.stem for x in (D/'receipts').glob('*.json')}==set(expected),'receipt files')
rows_by={}; csvhash={}; receipthash={}; seen_jobs=set()
for job in p['jobs']:
 name=job['name']; check(name not in seen_jobs and name in expected,'job duplicate');seen_jobs.add(name)
 role,kind,opp=expected[name]; check((job['role'],job['kind'],job['opponent'])==(role,kind,opp) and job['weights']==PATHS[role] and job['workers']==1,'job schedule')
 seeds=list(range(2100000,2100200)) if kind=='direct' else list(range(2000000,2000100))
 check(read(R/job['seed_list'])==seeds and job['expected_games']==2*len(seeds),'seed schedule')
 check(s['job_plan'][name]==dict(job,seeds=seeds),'state job plan')
 csvp=D/(name+'.csv'); rp=D/'receipts'/(name+'.json'); receipt=read(rp)
 csvhash[name]=digest(csvp);receipthash[name]=digest(rp)
 argv=[s['python'],'-B','-m','scripts.par_eval','--weights',str(R/job['weights']),'--seed-list',str(R/job['seed_list']),'--workers','1','--opponents',opp,'--out',str(csvp)]
 needed={'profile':'replacement20261108','status':'complete','returncode':0,'job_name':name,'phase':'confirmation','role':role,'opponent':opp,'weights':PATHS[role],'model_sha256':MODELS[role],'seed_list_sha256':digest(R/job['seed_list']),'csv_sha256':csvhash[name],'rows':len(seeds)*2,'source_identity':s['source'],'opponent_sha256':p['opponent_sha256'],'command':argv}
 check(all(receipt.get(k)==v for k,v in needed.items()),'receipt '+name)
 check(s['receipts'][name]=={'path':str(rp),'sha256':receipthash[name],'rows':2*len(seeds)},'state receipt')
 check(s['jobs'][name]['argv']==argv and s['jobs'][name]['returncode']==0,'job exit/argv')
 for path in (csvp,rp): check(s['inputs'].get(str(path))==digest(path),'unbound CSV/receipt')
 with csvp.open(newline='') as stream:
  reader=csv.DictReader(stream); check(len(reader.fieldnames)==len(FIELDS) and set(reader.fieldnames)==set(FIELDS),'columns'); rows=list(reader)
 check(len(rows)==len(seeds)*2,'row count'); keys=set(); cleaned=[]
 for row in rows:
  check(None not in row and all(v not in ('',None) for v in row.values()),'missing cell')
  n={k:float(v) for k,v in row.items() if k not in ('side','opponent')};check(all(math.isfinite(v) for v in n.values()),'finite')
  check(n['seed'].is_integer(),'integer seed');key=(int(n['seed']),row['side'],row['opponent']);check(key not in keys,'duplicate');keys.add(key)
  check(n['steps']==303 and n['point_counting_version']==2 and n['secs']>=0,'course')
  for field in 'our_wins opp_wins our_points opp_points sap_attempts sap_hits relics_found relics_seen known_point_tiles belief_contradictions unit_steps'.split(): check(n[field].is_integer() and n[field]>=0,'integer field')
  for field in 'wait_frac invalid_frac greedy_masked_frac stack_frac'.split(): check(0<=n[field]<=1,'fraction')
  check(n['our_wins']+n['opp_wins']<=3,'wins total')
  result=1. if n['our_wins']>n['opp_wins'] else 0. if n['our_wins']<n['opp_wins'] else .5
  pr=1. if n['our_points']>n['opp_points'] else 0. if n['our_points']<n['opp_points'] else .5
  check(n['result']==result and n['game_win']==int(result==1.) and n['point_win']==pr,'result consistency')
  cleaned.append(dict(n,seed=key[0],side=key[1],opponent=key[2]))
 check(keys=={(seed,side,opp) for seed in seeds for side in ('player_0','player_1')},'full keys')
 rows_by[name]=cleaned
check(sum(map(len,rows_by.values()))==3200,'total rows')
# Inputs must bind all required non-output data as well as CSV receipts.
required=[B/'validation_plan/jobs.json',B/'admission.json',B/'origin.json',B/'validation_launch.json',D/'provenance.json',R/p['protocol']]+[R/x for x in PATHS.values()]+[R/x for x in p['opponent_sha256']]+[R/j['seed_list'] for j in p['jobs']]+[R/x for x in o['prior_files_sha256']]
for path in required: check(s['inputs'].get(str(path))==digest(path),'required input binding '+str(path))
def counts(rows):
 vals=[r['result'] for r in rows];w=vals.count(1.);d=vals.count(.5);n=len(vals)
 return dict(games=n,wins=w,draws=d,losses=n-w-d,half_wins=2*w+d,score=(w+.5*d)/n,strict_winrate=w/n)
def interval(values):
 values=np.asarray(values,dtype=float); idx=np.random.Generator(np.random.PCG64(0)).integers(0,len(values),size=(5000,len(values)))
 return [float(x) for x in np.percentile(values[idx].mean(axis=1),[2.5,97.5])]
def compare(c,r,opponent=None):
 cm={};rm={}
 for row in c: cm.setdefault(row['seed'],[]).append(row['result'])
 for row in r: rm.setdefault(row['seed'],[]).append(row['result'])
 seeds=sorted(cm);cv=np.array([np.mean(cm[x]) for x in seeds]);rv=np.array([np.mean(rm[x]) for x in seeds]);diff=cv-rv;lo,hi=interval(diff)
 result=dict(maps=len(seeds),score=float(cv.mean()),ref_score=float(rv.mean()),delta=float(diff.mean()),low=lo,high=hi,candidate=counts(c),reference=counts(r))
 if opponent is not None: result.update(opponent=opponent,games=len(c),excluded_candidate=0,excluded_reference=0)
 return result
panels={role:[r for j in p['jobs'] if j['role']==role and j['kind']=='panel' for r in rows_by[j['name']]] for role in PATHS}
c=panels['REPLACE36'];r=panels['V14']; by={opp:compare([x for x in c if x['opponent']==opp],[x for x in r if x['opponent']==opp],opp) for opp in OPPS}
panel=compare([x for x in c if x['opponent']!='default'],[x for x in r if x['opponent']!='default'])
direct=rows_by['REPLACE36_direct']; dv=[np.mean([r['result'] for r in direct if r['seed']==seed]) for seed in range(2100000,2100200)];lo,hi=interval(dv)
d=dict(maps=200,games=400,score=float(np.mean(dv)),low=lo,high=hi,candidate=counts(direct))
sol=by['solution92'];default=by['default'];eps=1e-9
checks={'Local six score Δ >= +1 pp':panel['delta']>=.01-eps,'Local six score untere 95%-Grenze > 0':panel['low']>eps,'Solution_92 Δ >= -0.5 pp':sol['delta']>=-.005-eps,'Solution_92 untere 95%-Grenze > -2.5 pp':sol['low']>-.025+eps,'default >= 99%':default['score']>=.99-eps,'default Δ >= -1 pp':default['delta']>=-.01-eps,'direkt untere 95%-Grenze > 50 %':d['low']>.5+eps,'solution92_score_nonnegative':sol['candidate']['half_wins']>=sol['reference']['half_wins'],'solution92_strict_winrate_nonnegative':sol['candidate']['wins']>=sol['reference']['wins'],'default_strict_winrate_ge_0.99':default['candidate']['wins']>=198}
result=dict(panel=panel,direct=d,solution92=sol,default=default,opponent_outcomes=by,panel_half_win_gain=panel['candidate']['half_wins']-panel['reference']['half_wins'],solution_half_win_gain=sol['candidate']['half_wins']-sol['reference']['half_wins'],checks=checks,passed=all(checks.values()),nominable=False)
# The independent raw-data calculations are complete before opening production summary.
summary=read(D/'summary.json'); comparisons=[]
def eq(actual,expected,path=''):
 if isinstance(expected,dict):
  check(isinstance(actual,dict) and set(actual)==set(expected),'keys '+path)
  for k,v in expected.items():eq(actual[k],v,path+'.'+k)
 elif isinstance(expected,float):check(abs(actual-expected)<1e-12,'numeric '+path);comparisons.append(path)
 else:check(actual==expected,'value '+path);comparisons.append(path)
eq(summary['results']['REPLACE36'],result,'REPLACE36')
check(summary['status']=='complete' and summary['games']==3200 and summary['jobs']==15 and summary['nominee'] is None and summary['passed']==result['passed'],'summary envelope')
for key,path in [('plan',B/'validation_plan/jobs.json'),('origin',B/'origin.json'),('provenance',D/'provenance.json'),('state',D/'state.json'),('reservation',B/'validation_launch.json')]:check(summary['input_sha256'][key]==digest(path),'summary input '+key)
check(summary['input_sha256']['csv']==csvhash and summary['input_sha256']['receipts']==receipthash,'summary output hashes')
report=dict(status='PASS',audited_at=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),audit_scope='Complete recorded data and independent statistics; no new models, games, tests or replays',source_head=HEAD,jobs=15,games=3200,source_files=len(s['source']['files']),bound_inputs=len(s['inputs']),archive_files=len(o['prior_files_sha256']),processes_absent=sorted(pids),numeric_tolerance=1e-12,compared_values=len(comparisons),bootstrap=dict(generator='PCG64',seed=0,replicates=5000,unit='whole map, paired across roles, sides and all six panel opponents',interval='unadjusted 95% percentile'),results=result,summary_sha256=digest(D/'summary.json'),csv_sha256=csvhash,receipt_sha256=receipthash,verified_source_hashes=s['source'],verified_input_hashes=s['inputs'],protected=s['protected'],limitations=['Outcome-motivated separate prospective fixed-artifact validation; prior compact study remains closed with no nominee and diagnostic REPLACE36 non-nominable.','Fresh data only; no discovery outcomes pooled.','100 independent panel maps and 200 direct maps; sides and opponents are clustered within map.','Unadjusted 95% intervals do not control project-wide repeated exploration or multiplicity; this is a local fixed panel, not arbitrary-opponent general strength.','No isolated causal claim about ensemble size or curriculum: both candidates use 36 nets, exact members differ.','CSV has no source commit field: each row inherits recorded provenance via CSV hash and job receipt; no engine replay independently regenerated outcomes.'])
with (D/'independent_audit.json').open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False);stream.write('\n')
print(json.dumps({k:report[k] for k in ['status','jobs','games','source_files','bound_inputs','archive_files','compared_values']}));print(json.dumps(result,indent=2))
