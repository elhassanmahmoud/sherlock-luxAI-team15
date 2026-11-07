"""Six-arm ownership/queue tests: no model imports, processes or games."""
import importlib
import json
import os
import signal
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def s():
    return importlib.import_module("scripts.ensemble_diversity_supervisor")


def state(tmp_path):
    out = tmp_path / "operations"
    out.mkdir()
    return dict(root=str(tmp_path), out=str(out), prepared=str(tmp_path / "prepared"),
                python="/usr/bin/python3", jobs={}, active=[], queue=[], receipts={},
                stop_file=str(tmp_path / "STOP"), owner_pid=os.getpid())


def test_fixed_order_commands_and_atomic_ledger(s, tmp_path):
    st = state(tmp_path)
    assert s.ARMS == ("A0", "B0", "A1", "B1", "A2", "B2")
    cmd = s.training_command(st, "B2")
    assert cmd[1:4] == ["-B", "-m", "scripts.ensemble_diversity_train"]
    assert cmd[-4:] == ["--arm", "B2", "--name", "20261107_diversity_B2"]
    s.save_state(st)
    assert json.loads((Path(st['out']) / 'state.json').read_text()) == st
    assert not list(Path(st['out']).glob('*.tmp'))


@pytest.mark.parametrize('power,starting,allowed', [
    ({'ac': False, 'percent': 34}, True, False),
    ({'ac': False, 'percent': 35}, True, True),
    ({'ac': False, 'percent': 26}, False, True),
    ({'ac': False, 'percent': 25}, False, False),
    ({'ac': True, 'percent': 1}, True, True),
])
def test_power_thresholds(s, power, starting, allowed):
    if allowed:
        s.admit_power(power, starting=starting)
    else:
        with pytest.raises(ValueError):
            s.admit_power(power, starting=starting)


def test_stop_only_creates_inhibitor_and_is_idempotent(s, tmp_path):
    target = tmp_path / 'control' / 'STOP'
    s.request_stop(target)
    first = target.read_text()
    s.request_stop(target)
    assert target.read_text() == first


def test_stop_existing_inhibits_all_launches(s, tmp_path, monkeypatch):
    st = state(tmp_path)
    Path(st['stop_file']).touch()
    monkeypatch.setattr(s, 'spawn_owned', lambda *a: pytest.fail('must not launch'))
    with pytest.raises(s.StopRequested):
        s.run_queue(st)
    assert st['status'] == 'stopped'


@pytest.mark.parametrize('failure', [None, 'exit', 'receipt', 'low_power', 'stop'])
def test_queue_two_slots_no_retries_and_failure_stops_peers(s, tmp_path, monkeypatch, failure):
    st = state(tmp_path)
    launches, stopped, sampled = [], [], []
    clock = [0]
    def guard(st, owned):
        if failure == 'stop' and launches:
            raise s.StopRequested('STOP')
        if failure == 'low_power' and launches:
            s.admit_power({'ac': False, 'percent': 25}, starting=False)
        return {'ac': True, 'percent': 90}
    def spawn(st, arm, command, owned):
        launches.append(arm)
        code = 1 if failure == 'exit' and arm == 'A0' else 0
        # A0 completes first, leaving the peer live for failure cleanup.
        process = SimpleNamespace(pid=100 + len(launches),
            poll=lambda: code if arm == 'A0' or clock[0] > 0 else None)
        owned[arm] = dict(process=process, pgid=process.pid, owner_pid=os.getpid())
        st['jobs'][arm] = dict(pid=process.pid, pgid=process.pid, argv=command, returncode=None)
        sampled.append(len(owned))
    def receipt(st, arm):
        if failure == 'receipt' and arm == 'A0':
            raise ValueError('missing receipt')
        return {'arm': arm}
    monkeypatch.setattr(s, 'guard', guard)
    monkeypatch.setattr(s, 'spawn_owned', spawn)
    monkeypatch.setattr(s, 'verify_receipt', receipt)
    monkeypatch.setattr(s, 'group_exists', lambda _: False)
    monkeypatch.setattr(s, 'shutdown_owned', lambda owned, **kw: stopped.extend(owned))
    monkeypatch.setattr(s.time, 'sleep', lambda _: clock.__setitem__(0, clock[0]+1))
    if failure:
        with pytest.raises((ValueError, s.StopRequested)):
            s.run_queue(st)
        assert st['status'] in ('failed', 'stopped')
        assert len(launches) <= 2
        assert stopped
    else:
        s.run_queue(st)
        assert launches == list(s.ARMS)
        assert st['status'] == 'complete' and len(st['receipts']) == 6
    assert max(sampled) <= 2 and len(launches) == len(set(launches))


def test_queue_holds_until_power_recovers(s, tmp_path, monkeypatch):
    st = state(tmp_path)
    ticks = [0]
    calls = []
    def guard(st, owned):
        return {'ac': False, 'percent': 34 if ticks[0] == 0 else 35}
    def spawn(st, arm, command, owned):
        assert ticks[0] > 0
        calls.append(arm)
        process = SimpleNamespace(pid=100+len(calls), poll=lambda: 0)
        owned[arm] = {'process': process, 'pgid': process.pid, 'owner_pid': os.getpid()}
        st['jobs'][arm] = {'returncode': None}
    monkeypatch.setattr(s, 'guard', guard)
    monkeypatch.setattr(s, 'spawn_owned', spawn)
    monkeypatch.setattr(s, 'verify_receipt', lambda st, arm: {'arm': arm})
    monkeypatch.setattr(s, 'group_exists', lambda _: False)
    monkeypatch.setattr(s, 'shutdown_owned', lambda *a, **kw: None)
    monkeypatch.setattr(s.time, 'sleep', lambda _: ticks.__setitem__(0, ticks[0]+1))
    s.run_queue(st)
    assert calls == list(s.ARMS)


def test_shutdown_signals_all_owned_before_waiting_and_uses_grace(s, monkeypatch):
    events, now = [], [0.]
    children = {}
    for pid in (101, 102):
        p = SimpleNamespace(pid=pid, poll=lambda: None, wait=lambda timeout: 0)
        children[str(pid)] = dict(process=p, pgid=pid, owner_pid=os.getpid())
    monkeypatch.setattr(s.os, 'getpgid', lambda pid: pid)
    monkeypatch.setattr(s.os, 'killpg', lambda pid, sig: events.append((pid, sig, now[0])))
    monkeypatch.setattr(s, 'group_exists', lambda pid: now[0] < 181)
    monkeypatch.setattr(s.time, 'monotonic', lambda: now[0])
    monkeypatch.setattr(s.time, 'sleep', lambda sec: now.__setitem__(0, now[0] + sec))
    s.shutdown_owned(children, grace=180)
    assert events[:2] == [(101, signal.SIGTERM, 0), (102, signal.SIGTERM, 0)]
    assert all(t >= 180 for _, sig, t in events if sig == signal.SIGKILL)
    with pytest.raises(ValueError, match='unowned'):
        s.shutdown_owned({'bad': dict(process=children['101']['process'], pgid=101, owner_pid=-1)})


def test_receipt_missing_smoke_and_wrong_arm_rejected(s, tmp_path):
    st = state(tmp_path)
    run = tmp_path / 'experiments/runs/20261107_diversity_A0'
    run.mkdir(parents=True)
    (run/'progress.json').write_text(json.dumps(dict(status='done', eligible=True)))
    with pytest.raises((ValueError, FileNotFoundError)):
        s.verify_receipt(st, 'A0')
    for receipt in (dict(status='smoke_done', eligible=False, smoke=True, arm='A0'),
                    dict(status='done', eligible=True, smoke=False, arm='B0')):
        (run/'final_receipt.json').write_text(json.dumps(receipt))
        with pytest.raises(ValueError):
            s.verify_receipt(st, 'A0')


def test_guard_rejects_changed_source_and_protected_weights(s, tmp_path, monkeypatch):
    st = state(tmp_path)
    st.update(source={'head': 'abc'}, expected_head='abc', plans=[], protected={'x':'old'}, inputs={})
    monkeypatch.setattr(s, 'source_identity', lambda *a: {'head': 'def'})
    with pytest.raises(ValueError, match='source'):
        s.check_inputs(st)
    monkeypatch.setattr(s, 'source_identity', lambda *a: {'head': 'abc'})
    monkeypatch.setattr(s, 'hashes', lambda _: {'x':'changed'})
    with pytest.raises(ValueError, match='Protected'):
        s.check_inputs(st)


def test_valid_receipt_binds_artifact_bytes(s, tmp_path):
    st = state(tmp_path)
    run = tmp_path / 'experiments/runs/20261107_diversity_A0'
    (run/'weights').mkdir(parents=True)
    (run/'progress.json').write_text(json.dumps(dict(status='done', eligible=True)))
    receipt = dict(schema_version=1, status='done', eligible=True, smoke=False,
        arm='A0', name='20261107_diversity_A0', source_sha256=s.SOURCE_SHA,
        actual_prefill_games=120, actual_train_games=3000, actual_validation_games=128,
        learn_steps=450000, env_steps=1005360)
    for key, name in (('final_checkpoint_sha256','weights/agent.pth'),
                      ('rollouts_sha256','rollouts.jsonl'),
                      ('validation_sha256','validation_games.jsonl'),
                      ('audit_sha256','training_audit.json')):
        (run/name).write_text('evidence')
        receipt[key] = s.digest(run/name)
    (run/'final_receipt.json').write_text(json.dumps(receipt))
    assert s.verify_receipt(st, 'A0')['final_checkpoint_sha256'] == receipt['final_checkpoint_sha256']
    (run/'rollouts.jsonl').write_text('modified')
    with pytest.raises(ValueError, match='hash mismatch'):
        s.verify_receipt(st, 'A0')


def test_spawn_records_owned_group_and_thread_limits_without_process(s, tmp_path, monkeypatch):
    st = state(tmp_path)
    owned, calls = {}, []
    def popen(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(pid=4321)
    monkeypatch.setattr(s.subprocess, 'Popen', popen)
    command = s.training_command(st, 'A0')
    s.spawn_owned(st, 'A0', command, owned)
    assert owned['A0']['owner_pid'] == os.getpid()
    assert owned['A0']['pgid'] == 4321
    assert st['jobs']['A0']['argv'] == command
    assert calls[0][1]['start_new_session'] is True
    assert all(calls[0][1]['env'][key] == '1' for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    with pytest.raises(ValueError, match='Duplicate'):
        s.spawn_owned(st, 'A0', command, owned)


def test_lock_acquires_existing_cross_worktree_lock_and_external_lock(s, tmp_path, monkeypatch):
    from contextlib import contextmanager
    calls = []
    @contextmanager
    def shared(root):
        calls.append(root)
        yield
    monkeypatch.setattr(s, 'resource_lock', shared)
    with s.compute_lock(tmp_path, tmp_path/'compute.lock'):
        assert calls == [tmp_path]
        with pytest.raises(ValueError, match='lock'):
            with s.compute_lock(tmp_path, tmp_path/'compute.lock'):
                pass
