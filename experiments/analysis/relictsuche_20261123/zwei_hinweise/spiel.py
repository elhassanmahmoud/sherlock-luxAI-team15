"""Separate two simultaneous public clues in the sole extra held-out win."""
import gzip
import json
from pathlib import Path
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.punktwissen.kandidat import Knowledge,PACKAGE
from experiments.analysis.relictsuche_20261123.punktwissen.spiele import Tape,decoded
from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha,write_once
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent

HERE=Path(__file__).resolve().parent


class OnlyClues(Knowledge):
    def __init__(self,base,mode,selected):
        self.mode=mode;self.selected=selected
        super().__init__(base)

    def reset(self):
        super().reset()
        original=self.proof.observe
        def gate(row):
            positives=original(row)
            return [c for c in positives if (c in self.selected)==(self.mode=="only")]
        self.proof.observe=gate


def main():
    limit_threads()
    bank=HERE.parent/"punktwissen/allgemein_partien.jsonl.gz"
    with gzip.open(bank,"rt") as f:
        data={(r["seed"],r["team"],r["version"]):r for r in map(json.loads,f) if r["opponent"]=="solution92"}
    changed=[(s,t) for s,t,a in data if a=="neu" and data[s,t,a]["win"]>data[s,t,"v16"]["win"]]
    assert len(changed)==1
    seed,t=changed[0];ref,full=[data[seed,t,k] for k in ("v16","neu")]
    first=full["events"][0]["t"];marks=sorted(e["world"] for e in full["events"] if e["t"]==first)
    assert len(set(marks))==2
    cases=[("v16",None,[]),("alle",None,[]),("erstes","only",marks[:1]),("zweites","only",marks[1:]),
           ("beide","only",marks),("spaetere","except",marks)]
    env=LuxAIS3GymEnv(numpy_output=True);rows={}
    try:
        for label,mode,values in cases:
            side=f"player_{t}";orig=r3_package_agent(side,PACKAGE);foe=make_opponent("solution92",f"player_{1-t}")
            actor=orig if label=="v16" else Knowledge(orig) if label=="alle" else OnlyClues(orig,mode,set(values))
            tap=Tape(env,t,actor if label!="v16" else None);result=play_game(tap,actor,foe,seed,side,False)
            require_no_agent_errors(orig,foe)
            anchor=ref if label=="v16" else full if label=="alle" else None
            cmds=np.stack(tap.commands);digest=tap.digest.hexdigest()
            if anchor:
                assert np.array_equal(cmds,decoded(anchor)) and tap.matches==anchor["matches"] and digest==anchor["digest"]
            assert tap.turn==303 and result["game_win"]==int(sum(m["win"] for m in tap.matches)>=2)
            events=[] if label=="v16" else actor.events
            dif=np.flatnonzero(np.any(cmds!=decoded(ref),axis=(1,2,3)))
            idx=int(dif[0]) if len(dif) else None
            assert idx is None or idx>=min(e["t"] for e in events)
            units=[] if idx is None else np.flatnonzero(np.any(cmds[idx,t]!=decoded(ref)[idx,t],axis=1)).tolist()
            rows[label]=dict(allowed_ids=values,events=events,first_command=idx,ships=units,matches=tap.matches,
                 win=result["game_win"],digest=digest,sight=tap.first_sight,credit=tap.first_credit)
    finally:env.close()
    write_once(HERE/"ergebnis.json",dict(seed=seed,team=t,source_archive=sha(bank),initial=marks,cases=rows))


if __name__=="__main__":main()
