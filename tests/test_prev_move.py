"""Letzte eigene Bewegung als Schüler-Eingabe (v6, 16.11.2026): gleiche Werte im Training und im Spiel."""
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.prev_move import N_PREV, MoveTracker, archive_onehot
from scripts import imitate


def test_archive_rules_match_start_gaps_and_jumps():
    # Bild 0..2: Match-Schritte 1..3; Bild 3: neues Match (Schritt 1); Bild 4: Schritt 3 (Schritt 2 fehlt).
    step = np.array([0, 0, 1, 1, 2, 3, 4])
    uid = np.array([0, 1, 0, 1, 0, 0, 0])
    pos = np.array([[5, 5], [9, 9], [6, 5], [9, 9], [6, 4], [6, 5], [6, 6]])
    mstep = np.array([1, 1, 2, 2, 3, 1, 3])
    got = archive_onehot(step, uid, pos, mstep)
    assert got.shape == (7, N_PREV)
    assert not got[[0, 1]].any()                 # Matchbeginn: kein Vorgänger
    assert got[2, geo.RIGHT] == 1                # (5,5) -> (6,5)
    assert got[3, geo.STAY] == 1                 # stehen geblieben
    assert got[4, geo.UP] == 1                   # (6,5) -> (6,4)
    assert not got[5].any()                      # neues Match
    assert not got[6].any()                      # ausgelassener Zug
    assert got.sum() == 3
    jump = archive_onehot(np.array([0, 1]), np.array([3, 3]), np.array([[0, 0], [7, 7]]), np.array([4, 5]))
    assert not jump.any()                        # Sprung (z. B. neue Einheit im selben Platz)


def test_tracker_equals_archive_and_follows_actions_on_real_game():
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.imitation_agent import ImitationAgent, canonical_action, featurize
    from scripts.common import RandomAgent

    env = LuxAIS3GymEnv(numpy_output=True)
    cfg = imitate.v14_cfg()
    sides = ("player_0", "player_1")
    players = {s: RandomAgent(s) for s in sides}
    for k, s in enumerate(sides):
        players[s].rng = np.random.default_rng(10 + k)
    shadows = {s: ImitationAgent(s, agent_path=None, cfg=cfg, train=False, seed=0, prev_move_input=True)
               for s in sides}
    for s in sides:
        shadows[s].set_to_eval_mode()
        shadows[s].new_game(s)
    obs, info = env.reset(seed=4242)
    for p in list(players.values()) + list(shadows.values()):
        p.set_env_cfg(info["params"])
    recs = {s: imitate.SideRecord() for s in sides}
    live_feats = {s: [] for s in sides}
    expected_dir = {s: [] for s in sides}
    last_world = {s: None for s in sides}
    done, step = False, 0
    while not done:
        acts = {s: np.asarray(players[s].act(step, obs[s])) for s in sides}
        for s in sides:
            fz = featurize(shadows[s], obs[s])
            if fz is None:
                continue
            ctx, ids, feats, masks, _, planes, pos = fz
            extra = shadows[s].prev_move_features(ctx, ids, pos)
            recs[s].add(fz, acts[s], shadows[s].belief.mirrored)
            for k, u in enumerate(ids):
                if ctx["ally_ene"][u] >= 0:
                    live_feats[s].append(extra[k])
                    prior = last_world[s]
                    expected_dir[s].append(-1 if prior is None else
                                           canonical_action(prior[u], shadows[s].belief.mirrored)[0])
        for s in sides:
            last_world[s] = acts[s]
        obs, _, term, trunc, info = env.step(acts)
        done = bool(np.asarray(term["player_0"])) or bool(np.asarray(trunc["player_0"]))
        step += 1
    env.close()
    for s in sides:
        r = recs[s]
        archived = imitate.prev_move_columns(dict(step=np.array(r.step), uid=np.array(r.uid),
                                                  pos=np.array(r.pos), mstep=np.array(r.mstep)))
        played = np.array(live_feats[s], dtype=np.float16)
        np.testing.assert_array_equal(archived, played, err_msg=s)
        moved = played[:, 1:].any(axis=1)
        assert moved.mean() > 0.2 and played.any(axis=1).mean() > 0.6
        # Eine gemessene Bewegung entspricht dem kanonischen Befehl des Zugs davor (prüft die Spiegelung).
        cls = played.argmax(axis=1)
        exp = np.array(expected_dir[s])
        assert np.array_equal(cls[moved], exp[moved]), s


def _archive(path, seed, frames=21, width=5, height=5):
    rng = np.random.default_rng(seed)
    n = frames * 2
    feats = rng.normal(0, .1, (n, 79)).astype(np.float16)
    feats[:, 2], feats[:, 7], feats[:, 8] = .5, .6, 3 / 7
    step = np.repeat(np.arange(frames, dtype=np.int32), 2)
    uid = np.tile(np.array([0, 1], np.int8), frames)
    x = (np.arange(n) // 2 % 3 + 1).astype(np.int8)          # Unit 0 und 1 wandern nach rechts
    pos = np.stack([x, np.full(n, 2, np.int8)], axis=1)
    mstep = (step % 20 + 1).astype(np.int16)                 # Bild 20 beginnt ein neues Match
    act = (np.arange(n) % 5).astype(np.int8)
    np.savez_compressed(path, planes=rng.integers(-70, 70, (frames, 16, width, height), dtype=np.int8),
                        step=step, pos=pos, uid=uid, feats=feats, mask=np.ones((n, 6), bool), act=act,
                        sdx=np.zeros(n, np.int8), sdy=np.zeros(n, np.int8), mstep=mstep)


def test_storage_paths_agree_and_warm_start_keeps_outputs(tmp_path, monkeypatch):
    from scripts.imitation_storage import store_partition

    source = tmp_path / "games"
    source.mkdir()
    for s in range(4):
        _archive(source / f"g{s}_player_0_v14.npz", s)
    parts = imitate.partition_files([source], .25, 4)
    ordinary = imitate.concat_games(parts["train"], prev_move=True)
    _, stored = store_partition(parts["train"], tmp_path / "train", imitate.prepare_labels,
                                extra_feats=imitate.prev_move_columns)
    assert ordinary[1]["feats"].shape[1] == 79 + N_PREV
    np.testing.assert_array_equal(stored["feats"], ordinary[1]["feats"])
    assert ordinary[1]["feats"][:, 79:].sum() > 0

    monkeypatch.setattr(imitate, "v14_cfg", lambda: SimpleNamespace(to_dict=lambda: {}))
    torch.set_num_threads(1)
    base = dict(data=[str(source)], epochs=1, mb=16, ch=4, blocks=1, hidden=12, val_frac=.25, seed=4,
                device="cpu", lr=3e-4, sap_weight=.5)
    imitate.cmd_train(SimpleNamespace(**base, out=str(tmp_path / "parent.pth")))
    parent = torch.load(tmp_path / "parent.pth", map_location="cpu", weights_only=False)
    assert parent["arch"]["feat_dim"] == 79 and not parent.get("prev_move_input")
    for low in (False, True):
        out = tmp_path / f"child_{low}.pth"
        imitate.cmd_train(SimpleNamespace(**base, out=str(out), prev_move=True, init=str(tmp_path / "parent.pth"),
                                          low_memory=low))
        child = torch.load(out, map_location="cpu", weights_only=False)
        assert child["prev_move_input"] is True and child["arch"]["feat_dim"] == 79 + N_PREV
        log = out.with_suffix(".log").read_text()
        assert "Unit-Eingang erweitert" in log


def test_widen_keeps_outputs_and_agent_uses_tracker(tmp_path):
    from agents.sherlock.imitation_net import ImitationNet

    torch.manual_seed(0)
    net = ImitationNet(feat_dim=79, ch=4, blocks=1, hidden=12)
    check = imitate.widen_unit_input(net, N_PREV)
    assert check["new_feat_dim"] == 84 and max(check["max_abs_by_head"]) <= 1e-6
    assert net.unit[0].weight.shape[1] == 84 and torch.all(net.unit[0].weight[:, 79:] == 0)
    tracker = MoveTracker()
    assert not tracker.features(5, [0], [[1, 1]]).any()
    tracker.record(5, [0, 1], [[1, 1], [3, 3]], [True, False])
    f = tracker.features(6, [0, 1], [[1, 2], [3, 4]])
    assert f[0, geo.DOWN] == 1 and not f[1].any()          # Unit 1 hatte negative Energie
    assert not tracker.features(8, [0], [[1, 2]]).any()     # Lücke


@pytest.mark.parametrize("flag", [False, True])
def test_old_students_unchanged_without_flag(flag, tmp_path):
    from agents.sherlock.imitation_agent import ImitationAgent
    from agents.sherlock.imitation_net import ImitationNet
    from agents.sherlock.ppo_agent import save_policy

    torch.manual_seed(1)
    net = ImitationNet(feat_dim=79 + (N_PREV if flag else 0), ch=4, blocks=1, hidden=12)
    path = tmp_path / "s.pth"
    save_policy(str(path), net, imitate.v14_cfg(), extra={"kind": "imitation", "sap_own_tile": True,
                                                           **({"prev_move_input": True} if flag else {})})
    agent = ImitationAgent("player_0", agent_path=str(path), train=False)
    assert agent.prev_move_input is flag
