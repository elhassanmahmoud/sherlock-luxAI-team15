import json
import pytest
from scripts.residual_ensemble_run import accepted_previous, file_sha, phase_jobs


def test_acceptance_binds_actual_tensors_and_data_across_phases(tmp_path):
    weights=tmp_path/'model.pth';weights.write_bytes(b'accepted weights')
    rows=tmp_path/'games.jsonl';rows.write_text('{}\n')
    completion=tmp_path/'completion.json'
    completion.write_text(json.dumps(dict(inputs={str(weights):file_sha(weights)},
                                         outputs={str(rows):file_sha(rows)})))
    (tmp_path/'accepted.json').write_text(json.dumps(dict(completion_sha256=file_sha(completion))))
    accepted_previous(tmp_path)
    weights.write_bytes(b'changed model before confirmation')
    with pytest.raises(ValueError,match='bytes changed'): accepted_previous(tmp_path)
    weights.write_bytes(b'accepted weights')
    rows.write_text('{"replacement":true}\n')
    with pytest.raises(ValueError,match='bytes changed'): accepted_previous(tmp_path)


def test_no_implicit_phase_extension():
    assert phase_jobs('technical')==[dict(name='parity')]
    assert phase_jobs('training')==[dict(name='R61',seed=61),dict(name='R62',seed=62)]
    with pytest.raises(ValueError): phase_jobs('confirmation')


def test_signals_request_owned_cleanup_and_restore_handlers(monkeypatch,tmp_path):
    from scripts import residual_ensemble_run as run
    handlers={sig:object() for sig in (run.signal.SIGINT,run.signal.SIGTERM,run.signal.SIGHUP)}
    original=dict(handlers)
    monkeypatch.setattr(run.signal,'getsignal',lambda sig:handlers[sig])
    monkeypatch.setattr(run.signal,'signal',lambda sig,fn:handlers.__setitem__(sig,fn))
    stops=[]
    monkeypatch.setattr(run,'request_stop',lambda path:stops.append(path))
    with run.stop_signals(tmp_path/'STOP'):
        handlers[run.signal.SIGTERM](None,None)
        assert stops==[tmp_path/'STOP']
    assert handlers==original
