"""Count whether a previously certified public group invalidates the same old-zero flags as a set."""
import gzip
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def read(p):
    with gzip.open(p,"rt") as f:
        return {(r["seed"],r["team"]):r for r in map(json.loads,f)}


def bits(mask):
    while mask:
        bit=mask & -mask
        yield bit.bit_length()-1
        mask-=bit


def analyze(split):
    sources=read(HERE.parent/"punktspeicher"/split/"beobachtungen.jsonl.gz")
    groups=read(HERE.parent/"gruppenbeweis"/split/"gruppen.jsonl.gz")
    assert groups.keys()==sources.keys()
    events=[]
    for key,g in groups.items():
        src=sources[key]
        assert len(g["frames"])==len(src["policy"])==303 and src["action_hash"]==g["action_hash"]
        seen=set()
        prev=0
        hist=0
        for f,s,truth in zip(g["frames"],src["policy"],src["referee"],strict=True):
            t=f["t"]
            old=int(s["dead"],16)
            if t%101==0:
                hist=prev
            hist &= old
            prev=old
            for i in bits(int(f["open"],16)):
                pair=g["groups"][i]
                mask=sum(1<<v for v in pair)
                if mask & ~hist:
                    continue
                assert mask & int(truth,16)
                reach=bool(int(f["partial"],16)&(1<<i))
                k=(i,reach)
                if k not in seen:
                    events.append(dict(seed=key[0],team=key[1],t=t,pair=pair,reachable=reach))
                    seen.add(k)
    return dict(cards=len({s for s,_ in groups}),seats=len(groups),cases=events,
                conflict_maps=len({r["seed"] for r in events}),partial_reach_maps=len({r["seed"] for r in events if r["reachable"]}))


out={k:analyze(k) for k in ("archiv","frisch")}
(HERE/"gruppenwiderspruch.json").write_text(json.dumps(out,indent=2)+"\n")
print({k:(v["conflict_maps"],v["partial_reach_maps"]) for k,v in out.items()})
