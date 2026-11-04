import csv,hashlib,json,statistics,time
from pathlib import Path
import numpy as np
P=Path('/tmp/sherlock-a2-anchor-20261104');ROOT=Path.cwd();state=json.loads((P/'traces/state.json').read_text());checks=[];allpins={};cases=[];compact={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(s,c):
 checks.append({'check':s,'passed':bool(c)})
 if not c:raise AssertionError(s)
def digest(actions):
 h=hashlib.sha256()
 for side in ['player_0','player_1']:
  a=np.asarray(actions[side]);h.update(side.encode());h.update(str(a.shape).encode());h.update(a.astype('<i8').tobytes())
 return h.hexdigest()
def mean(a):return statistics.mean(a) if a else None
check('state complete 12 pairs 24 executions',state['status']=='complete' and state['games_completed']==24 and len(state['cases'])==12)
check('predeclared trace cases hash',sha(P/'trace_cases.json')==state['plan_sha256'])
for ci,entry in enumerate(state['cases']):
 path=Path(entry['path']);s=json.loads((path/'summary.json').read_text());case=entry['case'];tag=path.name;side=int(s['side'][-1]);other=1-side
 check(tag+' summary hash',sha(path/'summary.json')==entry['summary_sha256'])
 check(tag+' complete 2 games',s['status']=='done' and s['games_completed']==2 and s['cpu_threads']==1)
 for k,v in s['files_sha256'].items():check(tag+' file hash '+k,sha(path/k)==v)
 check(tag+' input/source/protected pins stable',s['inputs_before']==s['inputs_after'] and s['pins_before']==s['pins_after'])
 for k,v in {**s['inputs_before'],**s['pins_before']['sources'],**s['pins_before']['protected'],s['pins_before']['interpreter']:s['pins_before']['interpreter_sha256'],str(ROOT/'scripts/student_failure_trace.py'):s['source_sha256']}.items():
  check(tag+' consistent shared pin '+k,k not in allpins or allpins[k]==v);allpins[k]=v
 rs=[json.loads((path/(label+'_summary.json')).read_text()) for label in ['plain','observed']]
 check(tag+' inline and file summaries exact',rs==s['runs'])
 check(tag+' result and match equality',rs[0]['result']==rs[1]['result'] and rs[0]['matches']==rs[1]['matches'])
 historical_path=ROOT/'experiments/analysis/action_student_20261104/diagnostic'/('panel' if s['opponent']=='solution92' else 'direct')/(case['role']+'.csv')
 hist=[r for r in csv.DictReader(historical_path.open()) if int(r['seed'])==s['seed'] and r['side']==s['side'] and (s['opponent']!='solution92' or r['opponent']=='solution92')]
 check(tag+' historical row unique',len(hist)==1)
 fields=['result','our_wins','opp_wins','our_points','opp_points','steps']
 check(tag+' 6 historical fields exact',all(float(rs[1]['result'][k])==float(hist[0][k])==float(case['expected'][k]) for k in fields))
 check(tag+' 303 steps three matches stable learning',all(r['result']['steps']==303 and len(r['matches'])==3 and r['learning_state_unchanged'] for r in rs) and rs[1]['observed_act_steps']==303)
 plain=[json.loads(l) for l in (path/'plain.jsonl').open()];check(tag+' plain 303 transitions',len(plain)==303 and all(r['type']=='transition' and r['env_step']==i for i,r in enumerate(plain)))
 decisions=[];trans=[];unit_total=0;overrides=0;outside=0;matchdata={i:dict(rows=[],energies=[],negative=0,live=0,unit_rows=0,overrides=0,outside=0,occupancy=[],occupancy_units=[],knowledge=[],disappeared=[],respawn_candidates=[],point_departures=[],point_entries=[]) for i in range(3)}
 prev=None
 for l in (path/'observed.jsonl').open():
  r=json.loads(l)
  if r['type']=='transition':trans.append(r);continue
  check(tag+' decision step consecutive '+str(r['env_step']),r['env_step']==len(decisions))
  i=r['match_index'];md=matchdata[i];ctx=r['context'];points=set(map(tuple,r['known_point_tiles']));units={};positions={};energies={}
  if ctx:
   positions={int(uid):tuple(ctx['ally_pos'][uid]) for uid in ctx['ally_ids']};energies={uid:float(ctx['ally_ene'][uid]) for uid in positions}
   check(tag+' canonical positions agree world '+str(r['env_step']),all(tuple(r['observation']['units']['position'][side][u])==((23-pos[1],23-pos[0]) if r['canonical_mirrored'] else pos) for u,pos in positions.items()))
   for u in r['units']:
    uid=u['uid'];net=max((a for a in range(6) if u['mask'][a]),key=lambda a:u['raw_q'][a]);fin=u['final_canonical_action'][0];world=u['final_world_action'];can=list(world)
    if r['canonical_mirrored']:
     if can[0]<5:can[0]=[0,2,1,4,3][can[0]]
     else:can[1:]=[-can[2],-can[1]]
    check(tag+' network/final capture '+str(r['env_step'])+'/'+str(uid),net==u['network_action'] and can==u['final_canonical_action'] and (fin!=net)==u['override_observed'] and (not u['mask'][fin])==u['final_outside_network_mask'] and world==r['final_world_actions'][uid])
    unit_total+=1;overrides+=u['override_observed'];outside+=u['final_outside_network_mask'];md['unit_rows']+=1;md['overrides']+=u['override_observed'];md['outside']+=u['final_outside_network_mask']
    pos=positions[uid];ene=energies[uid];units[uid]={'pos':list(pos),'energy':ene,'target':ctx['assigned'].get(str(uid)),'network':net,'final':fin,'final_components':u['final_canonical_action'],'override':u['override_observed'],'mask':u['mask'],'features':u['features'],'q':u['raw_q'],'on_known_point':pos in points}
   nonneg=[pos for uid,pos in positions.items() if energies[uid]>=0]
   md['energies'].extend(energies.values());md['negative']+=sum(e<0 for e in energies.values());md['live']+=len(positions)
   occupied=set(nonneg)&points;md['occupancy'].append(len(occupied));md['occupancy_units'].append(sum(pos in points for pos in nonneg));md['knowledge'].append(len(points))
  else:occupied=set();md['occupancy'].append(0);md['occupancy_units'].append(0);md['knowledge'].append(len(points))
  small={'env_step':r['env_step'],'match_step':r['match_step'],'match_index':i,'points':[r['observation']['team_points'][side],r['observation']['team_points'][other]],'known':r['known_point_tiles'],'relics':r['known_relics'],'discoveries':r['discoveries'],'units':units,'actions':r['final_world_actions'],'occupied':sorted(map(list,occupied))}
  if prev and prev['match_index']==i and ctx:
   for uid,pu in prev['units'].items():
    if uid not in units:md['disappeared'].append({'env_step':r['env_step'],'uid':uid,'previous_position':pu['pos'],'previous_energy':pu['energy']})
    elif pu['pos']!=[0,0] and units[uid]['pos']==[0,0] and sum(abs(x-y) for x,y in zip(pu['pos'],[0,0]))>1:md['respawn_candidates'].append({'env_step':r['env_step'],'uid':uid,'previous_position':pu['pos']})
    elif pu['on_known_point'] and not units[uid]['on_known_point']:
     md['point_departures'].append({'env_step':prev['env_step'],'uid':uid,'before':{k:pu[k] for k in ['pos','energy','network','final','override','target']},'after':{k:units[uid][k] for k in ['pos','energy','network','final','override','target']}})
  decisions.append(small);prev=small
 check(tag+' observed decision/transitions 303',len(decisions)==len(trans)==303)
 check(tag+' exact plain/observed complete transitions',plain==trans)
 ds=[digest(t['actions_world']) for t in trans]
 check(tag+' independently reconstructed step/full action digests',all(ds==r['step_digests'] and hashlib.sha256(''.join(ds).encode()).hexdigest()==r['full_action_digest'] for r in rs) and all(d==t['action_digest'] for d,t in zip(ds,trans)))
 check(tag+' decision actions equal executed side actions',all(d['actions']==t['actions_world'][s['side']] for d,t in zip(decisions,trans)))
 terminals=[t for t in trans if t['next_match_step']==0];check(tag+' terminal matches 100/201/302',len(terminals)==3 and [t['env_step'] for t in terminals]==[100,201,302])
 matchout=[]
 for i,tm in enumerate(terminals):
  pts=tm['terminal_points_external_only'];md=matchdata[i];sco=[None,None]
  for t in trans[i*101:(i+1)*101]:
   ps=t.get('terminal_points_external_only',t['next_visible_team_points'])
   for k in range(2):
    if ps[k]>0 and sco[k] is None:sco[k]=t['env_step']
  check(tag+' terminal score/firstscore match '+str(i),rs[1]['matches'][i]['points']==pts and rs[1]['matches'][i]['first_positive_points_env_step']==sco)
  matchout.append({'match':i+1,'points':[pts[side],pts[other]],'margin':pts[side]-pts[other],'first_positive_score_env_step':[sco[side],sco[other]],'first_positive_score_match_step':[v-i*101 if v is not None else None for v in [sco[side],sco[other]]],'known_point_tiles_at_end':md['knowledge'][-1],'mean_distinct_known_point_occupancy_pre_action':mean(md['occupancy']),'known_point_occupancy_sum_pre_action':sum(md['occupancy']),'live_unit_observations':md['live'],'mean_observed_energy':mean(md['energies']),'negative_energy_unit_observations':md['negative'],'negative_energy_fraction':md['negative']/md['live'] if md['live'] else 0,'unit_rows':md['unit_rows'],'overrides':md['overrides'],'override_fraction':md['overrides']/md['unit_rows'],'final_outside_mask':md['outside'],'active_to_absent_events':md['disappeared'],'same_uid_spawn_jump_candidates':md['respawn_candidates'],'known_point_departure_events':md['point_departures']})
 check(tag+' sum match points matches historic result',sum(x['points'][0] for x in matchout)==rs[1]['result']['our_points'] and sum(x['points'][1] for x in matchout)==rs[1]['result']['opp_points'])
 c={'id':tag,'role':case['role'],'seed':s['seed'],'side':s['side'],'opponent':s['opponent'],'result':{k:rs[1]['result'][k] for k in fields},'unit_rows':unit_total,'overrides':overrides,'override_fraction':overrides/unit_total,'final_outside_mask':outside,'first_seen':rs[1]['first_seen'],'matches':matchout,'log_sha256':s['files_sha256'],'full_action_digest':rs[1]['full_action_digest']}
 cases.append(c);compact[(case['role'],s['seed'],s['side'])]=decisions
 print(tag,[(x['points'],round(x['mean_distinct_known_point_occupancy_pre_action'],2),round(x['negative_energy_fraction'],3)) for x in matchout],flush=True)
check('all actual pinned file hashes unchanged',all(sha(p)==v for p,v in allpins.items()))
paired=[]
for seed in [866000,866008]:
 for side in ['player_0','player_1']:
  aa=compact[('A2',seed,side)];vv=compact[('V14',seed,side)];diff={}
  for label,test in [('first_final_action_difference',lambda a,b:a['actions']!=b['actions']),('first_network_preference_difference',lambda a,b:any(u in b['units'] and x['network']!=b['units'][u]['network'] for u,x in a['units'].items())),('first_observed_points_difference',lambda a,b:a['points']!=b['points']),('first_known_point_difference',lambda a,b:a['known']!=b['known'])]:
   for a,b in zip(aa,vv):
    if test(a,b):
     dd={'env_step':a['env_step'],'match_index':a['match_index'],'match_step':a['match_step'],'A2_points':a['points'],'V14_points':b['points'],'A2_known':a['known'],'V14_known':b['known'],'units':[]}
     for uid in sorted(set(a['units'])&set(b['units'])):
      u,w=a['units'][uid],b['units'][uid]
      if u['network']!=w['network'] or u['final_components']!=w['final_components']:
       dd['units'].append({'uid':uid,'identical_features':u['features']==w['features'],'identical_masks':u['mask']==w['mask'],'A2':{k:u[k] for k in ['pos','energy','target','network','final','override','on_known_point','q']},'V14':{k:w[k] for k in ['pos','energy','target','network','final','override','on_known_point','q']}})
     diff[label]=dd;break
  paired.append({'seed':seed,'side':side,**diff})
limitations=['Only the evaluated side has instrumented agent-visible knowledge/energy/context. Direct games record V14 actions and aggregate points, but no V14 belief/context.','Occupancy counts distinct currently KNOWN canonical point coordinates occupied by own units with nonnegative energy before action; not true hidden scoring tiles or exact score contributions. It is descriptive and time-shifted from transition scoring.','Active-to-absent events exclude match resets. They do not identify exact death cause and can miss same-ID death/respawn in one transition; spawn-jump candidates listed separately. No cross-ID lifetime, kill count, or energy-delta reward is inferred.','Overrides identify a final action direction different from masked net argmax, not a particular rule; SAP target-component changes are captured in full actions but not the direction override count.','First action divergence is verified on shared features when available; later score differences do not prove this action caused the outcome. State trajectories and opponents adapt.','Terminal match points are external evaluation measurements, never decision inputs; discovery and energy summaries use only captured agent-visible observations/context.','These are targeted known development cases; not a fresh win-rate sample or an independently randomized causal experiment.']
out={'status':'passed','checks_passed':len(checks),'checks':checks,'source_pins':allpins,'cases':cases,'A2_vs_V14_same_solution_cases':paired,'definitions':{'time':'env_step zero-based; match 1 starts env0, match2 env101, match3 env202. First score denotes transition env_step. Discovery denotes pre-action decision env_step.','point_coordinates':'canonical x,y; player1 maps world to (23-y,23-x)','action_codes':{'0':'stay','1':'up','2':'right','3':'down','4':'left','5':'sap'}},'limitations':limitations}
(P/'trace_analysis.json').write_text(json.dumps(out,indent=2)+'\n')
(P/'trace_compact.json').write_text(json.dumps({f'{r}_{seed}_{side}':x for (r,seed,side),x in compact.items()},separators=(',',':'))+'\n')
print('CHECKS',len(checks),'PINNED',len(allpins),'PAIRS',json.dumps(paired,indent=2))
