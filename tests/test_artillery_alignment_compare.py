"""Synthetic artifacts/results only; no model games."""
import copy
import csv
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from scripts import ensemble_diversity_compare as C
from scripts import ensemble_diversity_eval_supervisor as S
from scripts import artillery_alignment_compare as F
from scripts import artillery_alignment_eval as E
from scripts.early_curriculum_study import GAME_FIELDS


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return path


def frame(opponents,first,maps,result=.5):
    return pd.DataFrame([dict(opponent=o,seed=s,side=side,result=result,game_win=int(result==1))
        for o in opponents for s in range(first,first+maps) for side in C.SIDES])


def screen():
    reference=frame(F.SCREEN_OPPONENTS,9800000,20)
    reference.loc[reference.opponent=='default',['result','game_win']]=1
    candidate=reference.copy()
    # Four half-win units = exactly two additional score wins out of80.
    eligible=candidate.index[candidate.opponent=='sol92_sq'][:4]
    candidate.loc[eligible,['result','game_win']]=1
    return reference,candidate,frame((C.V14_LABEL,),9800100,20)


def test_integer_threshold_exact_boundary_and_one_halfwin_below():
    r,c,d=screen();out=F.selection_checks(r,c,d,name='CONTROL38')
    assert out['passed'] and out['panel_half_win_gain']==4
    c.loc[c.index[c.opponent=='sol92_sq'][0],['result','game_win']]=[.5,0]
    assert not F.selection_checks(r,c,d,name='CONTROL38')['passed']


def test_both_roles_eligible_tie_control_and_rank_order():
    r,c,d=screen()
    results={role:F.selection_checks(r,c,d,name=role) for role in F.CANDIDATES}
    assert F.choose_nominee(results)=='CONTROL38'
    results['ALIGNED38']['direct']['candidate']['half_wins']+=1
    assert F.choose_nominee(results)=='ALIGNED38'
    results['CONTROL38']['solution92']['candidate']['wins']+=1
    assert F.choose_nominee(results)=='CONTROL38'
    results['ALIGNED38']['panel']['candidate']['half_wins']+=1
    assert F.choose_nominee(results)=='ALIGNED38'
    for x in results.values(): x['passed']=False
    assert F.choose_nominee(results) is None
    with pytest.raises(ValueError): F.choose_nominee({'CONTROL38':results['CONTROL38']})


@pytest.mark.parametrize('damage',['missing','duplicate','strict','unknown'])
def test_incomplete_or_inconsistent_screen_fails(damage):
    r,c,d=screen()
    if damage=='missing': c=c.iloc[:-1]
    elif damage=='duplicate': c=pd.concat([c,c.iloc[:1]])
    elif damage=='strict': c.loc[c.index[0],'game_win']=1
    else: c.loc[c.index[0],'opponent']='unknown'
    with pytest.raises(ValueError): F.selection_checks(r,c,d,name='ALIGNED38')


def test_confirmation_is_original_seven_plus_three_local_six():
    r=frame(C.OPPONENTS,9801000,20,.5)
    r.loc[r.opponent=='default',['result','game_win']]=1
    c=frame(C.OPPONENTS,9801000,20,1.)
    d=frame((C.V14_LABEL,),9801100,20,1.)
    out=F.confirmation_checks(r,c,d,name='ALIGNED38')
    assert out['passed'] and len(out['checks'])==10 and out['panel']['candidate']['games']==240
    assert out['default']['candidate']['wins']==40
    c.loc[c.index[c.opponent=='default'][0],['result','game_win']]=[.5,0]
    assert not F.confirmation_checks(r,c,d,name='ALIGNED38')['passed']


def test_original_profiles_unchanged():
    from scripts import fog_reward_compare as old
    assert set(C.PROFILES)=={'full20261107','compact20261108'}
    assert C.NOMINABLE==('A39','B39','ALL42') and len(C.LOCAL_SIX)==6
    assert old.PROFILE=='fog_reward_20261108' and old.CANDIDATES==('CONTROL38','NEUTRAL38')
    assert old.COHORTS['confirmation']==(7701000,40,7701100,40) and old.TOTALS['confirmation']==1200


def test_stop_path_resolves_system_tmp_only(tmp_path,monkeypatch):
    assert not E.STOP_FILE.parent.parent.is_symlink()
    link=tmp_path/'child';link.symlink_to(tmp_path/'elsewhere')
    with pytest.raises(ValueError): E.checked_stop(link/'STOP')


def test_stop_rejects_noncanonical_path(tmp_path,monkeypatch):
    canonical=tmp_path/'canonical'/'STOP'
    monkeypatch.setattr(E,'STOP_FILE',canonical)
    assert E.checked_stop(canonical)==canonical
    with pytest.raises(ValueError,match='canonical Artillery STOP'):
        E.checked_stop(tmp_path/'other'/'STOP')


def test_canonical_stop_blocks_start_and_cannot_be_bypassed(tmp_path,monkeypatch):
    canonical=tmp_path/'canonical'/'STOP';canonical.parent.mkdir();canonical.write_text('STOP')
    monkeypatch.setattr(E,'STOP_FILE',canonical)
    def forbidden(*args,**kwargs): raise AssertionError('STOP must block before admission or launch')
    monkeypatch.setattr(E,'build_state',forbidden)
    args=('unused jobs','unused admission','unused output',sys.executable,'b'*40)
    with pytest.raises(S.StopRequested,match='STOP inhibits start'):
        E.run_supervisor(*args,usage_file=tmp_path/'usage.json',stop_file=canonical)
    with pytest.raises(ValueError,match='canonical Artillery STOP'):
        E.run_supervisor(*args,usage_file=tmp_path/'usage.json',stop_file=tmp_path/'other'/'STOP')


def test_ac_wrapper_preserves_shared_guard_and_requires_ac(monkeypatch):
    original=S.guard
    monkeypatch.setattr(E,'_shared_guard',lambda state,owned:dict(ac=False,percent=100))
    with pytest.raises(ValueError): E.guard({}, {})
    assert S.guard is original


@pytest.fixture
def artifacts(tmp_path,monkeypatch):
    """Tiny real Q checkpoints and complete accepted byte inventories, no games."""
    import torch
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.model import QNet
    from scripts.night_train_pilot import tensor_sha256
    root=tmp_path/'root';root.mkdir();monkeypatch.chdir(root)
    monkeypatch.setattr(F,'ROOT',root);monkeypatch.setattr(E,'ROOT',root)
    monkeypatch.setattr(E,'STOP_FILE',root/'STOP')
    cfg=AgentConfig(hidden=4).to_dict()
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(0);q=QNet(79,6,hidden=4,dueling=cfg['dueling']).state_dict()
    states=[{k:v.clone()+i*.01 for k,v in q.items()} for i in range(36)]
    base=dict(q=states[0],target_q=states[0],cfg=cfg,feature_dim=79,n_actions=6,
              ensemble=states[1:],ensemble_dims=[79]*35,env_steps=60000,learn_steps=0)
    original=root/F.ROLE_PATHS['V14'];original.parent.mkdir(parents=True);torch.save(base,original)
    source_sha=C.digest(original);monkeypatch.setattr(F,'SOURCE_SHA',source_sha)
    protected={}
    for index in (0,1):
        path=root/f'agents/sherlock/weights/agent_p{index}.pth';path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(original.read_bytes());protected[str(path)]=source_sha
    archive=root/'Gruppe15.zip';archive.write_bytes(b'synthetic zip');protected[str(archive)]=C.digest(archive)
    prepared=root/'experiments/runs/prepared';prepared.mkdir(parents=True)
    historical_source=dict(head=F.TRAINING_HEAD,files={'historical/source.py':'f'*64},python='historical-python')
    manifest_data=dict(source_sha256=source_sha,source_config=cfg,
        pins=dict(source=historical_source,protected=protected),arms={})
    files={};arms={};receipts={}
    for arm in F.ARMS:
        directory=root/f'experiments/runs/{arm}';directory.mkdir(parents=True)
        config=dict(cfg,frozen=False,lr=5e-5,rules_in_training=True,rules_in_training_all=True,
            rescue_in_training=True,fog_unknown_reward_neutral=False,art_splash_in_training=arm.startswith('aligned'))
        final={k:v+(.5+int(arm[-2:])*.01) for k,v in q.items()}
        cp=dict(q=final,target_q=final,cfg=config,feature_dim=79,n_actions=6,ensemble=[],ensemble_dims=[],
                env_steps=193320,learn_steps=60000)
        checkpoint=directory/'weights/agent.pth';checkpoint.parent.mkdir();torch.save(cp,checkpoint)
        receipt=dict(schema_version=1,status='done',eligible=False,arm=arm,source_sha256=source_sha,
            component_index=18,run_seed=int(arm[-2:]),**F.RECEIPT_COUNTS,config=config,
            initial_tensor_sha256=tensor_sha256(states[18]),prepared=str(prepared),
            pins=manifest_data['pins'],artifacts={'weights/agent.pth':C.digest(checkpoint)})
        arm_files={str(checkpoint):C.digest(checkpoint)}
        for name in F.RECEIPT_FILES[1:]:
            path=directory/name;path.write_text('synthetic '+name);receipt['artifacts'][name]=C.digest(path)
            arm_files[str(path)]=C.digest(path)
        rp=put(directory/'final_receipt.json',receipt);arm_files[str(rp)]=C.digest(rp)
        files.update(arm_files)
        arms[arm]=dict(receipt_path=str(rp),checkpoint_path=str(checkpoint),
            final_checkpoint_sha256=C.digest(checkpoint),receipt_sha256=C.digest(rp),counts=F.COUNTS.copy(),files=arm_files)
        receipts[arm]={str(rp):C.digest(rp)}
        initial=prepared/arm/'weights/agent.pth';initial.parent.mkdir(parents=True)
        initial.write_bytes(b'initial '+arm.encode())
        entry=dict(config=config,component_index=18,run_seed=int(arm[-2:]),
            tensor_sha256=receipt['initial_tensor_sha256'],weights_sha256=C.digest(initial))
        manifest_data['arms'][arm]=entry
        local=put(prepared/arm/'manifest.json',dict(variant=F.PROFILE,base_variant=F.PROFILE,
            train_games=0,arm=arm,**entry))
        files.update({str(initial):C.digest(initial),str(local):C.digest(local)})
    manifest=put(prepared/'manifest.json',manifest_data);files[str(manifest)]=C.digest(manifest)
    launch=put(prepared/'supervisor_launch.json',{'synthetic':'single launch'})
    files[str(launch)]=C.digest(launch)
    pairs={};pair_values={}
    for seed in (43,44):
        value=dict(status='matched',eligible=False,run_seed=seed,
            proof_sha256={arm:{str(Path(arms[arm]['receipt_path']).parent/'prefill_proof.json'):
                files[str(Path(arms[arm]['receipt_path']).parent/'prefill_proof.json')]}
                for arm in (f'control{seed}',f'aligned{seed}')})
        path=put(root/F.ANALYSIS/f'paired_prefill_{seed}.json',value)
        files[str(path)]=C.digest(path);pairs[str(seed)]=dict(path=str(path),sha256=C.digest(path))
        pair_values[str(seed)]=value
    state=put(root/F.ANALYSIS/'training_state.json',dict(status='done',eligible=False,queue=[],active=[],
        source=historical_source,prepared=str(prepared),protected=protected,
        jobs={a:dict(returncode=0,finished_at=1) for a in F.ARMS},receipts=receipts,paired_prefill=pair_values))
    independent=put(root/F.ANALYSIS/'data_audit.json',dict(status='PASS_DATA_ONLY',source_head=F.TRAINING_HEAD))
    root_validation=put(root/F.ANALYSIS/'root_validation.json',dict(status='PASS',training_head=F.TRAINING_HEAD,
        validator='scripts.artillery_alignment_study.validate_final_receipt',arms={a:dict(status='PASS',
            receipt_sha256=arms[a]['receipt_sha256'],env_steps=193320,learn_steps=60000) for a in F.ARMS}))
    for path in (state,independent,root_validation): files[str(path)]=C.digest(path)
    accepted=dict(schema_version=1,status='PASS',eligible_for_comparison=True,training_head=F.TRAINING_HEAD,
        root=str(root),source=historical_source,protected=protected,prepared=str(prepared),
        prepared_manifest_sha256=C.digest(manifest),arms=arms,files=files,totals=F.TRAINING_TOTALS.copy(),
        supervisor=dict(path=str(state),sha256=C.digest(state)),paired_prefill=pairs,
        independent_audit=dict(path=str(independent),sha256=C.digest(independent)),
        root_validation=dict(path=str(root_validation),sha256=C.digest(root_validation)))
    acceptance=put(root/F.ACCEPTANCE,accepted)
    monkeypatch.setattr(F,'ACCEPTANCE_SHA256',C.digest(acceptance))
    # Bind fake opponent bytes independently; old module profile tables stay intact.
    pins={}
    for relative in C.OPPONENT_SHA256:
        path=root/relative
        if not path.exists(): path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(relative.encode())
        pins[relative]=C.digest(path)
    monkeypatch.setattr(C,'OPPONENT_SHA256',pins)
    for relative in (F.SPEC,F.PROTOCOL,F.SIZING):
        path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixed synthetic spec')
    return SimpleNamespace(root=root,accepted=accepted,acceptance=acceptance,base=base,source_sha=source_sha)


def test_exclusive_exact_38_build_reload_and_historical_head_transition(artifacts,monkeypatch):
    # Current HEAD is deliberately never queried by historical assembly.
    import torch
    record=F.build_candidates(root=artifacts.root)
    assert record['reload_verified'] and record['historical_source']['head']==F.TRAINING_HEAD
    for role in F.CANDIDATES:
        cp=torch.load(artifacts.root/F.ROLE_PATHS[role],weights_only=True)
        assert len(cp['ensemble'])==37 and cp['cfg']['art_splash_in_training'] is False
        assert record['roles'][role]['members'][:36]==record['roles']['V14']['members']
    admitted,bound=F.validate_admission(artifacts.root/F.CANDIDATE_DIR/'admission.json',root=artifacts.root)
    assert admitted==record and str(artifacts.acceptance) in bound
    with pytest.raises(ValueError): F.build_candidates(root=artifacts.root)


@pytest.mark.parametrize('damage',['acceptance','raw','receipt','checkpoint','missing_binding'])
def test_historical_changed_or_incomplete_bindings_fail(artifacts,monkeypatch,damage):
    a=artifacts.accepted
    if damage=='raw': Path(a['arms']['aligned43']['receipt_path']).parent.joinpath('train.csv').write_text('changed')
    elif damage=='checkpoint': Path(a['arms']['control44']['checkpoint_path']).write_bytes(b'changed')
    elif damage=='receipt': Path(a['arms']['control43']['receipt_path']).write_text('{}')
    elif damage=='missing_binding':
        a['files'].pop(a['arms']['aligned44']['receipt_path']);put(artifacts.acceptance,a)
        monkeypatch.setattr(F,'ACCEPTANCE_SHA256',C.digest(artifacts.acceptance))
    else: artifacts.acceptance.write_text('{}')
    with pytest.raises(ValueError): F.historical_acceptance(artifacts.root)
    assert not (artifacts.root/F.CANDIDATE_DIR).exists()


def test_historical_rebases_new_checkout_without_old_runtime(artifacts,tmp_path):
    import shutil
    portable=tmp_path/'portable';shutil.copytree(artifacts.root,portable)
    accepted,bound=F.historical_acceptance(portable)
    assert accepted['source']['python']=='historical-python'
    assert all(Path(p).is_relative_to(portable) for p in bound)
    assert str(portable/F.ACCEPTANCE) in bound


@pytest.mark.parametrize('damage',['order','flag','nan','member'])
def test_candidate_revalidation_rejects_semantic_tampering(artifacts,damage):
    import torch
    F.build_candidates(root=artifacts.root)
    admission=artifacts.root/F.CANDIDATE_DIR/'admission.json';record=C._load_json(admission)
    path=artifacts.root/F.ROLE_PATHS['ALIGNED38'];cp=torch.load(path,weights_only=True)
    if damage=='order': cp['ensemble'][-1],cp['ensemble'][-2]=cp['ensemble'][-2],cp['ensemble'][-1]
    elif damage=='flag': cp['cfg']['art_splash_in_training']=True
    elif damage=='nan': next(iter(cp['q'].values())).view(-1)[0]=float('nan')
    else: cp['ensemble'].pop()
    torch.save(cp,path)
    record['roles']['ALIGNED38']['sha256']=C.digest(path);put(admission,record)
    with pytest.raises((ValueError,RuntimeError)): F.validate_admission(admission,root=artifacts.root)


def test_plan_exact_440_and600_and_seed_blocks(artifacts):
    F.prepare_plans(root=artifacts.root)
    for phase,nominee,total,n_jobs in (('selection',None,440,11),('confirmation','CONTROL38',600,15)):
        plan=F.make_plan(phase,nominee)
        jobs=F.validate_plan(plan,artifacts.root,phase=phase,nominee=nominee)
        assert len(jobs)==n_jobs and sum(j['expected_games'] for j in jobs)==total
        assert len([j for j in jobs if j['kind']=='direct'])==(2 if phase=='selection' else 1)
    with pytest.raises(ValueError): F.prepare_plans(root=artifacts.root)


@pytest.mark.parametrize('damage',['duplicate','role','workers','bool_worker','count','nominee','seed'])
def test_plan_contract_tampering_fails(artifacts,damage):
    F.prepare_plans(root=artifacts.root);plan=F.make_plan('selection')
    if damage=='duplicate': plan['jobs'][-1]=plan['jobs'][0].copy()
    elif damage=='role': plan['roles']['CONTROL38']=plan['roles']['ALIGNED38']
    elif damage=='workers': plan['jobs'][0]['workers']=2
    elif damage=='bool_worker': plan['jobs'][0]['workers']=True
    elif damage=='count': plan['total_games']=441
    elif damage=='nominee': plan['nominee']='CONTROL38'
    else: put(artifacts.root/plan['jobs'][0]['seed_list'],list(range(9800001,9800021)))
    with pytest.raises(ValueError): F.validate_plan(plan,artifacts.root,phase='selection')


@pytest.fixture
def phase_ready(artifacts,monkeypatch):
    F.build_candidates(root=artifacts.root);F.prepare_plans(root=artifacts.root)
    raw=put(artifacts.root/F.ANALYSIS/'operations/seed_raw.json',{'status':'completed','limitations':['synthetic']})
    audit=put(artifacts.root/F.ANALYSIS/'operations/seed_audit.json',dict(status='PASS',
        no_observed_conflicts=True,limitations=['synthetic'],
        raw_audit=dict(path=str(raw.relative_to(artifacts.root)),sha256=C.digest(raw))))
    seed_acceptance=put(artifacts.root/F.SEED_ACCEPTANCE,dict(schema_version=1,status='PASS',profile=F.PROFILE,
        cohorts=F.seed_cohorts(),audit=dict(path=str(audit.relative_to(artifacts.root)),sha256=C.digest(audit))))
    monkeypatch.setattr(F,'SEED_ACCEPTANCE_SHA256',C.digest(seed_acceptance))
    source_file=artifacts.root/'phase_source.py';source_file.write_text('# current phase source')
    def identity(*args):
        return dict(head='b'*40,python=sys.executable,executable=sys.executable,
                    executable_sha256=C.digest(sys.executable),files={str(source_file):C.digest(source_file)})
    monkeypatch.setattr(S.helpers(),'source_identity',identity)
    return SimpleNamespace(**vars(artifacts),source_file=source_file)


def make_state(p,phase='selection',nominee=None,acceptance=None):
    jobs=p.root/F.ANALYSIS/'plans'/f'{phase}_jobs.json'
    if not jobs.exists(): put(jobs,F.make_plan(phase,nominee))
    return E.build_state(jobs,p.root/F.CANDIDATE_DIR/'admission.json',p.root/F.ANALYSIS/phase,
        sys.executable,'b'*40,usage_file=p.root/'usage.json',stop_file=p.root/'STOP',
        phase=phase,nominee=nominee,selection_acceptance=acceptance)


def complete_state(state,*,winner=True):
    out=Path(state['out']);out.mkdir();(out/'receipts').mkdir()
    S.reserve_launch(state)
    for name,job in state['job_plan'].items():
        rows=[]
        for seed in job['seeds']:
            for side in C.SIDES:
                result=1 if job['opponent']=='default' or (winner and job['role']!='V14') else .5
                row=dict.fromkeys(GAME_FIELDS,0)
                row.update(seed=seed,side=side,opponent=job['opponent'],result=result,
                    game_win=int(result==1),point_win=result,our_wins=int(result==1),opp_wins=int(result==0),
                    our_points=int(result==1),opp_points=int(result==0),point_counting_version=2,steps=303,secs=.1)
                rows.append(row)
        command=S.job_command(state,name)
        with (out/f'{name}.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,GAME_FIELDS);writer.writeheader();writer.writerows(rows)
        state['jobs'][name]=dict(returncode=0,argv=command)
        state['receipts'][name]=S.write_receipt(state,name)
    state.update(status='complete',completed_games=state['expected_games'],queue=[],active=[])
    S.helpers().save_state(state)
    return state


def analyze_state(p,state):
    return E.analyze(state['jobs_path'],state['out'],root=p.root,
        provenance=Path(state['out'])/'provenance.json',phase=state['phase'],nominee=state['nominee'])


def test_full_440_receipt_matrix_nomination_and_optional600(phase_ready):
    p=phase_ready
    selected=complete_state(make_state(p))
    summary=analyze_state(p,selected)
    assert (summary['games'],summary['jobs'],summary['nominee'])==(440,11,'CONTROL38')
    assert set(summary['results'])==set(F.CANDIDATES)
    assert summary['aligned_minus_control_panel']['delta']==0
    summary_path=put(Path(selected['out'])/'summary.json',summary)
    accepted=put(p.root/F.ANALYSIS/'selection_acceptance.json',dict(status='PASS',profile=F.PROFILE,
        summary_sha256=C.digest(summary_path),nominee='CONTROL38'))
    plan=E.prepare_confirmation(accepted,root=p.root)
    assert plan['nominee']=='CONTROL38' and plan['total_games']==600
    with pytest.raises((ValueError,FileExistsError)): E.prepare_confirmation(accepted,root=p.root)
    confirmed=complete_state(make_state(p,'confirmation','CONTROL38',accepted))
    report=analyze_state(p,confirmed)
    assert report['passed'] and (report['games'],report['jobs'])==(600,15)
    assert len(report['results']['CONTROL38']['checks'])==10


def test_no_eligible_nominee_no_confirmation(phase_ready):
    p=phase_ready;state=complete_state(make_state(p),winner=False)
    summary=analyze_state(p,state);assert summary['nominee'] is None
    path=put(Path(state['out'])/'summary.json',summary)
    acceptance=put(p.root/'rejected_nominee.json',dict(status='PASS',profile=F.PROFILE,
        summary_sha256=C.digest(path),nominee='ALIGNED38'))
    with pytest.raises(ValueError): E.prepare_confirmation(acceptance,root=p.root)
    assert not (p.root/F.ANALYSIS/'plans/confirmation_jobs.json').exists()


@pytest.mark.parametrize('damage',['missing_csv','extra_csv','duplicate_csv','receipt','command','state','source','plan'])
def test_full_analysis_fails_closed_before_stats(phase_ready,monkeypatch,damage):
    p=phase_ready;state=complete_state(make_state(p));out=Path(state['out'])
    name=next(iter(state['job_plan']))
    if damage=='missing_csv': (out/f'{name}.csv').unlink()
    elif damage=='extra_csv': (out/'extra.csv').write_text('unexpected')
    elif damage=='duplicate_csv':
        path=out/f'{name}.csv';lines=path.read_text().splitlines();path.write_text('\n'.join(lines+[lines[1]])+'\n')
    elif damage=='receipt':
        path=out/'receipts'/f'{name}.json';receipt=C._load_json(path);receipt['rows']-=1;put(path,receipt)
    elif damage=='command':
        path=out/'receipts'/f'{name}.json';receipt=C._load_json(path);receipt['command'][-1]='other.csv';put(path,receipt)
    elif damage=='state': state['completed_games']=439;S.helpers().save_state(state)
    elif damage=='source': p.source_file.write_text('# changed')
    else:
        path=Path(state['jobs_path']);plan=C._load_json(path);plan['jobs'][0]['workers']=2;put(path,plan)
    called=[]
    monkeypatch.setattr(F,'selection_checks',lambda *a,**kw:called.append(True))
    with pytest.raises((ValueError,OSError)): analyze_state(p,state)
    assert not called


def test_source_hash_stop_quota_ac_guards(phase_ready,monkeypatch):
    from datetime import datetime,timezone
    state=make_state(phase_ready)
    put(Path(state['usage_file']),dict(timestamp=datetime.now(timezone.utc).isoformat(),usedPercent=99.,ordinaryUsageAllowed=True))
    h=S.helpers();monkeypatch.setattr(h,'read_power',lambda:dict(ac=True,percent=100))
    monkeypatch.setattr(h,'check_model_processes',lambda owned:None)
    E.guard(state,{})
    Path(state['stop_file']).write_text('STOP')
    with pytest.raises(S.StopRequested): E.guard(state,{})
    Path(state['stop_file']).unlink()
    put(Path(state['usage_file']),dict(timestamp=datetime.now(timezone.utc).isoformat(),usedPercent=100.,ordinaryUsageAllowed=True))
    with pytest.raises(ValueError): E.guard(state,{})
    put(Path(state['usage_file']),dict(timestamp='1970-01-01T00:00:00Z',usedPercent=1.,ordinaryUsageAllowed=True))
    with pytest.raises(ValueError): E.guard(state,{})


def test_confirmation_wrong_nominee_and_no_resume(phase_ready):
    p=phase_ready;state=complete_state(make_state(p));summary=analyze_state(p,state)
    path=put(Path(state['out'])/'summary.json',summary)
    accepted=put(p.root/'acceptance.json',dict(status='PASS',profile=F.PROFILE,
        summary_sha256=C.digest(path),nominee='CONTROL38'))
    with pytest.raises(ValueError): make_state(p,'confirmation','ALIGNED38',accepted)
    # Selection single-use reservation prevents adopting any partial/new output.
    with pytest.raises(ValueError): make_state(p)


def test_new_guard_detects_foreign_probe_with_owned_group_exemption(monkeypatch):
    monkeypatch.setattr(E,'_shared_guard',lambda *a:dict(ac=True,percent=100))
    snapshot='91 91 python -m scripts.holder_rollout_probe\n92 92 python -m scripts.par_eval\n'
    monkeypatch.setattr(E.subprocess,'check_output',lambda *a,**kw:snapshot)
    with pytest.raises(ValueError): E.guard({}, {'model':{'pgid':92}})
    E.guard({}, {'probe':{'pgid':91},'model':{'pgid':92}})


def test_confirmation_analyze_requires_all_selection_bindings(phase_ready):
    p=phase_ready;selection=complete_state(make_state(p));summary=analyze_state(p,selection)
    path=put(Path(selection['out'])/'summary.json',summary)
    accepted=put(p.root/'accepted_selection.json',dict(status='PASS',profile=F.PROFILE,
        summary_sha256=C.digest(path),nominee='CONTROL38'))
    confirmation=complete_state(make_state(p,'confirmation','CONTROL38',accepted))
    assert analyze_state(p,confirmation)['passed']
    confirmation['inputs'].pop(str(accepted));S.helpers().save_state(confirmation)
    with pytest.raises(ValueError): analyze_state(p,confirmation)


def test_third_owned_worker_is_rejected_without_spawning(tmp_path,monkeypatch):
    def forbidden(*a,**kw): raise AssertionError('No process may be launched')
    monkeypatch.setattr(S.helpers().subprocess,'Popen',forbidden)
    with pytest.raises(ValueError):
        S.spawn_owned(dict(jobs={},out=str(tmp_path)),'third',['python','unused'],{'one':{},'two':{}})


def test_assembly_rechecks_archived_source_before_admission(artifacts,monkeypatch):
    import torch
    save=torch.save
    def mutate_source(value,destination,*args,**kwargs):
        result=save(value,destination,*args,**kwargs)
        if str(getattr(destination,'name',destination)).endswith('CONTROL38.pth'):
            (artifacts.root/F.ROLE_PATHS['V14']).write_bytes(b'changed source during assembly')
        return result
    monkeypatch.setattr(torch,'save',mutate_source)
    with pytest.raises(ValueError): F.build_candidates(root=artifacts.root)
    assert not (artifacts.root/F.CANDIDATE_DIR/'admission.json').exists()


@pytest.mark.parametrize('entrypoint',['api','cli'])
def test_analysis_relative_and_absolute_paths_match(phase_ready,monkeypatch,entrypoint):
    p=phase_ready
    state=complete_state(make_state(p))
    jobs=Path(state['jobs_path']);results=Path(state['out'])

    def analyze_paths(relative):
        selected_jobs=jobs.relative_to(p.root) if relative else jobs
        selected_results=results.relative_to(p.root) if relative else results
        if entrypoint=='api':
            return E.analyze(selected_jobs,selected_results,root=p.root,
                provenance=selected_results/'provenance.json')
        # Exercise the real argparse entrypoint against the synthetic checkout.
        monkeypatch.setitem(E.analyze.__kwdefaults__,'root',p.root)
        output=p.root/f'summary_{relative}.json'
        monkeypatch.setattr(sys,'argv',['artillery_alignment_eval','analyze','--jobs',str(selected_jobs),
            '--results',str(selected_results),'--out',str(output)])
        E.main()
        return C._load_json(output)

    assert analyze_paths(True)==analyze_paths(False)


def test_unpinned_historical_acceptance_blocks_build(artifacts,monkeypatch):
    monkeypatch.setattr(F,'ACCEPTANCE_SHA256',None)
    with pytest.raises(ValueError,match='not yet pinned'): F.build_candidates(root=artifacts.root)
    assert not (artifacts.root/F.CANDIDATE_DIR).exists()


@pytest.mark.parametrize('damage',['buffer','events','prepared_weights','prepared_manifest','pair',
    'supervisor','independent_audit','root_validation'])
def test_historical_requires_complete_raw_and_acceptance_inventory(artifacts,monkeypatch,damage):
    accepted=artifacts.accepted
    if damage in ('buffer','events'):
        name='weights/agent.buffer.npz' if damage=='buffer' else 'prefill_events.jsonl'
        path=str(Path(accepted['arms']['aligned44']['receipt_path']).parent/name)
        accepted['arms']['aligned44']['files'].pop(path)
        accepted['files'].pop(path)
    elif damage.startswith('prepared'):
        name='weights/agent.pth' if damage=='prepared_weights' else 'manifest.json'
        accepted['files'].pop(str(Path(accepted['prepared'])/'control44'/name))
    elif damage=='pair': accepted['paired_prefill'].pop('44')
    else: accepted.pop(damage)
    put(artifacts.acceptance,accepted);monkeypatch.setattr(F,'ACCEPTANCE_SHA256',C.digest(artifacts.acceptance))
    with pytest.raises(ValueError): F.historical_acceptance(artifacts.root)


def test_receipts_stay_ineligible_and_exact_artifact_schema(artifacts):
    accepted,_=F.historical_acceptance(artifacts.root)
    for arm in F.ARMS:
        receipt=C._load_json(Path(accepted['arms'][arm]['receipt_path']))
        assert receipt['eligible'] is False and set(receipt['artifacts'])==set(F.RECEIPT_FILES)
        assert 'smoke' not in receipt and 'final_checkpoint_sha256' not in receipt


@pytest.mark.parametrize('damage',['receipt_eligible','receipt_config','pair_status','supervisor_active',
    'root_counter','root_receipt'])
def test_historical_rejects_resigned_but_inconsistent_metadata(artifacts,monkeypatch,damage):
    accepted=artifacts.accepted
    if damage.startswith('receipt'):
        item=accepted['arms']['aligned43'];path=Path(item['receipt_path']);value=C._load_json(path)
        if damage=='receipt_eligible': value['eligible']=True
        else: value['config']['art_splash_in_training']=False
        put(path,value);item['receipt_sha256']=C.digest(path);item['files'][str(path)]=C.digest(path)
    elif damage=='pair_status':
        item=accepted['paired_prefill']['43'];path=Path(item['path']);value=C._load_json(path)
        value['status']='unmatched';put(path,value);item['sha256']=C.digest(path)
    elif damage=='supervisor_active':
        item=accepted['supervisor'];path=Path(item['path']);value=C._load_json(path)
        value['active']=['control43'];put(path,value);item['sha256']=C.digest(path)
    else:
        item=accepted['root_validation'];path=Path(item['path']);value=C._load_json(path)
        value['arms']['control43']['env_steps' if damage=='root_counter' else 'receipt_sha256']=0
        put(path,value);item['sha256']=C.digest(path)
    accepted['files'][str(path)]=C.digest(path)
    put(artifacts.acceptance,accepted);monkeypatch.setattr(F,'ACCEPTANCE_SHA256',C.digest(artifacts.acceptance))
    with pytest.raises(ValueError): F.historical_acceptance(artifacts.root)


def test_real_start_blocked_until_seed_acceptance_pinned(phase_ready,monkeypatch):
    monkeypatch.setattr(F,'SEED_ACCEPTANCE_SHA256',None)
    with pytest.raises(ValueError,match='not yet pinned'): make_state(phase_ready)


@pytest.mark.parametrize('damage',['seed_acceptance','raw_audit','other_phase_seed','sizing'])
def test_both_phase_inputs_frozen_from_selection(phase_ready,damage):
    p=phase_ready;state=make_state(p)
    relative={'seed_acceptance':F.SEED_ACCEPTANCE,
        'raw_audit':F.ANALYSIS/'operations/seed_raw.json',
        'other_phase_seed':F.ANALYSIS/'plans/confirmation_direct.json','sizing':F.SIZING}[damage]
    (p.root/relative).write_text('changed')
    with pytest.raises((ValueError,OSError)): S.check_inputs(state)


def test_confirmation_requires_only_fixed_nominee_and_20_maps(artifacts):
    F.prepare_plans(root=artifacts.root)
    plan=F.make_plan('confirmation','ALIGNED38')
    assert set(plan['roles'])=={'V14','ALIGNED38'}
    assert F.cohort('confirmation')==(9801000,20,9801100,20)
    assert {j['opponent'] for j in plan['jobs'] if j['kind']=='panel'}==set(C.LOCAL_SIX)|{'default'}
    plan['roles']['CONTROL38']=F.ROLE_PATHS['CONTROL38']
    with pytest.raises(ValueError): F.validate_plan(plan,artifacts.root,phase='confirmation',nominee='ALIGNED38')


@pytest.mark.parametrize('damage',['cohort','audit_status','conflict','limitations','raw_hash'])
def test_seed_admission_rejects_invalid_audit_even_if_acceptance_resigned(phase_ready,monkeypatch,damage):
    p=phase_ready;path=p.root/F.SEED_ACCEPTANCE;accepted=C._load_json(path)
    if damage=='cohort': accepted['cohorts']['confirmation_panel'][0]=9800999
    else:
        audit_path=p.root/accepted['audit']['path'];audit=C._load_json(audit_path)
        if damage=='audit_status': audit['status']='PASS_PARTIAL'
        elif damage=='conflict': audit['no_observed_conflicts']=False
        elif damage=='limitations': audit.pop('limitations')
        else: audit['raw_audit']['sha256']='f'*64
        put(audit_path,audit);accepted['audit']['sha256']=C.digest(audit_path)
    put(path,accepted);monkeypatch.setattr(F,'SEED_ACCEPTANCE_SHA256',C.digest(path))
    with pytest.raises(ValueError): F.freshness_acceptance(p.root)
