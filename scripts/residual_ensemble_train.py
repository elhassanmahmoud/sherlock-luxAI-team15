"""Bounded additive DDQN learner; evaluation actor and learning are separated.

Transitions finish at the next *actual* decision, after parameter estimation.
Calling _decide(next_obs) in update would populate the actor's cache too early
and silently change its evaluation behavior. Terminal contexts use a detached
shadow, so even target-assignment bookkeeping cannot change the acting agent.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import numpy as np
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.features import make_context
from agents.sherlock.residual import ResidualActor, V14_SHA
from agents.sherlock.reward import surviving, unit_rewards

CACHE_ID = V14_SHA + ':ordered-mean36:canonical79-float32-cpu:v1'


class ResidualReplay:
    FIELDS = ('s', 'a', 'r', 'ns', 'done', 'mask', 'base_s', 'base_ns', 'world', 'generation')

    def __init__(self, capacity, obs_dim, identity):
        self.capacity, self.obs_dim, self.identity = int(capacity), int(obs_dim), str(identity)
        if self.capacity <= 0 or self.obs_dim <= 0 or not self.identity:
            raise ValueError('Invalid replay dimensions/identity')
        self.s = np.zeros((capacity, obs_dim), np.float32)
        self.ns = np.zeros_like(self.s)
        self.a = np.zeros(capacity, np.int64)
        self.r = np.zeros(capacity, np.float32)
        self.done = np.zeros(capacity, np.float32)
        self.mask = np.zeros((capacity, 6), bool)
        self.base_s = np.zeros((capacity, 6), np.float32)
        self.base_ns = np.zeros_like(self.base_s)
        self.world = np.zeros((capacity, 3), np.int16)
        self.generation = np.zeros(capacity, np.int64)
        self.signatures = np.zeros((capacity, 32), np.uint8)
        self.pos = self.size = self.writes = 0

    def _signature(self, i):
        h = hashlib.sha256(self.identity.encode())
        for key in self.FIELDS:
            h.update(np.asarray(getattr(self, key)[i]).tobytes())
        return np.frombuffer(h.digest(), np.uint8)

    def push(self, s, a, r, ns, done, mask, base_s, base_ns, world, *, identity):
        if identity != self.identity:
            raise ValueError('Cache model/order/convention identity differs')
        for value, shape in ((s, (self.obs_dim,)), (ns, (self.obs_dim,)),
                             (base_s, (6,)), (base_ns, (6,))):
            if (np.asarray(value).shape != shape or np.asarray(value).dtype != np.float32
                    or not np.isfinite(value).all()):
                raise ValueError('Invalid float32 feature/cache value')
        if (np.asarray(mask).shape != (6,) or np.asarray(mask).dtype != bool or not np.any(mask)
                or not 0 <= int(a) < 6 or int(a) != a or not np.isfinite(r)
                or done not in (False, True) or np.asarray(world).shape != (3,)
                or not np.issubdtype(np.asarray(world).dtype, np.integer)
                or np.any(np.abs(np.asarray(world, dtype=np.int64)) > 32767)):
            raise ValueError('Invalid transition/action/mask')
        i = self.pos
        self.writes += 1
        for key, value in dict(s=s, a=a, r=r, ns=ns, done=done, mask=mask,
                               base_s=base_s, base_ns=base_ns, world=world,
                               generation=self.writes).items():
            getattr(self, key)[i] = value
        self.signatures[i] = self._signature(i)
        self.pos = (i + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def __len__(self):
        return self.size

    def sample(self, size, rng):
        if not self.size:
            raise ValueError('Empty replay')
        indices = rng.integers(0, self.size, size=size)  # exactly one shared draw
        for i in np.unique(indices):
            if not np.array_equal(self.signatures[i], self._signature(i)):
                raise ValueError('Stale/mutated cache-transition binding')
        return {k: getattr(self, k)[indices].copy() for k in self.FIELDS}

    def save(self, path):
        # Preserve physical slots, generations and cursor, not just one array's
        # chronological ordering. Identical RNG then samples identical rows.
        with open(path, 'xb') as f:
            np.savez_compressed(f, **{k:getattr(self,k)[:self.size] for k in self.FIELDS},
                                signatures=self.signatures[:self.size], identity=self.identity,
                                capacity=self.capacity, obs_dim=self.obs_dim, pos=self.pos,
                                size=self.size, writes=self.writes, schema=1)

    @classmethod
    def load(cls, path, identity):
        with np.load(path, allow_pickle=False) as z:
            if str(z['identity']) != identity or int(z['schema']) != 1:
                raise ValueError('Replay identity/schema differs')
            b = cls(int(z['capacity']), int(z['obs_dim']), identity)
            b.pos, b.size, b.writes = (int(z[k]) for k in ('pos', 'size', 'writes'))
            if not (0 <= b.size <= b.capacity and b.writes >= b.size
                    and b.pos == b.writes % b.capacity and b.size == min(b.writes,b.capacity)):
                raise ValueError('Invalid ring metadata')
            for k in (*cls.FIELDS, 'signatures'):
                dest = getattr(b,k)[:b.size]
                if z[k].shape != dest.shape or z[k].dtype != dest.dtype:
                    raise ValueError('Invalid replay array')
                dest[:] = z[k]
            for i in range(b.size):
                if not np.array_equal(b.signatures[i], b._signature(i)):
                    raise ValueError('Stored cache binding differs')
        return b


def residual_td_loss(batch, online, target, gamma):
    device = next(online.parameters()).device
    b = {k:torch.as_tensor(batch[k], device=device) for k in
         ('s','a','r','ns','done','mask','base_s','base_ns')}
    if not b['mask'].any(1).all():
        raise ValueError('No permitted next action')
    pred = (b['base_s'].detach() + online(b['s'])).gather(1, b['a'][:,None]).squeeze(1)
    with torch.no_grad():
        choice = (b['base_ns'] + online(b['ns'])).masked_fill(~b['mask'], -torch.inf).argmax(1)
        next_q = (b['base_ns'] + target(b['ns'])).gather(1, choice[:,None]).squeeze(1)
        y = b['r'] + (1 - b['done']) * gamma * next_q
    if not torch.isfinite(pred).all() or not torch.isfinite(y).all():
        raise ValueError('Nonfinite additive TD values')
    return torch.nn.functional.smooth_l1_loss(pred,y), pred, y


def finish_transition(cfg, replay, prev, ctx, feats, masks, bases, zero_base, terminal):
    reward = unit_rewards(cfg, prev['ctx'], ctx, prev['actions'], prev['hits'],
                          unknown_sap=prev['unknown'])
    alive = surviving(cfg, prev['ctx'], ctx)
    zero = np.zeros(replay.obs_dim, np.float32)
    dead_mask = np.array([True,False,False,False,False,False])
    for uid, s in prev['feats'].items():
        done = terminal or ctx['match_step'] == 0 or uid not in alive
        ns, mask, base_ns = (zero, dead_mask, zero_base) if done else (feats[uid], masks[uid], bases[uid])
        replay.push(s, prev['actions'][uid], reward.get(uid,0), ns, bool(done), mask,
                    prev['base'][uid], base_ns, prev['world'][uid], identity=replay.identity)


class ResidualLearner(ResidualActor):
    def __init__(self, player, base_path, *, seed, exploration=.05, capacity=300000):
        self.pending = self.current = None
        super().__init__(player, base_path, exploration=exploration, seed=seed)
        if self.device.type != 'cpu' or self.cfg.gamma != .99:
            raise ValueError('This pilot fixes CPU float32 and gamma=.99')
        self.replay = ResidualReplay(capacity, 79, CACHE_ID)
        self.target = copy.deepcopy(self.policy.residual).requires_grad_(False).eval()
        self.optimizer = torch.optim.Adam(self.policy.residual.parameters(), lr=5e-5)
        self.sample_rng = np.random.default_rng(np.random.SeedSequence([seed, 1001]))
        self.learn_enabled = False
        self.eligible_steps = self.updates = self.due_updates = 0
        self.losses = []
        with torch.no_grad():
            self.zero_base = self.policy.baseline(torch.zeros(1,79)).numpy()[0].copy()

    def new_game(self, player=None):
        if self.pending is not None:
            raise ValueError('Unfinished transition at new game')
        self.current = None
        super().new_game(player)

    def _reward_shadow(self, obs, *, observe):
        shadow = copy.copy(self)
        shadow.belief = copy.deepcopy(self.belief)
        shadow.feat_belief = shadow.belief
        if observe:
            shadow.belief.observe(obs)
        return make_context(shadow,obs)

    def _finish(self, ctx, feats, masks, bases, terminal):
        finish_transition(self.cfg,self.replay,self.pending,ctx,feats,masks,bases,self.zero_base,terminal)
        self.pending = None
        self.eligible_steps += 1
        if self.learn_enabled and len(self.replay) >= 5000 and self.eligible_steps % 2 == 0:
            self.due_updates += 1

    def act(self, step, obs):
        actions = super().act(step,obs)
        ctx = self._prev_ctx
        feats, masks = self._prev_feats, self._prev_masks
        ids = list(feats)
        bases = {}
        if ids:
            network_s, network_m, _ = self.last_network
            if not np.array_equal(network_s, np.stack([feats[u] for u in ids])):
                raise ValueError('Actual feature order differs from baseline cache')
            bases = {u:network_m[i].copy() for i,u in enumerate(ids)}
        if self.pending is not None:
            next_ctx = ctx if ctx is not None else self._reward_shadow(obs,observe=False)
            self._finish(next_ctx,feats,masks,bases,False)
        # Reconstruct the actual canonical action from the emitted world action,
        # including a SAP proposal that ultimately fell back to STAY.
        final = {u:int(actions[u,0]) for u in ids}
        if self.belief.mirrored:
            final = {u:int(geo.MIRROR_DIR[a]) if a < 5 else a for u,a in final.items()}
        self.current = None if ctx is None else dict(
            ctx=ctx, feats={u:f.copy() for u,f in feats.items()}, actions=final,
            hits=dict(self._sap_hits), unknown=set(self._sap_unknown), base=bases,
            world=np.asarray(actions,dtype=np.int16).copy())
        return actions

    def update(self, step, obs, reward, action, terminated, next_obs):
        self.env_steps += 1
        if self.pending is not None:
            raise ValueError('Pending transition was not finalized by next act')
        self.pending, self.current = self.current, None
        if terminated and self.pending is not None:
            self._finish(self._reward_shadow(next_obs,observe=True),{},{},{},True)
        while self.due_updates:
            batch = self.replay.sample(256,self.sample_rng)
            loss, pred, target = residual_td_loss(batch,self.policy.residual,self.target,.99)
            self.optimizer.zero_grad(set_to_none=True)
            loss.backward()
            norm = torch.nn.utils.clip_grad_norm_(self.policy.residual.parameters(),5.0)
            if not torch.isfinite(norm):
                raise ValueError('Nonfinite residual gradient')
            self.optimizer.step()
            self.updates += 1
            self.due_updates -= 1
            self.losses.append((float(loss.item()),float(norm),float(pred.mean()),float(target.mean())))
            if self.updates % 500 == 0:
                self.target.load_state_dict(self.policy.residual.state_dict())

    def learning_checkpoint(self):
        cp = self.policy.checkpoint(V14_SHA)
        cp.update(target=self.target.state_dict(), optimizer=self.optimizer.state_dict(),
                  updates=self.updates, eligible_steps=self.eligible_steps,
                  actor_rng=copy.deepcopy(self.rng.bit_generator.state),
                  sample_rng=copy.deepcopy(self.sample_rng.bit_generator.state),
                  cache_identity=CACHE_ID)
        return cp
