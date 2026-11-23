"""Independent exhaustive bit checks and protected-unit review of archived unchanged first matches."""
from collections import defaultdict
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from belegung import HERE, P, infer_bits
from auswerten import FOLDER


def brute():
    rng=np.random.default_rng(161422222)
    n=7
    qs=list(range(1,2**n))
    patterns=np.arange(2**n,dtype=np.int64)
    weights=np.asarray([P**int(i).bit_count()*(1-P)**(n-int(i).bit_count()) for i in patterns])
    for i in range(200):
        truth=int(rng.integers(2**n))
        forced=int(rng.integers(2**n))&~truth
        eqs=[]
        for _ in range(int(rng.integers(1,8))):
            terms=[int(rng.choice(qs)) for _ in range(int(rng.integers(1,6)))]
            target=sum(bool(m & truth) for m in terms)
            if i%11==0: target+=1
            eqs.append((terms,target))
        mass,calc=infer_bits(eqs,forced,qs)
        allow=(patterns & forced)==0
        for terms,g in eqs:
            equal=np.sum([(patterns & m)!=0 for m in terms],axis=0)==g
            allow &= equal
        prior=weights*allow
        np.testing.assert_allclose(mass,prior.sum(),atol=1e-11)
        physical=(np.asarray(qs)[:,None] & patterns[None,:])!=0
        np.testing.assert_allclose(calc,(physical*prior).sum(1),atol=1e-11)
    return 200


def main():
    source=json.loads(gzip.decompress((HERE/"quellen.json.gz").read_bytes()))
    diag=json.loads(gzip.decompress((HERE/"diagnose.json.gz").read_bytes()))
    r=json.loads((HERE/"ergebnis.json").read_bytes())
    if len(source["rows"])!=len(diag) or len(diag)!=160:
        raise ValueError("Incomplete source records")
    rng=np.random.default_rng(231123)
    scored=first_targets=base_hits=full_hits=actual_protected=0
    card=defaultdict(lambda:[0,0,0])
    late=defaultdict(list)
    for meta,row in zip(source["rows"],diag):
        s,t=meta["seed"],meta["team"]
        assert (s,t)==(row["seed"],row["team"])
        card[s]
        path=FOLDER/meta["name"]
        with np.load(path.with_suffix(".npz")) as data:
            after=data["after"][:,t]
            starts=data["team_points"][:,t]
            visible=data["relic_nodes_mask"].any(1)
            pos=data["position"][:,t]
            live=data["units_mask"][:,t] & (data["energy"][:,t]>=0)
        with np.load(path.with_suffix(".richter.npz")) as label:
            tiles=label["points"].ravel()
        first_hit=np.flatnonzero(starts>0)
        first_view=np.flatnonzero(visible)
        assert row["first_public_credit"]==(int(first_hit[0]) if len(first_hit) else 101)
        assert row["first_sight"]==(int(first_view[0]) if len(first_view) else 101)
        if row["first_public_credit"]<row["first_sight"]: scored+=1
        producers=set()
        first=None
        for snap in row["snapshots"]:
            step=snap["t"]
            if starts[step]>starts[step-1]:
                current=np.flatnonzero(live[step])
                xy=pos[step,current]
                idx=xy[:,0]*24+xy[:,1]
                producers.update(current[tiles[idx]].tolist())
            assert producers.issubset(snap["possibly_scored_ids"])
            assert not producers.intersection(snap["free_ids"])
            actual_protected+=len(producers)
            for name in ("chosen","baseline"):
                o=snap[name]
                if not o: continue
                assert o["uid"] in snap["free_ids"]
                x,y=o["target"]
                assert int(tiles[x*24+y])==int(o["real_score"])
                trajectory=[pos[step,o["uid"]].tolist(),*o["route"]]
                distances=np.abs(np.diff(trajectory,axis=0)).sum(1)
                assert (distances==1).all() and len(distances)==o["steps"]
            if first is None and snap["chosen"]:
                first=snap
        if first:
            first_targets+=1
            full_hits+=int(first["chosen"]["real_score"])
            base_hits+=int(first["baseline"]["real_score"])
            card[s][0]+=1
            card[s][1]+=int(first["chosen"]["real_score"])-int(first["baseline"]["real_score"])
            card[s][2]+=first["full"]["logloss"]-first["reference"]["logloss"]
            t0=row["first_public_credit"]
            late["time_to_option"].append(first["t"]-t0)
    assert scored==r["pre_sight"]["seats"]
    assert (first_targets,base_hits,full_hits)==(r["targets"]["chosen"]["n"],r["targets"]["baseline"]["true_hits"],r["targets"]["chosen"]["true_hits"])
    counts=np.array(list(card.values()))
    take=rng.integers(0,len(counts),(20000,len(counts)))
    draws=counts[take].sum(1)
    valid=draws[:,0]>0
    delta=draws[valid,1:]/draws[valid,0,None]
    summary={"brute_force_examples":brute(),"candidate_masks_per_example":127,"honored_true_producer_ship_ticks":actual_protected,
        "first_target_seats":first_targets,"mean_delay_to_first_option":float(np.mean(late["time_to_option"])),
        "hit_prob_difference_vs_same_candidates_no_positive":float(counts[:,1].sum()/counts[:,0].sum()),
        "hit_difference_map_ci95":np.quantile(delta[:,0],[.025,.975]).tolist(),
        "log_loss_delta_map_ci95":np.quantile(delta[:,1],[.025,.975]).tolist(),
        "source_files":{p.name:sha256(p.read_bytes()).hexdigest() for p in (HERE/"diagnose.json.gz",HERE/"ergebnis.json",Path(__file__))}}
    (HERE/"gegenrechnung.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
