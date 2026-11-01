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
import time
import csv
import math

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.early_curriculum_study import source_identity, hashes, THREAD_ENV


def stamp():
    return datetime.now(timezone.utc).isoformat()


def validate_output(target, args):
    first = 500000 + int(args[args.index('--first')+1])
    n = int(args[args.index('--n')+1])
    opponents = args[args.index('--opponents')+1].split(',')
    expected = {(s,p,o) for s in range(first,first+n) for p in ('player_0','player_1') for o in opponents}
    from scripts.experiment import GAME_FIELDS
    seen = set()
    with target.open(newline='') as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == list(GAME_FIELDS), 'Unexpected CSV schema'
        for r in reader:
            seed = float(r['seed']); assert seed.is_integer()
            key = (int(seed),r['side'],r['opponent'])
            assert key in expected and key not in seen, ('Unexpected/duplicate key',key)
            seen.add(key)
            vals = {k:float(v) for k,v in r.items() if k not in ('side','opponent')}
            assert all(math.isfinite(v) for v in vals.values())
            assert vals['secs'] >= 0
            for key in ('sap_attempts','sap_hits','relics_found','relics_seen',
                        'known_point_tiles','belief_contradictions','unit_steps'):
                assert vals[key].is_integer() and vals[key] >= 0
            for key in ('wait_frac','invalid_frac','greedy_masked_frac','stack_frac'):
                assert 0 <= vals[key] <= 1
            assert vals['steps']==303 and vals['point_counting_version']==2
            a,b=vals['our_wins'],vals['opp_wins']
            assert a.is_integer() and b.is_integer() and a>=0 and b>=0 and a+b<=3
            result=1 if a>b else 0 if a<b else .5
            assert vals['result']==result and vals['game_win']==int(result==1)
            a,b=vals['our_points'],vals['opp_points']
            assert a.is_integer() and b.is_integer() and min(a,b)>=0
            assert vals['point_win']==(1 if a>b else 0 if a<b else .5)
    assert seen==expected, ('Incomplete CSV',len(seen),len(expected))


def validate_inputs(args, frozen):
    def resolved(value):
        path = Path(value)
        return (ROOT/path).resolve() if not path.is_absolute() else path.resolve()
    required = [resolved(args[args.index('--weights')+1])]
    for opponent in args[args.index('--opponents')+1].split(','):
        if opponent.startswith(('self:', 'ppo:')):
            required.append(resolved(opponent.split(':', 1)[1]))
        elif opponent == 'dqn':
            required.append(ROOT/'agents/DQN/agent.pth')
    for i, arg in enumerate(args[:-1]):
        if arg == '--set' and args[i+1].startswith('cnn='):
            required.append(resolved(args[i+1].split('=', 1)[1]))
    frozen = {resolved(p) for p in frozen}
    for path in required:
        if not path.is_file():
            raise ValueError(f'Missing actual model input: {path}')
        if path not in frozen:
            raise ValueError(f'Actual model input is not frozen: {path}')


def main():
    def stop(sig, frame):
        raise SystemExit(f'Received signal {sig}')
    signal.signal(signal.SIGTERM, stop)
    phase_path = Path(sys.argv[1]).resolve()
    phase = json.loads(phase_path.read_text())
    if not phase['name'].replace('_', '').isalnum():
        raise ValueError('Invalid phase name')
    protected = [ROOT / 'agents/sherlock/weights' / f'agent_p{i}.pth' for i in (0, 1)]
    protected += [Path(p).resolve() for p in phase['frozen_weights']]
    for p in protected:
        if not p.is_file():
            raise ValueError(f'Missing protected weight: {p}')
    for job in phase['jobs']:
        validate_inputs(job['args'], protected)
    plans = [ROOT / 'docs/superpowers/plans/2026-11-01-night-improvement.md']
    def identity():
        return {'source': source_identity(ROOT, sys.executable, plans), 'weights': hashes(protected)}
    freeze_path = OUT / f"{phase['name']}_freeze.json"
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
        deadline = datetime.fromisoformat(phase['deadline_utc']).timestamp()
        for job in phase['jobs']:
            assert time.time() < deadline, 'Deadline reached before job'
            power = subprocess.check_output(['pmset', '-g', 'batt'], text=True)
            assert 'AC Power' in power, 'Long evaluations require AC power'
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
                    while child.poll() is None:
                        remaining = deadline-time.time()
                        if remaining <= 0:
                            raise TimeoutError('Evaluation deadline reached')
                        assert 'AC Power' in subprocess.check_output(['pmset','-g','batt'],text=True), 'AC power disconnected'
                        assert identity() == before, 'Frozen evaluation inputs changed'
                        try:
                            child.wait(timeout=min(15, remaining))
                        except subprocess.TimeoutExpired:
                            pass
                    code = child.returncode
                except BaseException:
                    if child.poll() is None:
                        os.killpg(child.pid, signal.SIGTERM)
                        try:
                            child.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            os.killpg(child.pid, signal.SIGKILL)
                            child.wait()
                    raise
            record.update(finished_at=stamp(), exit_code=code)
            journal_path.write_text(json.dumps(journal, indent=2) + '\n')
            assert code == 0, f"Evaluation failed: {log}"
            assert identity() == before, 'Frozen inputs changed during evaluation'
            validate_output(target, args)
            record['output_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
            journal_path.write_text(json.dumps(journal, indent=2) + '\n')
            print(f"{stamp()} COMPLETE {job['name']}: {target.name}", flush=True)
        journal.update(finished_at=stamp(), status='complete')
        journal_path.write_text(json.dumps(journal, indent=2) + '\n')
    except BaseException as exc:
        journal.update(finished_at=stamp(), status='incomplete', error=f'{type(exc).__name__}: {exc}')
        journal_path.write_text(json.dumps(journal, indent=2) + '\n')
        raise
    finally:
        if awake is not None:
            awake.terminate()
            awake.wait()


if __name__ == '__main__':
    main()
