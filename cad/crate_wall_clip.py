"""WALL clip for the Juggernaut 24 qt milk crates, rebuilt parametrically.

It is milk-crate-divider-wvmodified2.stl with one change, (2026-11-07): the channel is
5.9 mm wide instead of 6.5. 5.9 is the width that fit his 1/4" maple ply "perfectly" in the floor
insert's test print 2. The boards are 0.203" (5.16 mm) listed and 5.3-5.4 mm on his caliper, so the
6.5 mm channel left about a millimetre of slop.

Everything else is wvmodified2's, measured from its STL on 2026-11-07:
  - a cross of two 26 x 50 mm arms, 9 mm thick;
  - a cross-shaped channel 6 mm deep, open at the front and at every arm end, with its floor
    3 mm off the wall and a ~0.8 mm lead-in at the mouth;
  - the outer edges rounded ~0.8 mm on the wall side and ~0.6 on the channel side;
  - a square plug 29.65 mm across the flats, 6 mm deep, turned 45 deg so its corners point along
    the channels. It fits the wall holes.
wvmodified2's plug and channels sat ~0.4 mm off the centre of its outline (a hand edit in
Vectorworks). Here everything is concentric.

Frames: CAD frame = use frame. z = 0 on the crate wall (the body's back face), z up into the crate,
channels along x and y, plug below z = 0. Print orientation is wvmodified2's: channel face down on
the bed, plug up (`*_print.stl`). Slice with `--set bridge_angle=45` so the cross-shaped channel
ceiling bridges diagonally (README).

Run: ~/.venvs/cad/bin/python crate_wall_clip.py
"""
from pathlib import Path
from build123d import Axis, Box, Pos, Rot, chamfer, export_step, export_stl

HERE = Path(__file__).resolve().parent
NAME = "crate-wall-clip"

# --- parameters (mm) ---------------------------------------------------------------------------
PLUG = 29.65        # wvmodified2's plug across flats (from its face planes): fits the wall holes
PLUG_H = 6.0        # wvmodified2's plug depth
TIP_CHAMFER = 0.6   # lead-in on the plug tip (the floor insert's, which went in tight but fine)
ARM_W = 26.0        # wvmodified2's arm width
ARM_L = 50.0        # wvmodified2's arm length (overall 50 x 50)
BODY_T = 9.0        # wvmodified2's body thickness
SLOT_W = 5.9        # was 6.5; 5.9 fit the maple ply perfectly in floor insert test 2
SLOT_D = 6.0        # wvmodified2's channel depth; its floor sits 3 mm off the wall
LEAD = 0.8          # wvmodified2's mouth lead-in (8.1 wide at the face, 6.5 by 0.9 deep)
BACK_EDGE = 0.8     # wvmodified2 rounds its wall-side outer edges ~0.8
FRONT_EDGE = 0.6    # ... and its channel-side outer edges (its face section is ~134 mm2 smaller)
BOARD_T = 5.3       # 1/4" maple ply, for the fit numbers only


def build(slot_w=SLOT_W):
    arms = (Pos(0, 0, BODY_T / 2) * Box(ARM_L, ARM_W, BODY_T)
            + Pos(0, 0, BODY_T / 2) * Box(ARM_W, ARM_L, BODY_T))
    plug = Pos(0, 0, -PLUG_H / 2 + 0.25) * Rot(0, 0, 45) * Box(PLUG, PLUG, PLUG_H + 0.5)
    part = arms + plug
    zc = BODY_T - SLOT_D / 2 + 0.5
    part -= Pos(0, 0, zc) * Box(ARM_L + 10, slot_w, SLOT_D + 1)
    part -= Pos(0, 0, zc) * Box(slot_w, ARM_L + 10, SLOT_D + 1)
    notes = []

    def try_chamfer(p, edges, size, label):
        if not edges:
            notes.append(f"chamfer '{label}': no edges found")
            return p
        try:
            return chamfer(edges, size)
        except Exception as e:  # cosmetic chamfers sometimes fail in OCC; keep building
            notes.append(f"chamfer '{label}' skipped: {e}")
            return p

    ex, ey = part.edges().filter_by(Axis.X), part.edges().filter_by(Axis.Y)
    mouth = ([e for e in ex if abs(e.center().Z - BODY_T) < 1e-3 and abs(abs(e.center().Y) - slot_w / 2) < 1e-3]
             + [e for e in ey if abs(e.center().Z - BODY_T) < 1e-3 and abs(abs(e.center().X) - slot_w / 2) < 1e-3])
    part = try_chamfer(part, mouth, LEAD, "channel mouth")
    ex, ey = part.edges().filter_by(Axis.X), part.edges().filter_by(Axis.Y)
    outer = (ARM_L / 2, ARM_W / 2)
    back = ([e for e in ex if abs(e.center().Z) < 1e-3 and min(abs(abs(e.center().Y) - v) for v in outer) < 1e-3]
            + [e for e in ey if abs(e.center().Z) < 1e-3 and min(abs(abs(e.center().X) - v) for v in outer) < 1e-3])
    part = try_chamfer(part, back, BACK_EDGE, "back edges")
    ex, ey = part.edges().filter_by(Axis.X), part.edges().filter_by(Axis.Y)
    front = ([e for e in ex if abs(e.center().Z - BODY_T) < 1e-3 and min(abs(abs(e.center().Y) - v) for v in outer) < 1e-3]
             + [e for e in ey if abs(e.center().Z - BODY_T) < 1e-3 and min(abs(abs(e.center().X) - v) for v in outer) < 1e-3])
    part = try_chamfer(part, front, FRONT_EDGE, "front edges")
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
    out["print min z / max z"] = (round(float(mp.vertices[:, 2].min()), 3), round(float(mp.vertices[:, 2].max()), 3))
    # channel width read back from the mesh, halfway down the channel, near an arm end
    s = m.section(plane_origin=(0, 0, BODY_T - SLOT_D / 2), plane_normal=(0, 0, 1))
    pts = np.vstack([np.asarray(d) for d in s.discrete])
    ys = pts[(pts[:, 0] > 20) & (pts[:, 0] < 24), 1]
    inner = np.unique(np.round(ys[np.abs(ys) < 6], 3))
    out["channel walls (y) read back"] = tuple(inner.tolist())
    out["board play per side"] = round((SLOT_W - BOARD_T) / 2, 3)
    out["plug across flats / corner to corner"] = (PLUG, round(PLUG * 2 ** 0.5, 2))
    out["volume cm3"] = round(info["volume_cm3"], 2)
    return out


if __name__ == "__main__":
    part, info = build()
    stl = HERE / f"{NAME}.stl"
    stl_print = HERE / f"{NAME}_print.stl"
    export_step(part, str(HERE / f"{NAME}.step"))
    export_stl(part, str(stl), tolerance=0.01, angular_tolerance=0.1)
    export_stl(Pos(0, 0, BODY_T) * Rot(180, 0, 0) * part, str(stl_print), tolerance=0.01, angular_tolerance=0.1)
    for k, v in checks(info, stl, stl_print).items():
        print(f"{k:40s} {v}")
    for n in info["notes"]:
        print("NOTE", n)
