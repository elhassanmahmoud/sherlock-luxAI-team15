"""Replay the scout and advance only later confirmed true scoring pairs inside its known relic areas."""
import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv

from experiments.analysis.relictsuche_20261123.kundschafter_feldwissen.spielen import archive
from experiments.analysis.relictsuche_20261123.ortundflotte.kandidat import create
from experiments.analysis.relictsuche_20261123.vergleich.spielen import Monitor, sha, write_once
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.scoring import point_tile_map

HERE = Path(__file__).resolve().parent
SEATS = HERE.parent / "kundschafter_feldwissen/faelle.json"


class AdvanceKnowledge(Monitor):
    def __init__(self, env, actor, team, extra):
        super().__init__(env, team, "discovery", actor)
        decide = actor.base.act
        self.extra = set(extra)
        self.visits = Counter()
        self.later = {}
        self.opening = None

        def record(step, obs):
            if step < 101:
                live = np.asarray(obs["units_mask"][team], bool)
                live = live & (np.asarray(obs["units"]["energy"][team]).reshape(-1) >= 0)
                pos = np.asarray(obs["units"]["position"][team])[live]
                if team:
                    pos = 23 - pos[:, ::-1]
                self.visits.update(set(int(x * 24 + y) for x, y in pos))
            if step == 101:
                self.opening = self.digest.hexdigest()
                belief = actor.base._imitation.belief
                belief.observe(obs)
                truth = point_tile_map(env.state)
                if belief.mirrored:
                    truth = truth[::-1, ::-1].T
                self.already = sorted(belief._point)
                self.eligible = set(np.flatnonzero(truth & belief.relic_zone).tolist()) - set(self.already)
                assert self.extra <= self.eligible
                if self.extra & belief._dead:
                    belief.records.clear()
                for cell in sorted(self.extra):
                    belief._mark_point(cell)
                if self.extra:
                    belief._refresh_candidates()
                    assert self.extra <= belief._point
            result = decide(step=step, obs=obs)
            if 101 < step <= 201:
                for cell in actor.base._imitation.belief._point & self.eligible:
                    self.later.setdefault(int(cell), step)
            return result

        actor.base.act = record


def game(env, seed, team, extra=()):
    side = f"player_{team}"
    scout = create(side)
    rival = make_opponent("solution92", f"player_{1-team}")
    observer = AdvanceKnowledge(env, scout, team, extra)
    result = play_game(observer, scout, rival, seed, side, False)
    require_no_agent_errors(scout, rival)
    won = result["game_win"]
    assert observer.turn == 303 and won == int(sum(m["win"] for m in observer.matches) >= 2)
    return dict(opening=observer.opening, digest=observer.digest.hexdigest(), matches=observer.matches,
                win=won, already=observer.already, eligible=sorted(observer.eligible), later=observer.later,
                visits={c: observer.visits[c] for c in sorted(observer.eligible)}, extra=sorted(extra),
                sight=observer.first_sight, credit=observer.first_credit)


def compare(base, other):
    for field in ["opening", "already", "eligible", "visits", "sight", "credit"]:
        assert base[field] == other[field], field
    assert base["matches"][0] == other["matches"][0]
    if not other["extra"]:
        assert base["digest"] == other["digest"]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder", type=Path)
    a = p.parse_args()
    limit_threads()
    saved = json.loads(SEATS.read_bytes())["seats"]
    cards = sorted({r["seed"] for r in saved if not r["both"]})
    assert len(cards) == 2
    bank = archive()[0]
    cases = []
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for seed in cards:
            for team in (0, 1):
                base = game(env, seed, team)
                official = bank[seed, team, "joint"]
                assert base["digest"] == official["hash"] and base["matches"] == official["matches"]
                pair = game(env, seed, team, base["later"]) if base["later"] else base
                compare(base, pair)
                singles = []
                if pair["win"] > base["win"]:
                    pending = set(base["later"])
                    while pending:
                        c = min(pending)
                        x, y = divmod(c, 24)
                        symmetric = 24 * (23-y) + 23-x
                        group = {c, symmetric}
                        assert group <= pending
                        trial = pair if group == set(base["later"]) else game(env, seed, team, group)
                        compare(base, trial)
                        singles.append(dict(cells=sorted(group), win=trial["win"], matches=trial["matches"]))
                        pending -= group
                case = dict(seed=seed, team=team, original=base, advanced=pair, single_pairs=singles)
                write_once(a.folder / f"{seed}_{team}.json", case)
                cases.append(case)
    finally:
        env.close()
    write_once(HERE/"ergebnis.json", dict(seats_source=sha(SEATS), plan=sha(HERE/"PLAN.md"), cases=cases))


if __name__ == "__main__":
    main()
