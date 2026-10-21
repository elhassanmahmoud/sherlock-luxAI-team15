"""The early curriculum changes order only, and the CLI records actual inputs."""
import csv
import hashlib
import json
import sys
from collections import Counter
from types import SimpleNamespace

import pytest

from scripts import experiment as E, protocol as P
from agents.sherlock.main import Agent_x
from scripts.variants import variant_cfg


@pytest.mark.parametrize('total,sol,pool', [(1200, None, 0), (17, .4, .3), (3000, .7, 0)])
def test_standard_preserves_every_original_opponent(total, sol, pool):
    assert P.opponent_schedule(total, sol, pool, 'standard') == [
        P.train_opponent(g, total, sol, pool) for g in range(total)]


def test_early_changes_only_the_prescribed_pairs():
    control = P.opponent_schedule(3000, .7, 0, 'standard')
    early = P.opponent_schedule(3000, .7, 0, 'early_sol100')
    expected_late = [g for g in range(750, 3000, 2) if control[g] == 'solution92'][:50]
    assert (expected_late[0], expected_late[-1]) == (752, 892)
    changed = {g for g in range(3000) if early[g] != control[g]}
    assert changed == set(range(100, 200)) | {g + side for g in expected_late for side in (0, 1)}
    assert len(changed) == 200
    for schedule in (control, early):
        assert Counter(schedule) == {'default': 1426, 'solution92': 1574}
        assert all(schedule[g] == schedule[g + 1] for g in range(0, 3000, 2))
    assert early[100:200] == ['solution92'] * 100
    assert early[894:] == control[894:]
    for seed in (47, 48, 49):
        cards = {P.train_seed(seed, g) for g in range(3000)}
        assert cards == set(range(seed * 10000, seed * 10000 + 1500))
        assert not cards & set(range(500720, 500728))
        assert [P.train_side(g) for g in range(4)] == ['player_0', 'player_1'] * 2


@pytest.mark.parametrize('total,sol,pool,mode', [
    (2999, .7, 0, 'early_sol100'), (3000, None, 0, 'early_sol100'),
    (3000, .5, 0, 'early_sol100'), (3000, .7, .1, 'early_sol100'),
    (3000, .7, 0, 'typo'),
])
def test_rejects_unsupported_schedule(total, sol, pool, mode):
    with pytest.raises(ValueError):
        P.opponent_schedule(total, sol, pool, mode)


def install_tiny_cli(monkeypatch):
    """Keep real Learners/Agent construction; replace only costly games and files."""
    def make(variant, side, path, seed):
        cfg = variant_cfg(variant)
        cfg.hidden = 8
        cfg.buffer_capacity = 4
        a = Agent_x(side, cfg=cfg, seed=seed)
        a.autosave_on_terminate = False
        return a
    monkeypatch.setattr(E, 'make_learner', make)
    monkeypatch.setattr(E.Learners, 'save', lambda self: None)
    monkeypatch.setattr(E.Learners, 'save_buffers', lambda self: None)
    monkeypatch.setattr(E, 'make_opponent', lambda *a, **k: object())
    monkeypatch.setitem(sys.modules, 'luxai_s3.wrappers', SimpleNamespace(
        LuxAIS3GymEnv=lambda **k: SimpleNamespace(close=lambda: None)))
    def game(env, agent, opp, seed, side, train):
        return dict(seed=seed, side=side, result=1., point_win=1., our_wins=3,
                    opp_wins=0, our_points=10, opp_points=0, steps=303,
                    point_counting_version=2)
    monkeypatch.setattr(E, 'play_game', game)


@pytest.mark.parametrize('isolated', [False, True])
def test_cli_records_absolute_seeds_raw_rows_and_actual_initial_identity(tmp_path, monkeypatch, isolated):
    install_tiny_cli(monkeypatch)
    seen = []
    def validation(env, learners, seeds, opponents):
        assert list(seeds) == (list(range(500720, 500728)) if isolated else P.val_seeds(8))
        identity_path = tmp_path / 'initial_identity.json'
        assert identity_path.exists() == isolated
        if isolated:
            identity = json.loads(identity_path.read_text())
            # This is the actual constructed agent, not a later reconstruction.
            if not seen:
                assert identity == E.initial_identity(learners)
            assert identity['learners'][0]['env_steps'] == 0
        seen.append(1)
        return [dict(seed=seed, side=side, opponent=opp, result=1., point_win=1.,
                     our_wins=3, opp_wins=0, our_points=10, opp_points=0,
                     point_counting_version=2, steps=303)
                for opp in opponents for seed in seeds for side in P.SIDES]
    monkeypatch.setattr(E, 'play_set', validation)
    argv = ['--variant', 'full_rules_v3', '--run-seed', '47', '--games', '2',
            '--val-every', '1', '--no-test', '--out', str(tmp_path)]
    if isolated:
        argv += ['--val-seed-start', '500720', '--isolate-validation']
    E.main(argv)
    manifest = json.loads((tmp_path / 'manifest.json').read_text())
    assert manifest['opponent_plan'] == 'standard'
    assert manifest['opponent_schedule'] == ['default', 'default']
    labels = json.dumps(manifest['opponent_schedule'], separators=(',', ':')).encode()
    assert manifest['opponent_schedule_sha256'] == hashlib.sha256(labels).hexdigest()
    assert manifest['val_seeds'] == (list(range(500720, 500728)) if isolated else P.val_seeds(8))
    assert manifest['isolate_validation'] is isolated
    if isolated:
        identity = json.loads((tmp_path / 'initial_identity.json').read_text())
        assert manifest['learner_devices'] == [entry['device'] for entry in identity['learners']]
    else:
        assert 'learner_devices' not in manifest
    with (tmp_path / 'val_games.csv').open() as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == ['after_games'] + E.GAME_FIELDS
        rows = list(reader)
    assert len(rows) == 96
    assert Counter(int(row['after_games']) for row in rows) == {0: 32, 1: 32, 2: 32}
    assert {int(row['seed']) for row in rows} == set(manifest['val_seeds'])


def test_cli_training_consumes_early_plan_without_changing_seed_or_side(tmp_path, monkeypatch):
    install_tiny_cli(monkeypatch)
    monkeypatch.setattr(E, 'make_opponent', lambda label, side: label)
    original_game = E.play_game
    class StopAfterEarlyBlock(Exception):
        pass
    def game(env, agent, opp, seed, side, train):
        if seed == 470100:
            raise StopAfterEarlyBlock
        row = original_game(env, agent, opp, seed, side, train)
        assert opp == ('solution92' if 470050 <= seed < 470100 else 'default')
        return row
    monkeypatch.setattr(E, 'play_game', game)
    with pytest.raises(StopAfterEarlyBlock):
        E.main(['--variant', 'full_rules_v3', '--run-seed', '47', '--games', '3000',
                '--sol92-frac', '.7', '--pool-frac', '0', '--opponent-plan', 'early_sol100',
                '--val-every', '0', '--no-test', '--out', str(tmp_path)])
    manifest = json.loads((tmp_path / 'manifest.json').read_text())
    assert manifest['opponent_plan'] == 'early_sol100'
    assert manifest['curriculum'] == 'early_sol100'
    assert manifest['opponent_schedule'][100:200] == ['solution92'] * 100
    with (tmp_path / 'train.csv').open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 200
    assert [(int(row['seed']), row['side']) for row in rows] == [
        (470000 + g // 2, ('player_0', 'player_1')[g % 2]) for g in range(200)]
    assert [row['opponent'] for row in rows] == ['default'] * 100 + ['solution92'] * 100


def test_cli_invalid_early_plan_fails_before_model_construction(tmp_path, monkeypatch):
    def forbidden():
        pytest.fail('Invalid plan must be rejected before expensive imports/construction')
    monkeypatch.setattr(E, 'limit_threads', forbidden)
    with pytest.raises(SystemExit) as exc:
        E.main(['--variant', 'full_rules_v3', '--opponent-plan', 'early_sol100', '--out', str(tmp_path)])
    assert exc.value.code == 2
    assert not (tmp_path / 'manifest.json').exists()
