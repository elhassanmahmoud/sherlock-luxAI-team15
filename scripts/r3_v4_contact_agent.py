"""Unit-level routing between the original R3 movement adviser and original v4 mixed."""
from collections import Counter
from pathlib import Path
import sys
import numpy as np

from agents.sherlock.hybrid_agent import HybridAgent
from agents.sherlock.imitation_agent import canonical_action
from scripts.final_battle_compare import ROOT, WEIGHTS
from scripts.par_eval import build_cfg

# Old scripts/common.py makes its root importable as a convenience for historic CLIs.
# Restore the process search path so new v4 absolute imports still resolve in its tree.
saved_path = sys.path.copy()
try:
    from r3_native.scripts.selective_advice_agent import SelectiveAdviceAgent
    from r3_native.scripts.par_eval import build_cfg as original_r3_cfg
finally:
    sys.path[:] = saved_path

R3_MODEL = ROOT / "experiments/candidates/movement_dagger_20261115/r3_soft.pth"
V4_MODEL = ROOT / "experiments/candidates/umbau_20261115/student_v4.pth"


def make_r3(side):
    actor = SelectiveAdviceAgent(side, agent_path=str(WEIGHTS), advice_path=str(R3_MODEL),
                                 cfg=original_r3_cfg(str(WEIGHTS), []), mode="movement", train=False, seed=0)
    actor.set_to_eval_mode()
    actor.autosave_on_terminate = False
    return actor


def make_v4(side):
    return HybridAgent(side, str(WEIGHTS), str(V4_MODEL), mode="mixed", combat_radius=5,
                       student_cfg=build_cfg(str(V4_MODEL), ["imit_stay_bias=1.5","imit_unstack=true"]))


def routing(public, team):
    pos = np.asarray(public["units"]["position"])
    observed = np.asarray(public["units_mask"], dtype=bool)
    energy = np.asarray(public["units"]["energy"])[team].reshape(-1)
    live = observed[team] & (energy >= 0)
    foe = 1 - team
    enemy = pos[foe][observed[foe] & np.all(pos[foe] >= 0, axis=1)]
    # Visibility already comes from this player's sliced observation. Geometry is invariant
    # under the game's side-1 reflection; both parents return ready-to-send WORLD commands.
    if not len(enemy) or int(public["match_steps"]) == 0:
        return live, np.zeros_like(live)
    distances = np.abs(pos[team,:,None,:] - enemy[None,:,:]).max(axis=2)
    return live, live & (distances.min(axis=1) <= 5)


def sync(actor, public, final, *, estimator):
    # These optional action-dependent predictors are disabled in both frozen checkpoints.
    # A future checkpoint enabling one requires rebuilding its pending rows from actual commands.
    if actor.cfg.dodge_verify or actor.cfg.dodge_distrust or actor.cfg.dodge_shape or actor.training:
        raise ValueError("Actual-action feedback not registered for these switches")
    if actor._pred_pending or actor._shape_pending:
        raise ValueError("Unexpected action-dependent pending predictions")
    if estimator:
        prev = actor.param_est._prev
        if prev is None:
            raise ValueError("Frozen V14 estimator did not record its real input frame")
        # Old R3 predates record_played_actions(); the estimator consumes this exact world array.
        prev["act"] = np.asarray(final).copy()
    elif actor.param_est._prev is not None:
        raise ValueError("Plain v4 imitation unexpectedly retained an estimator observation")
    ctx = actor._prev_ctx
    if ctx is None:
        return
    # The imitation child uses features from current observations; prior orders are not
    # an input to its network. Still align the per-unit canonical cache of each policy.
    for uid in list(actor._prev_actions):
        world = final[uid]
        a, dx, dy = canonical_action(world, actor.belief.mirrored)
        actor._prev_actions[uid] = a
        actor._sap_hits.pop(uid, None)
        actor._sap_unknown.discard(uid)
        if a == 5:
            target = ctx["ally_pos"][uid] + (dx,dy)
            enemies = ctx["enemy_coords"][ctx["enemy_energies"] >= 0]
            actor._sap_hits[uid] = int(np.sum(np.all(np.abs(enemies-target)<=1, axis=1)))
            pos = np.asarray(public["units"]["position"])[actor.team_id,uid] + world[1:]
            if not public["sensor_mask"][tuple(pos)]:
                actor._sap_unknown.add(uid)


class ContactAgent:
    def __init__(self, side):
        self.r3 = make_r3(side)
        self.v4 = make_v4(side)
        self.new_game(side)

    def new_game(self, player=None):
        if player is not None:
            self.side = player
        self.team = ("player_0","player_1").index(self.side)
        for parent in (self.r3,self.v4):
            parent.new_game(self.side)
        self.counts = Counter()

    def set_env_cfg(self, env_cfg):
        for parent in (self.r3,self.v4):
            parent.set_env_cfg(env_cfg)

    def set_to_eval_mode(self):
        for actor in (self.r3, self.v4.v14, self.v4.student):
            actor.set_to_eval_mode()

    def update(self,*args,**kwargs):
        return

    def act(self,step,obs):
        r = np.asarray(self.r3.act(step,obs))
        v = np.asarray(self.v4.act(step,obs))
        live, near = routing(obs,self.team)
        if r.shape != v.shape or r.shape != (len(live),3):
            raise ValueError("Unexpected parent command matrix")
        final = np.where(near[:,None], v, r)
        if int(obs["match_steps"]):
            changed = np.any(r != v,axis=1)
            self.counts.update(far_unit_turns=int((live & ~near).sum()), near_unit_turns=int(near.sum()),
                               different_near=int((near & changed).sum()), different_far=int((live & ~near & changed).sum()))
        for actor, has_estimator in ((self.r3,True),(self.v4.v14,True),(self.v4.student,False)):
            sync(actor, obs, final, estimator=has_estimator)
        if any(getattr(a,"caught_errors",0) for a in (self.r3,self.v4,self.v4.v14,self.v4.student)):
            raise RuntimeError("An underlying original parent caught an error")
        return final

    def episode_stats(self):
        return dict(self.counts)
