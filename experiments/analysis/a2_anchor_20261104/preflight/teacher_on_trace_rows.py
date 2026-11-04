import hashlib,json,sys
from pathlib import Path
import numpy as np
import torch
root=Path.cwd();sys.path.insert(0,str(root));torch.set_num_threads(1)
from scripts.student_distill import load_teacher,teacher_q
P=Path('/tmp/sherlock-a2-anchor-20261104');teacher=root/'agents/sherlock/weights/agent_p0.pth';student=root/'experiments/candidates/action_student_20261104/A2.pth';trace=P/'traces/01_A2_866000_player_1/observed.jsonl';check_trace=P/'traces/03_A2_866008_player_1/observed.jsonl'
paths=[teacher,student,trace,check_trace,*[root/x for x in ['scripts/student_distill.py','agents/sherlock/model.py','agents/sherlock/config.py']]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins={str(p):sha(p) for p in paths}
assert pins[str(teacher)]=='98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
assert pins[str(student)]=='1baec85605e2b7aaad8c0beaa416d0489d2b9faa1362a9b361bbb63f04cc14bd'
for tr in [trace,check_trace]:
 summary=json.loads((tr.parent/'summary.json').read_text());assert sha(tr)==summary['files_sha256']['observed.jsonl']
selected=[]
for line in trace.open():
 d=json.loads(line)
 if d['type']=='decision' and d['env_step'] in [27,35]:
  uid={27:3,35:2}[d['env_step']];u=next(u for u in d['units'] if u['uid']==uid);ctx=d['context']
  selected.append({'env_step':d['env_step'],'uid':uid,'seed':866000,'side':'player_1','position_canonical':ctx['ally_pos'][uid],'energy':ctx['ally_ene'][uid],'assigned':ctx['assigned'].get(str(uid)),'on_known_point':ctx['ally_pos'][uid] in d['known_point_tiles'],'features':u['features'],'mask':u['mask'],'A2_raw_q':u['raw_q'],'A2_masked_action':u['network_action'],'A2_final_canonical_action':u['final_canonical_action'],'A2_override':u['override_observed']})
assert [(s['env_step'],s['uid']) for s in selected]==[(27,3),(35,2)]
# Requested env185 was inspected once; the sole current known-point holder stays.
for line in check_trace.open():
 d=json.loads(line)
 if d['type']=='decision' and d['env_step']==185:
  known=d['known_point_tiles'];holder_units=[u for u in d['units'] if d['context']['ally_pos'][u['uid']] in known]
  env185={'seed':866008,'side':'player_1','env_step':185,'decision':'omitted per request: no unit departing a currently known point','known_point_holders':[{'uid':u['uid'],'position_canonical':d['context']['ally_pos'][u['uid']],'energy':d['context']['ally_ene'][u['uid']],'network_action':u['network_action'],'final_canonical_action':u['final_canonical_action']} for u in holder_units]}
  assert len(holder_units)==1 and holder_units[0]['network_action']==holder_units[0]['final_canonical_action'][0]==0
  break
nets,cfg=load_teacher(teacher);assert len(nets)==36 and all(not p.requires_grad for net in nets for p in net.parameters())
for s in selected:
 x=np.array([s['features']],dtype=np.float32);mask=np.array(s['mask'],dtype=bool)
 q=teacher_q(nets,torch.from_numpy(x)).numpy()[0];rank=np.argsort(np.where(mask,q,-np.inf))[::-1];choice=int(rank[0]);a2=s['A2_masked_action'];final=s['A2_final_canonical_action'][0]
 assert np.argmax(np.where(mask,s['A2_raw_q'],-np.inf))==a2
 s.update(feature_float32_sha256=hashlib.sha256(x.tobytes()).hexdigest(),teacher_raw_q=q.tolist(),teacher_masked_action=choice,teacher_top_two_gap=float(q[rank[0]]-q[rank[1]]),teacher_regret_A2_network_action=float(q[choice]-q[a2]),teacher_regret_A2_final_direction=float(q[choice]-q[final]),teacher_and_A2_network_agree=choice==a2,teacher_and_A2_final_direction_agree=choice==final)
assert pins=={str(p):sha(p) for p in paths}
limits='Network-only V14 aggregate evaluated on exactly copied A2 features and its recorded mask. This is not a full V14-agent counterfactual: no recomputed V14 belief, assignment, rules, SAP target, future state, or game outcome. One-row float32 teacher reductions use existing frozen 36-network helper with no gradients. These two preselected events cannot estimate general imitation error.'
r={'status':'passed','method':'load_teacher/teacher_q on two preselected copied rows; batch1 each, CPU1, no-grad, frozen36','pins_before':pins,'pins_after':{str(p):sha(p) for p in paths},'selected_rows':selected,'env185_inspection':env185,'limitations':limits}
(P/'teacher_on_trace_rows.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'status':'passed','rows':[{k:v for k,v in s.items() if k not in ['features','mask','A2_raw_q','teacher_raw_q']} for s in selected],'env185':env185},indent=2))
