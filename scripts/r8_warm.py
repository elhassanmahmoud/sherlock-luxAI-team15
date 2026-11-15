"""Two paired 1024-update R3 warm starts. The only differing input is the second replay block."""
import argparse
from collections import Counter
import fcntl
import hashlib
import json
from pathlib import Path
import platform
import tempfile

import numpy as np
import torch
from torch.nn import functional as F

from agents.sherlock.imitation_net import masked_sap_logits
from scripts import imitate
from scripts.collect_combat_advice import ROTATION, SIDES, file_sha
from scripts.experiment import limit_threads
from scripts.r3_diagonal import R3
from scripts.selective_advice_agent import load_heads
from scripts.selective_dagger import mapped_part
from scripts.train_combat_advice import input_index, publish

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "experiments/analysis/movement_dagger_20261115/corpus.json"
HISTORY_SHA = "fed298f9dd84100c119423e2a8d9c5607291a54a028b3ca560b9d454e64d405f"
R1 = "5327d0ff4e2cc4b09bdcb43ae51fbd7dcc9f6d8487f79f4a7cfd1ad176813575"
PROTOCOL = {R1:"50bf0bb810f7b913acce8940937d335ebf180bc796457dcf880ffa6743ec2724",
            R3:"3476e80f57ff23f76fb4d8aa00269e647116ca9c468c0d2d0f6278af85567a03"}
BLOCKS = {"replay":range(7272000,7272048), "control":range(7272048,7272096), "r8":range(7287000,7287048),
          "old_validation":range(7272200,7272224), "new_validation":range(7287100,7287124)}
SEED, UPDATES = 2711, 1024
ARMS = ("control", "r8")


def identities(records):
    return [{k:r[k] for k in ("seed","side","opponent","sha256","protocol")} for r in records]


def index(directory, block):
    parent = R3 if block in ("r8", "new_validation") else R1
    protocol = PROTOCOL[parent]
    if file_sha(directory/"protocol.json") != protocol:
        raise ValueError(f"Wrong collector/parent for {block}")
    keys = [(seed,side) for seed in BLOCKS[block] for side in SIDES]
    records = input_index([directory], {"train":keys, "val":[]}, student_sha=parent)["train"]
    if any(r["protocol"] != protocol for r in records):
        raise ValueError("Undeclared nested collection")
    for r in records:
        with np.load(r["path"],allow_pickle=False) as archive:
            meta = json.loads(archive["meta"].item())
            if (meta.get("raw_teacher_policy")!="pre_fallback_scores_v1"
                    or not {"teacher_action_scores","teacher_frame_status","teacher_selected"}.issubset(archive.files)):
                raise ValueError("Registered raw teacher trace absent: "+r["path"])
    if parent == R1:
        if file_sha(HISTORY) != HISTORY_SHA:
            raise ValueError("Wrong original R1 corpus")
        old = {(r["seed"],r["side"]):r["sha256"] for r in json.loads(HISTORY.read_bytes())["games"]}
        if any(old[r["seed"],r["side"]] != r["sha256"] for r in records):
            raise ValueError("Changed historical archive")
    return records


def sources():
    files = ("scripts/r8_warm.py","scripts/r3_diagonal.py","scripts/imitate.py","scripts/selective_dagger.py",
             "scripts/collect_combat_advice.py","scripts/train_combat_advice.py","scripts/selective_advice_agent.py",
             "agents/sherlock/imitation_net.py","agents/sherlock/cnn_model.py")
    return {f:file_sha(ROOT/f) for f in files}


class HalfBatch:
    """One random cyclic slice per seat and opponent; each 16-update round covers every map and seat."""
    def __init__(self, records, eligible, seed):
        self.rng = np.random.default_rng(seed)
        self.pools = eligible
        self.groups = [[j for j,r in enumerate(records) if (r["opponent"],r["side"]) == (opp,side)]
                       for opp in ROTATION for side in SIDES]
        if (len(eligible)!=len(records) or any(len(g)!=16 for g in self.groups)
                or any(len(rows)<22 for rows in eligible)):
            raise ValueError("Expected 16 complete maps per opponent and eligible unit rows in every seat")
        self.order = []
        self.usage = np.zeros(len(records),np.int64)
        self.trace = hashlib.sha256()

    def draw(self, update):
        if update % 16 == 0:
            self.order = [self.rng.permutation(g) for g in self.groups]
        idx = []
        for group, order in enumerate(self.order):
            opponent, side = divmod(group,2)
            take = 21 + int(opponent == (update + side) % 3)
            j = int(order[update % 16])
            pool = self.pools[j]
            start = int(self.rng.integers(len(pool)))
            selected = pool[(start + np.arange(take)) % len(pool)]
            idx.append(selected)
            self.usage[j] += take
            self.trace.update(selected.astype("<i8",copy=False).tobytes())
        return np.concatenate(idx)

    def summary(self):
        return dict(sampled_rows=int(self.usage.sum()),sampled_rows_by_archive=self.usage.tolist(),
                    sampled_ids_sha256=self.trace.hexdigest())


def loss_for(net, boards, rows, chosen, device):
    # Each distinct game frame in the combined batch goes through the convolution exactly once.
    ids = torch.from_numpy(chosen)
    frames, inv = torch.unique(rows["step"][ids],sorted=True,return_inverse=True)
    inv = inv.to(device)
    pos = rows["pos"][ids].to(device)
    mask = rows["mask"][ids].to(device)
    logits, _, target_map = net.forward_all(boards[frames].to(device,dtype=torch.float32)/imitate.PLANE_SCALE,
                                            inv,pos,rows["feats"][ids].to(device,dtype=torch.float32))
    logits = logits.masked_fill(~mask, -torch.inf)
    loss = imitate.action_loss(logits,rows["act"][ids].to(device),rows["base_act"][ids].to(device))
    shots = rows["sap_label"][ids]
    if bool(shots.any()):
        shot_ids = torch.where(shots)[0].to(device)
        targets = masked_sap_logits(target_map,inv[shot_ids],pos[shot_ids],rows["rng"][ids[shots]].to(device))
        loss = loss + .5 * F.cross_entropy(targets,rows["tgt"][ids[shots]].to(device))
    soft = rows["distill_ok"][ids]
    if bool(soft.any()):
        soft_ids = torch.where(soft)[0].to(device)
        kl = imitate.movement_distillation_loss(logits[soft_ids,:5], rows["movement_scores"][ids[soft]].to(device),
                                                mask[soft_ids,:5],2.0)
        loss = loss + .5 * kl
    return loss, len(frames), int(soft.sum()), int(shots.sum())


def fit(a):
    limit_threads()
    torch.manual_seed(SEED)
    out = imitate._check_out(a.out) / (a.arm + ".pth")
    if any(part in ("weights","releases") for part in out.parts) or file_sha(a.parent) != R3:
        raise ValueError("Use a fresh study output and the fixed R3")
    out.parent.mkdir(parents=True,exist_ok=True)
    with (out.parent/(a.arm+".lock")).open("a") as lock, tempfile.TemporaryDirectory(dir=out.parent) as tmp:
        fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
        if out.exists():
            raise FileExistsError(out)
        code = sources()
        replay = index(a.old,"replay")
        support = index(a.old if a.arm=="control" else a.new,a.arm)
        data, raw, sizes = mapped_part(replay+support, Path(tmp)/"frames",distill_movement=True)
        boards = torch.from_numpy(data)
        rows = {k:torch.from_numpy(v) for k,v in raw.items()}
        imitate.prepare_labels(rows,24,24)
        ends = np.cumsum([0,*sizes])
        allowed = rows["admitted"].numpy()
        pools = [lo+np.flatnonzero(allowed[lo:hi]) for lo,hi in zip(ends,ends[1:])]
        replay_batch = HalfBatch(replay,pools[:len(replay)],SEED)
        support_batch = HalfBatch(support,pools[len(replay):],SEED+1)
        checkpoint = torch.load(a.parent,map_location="cpu",weights_only=True)
        nets, own_tile = load_heads(a.parent)
        if len(nets)!=1 or not own_tile or file_sha(a.parent)!=R3:
            raise ValueError("Warm start requires the exact single R3")
        net = nets[0].to(a.device).train()
        opt = torch.optim.AdamW(net.parameters(),lr=1e-4,weight_decay=1e-4)
        counts = Counter()
        for step in range(UPDATES):
            left, right = replay_batch.draw(step), support_batch.draw(step)
            selected = np.concatenate((left,right))
            if len(left)!=128 or len(right)!=128 or len(np.unique(selected))!=256 or not allowed[selected].all():
                raise ValueError("Invalid realized minibatch")
            opt.zero_grad(set_to_none=True)
            loss, frames, soft, shots = loss_for(net,boards,rows,selected,a.device)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(),1.,error_if_nonfinite=True)
            opt.step()
            counts.update(soft_replay_rows=int(raw["distill_ok"][left].sum()),
                          soft_support_rows=int(raw["distill_ok"][right].sum()))
            counts.update(updates=1,rows=len(selected),unique_frames_per_update_summed=frames,soft_rows=soft,
                          sap_target_rows=shots)
            if (step+1)%128==0:
                print(f'{a.arm} {step+1}/{UPDATES}, loss {loss.item():.5f}',flush=True)
        counts["policy_adam_steps"] = int(opt.state[net.pi.weight]["step"].item())
        if (counts["updates"]!=UPDATES or counts["policy_adam_steps"]!=UPDATES or counts["soft_rows"]<=0
                or counts["sap_target_rows"]<=0 or min(counts["soft_replay_rows"],counts["soft_support_rows"])<=0
                or counts["soft_rows"]!=counts["soft_replay_rows"]+counts["soft_support_rows"]
                or counts["rows"]!=UPDATES*256 or sources()!=code
                or file_sha(a.parent)!=R3):
            raise ValueError("Training identity or real update counts failed")
        training = dict(kind="r8_dagger_warm_v1",arm=a.arm,parent_sha256=R3,seed=SEED,steps=UPDATES,lr=.0001,
                        optimizer="AdamW",weight_decay=.0001,clip=1.,sap_target_weight=.5,movement_kl_weight=.5,
                        movement_temperature=2.,device=a.device,torch=str(torch.__version__),numpy=np.__version__,
                        python=platform.python_version(),sources=code,counts=dict(counts),
                        inputs=dict(replay=identities(replay),support=identities(support)),
                        replay=replay_batch.summary(),support=support_batch.summary())
        output = {k:checkpoint[k] for k in ("kind","arch","cfg","feature_dim","sap_own_tile")}
        output.update(policy=net.cpu().eval().state_dict(),warm_training=training)
        def save(path):
            with path.open("wb") as stream:
                torch.save(output,stream)
        publish(out,save)
        print(f'{out} {file_sha(out)}',flush=True)


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("arm",choices=ARMS)
    for name in ("parent","old","new","out"):
        p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--device",choices=("cpu","mps"),default="cpu")
    fit(p.parse_args())
