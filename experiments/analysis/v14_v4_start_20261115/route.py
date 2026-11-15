"""Read paired archives; recover only the original public parameter draws (no gym or gameplay)."""
import argparse
import ast
import csv
import hashlib
from importlib import metadata
import json
from pathlib import Path
import numpy as np

FIELDS=("unit_move_cost","unit_sap_cost","unit_sap_range","unit_sensor_range")
OPP=("kaggle3","solution92")
AGENTS=("v4","v14")
TABLES={
    "A":(7150000,100,"kaggle3_20261115/student_hyb_v4_mixed.csv","kaggle3_20261115/v14_ref_devA.csv"),
    "B":(7151000,100,"kaggle3_20261115/devB_hyb_v4_mixed.csv","kaggle3_20261115/devB_v14.csv"),
    "400":(7158000,400,"umbau_20261115/confirm/v15_candidate.csv","umbau_20261115/confirm/v14_ref.csv")}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def sampler():
    import jax
    import jax.numpy as jnp
    package=metadata.distribution("luxai-s3")
    params=Path(package.locate_file("luxai_s3/params.py")); wrappers=params.with_name("wrappers.py")
    # Read just the registered range expression, including the two intervening unused draws.
    tree=ast.parse(params.read_bytes())
    expr=next(n.value for n in tree.body if isinstance(n,ast.Assign) and n.targets[0].id=='env_params_ranges')
    ranges={}
    for kw in expr.keywords:
        n=kw.value
        if isinstance(n,ast.List): values=ast.literal_eval(n)
        elif (isinstance(n,ast.Call) and n.func.id=='list' and isinstance(n.args[0],ast.Call)
              and n.args[0].func.id=='range'):
            values=list(range(*(ast.literal_eval(k) for k in n.args[0].args)))
        else: raise ValueError("Changed parameter definition")
        ranges[kw.arg]=values
    def draw(seed):
        rng,_=jax.random.split(jax.random.key(seed))
        keep={}
        for name,vs in ranges.items():
            rng,key=jax.random.split(rng)
            if name in FIELDS:keep[name]=jax.random.choice(key,jnp.asarray(vs))
            if len(keep)==4:break
        return jnp.stack([keep[k] for k in FIELDS])
    def many(seeds):
        out=np.asarray(jax.vmap(draw)(np.asarray(seeds,dtype=np.uint32)))
        return out.astype(int)
    return many,ranges,{"params":sha(params),"wrapper_reference":sha(wrappers),"jax":jax.__version__}


def parameter_proof(root,draw):
    p=root/'experiments/analysis/battle_params_20261030/map_params.csv'
    raw=list(csv.DictReader(p.open()))
    # Verify every archived card in this original, separately produced table, without using its latent fields.
    observed=np.array([[int(row[k]) for k in FIELDS] for row in raw]); seeds=[int(row["seed"]) for row in raw]
    if not np.array_equal(draw(seeds),observed):raise ValueError("Independent archived public parameters differ")
    return {"maps":len(seeds),"first":min(seeds),"last":max(seeds),"sha":sha(p)}


def dataset(root,tag):
    first,n,*tables=TABLES[tag]
    all_keys={(s,o,side) for s in range(first,first+n) for o in OPP for side in ("player_0","player_1")}
    arrays=[];hashes={}
    for agent,table in zip(AGENTS,tables):
        p=root/"experiments/analysis"/table; seen={}; hashes[agent]=sha(p)
        for r in csv.DictReader(p.open()):
            if r["opponent"] not in OPP:continue
            s=int(r["seed"]);k=(s,r["opponent"],r["side"])
            w,l,res=(int(r[c]) for c in ("our_wins","opp_wins","game_win"))
            if (k in seen or k not in all_keys or int(r["steps"])!=303 or int(r["point_counting_version"])!=2
                    or w not in range(4) or l!=3-w or res!=(w>l) or float(r["result"])!=res):raise ValueError((p,k))
            seen[k]=(res,w)
        if set(seen)!=all_keys:raise ValueError("Unexpected game keys")
        arrays.append(np.array([seen[(s,o,sd)] for s in range(first,first+n) for o in OPP
                                for sd in ("player_0","player_1")],dtype=int).reshape(n,2,2,2))
    return np.stack(arrays),np.arange(first,first+n),hashes


def menu(ranges):
    yield {"constant":"v4"}
    yield {"constant":"v14"}
    for field in FIELDS:
        midpoint=(max(ranges[field])+min(ranges[field]))/2
        for take in ("low","high"):
            yield {"v14_when":take,"field":field,"midpoint":midpoint}


def routing(rule,params):
    if "constant" in rule:return np.full(len(params),int(rule["constant"]=="v14"),dtype=int)
    low=params[:,FIELDS.index(rule["field"])]<=rule["midpoint"]
    return (low if rule["v14_when"]=="low" else ~low).astype(int)


def summarize(data,decision):
    chosen=data[decision,np.arange(len(decision))]
    out={"chosen_v14_maps":int(np.sum(decision)),"n_maps":len(decision),"wins":int(chosen[:,:,:,0].sum()),
         "by_opponent":{o:{"wins":int(chosen[:,i,:,0].sum()),"match_wins":int(chosen[:,i,:,1].sum())} for i,o in enumerate(OPP)}}
    draws=np.random.Generator(np.random.PCG64(2711)).integers(0,len(decision),(10000,len(decision)))
    for j,agent in enumerate(AGENTS):
        diff=chosen[:,:,:,0]-data[j,:,:,:,0]
        def summary(arr):
            mapdiff=arr.reshape(len(arr),-1).mean(axis=1)
            return {"gained":int((arr>0).sum()),"lost":int((arr<0).sum()),"net":int(arr.sum()),
                    "CI95":np.quantile(mapdiff[draws].mean(axis=1),(.025,.975)).tolist()}
        out[agent]={"base_wins":int(data[j,:,:,:,0].sum()),"all":summary(diff),
                    **{o:summary(diff[:,i,:]) for i,o in enumerate(OPP)}}
    return out


def oracle(data,params):
    # Same policy on BOTH seats and against BOTH external opponents on a map. Ties go to v4.
    wins=data[:,:,:,:,0]; each=wins.sum(axis=(2,3)); ideal=np.argmax(each,axis=0)
    _,groups=np.unique(params,axis=0,return_inverse=True)
    lookup={g:int(each[1,groups==g].sum()>each[0,groups==g].sum()) for g in np.unique(groups)}
    return dict(best_complete_map=int(each[ideal,np.arange(len(ideal))].sum()),
                best_fixed_observed_public_tuple=int(each[[lookup[i] for i in groups],np.arange(len(ideal))].sum()),
                public_tuples=len(lookup),best_seat_and_opponent=int(wins.max(axis=0).sum()))


def save(path,value):
    with path.open("x") as f:json.dump(value,f,indent=2)


def main():
    ap=argparse.ArgumentParser();ap.add_argument("root",type=Path);ap.add_argument("stage",choices=("choose","evaluate"));ap.add_argument("--out",type=Path,required=True);a=ap.parse_args()
    draw,ranges,src=sampler();check=parameter_proof(a.root,draw)
    if a.stage=="choose":
        data,seeds,binding=dataset(a.root,'A'); pp=draw(seeds); options=list(menu(ranges))
        scores=[summarize(data,routing(r,pp))["wins"] for r in options]
        best=max(range(len(options)),key=scores.__getitem__)
        best_split=max(range(2,len(options)),key=scores.__getitem__)
        save(a.out/"selection.json",dict(phase='A',sources=src,proof=check,sha=binding,
             code=sha(Path(__file__)),scores=list(zip(options,scores)),selected=options[best],top_split=options[best_split]))
    else:
        selection=json.loads((a.out/"selection.json").read_bytes())
        if selection["code"]!=sha(Path(__file__)) or selection["sources"]!=src or selection["proof"]!=check:raise ValueError("Selection changed")
        result={}
        for tag in ('A','B','400'):
            data,seeds,h=dataset(a.root,tag);pp=draw(seeds);rule=selection['selected']
            result[tag]=dict(binding=h,rule=rule,routed=summarize(data,routing(rule,pp)),upper_bound=oracle(data,pp),
                pure={name:summarize(data,np.full(len(seeds),j))["by_opponent"] for j,name in enumerate(AGENTS)})
            if rule!=selection['top_split']:
                result[tag]['prespecified_top_nonconstant']=dict(rule=selection['top_split'],routed=summarize(data,routing(selection['top_split'],pp)))
        save(a.out/'comparison.json',dict(selection_sha=sha(a.out/"selection.json"),panels=result))
if __name__=='__main__': main()
