"""Mehrere CNN-Policy-Checkpoints (PPO/BC) zu einem Ensemble verbinden.

    python -m scripts.build_cnn_ensemble --out experiments/ensembles/cnn2_p345.pth \
        experiments/ppo/cnn2/ppo_0030.pth experiments/ppo/cnn2/ppo_0040.pth \
        experiments/ppo/cnn2/ppo_0050.pth

Der erste Checkpoint bleibt das Hauptnetz (inkl. Config), die uebrigen landen
unter "ensemble". PPOAgent mittelt im Eval-Modus die log-Wahrscheinlichkeiten
aller Netze. Eine einzelne .pth -> Runner und Abgabe brauchen keine Aenderung.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import torch

# Bedeutung der Eingaben muss gleich sein; die Netzgroesse darf abweichen.
PLAY_KEYS = ("use_sap", "use_belief", "canonical", "mask_actions")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("ckpts", nargs="+")
    args = ap.parse_args()

    base = torch.load(args.ckpts[0], map_location="cpu", weights_only=False)
    if base.get("kind") != "ppo":
        raise SystemExit(f"{args.ckpts[0]}: kein CNN-Policy-Checkpoint")
    extra = list(base.get("ensemble", []))
    for p in args.ckpts[1:]:
        c = torch.load(p, map_location="cpu", weights_only=False)
        if c.get("kind") != "ppo" or c.get("feature_dim") != base.get("feature_dim"):
            raise SystemExit(f"{p}: passt nicht zu {args.ckpts[0]}")
        for k in PLAY_KEYS:
            if c["cfg"].get(k) != base["cfg"].get(k):
                raise SystemExit(f"{p}: cfg.{k} passt nicht zu {args.ckpts[0]}")
        extra.append({"arch": c["arch"], "policy": c["policy"]})
        extra.extend(c.get("ensemble", []))
    base["ensemble"] = extra
    base["ensemble_sources"] = [str(p) for p in args.ckpts]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    torch.save(base, args.out)
    print(f"{args.out}: {1 + len(extra)} Netze")


if __name__ == "__main__":
    main()
