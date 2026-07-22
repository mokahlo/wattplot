"""
Mini v2 actuator mount - KICKSTAND design.

A 4" stroke 12V 75 lbf linear actuator in compression, mounted on the
SOUTH (low) side of the bed:
  - Bottom end: fixed bracket on the bed's south wall, low position
  - Top end: moving bracket on the panel's underside, ~6" from south edge
  - Tilt range: 0-35 degrees (the power-optimal range per Phoenix sun sim)

When the actuator extends, it pushes the panel up (rotating about the south
hinge). When it retracts, the panel falls back to flat (gravity returns it).

Why kickstand (not the high-side actuator on the north rail):
  - $18 small actuator vs $90 24" stroke actuator
  - Actuator is in compression, so it can hold position without power
  - Fails safely to flat if power dies (panel just lies on the bed)
  - 0-35 deg covers the power-optimal range (35 deg = 159 kWh/yr in Phoenix)
  - Much more compact; actuator is tucked under the bed's south wall

Design rules (enforced):
  1. NO MITER CUTS - blocks are simple rectangles, all square cuts
  2. ALL HARDWARE OFF THE SHELF - 2x2 PT DF, 1/2" steel pin, 4" linear actuator
  3. SIMPLE COMMON DIMENSIONS - 2x2 from 2x2x8ft stock (12" waste)
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
SKID_H = MINI["skid_h_in"]                      # 1.5 (2x2)
RAIL_T = MINI["long_rail_thk_in"]               # 1.5 (2x2)
RAIL_H = MINI["long_rail_h_in"]                 # 1.5 (2x2)

PANEL_W = MINI["panel_W_in"]                    # 20.87
PANEL_T = MINI["panel_t_in"]                    # 1.18
BED_L = MINI["bed_outer_L_in"]                  # 40
BED_W = MINI["bed_outer_W_in"]                  # 22
PANEL_L = MINI["panel_L_in"]                    # 38.58
PANEL_Y_BOTTOM = SKID_H + WALL_H + 0.5         # 5.5 (panel underside at 0 tilt)

# Hinge axis: at the top of the south wall, outer face
HINGE_Y = SKID_H + WALL_H                       # 5.0
HINGE_Z = +BED_W / 2.0                          # 11.0 (outer face of south wall)

# Kickstand geometry
ACT_STROKE = MINI["actuator_stroke_in"]         # 4.0
ACT_FORCE = MINI["actuator_rated_force_lb"]     # 75
TOP_OFFSET = MINI["kickstand_top_mount_offset_in"]  # 6.0 (north of hinge on panel)

# Bottom mount: 2x2 block on the bed's south wall, at the outer face, low position
#   Position: y=0 to 1.5 (from ground to top of skid), z=11 to 12.5 (wall outer face)
BOTTOM_BLOCK_T = 1.5    # 2x2 actual
BOTTOM_BLOCK_H = 1.5
BOTTOM_BLOCK_L = 4.0    # 4" wide along X, centered

# Top mount: small bracket hanging from the panel's underside
#   Position: y=4.0 to 5.5 (below the panel), z=4.25 to 5.75 (centered at z=5.0)
TOP_BLOCK_T = 1.5
TOP_BLOCK_H = 1.5
TOP_BLOCK_L = 4.0

# Pin positions
#   Bottom pin: at the top-outer corner of the bottom block, along X axis
#   Top pin: at the bottom-north corner of the top block, along X axis
BOTTOM_PIN_Y = 1.5                 # top of bottom block
BOTTOM_PIN_Z = HINGE_Z + 0.75       # outer face of bottom block (=12.5)
TOP_PIN_Y = 5.5 - 1.5              # 4.0 (bottom of top block, just below panel)
TOP_PIN_Z = HINGE_Z - TOP_OFFSET   # 5.0 (north of hinge)

# Actuator body dimensions
ACT_BODY_DIA = 0.75    # ~3/4" diameter cylinder
ACT_ROD_DIA = 0.375    # 3/8" rod

# Pin dimensions
PIN_DIA = 0.5          # 1/2" steel pin
PIN_LEN = 4.5          # 4.5" long (sticks out 1.5" each side of block)

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
                       BOT (bed south wall, z=12.5)
    """
    parts = []

    # Bottom mount block: 2x2 on bed's south wall, low
    # Position: x=-2 to 2, y=0 to 1.5, z=+11 to +12.5
    bottom_block = box(BOTTOM_BLOCK_L, BOTTOM_BLOCK_H, BOTTOM_BLOCK_T,
                       x=-BOTTOM_BLOCK_L / 2.0, y=0, z=HINGE_Z)
    parts.append(bottom_block)

    # Top mount bracket: 2x2 hanging below the panel
    # Position: x=-2 to 2, y=4.0 to 5.5, z=4.25 to 5.75
    top_block = box(TOP_BLOCK_L, TOP_BLOCK_H, TOP_BLOCK_T,
                    x=-TOP_BLOCK_L / 2.0, y=TOP_PIN_Y, z=TOP_PIN_Z - TOP_BLOCK_T / 2.0)
    parts.append(top_block)

    # Bottom pin: along X axis, at (y=1.5, z=12.5), length 4.5"
    bottom_pin = Part.makeCylinder(PIN_DIA / 2.0, PIN_LEN,
                                    App.Vector(-PIN_LEN / 2.0, BOTTOM_PIN_Y, BOTTOM_PIN_Z),
                                    App.Vector(1, 0, 0))
    parts.append(bottom_pin)

    # Top pin: along X axis, at (y=4.0, z=5.0), length 4.5"
    top_pin = Part.makeCylinder(PIN_DIA / 2.0, PIN_LEN,
                                 App.Vector(-PIN_LEN / 2.0, TOP_PIN_Y, TOP_PIN_Z),
                                 App.Vector(1, 0, 0))
    parts.append(top_pin)

    # Actuator body: cylinder from bottom pin to top pin
    actuator_body = _make_cylinder_between(ACT_BOTTOM, ACT_TOP_0, ACT_BODY_DIA / 2.0)
    if actuator_body is not None:
        parts.append(actuator_body)

    # Inner rod: smaller cylinder from top pin going down 80% of the way
    # (representing the actuator's extended inner rod)
    rod_end = ACT_TOP_0 - (ACT_TOP_0 - ACT_BOTTOM) * 0.8
    actuator_rod = _make_cylinder_between(ACT_TOP_0, rod_end, ACT_ROD_DIA / 2.0)
    if actuator_rod is not None:
        parts.append(actuator_rod)

    compound = Part.makeCompound(parts)
    return add_feature(doc, name, compound), parts


if __name__ == "__main__":
    doc = App.newDocument("test_actuator_v21")
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
