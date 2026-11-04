"""Execute the fixed, admitted 11 jobs; never select or alter a candidate."""
import argparse,datetime,hashlib,json,os,signal,subprocess,time
from pathlib import Path

ap=argparse.ArgumentParser();ap.add_argument('--protocol',type=Path,required=True);args=ap.parse_args()
protocol=json.loads(args.protocol.read_text());root=Path(protocol['root']);out=Path(protocol['output_directory'])
state_path=out/'state.json';assert not state_path.exists()
deadline=datetime.datetime.fromisoformat(protocol['deadline_utc'].replace('Z','+00:00'))
assert datetime.datetime.now(datetime.timezone.utc)<deadline
stopping=False
def stop(*_):
    global stopping
    stopping=True
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check_pins():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==protocol['source_commit']
    for rel,sha in protocol['source_sha256'].items():assert digest(root/rel)==sha,rel
    for path,sha in protocol['inputs_sha256'].items():assert digest(path)==sha,path
def cleanup_owned_group(record_path, grace_seconds=2.):
    """Bounded cleanup using only the child group recorded by this owned guard."""
    result = {'guard_record': str(record_path), 'status': 'unknown', 'errors': []}
    try:
        record = json.loads(Path(record_path).read_text())
        pgid = record.get('child_process_group')
        if type(pgid) is not int or pgid <= 1 or pgid != record.get('child_pid'):
            raise ValueError('Missing or inconsistent owned child process group')
        result['child_process_group'] = pgid
    except Exception as exc:
        result['errors'].append(repr(exc))
        return result

    def exists():
        try:
            os.killpg(pgid, 0)
            return True
        except ProcessLookupError:
            return False
        except OSError as exc:
            result['errors'].append(repr(exc))
            return None

    for sig in (signal.SIGTERM, signal.SIGKILL):
        if exists() is False:
            result['status'] = 'gone'
            return result
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            result['status'] = 'gone'
            return result
        except OSError as exc:
            result['errors'].append(repr(exc))
        until = time.monotonic() + grace_seconds
        while time.monotonic() < until:
            if exists() is False:
                result['status'] = 'gone'
                return result
            time.sleep(min(.1, max(0., until - time.monotonic())))
    remaining = exists()
    result['status'] = 'surviving' if remaining is True else ('gone' if remaining is False else 'unknown')
    return result

check_pins()
jobs=[]
for role,path in protocol['roles'].items():
    jobs.append(dict(name='panel_'+role,role=role,kind='panel',weights=path,seeds=protocol['panel_seed_file'],opponents=','.join(protocol['opponents']),csv=str(out/'panel'/f'{role}.csv')))
for role,path in protocol['roles'].items():
    if role!='V14':jobs.append(dict(name='direct_'+role,role=role,kind='direct',weights=path,seeds=protocol['direct_seed_file'],opponents=protocol['direct_opponent'],csv=str(out/'direct'/f'{role}.csv')))
assert len(jobs)==11
for job in jobs:
    job['guard']=str(out/'guards'/f"{job['name']}.json")
    assert not Path(job['csv']).exists() and not Path(job['guard']).exists()
state={'status':'running','pid':os.getpid(),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protocol_sha256':digest(args.protocol),'controller_sha256':digest(__file__),'jobs':jobs,'completed':0,'running':[]}
out.mkdir(parents=True,exist_ok=True);(out/'guards').mkdir(exist_ok=True)
def save():
    t=state_path.with_suffix('.tmp');t.write_text(json.dumps(state,indent=2)+'\n');t.replace(state_path)
active={};pending=list(jobs);failure=None
env=dict(os.environ)
env.update({k:'1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']})
env['PYTHONUNBUFFERED']='1';env['PYTHONPATH']=str(root)
try:
    while pending or active:
        if stopping or datetime.datetime.now(datetime.timezone.utc)>=deadline:raise RuntimeError('Controller deadline/stop reached')
        while pending and len(active)<2:
            check_pins();job=pending.pop(0)
            cmd=[protocol['python'],'-B',protocol['guard_script'],'--record',job['guard'],'--deadline',protocol['deadline_utc'],'--cwd',str(root),'--',protocol['python'],'-B','-m','scripts.par_eval','--weights',job['weights'],'--set','frozen=false','--seed-list',job['seeds'],'--workers','1','--opponents',job['opponents'],'--out',job['csv']]
            log=open(out/'guards'/f"{job['name']}_controller.log",'x')
            process=subprocess.Popen(cmd,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            job.update(status='running',guard_pid=process.pid,command=cmd)
            active[job['name']]=(process,log,job)
        for name,(process,log,job) in list(active.items()):
            rc=process.poll()
            if rc is None:continue
            log.close();del active[name]
            record=json.loads(Path(job['guard']).read_text())
            job.update(status=record['status'],returncode=rc,finished_utc=record.get('finished_utc'))
            if rc!=0 or record['status']!='completed' or not Path(job['csv']).is_file():raise RuntimeError(f"Incomplete job {name}")
            job['csv_sha256']=digest(job['csv']);state['completed']+=1
        state['running']=list(active);save()
        if pending or active:time.sleep(1)
    check_pins()
    state['status']='complete';state['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();state['pins_after_equal']=True;save()
except BaseException as exc:
    failure=exc
    for process,_,_ in active.values():
        if process.poll() is None:process.terminate()
    cleanup = []
    unresolved = []
    for process,log,job in active.values():
        guard_stopped = True
        try:
            process.wait(timeout=25)
        except subprocess.TimeoutExpired:
            # Do not remove the guard until its separately owned group has
            # received bounded TERM/KILL cleanup, including survival evidence.
            pass
        group = cleanup_owned_group(job['guard'])
        if process.poll() is None:
            process.kill()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                guard_stopped = False
        group.update(job=job['name'], guard_pid=process.pid, guard_stopped=guard_stopped)
        cleanup.append(group)
        if group['status'] != 'gone' or not guard_stopped:
            unresolved.append(job['name'])
        log.close();job['status']='incomplete'
    state.update(status='incomplete',error=repr(exc),finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 running=unresolved,cleanup=cleanup,cleanup_confirmed=not unresolved);save()
if failure:raise failure
print(json.dumps({'status':state['status'],'completed':state['completed'],'state':str(state_path)}))
