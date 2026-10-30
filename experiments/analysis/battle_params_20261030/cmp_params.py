"""Gepaarter Vergleich Kandidat gegen Basis, gesamt und nach Streufaktor / Reichweite / umkaempft.
    python cmp_params.py MAP_PARAMS.csv KANDIDAT.csv BASIS.csv [GEGNER,...]"""
import sys
import numpy as np
import pandas as pd
mp = pd.read_csv(sys.argv[1]).set_index("seed")
c, r = pd.read_csv(sys.argv[2]), pd.read_csv(sys.argv[3])
opps = sys.argv[4].split(",") if len(sys.argv) > 4 else sorted(set(c.opponent))
k = ["seed", "side", "opponent"]
j = c[c.opponent.isin(opps)].set_index(k).result.rename("c").to_frame().join(
    r[r.opponent.isin(opps)].set_index(k).result.rename("r"), how="inner").reset_index().join(mp, on="seed")
j["d"] = j.c - j.r
rng = np.random.default_rng(0)
def boot(sub):
    m = sub.groupby("seed").d.mean().to_numpy()
    if len(m) < 5:
        return f"{m.mean() * 100:+.1f}"
    b = rng.choice(m, (2000, len(m))).mean(axis=1)
    return f"{m.mean() * 100:+.1f} [{np.percentile(b, 2.5) * 100:+.1f}; {np.percentile(b, 97.5) * 100:+.1f}] (n={len(sub)})"
print(f"Kandidat {j.c.mean() * 100:.1f} %, Basis {j.r.mean() * 100:.1f} %, gesamt {boot(j)}")
for o in opps:
    print(f"  {o[:30]:30s} {boot(j[j.opponent == o])}")
for v in (0.25, 0.5, 1.0):
    print(f"  Streufaktor {v}: {boot(j[j.unit_sap_dropoff_factor == v])}")
print(f"  Reichweite 3-4: {boot(j[j.unit_sap_range <= 4])}; 5-7: {boot(j[j.unit_sap_range >= 5])}")
print(f"  umkaempft (min_axis<=5): {boot(j[j.min_axis <= 5])}; sonst: {boot(j[j.min_axis > 5])}")
