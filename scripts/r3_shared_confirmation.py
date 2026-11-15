"""Fixed original R3 on Mahmoud's 400-map V15 block, with a 16-game V14 preflight.

    python -B -m scripts.r3_shared_confirmation check --repo PROJECT
    python -B -u -m scripts.r3_shared_confirmation run --repo PROJECT --out RESULTS
    python -B -m scripts.r3_shared_confirmation assess --repo PROJECT --out RESULTS

The game command runs inside the frozen 0105658 tree. The assessment can also run
from a current checkout against the same published evidence and sealed results.
"""
import argparse
import csv
import fcntl
from importlib import metadata, util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from types import SimpleNamespace
import zipfile

import numpy as np

from scripts import final_battle_compare as battle
from scripts.final_battle_select import OPPONENTS, SEATS, checked_run_files
from scripts.residual_ensemble_compare import interval

MAPS = range(7158000, 7158400)
STUDY = Path("experiments/analysis/movement_soft_20261115")
PUBLISHED = Path("experiments/analysis/umbau_20261115/confirm")
MODEL = Path("experiments/candidates/movement_dagger_20261115/r3_soft.pth")
R3 = "99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9"
V14 = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
CSV = {"v14": ("v14_ref.csv", "957ac8668e10b6a118b40cb81338a86b3ec356556d68a116535b16d4130bfa05"),
       "v4_mixed": ("v15_candidate.csv", "1cc603732dafff379e57f236be4fc37a0bdd7dfcfa35fcc0e7ce78c95387c4cd")}
ORIG = {"v14": "807963c7ebe4b278c7f85e72f8e71978c3438070311ef92e1e60871817e6d42c",
        "r3": "cb904ef4d18ddbb6f05afc7092ba2dd5c86d63724c0b6193eb244c78173c49fd",
        "direct": "db650772a8858bb0cfc2828b7445d8c961bef8f5e3c1516055aec068b5f657b8"}
DIRECT_ROWS = "5a7c9322d6eae5fcf76fb61b0ceb1f15bcef380f012407b4ffc83863d9b8c3a0"
PARITY = "bf8a159eb3c1fd2cb47d13426fdaaaeb7c593d5fbc6a14be35079363b1bfcf16"
SELF = "self:agents/sherlock/weights/agent_p0.pth"
SCORES = ("result", "wins", "losses", "points", "opp_points", "steps")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pinned_json(path, sha):
    require(battle.digest(path) == sha, f"Different pinned file: {path}")
    return json.loads(path.read_bytes())


def reference_tables(repo):
    tables = {}
    for arm, (name, sha) in CSV.items():
        path = repo / PUBLISHED / name
        require(battle.digest(path) == sha, f"Different published CSV: {name}")
        opponents = (*OPPONENTS, "default", SELF) if arm == "v4_mixed" else (*OPPONENTS, "default")
        seen, scores = set(), {}
        with path.open(newline="") as f:
            for row in csv.DictReader(f):
                key = row["opponent"], int(row["seed"]), row["side"]
                require(key not in seen, f"Duplicate published game: {key}")
                seen.add(key)
                won, wins, lost, points, other, steps = (int(row[k]) for k in
                        ("game_win","our_wins","opp_wins","our_points","opp_points","steps"))
                require(steps == 303 and int(row["point_counting_version"]) == 2 and
                        wins in range(4) and wins + lost == 3 and won == float(row["result"]) == int(wins > lost)
                        and min(points, other) >= 0 and float(row["point_win"]) == (1 if points > other else .5 if points == other else 0),
                        f"Invalid 303-step published score: {key}")
                if key[0] in OPPONENTS:
                    scores[key] = (won,wins,lost,points,other,steps)
        require(seen == {(o,s,p) for o in opponents for s in MAPS for p in SEATS}, f"Incomplete published table: {arm}")
        tables[arm] = scores
    return tables


def original(repo, arm):
    return pinned_json(repo / STUDY / "confirmation" / arm / "manifest.json", ORIG[arm])


def config(repo, arm):
    return SimpleNamespace(candidate="v14" if arm == "v14" else "selective_movement",
                           model=None if arm == "v14" else str((repo/MODEL).resolve()),
                           first=MAPS.start, maps=4 if arm == "v14" else len(MAPS), opponents=",".join(OPPONENTS))


def expected(repo, arm):
    m = original(repo, arm)
    return {**m, "first": MAPS.start, "maps": 4 if arm == "v14" else len(MAPS)}


def check_live(repo):
    for arm in ("v14","r3"):
        require(battle.contract(config(repo,arm)) == expected(repo,arm),
                f"{arm} runner/agent/weights/native opponent/engine differ from the original R3 comparison")


def score(run):
    return tuple(int(run[k]) for k in SCORES)


def read_games(repo, out, arm):
    seeds = MAPS[:4] if arm == "v14" else MAPS
    data, m, seals = checked_run_files(out/arm, config(repo,arm).candidate, seeds, OPPONENTS)
    require(m == expected(repo,arm), "Sealed files differ from original R3 source")
    for key, row in data.items():
        require(all(type(row[k]) is int and row[k] >= 0 for k in ("points","opp_points")), f"Invalid end points: {key}")
    return {k:score(r) for k,r in data.items()}, seals


def replay_diagnosis(reference, actual):
    expected_keys = {(o,s,p) for o in OPPONENTS for s in MAPS[:4] for p in SEATS}
    require(set(actual) == expected_keys, "Need all 16 reproduction seats")
    report = {}
    for opponent in OPPONENTS:
        differences = []
        for key in sorted(k for k in expected_keys if k[0] == opponent):
            if actual[key] != reference[key]:
                differences.append(dict(seed=key[1],side=key[2],published=dict(zip(SCORES,reference[key])),
                                        local=dict(zip(SCORES,actual[key]))))
        report[opponent] = dict(games=8, identical=8-len(differences), differences=differences)
    return report


def replay_gate(reference, actual):
    report = replay_diagnosis(reference, actual)
    failed = [o for o,r in report.items() if r["differences"]]
    require(not failed, f"V14 mismatch for {failed}; inspect per-opponent reproduction.json before further play")


def bounds(values):
    return interval(values, seed=2711, draws=10000)


def paired(reference, candidate, seeds=MAPS):
    result, by_map, match_by_map = {}, {}, {}
    for o in OPPONENTS:
        keys = [(o,s,p) for s in seeds for p in SEATS]
        def scores(data):
            return np.asarray([data[k][:2] for k in keys]).reshape(len(seeds),len(SEATS),2)
        a,b = scores(reference),scores(candidate)
        d = b[:,:,0]-a[:,:,0]
        by_map[o] = d.mean(1)
        match_by_map[o] = (b[:,:,1] - a[:,:,1]).mean(1) / 3
        result[o] = dict(games=len(keys), reference_game_wins=int(a[:,:,0].sum()), r3_game_wins=int(b[:,:,0].sum()),
                         reference_match_wins=int(a[:,:,1].sum()), r3_match_wins=int(b[:,:,1].sum()),
                         gained=[k[1:] for k,x in zip(keys,d.flat) if x>0], lost=[k[1:] for k,x in zip(keys,d.flat) if x<0],
                         net_game_wins=int(d.sum()), winrate_delta=float(d.mean()), ci95=bounds(by_map[o]),
                         match_winrate_delta=float(match_by_map[o].mean()), match_ci95=bounds(match_by_map[o]))
    panel=np.mean(list(by_map.values()),axis=0)
    match_panel=np.mean(list(match_by_map.values()),axis=0)
    columns=("games","reference_game_wins","r3_game_wins","reference_match_wins","r3_match_wins","net_game_wins")
    return dict(by_opponent=result, external={**{k:sum(r[k] for r in result.values()) for k in columns},
                                              "winrate_delta":float(panel.mean()),"ci95":bounds(panel),
                                              "match_winrate_delta":float(match_panel.mean()),"match_ci95":bounds(match_panel)})


def incumbent(repo, source):
    rows=list(csv.reader((repo/"Paths.csv").read_text().splitlines(),delimiter=";"))
    row=[r for r in rows if r and r[0]=="15"]
    require(len(row)==1 and len(row[0])==4, "Current team 15 course row ambiguous")
    _, name, p0, p1 = row[0]
    weights={p:battle.digest(repo/p) if (repo/p).is_file() else None for p in (p0,p1)}
    changes=[p for p,h in source.items() if p.startswith("agents/sherlock/") and
             (not (repo/p).is_file() or battle.digest(repo/p)!=h)]
    return dict(course_import=name,weights=weights,registered_v14_weights_both=all(h==V14 for h in weights.values()),
                different_registered_agent_sources=sorted(changes),
                archived_direct_test_exact_current_sources=name=="agents.sherlock.main.Agent_x"
                and all(h==V14 for h in weights.values()) and not changes)


def separate_evidence(repo):
    old=original(repo,"direct")
    rows,m,seals=checked_run_files(repo/STUDY/"confirmation/direct","selective_movement",range(7273200,7273260),("v14",))
    require(m==old and seals["games_sha256"]==DIRECT_ROWS and (m["weights"],m["model"])==(V14,R3),"Different original direct duel")
    per_map=[sum(rows["v14",s,p]["result"] for p in SEATS)/2 for s in range(7273200,7273260)]
    ci=bounds(per_map)
    path=repo/STUDY/"candidate_package"
    parity=pinned_json(path/"parity.json",PARITY)
    checks=parity["games"]
    require(parity["result"]=="passed" and parity["format"]=="final" and parity["import_path"]=="agents.sherlock.main.Agent_x"
            and (parity["v14_sha256"],parity["r3_sha256"])==(V14,R3) and parity["engine_sha256"]==
            {"luxai_s3."+k[:-3]:v for k,v in m["engine"].items()}
            and len(checks)==2 and {g["side"] for g in checks}==set(SEATS) and all(
               g["equal_action_matrices"]==g["course_updates"]==303 and g["caught_errors"]==g["rejected_orders"]==0
               and g["match_start_steps"]==[0,101,202] for g in checks),"Unverified original course parity")
    package=path/"r3-final-candidate.zip"
    zip_matches=package.is_file() and battle.digest(package)==parity["zip_sha256"]
    if zip_matches:
        import hashlib
        with zipfile.ZipFile(package) as z:
            require(hashlib.sha256(z.read("sherlock/weights/agent.pth")).hexdigest()==parity["course_weights_sha256"],
                    "Packed R3 weight differs")
    cur=incumbent(repo,original(repo,"v14")["sources"])
    return dict(direct_vs_historical_v14=dict(games=len(rows),wins=int(sum(per_map)*2),winrate=float(np.mean(per_map)),
                ci95=ci,lower_above_half=ci[0]>.5,files=seals), current_incumbent=cur,
                direct_vs_v4_mixed="no direct duel in these data",
                course_candidate=dict(record_sha256=PARITY,ordered_matrices=606,zip_sha256=parity["zip_sha256"],
                                      local_zip_matches_verified_course_record=zip_matches))


def run_games(repo,out,arm,workers):
    cfg=config(repo,arm)
    args=[sys.executable,"-B","-u","-m","scripts.final_battle_compare","--candidate",cfg.candidate,
          "--opponents",cfg.opponents,"--first",str(cfg.first),"--maps",str(cfg.maps),"--workers",str(workers),"--out",str(out/arm)]
    if cfg.model:
        args.extend(["--model",cfg.model])
    subprocess.run(args,cwd=battle.ROOT,check=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("check","run","diagnose","assess"))
    p.add_argument("--repo",required=True,type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--workers",choices=(1,2),type=int,default=1)
    args=p.parse_args()
    repo=args.repo.resolve()
    tables=reference_tables(repo)
    if args.mode=="check":
        check_live(repo)
        print(json.dumps(separate_evidence(repo),indent=2))
        return
    if not args.out: p.error("--out required for run/assess")
    out=args.out.resolve()
    if args.mode=="diagnose":
        replay,files=read_games(repo,out,"v14")
        print(json.dumps(dict(by_opponent=replay_diagnosis(tables["v14"],replay),files=files),indent=2))
        return
    if args.mode=="run":
        check_live(repo)
        out.mkdir(parents=True,exist_ok=True)
        with (out/".shared.lock").open("a") as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            seal={"tool":battle.digest(Path(__file__)), "published_csv":{k:v[1] for k,v in CSV.items()},
                  "sources":ORIG,"python":platform.python_version(),"machine":platform.machine(),"platform":platform.system(),
                  "lux_engine_modules":{p.name:battle.digest(p) for p in Path(util.find_spec("luxai_s3").origin).parent.glob("*.py")},
                  "study_helpers":{p:battle.digest(battle.ROOT / p) for p in
                            ("scripts/final_battle_select.py","scripts/residual_ensemble_compare.py","scripts/variants.py",
                             "scripts/protocol.py","scripts/fetch_kaggle3.py","agents/__init__.py")},
                  "package_versions":{k:metadata.version(k) for k in ("numpy","scipy","torch","jax","jaxlib","luxai-s3")},
                  "flags":{k:os.getenv(k) for k in ("JAX_PLATFORMS","XLA_FLAGS","PYTHONHASHSEED","CUDA_VISIBLE_DEVICES")}}
            f=out/"protocol.json"
            if f.exists():
                require(json.loads(f.read_bytes())==seal,"Different shared-panel source/runtime on resume")
            else:
                require(not any((out/x).exists() for x in ("v14","r3")), "Unbound existing games")
                with f.open("x") as dest:json.dump(seal,dest,indent=2)
            run_games(repo,out,"v14",args.workers)
            replay,files=read_games(repo,out,"v14")
            diagnosis=dict(by_opponent=replay_diagnosis(tables["v14"],replay),files=files)
            (out/"reproduction.json").write_text(json.dumps(diagnosis,indent=2)+"\n")
            replay_gate(tables["v14"],replay)
            print("All 16 published V14 scores reproduced; opening fixed 1,600-game R3 panel",flush=True)
            run_games(repo,out,"r3",args.workers)
    proof=json.loads((out/"protocol.json").read_bytes())
    require(proof["tool"]==battle.digest(Path(__file__)) and proof["sources"]==ORIG and
            proof["published_csv"]=={k:v[1] for k,v in CSV.items()}, "Unbound shared-panel protocol")
    replay,replay_files=read_games(repo,out,"v14")
    replay_gate(tables["v14"],replay)
    r3,r3_files=read_games(repo,out,"r3")
    results={k:paired(v,r3) for k,v in tables.items()}
    base=results["v14"]
    result=dict(replay_matches=16,replay_files=replay_files,r3_files=r3_files,comparisons=results,
                game_panel=dict(external_lower_positive=base["external"]["ci95"][0]>0,
                    solution_at_least_v14=base["by_opponent"]["solution92"]["net_game_wins"]>=0),
                separate_evidence=separate_evidence(repo),protocol_sha256=battle.digest(out/"protocol.json"),
                scope="400 previously published confirmation maps; both seats and both external opponents paired. "
                      "Historical direct duel and R3 course ZIP parity are separate checks.")
    encoded=json.dumps(result,indent=2,allow_nan=False)+"\n"
    if args.mode=="run":
        (out/"assessment.json").write_text(encoded)
    print(encoded,end="")


if __name__=="__main__":main()
