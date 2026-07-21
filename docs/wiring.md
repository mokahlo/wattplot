# Wattplot v2 — Wiring Diagram

Pin-by-pin wiring from the **Wattplot Controller v1 PCB** (in its
waterproof enclosure, mounted on the bed's east short wall) to every
component on the apparatus. The PCB pin map is in `docs/pcb_design.md`.

**Wire types:** All low-voltage signal wires are 22-26 AWG stranded
(silicone-jacketed for outdoor use, e.g., EcoWire). The 12 V battery
and grow light cables are 16-14 AWG (use silicone wire for flexibility,
e.g., 14 AWG silicone from a hoverboard battery supply).

**Cable lengths** are the runs from PCB to component, with ~6" of slack
at each end for service. JST-XH connectors at the PCB side; bare wire or
ring terminals at the component side.

---

## 1. PCB header → component map

### Power (12 V battery)

| PCB header | Wire | Goes to | Notes |
|---|---|---|---|
| J1 pin 1 (+) | 12 AWG red, ~24" | Battery (+) terminal | Through 5A in-line fuse within 6" of battery |
| J1 pin 2 (−) | 12 AWG black, ~24" | Battery (−) terminal | Common ground |

### USB-C programming

| PCB header | Wire | Goes to | Notes |
|---|---|---|---|
| J3 | USB-C cable | External laptop (only for first flash) | After that, OTA updates via WiFi |

### I2C bus (BMI160 IMU, INA219, expansion)

| PCB header | Wire | Goes to | Notes |
|---|---|---|---|
| J2 pin 1 | 26 AWG red, ~36" | 3V3 rail (powers IMU + INA219) | Twisted with SDA/SCL |
| J2 pin 2 | 26 AWG black, ~36" | Common GND | |
| J2 pin 3 | 26 AWG white, ~36" | SDA — daisy-chain IMU → INA219 | I2C SDA |
| J2 pin 4 | 26 AWG green, ~36" | SCL — daisy-chain IMU → INA219 | I2C SCL |

The IMU is mounted on the panel frame (to measure actual tilt). The
INA219 is on the motor lead (to measure actuator current). Both sit on
the same I2C bus; daisy-chain with 4-wire cable.

### UART (DPS5005 MPPT controller)

| PCB header | Wire | Goes to | Notes |
|---|---|---|---|
| J4 pin 1 | 26 AWG red, ~30" | DPS5005 VCC (3.3 V logic) | |
| J4 pin 2 | 26 AWG black, ~30" | DPS5005 GND | |
| J4 pin 3 | 26 AWG white, ~30" | DPS5005 RX (received by ESP32 TX=GPIO26) | |
| J4 pin 4 | 26 AWG green, ~30" | DPS5005 TX (sent to ESP32 RX=GPIO27) | |

The DPS5005 is mounted in the same enclosure as the PCB (or in a
separate small enclosure near the battery). 9600 baud, 3.3 V logic.

### Grow light relay (12 V switched output)

| PCB header | Wire | Goes to | Notes |
|---|---|---|---|
| J5 pin 1 (12V in) | 14 AWG red, ~30" | 12 V battery (jumper from J1 +) | Looped from battery |
| J5 pin 2 (12V out, switched) | 14 AWG red, ~60" | Grow light fixture (+) | 12 V switched by relay |

Grow light is 12 V LED strip or 12 V COB panel, ~20 W. The relay (K1) is
rated 10 A at 125 VAC / 10 A at 30 VDC, plenty of headroom for a 20 W LED.

### Linear actuator

| PCB header | Wire | Goes to | Notes |
|---|---|---|---|
| J6 pin 1 | 14 AWG red, ~50" | Actuator motor lead A | ECO-WORTHY 12V 4" stroke |
| J6 pin 2 | 14 AWG black, ~50" | Actuator motor lead B | |

The actuator is on the north rail of the frame. The cable runs through
a flexible cable carrier or just a drip loop to allow tilt motion.

### Limit switches (hinge end-stops)

| PCB header | Wire | Goes to | Notes |
|---|---|---|---|
| J7 pin 1 | 26 AWG red, ~80" | Limit switch 0° (south wall, near hinge axis) | 10 kΩ pullup to 3V3 **at the PCB**, not at the switch |
| J7 pin 2 | 26 AWG white, ~80" | Limit switch 90° (north rail at 90° position) | 10 kΩ pullup to 3V3 at PCB |
| J7 pin 3 | 26 AWG black, ~80" | Common GND | Shared with both switches |

The 0° switch is mounted on the bed's south wall, just below the hinge
axis. It triggers when the frame is fully flat. The 90° switch is on
the north rail of the frame, triggering when the frame reaches vertical.
Both are NO (normally open) roller switches with a 10 kΩ pullup at the
PCB (not at the switch — long wire runs benefit from PCB-side pullup
to avoid noise pickup).

### DS18B20 soil temperature

| PCB header | Wire | Goes to | Notes |
|---|---|---|---|
| J8 pin 1 (data) | 26 AWG yellow, ~30" | DS18B20 data | 4.7 kΩ pullup to 3V3 **at the PCB** |
| J8 pin 2 (3V3) | 26 AWG red, ~30" | DS18B20 VDD | |
| J8 pin 3 (GND) | 26 AWG black, ~30" | DS18B20 GND | |

Mounted 6" deep in the bed soil, near the center.

### Soil moisture sensor (capacitive)

| PCB header | Wire | Goes to | Notes |
|---|---|---|---|
| J9 pin 1 (signal) | 26 AWG orange, ~30" | Capacitive sensor analog out | 0–3 V output |
| J9 pin 2 (GND) | 26 AWG black, ~30" | Capacitive sensor GND | |

Capacitive sensor mounted in the bed soil, near the DS18B20. Powered
from the same 3V3 rail as the DS18B20 (use a tap on the J8 3V3 wire,
not a separate connection, to avoid voltage drop).

### Battery voltage sense (divided)

| PCB header | Wire | Goes to | Notes |
|---|---|---|---|
| J10 pin 1 (divided) | 26 AWG purple, ~18" | PCB-side divider tap (after 10k/10k from 12V) | NOT directly to battery |
| J10 pin 2 (GND) | 26 AWG black, ~18" | Common GND | |

The 12V → divided voltage is done **on the PCB** (R1 = 10kΩ from 12V
to TP4, R2 = 10kΩ from TP4 to GND). J10 just brings the divided signal
(GPIO33 input) and GND back to the connector. So J10 is a 2-wire cable
from PCB to itself — actually, J10 is a connector on the PCB, with a
jumper or short wire from J1's 12V to the divider input. **In practice
you can omit J10 entirely and use the 10k divider as a through-hole
component on the PCB, with the divider input tapped from the 12V rail
right at the fuse output.**

Simplification: **skip J10 entirely.** Solder the two 10 kΩ resistors
on the PCB, with one end to 12V (after F1) and the other end to GND.
The middle tap goes to GPIO33. The wiring on the schematic stays as J10
for documentation, but the actual PCB can have the divider as a small
2-resistor network on the board.

---

## 2. Total wire run summary

| From PCB to | Wire count | AWG | Length (each) | Total wire |
|---|---|---|---|---|
| Battery | 2 | 12 | 24" | 4 ft |
| IMU (on frame) | 4 | 26 | 36" | 12 ft |
| INA219 (at motor) | 0 (shares IMU cable) | — | — | — |
| DPS5005 (in enclosure) | 4 | 26 | 30" | 10 ft |
| Grow light | 2 | 14 | 60" | 10 ft |
| Linear actuator | 2 | 14 | 50" | 8.3 ft |
| Limit switch 0° | 3 | 26 | 80" | 20 ft |
| Limit switch 90° | (shares 0° cable) | — | — | — |
| DS18B20 (in soil) | 3 | 26 | 30" | 7.5 ft |
| Soil moisture (in soil) | 2 | 26 | 30" | 5 ft |
| (Battery sense on PCB) | 0 | — | — | — |

**Total wire: ~75 ft of 26 AWG + ~22 ft of 14 AWG + ~4 ft of 12 AWG.**

JST-XH connectors: ~12 connectors (3-4 pin each), $2-3 total.

---

## 3. Cable routing diagram

Top-down view of the bed + frame:

```
       ┌────────────────────────────────────────────────────┐
       │                  96" bed length                     │
       │                                                    │
       │  [PCB]                                    [IMU]    │
       │  enclosure    [limit sw 0°]                       │
       │  on east      at south wall                       │
       │  wall         ↓                                    │
       │  │            ╓─╳─╖ ←─── hinges (4) ─────          │
       │  │            ║   ║                                │
       │  │            ║ F ║   FRAME (96"×44.6" rectangle) │
       │  │            ║ R ║   2x6 PT perimeter             │
       │  │            ║ A ║   + 2x4 diagonal brace          │
       │  │            ║ M ║                                │
       │  │            ║ E ║   ▓ panel (97"×44.6")          │
       │  │            ║   ║                                │
       │  │            ╙───╜   ┌─────────────┐              │
       │  │                    │ limit sw 90°│              │
       │  │                    └─────────────┘              │
       │  │                                                   │
       │  └────[cable carrier]────[actuator]────             │
       │         on north rail    [battery 12V]             │
       └────────────────────────────────────────────────────┘

       Legend:
         [PCB]  = Wattplot Controller v1 PCB (in enclosure)
         [IMU]  = BMI160 IMU on the frame
         [actuator] = linear actuator on north rail
         [limit sw 0°] = roller switch on south wall (triggers at flat)
         [limit sw 90°] = roller switch on frame (triggers at vertical)
         [battery 12V] = 12V LiFePO4 (e.g., 100Ah) under the bed
```

**Key routing rules:**

1. **Power first:** 12 AWG from battery to PCB. Fused within 6" of battery (+).
2. **Motor cable:** 14 AWG from PCB to actuator. Through a flexible cable
   carrier (or a simple drip loop with 4" of slack) to allow tilt motion.
3. **IMU cable:** 26 AWG 4-wire from PCB to IMU on the frame. Through the
   cable carrier with the motor cable. Twisted pair to reduce noise.
4. **Soil sensor cables:** 26 AWG 3-wire (DS18B20) and 2-wire (soil
   moisture), routed through a grommet in the bed's south wall into the
   soil. Both sensors buried 6" deep, 12" from the south wall.
5. **Limit switches:** 26 AWG 3-wire from PCB to the hinge area. The 0°
   switch mounts on the south wall just below the hinge axis. The 90°
   switch mounts on the north rail of the frame.
6. **DPS5005 + grow light:** Inside the PCB enclosure (or a small
   adjacent enclosure). 14 AWG from grow light back through the south
   wall grommet.

---

## 4. Connector pinouts (JST-XH, all viewed from the wire side)

**J1 — Battery (XT60):**
```
Pin 1: V+ (12V)
Pin 2: V− (GND)
```

**J2 — I2C breakout:**
```
Pin 1: 3V3 (red)
Pin 2: GND  (black)
Pin 3: SDA  (white)
Pin 4: SCL  (green)
```

**J4 — DPS5005 UART:**
```
Pin 1: 3V3 (red)
Pin 2: GND  (black)
Pin 3: TX  (white) → ESP32 sends to DPS5005 RX
Pin 4: RX  (green) ← ESP32 receives from DPS5005 TX
```

**J5 — Grow light:**
```
Pin 1: 12V switched (red) → to grow light (+)
Pin 2: 12V battery   (red) → from J1 (looped)
```

(Wait, this has only 2 pins, not 3. Let me re-check the PCB spec.)

**J5 — Grow light (revised, 2-pin):**
```
Pin 1: 12V switched (relay K1.NO → K1.COM)
Pin 2: 12V battery in (looped from J1)
```

The grow light has 2 wires: 12V switched, and GND (which comes from the
common ground rail). So the grow light gets:
- 12V switched (from J5 pin 1) — from the relay
- GND (from common ground, e.g., the battery − terminal)

This means the grow light cable has only ONE 14 AWG wire for 12V, and
the ground return is through the common ground (separate wire or via
the chassis/battery negative). The JST-XH connector is 2-pin for the
12V side; the ground return is via a separate 14 AWG wire from the
battery to the grow light.

Hmm, that means a 3-pin connector is cleaner. Let me update the PCB:

**J5 — Grow light (3-pin):**
```
Pin 1: 12V battery in (looped from J1)
Pin 2: 12V switched out (to grow light)
Pin 3: GND (to grow light ground)
```

The grow light has 2 wires going to the PCB: switched 12V and GND. The
PCB has the battery 12V looped to J5 to power the relay.

OK let me finalize the wiring list. The grow light cable is 2 wires
(12V switched, GND) plus 1 wire for the battery loop (12V in). That's
3 wires total to/from the grow light area.

---

## 5. Final cable list (with wire colors)

| Cable | From | To | Wires | Length | Connector |
|---|---|---|---|---|---|
| Battery | Battery + | PCB J1 + | 12 AWG red | 24" | XT60 |
| Battery | Battery − | PCB J1 − | 12 AWG black | 24" | XT60 |
| I2C | PCB J2 | IMU + INA219 (daisy) | 4× 26 AWG (red, black, white, green) | 36" | JST-XH 4-pin both ends |
| DPS5005 | PCB J4 | DPS5005 UART | 4× 26 AWG | 30" | JST-XH 4-pin both ends |
| Grow light | PCB J5 | Grow light fixture | 3× 14 AWG | 60" | JST-XH 3-pin at PCB, bare at light |
| Actuator | PCB J6 | Linear actuator | 2× 14 AWG | 50" | JST-XH 2-pin at PCB, spade at actuator |
| Limit sw 0° | PCB J7 | South wall switch | 3× 26 AWG | 80" | JST-XH 3-pin at PCB, bare at switch |
| Limit sw 90° | (shares 0° cable) | Frame switch | (daisy on same cable) | 0 | (daisy) |
| DS18B20 | PCB J8 | Soil temp sensor | 3× 26 AWG | 30" | JST-XH 3-pin at PCB, bare at sensor |
| Soil moisture | PCB J9 | Soil moisture sensor | 2× 26 AWG | 30" | JST-XH 2-pin at PCB, bare at sensor |
| USB-C | PCB J3 | Laptop (for first flash) | USB-C cable | 6 ft | USB-C both ends |

---

## 6. Tools for wiring

- Wire stripper (22-12 AWG range)
- JST-XH crimper (PA-09 or equivalent)
- XT60 connector crimper
- Multimeter (for continuity, voltage checks)
- Heat-shrink tubing (3 mm and 6 mm)
- Cable ties + cable carrier (for the actuator/IMU cable to the frame)
- Grommets (for the bed wall penetrations — 4× grommets for the
  sensor cables + 1× for the battery cables + 1× for the actuator cable)
- Silicone sealant (for sealing grommets against rain ingress)

---

## 7. Wiring checklist (pre-power)

Before connecting the battery, verify:

- [ ] All JST-XH connectors are fully seated (audible click)
- [ ] No bare wire is exposed at any connector
- [ ] Battery fuse (F1) is NOT installed yet (install last)
- [ ] All sensor cables are routed through grommets and sealed
- [ ] Cable carrier is installed on the frame-to-bed cable run
- [ ] Multimeter continuity check: no shorts between 12V and GND
- [ ] Multimeter continuity check: no shorts between 3V3 and GND
- [ ] Multimeter continuity check: each limit switch closes when pressed
  (should be 0 Ω or close)

When all checks pass: install the fuse. Power on. Verify the ESPHome
boot sequence in the serial monitor.
