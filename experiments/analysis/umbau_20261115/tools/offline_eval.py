"""Nachahmung mehrerer Schüler auf frischen, nie trainierten Spielen messen (17.11.2026).

    python experiments/analysis/umbau_20261115/tools/offline_eval.py \
        --data experiments/imitation/k3_holdout_teacher \
        --students V5C=experiments/imitation/students/v5c_from_v5.pth V6=experiments/imitation/students/v6_pm_from_v5.pth \
        --out ergebnis.json

Gewertet werden nur ausführbare Lehrerbefehle. Die Validierung im Training zählt zusätzlich die nicht ausführbaren
Lehrerbefehle (etwa 1,7 %) als Fehler. Auf den 331 Validierungsspielen von v6 und v5c ergibt die Umrechnung genau die
Trainingswerte (82,2 % und 80,2 %; Kontrolle vom 17.11. in umbau_20261115/v7/nachahmung/kontrolle_validierung_v6.md).
Je Schüler: Anteil gleicher Aktion, Trefferquote je
Lehreraktion und – für Einheiten mit bekannter letzter Bewegung – getrennt danach, ob der Lehrer diese Bewegung
wiederholt („gleich“) oder etwas anderes tut („anders“). Dazu: wie oft Schüler und Lehrer die letzte Bewegung
wiederholen. Ein Schüler, der nur „weiter wie eben“ gelernt hat, wiederholt öfter als der Lehrer und liegt bei
„anders“ schlechter. Ensembles (imitate ensemble) werden wie im Spiel über die Summe der Log-Wahrscheinlichkeiten
bewertet. Schussziele werden hier nicht bewertet.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from agents.sherlock.imitation_net import ImitationNet  # noqa: E402
from scripts.imitate import PLANE_SCALE, concat_games, prepare_labels, prev_move_columns  # noqa: E402

ACTIONS = ("stehen", "hoch", "rechts", "runter", "links", "Schuss")


def load_student(path: str):
    ck = torch.load(path, map_location="cpu", weights_only=False)
    nets = [ImitationNet(**ck["arch"])]
    nets[0].load_state_dict(ck["policy"])
    for m in ck.get("imitation_ensemble", []):
        extra = ImitationNet(**m["arch"])
        extra.load_state_dict(m["policy"])
        nets.append(extra)
    prev = bool(ck.get("prev_move_input", False))
    want = 79 + (5 if prev else 0)
    if any(n.arch["feat_dim"] != want for n in nets):
        raise ValueError(f"{path}: Eingabebreite passt nicht zu prev_move_input={prev}")
    return [n.eval() for n in nets], prev


def new_stats():
    return {k: 0 for k in ("n", "ok", "n_prev", "n_same", "ok_same", "n_diff", "ok_diff", "pred_rep", "teach_rep")} | {
        "n_cls": [0] * 6, "ok_cls": [0] * 6}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", nargs="+", required=True, help="Ordner mit g*.npz (frische Spiele)")
    ap.add_argument("--students", nargs="+", required=True, help="NAME=PFAD")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    torch.set_num_threads(4)
    students = {}
    for spec in a.students:
        name, path = spec.split("=", 1)
        students[name] = load_student(path)
    files = sorted(f for d in a.data for f in Path(d).glob("g*.npz"))
    if not files:
        raise SystemExit("keine Spiele gefunden")
    stats = {name: new_stats() for name in students}
    for f in files:
        with np.load(f, allow_pickle=False) as z:
            prev_cols = prev_move_columns(z).astype(np.float32)
        planes, rows = concat_games([f])
        R = {k: torch.from_numpy(v) for k, v in rows.items()}
        width, height = planes.shape[-2:]
        prepare_labels(R, width, height)
        P = torch.from_numpy(planes).float() / PLANE_SCALE
        inv, pos = R["step"].long(), R["pos"].long()
        feats79 = R["feats"].float()
        feats84 = torch.cat([feats79, torch.from_numpy(prev_cols)], dim=1)
        keep = R["admitted"]
        act = R["act"][keep]
        has_prev = torch.from_numpy(prev_cols.sum(1) == 1)[keep]
        prev = torch.from_numpy(prev_cols.argmax(1))[keep]
        same = has_prev & (act == prev)
        diff = has_prev & (act != prev)
        mask = R["mask"]
        for name, (nets, use_prev) in students.items():
            feats = feats84 if use_prev else feats79
            with torch.no_grad():
                logp = None
                for net in nets:
                    lg, _, _ = net.forward_all(P, inv, pos, feats)
                    lp = torch.log_softmax(lg.masked_fill(~mask, -torch.inf), dim=1)
                    logp = lp if logp is None else logp + lp
            pred = logp.argmax(1)[keep]
            s = stats[name]
            ok = pred == act
            s["n"] += int(len(act))
            s["ok"] += int(ok.sum())
            for c in range(6):
                sel = act == c
                s["n_cls"][c] += int(sel.sum())
                s["ok_cls"][c] += int((ok & sel).sum())
            s["n_prev"] += int(has_prev.sum())
            s["n_same"] += int(same.sum())
            s["ok_same"] += int((ok & same).sum())
            s["n_diff"] += int(diff.sum())
            s["ok_diff"] += int((ok & diff).sum())
            s["pred_rep"] += int((has_prev & (pred == prev)).sum())
            s["teach_rep"] += int(same.sum())
    pct = lambda x, n: round(100.0 * x / max(1, n), 2)  # noqa: E731
    summary = {}
    print(f"{len(files)} Spieldateien aus {', '.join(a.data)}")
    print("| Schüler | gleiche Aktion | " + " | ".join(ACTIONS) + " | Lehrer wiederholt: Schüler richtig | "
          "Lehrer wechselt: Schüler richtig | Schüler wiederholt | Lehrer wiederholt |")
    print("|---|" + "---:|" * 11)
    for name, s in stats.items():
        row = {"gleiche_aktion": pct(s["ok"], s["n"]),
               "je_aktion": {ACTIONS[c]: pct(s["ok_cls"][c], s["n_cls"][c]) for c in range(6)},
               "lehrer_wiederholt_richtig": pct(s["ok_same"], s["n_same"]),
               "lehrer_wechselt_richtig": pct(s["ok_diff"], s["n_diff"]),
               "schueler_wiederholt": pct(s["pred_rep"], s["n_prev"]),
               "lehrer_wiederholt": pct(s["teach_rep"], s["n_prev"]), "zaehler": s}
        summary[name] = row
        print(f"| {name} | {row['gleiche_aktion']:.2f} % | " +
              " | ".join(f"{row['je_aktion'][x]:.1f}" for x in ACTIONS) +
              f" | {row['lehrer_wiederholt_richtig']:.2f} % | {row['lehrer_wechselt_richtig']:.2f} % | "
              f"{row['schueler_wiederholt']:.2f} % | {row['lehrer_wiederholt']:.2f} % |")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"dateien": [str(f.relative_to(ROOT)) if f.is_relative_to(ROOT) else str(f) for f in files],
                               "schueler": {n: p for n, p in (s.split("=", 1) for s in a.students)},
                               "ergebnis": summary}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
