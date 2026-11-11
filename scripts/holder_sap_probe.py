"""One-shot public holder intervention; no deployable policy or training."""
from __future__ import annotations
import hashlib
import importlib
import json
from pathlib import Path
import sys
import zipfile
import numpy as np
from agents.sherlock.main import Agent_x

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT/'experiments/analysis/holder_sap_causality_20261111/reference_source.zip'


def load_reference_class():
    manifest = json.loads(REFERENCE.with_suffix('.json').read_text())
    if hashlib.sha256(REFERENCE.read_bytes()).hexdigest() != manifest['archive_sha256']:
        raise ValueError('Original source archive changed')
    with zipfile.ZipFile(REFERENCE) as z:
        if set(z.namelist()) != set(manifest['files']):
            raise ValueError('Original source inventory changed')
        for name, entry in manifest['files'].items():
            if hashlib.sha256(z.read(name)).hexdigest() != entry['sha256']:
                raise ValueError('Original source member changed')
    if str(REFERENCE) not in sys.path:
        sys.path.insert(0, str(REFERENCE))
    module = importlib.import_module('frozen_holder_v14.main')
    if not module.__file__.startswith(str(REFERENCE)+'/') or hasattr(module.Agent_x, '_final_sap_policy'):
        raise ValueError('Reference is not the untouched original package')
    return module.Agent_x


def eligible_holder_sap(ctx, uid, mask, network_action, action, sap, fog_origin):
    if (int(ctx['match_step']) == 0 or network_action != 0 or action != 5
            or sap is None or fog_origin is not None or not mask[0]
            or uid not in ctx['ally_ids'] or float(ctx['ally_ene'][uid]) < 0):
        return False
    x, y = map(int, ctx['ally_pos'][uid])
    if not ctx['point_tiles'][x, y]:
        return False
    holders = [u for u in ctx['ally_ids'] if float(ctx['ally_ene'][u]) >= 0
               and np.array_equal(ctx['ally_pos'][u], (x, y))]
    if len(holders) != 1:
        return False
    # Visible means the final target centre contains an observed opponent.
    target = (x+int(sap[0]), y+int(sap[1]))
    return any(np.array_equal(enemy, target) for enemy in ctx['enemy_coords'])


class HolderSapProbeAgent(Agent_x):
    _final_sap_experiment = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.training or self.cnn_policy is not None or self.cfg.smart_sap:
            raise ValueError('Probe requires frozen DQN evaluation without smart_sap')
        self.buffer = self.opt = None
        self.collect = False
        self.used_matches = set()
        self.candidate = self.intervention = None
        self.intervention_hits = 0
        for net in [self.q, self.target_q, *self.extra_q]:
            net.eval().requires_grad_(False)

    def new_game(self, player=None):
        super().new_game(player)
        self.used_matches = set()
        self.candidate = self.intervention = None
        self.intervention_hits = 0

    def update(self, *args, **kwargs):
        raise RuntimeError('Holder SAP probe cannot train')

    def act(self, step, obs):
        self.candidate = None
        return super().act(step, obs)

    def _policy_greedy(self, ctx, ids, masks, greedy):
        if list(ids) != sorted(ids):
            raise ValueError('First eligible unit requires ascending unit order')
        return greedy

    def _final_sap_policy(self, ctx, uid, mask, network_action, action, sap, fog_origin):
        valid = eligible_holder_sap(ctx, uid, mask, network_action, action, sap, fog_origin)
        event = None
        if valid:
            event = dict(step=int(ctx['step']), match=int(ctx['step'])//(int(ctx['max_match_steps'])+1),
                         match_step=int(ctx['match_step']), uid=int(uid), network_action=int(network_action),
                         action=int(action), sap=list(map(float, sap)),
                         energy=float(ctx['ally_ene'][uid]), position=list(map(int, ctx['ally_pos'][uid])),
                         rule_origin=self._final_sap_rule_origin, mask=np.asarray(mask).tolist(),
                         own_points=float(ctx['own_points']), opp_points=float(ctx['opp_points']),
                         sap_cost=float(ctx['sap_cost']), enemy_coords=np.asarray(ctx['enemy_coords']).tolist(),
                         enemy_energies=np.asarray(ctx['enemy_energies']).tolist())
            if self.collect and event['match'] not in self.used_matches:
                self.candidate = event
                self.used_matches.add(event['match'])
        order = self.intervention
        if order is not None and (int(ctx['step']), int(uid)) == (order['step'], order['uid']):
            if self.intervention_hits or not valid or event != order:
                raise ValueError('Repeated or changed intervention preconditions')
            self.intervention_hits += 1
            return 0, None
        return action, sap
