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
from scripts.selective_advice_agent import HISTORY_KIND, SelectiveAdviceAgent, is_next_frame
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


class RawMixedRecord(MixedRecord):
    def __init__(self,teacher):
        super().__init__()
        self.teacher = teacher
        self.scores, self.selected, self.status = [], [], []

    def capture(self,obs,actor,played,advised):
        first = len(self.uid)
        super().capture(obs,actor,played,advised)
        if int(obs["steps"]) != self.teacher.raw_step or bool(actor.belief.mirrored) != bool(actor.team_id):
            raise ValueError("Teacher policy and canonical V14 frame do not align")
        self.status.append(self.teacher.raw_status)
        for uid in self.uid[first:]:
            self.scores.append(self.teacher.raw_scores[uid].copy())
            self.selected.append(self.teacher.raw_selected[uid])

    def arrays(self):
        return dict(**super().arrays(),teacher_action_scores=np.asarray(self.scores, np.float32),
                    teacher_selected=np.asarray(self.selected,np.int8),teacher_frame_status=np.asarray(self.status,np.int8))


def bind(out, parent_sha, raw_teacher=False):
    cfg = collect.protocol()
    cfg.update(policy="selective_movement", teacher_history="played_selective_actions", student_sha256=parent_sha)
    for name in ("selective_dagger.py", "selective_advice_agent.py", "combat_teacher_counterfactual.py"):
        cfg["source_sha256"]["scripts/"+name] = collect.file_sha(Path(__file__).with_name(name))
    if raw_teacher:
        cfg["raw_teacher_policy"] = "pre_fallback_scores_v1"
        cfg["source_sha256"]["scripts/teacher_policy_trace.py"] = collect.file_sha(Path(__file__).with_name("teacher_policy_trace.py"))
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
    out, parent, parent_sha, binding, keys, raw_teacher = job
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
            if raw_teacher:
                from scripts.teacher_policy_trace import TracedTeacher
                teacher = TracedTeacher(side)
                record = RawMixedRecord(teacher)
            else:
                teacher = Kaggle3Opponent(side)
                record = MixedRecord()
            if isinstance(opp,Kaggle3Opponent) and teacher.base.Global is opp.base.Global:
                raise ValueError("Teacher and opponent share game history")
            arrays, game = collect.play(env, actor, opp, teacher, seed, side, record=record)
            meta = dict(seed=seed, side=side, opponent=opponent, steps=collect.STEPS, teacher="kaggle3",
                        policy="selective_movement", teacher_history="played_selective_actions",
                        student_sha256=parent_sha, protocol_sha256=binding, arrays_sha256=collect.array_digest(arrays), **game)
            if raw_teacher:
                meta["raw_teacher_policy"] = "pre_fallback_scores_v1"
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
    binding = bind(out,parent_sha,a.raw_teacher)
    pending = []
    for seed,side in mixed["train"]+mixed["val"]:
        path = out/collect.filename(seed,side)
        if path.exists():
            collect.check_archive(path,seed,side,binding,student_sha=parent_sha)
        else:
            pending.append((seed,side))
    if pending:
        n = min(a.workers,len(pending))
        jobs = [(out,a.parent,parent_sha,binding,pending[i::n],a.raw_teacher) for i in range(n)]
        if n == 1:
            worker(jobs[0])
        else:
            with mp.get_context("spawn").Pool(n) as pool:
                pool.map(worker,jobs)


def movement_targets(archive, rows, span):
    """Read a teacher trace in its own canonical frame, before applying the board index offset."""
    scores = archive["teacher_action_scores"]
    labels = rows["act"][span]
    legal = rows["mask"][span, :5]
    frames = archive["global_step"][rows["step"][span]]
    valid = archive["teacher_frame_status"][frames] == 1
    valid &= (archive["teacher_selected"] == 1) & np.isfinite(scores).all(axis=1)
    valid &= (rows["base_act"][span] != 5) & (labels >= 0) & (labels < 5)
    valid &= legal[np.arange(len(labels)), labels.clip(0, 4)]
    best = np.where(legal, scores[:, :5], -np.inf).argmax(axis=1)
    valid &= labels == best
    return valid, scores[:, :5]


def fill_previous_enemy(part, global_steps):
    """Fill channel 16 for one complete archive in its original map/seat order."""
    frame = np.asarray(global_steps, dtype=np.int64)
    mstep = frame % 101
    if (part.shape != (len(frame),17,24,24) or not len(frame) or np.any(mstep == 0)
            or np.any(np.diff(frame) <= 0)):
        raise ValueError("Unexpected or unordered stored decision frames")
    part[:,16] = 0
    following = 1 + np.flatnonzero(is_next_frame(frame[1:], mstep[1:], frame[:-1], mstep[:-1]))
    part[following,16] = part[following-1,10]


def mapped_part(records, path, *, distill_movement=False, previous_enemy=False, own_commands=False, combined_movement=False):
    """Map one intervention, or the predeclared pair of R3 targets and R5 inputs."""
    if combined_movement:
        if previous_enemy or not (distill_movement and own_commands):
            raise ValueError("The combined variant needs own commands and soft movement targets")
    elif sum(map(bool, (previous_enemy, distill_movement, own_commands))) > 1:
        raise ValueError("Movement-training variants are separate experiments; select at most one")
    sizes = []
    for record in records:
        with np.load(record["path"],allow_pickle=False) as z:
            sizes.append((len(z["global_step"]),len(z["act"])))
    boards = np.memmap(path,mode="w+",dtype=np.int8,shape=(sum(b for b,_ in sizes),17 if previous_enemy else 16,24,24))
    n = sum(u for _,u in sizes)
    widths = dict(step=(),pos=(2,),feats=(85 if own_commands else 79,),mask=(6,),act=(),sdx=(),sdy=(),base_act=())
    rows = {k: np.empty((n,*shape), np.int64 if k=="step" else collect.ROW_DTYPES[k]) for k,shape in widths.items()}
    if distill_movement:
        # Original archives have hard labels only. A missing/invalid trace contributes zero soft rows.
        rows["distill_ok"] = np.zeros(n, dtype=bool)
        rows["movement_scores"] = np.zeros((n, 5), dtype=np.float32)
    b0 = u0 = 0
    for r,(b,u) in zip(records,sizes):
        filename = Path(r["path"])
        if collect.file_sha(filename) != r["sha256"]:
            raise ValueError(f"Archive changed before training: {filename}")
        with np.load(filename,allow_pickle=False) as z:
            part = boards[b0:b0+b]
            part[:,:16] = z["planes"]
            if previous_enemy:
                fill_previous_enemy(part, z["global_step"])
            span = slice(u0, u0 + u)
            for key in widths:
                if key == "feats" and own_commands:
                    from agents.sherlock.own_command import archive_features
                    rows[key][span, :79] = z[key]
                    rows[key][span, 79:] = archive_features(z)
                else:
                    rows[key][span] = z[key]
            if distill_movement and "teacher_action_scores" in z:
                eligible, scores = movement_targets(z, rows, span)
                rows["distill_ok"][span] = eligible
                rows["movement_scores"][span] = np.where(eligible[:, None], scores, 0.0)
            rows["step"][span] += b0
        b0 += b
        u0 += u
    return boards, rows, [u for _,u in sizes]


def require_r2_inputs(path, metadata):
    """Bind the comparison to exactly the same parents, file hashes, splits and hyperparameters."""
    import torch
    digest = collect.file_sha(path)
    # Read only metadata. R2 weights are never copied into the freshly seeded policy.
    baseline = torch.load(path, map_location="cpu", weights_only=True, mmap=True)
    expected_arch = dict(feat_dim=79,n_actions=6,in_ch=16,ch=32,blocks=3,hidden=128,
                         detach_value=True,sap_head=True)
    if (baseline.get("kind") != "imitation" or baseline.get("epochs") != 5
            or baseline.get("sap_own_tile") is not True or baseline.get("arch") != expected_arch
            or baseline.get("selective_training") != metadata or baseline.get("imitation_ensemble")
            or collect.file_sha(path) != digest):
        raise ValueError("R2 input identity, architecture or training settings differ")
    return digest


def train_mixed(a):
    combined = getattr(a, "combined_controls", None)
    r2_path = getattr(a, "previous_enemy_r2", None)
    history = r2_path is not None
    if history and a.distill_movement:
        raise ValueError("Soft movement targets and previous enemy history are separate experiments")
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
    identity = {k: {split:[{field:r[field] for field in ("seed","side","sha256","protocol")} for r in records]
                    for split,records in index.items()} for k,index in (("original",original),("mixed",mixed))}
    training = dict(parent_sha256=parent_sha, initialized_from="fixed random seed 2711", inputs=identity,
                    combat_action_weight=3, other_action_weight=1, target_weight=0.5, mb=256,
                    seed=2711, lr=.001, lr_schedule="OneCycleLR", optimizer="AdamW")
    if history:
        training["previous_enemy_r2_sha256"] = require_r2_inputs(r2_path, training)
    r2 = getattr(a, "own_command_r2", None)
    extra = {}
    if r2 is not None:
        from scripts import own_command_study
        extra = {"kind": own_command_study.KIND, "feature_dim": 85,
                 "own_command": own_command_study.bind_control(r2, parent_sha, identity)}
    if combined is not None:
        from scripts import combined_movement
        if r2 is None or not a.distill_movement or history:
            raise ValueError("R7 requires soft targets and one own-command input")
        extra["combined_movement"] = combined_movement.bind_controls(combined, parent_sha, identity)
    with log_path.open("x") as f:
        f.write(f"Movement adviser parent SHA256 {parent_sha}\n")
    def log(msg):
        print(msg,flush=True)
        with log_path.open("a") as f:
            f.write(msg+"\n")
    with tempfile.TemporaryDirectory(prefix=".dagger-boards-",dir=out.parent) as tmp:
        train_boards, train_rows, _ = mapped_part(original["train"]+mixed["train"], Path(tmp)/"train.int8",
                                                   distill_movement=a.distill_movement, previous_enemy=history, own_commands=r2 is not None,
                                                   combined_movement=combined is not None)
        val_boards,val_rows, val_sizes = mapped_part(original["val"]+mixed["val"],Path(tmp)/"val.int8", previous_enemy=history, own_commands=r2 is not None)
        cut = sum(val_sizes[:len(original["val"])])
        cfg = SimpleNamespace(device=a.device, previous_enemy=history, own_command_input=r2 is not None, seed=2711,ch=32,blocks=3,hidden=128,mb=256,epochs=5,
                              lr=0.001,sap_weight=0.5,validation_groups=[
                                  ("eight original V14 maps",0,cut),("held-out mixed maps",cut,sum(val_sizes))])
        soft_metadata = {}
        if a.distill_movement:
            multiple = train_rows["mask"][:, :5].sum(axis=1, dtype=np.int8) > 1
            cfg.movement_distillation = dict(temperature=2.0, weight=0.5,
                                             eligible_train_rows=int(train_rows["distill_ok"].sum()),
                                             rows_with_multiple_legal_moves=int((train_rows["distill_ok"] & multiple).sum()),
                                             used_train_rows_per_epoch=[])
            if combined is not None:
                combined_movement.verify_targets(cfg.movement_distillation)
            soft_metadata["movement_distillation"] = cfg.movement_distillation
            log(f"Bewegungs-KL: {cfg.movement_distillation['eligible_train_rows']} geeignete Trainingszeilen, "
                f"davon {cfg.movement_distillation['rows_with_multiple_legal_moves']} mit mindestens zwei legalen Aktionen")
        log(f"Train: {len(train_rows['act'])} rows; validation: {cut} V14 + {sum(val_sizes)-cut} mixed rows")
        log(f"CPU board storage: {train_boards.nbytes+val_boards.nbytes} bytes in temporary disk files")
        net = imitate.train_student((train_boards,train_rows),(val_boards,val_rows),cfg,log)
        training.update(soft_metadata)
        if history:
            training["initial_parity"] = cfg.previous_enemy_initial_parity
        if r2 is not None:
            extra["own_command"]["initial_parity"] = cfg.initial_parity
        if combined is not None:
            combined_movement.verify_fit(extra, training)
        candidate = Path(tmp)/"student.pth"
        save_policy(str(candidate),net,imitate.v14_cfg(),
                    extra=(dict(kind=HISTORY_KIND if history else "imitation", sap_own_tile=True, epochs=5,
                               teacher="kaggle3 lux3-bot 0.4.8_fn", selective_training=training) | extra))
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
    coll.add_argument("--raw-teacher",action="store_true",help="Record original six teacher scores and actual queried unit IDs")
    coll.add_argument("--workers",choices=(1,2),type=int,default=1)
    fit.add_argument("--original-data",type=Path,nargs="+",required=True)
    fit.add_argument("--mixed-data",type=Path,nargs="+",required=True)
    options = fit.add_mutually_exclusive_group()
    options.add_argument("--previous-enemy-r2", type=Path, metavar="R2_CHECKPOINT",
                         help="Add previous observed enemy plane; verify every input against the fixed 16-channel R2")
    options.add_argument("--distill-movement", action="store_true",
                     help="Add temperature-2 KL for selected legal teacher movements with an observed raw policy")
    options.add_argument("--own-command-r2", type=Path,
                     help="Add six previous-issued-order inputs and bind to the exact R2 control checkpoint")
    fit.add_argument("--device",choices=("auto","cpu","mps"),default="auto")
    a = ap.parse_args()
    (collect_mixed if a.command=="collect" else train_mixed)(a)


if __name__ == "__main__":
    main()
