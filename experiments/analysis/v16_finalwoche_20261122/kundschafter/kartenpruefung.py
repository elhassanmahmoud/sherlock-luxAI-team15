"""Wie oft existierte das gesuchte Paar? Externe Kartenprüfung nach allen Leistungsdaten."""
import json
from pathlib import Path

import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv

HERE = Path(__file__).resolve().parent


def main():
    data = json.loads((HERE / "frisch.json").read_text())["rows"]
    env = LuxAIS3GymEnv(numpy_output=True)
    output = []
    for seed in sorted({r["seed"] for r in data}):
        env.reset(seed=seed)
        schedule = np.asarray(env.state.relic_spawn_schedule).reshape(-1)
        by_end = sum(0 <= int(t) <= 201 for t in schedule)
        if by_end % 2:
            raise ValueError("Unpaariger Reliktspawn")
        maps = [r for r in data if r["seed"] == seed and r["arm"] == "scout"]
        verified = [r for r in data if r["seed"] == seed and r["pair_turn"] is not None]
        if by_end < 4 and verified:
            raise ValueError("Agent sah ein angeblich fehlendes zweites Paar")
        output.append({"seed":seed,"raw_spawn_times":list(map(int,schedule)),"two_by_match2":bool(by_end>=4),
                       "changed_seats":{opp:sum(bool(r["changes"]) for r in maps if r["opponent"]==opp)
                                        for opp in ("solution92","kaggle3","v16")}})
    (HERE / "kartenpruefung.json").write_text(json.dumps(output,indent=2)+"\n")


if __name__ == "__main__":
    main()
