"""Independent samples. Map parameters alone decide low-vision inclusion."""
import json
from pathlib import Path
import sys

import jax
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/"vergleich"))
from panel import sensor

if __name__ == "__main__":
    sets = {}
    for block, start, end, n in (("train",161700000,161720000,1600),("test",161720000,161730000,800),("panel",161730000,161731000,60)):
        raw = np.arange(start, end, dtype=np.int32)
        idx = np.asarray(jax.jit(jax.vmap(sensor))(raw))
        chosen = raw[idx == 1][:n].tolist()
        if len(chosen) != n:
            raise ValueError("Insufficient maps in the reserved range")
        sets[block] = chosen
        if block == "train":
            sets["normal_technical"] = [int(raw[idx != 1][0])]
    loc = HERE/"karten.json"
    if loc.exists() and json.loads(loc.read_text()) != sets:
        raise ValueError("Map selections changed")
    loc.write_text(json.dumps(sets, separators=(",",":"))+"\n")
