"""Structured conditional P release; stdlib file checks only, never model execution.

No legacy PASS text/waiver. Three files are journaled and recoverable, not switched
simultaneously. Only explicit Root-authorized --install/--recover permits writes.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import csv
import fcntl
import hashlib
import json
import keyword
import math
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import tempfile
import time
import uuid
import zipfile

OLD_SHA='98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
P_SHA='dbb15222848b9ce8530080e128fa9ca66309c9900e98f50de5cce1d73e5b7f5a'
OLD_ZIP_SHA='88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6'
PERFORMANCE_HEAD='03e54e267242ff642c126313fe5f512ed9d959ac'
PANEL=('solution92','sol92_sq',
    'self:experiments/releases/20261022_all18_v3/agent_p0.pth',
    'self:experiments/releases/20261022_v7_Bsnpd/agent_p0.pth',
    'self:experiments/releases/20261022_v10_baseline/agent_p0.pth',
    'self:experiments/releases/20261101_v13_neb/agent_p0.pth')
DIRECT='self:experiments/releases/20261101_v14_baseline/agent_p0.pth'
SIDES=('player_0','player_1')
GAME_FIELDS=('seed','side','opponent','result','game_win','point_win','our_wins','opp_wins',
    'our_points','opp_points','point_counting_version','wait_frac','invalid_frac','greedy_masked_frac',
    'sap_attempts','sap_hits','stack_frac','relics_found','relics_seen','known_point_tiles',
    'belief_contradictions','unit_steps','steps','secs')
BACKUP_NAMES=dict(p0='agent_p0.pth',p1='agent_p1.pth',zip='Gruppe15.zip')
SIGNALS={signal.SIGHUP,signal.SIGINT,signal.SIGTERM}
EPS=1e-9


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):value.update(chunk)
    return value.hexdigest()


def path_alias(value):
    path=Path(value)
    require(path.is_absolute(),'Absolute path required')
    for alias in (Path('/tmp'),Path('/var')):
        if alias.is_symlink() and path.is_relative_to(alias):path=alias.resolve()/path.relative_to(alias)
    return path


def real_path(value, *, exists=True):
    path=path_alias(value)
    require(not any(p.is_symlink() for p in (path,*path.parents)),'Symlink path refused')
    require(path == path.resolve(strict=exists),'Noncanonical path refused')
    return path


def regular(path, *, single_link=False):
    path=real_path(path)
    info=path.stat()
    require(stat.S_ISREG(info.st_mode) and (not single_link or info.st_nlink==1),'Nonregular/hardlinked target')
    return path


def read(path):
    def pairs(values):
        result={}
        for key,value in values:
            require(key not in result,'Duplicate JSON key');result[key]=value
        return result
    def nonfinite(value):raise ValueError('Nonfinite JSON: '+value)
    return json.loads(regular(path).read_text(),object_pairs_hook=pairs,parse_constant=nonfinite)


def reference(value, evidence, substitutions=None):
    require(isinstance(value,dict) and set(value)=={'path','sha256'},'Invalid file reference')
    path=path_alias(value['path']);digest=value['sha256']
    if str(path) in (substitutions or {}):
        # Historical evidence may name a currently missing/new/foreign target.
        # Only the three verified old-backup substitutions bypass live lookup.
        require(real_path(path.parent)==path.parent and path.name not in ('.','..'),'Noncanonical historical target')
    else:path=real_path(path)
    require(isinstance(digest,str) and re.fullmatch('[0-9a-f]{64}',digest),'Invalid declared SHA256')
    actual=Path((substitutions or {}).get(str(path),path))
    require(sha(regular(actual))==digest,'Changed declared file: '+str(path))
    require(str(path) not in evidence or evidence[str(path)]==digest,'Conflicting hash declarations')
    evidence[str(path)]=digest
    return path


def verify_hashes(values,evidence,substitutions=None):
    require(isinstance(values,dict) and values,'Empty evidence hash manifest')
    for path,digest in values.items():reference(dict(path=path,sha256=digest),evidence,substitutions)


def targets(root):
    root=Path(root)
    return dict(p0=root/'agents/sherlock/weights/agent_p0.pth',
                p1=root/'agents/sherlock/weights/agent_p1.pth',zip=root/'Gruppe15.zip')


def numeric_gates(phase,panel,solution,default,direct):
    needed=[panel['delta'],solution['delta'],default['winrate'],direct.get('winrate',.5)]
    if phase=='confirmation':needed.extend([panel['low'],solution['low'],default['delta'],direct['low']])
    require(all(type(v) in (int,float) and math.isfinite(v) for v in needed),'Nonfinite/nonnumeric gate metric')
    if phase=='selection':
        return dict(panel_delta=panel['delta']>=.005-EPS,solution_delta=solution['delta']>=-EPS,
                    default=default['winrate']>=.99-EPS,direct=direct['winrate']>=.5-EPS)
    require(phase=='confirmation','Unknown phase')
    return dict(panel_delta=panel['delta']>=.01-EPS,panel_lower=panel['low']>EPS,
        solution_delta=solution['delta']>=-EPS,solution_lower=solution['low']>=-.01-EPS,
        default=default['winrate']>=.99-EPS,default_delta=default['delta']>=-.01-EPS,direct_lower=direct['low']>.5+EPS)


def passed_metrics(result,phase):
    checks=numeric_gates(phase,result['panel'],result['opponents']['solution92'],result['opponents']['default'],result['direct'])
    require(result['passed'] is True and result['gates']==checks
            and all(type(v) is bool and v for v in result['gates'].values()),'Missing/failed unchanged numeric gates')


def verify_csv(path,job):
    expected={(seed,side,opp) for seed in range(job['first_seed'],job['first_seed']+job['n_maps'])
              for side in SIDES for opp in job['opponents']}
    seen=set()
    with Path(path).open(newline='') as stream:
        reader=csv.DictReader(stream)
        require(reader.fieldnames==list(GAME_FIELDS),'Unexpected actual CSV schema/order')
        for row in reader:
            seed=float(row['seed'])
            require(math.isfinite(seed) and seed.is_integer(),'Invalid CSV seed')
            key=(int(seed),row['side'],row['opponent'])
            require(key in expected and key not in seen,'Wrong/duplicate CSV game key');seen.add(key)
            require(float(row['steps'])==303 and float(row['point_counting_version'])==2
                    and float(row['result']) in (0.,.5,1.),'Wrong CSV steps/point version/result')
    require(seen==expected and len(seen)==job['games'],'Incomplete CSV keys/count')


def job_command(job,python):
    return [python,'-B','-m','scripts.par_eval','--weights',job['weights'],'--first',str(job['first_seed']-500000),
        '--n',str(job['n_maps']),'--opponents',','.join(job['opponents']),'--workers',str(job['workers']),
        '--out',job['out'],*(item for flag in job['overrides'] for item in ('--set',flag))]


def fixed_job(job,done, *, name,role,seed,n,opponents,games,master):
    flag='false' if role=='baseline' else 'true'
    require(job['name']==done['name']==name and job['role']==role and job['first_seed']==seed
        and job['n_maps']==n and tuple(job['opponents'])==opponents and job['games']==games
        and done['status']=='complete' and done['exit_code']==0 and done['actual_games']==games
        and job['out']==done['out'] and job['weights']==master['weights'][role]
        and job['workers']==2 and job['engine']=='par_eval'
        and job['overrides']==['point_pair_swap='+flag,'art_move_guard='+flag]
        and done['command']==job_command(job,master['python']),'Incomplete/wrong fixed process job or command')


def phase_evidence(summary_path,audit_path,phase,evidence,substitutions):
    summary=read(summary_path);audit=read(audit_path)
    count,n,first=(3000,100,841000) if phase=='selection' else (9000,300,842000)
    require(summary['status']=='complete' and summary['phase']==phase and summary['nominee']=='P'
        and summary['completed_games']==count and set(summary['candidates'])=={'P'}
        and summary['bootstrap_samples']==5000 and summary['bootstrap_rng_seed']==0
        and summary['promotion_qualified'] is (phase=='confirmation'),'Incomplete/unqualified Root phase')
    passed_metrics(summary['candidates']['P'],phase)
    require(audit['verdict']=='ACCEPTED' and audit['phase']==phase and audit['error'] is None and audit['failed']==[]
        and type(audit['checks_total']) is int and audit['checks_total']==len(audit['checks'])>0
        and all(c['passed'] is True for c in audit['checks']),'Independent performance audit rejected/incomplete')
    verify_hashes(audit['evidence_sha256'],evidence,substitutions)
    independent=audit['results'][phase]
    require(independent['status']=='complete' and independent['phase']==phase and independent['nominee']=='P'
        and independent['completed_games']==count and independent['promotion_qualified'] is (phase=='confirmation'),
        'Independent phase not qualified')
    passed_metrics(independent,phase)
    for area,left,right in [('panel',summary['candidates']['P']['panel'],independent['panel']),
                           ('direct',summary['candidates']['P']['direct'],independent['direct']),
                           *[(o,summary['candidates']['P']['opponents'][o],independent['opponents'][o]) for o in ('solution92','default')]]:
        for key in ('delta','low','winrate'):
            if key in left or key in right:
                require(key in left and key in right and type(left[key]) in (int,float)
                        and type(right[key]) in (int,float) and math.isfinite(left[key]) and math.isfinite(right[key])
                        and abs(left[key]-right[key])<=1e-12,'Root/independent numeric disagreement '+area+'/'+key)
    plan_path=reference(dict(path=summary['plan_path'],sha256=summary['plan_sha256']),evidence,substitutions)
    require(plan_path.name=='plan.json' and plan_path.parent.name==phase,'Noncanonical phase plan')
    state_path=reference(dict(path=str(plan_path.parent/'state.json'),sha256=summary['state_sha256']),evidence,substitutions)
    plan,state=read(plan_path),read(state_path)
    master_path=reference(dict(path=plan['study_freeze_path'],sha256=plan['study_freeze_sha256']),evidence,substitutions)
    master=read(master_path)
    require(plan['phase']==state['phase']==phase and state['status']=='complete' and state['completed_games']==count
        and plan['candidate']==(None if phase=='selection' else 'P')
        and state['plan_sha256']==summary['plan_sha256']==independent['plan_sha256']
        and summary['state_sha256']==independent['state_sha256']
        and state['study_freeze_sha256']==summary['study_freeze_sha256']==independent['study_freeze_sha256']==sha(master_path),
        'Changed/mismatched phase provenance')
    require(master['expected_head']==PERFORMANCE_HEAD and master['identity']['source']['head']==PERFORMANCE_HEAD
        and set(master['weights'])=={'baseline','P'} and state['source_before']==state['source_after']==master['identity'],
        'Original P-only source freeze changed')
    reference(dict(path=master['weights']['baseline'],sha256=OLD_SHA),evidence,substitutions)
    reference(dict(path=master['weights']['P'],sha256=P_SHA),evidence,substitutions)
    verify_hashes(master['identity']['source']['files'],evidence,substitutions)
    source=master['identity']['source']
    require(source['python']==master['python'] and str(Path(source['python']).resolve(strict=True))==source['executable'],
            'Original interpreter declaration changed')
    reference(dict(path=source['executable'],sha256=source['executable_sha256']),evidence,substitutions)
    verify_hashes(master['frozen_weights'],evidence,substitutions)
    require(master['identity']['weights']==master['frozen_weights'],'Master weight identity disagrees')
    require(len(plan['jobs'])==len(state['jobs'])==3,'Wrong fixed job count')
    expected=[('baseline_panel','baseline',first,(*PANEL,'default'),14*n),
              ('P_panel','P',first,(*PANEL,'default'),14*n),
              ('P_direct','P',first if phase=='selection' else 843000,(DIRECT,),2*n)]
    csv_hashes={}
    for job,done,(name,role,seed,opponents,games) in zip(plan['jobs'],state['jobs'],expected):
        fixed_job(job,done,name=name,role=role,seed=seed,n=n,opponents=opponents,games=games,master=master)
        path=reference(dict(path=job['out'],sha256=done['output_sha256']),evidence,substitutions)
        require(path.parent==plan_path.parent and path.name==name+'.csv','Noncanonical CSV path')
        verify_csv(path,job);csv_hashes[str(path)]=done['output_sha256']
    require(summary['csv_sha256']==independent['csv_sha256']==csv_hashes,'CSV declaration mismatch')
    required={str(summary_path):sha(summary_path),str(plan_path):sha(plan_path),str(state_path):sha(state_path),
              str(master_path):sha(master_path),**csv_hashes}
    require(all(audit['evidence_sha256'].get(p)==h for p,h in required.items()),'Audit omits summary/CSV/state/master binding')
    return dict(summary=summary,audit=audit,plan=plan,state=state,master=master,master_path=str(master_path),
                summary_path=str(summary_path),state_path=str(state_path),required=required)


def technical_evidence(path,bundle,root,evidence,substitutions):
    qc=read(path)
    require(qc['verdict']=='ACCEPTED_P_RELEASE_QC' and qc['failed']==[] and qc['warnings']==[], 'Technical QC absent/rejected')
    require(qc['candidate']==bundle['candidate'] and qc['zip']==bundle['new_zip'],'QC candidate/ZIP binding differs')
    require(qc['feature_dim']==79 and qc['n_actions']==6 and qc['components']==36
        and all(qc[k] is True for k in ('all_ordered_tensors_equal','all_dtypes_shapes_equal','target_q_equal','other_checkpoint_fields_equal'))
        and qc['raw_frozen'] is False and qc['packed_frozen'] is True and qc['config_diff']=={'frozen':[False,True]}
        and qc['P_flags']==dict(point_pair_swap=True,art_move_guard=True),'Missing actual36tensor/dtype/config/mode proof')
    verify_hashes(qc['evidence_sha256'],evidence,substitutions)
    python=qc['python310'];version=python['version']
    require(isinstance(version,list) and len(version)==3 and all(type(v) is int for v in version)
            and version[:2]==[3,10] and version[2]>=0,'Actual Python3.10 proof required')
    py=reference(dict(path=python['path'],sha256=python['sha256']),evidence,substitutions)
    require(qc['runner']['games']==8 and qc['runner']['steps_each']==303 and qc['runner']['exit_code']==0
        and qc['zip_check']['layouts']==2 and qc['zip_check']['exit_code']==0
        and qc['replay']['steps']==303 and qc['replay']['components']==36
        and qc['replay']['action_differences']==0 and qc['replay']['exit_code']==0,'Missing actual runner/ZIP/replay proof')
    required=[reference(qc[k]['report'],evidence,substitutions) for k in ('runner','zip_check','replay')]
    required.extend((Path(bundle['candidate']['path']),Path(bundle['new_zip']['path']),py))
    require(all(qc['evidence_sha256'].get(str(p))==sha(p) for p in required),'QC omits actual declared artifacts')
    expected_sources={str(p.relative_to(root)) for p in (root/'agents/sherlock').glob('*.py')
                      if p.name!='__init__.py' and p.stem.isidentifier() and not keyword.iskeyword(p.stem)}
    require(len(expected_sources)==15 and set(qc['runtime_sources'])==expected_sources,'Wrong full runtime source list')
    for name,digest in qc['runtime_sources'].items():reference(dict(path=str(root/name),sha256=digest),evidence,substitutions)
    with zipfile.ZipFile(bundle['new_zip']['path']) as z:
        expected={'Gruppe15/__init__.py','Gruppe15/agent.pth','Gruppe15/agents.yaml','Gruppe15/LIESMICH.txt',
                  *('Gruppe15/'+Path(p).name for p in expected_sources)}
        require(len(z.namelist())==len(expected) and set(z.namelist())==expected and z.testzip() is None,'Unexpected/duplicate/corrupt ZIP entries')
        require(z.read('Gruppe15/__init__.py')==b'','ZIP initializer must be empty')
        require(hashlib.sha256(z.read('Gruppe15/agent.pth')).hexdigest()==qc['embedded_weights_sha256'],'Embedded checkpoint differs from QC')
        require(all(hashlib.sha256(z.read('Gruppe15/'+Path(p).name)).hexdigest()==h for p,h in qc['runtime_sources'].items()),
                'ZIP runtime source mismatch')
    return qc


def validate_bundle(bundle_path, *, substitutions=None, check_old=True):
    bundle_path=regular(bundle_path);bundle=read(bundle_path);evidence={str(bundle_path):sha(bundle_path)}
    require(bundle['schema_version']==1 and bundle['kind']=='qualified_P_release_20261102','Wrong release bundle type')
    root=real_path(bundle['target_root']);require(root.is_dir(),'Missing target root')
    require(re.fullmatch('[0-9a-f]{40}',bundle['expected_target_head']) and git_head(root)==bundle['expected_target_head'],'Target HEAD changed')
    dest=targets(root)
    require(bundle['candidate']['sha256']==P_SHA and bundle['new_zip']['sha256']!=OLD_ZIP_SHA,'Wrong raw P/new ZIP identity')
    candidate=reference(bundle['candidate'],evidence,substitutions);newzip=reference(bundle['new_zip'],evidence,substitutions)
    require(candidate!=newzip and candidate not in dest.values() and newzip not in dest.values(),'Input aliases an install target')
    if check_old:
        identities=[]
        for label,path in dest.items():
            path=regular(path,single_link=True)
            require(sha(path)==(OLD_ZIP_SHA if label=='zip' else OLD_SHA),'Expected old active bytes changed')
            identities.append((path.stat().st_dev,path.stat().st_ino))
        require(len(set(identities))==3,'Aliased active targets')
    required_study={'selection_summary','selection_audit','confirmation_summary','confirmation_audit','closure'}
    require(set(bundle['study'])==required_study,'Incomplete study evidence inputs')
    refs={name:reference(value,evidence,substitutions) for name,value in bundle['study'].items()}
    phases={p:phase_evidence(refs[p+'_summary'],refs[p+'_audit'],p,evidence,substitutions) for p in ('selection','confirmation')}
    selection,confirmation=phases['selection'],phases['confirmation']
    require(selection['master_path']==confirmation['master_path'] and selection['master']==confirmation['master']
        and confirmation['plan']['selection_summary_path']==str(refs['selection_summary'])
        and confirmation['plan']['selection_summary_sha256']==sha(refs['selection_summary'])
        and confirmation['master']['weights']['P']==str(candidate),'Selection/confirmation not same fixed P master')
    prior=confirmation['audit']['results']['selection']
    require(prior==selection['audit']['results']['selection'],'Confirmation audit has different selection result')
    required={**selection['required'],**confirmation['required']}
    require(all(confirmation['audit']['evidence_sha256'].get(p)==h for p,h in required.items()),'Confirmation audit omits selection evidence')
    close=read(refs['closure']);master=confirmation['master']
    require(close['status']=='closed' and close['phase']=='confirmation' and close['head']==PERFORMANCE_HEAD
        and close['model_jobs_stopped'] is True and close['source_before']==close['source_after']==master['identity']
        and close['master_sha256']==sha(confirmation['master_path'])
        and close['selection_state_sha256']==sha(selection['state_path'])
        and close['confirmation_state_sha256']==sha(confirmation['state_path'])
        and close['confirmation_summary_sha256']==sha(refs['confirmation_summary'])
        and close['confirmation_audit_sha256']==sha(refs['confirmation_audit']),'Missing/changed source freeze closure')
    verify_hashes(close['evidence_sha256'],evidence,substitutions)
    required[str(refs['confirmation_audit'])]=sha(refs['confirmation_audit'])
    require(all(close['evidence_sha256'].get(p)==h for p,h in required.items()),'Closure omits phase evidence')
    qcpath=reference(bundle['technical_qc'],evidence,substitutions)
    technical_evidence(qcpath,bundle,root,evidence,substitutions)
    return dict(bundle=bundle,bundle_path=str(bundle_path),bundle_sha256=sha(bundle_path),root=str(root),
                targets={k:str(v) for k,v in dest.items()},evidence_sha256=evidence)


def git_head(root):
    return subprocess.check_output(['git','-C',str(root),'rev-parse','--verify','HEAD'],text=True).strip()


def no_model_jobs():
    snapshot=subprocess.check_output(['ps','-axo','pid=,args='],text=True)
    pattern=re.compile(r'(?:-m\s+scripts\.|scripts/)(?:experiment|par_eval|train|finetune|evaluate|compare_weights|check_candidate_runner|build_submission|targeting_adapt(?:_backup)?|xversion_replay)(?:\s|\.py\b)|(?:train_targeting|run_backup_training|verify_P_package)\.py|from\s+scripts\.build_submission\s+import\s+check_battle')
    require(not any(pattern.search(line) for line in snapshot.splitlines() if line.strip().split(maxsplit=1)[0]!=str(os.getpid())),
            'Other model jobs active; exclusive installation refused')


@contextmanager
def quiet_lock(root):
    common=subprocess.check_output(['git','-C',str(root),'rev-parse','--path-format=absolute','--git-common-dir'],text=True).strip()
    with (Path(common)/'early_curriculum_resource.lock').open('a') as heavy, (Path(common)/'P_release_writer.lock').open('a') as writer:
        try:
            fcntl.flock(heavy,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(writer,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:raise ValueError('Shared resource/release lock held') from exc
        yield


def fsync_dir(path):
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_DIRECTORY',0))
    try:os.fsync(fd)
    finally:os.close(fd)


def save_json(path,value):
    path=Path(path)
    require(not path.is_symlink() and (not path.exists() or path.stat().st_nlink==1),'Unsafe own journal')
    with tempfile.NamedTemporaryFile('w',dir=path.parent,delete=False) as stream:
        temp=Path(stream.name);json.dump(value,stream,indent=2,allow_nan=False)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())
    os.replace(temp,path);fsync_dir(path.parent)


def copy_exclusive(source,target,expected, *, mode=0o444):
    with regular(source).open('rb') as src, Path(target).open('xb') as dst:
        shutil.copyfileobj(src,dst,1024*1024);dst.flush();os.fsync(dst.fileno())
    require(sha(target)==expected,'Prepared/backup copy hash mismatch')
    os.chmod(target,mode);fsync_dir(Path(target).parent)


def identity(path):
    path=regular(path);info=path.stat()
    return dict(dev=info.st_dev,ino=info.st_ino,sha256=sha(path))


def fresh_authorization(path,verdict, *, now):
    value=read(path);issued,expires=value['issued_at'],value['expires_at']
    require(value['verdict']==verdict and type(issued) in (int,float) and type(expires) in (int,float)
            and math.isfinite(issued) and math.isfinite(expires) and issued<=now<expires<=issued+600,
            'Fresh explicit Root authorization required')
    require(value['readers_stopped'] is True and value['writers_stopped'] is True
            and type(value['model_jobs']) is int and value['model_jobs']==0,'Exclusive reader/writer window required')
    return value


def check_install_authorization(path,ctx):
    auth=fresh_authorization(path,'AUTHORIZED_P_INSTALL',now=time.time())
    require(auth['bundle_sha256']==ctx['bundle_sha256'] and auth['target_root']==ctx['root']
            and auth['expected_target_head']==ctx['bundle']['expected_target_head'],'Root authorization binding changed')
    return auth


def backup_and_stage(journal,ctx,tx,save):
    backup=tx/'backup';backup.mkdir(mode=0o700)
    files={}
    for label,target in ctx['targets'].items():
        target=Path(target);old=OLD_ZIP_SHA if label=='zip' else OLD_SHA
        copy_exclusive(target,backup/BACKUP_NAMES[label],old)
        files[label]=dict(original_path=str(target),backup_file=BACKUP_NAMES[label],sha256=old,bytes=target.stat().st_size)
    manifest=dict(schema_version=1,kind='P_release_old_backup',target_root=ctx['root'],
        expected_target_head=ctx['bundle']['expected_target_head'],bundle_sha256=ctx['bundle_sha256'],files=files)
    save_json(backup/'manifest.json',manifest);os.chmod(backup/'manifest.json',0o444);os.chmod(backup,0o555);fsync_dir(backup)
    journal['backup_manifest_sha256']=sha(backup/'manifest.json');save()
    for label,target in ctx['targets'].items():
        target=Path(target);prefix=target.parent/('.P_release_'+journal['id']+'_'+label)
        entry=dict(label=label,target=str(target),old_sha256=files[label]['sha256'],
            new_sha256=ctx['bundle']['new_zip']['sha256'] if label=='zip' else P_SHA,
            backup=str(backup/BACKUP_NAMES[label]),new_stage=str(prefix)+'.new',old_stage=str(prefix)+'.old',
            holding=str(prefix)+'.holding',discard=str(prefix)+'.discard',phase='staging',old_identity=identity(target))
        journal['entries'].append(entry);save()
        source=ctx['bundle']['new_zip']['path'] if label=='zip' else ctx['bundle']['candidate']['path']
        copy_exclusive(source,entry['new_stage'],entry['new_sha256'])
        copy_exclusive(entry['backup'],entry['old_stage'],entry['old_sha256'])
        entry['new_identity']=identity(entry['new_stage']);entry['phase']='prepared';save()
    journal['status']='prepared';save()


def move_to_holding(entry,save):
    require(identity(entry['target'])==entry['old_identity'],'Target changed immediately before switch')
    require(not Path(entry['holding']).exists(),'Holding path already exists')
    entry['phase']='move_intent';save()
    os.rename(entry['target'],entry['holding']);fsync_dir(Path(entry['target']).parent)
    moved=identity(entry['holding'])
    if moved!=entry['old_identity']:
        entry['foreign_holding_identity']=moved;save()
        # Restore the moved foreign bytes only into an empty name; never overwrite.
        try:os.link(entry['holding'],entry['target']);fsync_dir(Path(entry['target']).parent)
        except FileExistsError:pass
        raise ValueError('Foreign replacement moved to holding; preserved for manual resolution')
    entry['phase']='old_held';save()


def publish(journal,entry,save):
    require(identity(entry['new_stage'])==entry['new_identity'],'Staged replacement changed')
    move_to_holding(entry,save)
    entry['phase']='publish_intent';save()
    os.link(entry['new_stage'],entry['target'])  # Atomic no-overwrite publication.
    fsync_dir(Path(entry['target']).parent)
    require(identity(entry['target'])==entry['new_identity'],'Published target differs')
    entry['phase']='published';journal['status']=entry['label']+'_swapped';save()


def verify_backup(journal,tx):
    manifest_path=tx/'backup/manifest.json'
    require(sha(regular(manifest_path,single_link=True))==journal['backup_manifest_sha256'],'Backup manifest changed')
    manifest=read(manifest_path)
    require(manifest_path.stat().st_mode&0o222==0 and manifest_path.parent.stat().st_mode&0o222==0,'Backup manifest/directory must remain immutable')
    require(manifest['kind']=='P_release_old_backup' and manifest['bundle_sha256']==journal['bundle_sha256']
        and manifest['target_root']==journal['root'] and set(manifest['files'])==set(BACKUP_NAMES),'Wrong backup identity')
    expected={*BACKUP_NAMES.values(),'manifest.json'}
    require({p.name for p in manifest_path.parent.iterdir()}==expected,'Unexpected backup contents')
    substitutions={}
    for label,record in manifest['files'].items():
        path=regular(manifest_path.parent/BACKUP_NAMES[label],single_link=True)
        require(record['original_path']==journal['targets'][label] and record['backup_file']==BACKUP_NAMES[label]
            and record['sha256']==(OLD_ZIP_SHA if label=='zip' else OLD_SHA) and sha(path)==record['sha256']
            and path.stat().st_size==record['bytes'] and path.stat().st_mode&0o222==0,'Old backup bytes/mode changed')
        substitutions[record['original_path']]=str(path)
    return substitutions


def rollback(journal,tx,save):
    blocked=signal.pthread_sigmask(signal.SIG_BLOCK,SIGNALS)
    try:
        substitutions=verify_backup(journal,tx) if journal.get('backup_manifest_sha256') else {}
        conflicts=[];journal['status']='rolling_back';save()
        by_label={e['label']:e for e in journal['entries']}
        for label,target in journal['targets'].items():
            target=Path(target);entry=by_label.get(label);old=OLD_ZIP_SHA if label=='zip' else OLD_SHA
            if target.exists() or target.is_symlink():
                try:actual=identity(target)
                except (ValueError,OSError):conflicts.append(str(target));continue
                if actual['sha256']==old:
                    owned_old=(not entry or actual==entry['old_identity'] or actual==entry.get('restored_identity')
                        or (entry.get('phase')=='rollback_publish_intent' and Path(entry['old_stage']).exists()
                            and actual==identity(entry['old_stage'])))
                    if not owned_old:
                        conflicts.append(str(target))  # Same bytes with foreign inode are still foreign ownership.
                    continue
                if not entry or actual!=entry.get('new_identity'):
                    conflicts.append(str(target));continue
                discard=Path(entry['discard'])
                require(not discard.exists(),'Recovery discard already occupied')
                entry['phase']='rollback_move_intent';save()
                os.rename(target,discard);fsync_dir(target.parent)
                if identity(discard)!=entry['new_identity']:
                    try:os.link(discard,target);fsync_dir(target.parent)
                    except FileExistsError:pass
                    conflicts.append(str(target));continue
            if not substitutions:
                conflicts.append(str(target));continue
            # Publish an old copy only into an empty path; never overwrite an interloper.
            oldstage=Path(entry['old_stage']) if entry else target.parent/('.P_release_'+journal['id']+'_'+label+'.recovery')
            if not oldstage.exists():copy_exclusive(substitutions[str(target)],oldstage,old)
            require(sha(regular(oldstage))==old,'Rollback staging changed')
            if entry:entry['phase']='rollback_publish_intent';save()
            try:os.link(oldstage,target);fsync_dir(target.parent)
            except FileExistsError:conflicts.append(str(target));continue
            if entry:entry['restored_identity']=identity(target);entry['phase']='restored';save()
            oldstage.unlink();fsync_dir(target.parent)
        if not conflicts:
            require(all(sha(regular(p))==(OLD_ZIP_SHA if label=='zip' else OLD_SHA) for label,p in journal['targets'].items()),'Rollback final hash mismatch')
        journal['status']='rollback_conflict' if conflicts else 'rolled_back';journal['conflicts']=conflicts;save()
    finally:signal.pthread_sigmask(signal.SIG_SETMASK,blocked)


def check_inputs_unchanged(ctx,substitutions=None):
    evidence={};verify_hashes(ctx['evidence_sha256'],evidence,substitutions)
    require(git_head(ctx['root'])==ctx['bundle']['expected_target_head'],'Target HEAD changed during transaction')


def pending_path(root):
    return Path(root)/'agents/sherlock/weights/.P_release_pending.json'


def pending_value(journal):
    return dict(kind='pending_qualified_P_transaction',transaction=journal['transaction'],root=journal['root'],
                id=journal['id'],bundle_sha256=journal['bundle_sha256'],installer_sha256=journal['installer_sha256'])


def reserve_pending(journal):
    path=pending_path(journal['root'])
    with path.open('x') as stream:
        json.dump(pending_value(journal),stream,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    fsync_dir(path.parent)


def clear_pending(journal):
    path=regular(pending_path(journal['root']),single_link=True)
    require(read(path)==pending_value(journal),'Foreign pending transaction marker; preserved')
    path.unlink();fsync_dir(path.parent)


def install(bundle_path,authorization_path,transaction):
    # No writes until the real resource lock and all checks have succeeded.
    root=real_path(read(bundle_path)['target_root']);tx=real_path(transaction,exists=False)
    if tx.exists():raise FileExistsError(tx)
    require(tx.parent.is_dir(),'Use a fresh transaction path in an existing directory')
    with quiet_lock(root):
        require(not pending_path(root).exists() and not pending_path(root).is_symlink(),'Unresolved pending transaction blocks a new release')
        no_model_jobs();ctx=validate_bundle(bundle_path);check_install_authorization(authorization_path,ctx)
        auth_sha=sha(authorization_path);tx.mkdir(mode=0o700,exist_ok=False);fsync_dir(tx.parent)
        journal=dict(schema_version=1,kind='qualified_P_transaction',id=uuid.uuid4().hex,status='preparing',
            transaction=str(tx),root=ctx['root'],targets=ctx['targets'],bundle_path=ctx['bundle_path'],bundle_sha256=ctx['bundle_sha256'],
            authorization_path=str(real_path(authorization_path)),authorization_sha256=auth_sha,
            installer_path=str(Path(__file__).resolve()),installer_sha256=sha(__file__),entries=[],history=[])
        journal_path=tx/'journal.json'
        def save():
            journal['updated_at']=time.time();save_json(journal_path,journal)
        handlers={};owned_pending=False
        def interrupted(sig,frame):raise InterruptedError('Installation interrupted by signal '+str(sig))
        try:
            blocked=signal.pthread_sigmask(signal.SIG_BLOCK,SIGNALS)
            try:
                save();reserve_pending(journal);owned_pending=True
                for sig in SIGNALS:handlers[sig]=signal.signal(sig,interrupted)
            finally:signal.pthread_sigmask(signal.SIG_SETMASK,blocked)
            backup_and_stage(journal,ctx,tx,save)
            # Last-moment guards: exact old targets, authorization, evidence, quiet window.
            validate_bundle(bundle_path);check_install_authorization(authorization_path,ctx)
            require(sha(authorization_path)==auth_sha,'Root authorization changed');no_model_jobs()
            for entry in journal['entries']:
                check_inputs_unchanged(ctx,verify_backup(journal,tx))
                publish(journal,entry,save)
            for entry in journal['entries']:
                require(identity(entry['target'])==entry['new_identity'],'Final active inode/hash differs')
            check_inputs_unchanged(ctx,verify_backup(journal,tx))
            # Remove own staging links so installed files are single-link regular files.
            for entry in journal['entries']:
                require(identity(entry['new_stage'])==entry['new_identity'],'Staging ownership changed')
                Path(entry['new_stage']).unlink();fsync_dir(Path(entry['target']).parent)
            journal.update(status='committed',installed_sha256={e['target']:sha(e['target']) for e in journal['entries']},
                           independent_evidence_verified=True,model_execution_by_installer=False)
            save();clear_pending(journal);owned_pending=False
        except BaseException as exc:
            journal['error']=f'{type(exc).__name__}: {exc}';journal['history'].append(dict(status=journal['status'],error=journal['error']))
            try:rollback(journal,tx,save)
            except BaseException as recovery_error:
                journal.update(status='rollback_conflict',rollback_error=repr(recovery_error));save()
            if owned_pending and journal['status']=='rolled_back':
                try:clear_pending(journal);owned_pending=False
                except BaseException as marker_error:
                    journal.update(status='rollback_conflict',pending_marker_error=repr(marker_error));save()
            raise
        finally:
            for sig,handler in handlers.items():signal.signal(sig,handler)
    return journal


def check_journal(journal,tx):
    require(journal['schema_version']==1 and journal['kind']=='qualified_P_transaction'
        and journal['transaction']==str(tx) and re.fullmatch('[0-9a-f]{32}',journal['id'])
        and journal['installer_path']==str(Path(__file__).resolve()) and journal['installer_sha256']==sha(__file__),'Unbound/foreign journal')
    root=real_path(journal['root'])
    require(journal['targets']=={k:str(v) for k,v in targets(root).items()},'Journal redirects install targets')
    require(sha(regular(journal['bundle_path']))==journal['bundle_sha256']
        and sha(regular(journal['authorization_path']))==journal['authorization_sha256'],'Historical bundle/authorization changed')
    require(len(journal['entries'])<=3 and len({e['label'] for e in journal['entries']})==len(journal['entries']), 'Duplicate journal entries')
    for entry in journal['entries']:
        label=entry['label'];require(label in BACKUP_NAMES,'Unknown target label')
        target=targets(root)[label];prefix=target.parent/('.P_release_'+journal['id']+'_'+label)
        require(entry['target']==str(target) and entry['backup']==str(tx/'backup'/BACKUP_NAMES[label])
            and all(entry[k]==str(prefix)+suffix for k,suffix in [('new_stage','.new'),('old_stage','.old'),('holding','.holding'),('discard','.discard')])
            and entry['old_sha256']==(OLD_ZIP_SHA if label=='zip' else OLD_SHA)
            and entry['new_sha256']==(read(journal['bundle_path'])['new_zip']['sha256'] if label=='zip' else P_SHA),'Journal entry path/hash differs')
    return root


def recover(transaction,authorization_path):
    tx=real_path(transaction);journal_path=regular(tx/'journal.json',single_link=True);journal=read(journal_path)
    root=check_journal(journal,tx)
    with quiet_lock(root):
        auth=fresh_authorization(authorization_path,'AUTHORIZED_P_RECOVERY',now=time.time())
        require(auth['transaction']==str(tx) and auth['journal_sha256']==sha(journal_path),'Recovery authorization does not bind journal')
        require(journal['status'] not in ('committed','rolled_back'),'Closed transaction is not crash recovery')
        no_model_jobs()
        marker=pending_path(root)
        if marker.exists() or marker.is_symlink():
            require(read(regular(marker,single_link=True))==pending_value(journal),'Foreign pending transaction marker')
        else:require(journal['status']=='preparing' and not journal['entries'],'Missing pending transaction marker')
        if journal.get('backup_manifest_sha256'):
            substitutions=verify_backup(journal,tx)
        else:
            # A crash before the backup was sealed cannot have published any
            # target: backup_and_stage records the seal before creating entries.
            require(not journal['entries'],'Unsealed backup with mutation entries')
            substitutions={}
        # Recovery validates evidence against verified OLD backup substitutions;
        # it must not demand the live transitional targets are still OLD.
        ctx=validate_bundle(journal['bundle_path'],substitutions=substitutions,check_old=not bool(substitutions))
        require(ctx['targets']==journal['targets'],'Recovery target mismatch')
        def save():save_json(journal_path,journal)
        journal['recovery_authorization']=dict(path=str(real_path(authorization_path)),sha256=sha(authorization_path))
        rollback(journal,tx,save)
        if journal['status']=='rolled_back' and marker.exists():clear_pending(journal)
        return journal


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    c=sub.add_parser('check');c.add_argument('--bundle',required=True)
    p=sub.add_parser('install')
    for name in ('bundle','authorization','transaction'):p.add_argument('--'+name,required=True)
    p.add_argument('--install',action='store_true')
    r=sub.add_parser('recover');r.add_argument('--transaction',required=True);r.add_argument('--authorization',required=True);r.add_argument('--recover',action='store_true')
    args=parser.parse_args(argv)
    if args.mode=='check':
        ctx=validate_bundle(args.bundle);print(json.dumps(dict(status='eligible_files_verified',bundle_sha256=ctx['bundle_sha256'],installed=False)))
    elif args.mode=='install':
        if not args.install:parser.error('Explicit --install required; no changes made')
        print(json.dumps(dict(status=install(args.bundle,args.authorization,args.transaction)['status'])))
    else:
        if not args.recover:parser.error('Explicit --recover required; no changes made')
        print(json.dumps(dict(status=recover(args.transaction,args.authorization)['status'])))


if __name__=='__main__':main()
