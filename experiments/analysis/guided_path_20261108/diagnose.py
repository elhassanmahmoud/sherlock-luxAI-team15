#!/usr/bin/env python3
"""Fixed archive-only guided-path diagnosis. Stdlib only; never imports project code.

prepare hashes compressed trace bytes but does NOT parse any trace.
selfcheck uses hand-built memory fixtures only. run needs a separately supplied
Root approval bound to this script, bindings.json and SPEC.md.
"""
import argparse
import ast
from collections import Counter, deque
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time

BASE = Path('/tmp/guided-path-diagnosis-20261108').resolve()
ROOT = Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
REL = Path('experiments/analysis/continuation_20261102')
FROZEN = '02ce1b2ce9a5b0780da1ee6462a2368b2226d495'
V14 = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
DX, DY = (0, 0, 1, 0, -1), (0, -1, 0, 1, 0)
KEYS = [(831006,'player_1'),(831029,'player_0'),(831042,'player_0'),
        (831042,'player_1'),(831043,'player_0'),(831043,'player_1'),
        (831000,'player_0'),(831000,'player_1'),(831001,'player_0'),
        (831001,'player_1'),(831002,'player_0'),(831002,'player_1')]
AST_ITEMS = {'agents/sherlock/main.py':['_path_fix','_step_toward','_guided_action'],
             'agents/sherlock/rules.py':['distance_map','first_step','PathCache.get']}
UNCHANGED_FILES = ['agents/sherlock/features.py','agents/sherlock/belief.py',
                   'agents/sherlock/geometry.py']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def write(path, value):
    path = Path(path).resolve()
    require(BASE in path.parents, 'Output must remain under fixed /tmp directory')
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def read_json(path):
    return json.loads(Path(path).read_text())


def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args],timeout=10)


def ast_part(raw, name):
    tree = ast.parse(raw)
    if '.' in name:
        cls, member = name.split('.')
        classes=[x for x in tree.body if isinstance(x,ast.ClassDef) and x.name==cls]
        require(len(classes)==1, 'Ambiguous class '+cls)
        nodes=[x for x in classes[0].body if isinstance(x,ast.FunctionDef) and x.name==member]
    else:
        nodes=[x for x in ast.walk(tree) if isinstance(x,ast.FunctionDef) and x.name==name]
    require(len(nodes)==1, 'Ambiguous function '+name)
    return ast.dump(nodes[0],include_attributes=False)


def source_proof(manifest):
    historical=manifest['git_head'];proof={}
    for relative in [*AST_ITEMS,*UNCHANGED_FILES,'scripts/targeting_probe.py']:
        old=git('show',f'{historical}:{relative}')
        pins=[v for k,v in manifest['sources'].items() if k.endswith('/'+relative)]
        require(len(pins)==1 and hashlib.sha256(old).hexdigest()==pins[0], 'Historical blob not manifest-bound: '+relative)
        now=(ROOT/relative).read_bytes()
        item={'historical_sha256':pins[0],'current_sha256':hashlib.sha256(now).hexdigest()}
        if relative in AST_ITEMS:
            item['ast']={}
            for function in AST_ITEMS[relative]:
                a,b=ast_part(old,function),ast_part(now,function)
                require(a==b,'Historical/current helper AST differs: '+function)
                item['ast'][function]=hashlib.sha256(a.encode()).hexdigest()
        if relative in UNCHANGED_FILES:
            require(now==old,'Context/geometry source changed: '+relative)
        proof[relative]=item
    return {'historical_head':historical,'current_head':git('rev-parse','HEAD').decode().strip(),'files':proof}


def prepare():
    require(git('rev-parse','HEAD').decode().strip()==FROZEN,'Current frozen HEAD differs')
    keys_path=ROOT/REL/'diagnostic_keys.json';manifest_path=ROOT/REL/'targeting/manifest.json'
    keys=read_json(keys_path);m=read_json(manifest_path)
    require([(k['seed'],k['side']) for k in keys['keys']]==KEYS,'Fixed twelve keys changed')
    require(m['status']=='complete' and m['keys']==keys['keys'] and m['keys_sha256']==sha(keys_path),'Archive/key provenance differs')
    require(m['weights']['sha256']==V14,'Archive is not exact V14')
    sources=source_proof(m)
    files=[keys_path,manifest_path,ROOT/'experiments/analysis/artillery_alignment_20261108/prepared_v1/manifest.json']
    traces=[]
    for seed,side in KEYS:
        name=f'{seed}_{side}.jsonl.gz';path=ROOT/REL/'targeting'/name
        matches=[g for g in m['games'] if g['key']['seed']==seed and g['key']['side']==side]
        require(len(matches)==1,'Missing/duplicate archive game')
        game=matches[0]
        require(game['trace']['path']==name and game['trace']['sha256']==sha(path),'Trace byte hash differs')
        require(all(game['passivity'].values()),'Historical observation passivity did not pass')
        traces.append({'seed':seed,'side':side,'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size})
        files.append(path)
    files.extend(ROOT/p for p in sources['files'])
    binding={'status':'prepared_only_no_trace_parsed','schema':1,'source':sources,'traces':traces,
             'inputs':{str(p):sha(p) for p in files},'input_sizes':{str(p):p.stat().st_size for p in files},
             'compressed_trace_bytes':sum(t['bytes'] for t in traces),'expected_frames':3636,
             'expected_decision_frames':3600,'max_seconds':120,'max_line_bytes':2_000_000,
             'hypothesis':'guided deterministic move followed by existing path_fix; no random fallback',
             'theoretical_branch_probability':0.035,'actual_games':0,'model_forwards':0}
    write(BASE/'bindings.json',binding)
    print(json.dumps({'status':binding['status'],'traces':len(traces),'compressed_bytes':binding['compressed_trace_bytes'],'ast_equal':True}))


def distance_map(passable, target):
    w,h=len(passable),len(passable[0]);gx,gy=target
    d=[[-1]*h for _ in range(w)];d[gx][gy]=0;queue=deque([(gx,gy)])
    # Matches rules.py exactly: even a blocked target is seeded at distance0.
    while queue:
        x,y=queue.popleft()
        for action in range(1,5):
            nx,ny=x+DX[action],y+DY[action]
            if 0<=nx<w and 0<=ny<h and d[nx][ny]<0 and passable[nx][ny]:
                d[nx][ny]=d[x][y]+1;queue.append((nx,ny))
    return d


def first_step(dist, position, mask, energy):
    w,h=len(dist),len(dist[0]);x,y=position;here=dist[x][y];best=None;best_energy=-math.inf
    for action in range(1,5):
        if not mask[action]:continue
        nx,ny=x+DX[action],y+DY[action]
        if not (0<=nx<w and 0<=ny<h):continue
        nd=dist[nx][ny]
        if nd<0:continue
        if here<0 or nd<here:
            e=energy[nx][ny]
            if best is None or e>best_energy:best,best_energy=action,e
    return best


def toward(position,target,mask):
    if target is None:return None
    x,y=position;dx,dy=target[0]-x,target[1]-y
    if abs(dx)>=abs(dy):prefs=[2 if dx>0 else 4,3 if dy>0 else 1]
    else:prefs=[3 if dy>0 else 1,2 if dx>0 else 4]
    if dx==0:prefs=[a for a in prefs if a not in (4,2)]
    if dy==0:prefs=[a for a in prefs if a not in (1,3)]
    return next((a for a in prefs if mask[a]),None)


def path_fix(position,target,mask,action,dist,energy):
    if target is None:return action
    x,y=position;tx,ty=x+DX[action],y+DY[action];here=dist[x][y]
    if here<=0:return action
    nd=dist[tx][ty]
    if 0<=nd<here:return action
    gx,gy=target
    if abs(gx-tx)+abs(gy-ty)>=abs(gx-x)+abs(gy-y):return action
    better=first_step(dist,position,mask,energy)
    return action if better is None else better


def selfcheck():
    mask=[True]*6;grid=[[True]*5 for _ in range(5)];energy=[[0.0]*5 for _ in range(5)]
    checks=[]
    def check(name,actual,expected):
        require(actual==expected,f'Selfcheck {name}: {actual!r} != {expected!r}')
        checks.append(name)
    check('open_grid_distance',distance_map(grid,(4,4))[0][0],8)
    blocked=[row[:] for row in grid];blocked[4][4]=False
    check('blocked_goal_seeded',distance_map(blocked,(4,4))[4][3],1)
    for x,y in [(3,2),(2,1),(2,3)]:grid[x][y]=False
    dist=distance_map(grid,(4,2));energy[1][1]=9.;energy[1][3]=4.
    check('guided_deadend',toward((1,2),(4,2),mask),2)
    check('deadend_longer',dist[2][2]>dist[1][2],True)
    check('energy_first_step',path_fix((1,2),(4,2),mask,2,dist,energy),1)
    energy[1][3]=9.;check('equal_energy_first_direction',first_step(dist,(1,2),mask,energy),1)
    no_up=mask[:];no_up[1]=False
    check('mask_excludes_energy_tie',path_fix((1,2),(4,2),no_up,2,dist,energy),3)
    no_routes=[True,False,True,False,False,False]
    check('no_legal_better_keeps_move',path_fix((1,2),(4,2),no_routes,2,dist,energy),2)
    check('away_move_kept',path_fix((1,2),(4,2),mask,4,dist,energy),4)
    check('target_already_reached',toward((1,2),(1,2),mask),None)
    check('missing_target_no_random',toward((1,2),None,mask),None)
    empty=[True,False,False,False,False,False]
    check('blocked_guided_no_random',toward((1,2),(4,2),empty),None)
    wall=[[True]*5 for _ in range(5)]
    for y in range(5):wall[2][y]=False
    unreach=distance_map(wall,(4,2))
    check('unreachable_here',unreach[1][2],-1)
    check('unreachable_helper_keeps_move',path_fix((1,2),(4,2),mask,2,unreach,energy),2)
    edge_dist=distance_map([[True]*3 for _ in range(3)],(2,2));edge_energy=[[0]*3 for _ in range(3)]
    check('edge_safe_first_step',first_step(edge_dist,(0,0),mask,edge_energy),2)
    check('energy_beats_direction_order',first_step([[2,1],[1,0]],(0,0),mask,[[0,5],[8,0]]),2)
    check('guided_equal_axes_prefers_horizontal',toward((0,0),(2,2),mask),2)
    check('guided_vertical_fallback',toward((0,0),(2,2),[True,False,False,True,False,False]),3)
    print(json.dumps({'status':'selfcheck_pass','checks':checks,'count':len(checks),'real_traces_read':0}))


def validate_frame(frame,game,index,expected_cfg):
    key=frame['key'];require((key['seed'],key['side'])==(game['seed'],game['side']) and key['obs_step']==index,'Trace key/order differs')
    require(key['match_idx']==index//101 and key['match_step']==index%101,'Unexpected match chronology')
    if frame['status']=='reset':
        require(key['match_step']==0 and not frame['units'] and not frame['events'],'Invalid reset row')
        return None
    require(frame['status']=='decision' and key['match_step']>0,'Missing decision context')
    p=frame['public'];w,h=p['W'],p['H'];require(w==24 and h==24,'Unexpected map dimensions')
    require(p['config']==expected_cfg,'Full archived frame config differs from manifest')
    require(p['config']['path_fix'] is True,'Archive path_fix inactive')
    require(p['step']==index and p['match_step']==key['match_step'] and p['match_idx']==key['match_idx'],'Public/key chronology differs')
    for field in ['passable','point_tiles','candidate','energy_map']:
        require(len(p[field])==w and all(len(row)==h for row in p[field]),'Bad map shape '+field)
    require(all(type(v) is bool for row in p['passable'] for v in row),'Passability not boolean')
    require(all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for row in p['energy_map'] for v in row),'Invalid energy map')
    units={u['uid']:u for u in frame['units']}
    require(len(units)==len(frame['units']) and list(units)==p['ally_ids'],'Unit identities/order differ')
    for uid,u in units.items():
        require(type(uid) is int and 0<=uid<len(p['ally_pos']),'Invalid unit id')
        pos=p['ally_pos'][uid];target=p['assigned'].get(str(uid))
        require(pos==u['position'] and p['ally_ene'][uid]==u['energy'] and target==u['assigned_target'],'Unit/public context differs')
        require(len(pos)==2 and all(type(v) is int for v in pos) and 0<=pos[0]<w and 0<=pos[1]<h,'Bad unit position')
        require(target is None or (len(target)==2 and all(type(v) is int for v in target) and 0<=target[0]<w and 0<=target[1]<h),'Bad target')
        mask=u['mask'];require(len(mask)==6 and all(type(v) is bool for v in mask) and mask[0],'Bad action mask')
        for a in range(1,5):
            if mask[a]:
                nx,ny=pos[0]+DX[a],pos[1]+DY[a]
                require(0<=nx<w and 0<=ny<h and p['passable'][nx][ny] and u['energy']>=p['move_cost'],'Legal move violates geometry/energy')
    return p,units


def run():
    approval=read_json(BASE/'ROOT_APPROVAL.json')
    for name in ['diagnose.py','bindings.json','SPEC.md','PLAN.md']:
        require(approval.get('sha256',{}).get(name)==sha(BASE/name),'Root approval missing/exact bytes differ: '+name)
    require(approval.get('approved') is True,'Root approval absent')
    b=read_json(BASE/'bindings.json');require(git('rev-parse','HEAD').decode().strip()==FROZEN,'Frozen HEAD differs')
    require(all(sha(p)==v for p,v in b['inputs'].items()),'Bound input changed')
    m=read_json(ROOT/REL/'targeting/manifest.json');require(source_proof(m)==b['source'],'Bound source proof changed')
    current=read_json(ROOT/'experiments/analysis/artillery_alignment_20261108/prepared_v1/manifest.json')['source_config']
    require(current['path_fix'] is True and current['guided_prob']==.7 and current['eps_end']==.05,'Current recipe differs')
    out=BASE/'run_v1';out.mkdir(exist_ok=False);started=time.monotonic();reports=[];total=Counter()
    try:
        os.nice(10)
        with (out/'golden.jsonl').open('x') as golden,(out/'opportunities.jsonl').open('x') as opportunities:
            for game in b['traces']:
                archived=[g for g in m['games'] if g['key']['seed']==game['seed'] and g['key']['side']==game['side']][0]
                cfg=archived['observed']['config'];counts=Counter();by_match={str(k):Counter() for k in range(3)}
                hashes=hashlib.sha256();observed_steps=set()
                with gzip.open(game['path'],'rt') as stream:
                    for index,line in enumerate(stream):
                        require(time.monotonic()-started<b['max_seconds'],'Fixed runtime bound exceeded; incomplete, no automatic retry')
                        require(len(line.encode())<=b['max_line_bytes'],'Trace row exceeds bound')
                        frame=json.loads(line);before=digest(frame);context=validate_frame(frame,game,index,cfg);counts['frames']+=1
                        if context is None:counts['reset_frames']+=1;continue
                        counts['decision_frames']+=1;p,units=context;cache={}
                        def distances(target):
                            if target is None:return None
                            key=tuple(target)
                            if key not in cache:cache[key]=distance_map(p['passable'],key)
                            return cache[key]
                        # Golden cases must all pass before this frame's hypothetical counts.
                        golden_uids=set()
                        for event_index,event in enumerate(frame['events']):
                            require(event['order']==event_index,'Event order differs')
                            if event['method']!='_path_fix':continue
                            uid=event['uid'];require(uid in units and uid not in golden_uids,'Golden unit absent/duplicated')
                            golden_uids.add(uid)
                            u=units[uid];args=event['arguments'];target=p['assigned'].get(str(uid))
                            require(event['return_status']=='returned' and args==event['arguments_after'] and set(args)=={'mask','a'},'Invalid/mutated golden arguments')
                            require(args['mask']==u['mask'] and event['caller_action_status']=='observed' and event['caller_action']==args['a'],'Golden mask/caller differs')
                            require(event['unit_context']=={'position':u['position'],'energy':u['energy'],'target':target},'Golden call-time/public context differs')
                            a=args['a'];require(type(a) is int and 1<=a<=4 and u['mask'][a],'Invalid golden action')
                            fixed=path_fix(u['position'],target,u['mask'],a,distances(target),p['energy_map'])
                            require(type(event['return']) is int and fixed==event['return'],'Golden historical helper does not reproduce')
                            counts['golden_calls']+=1;counts['golden_changes']+=fixed!=a
                            golden.write(json.dumps({'seed':game['seed'],'side':game['side'],'step':index,'uid':uid,'event_order':event['order'],'input':a,'historical':event['return'],'recomputed':fixed})+'\n')
                        for uid,u in units.items():
                            counts['unit_decisions']+=1;target=p['assigned'].get(str(uid));move=toward(u['position'],target,u['mask'])
                            if target is None:counts['no_assigned_target']+=1;continue
                            counts['assigned_units']+=1
                            if move is None:counts['no_deterministic_guided_move']+=1;continue
                            counts['deterministic_guided_moves']+=1
                            d=distances(target);fixed=path_fix(u['position'],target,u['mask'],move,d,p['energy_map'])
                            by_match[str(frame['key']['match_idx'])]['deterministic_guided_moves']+=1
                            if fixed==move:continue
                            counts['hypothetical_helper_changes']+=1;by_match[str(frame['key']['match_idx'])]['hypothetical_helper_changes']+=1;observed_steps.add(index)
                            x,y=u['position'];tx,ty=target
                            kind='known_point' if p['point_tiles'][tx][ty] else 'candidate' if p['candidate'][tx][ty] else 'exploration'
                            counts['changed_target_'+kind]+=1
                            opportunities.write(json.dumps({'seed':game['seed'],'side':game['side'],'step':index,'match_idx':frame['key']['match_idx'],'uid':uid,'position':u['position'],'target':target,'target_class':kind,'mask':u['mask'],'guided_move':move,'helper_move':fixed,'bfs_here':d[x][y],'bfs_guided_destination':d[x+DX[move]][y+DY[move]],'bfs_helper_destination':d[x+DX[fixed]][y+DY[fixed]],'public_context_sha256':digest(p),'meaning':'hypothetical helper opportunity only; no final action or outcome claim'})+'\n')
                        require(digest(frame)==before,'In-memory archived frame mutated');hashes.update(before.encode())
                require(counts['frames']==303 and counts['decision_frames']==300 and counts['reset_frames']==3,'Incomplete fixed archive')
                counts['steps_with_hypothetical_change']=len(observed_steps);total.update(counts)
                reports.append({'seed':game['seed'],'side':game['side'],'group':archived['key']['group'],'counts':dict(counts),'by_match':{k:dict(v) for k,v in by_match.items()},'decision_frames_sha256':hashes.hexdigest()})
        require(total['golden_calls']>0,'No historical golden calls available')
        require(all(sha(p)==v for p,v in b['inputs'].items()) and git('rev-parse','HEAD').decode().strip()==FROZEN,'Source/input changed during run')
        changed=[g for g in reports if g['counts'].get('hypothetical_helper_changes',0)]
        result={'status':'complete','counts':dict(total),'games':reports,'games_with_opportunity':len(changed),'map_seeds_with_opportunity':sorted({g['seed'] for g in changed}),
                'theoretical_branch_probability':.035,'theoretical_conditional_expected_count':.035*total['hypothetical_helper_changes'],
                'limits':['Selected old evaluation frames, not representative training states.','Theoretical .035 mass is not an observed training share.','Only deterministic guided moves; random fallback omitted and counted.','Helper changes are not final-action differences or quality/strength evidence.','No hidden truth, models, forward passes, games, updates, or policy changes.'],
                'elapsed_seconds':time.monotonic()-started,'bindings_sha256':sha(BASE/'bindings.json'),'script_sha256':sha(BASE/'diagnose.py'),'approval_sha256':sha(BASE/'ROOT_APPROVAL.json'),
                'artifacts':{p.name:sha(p) for p in [out/'golden.jsonl',out/'opportunities.jsonl']}}
        write(out/'summary.json',result);print(json.dumps({'status':'complete','golden_calls':total['golden_calls'],'hypothetical_helper_changes':total['hypothetical_helper_changes'],'elapsed_seconds':result['elapsed_seconds']}))
    except BaseException as exc:
        write(out/'incomplete.json',{'status':'incomplete','error':f'{type(exc).__name__}: {exc}','elapsed_seconds':time.monotonic()-started,'completed_games':reports})
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','selfcheck','run']);args=parser.parse_args()
    {'prepare':prepare,'selfcheck':selfcheck,'run':run}[args.mode]()
