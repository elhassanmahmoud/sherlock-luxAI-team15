"""The reserved, optional V4 teacher collection. Only collect in an explicitly allocated slot."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import fcntl
import hashlib
from importlib import metadata, util
import json
import multiprocessing
import os
from pathlib import Path
import platform
import random
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
STUDENT = ROOT / "experiments/candidates/umbau_20261115/student_v4.pth"
SET = ["imit_stay_bias=1.5", "imit_unstack=true"]
OPP = ("kaggle3", "v14", "solution92")
SIDES = ("player_0", "player_1")
REF = "d609183ea6d0ceb416687418613970a8ca2e53e3"
ROWS = dict(pos=("int8", (2,)), uid=("int8", ()), feats=("float16", (79,)), mask=("bool", (6,)),
            act=("int8", ()), sdx=("int8", ()), sdy=("int8", ()), mstep=("int16", ()), step=("int32", ()))


def insist(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=1, allow_nan=False) + "\n").encode()


def publish(path, value):
    data = encoded(value)
    if path.exists():
        insist(path.read_bytes() == data, f"Existing evidence changed: {path}")
        return
    with tempfile.NamedTemporaryFile(dir=path.parent) as tmp:
        tmp.write(data)
        tmp.flush()
        os.link(tmp.name, path)


def roster():
    rng = random.Random(7172000)
    return [(seed, rng.choice(SIDES), rng.choices(OPP, (.6, .2, .2))[0]) for seed in range(7172000, 7172400)]


def filename(key):
    seed, side, opp = key
    return f"g{seed}_{side}_{opp}_dagger.npz"


class PublicChecks:
    """Observe the original student's cache and the three actual match clocks; never call an actor."""
    def __init__(self, student):
        insist(student.cfg.imit_stay_bias == 1.5 and student.cfg.imit_unstack is True and
               not student.training and not student.sample and student.has_sap_head and
               not student.extra_nets and not student.autosave_on_terminate, "Unexpected V4 actor/config")
        self.feedback = 0
        self.alive_masks = []
        self.commands = hashlib.sha256()
        self.teacher = hashlib.sha256()
        self.canonical = hashlib.sha256()
        self.team = student.team_id

    def before(self, step, obs, fz, played, advised):
        insist(int(obs["steps"]) == self.feedback == step and int(obs["match_steps"]) == step % 101, "Clock mismatch")
        for arr, h in ((played, self.commands), (advised, self.teacher)):
            insist(arr.shape == (16, 3) and arr.dtype.kind in "iu" and np.all((arr[:, 0] >= 0) & (arr[:, 0] <= 5))
                    and np.all((arr >= -32768) & (arr < 32768)), "Invalid world command")
            h.update(np.ascontiguousarray(arr, dtype="<i2").tobytes())
        energy = np.asarray(obs["units"]["energy"])[self.team].reshape(16)
        live = np.asarray(obs["units_mask"])[self.team] & (energy >= 0)
        uids = np.flatnonzero(live).tolist() if step % 101 else []
        captured = [] if fz is None else [int(u) for u in fz[1] if fz[0]["ally_ene"][u] >= 0]
        insist(uids == captured, f"Missing/unexpected live unit at step {step}")
        self.alive_masks.append(sum(1 << u for u in uids))
        if uids:
            labels = advised[uids].astype(np.int16, copy=True)
            shots = labels[:,0] == 5
            labels[~shots,1:] = 0
            if self.team == 1:
                labels[~shots,0] = np.asarray([0,2,1,4,3])[labels[~shots,0]]
                labels[shots,1:] = -labels[shots,1:][:,::-1]
            self.canonical.update(np.ascontiguousarray(labels,dtype="<i2").tobytes())

    def result(self, student, opp, step):
        from scripts.par_eval import require_no_agent_errors
        require_no_agent_errors(student, opp)
        insist(self.feedback == step == len(self.alive_masks) == 303, "Incomplete game or teacher feedback")
        return dict(steps=step, acknowledged=self.feedback, live_masks=self.alive_masks,
                    played_sha256=self.commands.hexdigest(), teacher_sha256=self.teacher.hexdigest(),
                    canonical_teacher_sha256=self.canonical.hexdigest(), student_set=SET, source_protocol_sha256=os.environ["SHERLOCK_OPTIONAL_DAGGER_PROTOCOL"])


def check_npz(path, key, protocol_hash):
    with np.load(path, allow_pickle=False) as z:
        insist(set(z.files) == {*ROWS, "planes", "meta"}, "Unexpected NPZ fields")
        meta = json.loads(z["meta"].item())
        board = z["planes"]
        arr = {k: z[k] for k in ROWS}
    seed, side, opp = key
    expected = dict(seed=seed, side=side, opponent=opp, dagger=True, teacher_history="played_student_actions",
                    row_filter="unit_energy>=0", steps=303, acknowledged=303, student_set=SET,
                    source_protocol_sha256=protocol_hash)
    insist(all(meta.get(k) == v for k, v in expected.items()), f"Wrong collection identity for {key}")
    insist(sum(meta[k] for k in ("student_wins", "opp_wins")) == 3 and
           all(type(meta[k]) is int and 0 <= meta[k] <= 3 for k in ("student_wins", "opp_wins")), "Wrong result")
    insist(np.isfinite(meta["rollout_seconds"]) and meta["rollout_seconds"] > 0, "Bad rollout time")
    for k in ("played_sha256", "teacher_sha256"):
        insist(len(meta[k]) == 64 and len(bytes.fromhex(meta[k])) == 32, "Missing world command digest")
    masks = meta["live_masks"]
    insist(len(masks) == 303 and masks[::101] == [0, 0, 0] and
           all(type(x) is int and 0 <= x < 65536 for x in masks), "Bad public live unit masks")
    frames = np.array([i for i, bits in enumerate(masks) if bits], dtype=int)
    steps, uids = zip(*[(j, u) for j, step in enumerate(frames) for u in range(16) if masks[step] & (1 << u)])
    n = len(uids)
    insist(board.shape == (len(frames), 16, 24, 24) and board.dtype == np.int8, "Invalid board stream")
    insist(all(arr[k].shape == (n, *tail) and arr[k].dtype == kind for k, (kind, tail) in ROWS.items()),
           "Invalid training shapes/dtypes")
    insist(np.array_equal(arr["step"], steps) and np.array_equal(arr["uid"], uids)
           and np.array_equal(arr["mstep"], frames[arr["step"]] % 101), "Missing/duplicate UID or wrong match step")
    pos, act, feats = arr["pos"].astype(int), arr["act"], arr["feats"].astype(np.float32)
    dx, dy = arr["sdx"].astype(int), arr["sdy"].astype(int)
    insist(np.isfinite(feats).all() and np.all((pos >= 0) & (pos < 24)) and
           np.all((act >= 0) & (act < 6)) and arr["mask"][:, 0].all(), "Undecodable training row")
    energy, cost, radius = np.rint(feats[:, [2, 7, 8]] * [400, 50, 7]).astype(int).T
    insist(np.array_equal(np.rint(feats[:,:2] * 24),pos),"Position/feature mismatch")
    labels = np.stack((act,dx,dy),axis=1).astype("<i2")
    insist(hashlib.sha256(labels.tobytes()).hexdigest() == meta["canonical_teacher_sha256"],
           "Recorded labels differ from the teacher's original world commands")
    shot = act == 5
    insist(np.all(energy >= 0) and np.all(cost > 0) and np.all(radius >= 1) and
           np.all((dx[~shot] == 0) & (dy[~shot] == 0)), "Bad unit features or non-SAP offset")
    target = pos + np.stack((dx, dy), axis=1)
    legal_shot = shot & (energy >= cost) & (np.maximum(abs(dx), abs(dy)) <= radius) & ((target >= 0) & (target < 24)).all(1)
    admitted = (arr["mask"][np.arange(n), act] & ~shot) | legal_shot
    return dict(seed=seed, side=side, opponent=opp, rows=n, boards=len(frames), sha256=digest(path),
                rollout_seconds=meta["rollout_seconds"],
                student_wins=meta["student_wins"], opp_wins=meta["opp_wins"], admitted=int(admitted.sum()),
                sap=int(shot.sum()), legal_sap=int(legal_shot.sum()), own_tile_sap=int((legal_shot & (dx==0) & (dy==0)).sum()),
                rows_by_match=np.bincount(frames[arr["step"]] // 101, minlength=3).tolist())


def store_game(rec, dest, meta):
    """Atomic directory with the compatible original archive and independently computed hash/receipt."""
    key = (meta["seed"], meta["side"], meta["opponent"])
    tmp = Path(tempfile.mkdtemp(prefix=f'{meta["seed"]}-', dir=dest / "staging"))
    npz = tmp / filename(key)
    count = rec.save(npz, meta)
    proof = check_npz(npz, key, meta["source_protocol_sha256"])
    insist(proof["rows"] == count, "Recorder lost rows")
    (tmp / "receipt.json").write_bytes(encoded(proof))
    tmp.rename(dest / "records" / str(key[0]))
    print("sealed", key, count, flush=True)
    return count


def lane(args):
    index, jobs, out = args
    # Keep the two fixed stripes exclusive even if an interrupted coordinator left a live child.
    with (out / f"lane-{index}.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        remaining = [k for k in jobs if not (out / "records" / str(k[0])).exists()]
        if remaining:
            from scripts.imitate import _dagger_worker
            _dagger_worker((remaining, str(out), str(STUDENT), SET, "v4_extra_7172000"))


def prerequisites(project):
    d = project / "experiments/analysis/umbau_20261115/robustness/run1"
    files = read(d / "assessment.json")
    insist(files["full_games"] == 288 and files["maps"] == 24, "Robustness panel unfinished")
    for arm in ("v14", "v15"):
        base = d / arm
        insist(files["files"][arm] == read(base / "complete.json") ==
               {f: digest(base / f) for f in ("manifest.json", "games.jsonl")}, f"Unsealed robustness arm {arm}")
        data = [json.loads(l) for l in (base / "games.jsonl").read_bytes().splitlines()]
        expected = {(o, s, p) for o in ("sol92_sq", "rush", "dqn") for s in range(7170040, 7170064) for p in SIDES}
        insist(len(data) == 144 and {(r["opponent"],r["seed"],r["side"]) for r in data} == expected and
               all(r["steps"] == 303 and r["our_wins"] + r["opp_wins"] == 3 for r in data), "Incomplete robustness keys")
    return digest(d / "assessment.json")


def provenance():
    pins = read(ROOT / "freeze.json")
    insist(all(digest(ROOT / path) == value for path, value in pins["files"].items()), "Frozen source/weight changed")
    package = Path(util.find_spec("luxai_s3").origin).parent
    env = dict(python=platform.python_version(), architecture=platform.machine(),
               packages={name:metadata.version(name) for name in ("torch","numpy","scipy","jax","jaxlib","gymnasium","luxai-s3")},
               engine={p.name:digest(p) for p in sorted(package.glob("*.py"))})
    return dict(source=REF, freeze_sha256=digest(ROOT / "freeze.json"), model=pins["files"][str(STUDENT.relative_to(ROOT))],
                overrides=SET, rng="random.Random(7172000); choice(P0/P1), choices(kaggle3/v14/solution92; .6/.2/.2)",
                roster=roster(), runtime=env)


def inspect(out, through, protocol_hash, *, deep):
    expected = {k[0]:k for k in roster()}
    receipts = {}
    for d in sorted((out / "records").iterdir()):
        seed = int(d.name)
        key = expected[seed]
        npz = d / filename(key)
        insist(set(d.iterdir()) == {npz, d / "receipt.json"}, f"Unexpected game files in {d}")
        row = read(d / "receipt.json")
        insist((row["seed"], row["side"], row["opponent"]) == key and digest(npz) == row["sha256"],
               "Wrong archive or hash")
        if deep:
            insist(check_npz(npz, key, protocol_hash) == row, f"Stale receipt for {key}")
        receipts[seed] = row
    return [receipts[k[0]] for k in roster()[:through] if k[0] in receipts]


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("operation", choices=("plan", "collect", "validate"))
    cli.add_argument("--project", type=Path, required=True)
    cli.add_argument("--through", type=int, choices=range(25,401,25), default=25)
    cli.add_argument("--workers", type=int, choices=(1,2), default=1)
    args=cli.parse_args()
    project=args.project.resolve()
    out=project / "experiments/imitation/k3_v4_extra_7172000"
    protocol=provenance()
    print("fixed schedule:", sorted(Counter((s,o) for _,s,o in roster()).items()), flush=True)
    if args.operation=="plan":
        print("Only fixed schedule and sources checked. Output:", out)
        return
    protocol["robustness_assessment_sha256"]=prerequisites(project)
    if args.operation=="collect":
        for path in out.parent.rglob("g7172*.npz"):
            if out not in path.parents:
                seed=path.name[1:].split("_",1)[0]
                insist(not seed.isdecimal() or int(seed) not in range(7172000,7172400),
                       f"Reserved seed already present in another local collection: {path}")
        out.mkdir(exist_ok=True)
    lockfile=out / ".collection.lock"
    with lockfile.open("a" if args.operation=="collect" else "rb") as lock:
        fcntl.flock(lock, (fcntl.LOCK_EX if args.operation=="collect" else fcntl.LOCK_SH) | fcntl.LOCK_NB)
        if args.operation=="collect":
            if not (out/"protocol.json").exists():
                insist(set(out.iterdir()) == {lockfile},"Nonempty unbound destination")
            publish(out/"protocol.json", protocol)
            for folder in ("records","staging","data"):
                (out/folder).mkdir(exist_ok=True)
        insist((out/"protocol.json").read_bytes() == encoded(protocol),"Different collection provenance")
        signature = digest(out/"protocol.json")
        done = inspect(out,args.through,signature,deep=args.operation=="validate")
        if args.operation=="collect":
            have = {r["seed"] for r in done}
            missing = [k for k in roster()[:args.through] if k[0] not in have]
            if missing:
                os.environ["SHERLOCK_OPTIONAL_DAGGER_PROTOCOL"]=signature
                for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","VECLIB_MAXIMUM_THREADS","NUMEXPR_NUM_THREADS"):
                    os.environ[key]="1"
                jobs = [(i,[k for k in missing if k[0]%2 == i],out) for i in range(2)]
                with ProcessPoolExecutor(args.workers,mp_context=multiprocessing.get_context("spawn")) as pool:
                    list(pool.map(lane, [j for j in jobs if j[1]]))
            done = inspect(out,args.through,signature,deep=False)
        insist(len(done)==args.through, "Incomplete requested prefix")
        keys = {k[0]:k for k in roster()}
        for r in done:
            seed=r["seed"]
            src=out/"records"/str(seed)/filename(keys[seed])
            target=out/"data"/src.name
            if args.operation=="collect" and not target.exists():
                os.link(src,target)
            insist(target.is_file() and target.samefile(src),"Invalid training input alias")
        aliases={p.name for p in (out/"data").iterdir()}
        allowed={filename(keys[int(d.name)]) for d in (out/"records").iterdir()}
        insist(aliases <= allowed,"Unexpected file in training input directory")
        index=dict(protocol_sha256=signature,files=done,totals={k:sum(r[k] for r in done) for k in
                   ("rows","admitted","sap","legal_sap","own_tile_sap","boards")},games=len(done))
        path=out/f"index-{args.through:03d}.json"
        if args.operation=="collect":
            publish(path,index)
        else:
            insist(path.read_bytes()==encoded(index),"Stored dataset index disagrees")
        print("Verified",len(done),"games,",index["totals"],path,flush=True)


if __name__=="__main__":
    main()
