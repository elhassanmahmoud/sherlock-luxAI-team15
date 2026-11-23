"""Verifiziert beim gesperrten jeweils anderen Modul jeden der 303 kompletten Mannschaftsbefehle."""
import argparse
from hashlib import sha256
import json
import numpy as np

from technik import selection
from kombination import HERE, SignalScout, Middle, Combination, model
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors


def obs_digest(obs):
    h=sha256()
    def update(data):
        if isinstance(data,dict):
            for key in sorted(data):
                h.update(key.encode());update(data[key])
        else:
            a=np.asarray(data);h.update(a.dtype.str.encode());h.update(str(a.shape).encode());h.update(a.tobytes())
    update(obs);return h.digest()


class Lockstep:
    def __init__(self,candidate,reference):
        self.candidate=candidate;self.reference=reference;self.n=0;self.digest=sha256()
    def new_game(self,side):
        self.candidate.new_game(side);self.reference.new_game(side)
    def set_env_cfg(self,cfg):
        self.candidate.set_env_cfg(cfg);self.reference.set_env_cfg(cfg)
    def act(self,step,obs):
        before=obs_digest(obs)
        cand=self.candidate.act(step,obs)
        if obs_digest(obs)!=before:raise ValueError("Beobachtung des Kandidaten verändert")
        ref=self.reference.act(step,obs)
        if obs_digest(obs)!=before or not np.array_equal(cand,ref):
            raise ValueError(f"Sperre produziert andere Aktionen oder verfälscht die Sicht bei Zug {step}")
        self.n+=1;self.digest.update(np.asarray(cand,dtype="<i2").tobytes())
        return cand


def main():
    ap=argparse.ArgumentParser();ap.add_argument("team",type=int,choices=(0,1));t=ap.parse_args().team
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads();env=LuxAIS3GymEnv(numpy_output=True);nets=model()
    side=f"player_{t}";other=f"player_{1-t}";cases=selection();audits=[]
    for arm,label in (("signal","signal_pruef"),("mitte","mitte_archiv")):
        keys=sorted(k for k,c in cases.items() if k[1]==side and label in c["labels"])
        seed,p=keys[0]
        actor=Combination(p,nets,arm)
        ref=SignalScout(p,True) if arm=="signal" else Middle(p,nets,True)
        joint=Lockstep(actor,ref);enemy=make_opponent("solution92",other)
        outcome=play_game(env,joint,enemy,seed,side,False)
        require_no_agent_errors(actor.base,ref.base);require_no_agent_errors(actor.base,enemy)
        old=cases[seed,p][arm]
        if joint.n!=303 or any(outcome[k]!=old[k] for k in ("game_win","our_wins","opp_wins","our_points","opp_points")):
            raise ValueError("Das eindeutige Original wurde nicht reproduziert")
        audits.append(dict(seed=seed,side=side,arm=arm,identical_observations_and_commands=joint.n,actions_sha256=joint.digest.hexdigest()))
    (HERE/"technik"/f"paritaet_{t}.json").write_text(json.dumps(audits,indent=2)+"\n")
    print(audits)


if __name__=="__main__":main()
