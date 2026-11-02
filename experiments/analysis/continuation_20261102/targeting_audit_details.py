"""Bounded stdlib second pass: episodes/examples and declared descriptive limits."""
import hashlib
import importlib.util
import json
import gzip
from collections import defaultdict
from pathlib import Path

BASE=Path('/tmp/sherlock-continue-20261102')
REPO=Path('/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics')
RUN=REPO/'experiments/analysis/continuation_20261102/targeting'
spec=importlib.util.spec_from_file_location('audit_helpers', BASE/'audit_targeting.py')
a=importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
manifest=json.loads((RUN/'manifest.json').read_text())
report=json.loads((BASE/'targeting_independent_audit/targeting_audit.json').read_text())
cohorts=defaultdict(a.Metrics)
cases_h1=[]
cases_h2=[]
all_phases=set()
for g in manifest['games']:
    key=g['key']; game=(key['seed'],key['side']); group=key['group']
    free_since={}; h1_prev={}; h2_prev={}
    with gzip.open(RUN/g['trace']['path'],'rt') as stream:
        for raw in stream:
            f=json.loads(raw); k=f['key']; sid=k['obs_step']; mi=k['match_idx']
            if f['status']=='reset':
                free_since.clear(); h1_prev.clear(); h2_prev.clear(); continue
            p=f['public']; units={u['uid']:u for u in f['units']}; w=p['W']; pts=p['point_tiles']
            free={tuple(t['position']):t for t in f['free_own_tiles']}
            free_since={t:start for t,start in free_since.items() if t in free}
            for t in free: free_since.setdefault(t,sid)
            phase=lambda t:(*game,mi,*t,free_since[t]) if t in free else None
            groups=['all',group]
            if group=='loss':
                team=int(game[1][-1]); cumulative=g['observed']['matches'][mi]['cumulative_wins']
                prior=g['observed']['matches'][mi-1]['cumulative_wins'] if mi else [0,0]
                match_lost=cumulative[1-team]-prior[1-team]>cumulative[team]-prior[team]
                groups.append('loss_lost_matches' if match_lost else 'loss_won_matches')
            def add(name,n=1,ph=None):
                for c in groups: cohorts[c].add(name,game,n,ph)
            for t,r in free.items():
                if r['visible_enemy']: continue
                add('legacy_free_own_field_steps',ph=phase(t))
                if not r['assigned_units']: add('legacy_untargeted_free_own_field_steps',ph=phase(t))
                if not r['assigned_units'] and r['allowed_first_progress_units']:
                    candidates=[units[u] for u in r['allowed_first_progress_units']]
                    for tc in ('known_point','candidate','exploration',None):
                        label=tc or 'none'
                        if any(u['target_class']==tc for u in candidates): add('untargeted_supply_with_competing_'+label+'_field_steps',ph=phase(t))
                    if any(u['target_half']=='enemy' for u in candidates): add('untargeted_supply_with_enemy_goal_field_steps',ph=phase(t))
                    if any(u['target_half']=='own' and u['target_class']=='known_point' for u in candidates): add('untargeted_supply_with_other_own_point_goal_field_steps',ph=phase(t))
            truepts=f['posthoc']['before']['point_tiles']
            relics=p.get('relic_coords',[])
            for x in range(w):
                for y in range(p['H']):
                    if x+y>w-1 or not truepts[x][y]: continue
                    add('true_own_point_field_steps')
                    if not pts[x][y]:
                        near=any(max(abs(rx-x),abs(ry-y))<=2 for rx,ry in relics)
                        add('unknown_own_near_known_relic_field_steps' if near else 'unknown_own_no_known_relic_field_steps')
            events=f['events']
            for e in events:
                if not(e['method']=='_artillery_ok' and e.get('return') is True and e.get('caller_action_status')=='observed' and e.get('caller_action') in (1,2,3,4)): continue
                u=e['uid']; row=units[u]
                over=next((x for x in events[e['order']+1:] if x['uid']==u and x['method']=='_overkill'),None)
                if not(over and over.get('caller_action_status')=='observed' and over.get('caller_action')==5 and over.get('return') is True and row['final_action'][0]==0 and e['arguments']['sap']==over['arguments']['sap']): continue
                assert not p['config']['art_still'] and not p['config']['end_sap']
                target=tuple(row['assigned_target']) if row['assigned_target'] else None
                epkey=(mi,u,target)
                prev=h1_prev.get(epkey)
                episode=prev[1] if prev and prev[0]==sid-1 else sid
                h1_prev[epkey]=(sid,episode)
                episode_id=(*game,mi,u,target,episode)
                add('h1_chain_unit_steps',ph=episode_id)
                add('h1_chain_frame_marker',ph=(*game,mi,sid))
                if row['target_class']=='known_point' and row['target_half']=='own':
                    add('h1_chain_to_known_own_point_unit_steps',ph=phase(target))
                    if e['caller_action'] in row['allowed_target_progress']:
                        add('h1_chain_lost_legal_known_own_target_progress_unit_steps',ph=phase(target))
                add('h1_pre_artillery_move_legal_unit_steps',int(row['mask'][e['caller_action']]))
                cases_h1.append(dict(key=k,uid=u,position=row['position'],energy=row['energy'],
                    assigned_target=row['assigned_target'],target_class=row['target_class'],target_half=row['target_half'],
                    target_bfs_distance=row['target_bfs_distance'],allowed_target_progress=row['allowed_target_progress'],
                    actual_pre_artillery_move=e['caller_action'],move_was_legal=bool(row['mask'][e['caller_action']]),
                    masked_argmax=row['masked_argmax'],final_action=row['final_action'],sap=e['arguments']['sap'],
                    planned_dmg=over['arguments']['planned_dmg'],target_free=target in free,
                    frame=(*game,sid),episode=episode_id))
            swaps=f['two_owner_swap']['improvements']
            if swaps: add('h2_frames_with_counterfactual',ph=(*game,mi,sid))
            for s in swaps:
                epkey=(mi,*s['units'],tuple(map(tuple,s['old_targets'])))
                prev=h2_prev.get(epkey)
                episode=prev[1] if prev and prev[0]==sid-1 else sid
                h2_prev[epkey]=(sid,episode)
                epid=(*game,*epkey,episode)
                add('h2_pair_step_opportunities',ph=epid)
                for t in map(tuple,s['old_targets']):
                    if t in free: add('h2_target_field_steps_bearing_pair',ph=phase(t))
                cases_h2.append(dict(key=k,**s,positions=[units[u]['position'] for u in s['units']],
                    energies=[units[u]['energy'] for u in s['units']],
                    final_actions=[units[u]['final_action'] for u in s['units']],
                    target_classes=[units[u]['target_class'] for u in s['units']],
                    target_halves=[units[u]['target_half'] for u in s['units']],
                    episode=epid))
preflight=BASE/'v14_preflight.json'
pf=json.loads(preflight.read_text())
assert pf['weights_sha256']==a.V14_SHA and pf['loaded_nets']==36 and pf['feature_dim']==79 and pf['n_actions']==6
assert len(pf['tensor_hashes'])==36 and pf['all_loaded_tensors_exact'] is True and pf['finite'] is True
assert pf['training'] is False and pf['epsilon']==0 and pf['autosave'] is False
assert pf['games']==pf['forwards']==pf['environment_resets']==0
initial=BASE/'trace_impl/integration/manifest.json'
im=json.loads(initial.read_text())
assert im['completed_games']==2 and im['status']=='complete'
legacy_path=REPO/'experiments/analysis/night_20261101/remaining_solution_losses/aggregates.json'
legacy=json.loads(legacy_path.read_text())['totals_selected_sample_only']
legacy_checks={}
for group, oldgroup in (('loss_lost_matches','lost'),('loss_won_matches','won')):
    new=cohorts[group].export()
    for field,oldfield in (('legacy_free_own_field_steps','free_pt_own'),('legacy_untargeted_free_own_field_steps','untargeted_free_pt_own'),('true_own_point_field_steps','true_pt_own'),('unknown_own_near_known_relic_field_steps','unknown_own_relic_known'),('unknown_own_no_known_relic_field_steps','unknown_own_relic_unseen')):
        actual=new.get(field,{}).get('count',0)
        legacy_checks[group+':'+field]=dict(current=actual,legacy=legacy[oldgroup][oldfield],exact=actual==legacy[oldgroup][oldfield])
assert all(c['exact'] for c in legacy_checks.values()),legacy_checks
result=dict(legacy_selected_six_match_scope_reproduction=legacy_checks,core_audit_status=report['status'],core_checks=report['checks'],
    final_source_games=24,earlier_integration_games=im['completed_games'],total_actual_preparatory_and_diagnostic_games=26,
    preflight=dict(path=str(preflight),sha256=a.sha(preflight),metadata_valid=True,
        limit='Existing preflight receipt checked; no tensors/models loaded anew by this independent stdlib audit.'),
    earlier_integration=dict(path=str(initial),sha256=a.sha(initial),head=im['git_head'],
        limit='Earlier two-game integration is disclosed separately, not pooled with final-source traces.'),
    cohorts={c:m.export() for c,m in cohorts.items()},h1_cases=cases_h1,h2_cases=cases_h2)
(BASE/'targeting_audit_details.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('core_audit_status','final_source_games','earlier_integration_games','total_actual_preparatory_and_diagnostic_games')}))
for cohort,rows in result['cohorts'].items():
    print(cohort)
    for name,row in rows.items(): print(name,row)
print('H1 first known own:',next((c for c in cases_h1 if c['target_class']=='known_point' and c['target_half']=='own'),None))
print('H2 first:',cases_h2[0] if cases_h2 else None)
