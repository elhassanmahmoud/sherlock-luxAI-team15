"""Remove an original positive mark only if an independent public score bound disproves it now."""
from experiments.analysis.relictsuche_20261123.punktgrenzen.grenzen import PublicBounds, public_row
from experiments.analysis.relictsuche_20261123.punktspeicher.beweise import MIRROR, PAIR
from experiments.analysis.relictsuche_20261123.punktwissen.kandidat import PACKAGE
from scripts.r3_package import r3_package_agent


class Corrector:
    def __init__(self, base):
        self.base = base
        self.reset()

    def __getattr__(self, name):
        return getattr(self.base, name)

    def reset(self):
        self.public = PublicBounds()
        self.events = []
        self.last_step = -1

    def new_game(self, player=None):
        self.base.new_game(player)
        self.reset()

    def act(self, step, obs):
        if self.base.env_cfg["unit_sensor_range"] != 1 or step == self.last_step:
            return self.base.act(step, obs)
        row = public_row(step, self.base.team_id, obs["units"]["position"], obs["units"]["energy"],
                         obs["units_mask"], obs["team_points"], obs["relic_nodes_mask"], obs["relic_nodes"])
        self.public.observe(row)
        self.last_step = step
        belief = self.base._imitation.belief
        belief.observe(obs)
        pairs = {PAIR[f] for f in belief._point if (self.public.negative >> PAIR[f]) & 1}
        if pairs:
            belief.records.clear()
            for pair in sorted(pairs):
                for cell in {pair, MIRROR[pair]}:
                    belief._point.discard(cell)
                    belief.point_tiles[divmod(cell,24)] = False
                self.events.append(dict(t=step, pair=pair))
            belief._cand_dirty = belief._coords_dirty = True
            belief._refresh_candidates()
        return self.base.act(step, obs)


def create(side):
    return Corrector(r3_package_agent(side,PACKAGE))
