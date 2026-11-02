"""Owned-process envelope around the separately reviewed admission CLI."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
import re

ROOT = Path('/Users/moayedshawesh/Desktop/KI/sherlock-november-followup')
D = Path('/tmp/sherlock-continue-20261102')
PY = '/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python'
TOOL = ROOT / 'experiments/analysis/gauss_admission_20261102/admission.py'
OUT = ROOT / 'experiments/analysis/gauss_admission_20261102/evidence'

def now():
    return datetime.now(timezone.utc).isoformat()

def main():
    stage = sys.argv[1]
    assert stage in ('C', 'S')
    receipt = D / f'gauss_{stage}_execution.json'
    if receipt.exists():
        raise FileExistsError(receipt)
    command = [PY, '-B', str(TOOL), 'run-stage', '--out', str(OUT), '--stage', stage]
    deadline = time.time() + (660 if stage == 'C' else 1860)
    assert deadline < datetime(2026, 11, 3, 4, 30, tzinfo=timezone.utc).timestamp()
    state = dict(status='starting', stage=stage, command=command, supervisor_pid=os.getpid(),
                 supervisor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 started_utc=now(), deadline_utc=datetime.fromtimestamp(deadline, timezone.utc).isoformat(),
                 manifest_sha256=hashlib.sha256((OUT/'manifest.json').read_bytes()).hexdigest())
    def save():
        receipt.write_text(json.dumps(state, indent=2)+'\n')
    save()
    child = None
    def stop(sig, frame):
        raise RuntimeError(f'Own supervisor received signal {sig}')
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        with (D/f'gauss_{stage}_parent.log').open('x') as log:
            child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True, env={**os.environ, 'OMP_NUM_THREADS':'1',
                                     'OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'})
            state.update(status='running', child_pid=child.pid, process_group=child.pid)
            save()
            while child.poll() is None:
                power = subprocess.check_output(['pmset','-g','batt'], text=True)
                match = re.search(r'(\d+)%', power)
                if 'AC Power' not in power and (not match or int(match[1]) <= 25):
                    raise RuntimeError('Battery stop threshold')
                if time.time() >= deadline:
                    raise TimeoutError('Admission envelope deadline exceeded')
                try:
                    child.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    pass
            state['exit_code'] = child.returncode
            assert child.returncode == 0, 'Admission rejected or failed; inspect parent/child logs'
        complete = json.loads((OUT/stage/'complete.json').read_text())
        assert complete['status'] == 'complete'
        state.update(status='complete', finished_utc=now(),
                     complete_sha256=hashlib.sha256((OUT/stage/'complete.json').read_bytes()).hexdigest())
        save()
        print(json.dumps({k:state[k] for k in ('stage','status','started_utc','finished_utc')}), flush=True)
    except BaseException as exc:
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
        state.update(status='incomplete/rejected', finished_utc=now(), error=f'{type(exc).__name__}: {exc}')
        save()
        raise

if __name__ == '__main__':
    main()
