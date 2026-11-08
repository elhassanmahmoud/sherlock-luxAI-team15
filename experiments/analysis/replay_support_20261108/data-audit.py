#!/usr/bin/env python3
"""Independent saved-array recount; no project imports, models, or game execution."""
import collections, hashlib, json, math, os, signal, time, zipfile
from pathlib import Path
BASE=Path('/tmp/replay-support-diagnosis-20261108')
OUT=Path('/tmp/replay-support-data-audit')
START=time.monotonic()
CHECKS=0
ARMS=('control41','neutral41','control42','neutral42')
MEMBERS=(36,38,37,39)

def ck(condition,label):
    global CHECKS
    CHECKS+=1
    if not condition: raise AssertionError(label)
    if time.monotonic()-START>120: raise TimeoutError('120 second limit')

def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        while data:=f.read(1048576):h.update(data)
    return h.hexdigest()

def read(p):return json.loads(Path(p).read_text())

def alarm(*_):raise TimeoutError('120 second hard limit')

signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,120)
os.nice(10)
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[key]='1'
import numpy as np

def blocks(archive,key,shape,dtype):
    with archive.open(key+'.npy') as f:
        version=np.lib.format.read_magic(f)
        ck(version in ((1,0),(2,0)),key+' version')
        reader=np.lib.format.read_array_header_1_0 if version==(1,0) else np.lib.format.read_array_header_2_0
        found,fortran,dt=reader(f)
        ck(found==shape and not fortran and dt==np.dtype(dtype),key+' schema')
        stride=math.prod(shape[1:])*dt.itemsize
        for start in range(0,shape[0],8192):
            count=min(8192,shape[0]-start);raw=f.read(stride*count)
            ck(len(raw)==stride*count,key+' payload')
            yield start,np.frombuffer(raw,dtype=dt).reshape((count,*shape[1:]))
        ck(f.read(1)==b'',key+' end')

try:
    bind=read(BASE/'bindings.json');summary=read(BASE/'run_v1/summary.json');approval=read(BASE/'ROOT_APPROVAL.json')
    inputs=dict(bind['inputs'])
    for name in ('support.py','SPEC.md','bindings.json'):
        ck(digest(BASE/name)==approval['sha256'][name],name+' approved bytes')
    ck(approval['approved'] is True and approval['allow_numpy_saved_arrays_only'] is True,'approval')
    for field,name in [('rows_sha256','run_v1/rows.jsonl'),('bindings_sha256','bindings.json'),('script_sha256','support.py'),('approval_sha256','ROOT_APPROVAL.json')]:
        ck(digest(BASE/name)==summary[field],field)
    for path,sha in inputs.items():ck(digest(path)==sha,'input '+path)
    rows=[json.loads(line) for line in (BASE/'run_v1/rows.jsonl').read_text().splitlines()]
    ck(len(rows)==10000 and {r['bank_row'] for r in rows}==set(range(10000)),'row count/identity')
    rows={r['bank_row']:r for r in rows}
    bank_path=next(Path(p) for p in inputs if p.endswith('/bank.npz'))
    outputs_path=next(Path(p) for p in inputs if p.endswith('/outputs.npz'))
    with np.load(bank_path,allow_pickle=False) as src:
        ns=src['ns'];mask=src['mask'];ix=src['row_indices'];ai=src['arm_indices']
    with np.load(outputs_path,allow_pickle=False) as src:
        q=src['member_q'];labels=src['member_labels'].tolist()
        ck(np.array_equal(ix,src['row_indices']) and np.array_equal(ai,src['arm_indices']),'output identity')
        ck(src['ordered_member_hashes'].tolist()==bind['ordered_member_hashes'],'member hashes')
    ck(ns.shape==(10000,79) and ns.dtype==np.dtype('<f4') and np.isfinite(ns).all(),'ns schema')
    ck(mask.shape==(10000,6) and mask.dtype==np.bool_ and mask.any(axis=1).all(),'mask schema')
    ck(ix.shape==(10000,) and ix.dtype==np.dtype('<i8') and ai.shape==(10000,) and ai.dtype==np.uint8,'index schema')
    ck(q.shape==(40,10000,6) and q.dtype==np.dtype('<f4') and np.isfinite(q).all(),'q schema')
    ck(labels==[f'original{i}' for i in range(36)]+['control41','control42','neutral41','neutral42'],'labels')
    per_arm=[];totals=collections.Counter();source_rows=0
    for arm_index,(arm,member) in enumerate(zip(ARMS,MEMBERS)):
        ids=np.flatnonzero(ai==arm_index);original=ix[ids];role=bind['roles'][arm]
        ck(len(ids)==2500 and len(np.unique(original))==2500 and original.min()>=0 and original.max()<300000,arm+' source indexes')
        ck(role['member_index']==member and role['bank_arm_index']==arm_index and labels[member]==arm,arm+' role')
        ck(role['member_sha256']==bind['ordered_member_hashes'][member],arm+' member hash')
        legal_q=np.where(mask[ids],q[member,ids],-np.inf)
        winners=np.argmax(legal_q,axis=1)
        targetkeys=[ns[j].tobytes() for j in ids]
        hist={key:np.zeros(6,dtype=np.int64) for key in targetkeys}
        path=Path(role['buffer']);origin_verified=collections.Counter()
        with zipfile.ZipFile(path) as z:
            for name,shape,dtype in [('ns',(300000,79),'<f4'),('mask',(300000,6),'?'),('done',(300000,),'<f4')]:
                for start,part in blocks(z,name,shape,dtype):
                    locals_=np.flatnonzero((original>=start)&(original<start+len(part)))
                    for local in locals_:
                        actual=part[int(original[local])-start];global_row=int(ids[local])
                        if name=='done':ck(float(actual)==0.,arm+' nonterminal')
                        else:ck(actual.tobytes()==(ns[global_row] if name=='ns' else mask[global_row]).tobytes(),arm+' '+name+' origin')
                        origin_verified[name]+=1
            actions=np.empty(300000,dtype=np.int64)
            for start,part in blocks(z,'a',(300000,),'<i8'):actions[start:start+len(part)]=part
            ck(((actions>=0)&(actions<6)).all(),arm+' action range')
            for start,part in blocks(z,'s',(300000,79),'<f4'):
                ck(np.isfinite(part).all(),arm+' current s finite')
                for offset,value in enumerate(part):
                    key=value.tobytes()
                    if key in hist:hist[key][int(actions[start+offset])]+=1
            source_rows+=300000
        counts=collections.Counter();matched=[];margin_count=0
        for local,j in enumerate(ids):
            j=int(j);r=rows[j];h=hist[targetkeys[local]].tolist();total=sum(h);winner=int(winners[local])
            legal=np.flatnonzero(mask[j]);sorted_values=sorted(float(q[member,j,a]) for a in legal)
            margin=sorted_values[-1]-sorted_values[-2] if len(sorted_values)>1 else None
            margin_count+=margin is not None
            kind='unknown_no_current_s_match' if total==0 else 'matched_winner_observed' if h[winner]>0 else 'matched_winner_unobserved'
            expected={'arm':arm,'bank_row':j,'source_transition_index':int(original[local]),'member_index':member,
                'feature_bytes_sha256':hashlib.sha256(targetkeys[local]).hexdigest(),'masked_endnetwork_winner':winner,
                'legal_q_margin':margin,'actual_a_counts_at_exact_current_s':h,'current_s_matches':total,
                'winner_action_matches':h[winner],'conditional_empirical_winner_share':h[winner]/total if total else None,'classification':kind}
            ck(r==expected,arm+' complete row '+str(j))
            counts[kind]+=1
            if total:matched.append(total)
        expected_arm={'arm':arm,'bank_rows':2500,'unique_feature_byte_keys':len(hist),'counts':dict(counts),
            'matched_row_multiplicity':{'count':len(matched),'sum':sum(matched),'max':max(matched,default=0)},
            'legal_margin_rows':margin_count,'bank_origin_checks':dict(origin_verified),'terminal_bank_rows':0,'nonterminal_bank_rows':2500,
            'buffer_sha256':inputs[str(path)]}
        ck(summary['arms'][arm_index]==expected_arm,arm+' summary')
        per_arm.append({'arm':arm,'observed':counts['matched_winner_observed'],'unobserved':counts['matched_winner_unobserved'],'unknown':counts['unknown_no_current_s_match']})
        totals.update(counts)
        del actions,hist
    ck(summary['status']=='complete' and summary['bank_rows']==10000 and summary['terminal_bank_rows']==0 and summary['nonterminal_bank_rows']==10000,'summary totals')
    ck(summary['pooled_row_counts']==dict(totals) and sum(totals.values())==10000,'category totals')
    for path,sha in inputs.items():ck(digest(path)==sha,'unchanged input '+path)
    artifacts={str(BASE/p):digest(BASE/p) for p in ('support.py','SPEC.md','bindings.json','ROOT_APPROVAL.json','run_v1/rows.jsonl','run_v1/summary.json')}
    report={'status':'PASS','checks':CHECKS,'bank_rows':10000,'independently_streamed_current_s_rows':source_rows,
        'full_source_histograms_reconstructed':True,'per_arm':per_arm,'counts':dict(totals),'terminal_bank_rows':0,
        'elapsed_seconds':time.monotonic()-START,'numpy_version':np.__version__,'inputs':inputs,'artifacts':artifacts,
        'audit_script_sha256':digest(__file__),'limits':['Saved final Q only; no model forward, historical TD or quality claim.','Exact 79-feature bytes are not full Belief/state identity.','Finite correlated retained replay is descriptive; absence is not impossibility.','No original sampler RNG rerun, historical training or source policy re-execution.']}
except BaseException as exc:
    report={'status':'FAIL','checks':CHECKS,'error':f'{type(exc).__name__}: {exc}','elapsed_seconds':time.monotonic()-START}
    raise
finally:
    signal.setitimer(signal.ITIMER_REAL,0)
    with OUT.with_suffix('.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in report.items() if k in ('status','checks','bank_rows','independently_streamed_current_s_rows','elapsed_seconds','counts')}))
