"""Record the three preregistered V15 presentation games via lux.runner.run_agents."""
import argparse
import csv
import fcntl
import gzip
import hashlib
import json
from pathlib import Path
import random
import sys
import tempfile
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT/"Gruppe15_V15.zip"
ZIP_SHA = "0e3af9db15bcfb1e2fd315ed9da5169e51b1f5f42561d52a15af32bb75ad64ee"
PACK_SHA = "aafb1a22de0f76e540c32797cb4cd1f3968bd9dec193202c31e582f8a6be2b0e"
V14_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
CASES = ((7171000, 0, "V14", 14), (7171001, 1, "Solution_92", 2), (7171002, 0, "Kaggle-Platz 3", 3))
SIDES = ("player_0","player_1")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encode(data):
    return json.dumps(data,ensure_ascii=False,separators=(",",":"))


def material():
    from importlib.util import find_spec
    from scripts.fetch_kaggle3 import TARGET, verify
    if sha(PACKAGE)!=ZIP_SHA or not verify():
        raise ValueError("Falsche V15-ZIP oder fehlende Kaggle-Gewichte")
    with zipfile.ZipFile(PACKAGE) as z:
        if hashlib.sha256(z.read("Gruppe15/agent.pth")).hexdigest()!=PACK_SHA:
            raise ValueError("Falsches Gewicht im V15-Paket")
    if any(sha(ROOT/f"agents/sherlock/weights/agent_p{i}.pth")!=V14_SHA for i in (0,1)):
        raise ValueError("Falsche V14-Gewichte")
    engine = Path(find_spec("luxai_s3").origin).parent
    files = [ROOT/"lux/runner.py",Path(__file__),Path(__file__).with_name("v15_demo_view.html")]
    files += [ROOT/"scripts"/n for n in ("scoring.py","kaggle3_opponent.py","play_and_view.py",
                                       "xversion_replay.py","check_candidate_runner.py","fetch_kaggle3.py")]
    for folder in (ROOT/"agents/sherlock",ROOT/"agents/Solution_92_Kaggle",TARGET):
        files.extend(folder.rglob("*.py"))
    from importlib.metadata import version
    return dict(package=ZIP_SHA,package_weights=PACK_SHA,v14=V14_SHA,source="e793d53e7d1856ffbd8f324da0e26fad2b3a2085",
                engines={p.name:sha(p) for p in engine.glob("*.py")},sources={str(p.relative_to(ROOT)):sha(p) for p in files},
                packages={k:version(k) for k in ("luxai-s3","numpy","torch","jax","jaxlib")},cases=[list(c) for c in CASES])


def paths(work):
    classes = {15:("Gruppe15.main.Agent_x", "Gruppe15/agent.pth"),
               14:("agents.sherlock.main.Agent_x", None),
               2:("agents.Solution_92_Kaggle.agent.Agent",""),
               3:("scripts.kaggle3_opponent.Kaggle3Opponent","")}
    names = ("Moodle Gruppe","Import_Path","Load_Path_P0","Load_Path_P1")
    with (work/"Paths.csv").open("w",encoding="cp1252",newline="") as f:
        w=csv.writer(f,delimiter=";"); w.writerow(names)
        for number,(cls,file) in classes.items():
            weights = [str(work/"agents"/file)]*2 if file else [str(ROOT/f"agents/sherlock/weights/agent_p{i}.pth") for i in (0,1)] if file is None else ["",""]
            w.writerow([number,cls,*weights])


def record(work, case):
    import numpy as np
    import torch
    from lux import runner
    from scripts.check_candidate_runner import seed_proxy, verify_loaded
    from scripts.scoring import match_points_after_step, point_tile_map
    from scripts.xversion_replay import guard_course_calls

    seed, version_side, rival, group = case
    pair = (15,group) if version_side==0 else (group,15)
    public, occupied, closed_points = [], [], {}
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)

    class Recorder(runner.RecordEpisode):
        def reset(self, **kw):
            obs, info = super().reset(**kw)
            self.previous = obs[SIDES[version_side]]
            if int(info["params"]["match_count_per_episode"])!=3 or int(info["params"]["max_steps_in_match"])!=100:
                raise ValueError("Kurs erwartet drei Matches zu 101 Schritten")
            public.append([int(x) for x in self.previous["team_points"]]); occupied.append([[],[]])
            return obs, info

        def step(self, actions):
            obs, reward, terminal, truncated, info = super().step(actions)
            current = obs[SIDES[version_side]]
            points = match_points_after_step(self.previous,current,info)
            s=info["final_state"]
            on=point_tile_map(s)
            xy=np.asarray(s.units.position)
            active=np.asarray(s.units_mask,dtype=bool)&(np.asarray(s.units.energy)[:,:,0]>=0)
            tiles=[sorted({(int(x),int(y)) for x,y in xy[t][active[t]] if on[x,y]}) for t in (0,1)]
            if [len(v) for v in tiles] != (points-np.asarray(self.previous["team_points"])).tolist():
                raise ValueError("Gewertete Felder und Punktzuwachs stimmen nicht überein")
            occupied.append(tiles)
            public.append([int(x) for x in current["team_points"]])
            if int(current["match_steps"])==0:
                closed_points[len(public)-1]=points.tolist()
            self.previous=current
            return obs,reward,terminal,truncated,info

    native=runner.load_class_from_path
    def checked_class(path):
        cls=native(path)
        if not path.endswith(".Agent_x"):
            return cls
        class Checked(cls):
            def __init__(self, player, agent_path):
                super().__init__(player,agent_path=agent_path)
                verify_loaded(self,torch.load(agent_path,map_location="cpu",weights_only=False))
                guard_course_calls(self)
        return Checked

    with patch.object(runner,"_base_dir",str(work)), patch.object(runner,"np",seed_proxy([seed])), patch.object(
            runner,"RecordEpisode",Recorder), patch.object(runner,"load_class_from_path",checked_class):
        runner.run_agents(*pair,games_to_play=1,train=False)
    files=list((work/f"replays/{pair[0]}_vs_{pair[1]}").glob("*.json"))
    if len(files)!=1:
        raise ValueError("Erwartet genau eine Originalaufnahme")
    replay=json.loads(files[0].read_bytes())
    if replay["metadata"]["seed"]!=seed or set(closed_points)!={101,202,303}:
        raise ValueError("Falscher Seed oder falsche Matchgrenzen")
    return replay,public,occupied,closed_points


def scene(frames):
    """First change of leader within a match, then first simultaneous gain, then first score."""
    any_score = simultaneous = None
    for start in (0,101,202):
        last_leader=0
        previous=[0,0]
        for step in range(start+1,start+101):
            points=frames[step]["public"]
            if any_score is None and sum(points)>0:
                any_score=step
            if simultaneous is None and all(v>u for u,v in zip(previous,points)):
                simultaneous=step
            lead=(points[0]>points[1])-(points[1]>points[0])
            if lead and last_leader and lead!=last_leader:
                return step,"Erster Führungswechsel innerhalb eines Matches"
            last_leader=lead or last_leader
            previous=points
    if simultaneous is not None: return simultaneous,"Erster gleichzeitiger Punktgewinn"
    if any_score is not None: return any_score,"Erster öffentlicher Punktgewinn"
    return 100,"Letzter öffentlicher Zugstand des ersten Matches"


def present(case,replay,public,occupied,ends):
    from scripts.play_and_view import match_sequence, match_wins
    seed,side,rival,_=case
    states=replay["observations"]
    if (len(replay["actions"])!=303 or len(states)!=304 or len(public)!=304 or len(occupied)!=304 or
            any(s["steps"]!=i or s["match_steps"]!=i%101 or s["team_points"]!=public[i] for i,s in enumerate(states))):
        raise ValueError("Original-Replay und öffentliche Zählung stimmen nicht überein")
    labels = [rival,rival]; labels[side]="Sherlock V15"
    replay["metadata"]["players"]=dict(zip(SIDES,labels))
    wins=match_wins(replay,SIDES[side]); seq=match_sequence(replay,SIDES[side])
    if sum(wins)!=3 or len(seq)!=3 or any(v is None for v in seq) or sum(seq)!=wins[0]:
        raise ValueError("Unvollständige Matchentscheidungen")
    frames=[]; terrain=[]; indexed={}; matches=[]
    for i,state in enumerate(states):
        tiles=state["map_features"]["tile_type"]
        code="".join(str(t) for col in tiles for t in col)
        if code not in indexed:
            indexed[code]=len(terrain); terrain.append(code)
        fleets=[[xy for u,xy in enumerate(state["units"]["position"][t])
                 if state["units_mask"][t][u] and state["units"]["energy"][t][u][0]>=0] for t in (0,1)]
        frames.append(dict(map=indexed[code],fleets=fleets,relics=state["relic_nodes"],scored=occupied[i],
                           public=public[i],points=ends.get(i,public[i]),wins=state["team_wins"]))
        if i in (101,202,303):
            m=i//101
            previous=states[i-1]["team_wins"]
            delta=[v-u for v,u in zip(state["team_wins"],previous)]
            if delta not in ([0,1],[1,0]) or (delta[side]==1)!=seq[m-1]:
                raise ValueError("Siegeränderung an unerwarteter Stelle")
            w=delta.index(1); points=ends[i]
            if points[w]<points[1-w]:
                raise ValueError("Mehr Matchpunkte beim Verlierer")
            matches.append(dict(match=m,points=points,winner=labels[w],tiebreak=points[0]==points[1]))
    turn,reason=scene(frames)
    prev=frames[turn-1]["public"]; cur=frames[turn]["public"]
    coordinates=occupied[turn]
    def cells(t):
        return ", ".join(f"({x}, {y})" for x,y in coordinates[t]) or "keines"
    sentences=[f"Match {(turn-1)//101+1}, Zug {(turn-1)%101+1}: {reason}. "
               f"Der öffentliche Spielstand aus Sicht von V15 geht von {prev[side]}:{prev[1-side]} auf {cur[side]}:{cur[1-side]}.",
               f"Gewertete Felder in diesem Zug – V15: {cells(side)}; {rival}: {cells(1-side)}."]
    summary=dict(seed=seed,v15_side=SIDES[side],opponent=rival,steps=303,team_order=labels,matches=matches,
                 winner=labels[side if wins[0]>wins[1] else 1-side],v15_match_wins=wins[0],opponent_match_wins=wins[1],
                 example=dict(step=turn,reason=reason,text=sentences))
    return summary,dict(summary=summary,width=replay["params"]["map_width"],height=replay["params"]["map_height"],
                        terrain=terrain,frames=frames)


def complete(folder, protocol):
    receipt=json.loads((folder/"receipt.json").read_bytes())
    if receipt["protocol"]!=protocol or set(receipt["files"])!={"partie.html","episode.json.gz","ereignisse.json"}:
        raise ValueError("Abweichender Beleg")
    for name,expected in receipt["files"].items():
        if sha(folder/name)!=expected: raise ValueError(f"Abweichende Datei: {folder/name}")
    return json.loads((folder/"ereignisse.json").read_bytes())["summary"]


def run(out, evidence):
    from scripts.experiment import limit_threads
    limit_threads()
    protocol=hashlib.sha256(json.dumps(evidence,sort_keys=True).encode()).hexdigest()
    out.mkdir(parents=True,exist_ok=True)
    with (out/".record.lock").open("a") as lock, tempfile.TemporaryDirectory(prefix="v15-course-demo-") as scratch:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        protocol_path=out/"herkunft.json"
        if protocol_path.exists() and json.loads(protocol_path.read_bytes())!=evidence: raise ValueError("Abweichende Herkunft")
        protocol_path.write_text(json.dumps(evidence,indent=2,ensure_ascii=False))
        work=Path(scratch)
        with zipfile.ZipFile(PACKAGE) as z: z.extractall(work/"agents")
        sys.path.insert(0,str(work/"agents"))
        paths(work)
        summaries=[]
        for case in CASES:
            dest=out/str(case[0])
            if not dest.exists():
                replay,public,cells,ends=record(work,case)
                summary, view=present(case,replay,public,cells,ends)
                with tempfile.TemporaryDirectory(dir=out,prefix=".replay-") as t:
                    folder=Path(t)/str(case[0]); folder.mkdir()
                    raw=encode(replay).encode()
                    (folder/"episode.json.gz").write_bytes(gzip.compress(raw,compresslevel=6,mtime=0))
                    (folder/"partie.html").write_text(Path(__file__).with_name("v15_demo_view.html").read_text().replace("__FRAMES__",encode(view)))
                    (folder/"ereignisse.json").write_text(encode(dict(summary=summary,public_team_points=public,
                                                                final_match_points={str(k):v for k,v in ends.items()})))
                    receipt=dict(protocol=protocol,full_replay_sha256=hashlib.sha256(raw).hexdigest(),
                                 files={p.name:sha(p) for p in folder.iterdir()})
                    (folder/"receipt.json").write_text(encode(receipt))
                    folder.rename(dest)
            summaries.append(complete(dest,protocol))
        lines=["# Drei V15-Partien im Kursformat","", "Alle drei vorab festgelegten Karten und Sitze sind vertreten. "
               "Die Punktkurven zeigen die öffentlichen Stände. Am Matchende wird der letzte Zuwachs vor dem Reset aus den tatsächlich gewerteten Feldern ergänzt. "
               "Die Karte zeigt die Schiedsrichtersicht. Die beiden Agenten erhielten ausschließlich ihre eigenen Beobachtungen.",""]
        for s in summaries:
            lines.extend([f"## V15 gegen {s['opponent']}","",f"{s['winner']} gewinnt. Matchsiege aus Sicht von V15: "
                          f"{s['v15_match_wins']}:{s['opponent_match_wins']}. Karte {s['seed']}, V15 als {s['v15_side']}.","",
                          " ".join(s["example"]["text"]),"",f"[Partie lokal öffnen]({s['seed']}/partie.html) · "
                          f"[Originalaufnahme, gzip]({s['seed']}/episode.json.gz)",""])
        (out/"README.md").write_text("\n".join(lines))


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("command",choices=("check","run")); p.add_argument("--out",type=Path)
    a=p.parse_args()
    evidence=material()
    if a.command=="check": print(json.dumps(evidence,ensure_ascii=False,indent=2))
    elif a.out is None: p.error("--out ist für run erforderlich")
    else: run(a.out.resolve(),evidence)


if __name__=="__main__": main()
