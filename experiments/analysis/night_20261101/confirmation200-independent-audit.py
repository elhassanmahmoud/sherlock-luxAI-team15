"""Independent confirmation200 audit. Pin only AFTER nomination and BEFORE jobs.
No repository imports, Torch, Lux, models, games or evaluation subprocesses.
The pin command reads only completed selection/admission metadata, never confirmation outcomes.
The audit command refuses an incomplete confirmation before reading any outcome CSV.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,subprocess
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
ROOT=Path('/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics')
D=ROOT/'experiments/analysis/night_20261101'
HEAD='aa0660183cace1e21285fde30ae61e3812136f05'
SELECTION_PHASE_SHA='54c8f8593396fc5ef035c48cd1e2f2899f660a969c2d6bd33f60c453a3b5212c'
SELECTION_FREEZE_SHA='96385f7398bcc531d6983ab7d127df200b74fb4ca54599a8b4ad6e64e51d61ab'
AMENDMENT_SHA='3319dcfa8cec9b979945cd6fe9e12fb41d5a53e2ccf7d41885450eae158e2aaf'
SUMMARY_TOOL=Path('/tmp/sherlock-night-20261101/confirmation200-summary.py')
SUMMARY_TOOL_SHA='83430c9f2b8aadede9da807d88026c2416b07b89a5d2eccbac28ce8829216c4d'
PANEL=('solution92','sol92_sq',
       'self:experiments/releases/20261022_all18_v3/agent_p0.pth',
       'self:experiments/releases/20261022_v7_Bsnpd/agent_p0.pth',
       'self:experiments/releases/20261022_v10_baseline/agent_p0.pth',
       'self:experiments/releases/20261101_v13_neb/agent_p0.pth')
REFERENCE='self:experiments/releases/20261101_v14_baseline/agent_p0.pth'
SIDES=('player_0','player_1')
CARD_SEEDS=tuple(range(832000,832200));DIRECT_SEEDS=tuple(range(833000,833200))
EPS=1e-9
FIELDS=['seed','side','opponent','result','game_win','point_win','our_wins','opp_wins',
        'our_points','opp_points','point_counting_version','wait_frac','invalid_frac',
        'greedy_masked_frac','sap_attempts','sap_hits','stack_frac','relics_found',
        'relics_seen','known_point_tiles','belief_contradictions','unit_steps','steps','secs']

def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def load_complete_csv(path, opponents, seeds):
    required = {(s, side, opp) for s in seeds for side in SIDES for opp in opponents}
    rows = {}
    with path.open(newline='') as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames == FIELDS, f'{path.name}: exact CSV schema')
        for row in reader:
            values = {k: float(row[k]) for k in FIELDS if k not in ('side', 'opponent')}
            require(all(math.isfinite(v) for v in values.values()), f'{path.name}: nonfinite value')
            require(values['seed'].is_integer(), f'{path.name}: nonintegral seed')
            key = (int(values['seed']), row['side'], row['opponent'])
            require(key in required and key not in rows, f'{path.name}: unexpected/duplicate key {key}')
            require(values['steps'] == 303 and values['point_counting_version'] == 2, f'{key}: incomplete/old game')
            a, b = values['our_wins'], values['opp_wins']
            require(a.is_integer() and b.is_integer() and min(a, b) >= 0 and a + b <= 3, f'{key}: match wins')
            result = 1.0 if a > b else 0.0 if a < b else .5
            require(values['result'] == result and values['game_win'] == int(result == 1), f'{key}: result incoherent')
            a, b = values['our_points'], values['opp_points']
            require(a.is_integer() and b.is_integer() and min(a, b) >= 0, f'{key}: invalid points')
            point_result = 1.0 if a > b else 0.0 if a < b else .5
            require(values['point_win'] == point_result, f'{key}: point result incoherent')
            require(values['secs'] >= 0, f'{key}: negative time')
            require(all(0 <= values[k] <= 1 for k in ('wait_frac', 'invalid_frac', 'greedy_masked_frac', 'stack_frac')), f'{key}: fraction')
            require(all(values[k].is_integer() and values[k] >= 0 for k in ('sap_attempts', 'sap_hits', 'relics_found', 'relics_seen', 'known_point_tiles', 'belief_contradictions', 'unit_steps')), f'{key}: invalid count')
            rows[key] = result
    require(set(rows) == required, f'{path.name}: incomplete expected key set')
    return rows


def bootstrap(values):
    # Draw card indices once per comparison. Both sides and all panel opponents
    # have already been averaged WITHIN each card; never resample game rows.
    values = np.asarray(values, dtype=float)
    indexes = np.random.default_rng(0).integers(0, len(values), size=(5000, len(values)))
    means = values[indexes].mean(axis=1)
    low, high = np.percentile(means, [2.5, 97.5])
    return float(low), float(high)


def matrix(rows, opponents, seeds):
    return np.array([[[rows[(s, side, opp)] for side in SIDES] for opp in opponents] for s in seeds])


def comparison(candidate, baseline):
    low, high = bootstrap(candidate - baseline)
    return dict(maps=len(candidate), games=2 * len(candidate), winrate=float(candidate.mean()), ref_winrate=float(baseline.mean()),
                delta=float((candidate - baseline).mean()), low=low, high=high)


def raw_counts(rows, opponent):
    values = [value for (seed, side, opp), value in rows.items() if opp == opponent]
    return dict(games=len(values), wins=values.count(1.0), draws=values.count(.5), losses=values.count(0.0))


def same_number(a, b):
    return math.isclose(float(a), float(b), rel_tol=0, abs_tol=1e-12)


def check_metadata(manifest_path,selection_audit_path):
    phase=read_json(manifest_path)
    selection=read_json(D/'selection_summary.json')
    selection_state=read_json(D/'selection_state.json')
    independent=read_json(selection_audit_path)
    require(selection_state['status']=='complete','Selection not complete')
    require(sha(D/'selection_jobs.json')==SELECTION_PHASE_SHA==selection_state['phase_sha256'],'Selection phase binding')
    require(sha(D/'selection_freeze.json')==SELECTION_FREEZE_SHA,'Original selection freeze changed')
    require(independent['accepted_data'] is True and independent['phase']=='selection','Independent selection not accepted')
    require(independent['nominee']==selection['nominee'] and independent['csv_sha256']==selection['csv_sha256'],'Independent/official selection mismatch')
    nominee=selection['nominee']
    require(nominee in ('overlap','control','discovery') and selection['candidates'][nominee]['passed'],'No single qualified nominee')
    require(selection['promotion_qualified'] is False,'Selection is not confirmation')
    require(sha(D/'confirmation_time_addendum.json')==AMENDMENT_SHA,'Time amendment changed')
    amendment=read_json(D/'confirmation_time_addendum.json')
    require(amendment['confirmation_maps']==200 and amendment['confirmation_games']==6000,'Fixed amendment sample size')
    require(amendment['confirmation_seed_range']==[832000,832199] and amendment['direct_seed_range']==[833000,833199],'Amendment seed ranges')
    require(amendment['max_nominees']==1 and amendment['allow_runner_up'] is False,'No runner up allowed')
    require(amendment['frozen_head']==HEAD,'Amendment source revision')
    require(sha(SUMMARY_TOOL)==SUMMARY_TOOL_SHA,'Reviewed external summary tool changed')
    require(phase['name']=='confirmation200' and phase['candidate']==nominee,'Wrong confirmation nominee/phase')
    require(phase['manifest_path']==str(manifest_path.resolve()),'Manifest path binding')
    require(phase['selection_sha256']==sha(D/'selection_summary.json'),'Selection summary SHA binding')
    require(phase['time_addendum_sha256']==AMENDMENT_SHA and phase['summary_tool_sha256']==SUMMARY_TOOL_SHA,'Amendment/tool manifest binding')
    require(phase['selection_freeze_sha256']==SELECTION_FREEZE_SHA,'Selection freeze manifest binding')
    require(tuple(phase['panel'])==PANEL and phase['direct_opponent']==REFERENCE,'Exact panel and V14 reference')
    require(phase['deadline_utc']==amendment['deadline_utc'],'Time amendment deadline')
    source_phase=read_json(D/'selection_jobs.json')
    require(phase['frozen_weights']==source_phase['frozen_weights'],'Exact same frozen weight inventory')
    names=['baseline',nominee,nominee+'_direct']
    require([job['name'] for job in phase['jobs']]==names,'Exactly three confirmation jobs')
    outputs=[]
    for job in phase['jobs']:
        direct=job['name'].endswith('_direct')
        args=job['args'];output=Path(args[args.index('--out')+1])
        require(output.is_absolute() and output.parent==D and output.suffix=='.csv','Output must be a declared CSV in phase directory')
        weight=('experiments/releases/20261101_v14_baseline/agent_p0.pth' if job['name']=='baseline' else f'experiments/ensembles/night_20261101_{nominee}.pth')
        expected=['--weights',weight,'--first','333000' if direct else '332000','--n','200','--workers','2',
                  '--opponents',REFERENCE if direct else ','.join((*PANEL,'default')),'--out',str(output)]
        require(args==expected,'Exact confirmation command recipe: '+job['name'])
        outputs.append(output)
    require(len(set(outputs))==3,'Distinct confirmation CSV outputs')
    return phase,selection,outputs


def pin_phase(manifest_path,selection_audit_path,out):
    # This step may run only in the gap AFTER selection nomination and BEFORE
    # run_jobs creates its confirmation journal or any confirmation CSV.
    require(not (D/'confirmation200_state.json').exists(),'Too late to pin: confirmation journal exists')
    require(not out.exists(),'Pin already exists')
    phase,selection,outputs=check_metadata(manifest_path,selection_audit_path)
    require(not any(path.exists() for path in outputs),'Too late to pin: output CSV exists')
    record=dict(kind='preconfirmation-independent-pin',pinned_at_utc=datetime.now(timezone.utc).isoformat(),
                manifest_path=str(manifest_path.resolve()),manifest_sha256=sha(manifest_path),
                selection_sha256=sha(D/'selection_summary.json'),selection_audit_path=str(selection_audit_path.resolve()),
                selection_audit_sha256=sha(selection_audit_path),selection_freeze_sha256=SELECTION_FREEZE_SHA,
                time_addendum_sha256=AMENDMENT_SHA,summary_tool_sha256=SUMMARY_TOOL_SHA,
                auditor_sha256=sha(Path(__file__)),candidate=selection['nominee'],
                jobs_not_started=True,source_head=HEAD)
    with out.open('x') as handle:json.dump(record,handle,indent=2)
    print(json.dumps(dict(pinned=True,candidate=record['candidate'],manifest_sha256=record['manifest_sha256'],pin=str(out)),indent=2))


def audit(pin_path):
    state=read_json(D/'confirmation200_state.json')
    require(state.get('status')=='complete','Confirmation incomplete; no outcome CSV may be read')
    pin=read_json(pin_path)
    require(pin['kind']=='preconfirmation-independent-pin' and pin['jobs_not_started'] is True,'Valid pre-job pin required')
    require(sha(Path(__file__))==pin['auditor_sha256'],'Independent auditor changed after pin')
    manifest_path=Path(pin['manifest_path']);selection_audit_path=Path(pin['selection_audit_path'])
    require(sha(manifest_path)==pin['manifest_sha256']==state['phase_sha256'],'Pinned confirmation phase changed')
    require(sha(selection_audit_path)==pin['selection_audit_sha256'],'Independent selection evidence changed')
    phase,selection,outputs=check_metadata(manifest_path,selection_audit_path)
    require(state['phase']==phase and selection['nominee']==pin['candidate'],'Journal/nominee binding')
    require(sha(D/'selection_summary.json')==pin['selection_sha256'],'Selected nominee summary changed after pin')
    require(datetime.fromisoformat(pin['pinned_at_utc'])<=datetime.fromisoformat(state['started_at']),'Pin was not written before confirmation')
    require(datetime.fromisoformat(state['finished_at'])<=datetime.fromisoformat(phase['deadline_utc']),'Confirmation missed deadline')
    freeze=read_json(D/'confirmation200_freeze.json')
    require(freeze==read_json(D/'selection_freeze.json'),'Selection/confirmation inputs differ')
    require(freeze['source']['head']==HEAD,'Frozen source HEAD')
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==HEAD,'Current source HEAD')
    require(sha(freeze['source']['executable'])==freeze['source']['executable_sha256'],'Interpreter changed')
    for path,expected in freeze['source']['files'].items():require(sha(path)==expected,'Frozen source changed: '+path)
    for path,expected in freeze['weights'].items():require(sha(path)==expected,'Frozen weight changed: '+path)
    require([job['name'] for job in state['jobs']]==[job['name'] for job in phase['jobs']],'Executed job names/order')
    for planned,actual,output in zip(phase['jobs'],state['jobs'],outputs):
        require(actual['command']==[freeze['source']['python'],'-B','-m','scripts.par_eval',*planned['args']],'Executed command mismatch')
        require(actual.get('exit_code')==0 and sha(output)==actual.get('output_sha256'),'Incomplete/unbound output')
    tables={};csv_hashes={}
    for job,output in zip(phase['jobs'],outputs):
        direct=job['name'].endswith('_direct')
        tables[job['name']]=load_complete_csv(output,(REFERENCE,) if direct else (*PANEL,'default'),DIRECT_SEEDS if direct else CARD_SEEDS)
        csv_hashes[output.name]=sha(output)
    require(sum(len(rows) for rows in tables.values())==6000,'Exactly 6000 complete confirmation games')
    nominee=phase['candidate'];baseline=matrix(tables['baseline'],(*PANEL,'default'),CARD_SEEDS)
    candidate=matrix(tables[nominee],(*PANEL,'default'),CARD_SEEDS)
    panel=comparison(candidate[:,:6,:].mean(axis=(1,2)),baseline[:,:6,:].mean(axis=(1,2)));panel.pop('games')
    opponents={opp:comparison(candidate[:,i,:].mean(axis=1),baseline[:,i,:].mean(axis=1)) for i,opp in enumerate((*PANEL,'default'))}
    direct_values=matrix(tables[nominee+'_direct'],(REFERENCE,),DIRECT_SEEDS).mean(axis=(1,2));low,high=bootstrap(direct_values)
    direct=dict(maps=200,games=400,winrate=float(direct_values.mean()),low=low,high=high)
    sol,default=opponents['solution92'],opponents['default']
    gates=dict(panel_delta=panel['delta']>=.01-EPS,panel_lower=panel['low']>EPS,
               solution_delta=sol['delta']>=-EPS,solution_lower=sol['low']>=-.01-EPS,
               default=default['winrate']>=.99-EPS,default_delta=default['delta']>=-.01-EPS,direct_lower=direct['low']>.5+EPS)
    counts={opp:dict(baseline=raw_counts(tables['baseline'],opp),candidate=raw_counts(tables[nominee],opp)) for opp in (*PANEL,'default')}
    entry=dict(panel=panel,direct=direct,opponents=opponents,gates=gates,counts=counts,passed=all(gates.values()))
    return dict(phase='confirmation200',independent=True,accepted_data=True,completed_games=6000,panel=PANEL,
                nominee=nominee,candidates={nominee:entry},promotion_qualified=entry['passed'],csv_sha256=csv_hashes,
                phase_sha256=pin['manifest_sha256'],pin_sha256=sha(pin_path),time_addendum_sha256=AMENDMENT_SHA,
                bootstrap=dict(unit='whole card including both sides; panel keeps all six opponents together',draws=5000,rng_seed=0,percentiles=[2.5,97.5]),
                limitation='200 rather than 300 independent maps; unchanged gates, one nominee, no runner-up.')


def compare_official(ours,path):
    official=read_json(path);name=ours['nominee'];left,right=ours['candidates'][name],official['candidates'][name]
    require(official['phase']=='confirmation200' and tuple(official['panel'])==PANEL,'Official phase/panel')
    require(official['nominee']==name and set(official['candidates'])=={name},'Official single nominee')
    require(official['promotion_qualified']==ours['promotion_qualified'] and official['completed_games']==6000,'Official verdict/total')
    require(official['csv_sha256']==ours['csv_sha256'],'Official CSV hashes')
    require(left['gates']==right['gates'] and left['passed']==right['passed'] and left['counts']==right['counts'],'Official gates/counts')
    for group in ('panel','direct'):
        for key,value in left[group].items():require(same_number(value,right[group][key]),f'Official {group}.{key}')
    for opponent in (*PANEL,'default'):
        for key,value in left['opponents'][opponent].items():require(same_number(value,right['opponents'][opponent][key]),'Official opponent metric')
        require(right['opponents'][opponent]['excluded_candidate']==0 and right['opponents'][opponent]['excluded_reference']==0,'Official excluded maps')
    return dict(path=str(path),sha256=sha(path),matched=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__.splitlines()[0]);commands=parser.add_subparsers(dest='mode',required=True)
    pin=commands.add_parser('pin');pin.add_argument('--manifest',type=Path,required=True);pin.add_argument('--selection-audit',type=Path,required=True);pin.add_argument('--out',type=Path,required=True)
    run=commands.add_parser('audit');run.add_argument('--pin',type=Path,required=True);run.add_argument('--out',type=Path,required=True);run.add_argument('--compare-summary',type=Path)
    args=parser.parse_args()
    require(not args.out.resolve().is_relative_to(ROOT),'Independent artifacts must stay outside the frozen worktree')
    if args.mode=='pin':pin_phase(args.manifest,args.selection_audit,args.out);return
    require(not args.out.exists(),'Independent audit output exists')
    report=audit(args.pin)
    if args.compare_summary:report['official_comparison']=compare_official(report,args.compare_summary)
    report['reviewed_at_utc']=datetime.now(timezone.utc).isoformat()
    with args.out.open('x') as handle:json.dump(report,handle,indent=2)
    print(json.dumps(dict(accepted_data=True,nominee=report['nominee'],promotion_qualified=report['promotion_qualified'],completed_games=6000,output=str(args.out)),indent=2))

if __name__=='__main__':main()
