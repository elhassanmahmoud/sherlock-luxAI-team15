"""Run explicit, predeclared evaluation commands sequentially with frozen inputs.

Usage: python run_jobs.py NEW_PHASE_JOBS.json
JSON: {"name": "selection", "jobs": [{"name": "baseline", "args": [...]}]}.
args are arguments to scripts.par_eval. This runner never chooses/promotes a model.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.early_curriculum_study import source_identity, hashes, THREAD_ENV


def stamp():
    return datetime.now(timezone.utc).isoformat()


def main():
    phase_path = Path(sys.argv[1]).resolve()
    phase = json.loads(phase_path.read_text())
    if not phase['name'].replace('_', '').isalnum():
        raise ValueError('Invalid phase name')
    protected = [ROOT / 'agents/sherlock/weights' / f'agent_p{i}.pth' for i in (0, 1)]
    protected += [ROOT / 'experiments/releases/20261022_v10_baseline' / f'agent_p{i}.pth' for i in (0, 1)]
    plans = [ROOT / 'docs/superpowers/plans/2026-10-22-v10-mechanics.md']
    def identity():
        return {'source': source_identity(ROOT, sys.executable, plans), 'weights': hashes(protected)}
    freeze_path = OUT / 'source_freeze.json'
    before = identity()
    if freeze_path.exists():
        assert before == json.loads(freeze_path.read_text()), 'Frozen inputs changed'
    else:
        with freeze_path.open('x') as f:
            json.dump(before, f, indent=2)
    journal_path = OUT / f"{phase['name']}_state.json"
    journal = {'started_at': stamp(), 'phase': phase,
               'phase_sha256': hashlib.sha256(phase_path.read_bytes()).hexdigest(), 'jobs': []}
    with journal_path.open('x') as f:
        json.dump(journal, f, indent=2)
    awake = subprocess.Popen(['caffeinate', '-i', '-w', str(os.getpid())]) if shutil.which('caffeinate') else None
    try:
        for job in phase['jobs']:
            assert identity() == before, 'Frozen inputs changed'
            args = job['args']
            assert args[args.index('--workers') + 1] == '2'
            target = Path(args[args.index('--out') + 1]).resolve()
            assert target.parent == OUT and not target.exists(), 'Invalid/existing output'
            log = OUT / f"{phase['name']}_{job['name']}.log"
            command = [sys.executable, '-B', '-m', 'scripts.par_eval', *args]
            record = {'name': job['name'], 'command': command, 'started_at': stamp(), 'log': str(log)}
            journal['jobs'].append(record)
            journal_path.write_text(json.dumps(journal, indent=2) + '\n')
            print(f"{stamp()} START {job['name']}", flush=True)
            with log.open('x') as f:
                child = subprocess.Popen(command, cwd=ROOT, env={**os.environ, **THREAD_ENV},
                                         stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    code = child.wait()
                except BaseException:
                    os.killpg(child.pid, signal.SIGTERM)
                    child.wait()
                    raise
            record.update(finished_at=stamp(), exit_code=code)
            journal_path.write_text(json.dumps(journal, indent=2) + '\n')
            assert code == 0, f"Evaluation failed: {log}"
            assert identity() == before, 'Frozen inputs changed during evaluation'
            record['output_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
            journal_path.write_text(json.dumps(journal, indent=2) + '\n')
            print(f"{stamp()} COMPLETE {job['name']}: {target.name}", flush=True)
        journal.update(finished_at=stamp(), status='complete')
        journal_path.write_text(json.dumps(journal, indent=2) + '\n')
    finally:
        if awake is not None:
            awake.terminate()
            awake.wait()


if __name__ == '__main__':
    main()
