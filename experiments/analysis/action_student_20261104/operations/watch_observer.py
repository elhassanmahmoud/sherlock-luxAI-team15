import os,time,json,subprocess,datetime
from pathlib import Path
D=Path('/tmp/sherlock-action-student-20261104/watch'); R='/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15'
base='b19e5201893436a74b06fb9b222bcfcc7505ce9e'
def save(n,obj):
 p=D/(n+'.tmp');p.write_text(json.dumps(obj,indent=2));p.replace(D/n)
def log(obj):
 with (D/'events.jsonl').open('a') as f:f.write(json.dumps(dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),**obj))+'\n')
def run(cmd):
 p=subprocess.run(cmd,cwd=R,text=True,capture_output=True,timeout=25);return dict(code=p.returncode,stdout=p.stdout.strip(),stderr=p.stderr.strip())
save('owner.json',dict(pid=os.getpid(),owner='action_student_remote_watch',started=datetime.datetime.now(datetime.timezone.utc).isoformat(),stop_file=str(D/'STOP'),repository=R,recorded_sha=base,deadline='2026-11-04T17:00:00+00:00'))
nextr=0;nextb=0
try:
 while not (D/'STOP').exists() and datetime.datetime.now(datetime.timezone.utc)<datetime.datetime(2026,11,4,17,tzinfo=datetime.timezone.utc):
  now=time.monotonic()
  if now>=nextr:
   try:
    r=run(['git','-c','core.sshCommand=ssh -o BatchMode=yes -o ConnectTimeout=10','ls-remote','origin','refs/heads/main']);sha=r['stdout'].split()[0] if r['stdout'] else ''
    save('remote.json',dict(time=time.time(),**r,sha=sha))
    if r['code'] or sha!=base:log(dict(kind='remote_failure' if r['code'] else 'remote_change',previous=base,**r));base=sha or base
   except Exception as e:log(dict(kind='remote_failure',error=str(e)))
   nextr=now+600
  if now>=nextb:
   try:
    r=run(['pmset','-g','batt']);save('battery.json',dict(time=time.time(),**r))
    import re
    m=re.search(r'(\d+)%;',r['stdout']);pct=int(m[1]) if m else None
    if r['code'] or pct is None or pct<35:log(dict(kind='battery',percent=pct,**r))
   except Exception as e:log(dict(kind='battery_failure',error=str(e)))
   nextb=now+300
  time.sleep(10)
finally:save('receipt.json',dict(pid=os.getpid(),stopped=datetime.datetime.now(datetime.timezone.utc).isoformat(),reason='stop_file' if (D/'STOP').exists() else 'deadline'))
