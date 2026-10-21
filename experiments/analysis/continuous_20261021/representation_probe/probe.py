#!/usr/bin/env python3
"""One bounded source-isolated representation probe. Never imports project packages.
Only four predeclared archived cases, local t65..85. No engine/model execution.
"""
import ast
import copy
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
import numpy as np

ROOT = Path('/Users/moayedshawesh/Desktop/KI/sherlock-counterplay')
DATA = ROOT / 'experiments/analysis/continuous_20261021/loss_observation'
OUT = Path('/tmp/sherlock-representation-probe-20261021')
CASES = ((510858,1,2), (510858,0,2), (510847,0,3), (510930,1,2))
EXPECTED_HEAD = 'a5d2e61b0e8654bad64e31c29447ada1e439174d'
SOURCES = ['agents/sherlock/features.py','agents/sherlock/geometry.py',
           'agents/sherlock/main.py','scripts/observe_loss_mechanisms.py']
EXPECTED = {'agents/sherlock/features.py':'1ac9fa9f2bc7d74d70e72bf23a44c7d532687adbbadb0b8ba2df6f44c4c082e6',
            'agents/sherlock/main.py':'4b53d516485649736f049728f88be1e666e0229c54de59f0819ff8fb353da457'}

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def head(): return subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'], text=True).strip()
def source_hashes(): return {p:sha(ROOT/p) for p in SOURCES}
def extract(path, functions, assignments, namespace):
    """Compile only explicitly allowlisted original AST nodes, with no imports."""
    tree = ast.parse(path.read_text(), filename=str(path))
    kept = []
    found = set()
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name in functions:
            kept.append(node); found.add(node.name)
        elif isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in assignments:
            kept.append(node); found.add(node.targets[0].id)
    assert found == set(functions)|set(assignments), found
    assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) for node in kept for n in ast.walk(node))
    exec(compile(ast.Module(body=kept,type_ignores=[]),str(path),'exec'), namespace)
    return [getattr(n,'name',getattr(n.targets[0],'id','')) if isinstance(n,ast.Assign) else n.name for n in kept]

def nominal(pos, action):
    a=int(action[0]); dx,dy=((0,0),(0,-1),(1,0),(0,1),(-1,0),(0,0))[a]
    return [pos[0]+dx,pos[1]+dy]
def nearest(enemies,pos):
    # Source make_context: ascending np.where(mask) slots, no energy filter.
    es=sorted(enemies,key=lambda e:e['uid'])
    return min(es,key=lambda e:abs(e['position'][0]-pos[0])+abs(e['position'][1]-pos[1]))['uid'] if es else None

def fixture(ns, geo, anchor):
    u=next(u for u in anchor['decision']['units'] if u['uid']==7)
    assert u['position']==[19,10] and u['energy']==125
    es=sorted(u['visible_enemies'],key=lambda e:e['uid'])
    assert [(e['uid'],e['position'],e['energy']) for e in es]==[(4,[20,9],89),(7,[19,8],150)]
    out={}
    for canonical in (False,True):
        p=np.full((16,2),-1,np.int32);p[7]=u['position']
        ec=np.array([e['position'] for e in es],np.int32)
        if canonical:p=geo.mirror_positions(p);ec=geo.mirror_positions(ec)
        energy=np.zeros(16,np.float32);energy[7]=125
        count=np.zeros((24,24),np.float32);count[tuple(p[7])]=1
        empty=np.empty((0,2),np.int32)
        # All context beyond recorded focal positions/energies is CONTROLLED SYNTHETIC.
        ctx=dict(W=24,H=24,ally_ids=np.array([7]),ally_pos=p,ally_ene=energy,
                 enemy_coords=ec,enemy_energies=np.array([89,150],np.float32),enemy_vis_ids=np.array([4,7]),
                 ally_count=count,first_on_tile={tuple(p[7]):7},assigned={},
                 point_coords=empty,cand_coords=empty,relic_coords=empty,unexp_coords=empty,
                 passable=np.ones((24,24),bool),nebula=np.zeros((24,24),bool),
                 energy_map=np.zeros((24,24),np.float32),point_tiles=np.zeros((24,24),bool),
                 candidate=np.zeros((24,24),bool),explored=np.zeros((24,24),bool),
                 own_points=0.,opp_points=0.,own_wins=0.,opp_wins=0.,step=179,
                 match_step=78,max_match_steps=100.,match_idx=1,move_cost=1.,sap_cost=37.,
                 sap_range=6,sensor_range=2.,max_units=16)
        d=np.abs(ec-p[7]).sum(axis=1);selected=int(ctx['enemy_vis_ids'][np.argmin(d)])
        assert selected==4 and d.tolist()==[2,2]
        base=ns['build_features'](ctx,7)
        changed=copy.deepcopy(ctx);changed['enemy_energies'][1]=50
        nonselected=ns['build_features'](changed,7)
        positive=copy.deepcopy(ctx);positive['enemy_energies'][0]=50
        selected_changed=ns['build_features'](positive,7)
        diff=np.flatnonzero(base!=selected_changed).tolist()
        assert np.isfinite(base).all() and base.shape==(79,)
        assert np.array_equal(base,nonselected)
        assert [ns['FEATURE_NAMES'][i] for i in diff]==['enemy_energy_rel']
        out['canonical' if canonical else 'world']={
            'selected_uid':selected,'distances':d.tolist(),'feature_dim':len(base),
            'nonselected_uid7_energy_change':[150,50], 'nonselected_whole_vector_identical':True,
            'positive_control_uid4_energy_change':[89,50], 'positive_control_changed_indices':diff,
            'positive_control_changed_features':[ns['FEATURE_NAMES'][i] for i in diff],
            'positive_control_values':[[float(base[i]),float(selected_changed[i])] for i in diff],
            'base_feature_vector_sha256':hashlib.sha256(base.tobytes()).hexdigest()}
    return out

def main():
    started=time.monotonic(); before=source_hashes();h=head()
    assert h==EXPECTED_HEAD,(h,EXPECTED_HEAD)
    for p,v in EXPECTED.items():assert before[p]==v,(p,before[p])
    gn={'np':np}
    geonodes=extract(ROOT/SOURCES[1], {'mirror_positions'}, {'DIR_DX','DIR_DY'},gn)
    geo=SimpleNamespace(**{k:v for k,v in gn.items() if k!='__builtins__'})
    ns={'np':np,'geo':geo}
    fnodes=extract(ROOT/SOURCES[0], {'_names','_nearest','build_features'},
                  {'MAX_UNIT_ENERGY','MAX_TILE_ENERGY','N_MATCHES','_DIR_NAMES','FEATURE_NAMES','FEATURE_DIM'},ns)
    result={'protocol':{'cases':[list(c) for c in CASES],'local_steps':[65,85],
                       'own_denominator':'mask at t, energy>=0, final cardinal action1..4',
                       'convergence':'visible-at-t enemy with cardinal action1..4 has same nominal proposed destination; energy eligibility and actual next masks separate',
                       'nearest':'all visible masked enemies including negative energy, ascending UID ties; world and canonical identical UID',
                       'stop':'fixture failure OR omitted-convergence evidence limited to known card510930 => close path',
                       'max_effort_minutes':30,'only_numpy_and_stdlib':True},
            'head_before':h,'source_hashes_before':before,'script_sha256':sha(__file__),
            'ast_nodes':{'features':fnodes,'geometry':geonodes},
            'source_inspection':{'make_context_enemy_order':'np.where(enemy_mask)[0] ascending; filters negative position but NOT negative energy',
                                 'nearest_tie':'np.argmin returns first ascending-UID entry; Manhattan invariant under mirror_positions',
                                 'observer':'visible_context also iterates ascending mask IDs, excludes invisible coordinates, no energy filter; trace actions and coordinates world frame'},
            'cases':[]}
    anchor=None;all_events=[];totals={'transitions':0,'recorded_unit_decisions':0,'nonnegative_own_moves':0,'own_moves_with_convergence':0,'convergent_pairs':0,'own_moves_with_omitted_convergence':0,'omitted_pairs':0}
    for seed,side,match in CASES:
        p=DATA/f'{seed}_player_{side}.jsonl.gz';ph=sha(p)
        rows=[]
        with gzip.open(p,'rt') as f:
            for line in f:
                z=json.loads(line)
                if z['match']==match-1 and 65<=z['match_step_t']<=85:rows.append(z)
        assert [z['match_step_t'] for z in rows]==list(range(65,86))
        c={'seed':seed,'side':side,'match':match,'raw_sha256':ph,'transitions':len(rows),
           'recorded_unit_decisions':0,'nonnegative_own_moves':0,'own_moves_with_convergence':0,
           'convergent_pairs':0,'own_moves_with_omitted_convergence':0,'omitted_pairs':0,'events':[]}
        for r in rows:
            if (seed,side,match,r['match_step_t'])==(510930,1,2,78):anchor=r
            a=r['truth_t'];b=r['truth_after'];units=r['decision']['units']
            c['recorded_unit_decisions']+=len(units)
            expected={i for i in range(16) if a['mask'][side][i] and a['energy'][side][i]>=0 and 1<=r['actions'][f'player_{side}'][i][0]<=4}
            moves=[u for u in units if a['mask'][side][u['uid']] and u['energy']>=0 and 1<=u['final_action'][0]<=4]
            assert {u['uid'] for u in moves}==expected
            for u in moves:
                uid=u['uid']; assert u['final_action']==r['actions'][f'player_{side}'][uid]
                assert u['position']==a['position'][side][uid] and u['energy']==a['energy'][side][uid]
                c['nonnegative_own_moves']+=1;dest=nominal(u['position'],u['final_action'])
                enemies=u['visible_enemies'];assert [e['uid'] for e in enemies]==sorted(e['uid'] for e in enemies)
                selected=nearest(enemies,u['position'])
                mirrored=[dict(e,position=geo.mirror_positions(np.array([e['position']]))[0].tolist()) for e in enemies]
                assert nearest(mirrored,geo.mirror_positions(np.array([u['position']]))[0])==selected
                events=[]
                for e in enemies:
                    eid=e['uid'];assert a['mask'][1-side][eid]
                    assert e['position']==a['position'][1-side][eid] and e['energy']==a['energy'][1-side][eid]
                    ea=r['actions'][f'player_{1-side}'][eid]
                    if not (1<=ea[0]<=4 and nominal(e['position'],ea)==dest):continue
                    event={'local_t':r['match_step_t'],'global_t':r['step_t'],'own_uid':uid,'enemy_uid':eid,
                        'own_position':u['position'],'enemy_position':e['position'],'own_energy':u['energy'],'enemy_energy':e['energy'],
                        'own_action':u['final_action'],'enemy_action':ea,'nominal_destination':dest,
                        'nearest_feature_uid':selected,'enemy_omitted_from_nearest':eid!=selected,
                        'nearest_feature_enemy':next(dict(uid=q['uid'],position=q['position'],energy=q['energy']) for q in enemies if q['uid']==selected),
                        'visible_enemy_count':len(enemies),
                        'negative_energy_visible_enemy_ids':[q['uid'] for q in enemies if q['energy']<0],
                        'enemy_nonnegative':e['energy']>=0,'own_can_pay_move':u['energy']>=u['move_cost'],
                        'enemy_can_pay_move':e['energy']>=u['move_cost'],
                        'own_after_mask':b['mask'][side][uid],'enemy_after_mask':b['mask'][1-side][eid],
                        'own_after_position':b['position'][side][uid],'enemy_after_position':b['position'][1-side][eid],
                        'own_after_energy_raw':b['energy'][side][uid],'enemy_after_energy_raw':b['energy'][1-side][eid]}
                    events.append(event)
                if events:
                    c['own_moves_with_convergence']+=1
                    c['own_moves_with_omitted_convergence']+=int(any(e['enemy_omitted_from_nearest'] for e in events))
                    c['convergent_pairs']+=len(events);c['omitted_pairs']+=sum(e['enemy_omitted_from_nearest'] for e in events)
                    c['events'].extend(events);all_events.extend(dict(e,seed=seed,side=side,match=match) for e in events)
        assert ph==sha(p)
        for k in totals:totals[k]+=c[k]
        result['cases'].append(c)
    assert totals['transitions']==84 and totals['recorded_unit_decisions']<=1344
    result['fixture']=fixture(ns,geo,anchor)
    result['totals']=totals
    result['omitted_convergence_cards']=sorted({e['seed'] for e in all_events if e['enemy_omitted_from_nearest']})
    result['convergence_cards']=sorted({e['seed'] for e in all_events})
    result['decision']='close_path_per_predeclared_stop' if not set(result['omitted_convergence_cards'])-{510930} else 'bounded_discussion_only_no_training_authorization'
    result['next_mask_counts']={f"own_{int(om)}_enemy_{int(em)}":sum(e['own_after_mask']==om and e['enemy_after_mask']==em for e in all_events) for om in (False,True) for em in (False,True)}
    result['source_hashes_after']=source_hashes();result['head_after']=head()
    assert before==result['source_hashes_after'] and h==result['head_after']
    result['forbidden_imports_loaded']=[m for m in sys.modules if m=='torch' or m.startswith('torch.') or m=='jax' or m.startswith('jax.') or m=='agents' or m.startswith('agents.')]
    assert not result['forbidden_imports_loaded']
    result['elapsed_compute_seconds']=round(time.monotonic()-started,3)
    assert time.monotonic()-started<30*60
    OUT.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('totals','omitted_convergence_cards','convergence_cards','next_mask_counts','decision','elapsed_compute_seconds')},indent=2))

if __name__=='__main__':main()
