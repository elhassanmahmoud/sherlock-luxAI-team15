"""For duplicate planned point occupations, consider exactly one legal alternative."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

import numpy as np
import torch

from pruefen import HERE, choices
sys.path.insert(0, str(HERE.parent))
from feldverlauf import PACKAGE, DIGEST, SEEDS
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.fetch_kaggle3 import verify
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent

FIELDS = ("steps", "point_counting_version", "game_win", "our_wins", "opp_wins", "our_points", "opp_points")


class Player:
    def __init__(self, side, observe=False):
        self.base = r3_package_agent(side, PACKAGE)
        self.observe = observe
        self.events = []
        self.logits = [None, None]
        p = self.base._imitation
        if len(p.extra_nets) != 1:
            raise ValueError("Expected first and second V16 member")
        for i, net in enumerate((p.net, p.extra_nets[0])):
            def forward(*args, original=net.forward_all, index=i):
                out = original(*args)
                self.logits[index] = out[0].detach().numpy()
                return out
            net.forward_all = forward

    def __getattr__(self, name):
        return getattr(self.base, name)

    def act(self, step, obs):
        action = self.base.act(step, obs)
        p = self.base._imitation
        fz = p.last_fz
        if fz is None:
            return action
        ctx, ids, feats, masks, _, _, pos = fz
        live = np.array([ctx["ally_ene"][u] >= 0 for u in ids], dtype=bool)
        if live.sum() < 2:
            return action
        from sherlock import geometry as g
        world = action[ids, 0].copy()
        if p.belief.mirrored:
            m = world <= 4
            world[m] = g.MIRROR_DIR[world[m]]
        kept = np.flatnonzero(live)
        options = choices(pos[live], feats[live], masks[live], world[live])
        if not options:
            return action
        from scipy.special import logsumexp
        mask = masks.copy()
        mask[:, 5] = np.asarray([ctx["ally_ene"][u] >= ctx["sap_cost"] for u in ids])
        logp = np.zeros(mask.shape)
        for scores in self.logits:
            valid = np.where(mask, scores, -np.inf)
            logp += valid - logsumexp(valid, axis=1, keepdims=True)
        holders = set(p._point_holder_rows(ctx, ids, pos))
        logp[[i for i in range(len(ids)) if i not in holders], 0] -= float(p.cfg.imit_stay_bias)
        score, neg_uid, neg_alt = max((float(logp[kept[k], alt]), -int(ids[kept[k]]), -alt)
                                      for k, alt in options)
        u, alt = -neg_uid, -neg_alt
        real = g.mirror_dir(alt) if p.belief.mirrored else alt
        self.events.append([int(step), u, int(action[u, 0]), int(real)])
        if self.observe:
            return action
        out = action.copy()
        out[u] = [real, 0, 0]
        return out


def cases(seeds):
    for seed in seeds:
        for side in ("player_0", "player_1"):
            for rival in ("solution92", "kaggle3", "v16"):
                for arm in (("adviser",) if rival == "v16" else ("original", "adviser")):
                    yield seed, side, rival, arm


def run(out, technical, offset, stride):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads()
    if (os.environ.get("PYTHONHASHSEED") != "0" or sha256(PACKAGE.read_bytes()).hexdigest() != DIGEST or not verify()
            or not json.loads((HERE / "archiv.json").read_text())["passes_archive"]):
        raise ValueError("Study identity mismatch")
    version = sha256((HERE / "PLAN.md").read_bytes() + (HERE / "spielen.py").read_bytes() + (HERE / "pruefen.py").read_bytes()).hexdigest()
    out.mkdir(parents=True, exist_ok=True)
    if technical:
        planned = [(s, "player_0", "kaggle3", "observed") for s in SEEDS]
        original = {r["seed"]: r for r in json.loads((HERE.parent / "feldverlauf.json").read_text())["games"]}
    else:
        technical_rows = [json.loads((out / f"{s}_player_0_kaggle3_observed.json").read_text()) for s in SEEDS]
        if not any(r["changes"] for r in technical_rows) or any(r["model"] != version for r in technical_rows):
            raise ValueError("Unmet other opponent gate")
        planned = cases(range(160360000, 160360040))
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for seed, side, rival, arm in list(planned)[offset::stride]:
            dest = out / f"{seed}_{side}_{rival}_{arm}.json"
            if dest.exists():
                old = json.loads(dest.read_text())
                if (old["model"] != version or old["steps"] != 303 or
                        (old["seed"], old["side"], old["opponent"], old["arm"]) != (seed, side, rival, arm)):
                    raise ValueError("Changed trial files")
                continue
            torch.manual_seed(seed)
            player = r3_package_agent(side, PACKAGE) if arm == "original" else Player(side, observe=technical)
            other = "player_0" if side == "player_1" else "player_1"
            enemy = r3_package_agent(other, PACKAGE) if rival == "v16" else make_opponent(rival, other)
            r = play_game(env, player, enemy, seed, side, train=False)
            require_no_agent_errors(player.base if arm != "original" else player, enemy)
            if (r["steps"] != 303 or r["point_counting_version"] != 2 or r["our_wins"] + r["opp_wins"] != 3
                    or r["game_win"] != int(r["our_wins"] >= 2)):
                raise ValueError("Invalid game")
            if technical and any(r[k] != original[seed][k] for k in ("steps","our_points","opp_points","our_wins","opp_wins")):
                raise ValueError("Did not reproduce original diagnostic seat")
            events = [] if arm == "original" else player.events
            row = dict(seed=seed, side=side, opponent=rival, arm=arm, model=version, changes=len(events), events=events,
                       **{k: r[k] for k in FIELDS})
            tmp = dest.with_suffix(".pending")
            tmp.write_text(json.dumps(row) + "\n")
            tmp.replace(dest)
            print(dest.name, flush=True)
    finally:
        env.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("out", type=Path)
    p.add_argument("--technical", action="store_true")
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--stride", type=int, default=1)
    args = p.parse_args()
    if not 0 <= args.offset < args.stride:
        p.error("Invalid lane")
    run(args.out, args.technical, args.offset, args.stride)
