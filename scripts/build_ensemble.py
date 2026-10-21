"""Mehrere Checkpoints derselben Variante zu einem Ensemble-Checkpoint verbinden.

    python -m scripts.build_ensemble --out experiments/ensembles/full_s012.pth \
        experiments/runs/20261010_full_s0/weights/agent.pth \
        experiments/runs/20261010_full_s1/weights/agent.pth \
        experiments/runs/20261010_full_s2/weights/agent.pth

Der erste Checkpoint bleibt das Hauptnetz (inkl. Target/Optimizer/Config), die
uebrigen landen unter "ensemble". Agent_x mittelt beim Spielen die Q-Werte aller
Netze. Eine einzelne .pth -> Runner und Abgabe brauchen keine Aenderung.

--mixed (21.10.2026): weitere Netze duerfen weniger Eingaben haben als das Hauptnetz
(V3-Netze mit 79 neben Netzen mit Gefahr-Merkmalen, cfg.threat_feats). Sie bekommen die
ersten Merkmale; ihre Eingabegroessen stehen unter "ensemble_dims".
"""
from __future__ import annotations

import argparse
from pathlib import Path

import torch

# Nur was Netzform und Bedeutung der Eingaben bestimmt; Lernrate & Co. duerfen abweichen.
PLAY_KEYS = ("hidden", "dueling", "use_sap", "use_belief", "canonical", "mask_actions")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--mixed", action="store_true",
                    help="kleinere Eingabegroessen der weiteren Netze erlauben")
    ap.add_argument("ckpts", nargs="+")
    args = ap.parse_args()

    base = torch.load(args.ckpts[0], map_location="cpu", weights_only=False)
    dim0 = base["feature_dim"]
    extra = []
    dims = list(base.get("ensemble_dims") or [dim0] * len(base.get("ensemble", [])))
    for p in args.ckpts[1:]:
        c = torch.load(p, map_location="cpu", weights_only=False)
        if c.get("n_actions") != base.get("n_actions"):
            raise SystemExit(f"{p}: n_actions passt nicht zu {args.ckpts[0]}")
        dim = c.get("feature_dim")
        if dim != dim0 and not (args.mixed and dim < dim0):
            raise SystemExit(f"{p}: feature_dim {dim} passt nicht zu {args.ckpts[0]} ({dim0})")
        for k in PLAY_KEYS:
            if c["cfg"].get(k) != base["cfg"].get(k):
                raise SystemExit(f"{p}: cfg.{k} passt nicht zu {args.ckpts[0]}")
        extra.append(c["q"])
        extra.extend(c.get("ensemble", []))
        dims += [dim] + list(c.get("ensemble_dims") or [dim] * len(c.get("ensemble", [])))
    base["ensemble"] = list(base.get("ensemble", [])) + extra
    if any(d != dim0 for d in dims):
        base["ensemble_dims"] = dims
    base["ensemble_sources"] = [str(p) for p in args.ckpts]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    torch.save(base, args.out)
    print(f"{args.out}: {1 + len(base['ensemble'])} Netze")


if __name__ == "__main__":
    main()
