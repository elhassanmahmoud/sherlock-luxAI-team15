"""One fixed on-policy data aggregation round for the V14 movement adviser; no teacher at deployment."""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from scripts import collect_combat_advice as collect, imitate
from scripts.selective_advice_agent import SelectiveAdviceAgent
from scripts.train_combat_advice import input_index, make_plan


class RecordingMovement(SelectiveAdviceAgent):
    def _advise(self, step, obs, base):
        # Exactly the completed V14 command on the same state and actual mixed history.
        self.v14_command = base.copy()
        return super()._advise(step, obs, base)


class MixedRecord(collect.AdviceRecord):
    def __init__(self):
        super().__init__()
        self.executed = []

    def capture(self, obs, actor, played, advised):
        from agents.sherlock.imitation_agent import canonical_action
        first = len(self.uid)
        super().capture(obs, actor, actor.v14_command, advised)
        self.executed.extend(canonical_action(played[u], actor.belief.mirrored) for u in self.uid[first:])

    def arrays(self):
        arrays = super().arrays()
        actions = np.asarray(self.executed, dtype=np.int8)
        for i, key in enumerate(("played_act","played_sdx","played_sdy")):
            arrays[key] = actions[:,i]
        return arrays


def bind(out, parent_sha):
    cfg = collect.protocol()
    cfg.update(policy="selective_movement", teacher_history="played_selective_actions", student_sha256=parent_sha)
    for name in ("selective_dagger.py", "selective_advice_agent.py", "combat_teacher_counterfactual.py"):
        cfg["source_sha256"]["scripts/"+name] = collect.file_sha(Path(__file__).with_name(name))
    raw = collect.canonical_json(cfg) + b"\n"
    path = out/"protocol.json"
    collect.publish(path, lambda f: f.write(raw))
    if path.read_bytes() != raw:
        raise ValueError("Existing collection belongs to a different parent, source or protocol")
    return collect.sha256(raw).hexdigest()


def worker(job):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.experiment import limit_threads
    from scripts.kaggle3_opponent import Kaggle3Opponent
    out, parent, parent_sha, binding, keys = job
    limit_threads()
    if collect.file_sha(parent) != parent_sha:
        raise ValueError("Parent checkpoint changed")
    actor = RecordingMovement("player_0", agent_path=str(imitate.V14), cfg=imitate.v14_cfg(),
                              advice_path=str(parent), mode="movement", train=False, seed=0)
    actor.set_to_eval_mode()
    if collect.file_sha(parent) != parent_sha:
        raise ValueError("Parent checkpoint changed while loading")
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for seed, side in keys:
            path = out/collect.filename(seed,side)
            opponent = collect.opponent_for(seed)
            opp = imitate.make_player(opponent, f"player_{1-int(side[-1])}")
            teacher = Kaggle3Opponent(side)
            if isinstance(opp,Kaggle3Opponent) and teacher.base.Global is opp.base.Global:
                raise ValueError("Teacher and opponent share game history")
            arrays, game = collect.play(env, actor, opp, teacher, seed, side, record=MixedRecord())
            meta = dict(seed=seed, side=side, opponent=opponent, steps=collect.STEPS, teacher="kaggle3",
                        policy="selective_movement", teacher_history="played_selective_actions",
                        student_sha256=parent_sha, protocol_sha256=binding, arrays_sha256=collect.array_digest(arrays), **game)
            collect.publish(path, lambda f: np.savez_compressed(f, meta=collect.canonical_json(meta).decode(), **arrays),
                            lambda tmp: collect.check_archive(tmp,seed,side,binding,student_sha=parent_sha))
            n = collect.check_archive(path,seed,side,binding,student_sha=parent_sha)
            print(f"{path.name}: {n} on-policy rows",flush=True)
    finally:
        env.close()


def plans(a):
    original = make_plan(7271000,32,7271032,8)
    mixed = make_plan(a.train_first,a.train_count,a.val_first,a.val_count)
    if {k for keys in original.values() for k in keys} & {k for keys in mixed.values() for k in keys}:
        raise ValueError("Mixed and original maps must be disjoint")
    return original, mixed


def collect_mixed(a):
    _, mixed = plans(a)
    out = imitate._check_out(a.out)
    out.mkdir(parents=True, exist_ok=True)
    parent_sha = collect.file_sha(a.parent)
    binding = bind(out,parent_sha)
    pending = []
    for seed,side in mixed["train"]+mixed["val"]:
        path = out/collect.filename(seed,side)
        if path.exists():
            collect.check_archive(path,seed,side,binding,student_sha=parent_sha)
        else:
            pending.append((seed,side))
    if pending:
        n = min(a.workers,len(pending))
        jobs = [(out,a.parent,parent_sha,binding,pending[i::n]) for i in range(n)]
        if n == 1:
            worker(jobs[0])
        else:
            with mp.get_context("spawn").Pool(n) as pool:
                pool.map(worker,jobs)


def mapped_part(records, path):
    """Disk map for the 16 int8 board channels; allocate row columns once, one decompressed archive at a time."""
    sizes = []
    for record in records:
        with np.load(record["path"],allow_pickle=False) as z:
            sizes.append((len(z["global_step"]),len(z["act"])))
    boards = np.memmap(path,mode="w+",dtype=np.int8,shape=(sum(b for b,_ in sizes),16,24,24))
    n = sum(u for _,u in sizes)
    widths = dict(step=(),pos=(2,),feats=(79,),mask=(6,),act=(),sdx=(),sdy=(),base_act=())
    rows = {k: np.empty((n,*shape), np.int64 if k=="step" else collect.ROW_DTYPES[k]) for k,shape in widths.items()}
    b0 = u0 = 0
    for r,(b,u) in zip(records,sizes):
        filename = Path(r["path"])
        if collect.file_sha(filename) != r["sha256"]:
            raise ValueError(f"Archive changed before training: {filename}")
        with np.load(filename,allow_pickle=False) as z:
            boards[b0:b0+b] = z["planes"]
            for key,target in rows.items():
                target[u0:u0+u] = z[key]
            rows["step"][u0:u0+u] += b0
        b0 += b
        u0 += u
    return boards, rows, [u for _,u in sizes]


def train_mixed(a):
    from agents.sherlock.ppo_agent import save_policy
    from scripts.experiment import limit_threads
    limit_threads()
    base_plan, mixed_plan = plans(a)
    parent_sha = collect.file_sha(a.parent)
    out = imitate._check_out(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    log_path = out.with_suffix(".log")
    if out.exists() or log_path.exists():
        raise ValueError("Provide a new checkpoint and log path")
    if collect.file_sha(imitate.V14) != collect.V14_SHA:
        raise ValueError("V14 config source differs")
    original = input_index(a.original_data,base_plan)
    mixed = input_index(a.mixed_data,mixed_plan,student_sha=parent_sha)
    with log_path.open("x") as f:
        f.write(f"Movement adviser parent SHA256 {parent_sha}\n")
    def log(msg):
        print(msg,flush=True)
        with log_path.open("a") as f:
            f.write(msg+"\n")
    with tempfile.TemporaryDirectory(prefix=".dagger-boards-",dir=out.parent) as tmp:
        train_boards, train_rows, _ = mapped_part(original["train"]+mixed["train"], Path(tmp)/"train.int8")
        val_boards,val_rows, val_sizes = mapped_part(original["val"]+mixed["val"],Path(tmp)/"val.int8")
        cut = sum(val_sizes[:len(original["val"])])
        cfg = SimpleNamespace(device=a.device, seed=2711,ch=32,blocks=3,hidden=128,mb=256,epochs=5,
                              lr=0.001,sap_weight=0.5,validation_groups=[
                                  ("eight original V14 maps",0,cut),("held-out mixed maps",cut,sum(val_sizes))])
        log(f"Train: {len(train_rows['act'])} rows; validation: {cut} V14 + {sum(val_sizes)-cut} mixed rows")
        log(f"CPU board storage: {train_boards.nbytes+val_boards.nbytes} bytes in temporary disk files")
        net = imitate.train_student((train_boards,train_rows),(val_boards,val_rows),cfg,log)
        candidate = Path(tmp)/"student.pth"
        identity = {k: {split:[{field:r[field] for field in ("seed","side","sha256","protocol")} for r in records]
                        for split,records in index.items()} for k,index in (("original",original),("mixed",mixed))}
        save_policy(str(candidate),net,imitate.v14_cfg(),extra=dict(kind="imitation",sap_own_tile=True,epochs=5,
                    teacher="kaggle3 lux3-bot 0.4.8_fn",selective_training=dict(parent_sha256=parent_sha,
                    initialized_from="fixed random seed 2711", inputs=identity, combat_action_weight=3, other_action_weight=1,
                    target_weight=0.5,mb=256,seed=2711,lr=.001,lr_schedule="OneCycleLR",optimizer="AdamW")))
        os.link(candidate,out)
    log(f"Saved {out} {collect.file_sha(out)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    cmd = ap.add_subparsers(dest="command",required=True)
    coll, fit = cmd.add_parser("collect"), cmd.add_parser("train")
    for sub in (coll,fit):
        sub.add_argument("--parent",type=Path,required=True)
        sub.add_argument("--out",type=Path,required=True)
        for name,value in (("train-first",7272000),("train-count",120),("val-first",7272200),("val-count",24)):
            sub.add_argument("--"+name,type=int,default=value)
    coll.add_argument("--workers",choices=(1,2),type=int,default=1)
    fit.add_argument("--original-data",type=Path,nargs="+",required=True)
    fit.add_argument("--mixed-data",type=Path,nargs="+",required=True)
    fit.add_argument("--device",choices=("auto","cpu","mps"),default="auto")
    a = ap.parse_args()
    (collect_mixed if a.command=="collect" else train_mixed)(a)


if __name__ == "__main__":
    main()
