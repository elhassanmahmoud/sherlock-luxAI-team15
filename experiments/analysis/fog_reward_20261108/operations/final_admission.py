"""Root admission, execute only after all training processes have exited."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
BASE = ROOT / 'experiments/analysis/fog_reward_20261108'
HEAD = 'a3111c3d0aa0aa974298daabe300bba7be157da1'
ARMS = ['control41', 'neutral41', 'control42', 'neutral42']
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
state = read(BASE / 'training_v1/state.json')
assert state['status'] == 'done' and not state['active'] and not state['queue']
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == HEAD
for job in state['jobs'].values():
    assert job['returncode'] == 0
    assert subprocess.run(['ps', '-p', str(job['pid']), '-o', 'command='], capture_output=True).returncode != 0
from scripts.fog_reward_study import validate_final_receipt
prepared = Path(state['prepared'])
manifest = read(prepared / 'manifest.json')
files = dict(state['inputs'])
files[str(prepared / 'manifest.json')] = sha(prepared / 'manifest.json')
arms = {}
for arm in ARMS:
    directory = ROOT / 'experiments/runs' / ('20261108_fog_reward_' + arm)
    receipt_path = directory / 'final_receipt.json'
    receipt = validate_final_receipt(receipt_path, arm=arm)
    names = ['final_receipt.json', 'weights/agent.pth', 'rollouts.jsonl', 'validation_games.jsonl',
             'training_audit.json', 'train.csv', 'prefill_proof.json', 'prefill_bundle.json']
    armfiles = {str(directory / name): sha(directory / name) for name in names}
    files.update(armfiles)
    arms[arm] = dict(receipt_path=str(receipt_path), checkpoint_path=str(directory / 'weights/agent.pth'),
                     final_checkpoint_sha256=receipt['final_checkpoint_sha256'],
                     receipt_sha256=sha(receipt_path), files=armfiles,
                     counts={k:receipt[k] for k in ['actual_prefill_games','actual_train_games','actual_validation_games','learn_steps','env_steps']})
for seed in (41,42):
    p = BASE / f'training_v1/paired_prefill_{seed}.json'
    assert read(p)['status'] == 'matched'
    files[str(p)] = sha(p)
for path, digest in state['protected'].items(): assert sha(path) == digest
for path, digest in files.items(): assert sha(path) == digest
for suffix in ('json', 'md'):
    p = BASE / f'operations/final-independent-audit.{suffix}'
    if suffix == 'json': assert read(p)['status'] == 'PASS'
    files[str(p)] = sha(p)
out = BASE / 'operations/historical_training_acceptance.json'
payload = dict(schema_version=1, status='PASS', eligible_for_comparison=True,
               timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               training_head=HEAD, root=str(ROOT), source=manifest['pins']['source'],
               protected=state['protected'], prepared=str(prepared),
               prepared_manifest_sha256=sha(prepared / 'manifest.json'),
               arms=arms, files=files,
               total_prefill_games=160, total_train_games=1600,
               total_validation_games=128, total_executions=1888, total_updates=240000,
               limitations='Technical and training provenance admission only; no performance or promotion claim.')
with out.open('x') as f: json.dump(payload, f, indent=2); f.write('\n')
print(json.dumps(dict(status='PASS', acceptance=str(out), sha256=sha(out), total_executions=1888, updates=240000)))
