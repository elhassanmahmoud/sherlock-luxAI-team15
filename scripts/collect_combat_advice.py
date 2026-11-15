"""Record Kaggle3 advice on the public observations from real V14 course games.

python -m scripts.collect_combat_advice --first 7271000 --maps 3 --workers 1 --out NEW_DIR
One SideRecord-compatible NPZ per (map, V14 seat). global_step indexes boards;
base_act/base_sdx/base_sdy are the actual V14 orders, in canonical space.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import multiprocessing as mp
import os
from pathlib import Path
import random
import tempfile

import numpy as np

from scripts import imitate
from scripts.fetch_kaggle3 import ARCHIVE_SHA256, TARGET, WEIGHT_SHA256, sha256 as file_sha, verify
from scripts.par_eval import require_no_agent_errors
from scripts.protocol import SIDES

FIRST = 7_271_000
ROTATION = ("kaggle3", "solution92", "v14")
STEPS = 303
V14_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
ROOT = Path(__file__).resolve().parents[1]
ROW_DTYPES = dict(step="int32", pos="int8", uid="int8", feats="float16", mask="bool",
                  act="int8", sdx="int8", sdy="int8", mstep="int16",
                  base_act="int8", base_sdx="int8", base_sdy="int8")


def opponent_for(seed):
    return ROTATION[(seed - FIRST) % len(ROTATION)]


def filename(seed, side):
    return f"g{seed}_{side}_{opponent_for(seed)}.npz"


def canonical_json(value):
    return json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":")).encode()


def protocol():
    from luxai_s3 import env, params, wrappers
    from scripts.kaggle3_opponent import Kaggle3Opponent
    if not callable(getattr(Kaggle3Opponent, "remember_played_actions", None)):
        raise RuntimeError("Kaggle3 adapter lacks played-action synchronization")
    if not verify() or file_sha(imitate.V14) != V14_SHA:
        raise ValueError("Missing or different V14 or Kaggle3 teacher weights")
    files = [*sorted((ROOT / "agents/sherlock").glob("*.py")),
             *sorted((ROOT / "agents/Solution_92_Kaggle").rglob("*.py")),
             *(ROOT / "scripts" / n for n in ("collect_combat_advice.py", "imitate.py", "par_eval.py",
                                               "fetch_kaggle3.py", "common.py", "kaggle3_opponent.py",
                                               "experiment.py", "protocol.py"))]
    return dict(schema=1, source_base="900330260c440d953ac4d6adf20171e827d60c02",
                source_sha256={str(p.relative_to(ROOT)): file_sha(p) for p in files},
                engine_sha256={m.__name__: file_sha(Path(m.__file__)) for m in (env, params, wrappers)},
                v14_sha256=V14_SHA, teacher_version="lux3-bot 0.4.8_fn",
                teacher_archive_sha256=ARCHIVE_SHA256, teacher_weight_sha256=WEIGHT_SHA256,
                teacher_source_sha256={str(p.relative_to(TARGET)): file_sha(p)
                                       for p in sorted(TARGET.rglob("*.py"))},
                steps=STEPS, rotation_origin=FIRST, rotation=ROTATION)


def publish(path, write, validate=None):
    """Hard-link a completed private file. On a concurrent restart accept only a checked winner."""
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".advice-", delete=False) as stream:
        tmp = Path(stream.name)
    try:
        with tmp.open("wb") as f:
            write(f)
        if validate is not None:
            validate(tmp)
        try:
            os.link(tmp, path)
        except FileExistsError:
            return False
        return True
    finally:
        tmp.unlink(missing_ok=True)


def bind_output(out):
    raw = canonical_json(protocol()) + b"\n"
    path = out / "protocol.json"
    publish(path, lambda f: f.write(raw))
    if path.read_bytes() != raw:
        raise ValueError(f"Output is already bound to another source or protocol: {out}")
    return sha256(raw).hexdigest()


def array_digest(arrays):
    digest = sha256()
    for name, value in sorted(arrays.items()):
        digest.update(canonical_json([name, value.dtype.str, list(value.shape)]) + b"\n")
        digest.update(np.ascontiguousarray(value).tobytes())
    return digest.hexdigest()


class AdviceRecord(imitate.SideRecord):
    def __init__(self):
        super().__init__()
        self.global_step, self.base_act, self.base_sdx, self.base_sdy = [], [], [], []

    def capture(self, obs, actor, played, advised):
        from agents.sherlock.cnn_model import map_planes
        from agents.sherlock.imitation_agent import canonical_action
        step, ms = int(obs["steps"]), int(obs["match_steps"])
        if ms == 0:
            if actor._prev_ctx is not None:
                raise ValueError("Expected empty V14 context at match reset")
            return
        cached = actor._cache
        if cached is None or cached[0] != step or cached[1] is not actor._prev_ctx:
            raise ValueError(f"Missing V14 decision cache at {step}")
        _, ctx, cached_ids, feats, masks, saps = cached
        if ctx["step"] != step or ctx["match_step"] != ms:
            raise ValueError("Stale V14 decision context")
        ids = [u for u in cached_ids if ctx["ally_ene"][u] >= 0]
        team = actor.team_id
        own_energy = np.asarray(obs["units"]["energy"])[team].reshape(-1)
        expected = np.flatnonzero(np.asarray(obs["units_mask"])[team] & (own_energy >= 0))
        if ids != expected.tolist():
            raise ValueError("V14 cache omits or duplicates a live ship")
        if not ids:
            return
        fz = (ctx, ids, np.stack([feats[u] for u in ids]), np.stack([masks[u] for u in ids]), saps,
              map_planes(ctx), ctx["ally_pos"][ids])
        self.add(fz, advised, actor.belief.mirrored)
        self.global_step.append(step)
        for uid in ids:
            a, dx, dy = canonical_action(played[uid], actor.belief.mirrored)
            self.base_act.append(a)
            self.base_sdx.append(dx)
            self.base_sdy.append(dy)

    def arrays(self):
        if not self.act:
            raise ValueError("No live V14 decisions recorded")
        return dict(planes=np.stack(self.planes), global_step=np.asarray(self.global_step, np.int16),
                    **{k: np.asarray(getattr(self, k), dtype) for k, dtype in ROW_DTYPES.items()})


def check_archive(path, seed, side, binding, *, student_sha=None):
    rows = list(ROW_DTYPES)
    with np.load(path, allow_pickle=False) as z:
        meta = json.loads(z["meta"].item())
        expected = dict(seed=seed, side=side, opponent=opponent_for(seed), steps=STEPS,
                        policy="v14", teacher="kaggle3", teacher_history="played_v14_actions",
                        protocol_sha256=binding)
        if student_sha is not None:
            expected.update(policy="selective_movement", teacher_history="played_selective_actions",
                            student_sha256=student_sha)
            rows.extend(("played_act","played_sdx","played_sdy"))
        if any(meta.get(k) != v for k, v in expected.items()):
            raise ValueError(f"Archive identity mismatch: {path}")
        arrays = {k: z[k] for k in (*rows, "planes", "global_step")}
    n, frames = len(arrays["act"]), arrays["global_step"]
    if (not n or not len(frames) or len(arrays["planes"]) != len(frames)
            or any(len(arrays[k]) != n for k in rows)
            or len(np.unique(np.stack((arrays["step"], arrays["uid"]), axis=1), axis=0)) != n
            or frames[0] < 0 or frames[-1] >= STEPS or np.any(np.diff(frames) <= 0)
            or not np.array_equal(np.unique(arrays["step"]), np.arange(len(frames)))
            or not np.array_equal(frames[arrays["step"]] % 101, arrays["mstep"])
            or array_digest(arrays) != meta.get("arrays_sha256")):
        raise ValueError(f"Invalid or altered advice data: {path}")
    if student_sha is not None:
        base, played = arrays["base_act"], arrays["played_act"]
        if not np.all((played >= 0) & (played <= 5)):
            raise ValueError("Invalid executed command class")
        nonmovement = (base == 5) | (played == 5)
        for suffix in ("act","sdx","sdy"):
            if not np.array_equal(arrays["played_"+suffix][nonmovement],arrays["base_"+suffix][nonmovement]):
                raise ValueError("Movement adviser changed an actual SAP order")
    return n


def play(env, actor, opp, teacher, seed, side, *, record=None):
    other = SIDES[1 - SIDES.index(side)]
    for p, seat in ((actor, side), (opp, other), (teacher, side)):
        if hasattr(p, "new_game"):
            p.new_game(seat)
    random.seed(seed)
    np.random.seed(seed % 2**32)
    obs, info = env.reset(seed=seed)
    for p in (actor, opp, teacher):
        p.set_env_cfg(info["params"])
    sap_range = int(info["params"]["unit_sap_range"])
    if record is None:
        record = AdviceRecord()
    for step in range(STEPS):
        public = obs[side]
        if int(public["steps"]) != step:
            raise ValueError("Unexpected observation step")
        played = np.asarray(actor.act(step, public)).copy()
        opposing = opp.act(step, obs[other])
        label = teacher.act(step, public)
        require_no_agent_errors(actor, opp)
        require_no_agent_errors(actor, teacher)
        record.capture(public, actor, played, label)
        obs, _, term, trunc, _ = env.step({side: played, other: opposing})
        teacher.remember_played_actions(played)
        done = bool(term[side]) or bool(trunc[side])
        if done != (step == STEPS - 1):
            raise ValueError(f"Expected a 303-step course game, terminal={done} after {step+1}")
    wins = np.asarray(obs[side]["team_wins"]).tolist()
    return record.arrays(), dict(sap_range=sap_range, our_wins=int(wins[SIDES.index(side)]),
                                 opp_wins=int(wins[SIDES.index(other)]))


def worker(job):
    from scripts.experiment import limit_threads
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.kaggle3_opponent import Kaggle3Opponent
    out, keys, binding = job
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        actor = imitate.make_player("v14", "player_0")
        if actor.training or len(actor.extra_q) != 35:
            raise ValueError("Expected evaluation V14 with 36 ensemble members")
        for seed, side in keys:
            path = out / filename(seed, side)
            if not path.exists():
                other = SIDES[1 - SIDES.index(side)]
                opp = imitate.make_player(opponent_for(seed), other)
                teacher = Kaggle3Opponent(side)
                if isinstance(opp, Kaggle3Opponent) and teacher.base.Global is opp.base.Global:
                    raise ValueError("Teacher and opponent share Kaggle history")
                arrays, game = play(env, actor, opp, teacher, seed, side)
                meta = dict(seed=seed, side=side, opponent=opponent_for(seed), steps=STEPS,
                            teacher="kaggle3", policy="v14", teacher_history="played_v14_actions",
                            protocol_sha256=binding, arrays_sha256=array_digest(arrays), **game)
                publish(path, lambda fh: np.savez_compressed(fh, meta=canonical_json(meta).decode(), **arrays),
                        lambda tmp: check_archive(tmp, seed, side, binding))
            n = check_archive(path, seed, side, binding)
            print(f"{path.name}: {n} live-unit recommendations", flush=True)
    finally:
        env.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--first", type=int, default=FIRST)
    ap.add_argument("--maps", type=int, required=True)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.first < FIRST or args.maps < 1 or args.workers < 1:
        ap.error(f"--first >= {FIRST}, positive --maps and --workers required")
    out = imitate._check_out(args.out)
    out.mkdir(parents=True, exist_ok=True)
    binding = bind_output(out)
    pending = []
    for seed in range(args.first, args.first + args.maps):
        for side in SIDES:
            path = out / filename(seed, side)
            if path.exists():
                check_archive(path, seed, side, binding)
            else:
                pending.append((seed, side))
    if pending:
        workers = min(len(pending), args.workers)
        jobs = [(out, pending[i::workers], binding) for i in range(workers)]
        if workers == 1:
            worker(jobs[0])
        else:
            with mp.get_context("spawn").Pool(workers) as pool:
                pool.map(worker, jobs)
    print(f"Complete: {args.maps} maps, {2*args.maps} seat archives; protocol {binding}")


if __name__ == "__main__":
    main()
