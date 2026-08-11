# Surge protection, lightning, and outdoor electrical safety

The wattplot lives outside. The panel, battery, MPPT, microinverter,
DRV8871 H-bridges, and ESPHome controller are all exposed to the
same electrical environment as any rooftop solar install. The
microinverter and MPPT have internal surge protection (UL 1741
requires it), but the **low-voltage DC side** (12 V battery, DRV8871
leads, DS18B20, INA219 I²C bus, the 100k/10k divider to GPIO7) does
not. A nearby lightning strike induces a voltage spike on every
conductor — including the panel frame, which is grounded only by
chance through the soil.

This doc is what to do about it. It's not a substitute for a
licensed electrician; it's a checklist of where the gaps are in
the off-the-shelf MPPTs and what to add on top.

## What's already protected

- **Microinverter (Enphase IQ7+, APsystems DS3):** UL 1741
  certified. Has Type 2 surge protection on the AC output and the
  DC input. Doesn't protect the downstream DC bus — it only
  protects itself.
- **Sunapex 10A MPPT (mini):** IP67 enclosure. No internal surge
  protection documented; the spec sheet says "DC input transient
  voltage: 25 V max" (which is the normal Voc, not a surge rating).
  In practice the Sunapex has a TVS diode on the input that
  clamps at ~32 V. A direct lightning strike will still kill it.
- **Victron SmartSolar 100/30 / EPEver Tracer 4210AN (full-size):**
  Both have internal surge protection on the PV input (Type 2 SPD,
  rated to 4 kV / 8/20 µs). They protect themselves; they don't
  protect downstream.

## What is NOT protected

- **12 V battery bus.** A 1 km lateral lightning strike induces
  ~6 kV on every conductor in the area, including the battery
  leads. The DRV8871's absolute max on its VM pin is 45 V; the
  ESP32-S3 is 3.6 V on its GPIO; the INA219 is 6 V on SDA/SCL.
  A direct strike will destroy the controller.
- **DS18B20 1-Wire bus.** The DS18B20 is a 3.3 V part on a 30 m
  wire. The 1-Wire protocol has no error correction and no
  transient protection. A strike within 100 m can latch up the bus
  and require a power-cycle.
- **I²C bus (INA219, panel-telemetry, future MPPT).** I²C is
  differential on the SCL/SCA pair, but the INA219 inputs are
  referenced to the battery bus. A 5 kV spike on the panel
  side couples through the shunt resistor and lands on the INA219
  SDA pin.
- **The soil itself.** A ground rod near the wattplot (for the
  AC microinverter's safety ground) is a high-current return
  path during a strike. Bury it ≥ 3 m from the bed; the closer
  it is, the more voltage gradient in the soil the bed's buried
  sensors see.

## What to add (full-size build only; the Mini is indoors-on-bench)

### 1. DC-side Type 2 SPD on the battery bus

Mount a **Dehn DEHNguard DG M YPV 1000** (or equivalent) on the
12 V battery side, as close to the MPPT as possible. Cost ~$80.
Specs: 5 kA nominal discharge, 40 kA max, 1.5 kV voltage
protection level. Wires from the SPD to the MPPT battery terminal
should be < 0.5 m; longer is worse because the inductance of the
lead adds to the residual voltage.

### 2. TVS diode on every low-voltage signal line

The DS18B20 1-Wire bus should have a **P6KE6.8CA** (or similar
6.8 V bidirectional TVS) at the controller end. The INA219 I²C
bus should have one on each of SDA and SCL. Cost: $0.50 each.

Wiring: TVS between the signal line and ground, as close to the
controller's GPIO as possible (within 50 mm).

### 3. AC-side Type 1 SPD at the microinverter

The Enphase / APsystems has internal Type 2 protection. Adding a
Type 1 SPD at the AC disconnect (between the microinverter and the
service panel) is the right place for a whole-home lightning
arrestor. Cost: ~$150 for an Intermatic IG1240RC3 or equivalent.
This protects the microinverter, the AC wiring, and the home
service panel — the wattplot's benefit is indirect (less surge
coupling onto the ground wire).

### 4. Galvanic isolation on the I²C bus

The panel-side INA219 (at 0x41) is at panel ground; the
controller-side INA219 (at 0x40) is at battery ground. A direct
strike on the panel couples through the panel's I²C ground into
the controller. The cheapest isolation is an **I²C isolator**
(ADuM1251 or similar; ~$5). Run the panel-side INA219 over the
isolator, keep the controller-side direct.

For a 30 m run, the I²C bus should also have a twisted pair with
shield tied to ground at one end (the controller). The 4.7 kΩ
pullups go on the controller side, not the panel side.

### 5. Ground the panel frame

The LONGi Hi-MO X10 has a frame ground hole. Connect it to the
same ground rod as the microinverter with 6 AWG copper. A
resistance < 25 Ω to earth is the NEC minimum; aim for < 10 Ω
with a proper 8 ft copper-clad rod in moist soil.

## What NOT to do

- **Don't use a gas discharge tube (GDT) alone.** GDTs have a
  high striking voltage (75-300 V) and a slow response time
  (microseconds). They are good for AC-line protection at the
  service panel, NOT for the 5 V / 3.3 V DC bus.
- **Don't put a fuse on the battery bus.** A fuse won't fire
  fast enough to protect the DRV8871 from a 5 kV surge. Fuses
  are for overcurrent (short circuit), not overvoltage.
- **Don't rely on the MPPT's surge rating.** The MPPT's
  internal TVS protects the MPPT. It does NOT protect the
  downstream DRV8871 / ESP32 / sensors.
- **Don't run signal wires parallel to AC.** The microinverter's
  AC output is 240 V; a 30 m parallel run with a 5 V signal wire
  couples ~5 mA of capacitive current into the signal, which is
  enough to latch up a DS18B20. Cross at 90° if you have to cross.

## Cost summary

For the full-size build:

| Item | Cost | Source |
|---|---|---|
| DEHNguard DG M YPV 1000 (DC SPD) | $80 | DEHN, alliedelec |
| Intermatic IG1240RC3 (AC Type 1 SPD) | $150 | Home Depot, electric supply |
| P6KE6.8CA TVS (×6) | $3 | Digi-Key |
| ADuM1251 I²C isolator | $5 | Digi-Key |
| 6 AWG copper ground wire + 8 ft rod | $40 | Home Depot |
| **Total** | **~$280** | |

For the Mini (10 W panel, indoor bench), none of this applies.
The bench PSU is already surge-protected by the lab's breaker
panel. Skip.

## When to revisit

- After the first direct strike. The wattplot's electronics will
  be dead; the surge protection should keep the **structure**
  (the bed, the posts, the panel frame) intact. Replace the
  DRV8871s, the ESP32, the INA219s, the DS18B20s.
- If you move the wattplot to a rooftop or other elevated
  location, the strike probability goes up significantly.
  Lightning arrestors on the structure itself become necessary
  (NEC 690.31 for PV).
- If a future rev of the firmware supports OTA firmware update
  (it doesn't yet, beyond the initial flash), surge damage that
  bricks the chip becomes much less of an outage. Worth waiting
  for.