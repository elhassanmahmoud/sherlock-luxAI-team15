"""One fixed, passive V3 loss diagnostic; run only after source review.

Uses common.play_game unchanged. All coordinates in records are REAL coordinates.
Recorded direction classes and legal-mask indices also use the real frame.
The agent receives only its original observation/params; truth is external. A
transition's t snapshot precedes env.step, while known tiles reflect act(obs_t).
Net energy changes are not damage attribution, masks are not unit lifetimes, and
cost-only collision margins ignore stacks, sap hits and other simultaneous effects.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import subprocess
from dataclasses import asdict
from pathlib import Path

import numpy as np

from scripts.common import ROOT, make_opponent, play_game
from scripts.experiment import GAME_FIELDS, limit_threads
from scripts.scoring import match_points_after_step, point_tile_map

SEEDS = (510862, 510847, 510930, 510956, 510950, 510972, 510819, 510858, 510911, 510839)
GAME_KEYS = tuple((seed, side) for seed in SEEDS for side in ('player_0', 'player_1'))
V3_SHA256 = 'aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935'
REFERENCE_SHA256 = '71705b366a6012ff56285fd6dfb7964365e6e711439d37f33a6e2875dbdd44e2'
SNAPSHOT_STEPS = (25, 50, 75, 100)


def coords(mask):
    return np.argwhere(mask).tolist()


def visible_context(obs, team, uid, params):
    """Legal observation only; no hidden sap dropoff parameter or kill claim."""
    pos = np.asarray(obs['units']['position'])
    energy = np.asarray(obs['units']['energy'])
    mask = np.asarray(obs['units_mask'], bool)
    xy = pos[team, uid]
    our_energy = int(energy[team, uid])
    move_cost = int(params['unit_move_cost'])
    sap_cost = int(params['unit_sap_cost'])
    direct = bool(obs['sensor_mask'][tuple(xy)])
    terrain = int(obs['map_features']['tile_type'][tuple(xy)])
    stack = int((mask[team] & (energy[team] >= 0) & (pos[team] == xy).all(axis=1)).sum())
    visible = []
    for enemy in np.flatnonzero(mask[1 - team]):
        exy = pos[1 - team, enemy]
        if (exy < 0).any():
            continue
        ee = int(energy[1 - team, enemy])
        adjacent = bool(np.abs(exy - xy).sum() == 1)
        # This only says the observed neighbor could enter our current tile.
        can_enter = adjacent and ee >= move_cost and direct and terrain in (0, 1)
        visible.append(dict(uid=int(enemy), position=exy.tolist(), energy=ee,
                            adjacent=adjacent, can_move_to_unit=can_enter,
                            cost_only_margin_stay=our_energy - (ee - move_cost),
                            cost_only_margin_sap=our_energy - sap_cost - (ee - move_cost)))
    return dict(position=xy.tolist(), energy=our_energy, sap_cost=sap_cost,
                move_cost=move_cost, sap_range=int(params['unit_sap_range']),
                own_stack_size=stack, direct_sensor=direct, tile_type=terrain,
                visible_enemies=visible)


class ObservedAgent:
    """Read existing call results once; never call a policy a second time."""
    def __init__(self, agent, side):
        self.agent = agent
        self.team = int(side[-1])
        self.decision = None

    def __getattr__(self, name):
        return getattr(self.agent, name)

    def act(self, step, obs):
        agent = self.agent
        calls = {}
        original = getattr(agent, '_rule_override', None)
        had_instance = '_rule_override' in vars(agent)
        previous_instance = vars(agent).get('_rule_override')

        def world_direction(action):
            from agents.sherlock.geometry import mirror_dir
            return mirror_dir(action) if agent.belief.mirrored and action < 5 else int(action)

        def record_rule(ctx, uid, mask, action):
            result = original(ctx, uid, mask, action)
            calls[int(uid)] = dict(before_rule=world_direction(action), after_rule=world_direction(result),
                                   legal_mask=np.asarray(mask, bool)[
                                       [world_direction(i) for i in range(len(mask))]].tolist(),
                                   first_on_tile=int(ctx['first_on_tile'].get(
                                       tuple(ctx['ally_pos'][uid]), -1)))
            return result

        if original is not None:
            agent._rule_override = record_rule
        try:
            actions = agent.act(step=step, obs=obs)
        finally:
            if original is not None:
                if had_instance:
                    agent._rule_override = previous_instance
                else:
                    del agent._rule_override
        from agents.sherlock.geometry import mirror_map
        known = np.asarray(agent.belief.point_tiles, bool)
        if agent.belief.mirrored:
            known = mirror_map(known)
        cfg = getattr(agent, 'cfg', None)
        competing = getattr(agent, 'cnn_policy', None) is not None or any(getattr(cfg, name, False) for name in
                        ('ram', 'fog_sap', 'contest_sap', 'idle_sap', 'smart_sap'))
        units = []
        for uid, call in calls.items():
            context = visible_context(obs, self.team, uid, agent.env_cfg)
            late = call['after_rule'] == 0 and int(actions[uid, 0]) == 5
            xy = tuple(context['position'])
            units.append(dict(uid=uid, **context, **call, final_action=actions[uid].tolist(),
                              recorded_action_class=world_direction(agent._prev_actions[uid]),
                              on_known_point=bool(known[xy]), late_stay_to_sap=late,
                              inferred_pt_sap=bool(late and getattr(cfg, 'pt_sap', False)
                                                   and not competing)))
        self.decision = dict(step=int(step), known_point_tiles=coords(known), units=units,
                             competing_late_flags=competing)
        return actions


def truth_snapshot(state):
    """External engine state, copied before transition; never agent input."""
    mask = np.asarray(state.units_mask, bool)
    pos = np.asarray(state.units.position)
    energy = np.asarray(state.units.energy)[..., 0]
    tiles = point_tile_map(state)
    productive = []
    for team in (0, 1):
        occupied = np.zeros_like(tiles)
        valid = mask[team] & (energy[team] >= 0)
        p = pos[team, valid]
        occupied[p[:, 0], p[:, 1]] = True
        productive.append(coords(occupied & tiles))
    return dict(position=pos.tolist(), energy=energy.tolist(), mask=mask.tolist(),
                active_point_tiles=coords(tiles), productive_tiles=productive,
                relic_nodes=np.asarray(state.relic_nodes).tolist(),
                relic_mask=np.asarray(state.relic_nodes_mask, bool).tolist(),
                energy_total=[int(energy[t, mask[t]].sum()) for t in (0, 1)])


class ObservedEnv:
    def __init__(self, env, agent, side, sink):
        self.env, self.agent, self.side, self.sink = env, agent, side, sink
        self.summary = dict(matches=[], snapshots=[])
        self.match = 0

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        self.obs = obs[self.side]
        self.params = dict(info['params'])
        return obs, info

    def step(self, actions):
        before = self.obs
        truth = truth_snapshot(self.env.state)
        action_copy = {side: np.asarray(a).tolist() for side, a in actions.items()}
        result = self.env.step(actions)
        obs, _, _, _, info = result
        after = obs[self.side]
        points = match_points_after_step(before, after, info)
        state_after = info['final_state']
        truth_after = truth_snapshot(state_after)
        reset = int(after['match_steps']) == 0
        event = dict(match=self.match, step_t=int(before['steps']),
                     match_step_t=int(before['match_steps']), step_after=int(after['steps']),
                     match_step_after=int(after['match_steps']), match_reset_after=reset,
                     points_t=np.asarray(before['team_points']).tolist(),
                     points_after=points.tolist(), wins_after=np.asarray(after['team_wins']).tolist(),
                     decision=self.agent.decision, actions=action_copy,
                     truth_t=truth, truth_after=truth_after,
                     observed_after=dict(mask=np.asarray(after['units_mask'], bool).tolist(),
                                         position=np.asarray(after['units']['position']).tolist(),
                                         energy=np.asarray(after['units']['energy']).tolist()))
        self.sink(event)
        if event['match_step_t'] in SNAPSHOT_STEPS:
            self.summary['snapshots'].append(event)
        if reset:
            delta = np.asarray(after['team_wins']) - np.asarray(before['team_wins'])
            winners = np.flatnonzero(delta == 1)
            if len(winners) != 1 or int(delta.sum()) != 1:
                raise ValueError('invalid match winner delta')
            energy = truth_after['energy_total']
            tiebreak = 'points' if points[0] != points[1] else (
                'energy' if energy[0] != energy[1] else 'random')
            self.summary['matches'].append(dict(match=self.match, points=points.tolist(),
                                                winner=int(winners[0]), tiebreak=tiebreak,
                                                energy_total=energy, step_after=int(after['steps']),
                                                point_counting_version=2))
            self.match += 1
        self.obs = after
        return result


def observe_game(env, agent, opp, seed, side, sink):
    proxy = ObservedAgent(agent, side)
    wrapped = ObservedEnv(env, proxy, side, sink)
    row = play_game(wrapped, proxy, opp, seed, side, train=False)
    row['opponent'] = 'solution92'
    return row, wrapped.summary


def load_reference(path):
    reference = {}
    with Path(path).open(newline='') as handle:
        reader = csv.DictReader(handle)
        missing_fields = set(GAME_FIELDS) - set(reader.fieldnames or [])
        if missing_fields:
            raise ValueError(f'missing reference fields: {sorted(missing_fields)}')
        for row in reader:
            if row['opponent'] != 'solution92':
                continue
            key = (int(row['seed']), row['side'])
            if key not in GAME_KEYS:
                continue
            if key in reference:
                raise ValueError(f'duplicate reference key {key}')
            if int(row['steps']) != 303 or int(row['point_counting_version']) != 2:
                raise ValueError(f'invalid reference length/version {key}')
            reference[key] = row
    missing = set(GAME_KEYS) - reference.keys()
    if missing:
        raise ValueError(f'missing reference keys: {sorted(missing)}')
    return reference


def check_reference(row, reference):
    key = (int(row['seed']), row['side'])
    expected = reference[key]
    for field in GAME_FIELDS:
        if field == 'secs':
            continue
        actual, wanted = row[field], expected[field]
        if field in ('side', 'opponent'):
            equal = actual == wanted
        else:
            actual, wanted = float(actual), float(wanted)
            equal = math.isfinite(actual) and actual == wanted
        if not equal:
            raise ValueError(f'reference mismatch {key} {field}: {actual!r} != {wanted!r}')


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_output(path):
    Path(path).mkdir(parents=True, exist_ok=False)


def verify_hashes(manifest):
    for section in ('inputs', 'sources'):
        for name, expected in manifest[section].items():
            if sha256(name) != expected:
                raise ValueError(f'{section} changed: {name}')
    if 'head' in manifest and git_head() != manifest['head']:
        raise ValueError('source HEAD changed')


def git_head():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()


def build_manifest(weights, reference):
    import luxai_s3
    files = subprocess.check_output(['git', 'ls-files', '*.py'], cwd=ROOT, text=True).splitlines()
    paths = {ROOT / p for p in files}
    paths.add(Path(__file__).resolve())
    paths.update(Path(luxai_s3.__file__).parent.rglob('*.py'))
    return dict(status='running', schema_version=1, head=git_head(),
                game_keys=[list(k) for k in GAME_KEYS], point_counting_version=2,
                inputs={str(p): sha256(p) for p in (weights, reference)},
                sources={str(p): sha256(p) for p in sorted(paths)},
                limits=['Outcome-stratified known maps; no prevalence/strength inference.',
                        'Cost-only margins are not counterfactual collision outcomes.',
                        'Net energy delta is not attributed damage; unit slots can respawn.',
                        'Hidden unit_sap_dropoff_factor is not a legal policy input.',
                        'Snapshots are t/act/t+1; known tiles were updated using obs_t.'])


def dump_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='New exclusive output directory')
    parser.add_argument('--weights', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    args = parser.parse_args()
    weights, reference_path = args.weights.resolve(), args.reference.resolve()
    if sha256(weights) != V3_SHA256:
        raise ValueError('weights are not the fixed V3 input')
    if sha256(reference_path) != REFERENCE_SHA256:
        raise ValueError('reference is not the fixed fresh_v3.csv input')
    reference = load_reference(reference_path)
    prepare_output(args.out)
    manifest = build_manifest(weights, reference_path)
    manifest_path = args.out / 'manifest.json'
    dump_json(manifest_path, manifest)
    env = None
    try:
        from agents.sherlock.main import Agent_x
        from luxai_s3.wrappers import LuxAIS3GymEnv
        limit_threads()
        env = LuxAIS3GymEnv(numpy_output=True)
        agent = Agent_x('player_0', agent_path=str(weights), train=False)
        agent.set_to_eval_mode()
        manifest['agent_config'] = asdict(agent.cfg)
        dump_json(manifest_path, manifest)
        with (args.out / 'games.csv').open('x', newline='') as games:
            writer = csv.DictWriter(games, GAME_FIELDS)
            writer.writeheader()
            for seed, side in GAME_KEYS:
                verify_hashes(manifest)
                opp = make_opponent('solution92', 'player_1' if side == 'player_0' else 'player_0')
                count = 0
                stem = f'{seed}_{side}'
                with gzip.open(args.out / f'{stem}.jsonl.gz', 'xt') as raw:
                    def emit(event):
                        nonlocal count
                        raw.write(json.dumps(event, separators=(',', ':')) + '\n')
                        count += 1
                    row, summary = observe_game(env, agent, opp, seed, side, emit)
                check_reference(row, reference)
                if count != 303 or len(summary['matches']) != 3 or len(summary['snapshots']) != 12:
                    raise ValueError(f'incomplete transitions/matches/snapshots for {stem}')
                verify_hashes(manifest)
                dump_json(args.out / f'{stem}.summary.json', summary)
                writer.writerow({field: row[field] for field in GAME_FIELDS})
                games.flush()
                print(f'{seed} {side}: matched all 23 non-time fields; 303 transitions', flush=True)
        verify_hashes(manifest)
        manifest['outputs'] = {p.name: sha256(p) for p in sorted(args.out.iterdir())
                               if p != manifest_path}
        manifest['status'] = 'complete'
    except BaseException as error:
        manifest['status'] = 'failed'
        manifest['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        if env is not None:
            env.close()
        dump_json(manifest_path, manifest)


if __name__ == '__main__':
    main()
