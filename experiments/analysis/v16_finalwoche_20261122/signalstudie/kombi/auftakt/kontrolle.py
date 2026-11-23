"""Festgelegte Reichweiten-Kontrollen auf demselben Solution-Panel."""
import gzip
import json
import sys

from match1 import HERE, STUDY, CASES, record, limit_threads

sys.path.insert(0, str(STUDY/"kartenparameter"))
from auswerten import generate

import jax
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv


def main():
    limit_threads()
    raw = [r for lane in (0, 1) for r in map(json.loads, (HERE.parent/"frisch"/f"worker_{lane}.jsonl").read_text().splitlines())]
    references = {(r["seed"],r["side"]):r for r in raw if r["arm"]=="aus" and r["opponent"]=="solution92"}
    seeds = sorted({s for s,p in references})
    if len(references)!=160 or len(seeds)!=80:
        raise ValueError("Unerwartete Kartenzahl")
    parameters = np.asarray(jax.jit(jax.vmap(generate))(np.asarray(seeds,dtype=np.int32)))
    sensor = {s: int(params[0]) for s,params in zip(seeds,parameters,strict=True)}
    used = {s for s,p in CASES}
    controls = [(160386070, "player_0")]
    for s,side in CASES:
        available = [seed for seed in seeds if seed not in used and sensor[seed]==sensor[s] and references[seed,side]["game_win"]]
        if len(available)<2:
            raise ValueError("Zu wenige verschiedene passende Karten")
        controls.extend((seed,side) for seed in available[:2])
        used.update(available[:2])
    if not all(references[key]["game_win"] for key in controls):
        raise ValueError("Unter den ausgewählten Referenzen befindet sich eine Niederlage")
    env = LuxAIS3GymEnv(numpy_output=True)
    for seed in used:
        _, info = env.reset(seed=seed)
        if int(info["params"]["unit_sensor_range"])!=sensor[seed]:
            raise ValueError("Reichweite am echten Kurs-Reset abweichend")
    env.close()
    selected = [{"seed":seed,"side":side,"sensor":sensor[seed]} for seed,side in controls]
    selection = {"lost_sensor":{str(seed):sensor[seed] for seed,_ in CASES},"controls":selected}
    frozen = HERE/"kontrollauswahl.json"
    if frozen.exists() and json.loads(frozen.read_text()) != selection:
        raise ValueError("Original-Vorauswahl entspricht nicht mehr der Reproduktion")
    frozen.write_text(json.dumps(selection,indent=2)+"\n")
    print("Auswahl gespeichert", selected, flush=True)
    rows = record(controls, references)
    packed = json.dumps({"controls":rows},separators=(",",":")).encode()
    (HERE/"kontrollzuege.json.gz").write_bytes(gzip.compress(packed,mtime=0))


if __name__=="__main__":
    main()
