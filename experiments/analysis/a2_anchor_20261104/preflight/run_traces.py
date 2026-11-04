import datetime,hashlib,json,sys,time,subprocess
from pathlib import Path
ROOT=Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15');sys.path.insert(0,str(ROOT))
from scripts.student_failure_trace import trace_pair
P=Path('/tmp/sherlock-a2-anchor-20261104'); plan=json.loads((P/'trace_cases.json').read_text()); out=P/'traces'; out.mkdir(exist_ok=False)
state={'status':'running','cases':[],'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'plan_sha256':hashlib.sha256((P/'trace_cases.json').read_bytes()).hexdigest()}
def save():
 (out/'state.json').write_text(json.dumps(state,indent=2)+'\n')
def check():
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==plan['source_commit']
 for rel,h in plan['source_sha256'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==h,rel
try:
 check();save()
 for i,c in enumerate(plan['cases']):
  dest=out/f'{i:02d}_{c["role"]}_{c["seed"]}_{c["side"]}'
  r=trace_pair(Path(c['model']),c['opponent'],c['seed'],c['side'],dest,datetime.datetime.fromisoformat('2026-11-04T20:00:00+00:00'),Path(c['opponent_path']) if c.get('opponent_path') else None)
  actual=r['runs'][0]['result']
  assert all(float(actual[k])==float(v) for k,v in c['expected'].items()),(c,actual)
  state['cases'].append({'path':str(dest),'case':c,'games_completed':r['games_completed'],'status':r['status'],'historical_result_equal':True,'summary_sha256':hashlib.sha256((dest/'summary.json').read_bytes()).hexdigest()});check();save();print(json.dumps({'case':i,'path':str(dest),'status':'done'}),flush=True)
 state.update(status='complete',games_completed=sum(x['games_completed'] for x in state['cases']),finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());save()
except BaseException as e:
 state.update(status='incomplete',error=repr(e));save();raise
