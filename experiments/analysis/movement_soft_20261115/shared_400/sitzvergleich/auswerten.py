#!/usr/bin/env python3
"""Reconstruct retrospective three-policy coverage only after the original 400-map study is sealed."""
import argparse
import csv
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

MAPS = range(7158000, 7158400)
SEATS = ("player_0", "player_1")
OPP = ("kaggle3", "solution92")
ARMS = ("r3", "v14", "v15")
SELF = "self:agents/sherlock/weights/agent_p0.pth"
STUDY = Path("experiments/analysis/movement_soft_20261115")
CSV_DIR = Path("experiments/analysis/umbau_20261115/confirm")
CSV = {"v14": ("v14_ref.csv", "957ac8668e10b6a118b40cb81338a86b3ec356556d68a116535b16d4130bfa05"),
       "v15": ("v15_candidate.csv", "1cc603732dafff379e57f236be4fc37a0bdd7dfcfa35fcc0e7ce78c95387c4cd")}
ORIGINAL = {"v14": "807963c7ebe4b278c7f85e72f8e71978c3438070311ef92e1e60871817e6d42c",
            "r3": "cb904ef4d18ddbb6f05afc7092ba2dd5c86d63724c0b6193eb244c78173c49fd",
            "direct": "db650772a8858bb0cfc2828b7445d8c961bef8f5e3c1516055aec068b5f657b8"}
R3 = "99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9"
V14 = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
PROTOCOL = "1a4757fbafa5602c089425788b1cf46d901555bea440b6af12d689146c385029"
REPRO = "d1123e38fac3fb0218a3b4d712c7a045c5ae620534b772bc8e337cd45f96aced"
PREFIX = "c0e04b915ad6cfd60f010c1a694222d72184c11e4bb2bf8defe167d3976f33c4"
FIELDS = ("win", "matches_won", "matches_lost", "points", "opp_points", "steps")


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, expected=None):
    blob = path.read_bytes()
    if expected:
        need(digest(blob) == expected, f"SHA-256 mismatch: {path}")
    return blob


def keys(opponents, seeds):
    return {(o, s, seat) for o in opponents for s in seeds for seat in SEATS}


def outcome(values):
    win, w, l, p, q, n = values
    need(all(type(v) is int and v >= 0 for v in values) and w+l == 3 and win == int(w>l) and n == 303,
         f"illegal whole-game score: {values}")
    return dict(zip(FIELDS, values))


def refs(repo, arm):
    fname, fingerprint = CSV[arm]
    raw = read(repo/CSV_DIR/fname, fingerprint)
    ok = keys((*OPP,"default",SELF) if arm == "v15" else (*OPP,"default"), MAPS)
    rows = {}
    for r in csv.DictReader(raw.decode().splitlines()):
        key = r["opponent"], int(r["seed"]), r["side"]
        win,w,l,p,q,n = [int(r[k]) for k in ("game_win","our_wins","opp_wins","our_points","opp_points","steps")]
        need(key not in rows and int(r["point_counting_version"]) == 2 and float(r["result"]) == win and
             float(r["point_win"]) == (1 if p>q else .5 if p==q else 0), f"invalid CSV row {key}")
        rows[key] = outcome((win,w,l,p,q,n))
    need(rows.keys() == ok, f"wrong published roster in {fname}")
    return {k:v for k,v in rows.items() if k[0] in OPP}


def sealed(folder, arm, seeds, original):
    spec = read(folder/"manifest.json")
    need(json.loads(spec) == dict(original, first=seeds.start, maps=len(seeds)), f"{arm} source manifest changed")
    done_raw = read(folder/"completed.json")
    done = json.loads(done_raw)
    raw = read(folder/"games.jsonl", done["rows_sha256"])
    if arm == "r3":
        need(digest(b"".join(raw.splitlines(keepends=True)[:400])) == PREFIX, "changed sealed first 400 games")
    rows = {}
    for line in raw.splitlines():
        r=json.loads(line)
        key=r["opponent"],r["seed"],r["side"]
        need(type(r["seed"]) is int and key not in rows and r["candidate"]==original["candidate"] and
             type(r["result"]) in (int,float) and r["result"] in (0,1), f"invalid research row {key}")
        rows[key]=outcome((int(r["result"]),r["wins"],r["losses"],r["points"],r["opp_points"],r["steps"]))
    need(rows.keys()==keys(OPP,seeds),f"incomplete {arm} roster")
    summary={}
    for o in OPP:
        sub=[v for (opp,_,_),v in rows.items() if opp==o]
        summary[o]=dict(played=len(sub),wins=sum(v["win"] for v in sub),matches=sum(v["matches_won"] for v in sub))
    need(done["summary"]==summary,f"{arm} finish summary differs")
    return rows, {"games_sha256":digest(raw),"manifest_sha256":digest(spec)}, digest(done_raw)


def totals(data):
    return {name:sum(r[name] for r in data) for name in FIELDS}


def analyse(rows, opp, assessment):
    joined={}
    for seed in MAPS:
        for side in SEATS:
            joined[seed,side]={arm:rows[arm][opp,seed,side] for arm in ARMS}
    totals_by_arm={arm:totals([r[arm] for r in joined.values()]) for arm in ARMS}
    for arm, baseline in (("v14","v14"),("v15","v4_mixed")):
        official=assessment["comparisons"][baseline]["by_opponent"][opp]
        a,b=totals_by_arm[arm],totals_by_arm["r3"]
        gain=[list(k) for k,v in joined.items() if v["r3"]["win"]>v[arm]["win"]]
        loss=[list(k) for k,v in joined.items() if v["r3"]["win"]<v[arm]["win"]]
        compare={"games":len(joined),"r3_game_wins":b["win"], "reference_game_wins":a["win"],
                 "net_game_wins":b["win"]-a["win"],"reference_match_wins":a["matches_won"],
                 "r3_match_wins":b["matches_won"],"gained":gain,"lost":loss}
        need(all(official[k]==v for k,v in compare.items()),f"assessment vs raw {opp}/{arm}")
    patterns=Counter({format(i,"03b"):0 for i in range(8)})
    multi=Counter({i:0 for i in range(3)})
    lost=[]
    conflicts=[]
    for seed in MAPS:
        w=[[joined[seed,side][arm]["win"] for arm in ARMS] for side in SEATS]
        best=max(map(sum,zip(*w)))
        multi[best]+=1
        if sum(map(max,w))>best:
            conflicts.append(seed)
        for side, bits in zip(SEATS,w):
            patterns["".join(map(str,bits))]+=1
            if not any(bits) and opp=="solution92":
                lost.append(dict(seed=seed,side=side,policies=joined[seed,side]))
    return {"n_seats":len(joined),"n_maps":len(MAPS),"totals":totals_by_arm,"patterns":dict(patterns),
            "seat_oracle_wins":len(joined)-patterns["000"],"same_policy_both_seats_oracle_wins":sum(n*v for n,v in multi.items()),
            "maps_by_best_same_policy_wins":dict(multi),"maps_requiring_different_policies_for_both_wins":conflicts,
            **({"all_three_lost":lost} if opp=="solution92" else {})}, joined


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True,help="original frozen shared400 sources, including the native opponents")
    p.add_argument("--measured",type=Path,help="defaults to shared_400/measured under repo")
    p.add_argument("--engine",type=Path,help="luxai_s3 directory (otherwise discovered in current Python environment)")
    p.add_argument("--out",type=Path,required=True,help="new output directory")
    a=p.parse_args()
    run=a.measured or a.repo/STUDY/"shared_400/measured"
    # This is a terminal-only reader. Do not open a partial JSONL or CSV.
    need((run/"r3/completed.json").is_file() and (run/"assessment.json").is_file(),
         "Final r3/completed.json and assessment.json are required; no data opened.")
    assessment_raw=read(run/"assessment.json")
    assessment=json.loads(assessment_raw)
    protocol=json.loads(read(run/"protocol.json",PROTOCOL))
    repro=json.loads(read(run/"reproduction.json",REPRO))
    need(protocol["sources"]==ORIGINAL and protocol["published_csv"]=={"v14":CSV["v14"][1],"v4_mixed":CSV["v15"][1]}
         and assessment["protocol_sha256"]==PROTOCOL and assessment["replay_matches"]==16,"foreign assessment/protocol")
    manifests={arm:json.loads(read(a.repo/STUDY/"confirmation"/arm/"manifest.json",h)) for arm,h in ORIGINAL.items()}
    inputs=dict(protocol["study_helpers"])
    for m in manifests.values():
        for rel,h in m["sources"].items():
            need(inputs.setdefault(rel,h)==h, f"source disagreement: {rel}")
        for rel,h in m["engine"].items():
            need(protocol["lux_engine_modules"][rel]==h,f"engine mismatch: {rel}")
    inputs["scripts/r3_shared_confirmation.py"]=protocol["tool"]
    for rel,h in inputs.items():
        read(a.freeze/rel,h)
    engine=a.engine
    if engine is None:
        spec=importlib.util.find_spec("luxai_s3")
        need(spec is not None,"use --engine PATH or the project Python environment")
        engine=Path(spec.origin).parent
    for rel,h in protocol["lux_engine_modules"].items():
        read(engine/rel,h)
    read(a.freeze/"agents/sherlock/weights/agent_p0.pth",V14)
    read(a.repo/"experiments/candidates/movement_dagger_20261115/r3_soft.pth",R3)
    tables={arm:refs(a.repo,arm) for arm in CSV}
    pre, seal_pre, done_pre=sealed(run/"v14","v14",MAPS[:4],manifests["v14"])
    need(all(tables["v14"][k]==r for k,r in pre.items()) and assessment["replay_files"]==repro["files"]==seal_pre
         and all(repro["by_opponent"][o]==dict(games=8,identical=8,differences=[]) for o in OPP),
         "failed 16-score historical V14 reproduction")
    tables["r3"], seal_r3, done_r3=sealed(run/"r3","r3",MAPS,manifests["r3"])
    need(assessment["r3_files"]==seal_r3,"assessment does not describe measured R3 games")
    panels={}
    audits=[]
    for opp in OPP:
        panels[opp],joined=analyse(tables,opp,assessment)
        for (seed,side),r in joined.items():
            audits.append(dict(opponent=opp,seed=seed,side=side,bits="".join(str(r[k]["win"]) for k in ARMS),
                         **{f"{arm}_{field}":r[arm][field] for arm in ARMS for field in FIELDS}))
    for arm,baseline in (("v14","v14"),("v15","v4_mixed")):
        ext=assessment["comparisons"][baseline]["external"]
        def total(policy,field):
            return sum(panels[o]["totals"][policy][field] for o in OPP)
        expected=dict(games=1600,r3_game_wins=total("r3","win"),reference_game_wins=total(arm,"win"),
                      r3_match_wins=total("r3","matches_won"),reference_match_wins=total(arm,"matches_won"),
                      net_game_wins=total("r3","win")-total(arm,"win"))
        need(all(ext[k]==v for k,v in expected.items()),f"official external totals {baseline}")
    a.out.mkdir(parents=True,exist_ok=False)
    joined_path=a.out/"joined.csv"
    with joined_path.open("x",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(audits[0])); w.writeheader(); w.writerows(audits)
    report=dict(bit_order=list(ARMS),panels=panels,source_sha256=dict(assessment=digest(assessment_raw),protocol=PROTOCOL,
                reproduction=REPRO,replay_files=seal_pre,r3_files=seal_r3,v14_completed=done_pre,r3_completed=done_r3,
                r3_400row_prefix=PREFIX,original_manifests=ORIGINAL,published_csv={k:v[1] for k,v in CSV.items()},
                r3_weights=R3,v14_weights=V14,external_sources_checked=inputs,engine_checked=protocol["lux_engine_modules"],
                joined_csv=digest(read(joined_path)),reader=digest(read(Path(__file__)))),
                interpretation="Retrospective oracle bounds. Each opponent is considered separately. Match counts and point sums cover the full three-match game. Per-match point histories and causes are not recorded here.")
    (a.out/"coverage.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    for opp in OPP:
        panel=panels[opp]
        print(opp, {k:v["win"] for k,v in panel["totals"].items()}, "oracle seat / one policy per map",
              panel["seat_oracle_wins"],panel["same_policy_both_seats_oracle_wins"],"/ 800")


if __name__=="__main__":
    main()
