from pathlib import Path
import datetime,json,hashlib,subprocess,os,re
root=Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15');tmp=Path('/tmp/sherlock-a2-anchor-20261104')
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=read(tmp/'training_admission.json')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==a['source_commit']
for p,h in a['source_sha256'].items():assert sha(root/p)==h,p
for p,h in a['protected_sha256'].items():assert sha(p)==h,p
pair=root/'experiments/runs/20261104_a2_anchor/seed25';paired=read(pair/'paired_prefill.json');assert paired['status']=='matched'
guards={};durations=[]
for arm in ['control','anchor']:
 g=read(tmp/f'seed25_{arm}_guard.json');assert g['status']=='completed' and g['returncode']==0
 try:os.killpg(g['child_process_group'],0)
 except ProcessLookupError:pass
 else:raise RuntimeError('Owned group still live')
 r=read(pair/f'audits/{arm}/anchor_receipt.json');assert r['status']=='done' and sha(r['final_checkpoint'])==r['checkpoint_sha256']
 assert sha(pair/f'audits/{arm}/anchor_receipt.json')==paired['receipts_sha256'][['control','anchor'].index(arm)]
 inner=read(pair/f'engine/{arm}/runs/control/final_receipt.json');assert [inner[k] for k in ['actual_prefill_games','actual_train_games','actual_validation_games']]==[40,160,32]
 assert inner['end']['learning']['learn_steps']==24000
 durations.append((datetime.datetime.fromisoformat(g['finished_utc'])-datetime.datetime.fromisoformat(g['started_utc'])).total_seconds());guards[arm]=sha(tmp/f'seed25_{arm}_guard.json')
battery=int(re.search(r'(\d+)%;',subprocess.check_output(['pmset','-g','batt'],text=True)).group(1));assert battery>=35
now=datetime.datetime.now(datetime.timezone.utc);est=max(durations)*1.25+90
assert now+datetime.timedelta(seconds=est)<datetime.datetime.fromisoformat('2026-11-04T21:00:00+00:00')
assert now+datetime.timedelta(seconds=est+3000+600)<datetime.datetime.fromisoformat('2026-11-04T22:00:00+00:00')
out=tmp/'seed26_admission.json';assert not out.exists()
record=dict(status='admitted',recorded_utc=now.isoformat(),seed25_guard_sha256=guards,seed25_max_wall_seconds=max(durations),seed26_padded_seconds=est,post_training_evaluation_and_audit_seconds=3600,projected_all_model_end_utc=(now+datetime.timedelta(seconds=est+3600)).isoformat(),account_used_percent=31,battery_percent=battery,source_commit=a['source_commit'],protected_unchanged=True,independent_all_four_learning_audit_pending=True)
out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
