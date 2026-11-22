"""Drei vorab gewählte Archive; tatsächliches V16-Gedächtnis auf Teambeobachtungen fremder Partien."""
from hashlib import sha256
import gzip
import inspect as inspect_module
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0,str(HERE.parent))
from obergrenze import inspect, ARCHIVE, ARCHIVE_DIGEST, ENV_SHA, STATE_SHA
from importlib.metadata import distribution

SOURCES=ROOT/"docs/presentation/finale_2711/replays"
ZIP=ROOT/"experiments/releases/20261117_sherlock_v16/agent.zip"
V16="0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"
SEEDS=range(7171000,7171003)


def project(row,team):
    sight = np.asarray(row["vision_power_map"])[team]>0
    pos=np.asarray(row["units"]["position"])
    mask=np.asarray(row["units_mask"],dtype=bool).copy()
    other=1-team
    mask[other] &= sight[pos[other,:,0],pos[other,:,1]]
    active=np.asarray(row["relic_nodes"],dtype=int).reshape(-1,2)
    # Der Serializer entfernt inaktive Slots. Die Engine ordnet die erste Hälfte
    # der Relikte zuerst an, danach die jeweiligen Spiegel gegenüber.
    half=len(active)//2
    slots=([*range(half),*range(3,3+half)])
    if len(slots)!=len(active): raise ValueError("Unpaarige Relikte")
    relic_pos=np.full((6,2),-1,dtype=int)
    relic_mask=np.zeros(6,dtype=bool)
    for slot,(x,y) in zip(slots,active):
        if sight[x,y]:
            relic_pos[slot]=(x,y)
            relic_mask[slot]=True
    return dict(steps=row["steps"],match_steps=row["match_steps"],team_points=row["team_points"],team_wins=row["team_wins"],
                units={"position":np.where(mask[...,None],pos,-1),"energy":np.where(mask,np.asarray(row["units"]["energy"])[...,0],-1)},
                units_mask=mask,sensor_mask=sight,relic_nodes=relic_pos,relic_nodes_mask=relic_mask,
                map_features={k:np.where(sight,np.asarray(v),-1) for k,v in row["map_features"].items()})


def observations(data,team,flags):
    from sherlock.belief import Belief
    init_params=inspect_module.signature(Belief).parameters
    b=Belief(team,**{k:v for k,v in flags.items() if k in init_params})
    for k,v in flags.items():
        if k not in init_params and k!="mirrored":
            setattr(b,k,v)
    b.sensor_range=int(data["params"]["unit_sensor_range"])
    frames=[]
    first_sight=None
    for step,row in enumerate(data["observations"][:202]):
        if row["steps"]!=step or row["match_steps"]!=step%101: raise ValueError("Lückenhafte Aufnahme")
        public=project(row,team)
        b.observe(public)
        if step>=101:
            t=step-101
            if b.known_pairs()>=2 and first_sight is None:
                first_sight=t
            frames.append(dict(match=2,turn=t,remembered_relic=sorted([list(map(int,r)) for r in b.relic_positions]),
                               known=sorted(map(int,b._point)),candidate_n=int(b.candidate.sum()),
                               public_points=[row["team_points"][team],row["team_points"][1-team]]))
    if len(frames[0]["remembered_relic"])!=2:
        return {"eligible":0,"joint_count":0,"joint_first":None,"first_seen":first_sight,"opening_pair":False}
    signals=inspect(frames)
    return dict(eligible=signals["eligible"],joint_count=signals["joint_count"],joint_first=signals["joint_first"],
                first_seen=first_sight,opening_pair=True)


def main():
    if sha256(ZIP.read_bytes()).hexdigest()!=V16 or sha256(ARCHIVE.read_bytes()).hexdigest()!=ARCHIVE_DIGEST:
        raise ValueError("Anderes Abgabepaket oder andere gemessene Modelleinstellungen")
    sys.path.insert(0,str(ZIP))
    flags_raw=json.loads(gzip.decompress(ARCHIVE.read_bytes()))
    flags=flags_raw["v16"]["7261020"]["flags"]
    ref=json.loads((SOURCES/"herkunft.json").read_bytes())
    if ref["engines"]["env.py"]!=ENV_SHA or ref["engines"]["state.py"]!=STATE_SHA:
        raise ValueError("Andere Engine in der Aufnahme")
    installed=distribution("luxai-s3")
    for name,digest in (("env.py",ENV_SHA),("state.py",STATE_SHA)):
        if sha256(Path(installed.locate_file("luxai_s3/"+name)).read_bytes()).hexdigest()!=digest:
            raise ValueError("Abweichende Engine")
    full={}
    observed={}
    for seed in SEEDS:
        folder=SOURCES/str(seed)
        raw=(folder/"episode.json.gz").read_bytes()
        receipt=json.loads((folder/"receipt.json").read_bytes())
        if sha256(raw).hexdigest()!=receipt["files"]["episode.json.gz"]: raise ValueError("Archivfehler")
        expanded=gzip.decompress(raw)
        if sha256(expanded).hexdigest()!=receipt["full_replay_sha256"]: raise ValueError("Dekompressionsabweichung")
        replay=json.loads(expanded)
        if replay["metadata"]["seed"]!=seed or len(replay["observations"])!=304: raise ValueError("Unerwartete Partie")
        full[seed]=replay
        observed[seed]={f"player_{t}":observations(replay,t,flags) for t in (0,1)}
    # Erst nachdem für alle sechs Perspektiven die Signale feststehen: externe Wahrheit.
    cases=[]
    for seed,data in full.items():
        sizes=[len(r["relic_nodes"])//2 for r in data["observations"][101:202]]
        second=next((t for t,n in enumerate(sizes) if n>=2),None)
        for row in observed[seed].values():
            first=row["joint_first"]
            t=first["turn"] if first else None
            row["signal_while_absent"]=t is not None and (second is None or t<second)
            row["lead_until_sighting"]=row["first_seen"]-t if t is not None and row["first_seen"] is not None else None
        cases.append({"seed":seed,"true_second_pair_first_active":second,"public":observed[seed]})
    output={"archive_seeds":list(SEEDS),"recorded_trajectories":"V15/V14, V15/Solution_92, V15/Kaggle",
            "v16_belief_from_release":V16,"observation_rows":3*2*202,"cases":cases}
    (HERE/"ergebnis.json").write_text(json.dumps(output,indent=2)+"\n")


if __name__=="__main__":
    main()
