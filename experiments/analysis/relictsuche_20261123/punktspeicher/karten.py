import json
from pathlib import Path
import sys
import jax
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/"vergleich"))
from panel import sensor

if __name__ == "__main__":
    seeds=np.arange(162300000,162301000,dtype=np.int32)
    values=np.asarray(jax.jit(jax.vmap(sensor))(seeds))
    fresh=seeds[values==1][:40].tolist()
    assert len(fresh)==40
    path=HERE/"karten.json"
    rows={"archiv":[161620068,161620111],"frisch":fresh}
    if path.exists():
        assert rows==json.loads(path.read_text())
    else:
        path.write_text(json.dumps(rows,indent=2)+"\n")
