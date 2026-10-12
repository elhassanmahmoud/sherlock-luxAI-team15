"""Kopie eines Checkpoints mit geaenderten Config-Schaltern (Netze unveraendert).

    python -m scripts.set_cfg experiments/ensembles/old3_sym3.pth \
        experiments/ensembles/old3_sym3_grid.pth explore_grid=true scripted_explore=true

Werte: true/false, Ganzzahlen, Kommazahlen. Nur bekannte AgentConfig-Felder.
"""
from __future__ import annotations

import argparse
from dataclasses import fields

import torch

from agents.sherlock.config import AgentConfig


def parse(v: str):
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    for t in (int, float):
        try:
            return t(v)
        except ValueError:
            pass
    return v


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("sets", nargs="+", help="key=value")
    args = ap.parse_args()

    known = {f.name for f in fields(AgentConfig)}
    ckpt = torch.load(args.src, map_location="cpu", weights_only=False)
    for kv in args.sets:
        k, v = kv.split("=", 1)
        if k not in known:
            raise SystemExit(f"unbekannter Schalter: {k}")
        ckpt["cfg"][k] = parse(v)
    torch.save(ckpt, args.dst)
    print(args.dst, {kv.split("=")[0]: ckpt["cfg"][kv.split("=")[0]] for kv in args.sets})


if __name__ == "__main__":
    main()
