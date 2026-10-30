"""30.10.2026: verlorene und gewonnene Matches (scripts/par_losses-Ausgabe) je Match vergleichen, wir gegen Gegner.

    .venv/bin/python experiments/analysis/battle/v11_loss_matches.py V11_sol92_sq V11_league6
"""
import sys, os
import pandas as pd
O = "/Users/elhassanmahmoud/Documents/AKI_LuxAgent15/experiments/analysis/battle"
cols = ["points", "first_score_step", "occ_mean", "occ_mean_late", "point_tiles_total", "occ_own_half",
        "occ_enemy_half", "contested_mean", "units_mean", "units_on_points_mean", "energy_mean", "deaths", "know"]
def load(f):
    d = pd.read_csv(os.path.join(O, f))
    d["know"] = d["belief_known"] / d["point_tiles_total"].where(d["point_tiles_total"] > 0)
    return d
for tag in sys.argv[1:]:
    print("=====", tag)
    for kind in ("lost", "won"):
        f = f"L_{tag}_{kind}.csv"
        if not os.path.exists(os.path.join(O, f)): continue
        d = load(f)
        g = d.groupby(["seed", "side"])
        print(f"--- {kind}: {g.ngroups} Spiele")
        us, them = d[d.is_us == 1].set_index(["seed", "side", "match"]), d[d.is_us == 0].set_index(["seed", "side", "match"])
        j = us.join(them, rsuffix="_opp")
        # Matchergebnis aus unserer Sicht
        for m in (0, 1, 2):
            jm = j.xs(m, level="match")
            print(f"  Match {m+1}: gewonnen {jm.won_match.mean()*100:5.1f} %  Punkte {jm.points.mean():6.0f}:{jm.points_opp.mean():<6.0f}"
                  f" erster Punkt {jm.first_score_step.mean():5.1f}:{jm.first_score_step_opp.mean():<5.1f}"
                  f" Felder {jm.point_tiles_total.mean():4.1f} besetzt {jm.occ_mean.mean():4.2f}:{jm.occ_mean_opp.mean():<4.2f}"
                  f" eigene/fremde Haelfte {jm.occ_own_half.mean():4.2f}/{jm.occ_enemy_half.mean():4.2f} : {jm.occ_own_half_opp.mean():4.2f}/{jm.occ_enemy_half_opp.mean():4.2f}"
                  f" Tode {jm.deaths.mean():4.1f}:{jm.deaths_opp.mean():<4.1f} Einheiten {jm.units_mean.mean():4.1f}:{jm.units_mean_opp.mean():<4.1f}"
                  f" Energie {jm.energy_mean.mean():5.0f}:{jm.energy_mean_opp.mean():<5.0f} Wissen {jm.know.mean()*100:4.0f} %")
