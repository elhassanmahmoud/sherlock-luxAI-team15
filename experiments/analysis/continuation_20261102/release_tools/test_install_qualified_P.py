"""Synthetic filesystem/evidence contracts; no project/model imports or real release."""
from contextlib import nullcontext
import copy
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest
from unittest import mock
import zipfile

HERE=Path(__file__).resolve().parent
SCRIPT=HERE/'install_qualified_P.py'


def subject():
    if not SCRIPT.is_file():raise AssertionError('Missing conditional structured P installer')
    spec=importlib.util.spec_from_file_location('qualified_P_contract_subject',SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,allow_nan=False));return path


def ref(path):return dict(path=str(path),sha256=sha(path))


class Fixture:
    def __init__(self,base,m):
        self.base=Path(base);self.root=self.base/'primary';self.perf=self.base/'performance'
        self.root.mkdir();self.perf.mkdir();self.head='a'*40
        self.old=b'synthetic OLD V14';self.new=b'synthetic raw P frozenFalse';self.oldzip=b'synthetic old ZIP'
        self.candidate=self.perf/'P.pth';self.candidate.write_bytes(self.new)
        self.baseline=self.perf/'V14.pth';self.baseline.write_bytes(self.old)
        self.targets=m.targets(self.root)
        for label,path in self.targets.items():
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(self.oldzip if label=='zip' else self.old)
        self.runtime={}
        for name in ['main','assignment',*[f'runtime{i}' for i in range(13)]]:
            p=self.root/'agents/sherlock'/f'{name}.py';p.write_text('# synthetic runtime\n')
            self.runtime[str(p.relative_to(self.root))]=sha(p)
        self.zip=self.base/'staged_new.zip'
        with zipfile.ZipFile(self.zip,'w') as z:
            z.writestr('Gruppe15/__init__.py','')
            for name in self.runtime:z.write(self.root/name,'Gruppe15/'+Path(name).name)
            z.writestr('Gruppe15/agent.pth',b'synthetic packed P frozenTrue')
            z.writestr('Gruppe15/agents.yaml','synthetic independently audited YAML')
            z.writestr('Gruppe15/LIESMICH.txt','synthetic documentation')
        source=self.perf/'runtime.py';source.write_text('# frozen03e source')
        py13=self.perf/'python13';py13.write_bytes(b'synthetic historical interpreter')
        weights={str(self.baseline):sha(self.baseline),str(self.candidate):sha(self.candidate)}
        identity=dict(source=dict(head=m.PERFORMANCE_HEAD,files={str(source):sha(source)},
            python=str(py13),executable=str(py13),executable_sha256=sha(py13)),weights=weights)
        self.master=write(self.perf/'study_freeze.json',dict(expected_head=m.PERFORMANCE_HEAD,
            root=str(self.perf),python=str(py13),weights=dict(baseline=str(self.baseline),P=str(self.candidate)),
            frozen_weights=weights,identity=identity))
        self.summaries={};self.audits={};all_evidence={str(source):sha(source),**weights,str(self.master):sha(self.master)}
        for phase,n,first in [('selection',100,841000),('confirmation',300,842000)]:
            directory=self.perf/phase;directory.mkdir();jobs=[];done=[];csvs={}
            for label,role,opponents,seed in [('baseline_panel','baseline',(*m.PANEL,'default'),first),
                    ('P_panel','P',(*m.PANEL,'default'),first),('P_direct','P',(m.DIRECT,),first if phase=='selection' else 843000)]:
                path=directory/(label+'.csv')
                with path.open('w',newline='') as stream:
                    out=csv.DictWriter(stream,fieldnames=m.GAME_FIELDS);out.writeheader()
                    for s in range(seed,seed+n):
                        for side in m.SIDES:
                            for opp in opponents:out.writerow(dict.fromkeys(m.GAME_FIELDS,0)|dict(seed=s,side=side,opponent=opp,result=1,steps=303,point_counting_version=2))
                games=n*2*len(opponents)
                jobs.append(dict(name=label,role=role,first_seed=seed,n_maps=n,opponents=list(opponents),games=games,out=str(path)))
                jobs[-1].update(weights=str(self.baseline if role=='baseline' else self.candidate),workers=2,engine='par_eval',
                    overrides=['point_pair_swap='+('false' if role=='baseline' else 'true'),'art_move_guard='+('false' if role=='baseline' else 'true')])
                done.append(dict(name=label,status='complete',exit_code=0,out=str(path),actual_games=games,output_sha256=sha(path)))
                done[-1]['command']=m.job_command(jobs[-1],str(py13))
                csvs[str(path)]=sha(path)
            plan=write(directory/'plan.json',dict(phase=phase,candidate=None if phase=='selection' else 'P',jobs=jobs,
                study_freeze_path=str(self.master),study_freeze_sha256=sha(self.master),
                **({} if phase=='selection' else dict(selection_summary_path=str(self.summaries['selection']),
                                                    selection_summary_sha256=sha(self.summaries['selection'])))))
            state=write(directory/'state.json',dict(status='complete',phase=phase,completed_games=3000 if phase=='selection' else 9000,
                plan_sha256=sha(plan),study_freeze_sha256=sha(self.master),source_before=identity,source_after=identity,jobs=done))
            panel=dict(maps=n,delta=.10,low=.05,high=.15)
            opponents={'solution92':dict(delta=.1,low=.05,high=.15),'default':dict(winrate=1.,delta=0.,low=0.,high=0.)}
            direct=dict(maps=n,games=n*2,winrate=.65,low=.58,high=.72)
            checks=m.numeric_gates(phase,panel,opponents['solution92'],opponents['default'],direct)
            result=dict(panel=panel,opponents=opponents,direct=direct,gates=checks,passed=True)
            summary=write(directory/'summary.json',dict(status='complete',phase=phase,nominee='P',
                promotion_qualified=phase=='confirmation',completed_games=3000 if phase=='selection' else 9000,
                bootstrap_samples=5000,bootstrap_rng_seed=0,candidates={'P':result},plan_path=str(plan),plan_sha256=sha(plan),
                state_sha256=sha(state),study_freeze_sha256=sha(self.master),csv_sha256=csvs))
            self.summaries[phase]=summary
            all_evidence.update({str(p):sha(p) for p in (plan,state,summary)});all_evidence.update(csvs)
            independent=dict(result,phase=phase,status='complete',nominee='P',promotion_qualified=phase=='confirmation',
                completed_games=3000 if phase=='selection' else 9000,plan_sha256=sha(plan),state_sha256=sha(state),
                study_freeze_sha256=sha(self.master),csv_sha256=csvs)
            prior={} if phase=='selection' else {'selection':json.loads(self.audits['selection'].read_text())['results']['selection']}
            audit=write(self.base/f'{phase}_audit.json',dict(verdict='ACCEPTED',phase=phase,error=None,failed=[],
                checks_total=1,checks=[dict(name='synthetic all checks',passed=True)],
                results={**prior,phase:independent},evidence_sha256=dict(all_evidence)))
            self.audits[phase]=audit
        closure=write(self.base/'closure.json',dict(status='closed',phase='confirmation',head=m.PERFORMANCE_HEAD,
            master_sha256=sha(self.master),selection_state_sha256=sha(self.perf/'selection/state.json'),
            confirmation_state_sha256=sha(self.perf/'confirmation/state.json'),
            confirmation_summary_sha256=sha(self.summaries['confirmation']),confirmation_audit_sha256=sha(self.audits['confirmation']),
            source_before=identity,source_after=identity,model_jobs_stopped=True,
            evidence_sha256={**all_evidence,str(self.audits['confirmation']):sha(self.audits['confirmation'])}))
        py=self.base/'python310';py.write_bytes(b'synthetic interpreter, never executed')
        reports={name:write(self.base/f'{name}.json',{'synthetic':True}) for name in ('runner','zip_check','replay')}
        technical=write(self.base/'technical_qc.json',dict(verdict='ACCEPTED_P_RELEASE_QC',failed=[],warnings=[],
            candidate=ref(self.candidate),zip=ref(self.zip),embedded_weights_sha256=hashlib.sha256(b'synthetic packed P frozenTrue').hexdigest(),
            feature_dim=79,n_actions=6,components=36,all_ordered_tensors_equal=True,all_dtypes_shapes_equal=True,
            target_q_equal=True,other_checkpoint_fields_equal=True,raw_frozen=False,packed_frozen=True,
            config_diff={'frozen':[False,True]},P_flags=dict(point_pair_swap=True,art_move_guard=True),runtime_sources=self.runtime,
            python310=dict(path=str(py),sha256=sha(py),version=[3,10,99]),
            runner=dict(report=ref(reports['runner']),games=8,steps_each=303,exit_code=0),
            zip_check=dict(report=ref(reports['zip_check']),layouts=2,exit_code=0),
            replay=dict(report=ref(reports['replay']),steps=303,components=36,action_differences=0,exit_code=0),
            evidence_sha256={str(p):sha(p) for p in (self.candidate,self.zip,py,*reports.values())}))
        self.bundle=write(self.base/'bundle.json',dict(schema_version=1,kind='qualified_P_release_20261102',
            target_root=str(self.root),expected_target_head=self.head,candidate=ref(self.candidate),new_zip=ref(self.zip),
            study={**{p+'_summary':ref(v) for p,v in self.summaries.items()},
                   **{p+'_audit':ref(v) for p,v in self.audits.items()},'closure':ref(closure)},technical_qc=ref(technical)))
        self.auth=write(self.base/'authorization.json',dict(verdict='AUTHORIZED_P_INSTALL',bundle_sha256=sha(self.bundle),
            target_root=str(self.root),expected_target_head=self.head,issued_at=time.time()-10,expires_at=time.time()+300,
            readers_stopped=True,writers_stopped=True,model_jobs=0))
        self.tx=self.base/'NEW_transaction'
        self.patches=[mock.patch.object(m,'OLD_SHA',sha(self.baseline)),mock.patch.object(m,'P_SHA',sha(self.candidate)),
            mock.patch.object(m,'OLD_ZIP_SHA',sha(self.targets['zip'])),mock.patch.object(m,'git_head',return_value=self.head),
            mock.patch.object(m,'quiet_lock',side_effect=lambda root:nullcontext()),mock.patch.object(m,'no_model_jobs')]
        for patch in self.patches:patch.start()
    def close(self):
        for p in reversed(self.patches):p.stop()


class QualifiedReleaseContracts(unittest.TestCase):
    def setUp(self):
        self.m=subject();self.tmp=tempfile.TemporaryDirectory(dir=Path('/tmp').resolve());self.f=Fixture(self.tmp.name,self.m)
    def tearDown(self):
        if hasattr(self,'f'):self.f.close()
        if hasattr(self,'tmp'):self.tmp.cleanup()
    def old_unchanged(self):
        for key,p in self.f.targets.items():self.assertEqual(p.read_bytes(),self.f.oldzip if key=='zip' else self.f.old)

    def test_read_only_check_accepts_complete_structured_evidence(self):
        self.m.validate_bundle(self.f.bundle);self.old_unchanged();self.assertFalse(self.f.tx.exists())

    def test_each_numeric_gate_is_required_without_false_bool_escape(self):
        gate_inputs=[('panel','delta',.009),('panel','low',0),('solution92','delta',-.001),
                     ('solution92','low',-.011),('default','winrate',.989),('default','delta',-.011),('direct','low',.5)]
        for area,key,value in gate_inputs:
            panel={'delta':.02,'low':.01};solution={'delta':0,'low':0};default={'winrate':1,'delta':0};direct={'low':.6}
            target={'panel':panel,'solution92':solution,'default':default,'direct':direct}[area];target[key]=value
            with self.subTest(area=area,key=key):self.assertFalse(all(self.m.numeric_gates('confirmation',panel,solution,default,direct).values()))
        with self.assertRaises(ValueError):self.m.numeric_gates('confirmation',{'delta':float('nan'),'low':1},solution,default,direct)

    def test_rejects_changed_summary_csv_state_master_or_audit_bytes(self):
        paths=[self.f.summaries['confirmation'],self.f.perf/'confirmation/P_direct.csv',self.f.perf/'confirmation/state.json',
               self.f.master,self.f.audits['confirmation']]
        for p in paths:
            original=p.read_bytes();p.write_bytes(original+b' ')
            with self.subTest(path=p.name),self.assertRaises(ValueError):self.m.validate_bundle(self.f.bundle)
            p.write_bytes(original)
        self.old_unchanged()

    def test_missing_python310_or_tensor_frozen_proof_rejects_even_accepted_label(self):
        bundle=json.loads(self.f.bundle.read_text());qp=Path(bundle['technical_qc']['path']);original=json.loads(qp.read_text())
        for key,value in [('python310',dict(path='/missing',sha256='0'*64,version=[3,13,1])),
                          ('all_ordered_tensors_equal',False),('packed_frozen',False),('config_diff',{}),('components',37)]:
            data=copy.deepcopy(original);data[key]=value;write(qp,data);bundle['technical_qc']=ref(qp);write(self.f.bundle,bundle)
            with self.subTest(key=key),self.assertRaises(ValueError):self.m.validate_bundle(self.f.bundle)
        self.old_unchanged()

    def test_install_requires_explicit_switch_and_fresh_authorization(self):
        with mock.patch.object(self.m,'install') as install,mock.patch('sys.stderr',new=io.StringIO()):
            with self.assertRaises(SystemExit):self.m.main(['install','--bundle',str(self.f.bundle),'--authorization',str(self.f.auth),'--transaction',str(self.f.tx)])
            install.assert_not_called()
        auth=json.loads(self.f.auth.read_text());auth['expires_at']=0;write(self.f.auth,auth)
        with self.assertRaises(ValueError):self.m.install(self.f.bundle,self.f.auth,self.f.tx)
        self.old_unchanged()

    def test_success_installs_both_raw_P_and_new_zip_and_keeps_immutable_old_backup(self):
        result=self.m.install(self.f.bundle,self.f.auth,self.f.tx)
        self.assertEqual(result['status'],'committed')
        self.assertEqual(self.f.targets['p0'].read_bytes(),self.f.new);self.assertEqual(self.f.targets['p1'].read_bytes(),self.f.new)
        self.assertEqual(sha(self.f.targets['zip']),sha(self.f.zip))
        for key in self.f.targets:
            p=self.f.tx/'backup'/self.m.BACKUP_NAMES[key]
            self.assertEqual(p.read_bytes(),self.f.oldzip if key=='zip' else self.f.old)
            self.assertEqual(p.stat().st_mode&0o222,0)
        self.assertTrue((self.f.tx/'backup/manifest.json').is_file())

    def test_failure_at_every_publish_boundary_rolls_back_all_three(self):
        original=self.m.publish
        for failed in ('p0','p1','zip'):
            tx=self.f.base/('failed_'+failed)
            def publish(journal,entry,save):
                original(journal,entry,save)
                if entry['label']==failed:raise OSError('synthetic publish failure')
            with mock.patch.object(self.m,'publish',side_effect=publish),self.assertRaises(OSError):
                self.m.install(self.f.bundle,self.f.auth,tx)
            self.old_unchanged();self.assertEqual(json.loads((tx/'journal.json').read_text())['status'],'rolled_back')

    def test_handled_signal_after_first_switch_rolls_back_and_restores_handlers(self):
        original=self.m.publish;before=signal.getsignal(signal.SIGTERM)
        def interrupted(journal,entry,save):
            original(journal,entry,save)
            if entry['label']=='p0':signal.raise_signal(signal.SIGTERM)
        with mock.patch.object(self.m,'publish',side_effect=interrupted),self.assertRaises(InterruptedError):
            self.m.install(self.f.bundle,self.f.auth,self.f.tx)
        self.old_unchanged();self.assertEqual(signal.getsignal(signal.SIGTERM),before)

    def test_foreign_target_after_publish_is_preserved_and_conflict_recorded(self):
        original=self.m.publish;foreign=b'FOREIGN concurrent change'
        def interference(journal,entry,save):
            original(journal,entry,save)
            if entry['label']=='p0':
                replacement=self.f.root/'foreign.tmp';replacement.write_bytes(foreign);replacement.replace(self.f.targets['p0'])
                raise OSError('synthetic foreign writer')
        with mock.patch.object(self.m,'publish',side_effect=interference),self.assertRaises(OSError):
            self.m.install(self.f.bundle,self.f.auth,self.f.tx)
        self.assertEqual(self.f.targets['p0'].read_bytes(),foreign)
        journal=json.loads((self.f.tx/'journal.json').read_text());self.assertEqual(journal['status'],'rollback_conflict')
        self.assertEqual(self.f.targets['p1'].read_bytes(),self.f.old)

    def test_no_overwrite_publish_preserves_foreign_name_creation(self):
        original=self.m.move_to_holding;foreign=b'FOREIGN appeared while vacant'
        def interfere(entry,save):
            original(entry,save)
            if entry['label']=='p0':Path(entry['target']).write_bytes(foreign)
        with mock.patch.object(self.m,'move_to_holding',side_effect=interfere),self.assertRaises(FileExistsError):
            self.m.install(self.f.bundle,self.f.auth,self.f.tx)
        self.assertEqual(self.f.targets['p0'].read_bytes(),foreign)

    def test_existing_transaction_or_failed_backup_is_never_blindly_reused(self):
        self.f.tx.mkdir();(self.f.tx/'journal.json').write_text('{"foreign":true}')
        with self.assertRaises(FileExistsError):self.m.install(self.f.bundle,self.f.auth,self.f.tx)
        self.assertEqual(json.loads((self.f.tx/'journal.json').read_text()),{'foreign':True});self.old_unchanged()

    def test_pending_prepared_transaction_blocks_a_different_new_transaction(self):
        with mock.patch.object(self.m,'publish',side_effect=OSError('synthetic crash before any switch')), \
             mock.patch.object(self.m,'rollback'),self.assertRaises(OSError):
            self.m.install(self.f.bundle,self.f.auth,self.f.tx)
        self.old_unchanged()
        with self.assertRaisesRegex(ValueError,'pending'):
            self.m.install(self.f.bundle,self.f.auth,self.f.base/'other_transaction')

    def test_lock_denial_cannot_create_or_modify_transaction(self):
        with mock.patch.object(self.m,'quiet_lock',side_effect=ValueError('lock held')),self.assertRaisesRegex(ValueError,'lock held'):
            self.m.install(self.f.bundle,self.f.auth,self.f.tx)
        self.assertFalse(self.f.tx.exists());self.old_unchanged()

    def test_inline_zip_check_and_external_model_verifier_block_install_window(self):
        # Temporarily remove the fixture's no_model_jobs patch, test real snapshot parsing.
        self.f.patches[-1].stop()
        for command in ["999 /python -c from scripts.build_submission import check_battle; check_battle(...)\n",
                        '999 /python /tmp/verify_P_package.py --zip staged.zip\n']:
            with self.subTest(command=command),mock.patch.object(self.m.subprocess,'check_output',return_value=command),self.assertRaises(ValueError):
                self.m.no_model_jobs()
        self.f.patches[-1].start()

    def test_fixed_job_weights_workers_overrides_and_actual_command_are_bound(self):
        master=json.loads(self.f.master.read_text());plan=json.loads((self.f.perf/'confirmation/plan.json').read_text())
        state=json.loads((self.f.perf/'confirmation/state.json').read_text());job,done=plan['jobs'][1],state['jobs'][1]
        self.m.fixed_job(job,done,name='P_panel',role='P',seed=842000,n=300,opponents=(*self.m.PANEL,'default'),games=4200,master=master)
        for key,value in [('weights',str(self.f.baseline)),('workers',1),('overrides',['point_pair_swap=false','art_move_guard=true'])]:
            bad=copy.deepcopy(job);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.m.fixed_job(bad,done,name='P_panel',role='P',seed=842000,n=300,opponents=(*self.m.PANEL,'default'),games=4200,master=master)

    def test_recovery_before_backup_manifest_requires_only_untouched_old_targets(self):
        with mock.patch.object(self.m,'backup_and_stage',side_effect=OSError('crash before backup seal')), \
             mock.patch.object(self.m,'rollback'),self.assertRaises(OSError):
            self.m.install(self.f.bundle,self.f.auth,self.f.tx)
        journal=self.f.tx/'journal.json';auth=write(self.f.base/'early_recovery.json',dict(verdict='AUTHORIZED_P_RECOVERY',
            transaction=str(self.f.tx),journal_sha256=sha(journal),issued_at=time.time()-10,expires_at=time.time()+300,
            readers_stopped=True,writers_stopped=True,model_jobs=0))
        self.assertEqual(self.m.recover(self.f.tx,auth)['status'],'rolled_back');self.old_unchanged()

    def test_symlink_and_hardlink_targets_are_refused(self):
        p=self.f.targets['p1'];p.unlink();p.symlink_to(self.f.targets['p0'])
        with self.assertRaises(ValueError):self.m.validate_bundle(self.f.bundle)
        p.unlink();import os;os.link(self.f.targets['p0'],p)
        with self.assertRaises(ValueError):self.m.validate_bundle(self.f.bundle)

    def test_recovery_handles_owned_new_and_missing_target_without_old_guard(self):
        bundle=json.loads(self.f.bundle.read_text());qcpath=Path(bundle['technical_qc']['path']);qc=json.loads(qcpath.read_text())
        # Real preflight evidence may protect old active files. Recovery must
        # validate those historical hashes through the immutable old backup.
        qc['evidence_sha256'][str(self.f.targets['p1'])]=sha(self.f.targets['p1'])
        write(qcpath,qc);bundle['technical_qc']=ref(qcpath);write(self.f.bundle,bundle)
        auth=json.loads(self.f.auth.read_text());auth['bundle_sha256']=sha(self.f.bundle);write(self.f.auth,auth)
        # Simulate uncatchable termination by deliberately suppressing rollback once.
        original=self.m.publish
        def crash(journal,entry,save):
            original(journal,entry,save)
            if entry['label']=='p0':raise OSError('synthetic crash intent')
        with mock.patch.object(self.m,'publish',side_effect=crash),mock.patch.object(self.m,'rollback'),self.assertRaises(OSError):
            self.m.install(self.f.bundle,self.f.auth,self.f.tx)
        self.f.targets['p1'].unlink()
        journal=self.f.tx/'journal.json'
        auth=write(self.f.base/'recovery_authorization.json',dict(verdict='AUTHORIZED_P_RECOVERY',transaction=str(self.f.tx),
            journal_sha256=sha(journal),issued_at=time.time()-10,expires_at=time.time()+300,
            readers_stopped=True,writers_stopped=True,model_jobs=0))
        result=self.m.recover(self.f.tx,auth)
        self.assertEqual(result['status'],'rolled_back');self.old_unchanged()

    def test_model_or_environment_stack_never_imported(self):
        self.assertFalse(any(n=='torch' or n.startswith(('torch.','agents.','luxai_s3.')) for n in sys.modules))


if __name__=='__main__':unittest.main()
