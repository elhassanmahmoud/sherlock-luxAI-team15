"""30.10.2026: Energiebilanz (scripts/mechanism_probe.py) je Match zusammenfassen, verloren gegen gewonnen.

    .venv/bin/python experiments/analysis/battle/v11_loss_mechanisms.py V11_sol92_sq_lost V11_sol92_sq_won
"""
import json, sys
import pandas as pd
O = "/Users/elhassanmahmoud/Documents/AKI_LuxAgent15/experiments/analysis/battle/"
keys = ["unit_steps", "pt_unit_steps", "productive", "stacked_unit_steps", "pt_stacked_unit_steps", "sap_fired", "sap_hit",
        "sap_dmg_direct_dealt", "sap_dmg_adj_dealt", "void_dealt", "kills_by_sap_dealt", "kills_by_void_dealt",
        "deaths_collision", "deaths_energy", "deaths_on_pt", "move_paid", "field_gain", "pt_unit_steps_lowE",
        "cls_explore", "cls_to_cand_own", "cls_to_cand_enemy", "cls_to_pt_own", "cls_to_pt_enemy", "cls_on_pt_first",
        "cls_on_pt_stacked", "cls_dying", "true_pt_own", "true_pt_unknown_own", "unknown_own_relic_known",
        "unknown_own_relic_unseen", "free_pt_own", "untargeted_free_pt_own", "free_pt_enemy", "opp_on_pt_our_half",
        "opp_on_pt_their_half", "first_point_step", "first_3pt_step"]
frames = {}
for tag in sys.argv[1:]:
    rows = []
    for g in json.load(open(O + f"M_{tag}.json")):
        for m, mt in enumerate(g["matches"]):
            for who in ("us", "opp"):
                r = {k: mt[who].get(k) for k in keys}
                r.update(seed=g["seed"], match=m + 1, who=who)
                rows.append(r)
    frames[tag] = pd.DataFrame(rows)
pd.set_option("display.width", 250)
for m in (1, 2, 3):
    print(f"===== Match {m}")
    t = {}
    for tag, d in frames.items():
        for who in ("us", "opp"):
            t[f"{tag[-4:]}/{who}"] = d[(d.match == m) & (d.who == who)][keys].mean()
    print(pd.DataFrame(t).round(1).to_string())
