"""Four known complete trace reproductions, never strength tests or training."""
from pathlib import Path
import argparse, collections, gzip, hashlib, json, os, subprocess, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from scripts import holder_rollout_probe as probe
from scripts.early_curriculum_study import resource_lock, source_identity, hashes
from scripts import par_eval
from agents.sherlock.main import Agent_x

parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--usage-file',type=Path,required=True);parser.add_argument('--expected-head',required=True);args=parser.parse_args()
root=probe.ROOT
protocols=[root/'docs/superpowers/specs/2026-11-08-artillery-alignment.md',root/'docs/superpowers/plans/2026-11-08-artillery-alignment.md']
old=root/'experiments/analysis/holder_learning_20261108/neutral_v1'
reference=json.loads((old/'manifest.json').read_text())
keys=[dict(seed=s,side=p) for s,p in probe.SMOKE_KEYS]
inputs=[Path(__file__).resolve(),old/'manifest.json',*[old/f"{k['seed']}_{k['side']}_reference.frames.jsonl.gz" for k in keys]]
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==args.expected_head
args.out.mkdir(parents=True,exist_ok=False)
state=dict(status='running',source=source_identity(root,sys.executable,protocols),source_plans=list(map(str,protocols)),inputs=hashes(inputs),protected=hashes(probe.protected_inputs(root)),usage_file=str(args.usage_file.resolve()),stop_file='/private/tmp/sherlock-artillery-alignment-20261108/STOP',executions=[],progress={},pid=os.getpid(),pgid=os.getpgrp(),argv=sys.argv)
guard=probe.Guard(state)
original_cfg=par_eval.build_cfg;original_act=Agent_x.act
try:
 with resource_lock(root):
  guard(force=True)
  for flag in (False,True):
   def config(*a,**kw):
    c=original_cfg(*a,**kw);c.art_splash_in_training=flag;return c
   par_eval.build_cfg=config
   for key in keys:
    counters=collections.Counter()
    def observed_act(self,*a,**kw):
     assert not self.training and self.cfg.art_splash_in_training is flag
     result=original_act(self,*a,**kw);counters['act_calls']+=1;return result
    Agent_x.act=observed_act
    label=f"{key['seed']}_{key['side']}_{int(flag)}"
    f=args.out/(label+'.frames.jsonl.gz');p=args.out/(label+'.pairs.jsonl')
    def progress(name): state['progress'][name]=state['progress'].get(name,0)+1
    result=probe.play(key['seed'],key['side'],root/'agents/sherlock/weights/agent_p0.pth',instrumented=False,frame_path=f,pair_path=p,guard=guard,progress=progress,max_pairs=0)
    oldfile=old/f"{key['seed']}_{key['side']}_reference.frames.jsonl.gz"
    with gzip.open(f,'rt') as stream:new=[json.loads(l) for l in stream]
    with gzip.open(oldfile,'rt') as stream:prior=[json.loads(l) for l in stream]
    assert len(new)==len(prior)==303 and new==prior, label+' differs from original V14'
    oldgame=next(g for g in reference['games'] if g['key']['seed']==key['seed'] and g['key']['side']==key['side'])
    assert result==oldgame['reference'], label+' game result differs'
    state['executions'].append(dict(key=key,flag=flag,result=result,counters=dict(counters),original=hashes([oldfile]),artifacts=hashes([f,p]),all_303_frames_identical=True))
    probe.write_json(args.out/'manifest.json',state)
    print(label,'PASS',dict(counters),flush=True)
  guard(force=True);state['status']='complete';state['complete_executions']=4
except BaseException as exc:
 state['status']='failed';state['error']=repr(exc);raise
finally:
 par_eval.build_cfg=original_cfg;Agent_x.act=original_act
 probe.write_json(args.out/'manifest.json',state)
