"""
Mini v2.3 watering system - pump, reservoir, drip line.

Smart planter features:
- 12V peristaltic pump (moves water from reservoir to bed soil)
- 5-gallon bucket reservoir (18.9 L)
- Vinyl drip line with pressure-compensating emitter
- 1-channel relay module (ESP32 GPIO 5 controls pump on/off)
- Soil moisture sensor (V1.2 capacitive) in bed
- 3 DS18B20 temp sensors (panel, soil, battery) on 1-Wire bus

The pump sits on the workbench next to the bed. A vinyl tube runs from
the pump outlet to a drip emitter stuck in the bed's soil. ESPHome
firmware reads soil moisture and auto-waters when below threshold.

Design rules (enforced):
  1. NO MITER CUTS - all shapes are stock cylinders/boxes
  2. ALL HARDWARE OFF THE SHELF - 12V pump, 1-ch relay, vinyl tubing
  3. SIMPLE COMMON DIMENSIONS - 5-gallon bucket is standard

Coordinates (relative to bed center at origin):
  - Pump: sits to the right of the bed (positive X), on the workbench
  - Reservoir: sits behind the pump (positive X, lower Z than bed)
  - Drip line: runs from pump outlet to bed soil surface
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wattplot_params import MINI
from models.freecad.parts._helpers import box, cylinder, add_feature

import FreeCAD as App
import Part


# Bed reference (matches bed_wall.py)
BED_L = MINI["bed_outer_L_in"]   # 18
BED_W = MINI["bed_outer_W_in"]   # 14


def make_pump(doc, name="Mini_Pump"):
    """12V peristaltic pump - small block representing the pump body.

    Typical peristaltic pump: ~3" x 3" x 2" with 1/4" tubing inlet/outlet.
    Positioned next to the bed on the workbench.
    """
    # Pump body: 3" x 2" x 3" block
    pump = box(3.0, 2.0, 3.0, x=12.0, y=2.0, z=-8.0)
    # Inlet/outlet nozzles: 0.25" diameter cylinders sticking out
    inlet = cylinder(0.125, 0.5, x=10.5, y=2.5, z=-8.0, axis="X")
    outlet = cylinder(0.125, 0.5, x=13.5, y=2.5, z=-8.0, axis="X")
    # Wire pigtail: small black box on top
    wires = box(0.5, 0.3, 1.0, x=12.0, y=3.1, z=-7.0)
    compound = Part.makeCompound([pump, inlet, outlet, wires])
    return add_feature(doc, name, compound)


def make_reservoir(doc, name="Mini_Reservoir"):
    """5-gallon bucket reservoir (18.9 L) - cylinder with lid.

    Positioned behind the pump (further +X, lower Z than bed).
    """
    # Bucket: 12" diameter x 14" tall cylinder
    bucket = cylinder(6.0, 14.0, x=18.0, y=7.0, z=-10.0, axis="Y")
    # Lid: slightly larger disc on top
    lid = cylinder(6.2, 0.3, x=18.0, y=14.1, z=-10.0, axis="Y")
    # Water level indicator (a line on the side, represented as a small box)
    water_line = box(0.1, 8.0, 12.0, x=11.9, y=4.0, z=-10.0)
    compound = Part.makeCompound([bucket, lid, water_line])
    return add_feature(doc, name, compound)


def make_drip_line(doc, name="Mini_DripLine"):
    """1/4" vinyl drip line from pump to bed soil surface.

    Runs from pump outlet (x=13.5, y=2.5, z=-8) to soil surface at
    bed center (x=0, y=4.75, z=0). 1/4" OD vinyl tubing.
    """
    # Tube: 1/4" diameter cylinder from pump to bed
    tube_radius = 0.125
    # Path: pump outlet -> curve over bed wall -> drip into soil
    # Use a series of short cylinders to approximate a curved path
    segments = []
    # Segment 1: pump outlet to bed edge (horizontal)
    seg1 = cylinder(tube_radius, 6.0, x=10.5, y=2.5, z=-7.0, axis="X")
    segments.append(seg1)
    # Segment 2: vertical drop down to soil
    seg2 = cylinder(tube_radius, 2.0, x=4.5, y=3.5, z=-7.0, axis="Y")
    segments.append(seg2)
    # Segment 3: horizontal into bed center
    seg3 = cylinder(tube_radius, 4.5, x=4.5, y=2.5, z=-5.0, axis="X")
    segments.append(seg3)
    # Drip emitter at the end (small cylinder on the soil surface)
    emitter = cylinder(0.15, 0.4, x=2.0, y=2.3, z=-5.0, axis="Y")
    segments.append(emitter)
    compound = Part.makeCompound(segments)
    return add_feature(doc, name, compound)


def make_relay(doc, name="Mini_Relay"):
    """1-channel 5V relay module - small block on the bed wall.

    The relay is mounted on the bed's east short wall, near the
    breadboard. ESP32 GPIO 5 controls the relay coil, which switches
    12V power to the pump.
    """
    # Relay module: 1.5" x 0.7" x 0.5" PCB
    relay = box(1.5, 0.7, 0.5, x=9.5, y=3.0, z=7.25)
    # Terminal block (small green block on one end)
    terminal = box(0.3, 0.5, 0.3, x=8.85, y=3.0, z=7.25)
    # LED indicator (small red cylinder on top)
    led = cylinder(0.05, 0.1, x=9.5, y=3.4, z=7.25, axis="Y")
    compound = Part.makeCompound([relay, terminal, led])
    return add_feature(doc, name, compound)


def make_watering_assembly(doc, name="Mini_WateringAssembly"):
    """All watering parts combined."""
    pump = make_pump(doc, "Mini_Pump")
    reservoir = make_reservoir(doc, "Mini_Reservoir")
    drip = make_drip_line(doc, "Mini_DripLine")
    relay = make_relay(doc, "Mini_Relay")
    compound = Part.makeCompound([pump.Shape, reservoir.Shape,
                                  drip.Shape, relay.Shape])
    return add_feature(doc, name, compound), [pump, reservoir, drip, relay]
