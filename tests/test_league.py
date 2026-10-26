"""Gegner-Liga und Training unter allen V10-Regeln (26.10.2026)."""
import hashlib
import json
from collections import Counter

import pytest

from agents.sherlock import geometry as geo
from scripts import experiment as E, protocol as P
from scripts.variants import variant_cfg
from tests.conftest import make_obs
from tests.test_early_curriculum import install_tiny_cli
from tests.test_rules_1910 import _stay_agent
from tests.test_rules_2110 import _with_nebula_estimate

V10_RELEASE = "experiments/releases/20261022_v10_baseline/agent_p0.pth"


def test_league_schedule_shares_warmup_and_pairs():
    s = P.opponent_schedule(4000, None, 0.0, "league")
    assert s[:1000] == ["default"] * 1000
    assert all(s[g] == s[g + 1] for g in range(0, 4000, 2))
    late = Counter(s[1000:])
    for name, frac in P.LEAGUE_MIX:
        assert abs(late[name] / 3000 - frac) < 0.02, name
    assert set(late) == {name for name, _ in P.LEAGUE_MIX}
    assert s == P.opponent_schedule(4000, None, 0.0, "league")


@pytest.mark.parametrize("sol,pool", [(0.7, 0.0), (None, 0.2)])
def test_league_rejects_own_shares(sol, pool):
    with pytest.raises(ValueError):
        P.opponent_schedule(4000, sol, pool, "league")


def test_cli_league_needs_existing_pool_before_model_construction(tmp_path, monkeypatch):
    def forbidden():
        pytest.fail("Pool-Fehler muss vor teuren Importen/Konstruktion abgewiesen werden")
    monkeypatch.setattr(E, "limit_threads", forbidden)
    for extra in ([], ["--pool", str(tmp_path / "fehlt.pth")]):
        with pytest.raises(SystemExit) as exc:
            E.main(["--variant", "full_rules_v10", "--games", "4000", "--opponent-plan", "league",
                    "--out", str(tmp_path / "run")] + extra)
        assert exc.value.code == 2
    assert not (tmp_path / "run").exists()


def test_cli_league_plays_pool_and_records_pool_hash(tmp_path, monkeypatch):
    install_tiny_cli(monkeypatch)
    made = []

    def opponent(label, side, self_play_path=None):
        made.append((label, self_play_path))
        return label
    monkeypatch.setattr(E, "make_opponent", opponent)
    pool = tmp_path / "v10.pth"
    pool.write_bytes(b"gewichte")
    E.main(["--variant", "full_rules_v10", "--run-seed", "73", "--games", "8", "--opponent-plan",
            "league", "--pool", str(pool), "--val-every", "0", "--no-test", "--out", str(tmp_path / "run")])
    manifest = json.loads((tmp_path / "run" / "manifest.json").read_text())
    assert manifest["opponent_schedule"] == P.opponent_schedule(8, None, 0.0, "league")
    assert manifest["opponent_schedule"][2:4] == ["pool", "pool"]
    assert manifest["pool"] == [{"path": str(pool), "sha256": hashlib.sha256(b"gewichte").hexdigest()}]
    assert ("self", str(pool)) in made
    assert manifest["curriculum"].startswith("erste 25% default, dann Liga solution92 40%")


def test_cli_league_names_pool_files_with_equal_stems_by_folder(tmp_path, monkeypatch):
    install_tiny_cli(monkeypatch)
    monkeypatch.setattr(E, "make_opponent", lambda *a, **k: object())
    pool = []
    for folder in ("v10", "v7"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "agent_p0.pth").write_bytes(folder.encode())
        pool.append(str(tmp_path / folder / "agent_p0.pth"))
    # bei 40 Spielen sind die Paare 6, 11, 14 und 19 Pool-Paare -> reihum v10, v7
    E.main(["--variant", "full_rules_v10", "--games", "40", "--opponent-plan", "league",
            "--pool", *pool, "--val-every", "0", "--no-test", "--out", str(tmp_path / "run")])
    import csv
    with (tmp_path / "run" / "train.csv").open() as f:
        labels = {row["opponent"] for row in csv.DictReader(f) if row["opponent"].startswith("pool")}
    assert labels == {"pool:v10", "pool:v7"}


def test_full_rules_v10_matches_submitted_v10_config():
    torch = pytest.importorskip("torch")
    shipped = torch.load(V10_RELEASE, map_location="cpu", weights_only=False)["cfg"]
    cfg = variant_cfg("full_rules_v10").to_dict()
    assert {k for k, v in shipped.items() if cfg.get(k) != v} == set()
    assert cfg["rules_in_training"] and cfg["rules_in_training_all"]


def test_rules_in_training_all_applies_sap_still_while_training():
    # Halter (5,5), Gegner zieht von (8,8) nach (8,7): im Training bisher trotzdem Sap
    for flag, want in ((False, geo.SAP), (True, geo.STAY)):
        a = _stay_agent(pt_sap=True, sap_still=True, rules_in_training_all=flag,
                        eps_start=0.0, eps_end=0.0)
        a.set_to_train_mode()
        a.belief.point_tiles[5, 5] = True
        a.act(9, make_obs(9, 9, units=[(5, 5, 200)], enemies=[(8, 8, 60)], relics=[(9, 9)]))
        act = a.act(10, make_obs(10, 10, units=[(5, 5, 200)], enemies=[(8, 7, 60)], relics=[(9, 9)]))
        assert int(act[0, 0]) == want, flag


def test_rules_in_training_all_applies_nebula_avoidance_while_training():
    import numpy as np
    obs = make_obs(10, 10, units=[(5, 5, 100)], relics=[(12, 12)])
    obs["map_features"]["tile_type"] = np.zeros((24, 24), np.int32)
    obs["map_features"]["tile_type"][6, 5] = 1   # schaedlicher Nebel rechts
    for flag, right_ok in ((False, True), (True, False)):
        a = _with_nebula_estimate(_stay_agent(nebula_avoid=True, rules_in_training_all=flag,
                                              eps_start=0.0, eps_end=0.0), 25)
        a.set_to_train_mode()
        a.act(10, obs)
        assert bool(a._prev_masks[0][geo.RIGHT]) == right_ok, flag
