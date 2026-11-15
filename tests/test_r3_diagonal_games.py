import json
from types import SimpleNamespace
import pytest

from scripts import r3_diagonal_games as games


def test_panel_lengths_and_separation():
    screen,confirm = [games.schedule(s) for s in ("screen","confirm")]
    assert list(screen) == ["diagonal","v14","r3"]
    assert sum(2*len(x)*len(o) for x,o in screen.values()) == 224
    assert sum(2*len(x)*len(o) for x,o in confirm.values()) == 600
    assert set(screen["diagonal"][0]).isdisjoint(confirm["diagonal"][0])
    assert set(confirm["diagonal"][0]).isdisjoint(confirm["direct"][0])


def test_a_confirm_requires_the_completed_positive_selection(monkeypatch,tmp_path):
    args = SimpleNamespace(out=tmp_path)
    measured = {"game_gates_pass":True,"model":"a"}
    monkeypatch.setattr(games,"report",lambda *unused: measured)
    f=tmp_path/"screen/assessment.json"
    f.parent.mkdir()
    with pytest.raises(ValueError):
        games.selection(args)
    f.write_text(json.dumps({**measured,"model":"b"}))
    with pytest.raises(ValueError):
        games.selection(args)
    f.write_text(json.dumps(measured))
    assert games.selection(args) == measured
    measured["game_gates_pass"]=False
    f.write_text(json.dumps(measured))
    with pytest.raises(ValueError):
        games.selection(args)
