"""Single-channel FLOOR insert for the Juggernaut 24 qt milk crates.

It is the wall clip (milk-crate-divider-wvmodified2.stl) with two changes, (2026-11-07):
  1. One channel instead of the cross. Only one is ever used, so the second arm was waste.
  2. A smaller square plug. The floor holes are smaller than the wall holes.
Everything else matches the wall clip: a 26 mm x 50 mm arm, 9 mm thick, a 6 mm deep channel
with its floor 3 mm off the crate, a 6 mm plug, and the plug square turned 45 deg to the channel
(corners along and across the channel), the same as on the wall clip.
The channel is narrower than the wall clip's 6.5 mm: the boards are 1/4" maple ply, 0.203"
(5.16 mm) per Lowe's and 5.3-5.4 mm on his caliper, so 6.5 left a millimetre of slop (2026-11-07).

Test print 1 (2026-11-07) had a 28.5 mm plug and didn't fit: it was sized off a misread caliper
photo. The hole was re-measured with the jaw tips spread inside it: 23.9 mm at the IN line.

Dropping the cross arm leaves the plug's two side corners hanging past the 26 mm arm. The plug
square therefore runs up through the body to the front face (the two small "ears"), so every part
of the plug has body under it in the print and nothing overhangs.

Frames: CAD frame = use frame. z up, z = 0 on the crate floor (the body's back face), channel
along x, plug below z = 0. Print orientation is the wall clip's: channel face down on the bed,
plug up (`*_print.stl`). The only span over air is the channel ceiling, 5.9 mm across.

Run: ~/.venvs/cad/bin/python crate_floor_insert.py
"""
import math
from pathlib import Path
from build123d import Axis, Box, Pos, Rot, chamfer, export_step, export_stl

HERE = Path(__file__).resolve().parent
NAME = "crate-floor-insert"

# --- parameters (mm) ---------------------------------------------------------------------
HOLE = 23.9         # floor hole across flats: tips spread inside the hole, IN line (2026-11-07)
PLUG = 23.4         # plug across flats: 0.25 mm a side under HOLE (wall clip's plug: 29.65)
PLUG_H = 6.0        # same plug depth as the wall clip
TIP_CHAMFER = 0.6   # lead-in on the plug tip
ARM_W = 26.0        # wall clip arm width
ARM_L = 50.0        # wall clip arm length; its ends land on the floor past the hole's corners
BODY_T = 9.0        # wall clip body thickness, back face to channel face
SLOT_W = 5.9        # board 5.16-5.4 mm + poly; PLA slots print ~0.1-0.2 under, so ~0.2-0.5 total play
SLOT_D = 6.0        # wall clip channel depth
BASE = BODY_T - SLOT_D   # 3.0: the panel sits this far above the crate floor
LEAD = 0.6          # lead-in on the channel mouth so the panel drops in
BOARD_T = 5.3       # 1/4" maple ply: 0.203" listed, 5.3-5.4 measured; fit numbers only
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
    mp = trimesh.load(stl_print, force="mesh")
    z = mp.vertices[:, 2]
    out["print min z / max z"] = (round(float(z.min()), 3), round(float(z.max()), 3))
    out["plug across flats / corner to corner"] = (PLUG, round(2 * CORNER, 2))
    out["plug clearance per side"] = round((HOLE - PLUG) / 2, 3)
    out["arm past the hole corner (each end)"] = round(ARM_L / 2 - HOLE_CORNER, 2)
    # back-face area that rests on the floor: arm minus the diamond hole (ears sit over the hole)
    tri = max(0.0, HOLE_CORNER - ARM_W / 2) ** 2          # each hole corner beyond the arm's sides
    out["landing area on floor (mm2)"] = round(ARM_L * ARM_W - (HOLE ** 2 - 2 * tri), 1)
    out["ear past arm side (each)"] = round(CORNER - ARM_W / 2, 2)
    out["panel rise (mm / in)"] = (BASE, round(BASE / 25.4, 3))
    out["board play per side in channel"] = round((SLOT_W - BOARD_T) / 2, 3)
    out["volume cm3"] = round(info["volume_cm3"], 2)
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
        print(f"{k:40s} {v}")
    for n in info["notes"]:
        print("NOTE", n)
