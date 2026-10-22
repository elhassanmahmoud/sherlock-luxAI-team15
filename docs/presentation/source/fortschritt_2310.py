"""Fortschrittsdiagramm fuer die Folien vom 23.10.2026 (Werte aus den Uebernahmeberichten).

Aufruf: .venv/bin/python docs/presentation/source/fortschritt_2310.py docs/presentation/folie_2310_fortschritt.png
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

BG, INK, GREY, TEAL, LIGHT = "#F7F6F1", "#142D35", "#56676C", "#0F7C7A", "#8FB9B3"
labels = ["16.10.\nAbgabe Review 1", "20.10.\nV3", "22.10.\nV7", "22.10.\nV10"]
vals = [46.7, 78.25, 83.5, 90.3]
texts = ["46,7 %", "78,25 %", "83,5 %", "90,3 %"]
base = ["28/60 Testkarten", "200 neue Karten", "400 neue Karten", "800 neue Karten"]
colors = ["#A7B4B6", LIGHT, TEAL, TEAL]

fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=200)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
x = range(len(vals))
bars = ax.bar(x, vals, width=0.58, color=colors, zorder=3)
for i, (v, t, b) in enumerate(zip(vals, texts, base)):
    ax.text(i, v + 1.6, t, ha="center", va="bottom", fontsize=15, fontweight="bold", color=INK)
    ax.text(i, 3.5, b, ha="center", va="bottom", fontsize=8.5, color="white" if i >= 2 else INK)
ax.set_xticks(list(x))
ax.set_xticklabels(labels, fontsize=11, color=INK)
ax.set_ylim(0, 116)
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_yticklabels(["0 %", "25 %", "50 %", "75 %", "100 %"], fontsize=10.5, color=GREY)
ax.grid(axis="y", color="#DCDCD6", zorder=0)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#B9C2C2")
ax.tick_params(axis="both", length=0)
# Klammern: welcher Schritt woher kam
def bracket(x0, x1, y, text, color):
    ax.plot([x0, x0, x1, x1], [y - 2.2, y, y, y - 2.2], color=color, lw=1.4, zorder=4)
    ax.text((x0 + x1) / 2, y + 1.2, text, ha="center", va="bottom", fontsize=10.5, color=color, fontweight="bold")
bracket(-0.1, 0.95, 105, "Regeln + Neutraining + 18 Netze", GREY)
bracket(1.05, 3.1, 105, "Fehlersuche, gleiche 18 Netze", TEAL)
fig.tight_layout()
fig.savefig(sys.argv[1], facecolor=BG)
