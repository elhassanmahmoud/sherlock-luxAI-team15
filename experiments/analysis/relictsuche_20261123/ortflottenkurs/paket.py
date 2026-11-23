"""Build reproducible, separate competition-layout and native research archives from frozen sources."""
import argparse
import ast
from hashlib import sha256
import io
import json
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED,ZipFile,ZipInfo

HERE=Path(__file__).resolve().parent
D=HERE.parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT))
from experiments.analysis.relictsuche_20261123.vergleich.spielen import common_source,sha,stamp,require
from experiments.analysis.relictsuche_20261123.flottenkurs.paket import WRAPPER as FLEET_WRAPPER, OFFICIAL,WEIGHT
from scripts.build_submission import battle_paths,check_battle

COURSE=ROOT/"dist/Gruppe15.zip"
NATIVE=ROOT/"experiments/releases/20261117_sherlock_v16/agent.zip"
NATIVE_SHA="0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"
DEFAULT=Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/ortflottenkurs")


def provenance():
    joint=D/"ortundflotte"
    pilot=json.loads((joint/"duelle.json").read_bytes())
    val=json.loads((joint/"valid.json").read_bytes())
    official=[joint/n for n in ("PLAN.md","richtung.py","kandidat.py","spielen.py","train.json","valid.json")]
    official.extend(D/"flottenblick"/n for n in ("flotte.py","kandidat.py","vorhersage.py","flottengewichte.npz","modell.json"))
    pilot_id=stamp(dict(common=common_source(),files={str(p.relative_to(D)):sha(p) for p in official}))
    require(pilot["passed"] and pilot["games"]==288 and pilot["source"]==pilot_id and val["selected"] in (1,2),"Fresh panel source or weights changed")
    prior=D/"zielschaetzer";other=[prior/"kandidat.py",prior/"ort.json",D/"routenlernen/routes.py"]
    archived=json.dumps(json.loads((D/"vergleich/discovery/herkunft.json").read_bytes()),sort_keys=True)
    fleet=json.dumps(json.loads((D/"flottenblick/ganzspiel/serie.json").read_bytes()),sort_keys=True)
    require(all(sha(p) in archived for p in other[:2]) and sha(other[2]) in fleet,"Transitive model input differs from earlier frozen evaluation")
    return {"fresh_pilot_source":pilot_id,"fresh_result":sha(joint/"duelle.json"),"prior_index":val["selected"],
            "runtime_and_lineage":{str(p.relative_to(ROOT)):sha(p) for p in official+other}}


def packed_prior():
    p=D/"zielschaetzer/kandidat.py"
    text=p.read_text();lines=text.splitlines()
    nodes=ast.parse(text).body
    xy=next(n for n in nodes if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=="COORD")
    fn=next(n for n in nodes if isinstance(n,ast.FunctionDef) and n.name=="parameters")
    source="from functools import lru_cache\nfrom pathlib import Path\nimport json\nimport numpy as np\n\nHERE=Path(__file__).resolve().parent\n"
    return (source+"\n".join(lines[xy.lineno-1:xy.end_lineno])+"\n\n"+"\n".join(lines[min(d.lineno for d in fn.decorator_list)-1:fn.end_lineno])+"\n").encode()


def runtime(prior_index):
    f=D/"flottenblick"
    def xcode(path):
        s=path.read_text()
        transforms={"experiments.analysis.relictsuche_20261123.flottenblick.kandidat":".kundschafter",
                    "experiments.analysis.relictsuche_20261123.flottenblick.flotte":".flotte",
                    "experiments.analysis.relictsuche_20261123.flottenblick.vorhersage":".vorhersage",
                    "experiments.analysis.relictsuche_20261123.routenlernen.routes":".routes",
                    "experiments.analysis.relictsuche_20261123.zielschaetzer.kandidat":".ortsprior",
                    "experiments.analysis.relictsuche_20261123.ortundflotte.richtung":".richtung"}
        for old,new in transforms.items():s=s.replace("from "+old+" import","from "+new+" import")
        if path.name=="kandidat.py":
            s=s[:s.index("\ndef create(side")]
            s="\n".join(z for z in s.splitlines() if not z.startswith(("from scripts.", "HERE =", "HERE=", "PACKAGE =","from pathlib import Path","import json")))
            s=s.replace("MIRROR_DIR, PACKAGE, flat","MIRROR_DIR, flat")
        require("from experiments" not in s and "from scripts" not in s and "import sherlock" not in s,"Nonportable runtime code")
        ast.parse(s)
        return (s.rstrip()+"\n").encode()
    main=FLEET_WRAPPER.replace("from .kundschafter import FleetScout","from .sucher import JointScout").replace("class Agent_x(FleetScout):","class Agent_x(JointScout):").replace(" *load())",f" *load(), {prior_index})")
    require(" *load(), " in main,"Wrapper prior missing")
    return {"main.py":main.encode(),"kundschafter.py":xcode(f/"kandidat.py"),"sucher.py":xcode(D/"ortundflotte/kandidat.py"),
        "richtung.py":xcode(D/"ortundflotte/richtung.py"),"flotte.py":xcode(f/"flotte.py"),"vorhersage.py":xcode(f/"vorhersage.py"),
        "routes.py":xcode(D/"routenlernen/routes.py"),"ortsprior.py":packed_prior(),"ort.json":(D/"zielschaetzer/ort.json").read_bytes(),
        "modell.json":(f/"modell.json").read_bytes(),"flottengewichte.npz":(f/"flottengewichte.npz").read_bytes()}


def content(base,kind,policy):
    require(sha(base)==(OFFICIAL if kind=="Gruppe15" else NATIVE_SHA),"Release ZIP changed")
    with ZipFile(base) as z:parts={k:z.read(k) for k in z.namelist()}
    weight=kind+("/agent.pth" if kind=="Gruppe15" else "/weights/agent.pth")
    require(sha256(parts[weight]).hexdigest()==WEIGHT,"Wrong base network bytes")
    for k in list(parts):
        if k.endswith(".py"):parts[k]=parts[k].replace(b"from .main import ",b"from .v16_main import ")
    parts[kind+"/v16_main.py"]=parts[kind+"/main.py"]
    for name,bytes_ in policy.items():
        require(name=="main.py" or kind+"/"+name not in parts,"Candidate name collides with original")
        parts[kind+"/"+name]=bytes_
    if kind=="Gruppe15":
        parts[kind+"/LIESMICH.txt"]=("Team 15 – Sherlock mit gemeinsamer Wahl von Reliktort und Flottensicht\n"
            "Die Kursklasse ist Gruppe15.main.Agent_x. Beide Spieler verwenden Gruppe15/agent.pth.\n"
            "Die Vorhersage verwendet flottengewichte.npz, modell.json und ort.json aus demselben Ordner.\n").encode()
    return parts


def encoded(parts):
    buf=io.BytesIO()
    with ZipFile(buf,"w") as z:
        for k,v in sorted(parts.items()):
            info=ZipInfo(k,(2026,11,23,0,0,0));info.compress_type=ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,v)
    return buf.getvalue()


def build(folder):
    folder=folder.resolve()
    require(not any(folder.is_relative_to((ROOT/d).resolve()) for d in ("dist","agents","experiments/releases")),
            "Cannot write into official agent, release or dist paths")
    info=provenance()
    folder.mkdir(parents=True,exist_ok=True)
    results={}
    for kind,base,name in (("Gruppe15",COURSE,"Gruppe15.zip"),("sherlock",NATIVE,"agent.zip")):
        obj=content(base,kind,runtime(info["prior_index"]))
        raw=encoded(obj)
        # Independent reconstruction from the unchanged sources; the intermediate member objects are rebuilt.
        require(raw==encoded(content(base,kind,runtime(provenance()["prior_index"]))),"Nondeterministic rebuild")
        path=folder/name
        if not path.exists():
            with path.open("xb") as dest:dest.write(raw)
        require(path.read_bytes()==raw,"Existing archive differs")
        with ZipFile(path) as z:require(z.testzip() is None and all(z.read(k)==v for k,v in obj.items()),"Wrong stored ZIP")
        if kind=="Gruppe15":check_battle(path,battle_paths(15,True))
        results[name]=dict(path=str(path),sha256=sha(path),original_sha256=sha(base),bytes=len(raw),member_count=len(obj),
                           base_weight_sha256=WEIGHT,forecast_weight_sha256=sha256(obj[kind+"/flottengewichte.npz"]).hexdigest())
    info["archives"]=results
    (HERE/"pakete.json").write_text(json.dumps(info,indent=2)+"\n")
    print(json.dumps(results),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--out",type=Path,default=DEFAULT)
    build(p.parse_args().out)
