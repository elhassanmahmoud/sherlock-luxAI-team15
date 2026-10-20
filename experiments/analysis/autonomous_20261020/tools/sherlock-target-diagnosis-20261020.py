"""Observation-only diagnosis. Default: no games, weights, torch or JAX load.

Use --self-test for small NumPy reproductions. --run-games explicitly enables
future observational games; do not run while the existing evaluation is active.
Shadow assignments never reach the policy and use only its observation/belief.
"""
import argparse
import copy
import hashlib
import importlib
import types
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

# Supports placement under experiments/analysis/autonomous_20261020/tools/,
# worktrees and source copies without depending on the current directory.
ROOT = next((parent for parent in Path(__file__).resolve().parents
             if (parent / 'agents/sherlock/features.py').is_file()
             and (parent / 'scripts/common.py').is_file()), None)
if ROOT is None:
    raise RuntimeError('Place this tool inside a Sherlock repository checkout')
sys.path.insert(0, str(ROOT))
for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(name, '1')
import numpy as np
# agents/__init__.py eagerly imports every agent (including torch). Load only
# the pure NumPy source modules under an isolated package name instead.
_package_name = '_sherlock_diagnostic_source'
_package = types.ModuleType(_package_name)
_package.__path__ = [str(ROOT / 'agents' / 'sherlock')]
sys.modules[_package_name] = _package
_features = importlib.import_module(_package_name + '.features')
assign_targets = _features.assign_targets
make_context = _features.make_context
build_features = _features.build_features
FEATURE_NAMES = _features.FEATURE_NAMES
_home_penalty = _features._home_penalty
AgentConfig = importlib.import_module(_package_name + '.config').AgentConfig


def active_ids(ctx):
    ids = np.asarray(ctx['ally_ids'], dtype=np.int32)
    # Exactly the engine removal boundary: zero-energy units survive.
    return ids[ctx['ally_ene'][ids] >= 0]


def allocation(ctx, cfg, ids, previous=None):
    """Same assignment call as make_context, on a private belief/cache copy."""
    belief = copy.deepcopy(ctx['belief'])
    prev = previous[1] if cfg.sticky and previous is not None and previous[0] == belief.match_idx else None
    return assign_targets(
        belief, ids, ctx['ally_pos'][ids], ctx['W'], ctx['H'],
        enemy_half_penalty=_home_penalty(cfg, belief.match_idx),
        seen_before_penalty=300.0 if cfg.explore_memory else 0.0,
        grid=4 if cfg.explore_grid else 0, stale=int(cfg.explore_stale),
        cand_quota=int(cfg.cand_quota), far_opp=int(cfg.far_opp),
        prev=prev, sticky=float(cfg.sticky), far_cand=bool(cfg.far_cand),
        cand_boost=float(cfg.cand_boost),
    )


def own_half(ctx, target):
    # Strict own half, matching historical metric; diagonal is separate.
    own_origin = ctx['belief'].canonical or ctx['belief'].team_id == 0
    return sum(target) < ctx['W'] - 1 if own_origin else sum(target) > ctx['W'] - 1


def diagnose(ctx, cfg, previous=None):
    ids, live = ctx['ally_ids'], active_ids(ctx)
    dead = [int(u) for u in ids if ctx['ally_ene'][u] < 0]
    baseline = ctx['assigned']
    d = defaultdict(int, steps=1, units=len(ids), live_units=len(live),
                    negative_units=len(dead), negative_enemies=int((ctx['enemy_energies'] < 0).sum()))
    # Recompute original on affected steps; catches drift between shadow and production.
    if dead:
        if allocation(ctx, cfg, ids, previous) != baseline:
            raise RuntimeError('Shadow baseline does not reproduce production assignments')
        shadow = allocation(ctx, cfg, live, previous)
        d['steps_with_negative_units'] = 1
    else:
        shadow = dict(baseline)
    changed = [int(u) for u in live if baseline.get(int(u)) != shadow.get(int(u))]
    d['live_assignments_changed'] = len(changed)
    d['steps_with_live_assignment_change'] = int(bool(changed))
    live_pos = {tuple(map(int, ctx['ally_pos'][u])) for u in live}
    shadow_owner = {target: int(u) for u, target in shadow.items()}
    examples = []
    for u in dead:
        target = baseline.get(u)
        if target is None:
            continue
        d['negative_assignments'] += 1
        if not ctx['point_tiles'][target]:
            continue
        d['negative_point_assignments'] += 1
        if not own_half(ctx, target):
            continue
        d['negative_own_point_assignments'] += 1
        if target in live_pos:
            continue
        d['uncovered_own_point_reserved_by_negative'] += 1
        if target not in shadow_owner:
            continue
        v = shadow_owner[target]
        d['uncovered_own_point_reassigned_to_live'] += 1
        distance = int(np.abs(ctx['ally_pos'][v] - target).sum())
        d['reassigned_live_distance_sum'] += distance
        if distance <= 2 and ctx['ally_ene'][v] >= ctx['move_cost']:
            d['reassigned_with_live_nearby_energy'] += 1
        examples.append(dict(step=int(ctx['step']), match_step=int(ctx['match_step']),
                             dead_uid=u, target=list(target), live_uid=v,
                             live_previous_target=baseline.get(v), live_distance=distance,
                             live_energy=float(ctx['ally_ene'][v])))
    for target, u in ctx['first_on_tile'].items():
        if ctx['point_tiles'][target] and ctx['ally_ene'][u] < 0 and target in live_pos:
            d['negative_first_on_point_with_live_stack'] += 1
    return dict(d), examples


def synthetic_self_test():
    """Exercise production functions without importing Agent_x or the engine."""
    class Belief:
        W = H = 24
        team_id = 0
        opp_team_id = 1
        mirrored = False
        canonical = True
        match_idx = 2
        def __init__(self):
            self.point_tiles = np.zeros((24, 24), bool)
            self.point_tiles[3, 3] = self.point_tiles[10, 10] = True
            self.candidate = np.zeros((24, 24), bool)
            self.explored = np.ones((24, 24), bool)
            self.explored_ever = self.explored.copy()
            self.passable = np.ones((24, 24), bool)
            self.nebula = np.zeros((24, 24), bool)
            self.energy_map = np.zeros((24, 24), np.float32)
        def point_coords(self): return np.argwhere(self.point_tiles).astype(np.int32)
        def candidate_coords(self): return np.argwhere(self.candidate).astype(np.int32)
        def unexplored_coords(self): return np.argwhere(~self.explored).astype(np.int32)
        def explore_coords(self, stale): return self.unexplored_coords()
        def relic_coords(self): return np.empty((0, 2), np.int32)

    cfg = AgentConfig()
    agent = SimpleNamespace(cfg=cfg, env_cfg={}, belief=Belief(), _sticky_prev=None)
    positions = np.full((2, 4, 2), -1, np.int32)
    energies = np.full((2, 4), -1, np.float32)
    masks = np.zeros((2, 4), bool)
    masks[0, :2] = True
    positions[0, :2] = [[3, 3], [3, 4]]
    energies[0, :2] = [-1, 50]
    obs = dict(units_mask=masks, units=dict(position=positions, energy=energies),
               team_points=[0, 0], team_wins=[0, 0], match_steps=60, steps=262)
    ctx = make_context(agent, obs)
    assert ctx['assigned'] == {0: (3, 3), 1: (10, 10)}
    shadow = allocation(ctx, cfg, active_ids(ctx))
    assert shadow == {1: (3, 3)}
    d, examples = diagnose(ctx, cfg)
    assert d['uncovered_own_point_reassigned_to_live'] == 1
    assert d['live_assignments_changed'] == 1 and len(examples) == 1
    # Assignment-only changes exactly the assigned target fields, not occupancy features.
    old_features = build_features(ctx, 1)
    new_features = build_features(dict(ctx, assigned=shadow), 1)
    changed_features = [name for name, old, new in zip(FEATURE_NAMES, old_features, new_features) if old != new]
    assert changed_features and all(name.startswith('assigned_') for name in changed_features)
    # Zero energy is not death, even when it cannot currently pay movement cost.
    energies[0, 0] = 0
    zero = make_context(agent, obs)
    assert active_ids(zero).tolist() == [0, 1]
    assert allocation(zero, cfg, active_ids(zero)) == zero['assigned']
    # All-negative and masked slots do not leak into shadow assignment.
    energies[0, :2] = [-1, -5]
    all_negative = make_context(agent, obs)
    assert active_ids(all_negative).size == 0
    assert allocation(all_negative, cfg, active_ids(all_negative)) == {}
    # Separate occupancy/first-owner problem: changing assignment alone leaves it unchanged.
    positions[0, 1] = [3, 3]
    energies[0, 1] = 50
    stacked = make_context(agent, obs)
    assert stacked['first_on_tile'][(3, 3)] == 0 and stacked['ally_count'][3, 3] == 2
    assert diagnose(stacked, cfg)[0]['negative_first_on_point_with_live_stack'] == 1
    assert build_features(stacked, 1)[FEATURE_NAMES.index('redundant_here')] == 1
    # Mirror-side correctness and supported energy shape (..., 1).
    agent.belief.team_id, agent.belief.opp_team_id, agent.belief.mirrored = 1, 0, True
    positions[1, :2] = [[20, 20], [20, 19]]  # mirrors to (3,3), (4,3)
    masks[0] = False
    masks[1, :2] = True
    energies[1, :2] = [-1, 50]
    obs['units']['energy'] = energies[..., None]
    mirrored = make_context(agent, obs)
    assert diagnose(mirrored, cfg)[0]['uncovered_own_point_reassigned_to_live'] == 1
    # Sticky shadow must receive PRE-decision history, including on matching match only.
    cfg.sticky = 3
    agent._sticky_prev = (2, {1: (10, 10)})
    previous = copy.deepcopy(agent._sticky_prev)
    sticky = make_context(agent, obs)
    assert allocation(sticky, cfg, sticky['ally_ids'], previous) == sticky['assigned']
    diagnose(sticky, cfg, previous)
    # Noncanonical player 1: own half is the high-coordinate side.
    noncanonical = dict(ctx, belief=SimpleNamespace(canonical=False, team_id=1))
    assert own_half(noncanonical, (20, 20)) and not own_half(noncanonical, (3, 3))
    assert not own_half(ctx, (10, 13))  # diagonal counted in neither strict half
    # Empty targets yield no phantom reservation; dead-ID removal remains safe.
    agent.belief.point_tiles[:] = False
    empty = make_context(agent, obs)
    assert empty['assigned'] == {} and diagnose(empty, cfg, previous)[0]['live_assignments_changed'] == 0
    assert 'torch' not in sys.modules and 'jax' not in sys.modules
    print(json.dumps(dict(status='synthetic_checks_passed', games=0,
                          torch_loaded=False, jax_loaded=False,
                          baseline={str(k): v for k, v in ctx['assigned'].items()},
                          shadow={str(k): v for k, v in shadow.items()},
                          changed_features=changed_features,
                          note='Mechanism reproduced, not empirical frequency or playing-strength benefit.'), indent=2))


def run_games(args):
    # Deliberately lazy: importing this file and self-testing never load torch/JAX.
    from scripts.experiment import limit_threads
    limit_threads()
    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent, play_game
    from luxai_s3.wrappers import LuxAIS3GymEnv
    spec = importlib.util.spec_from_file_location(
        'sap_geometry_shadow', str(Path(__file__).with_name('observe_sap_geometry.py')))
    sap_shadow = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sap_shadow)

    class ObservedAgent(Agent_x):
        def new_game(self, player=None):
            super().new_game(player)
            self.diagnostics = defaultdict(lambda: defaultdict(int))
            self.observed = set()
            self.examples = []
            self.sap_examples = []
        def _decide(self, obs):
            previous = copy.deepcopy(getattr(self, '_sticky_prev', None))
            result = super()._decide(obs)
            ctx = result[0]
            step = int(np.asarray(obs['steps']))
            if step not in self.observed:
                self.observed.add(step)
                d, examples = diagnose(ctx, self.cfg, previous)
                for key, value in d.items():
                    self.diagnostics[int(ctx['match_idx'])][key] += value
                self.examples.extend(examples[:max(0, 20 - len(self.examples))])
            return result
        def act(self, step, obs):
            actions = super().act(step, obs)
            if int(np.asarray(obs['match_steps'])) == 0:
                return actions
            assert self._cache is not None and self._cache[0] == int(np.asarray(obs['steps']))
            ctx, ids, feats, masks, saps = self._cache[1:]
            d = self.diagnostics[int(ctx['match_idx'])]
            sap_observation = sap_shadow.observe_sap_geometry(
                ctx, ids, saps, actions, mirrored=self.belief.mirrored,
                sap_pt_first=self.cfg.sap_pt_first, smart_sap=self.cfg.smart_sap, example_limit=1)
            for key, value in sap_observation['counters'].items():
                d['sap_geometry_' + key] += value
            self.sap_examples.extend(sap_observation['examples'][:max(0, 10 - len(self.sap_examples))])
            if self.cfg.pt_sap and not self.cfg.pt_sap_zone:
                live_first = {}
                for uid in active_ids(ctx):
                    live_first.setdefault(tuple(map(int, ctx['ally_pos'][uid])), int(uid))
                for uid in active_ids(ctx):
                    tile = tuple(map(int, ctx['ally_pos'][uid]))
                    owner = ctx['first_on_tile'].get(tile)
                    if (ctx['point_tiles'][tile] and live_first[tile] == int(uid) and owner is not None
                            and ctx['ally_ene'][owner] < 0 and actions[uid, 0] == 0
                            and saps[int(uid)] is not None and masks[int(uid)][5]
                            and ctx['ally_ene'][uid] >= ctx['sap_cost'] + self.cfg.pt_sap_reserve):
                        d['pt_sap_stay_opportunities_blocked_by_negative_first_owner'] += 1
            return actions

    output = Path(args.out)
    if output.exists():
        raise FileExistsError(output)
    source = Path(args.weights).resolve()
    before_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    before_code = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    agent = ObservedAgent('player_0', agent_path=str(source), train=False)
    assert not agent.cfg.contest_sap and not agent.cfg.smart_sap, 'Baseline diagnosis excludes alternate Sap planners'
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    env = LuxAIS3GymEnv(numpy_output=True)
    rows, games, examples, sap_examples = [], [], [], []
    try:
        for seed in range(500000 + args.first, 500000 + args.first + args.n):
            for side in ('player_0', 'player_1'):
                opp = make_opponent('solution92', 'player_1' if side == 'player_0' else 'player_0')
                games.append(play_game(env, agent, opp, seed, side, train=False))
                for match, d in sorted(agent.diagnostics.items()):
                    rows.append(dict(seed=seed, side=side, match=match, **d))
                examples.extend(dict(seed=seed, side=side, **e) for e in agent.examples)
                sap_examples.extend(dict(seed=seed, side=side, **e) for e in agent.sap_examples)
            print('seed', seed, 'complete', flush=True)
    finally:
        env.close()
    assert len(games) == 2 * args.n and len(rows) == 6 * args.n
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before_hash
    assert subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip() == before_code
    payload = dict(code_commit=before_code, weights=str(source), sha256=before_hash,
                   cfg=vars(agent.cfg), games=games, diagnostics=rows, examples=examples,
                   sap_geometry_examples=sap_examples,
                   note='Observation only. Shadow allocation reproduces baseline before filtering. '
                        'Counts are unit/step opportunities, not independent events, lost points, '
                        'legal-path guarantees, changed real actions, or causal playing-strength gain. '
                        'All shadow inputs come exclusively from existing observation/belief. '
                        'Check non-time game metrics against baseline before interpreting results.')
    with output.open('x') as f:
        json.dump(payload, f, indent=2)
        f.write('\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    modes = ap.add_mutually_exclusive_group(required=True)
    modes.add_argument('--self-test', action='store_true')
    modes.add_argument('--run-games', action='store_true')
    ap.add_argument('--weights')
    ap.add_argument('--out')
    ap.add_argument('--first', type=int, default=720)
    ap.add_argument('--n', type=int, default=20)
    args = ap.parse_args()
    if args.self_test:
        synthetic_self_test()
    else:
        if not args.weights or not args.out or args.n <= 0:
            ap.error('--run-games requires --weights, --out and positive --n')
        if not 720 <= args.first < args.first + args.n <= 780:
            ap.error('Diagnosis is restricted to the assigned development block 500720–500779')
        run_games(args)


if __name__ == '__main__':
    main()
