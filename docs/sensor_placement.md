# Wattplot v2 — Sensor Placement

Where each sensor mounts on the apparatus, why that location, and how to
route its cable. Reference the **side view** at the end of this doc.

---

## 1. BMI160 IMU (panel tilt feedback)

**Mount location:** Centered on the **underside of the panel frame's NORTH
rail** (the 2x6 PT clevis that the actuator pushes). Specifically:
screwed to the inside face of the north rail, with the IMU's X axis aligned
along the bed's long axis (east-west) and the Z axis pointing up (panel
normal).

**Why the north rail, not on the panel itself:**
- The frame is the structural member; the IMU is the structural reference.
- The panel sits inside the frame with some compliance; measuring the
  frame is more accurate.
- The IMU is closer to the actuator, where the actual tilt movement is
  being applied. Less slop.
- The cable to the IMU runs through the cable carrier with the actuator
  cable, no extra routing.

**Why the underside (not the topside):**
- Weather protection: the panel frame's top side is exposed to rain and
  UV. Underside is sheltered.
- The IMU's Z axis (up) needs to point in the panel normal direction.
  Mounting on the underside means the IMU's "up" matches the panel's "up"
  when the IMU is right-side-up (Z+ out of the chip).
- The IMU faces DOWN, so the +Z direction (panel up) is opposite of the
  IMU's +Z. The firmware needs to invert the Z reading (or mount the IMU
  Z+ up — depends on chip orientation, check the BMI160 datasheet).

**Orientation:** IMU X axis = bed long axis (east-west). IMU Y axis = bed
short axis (north-south). IMU Z axis = panel normal (up when panel is flat).

**Mounting:** 2× #4 wood screws through the IMU breakout board's
mounting holes, into the underside of the north rail. Use a small
adhesive foam pad between the IMU and the wood to dampen vibration.

**Cable:** 4-wire I2C (3V3, GND, SDA, SCL) through the cable carrier to
the PCB. ~36" total length.

---

## 2. INA219 current/power sensor (motor current feedback)

**Mount location:** Inside the PCB enclosure, **on the high side of the
actuator's motor lead**. The INA219 measures the current going TO the
actuator, so it goes in series with the motor wire.

**Why inside the enclosure (not at the actuator):**
- The enclosure is already weatherproof.
- The INA219 is connected to the I2C bus; keeping it close to the ESP32
  keeps the I2C wires short.
- The actuator wire enters the enclosure through a cable gland, connects
  to the INA219, then exits to the actuator. Net: 6" of wire between
  enclosure and actuator.

**Wiring:** The INA219 has 4 screw terminals: VCC, GND, SDA, SCL (for
I2C), and 2 high-side terminals (VIN+ and VIN−). The actuator motor wire
goes: PCB J6 → INA219 VIN+ → INA219 VIN− → actuator lead A. The other
motor lead (B) goes from PCB J6 directly to actuator lead B.

**Cable:** 2-wire I2C (SDA, SCL) from INA219 to ESP32 (4" inside the
enclosure). 2-wire motor (red/black) from INA219 to actuator (~46" total
length, through cable carrier).

---

## 3. DS18B20 soil temperature sensor

**Mount location:** **6" deep in the bed soil**, 12" from the south wall,
centered between the east and west walls.

**Why 6" deep:**
- This is the root zone for tomato plants. Soil temperature at root depth
  affects germination, growth, and yield.
- 6" is below the surface heating zone (the top 1-2" swings 20°F
  between day and night, the 6" zone is more stable).
- Above the deepest root zone (tomato roots go to 18-24" but the active
  root mass is 6-12").

**Why 12" from the south wall (not the center):**
- The south wall is the warmest wall (faces the sun when the panel is
  tilted). Placing the sensor near the south wall gives a "warm zone"
  reading. (For an average reading, center the sensor.)
- The frame's south rail is at the south wall, so the wall is partially
  shaded. This is a representative spot.

**Mounting:** Stainless steel probe (DS18B20 in a waterproof stainless
housing, ~6mm diameter). Insert into the soil so the probe tip is at 6"
depth. The cable exits the soil near the south wall and routes through
a grommet in the south wall, into the cable carrier, to the PCB.

**Cable:** 3-wire (data, 3V3, GND), 26 AWG, ~30" total length.

---

## 4. Capacitive soil moisture sensor

**Mount location:** **4" deep in the bed soil**, 18" from the south wall,
centered between the east and west walls.

**Why 4" deep:**
- Different from the temperature sensor (which is 6" deep) on purpose.
  This gives a vertical profile of the soil (one temp at 6", one moisture
  at 4").
- 4" is the active root zone for seedlings and shallow-rooted plants.

**Why 18" from the south wall:**
- Different from the temperature sensor (12" from south). Gives a
  horizontal profile: temp is 12" south, moisture is 18" south.

**Why capacitive (not resistive):**
- Capacitive sensors don't corrode in moist soil (resistive sensors do).
- Capacitive sensors measure dielectric permittivity, which correlates
  well with volumetric water content.
- Capacitive sensors need AC excitation (the sensor IC handles this).

**Mounting:** Capacitive sensor v1.2 (or similar) inserted into the soil
with the tip at 4" depth. The PCB (the sensor's own small PCB) is above
the soil line, with the cable exiting upward. Hot-glue or epoxy the
cable entry to seal against moisture intrusion into the sensor's own PCB.

**Cable:** 2-wire (signal, GND), 26 AWG, ~30" total length.

---

## 5. Battery voltage sense (10k/10k divider)

**Mount location:** **ON the PCB**, not external. The divider resistors
(R1 = 10 kΩ from 12V rail, R2 = 10 kΩ from divider tap to GND) are
soldered on the PCB near the 12V input. The tap goes to GPIO33.

**Why on the PCB:**
- The 12V is already on the PCB (at J1). Routing the divider output
  through a separate wire to a remote divider is asking for noise pickup.
- The PCB has stable ground; the divider is referenced to PCB ground.
- Saves a cable run.

**Range:** With 10k/10k on a 12V battery, the divider output is 6V at
12V input. GPIO33 max is 3.3V. So we use a 3-resistor divider for
12V → 3.0V (10k from 12V, 10k from tap to GND, and a 33k from tap to
GPIO33 as a current limiter — no wait, that's wrong, you can't have a
3-resistor divider that way).

Let me re-think. With 12V across 10k+10k, the tap is at 6V. To bring
this down to 3V, use 10k+3.4k (10k from 12V to tap, 3.4k from tap to
GND, gives V_tap = 12 × 3.4 / 13.4 = 3.04V). Or use the original 10k+10k
and just clamp the GPIO33 input with a 3.3V Zener diode to protect
against over-voltage (the GPIO reads 3.3V when input > 3.3V, but the
Zener clamps at 3.3V — this works as long as the input current is
limited, which the 10k series resistor does at 12V: 6V across 10k = 0.6
mA, well within the Zener's rating).

Cleanest: **use a 30k + 10k divider on the PCB.** Tap = 12 × 10 / 40 =
3V. That's directly within the ESP32 ADC range. No Zener needed.

Update the PCB spec: R1 = 30kΩ (from 12V to tap), R2 = 10kΩ (from tap
to GND). The tap goes to GPIO33. This is documented in
`docs/pcb_design.md` (J10 section needs updating).

---

## 6. Limit switches (0° and 90° end-stops)

### 6a. Limit switch 0° (south wall, near hinge)

**Mount location:** On the **bed's south wall top edge**, just below the
hinge axis. Specifically: a roller switch mounted on a small wood block
attached to the south wall, with the roller positioned so the frame's
south rail presses it when the frame is at 0° (fully flat).

**Why a roller switch:**
- A roller switch activates on contact, not on a specific angle. As
  the frame tilts down to 0°, the rail presses the roller.
- Limit switches (vs. just relying on IMU for position) provide a
  hard end-stop, important for safety (the firmware can detect
  "limit switch activated but IMU says 5°" = IMU drift, recalibrate).

**Wiring:** NO (normally open) contact. 26 AWG 2-wire (signal, GND)
from the switch to the PCB's J7. The 10 kΩ pullup is **on the PCB** (not
at the switch — long wire runs benefit from PCB-side pullup).

### 6b. Limit switch 90° (frame, near vertical position)

**Mount location:** On the **frame's east or west cross rail** (the
2x6 at the east or west end of the frame), positioned so the rail
touches a fixed stop on the bed when the frame reaches 90° (vertical).

**Why on the cross rail (not on the bed):**
- The cross rail moves with the frame, so the switch moves with the
  frame. The switch is wired to the PCB via the cable carrier.
- The fixed stop is a small wood block mounted on the bed's north wall
  (or attached to the actuator mount). The switch contacts the stop at
  90°.

**Alternative:** mount the switch on the bed's north wall and have it
contact the frame's north rail at 90°. Same effect, but the wire is
fixed to the bed (no cable carrier needed). **This is the cleaner
design — let me update.**

**Updated 90° switch design:**
- Mount the 90° switch on a small wood block attached to the **bed's
  north wall**, near the actuator mount.
- The frame's north rail contacts the switch when the frame is at 90°.
- The wire is fixed to the bed (no cable carrier).

**Wiring:** 2-wire (signal, GND) from the switch to J7 on the PCB. The
J7 connector is 3-pin (signal, signal, GND), so both switches share
the GND wire.

---

## 7. WS2812B status LED

**Mount location:** **On the PCB** (or in the enclosure wall, with the
LED protruding). The LED indicates controller state:
- Solid red = NORMAL
- Solid blue = FOLDING
- Solid green = LOCKED
- Solid yellow = MONITORING
- Flashing red = error
- Off = off

**Why on the PCB:** the LED is a status indicator. Visible from outside
the enclosure (if the enclosure has a transparent window) or via a panel
mount LED extension. No need to be on the apparatus itself.

**Wiring:** 1-wire (data) with 100 Ω series resistor on the PCB. The
LED's VDD and GND come from the PCB's 3V3 and GND rails.

---

## 8. Grow light fixture

**Mount location:** **Above the panel** (the panel frame is the support
structure), pointing down at the bed. Or on a separate mast above the
bed. Or on a wire strung between two posts.

**Why above the panel (frame-supported):**
- The frame can hold the weight of a small grow light (~5-10 lb).
- The light is at a fixed distance from the bed, regardless of panel
  tilt. Simplifies light integration calculations.
- No need for a separate structure.

**Mounting:** Bolt the grow light fixture to the top of the panel
frame's east and west cross rails, with a small bracket.

**Wiring:** 2-wire (12V switched, GND) from PCB J5, through the cable
carrier, to the light. ~60" total.

---

## 9. DPS5005 MPPT controller

**Mount location:** **Inside the PCB enclosure** (or a small adjacent
enclosure). The DPS5005 is a 5A buck converter, so it generates some
heat. Mount with a small heatsink if needed.

**Wiring:** 4-wire UART to PCB J4. Power: 12V from the main battery
(jumper from J1 +) and 12V output to the battery (the DPS5005
regulates 12V battery charging). The DPS5005 is configured to output
14.4V (LiFePO4 charge voltage) — but wait, the battery is 12V (already
charged), so the DPS5005 is acting as a **trickle charger / MPPT**,
not a primary charger. The main charging comes from the solar panel
via the DPS5005, but the battery is also charged by the microinverter
during the day (in grid-tie mode).

**Updated DPS5005 role:** The DPS5005 is the **MPPT charge controller**.
The solar panel's MPPT output goes through the DPS5005, which regulates
the voltage to 14.4V for LiFePO4 charging. The DPS5005's input comes
from the solar panel (a tap from the panel's output), and its output
goes to the 12V battery.

**Wiring update:**
- DPS5005 input (high voltage side) = solar panel MPPT tap (panel's
  Voc ~40V max, well within DPS5005's 50V limit)
- DPS5005 output = 12V battery
- DPS5005 UART = PCB J4 (for monitoring/control)

This means the DPS5005 has 4 high-current wires (input +, input −,
output +, output −) and 4 signal wires (VCC, GND, TX, RX). Total 8
wires to the DPS5005.

**Where is the solar panel MPPT tap?** From the main panel's MC4
connectors, a Y-splitter or junction box routes one leg to the
microinverter (240 VAC) and the other leg to the DPS5005 (12 VDC). The
DPS5005 input is high voltage (up to 40V), so use 14 AWG wire for
this run.

---

## 10. Side view summary

```
   ↑ Y (up)
   │
40 ┤       ╱│ ←─── panel frame (tilted at 35°)
   │      ╱ │
   │     ╱  │
30 ┤    ╱   │
   │   ╱    │
   │  ╱     │
20 ┤ ╱      │
   │╱       │
   ┌───────┐│
10 ┤soil   ││ ←─── IMU on underside of north rail
   │       ││
   ├───────┤│
 0 ┤bed    ││
   │       ││
   ├───────┤│
-3 ┤skid   ││
   └───────┘└──
   Z (south ↑ north)
```

| Sensor | Mount | Cable length |
|---|---|---|
| IMU (BMI160) | Underside of frame's north rail | 36" |
| INA219 | Inside PCB enclosure (on actuator lead) | 4" internal + 46" to actuator |
| DS18B20 | 6" deep in bed soil, 12" from south wall | 30" |
| Soil moisture | 4" deep in bed soil, 18" from south wall | 30" |
| Battery sense | On PCB (no external wire) | 0" |
| Limit switch 0° | South wall, just below hinge | 80" |
| Limit switch 90° | North wall, near actuator | 60" |
| Status LED | On PCB (or enclosure wall) | 0" |
| Grow light | On top of frame, pointing down | 60" |
| DPS5005 | Inside PCB enclosure (or adjacent) | 4" internal + 30" to panel MC4 |
