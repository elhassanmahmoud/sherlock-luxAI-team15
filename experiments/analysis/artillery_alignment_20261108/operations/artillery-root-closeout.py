"""Root's one-shot receipt revalidation and acceptance assembly. Never starts games."""
import argparse, hashlib, json, os, pathlib, shutil, subprocess, sys
ROOT=pathlib.Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
HEAD='02ce1b2ce9a5b0780da1ee6462a2368b2226d495'
BASE=ROOT/'experiments/analysis/artillery_alignment_20261108'
OPS=BASE/'operations'; PREP=BASE/'prepared_v1'; STATE=BASE/'training_v1/state.json'
ARMS=('control43','aligned43','control44','aligned44')
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text())
def write(p,d):
 with pathlib.Path(p).open('x') as f:json.dump(d,f,indent=2,allow_nan=False);f.write('\n')
def need(x,m):
 if not x:raise RuntimeError(m)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--after-supervisor-exit',action='store_true');args=parser.parse_args()
 need(args.after_supervisor_exit,'Explicit stopped-supervisor authorization required')
 state=read(STATE)
 need(state['status']=='done' and not state['active'] and not state['queue'],'Supervisor unfinished')
 need(set(state['jobs'])==set(state['receipts'])==set(ARMS),'Incomplete jobs')
 need('returncode' in state['wake'],'Wake cleanup not completed')
 proc=subprocess.check_output(['ps','-axo','pid=,command='],text=True)
 for line in proc.splitlines():
  bits=line.strip().split(None,1)
  if len(bits)!=2 or int(bits[0])==os.getpid():continue
  executable=pathlib.Path(bits[1].split()[0]).name.lower()
  if 'python' in executable or executable=='pytest':
   need(not any(x in bits[1] for x in ('-m scripts.artillery_alignment_study','-m scripts.artillery_alignment_supervisor','artillery-training-tensor-audit.py','pytest')),'Concurrent model/test process: '+bits[1])
 need(subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()==HEAD,'Training HEAD changed')
 audit_paths=[pathlib.Path('/tmp/artillery-training-audit.json'),pathlib.Path('/tmp/artillery-training-tensor-audit.json')]
 audit_bytes={str(p):sha(p) for p in audit_paths}
 audit,tensor=map(read,audit_paths)
 manifest=read(PREP/'manifest.json')
 def check_independent_bindings():
  need(all(sha(p)==h for p,h in audit_bytes.items()),'Independent reports changed')
  for report in (audit,tensor):
   need(report['prepared_manifest_sha256']==sha(PREP/'manifest.json') and report['source']==manifest['pins']['source'] and report['protected']==manifest['pins']['protected'],'Independent audit provenance differs')
   need(set(report['arms'])==set(ARMS) and bool(report['files']),'Independent audit missing complete artifact bindings')
   need(all(sha(p)==h for p,h in report['files'].items()),'Independent audit bound artifact changed')
   for arm in ARMS:
    receipt=ROOT/'experiments/runs'/f'20261108_artillery_alignment_{arm}'/'final_receipt.json'
    need(report['arms'][arm]['receipt_sha256']==sha(receipt),'Independent receipt differs')
 check_independent_bindings()
 need(audit['status']=='PASS_DATA_ONLY' and audit['source_head']==HEAD,'Independent data audit incomplete')
 need(tensor['status']=='PASS_TENSORS_AND_REPLAY' and tensor['training_head']==HEAD,'Independent tensor audit incomplete')
 sys.path.insert(0,str(ROOT))
 from scripts import artillery_alignment_study as study
 manifest=read(PREP/'manifest.json')
 need(study.source_identity(ROOT,sys.executable,study.PLANS)==manifest['pins']['source'],'Current source not frozen identity')
 need(study._protected_hashes()==manifest['pins']['protected'],'Protected files changed')
 validated={};receipts={}
 for arm in ARMS:
  p=ROOT/'experiments/runs'/f'20261108_artillery_alignment_{arm}'/'final_receipt.json'
  receipt=study.validate_final_receipt(p,arm=arm);receipts[arm]=(p,receipt)
  need(state['jobs'][arm]['returncode']==0 and 'finished_at' in state['jobs'][arm],'Nonzero/uncompleted job')
  need(state['receipts'][arm]=={str(p):sha(p)},'Supervisor receipt differs')
  validated[arm]=dict(status='PASS',receipt_sha256=sha(p),env_steps=receipt['env_steps'],learn_steps=receipt['learn_steps'])
 for seed in (43,44):
  proofs=[read(receipts[f'{role}{seed}'][0].parent/'prefill_proof.json') for role in ('control','aligned')]
  expected=study.compare_prefill_proofs(*proofs,seed)
  expected['proof_sha256']={a:{str(receipts[a][0].parent/'prefill_proof.json'):sha(receipts[a][0].parent/'prefill_proof.json')} for a in (f'control{seed}',f'aligned{seed}')}
  need(expected==state['paired_prefill'][str(seed)]==read(BASE/f'training_v1/paired_prefill_{seed}.json'),'Paired proof differs')
 need(study.source_identity(ROOT,sys.executable,study.PLANS)==manifest['pins']['source'],'Source changed during validation')
 need(study._protected_hashes()==manifest['pins']['protected'],'Protected files changed during validation')
 root_validation=OPS/'root-final-validation.json'
 write(root_validation,dict(status='PASS',training_head=HEAD,validator='scripts.artillery_alignment_study.validate_final_receipt',arms=validated))
 # Only JSON/Markdown evidence enters the frozen checkout. Audit Python stays outside until freeze ends.
 for stem in ('artillery-training-audit','artillery-training-tensor-audit'):
  for suffix in ('.json','.md'):
   target=OPS/(stem+suffix);need(not target.exists(),'Evidence destination already exists');shutil.copyfile('/tmp/'+stem+suffix,target)
 files={}
 def bind(p):
  p=pathlib.Path(p).resolve();files[str(p)]=sha(p);return str(p)
 def ref(p):
  p=bind(p);return dict(path=p,sha256=files[p])
 for p in (PREP/'manifest.json',PREP/'supervisor_launch.json'):bind(p)
 arms={}
 for arm,(p,r) in receipts.items():
  armfiles={str(p):sha(p)}
  for name in study.RECEIPT_FILES:
   path=p.parent/name;need(sha(path)==r['artifacts'][name],'Receipt hash changed');armfiles[str(path)]=sha(path)
  for path in armfiles:bind(path)
  for path in (PREP/arm/'manifest.json',PREP/arm/'weights/agent.pth'):bind(path)
  arms[arm]=dict(receipt_path=str(p),receipt_sha256=sha(p),checkpoint_path=str(p.parent/'weights/agent.pth'),final_checkpoint_sha256=r['artifacts']['weights/agent.pth'],counts={**{k:r[k] for k in ('actual_prefill_games','actual_train_games','actual_validation_games','learn_steps','env_steps')},'executions':472},files=armfiles)
 for stem in ('artillery-training-audit','artillery-training-tensor-audit'):
  for suffix in ('.json','.md'):bind(OPS/(stem+suffix))
 record=dict(schema_version=1,status='PASS',eligible_for_comparison=True,training_head=HEAD,root=str(ROOT),source=manifest['pins']['source'],protected=manifest['pins']['protected'],prepared=str(PREP),prepared_manifest_sha256=sha(PREP/'manifest.json'),files=files,arms=arms,totals=dict(actual_prefill_games=160,actual_train_games=1600,actual_validation_games=128,executions=1888,learn_steps=240000),supervisor=ref(STATE),paired_prefill={str(s):ref(BASE/f'training_v1/paired_prefill_{s}.json') for s in (43,44)},independent_audit=ref(OPS/'artillery-training-audit.json'),root_validation=ref(root_validation),tensor_audit=ref(OPS/'artillery-training-tensor-audit.json'))
 need(all(sha(p)==h for p,h in files.items()),'Evidence changed while binding')
 check_independent_bindings()
 output=OPS/'historical_training_acceptance.json';write(output,record)
 print(json.dumps(dict(status='PASS',acceptance=str(output),sha256=sha(output),arms=list(arms),files=len(files))))
if __name__=='__main__':main()
