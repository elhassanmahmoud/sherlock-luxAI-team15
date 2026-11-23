"""Measure public disproof of original mistaken point marks on three reproduced game histories."""
import json
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv

from experiments.analysis.relictsuche_20261123.fehlmarkierung.verfolgen import HERE
from experiments.analysis.relictsuche_20261123.punktspeicher.beweise import PAIR, worlds
from experiments.analysis.relictsuche_20261123.punktgrenzen.archiv import bits
from experiments.analysis.relictsuche_20261123.punktgrenzen.grenzen import PublicBounds, public_row
from experiments.analysis.relictsuche_20261123.vergleich.spielen import Monitor, PACKAGE, write_once
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import point_tile_map


class Contradictions:
    def __init__(self, base, env):
        self.base = base
        self.env = env
        self.memory = PublicBounds()
        self.ticks = []
        self.total = self.camp = self.stay = 0

    def __getattr__(self, name):
        return getattr(self.base, name)

    def act(self, step, obs):
        team = self.base.team_id
        positions = obs["units"]["position"]
        energy = obs["units"]["energy"]
        alive = obs["units_mask"]
        row = public_row(step, team, positions, energy, alive, obs["team_points"],
                         obs["relic_nodes_mask"], obs["relic_nodes"])
        self.memory.observe(row)
        cmd = self.base.act(step, obs)
        belief = self.base._imitation.belief
        known = belief.point_tiles[::-1, ::-1].T if belief.mirrored else belief.point_tiles
        truth = bits(point_tile_map(self.env.state))
        proved_empty = worlds(self.memory.negative)
        assert not (proved_empty & truth)
        wrong = bits(known) & ~truth
        self.total += int(bool(wrong))
        contradicted = bits(known) & proved_empty
        assert contradicted & ~wrong == 0
        if contradicted:
            own = []
            active = np.asarray(alive[team], bool) & (np.asarray(energy[team]).reshape(-1) >= 0)
            for uid in np.flatnonzero(active):
                x,y = map(int, positions[team][uid])
                if (contradicted >> (24*x+y)) & 1:
                    own.append([int(uid), 24*x+y, int(cmd[uid,0])])
            self.camp += len(own)
            self.stay += sum(a==0 for _,_,a in own)
            self.ticks.append(dict(t=step, orbits=sorted({PAIR[i] for i in range(576) if contradicted>>i & 1}), own=own))
        return cmd


def main():
    limit_threads()
    cases = json.loads((HERE/"ursachen.json").read_text())["cases"]
    rows = []
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for ex in cases:
            side = f"player_{ex['team']}"
            other = f"player_{1-ex['team']}"
            actor = Contradictions(r3_package_agent(side,PACKAGE),env)
            opp = make_opponent(ex["opp"],other) if ex["opp"]=="solution92" else r3_package_agent(other,PACKAGE)
            mon = Monitor(env,ex["team"],"discovery")
            play_game(mon,actor,opp,ex["seed"],side,False)
            require_no_agent_errors(actor.base,opp)
            assert mon.digest.hexdigest()==ex["hash"] and mon.matches==ex["matches"] and actor.total==ex["ticks"]
            rows.append(dict(seed=ex["seed"],team=ex["team"],opponent=ex["opp"],
                             original_ticks=actor.total, original_ship_ticks=ex["occupied"],
                             seen_ticks=len(actor.ticks), ship_ticks=actor.camp, stays=actor.stay, states=actor.ticks))
    finally:
        env.close()
    passed=sum(bool(r["seen_ticks"]) for r in rows)>=2 and sum(r["ship_ticks"] for r in rows)>=8
    write_once(HERE/"widerspruch.json",dict(passed=passed,cases=rows))


if __name__=="__main__":
    main()
