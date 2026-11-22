"""Wiederholt nur tatsächlich geänderte Entwicklungssitze für Felder und öffentliche Sensorsichten."""
import json
import os

import numpy as np

from aktion import HERE, SignalScout, GroundTruth, baseline_data, SCORES
from aktionsbilanz import load_selection
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads


class SensorScout(SignalScout):
    """Fängt allein die vom Team wirklich empfangene Sicht in Originalkoordinaten ab."""
    def new_game(self, side):
        super().new_game(side)
        self.sight = {}
        self.ended = None

    def act(self,step,obs):
        prev=self.finished
        move=super().act(step,obs)
        if 101<=step<=201:
            t=step-101
            self.sight[t]=np.asarray(obs["sensor_mask"],dtype=bool).copy()
            if self.start is not None and self.finished and not prev:
                self.ended=t
        return move


def covered(frames,start,end):
    return np.logical_or.reduce([frames[t] for t in range(start,end+1)])


def compare_sensors(original, candidate, start, end):
    # Eine Bewegung in t beeinflusst die nächste Beobachtung. Die gemeinsame
    # Ausgangssicht schließt t ein, der Vergleich beginnt in t+1.
    until_start=covered(original,49,start)
    if (not np.array_equal(until_start,covered(candidate,49,start))
            or not np.array_equal(original[start],candidate[start])):
        raise ValueError("Suchaufträge hatten ungleiche Sicht vor ihrem ersten Auftrag")
    left=covered(original,start+1,end)&~until_start
    right=covered(candidate,start+1,end)&~until_start
    # IDs in physischen Engine-Koordinaten x*24+y, unabhängig von der Spielerperspektive.
    return dict(known_since49_at_start=int(until_start.sum()),original_new=int(left.sum()),
                candidate_new=int(right.sum()),common_new=int((left&right).sum()),
                candidate_exclusive=np.flatnonzero(right&~left).tolist(),
                original_exclusive=np.flatnonzero(left&~right).tolist())


def main():
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv
    all_rows=load_selection()
    baseline=baseline_data()
    expected=sorted([r for r in all_rows if r["opponent"]=="solution92" and r["changes"]],
                    key=lambda r:(r["seed"],r["side"]))
    folder=HERE/"aktion"
    checkpoints=folder/"feldkontrolle.jsonl"
    stored=list(map(json.loads,checkpoints.read_text().splitlines())) if checkpoints.exists() else []
    keys=[(r["seed"],r["side"]) for r in expected]
    if [(r["seed"],r["side"]) for r in stored]!=keys[:len(stored)]:
        raise ValueError("Fremde oder doppelte Nachmessung")
    env=LuxAIS3GymEnv(numpy_output=True)
    for r in expected[len(stored):]:
        seed,side=r["seed"],r["side"]
        orig=baseline[seed,side]
        other="player_1" if side=="player_0" else "player_0"
        observed={}
        for is_candidate in (False,True):
            ref=r if is_candidate else orig
            me=SensorScout(side,is_candidate)
            trace=GroundTruth(env)
            res=play_game(trace,me,make_opponent("solution92",other),seed,side,False)
            if (any(res[k]!=ref[k] for k in SCORES) or me.changes!=ref.get("changes",[])
                    or trace.match_winners!=ref["match_winners"] or me.sighting!=ref["known_second"]
                    or me.first_signal!=r["first"] or me.base.caught_errors or getattr(me.base._imitation,"caught_errors",0)):
                raise ValueError("Ausgang oder geänderte Befehle nicht reproduziert")
            observed[is_candidate]=me
        before,after=observed[False],observed[True]
        if (after.start!=r["start"] or after.reason!=r["stop"] or after.fields_third!=r["fields_match3_step0"]
                or after.known_at_third!=r["fields_match3_step1"] or after.ended is None):
            raise ValueError("Auftrags-/Feldstand des Kandidaten nicht belegt")
        row=dict(seed=seed,side=side,baseline_step0=before.fields_third,candidate_step0=after.fields_third,
                 baseline_step1=before.known_at_third,candidate_step1=after.known_at_third,
                 start=after.start,end_exclusive=after.ended,duration=after.ended-after.start,
                 overrides=len(after.changes),stop=after.reason,
                 during_mission=compare_sensors(before.sight,after.sight,after.start,after.ended),
                 through_end=compare_sensors(before.sight,after.sight,after.start,100))
        with checkpoints.open("a") as sink:
            sink.write(json.dumps(row)+"\n")
            sink.flush()
            os.fsync(sink.fileno())
        stored.append(row)
        print(seed,side,flush=True)
    if len(stored)!=len(expected): raise ValueError("Unvollständige Nachmessung")
    print("Geprüfte Sitzpaare",len(stored))


if __name__=="__main__":
    main()
