"""Check every move against independently recorded original-V16 normal-vision commands."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from kandidat import create
from scripts.experiment import limit_threads
from scripts.xversion_replay import require_clean_policy

TAPES = Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/routenlernen/tapes")


def main():
    limit_threads()
    results = []
    # Routenlernen had no intervention and was compared on exactly these normalsight tapes to V16.
    for idx,s in enumerate(("player_0","player_1")):
        path = TAPES/f"161050000_{s}.npz"
        with np.load(path, allow_pickle=False) as r:
            meta = json.loads(str(r["metadata"]))
            data = {k: r[k] for k in r.files if k != "metadata"}
        if meta["cfg"]["unit_sensor_range"] <= 1 or meta["changes"] != 0 or meta["side"] != s:
            raise ValueError("Wrong normal-sight reference")
        # Reuse the very same instance on the second seat to check game/side reset.
        if idx == 0:
            agent = create(s)
        agent.new_game(s)
        agent.set_env_cfg(meta["cfg"])
        for step, ref in enumerate(data["commands"]):
            obs = {}
            for k,v in data.items():
                if k == "commands":
                    continue
                if "/" in k:
                    a,b = k.split("/",1)
                    obs.setdefault(a,{})[b] = v[step]
                else:
                    obs[k] = v[step]
            if agent.base.team_id != idx or not np.array_equal(agent.act(step,obs),ref):
                raise ValueError(f"Wrong normal-sight action or side at turn {step}")
        require_clean_policy(agent.base,s)
        if agent.changes != 0 or agent.event is not None or len(data["commands"]) != 303:
            raise ValueError("Active normal-sight scout")
        results.append(dict(side=s, source_sha256=sha256(path.read_bytes()).hexdigest(),
                            unit_commands=int(np.prod(data["commands"].shape[:2])), changes=0))
    (HERE/"normalsicht.json").write_text(json.dumps(dict(seats=results, reused_on_other_side=True),indent=2)+"\n")


if __name__=="__main__":
    main()
