"""Rekonstruiert genau die drei Solution-Verluste aus dem vorab abgeschlossenen Kombivergleich."""
import gzip
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
STUDY = HERE.parents[2]
sys.path.insert(0, str(STUDY / "solution/frueh"))
from messen import MatchRecord, PACKAGES, limit_threads, make_opponent, measure_options, play_game, r3_package_agent
from scripts.par_eval import require_no_agent_errors
from scripts.scoring import point_tile_map

CASES = ((160386062, "player_0"), (160386062, "player_1"), (160386070, "player_1"))
KEYS = ("steps", "our_points", "opp_points", "our_wins", "opp_wins", "game_win")


class Trace(MatchRecord):
    def __init__(self, env, agent, side):
        super().__init__(env)
        self.inner = agent._imitation
        self.side = side
        self.samples = []

    def reset(self, **kwargs):
        observations, info = super().reset(**kwargs)
        self.own_obs = observations[self.side]
        return observations, info

    def step(self, actions):
        turn = len(self.frames)
        if turn < 101:
            obs = self.own_obs
            belief = self.inner.belief
            if turn != int(obs["match_steps"]) or (belief.match_idx, belief.match_step) != (0, turn):
                raise ValueError("Falscher Wissens- oder Zeitstand")
            true_tiles = point_tile_map(self.env.state)
            coverage, legal, ordered = measure_options(obs, self.side, self.inner, actions[self.side], true_tiles)
            own = int(self.side[-1])
            paired = bool(belief.mirrored)
            known = np.asarray(belief.point_tiles, dtype=bool)
            if paired:
                known = known[::-1, ::-1].T
            rawnodes = [[*map(int, xy)] for xy in np.asarray(obs["relic_nodes"])[np.asarray(obs["relic_nodes_mask"], dtype=bool)]]
            if coverage["known"] != coverage["known_true"]:
                raise ValueError("Bekannte Punkte nicht in aktiver Referenz")
            sample = dict(turn=turn, score_before=list(map(int,np.asarray(obs["team_points"])[[own,1-own]])),
                          true_tiles=int(true_tiles.sum()), true_relics=int(np.asarray(self.env.state.relic_nodes_mask).sum()),
                          public_relics=len(belief.relic_positions), visible_relic_positions=rawnodes,
                          unresolved=int(belief.candidate.sum()), **dict(coverage))
        result = super().step(actions)
        self.own_obs = result[0][self.side]
        if turn < 101:
            own_scored, opp_scored = self.frames[-1][own], self.frames[-1][1-own]
            sample.update(our_gain=len(own_scored), opponent_gain=len(opp_scored),
                          our_scored_previously_known=sum(bool(known[p]) for p in own_scored),
                          opponent_scored_previously_known=sum(bool(known[p]) for p in opp_scored),
                          legal_scored=len(legal & own_scored), ordered_scored=len(ordered & own_scored))
            self.samples.append(sample)
        return result


def record(labels, references):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    pkg, signature = PACKAGES["v16"]
    if hashlib.sha256(pkg.read_bytes()).hexdigest() != signature:
        raise ValueError("Falsches Release")
    env = LuxAIS3GymEnv(numpy_output=True)
    cases = []
    for seed, side in labels:
        agent = r3_package_agent(side, pkg)
        team = int(side[-1])
        opponent = make_opponent("solution92", f"player_{1-team}")
        recorder = Trace(env, agent, side)
        replay = play_game(recorder, agent, opponent, seed, side, train=False)
        require_no_agent_errors(agent, opponent)
        reference = references[seed,side]
        if len(recorder.samples) != 101 or any(replay[k]!=reference[k] for k in KEYS) or recorder.match_winners!=reference["match_winners"]:
            raise ValueError(f"Abweichendes Ergebnis: {seed}/{side}")
        if any(
            [sum(r[k] for r in recorder.samples[:t]) for k in ("our_gain","opponent_gain")]!=s["score_before"]
            for t,s in enumerate(recorder.samples)):
            raise ValueError("Kumulierte Züge ergeben nicht die öffentlichen Anzeigewerte")
        print(seed, side, "reproduziert", flush=True)
        cases.append(dict(seed=seed, side=side, total={k:replay[k] for k in KEYS},
                          match_winners=recorder.match_winners, frames=recorder.samples))
    return cases


def main():
    limit_threads()
    _, signature = PACKAGES["v16"]
    archive = [r for lane in (0, 1) for r in map(json.loads, (HERE.parent/"frisch"/f"worker_{lane}.jsonl").read_text().splitlines())]
    losses = {(r["seed"],r["side"]):r for r in archive if r["arm"]=="aus" and r["opponent"]=="solution92" and not r["game_win"]}
    if set(losses) != set(CASES):
        raise ValueError("Die Fälle sind nicht alle verbliebenen Originalverluste")
    cases = record(CASES,losses)
    raw = json.dumps(dict(v16_sha256=signature,cases=cases),separators=(",",":")).encode()
    (HERE/"zugdaten.json.gz").write_bytes(gzip.compress(raw,mtime=0))


if __name__=="__main__":
    main()
