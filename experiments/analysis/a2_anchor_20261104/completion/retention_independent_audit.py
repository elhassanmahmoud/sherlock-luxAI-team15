import json, hashlib, os, sys, time
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F
torch.set_num_threads(1)
start=time.monotonic()
root=Path.cwd(); report_path=Path('/tmp/sherlock-a2-anchor-20261104/retention_before/report.json');r=json.loads(report_path.read_text())
checks=[]
def check(label, condition):
 checks.append({'check':label,'passed':bool(condition)})
 if not condition: raise AssertionError(label)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
all_pins={**r['inputs_before'],**r['sources_before']}
check('complete original retention report', r['status']=='complete')
check('report before/after input hashes match',r['inputs_before']==r['inputs_after'])
check('report before/after source hashes match',r['sources_before']==r['sources_after'])
actual_pins={p:sha(p) for p in all_pins}
check('all reported input and source hashes match actual files',actual_pins==all_pins)
parts=[]; datasets=[]; global_split={}
for round_i in (1,2):
 d=root/f'experiments/analysis/action_student_20261104/collection/r{round_i}'
 m=json.loads((d/'manifest.json').read_text());st=json.loads((d/'status.json').read_text())
 with np.load(d/'dataset.npz',allow_pickle=False) as z: a={k:z[k] for k in z.files}
 games=[json.loads(x) for x in (d/'games.jsonl').read_text().splitlines()]
 check(f'r{round_i} completed, pinned 36-member V14',m['status']==st['status']=='done' and m['teacher_members']==36 and m['teacher_sha256']=='98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8')
 check(f'r{round_i} dataset/games manifest hashes',all(sha(d/k)==v for k,v in m['files_sha256'].items()))
 check(f'r{round_i} row counts',len(a['s'])==m['rows']==st['rows']==sum(g['rows'] for g in games))
 check(f'r{round_i} finite inputs/targets',all(np.isfinite(a[k]).all() for k in ('s','teacher_q','student_q')))
 check(f'r{round_i} valid mask and actions',a['mask'].dtype==bool and a['mask'].any(axis=1).all() and np.all((a['final_action']>=0)&(a['final_action']<6)))
 check(f'r{round_i} unique game/step/unit rows',len(np.unique(np.column_stack([a[k] for k in ('game_index','env_step','uid')]),axis=0))==len(a['s']))
 check(f'r{round_i} full game plan',len(games)==len(m['game_plan'])==m['games_completed']==60 and set(a['game_index'])==set(g['game_index'] for g in m['game_plan']))
 for game in m['game_plan']:
  sel=a['game_index']==game['game_index'];seed=game['env_seed'];tr=game['is_train']
  check(f'r{round_i} game {game["game_index"]} row split/seed/side',all(np.all(a[k][sel]==game[k]) for k in ('env_seed','side','is_train')))
  check(f'r{round_i} seed {seed} whole seed split',seed not in global_split or global_split[seed]==tr);global_split[seed]=tr
  gj=[g for g in games if g['game_index']==game['game_index']][0]
  check(f'r{round_i} game {game["game_index"]} recorded count',gj['rows']==int(sel.sum()) and gj['env_seed']==seed and gj['is_train']==tr)
 for seed in set(a['env_seed']): check(f'r{round_i} seed {seed} both sides',set(a['side'][a['env_seed']==seed])=={0,1})
 excluded=~a['is_train'];parts.append({k:v[excluded] for k,v in a.items()})
 datasets.append({'round':round_i,'rows':len(a['s']),'train_rows':int(a['is_train'].sum()),'diagnostic_rows':int(excluded.sum()),'diagnostic_games':sum(not g['is_train'] for g in m['game_plan'])})
a={k:np.concatenate([p[k] for p in parts]) for k in parts[0]};n=len(a['s']);mask=a['mask'];target=a['teacher_q'].astype(np.float64);cnt=mask.sum(1);row=np.arange(n)
check('exact diagnostic seeds match and are disjoint from train',sorted(set(a['env_seed']))==r['split']['diagnostic_seeds']==list(range(865125,865130)) and set(a['env_seed']).isdisjoint(seed for seed,tr in global_split.items() if tr))
check('exact split totals match',n==r['split']['diagnostic_rows']==68687 and sum(d['train_rows'] for d in datasets)==r['split']['excluded_training_rows']==356415)
def summary(q):
 vals=q[mask];means=np.sum(np.where(mask,q,0),axis=1)/cnt
 centered=np.where(mask,q-means[:,None],0)
 multiple=cnt>=2;top=np.sort(np.where(mask[multiple],q[multiple],-np.inf),axis=1)[:,-2:];gaps=top[:,1]-top[:,0]
 return {'legal_q_entries':int(mask.sum()),'legal_q_mean':float(vals.mean()),'legal_q_std':float(vals.std(ddof=0)),'mean_row_legal_q_std':float(np.sqrt((centered**2).sum(1)/cnt).mean()),'top_two_gap_rows':len(gaps),'top_two_gap_mean':float(gaps.mean()),'top_two_gap_std':float(gaps.std(ddof=0)),'top_two_gap_zero_rate':float((gaps==0).mean())}
def metrics(q):
 choices=np.argmax(np.where(mask,q,-np.inf),axis=1);best=np.argmax(np.where(mask,target,-np.inf),axis=1)
 delta=np.where(mask,q-target,0);mean_delta=delta.sum(1)/cnt;cent=np.where(mask,delta-mean_delta[:,None],0)
 collector=np.argmax(np.where(mask,a['student_q'],-np.inf),axis=1)
 return dict(rows=n,masked_argmax_agreement=float((choices==best).mean()),legal_regret=float((target[row,best]-target[row,choices]).mean()),legal_q_mse=float(((delta**2).sum(1)/cnt).mean()),centered_legal_q_mse=float(((cent**2).sum(1)/cnt).mean()),legal_mean_q_mse=float((mean_delta**2).mean()),recorded_collector_rule_override_rate=float((a['final_action']!=collector).mean()),recorded_collector_final_outside_mask_rate=float((~mask[row,a['final_action']]).mean()),**summary(q))
comparisons={};recomputed={}
def compare(name,actual,expected):
 dif={k:float(abs(actual[k]-expected[k])) for k in expected}; comparisons[name]=dif
 check(name+' all metrics independently agree atol=1e-10 rtol=1e-10',all(np.isclose(actual[k],expected[k],atol=1e-10,rtol=1e-10) for k in expected))
compare('teacher',summary(target),r['teacher_metrics'])
@torch.no_grad()
def independent_forward(x,w):
 h=F.relu(F.linear(x,w['body.0.weight'],w['body.0.bias']));h=F.relu(F.linear(h,w['body.2.weight'],w['body.2.bias']))
 v=F.linear(F.relu(F.linear(h,w['value.0.weight'],w['value.0.bias'])),w['value.2.weight'],w['value.2.bias'])
 adv=F.linear(F.relu(F.linear(h,w['adv.0.weight'],w['adv.0.bias'])),w['adv.2.weight'],w['adv.2.bias'])
 return v+adv-adv.mean(-1,keepdim=True)
for name,item in r['models'].items():
 ck=torch.load(item['path'],weights_only=True,map_location='cpu');w=ck['q']
 check(name+' single 79-512-512 dueling checkpoint',not ck.get('ensemble') and list(w['body.0.weight'].shape)==[512,79] and list(w['body.2.weight'].shape)==[512,512])
 check(name+' frozen finite weights',all(torch.isfinite(x).all() and not x.requires_grad for x in w.values()))
 q=np.concatenate([independent_forward(torch.from_numpy(a['s'][i:i+1024]),w).numpy() for i in range(0,n,1024)]).astype(np.float64)
 check(name+' finite full no-grad predictions',np.isfinite(q).all())
 recomputed[name]=metrics(q);compare(name,recomputed[name],item['metrics'])
 check(name+' centered+mean decomposition',np.isclose(recomputed[name]['legal_q_mse'],recomputed[name]['centered_legal_q_mse']+recomputed[name]['legal_mean_q_mse'],atol=1e-12))
check('all input/source files unchanged by independent audit',actual_pins=={p:sha(p) for p in all_pins})
audit={'status':'passed','report':str(report_path),'report_sha256':sha(report_path),'method':'Full 68,687-row no-grad inference for all five checkpoints using manually assembled torch.nn.functional linear/ReLU/dueling forward; independent NumPy metric formulas; no imports of student_retention, student_action_distill, student_distill, or QNet; no games/training','runtime':{'python':sys.executable,'torch_threads':torch.get_num_threads(),'env_threads':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS']},'seconds':time.monotonic()-start},'checks':checks,'datasets':datasets,'diagnostic_rows':n,'teacher_metrics':summary(target),'recomputed':recomputed,'absolute_differences':comparisons,'hashes':actual_pins,'interpretation':['A2 agreement with recorded masked V14 argmax is compared on identical known development features and masks to the four earlier RL endpoints. Lower agreement and higher teacher regret establish a change in learned preferences on this fixed data distribution.','Raw Q-MSE decomposes into centered action-value mismatch and squared per-row legal mean shift. A common value shift changes neither masked argmax nor regret; these components must not be conflated.','These rows are excluded from supervised learning and teacher calibration, but remain development data (five seeds, both sides, two collector distributions), not a fresh performance test. Correlated rows are not independent games.','Teacher Q values are scores on recorded feature vectors; recorded collector final actions/overrides belong to the collector and are identical across evaluated model roles. They are not final actions of these evaluated RL models or teacher.','Reduced teacher agreement is not proof that forgetting caused losses: teacher need not be optimal; useful RL adaptation can disagree; final rule overrides, later state distributions, and win outcomes are not reconstructed. Fresh paired intervention results are required to assess the fixed weak anchor.']}
output=Path('/tmp/sherlock-a2-anchor-20261104/retention_independent.json');output.write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps({'status':audit['status'],'checks':len(checks),'datasets':datasets,'max_metric_abs_difference':max(max(x.values()) for x in comparisons.values()),'summary':{name:{k:x[k] for k in ['masked_argmax_agreement','legal_regret','centered_legal_q_mse','legal_mean_q_mse','legal_q_mean']} for name,x in recomputed.items()},'seconds':audit['runtime']['seconds'],'output':str(output)},indent=2))
