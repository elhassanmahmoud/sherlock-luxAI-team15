"""Reconstruct all 368 official R3 results and compare them to the sealed pre-run registration."""
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DESIGN=Path("experiments/analysis/r3_v4_wl_20261115/solution_scope_design")
PANELS=(("movement_soft_20261115/screen/r3",7273000,16),
        ("movement_soft_20261115/confirmation/r3",7273100,60),
        ("movement_soft_20261115/restart_route/followup/solution/r3",7283000,60),
        ("movement_reflection_20261115/screen/r3",7286000,16),
        ("r8_midpoint_20261115/games/screen/r3",7170230,16),
        ("r3_v4_contact_20261115/observed",7170260,16))
R3="99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9"
V14="98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
SEATS=("player_0","player_1")
CHECKSUM="ca963ef113d0257a8ff12e1b2d9a520a424d93bbf419477b8b151a6392375bc1"
GAME=("result","wins","losses","points","opp_points","steps")


def require(test,message):
    if not test: raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def rebuild(project):
    base=project/"experiments/analysis"
    source={}; cases={}
    def remember(path):
        source[str(path.relative_to(project))]=digest(path)
        return path
    prior=read(remember(base/"r3_v4_wl_20261115/registered.json"))
    excluded={(r["seed"],r["side"],r["opponent"]) for r in prior["cases"]}
    contact=read(remember(base/PANELS[-1][0]/"screen_assessment.json"))
    frozen=contact["source"]; engine=frozen["engine"]
    require((frozen["r3"],frozen["v14"])==(R3,V14),"Different contact parent")
    reference=None
    for panel,first,maps in PANELS:
        root=base/panel
        roster=[(s,p,"solution92") for s in range(first,first+maps) for p in SEATS]
        if panel==PANELS[-1][0]:
            items=[]
            for seed,seat,opp in roster:
                f=root/"screen"/f"r3_{opp}_{seed}_{seat}.json";h=digest(remember(f))
                require(h==contact["raw_sha256"][str(f.relative_to(root))],"Different native contact seat")
                row=read(f);g=row["game"]
                require(row["arm"]=="r3" and row["source"]==frozen,"Different native contact actor")
                items.append((row,dict(zip(GAME,[g[k] for k in ("game_win","our_wins","opp_wins","our_points","opp_points","steps")]))))
        else:
            m=read(remember(root/"manifest.json")); seal=read(remember(root/"completed.json"))
            f=remember(root/"games.jsonl")
            require(digest(f)==seal["rows_sha256"] and (m["model"],m["weights"],m["first"],m["maps"])==(R3,V14,first,maps),"Different archived roster or models")
            raw=[r for r in map(json.loads,f.read_bytes().splitlines()) if r["opponent"]=="solution92"]
            items=[(r,{k:int(r[k]) for k in GAME}) for r in raw]
            if "binding" in m:
                bind=m["binding"]; core=bind["sources"]
                require(bind["lux_engine"]==engine["lux_modules"] and bind["runtime"]==engine["versions"] and
                        bind["runtime_flags"]==engine["runtime_flags"] and all(bind[k]==engine[k] for k in ("platform","python","machine")),
                        "Different route engine")
                require(all(r.get("restored")==0 and r.get("origin")=="fresh" for r in raw),"Route action intervention occurred")
                # The registered control sets restore=False. Its passive route probe keeps a separate cache.
                require(core["scripts/selective_advice_agent.py"]=="2659086c1b58963da910f9a22739eec8f52a7dfcc818692040f852112bd21ba8"
                        and core["scripts/r3_route_games.py"]=="d5ed93e770a496a8f8399f27b699941473472c45c56fe684ea456245ec5421ef"
                        and core["scripts/r3_restart_route.py"]=="a186a725733aec6a1f137492cacf0e3fbe34401e1ea24f258692d9f447452f95","Different passive probe")
                require(all(core.get(k)==v for k,v in reference.items() if k!="scripts/selective_advice_agent.py"),"Route action/engine source mismatch")
            else:
                require(all(m["engine"].get(k)==engine["lux_modules"][k] for k in ("env.py","wrappers.py","params.py")),"Different Lux rules")
                if reference is None: reference=m["sources"]
                require(all(m["sources"].get(k)==v for k,v in reference.items()),"Different actor/opponent/runner sources")
                if "environment" in m:
                    hist=m["environment"]
                    require(hist["engine"]==engine["lux_modules"] and hist["versions"]==engine["versions"] and
                            hist["flags"]==engine["runtime_flags"] and all(hist[k]==engine[k] for k in ("platform","python","machine")),"Different environment")
        keys=[]
        for r,g in items:
            key=(r["seed"],r["side"],r["opponent"]);keys.append(key)
            require(key not in excluded and key not in cases and g["steps"]==303 and g["wins"] in range(4) and
                    g["wins"]+g["losses"]==3 and g["result"]==int(g["wins"]>g["losses"]),"Unexpected or invalid seat")
            cases[key]=dict(panel=panel,expected=g)
        require(set(keys)==set(roster) and len(keys)==len(roster),"Incomplete original Solution roster")
    for rel,h in reference.items():
        if rel.startswith("agents/Solution_92_Kaggle/") or rel in ("scripts/common.py","scripts/metrics.py","scripts/scoring.py"):
            require(digest(ROOT/rel)==h,"Frozen live source differs: "+rel)
    return dict(sources=source,seats=[dict(seed=k[0],side=k[1],opponent=k[2],**c) for k,c in sorted(cases.items())])


def registered(project):
    p=ROOT/DESIGN/"roster.json";raw=read(p)
    require(digest(p)==CHECKSUM and rebuild(Path(project).resolve())==raw,"Different preregistered sources or rows")
    sources=dict(files=raw["sources"],roster_sha256=CHECKSUM,plan_sha256=digest(ROOT/DESIGN/"PLAN.md"))
    rows={(r["seed"],r["side"],r["opponent"]):{k:r[k] for k in ("panel","expected")} for r in raw["seats"]}
    return rows,sources
