"""Fortschrittsdiagramm fuer die Battle-Folien vom 06.11.2026 (Werte aus den Uebernahmeberichten bis V11).

Aufruf: .venv/bin/python docs/presentation/source/fortschritt_0611.py docs/presentation/folie_0611_fortschritt.png
"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

try:
    font_manager.fontManager.addfont("/System/Library/Fonts/HelveticaNeue.ttc")
    plt.rcParams["font.family"] = "Helvetica Neue"
except Exception:
    pass

BG, INK, GREY, TEAL, LIGHT, DARK = "#F7F6F1", "#142D35", "#56676C", "#0F7C7A", "#8FB9B3", "#0B5755"
labels = ["16.10.\nReview 1", "20.10.\nV3", "22.10.\nV7", "22.10.\nV10", "30.10.\nV11"]
vals = [46.7, 78.25, 83.5, 90.3, 94.1]
texts = ["46,7 %", "78,25 %", "83,5 %", "90,3 %", "94,1 %"]
base = ["28/60\nTestkarten", "200 neue\nKarten", "400 neue\nKarten", "800 neue\nKarten", "800 neue\nKarten"]
colors = ["#A7B4B6", LIGHT, TEAL, TEAL, DARK]

fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=200)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
x = range(len(vals))
ax.bar(x, vals, width=0.6, color=colors, zorder=3)
for i, (v, t, b) in enumerate(zip(vals, texts, base)):
    ax.text(i, v + 1.6, t, ha="center", va="bottom", fontsize=14, fontweight="bold", color=INK)
    ax.text(i, 3.0, b, ha="center", va="bottom", fontsize=8.5, linespacing=1.15, color="white" if i >= 2 else INK)
ax.set_xticks(list(x))
ax.set_xticklabels(labels, fontsize=10.5, color=INK)
ax.set_ylim(0, 118)
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_yticklabels(["0 %", "25 %", "50 %", "75 %", "100 %"], fontsize=10, color=GREY)
ax.grid(axis="y", color="#DCDCD6", zorder=0)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#B9C2C2")
ax.tick_params(axis="both", length=0)


def bracket(x0, x1, y, text, color):
    """Klammer ueber den Balken: welcher Schritt woher kam."""
    ax.plot([x0, x0, x1, x1], [y - 2.2, y, y, y - 2.2], color=color, lw=1.4, zorder=4)
    ax.text((x0 + x1) / 2, y + 1.2, text, ha="center", va="bottom", fontsize=9.5, color=color, fontweight="bold")


bracket(-0.1, 0.95, 106, "Regeln + Training\n18 Netze", GREY)
bracket(1.05, 3.1, 106, "Fehlersuche,\ngleiche 18 Netze", TEAL)
bracket(3.2, 4.25, 106, "Nachtraining\n+ Sap-Regeln", DARK)
fig.tight_layout()
fig.savefig(sys.argv[1], facecolor=BG)
