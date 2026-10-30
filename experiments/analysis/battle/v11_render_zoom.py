"""Spielfeld-Schnappschuesse eines Spiels Sherlock gegen Solution_92 (oder einen anderen Gegner) als PNG.

    python scripts/render_snapshots.py SEED SIDE MATCH STEP,STEP OUT.png [WEIGHTS] [GEGNER]
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path("/Users/elhassanmahmoud/Documents/AKI_LuxAgent15")
sys.path.insert(0, str(ROOT))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def main():
    seed, side, match, steps, out = int(sys.argv[1]), sys.argv[2], int(sys.argv[3]), \
        [int(s) for s in sys.argv[4].split(",")], sys.argv[5]
    import os
    crop = [int(v) for v in os.environ.get("CROP", "0,23,0,23").split(",")]  # x0,x1,y0,y1
    weights = sys.argv[6] if len(sys.argv) > 6 else str(ROOT / "agents/sherlock/weights/agent_p0.pth")
    opponent = sys.argv[7] if len(sys.argv) > 7 else "solution92"  # 29.10.2026: auch sol92_sq usw.
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent
    env = LuxAIS3GymEnv(numpy_output=True)
    agent = Agent_x("player_0", agent_path=weights, train=False, seed=0)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    opp_side = "player_1" if side == "player_0" else "player_0"
    opp = make_opponent(opponent, opp_side)
    agent.new_game(side)
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    obs, info = env.reset(seed=seed)
    agent.set_env_cfg(info["params"])
    opp.set_env_cfg(info["params"])
    fp = info["full_params"]
    us = 0 if side == "player_0" else 1
    frames = []
    step, done = 0, False
    while not done:
        a_us = agent.act(step=step, obs=obs[side])
        a_op = opp.act(step=step, obs=obs[opp_side])
        st = env.state
        ms, mi = int(st.match_steps), int(st.steps) // 101
        if mi == match and ms in steps:
            ctx = agent._cache[1] if agent._cache and agent._cache[0] == int(st.steps) else None
            frames.append(dict(
                ms=ms, pos=np.asarray(st.units.position), ene=np.asarray(st.units.energy)[..., 0],
                mask=np.asarray(st.units_mask), tile=np.asarray(st.map_features.tile_type),
                rw=np.asarray(st.relic_nodes_map_weights), rmask=np.asarray(st.relic_nodes_mask),
                relics=np.asarray(st.relic_nodes), points=np.asarray(st.team_points),
                acts={us: np.asarray(a_us), 1 - us: np.asarray(a_op)},
                known=(agent.belief.point_tiles.copy(), agent.belief.mirrored),
                assigned=dict(ctx["assigned"]) if ctx else {},
            ))
        obs, r, term, trunc, info = env.step({side: a_us, opp_side: a_op})
        done = bool(term[side]) or bool(trunc[side])
        step += 1
    n = len(frames)
    cols = min(4, n)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(5.2 * cols, 5.2 * rows))
    axes = np.atleast_1d(axes).ravel()
    for ax, f in zip(axes, frames):
        W, H = f["tile"].shape
        img = np.ones((H, W, 3))
        img[f["tile"].T == 1] = (0.85, 0.75, 0.95)  # Nebel
        img[f["tile"].T == 2] = (0.35, 0.35, 0.35)  # Asteroid
        ax.imshow(img, origin="upper", extent=(-0.5, W - 0.5, H - 0.5, -0.5))
        n_rel = f["rmask"].sum() // 2
        pt = (f["rw"] > 0) & (f["rw"] <= n_rel)
        known, mir = f["known"]
        if mir:
            known = np.ascontiguousarray(known[::-1, ::-1].T)
        for x, y in np.argwhere(pt):
            ax.add_patch(plt.Rectangle((x - .5, y - .5), 1, 1, color="gold", alpha=.55 if known[x, y] else .25,
                                       ec="orange" if known[x, y] else "none", lw=1.5))
        for i in np.nonzero(f["rmask"])[0]:
            ax.plot(*f["relics"][i], marker="*", color="k", ms=10)
        for t, col in ((us, "tab:blue"), (1 - us, "tab:red")):
            occ = {}
            for u in np.nonzero(f["mask"][t])[0]:
                occ.setdefault(tuple(f["pos"][t, u]), []).append(u)
            for (x, y), uu in occ.items():
                e = int(sum(f["ene"][t, u] for u in uu))
                off = -0.18 if t == us else 0.18
                ax.plot(x + off, y + off, "o", color=col, ms=7 + 2 * (len(uu) - 1), alpha=.85)
                ax.text(x + off, y + off - .45, f"{e}" + (f"×{len(uu)}" if len(uu) > 1 else "")
                        + " #" + ",".join(str(u) for u in uu), fontsize=6, color=col, ha="center")
            for u in np.nonzero(f["mask"][t])[0]:
                a = f["acts"][t][u]
                if int(a[0]) == 5:
                    x, y = f["pos"][t, u]
                    ax.annotate("", xy=(x + a[1], y + a[2]), xytext=(x, y),
                                arrowprops=dict(arrowstyle="->", color=col, lw=1))
        ax.set_title(f"Match {match + 1}, Step {f['ms']}  Punkte wir {f['points'][us]} : {f['points'][1 - us]} Gegner",
                     fontsize=10)
        ax.set_xticks(range(0, W, 2))
        ax.set_yticks(range(0, H, 2))
        ax.set_xlim(crop[0] - .5, crop[1] + .5)
        ax.set_ylim(crop[3] + .5, crop[2] - .5)
        ax.grid(alpha=.15)
    fig.suptitle(f"Seed {seed}, wir = {side} (blau), Solution_92 rot; gold = Punktfeld (kräftig = uns bekannt); "
                 f"sap {fp['unit_sap_cost']} r{fp['unit_sap_range']} drop {fp['unit_sap_dropoff_factor']} "
                 f"void {fp['unit_energy_void_factor']} move {fp['unit_move_cost']}", fontsize=10)
    fig.tight_layout()
    fig.savefig(out, dpi=90)
    print(out)


if __name__ == "__main__":
    main()
