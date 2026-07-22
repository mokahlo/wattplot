"""
Mini v2.4 watering system - solenoid valve on tap water.

Smart planter watering (v2.4: simplified, no pump/reservoir):
- 12V DC normally-closed solenoid valve (1/4" NPT or barb)
- Tap water provides pressure (40-80 PSI typical)
- Pressure regulator on the inlet side (optional but recommended)
- 1/4" vinyl tubing from solenoid to drip emitter
- 1-channel relay on ESP32 GPIO 5 controls solenoid
- Soil moisture sensor (V1.2 capacitive) in bed
- 3 DS18B20 temp sensors (panel, soil, battery) on 1-Wire bus

The solenoid sits near the bed (workbench or wall). A tee fitting taps
into the cold water supply line, feeds the solenoid inlet via 1/4"
tubing, and the solenoid outlet feeds the drip emitter in the bed soil.

When the soil moisture drops below threshold, ESP32 fires the relay,
energizing the solenoid for ~50 sec to deliver ~100 mL. The solenoid
is in compression when energized (water flows), and naturally closed
when de-energized (fail-safe - no flooding if power dies).

Coordinates (relative to bed center at origin):
  - Solenoid: hangs off bed's east short wall, at 1/4" tubing height
  - Tee fitting: on cold water supply pipe, typically under sink
  - Tubing: runs from tee (under sink) -> up to workbench -> to solenoid -> to bed

Design rules (enforced):
  1. NO MITER CUTS - all shapes are stock cylinders/boxes
  2. ALL HARDWARE OFF THE SHELF - solenoid, 1-ch relay, vinyl tubing
  3. SIMPLE COMMON DIMENSIONS - 1/4" tubing is standard
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


def make_solenoid(doc, name="Mini_Solenoid"):
    """12V DC normally-closed solenoid valve (small block).

    Typical 1/4" solenoid: ~2.5" x 1.5" x 1.5" with 1/4" barbs on
    each end. Mounted on the bed's east short wall, at 1/4" tubing
    height (~6" off the ground).
    """
    # Solenoid body: 2.5" x 1.5" x 1.5"
    body = box(2.5, 1.5, 1.5, x=11.0, y=6.0, z=8.0)
    # Inlet barb (1/4" OD cylinder on south side)
    inlet = cylinder(0.125, 0.5, x=10.25, y=6.5, z=8.0, axis="X")
    # Outlet barb (1/4" OD cylinder on north side)
    outlet = cylinder(0.125, 0.5, x=11.75, y=6.5, z=8.0, axis="X")
    # Wire pigtail (small black box on top)
    wires = box(0.5, 0.3, 1.0, x=11.0, y=7.0, z=8.0)
    compound = Part.makeCompound([body, inlet, outlet, wires])
    return add_feature(doc, name, compound)


def make_pressure_regulator(doc, name="Mini_PressureRegulator"):
    """Optional pressure regulator (1/4" NPT, 5-30 PSI adjustable).

    Reduces tap pressure (40-80 PSI) to a safe level for the drip
    emitter. Optional - can skip if emitter can handle full tap pressure.
    """
    # Regulator body: 2" x 1.5" x 1.5" cylinder
    body = cylinder(0.75, 2.0, x=14.0, y=6.0, z=8.0, axis="X")
    # Adjustment knob on top
    knob = cylinder(0.4, 0.3, x=14.0, y=7.0, z=8.0, axis="Y")
    # Inlet/outlet barbs
    inlet = cylinder(0.125, 0.5, x=12.75, y=6.0, z=8.0, axis="X")
    outlet = cylinder(0.125, 0.5, x=15.25, y=6.0, z=8.0, axis="X")
    compound = Part.makeCompound([body, knob, inlet, outlet])
    return add_feature(doc, name, compound)


def make_drip_line(doc, name="Mini_DripLine"):
    """1/4" vinyl drip line from solenoid to bed soil surface.

    Runs from solenoid outlet (x=11.75, y=6.5, z=8) to soil surface at
    bed center (x=0, y=4.75, z=0). 1/4" OD vinyl tubing.
    """
    tube_radius = 0.125
    # Path: solenoid outlet -> horizontal across bed -> vertical down -> drip
    # Use a series of short cylinders to approximate a curved path
    segments = []
    # Segment 1: solenoid outlet to bed east wall (horizontal, going west)
    seg1 = cylinder(tube_radius, 1.5, x=11.0, y=6.5, z=8.0, axis="X")
    segments.append(seg1)
    # Segment 2: down to bed soil surface
    seg2 = cylinder(tube_radius, 1.75, x=10.0, y=5.5, z=8.0, axis="Y")
    segments.append(seg2)
    # Segment 3: horizontal across to bed center
    seg3 = cylinder(tube_radius, 6.0, x=8.0, y=4.75, z=8.0, axis="X")
    segments.append(seg3)
    # Segment 4: down to drip emitter
    seg4 = cylinder(tube_radius, 0.5, x=2.0, y=4.5, z=8.0, axis="Y")
    segments.append(seg4)
    # Drip emitter at the end (small cylinder on the soil surface)
    emitter = cylinder(0.15, 0.3, x=2.0, y=4.3, z=8.0, axis="Y")
    segments.append(emitter)
    compound = Part.makeCompound(segments)
    return add_feature(doc, name, compound)


def make_supply_line(doc, name="Mini_SupplyLine"):
    """Tap water supply line (1/4" tubing from house plumbing to solenoid).

    Represents the long run from under the sink (or wherever the cold
    water supply is) up to the workbench level. In reality this is
    just standard 1/4" vinyl tubing, no special components.
    """
    tube_radius = 0.125
    # 6 ft long tube going up from the supply (under sink) to the workbench
    tube = cylinder(tube_radius, 72.0, x=14.0, y=-30.0, z=8.0, axis="Y")
    compound = Part.makeCompound([tube])
    return add_feature(doc, name, compound)


def make_relay(doc, name="Mini_Relay"):
    """1-channel 5V relay module - small block on the bed wall.

    The relay is mounted on the bed's east short wall, near the
    breadboard. ESP32 GPIO 5 controls the relay coil, which switches
    12V power to the solenoid.
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
    solenoid = make_solenoid(doc, "Mini_Solenoid")
    regulator = make_pressure_regulator(doc, "Mini_PressureRegulator")
    drip = make_drip_line(doc, "Mini_DripLine")
    supply = make_supply_line(doc, "Mini_SupplyLine")
    relay = make_relay(doc, "Mini_Relay")
    compound = Part.makeCompound([solenoid.Shape, regulator.Shape,
                                  drip.Shape, supply.Shape, relay.Shape])
    return add_feature(doc, name, compound), [solenoid, regulator, drip, supply, relay]
