#!/usr/bin/env python3
"""Fixed replay support question. No project imports or model execution.

prepare is stdlib-only and never opens NPZ contents. selfcheck uses only tiny
synthetic NumPy fixtures. Real NPZ contents require run and exact Root approval.
"""
import argparse
import ast
from collections import Counter
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import struct
import subprocess
import tempfile
import time
import zipfile

BASE=Path('/tmp/replay-support-diagnosis-20261108').resolve()
ROOT=Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
ARCHIVE=ROOT/'experiments/analysis/fog_influence_20261108/run_v1'
ARMS=('control41','neutral41','control42','neutral42')
NEW_MEMBERS=('control41','control42','neutral41','neutral42')
MEMBER_INDEX={arm:36+NEW_MEMBERS.index(arm) for arm in ARMS}
EXPECTED_BANK_SHA='e64df568ab55b9ba4ab915b061d3dd8449786f8bb6d9accdf65bea263e988774'
SOURCE_REL='scripts/fog_influence.py'
CHUNK=4096
LIMIT=120


def require(value,message):
    if not value:raise ValueError(message)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text())


def write(path,value):
    path=Path(path).resolve();require(BASE in path.parents,'Output outside fixed /tmp directory')
    with path.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def source_metadata(summary):
    source=summary['source'];old=subprocess.check_output(['git','-C',str(ROOT),'show',f"{source['head']}:{SOURCE_REL}"],timeout=10)
    matches=[v for p,v in source['files'].items() if p.endswith('/'+SOURCE_REL)]
    require(len(matches)==1 and hashlib.sha256(old).hexdigest()==matches[0],'Historical influence source not hash-bound')
    tree=ast.parse(old);constants={}
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id in {'ARMS','NEW_MEMBERS','LIMIT'}:
                    constants[target.id]=ast.literal_eval(node.value)
    require(constants=={'ARMS':ARMS,'NEW_MEMBERS':NEW_MEMBERS,'LIMIT':2500},'Historical ordering/sample limit differs')
    return {'historical_head':source['head'],'source_file':SOURCE_REL,'source_sha256':matches[0],
            'bank_arm_order':list(ARMS),'new_member_order':list(NEW_MEMBERS),'member_index':MEMBER_INDEX}


def prepare():
    summary=read(ARCHIVE/'summary.json');bank=read(ARCHIVE/'bank_manifest.json')
    require(summary['status']=='complete' and summary['bank']==bank,'Completed bank metadata differs')
    require(bank['sampled_rows']==10000 and bank['limit_per_arm']==2500 and tuple(bank['arms'])==ARMS,'Fixed bank differs')
    require(bank['bank_sha256']==EXPECTED_BANK_SHA and len(bank['ordered_member_hashes'])==40,'Bank identity/member hashes differ')
    proof=source_metadata(summary)
    expected={ARCHIVE/'bank.npz':bank['bank_sha256'],ARCHIVE/'outputs.npz':summary['outputs_sha256']}
    roles={}
    for index,arm in enumerate(ARMS):
        meta=bank['arms'][arm];path=ROOT/f'experiments/runs/20261108_fog_reward_{arm}/weights/agent.buffer.npz'
        require(Path(meta['path']).resolve()==path.resolve(),'Original arm buffer path differs')
        require(meta['source_rows']==300000 and meta['sampled_rows']==2500,'Fixed replay/bank row count differs')
        expected[path]=meta['sha256']
        roles[arm]={'bank_arm_index':index,'member_index':MEMBER_INDEX[arm],
                    'member_sha256':bank['ordered_member_hashes'][MEMBER_INDEX[arm]],
                    'buffer':str(path),'buffer_rows':meta['source_rows'],'bank_rows':meta['sampled_rows']}
    for path,want in expected.items():require(sha(path)==want,'Input bytes differ: '+str(path))
    for name in ('summary.json','bank_manifest.json'):expected[ARCHIVE/name]=sha(ARCHIVE/name)
    binding={'status':'prepared_only_no_npz_opened','source':proof,'roles':roles,
             'inputs':{str(p):v for p,v in expected.items()},'sizes':{str(p):p.stat().st_size for p in expected},
             'ordered_member_hashes':bank['ordered_member_hashes'],'max_bank_rows':10000,
             'max_seconds':LIMIT,'stream_chunk_rows':CHUNK,
             'arrays_from_source':{'bank':['ns','mask','row_indices','arm_indices'],
                'outputs':['member_q','V14_mean_q','CONTROL38_mean_q','NEUTRAL38_mean_q',
                           'CONTROL38_independent_mean_q','NEUTRAL38_independent_mean_q',
                           'row_indices','arm_indices','ordered_member_hashes','member_labels'],
                'replay':['s','ns','a','r','done','mask']},
             'no_model_imports':True,'real_npz_parsed':0}
    write(BASE/'bindings.json',binding)
    print(json.dumps({'status':binding['status'],'arm_mapping':MEMBER_INDEX,'stored_bytes':sum(binding['sizes'].values())}))


def winner(q,mask):
    require(len(q)==len(mask)==6 and all(math.isfinite(float(x)) for x in q),'Invalid six finite Q values')
    legal=[i for i,v in enumerate(mask) if v];require(legal,'No legal action')
    best=max(legal,key=lambda i:float(q[i]))
    gap=None if len(legal)==1 else float(q[best])-max(float(q[i]) for i in legal if i!=best)
    return best,gap


def histograms(query_keys,records,check=lambda:None):
    counts={key:[0]*6 for key in query_keys}
    for i,(key,action) in enumerate(records):
        if i%4096==0:check()
        require(type(action) is int and 0<=action<6,'Invalid recorded action')
        if key in counts:counts[key][action]+=1
    return counts


def classification(hist,selected):
    n=sum(hist)
    return ('unknown_no_current_s_match' if not n else
            'matched_winner_observed' if hist[selected] else 'matched_winner_unobserved')


def require_nonterminal(value):
    require(float(value) in (0.0,1.0),'Invalid original terminal value')
    require(float(value)==0.0,'Historical bank contract violated: terminal original transition')


def selfcheck():
    checks=[]
    def check(name,value,want):require(value==want,'Synthetic '+name);checks.append(name)
    a=struct.pack('<79f',*([1.0]*79));b=struct.pack('<79f',*([2.0]*79));missing=struct.pack('<79f',*([3.0]*79))
    h=histograms([a,a,b,missing],[(a,1),(a,1),(a,4),(b,0)])
    check('duplicate_query_not_duplicate_records',h[a],[0,2,0,0,1,0])
    check('missing_s_unknown',classification(h[missing],1),'unknown_no_current_s_match')
    check('matched_without_winner',classification(h[a],2),'matched_winner_unobserved')
    check('matched_with_winner',classification(h[a],1),'matched_winner_observed')
    check('mask_excludes_global_max',winner([99,2,1,0,-1,-2],[False,True,True,True,True,True]),(1,1.))
    check('tie_uses_first_action',winner([1,1,0,0,0,0],[True]*6),(0,0.))
    check('single_legal_margin_unknown',winner([4,3,2,1,0,-1],[False,False,False,False,False,True]),(5,None))
    plus=struct.pack('<79f',*([0.0]*79));minus=struct.pack('<79f',-0.0,*([0.0]*78))
    check('signed_zero_bytes_distinct',plus!=minus,True)
    check('signed_zero_not_merged',histograms([plus],[(minus,5)])[plus],[0]*6)
    check('arm_mapping_not_bank_order',MEMBER_INDEX,{'control41':36,'neutral41':38,'control42':37,'neutral42':39})
    left=histograms([a],[(a,0)]);right=histograms([a],[(a,5)])
    check('arms_not_pooled',(left[a][5],right[a][5]),(0,1))
    check('next_row_not_assigned_to_prior_s',histograms([a],[(b,5)])[a],[0]*6)
    rejected=0
    for q,m in [([float('nan')]*6,[True]*6),([0]*6,[False]*6)]:
        try:winner(q,m)
        except ValueError:rejected+=1
    check('nonfinite_or_empty_mask_rejected',rejected,2)
    try:histograms([a],[(a,6)])
    except ValueError:checks.append('invalid_replay_action_rejected')
    else:raise ValueError('Invalid action accepted')
    for env in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[env]='1'
    import numpy as np
    synthetic=np.asarray([[1.0]*79,[2.0]*79],dtype='<f4')
    check('numpy_bytes_match_struct',synthetic[0].tobytes(),a)
    with tempfile.TemporaryDirectory(dir=BASE,prefix='synthetic-') as directory:
        path=Path(directory)/'tiny.npz';np.savez(path,s=synthetic,a=np.asarray([1,5],dtype='<i8'))
        with zipfile.ZipFile(path) as zf:
            blocks=list(stream_array(zf,'s',(2,79),'<f4',np,lambda:None))
            check('synthetic_stream_preserves_bytes',b''.join(block.tobytes() for _,block in blocks),synthetic.tobytes())
            check('synthetic_stream_action_schema',list(stream_array(zf,'a',(2,),'<i8',np,lambda:None))[0][1].tolist(),[1,5])
            try:list(stream_array(zf,'s',(2,79),'<f8',np,lambda:None))
            except ValueError:checks.append('stream_wrong_dtype_rejected')
            else:raise ValueError('Wrong stream dtype accepted')
    check('masked_numpy_and_scalar_agree',winner(np.asarray([9,2,2,1,0,-1],dtype='<f4'),np.asarray([False,True,True,True,True,True]))[0],1)
    require_nonterminal(np.float32(0));checks.append('nonterminal_original_accepted')
    for value,label in [(np.float32(1),'terminal_original_aborts'),(np.float32(.5),'invalid_terminal_flag_aborts')]:
        try:require_nonterminal(value)
        except ValueError:checks.append(label)
        else:raise ValueError('Invalid bank terminal provenance accepted')
    print(json.dumps({'status':'selfcheck_pass','count':len(checks),'checks':checks,'numpy_version':np.__version__,'numerical_threads':1,'real_npz_parsed':0}))


def stream_array(zf,name,shape,dtype,np,check):
    """Bounded NPY streaming inside NPZ, preserving exact row bytes."""
    with zf.open(name+'.npy') as stream:
        version=np.lib.format.read_magic(stream)
        require(version in ((1,0),(2,0)),'Unsupported NPY header version')
        header=(np.lib.format.read_array_header_1_0 if version==(1,0) else np.lib.format.read_array_header_2_0)(stream)
        actual_shape,fortran,actual_dtype=header
        require(tuple(actual_shape)==tuple(shape) and not fortran and actual_dtype==np.dtype(dtype),'NPY schema/order differs: '+name)
        width=math.prod(shape[1:]) if len(shape)>1 else 1;stride=width*actual_dtype.itemsize
        for start in range(0,shape[0],CHUNK):
            check();count=min(CHUNK,shape[0]-start);raw=stream.read(count*stride)
            require(len(raw)==count*stride,'Truncated NPY payload')
            values=np.frombuffer(raw,dtype=actual_dtype).reshape((count,*shape[1:]))
            yield start,values
        require(stream.read(1)==b'','Extra NPY payload')


def run():
    approval=read(BASE/'ROOT_APPROVAL.json')
    require(approval.get('approved') is True and approval.get('allow_numpy_saved_arrays_only') is True,'Explicit Root/NumPy approval absent')
    for name in ('support.py','SPEC.md','bindings.json'):
        require(approval.get('sha256',{}).get(name)==sha(BASE/name),'Approval exact bytes differ: '+name)
    binding=read(BASE/'bindings.json');out=BASE/'run_v1';out.mkdir(exist_ok=False)
    started=time.monotonic()
    def check():require(time.monotonic()-started<LIMIT,'120-second deadline exceeded; incomplete, no automatic retry')
    def timeout(signum,frame):raise TimeoutError('120-second hard deadline')
    old_handler=signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,LIMIT)
    try:
        os.nice(10)
        for env in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[env]='1'
        # Deliberately deferred until after explicit approval; no Torch/project imports.
        import numpy as np
        for path,want in binding['inputs'].items():check();require(sha(path)==want,'Input hash changed')
        meta=read(ARCHIVE/'summary.json');require(source_metadata(meta)==binding['source'],'Historical metadata/order differs')
        with np.load(ARCHIVE/'bank.npz',allow_pickle=False) as bank:
            require(set(bank.files)==set(binding['arrays_from_source']['bank']),'Bank arrays differ')
            ns,mask,indices,arms=(bank[k] for k in ('ns','mask','row_indices','arm_indices'))
        require(ns.shape==(10000,79) and ns.dtype==np.dtype('<f4') and np.isfinite(ns).all(),'Bank ns schema differs')
        require(mask.shape==(10000,6) and mask.dtype==np.bool_ and mask.any(axis=1).all(),'Bank masks differ')
        require(indices.shape==(10000,) and indices.dtype==np.dtype('<i8') and arms.shape==(10000,) and arms.dtype==np.uint8,'Bank key schema differs')
        with np.load(ARCHIVE/'outputs.npz',allow_pickle=False) as outputs:
            require(set(outputs.files)==set(binding['arrays_from_source']['outputs']),'Saved output arrays differ')
            require(np.array_equal(outputs['row_indices'],indices) and np.array_equal(outputs['arm_indices'],arms),'Output/bank row keys differ')
            require(outputs['member_labels'].tolist()==[f'original{i}' for i in range(36)]+list(NEW_MEMBERS),'Member labels differ')
            require(outputs['ordered_member_hashes'].tolist()==binding['ordered_member_hashes'],'Member hashes differ')
            member_q=outputs['member_q']
        require(member_q.shape==(40,10000,6) and member_q.dtype==np.dtype('<f4') and np.isfinite(member_q).all(),'Stored Q schema differs')
        require(set(arms.tolist())=={0,1,2,3},'Bank arm indices differ')
        results=[]
        with (out/'rows.jsonl').open('x') as sink:
            for arm in ARMS:
                check();role=binding['roles'][arm];where=np.flatnonzero(arms==role['bank_arm_index'])
                require(len(where)==2500,'Wrong bank rows per arm')
                ix=indices[where];n=role['buffer_rows']
                require(len(np.unique(ix))==2500 and int(ix.min())>=0 and int(ix.max())<n,'Original row indices invalid')
                queries=ns[where];keys=[row.tobytes() for row in queries];selection=[winner(member_q[role['member_index'],i],mask[i]) for i in where]
                # Mapping verifies sampled ns, next-mask and nonterminal flag in the
                # original replay. It does NOT manufacture a next executed action.
                wanted={int(original):local for local,original in enumerate(ix)};verified=Counter();done_counts=Counter()
                path=Path(role['buffer'])
                with zipfile.ZipFile(path) as zf:
                    require(set(zf.namelist())=={k+'.npy' for k in binding['arrays_from_source']['replay']},'Replay members differ')
                    for name,shape,dtype in [('ns',(n,79),'<f4'),('mask',(n,6),'?'),('done',(n,),'<f4')]:
                        for start,block in stream_array(zf,name,shape,dtype,np,check):
                            selected=[i for i in wanted if start<=i<start+len(block)]
                            for original in selected:
                                local=wanted[original];value=block[original-start]
                                expected=queries[local] if name=='ns' else mask[where[local]] if name=='mask' else 0.0
                                if name=='done':
                                    require(float(value) in (0.0,1.0),'Invalid original terminal value')
                                    done_counts['terminal' if float(value) else 'nonterminal']+=1
                                    require_nonterminal(value)
                                require((value.tobytes()==expected.tobytes()) if name in ('ns','mask') else float(value)==expected,
                                        f'Bank origin/nonterminal provenance differs: {arm} row{original} array{name}')
                                verified[name]+=1
                    require(dict(verified)=={'ns':2500,'mask':2500,'done':2500},'Incomplete bank origin checks')
                    action_parts=[block.copy() for _,block in stream_array(zf,'a',(n,),'<i8',np,check)]
                    actions=np.concatenate(action_parts);del action_parts
                    require(((0<=actions)&(actions<6)).all(),'Replay action range differs')
                    def records():
                        for start,block in stream_array(zf,'s',(n,79),'<f4',np,check):
                            require(np.isfinite(block).all(),'Nonfinite current s')
                            for offset,row in enumerate(block):yield row.tobytes(),int(actions[start+offset])
                    hist=histograms(keys,records(),check)
                counts=Counter();matched_counts=[];margins=[]
                for local,global_index in enumerate(where):
                    selected,gap=selection[local];h=hist[keys[local]];kind=classification(h,selected);counts[kind]+=1
                    if sum(h):matched_counts.append(sum(h))
                    if gap is not None:margins.append(gap)
                    sink.write(json.dumps({'arm':arm,'bank_row':int(global_index),'source_transition_index':int(ix[local]),
                        'member_index':role['member_index'],'feature_bytes_sha256':hashlib.sha256(keys[local]).hexdigest(),
                        'masked_endnetwork_winner':selected,'legal_q_margin':gap,'actual_a_counts_at_exact_current_s':h,
                        'current_s_matches':sum(h),'winner_action_matches':h[selected],
                        'conditional_empirical_winner_share':h[selected]/sum(h) if sum(h) else None,
                        'classification':kind},allow_nan=False)+'\n')
                results.append({'arm':arm,'bank_rows':2500,'unique_feature_byte_keys':len(hist),'counts':dict(counts),
                    'matched_row_multiplicity':{'count':len(matched_counts),'sum':sum(matched_counts),'max':max(matched_counts,default=0)},
                    'legal_margin_rows':len(margins),'bank_origin_checks':dict(verified),
                    'terminal_bank_rows':done_counts['terminal'],'nonterminal_bank_rows':done_counts['nonterminal'],
                    'buffer_sha256':sha(path)})
                require(results[-1]['buffer_sha256']==binding['inputs'][str(path)],'Replay changed during scan')
                del actions,hist,keys,queries,selection;gc.collect()
        for path,want in binding['inputs'].items():check();require(sha(path)==want,'Input hash changed at completion')
        total=Counter()
        for result in results:total.update(result['counts'])
        require(sum(total.values())==10000,'Aggregate bank row count differs')
        report={'status':'complete','arms':results,'pooled_row_counts':dict(total),'bank_rows':10000,
            'terminal_bank_rows':sum(r['terminal_bank_rows'] for r in results),
            'nonterminal_bank_rows':sum(r['nonterminal_bank_rows'] for r in results),
            'elapsed_seconds':time.monotonic()-started,'numpy_version':np.__version__,'rows_sha256':sha(out/'rows.jsonl'),
            'bindings_sha256':sha(BASE/'bindings.json'),'script_sha256':sha(BASE/'support.py'),'approval_sha256':sha(BASE/'ROOT_APPROVAL.json'),
            'limits':['No exact current-s match means unknown, not zero coverage.','Byte-equal 79 features do not prove equal full state/belief/history.','mask belongs to ns; replay a belongs to current s. No a[i+1] linkage or next_actual_action exists.','Fixed endnetwork Q values are not training-time online/target Q values; no historical TD errors inferred.','Repeated bank states and correlated replay rows are not independent observations.','Empirical absent winner in finite retained replay does not prove action impossible or Q erroneous.','No model import/forward, games, training, action/network selection or policy change.']}
        write(out/'summary.json',report);print(json.dumps({'status':'complete','rows':10000,'elapsed_seconds':report['elapsed_seconds']}))
    except BaseException as exc:
        write(out/'incomplete.json',{'status':'incomplete','error':f'{type(exc).__name__}: {exc}','elapsed_seconds':time.monotonic()-started})
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old_handler)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','selfcheck','run']);args=parser.parse_args()
    {'prepare':prepare,'selfcheck':selfcheck,'run':run}[args.mode]()
