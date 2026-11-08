#!/usr/bin/env python3
"""Independent output-ledger audit; stdlib only, no helper port or trace parsing."""
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib, json, math, re, subprocess
from pathlib import Path

B = Path('/tmp/guided-path-diagnosis-20261108').resolve()
R = B/'run_v1'
checks = 0
def check(condition, message):
    global checks
    checks += 1
    if not condition: raise ValueError(message)
def unique(pairs):
    out = {}
    for k, v in pairs:
        if k in out: raise ValueError('Duplicate JSON key: '+k)
        out[k] = v
    return out
def read(path): return json.loads(Path(path).read_text(), object_pairs_hook=unique)
def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''): h.update(block)
    return h.hexdigest()
def game(row): return row['seed'], row['side']
def ident(row): return (*game(row), row['step'], row['uid'])
def ledger(name):
    with (R/name).open() as f: return [json.loads(line, object_pairs_hook=unique) for line in f]
s, b, a = read(R/'summary.json'), read(B/'bindings.json'), read(B/'ROOT_APPROVAL.json')
pins = {str(B/k): v for k, v in a['sha256'].items()}
pins.update(b['inputs']); pins.update({str(R/k): v for k, v in s['artifacts'].items()})
pins[str(R/'summary.json')] = sha(R/'summary.json'); pins[str(B/'ROOT_APPROVAL.json')] = s['approval_sha256']
check(a['approved'] is True and s['status']=='complete' and not (R/'incomplete.json').exists(), 'Completion/approval')
check(s['script_sha256']==sha(B/'diagnose.py')=='997dc49f332de7aa6fba18cb314725c89b3824a6fde6d87b521bcfc7d12bafa2', 'Reviewed script')
check(s['bindings_sha256']==sha(B/'bindings.json'), 'Bindings digest')
for p, digest in pins.items(): check(sha(p)==digest, 'Input/output digest: '+p)
for t in b['traces']: check(sha(t['path'])==t['sha256'] and Path(t['path']).stat().st_size==t['bytes'], 'Trace byte binding')
root = Path(next(p for p in b['inputs'] if p.endswith('/agents/sherlock/main.py'))).parents[2]
check(subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==b['source']['current_head'], 'Frozen HEAD')
keys = [game(t) for t in b['traces']]
check(len(keys)==len(set(keys))==12 and [game(t) for t in s['games']]==keys, 'Twelve exact ordered games')
check(sum(t['bytes'] for t in b['traces'])==b['compressed_trace_bytes']==28710846, 'Compressed byte total')
gs, ops = ledger('golden.jsonl'), ledger('opportunities.jsonl')
gc, oc, steps, matches, classes = defaultdict(Counter), defaultdict(Counter), defaultdict(set), Counter(), Counter()
gold = {}; seen = set(); last = (-1,-1,-1); public_hash = {}
for row in gs:
    k=game(row); key=ident(row); order=(keys.index(k),row['step'],row['event_order'])
    check(k in keys and key not in gold and order>last, 'Golden identity/order'); last=order; gold[key]=row
    check(type(row['step']) is int and 0<row['step']<303 and row['step']%101 and type(row['uid']) is int and 0<=row['uid']<16, 'Golden bounds')
    check(all(type(row[x]) is int and 1<=row[x]<=4 for x in ('input','historical','recomputed')) and row['historical']==row['recomputed'], 'Golden output equality')
    gc[k]['golden_calls']+=1; gc[k]['golden_changes']+=int(row['input']!=row['historical'])
last=(-1,-1,-1)
for row in ops:
    k=game(row); key=ident(row); order=(keys.index(k),row['step'],row['uid'])
    check(k in keys and key not in seen and order>last, 'Opportunity identity/order'); seen.add(key); last=order
    check(type(row['step']) is int and 0<row['step']<303 and row['step']%101 and row['match_idx']==row['step']//101 and type(row['uid']) is int and 0<=row['uid']<16, 'Opportunity bounds')
    mask=row['mask']; x,y=row['position']; gx,gy=row['target']; move,fixed=row['guided_move'],row['helper_move']
    check(len(mask)==6 and all(type(v) is bool for v in mask) and mask[0] and all(type(v) is int and 0<=v<24 for v in (x,y,gx,gy)), 'Opportunity context')
    check(type(move) is int and type(fixed) is int and 1<=move<=4 and 1<=fixed<=4 and move!=fixed and mask[move] and mask[fixed], 'Distinct legal helper classes')
    check(row['bfs_here']>0 and (row['bfs_guided_destination']<0 or row['bfs_guided_destination']>=row['bfs_here']) and 0<=row['bfs_helper_destination']<row['bfs_here'], 'Stored BFS ordering')
    h=row['public_context_sha256']; fk=(*k,row['step'])
    check(re.fullmatch('[0-9a-f]{64}',h) and public_hash.get(fk,h)==h, 'Within-frame context digest'); public_hash[fk]=h
    check(row['target_class'] in ('known_point','candidate','exploration') and row['meaning']=='hypothetical helper opportunity only; no final action or outcome claim', 'Classification/claim scope')
    if key in gold and gold[key]['input']==move: check(gold[key]['historical']==fixed, 'Same-input cross-ledger output')
    oc[k]['hypothetical_helper_changes']+=1; oc[k]['changed_target_'+row['target_class']]+=1
    steps[k].add(row['step']); matches[(*k,row['match_idx'])]+=1; classes[row['target_class']]+=1
summed=Counter(); per_game=[]; groups=Counter()
for g in s['games']:
    k=game(g); c=Counter(g['counts']); summed.update(c); groups[g['group']]+=oc[k]['hypothetical_helper_changes']
    check(all(type(v) is int and v>=0 for v in c.values()) and (c['frames'],c['decision_frames'],c['reset_frames'])==(303,300,3), 'Frame/count schema')
    check(c['unit_decisions']==c['no_assigned_target']+c['assigned_units'] and c['assigned_units']==c['deterministic_guided_moves']+c['no_deterministic_guided_move'], 'Denominator partitions')
    for name in ('golden_calls','golden_changes'): check(c[name]==gc[k][name], 'Golden recount '+name)
    for name in ('hypothetical_helper_changes','changed_target_known_point','changed_target_candidate','changed_target_exploration'): check(c[name]==oc[k][name], 'Opportunity recount '+name)
    check(c['steps_with_hypothetical_change']==len(steps[k]) and c['hypothetical_helper_changes']<=c['deterministic_guided_moves'], 'Distinct steps/denominator')
    check(set(g['by_match'])=={'0','1','2'} and sum(v.get('deterministic_guided_moves',0) for v in g['by_match'].values())==c['deterministic_guided_moves'], 'Match denominator sum')
    for m in range(3): check(g['by_match'][str(m)].get('hypothetical_helper_changes',0)==matches[(*k,m)], 'Match opportunity recount')
    per_game.append(dict(seed=k[0],side=k[1],group=g['group'],golden=dict(gc[k]),opportunities=dict(oc[k]),distinct_steps=len(steps[k])))
check(summed==Counter(s['counts']) and len(gs)==22258 and len(ops)==343, 'Complete totals')
check((summed['frames'],summed['decision_frames'])==(b['expected_frames'],b['expected_decision_frames'])==(3636,3600), 'Bound frame totals')
check(s['games_with_opportunity']==sum(bool(oc[k]) for k in keys)==12 and s['map_seeds_with_opportunity']==sorted({k[0] for k in keys if oc[k]}) and len(s['map_seeds_with_opportunity'])==7, 'Game/map counts')
mass=Decimal('0.035')*len(ops)
check(Decimal(str(s['theoretical_branch_probability']))==Decimal('0.035') and Decimal(str(s['theoretical_conditional_expected_count']))==mass==Decimal('12.005'), 'Theoretical mass')
check(math.isfinite(s['elapsed_seconds']) and 0<s['elapsed_seconds']<b['max_seconds']==120, 'Reported duration bound')
check(all(any(term in x for x in s['limits']) for term in ('not representative','not an observed training share','random fallback','not final-action')), 'Honest limits')
for p, digest in pins.items(): check(sha(p)==digest, 'Final hash stability: '+p)
result=dict(status='PASS',checks=checks,golden_calls=len(gs),golden_changes=sum(v['golden_changes'] for v in gc.values()),hypothetical_helper_changes=len(ops),target_classes=dict(classes),groups=dict(groups),games=per_game,distinct_game_steps=sum(map(len,steps.values())),distinct_map_seeds=7,theoretical_mass=str(mass),script_sha256=sha(__file__),input_sha256=pins,limits=['No helper reimplementation or archive decompression; historical equality checked in emitted golden ledger.','343 opportunity rows independently recounted; all-unit/frame denominators checked arithmetically across summary, not independently regenerated.','Old selected evaluation states; 12.005 is theoretical mass over twelve archived executions, no observed training share or final-action/quality effect.'])
with Path('/tmp/guided-path-data-audit.json').open('x') as f: json.dump(result,f,indent=2); f.write('\n')
print(json.dumps({k:result[k] for k in ('status','checks','golden_calls','golden_changes','hypothetical_helper_changes','target_classes','groups','distinct_game_steps','theoretical_mass')}))
