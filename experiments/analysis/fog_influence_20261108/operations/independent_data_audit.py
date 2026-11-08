import json,hashlib,math,os,subprocess,datetime
from pathlib import Path
import numpy as np
R=Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15');O=R/'experiments/analysis/fog_influence_20261108/run_v1';H='f6f8b8ad2feecb680a3cd06a0eab2669d5d7b4d7'
ARMS=('control41','neutral41','control42','neutral42');NEW=('control41','control42','neutral41','neutral42')
def need(v,m):
 if not v:raise ValueError(m)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 d=hashlib.sha256()
 with Path(p).open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''):d.update(c)
 return d.hexdigest()
def verify(m):
 for p,s in m.items():need(sha(p)==s,'hash '+p)
def treehash(v):
 d=hashlib.sha256()
 def emit(b):d.update(len(b).to_bytes(8,'big'));d.update(b)
 def visit(x):
  if isinstance(x,np.ndarray):emit(b'ndarray');emit(x.dtype.str.encode());visit(list(x.shape));emit(x.tobytes(order='C'))
  elif isinstance(x,dict):
   emit(b'dict');emit(str(len(x)).encode())
   for k in sorted(x,key=lambda k:(type(k).__name__,repr(k))):visit(k);visit(x[k])
  elif isinstance(x,(list,tuple)):
   emit(type(x).__name__.encode());emit(str(len(x)).encode())
   for y in x:visit(y)
  elif x is None or isinstance(x,(str,int,float,bool)):emit(type(x).__name__.encode());emit(repr(x).encode())
  else:raise TypeError(type(x))
 visit(v);return d.hexdigest()
def sourcecheck(state):
 s=state['source'];need(subprocess.check_output(['git','-C',str(R),'rev-parse','HEAD'],text=True).strip()==s['head']==H,'frozen HEAD');verify(s['files']);need(sha(s['python'])==s['executable_sha256'] and str(Path(s['python']).resolve())==s['executable'],'runtime')
 names=subprocess.check_output(['git','-C',str(R),'ls-files','-z','--cached','--others','--exclude-standard','--','*.py']).split(b'\0');paths={R/os.fsdecode(n) for n in names if n}
 for name in ('scripts','agents','lux'):paths.update((R/name).rglob('*.py'))
 paths.update(map(Path,state['plans']))
 for name in ('requirements.txt','pyproject.toml'):
  if (R/name).is_file():paths.add(R/name)
 venv=Path(s['python']).parent.parent
 if (venv/'pyvenv.cfg').is_file():paths.add(venv/'pyvenv.cfg')
 for engine in (venv/'lib').glob('python*/site-packages/luxai_s3'):paths.update(engine.rglob('*.py'))
 need(set(map(str,paths))==set(s['files']),'source inventory')
state=read(O/'state.json');summary=read(O/'summary.json');proof=read(O/'bank_manifest.json');summary_hash=sha(O/'summary.json')
need(state['status']==summary['status']=='complete' and state['model_processes']==1 and summary['source']==state['source'],'complete source-bound run')
sourcecheck(state);verify(state['inputs']);verify(state['protected']);need(summary['input_sha256']==state['inputs'],'summary input bindings')
audit_path=R/'experiments/analysis/fog_reward_20261108/operations/final-independent-audit.json';need(sha(audit_path)=='cf563a0ac4c8ee890ee33800cc00e189d3d9104e11becca99e51c91441b49198','original audit anchor');audit=read(audit_path)
admission_path=R/'experiments/candidates/fog_reward_20261108/admission.json';admission=read(admission_path)
for role,e in admission['roles'].items():need(sha(R/e['path'])==e['sha256'],'admitted model bytes '+role)
with np.load(O/'bank.npz',allow_pickle=False) as f:bank={k:f[k] for k in f.files}
need(set(bank)=={'ns','mask','row_indices','arm_indices'} and bank['ns'].shape==(10000,79) and bank['ns'].dtype==np.float32 and bank['mask'].shape==(10000,6) and bank['mask'].dtype==np.bool_,'bank shape/type')
need(summary['bank']==proof and sha(O/'bank.npz')==proof['bank_sha256'] and treehash(bank)==proof['bank_content_sha256'],'bank hashes');rng=np.random.Generator(np.random.PCG64(0));buffer_bindings={}
for i,arm in enumerate(ARMS):
 p=R/f'experiments/runs/20261108_fog_reward_{arm}/weights/agent.buffer.npz';bound=audit['artifact_files'][str(p)];need(proof['arms'][arm]['path']==str(p) and proof['arms'][arm]['sha256']==bound and state['inputs'][str(p)]==bound,'replay original binding');buffer_bindings[str(p)]=bound
 with np.load(p,allow_pickle=False) as f:
  ns,mask,done=f['ns'],f['mask'],f['done'];need(ns.dtype==np.float32 and ns.shape[1]==79 and mask.dtype==bool and mask.shape==(len(ns),6) and done.shape==(len(ns),),'replay shape/type');need(np.isfinite(ns).all() and np.isfinite(done).all() and np.isin(done,(0,1)).all(),'finite replay')
  eligible=np.flatnonzero((done==0)&mask.any(1));idx=rng.choice(eligible,min(2500,len(eligible)),replace=False);take=bank['arm_indices']==i
  need(len(idx)==2500 and len(np.unique(idx))==2500 and take.sum()==2500 and np.array_equal(bank['row_indices'][take],idx) and np.array_equal(bank['ns'][take],ns[idx]) and np.array_equal(bank['mask'][take],mask[idx]),'exact PCG64 sampled ns/mask/index '+arm)
  need(proof['arms'][arm]['eligible_rows']==len(eligible) and proof['arms'][arm]['source_rows']==len(ns),'buffer metadata')
 del ns,mask,done
unique=len({n.tobytes()+m.tobytes() for n,m in zip(bank['ns'],bank['mask'])});need(unique==9996==proof['unique_ns_mask_rows'] and proof['sampled_rows']==10000,'exact duplicates')
with np.load(O/'outputs.npz',allow_pickle=False) as f:out={k:f[k] for k in f.files}
need(sha(O/'outputs.npz')==summary['outputs_sha256']==state['outputs_sha256'],'outputs hash')
need(out['member_q'].shape==(40,10000,6) and out['member_q'].dtype==np.float32 and np.isfinite(out['member_q']).all(),'40 finite raw members')
need(np.array_equal(out['row_indices'],bank['row_indices']) and np.array_equal(out['arm_indices'],bank['arm_indices']),'output row identity')
expected_members=admission['roles']['V14']['members']+[audit['arms'][a]['final_q_tensor_sha256'] for a in NEW]
need(out['ordered_member_hashes'].tolist()==proof['ordered_member_hashes']==expected_members,'ordered original36+four member identity');need(out['member_labels'].tolist()==[f'original{i}' for i in range(36)]+list(NEW),'labels')
need(expected_members[18]==audit['arms']['control41']['initial_tensor_sha256'],'component18 parent')
for role,indices in [('CONTROL38',(36,37)),('NEUTRAL38',(38,39))]:need(admission['roles'][role]['members']==expected_members[:36]+[expected_members[j] for j in indices],'admitted38 order')
raw=out['member_q'];mask=bank['mask'];arm_ids=bank['arm_indices'];rows=np.arange(10000);mean_checks={}
for role,idx in [('V14',list(range(36))),('CONTROL38',list(range(38))),('NEUTRAL38',list(range(36))+[38,39])]:
 recorded=out[role+'_mean_q'];reconstructed=raw[idx].mean(0,dtype=np.float32);need(recorded.shape==(10000,6) and recorded.dtype==np.float32 and np.isfinite(recorded).all() and np.allclose(reconstructed,recorded,rtol=1e-6,atol=1e-6),'NumPy reconstruction '+role)
 mean_checks[role]=dict(numpy_vs_recorded_max_error=float(np.abs(reconstructed-recorded).max()))
 if role!='V14':
  independent=out[role+'_independent_mean_q'];error=float(np.abs(independent-recorded).max());need(independent.dtype==np.float32 and independent.shape==recorded.shape and np.isfinite(independent).all() and error==summary['reproduction'][role]['max_absolute_error']==0,'stored independent candidate mean '+role);mean_checks[role]['stored_independent_vs_recorded_max_error']=error
checks=0

def cmp(a,b,path='summary'):
 global checks
 checks+=1
 if isinstance(b,dict):
  need(set(a)==set(b),'keys '+path)
  for k,v in b.items():cmp(a[k],v,path+'.'+k)
 elif isinstance(b,list):
  need(len(a)==len(b),'length '+path)
  for i,v in enumerate(b):cmp(a[i],v,path+'.'+str(i))
 elif isinstance(b,float):need(math.isclose(a,b,abs_tol=1e-10,rel_tol=1e-10),'statistic '+path)
 else:need(a==b,'value '+path)
def dist(x):
 x=np.asarray(x,dtype=np.float64).ravel();need(np.isfinite(x).all(),'finite distribution')
 return dict(count=0) if not len(x) else dict(count=len(x),mean=float(x.mean()),std=float(x.std()),min=float(x.min()),max=float(x.max()),quantiles={str(q):float(np.quantile(x,q)) for q in (0,.05,.25,.5,.75,.95,1)})
def win(q,m=mask):
 a=np.where(m,q,-np.inf).argmax(1);b=np.where(m,q,np.float32(-1e9)).argmax(1);need(np.array_equal(a,b) and m[np.arange(len(m)),a].all(),'Agent-inf versus diagnostic-1e9/legal equivalence');return a
def change(a,b):return dict(rows=len(a),changed=int((a!=b).sum()),to_sap=int(((a!=5)&(b==5)).sum()),from_sap=int(((a==5)&(b!=5)).sum()))
def gap(q):
 multi=mask.sum(1)>=2;m=mask[multi].copy();v=q[multi];best=win(v,m);m[np.arange(len(m)),best]=False;runner=win(v,m);return multi,best,runner,v[np.arange(len(v)),best]-v[np.arange(len(v)),runner]
base=out['V14_mean_q'];bw=win(base);multi,best,runner,_=gap(base)
recomputed=dict(rows=10000,rows_with_two_legal=int(multi.sum()),candidates={},members=[],parent18={})
for i,q in enumerate(raw):recomputed['members'].append(dict(index=i,q=dist(q),legal_action_gap=dist(gap(q)[3]),proposals_vs_v14=change(bw,win(q))))
for role,start in [('CONTROL38',36),('NEUTRAL38',38)]:
 full=out[role+'_mean_q'];cw=win(full);pair=raw[start:start+2].mean(0,dtype=np.float32);d=pair-base;delta=np.float32(2/38)*d;changed=bw!=cw;rr=rows[changed]
 recomputed['candidates'][role]=dict(proposal_changes=change(bw,cw),per_bank_arm={a:change(bw[arm_ids==i],cw[arm_ids==i]) for i,a in enumerate(ARMS)},pair_minus_base_all_q=dist(d),full_mean_delta_all_q=dist(delta),pair_minus_base_at_v14_winner=dist(d[rows,bw]),pair_minus_base_at_candidate_winner=dist(d[rows,cw]),full_mean_delta_at_v14_winner=dist(delta[rows,bw]),full_mean_delta_at_candidate_winner=dist(delta[rows,cw]),v14_fixed_margin_change=dist(delta[multi][np.arange(len(best)),best]-delta[multi][np.arange(len(best)),runner]),changed_candidate_vs_v14_margin_contribution=dist(delta[rr,cw[changed]]-delta[rr,bw[changed]]),changed_candidate_vs_v14_original_margin=dist(base[rr,cw[changed]]-base[rr,bw[changed]]),changed_candidate_vs_v14_full_margin=dist(full[rr,cw[changed]]-full[rr,bw[changed]]),float32_decomposition_max_error=float(np.abs((full-base)-delta).max()))
parent=raw[18];pw=win(parent)
for i,a in enumerate(NEW):
 q=raw[36+i];qw=win(q);recomputed['parent18'][a]=dict(proposal_changes=change(pw,qw),q_minus_parent=dist(q-parent),per_bank_arm={a:change(pw[arm_ids==j],qw[arm_ids==j]) for j,a in enumerate(ARMS)})
cmp(summary['descriptive'],recomputed)
# Explicitly post hoc, nonselectable arithmetic reference, no new model or forward.
init38=np.concatenate((raw[:36],raw[18:19],raw[18:19])).mean(0,dtype=np.float32);iw=win(init38)
posthoc=dict(label='POST HOC interpretation check only; nonselectable arithmetic reference',definition='INIT38=mean(original36 stored Q arrays + two copies of stored original18 Q); NumPy float32 reduction',INIT38_vs_V14=change(bw,iw),CONTROL38_vs_INIT38=change(iw,win(out['CONTROL38_mean_q'])),NEUTRAL38_vs_INIT38=change(iw,win(out['NEUTRAL38_mean_q'])),limits='Different baselines: 19–21% versus parent18 cannot be compared directly with 1.4% versus V14. Low ensemble disagreement does not prove averaging suppresses helpful learning. No action-quality or causal reward conclusion.')
sourcecheck(state);verify(state['inputs']);verify(state['protected']);need(sha(O/'summary.json')==summary_hash,'summary unchanged')
bindings={**state['inputs'],str(O/'state.json'):sha(O/'state.json'),str(O/'summary.json'):summary_hash}
report=dict(schema_version=1,status='PASS',time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=H,summary_sha256=summary_hash,rows=10000,unique_ns_mask_rows=unique,duplicates_beyond_unique=10000-unique,source=state['source'],protected=state['protected'],input_sha256=bindings,ordered_member_hashes=expected_members,buffer_hashes=buffer_bindings,mean_reconstruction=mean_checks,descriptive_comparisons=checks,proposal_changes={r:v['proposal_changes'] for r,v in recomputed['candidates'].items()},parent18_changes={a:v['proposal_changes'] for a,v in recomputed['parent18'].items()},posthoc=posthoc,script_sha256=sha(__file__),limits='Independent NumPy/stdlib recomputation of stored output arithmetic and original replay sampling. No Torch/model import, independent neural forward, tests, games, fitting or weight file. Recorded model member identity is checked against admitted/historically accepted hash metadata and model-file byte bindings, not newly recomputed tensor hashes.')
Path('/tmp/sherlock-fog-influence-data-audit.json').write_text(json.dumps(report,indent=2)+'\n')
text='# Independent Fog influence data/math audit\n\n**PASS** — 10000 sampled rows, 9996 exact unique feature/mask pairs, four duplicate rows beyond unique. All four original replay hashes and sequential PCG64(0) indices reproduced exactly, with matching nonterminal ns/mask rows and2500 rows per arm.\n\nAll40 stored member arrays finite and correctly ordered; NumPy36/38 means agree with recorded means within declared1e-6 tolerance, and stored independently forwarded candidate means equal recorded candidate means exactly. Every member/ensemble legal argmax agrees for actualAgent −inf and diagnostic −1e9. All '+str(checks)+' summary fields/statistics independently reproduced from stored arrays.\n\n'
text+='Control changes143/10000 (SAPto3/from5); neutral139/10000 (to4/from4). New members versus parent18: '+', '.join(f"{a}={v['changed']}" for a,v in report['parent18_changes'].items())+'.\n\n'
text+='Post hoc, nonselectable arithmetic INIT38 check: '+json.dumps(posthoc)+'\n\n'+report['limits']+' Source/HEAD/runtime/input/protected hashes verified unchanged before and after. Original summary was not modified.\n'
Path('/tmp/sherlock-fog-influence-data-audit.md').write_text(text)
print(json.dumps({k:report[k] for k in ('status','rows','unique_ns_mask_rows','descriptive_comparisons','proposal_changes','parent18_changes','mean_reconstruction','posthoc')},indent=2))
