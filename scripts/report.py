"""Auswertung aller Run-Ordner -> Markdown-Tabellen + PNG-Diagramme.

    python -m scripts.report                      # alle fertigen Laeufe
    python -m scripts.report --prefix 20261010    # nur ein Batch
    python -m scripts.report --out docs/report

Statistik (siehe docs/EXPERIMENT_PROTOKOLL.md, Abschnitt 6):
  * Winrate-KI: zweistufiger Bootstrap (Trainingsstarts, dann Test-Seeds; beide
    Seiten eines Seeds bleiben zusammen), 10 000 Wiederholungen, Perzentile.
  * Differenz zu `full`: gepaart ueber dieselbe Seed-Stichprobe (gleicher Seed,
    gleiche Seite), Starts je Variante unabhaengig gezogen.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.common import ROOT
from scripts.experiment import RUNS
from scripts.variants import VARIANTS

B = 10_000
OPP_LABEL = {"default": "default", "solution92": "Solution_92"}
ORDER = list(VARIANTS)

# Referenzpalette (dataviz, Light-Mode), feste Reihenfolge = feste Variante
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
COLOR = {v: PALETTE[i % len(PALETTE)] for i, v in enumerate(ORDER)}
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


# ------------------------------------------------------------------ laden
def load_runs(prefix: str, runs_dir: Path):
    runs = []
    for d in sorted(runs_dir.glob(f"{prefix}*")):
        man = d / "manifest.json"
        if not man.is_file():
            continue
        m = json.loads(man.read_text())
        if m.get("status") != "done" or not (d / "eval.csv").is_file():
            continue
        runs.append(dict(
            dir=d, manifest=m, variant=m["variant"], run_seed=m["run_seed"],
            eval=pd.read_csv(d / "eval.csv"),
            train=pd.read_csv(d / "train.csv") if (d / "train.csv").is_file() else None,
            val=pd.read_csv(d / "val.csv") if (d / "val.csv").is_file() else None,
        ))
    return runs


def matrix(runs, variant, opponent, col="result"):
    """[Start, Seed] -> Mittel ueber beide Seiten. Seeds sortiert, gemeinsam fuer alle."""
    mats, seeds = [], None
    for r in runs:
        if r["variant"] != variant:
            continue
        e = r["eval"][r["eval"]["opponent"] == opponent]
        piv = e.groupby("seed")[col].mean().sort_index()
        seeds = piv.index.to_numpy() if seeds is None else seeds
        mats.append(piv.reindex(seeds).to_numpy(dtype=float))
    return (np.array(mats), seeds) if mats else (None, None)


# -------------------------------------------------------------- bootstrap
def boot_mean(M, rng):
    n_r, n_s = M.shape
    ri = rng.integers(0, n_r, (B, n_r))
    si = rng.integers(0, n_s, (B, n_s))
    return M[ri[:, :, None], si[:, None, :]].mean(axis=(1, 2))


def boot_diff(MA, MB, rng):
    n_s = MA.shape[1]
    si = rng.integers(0, n_s, (B, n_s))
    ra = rng.integers(0, MA.shape[0], (B, MA.shape[0]))
    rb = rng.integers(0, MB.shape[0], (B, MB.shape[0]))
    a = MA[ra[:, :, None], si[:, None, :]].mean(axis=(1, 2))
    b = MB[rb[:, :, None], si[:, None, :]].mean(axis=(1, 2))
    return a - b


def ci(x):
    lo, hi = np.percentile(x, [2.5, 97.5])
    return float(lo), float(hi)


# -------------------------------------------------------------- tabellen
def summarize(runs, rng):
    rows, diffs = [], []
    variants = [v for v in ORDER if any(r["variant"] == v for r in runs)]
    for opp in OPP_LABEL:
        base, _ = matrix(runs, "full", opp)
        base_pd, _ = matrix(runs, "full", opp, "pdiff")
        for v in variants:
            M, seeds = matrix(runs, v, opp)
            if M is None:
                continue
            per_run = M.mean(axis=1)
            lo, hi = ci(boot_mean(M, rng))
            sub = pd.concat([r["eval"][r["eval"]["opponent"] == opp]
                             for r in runs if r["variant"] == v])
            mw = sub["our_wins"].sum() / max(1, (sub["our_wins"] + sub["opp_wins"]).sum())
            rows.append(dict(
                variant=v, opponent=opp, starts=len(per_run), games=len(sub),
                winrate=float(M.mean()), ci_lo=lo, ci_hi=hi,
                run_mean=float(per_run.mean()),
                run_sd=float(per_run.std(ddof=1)) if len(per_run) > 1 else float("nan"),
                match_winrate=float(mw),
                point_winrate=float(sub["point_win"].mean()),
                points=float(sub["our_points"].mean()), opp_points=float(sub["opp_points"].mean()),
            ))
            if v != "full" and base is not None:
                d = boot_diff(M, base, rng)
                Pd, _ = matrix(runs, v, opp, "pdiff")
                dp = boot_diff(Pd, base_pd, rng)
                diffs.append(dict(
                    variant=v, opponent=opp,
                    delta=float(M.mean() - base.mean()), d_lo=ci(d)[0], d_hi=ci(d)[1],
                    delta_pd=float(Pd.mean() - base_pd.mean()), pd_lo=ci(dp)[0], pd_hi=ci(dp)[1],
                ))
    return pd.DataFrame(rows), pd.DataFrame(diffs)


def behaviour(runs):
    rows = []
    for v in ORDER:
        sub = [r["eval"] for r in runs if r["variant"] == v]
        if not sub:
            continue
        e = pd.concat(sub)
        sap = e["sap_attempts"].sum()
        rows.append(dict(
            variant=v, wait=e["wait_frac"].mean(), invalid=e["invalid_frac"].mean(),
            masked=e["greedy_masked_frac"].mean(), sap_per_game=e["sap_attempts"].mean(),
            sap_hit=(e["sap_hits"].sum() / sap) if sap else float("nan"),
            stack=e["stack_frac"].mean(), relics=e["relics_found"].mean(),
            point_tiles=e["known_point_tiles"].mean(),
        ))
    return pd.DataFrame(rows)


def pct(x, d=1):
    return "–" if pd.isna(x) else f"{100 * x:.{d}f} %"


def fmt_ci(lo, hi, signed=False):
    f = (lambda x: f"{100 * x:+.1f}") if signed else (lambda x: f"{100 * x:.1f}")
    return f"[{f(lo)}, {f(hi)}]"


def write_markdown(out, summ, diffs, beh, runs):
    L = ["<!-- automatisch erzeugt von scripts/report.py - nicht von Hand bearbeiten -->", ""]
    L += ["## Winrate auf den Test-Seeds (ε = 0)", "",
          "Winrate = Mittel von `result` (Sieg 1, Remis 0,5). KI: 95 %, zweistufiger Bootstrap "
          "(Starts × Seeds). ± = Standardabweichung über die Trainingsstarts.", ""]
    for opp, lab in OPP_LABEL.items():
        s = summ[summ["opponent"] == opp]
        if s.empty:
            continue
        L += [f"### Gegner: {lab}", "",
              "| Variante | Starts | Spiele | Winrate | 95-%-KI | Mittel ± SD (Starts) | Match-WR | Punkte-WR | Punkte wir : Gegner |",
              "|---|---:|---:|---:|---|---|---:|---:|---|"]
        for _, r in s.iterrows():
            sd = "–" if pd.isna(r.run_sd) else f"{100 * r.run_mean:.1f} ± {100 * r.run_sd:.1f}"
            L.append(f"| `{r.variant}` | {r.starts} | {r.games} | {pct(r.winrate)} | "
                     f"{fmt_ci(r.ci_lo, r.ci_hi)} | {sd} | {pct(r.match_winrate)} | "
                     f"{pct(r.point_winrate)} | {r.points:.0f} : {r.opp_points:.0f} |")
        L.append("")
    if not diffs.empty:
        L += ["## Unterschied zu `full` (gepaarter Bootstrap, gleicher Seed + gleiche Seite)", "",
              "Δ in Prozentpunkten (Winrate) bzw. Punkten (Punktedifferenz wir − Gegner pro Spiel). "
              "KI schließt 0 ein ⇒ kein belegter Unterschied.", "",
              "| Variante | Gegner | Δ Winrate | 95-%-KI | Δ Punktedifferenz | 95-%-KI |",
              "|---|---|---:|---|---:|---|"]
        for _, r in diffs.iterrows():
            L.append(f"| `{r.variant}` | {OPP_LABEL[r.opponent]} | {100 * r.delta:+.1f} | "
                     f"{fmt_ci(r.d_lo, r.d_hi, True)} | {r.delta_pd:+.1f} | "
                     f"[{r.pd_lo:+.1f}, {r.pd_hi:+.1f}] |")
        L.append("")
    if not beh.empty:
        L += ["## Verhalten (Test-Spiele, beide Gegner)", "",
              "| Variante | Warten | ungültig | Maske griff | Saps/Spiel | Sap-Treffer | Stacking | Relics | Punkte-Tiles |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for _, r in beh.iterrows():
            pt = "–" if pd.isna(r.point_tiles) else f"{r.point_tiles:.1f}"
            L.append(f"| `{r.variant}` | {pct(r.wait)} | {pct(r.invalid)} | {pct(r.masked)} | "
                     f"{r.sap_per_game:.1f} | {pct(r.sap_hit)} | {pct(r.stack)} | "
                     f"{r.relics:.1f} | {pt} |")
        L.append("")
    L += ["## Läufe", "", "| Lauf | Trainingsspiele | Laufzeit | Commit | dirty |", "|---|---:|---:|---|---|"]
    for r in runs:
        m = r["manifest"]
        L.append(f"| `{r['dir'].name}` | {m.get('train_games', 0)} | "
                 f"{m.get('runtime_secs', 0) / 60:.0f} min | `{m.get('git', {}).get('commit', '')[:7]}` | "
                 f"{m.get('git', {}).get('dirty')} |")
    (out / "tabellen.md").write_text("\n".join(L) + "\n", encoding="utf-8")


# ------------------------------------------------------------- diagramme
def _style(plt):
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
        "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
        "axes.titlesize": 11, "axes.titleweight": "bold", "legend.frameon": False,
    })


def plot_winrates(summ, out, plt):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    for ax, (opp, lab) in zip(axes, OPP_LABEL.items()):
        s = summ[summ["opponent"] == opp].reset_index(drop=True)
        y = np.arange(len(s))[::-1]
        for yi, (_, r) in zip(y, s.iterrows()):
            c = COLOR[r.variant]
            ax.plot([100 * r.ci_lo, 100 * r.ci_hi], [yi, yi], color=c, lw=2, solid_capstyle="round")
            ax.plot(100 * r.winrate, yi, "o", ms=8, color=c, mec=SURFACE, mew=2)
            ax.text(100 * r.ci_hi + 1.5, yi, f"{100 * r.winrate:.0f} %", va="center", fontsize=9, color=INK2)
        ax.set_yticks(y, s["variant"])
        ax.set_xlim(-2, 105)
        ax.set_xlabel("Winrate auf Test-Seeds in % (95-%-KI)")
        ax.set_title(f"gegen {lab}", loc="left")
        ax.grid(axis="y", visible=False)
    fig.suptitle("Winrate je Variante (Testmenge, ε = 0)", x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out / "winrate_ci.png", dpi=160)
    plt.close(fig)


def plot_ablation(diffs, out, plt):
    if diffs.empty:
        return
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    for ax, (opp, lab) in zip(axes, OPP_LABEL.items()):
        d = diffs[diffs["opponent"] == opp].reset_index(drop=True)
        y = np.arange(len(d))[::-1]
        for yi, (_, r) in zip(y, d.iterrows()):
            c = COLOR[r.variant]
            ax.barh(yi, 100 * r.delta, height=0.55, color=c, alpha=0.85)
            ax.plot([100 * r.d_lo, 100 * r.d_hi], [yi, yi], color=INK, lw=1.2)
        ax.axvline(0, color=INK2, lw=1)
        ax.set_yticks(y, d["variant"])
        ax.set_xlabel("Δ Winrate zu full in Prozentpunkten (gepaart, 95-%-KI)")
        ax.set_title(f"gegen {lab}", loc="left")
        ax.grid(axis="y", visible=False)
    fig.suptitle("Ablation: was kostet das Abschalten eines Bausteins?", x=0.01, ha="left",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(out / "ablation.png", dpi=160)
    plt.close(fig)


def plot_learning(runs, out, plt):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, (opp, lab) in zip(axes, OPP_LABEL.items()):
        for v in ORDER:
            vals = [r["val"][r["val"]["opponent"] == opp].set_index("after_games")["winrate"]
                    for r in runs if r["variant"] == v and r["val"] is not None and len(r["val"])]
            if not vals:
                continue
            df = pd.concat(vals, axis=1)
            m = 100 * df.mean(axis=1)
            ax.plot(m.index, m.values, color=COLOR[v], lw=2, label=v)
            if df.shape[1] > 1:
                ax.fill_between(m.index, 100 * df.min(axis=1), 100 * df.max(axis=1),
                                color=COLOR[v], alpha=0.10, lw=0)
        ax.set_title(f"gegen {lab}", loc="left")
        ax.set_xlabel("Trainingsspiele")
        ax.set_ylabel("Winrate Validierung in %")
    axes[1].legend(loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=9)
    fig.suptitle("Lernkurven (Validierungs-Seeds, ε = 0; Linie = Mittel, Band = min–max der Starts)",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out / "lernkurven.png", dpi=160)
    plt.close(fig)


def plot_training(runs, out, plt):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0))
    for v in ORDER:
        tr = [r["train"] for r in runs if r["variant"] == v and r["train"] is not None]
        if not tr:
            continue
        wr = pd.concat([t.set_index("game")["result"].rolling(100, min_periods=20).mean()
                        for t in tr], axis=1).mean(axis=1)
        axes[0].plot(wr.index, 100 * wr.values, color=COLOR[v], lw=1.6, label=v)
        loss = pd.concat([t.set_index("game")["mean_loss"].rolling(50, min_periods=5).mean()
                          for t in tr], axis=1).mean(axis=1)
        if loss.notna().any():
            axes[1].plot(loss.index, loss.values, color=COLOR[v], lw=1.6, label=v)
    axes[0].set_title("Trainings-Winrate (gleitend, 100 Spiele, mit Exploration)", loc="left")
    axes[0].set_xlabel("Trainingsspiel"); axes[0].set_ylabel("%")
    axes[1].set_title("Mittlerer TD-Loss pro Spiel (gleitend, 50)", loc="left")
    axes[1].set_xlabel("Trainingsspiel"); axes[1].set_yscale("log")
    axes[1].legend(loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=9)
    fig.tight_layout()
    fig.savefig(out / "training.png", dpi=160)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="", help="nur Run-Ordner mit diesem Praefix")
    ap.add_argument("--runs", default=str(RUNS))
    ap.add_argument("--out", default=str(ROOT / "docs" / "report"))
    ap.add_argument("--seed", type=int, default=0, help="Bootstrap-Seed")
    args = ap.parse_args()

    runs = load_runs(args.prefix, Path(args.runs))
    runs = [r for r in runs if not r["dir"].name.endswith(("_probe", "_pilot"))]
    if not runs:
        raise SystemExit("Keine fertigen Laeufe gefunden.")
    for r in runs:
        r["eval"]["pdiff"] = r["eval"]["our_points"] - r["eval"]["opp_points"]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(args.seed)
    summ, diffs = summarize(runs, rng)
    beh = behaviour(runs)
    write_markdown(out, summ, diffs, beh, runs)
    (out / "summary.json").write_text(json.dumps(
        {"winrates": summ.to_dict("records"), "ablation": diffs.to_dict("records"),
         "behaviour": beh.to_dict("records"), "runs": [r["dir"].name for r in runs]},
        indent=2, default=float))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _style(plt)
    plot_winrates(summ, out, plt)
    plot_ablation(diffs, out, plt)
    plot_learning(runs, out, plt)
    plot_training(runs, out, plt)
    print(f"{len(runs)} Laeufe ausgewertet -> {out}")
    print(summ[["variant", "opponent", "winrate", "ci_lo", "ci_hi", "run_sd"]].to_string(index=False))


if __name__ == "__main__":
    main()
