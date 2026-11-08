"""Independent data-only Artillery confirmation audit; no repository or model imports."""
import argparse,csv,datetime,hashlib,json,math,os,re,subprocess
from pathlib import Path
ROOT=Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
BASE=ROOT/'experiments/analysis/artillery_comparison_20261108';OUT=BASE/'confirmation'
HEAD=None;PROFILE='artillery_alignment_20261108'
FROZEN_HEAD='70669eb9e1509b1bddff902c22a2b7e394167f97'
ACCEPTED=None;MODEL_HASHES=None
V14_SHA='98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
PIN_PATH=Path('/tmp/artillery-confirmation-root-pins.json')
OUTPUT_JSON=Path('/tmp/artillery-confirmation-audit.json')
OUTPUT_MD=Path('/tmp/artillery-confirmation-audit.md')
SEED_ACCEPTANCE=BASE/'operations/seed_acceptance.json'
COHORTS={'selection_panel':list(range(9800000,9800020)),
         'selection_direct':list(range(9800100,9800120)),
         'confirmation_panel':list(range(9801000,9801020)),
         'confirmation_direct':list(range(9801100,9801120))}
ALL_ROLE_PATHS={'V14':'experiments/releases/20261101_v14_baseline/agent_p0.pth','CONTROL38':'experiments/candidates/artillery_alignment_20261108/CONTROL38.pth','ALIGNED38':'experiments/candidates/artillery_alignment_20261108/ALIGNED38.pth'}
ROLE_PATHS=None;NOMINEE=None
OPPONENT_HASHES={'experiments/releases/20261022_all18_v3/agent_p0.pth':'aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935','experiments/releases/20261022_v7_Bsnpd/agent_p0.pth':'c394acba84f7a298f8f1e6107328d8e6ce151b367a28997b059aa82fc8a895e6','experiments/releases/20261022_v10_baseline/agent_p0.pth':'03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67','experiments/releases/20261101_v13_neb/agent_p0.pth':'6d00b6c52366a613eed3b7b5b6f9c3c088802716a85c30fe192c46c57bdd8e62','experiments/releases/20261101_v14_baseline/agent_p0.pth':V14_SHA}
FIELDS=('seed','side','opponent','result','game_win','point_win','our_wins','opp_wins','our_points','opp_points','point_counting_version','wait_frac','invalid_frac','greedy_masked_frac','sap_attempts','sap_hits','stack_frac','relics_found','relics_seen','known_point_tiles','belief_contradictions','unit_steps','steps','secs')
SIDES=('player_0','player_1')
PANEL=('solution92','sol92_sq','self:experiments/releases/20261022_all18_v3/agent_p0.pth','self:experiments/releases/20261022_v7_Bsnpd/agent_p0.pth','self:experiments/releases/20261022_v10_baseline/agent_p0.pth','self:experiments/releases/20261101_v13_neb/agent_p0.pth')
OPPONENTS=PANEL+('default',);CANDIDATES=('CONTROL38','ALIGNED38');DIRECT='self:'+ALL_ROLE_PATHS['V14']
def need(ok,msg):
    if not ok: raise ValueError(msg)
def read(p): return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
    return h.hexdigest()
def verify(mapping):
    for p,value in mapping.items():need(sha(p)==value,'changed input '+p)
def hexhash(value,length=64):return isinstance(value,str) and re.fullmatch('[0-9a-f]{'+str(length)+'}',value) is not None
def pinned_root_inputs(expected_pin_hash):
    global HEAD,ACCEPTED,MODEL_HASHES,NOMINEE,ROLE_PATHS
    need(hexhash(expected_pin_hash) and sha(PIN_PATH)==expected_pin_hash,'Explicit Root pin hash absent or changed')
    pins=read(PIN_PATH)
    need(pins.get('schema_version')==1 and pins.get('approved') is True and pins.get('profile')==PROFILE
        and pins.get('phase')=='confirmation' and pins.get('root')==str(ROOT),'Wrong explicit Root pins')
    HEAD=pins.get('expected_head');ACCEPTED=pins.get('historical_acceptance_sha256');MODEL_HASHES=pins.get('model_sha256')
    NOMINEE=pins.get('nominee');need(NOMINEE in CANDIDATES,'Exactly one accepted nominee required')
    ROLE_PATHS={r:ALL_ROLE_PATHS[r] for r in ('V14',NOMINEE)}
    need(HEAD==FROZEN_HEAD and hexhash(ACCEPTED) and hexhash(pins.get('admission_sha256'))
        and hexhash(pins.get('seed_acceptance_sha256')) and hexhash(pins.get('confirmation_plan_sha256'))
        and hexhash(pins.get('selection_summary_sha256')),'Missing future actual trust anchors or changed selection freeze')
    selection=pins.get('selection_acceptance')
    need(isinstance(selection,dict) and set(selection)=={'path','sha256'} and Path(selection['path']).is_absolute()
        and hexhash(selection['sha256']),'Actual accepted selection pin required')
    need(isinstance(MODEL_HASHES,dict) and set(MODEL_HASHES)==set(ROLE_PATHS)
        and all(hexhash(v) for v in MODEL_HASHES.values()) and MODEL_HASHES['V14']==V14_SHA,'Incomplete actual model pins')
    need(pins.get('source_identity',{}).get('head')==HEAD and bool(pins['source_identity'].get('files')),'Root source identity absent')
    need(isinstance(pins.get('files'),dict) and bool(pins['files'])
        and all(Path(p).is_absolute() and hexhash(v) for p,v in pins['files'].items()),'Root file pins absent')
    verify(pins['files'])
    return pins
def freshness_bindings(expected_hash):
    need(sha(SEED_ACCEPTANCE)==expected_hash,'Root-pinned freshness acceptance changed')
    accepted=read(SEED_ACCEPTANCE)
    need(all(accepted.get(k)==v for k,v in dict(schema_version=1,status='PASS',profile=PROFILE,cohorts=COHORTS).items()),'Wrong fresh cohorts')
    bound={str(SEED_ACCEPTANCE):expected_hash}
    def artifact(item):
        need(isinstance(item,dict) and set(item)=={'path','sha256'} and hexhash(item['sha256']),'Malformed seed evidence')
        relative=Path(item['path']);need(not relative.is_absolute() and '..' not in relative.parts,'Seed evidence outside repository')
        path=(ROOT/relative).resolve();need(path.is_relative_to(ROOT.resolve()) and sha(path)==item['sha256'],'Seed artifact hash/path differs')
        bound[str(path)]=item['sha256'];return path
    audit=read(artifact(accepted.get('audit')))
    need(audit.get('status')=='PASS' and audit.get('no_observed_conflicts') is True
        and isinstance(audit.get('limitations'),list) and bool(audit['limitations']),'Seed audit decision/limits absent')
    artifact(audit.get('raw_audit'))
    for relative,digest in audit.get('files',{}).items():artifact(dict(path=relative,sha256=digest))
    for name,seeds in COHORTS.items():
        path=BASE/'plans'/f'{name}.json';need(read(path)==seeds,'Fresh seed list differs')
        bound[str(path)]=sha(path)
    return bound
def source_check(source,plans):
    need(subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()==HEAD==source['head'],'wrong frozen HEAD')
    verify(source['files']);need(str(Path(source['python']).resolve())==source['executable'] and sha(source['python'])==source['executable_sha256'],'changed interpreter')
    names=subprocess.check_output(['git','-C',str(ROOT),'ls-files','-z','--cached','--others','--exclude-standard','--','*.py']).split(b'\0')
    inventory={ROOT/os.fsdecode(n) for n in names if n}
    for d in ('scripts','agents','lux'):inventory.update((ROOT/d).rglob('*.py'))
    inventory.update(map(Path,plans))
    for name in ('requirements.txt','pyproject.toml'):
        if (ROOT/name).is_file():inventory.add(ROOT/name)
    venv=Path(source['python']).parent.parent
    if (venv/'pyvenv.cfg').is_file():inventory.add(venv/'pyvenv.cfg')
    for engine in (venv/'lib').glob('python*/site-packages/luxai_s3'):inventory.update(engine.rglob('*.py'))
    need({str(p) for p in inventory}==set(source['files']),'changed source inventory')
def compare(actual,expected,path='root',stats=None):
    if stats is not None:stats[0]+=1
    if isinstance(expected,dict):
        need(isinstance(actual,dict) and set(actual)==set(expected),'keys differ at '+path)
        for k,v in expected.items():compare(actual[k],v,path+'.'+k,stats)
    elif isinstance(expected,list):
        need(isinstance(actual,list) and len(actual)==len(expected),'list differs at '+path)
        for i,v in enumerate(expected):compare(actual[i],v,path+'.'+str(i),stats)
    elif type(expected) is float:
        need(type(actual) in (float,int) and math.isfinite(actual) and math.isclose(actual,expected,abs_tol=1e-12,rel_tol=1e-12),'numeric mismatch at '+path+': '+repr((actual,expected)))
    else:need(type(actual)==type(expected) and actual==expected,'value mismatch at '+path+': '+repr((actual,expected)))
def counts(rows):
    w=sum(r['result']==1 for r in rows);d=sum(r['result']==.5 for r in rows);n=len(rows)
    return dict(games=n,wins=w,draws=d,losses=n-w-d,half_wins=2*w+d,score=(w+.5*d)/n,strict_winrate=w/n)
def subset(rows,opponents):return [r for r in rows if r['opponent'] in opponents]
def accepted_selection_bindings(pins):
    """Trust only Root-pinned independent acceptance, then retain its exact evidence chain."""
    acceptance_path=Path(pins['selection_acceptance']['path']);acceptance_hash=pins['selection_acceptance']['sha256']
    need(sha(acceptance_path)==acceptance_hash,'Accepted selection bytes changed')
    audit=read(acceptance_path);selection=BASE/'selection';summary_path=selection/'summary.json'
    need(all(audit.get(k)==v for k,v in dict(schema_version=1,status='PASS',profile=PROFILE,phase='selection',
        nominee=NOMINEE,jobs=11,games=440,source_head=FROZEN_HEAD).items()),'Wrong independent selection acceptance')
    need(audit.get('source')==pins['source_identity'],'Selection and confirmation source identities differ')
    need(audit.get('summary_sha256')==pins['selection_summary_sha256']==sha(summary_path),'Selection summary trust anchor differs')
    summary=read(summary_path)
    need(all(summary.get(k)==v for k,v in dict(schema_version=1,status='complete',profile=PROFILE,
        phase='selection',nominee=NOMINEE,jobs=11,games=440).items()),'Wrong accepted selection summary')
    compare(summary['results'],audit['results'],'accepted_selection_results')
    compare(summary['aligned_minus_control_panel'],audit['aligned_minus_control_panel'],'accepted_selection_arm_contrast')
    need(set(audit['results'])==set(CANDIDATES),'Both selection candidates must have been accepted')
    # Reconstruct the fixed nomination from accepted integer counts; no new selection or pooling.
    for role,result in audit['results'].items():
        panel=result['panel'];sol=result['solution92'];dfl=result['default']['candidate'];duel=result['direct']['candidate']
        gain=panel['candidate']['half_wins']-panel['reference']['half_wins']
        checks=dict(panel_half_win_gain_ge4=gain>=4,solution_score_nonnegative=sol['candidate']['half_wins']>=sol['reference']['half_wins'],
            solution_strict_wins_nonnegative=sol['candidate']['wins']>=sol['reference']['wins'],default40_strict_wins=dfl['wins']==40,
            direct_score_ge50pct=duel['half_wins']>=40)
        compare(result['checks'],checks,'accepted_selection_checks.'+role)
        need(result['passed'] is all(checks.values()) and result['nominable'] is True and result['panel_half_win_gain']==gain,'Selection decision differs')
    eligible=[r for r in CANDIDATES if audit['results'][r]['passed']]
    selected=min(eligible,key=lambda r:(-audit['results'][r]['panel']['candidate']['half_wins'],
        -audit['results'][r]['solution92']['candidate']['wins'],-audit['results'][r]['direct']['candidate']['half_wins'],CANDIDATES.index(r))) if eligible else None
    need(selected==NOMINEE,'Root nominee differs from exact independently accepted selection')
    bindings=audit.get('input_sha256')
    need(isinstance(bindings,dict) and bool(bindings) and all(Path(p).is_absolute() and hexhash(h) for p,h in bindings.items()),'Selection evidence hashes missing')
    verify(bindings)
    paths=[acceptance_path,BASE/'selection_launch.json',summary_path,selection/'state.json',selection/'provenance.json',BASE/'plans/selection_jobs.json']
    names={f'{r}_panel_{i}' for r in ALL_ROLE_PATHS for i in range(3)}|{f'{r}_direct' for r in CANDIDATES}
    need(set(summary['input_sha256']['csv'])==set(summary['input_sha256']['receipts'])==names,'Accepted selection job matrix changed')
    for name in sorted(names):
        csv_path=selection/f'{name}.csv';receipt=selection/'receipts'/f'{name}.json'
        need(sha(csv_path)==summary['input_sha256']['csv'][name] and sha(receipt)==summary['input_sha256']['receipts'][name],'Accepted selection raw evidence changed')
        paths.extend((csv_path,receipt))
    for path in paths:
        digest=sha(path)
        need(pins['files'].get(str(path))==digest,'Root pins omit accepted selection evidence')
        if path!=acceptance_path:need(bindings.get(str(path))==digest,'Accepted selection audit omits required evidence')
    old_state=read(selection/'state.json');old_provenance=read(selection/'provenance.json');old_launch=read(BASE/'selection_launch.json')
    need(old_state['source']==old_provenance['source_identity']==old_launch['source_identity']==pins['source_identity'],
        'Source/HEAD changed between selection and confirmation')
    need(old_state['status']=='complete' and old_state['completed_games']==old_state['expected_games']==440
        and not old_state['active'] and not old_state['queue'],'Selection not fully closed')
    return paths,{**bindings,str(acceptance_path):acceptance_hash}
def expected_jobs():
    jobs=[]
    for role in ROLE_PATHS:
        for i,opp in enumerate(OPPONENTS):jobs.append(dict(name=f'{role}_panel_{i}',role=role,kind='panel',weights=ROLE_PATHS[role],opponent=opp,seed_list='experiments/analysis/artillery_comparison_20261108/plans/confirmation_panel.json',expected_games=40,workers=1))
    jobs.append(dict(name=f'{NOMINEE}_direct',role=NOMINEE,kind='direct',weights=ROLE_PATHS[NOMINEE],opponent=DIRECT,seed_list='experiments/analysis/artillery_comparison_20261108/plans/confirmation_direct.json',expected_games=40,workers=1))
    return jobs

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--completed-authorized',action='store_true')
    parser.add_argument('--pins-sha256',required=True);args=parser.parse_args()
    need(args.completed_authorized,'Await explicit root completed signal; no interim outcomes audited')
    need(not OUTPUT_JSON.exists() and not OUTPUT_MD.exists(),'No overwrite or automatic repeat')
    pins=pinned_root_inputs(args.pins_sha256)
    seed_bindings=freshness_bindings(pins['seed_acceptance_sha256'])
    selection_paths,selection_bindings=accepted_selection_bindings(pins)
    nominee=NOMINEE
    need(sha(BASE/'plans/confirmation_jobs.json')==pins['confirmation_plan_sha256'],'Root-pinned future confirmation plan changed')
    state_initial_hash=sha(OUT/'state.json');summary_initial_hash=sha(OUT/'summary.json')
    state=read(OUT/'state.json');provenance=read(OUT/'provenance.json');launch=read(BASE/'confirmation_launch.json');plan=read(BASE/'plans/confirmation_jobs.json');summary=read(OUT/'summary.json')
    need(state['status']=='complete' and state['completed_games']==state['expected_games']==600 and not state['active'] and not state['queue'],'confirmation not completely ended')
    need(type(state.get('wake',{}).get('returncode')) is int,'Supervisor cleanup not yet completed')
    snapshot=subprocess.check_output(['ps','-axo','pid=,pgid=,args='],text=True);groups={j['pgid'] for j in state['jobs'].values()}
    groups.add(state['wake']['pgid'])
    need(not any(int(p[1]) in groups for line in snapshot.splitlines() if len(p:=line.split(None,2))==3),'owned group still alive')
    need(not any(int(p[0])==state['owner_pid'] for line in snapshot.splitlines() if len(p:=line.split(None,2))==3),'Supervisor still alive')
    for d in (state,provenance,launch):need(d['profile']==PROFILE and d['phase']=='confirmation','phase identity')
    need(state['nominee']==provenance['nominee']==nominee and state['selection_acceptance']==pins['selection_acceptance']['path'],'Confirmation nominee/selection acceptance differs')
    need(state['source']==provenance['source_identity']==launch['source_identity'] and state['provenance']==provenance and state['expected_head']==HEAD and state['python']==state['source']['python'],'source/launch/provenance identity')
    need(state['source']==pins['source_identity'],'Source identity differs from independent Root pins')
    need(state['seed_acceptance_sha256']==provenance['seed_acceptance_sha256']==pins['seed_acceptance_sha256']
        and provenance['study_kind']=='fixed_paired_artillery_alignment_comparison','Freshness/study provenance')
    need(state['root']==str(ROOT) and state['out']==launch['out']==str(OUT) and state['jobs_path']==launch['jobs_path']==str(BASE/'plans/confirmation_jobs.json') and state['reservation']==str(BASE/'confirmation_launch.json'),'exact paths')
    source_check(state['source'],state['plans']);verify(state['inputs']);verify(state['protected'])
    need(state['model_sha256']==provenance['model_sha256']==MODEL_HASHES,'exact candidate hashes')
    for role,path in ROLE_PATHS.items():need(sha(ROOT/path)==MODEL_HASHES[role],'model byte binding '+role)
    need(state['protected'][str(ROOT/'Gruppe15.zip')]=='88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6','protected ZIP')
    for i in (0,1):need(state['protected'][str(ROOT/f'agents/sherlock/weights/agent_p{i}.pth')]==MODEL_HASHES['V14'],'protected V14')
    acceptance_path=ROOT/'experiments/analysis/artillery_alignment_20261108/operations/historical_training_acceptance.json';need(sha(acceptance_path)==ACCEPTED and state['acceptance_sha256']==provenance['acceptance_sha256']==ACCEPTED,'historical training acceptance')
    admission_path=ROOT/'experiments/candidates/artillery_alignment_20261108/admission.json';admission=read(admission_path)
    need(state['admission_path']==str(admission_path) and state['admission_sha256']==sha(admission_path)==pins['admission_sha256'] and admission['acceptance_sha256']==ACCEPTED,'admission binding')
    need(admission['inference_config']['fog_unknown_reward_neutral'] is False
        and admission['inference_config']['art_splash_in_training'] is False and admission['reload_verified'] is True,'admitted inference config')
    for role in ROLE_PATHS:need(admission['roles'][role]['path']==ROLE_PATHS[role] and admission['roles'][role]['sha256']==MODEL_HASHES[role] and len(admission['roles'][role]['members'])==(36 if role=='V14' else 38),'admitted exact role '+role)
    jobs=expected_jobs();expected_plan=dict(profile=PROFILE,protocol='docs/superpowers/plans/2026-11-08-artillery-comparison.md',phase='confirmation',nominee=nominee,roles=ROLE_PATHS,total_games=600,max_simultaneous_model_processes=2,opponent_sha256=OPPONENT_HASHES,jobs=jobs)
    compare(plan,expected_plan)
    for path,digest in OPPONENT_HASHES.items():need(sha(ROOT/path)==digest,'opponent '+path)
    need(read(BASE/'plans/confirmation_panel.json')==list(range(9801000,9801020)) and read(BASE/'plans/confirmation_direct.json')==list(range(9801100,9801120)),'confirmation seed lists')
    names={j['name'] for j in jobs};need(set(state['jobs'])==set(state['receipts'])==names,'exact job membership')
    need({p.stem for p in OUT.glob('*.csv')}=={p.stem for p in (OUT/'receipts').glob('*.json')}==names,'exact artifact membership')
    expected_job_plan={j['name']:{**j,'seeds':list(range(9801100 if j['kind']=='direct' else 9801000,9801120 if j['kind']=='direct' else 9801020))} for j in jobs}
    compare(state['job_plan'],expected_job_plan)
    all_rows={};csv_hashes={};receipt_hashes={};bound_artifacts={}
    required=[BASE/'plans/confirmation_jobs.json',OUT/'provenance.json',BASE/'confirmation_launch.json',admission_path,acceptance_path,*selection_paths,*map(Path,admission['input_sha256']),*map(Path,seed_bindings),*(ROOT/p for p in ROLE_PATHS.values()),*(ROOT/p for p in OPPONENT_HASHES),*(ROOT/p for p in state['plans'])]
    trusted_before_launch={str(p):sha(p) for p in required if p not in (OUT/'provenance.json',BASE/'confirmation_launch.json')}
    need(all(pins['files'].get(p)==digest for p,digest in trusted_before_launch.items()),'Root pins omit an admitted prelaunch file')
    need(all(state['inputs'].get(p)==digest for p,digest in pins['files'].items()),'Root-pinned file absent from supervisor inputs')
    for job in jobs:
        name=job['name'];csv_path=OUT/f'{name}.csv';rp=OUT/'receipts'/f'{name}.json';receipt=read(rp);csv_hashes[name]=sha(csv_path);receipt_hashes[name]=sha(rp);required.extend((csv_path,rp,ROOT/job['seed_list']))
        expected=dict(profile=PROFILE,status='complete',returncode=0,job_name=name,phase='confirmation',role=job['role'],opponent=job['opponent'],weights=job['weights'],model_sha256=MODEL_HASHES[job['role']],seed_list_sha256=sha(ROOT/job['seed_list']),csv_sha256=csv_hashes[name],rows=40,source_identity=state['source'],opponent_sha256=OPPONENT_HASHES)
        command=[state['python'],'-B','-m','scripts.par_eval','--weights',str(ROOT/job['weights']),'--seed-list',str(ROOT/job['seed_list']),'--workers','1','--opponents',job['opponent'],'--out',str(csv_path)];expected['command']=command
        compare(receipt,expected);need(state['jobs'][name]['returncode']==0 and state['jobs'][name]['argv']==command,'actual job command/exit')
        compare(state['receipts'][name],dict(path=str(rp),sha256=receipt_hashes[name],rows=40))
        start=9801100 if job['kind']=='direct' else 9801000;keys={(job['opponent'],seed,side) for seed in range(start,start+20) for side in SIDES};seen=set();normalized=[]
        with csv_path.open() as f:
            reader=csv.DictReader(f);need(len(reader.fieldnames)==len(FIELDS) and set(reader.fieldnames)==set(FIELDS),'CSV schema '+name)
            for raw in reader:
                need(None not in raw and all(v not in ('',None) for v in raw.values()),'incomplete raw row')
                row={k:(v if k in ('side','opponent') else float(v)) for k,v in raw.items()}
                need(all(math.isfinite(v) for k,v in row.items() if k not in ('side','opponent')),'nonfinite raw row')
                need(row['seed'].is_integer(),'noninteger seed');row['seed']=int(row['seed']);key=(row['opponent'],row['seed'],row['side']);need(key in keys and key not in seen,'wrong or duplicate raw key');seen.add(key)
                own,other=row['our_wins'],row['opp_wins'];need(own.is_integer() and other.is_integer() and min(own,other)>=0 and own+other<=3,'match wins')
                need(row['result']==(1. if own>other else 0. if own<other else .5) and row['game_win']==int(own>other),'result/strict win consistency')
                need(row['point_win']==(1. if row['our_points']>row['opp_points'] else 0. if row['our_points']<row['opp_points'] else .5),'point result')
                need(row['steps']==303 and row['point_counting_version']==2 and row['secs']>=0,'complete engine game')
                for k in ('sap_attempts','sap_hits','relics_found','relics_seen','known_point_tiles','belief_contradictions','unit_steps','our_points','opp_points'):need(row[k].is_integer() and row[k]>=0,'nonnegative integer '+k)
                for k in ('wait_frac','invalid_frac','greedy_masked_frac','stack_frac'):need(0<=row[k]<=1,'invalid fraction '+k)
                normalized.append(row)
        need(seen==keys and len(normalized)==40,'full 40-game matrix '+name);all_rows[name]=normalized
    for path in required:need(state['inputs'].get(str(path))==sha(path),'missing required pinned input '+str(path))
    # Only after all 600 raw rows and bindings pass, compute independent statistics.
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[key]='1'
    import numpy as np
    def interval(values):
        values=np.asarray(values,dtype=float);rng=np.random.Generator(np.random.PCG64(0));means=rng.choice(values,size=(5000,len(values)),replace=True).mean(axis=1)
        return [float(x) for x in np.percentile(means,[2.5,97.5])]
    def paired(candidate,reference,opponents,per_opponent=False):
        c=subset(candidate,opponents);r=subset(reference,opponents)
        cm={s:sum(x['result'] for x in c if x['seed']==s)/(2*len(opponents)) for s in range(9801000,9801020)}
        rm={s:sum(x['result'] for x in r if x['seed']==s)/(2*len(opponents)) for s in range(9801000,9801020)}
        cv=np.asarray(list(cm.values()));rv=np.asarray(list(rm.values()));diff=cv-rv;lo,hi=interval(diff)
        out=dict(maps=20,score=float(cv.mean()),ref_score=float(rv.mean()),delta=float(diff.mean()),low=lo,high=hi)
        if per_opponent:out.update(opponent=opponents[0],games=40,excluded_candidate=0,excluded_reference=0)
        return dict(out,candidate=counts(c),reference=counts(r))
    def direct(rows):
        values=[sum(r['result'] for r in rows if r['seed']==s)/2 for s in range(9801100,9801120)];lo,hi=interval(values)
        return dict(maps=20,games=40,score=float(np.mean(values)),low=lo,high=hi,candidate=counts(rows))
    panels={role:[r for j in jobs if j['role']==role and j['kind']=='panel' for r in all_rows[j['name']]] for role in ROLE_PATHS}
    result=dict(panel=paired(panels[nominee],panels['V14'],PANEL),direct=direct(all_rows[nominee+'_direct']))
    for opp in ('solution92','default'):result[opp]=paired(panels[nominee],panels['V14'],(opp,),True)
    result['opponent_outcomes']={opp:dict(candidate=counts(subset(panels[nominee],(opp,))),reference=counts(subset(panels['V14'],(opp,)))) for opp in OPPONENTS}
    p=result['panel'];sol=result['solution92'];dfl=result['default'];duel=result['direct']
    result['panel_half_win_gain']=p['candidate']['half_wins']-p['reference']['half_wins']
    result['solution_half_win_gain']=sol['candidate']['half_wins']-sol['reference']['half_wins']
    # Match the fixed threshold tolerance, independently of all project helpers.
    def ge(value,threshold):return value>=threshold-1e-9
    def gt(value,threshold):return value>threshold+1e-9
    checks={
        'Local six score Δ >= +1 pp':ge(p['delta'],.01),
        'Local six score untere 95%-Grenze > 0':gt(p['low'],0.),
        'Solution_92 Δ >= -0.5 pp':ge(sol['delta'],-.005),
        'Solution_92 untere 95%-Grenze > -2.5 pp':gt(sol['low'],-.025),
        'default >= 99%':ge(dfl['score'],.99),
        'default Δ >= -1 pp':ge(dfl['delta'],-.01),
        'direkt untere 95%-Grenze > 50 %':gt(duel['low'],.5),
        'solution92_score_nonnegative':result['solution_half_win_gain']>=0,
        'solution92_strict_winrate_nonnegative':sol['candidate']['wins']>=sol['reference']['wins'],
        'default_strict_winrate_ge_0.99':dfl['candidate']['wins']*100>=99*dfl['candidate']['games']}
    result.update(checks=checks,passed=all(checks.values()),nominable=True);results={nominee:result};comparisons=[0]
    compare(summary['results'],results,'results',comparisons)
    need(summary['status']=='complete' and summary['profile']==PROFILE and summary['phase']=='confirmation' and summary['jobs']==15 and summary['games']==600 and summary['nominee']==nominee,'summary outcome/header')
    compare(summary['passed'],result['passed'],'summary.passed',comparisons)
    need('aligned_minus_control_panel' not in summary,'Confirmation must not pool a second candidate')
    expected_inputs=dict(plan=sha(BASE/'plans/confirmation_jobs.json'),provenance=sha(OUT/'provenance.json'),state=sha(OUT/'state.json'),reservation=sha(BASE/'confirmation_launch.json'),admission=sha(admission_path),historical_acceptance=ACCEPTED,seed_acceptance=pins['seed_acceptance_sha256'],csv=csv_hashes,receipts=receipt_hashes)
    compare(summary['input_sha256'],expected_inputs)
    source_check(state['source'],state['plans']);verify(state['inputs']);verify(state['protected'])
    verify(pins['files']);verify(seed_bindings);verify(selection_bindings)
    need(sha(PIN_PATH)==args.pins_sha256,'Root pin bytes changed during audit')
    need(sha(OUT/'state.json')==state_initial_hash,'state changed during independent audit')
    need(sha(OUT/'summary.json')==summary_initial_hash,'summary changed during independent audit')
    for path in [*required,OUT/'state.json',OUT/'summary.json']:bound_artifacts[str(path)]=sha(path)
    bound_artifacts[str(PIN_PATH)]=args.pins_sha256
    report=dict(schema_version=1,status='PASS',profile=PROFILE,phase='confirmation',nominee=nominee,summary_sha256=sha(OUT/'summary.json'),time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=HEAD,jobs=15,games=600,numeric_and_structural_comparisons=comparisons[0],results=results,passed=result['passed'],source=state['source'],protected=state['protected'],input_sha256=bound_artifacts,root_pins_sha256=args.pins_sha256,seed_acceptance_sha256=pins['seed_acceptance_sha256'],freshness_bindings=seed_bindings,selection_bindings=selection_bindings,selection_acceptance=pins['selection_acceptance'],script_sha256=sha(__file__),method='Independent raw CSV math and all7+3fixed gates; paired whole-map bootstrap5000 explicit PCG64(0),95% percentiles; selection nomination preserved from independently accepted evidence; no repository/model imports, tests or games.',limits='Technical data/statistics acceptance is distinct from passing performance gates and is not a promotion decision. Unadjusted intervals, only20 independent map clusters; no quantitative power guarantee. Two training starts do not establish general causal training-rule effects. No pooling, top-up, second candidate or extra maps. No TD or causal claim.')
    with OUTPUT_JSON.open('x') as stream:stream.write(json.dumps(report,indent=2,allow_nan=False)+'\n')
    text='# Independent Artillery confirmation audit\n\n**PASS** — 15 jobs / 600 complete games, source '+HEAD+'.\n\nNominee: '+str(nominee)+'. No second candidate or extra confirmation games.\n\n'
    for role,r in results.items():text+=f"- {role}: panel score {r['panel']['candidate']['half_wins']}/480 half-win units, panel delta {100*r['panel']['delta']:+.3f}pp [{100*r['panel']['low']:+.3f},{100*r['panel']['high']:+.3f}]; Solution strict {r['solution92']['candidate']['wins']}/40; default strict {r['default']['candidate']['wins']}/40; direct score {100*r['direct']['score']:.1f}%; all10 gates {r['passed']}.\n"
    for label,passed in checks.items():text+=f"- {'PASS' if passed else 'FAIL'}: {label}.\n"
    text+='\n'+report['method']+' '+report['limits']+'\n\nExact plans, CSV keys/counts/results, commands, receipts, state/source/input/model hashes and accepted nomination were checked before accepting the complete summary. Full bindings and independently recomputed confirmation statistics are in the companion JSON.\n'
    with OUTPUT_MD.open('x') as stream:stream.write(text)
    print(json.dumps({k:report[k] for k in ('status','nominee','summary_sha256','jobs','games','numeric_and_structural_comparisons')}))
if __name__=='__main__':main()
