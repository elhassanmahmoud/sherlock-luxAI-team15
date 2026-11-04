"""Freeze the already specified full diagnostic after all four RL receipts pass."""
import csv, datetime, hashlib, importlib.metadata, importlib.util, json, os, subprocess, sys
from pathlib import Path
import numpy as np
import torch

root=Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
tmp=Path('/tmp/sherlock-action-student-20261104')
sys.path.insert(0,str(root))
from agents.sherlock.main import Agent_x
torch.set_num_threads(1)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def write(p,d):
    assert not p.exists(),str(p)
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
plan=read(tmp/'planned_comparison.json')
for seed in (27,28):
    a=read(tmp/f'learning_audit_rl_seed{seed}.json')
    assert a['status']=='passed',a.get('status')
    for arm in ('control','sap0'):
        g=read(tmp/f'rl{seed}_{arm}_guard.json')
        assert g['status']=='completed' and g['returncode']==0
ensembles={}
for name,roles in [('CONTROL2',['CONTROL27','CONTROL28']),('SAP02',['SAP027','SAP028'])]:
    inputs=[root/plan['roles'][r] for r in roles];out=root/plan['roles'][name]
    assert not out.exists() and out.is_relative_to(root/'experiments/runs/20261104_action_student/ensembles')
    original={str(p):sha(p) for p in inputs}
    cp=[torch.load(p,map_location='cpu',weights_only=False) for p in inputs]
    assert cp[0]['cfg']==cp[1]['cfg']
    assert all(not c.get('ensemble') for c in cp)
    assert any(not torch.equal(cp[0]['q'][k],cp[1]['q'][k]) for k in cp[0]['q']), 'Ensemble members must be distinct trained states'
    subprocess.run([sys.executable,'-B','-m','scripts.build_ensemble','--out',str(out),*[str(p) for p in inputs]],cwd=root,check=True)
    made=torch.load(out,map_location='cpu',weights_only=False)
    assert len(made['ensemble'])==1 and made['ensemble_dims']==[79]
    for sd,expected in zip([made['q'],made['ensemble'][0]],[c['q'] for c in cp]):
        assert sd.keys()==expected.keys() and all(torch.equal(sd[k],expected[k]) for k in sd)
    agent=Agent_x('player_0',agent_path=str(out),train=False);agent.set_to_eval_mode();agent.autosave_on_terminate=False
    assert len(agent.extra_q)==1
    x=torch.from_numpy(np.load(root/'experiments/runs/20261104_action_student/collect_r2/dataset.npz')['s'][:256].copy())
    with torch.no_grad():
        combined=torch.stack([agent.q(x),agent.extra_q[0](x)]).mean(0)
        singles=[]
        for p in inputs:
            a=Agent_x('player_0',agent_path=str(p),train=False);a.set_to_eval_mode();singles.append(a.q(x))
        assert torch.equal(combined,torch.stack(singles).mean(0)) and torch.isfinite(combined).all()
    assert all(sha(p)==h for p,h in original.items())
    ensembles[name]={'inputs':original,'sha256':sha(out),'members':2,'exact_tensor_order':True,'runtime_component_mean_exact_rows':256,'not_promoted':True}
write(tmp/'ensemble_verification.json',ensembles)

# Runtime estimate uses only historical completed timings, never fresh outcomes.
old=root/'experiments/analysis/student_reward_20261104/diagnostic'
timing_sources={}
for role in ('V14','S3','S30','CONTROL30','SAP0_30'):
    rows=list(csv.DictReader((old/f'{role}.csv').open()))
    timing_sources[role]={'sha256':sha(old/f'{role}.csv'),'mean_seconds_by_opponent':{opp:sum(float(r['secs']) for r in rows if r['opponent']==opp)/40 for opp in plan['opponents']}}
means=timing_sources['V14']['mean_seconds_by_opponent']
single_means={o:max(timing_sources[r]['mean_seconds_by_opponent'][o] for r in ('S3','S30','CONTROL30','SAP0_30')) for o in plan['opponents']}
queue=[0.,0.];schedule=[]
for kind,roles in [('panel',list(plan['roles'])),('direct',[r for r in plan['roles'] if r!='V14'])]:
    for role in roles:
        timing=means if role in ('V14','CONTROL2','SAP02') else single_means
        seconds=40*(sum(timing.values()) if kind=='panel' else timing[plan['opponents'][2]])*1.15+12
        worker=min(range(2),key=lambda i:queue[i]);start=queue[worker];queue[worker]+=seconds
        schedule.append({'kind':kind,'role':role,'worker':worker,'start_s':start,'end_s':queue[worker]})
now=datetime.datetime.now(datetime.timezone.utc);deadline=datetime.datetime.fromisoformat('2026-11-04T16:40:00+00:00')
runtime={'created_utc':now.isoformat(),'historical_timing_sources':timing_sources,'single_net_bound':single_means,'two_net_and_V14_bound':means,'explanation':'Same 512 architecture: maximum opponent mean across all four earlier single-net roles; two-net ensembles conservatively use full36 V14 timing. Direct V14 uses measured V13 timing, same36 architecture. All means padded15% plus12s startup/job. No fresh outcomes used. Estimate, not guaranteed worst-case.','multiplier':1.15,'startup_seconds_per_job':12,'two_worker_queue_seconds':max(queue),'schedule':schedule,'model_deadline_utc':deadline.isoformat(),'closure_reserve_minutes':20,'projected_finish_utc':(now+datetime.timedelta(seconds=max(queue))).isoformat(),'admitted':now+datetime.timedelta(seconds=max(queue))<deadline}
write(tmp/'diagnostic_runtime_admission.json',runtime)
assert runtime['admitted'],'Full diagnostic does not fit; no games started'
sources={p:sha(root/p) for p in subprocess.check_output(['git','ls-files','*.py'],cwd=root,text=True).splitlines() if p.startswith(('agents/','scripts/','lux/'))}
inputs={str(root/p):sha(root/p) for p in plan['roles'].values()}
for p in [root/'experiments/releases/20261101_v13_neb/agent_p0.pth',root/'agents/sherlock/weights/agent_p1.pth',Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/Gruppe15.zip'),Path(sys.executable).resolve(),tmp/'panel_seeds.json',tmp/'direct_seeds.json',tmp/'run_guarded.py',tmp/'run_diagnostic.py',tmp/'planned_comparison.json',tmp/'audit_final.py']:
    inputs[str(p)]=sha(p)
protected=read(root/'experiments/runs/20261104_action_student/fit_r2/manifest.json')['protected_before']
for p,h in protected.items():
    assert sha(p)==h,p
    inputs[p]=h
engine=Path(importlib.util.find_spec('luxai_s3').origin).parent
for p in engine.rglob('*.py'):inputs[str(p)]=sha(p)
protocol=dict(plan, status='admitted_frozen_before_first_game', recorded_utc=now.isoformat(),output_directory=str(root/'experiments/analysis/action_student_20261104/diagnostic'),deadline_utc='2026-11-04T16:40:00Z',source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),source_sha256=sources,inputs_sha256=inputs,python=sys.executable,guard_script=str(tmp/'run_guarded.py'),panel_seed_file=str(tmp/'panel_seeds.json'),direct_seed_file=str(tmp/'direct_seeds.json'),runtime_admission=runtime,statistical_unit='whole card across sides and opponents',bootstrap_replicates=5000,bootstrap_seed=0,confirmation=False)
protocol['dependency_versions']={p:importlib.metadata.version(p) for p in ['torch','numpy','luxai-s3','jax','jaxlib']}
write(tmp/'diagnostic_protocol.json',protocol)
print(json.dumps({'status':'admitted','projected_finish':runtime['projected_finish_utc'],'duration_minutes':max(queue)/60,'protocol':str(tmp/'diagnostic_protocol.json')}))
