"""Test a qualified low-visibility adviser against course opponents with both seats."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import sys

import numpy as np
import torch

from berater import Adviser, HERE, eligible
from sammeln import PACKAGES, ROOT
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.fetch_kaggle3 import verify
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent

RELEASE = ROOT / "experiments/releases" / PACKAGES["v16"][0] / "agent.zip"


def low_maps():
    # Only measurement scheduling sees the seed; the playing policy is passed the public configuration.
    import jax
    sys.path.insert(0, str(HERE.parent / "kartenparameter"))
    from auswerten import generate
    seeds = np.arange(160350000, 160350200, dtype=np.int32)
    sensor = np.asarray(jax.jit(jax.vmap(generate))(seeds))[:, 0]
    low = seeds[sensor <= 2][:40].tolist()
    high = seeds[sensor > 2][:2].tolist()
    if len(low) != 40 or len(high) != 2:
        raise ValueError("Not enough eligible maps")
    return low, high


def cases(low):
    for seed in low:
        for side in ("player_0", "player_1"):
            for rival in ("solution92", "kaggle3", "v16"):
                for arm in (("adviser",) if rival == "v16" else ("original", "adviser")):
                    yield seed, side, rival, arm


class AdviserPlayer:
    def __init__(self, agent, net):
        self.base = agent
        self.net = net
        self.values = [None, None]
        self.changed = 0
        self.alternatives = 0
        policy = self.base._imitation
        if len(policy.extra_nets) != 1:
            raise ValueError("Expected the released two models")
        for slot, member in enumerate((policy.net, policy.extra_nets[0])):
            def capture(*args, original=member.forward_all, index=slot):
                values = original(*args)
                self.values[index] = values[0].detach().numpy()[:, 1:5]
                return values
            member.forward_all = capture

    def __getattr__(self, name):
        return getattr(self.base, name)

    def act(self, step, obs):
        a = self.base.act(step, obs)
        p = self.base._imitation
        data = p.last_fz
        if data is None or int(p.belief.sensor_range) > 2:
            return a
        from sherlock import geometry as g
        ctx, ids, feats, mask, _, _, pos = data
        if ctx["match_idx"] >= 2:
            return a
        legal = mask[:, 1:5]
        allowed = eligible(feats, legal)
        if not allowed.any():
            return a
        real = a[ids, 0]
        move = np.where(real <= 4, real, 0)
        canon = g.MIRROR_DIR[move] if p.belief.mirrored else move
        final = pos + np.stack([g.DIR_DX[canon], g.DIR_DY[canon]], axis=-1)
        old_cells = set(map(tuple, pos))
        planned = set(map(tuple, final))
        with torch.inference_mode():
            change = self.net(torch.from_numpy(feats)).numpy()
        logits = self.values[0] + self.values[1] + change
        logits = np.where(legal, logits, -np.inf)
        top = logits.argmax(1) + 1
        candidates = []
        for k in np.flatnonzero(allowed & (real >= 1) & (real <= 4) & (top != canon)):
            alt = int(top[k])
            dest = (int(pos[k, 0]) + int(g.DIR_DX[alt]), int(pos[k, 1]) + int(g.DIR_DY[alt]))
            if dest in old_cells or dest in planned:
                continue
            margin = float(logits[k, alt-1] - logits[k, canon[k]-1])
            if legal[k, canon[k]-1] and margin >= 0.75:
                candidates.append((margin, -int(ids[k]), alt))
        if not candidates:
            return a
        _, neg_uid, alt = max(candidates)
        out = a.copy()
        out[-neg_uid] = [g.mirror_dir(alt) if p.belief.mirrored else alt, 0, 0]
        self.changed += 1
        self.alternatives += len(candidates)
        return out


def load_model():
    result = json.loads((HERE / "bewegung_offline.json").read_text())
    path = HERE / "bewegungsberater.npz"
    if (not result["eligible"] or not all(result["gates"].values()) or result["checkpoint"] != sha256(path.read_bytes()).hexdigest()
            or result["plan"] != sha256((HERE / "BEWEGUNG.md").read_bytes()).hexdigest()):
        raise ValueError("The offline gate and fixed model are required")
    net = Adviser().eval()
    with np.load(path, allow_pickle=False) as z:
        net.load_state_dict({k: torch.from_numpy(z[k]) for k in z.files}, strict=True)
    return net, result["checkpoint"]


def validate(game):
    if (game["steps"] != 303 or game["point_counting_version"] != 2 or game["our_wins"] + game["opp_wins"] != 3
            or game["game_win"] != int(game["our_wins"] >= 2)):
        raise ValueError("Invalid complete season")


class IdentityPlayer:
    def __init__(self, base, test):
        self.base = base
        self.test = test
        self.decisions = 0

    def __getattr__(self, name):
        return getattr(self.base, name)

    def new_game(self, side):
        for p in (self.base, self.test):
            p.new_game(side)

    def set_env_cfg(self, cfg):
        if cfg["unit_sensor_range"] <= 2:
            raise ValueError("Identity test requires high visibility")
        for p in (self.base, self.test):
            p.set_env_cfg(cfg)

    def act(self, step, obs):
        a, b = self.base.act(step, obs), self.test.act(step, obs)
        if not np.array_equal(a, b):
            raise ValueError("High-visibility original and adviser differ")
        self.decisions += len(a)
        return a


def games(out, offset, stride, identity):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads()
    if sha256(RELEASE.read_bytes()).hexdigest() != PACKAGES["v16"][1] or not verify() or os.getenv("PYTHONHASHSEED") != "0":
        raise ValueError("Experiment identity mismatch")
    net, model_hash = load_model()
    lo, hi = low_maps()
    env = LuxAIS3GymEnv(numpy_output=True)
    out.mkdir(parents=True, exist_ok=True)
    try:
        if identity:
            checks = []
            for seed in hi:
                for side in ("player_0", "player_1"):
                    agent = IdentityPlayer(r3_package_agent(side, RELEASE), AdviserPlayer(r3_package_agent(side, RELEASE), net))
                    rival = make_opponent("solution92", "player_1" if side == "player_0" else "player_0")
                    g = play_game(env, agent, rival, seed, side, train=False)
                    validate(g)
                    require_no_agent_errors(agent.base, rival)
                    require_no_agent_errors(agent.test.base, rival)
                    if agent.decisions != 4848 or agent.test.changed != 0:
                        raise ValueError("Incomplete identity check")
                    checks.append(dict(seed=seed, side=side, triplets=agent.decisions))
            (out / "paritaet.json").write_text(json.dumps(dict(model=model_hash, identical=checks), indent=2) + "\n")
            return
        checks = json.loads((out / "paritaet.json").read_text())
        if checks["model"] != model_hash or len(checks["identical"]) != 4:
            raise ValueError("High visibility check is missing")
        for seed, side, kind, arm in list(cases(lo))[offset::stride]:
            path = out / f"{seed}_{side}_{kind}_{arm}.json"
            if path.exists():
                r = json.loads(path.read_text())
                if r["model"] != model_hash or (r["seed"], r["side"], r["opponent"], r["arm"]) != (seed, side, kind, arm):
                    raise ValueError(f"Existing game mismatch: {path.name}")
                validate(r)
                continue
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)
            other = "player_1" if side == "player_0" else "player_0"
            agent = r3_package_agent(side, RELEASE)
            if arm == "adviser":
                agent = AdviserPlayer(agent, net)
            rival = r3_package_agent(other, RELEASE) if kind == "v16" else make_opponent(kind, other)
            g = play_game(env, agent, rival, seed, side, train=False)
            validate(g)
            require_no_agent_errors(agent, rival)
            if int(agent.env_cfg["unit_sensor_range"]) > 2:
                raise ValueError("Unexpected activity on a high visibility card")
            r = {k: g[k] for k in ("seed","side","steps","point_counting_version","our_wins","opp_wins",
                                    "our_points","opp_points","game_win")}
            r.update(model=model_hash, opponent=kind, arm=arm, changes=getattr(agent, "changed", 0))
            tmp = path.with_suffix(".pending")
            tmp.write_text(json.dumps(r) + "\n")
            tmp.replace(path)
            print(path.name, flush=True)
    finally:
        env.close()


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("out", type=Path)
    cli.add_argument("--offset", type=int, default=0)
    cli.add_argument("--stride", type=int, default=1)
    cli.add_argument("--identity", action="store_true")
    args = cli.parse_args()
    if not 0 <= args.offset < args.stride:
        cli.error("Invalid worker partition")
    games(args.out, args.offset, args.stride, args.identity)
