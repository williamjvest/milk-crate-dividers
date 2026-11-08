"""Single-channel WALL clip for the Juggernaut 24 qt milk crates.

It is the floor insert (crate_floor_insert.py) with the wall clip's plug: one channel instead of
the original cross, because only one channel is ever used and the second arm was waste (2026-11-08).
  - Plug: 29.65 mm across the flats, 6 mm deep, turned 45 deg so its corners point along and
    across the channel. That is milk-crate-divider-wvmodified2's plug, proven in the wall holes.
  - Everything else is the floor insert's: a 26 x 50 mm arm, 9 mm thick, a 5.9 x 6 mm channel with
    its floor 3 mm off the wall, the same lead-ins.
  - The plug square runs up through the body to the front face, as on the floor insert. With the
    cross arm gone, that is what keeps the plug's side corners from printing over air. On this
    bigger plug those "ears" stick out 8 mm past the arm.
  - The plug is square, so the clip goes in with the channel vertical (dividers) or turned 90 deg
    (shelves).
The cross-channel version it replaces is in this repo's history (commit a304c20).

Frames: CAD frame = use frame. z = 0 on the crate wall (the body's back face), z up into the crate,
channel along x, plug below z = 0. Print orientation: channel face down on the bed, plug up
(`*_print.stl`). The only span over air is the channel ceiling, 5.9 mm across, so no special
bridge settings.

Run: ~/.venvs/cad/bin/python crate_wall_clip.py
"""
import math
from pathlib import Path
from build123d import Axis, Box, Pos, Rot, chamfer, export_step, export_stl

HERE = Path(__file__).resolve().parent
NAME = "crate-wall-clip"

# --- parameters (mm) ---------------------------------------------------------------------
PLUG = 29.65        # wvmodified2's plug across flats: fits the Juggernaut's wall holes
HOLE = 30.0         # wall hole across flats: NOT measured; for the fit numbers only
PLUG_H = 6.0        # same plug depth as wvmodified2 and the floor insert
TIP_CHAMFER = 0.6   # lead-in on the plug tip
ARM_W = 26.0        # arm width (floor insert's, = wvmodified2's arms)
ARM_L = 50.0        # arm length; its ends land on the wall past the hole's corners
BODY_T = 9.0        # body thickness, back face to channel face
SLOT_W = 5.9        # 1/4" maple ply (5.16-5.4 mm): the floor insert's, which fit "perfectly"
SLOT_D = 6.0        # channel depth
BASE = BODY_T - SLOT_D   # 3.0: the panel edge sits this far off the wall
LEAD = 0.6          # lead-in on the channel mouth so the panel drops in
BOARD_T = 5.3       # 1/4" maple ply as measured; fit numbers only
CORNER = PLUG / math.sqrt(2)        # plug centre to corner (along and across the channel)
HOLE_CORNER = HOLE / math.sqrt(2)


def build():
    arm = Pos(0, 0, BODY_T / 2) * Box(ARM_L, ARM_W, BODY_T)
    # plug square turned 45 deg, running from the plug tip up through the body to the front face
    square = Pos(0, 0, (BODY_T - PLUG_H) / 2) * Rot(0, 0, 45) * Box(PLUG, PLUG, BODY_T + PLUG_H)
    slot = Pos(0, 0, BODY_T - SLOT_D / 2 + 0.5) * Box(ARM_L + 10, SLOT_W, SLOT_D + 1)
    part = arm + square - slot
    notes = []

    def try_chamfer(p, edges, size, label):
        try:
            return chamfer(edges, size)
        except Exception as e:  # cosmetic chamfers sometimes fail in OCC; keep building
            notes.append(f"chamfer '{label}' skipped: {e}")
            return p

    mouth = [e for e in part.edges().filter_by(Axis.X)
             if abs(e.center().Z - BODY_T) < 1e-3 and abs(abs(e.center().Y) - SLOT_W / 2) < 1e-3]
    part = try_chamfer(part, mouth, LEAD, "channel mouth")
    tip = [e for e in part.edges() if abs(e.center().Z + PLUG_H) < 1e-3]
    part = try_chamfer(part, tip, TIP_CHAMFER, "plug tip")
    return part, {"solids": len(part.solids()), "volume_cm3": part.volume / 1000.0, "notes": notes}


def checks(info, stl_cad, stl_print):
    import numpy as np
    import trimesh
    out = {}
    m = trimesh.load(stl_cad, force="mesh")
    out["watertight"] = bool(m.is_watertight)
    out["bodies"] = len(m.split(only_watertight=False))
    out["solids (B-rep)"] = info["solids"]
    out["bbox"] = [tuple(round(float(v), 2) for v in m.bounds[:, i]) for i in range(3)]
    mp = trimesh.load(stl_print, force="mesh")
    z = mp.vertices[:, 2]
    out["print min z / max z"] = (round(float(z.min()), 3), round(float(z.max()), 3))
    out["plug across flats / corner to corner"] = (PLUG, round(2 * CORNER, 2))
    out["arm past the hole corner (each end, est.)"] = round(ARM_L / 2 - HOLE_CORNER, 2)
    tri = max(0.0, HOLE_CORNER - ARM_W / 2) ** 2
    out["landing area on wall (mm2, est.)"] = round(ARM_L * ARM_W - (HOLE ** 2 - 2 * tri), 1)
    out["ear past arm side (each)"] = round(CORNER - ARM_W / 2, 2)
    out["board play per side in channel"] = round((SLOT_W - BOARD_T) / 2, 3)
    out["volume cm3 (cross version: 19.09)"] = round(info["volume_cm3"], 2)
    return out


if __name__ == "__main__":
    part, info = build()
    stl = HERE / f"{NAME}.stl"
    stl_print = HERE / f"{NAME}_print.stl"
    export_step(part, str(HERE / f"{NAME}.step"))
    export_stl(part, str(stl), tolerance=0.01, angular_tolerance=0.1)
    export_stl(Pos(0, 0, BODY_T) * Rot(180, 0, 0) * part, str(stl_print),
               tolerance=0.01, angular_tolerance=0.1)
    for k, v in checks(info, stl, stl_print).items():
        print(f"{k:42s} {v}")
    for n in info["notes"]:
        print("NOTE", n)
