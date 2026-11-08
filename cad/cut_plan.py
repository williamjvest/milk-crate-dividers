"""Cut plan for the dividers: one 4x8 sheet of 1/4" plywood -> 36 panels, 12" x 9-7/8".
Run: python3 cut_plan.py ../images/cut-plan.png   (needs matplotlib)
"""
import sys, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

OUT = sys.argv[1]
W, L = 48.47, 96.47            # Lowe's 1/4" maple, oversized panel: 4.039 x 8.039 ft actual
K = 0.125                      # kerf
PW, PH = 12.0, 9.875           # divider panel: 12" wide x 9-7/8" tall
CIRC = [32.0, 64.0]            # breakdown cuts, measured from one end
bases = [0.0, CIRC[0] + K / 2, CIRC[1] + K / 2]
tops = [CIRC[0] - K / 2, CIRC[1] - K / 2, L]
TRIM = 0.25                    # squaring cut on each piece's rough end
used_w = 4 * PW + 3 * K        # 48.375

RED, BLUE, GREEN = "#D62839", "#1F5FD1", "#138A55"
WOOD, INK, WASTE = "#F5E6C6", "#222222", "#D3D3D3"

FIG_W, FIG_H = 8.0, 20.0
fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=150)


def F(x_in, y_in):
    return x_in / FIG_W, 1 - y_in / FIG_H


def ftext(x_in, y_in, s, **kw):
    x, y = F(x_in, y_in)
    kw.setdefault("va", "top")
    kw.setdefault("ha", "left")
    kw.setdefault("color", INK)
    return fig.text(x, y, s, **kw)


ftext(0.45, 0.35, "Milk crate dividers: cut plan", fontsize=24, weight="bold")
ftext(0.45, 0.9, '1 sheet 1/4" maple plywood 4x8 (Lowe\'s oversized, 48-1/2 x 96-1/2)', fontsize=14)
ftext(0.45, 1.2, '36 panels, 12" wide x 9-7/8" tall. 1/8" kerf.', fontsize=14, weight="bold")

xl, yl = (-15.0, 57.0), (-4.0, 101.0)
ax_w_in = 7.2
upi = (xl[1] - xl[0]) / ax_w_in
ax_h_in = (yl[1] - yl[0]) / upi
ax_top_in = 1.55
x0f, y0f = F((FIG_W - ax_w_in) / 2, ax_top_in + ax_h_in)
ax = fig.add_axes([x0f, y0f, ax_w_in / FIG_W, ax_h_in / FIG_H])
ax.set_xlim(*xl)
ax.set_ylim(*yl)
ax.set_aspect("equal")
ax.axis("off")


def waste(x, y, w, h):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=WASTE, edgecolor="#8C8C8C",
                           hatch="////", lw=0, zorder=1))


cells = []
for t in range(3):
    for r in range(3):
        y = bases[t] + TRIM + r * (PH + K)
        for c in range(4):
            cells.append((c * (PW + K), y))
    top_off = bases[t] + TRIM + 3 * PH + 2 * K
    waste(0, bases[t], used_w, TRIM)
    waste(0, top_off, used_w, tops[t] - top_off)
    waste(used_w, bases[t], W - used_w, tops[t] - bases[t])

cells.sort(key=lambda p: (-p[1], p[0]))
for i, (x, y) in enumerate(cells, 1):
    ax.add_patch(Rectangle((x, y), PW, PH, facecolor=WOOD, edgecolor="none", zorder=1))
    ax.text(x + PW / 2, y + PH / 2, str(i), ha="center", va="center",
            fontsize=14, color="#9A7B4F", zorder=3)

for t in range(3):
    for c in range(1, 4):
        xc = c * (PW + K) - K / 2
        ax.plot([xc, xc], [bases[t], tops[t]], color=BLUE, lw=2.4, zorder=4)
    xc = used_w + K / 2  # skim the 4th strip down to 12
    ax.plot([xc, xc], [bases[t], tops[t]], color=BLUE, lw=2.4, zorder=4)
    for r in range(3):
        yc = bases[t] + TRIM + (r + 1) * PH + r * K + K / 2
        ax.plot([0, used_w], [yc, yc], color=GREEN, lw=2.4, zorder=4)

for y in CIRC:
    ax.plot([-0.9, W + 0.9], [y, y], color=RED, lw=3.6, ls=(0, (5, 2.5)), zorder=6)
    ax.text(-1.6, y, f'circ saw\n{y:.0f}"', ha="right", va="center", fontsize=13,
            weight="bold", color=RED, linespacing=1.1)

ax.add_patch(Rectangle((0, 0), W, L, fill=False, edgecolor=INK, lw=2.2, zorder=7))

for c in range(4):
    ax.text(c * (PW + K) + PW / 2, L + 1.4, '12"', ha="center", va="bottom",
            fontsize=13, weight="bold", color=BLUE)
for t in range(3):
    for r in range(3):
        y = bases[t] + TRIM + r * (PH + K) + PH / 2
        ax.text(W + 1.3, y, '9-7/8"', ha="left", va="center", fontsize=13,
                weight="bold", color=GREEN)

ax.text(W / 2, -0.9, '\u2191 measure 32" and 64" from this end', ha="center",
        va="top", fontsize=12, color=RED)

y = ax_top_in + ax_h_in + 0.3
legend = [
    ("line", RED, (0, (5, 2.5)), 3.6, "Circular saw (or Lowe's): 2 rough cuts"),
    ("line", BLUE, "-", 2.4, 'Table saw rip, fence at 12"'),
    ("line", GREEN, "-", 2.4, 'Crosscut at 9-7/8": miter gauge or sled + stop block'),
    ("box", None, None, None, "Waste"),
]
for kind, col, ls, lw, label in legend:
    yc = y + 0.13
    if kind == "line":
        x1, y1 = F(0.5, yc)
        x2, _ = F(1.25, yc)
        fig.add_artist(Line2D([x1, x2], [y1, y1], color=col, lw=lw, ls=ls,
                              transform=fig.transFigure))
    else:
        bx, by = F(0.5, yc + 0.11)
        fig.add_artist(Rectangle((bx, by), 0.75 / FIG_W, 0.22 / FIG_H,
                                 transform=fig.transFigure, facecolor=WASTE,
                                 edgecolor="#8C8C8C", hatch="////", lw=0.8))
    ftext(1.45, y, label, fontsize=14)
    y += 0.38

steps = [
    'Circular saw (or Lowe\'s panel saw): cut the sheet at 32" and 64". '
    'Good face DOWN. Rough is fine, the table saw trims it.',
    'Table saw, fence at 12", good face UP. Rip ONE strip, crosscut ONE 9-7/8" '
    'panel, and test it in a crate with its clips before cutting the rest.',
    'Rip each piece into 4 strips. The 4th comes out about 12-1/8": skim it to 12".',
    'Crosscut with the miter gauge or a sled and a stop block at 9-7/8". Square '
    'one end first, then 3 panels per strip. You can stack 2-3 strips. Never use '
    'the rip fence as the length stop.',
    'Sand the edges. If you seal them, keep it thin: the channels are 5.9 mm.',
]
note = ('Fine-tooth blade (60T+). A zero-clearance insert or painter\'s tape on the '
        'cut line stops the underside splintering.')

y += 0.25
ftext(0.45, y, "STEPS", fontsize=16, weight="bold")
y += 0.42
WRAP = 54
for i, s in enumerate(steps, 1):
    ftext(0.45, y, f"{i}.", fontsize=14, weight="bold")
    for ln in textwrap.wrap(s, WRAP):
        ftext(0.8, y, ln, fontsize=14)
        y += 0.27
    y += 0.1
y += 0.1
for ln in textwrap.wrap(note, WRAP + 4):
    ftext(0.45, y, ln, fontsize=13, style="italic")
    y += 0.25

fig.savefig(OUT, dpi=150, bbox_inches="tight", pad_inches=0.3, facecolor="white")
print("text ends at y_in", round(y, 2), "of", FIG_H)
