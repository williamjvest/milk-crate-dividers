"""Blueprint sheet for the crate floor insert: a top view and two sections, all cut from the real
STL, plus the key numbers. Run: ~/.venvs/cad/bin/python blueprint_floor_insert.py [out.png]"""
import sys
import textwrap
from pathlib import Path
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import crate_floor_insert as P  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "renders" / "floor-insert-blueprint.png"
m = trimesh.load(HERE / "crate-floor-insert.stl", force="mesh")
INK, CUT, DIM, FLOOR, WOOD = "#1d2733", "#9fb4cc", "#c0392b", "#555555", "#e8d3ac"
L, Wd, C, HC = P.ARM_L / 2, P.ARM_W / 2, P.CORNER, P.HOLE_CORNER
XA = 12.0                                   # section A-A: across the channel, beside the ears


def loops(normal, origin=(0, 0, 0)):
    sec = m.section(plane_origin=origin, plane_normal=normal)
    return [] if sec is None else [np.asarray(d) for d in sec.discrete]


def dim_h(ax, x0, x1, y, text, above=True, fs=10.5):
    ax.annotate("", xy=(x0, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="<->", color=DIM, lw=1.1, shrinkA=0, shrinkB=0))
    ax.text((x0 + x1) / 2, y + (0.5 if above else -0.5), text, color=DIM, fontsize=fs,
            ha="center", va="bottom" if above else "top", weight="bold")


def dim_v(ax, x, y0, y1, text, side="right", fs=10.5):
    ax.annotate("", xy=(x, y0), xytext=(x, y1),
                arrowprops=dict(arrowstyle="<->", color=DIM, lw=1.1, shrinkA=0, shrinkB=0))
    ax.text(x + (0.6 if side == "right" else -0.6), (y0 + y1) / 2, text, color=DIM, fontsize=fs,
            ha="left" if side == "right" else "right", va="center", weight="bold")


def section(ax, normal, origin, cols, floor_half, title):
    for d in loops(normal, origin):
        ax.add_patch(Polygon(d[:, cols], closed=True, facecolor=CUT, edgecolor=INK, lw=1.5, hatch="///",
                             zorder=3))
    for s in (-1, 1):                       # crate floor either side of the hole at this cut
        ax.add_patch(Rectangle((min(s * floor_half, s * (floor_half + 9)), -8), 9, 8, facecolor="#d9d9d9",
                               edgecolor=FLOOR, lw=1.0, ls="--", zorder=1))
    ax.add_patch(Rectangle((-P.BOARD_T / 2, P.BASE), P.BOARD_T, P.SLOT_D + 5, facecolor=WOOD,
                           edgecolor="#8a6d3b", lw=1.0, zorder=2)) if cols == [1, 2] else None
    ax.text(0, P.BODY_T + 7.5, title, fontsize=11, weight="bold", color=INK, ha="center", va="bottom")


fig = plt.figure(figsize=(8.5, 11.5), dpi=150)
fig.text(0.06, 0.975, "Crate floor insert: single channel", fontsize=21, weight="bold", va="top", color=INK)
fig.text(0.06, 0.945, "The wall clip with one channel and a smaller square plug.", fontsize=12, va="top",
         color=INK)

# --- Top view (in use, looking down into the channel) -----------------------------------------
ax = fig.add_axes([0.03, 0.62, 0.94, 0.30]); ax.set_aspect("equal"); ax.axis("off")
for d in loops([0, 0, 1], (0, 0, P.BASE + 1.0)):
    ax.add_patch(Polygon(d[:, :2], closed=True, facecolor="#dfe7f0", edgecolor=INK, lw=1.6))
for d in loops([0, 0, 1], (0, 0, -P.PLUG_H / 2)):
    ax.plot(np.r_[d[:, 0], d[0, 0]], np.r_[d[:, 1], d[0, 1]], color="#5b6b7d", lw=1.2, ls="--")
dim_h(ax, -L, L, C + 3.0, f"{P.ARM_L:.0f}")
dim_v(ax, L + 3, -Wd, Wd, f"{P.ARM_W:.0f}")
dim_h(ax, -C, C, -C - 3.0, f"plug {P.PLUG} square (dashed), {2 * C:.1f} corner to corner", above=False)
ax.text(-L - 1.5, 0, f"{P.SLOT_W}\nchannel", fontsize=10, color=DIM, weight="bold", ha="right", va="center")
for x, lab in ((XA, "A"),):
    ax.plot([x, x], [-Wd - 3, Wd + 3], color=DIM, lw=0.8, ls="-.")
    ax.text(x, Wd + 3.4, lab, color=DIM, fontsize=11, weight="bold", ha="center", va="bottom")
ax.plot([-L - 3, L + 3], [0, 0], color="#7d8a99", lw=0.7, ls="-.")
ax.text(L + 9.5, 0.2, "B", color=DIM, fontsize=11, weight="bold", va="center")
ax.text(-L, -C - 9, "TOP  (ears = the plug square running up through the body)", fontsize=10.5,
        color=INK, weight="bold", ha="left")
ax.set_xlim(-L - 12, L + 14); ax.set_ylim(-C - 11, C + 7)

# --- Section A-A: across the channel, through the arm beside the ears ----------------------------
bx = fig.add_axes([0.03, 0.335, 0.45, 0.26]); bx.set_aspect("equal"); bx.axis("off")
section(bx, [1, 0, 0], (XA, 0, 0), [1, 2], HC - XA, "SECTION A-A")
dim_h(bx, -Wd, Wd, -P.PLUG_H - 3.0, f"{P.ARM_W:.0f} arm", above=False)
dim_v(bx, Wd + 2.5, P.BASE, P.BODY_T, f"{P.SLOT_D:.0f}")
dim_v(bx, Wd + 2.5, 0, P.BASE, f"{P.BASE:.0f}")
dim_v(bx, Wd + 2.5, -P.PLUG_H, 0, f"{P.PLUG_H:.0f}")
bx.set_xlim(-Wd - 10, Wd + 12); bx.set_ylim(-P.PLUG_H - 9, P.BODY_T + 11)

# --- Section B-B: along the channel ----------------------------------------------------------------
cx = fig.add_axes([0.49, 0.335, 0.49, 0.26]); cx.set_aspect("equal"); cx.axis("off")
section(cx, [0, 1, 0], (0, 0, 0), [0, 2], HC, "SECTION B-B (along the channel)")
cx.add_patch(Rectangle((-L + 2, P.BASE), 2 * L - 4, 4.5, facecolor=WOOD, edgecolor="#8a6d3b", lw=1.0,
                       zorder=2))
cx.text(0, P.BASE + 2.2, "panel", fontsize=9.5, color="#8a6d3b", ha="center", va="center", weight="bold")
dim_h(cx, -L, L, P.BODY_T + 3.5, f"{P.ARM_L:.0f}", fs=10)
dim_h(cx, -C, C, -P.PLUG_H - 3.0, f"{2 * C:.1f}", above=False, fs=10)
cx.annotate(f"{L - HC:.1f} on the floor\npast the hole corner", xy=(L - 1.5, -0.3), xytext=(L - 14, -12.5),
            fontsize=9, color=FLOOR, ha="left", va="top", arrowprops=dict(arrowstyle="->", color=FLOOR, lw=0.8))
cx.set_xlim(-L - 10, L + 10); cx.set_ylim(-P.PLUG_H - 15, P.BODY_T + 11)

# --- Notes -----------------------------------------------------------------------------------
notes = [
    ("Same as the wall clip", f"{P.ARM_W:.0f} x {P.ARM_L:.0f} arm, {P.BODY_T:.0f} thick, {P.SLOT_W} x "
     f"{P.SLOT_D:.0f} channel, {P.PLUG_H:.0f} mm plug turned 45° to the channel."),
    ("Changed", f"One channel. Plug {P.PLUG} mm ({P.PLUG / 25.4:.2f}\") square; the wall clip's is 29.65 mm (1.17\")."),
    ("Fit", f"Floor hole {P.HOLE:.1f} mm ({P.HOLE / 25.4:.2f}\"): "
     f"{P.HOLE / 2 - P.PLUG / 2:.2f} mm a side. Snug by design."),
    ("Height", f"Panel sits {P.BASE:.0f} mm (about 1/8\") off the floor. 9-7/8\" boards still let the crates stack."),
    ("Print", "Like the wall clip: channel face down, plug up. No supports."),
]
cols = [(0.06, 0.30), (0.53, 0.30)]
for i, (k, v) in enumerate(notes):
    x, y0 = cols[0] if i < 3 else cols[1]
    y = y0 - sum(0.03 + 0.0185 * len(textwrap.wrap(nv, 44)) for _, nv in (notes[:i] if i < 3 else notes[3:i]))
    fig.text(x, y, k, fontsize=11.5, weight="bold", color=INK, va="top")
    for j, line in enumerate(textwrap.wrap(v, 44)):
        fig.text(x, y - 0.021 - j * 0.0185, line, fontsize=10.5, color=INK, va="top")
fig.text(0.06, 0.02, f"crate_floor_insert.py · {P.ARM_L:.0f} x {2 * C:.1f} x {P.BODY_T + P.PLUG_H:.0f} mm · "
         f"{P.SLOT_W} channel for 1/4\" maple ply ({P.BOARD_T} mm)", fontsize=9, color="#667788")
OUT.parent.mkdir(exist_ok=True)
fig.savefig(OUT, dpi=150, facecolor="white")
print("wrote", OUT)
