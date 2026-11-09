"""Own exactly the admitted 160+160+120 confirmation games, with no restart."""
import argparse
import os
from pathlib import Path
import signal
import sys
import time

from scripts.match_weight_compare_owner import await_group_exit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--admission',type=Path,required=True)
    parser.add_argument('--admission-sha',required=True)
    parser.add_argument('--usage-file',type=Path,required=True)
    args = parser.parse_args()
    from scripts import match_weight_confirmation as s
    from scripts.ensemble_diversity_supervisor import compute_lock,spawn_owned,shutdown_owned,request_stop
    from scripts.final_training_supervisor import save_state,safe_path
    from scripts.fog_reward_supervisor import guard
    path = safe_path(args.admission); a = s.admission(path,args.admission_sha)
    s.require(sys.executable == a['python'], 'Wrong admitted interpreter')
    s.bound(a,Path(__file__).resolve())
    out = s.output_dir(a); s.require(not out.exists(), 'Output already exists; no resume')
    state = {k:a[k] for k in ('root','out','python','plans','source','protected','inputs','stop_file','allow_battery')}
    state.update(profile=s.PROFILE,stage='confirmation',status='running',owner_pid=os.getpid(),
        usage_file=str(safe_path(args.usage_file)),admission_sha256=args.admission_sha,
        jobs={},active=[],receipts={},started_at=time.time())
    owned = {}; handlers = {sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP)}
    def check():
        s.require(s.digest(path) == args.admission_sha, 'Admission changed')
        guard(state,owned,allow_battery=True)
    try:
        for sig in handlers: signal.signal(sig,lambda *_:request_stop(state['stop_file']))
        with compute_lock(a['root']):
            check(); out.mkdir(parents=True,exist_ok=False); s.write(out/'state.json',state)
            try:
                for wave in (s.JOBS[:2],s.JOBS[2:]):
                    for name in wave:
                        check(); spec = s.job_spec(a,name)
                        s.require(not safe_path(spec['csv']).exists(), 'CSV already exists')
                        spawn_owned(state,name,s.performance_command(a,name),owned)
                    last_check = 0.
                    while owned:
                        s.require(not Path(state['stop_file']).exists(), 'External STOP')
                        if time.monotonic()-last_check >= 10:
                            check(); last_check = time.monotonic(); save_state(state)
                        for name,child in list(owned.items()):
                            code = child['process'].poll()
                            if code is None: continue
                            state['jobs'][name].update(returncode=code,finished_at=time.time())
                            s.require(code == 0, 'Job failed')
                            await_group_exit(child,check)
                            s.validate_csv(a,name); spec = s.job_spec(a,name)
                            state['receipts'][name] = dict(path=spec['csv'],sha256=s.digest(spec['csv']),games=spec['games'])
                            del owned[name]; state['active'] = list(owned); save_state(state)
                        if owned: time.sleep(.25)
                check()
                summary = s.analyze(a)
                summary.update(source=a['source'],admission_sha256=args.admission_sha)
                s.write(out/'summary.json',summary)
                state.update(status='complete',finished_at=time.time()); save_state(state)
            except BaseException as error:
                request_stop(state['stop_file'])
                state.update(status='failed',error=f'{type(error).__name__}: {error}',
                    interrupted_game_count='Unknown for unfinished par_eval jobs: CSV is published only at job end. '
                        'Completed validated jobs remain listed; no rerun/resume is admitted.')
                raise
            finally:
                cleaned = False
                try: shutdown_owned(owned); cleaned = True
                except BaseException as error:
                    state.update(status='failed',cleanup_error=f'{type(error).__name__}: {error}'); raise
                finally:
                    for name,child in owned.items():
                        state['jobs'][name].update(returncode=child['process'].poll(),finished_at=time.time())
                    state['active'] = [] if cleaned else list(owned); save_state(state)
    finally:
        for sig,handler in handlers.items(): signal.signal(sig,handler)


if __name__ == '__main__': main()
