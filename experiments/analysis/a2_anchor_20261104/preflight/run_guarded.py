"""Operational subprocess guard; no model/agent imports or experiment choices."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('--record', type=Path, required=True)
p.add_argument('--deadline', required=True)
p.add_argument('--cwd', required=True)
p.add_argument('command', nargs=argparse.REMAINDER)
a = p.parse_args()
command = a.command[1:] if a.command and a.command[0] == '--' else a.command
assert command and not a.record.exists(), 'Command missing or duplicate launch record'
deadline = datetime.fromisoformat(a.deadline.replace('Z', '+00:00'))
assert deadline.tzinfo and datetime.now(timezone.utc) < deadline
a.record.parent.mkdir(parents=True, exist_ok=True)
record = {'status': 'starting', 'launcher_pid': os.getpid(), 'command': command,
          'cwd': a.cwd, 'deadline_utc': deadline.isoformat(),
          'started_utc': datetime.now(timezone.utc).isoformat(),
          'guard_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
def save():
    temp = a.record.with_suffix('.tmp')
    temp.write_text(json.dumps(record, indent=2) + '\n')
    temp.replace(a.record)
save()
env = dict(os.environ)
env.update({k:'1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
                          'VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']})
env['PYTHONUNBUFFERED'] = '1'
stop_requested = False
def request_stop(*_):
    global stop_requested
    stop_requested = True
signal.signal(signal.SIGTERM, request_stop)
signal.signal(signal.SIGINT, request_stop)
child = None
try:
    with a.record.with_suffix('.log').open('x') as log:
        child = subprocess.Popen(command, cwd=a.cwd, env=env, stdin=subprocess.DEVNULL,
                                 stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        record.update(status='running', child_pid=child.pid, child_process_group=child.pid)
        save()
        while child.poll() is None:
            if stop_requested or a.record.with_suffix('.stop').exists() or datetime.now(timezone.utc) >= deadline:
                record['stop_reason'] = 'requested' if stop_requested or a.record.with_suffix('.stop').exists() else 'deadline'
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                break
            time.sleep(1)
        record['returncode'] = child.returncode
        record['status'] = 'completed' if child.returncode == 0 and 'stop_reason' not in record else 'incomplete'
except BaseException as error:
    record.update(status='failed', error=repr(error))
    if child is not None and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
    raise
finally:
    record['finished_utc'] = datetime.now(timezone.utc).isoformat()
    save()
    print(json.dumps(record), flush=True)
raise SystemExit(0 if record['status'] == 'completed' else 2)
