"""Stdlib-only isolated mocked cleanup checks; no controller launch or models."""
import ast, hashlib, json, os, signal, tempfile, time
from pathlib import Path
from types import SimpleNamespace
source=Path('/tmp/sherlock-a2-anchor-20261104/run_diagnostic.py')
tree=ast.parse(source.read_text())
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='cleanup_owned_group')
results=[]
with tempfile.TemporaryDirectory() as td:
    record=Path(td)/'guard.json'
    record.write_text(json.dumps({'child_process_group':12345,'child_pid':12345}))
    for name, initial, dies, denied in [('already_gone',False,None,False),('term_sufficient',True,signal.SIGTERM,False),('kill_required',True,signal.SIGKILL,False),('survivor',True,None,False),('permission_unknown',True,None,True)]:
        live=[initial]; sent=[]
        def killpg(pgid,sig):
            assert pgid==12345
            if denied: raise PermissionError('mock denied')
            if not live[0]: raise ProcessLookupError('mock gone')
            if sig:
                sent.append(sig)
                if sig==dies:live[0]=False
        scope=dict(json=json,Path=Path,os=SimpleNamespace(killpg=killpg),signal=signal,time=time)
        exec(compile(ast.Module(body=[function],type_ignores=[]),str(source),'exec'),scope)
        proof=scope['cleanup_owned_group'](record,grace_seconds=0)
        expected='unknown' if denied else ('surviving' if live[0] else 'gone')
        assert proof['status']==expected,(name,proof)
        if name=='kill_required':assert sent==[signal.SIGTERM,signal.SIGKILL]
        if name=='survivor':assert sent==[signal.SIGTERM,signal.SIGKILL]
        results.append(dict(case=name,status=proof['status'],signals=[int(x) for x in sent]))
    proof=scope['cleanup_owned_group'](Path(td)/'missing.json',grace_seconds=0)
    assert proof['status']=='unknown'
    results.append(dict(case='missing_record',status='unknown'))
    record.write_text(json.dumps({'child_process_group':12345,'child_pid':54321}))
    proof=scope['cleanup_owned_group'](record,grace_seconds=0)
    assert proof['status']=='unknown'
    results.append(dict(case='inconsistent_owned_group',status='unknown'))
output=dict(status='passed',checks=results,helper_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),scope='AST-isolated stdlib mocks only; no process launch/model/test-suite execution')
Path('/tmp/sherlock-a2-anchor-20261104/diagnostic_cleanup_check.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output))
