"""The 60 fresh R2 maps are a separate control, even after R5 passes selection."""
import json
from hashlib import sha256

import pytest

from scripts import final_battle_assess as audit
from tests import test_final_battle_assess as fixtures


def test_r5_confirmation_requires_fresh_r2_and_same_environment(tmp_path, monkeypatch):
    monkeypatch.setitem(fixtures.MOVEMENT_PANELS, "own_command", (7277000, 7277100, 7277200))
    args, make = fixtures.movement_fixture(tmp_path, "own_command", model=audit.OWN_COMMAND_MODEL)
    fixtures.use_movement_confirmation(args, make)
    # A strong candidate loses one external game that the fresh control wins.
    args.candidate = make("fresh_candidate", "candidate", 7277100, 60, fixtures.EXT,
                          lambda seed, opp, seat: (seed, opp, seat) != (7277100, "kaggle3", "player_1"))
    fresh = make("fresh_r2", "control", 7277100, 60, fixtures.EXT, lambda *_: True)
    assert args.selection_control != fresh
    with pytest.raises(ValueError, match="confirmation-control"):
        audit.assess(args)
    args.confirmation_control = fresh

    # Synthetic manifests exercise source-bindings with their own digests.
    env = dict(engine=dict.fromkeys(audit.OWN_ENGINE_FILES, "e" * 64),
               python="3.13", platform="Test", machine="Test", flags={},
               versions={"numpy": "test", "scipy": "test", "torch": "test", "jax": "test",
                         "jaxlib": "test", "luxai-s3": "test"})
    for p in tmp_path.iterdir():
        mf = p / "manifest.json"
        m = json.loads(mf.read_text())
        m["environment"] = env
        mf.write_text(json.dumps(m))
        key = (m["candidate"], "kaggle3" in m["opponents"])
        digest = sha256(json.dumps(m["sources"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        monkeypatch.setitem(audit.OWN_SOURCE_DIGESTS, key, digest)
    report = audit.assess(args)
    assert report["selection"]["game_gates_pass"] and report["selection"]["selection_control"]["net_wins"] == 0
    assert report["confirmation_control"]["net_wins"] == -1
    assert not report["gates"]["external_at_least_r2"] and not report["game_gates_pass"]
    assert all(v for k, v in report["gates"].items() if k != "external_at_least_r2")

    args.confirmation_control = args.selection_control
    with pytest.raises(ValueError):
        audit.assess(args)
    args.confirmation_control = fresh
    mf = fresh / "manifest.json"
    m = json.loads(mf.read_text())
    m["environment"]["versions"]["numpy"] = "other"
    mf.write_text(json.dumps(m))
    with pytest.raises(ValueError, match="environment"):
        audit.assess(args)
