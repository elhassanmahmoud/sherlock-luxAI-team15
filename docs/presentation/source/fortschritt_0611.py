"""Fortschrittsdiagramm fuer die Battle-Folien vom 06.11.2026 (Werte aus den Uebernahmeberichten bis V14, Stand 01.11.).

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
ACC = "#123F4A"
labels = ["16.10.\nReview 1", "20.10.\nV3", "22.10.\nV7", "22.10.\nV10", "30.10.\nV11", "31.10.\nV12", "01.11.\nV14"]
vals = [46.7, 78.25, 83.5, 90.3, 94.1, 94.4, 95.4]
texts = ["46,7 %", "78,3 %", "83,5 %", "90,3 %", "94,1 %", "94,4 %", "95,4 %"]
base = ["28/60\nTest-\nkarten", "200\nneue\nKarten", "400\nneue\nKarten", "800\nneue\nKarten", "800\nneue\nKarten", "800\nneue\nKarten", "800\nneue\nKarten"]
colors = ["#A7B4B6", LIGHT, TEAL, TEAL, DARK, ACC, ACC]

fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=200)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
x = range(len(vals))
ax.bar(x, vals, width=0.62, color=colors, zorder=3)
for i, (v, t, b) in enumerate(zip(vals, texts, base)):
    ax.text(i, v + 1.6, t, ha="center", va="bottom", fontsize=12.5, fontweight="bold", color=INK)
    ax.text(i, 3.0, b, ha="center", va="bottom", fontsize=7.6, linespacing=1.1, color="white" if i >= 2 else INK)
ax.set_xticks(list(x))
ax.set_xticklabels(labels, fontsize=9.5, color=INK)
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
    ax.text((x0 + x1) / 2, y + 1.2, text, ha="center", va="bottom", fontsize=8.8, color=color, fontweight="bold")


bracket(-0.1, 0.95, 106, "Regeln + Training\n18 Netze", GREY)
bracket(1.05, 3.25, 106, "Fehlersuche,\ngleiche 18 Netze", TEAL)
bracket(3.65, 4.3, 106, "Nach-\ntraining", DARK)
bracket(4.7, 6.3, 106, "gezielte\nKorrekturen", ACC)
fig.tight_layout()
fig.savefig(sys.argv[1], facecolor=BG)
