import json
from types import SimpleNamespace

import pytest

from scripts import combined_movement_games as study


def test_planned_rosters_and_independent_seeds():
    screen = study.blocks("screen")
    confirm = study.blocks("confirm")
    def count(arms):
        return sum(len(seeds)*len(opponents)*2 for seeds,opponents in arms.values())
    assert list(screen) == ["r7","v14","r3","r5"]
    assert count(screen) == 288 and count(confirm) == 600
    assert set(screen["r7"][0]).isdisjoint(confirm["r7"][0])
    assert set(confirm["r7"][0]).isdisjoint(confirm["direct"][0])
    assert "r3" not in confirm and "r5" not in confirm


def test_game_admission_requires_actual_strict_improvement():
    mixed = {"r3":{"hurt":2343}, "r5":{"net":17481}, "r7":{"net":17481,"hurt":2342}}
    checks = {"net_at_least_r5":True,"hurt_at_most_r3":True,"one_strict":True}
    study.verify_gate(mixed,checks,True)
    with pytest.raises(ValueError):
        study.verify_gate({**mixed,"r7":{"net":17481,"hurt":2343}},checks,True)
    with pytest.raises(ValueError):
        study.verify_gate(mixed,checks,False)


def test_confirm_uses_measured_selection_and_the_identical_receipt(monkeypatch,tmp_path):
    args = SimpleNamespace(out=tmp_path)
    directory = tmp_path/"screen"
    directory.mkdir()
    measured = {"game_gates_pass":True,"model":"m"}
    monkeypatch.setattr(study,"paired",lambda *unused: measured)
    record = directory/"assessment.json"
    record.write_text(json.dumps({**measured,"model":"different"}))
    with pytest.raises(ValueError,match="verified selection"):
        study.checked_selection(args,{})
    record.write_text(json.dumps(measured))
    assert study.checked_selection(args,{}) == measured
    measured["game_gates_pass"] = False
    record.write_text(json.dumps(measured))
    with pytest.raises(ValueError,match="verified selection"):
        study.checked_selection(args,{})


def test_unknown_game_sources_fail_before_start():
    manifest = {"sources":{},"weights":study.assess.V14_SHA,"candidate":"v14",
                "opponents":["kaggle3","solution92"],"model":None}
    with pytest.raises(ValueError,match="frozen runtime"):
        study.check_live_manifest(manifest,None)
