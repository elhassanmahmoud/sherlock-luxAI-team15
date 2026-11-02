"""One fixed 24-game diagnostic; preserve inputs and stop only owned processes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time

ROOT = Path('/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics')
PRIVATE = Path('/tmp/sherlock-continue-20261102')
PYTHON = '/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python'
OUT = ROOT / 'experiments/analysis/continuation_20261102/targeting'
KEYS = ROOT / 'experiments/analysis/continuation_20261102/diagnostic_keys.json'
WEIGHTS = ROOT / 'experiments/releases/20261101_v14_baseline/agent_p0.pth'
EXPECTED = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
sys.path.insert(0, str(ROOT))
from scripts.early_curriculum_study import source_identity, hashes, THREAD_ENV

def stamp():
    return datetime.now(timezone.utc).isoformat()

def power_ok(text, threshold):
    if 'AC Power' in text:
        return True
    match = re.search(r'(\d+)%', text)
    return bool(match and int(match[1]) > threshold)

def main():
    receipt = PRIVATE / 'targeting_execution.json'
    if receipt.exists() or OUT.exists():
        raise FileExistsError('Do not duplicate or replace a diagnostic run')
    assert hashlib.sha256(WEIGHTS.read_bytes()).hexdigest() == EXPECTED
    assert len(json.loads(KEYS.read_text())['keys']) == 12
    assert power_ok(subprocess.check_output(['pmset', '-g', 'batt'], text=True), 35)
    plans = [ROOT / 'docs/superpowers/plans/2026-11-02-targeting-continuation.md',
             ROOT / 'docs/superpowers/plans/2026-11-02-targeting-trace-schema.md',
             ROOT / 'docs/superpowers/specs/2026-11-02-targeting-continuation-design.md',
             KEYS, ROOT / 'experiments/analysis/night_20261101/selection_baseline.csv',
             Path(__file__).resolve()]
    protected = [WEIGHTS, *(ROOT / f'agents/sherlock/weights/agent_p{i}.pth' for i in (0, 1)),
                 *(ROOT / f'experiments/releases/20261020_old3_sym3/agent_p{i}.pth' for i in (0, 1))]
    def identity():
        return dict(source=source_identity(ROOT, PYTHON, plans), weights=hashes(protected))
    frozen = identity()
    command = [PYTHON, '-B', '-m', 'scripts.targeting_probe', '--weights', str(WEIGHTS),
               '--keys', str(KEYS), '--out', str(OUT)]
    state = dict(status='starting', started_utc=stamp(), root=str(ROOT), command=command,
                 supervisor_pid=os.getpid(), identity=frozen, planned_games=24,
                 deadline_utc=datetime.fromtimestamp(time.time()+1200, timezone.utc).isoformat())
    def save():
        receipt.write_text(json.dumps(state, indent=2) + '\n')
    save()
    child = awake = None
    def stop(sig, frame):
        raise RuntimeError(f'Supervisor received signal {sig}')
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        with (PRIVATE / 'targeting_cli.log').open('x') as log:
            child = subprocess.Popen(command, cwd=ROOT, env={**os.environ, **THREAD_ENV},
                                     stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            awake = subprocess.Popen(['caffeinate', '-i', '-w', str(os.getpid())])
            state.update(status='running', child_pid=child.pid, child_process_group=child.pid,
                         awake_pid=awake.pid)
            save()
            deadline = datetime.fromisoformat(state['deadline_utc']).timestamp()
            while child.poll() is None:
                if time.time() >= deadline:
                    raise TimeoutError('Full diagnostic deadline exceeded; no partial acceptance')
                if not power_ok(subprocess.check_output(['pmset', '-g', 'batt'], text=True), 25):
                    raise RuntimeError('Battery reached stop threshold')
                if identity() != frozen:
                    raise RuntimeError('Frozen diagnostic inputs changed')
                try:
                    child.wait(timeout=min(15, max(.1, deadline-time.time())))
                except subprocess.TimeoutExpired:
                    pass
            state['exit_code'] = child.returncode
            assert child.returncode == 0, 'Diagnostic child failed; see log'
        assert identity() == frozen
        data = json.loads((OUT / 'manifest.json').read_text())
        assert data['status'] == 'complete' and data['completed_games'] == 24 and len(data['games']) == 12
        state.update(status='complete', finished_utc=stamp(), inputs_unchanged=True,
                     manifest_sha256=hashlib.sha256((OUT/'manifest.json').read_bytes()).hexdigest())
        save()
        print(json.dumps({k:state[k] for k in ('status','started_utc','finished_utc','planned_games')}), flush=True)
    except BaseException as exc:
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
        state.update(status='incomplete', finished_utc=stamp(), error=f'{type(exc).__name__}: {exc}')
        save()
        raise
    finally:
        if awake is not None:
            awake.terminate()
            awake.wait()

if __name__ == '__main__':
    main()
