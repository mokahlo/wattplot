"""
Mini v2.2 actuator mount - KICKSTAND design with 100mm/70N actuator.

A 100mm (3.94") stroke 12V 70N (15.7 lbf) linear actuator in compression,
mounted on the SOUTH (low) side of the bed:
  - Bottom end: fixed bracket on the bed's south wall, low position
  - Top end: moving bracket on the panel's underside, ~2" from south edge
  - Tilt range: 0-35 degrees

When the actuator extends, it pushes the panel up (rotating about the south
hinge). When it retracts, the panel falls back to flat (gravity returns it).

Force analysis (for the 1.88 lb ECO-WORTHY 10W panel):
  - Gravity torque: 1.88 lb * 4" COM = 7.52 in-lb
  - Required actuator force at 0 deg: ~5.1 lbf
  - Actuator capacity: 15.7 lbf (3x headroom)
  - Stroke needed for 35 deg: 0.72" (vs 3.94" available, 5.5x headroom)

The actuator is way overkill for this panel - it could lift a much heavier
panel if scaled up. For v2.2, we're using the actuator the user already
ordered, so the design accommodates it with tons of margin.

Design rules (enforced):
  1. NO MITER CUTS - blocks are simple rectangles, all square cuts
  2. ALL HARDWARE OFF THE SHELF - 1x2 PT DF, 3/8" steel pin, 100mm actuator
  3. SIMPLE COMMON DIMENSIONS - 1x2 scraps from the rails/skids boards
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wattplot_params import MINI
from models.freecad.parts._helpers import box, add_feature

import FreeCAD as App
import Part


# Bed/frame Y positions (matches frame.py)
WALL_T = MINI["bed_wall_thk_in"]                # 0.75
WALL_H = MINI["bed_wall_h_in"]                  # 3.5
SKID_H = MINI["skid_h_in"]                      # 0.75 (1x2)
RAIL_T = MINI["long_rail_thk_in"]               # 0.75 (1x2)
RAIL_H = MINI["long_rail_h_in"]                 # 1.5

PANEL_W = MINI["panel_W_in"]                    # 8.1
PANEL_T = MINI["panel_t_in"]                    # 0.7
BED_L = MINI["bed_outer_L_in"]                  # 18
BED_W = MINI["bed_outer_W_in"]                  # 14
PANEL_L = MINI["panel_L_in"]                    # 13.3
PANEL_Y_BOTTOM = SKID_H + WALL_H + 0.5         # 4.75 (panel underside at 0 tilt)
PANEL_Y_TOP = PANEL_Y_BOTTOM + PANEL_T          # 5.45

# Hinge axis: at the top of the south wall, outer face
HINGE_Y = SKID_H + WALL_H                       # 4.25
HINGE_Z = +BED_W / 2.0                          # 7.0 (outer face of south wall)

# Kickstand geometry
ACT_STROKE = MINI["actuator_stroke_in"]         # 3.94 (100mm)
ACT_FORCE = MINI["actuator_rated_force_lb"]     # 15.7 (70N)
TOP_OFFSET = MINI["kickstand_top_mount_offset_in"]  # 2.0 (north of hinge on panel)

# Bottom mount: 1x2 block on the bed's south wall, at the outer face, low
#   Position: y=0 to 0.75 (from ground to top of skid), z=+7 to +7.75
BOTTOM_BLOCK_T = 0.75
BOTTOM_BLOCK_H = 0.75
BOTTOM_BLOCK_L = 3.0    # 3" wide along X (shorter for the small bed)

# Top mount: 1x2 block hanging from the panel's underside
#   Position: y=4.0 to 4.75 (just below panel), z=+4.625 to +5.375 (centered at +5.0)
TOP_BLOCK_T = 0.75
TOP_BLOCK_H = 0.75
TOP_BLOCK_L = 3.0

# Pin positions
#   Bottom pin: at the top-outer corner of the bottom block, along X axis
#   Top pin: at the top-south corner of the top block (just below panel), along X axis
BOTTOM_PIN_Y = BOTTOM_BLOCK_H                  # 0.75
BOTTOM_PIN_Z = HINGE_Z + BOTTOM_BLOCK_T         # 7.75
TOP_PIN_Y = PANEL_Y_BOTTOM                      # 4.75
TOP_PIN_Z = HINGE_Z - TOP_OFFSET                # 5.0

# Actuator body dimensions
ACT_BODY_DIA = 0.75    # ~3/4" diameter cylinder
ACT_ROD_DIA = 0.375    # 3/8" rod

# Pin dimensions
PIN_DIA = 0.375        # 3/8" steel pin (matches the hinge pin)
PIN_LEN = 3.5          # 3.5" long (sticks out 0.25" each side of block)

# Vector from bottom pin to top pin (the actuator's axis)
ACT_BOTTOM = App.Vector(0, BOTTOM_PIN_Y, BOTTOM_PIN_Z)
ACT_TOP_0 = App.Vector(0, TOP_PIN_Y, TOP_PIN_Z)
ACT_AXIS = ACT_TOP_0 - ACT_BOTTOM
ACT_LEN_COLLAPSED = ACT_AXIS.Length


def _make_cylinder_between(p1, p2, radius):
    """Make a cylinder of given radius from p1 to p2."""
    axis = p2 - p1
    length = axis.Length
    if length < 1e-9:
        return None
    unit = App.Vector(axis.x / length, axis.y / length, axis.z / length)
    return Part.makeCylinder(radius, length, p1, unit)


def make_actuator_mount(doc, name="Mini_ActuatorMount"):
    """Bottom mount block + top mount bracket + actuator body + pins.

    Geometry (at 0 deg panel tilt, viewed from +X looking in -X):
                       TOP (panel, z=5)
                        |
                        | actuator body
                        |
                       BOT (bed south wall, z=7.75)
    """
    parts = []

    # Bottom mount block: 1x2 on bed's south wall, low
    # Position: x=-1.5 to 1.5, y=0 to 0.75, z=+7 to +7.75
    bottom_block = box(BOTTOM_BLOCK_L, BOTTOM_BLOCK_H, BOTTOM_BLOCK_T,
                       x=-BOTTOM_BLOCK_L / 2.0, y=0, z=HINGE_Z)
    parts.append(bottom_block)

    # Top mount bracket: 1x2 hanging below the panel
    # Position: x=-1.5 to 1.5, y=4.0 to 4.75, z=+4.625 to +5.375
    top_block = box(TOP_BLOCK_L, TOP_BLOCK_H, TOP_BLOCK_T,
                    x=-TOP_BLOCK_L / 2.0, y=TOP_PIN_Y - TOP_BLOCK_H,
                    z=TOP_PIN_Z - TOP_BLOCK_T / 2.0)
    parts.append(top_block)

    # Bottom pin: along X axis, at (y=0.75, z=7.75), length 3.5"
    bottom_pin = Part.makeCylinder(PIN_DIA / 2.0, PIN_LEN,
                                    App.Vector(-PIN_LEN / 2.0, BOTTOM_PIN_Y, BOTTOM_PIN_Z),
                                    App.Vector(1, 0, 0))
    parts.append(bottom_pin)

    # Top pin: along X axis, at (y=4.75, z=5.0), length 3.5"
    top_pin = Part.makeCylinder(PIN_DIA / 2.0, PIN_LEN,
                                 App.Vector(-PIN_LEN / 2.0, TOP_PIN_Y, TOP_PIN_Z),
                                 App.Vector(1, 0, 0))
    parts.append(top_pin)

    # Actuator body: cylinder from bottom pin to top pin
    actuator_body = _make_cylinder_between(ACT_BOTTOM, ACT_TOP_0, ACT_BODY_DIA / 2.0)
    if actuator_body is not None:
        parts.append(actuator_body)

    # Inner rod: smaller cylinder from top pin going down 80% of the way
    rod_end = ACT_TOP_0 - (ACT_TOP_0 - ACT_BOTTOM) * 0.8
    actuator_rod = _make_cylinder_between(ACT_TOP_0, rod_end, ACT_ROD_DIA / 2.0)
    if actuator_rod is not None:
        parts.append(actuator_rod)

    compound = Part.makeCompound(parts)
    return add_feature(doc, name, compound), parts


if __name__ == "__main__":
    doc = App.newDocument("test_actuator_v22")
    am, parts = make_actuator_mount(doc)
    doc.recompute()
    bb = am.Shape.BoundBox
    print(f"  Actuator mount: vol={am.Shape.Volume:.1f} in^3, "
          f"X=[{bb.XMin:.1f},{bb.XMax:.1f}], "
          f"Y=[{bb.YMin:.1f},{bb.YMax:.1f}], "
          f"Z=[{bb.ZMin:.1f},{bb.ZMax:.1f}]")
    print(f"  Actuator collapsed length: {ACT_LEN_COLLAPSED:.2f}\"")
    print(f"  Bottom pin: y={BOTTOM_PIN_Y}, z={BOTTOM_PIN_Z}")
    print(f"  Top pin (0 deg): y={TOP_PIN_Y}, z={TOP_PIN_Z}")
