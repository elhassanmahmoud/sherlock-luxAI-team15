"""Bounded read-only late-gap inspection. Stdlib; four fixed snapshots, no jobs/policy imports."""
from pathlib import Path
import json,gzip,hashlib,collections
D=Path('/Users/moayedshawesh/Desktop/KI/sherlock-counterplay/experiments/analysis/continuous_20261021/loss_observation')
def sh(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pairs(a):return {tuple(p) for p in a}
def dist(a,b):return sum(abs(x-y) for x,y in zip(a,b))
def half(p,t):return 'midline' if sum(p)==23 else 'home' if ((sum(p)<23)==(t==0)) else 'opponent'
candidates=[]
for p in sorted(D.glob('*.summary.json')):
 seed=int(p.name.split('_')[0]);team=int(p.name.split('_')[2].split('.')[0])
 for r in json.loads(p.read_text())['snapshots']:
  if r['match'] in (1,2) and r['match_step_t']==75:
   tr=r['truth_t'];gap=len(tr['productive_tiles'][1-team])-len(tr['productive_tiles'][team]);candidates.append((gap,seed,team,r['match']+1,p))
chosen=sorted(candidates,key=lambda a:(-a[0],a[1],a[2],a[3]))[:4]
x={'selection':'Four largest opponent-minus-own productive-field gaps among all 40 Match2/3 snapshots at local t75; tie by seed,side,match ascending. Fixed before locality inspection; outcome-biased, not representative.','source_manifest_sha256':sh(D/'manifest.json'),'script_sha256':sh(__file__),'cases':[]}
for gap,seed,t,m,p in chosen:
 raw=D/f'{seed}_player_{t}.jsonl.gz';rr=[json.loads(s) for s in gzip.open(raw,'rt')];r=next(z for z in rr if z['match']==m-1 and z['match_step_t']==75);tr=r['truth_t'];own=pairs(tr['productive_tiles'][t]);opp=pairs(tr['productive_tiles'][1-t]);true=pairs(tr['active_point_tiles']);known=pairs(r['decision']['known_point_tiles']);empty=(known&true)-own
 units=[u for u in r['decision']['units'] if u['energy']>=0 and tr['mask'][t][u['uid']]];off=[u for u in units if tuple(u['position']) not in true];visible={e['uid']:e for u in units for e in u['visible_enemies']}
 fields=[]
 for q in sorted(empty):
  near=sorted(((dist(q,u['position']),u['uid'],u) for u in units),key=lambda z:(z[0],z[1]));n=near[0] if near else None;on=sorted(((dist(q,u['position']),u['uid'],u) for u in off),key=lambda z:(z[0],z[1]));o=on[0] if on else None
  fields.append(dict(position=q,half=half(q,t),opponent_productive_truth=q in opp,visible_enemy_here=[e['uid'] for e in visible.values() if e['energy']>=0 and tuple(e['position'])==q],visible_enemy_within1=[e['uid'] for e in visible.values() if e['energy']>=0 and dist(e['position'],q)<=1],nearest_live_unit=n[1] if n else None,nearest_distance=n[0] if n else None,nearest_offpoint_unit=o[1] if o else None,nearest_offpoint_distance=o[0] if o else None,offpoint_units_within5=[u['uid'] for u in off if dist(q,u['position'])<=5],offpoint_units_within5_current_move_budget=[u['uid'] for u in off if dist(q,u['position'])<=5 and u['energy']>=dist(q,u['position'])*u['move_cost']]))
 # Fixed +/-10 local steps, actual decisions only; truth pressure kept separately.
 windows=[]
 for z in rr:
  if z['match']!=m-1 or not 65<=z['match_step_t']<=85:continue
  a=z['truth_t'];b=z['truth_after'];up=pairs(a['productive_tiles'][t]);op=pairs(a['productive_tiles'][1-t]);pt=pairs(a['active_point_tiles']);kk=pairs(z['decision']['known_point_tiles']);uds=[]
  for u in z['decision']['units']:
   uid=u['uid'];pos=u['position'];after=b['position'][t][uid];active=a['mask'][t][uid];en=u['energy']; empt=(kk&pt)-up
   local=[q for q in empt if dist(pos,q)<=5];dmin=min((dist(pos,q) for q in empt),default=None)
   uds.append(dict(uid=uid,mask=active,energy=en,position=pos,half=half(pos,t),on_true_point=tuple(pos) in pt,on_known_point=u['on_known_point'],action=u['final_action'],after_rule=u['after_rule'],forced_sap=u['inferred_pt_sap'],legal_mask=u['legal_mask'],move_cost=u['move_cost'],sap_cost=u['sap_cost'],visible_enemies=u['visible_enemies'],distance_nearest_known_empty=dmin,nearby_known_empty=sorted(local),after_mask=b['mask'][t][uid],after_energy=b['energy'][t][uid],after_position=after))
  windows.append(dict(step_t=z['step_t'],match_step_t=z['match_step_t'],known=len(kk&pt),own_productive=len(up),opponent_productive=len(op),known_empty_by_half=dict(collections.Counter(half(q,t) for q in (kk&pt)-up)),masked_negative=sum(a['mask'][t][j] and a['energy'][t][j]<0 for j in range(16)),live_nonnegative=sum(a['mask'][t][j] and a['energy'][t][j]>=0 for j in range(16)),units=uds,own_productive_positions=sorted(up),opp_productive_positions=sorted(op)))
 c=dict(seed=seed,side=t,match=m,gap=gap,step_t=r['step_t'],known=len(known&true),true=len(true),own_productive=len(own),opp_productive=len(opp),own_productive_by_half=dict(collections.Counter(half(q,t) for q in own)),opp_productive_by_half=dict(collections.Counter(half(q,t) for q in opp)),live_units=len(units),live_offpoint=len(off),masked_negative=sum(tr['mask'][t][j] and tr['energy'][t][j]<0 for j in range(16)),known_empty=len(empty),empty_by_half=dict(collections.Counter(half(q,t) for q in empty)),fields=fields,windows=windows,raw_sha256=sh(raw),summary_sha256=sh(p))
 c['screen']={'opponent_productive':sum(f['opponent_productive_truth'] for f in fields),'visible_enemy_on_tile':sum(bool(f['visible_enemy_here']) for f in fields),'not_opp_productive_with_offpoint_within5':sum(not f['opponent_productive_truth'] and bool(f['offpoint_units_within5']) for f in fields),'not_opp_productive_with_offpoint_within5_move_budget':sum(not f['opponent_productive_truth'] and bool(f['offpoint_units_within5_current_move_budget']) for f in fields),'home_or_midline_not_opp_productive_with_offpoint_within5_move_budget':sum(f['half']!='opponent' and not f['opponent_productive_truth'] and bool(f['offpoint_units_within5_current_move_budget']) for f in fields)}
 c['window_counts']={
 'new_masked_negative_unit_steps':sum(u['mask'] and u['energy']>=0 and u['after_mask'] and u['after_energy']<0 for w in windows for u in w['units']),
 'mask_off_after_nonnegative_unit_steps':sum(u['mask'] and u['energy']>=0 and not u['after_mask'] for w in windows for u in w['units']),
 'new_masked_negative_from_true_point_unit_steps':sum(u['mask'] and u['energy']>=0 and u['on_true_point'] and u['after_mask'] and u['after_energy']<0 for w in windows for u in w['units'])}
 if (seed,t,m)==(510930,1,2):
  z=next(z for z in rr if z['match']==1 and z['match_step_t']==78)
  c['observed_convergence_local78']=[dict(team=v,uid=7,position=z['truth_t']['position'][v][7],energy=z['truth_t']['energy'][v][7],action=z['actions'][f'player_{v}'][7],after_position=z['truth_after']['position'][v][7],after_mask=z['truth_after']['mask'][v][7],after_energy=z['truth_after']['energy'][v][7]) for v in (1,0)]
 x['cases'].append(c)
assert [(c['gap'],c['seed'],c['side'],c['match']) for c in x['cases']]==[(10,510858,1,2),(7,510858,0,2),(6,510847,0,3),(6,510930,1,2)]
assert all(len(c['windows'])==21 and c['known_empty']==len(c['fields']) and sum(c['empty_by_half'].values())==c['known_empty'] for c in x['cases'])
x['checks']='Fixed selection and 4x21 consecutive window/field partition assertions passed.'
Path('/tmp/sherlock-late-locality-20261021.json').write_text(json.dumps(x,indent=2)+'\n')
for c in x['cases']:
 print({k:v for k,v in c.items() if k not in ('fields','windows','raw_sha256','summary_sha256')})
 print('FIELDS',c['fields'])
 print('UNITS t75',[{k:v for k,v in u.items() if k not in ('visible_enemies','nearby_known_empty','legal_mask')} for w in c['windows'] if w['match_step_t']==75 for u in w['units']])
