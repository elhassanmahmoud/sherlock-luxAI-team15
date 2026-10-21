import json, sys
import numpy as np
g = json.load(open(sys.argv[1]))
wins = sum(x["wins"][0] > x["wins"][1] for x in g)
print(f"Spiele {len(g)}, Siege {wins}")
keys = ["unit_steps","productive","pt_unit_steps","stacked_unit_steps","pt_stacked_unit_steps","pt_unit_steps_lowE",
        "sap_fired","sap_hit","sap_dmg_direct_dealt","sap_dmg_adj_dealt","void_dealt","sap_paid","move_paid","field_gain",
        "deaths_collision","deaths_energy","deaths_on_pt","kills_by_sap_dealt","kills_by_void_dealt"]
for mi in range(3):
    ms = [x["matches"][mi] for x in g if len(x["matches"]) > mi]
    won = [m["us"]["productive"] > m["opp"]["productive"] for m in ms]
    print(f"\nMatch {mi+1}: Punkte-Siege (approx) {sum(won)}/{len(ms)}")
    print(f"{'Kennzahl':26s} {'wir':>8s} {'Gegner':>8s}   | in verlorenen Matches: {'wir':>8s} {'Gegner':>8s}")
    lost = [m for m, w in zip(ms, won) if not w]
    for k in keys:
        a = np.mean([m["us"][k] for m in ms]); b = np.mean([m["opp"][k] for m in ms])
        la = np.mean([m["us"][k] for m in lost]) if lost else float("nan"); lb = np.mean([m["opp"][k] for m in lost]) if lost else float("nan")
        print(f"{k:26s} {a:8.1f} {b:8.1f}   |                        {la:8.1f} {lb:8.1f}")
    a = np.mean([m["us"]["pt_energy_sum"]/max(1,m["us"]["pt_unit_steps"]) for m in ms]); b = np.mean([m["opp"]["pt_energy_sum"]/max(1,m["opp"]["pt_unit_steps"]) for m in ms])
    print(f"{'Ø Energie auf Punktfeld':26s} {a:8.1f} {b:8.1f}")
