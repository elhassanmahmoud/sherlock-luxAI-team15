"""Mehrere Checkpoints derselben Variante zu einem Ensemble-Checkpoint verbinden.

    python -m scripts.build_ensemble --out experiments/ensembles/full_s012.pth \
        experiments/runs/20261010_full_s0/weights/agent.pth \
        experiments/runs/20261010_full_s1/weights/agent.pth \
        experiments/runs/20261010_full_s2/weights/agent.pth

Der erste Checkpoint bleibt das Hauptnetz (inkl. Target/Optimizer/Config), die
uebrigen landen unter "ensemble". Agent_x mittelt beim Spielen die Q-Werte aller
Netze. Eine einzelne .pth -> Runner und Abgabe brauchen keine Aenderung.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import torch


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("ckpts", nargs="+")
    args = ap.parse_args()

    base = torch.load(args.ckpts[0], map_location="cpu", weights_only=False)
    extra = []
    for p in args.ckpts[1:]:
        c = torch.load(p, map_location="cpu", weights_only=False)
        for k in ("feature_dim", "n_actions", "cfg"):
            if c.get(k) != base.get(k):
                raise SystemExit(f"{p}: {k} passt nicht zu {args.ckpts[0]}")
        extra.append(c["q"])
        extra.extend(c.get("ensemble", []))
    base["ensemble"] = list(base.get("ensemble", [])) + extra
    base["ensemble_sources"] = [str(p) for p in args.ckpts]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    torch.save(base, args.out)
    print(f"{args.out}: {1 + len(base['ensemble'])} Netze")


if __name__ == "__main__":
    main()
