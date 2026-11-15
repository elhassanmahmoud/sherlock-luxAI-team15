"""Rebuild the registration using only stored records. Pass the main project as the first argument."""
from collections import Counter
import csv
import gzip
import json
from pathlib import Path
import sys

import numpy as np
from scripts.r3_v4_wl_plan import GAME, digest


def summarize(project):
    analysis = project / "experiments/analysis"
    data = project / "experiments/imitation/final_20261115_r3_context"
    collected, roster = {}, []
    def source(path):
        collected[str(path.relative_to(project))] = digest(path)
        return path
    def read(path):
        return json.loads(source(path).read_bytes())
    def rows(path):
        return list(map(json.loads, source(path).read_bytes().splitlines()))
    def add(key, rival, group, seq, result):
        roster.append(dict(seed=key[0], side=key[1], opponent=rival, group=group, sequence=seq, expected=result))
    def ordered(wins):
        return "".join("W" if v else "L" for v in wins)
    def score(r):
        return {k:int(r[k]) for k in GAME}
    dev = rows(analysis / "movement_soft_20261115/dev_a_solution/r3/games.jsonl")
    with source(analysis / "kaggle3_20261115/student_hyb_v4_mixed.csv").open() as fp:
        refs = [r for r in csv.DictReader(fp) if r["opponent"] == "solution92"]
    dev = {(r["seed"],r["side"]):r for r in dev}
    refs = {(int(r["seed"]),r["side"]):int(r["our_wins"]) for r in refs}
    assert dev.keys() == refs.keys() and len(dev) == 200
    folder = analysis / "movement_soft_20261115/dev_a_retrace/run1/r3"
    complete = read(folder / "complete.json")
    sequences = {}
    for name,h in complete["files"].items():
        file=folder/name
        assert digest(file)==h
        r=read(file); key=r["seed"],r["side"]
        sequences[key]=ordered(m["final"]["own_won"] for m in r["observation"]["matches"])
    for key,r in sorted(dev.items()):
        if key[0] in (7150079,7150096):
            seq=sequences.get(key,"WWW" if r["wins"]==3 else None)
            assert seq in ("WLL","WWW") and (seq != "WLL" or refs[key]==3)
            add(key,"solution92","dev_a_target" if seq=="WLL" else "neutral",seq,score(r))
    losses=[key for key,r in dev.items() if not r["result"]]
    assert len(losses)==5 and all(key in sequences for key in losses)
    dev_cross = Counter((r["wins"],refs[key]) for key,r in dev.items())
    dev_loss_orders=Counter(sequences[key] for key in losses)
    duels=rows(analysis/"r3_v4_mixed_duel_20261115/run/games.jsonl")
    duelseq={}
    for r in duels:
        key=r["seed"],r["side"]
        assert key not in duelseq and r["steps"]==303
        seq=ordered(m["winner"]==key[1] for m in r["matches"])
        duelseq[key]=seq
        if seq=="WLW":add(key,"v4_mixed","direct_risk",seq,score(r))
    assert len(duelseq)==48
    hard=analysis/"movement_reflection_20261115/last_solution_map/run"
    hard_seq={}
    for arm in ("r3","diagonal","v4"):
        hard_seq[arm]={}
        for s in ("player_0","player_1"):
            r=read(hard/f"{arm}_{s}.json")
            trace=source(hard/f"{arm}_{s}.json.gz")
            assert digest(trace)==r["timeline_sha256"]
            with gzip.open(trace,"rt") as fp:
                assert len(json.load(fp))==303
            seq=ordered(m["won"] for m in r["matches"])
            hard_seq[arm][s]=seq
            if arm=="r3":
                tag="hard_map_target" if seq=="WLL" else "neutral"
                result=dict(zip(GAME,(int(r["score"][k]) for k in
                                 ("game_win","our_wins","opp_wins","our_points","opp_points","steps"))))
                add((r["seed"],s),"solution92",tag,seq,result)
    read(data/"protocol.json")
    protocol=digest(data/"protocol.json")
    context_sequences=Counter()
    for f in sorted(data.glob("*solution92.npz")):
        with np.load(source(f),allow_pickle=False) as z:
            meta=json.loads(z["meta"].item())
            assert meta["protocol_sha256"]==protocol and meta["steps"]==303
            own, opp = [], []
            frames, ix = z["global_step"], z["step"]
            for first in (102,203):
                frame=int(np.flatnonzero(frames >= first)[0])
                i=int(np.searchsorted(ix, frame))
                assert ix[i]==frame and first<=frames[frame]<first+100
                pair=z["feats"][i,12:14].astype(float)*3
                assert np.max(np.abs(pair-np.rint(pair)))<.002
                a,b=map(int,np.rint(pair));own.append(a);opp.append(b)
            assert [a+b for a,b in zip(own,opp)]==[1,2]
            totals=[0,*own,meta["our_wins"]]
            changes=np.diff(totals)
            assert all(x in (0,1) for x in changes)
            seq=ordered(changes);context_sequences[seq]+=1
            if meta["seed"]==7287108:
                result=dict(result=int(meta["our_wins"]>=2),wins=meta["our_wins"],
                            losses=meta["opp_wins"],steps=meta["steps"])
                add((meta["seed"],meta["side"]),"solution92","solution_risk" if seq=="WLW" else "neutral",seq,result)
    assert context_sequences=={"WWW":43,"WWL":4,"WLW":1}
    scr=analysis/"r3_v4_contact_20261115/observed"
    screen=read(scr/"screen_assessment.json")
    paired={}
    for op in ("solution92","kaggle3","v14"):
        grid={}
        for f in sorted((scr/"screen").glob("*_"+op+"_*.json")):
            if not f.name.startswith(("r3_","v4_")):continue
            assert digest(f)==screen["raw_sha256"][str(f.relative_to(scr))]
            r=json.loads(f.read_bytes());grid.setdefault((r["seed"],r["side"]),{})[r["arm"]]=r["game"]["our_wins"]
        assert len(grid)==32 and all(set(v)=={"r3","v4"} for v in grid.values())
        paired[op]={f"{a},{b}":n for (a,b),n in sorted(Counter((x["r3"],x["v4"]) for x in grid.values()).items())}
    return dict(cases=sorted(roster,key=lambda r:(r["seed"],r["side"])),inputs_sha256=collected,
                context_solution_sequences=dict(context_sequences),hard_map_sequences=hard_seq,
                dev_a_solution_match_wins_r3_v4={f"{a},{b}":v for (a,b),v in sorted(dev_cross.items())},
                dev_a_r3_losses_sequences=dict(dev_loss_orders),direct_r3_sequences=dict(Counter(duelseq.values())),
                screen_match_wins_r3_v4=paired)


if __name__=="__main__":
    print(json.dumps(summarize(Path(sys.argv[1]).resolve()),sort_keys=True,indent=2))
