import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from scripts import full_student_gate as gate


def test_exact_heldout_commands_and_equality_boundary():
    assert gate.correct_count(513 / 1001, 1001) == 513
    with pytest.raises(ValueError, match="fraction"):
        gate.correct_count(.51, 1001)
    before = {"mixed": 13, "expert": 7, "v14": 11}
    assert all(gate.offline_checks(before, dict(before, expert=8, v14=0)).values())
    assert not all(gate.offline_checks(before, before).values())
    assert not all(gate.offline_checks(before, dict(before, mixed=12, expert=9)).values())


def test_registered_panels():
    assert gate.panel("screen", "historical") == (range(7281000, 7281016), gate.OPPONENTS)
    assert gate.panel("screen", "plus_teacher")[1] == (*gate.OPPONENTS, "v14")
    assert gate.panel("confirm", "plus_teacher") == (range(7281100, 7281160), gate.OPPONENTS)
    assert gate.panel("direct", "plus_teacher") == (range(7281200, 7281260), ("v14",))
    for pair in (("direct", "v14"), ("confirm", "historical"), ("unknown", "v14")):
        with pytest.raises(ValueError):
            gate.panel(*pair)


def test_offline_checks_checkpoint_identity_and_fixed_input(tmp_path, monkeypatch):
    from scripts import full_student_study as fit

    monkeypatch.setattr(fit, "roster", lambda: {
        (c, n, "player_0"): ("val", "solution92") for n, c in enumerate(fit.COHORTS)})
    rows = [dict(cohort=c, seed=n, side="player_0", split="val", opponent="solution92", rows=41)
            for n, c in enumerate(fit.COHORTS)]
    manifest = dict(model=fit.MODEL, collector_sha256=fit.COLLECTOR_DIGEST, teacher=fit.TEACHER, files=rows)
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(manifest))
    sources = {"trainer": "123"}
    monkeypatch.setattr(gate, "TRAINING_SOURCES", fit.digest_json(sources))
    receipts = {}
    for arm in gate.STUDENTS:
        (tmp_path / (arm + ".pth")).write_text(arm)
        val = {c: dict(rows=41, legal_teacher_saps=2, full_order=(21 + int(c == "expert" and arm == "plus_teacher")) / 41)
               for c in fit.COHORTS}
        receipts[arm] = dict(kind="imitation", feature_dim=79, teacher=fit.TEACHER, sap_own_tile=True,
                             arch=gate.ARCH, full_policy_study=dict(study="whole_policy_20261115",
                             torch_version="test", numpy_version="test", training_device="cpu", arm=arm,
                             manifest_sha256=gate.base.digest(path), settings=fit.MODEL, validation=val,
                             training_sources_sha256=sources))
    monkeypatch.setattr(gate, "load_checkpoint", lambda p: deepcopy(receipts[p.stem]))
    result = gate.offline(path, tmp_path)
    assert result["passes"] and result["complete_orders"]["expert"] == {
        "rows": 41, "legal_teacher_saps": 2, "historical": 21, "plus_teacher": 22}
    receipts["plus_teacher"]["full_policy_study"]["arm"] = "historical"
    with pytest.raises(ValueError, match="checkpoint"):
        gate.offline(path, tmp_path)


def test_screen_accounts_for_actual_external_control(monkeypatch):
    runs = {arm: SimpleNamespace(manifest={"candidate": arm, "model": arm}, hashes={})
            for arm in ("v14", *gate.STUDENTS)}
    monkeypatch.setattr(gate, "read_run", lambda study, name, directory, receipt: runs[name])
    monkeypatch.setattr(gate, "compatible", lambda *args: None)
    monkeypatch.setattr(gate.audit, "summarize", lambda phase, stage: {"gates": {"other": True}})
    monkeypatch.setattr(gate.audit, "external_comparison", lambda *args: ({}, {"net_wins": -1}))
    result = gate.selection(gate.Path("."), {})
    assert not result["gates"]["external_at_least_historical"] and not result["game_gates_pass"]
