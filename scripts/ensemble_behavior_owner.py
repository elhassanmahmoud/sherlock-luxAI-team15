"""Own one admitted phase: four technical games OR both fixed ON workers; never auto-release."""
import argparse
import json
import os
from pathlib import Path
import signal
import sys
import time

from scripts.early_curriculum_study import digest, require
from scripts.ensemble_diversity_supervisor import compute_lock, spawn_owned, shutdown_owned, group_alive, request_stop
from scripts.final_training_supervisor import safe_path, save_state
from scripts.fog_reward_supervisor import guard
from scripts.threat_warmstart_compare import write


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=('technical','training'),required=True)
    parser.add_argument('--admission',type=Path,required=True)
    parser.add_argument('--admission-sha',required=True)
    parser.add_argument('--usage-file',type=Path,required=True)
    args=parser.parse_args()
    from scripts import ensemble_behavior_study as study
    path=safe_path(args.admission); a=study.admission(path,args.admission_sha,args.stage)
    require(a['inputs'].get(str(Path(__file__).resolve())) == digest(__file__) and sys.executable == a['python'],
            'Owner source/interpreter unbound')
    out=safe_path(study.output_dir(a)); require(not out.exists(),'Phase already exists; no resume/retry')
    roles=('technical',) if args.stage=='technical' else study.ROLES
    state={k:a[k] for k in ('root','out','python','plans','source','protected','allow_battery','starts')}
    state.update(profile=study.PROFILE,stage=args.stage,status='running',owner_pid=os.getpid(),
        usage_file=str(safe_path(args.usage_file)),stop_file=str(safe_path(a['stop_file'])),
        inputs={**a['inputs'],str(path):args.admission_sha},admission_sha256=args.admission_sha,
        jobs={},active=[],receipts={},started_at=time.time(),promotion=False)
    owned={}; handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP)}

    def check():
        require(digest(path)==args.admission_sha,'Admission changed')
        if state.get('release_sha256'):
            require(digest(out/'release.json')==state['release_sha256'],'Root release changed')
        guard(state,owned,allow_battery=a['allow_battery'])

    try:
        for sig in handlers: signal.signal(sig,lambda *_:request_stop(state['stop_file']))
        with compute_lock(a['root']):
            check(); out.mkdir(parents=True,exist_ok=False); write(out/'state.json',state)
            try:
                for role in roles:
                    check(); command=study.worker_command(a,path,args.admission_sha,out/'state.json',role)
                    spawn_owned(state,role,command,owned)
                checked=0.
                while owned:
                    require(not Path(state['stop_file']).exists(),'External STOP')
                    if time.monotonic()-checked>=10:
                        check(); checked=time.monotonic(); save_state(state)
                    if args.stage=='training' and 'prefill_ready' not in state:
                        if all((out/r/'prefill.json').is_file() and (out/r/'waiting.json').is_file() for r in roles):
                            state['prefill_ready']={r:digest(out/r/'prefill.json') for r in roles}
                            state['awaiting_root_release']=True; save_state(state)
                    if state.get('awaiting_root_release') and (out/'release.json').is_file():
                        release=json.loads((out/'release.json').read_text())
                        study.validate_release(release,a,args.admission_sha,state['prefill_ready'])
                        require(digest(release['root_review'])==release['root_review_sha256'],'Root review changed')
                        state.update(awaiting_root_release=False,release_sha256=digest(out/'release.json'))
                        save_state(state)
                    for role,child in list(owned.items()):
                        code=child['process'].poll()
                        if code is None: continue
                        state['jobs'][role].update(returncode=code,finished_at=time.time())
                        require(code==0 and not group_alive(child['pgid']),'Worker failed or left descendants')
                        receipt_path=out/role/'receipt.json'; receipt=json.loads(receipt_path.read_text())
                        require(receipt.get('status')=='complete' and receipt.get('profile')==study.PROFILE
                            and receipt.get('stage')==args.stage and receipt.get('role')==role
                            and receipt.get('start')==(49 if role=='on49' else 48) and receipt.get('source')==a['source']
                            and receipt.get('admission_sha256')==args.admission_sha
                            and receipt.get('command')==state['jobs'][role]['argv'],'Wrong worker receipt binding')
                        if role=='technical': study.check_technical(receipt,study.historical(a))
                        else:
                            require('prefill_ready' in state and len(receipt['games'])==440
                                and (out/'release.json').is_file()
                                and receipt.get('release_sha256')==digest(out/'release.json'),'Unreleased/incomplete training')
                        state['receipts'][role]=dict(path=str(receipt_path),sha256=digest(receipt_path))
                        del owned[role]; state['active']=list(owned); save_state(state)
                    if owned: time.sleep(.25)
                if args.stage=='training':
                    state['final_checks']={}
                    for role in roles:
                        result=study.validate_final_receipt(out/role/'receipt.json',a,args.admission_sha,role)
                        require(result.get('status')=='PASS','Final validator rejected artifacts')
                        state['final_checks'][role]=result
                    state['awaiting_root_release']=False
                check(); state.update(status='complete',finished_at=time.time()); save_state(state)
            except BaseException as exc:
                request_stop(state['stop_file']); state.update(status='incomplete',error=f'{type(exc).__name__}: {exc}')
                raise
            finally:
                cleaned=False
                try: shutdown_owned(owned); cleaned=True
                except BaseException as exc:
                    state.update(status='incomplete',cleanup_error=f'{type(exc).__name__}: {exc}'); raise
                finally:
                    for role,child in owned.items():
                        state['jobs'][role].update(returncode=child['process'].poll(),finished_at=time.time())
                    state['active']=[] if cleaned else list(owned); save_state(state)
    finally:
        for sig,handler in handlers.items(): signal.signal(sig,handler)


if __name__=='__main__': main()
