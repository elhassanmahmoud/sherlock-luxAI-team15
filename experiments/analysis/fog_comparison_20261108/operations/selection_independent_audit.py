"""Independent data-only Fog screening audit; no repository or model imports."""
import argparse,csv,datetime,hashlib,json,math,os,subprocess
from pathlib import Path
ROOT=Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
BASE=ROOT/'experiments/analysis/fog_comparison_20261108';OUT=BASE/'selection'
HEAD='c096e4f0d1720900ee04d5acaa7faaef465fcded';PROFILE='fog_reward_20261108'
ACCEPTED='8cfea7a7e28cdd010de1ef9693334f028ce8e3b52716805c5d91b6b0ec528e7b'
ROLE_PATHS={'V14':'experiments/releases/20261101_v14_baseline/agent_p0.pth','CONTROL38':'experiments/candidates/fog_reward_20261108/CONTROL38.pth','NEUTRAL38':'experiments/candidates/fog_reward_20261108/NEUTRAL38.pth'}
MODEL_HASHES={'V14':'98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8','CONTROL38':'efa81d3bbf5065c71d8106e016921d2640d368722546f0b8a40086173e95c947','NEUTRAL38':'b928d4a8a66403526b77c656d4373f3fe6e31ffe9e7cc9f6d4b64e63d4566a39'}
OPPONENT_HASHES={'experiments/releases/20261022_all18_v3/agent_p0.pth':'aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935','experiments/releases/20261022_v7_Bsnpd/agent_p0.pth':'c394acba84f7a298f8f1e6107328d8e6ce151b367a28997b059aa82fc8a895e6','experiments/releases/20261022_v10_baseline/agent_p0.pth':'03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67','experiments/releases/20261101_v13_neb/agent_p0.pth':'6d00b6c52366a613eed3b7b5b6f9c3c088802716a85c30fe192c46c57bdd8e62','experiments/releases/20261101_v14_baseline/agent_p0.pth':MODEL_HASHES['V14']}
FIELDS=('seed','side','opponent','result','game_win','point_win','our_wins','opp_wins','our_points','opp_points','point_counting_version','wait_frac','invalid_frac','greedy_masked_frac','sap_attempts','sap_hits','stack_frac','relics_found','relics_seen','known_point_tiles','belief_contradictions','unit_steps','steps','secs')
SIDES=('player_0','player_1');PANEL=('solution92','sol92_sq');OPPONENTS=PANEL+('default',);CANDIDATES=('CONTROL38','NEUTRAL38');DIRECT='self:'+ROLE_PATHS['V14']
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
def expected_jobs():
    jobs=[]
    for role in ROLE_PATHS:
        for i,opp in enumerate(OPPONENTS):jobs.append(dict(name=f'{role}_panel_{i}',role=role,kind='panel',weights=ROLE_PATHS[role],opponent=opp,seed_list='experiments/analysis/fog_comparison_20261108/plans/selection_panel.json',expected_games=40,workers=1))
    for role in CANDIDATES:jobs.append(dict(name=f'{role}_direct',role=role,kind='direct',weights=ROLE_PATHS[role],opponent=DIRECT,seed_list='experiments/analysis/fog_comparison_20261108/plans/selection_direct.json',expected_games=40,workers=1))
    return jobs

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--completed-authorized',action='store_true');args=parser.parse_args()
    need(args.completed_authorized,'Await explicit root completed signal; no interim outcomes audited')
    state=read(OUT/'state.json');provenance=read(OUT/'provenance.json');launch=read(BASE/'selection_launch.json');plan=read(BASE/'plans/selection_jobs.json');summary=read(OUT/'summary.json');summary_initial_hash=sha(OUT/'summary.json')
    need(state['status']=='complete' and state['completed_games']==state['expected_games']==440 and not state['active'] and not state['queue'],'selection not completely ended')
    snapshot=subprocess.check_output(['ps','-axo','pid=,pgid=,args='],text=True);groups={j['pgid'] for j in state['jobs'].values()}
    need(not any(int(p[1]) in groups for line in snapshot.splitlines() if len(p:=line.split(None,2))==3),'owned group still alive')
    for d in (state,provenance,launch):need(d['profile']==PROFILE and d['phase']=='selection','phase identity')
    need(state['nominee'] is provenance['nominee'] is None and state['selection_acceptance'] is None,'unexpected prior nomination')
    need(state['source']==provenance['source_identity']==launch['source_identity'] and state['provenance']==provenance and state['expected_head']==HEAD and state['python']==state['source']['python'],'source/launch/provenance identity')
    need(state['root']==str(ROOT) and state['out']==launch['out']==str(OUT) and state['jobs_path']==launch['jobs_path']==str(BASE/'plans/selection_jobs.json') and state['reservation']==str(BASE/'selection_launch.json'),'exact paths')
    source_check(state['source'],state['plans']);verify(state['inputs']);verify(state['protected'])
    need(state['model_sha256']==provenance['model_sha256']==MODEL_HASHES,'exact candidate hashes')
    for role,path in ROLE_PATHS.items():need(sha(ROOT/path)==MODEL_HASHES[role],'model byte binding '+role)
    need(state['protected'][str(ROOT/'Gruppe15.zip')]=='88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6','protected ZIP')
    for i in (0,1):need(state['protected'][str(ROOT/f'agents/sherlock/weights/agent_p{i}.pth')]==MODEL_HASHES['V14'],'protected V14')
    acceptance_path=ROOT/'experiments/analysis/fog_reward_20261108/operations/historical_training_acceptance.json';need(sha(acceptance_path)==ACCEPTED and state['acceptance_sha256']==provenance['acceptance_sha256']==ACCEPTED,'historical training acceptance')
    admission_path=ROOT/'experiments/candidates/fog_reward_20261108/admission.json';admission=read(admission_path)
    need(state['admission_path']==str(admission_path) and state['admission_sha256']==sha(admission_path) and admission['acceptance_sha256']==ACCEPTED,'admission binding')
    need(admission['inference_config']['fog_unknown_reward_neutral'] is False and admission['reload_verified'] is True,'admitted inference config')
    for role in ROLE_PATHS:need(admission['roles'][role]['path']==ROLE_PATHS[role] and admission['roles'][role]['sha256']==MODEL_HASHES[role] and len(admission['roles'][role]['members'])==(36 if role=='V14' else 38),'admitted exact role '+role)
    jobs=expected_jobs();expected_plan=dict(profile=PROFILE,protocol='docs/superpowers/plans/2026-11-08-fog-comparison.md',phase='selection',nominee=None,roles=ROLE_PATHS,total_games=440,max_simultaneous_model_processes=2,opponent_sha256=OPPONENT_HASHES,jobs=jobs)
    compare(plan,expected_plan)
    for path,digest in OPPONENT_HASHES.items():need(sha(ROOT/path)==digest,'opponent '+path)
    need(read(BASE/'plans/selection_panel.json')==list(range(7700000,7700020)) and read(BASE/'plans/selection_direct.json')==list(range(7700100,7700120)),'selection seed lists')
    need(read(BASE/'plans/confirmation_panel.json')==list(range(7701000,7701040)) and read(BASE/'plans/confirmation_direct.json')==list(range(7701100,7701140)),'reserved confirmation seed lists')
    names={j['name'] for j in jobs};need(set(state['jobs'])==set(state['receipts'])==names,'exact job membership')
    need({p.stem for p in OUT.glob('*.csv')}=={p.stem for p in (OUT/'receipts').glob('*.json')}==names,'exact artifact membership')
    expected_job_plan={j['name']:{**j,'seeds':list(range(7700100 if j['kind']=='direct' else 7700000,7700120 if j['kind']=='direct' else 7700020))} for j in jobs}
    compare(state['job_plan'],expected_job_plan)
    all_rows={};csv_hashes={};receipt_hashes={};bound_artifacts={}
    required=[BASE/'plans/selection_jobs.json',OUT/'provenance.json',BASE/'selection_launch.json',admission_path,acceptance_path,*map(Path,admission['input_sha256']),*(ROOT/p for p in ROLE_PATHS.values()),*(ROOT/p for p in OPPONENT_HASHES),*(ROOT/p for p in state['plans'])]
    for job in jobs:
        name=job['name'];csv_path=OUT/f'{name}.csv';rp=OUT/'receipts'/f'{name}.json';receipt=read(rp);csv_hashes[name]=sha(csv_path);receipt_hashes[name]=sha(rp);required.extend((csv_path,rp,ROOT/job['seed_list']))
        expected=dict(profile=PROFILE,status='complete',returncode=0,job_name=name,phase='selection',role=job['role'],opponent=job['opponent'],weights=job['weights'],model_sha256=MODEL_HASHES[job['role']],seed_list_sha256=sha(ROOT/job['seed_list']),csv_sha256=csv_hashes[name],rows=40,source_identity=state['source'],opponent_sha256=OPPONENT_HASHES)
        command=[state['python'],'-B','-m','scripts.par_eval','--weights',str(ROOT/job['weights']),'--seed-list',str(ROOT/job['seed_list']),'--workers','1','--opponents',job['opponent'],'--out',str(csv_path)];expected['command']=command
        compare(receipt,expected);need(state['jobs'][name]['returncode']==0 and state['jobs'][name]['argv']==command,'actual job command/exit')
        compare(state['receipts'][name],dict(path=str(rp),sha256=receipt_hashes[name],rows=40))
        start=7700100 if job['kind']=='direct' else 7700000;keys={(job['opponent'],seed,side) for seed in range(start,start+20) for side in SIDES};seen=set();normalized=[]
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
    # Only after all 440 raw rows and bindings pass, compute independent statistics.
    import numpy as np
    def interval(values):
        values=np.asarray(values,dtype=float);rng=np.random.Generator(np.random.PCG64(0));means=rng.choice(values,size=(5000,len(values)),replace=True).mean(axis=1)
        return [float(x) for x in np.percentile(means,[2.5,97.5])]
    def paired(candidate,reference,opponents,per_opponent=False):
        c=subset(candidate,opponents);r=subset(reference,opponents)
        cm={s:sum(x['result'] for x in c if x['seed']==s)/(2*len(opponents)) for s in range(7700000,7700020)}
        rm={s:sum(x['result'] for x in r if x['seed']==s)/(2*len(opponents)) for s in range(7700000,7700020)}
        cv=np.asarray(list(cm.values()));rv=np.asarray(list(rm.values()));diff=cv-rv;lo,hi=interval(diff)
        out=dict(maps=20,score=float(cv.mean()),ref_score=float(rv.mean()),delta=float(diff.mean()),low=lo,high=hi)
        if per_opponent:out.update(opponent=opponents[0],games=40,excluded_candidate=0,excluded_reference=0)
        return dict(out,candidate=counts(c),reference=counts(r))
    def direct(rows):
        values=[sum(r['result'] for r in rows if r['seed']==s)/2 for s in range(7700100,7700120)];lo,hi=interval(values)
        return dict(maps=20,games=40,score=float(np.mean(values)),low=lo,high=hi,candidate=counts(rows))
    panels={role:[r for j in jobs if j['role']==role and j['kind']=='panel' for r in all_rows[j['name']]] for role in ROLE_PATHS};results={}
    for role in CANDIDATES:
        result=dict(panel=paired(panels[role],panels['V14'],PANEL),direct=direct(all_rows[role+'_direct']))
        for opp in OPPONENTS:result[opp]=paired(panels[role],panels['V14'],(opp,),True)
        gain=result['panel']['candidate']['half_wins']-result['panel']['reference']['half_wins'];sol=result['solution92']
        checks=dict(panel_half_win_gain_ge4=gain>=4,solution_score_nonnegative=sol['candidate']['half_wins']>=sol['reference']['half_wins'],solution_strict_wins_nonnegative=sol['candidate']['wins']>=sol['reference']['wins'],default40_strict_wins=result['default']['candidate']['wins']==40,direct_score_ge50pct=result['direct']['candidate']['half_wins']>=40)
        result.update(panel_half_win_gain=gain,checks=checks,passed=all(checks.values()),nominable=True);results[role]=result
    eligible=[r for r in CANDIDATES if results[r]['passed']];nominee=min(eligible,key=lambda r:(-results[r]['panel']['candidate']['half_wins'],-results[r]['solution92']['candidate']['wins'],-results[r]['direct']['candidate']['half_wins'],CANDIDATES.index(r))) if eligible else None
    nc=paired(panels['NEUTRAL38'],panels['CONTROL38'],PANEL);comparisons=[0]
    compare(summary['results'],results,'results',comparisons);compare(summary['neutral_minus_control_panel'],nc,'neutral_minus_control',comparisons)
    need(summary['status']=='complete' and summary['profile']==PROFILE and summary['phase']=='selection' and summary['jobs']==11 and summary['games']==440 and summary['nominee']==nominee,'summary outcome/header')
    expected_inputs=dict(plan=sha(BASE/'plans/selection_jobs.json'),provenance=sha(OUT/'provenance.json'),state=sha(OUT/'state.json'),reservation=sha(BASE/'selection_launch.json'),admission=sha(admission_path),historical_acceptance=ACCEPTED,csv=csv_hashes,receipts=receipt_hashes)
    compare(summary['input_sha256'],expected_inputs)
    source_check(state['source'],state['plans']);verify(state['inputs']);verify(state['protected'])
    need(sha(OUT/'summary.json')==summary_initial_hash,'summary changed during independent audit')
    for path in [*required,OUT/'state.json',OUT/'summary.json']:bound_artifacts[str(path)]=sha(path)
    report=dict(schema_version=1,status='PASS',profile=PROFILE,phase='selection',nominee=nominee,summary_sha256=sha(OUT/'summary.json'),time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=HEAD,jobs=11,games=440,numeric_and_structural_comparisons=comparisons[0],results=results,neutral_minus_control_panel=nc,source=state['source'],protected=state['protected'],input_sha256=bound_artifacts,script_sha256=sha(__file__),method='Independent raw CSV math; integer half-win nomination; paired whole-map bootstrap5000 explicit PCG64(0),95% percentiles; no repository/model imports, tests or games.',limits='Technical data/statistics acceptance; screening is exploratory, not promotion. Two training starts do not establish general causal reward effects. No pooling or extra maps.')
    Path('/tmp/sherlock-fog-selection-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    text='# Independent Fog selection audit\n\n**PASS** — 11 jobs / 440 complete games, source '+HEAD+'.\n\nNominee: '+str(nominee)+'. No second candidate or extra selection games.\n\n'
    for role,r in results.items():text+=f"- {role}: panel score {r['panel']['candidate']['half_wins']}/160 half-win units, panel delta {100*r['panel']['delta']:+.3f}pp [{100*r['panel']['low']:+.3f},{100*r['panel']['high']:+.3f}]; Solution strict {r['solution92']['candidate']['wins']}/40; default strict {r['default']['candidate']['wins']}/40; direct score {100*r['direct']['score']:.1f}%; gates {r['passed']}.\n"
    text+='\nN−C panel delta '+f"{100*nc['delta']:+.3f}pp [{100*nc['low']:+.3f},{100*nc['high']:+.3f}]"+'.\n\n'+report['method']+' '+report['limits']+'\n\nExact plans, CSV keys/counts/results, commands, receipts, state/source/input/model hashes and nomination were independently checked before accepting the complete summary. Full bindings and recomputed statistics are in the companion JSON.\n'
    Path('/tmp/sherlock-fog-selection-audit.md').write_text(text)
    print(json.dumps({k:report[k] for k in ('status','nominee','summary_sha256','jobs','games','numeric_and_structural_comparisons')}))
if __name__=='__main__':main()
