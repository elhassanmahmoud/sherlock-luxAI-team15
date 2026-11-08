"""Synthetic fixed-artifact validation; never load models or run games."""
import csv
import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import ensemble_diversity_compare as C
from scripts import ensemble_diversity_eval_supervisor as S
from scripts.early_curriculum_study import GAME_FIELDS


def test_isolated_validation_entrypoint_exists():
    assert importlib.util.find_spec('scripts.replacement_validation') is not None


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return path


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, GAME_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    V = importlib.import_module('scripts.replacement_validation')
    root = tmp_path / 'root'
    root.mkdir()
    monkeypatch.chdir(root)
    monkeypatch.setattr(V, 'ROOT', root)
    models = {}
    for role, relative in V.ROLE_PATHS.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(role.encode())
        models[role] = C.digest(path)
    monkeypatch.setattr(V, 'MODEL_HASHES', models)
    pinned = {}
    for relative in C.OPPONENT_SHA256:
        path = root / relative
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(relative.encode())
        pinned[relative] = C.digest(path)
    monkeypatch.setattr(C, 'OPPONENT_SHA256', pinned)
    # Shared supervisor checks its protected reference constant.
    monkeypatch.setattr(S, 'SOURCE_SHA', models['V14'])
    for i in (0, 1):
        path = root / f'agents/sherlock/weights/agent_p{i}.pth'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'V14')
    (root / 'Gruppe15.zip').write_bytes(b'protected archive')
    (root / V.PROTOCOL).parent.mkdir(parents=True, exist_ok=True)
    (root / V.PROTOCOL).write_text('frozen prospective synthetic protocol')
    prior = 'experiments/analysis/ensemble_diversity_20261108_compact/selection/summary.json'
    old = put(root / prior, dict(status='complete', nominee=None,
        results={'REPLACE36': {'nominable': False}}))
    origin = dict(kind='outcome_motivated_separate_validation', prior_selection_nominee=None,
        prior_diagnostic_role='REPLACE36', prior_performance_source_head='b'*40,
        prior_files_sha256={prior: C.digest(old)},
        fixed_models={r: {'path': p, 'sha256': models[r]} for r, p in V.ROLE_PATHS.items()},
        not_compact_protocol_confirmation=True, new_games_cap=3200, no_successor_or_topup=True)
    origin_path = put(root / V.ORIGIN, origin)
    monkeypatch.setattr(V, 'ORIGIN_SHA256', C.digest(origin_path))
    jobs = []
    for role in ('V14', 'REPLACE36'):
        for i, opponent in enumerate(C.OPPONENTS):
            jobs.append(dict(name=f'{role}_panel_{i}', role=role, kind='panel',
                weights=V.ROLE_PATHS[role], opponent=opponent,
                seed_list=str(V.ANALYSIS / 'seeds/panel.json'), expected_games=200, workers=1))
    jobs.append(dict(name='REPLACE36_direct', role='REPLACE36', kind='direct',
        weights=V.ROLE_PATHS['REPLACE36'], opponent=C.V14_LABEL,
        seed_list=str(V.ANALYSIS / 'seeds/direct.json'), expected_games=400, workers=1))
    put(root / jobs[0]['seed_list'], list(range(2000000, 2000100)))
    put(root / jobs[-1]['seed_list'], list(range(2100000, 2100200)))
    plan = dict(profile='replacement20261108', protocol=V.PROTOCOL, phase='confirmation',
        nominee=None, roles=V.ROLE_PATHS.copy(), total_games=3200,
        max_simultaneous_model_processes=2, opponent_sha256=pinned, jobs=jobs)
    jobs_path = put(root / V.ANALYSIS / 'jobs.json', plan)
    admission = put(root / V.ANALYSIS / 'admission.json', dict(status='admitted', roles=origin['fixed_models']))
    source_path = root / 'source.py'
    source_path.write_text('# frozen synthetic source')
    source = dict(head='a'*40, python=sys.executable, files={str(source_path): C.digest(source_path)},
        executable=sys.executable, executable_sha256=C.digest(sys.executable))
    def source_identity(*args):
        return {**source, 'files': {str(source_path): C.digest(source_path)}}
    monkeypatch.setattr(S.helpers(), 'source_identity', source_identity)
    state = V.build_state(jobs_path, admission, root / V.ANALYSIS / 'fresh', sys.executable,
        'a'*40, usage_file=root / 'usage.json', max_used_percent=100)
    return SimpleNamespace(V=V, root=root, plan=plan, jobs=jobs_path, admission=admission,
        state=state, out=Path(state['out']), origin=origin_path, prior=old)


def complete(p, *, wins=True):
    """Create real wire-schema files, no model execution or statistical mocks."""
    p.out.mkdir()
    (p.out / 'receipts').mkdir()
    S.reserve_launch(p.state)
    for name, job in p.state['job_plan'].items():
        rows = []
        for seed in job['seeds']:
            for side in C.SIDES:
                value = 1 if job['opponent'] == 'default' else .5
                if wins and job['role'] == 'REPLACE36':
                    value = 1
                row = dict.fromkeys(GAME_FIELDS, 0)
                row.update(seed=seed, side=side, opponent=job['opponent'], result=value,
                    game_win=int(value == 1), point_win=value,
                    our_wins=int(value == 1), opp_wins=int(value == 0),
                    our_points=int(value == 1), opp_points=int(value == 0),
                    point_counting_version=2, steps=303, secs=.1)
                rows.append(row)
        argv = S.job_command(p.state, name)
        write_csv(p.out / f'{name}.csv', rows)
        p.state['jobs'][name] = dict(returncode=0, argv=argv)
        p.state['receipts'][name] = S.write_receipt(p.state, name)
    p.state.update(status='complete', completed_games=3200, queue=[], active=[])
    S.helpers().save_state(p.state)
    return p


def analyze(p):
    return p.V.analyze(p.jobs, p.out, root=p.root, provenance=p.out / 'provenance.json')


def test_complete_synthetic_matrix_reports_ten_gates_without_nomination(prepared):
    report = analyze(complete(prepared))
    assert (report['games'], report['jobs'], report['nominee']) == (3200, 15, None)
    assert report['profile'] == 'replacement20261108'
    assert report['study_kind'] == 'outcome_motivated_separate_validation'
    r = report['results']['REPLACE36']
    assert r['passed'] and report['passed'] and not r['nominable']
    assert len(r['checks']) == 10
    assert r['panel']['candidate']['wins'] == 1200
    assert r['panel']['reference']['draws'] == 1200
    assert r['direct']['candidate']['games'] == 400
    assert r['direct']['low'] == 1
    assert len(r['opponent_outcomes']) == 7
    for opponent in r['opponent_outcomes'].values():
        assert 'low' in opponent and 'high' in opponent and 'delta' in opponent
        assert opponent['candidate']['games'] == 200


def test_complete_inconclusive_synthetic_matrix_does_not_pass(prepared):
    report = analyze(complete(prepared, wins=False))
    assert not report['passed']
    assert report['results']['REPLACE36']['direct']['candidate']['draws'] == 400
    assert report['nominee'] is None


@pytest.mark.parametrize('damage', ['candidate', 'role', 'direct_seed', 'budget', 'old_seed_root'])
def test_plan_refuses_changed_fixed_schedule(prepared, damage):
    p = prepared
    if damage == 'candidate':
        p.plan['roles']['REPLACE36'] = C.ROLE_PATHS['ALL42']
    elif damage == 'role':
        p.plan['jobs'][0]['role'] = 'ALL42'
    elif damage == 'direct_seed':
        put(p.root / p.plan['jobs'][-1]['seed_list'], list(range(1900000, 1900200)))
    elif damage == 'budget':
        p.plan['total_games'] = 3202
    else:
        p.plan['jobs'][0]['seed_list'] = 'experiments/analysis/ensemble_diversity_20261108_compact/seeds.json'
    with pytest.raises(ValueError):
        p.V.validate_plan(p.plan, p.root)


@pytest.mark.parametrize('damage', ['origin', 'prior', 'model', 'source', 'missing_csv',
    'duplicate_rows', 'missing_rows', 'mixed_rows', 'bad_field', 'missing_receipt',
    'receipt_head', 'receipt_model', 'receipt_command', 'receipt_seed', 'receipt_status',
    'state_partial', 'state_head', 'state_origin', 'state_protected', 'provenance_origin'])
def test_analysis_rejects_incomplete_or_changed_bound_evidence(prepared, monkeypatch, damage):
    p = complete(prepared)
    csv_path = p.out / 'REPLACE36_direct.csv'
    receipt_path = p.out / 'receipts/REPLACE36_direct.json'
    if damage in ('origin', 'prior', 'model', 'source'):
        target = {'origin': p.origin, 'prior': p.prior,
            'model': p.root / p.V.ROLE_PATHS['REPLACE36'], 'source': p.root / 'source.py'}[damage]
        target.write_text(target.read_text() + '\n')
    elif damage == 'missing_csv':
        csv_path.unlink()
    elif damage in ('duplicate_rows', 'missing_rows', 'mixed_rows', 'bad_field'):
        with csv_path.open() as f:
            rows = list(csv.DictReader(f))
        if damage == 'duplicate_rows':
            rows[-1] = rows[0]
        elif damage == 'missing_rows':
            rows.pop()
        elif damage == 'mixed_rows':
            rows[0]['seed'] = 2000000
        else:
            rows[0]['steps'] = 302
        write_csv(csv_path, rows)
        receipt = C._load_json(receipt_path)
        receipt['csv_sha256'] = C.digest(csv_path)
        put(receipt_path, receipt)
        # Rebind file hashes: row validation still must reject the data.
        p.state['inputs'].update(S.helpers().hashes([csv_path, receipt_path]))
        p.state['receipts']['REPLACE36_direct']['sha256'] = C.digest(receipt_path)
        S.helpers().save_state(p.state)
    elif damage == 'missing_receipt':
        receipt_path.unlink()
    elif damage.startswith('receipt_'):
        r = C._load_json(receipt_path)
        k, v = {'receipt_head': ('source_identity', {'head': 'b'*40}),
            'receipt_model': ('model_sha256', '0'*64), 'receipt_command': ('command', ['wrong']),
            'receipt_seed': ('seed_list_sha256', '0'*64), 'receipt_status': ('status', 'running')}[damage]
        r[k] = v
        put(receipt_path, r)
        p.state['inputs'].update(S.helpers().hashes([receipt_path]))
        p.state['receipts']['REPLACE36_direct']['sha256'] = C.digest(receipt_path)
        S.helpers().save_state(p.state)
    elif damage == 'provenance_origin':
        path = p.out / 'provenance.json'
        r = C._load_json(path)
        r['origin_sha256'] = '0'*64
        put(path, r)
    else:
        k, v = {'state_partial': ('status', 'running'), 'state_head': ('expected_head', 'b'*40),
                'state_origin': ('origin_sha256', '0'*64), 'state_protected': ('protected', {})}[damage]
        p.state[k] = v
        S.helpers().save_state(p.state)
    monkeypatch.setattr(p.V, 'validation_checks', lambda *a: pytest.fail('statistics ran before full validation'))
    with pytest.raises((ValueError, OSError)):
        analyze(p)


@pytest.mark.parametrize('relative', ['experiments/analysis/ensemble_diversity_20261108_compact/fresh',
    'experiments/analysis/ensemble_diversity_20261107/fresh', 'agents/new',
    'experiments/analysis/replacement_validation_20261108'])
def test_launch_refuses_other_studies_or_base_directory(prepared, relative):
    p = prepared
    with pytest.raises(ValueError, match='output'):
        p.V.build_state(p.jobs, p.admission, p.root / relative, sys.executable, 'a'*40,
            usage_file=p.root / 'usage.json')


def test_launch_is_single_use_and_never_reuses_partial_csv(prepared):
    p = prepared
    p.out.mkdir()
    (p.out / 'receipts').mkdir()
    S.reserve_launch(p.state)
    with pytest.raises(ValueError):
        p.V.build_state(p.jobs, p.admission, p.out.parent / 'another', sys.executable,
            'a'*40, usage_file=p.root / 'usage.json')
    name = 'REPLACE36_direct'
    (p.out / f'{name}.csv').write_text('partial')
    with pytest.raises(ValueError, match='never resume'):
        S.job_command(p.state, name)


def test_stale_quota_and_source_drift_use_shared_guard(prepared, monkeypatch):
    from datetime import datetime, timezone
    import time
    p = prepared
    put(p.root / 'usage.json', dict(timestamp=datetime.fromtimestamp(time.time()-1300,
        timezone.utc).isoformat(), usedPercent=20, ordinaryUsageAllowed=True))
    with pytest.raises(ValueError, match='stale'):
        S.guard(p.state, {})
    put(p.root / 'usage.json', dict(timestamp=datetime.now(timezone.utc).isoformat(),
        usedPercent=99, ordinaryUsageAllowed=True))
    monkeypatch.setattr(S.helpers(), 'read_power', lambda: {'ac': True, 'percent': 80})
    monkeypatch.setattr(S.helpers(), 'check_model_processes', lambda owned: None)
    assert S.guard(p.state, {})['ac']
    (p.root / 'source.py').write_text('# changed')
    with pytest.raises(ValueError, match='source/HEAD'):
        S.guard(p.state, {})


@pytest.mark.parametrize('damage', ['model', 'origin', 'admission', 'head', 'protected'])
def test_build_refuses_changed_admission_or_fixed_bytes(prepared, damage):
    p = prepared
    head = 'a'*40
    if damage == 'model':
        (p.root / p.V.ROLE_PATHS['REPLACE36']).write_bytes(b'changed')
    elif damage == 'origin':
        p.origin.write_text(p.origin.read_text() + '\n')
    elif damage == 'admission':
        data = C._load_json(p.admission)
        data['roles']['REPLACE36']['sha256'] = '0'*64
        put(p.admission, data)
    elif damage == 'head':
        head = 'b'*40
    else:
        (p.root / 'agents/sherlock/weights/agent_p1.pth').write_bytes(b'changed')
    with pytest.raises(ValueError):
        p.V.build_state(p.jobs, p.admission, p.out, sys.executable, head,
            usage_file=p.root / 'usage.json')


@pytest.mark.parametrize('damage', ['default_draws', 'solution_strict', 'direct_tie'])
def test_unchanged_strict_gates_and_direct_lower_bound(prepared, damage):
    import pandas as pd
    p = complete(prepared)
    frames = {r: pd.concat([pd.read_csv(p.out / f'{r}_panel_{i}.csv') for i in range(7)])
        for r in ('V14', 'REPLACE36')}
    direct = pd.read_csv(p.out / 'REPLACE36_direct.csv')
    def outcomes(frame, opponent, values):
        frame['result'] = frame['result'].astype(float)
        mask = frame['opponent'] == opponent
        frame.loc[mask, 'result'] = values
        frame.loc[mask, 'game_win'] = [int(v == 1) for v in values]
    if damage == 'default_draws':
        outcomes(frames['REPLACE36'], 'default', [1]*197 + [.5]*2 + [0])
        failed = 'default_strict_winrate_ge_0.99'
    elif damage == 'solution_strict':
        outcomes(frames['V14'], 'solution92', [1]*100 + [0]*100)
        outcomes(frames['REPLACE36'], 'solution92', [1]*99 + [.5]*2 + [0]*99)
        failed = 'solution92_strict_winrate_nonnegative'
    else:
        outcomes(direct, C.V14_LABEL, [.5]*400)
        failed = 'direkt untere 95%-Grenze > 50 %'
    result = p.V.validation_checks(frames['V14'], frames['REPLACE36'], direct)
    assert not result['passed']
    assert not result['checks'][failed]
    assert len(result['checks']) == 10


def test_cli_outputs_complete_report_and_refuses_partial_summary(prepared, capsys):
    p = complete(prepared)
    args = ['analyze', '--jobs', str(p.jobs), '--results', str(p.out),
        '--provenance', str(p.out / 'provenance.json'), '--root', str(p.root)]
    assert p.V.main(args) == 0
    assert json.loads(capsys.readouterr().out)['games'] == 3200
    (p.out / 'REPLACE36_direct.csv').unlink()
    summary = p.out / 'summary.json'
    with pytest.raises(SystemExit) as error:
        p.V.main(args + ['--out', str(summary)])
    assert error.value.code == 2
    assert not summary.exists()


def test_lifecycle_preserves_failed_reservation_and_cleans_wake(prepared, monkeypatch):
    from contextlib import contextmanager
    p = prepared
    events = []
    handlers = {sig: p.V.signal.getsignal(sig) for sig in
        (p.V.signal.SIGINT, p.V.signal.SIGTERM, p.V.signal.SIGHUP)}
    @contextmanager
    def lock(root):
        events.append('locked')
        try:
            yield
        finally:
            events.append('unlocked')
    wake = SimpleNamespace(pid=900, returncode=0, poll=lambda: None,
        terminate=lambda: events.append('terminated'), wait=lambda timeout: 0)
    monkeypatch.setattr(S.helpers(), 'compute_lock', lock)
    monkeypatch.setattr(S.helpers(), 'check_model_processes', lambda _: None)
    monkeypatch.setattr(S, 'guard', lambda *a: {'ac': True, 'percent': 80})
    monkeypatch.setattr(p.V.subprocess, 'Popen', lambda *a, **kw: wake)
    def failed_queue(state):
        raise ValueError('synthetic queue failure')
    monkeypatch.setattr(S, 'run_queue', failed_queue)
    with pytest.raises(ValueError, match='synthetic queue failure'):
        p.V.run_supervisor(p.jobs, p.admission, p.out, sys.executable, 'a'*40,
            usage_file=p.root / 'usage.json')
    saved = C._load_json(p.out / 'state.json')
    assert saved['status'] == 'failed'
    assert saved['wake']['returncode'] == 0
    assert Path(saved['reservation']).exists()
    assert events == ['locked', 'unlocked', 'terminated']
    assert all(p.V.signal.getsignal(sig) == handler for sig, handler in handlers.items())
    with pytest.raises(ValueError, match='already launched'):
        p.V.run_supervisor(p.jobs, p.admission, p.out.parent / 'retry', sys.executable,
            'a'*40, usage_file=p.root / 'usage.json')


def test_cli_start_reaches_single_use_lifecycle_and_respects_existing_stop(prepared, monkeypatch, capsys):
    p = prepared
    stop = p.root / 'STOP'
    monkeypatch.setattr(S, 'request_stop', lambda path=S.STOP_FILE: stop.write_text('stop'))
    assert p.V.main(['stop']) == 0
    assert stop.exists()
    with pytest.raises(S.StopRequested):
        p.V.run_supervisor(p.jobs, p.admission, p.out, sys.executable, 'a'*40,
            usage_file=p.root / 'usage.json', stop_file=stop)
    def simulate(jobs, admission, out, python, head, **kwargs):
        assert (Path(jobs), Path(admission), Path(out)) == (p.jobs, p.admission, p.out)
        assert python == sys.executable and head == 'a'*40
        assert kwargs['max_used_percent'] == 100
        return dict(status='complete', out=str(out), completed_games=3200)
    monkeypatch.setattr(p.V, 'run_supervisor', simulate)
    assert p.V.main(['start', '--jobs', str(p.jobs), '--admission', str(p.admission),
        '--out', str(p.out), '--python', sys.executable, '--expected-head', 'a'*40,
        '--usage-file', str(p.root / 'usage.json'), '--max-used-percent', '100']) == 0
    assert json.loads(capsys.readouterr().out)['games'] == 3200
