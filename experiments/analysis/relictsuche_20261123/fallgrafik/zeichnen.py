"""Render the verified 164050141 world-coordinate teaching figure from archived real games."""
import gzip
from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
import numpy as np


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "ortundflotte"
SEED = 164050141
STEM = "schiff_0_vier_punktefelder"
INK = "#112B32"
MUTED = "#415B61"
TEAL = "#006A62"
GRID = "#CAD7D5"
PAPER = "#FAFBF7"
DARK = "#11393C"


def evidence():
    source = json.loads((PARENT / "fallstudie/ergebnis.json").read_bytes())
    archive = PARENT / "duelle_karten.jsonl.gz"
    assert sha256(archive.read_bytes()).hexdigest() == source["archive"]
    case = next(r for r in source["cases"] if r["seed"] == SEED and r["team"] == 1)
    old, new = case["controls"]
    independent = {r["id"]: r for r in map(json.loads, gzip.decompress(archive.read_bytes()).splitlines())
                   if r["seed"] == SEED and r["team"] == 1 and r["opponent"] == "solution92"}
    for actor, arm in ((old, "reference"), (new, "scout")):
        assert actor["hash"] == independent[arm]["action_hash"] and actor["matches"] == independent[arm]["matches"]
    assert new["route"] == [[21, 0, 0, 3], [22, 0, 1, 3]]
    positions = [np.asarray([p["pos"] for p in a["opening"][21:24]]) for a in (old, new)]
    assert positions[0].tolist() == [[10, 19], [10, 19], [10, 19]]
    assert positions[1].tolist() == [[10, 19], [10, 20], [10, 21]]
    assert [a["opening"][1]["pos"] for a in (old, new)] == [[23, 23], [23, 23]]
    assert [old["credit"], new["credit"], old["sight"], new["sight"]] == [61, 42, 65, 71]
    extra = case["transfer"][0]
    known = [set(r["known"]["points"]) for r in (old, new)]
    assert [len(g) for g in known] == [6, 10] and set(extra["added"]) == known[1]-known[0]
    assert set(extra["added"]) <= set(old["known"]["true_points"])
    # Belief entries use canonical x*24+y; the P1 transform is an involution.
    from_p1 = lambda xy: (23-xy[1], 23-xy[0])
    world = set(from_p1(divmod(k, 24)) for k in extra["added"])
    assert world == {(14, 1), (22, 9), (18, 4), (19, 5)}
    pairs = sorted((cell, from_p1(cell)) for cell in world if cell < from_p1(cell))
    assert extra["replayed"] and old["matches"][0] == extra["matches"][0] and old["matches"][0]["points"] == [140, 1]
    assert [old["matches"][1]["points"], extra["matches"][1]["points"]] == [[183, 197], [190, 186]]
    assert [old["win"], extra["win"], new["matches"][1]["points"]] == [0, 1, [294, 266]]
    return positions, pairs


def main():
    paths, pairs = evidence()
    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "ps.fonttype": 42})
    fig = plt.figure(figsize=(16, 9), facecolor=PAPER)
    txt = lambda x, y, s, fs, col=INK, weight="normal", **args: fig.text(
        x, y, s, fontsize=fs, color=col, weight=weight, va="center", **args)
    box = lambda x, y, w, h, col: fig.add_artist(
        Rectangle((x, y), w, h, transform=fig.transFigure, facecolor=col, edgecolor="none", zorder=-1))
    txt(.055, .937, "SHERLOCK GEGEN SOLUTION   ·   KARTE 164050141   ·   SPIELER 1", 15, MUTED, "bold")
    txt(.0525, .849, "Vier zusätzliche Punktefelder drehen Match 2", 37, INK, "bold")
    box(.055, .781, .890, .002, GRID)

    txt(.055, .718, "Schiff 0 auf der neuen Route", 23, INK, "bold")
    txt(.055, .666, "Weltkarte (x, y) · Spieler 1 startet unten rechts bei (23, 23).", 13.8, MUTED)
    ax = fig.add_axes([.055, .323, .202, .310], facecolor="#F1F6F2")
    ax.set_aspect("equal")
    ax.set_xlim(8.5, 11.5)
    ax.set_ylim(21.5, 18.5)
    ax.set_xticks([9, 10, 11])
    ax.set_yticks([19, 20, 21])
    ax.tick_params(axis="both", length=0, labelsize=13, colors=MUTED, pad=6)
    for v in np.arange(8.5, 12, 1):
        ax.axvline(v, color=GRID, linewidth=1.5, zorder=0)
    for v in np.arange(18.5, 22, 1):
        ax.axhline(v, color=GRID, linewidth=1.5, zorder=0)
    ax.spines[:].set_visible(False)
    original, scout = paths
    for start, end in zip(scout[:-1], scout[1:], strict=True):
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", color=TEAL, mutation_scale=23,
                                    shrinkA=9, shrinkB=8, linewidth=3.7, zorder=3))
    for x, y in scout[1:]:
        ax.add_patch(Circle((x, y), .092, color=TEAL, zorder=4))
    # The stationary original holds the shared starting position on both real turns.
    ax.scatter(*original[0], s=120, facecolor=PAPER, edgecolor=INK, linewidth=2.8, marker="s", zorder=5)
    for i, (header, subtitle) in enumerate([
        ("(10, 19)", "V16 bleibt hier."),
        ("(10, 20)", "Nach Zug 21"),
        ("(10, 21)", "Nach Zug 22"),
    ]):
        y = .633 - (i+.5)*.310/3
        txt(.265, y+.013, header, 20, INK if i == 0 else TEAL, "bold")
        txt(.265, y-.024, subtitle, 15, MUTED)
    box(.487, .315, .0014, .428, GRID)

    txt(.527, .718, "Erster Teampunkt in Match 1", 21, INK, "bold")
    txt(.526, .631, "Zug 42", 36, TEAL, "bold")
    txt(.686, .629, "statt Zug 61", 22, MUTED)
    box(.527, .558, .418, .002, GRID)
    txt(.527, .508, "Zu Beginn von Match 2", 19, MUTED)
    txt(.525, .441, "10 richtige Punktefelder statt 6", 23, INK, "bold")
    fmt = lambda xy: f"({xy[0]}, {xy[1]})"
    coords = [f"{fmt(a)} ↔ {fmt(b)}" for a, b in pairs]
    txt(.527, .373, "Die vier neuen Felder bilden zwei Spiegelpaare.", 15, MUTED)
    txt(.527, .320, "    ·    ".join(coords), 16, TEAL, "bold")

    box(0., .0, 1., .243, DARK)
    txt(.055, .171, "Isolierter V16-Gegenversuch", 23, "#FFFFFF", "bold")
    txt(.055, .097, "V16 erhält nur die vier Felder für Match 2.", 17, "#E3F0E9")
    txt(.535, .180, "Ohne Hinweis · verloren", 13.5, "#D7E8E1")
    txt(.535, .095, "183:197", 34, "#FFFFFF", "bold")
    txt(.706, .095, "→", 32, "#A1BBB5")
    txt(.779, .180, "Mit Hinweis · gewonnen", 13.5, "#DAF1DD")
    txt(.779, .095, "190:186", 34, "#A1E4B0", "bold")
    fig.savefig(HERE / (STEM+".png"), dpi=160, facecolor=fig.get_facecolor())
    fig.savefig(HERE / (STEM+".pdf"), facecolor=fig.get_facecolor(),
                metadata={"Title": "Vier zusätzliche Punktefelder drehen Match 2", "Author": "Sherlock, Team 15"})
    plt.close(fig)


if __name__ == "__main__":
    main()
