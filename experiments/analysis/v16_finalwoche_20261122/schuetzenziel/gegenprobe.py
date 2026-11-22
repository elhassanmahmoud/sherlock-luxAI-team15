"""Independent coordinate/energy reconstruction of every mutually available teacher target pair."""
from collections import Counter,defaultdict
from itertools import combinations
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"netzwahl"))
from vorhersagen import input_files


def verify(base):
    overall=Counter(); conflicts=[]; tagged=set()
    for meta,p,source in input_files(base,False,include_validation=False):
        with np.load(p,allow_pickle=False) as z:
            shot=np.flatnonzero(z["act"]==5)
            coord=z["pos"][shot].astype(int); feat=z["feats"][shot].astype(float)
            dx=z["sdx"][shot].astype(int); dy=z["sdy"][shot].astype(int)
            unit=z["uid"][shot]; step=z["step"][shot]; w,h=z["planes"].shape[-2:]
        frames=defaultdict(list)
        for i in range(len(shot)):
            x,y=map(int,coord[i]); tx,ty=x+int(dx[i]),y+int(dy[i]); rad=round(7*feat[i,8])
            if (round(400*feat[i,2]) < round(50*feat[i,7]) or not (0<=tx<w and 0<=ty<h)
                    or max(abs(x-tx),abs(y-ty))>rad):
                continue
            bounds=(max(0,x-rad),min(w-1,x+rad),max(0,y-rad),min(h-1,y+rad))
            frames[int(step[i])].append((int(unit[i]),(tx,ty),bounds))
            overall["legal_shots"]+=1
        for f,shooters in frames.items():
            for a,b in combinations(shooters,2):
                overall["pairs"]+=1
                left=max(a[2][0],b[2][0]);right=min(a[2][1],b[2][1])
                low=max(a[2][2],b[2][2]);high=min(a[2][3],b[2][3])
                if left>right or low>high:continue
                overall["overlap"]+=1
                if not all(left<=x<=right and low<=y<=high for x,y in (a[1],b[1])):continue
                overall["mutual"]+=1
                if a[1]==b[1]:continue
                overall["conflict_pairs"]+=1
                conflicts.append(dict(seed=meta["seed"],side=meta["side"],frame=f,source=source,
                                      shooters=[a[0],b[0]],targets=[a[1],b[1]],intersection=[left,right,low,high]))
                tagged.update((meta["seed"],f,u) for u in (a[0],b[0]))
    overall["conflicting_rows"]=len(tagged)
    overall["conflict_frames"]=len({(s,f) for s,f,u in tagged})
    overall["maps_with_conflicts"]=len({s for s,f,u in tagged})
    original=json.loads((HERE/"struktur.json").read_text())["totals"]
    if any(overall[k]!=v for k,v in original.items() if k!="gate"):raise ValueError("Counts disagree")
    return dict(counts=dict(overall),pairs=conflicts)


if __name__=="__main__":print(json.dumps(verify(Path(sys.argv[1])),indent=2))
