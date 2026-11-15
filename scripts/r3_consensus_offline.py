"""Compare a single preset agreement rule against the diagonal on the 48 known R3 validation archives."""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import numpy as np
import torch

from scripts.experiment import limit_threads
from scripts.imitate import PLANE_SCALE, prepare_labels
from scripts.r3_diagonal import DIRECTIONS,R3,decision_counts,digest,played_action
from scripts.r3_view_consensus import proposals,scores
from scripts.selective_advice_agent import load_heads
from scripts.train_combat_advice import publish_json

REFERENCE="3f05bde9320d9c718e404d2280590f76ab5de823c9fdea594f564433bbcc54de"
SEEDS=range(7287100,7287124)
ROOT=Path(__file__).resolve().parents[1]


def counters(before,after,agree,base,teacher):
    veto=before!=after
    gain=veto & (after==teacher)
    lost=veto & (before==teacher)
    if (veto & ((after!=base) | agree | (before==5) | (after==5))).any():
        raise ValueError("Only disagreement-driven movement fallback is permitted")
    masks=dict(rows=torch.ones_like(veto),view_disagrees=~agree,diagonal_changed=before!=base,
               consensus_changed=after!=base,changed_by_consensus=veto,gained=gain,lost=lost,neutral=veto & ~gain & ~lost)
    for name,action in (("diagonal",before),("consensus",after)):
        masks[name+"_correct"]=action==teacher
        masks[name+"_helped_v14"]=(action==teacher) & (base!=teacher)
        masks[name+"_hurt_v14"]=(action!=teacher) & (base==teacher)
    return masks


@torch.inference_mode()
def measure(net,path):
    with np.load(path,allow_pickle=False) as z:
        board=torch.from_numpy(z["planes"])
        actual=torch.from_numpy(z["played_act"])
        rows={k:torch.from_numpy(z[k]) for k in ("step","pos","feats","mask","act","base_act","sdx","sdy")}
    prepare_labels(rows,*board.shape[-2:])
    steps=rows["step"].numpy()
    measured=Counter()
    directions={d:Counter() for d in DIRECTIONS}
    audit=Counter()
    for start in range(0,len(board),24):
        stop=min(len(board),start+24)
        span=slice(*np.searchsorted(steps,(start,stop)))
        views=scores(net,board[start:stop].float()/PLANE_SCALE,rows["step"][span].long()-start,
                     rows["pos"][span],rows["feats"][span].float())
        mask,base,label=rows["mask"][span],rows["base_act"][span],rows["act"][span]
        original=played_action(views[0],mask,base)
        old,new,agree=proposals(*views,mask,base)
        actual_r3=actual[span]
        audit.update(rows=len(label),r3_correct=int((original==label).sum()),v14_correct=int((base==label).sum()),
                     actual_r3_correct=int((actual_r3==label).sum()),reconstructed_r3_differs_from_actual=int((actual_r3!=original).sum()),
                     r3_hurt_correct_v14=int(((base==label)&(original!=label)).sum()))
        for name,bit in counters(old,new,agree,base,label).items():
            counts=torch.bincount(label[bit],minlength=6).tolist()
            measured[name]+=sum(counts)
            for d,x in zip(DIRECTIONS,counts): directions[d][name]+=x
    return audit,measured,directions


def checks(c):
    if c["changed_by_consensus"]!=c["gained"]+c["lost"]+c["neutral"]:
        raise ValueError("Incomplete intervention partitions")
    if c["consensus_correct"]-c["diagonal_correct"]!=c["gained"]-c["lost"]:
        raise ValueError("Unpaired agreement difference")
    if c["diagonal_changed"]-c["consensus_changed"]!=c["changed_by_consensus"]:
        raise ValueError("Not all differences are reverts to V14")
    if c["diagonal_hurt_v14"]-c["consensus_hurt_v14"]!=c["gained"]:
        raise ValueError("Every recovered label must be a formerly correct V14 command")
    return dict(different_final_class=c["changed_by_consensus"]>0,more_correct_reverts=c["gained"]>c["lost"])


def run(a):
    if a.out.exists(): raise FileExistsError(a.out)
    if digest(a.model)!=R3 or digest(a.reference)!=REFERENCE: raise ValueError("Frozen inputs required")
    ref=json.loads(a.reference.read_bytes())
    refs=[r for r in ref["archives"] if r["cohort"]=="new_validation"]
    expected={(s,f"player_{t}") for s in SEEDS for t in (0,1)}
    if len(refs)!=48 or {(r["seed"],r["side"]) for r in refs}!=expected:
        raise ValueError("Incomplete independent validation reference")
    files={r["sha256"]:a.data/f"g{r['seed']}_{r['side']}_{r['opponent']}.npz" for r in refs}
    if len(files)!=48 or any(digest(f)!=h for h,f in files.items()): raise ValueError("Archive content changed")
    hashed=("scripts/r3_diagonal.py","scripts/r3_view_consensus.py","scripts/r3_consensus_offline.py",
            "scripts/selective_advice_agent.py","scripts/combat_teacher_counterfactual.py","scripts/imitate.py",
            "agents/sherlock/imitation_net.py","agents/sherlock/cnn_model.py","agents/sherlock/features.py",
            "experiments/analysis/r3_view_consensus_20261115/PLAN.md")
    source={f:digest(ROOT/f) for f in hashed}
    limit_threads()
    heads,_=load_heads(a.model)
    if len(heads)!=1: raise ValueError("One original R3 required")
    groups=defaultdict(Counter)
    by_map=defaultdict(Counter)
    by_dir=defaultdict(Counter)
    cases=[]
    truth=Counter()
    for ref_case in refs:
        r=ref_case
        control,c,directions=measure(heads[0],files[r["sha256"]])
        if {k:r["counts"][k] for k in control}!=control: raise ValueError(f"Changed original R3 on {r['seed']} {r['side']}")
        checks(c)
        groups[r["opponent"]].update(c)
        by_map[r["seed"]].update(c)
        for d,v in directions.items(): by_dir[d].update(v)
        truth.update(control)
        cases.append({**{k:r[k] for k in ("seed","side","opponent","sha256")},"original":control,"measured":c,
                      "by_teacher_direction":directions})
    total=sum(groups.values(),Counter())
    if (truth["rows"],truth["r3_correct"],truth["reconstructed_r3_differs_from_actual"])!=(160863,109585,164):
        raise ValueError("Incomplete published R3 check")
    eligibility=checks(total)
    if (digest(a.model)!=R3 or digest(a.reference)!=REFERENCE or any(digest(f)!=h for h,f in files.items())
            or any(digest(ROOT/f)!=v for f,v in source.items())): raise ValueError("Changed sources during audit")
    report=dict(source=source,model=R3,reference=REFERENCE,original_reproduction=truth,by_opponent=groups,
                per_map=by_map,by_teacher_direction=by_dir,cases=cases,total=total,offline_criteria=eligibility,
                passes=all(eligibility.values()))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    publish_json(a.out,report)
    print(json.dumps({k:report[k] for k in ("original_reproduction","total","offline_criteria","passes")},indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("model","data","reference","out"): p.add_argument("--"+name,type=Path,required=True)
    run(p.parse_args())
