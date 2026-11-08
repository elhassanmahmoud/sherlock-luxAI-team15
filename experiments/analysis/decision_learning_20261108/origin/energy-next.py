import collections, gzip, hashlib, json
from pathlib import Path

root=Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
base=root/'experiments/analysis/continuation_20261102/targeting'
totals={k:collections.Counter() for k in ['loss','control']}
records=[]; mismatches=[]; sources=[]
for path in sorted(base.glob('*.jsonl.gz')):
    sources.append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    with gzip.open(path,'rt') as f:frames=[json.loads(line) for line in f]
    for ix,frame in enumerate(frames):
        if frame['status']!='decision':continue
        pub=frame['public']; group='control' if frame['key']['seed'] in [831000,831001,831002] else 'loss'
        c=totals[group]
        nxt=frames[ix+1] if ix+1<len(frames) else None
        nxt_valid=nxt and nxt['status']=='decision' and nxt['key']['match_idx']==frame['key']['match_idx']
        nextunits={u['uid']:u for u in nxt['units']} if nxt_valid else {}
        for u in frame['units']:
            c['all_unit_decisions']+=1
            a=u['final_action'][0]
            if not u['mask'][a]:
                c['final_action_outside_mask']+=1
                c['outside_mask_action_'+str(a)]+=1
                c['outside_mask_source_'+str(u['masked_argmax'])]+=1
                mismatches.append({'group':group,**frame['key'],'uid':u['uid'],'energy':u['energy'],
                    'masked_argmax':u['masked_argmax'],'final_action':u['final_action'],'sap_cost':pub['sap_cost'],
                    'q_stay':u['q_values'][0],'q_sap':u['q_values'][5], 'mask':u['mask'],
                    'holder':u['holder'],'sole_holder':u['sole_holder'],'sap_target':u['sap_target']})
            if not u['sole_holder'] or u['energy']<0:continue
            c['sole_holder_decisions']+=1
            if a!=5:continue
            c['sole_holder_sap']+=1
            c['holder_sap_outside_mask']+=not u['mask'][5]
            c['holder_sap_q_source_'+str(u['masked_argmax'])]+=1
            x,y=u['position'];cost=pub['sap_cost']; field=pub['energy_map'][x][y]
            cost_balance=u['energy']-cost+field
            near=[i for i,(ex,ey) in enumerate(pub['enemy_coords'])
                  if max(abs(ex-x),abs(ey-y))<=pub['sap_range']+1 and pub['enemy_energies'][i]>=cost]
            r={'group':group,**frame['key'],'uid':u['uid'],'position':[x,y],
               'energy':u['energy'],'sap_cost':cost,'tile_energy':field,'nebula':bool(pub['nebula'][x][y]),
               'energy_observation_age':pub['energy_observation_age'][x][y],
               'cost_plus_observed_field_balance':cost_balance,'armed_visible_near':len(near),
               'mask_sap':u['mask'][5],'masked_argmax':u['masked_argmax'],
               'next_exists':u['uid'] in nextunits,'next_same_position':False}
            c['holder_sap_balance_negative']+=cost_balance<0
            c['holder_sap_balance_below_sap_cost']+=cost_balance<cost
            c['holder_sap_current_nebula']+=r['nebula']
            if u['uid'] in nextunits and nextunits[u['uid']]['position']==u['position']:
                n=nextunits[u['uid']];r['next_same_position']=True;r['next_energy']=n['energy']
                r['net_residual']=n['energy']-cost_balance
                c['holder_sap_followed_same_slot_same_position']+=1
                c['same_position_next_negative']+=n['energy']<0
                c['same_position_next_below_sap_cost']+=n['energy']<cost
                c['same_position_negative_with_nonnegative_cost_field_balance']+=(n['energy']<0 and cost_balance>=0)
                c['same_position_residual_negative']+=r['net_residual']<0
                c['same_position_residual_zero']+=r['net_residual']==0
                c['same_position_residual_positive']+=r['net_residual']>0
            else:c['holder_sap_no_same_position_followup']+=1
            records.append(r)
output={'warning':'Pure historical observation. Cost+field balance omits clipping, nebula, void, enemy SAP, collisions, drift and identity changes; residual is not a damage estimate. Same UID/position is not proven life identity.',
        'totals':{g:dict(c) for g,c in totals.items()},'sources':sources,'holder_sap_records':records,'outside_mask_records':mismatches}
Path('/tmp/sherlock-energy-next.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output['totals'],indent=2))
