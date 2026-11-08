"""Product-style renders of the crate wall clip (Blender 3.5, Cycles).
Run: PART_DIR=<this folder> Blender -b -P render_floor_insert.py -- <out_dir> <samples> <shot,shot,...>
Shots: inuse (insert in a floor hole holding a panel stub), top, under (flipped, plug up).
Numbers come from crate_wall_clip.py so the context pieces line up with the part."""
import bpy, sys, math, os
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
OUT, SAMPLES, SHOTS = argv[0], int(argv[1]), argv[2].split(",")
HERE = os.environ.get("PART_DIR") or os.path.dirname(os.path.abspath(__file__))
P = type("P", (), {})()
src = open(os.path.join(HERE, "crate_wall_clip.py")).read().split("def build():")[0]
src = "\n".join(l for l in src.splitlines() if not l.startswith("from build123d"))
ns = {"__file__": os.path.join(HERE, "crate_wall_clip.py")}
exec(src, ns)                              # parameters only (Blender has no build123d)
P.__dict__.update(ns)
P.HOLE = getattr(P, "HOLE", P.PLUG + 0.5)      # render only: wall holes aren't modelled
P.BASE = getattr(P, "BASE", P.BODY_T - P.SLOT_D)
S = 0.001                                  # mm -> m
STL = os.path.join(HERE, "crate-wall-clip.stl")


def mat(name, color, metallic=0.0, rough=0.5, spec=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough; b.inputs["Specular"].default_value = spec
    return m


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        prefs.compute_device_type = "METAL"; prefs.get_devices()
        for d in prefs.devices: d.use = True
        sc.cycles.device = "GPU"
    except Exception:
        sc.cycles.device = "CPU"
    sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "Filmic"; sc.view_settings.look = "Medium Contrast"
    sc.view_settings.exposure = float(os.environ.get("EXPOSURE", "0"))
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.82, 0.83, 0.85, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = float(os.environ.get("WORLD", "0.35"))
    return sc


def box(name, size, center, m, rot_z=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object; o.name = name
    o.scale = Vector(size) * S; o.location = Vector(center) * S; o.rotation_euler = (0, 0, rot_z)
    if m is not None:
        o.data.materials.append(m)
    return o


def part(loc=(0, 0, 0), rot=(0, 0, 0)):
    m = mat("pla", tuple(float(x) for x in os.environ.get("COLOR", "0.16,0.165,0.17").split(",")),
            rough=0.55, spec=0.35)
    bpy.ops.import_mesh.stl(filepath=STL, global_scale=S)
    o = bpy.context.selected_objects[0]
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth(); o.data.use_auto_smooth = True; o.data.auto_smooth_angle = math.radians(30)
    o.rotation_euler = rot; o.location = Vector(loc) * S
    return o


FLOOR_T = 8.0   # illustrative crate-floor thickness (unmeasured); deep enough to hide the plug


def context():
    """A slab of crate floor with one square hole turned like the plug, and a panel stub."""
    slab = box("floor", (120, 120, FLOOR_T), (0, 0, -FLOOR_T / 2), mat("crate", (0.025, 0.025, 0.028), rough=0.6, spec=0.3))
    cutter = box("hole", (P.HOLE, P.HOLE, FLOOR_T + 4), (0, 0, -FLOOR_T / 2), None, math.radians(45))
    cutter.hide_render = True; cutter.display_type = "WIRE"
    mod = slab.modifiers.new("hole", "BOOLEAN"); mod.operation = "DIFFERENCE"; mod.object = cutter
    box("panel", (80, P.BOARD_T, 38), (0, 0, P.BASE + 19), mat("ply", (0.62, 0.45, 0.26), rough=0.7, spec=0.25))


def ground(z=0.0):
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, z))
    bpy.context.active_object.data.materials.append(mat("ground", (0.72, 0.73, 0.75), rough=0.9, spec=0.2))


def lights(aim):
    centre = bpy.data.objects.new("centre", None); bpy.context.scene.collection.objects.link(centre)
    centre.location = aim
    def light(name, loc, power, size, color=(1, 1, 1)):
        d = bpy.data.lights.new(name, "AREA"); d.energy = power; d.size = size; d.color = color
        o = bpy.data.objects.new(name, d); bpy.context.scene.collection.objects.link(o); o.location = loc
        t = o.constraints.new("TRACK_TO"); t.target = centre; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    k = float(os.environ.get("KEY", "6"))
    light("key", (0.30, -0.40, 0.50), k, 0.5, (1.0, 0.97, 0.93))
    light("fill", (-0.45, -0.20, 0.25), k * 0.35, 0.6, (0.92, 0.95, 1.0))
    light("rim", (-0.10, 0.50, 0.40), k * 0.8, 0.35)


def shoot(name, cam_loc, target, lens, res):
    sc = bpy.context.scene
    tgt = bpy.data.objects.new("tgt_" + name, None); sc.collection.objects.link(tgt); tgt.location = target
    cd = bpy.data.cameras.new("cam_" + name); cd.lens = lens
    cam = bpy.data.objects.new("cam_" + name, cd); sc.collection.objects.link(cam); cam.location = cam_loc
    t = cam.constraints.new("TRACK_TO"); t.target = tgt; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    sc.camera = cam; sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = int(os.environ.get("PCT", "100"))
    sc.render.filepath = os.path.join(OUT, name + ".png"); bpy.ops.render.render(write_still=True)
    print("rendered", sc.render.filepath)


for shot in SHOTS:
    reset()
    if shot == "inuse":
        part(); context(); ground(-FLOOR_T * S - 0.0001); lights((0, 0, 0.01))
        shoot("wall-clip-in-use", (0.135, -0.19, 0.125), (0, 0, 0.008), 85, (1600, 1200))
    elif shot == "top":
        lift = P.PLUG_H + 0.05                         # standing on its plug tip
        part((0, 0, lift)); ground(0); lights((0, 0, 0.01))
        shoot("wall-clip-top", (0.11, -0.15, 0.125), (0, 0, (lift + 3) * S), 100, (1500, 1500))
    elif shot == "under":
        lift = P.BODY_T + 0.05                         # flipped onto its channel face, plug up
        part((0, 0, lift), (math.radians(180), 0, 0)); ground(0); lights((0, 0, 0.01))
        shoot("wall-clip-underside", (0.11, -0.15, 0.13), (0, 0, (lift - 2) * S), 100, (1500, 1500))
