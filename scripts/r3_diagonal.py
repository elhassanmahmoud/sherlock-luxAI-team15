"""Test one frozen R3 movement adviser with two equivalent coordinate views on its archived decisions."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import torch

from agents.sherlock.features import FEATURE_NAMES
from scripts.collect_combat_advice import filename
from scripts.experiment import limit_threads
from scripts.imitate import PLANE_SCALE, prepare_labels
from scripts.selective_advice_agent import SelectiveAdviceAgent, load_heads
from scripts.train_combat_advice import publish_json

R3 = "99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9"
REFERENCE = "6d2cefcc03703596b44b87d0c611e44f015db2ba0fe6fcb708d9e1a1ec2ba523"
ACTIONS = (0,4,3,2,1,5)
DIRECTIONS = ("stay","up","right","down","left","sap")


def swap_feature(name):
    first, _, suffix = name.partition("_")
    compass = {"u":"l","l":"u","r":"d","d":"r"}
    if first in compass:
        return compass[first]+"_"+suffix
    prefix, _, last = name.rpartition("_")
    axes = {"x":"y","y":"x","dx":"dy","dy":"dx"}
    return prefix+"_"+axes[last] if last in axes else name


FEATURES = tuple(FEATURE_NAMES.index(swap_feature(n)) for n in FEATURE_NAMES)


class TwoViews:
    def __init__(self, net):
        self.net, self.arch = net, net.arch
        if self.arch["feat_dim"] != len(FEATURES) or self.arch["in_ch"] != 16 or len(FEATURES) != 79:
            raise ValueError("Expected the R3 16-plane, 79-feature student")

    def pair(self, board, step, pos, features):
        normal = self.net.forward_all(board, step, pos, features)
        mirrored = self.net.forward_all(board.transpose(-1,-2).contiguous(),step,pos[:,[1,0]],features[:,FEATURES])
        return normal, (normal[0] + mirrored[0][:,ACTIONS]) * .5

    def forward_all(self, board, step, pos, features):
        normal, mean_logits = self.pair(board,step,pos,features)
        return mean_logits, normal[1], normal[2]


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


class DiagonalAgent(SelectiveAdviceAgent):
    def __init__(self,*args,advice_path,mode="movement",**kwargs):
        if mode != "movement" or digest(advice_path) != R3:
            raise ValueError("The diagonal study uses only the registered R3 movement weights")
        super().__init__(*args,advice_path=advice_path,mode=mode,**kwargs)
        if len(self.members) != 1:
            raise ValueError("Expected one R3 student")
        self.members = [TwoViews(self.members[0])]


def played_action(logits, mask, base):
    score, action = logits.masked_fill(~mask, -torch.inf).softmax(1).max(1)
    return torch.where((base != 5) & (action != 5) & (score >= .70),action,base)


def decision_counts(issued,base,teacher,played):
    changed = issued != base
    before, after = base == teacher, issued == teacher
    bits = dict(rows=torch.ones_like(changed),changed=changed,base_matches=before,advised_matches=after,
                helped=after & ~before,hurt=before & ~after,changed_both_disagree=changed & ~before & ~after)
    if played is not None:
        parent = played == teacher
        bits.update(parent_played_matches=parent,parent_changed=played!=base,model_recovers_over_parent=~parent & after,
                    parent_matches_lost_by_model=parent & ~after)
    return {k:int(v.sum()) for k,v in bits.items()}


def empty():
    return {"original":Counter(), "reflected":Counter(), "pair":Counter(),
            "by_teacher_direction":{name:Counter() for name in DIRECTIONS}}


def merge(dst, group):
    for k in ("original","reflected","pair"):
        dst[k].update(group[k])
    for name,c in group["by_teacher_direction"].items():
        dst["by_teacher_direction"][name].update(c)


def measure(net,path):
    with np.load(path,allow_pickle=False) as data:
        board = torch.from_numpy(data["planes"])
        keys = ("step","pos","feats","mask","act","sdx","sdy","base_act")
        rows = {k:torch.from_numpy(data[k]) for k in keys}
        old = torch.from_numpy(data["played_act"]) if "played_act" in data else None
    prepare_labels(rows,*board.shape[-2:])
    steps = rows["step"].numpy()
    result = empty()
    for first in range(0,len(board),24):
        end=min(len(board),first+24)
        b=slice(*np.searchsorted(steps,(first,end)))
        normal, logits = net.pair(board[first:end].float()/PLANE_SCALE,rows["step"][b].long()-first,
                                  rows["pos"][b],rows["feats"][b].float())
        base,teacher = rows["base_act"][b],rows["act"][b]
        a,both = (played_action(l,rows["mask"][b],base) for l in (normal[0],logits))
        for name,issued in (("original",a),("reflected",both)):
            result[name].update(decision_counts(issued,base,teacher,None if old is None else old[b]))
        bits = {"rows":torch.ones_like(a,dtype=torch.bool),"changed":a!=both,"gained":(a!=teacher)&(both==teacher),
                "lost":(a==teacher)&(both!=teacher)}
        for key,mask in bits.items():
            counts=torch.bincount(teacher[mask],minlength=6).tolist()
            result["pair"][key] += sum(counts)
            for name,count in zip(DIRECTIONS,counts):
                result["by_teacher_direction"][name][key] += count
    if (result["pair"]["gained"]-result["pair"]["lost"] !=
            result["reflected"]["advised_matches"]-result["original"]["advised_matches"]):
        raise ValueError("Unpaired additional teacher matches")
    return result


def gates(mixed):
    return {"more_additional_teacher_matches":mixed["pair"]["gained"] > mixed["pair"]["lost"],
            "hurt_at_most_original":mixed["reflected"]["hurt"] <= mixed["original"]["hurt"]}


def audit(a):
    limit_threads()
    if a.out.exists():
        raise FileExistsError(a.out)
    if digest(a.model) != R3 or digest(a.reference) != REFERENCE:
        raise ValueError("Different model or archived R3 reference")
    reference = json.loads(a.reference.read_text())
    known = {(r["cohort"],r["seed"],r["side"]):r["counts"] for r in reference["games"]}
    expected = {(name,seed,f"player_{side}") for name,seeds in (("original",range(7271032,7271040)),
                ("mixed",range(7272200,7272224))) for seed in seeds for side in (0,1)}
    checkpoint=torch.load(a.model,weights_only=True,map_location="cpu",mmap=True)
    inputs = checkpoint["selective_training"]["inputs"]
    cases=[(name,r) for name,cohort in inputs.items() for r in cohort["val"]]
    if (reference["model_sha256"] != R3 or set(known) != expected or len(cases)!=64
            or {(name,r["seed"],r["side"]) for name,r in cases} != expected):
        raise ValueError("Wrong map or seat selection")
    nets,_ = load_heads(a.model)
    if len(nets)!=1:
        raise ValueError("Expected a single R3")
    adviser=TwoViews(nets[0])
    groups={name:empty() for name in inputs}
    games=[]
    with torch.inference_mode():
        for name,r in cases:
            key = (name,r["seed"],r["side"])
            paths=[d/filename(*key[1:]) for d in a.data]
            files=[f for f in paths if f.is_file()]
            if len(files)!=1 or digest(files[0])!=r["sha256"]:
                raise ValueError(f"Missing, duplicate or changed archive: {key}")
            measured=measure(adviser,files[0])
            if dict(measured["original"])!=known[key]:
                raise ValueError(f"Original R3 failed exact count reproduction: {key}")
            games.append(dict(cohort=name,**r,**measured))
            merge(groups[name],measured)
    if digest(a.model)!=R3 or digest(a.reference)!=REFERENCE:
        raise ValueError("Registered inputs changed during the comparison")
    checks=gates(groups["mixed"])
    expected_sizes={"original":51048,"mixed":156243}
    if any(groups[k]["pair"]["rows"]!=n for k,n in expected_sizes.items()):
        raise ValueError("Incomplete decision populations")
    source=Path(__file__).resolve().parents[1]
    sources=("scripts/r3_diagonal.py","agents/sherlock/features.py","agents/sherlock/cnn_model.py",
             "agents/sherlock/imitation_net.py","scripts/imitate.py","scripts/selective_advice_agent.py",
             "scripts/combat_teacher_counterfactual.py")
    result=dict(model_sha256=R3,reference_sha256=REFERENCE,sources={f:digest(source/f) for f in sources},
                validation=groups, games=games,offline_checks=checks,passes_offline_gate=all(checks.values()))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    publish_json(a.out,result)
    print(json.dumps({k:v for k,v in result.items() if k!="games"},indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("reference","model","out"):
        parser.add_argument("--"+name,type=Path,required=True)
    parser.add_argument("--data",nargs="+",type=Path,required=True)
    audit(parser.parse_args())
