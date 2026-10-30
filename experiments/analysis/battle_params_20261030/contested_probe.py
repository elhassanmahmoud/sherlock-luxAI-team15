"""Umkaempfte Karten mit starkem Sap: V10 gegen solution92, Spiele mit Ground Truth je Match (analyze_losses).

    .venv/bin/python experiments/analysis/battle_params_20261030/contested_probe.py MAP_PARAMS.csv OUT.csv N_JE_GRUPPE
Waehlt aus G1_V10_conf.csv (solution92) Spiele auf umkaempften Karten (min_axis <= 5) mit Streufaktor 1,0
oder Reichweite >= 5: N verlorene und N gewonnene, spielt sie mit denselben Seeds/Seiten nach.
"""
import csv
import sys

import pandas as pd

sys.path.insert(0, ".")  # aus der Projektwurzel starten
from scripts.analyze_losses import FIELDS, play_and_measure  # noqa: E402
from scripts.experiment import limit_threads  # noqa: E402

V10 = "experiments/releases/20261022_v10_baseline/agent_p0.pth"


def main():
    mp_path, out, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
    mp = pd.read_csv(mp_path)
    g = pd.read_csv("experiments/compare/battle/G1_V10_conf.csv")
    g = g[g.opponent == "solution92"].merge(mp, on="seed")
    sel = g[(g.min_axis <= 5) & ((g.unit_sap_dropoff_factor == 1.0) | (g.unit_sap_range >= 5))]
    pick = pd.concat([sel[sel.result == 0].head(n), sel[sel.result == 1].head(n)])
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent
    from scripts.par_eval import build_cfg
    env = LuxAIS3GymEnv(numpy_output=True)
    agent = Agent_x("player_0", agent_path=V10, cfg=build_cfg(V10, []), train=False)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS + ["result"])
        w.writeheader()
        for seed, side, res in pick[["seed", "side", "result"]].itertuples(index=False):
            opp = make_opponent("solution92", "player_1" if side == "player_0" else "player_0")
            for r in play_and_measure(env, agent, opp, int(seed), side):
                r["result"] = res
                w.writerow(r)
            fh.flush()
    env.close()


if __name__ == "__main__":
    main()
