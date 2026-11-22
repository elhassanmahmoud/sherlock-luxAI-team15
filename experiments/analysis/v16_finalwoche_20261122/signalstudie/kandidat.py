"""Einzige Änderung gegenüber dem untersuchten Kundschafter: öffentliche Auslösung."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "kundschafter"))
# Dieses Modul heißt im Entwicklungsstrang ebenfalls kandidat.py. Eindeutig
# unter eigenem Modulnamen laden, ohne den produktiven Agenten zu verändern.
from importlib.util import module_from_spec, spec_from_file_location
spec = spec_from_file_location("v16_vorheriger_kundschafter", HERE.parent/"kundschafter"/"kandidat.py")
original = module_from_spec(spec)
spec.loader.exec_module(original)
sys.path.insert(0, str(HERE.parent / "paarhinweis"))
from obergrenze import inspect


class SignalScout(original.Scout):
    def __init__(self, side, active):
        super().__init__(side, False)
        self.active = active
        self.side = side
        self.v16_act = self.base.act
        self.base.act = self._unchanged_action_then_public_observation

    def new_game(self, side):
        super().new_game(side)
        self.enable = False
        self.opening = None
        self.previous = None
        self.first_signal = None
        self.sighting = None
        self.fields_third = None

    def _unchanged_action_then_public_observation(self, step, obs):
        action = self.v16_act(step, obs)
        belief = self.base._imitation.belief
        if step == 202:
            self.fields_third = int(belief.point_tiles.sum())
        if not 101 <= step <= 201:
            return action
        t = step-101
        if (belief.match_idx,belief.match_step)!=(1,t):
            raise ValueError("Kein aktueller öffentlicher Wissensstand")
        if belief.known_pairs()>=2 and self.sighting is None:
            self.sighting=t
        scores=list(map(int,obs["team_points"]))
        if self.side=="player_1":
            scores.reverse()
        row=dict(match=2,turn=t,
                 remembered_relic=sorted([list(map(int,p)) for p in belief.relic_positions]),
                 known=sorted(map(int,belief._point)),candidate_n=int(belief.candidate.sum()),
                 public_points=scores)
        if t==0:
            pair=row["remembered_relic"]
            if len(pair)==2 and pair[1]==[23-pair[0][1],23-pair[0][0]]:
                self.opening=row
        if self.opening is not None and self.first_signal is None and 50<=t<=79:
            event=inspect([self.opening,self.previous,row])["joint_first"]
            if event is not None:
                self.first_signal=event
                self.enable=self.active
        self.previous=row
        return action
