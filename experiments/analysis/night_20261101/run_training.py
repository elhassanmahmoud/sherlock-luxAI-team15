"""Admit exactly two fixed pilot arms and stop both on deadline/power/input failure."""
import csv,hashlib,json,os,signal,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; D=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.early_curriculum_study import source_identity,hashes,THREAD_ENV

def stamp():return datetime.now(timezone.utc).isoformat()

def validate_training_pair(paths):
    schedules=[]
    reports=[]
    for path in paths:
        with path.open(newline='') as f:
            rows=list(csv.DictReader(f))
        assert len(rows)==600, 'Incomplete training arm'
        schedule=[]
        for g,row in enumerate(rows):
            assert int(row['game'])==g
            assert int(row['seed'])==294200+g//2
            assert row['side']==('player_0' if g%2==0 else 'player_1')
            assert int(row['steps'])==303 and int(row['point_counting_version'])==2
            schedule.append((int(row['game']),int(row['seed']),row['side'],row['opponent']))
        schedules.append(schedule)
        reports.append(dict(path=str(path),games=len(rows),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    assert schedules[0]==schedules[1], 'Training opponent schedules differ'
    return reports

def main():
    if time.time() >= datetime(2026,11,2,4,tzinfo=timezone.utc).timestamp():
        raise TimeoutError('No new long training after 05:00 Berlin')
    init=ROOT/'experiments/runs/20261101_nov_info_init18'
    protected=[ROOT/'agents/sherlock/weights'/f'agent_p{i}.pth' for i in (0,1)]
    protected += [ROOT/'experiments/releases/20261101_v14_baseline'/f'agent_p{i}.pth' for i in (0,1)]
    protected += [init/'weights/agent.pth',init/'manifest.json']
    def identity():return dict(source=source_identity(ROOT,sys.executable,[ROOT/'docs/superpowers/plans/2026-11-01-night-improvement.md']),weights=hashes(protected))
    before=identity()
    journal=dict(started_at=stamp(),pid=os.getpid(),status='running',jobs=[])
    path=D/'training_state.json'
    with path.open('x') as f:json.dump(journal,f,indent=2)
    with (D/'training_freeze.json').open('x') as f:json.dump(before,f,indent=2)
    deadline=min(time.time()+7200,datetime(2026,11,2,4,30,tzinfo=timezone.utc).timestamp())
    children=[];handles=[]
    def stop(sig,frame):raise SystemExit(f'Received signal {sig}')
    signal.signal(signal.SIGTERM,stop)
    try:
        assert 'AC Power' in subprocess.check_output(['pmset','-g','batt'],text=True)
        for arm in ('control','discovery'):
            name=f'20261101_nov_info_{arm}_s9'
            assert not (ROOT/'experiments/runs'/name).exists()
            cmd=[sys.executable,'-B','-m','scripts.night_train_pilot','runarm','--init',str(init),'--arm',arm,'--name',name]
            log=D/f'training_{arm}.log';handle=log.open('x');handles.append(handle)
            child=subprocess.Popen(cmd,cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT,env={**os.environ,**THREAD_ENV},start_new_session=True)
            children.append(child)
            journal['jobs'].append(dict(arm=arm,name=name,pid=child.pid,command=cmd,log=str(log),started_at=stamp()))
        path.write_text(json.dumps(journal,indent=2)+'\n')
        while any(c.poll() is None for c in children):
            if any(c.poll() not in (None,0) for c in children):raise RuntimeError('A training arm failed')
            if time.time()>=deadline:raise TimeoutError('Two-hour/deadline limit reached')
            if 'AC Power' not in subprocess.check_output(['pmset','-g','batt'],text=True):raise RuntimeError('AC power disconnected')
            assert identity()==before,'Frozen training inputs changed'
            time.sleep(min(30,max(0,deadline-time.time())))
        assert all(c.returncode==0 for c in children)
        assert time.time()<=deadline,'Training finished after the admitted deadline'
        assert identity()==before,'Frozen training inputs changed'
        for item,child in zip(journal['jobs'],children):
            item['exit_code']=child.returncode
            manifest=ROOT/'experiments/runs'/item['name']/'manifest.json'
            data=json.loads(manifest.read_text());assert data['status']=='done' and data['train_games']==600
            item['manifest_sha256']=hashlib.sha256(manifest.read_bytes()).hexdigest()
            item['weights_sha256']=hashlib.sha256((manifest.parent/'weights/agent.pth').read_bytes()).hexdigest()
        journal['validated_training_csvs']=validate_training_pair([
            ROOT/'experiments/runs'/item['name']/'train.csv' for item in journal['jobs']])
        journal['status']='complete'
    except BaseException as exc:
        journal.update(status='incomplete',error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        for child in children:
            if child.poll() is None:
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid,signal.SIGKILL);child.wait()
        for item,child in zip(journal['jobs'],children):item['exit_code']=child.returncode
        for handle in handles:handle.close()
        journal['finished_at']=stamp();path.write_text(json.dumps(journal,indent=2)+'\n')
        print(json.dumps(journal),flush=True)

if __name__=='__main__':main()
