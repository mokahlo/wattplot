# Wattplot v2 — Bill of Materials

## Design rules (enforced)

1. **No miter cuts.** Every cut is a 90° square cut. Joints are butt,
   half-lap, or lap. The diagonal brace has square ends that butt into the
   long rails — no angled cuts at the corners.
2. **All hardware off the shelf.** Hinges, panel clamps, bolts, screws,
   rod, and pins are all standard sizes from Home Depot, McMaster, or
   solar-mounting suppliers (IronRidge / Unirac / Quick Mount). No custom
   metal parts.
3. **Simple, common dimensions.** All lumber is from standard stock lengths
   (8 ft, 10 ft, 12 ft) with reasonable waste (≤ 18" per board). No
   fractional-inch stock lengths.

## Sustainability & sourcing

The frame and planter are **all lumber** (Douglas Fir, pressure-treated for ground
contact). Hardware is metal where it has to be (hinges, panel clamps) — there's
no functional benefit to making a ½" hinge pin out of wood.

For the most sustainable build:
- **Wood:** specify **FSC-certified** Douglas Fir where available
  (look for the FSC label or the "SFI" chain-of-custody mark)
- **Fasteners:** **HDG (hot-dipped galvanized)** is the cost-effective choice for
  ACQ-treated lumber. Stainless (304/316) lasts longer but ~3× the cost.
- **Finish:** raw PT lumber is fine. If you want a tinted look, use a
  **linseed-oil-based** exterior finish (e.g. Tried & True). Avoid film-forming
  stains on PT lumber — they peel in 2 years.
- **Local sourcing:** most home improvement stores stock PT DF in standard
  sizes (2x6x8, 2x4x8, 4x4x8) and 1x6x8 cedar fence/deck boards. For FSC,
  check a local lumber yard.

---

## Lumber (PT Douglas Fir structure, 1x6 cedar wall skin, dressed "S4S")

### Bed walls (1x6 cedar skin + 2x4 PT cleats + 2x6 PT caps, 22" tall)

Wheelchair-accessible height: 4 courses of 1x6 (5.5" actual) = 22" wall,
25" rim on the 3" skids. The ¾" skin carries no structural load — vertical
2x4 cleats (≤24" o.c.) resist soil pressure, and a flat 2x6 cap on the
hinge (S) and strut (N) walls takes the hinge/strut screws. Never screw
hinges into the ¾" skin.

| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 8 | 1x6 cedar | 8 ft | Long wall skin (N/S), 4 courses × 2 walls | 1x6x8ft, no waste |
| 8 | 1x6 cedar | 43.1" | Short wall skin (W/E), 4 courses × 2 walls | 2 per 1x6x8ft (4 boards), 9.8" waste |
| 16 | 2x4 PT | 22" | Vertical cleats: 5 per long wall, 3 per short | 4 per 2x4x8ft (4 boards), 8" waste |
| 2 | 2x6 PT | 8 ft | Wall caps, hinge + strut walls (laid flat) | 2x6x8ft, no waste |

**Lumber for bed walls: 12× 1x6 cedar + 4× 2x4 + 2× 2x6 = 18 boards**

### Bed skids (4x4 PT DF, actual 3.5" × 3.5")
| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 2 | 4x4 | 8 ft | Long skids, under the long walls | 4x4x8ft, no waste |

**Lumber for skids: 2 boards, 16 linear feet, ~11 bf**

### Frame long rails (2x6 PT DF, actual 1.5" × 5.5")
| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 2 | 2x6 | 8 ft | Long rails (E and W sides of the frame), 96" each | 2x6x8ft, no waste |

**Lumber for long rails: 2 boards, 16 linear feet, ~11 bf**

### Frame cross rails (2x6 PT DF, actual 1.5" × 5.5")
| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 2 | 2x6 | 8 ft | Cross rails (N and S ends), 42" each, 2 from 1 board | 2x6x8ft, 12" waste per board |

**Lumber for cross rails: 2 boards, 16 linear feet, ~11 bf**

### Diagonal brace (2x4 PT DF, actual 1.5" × 3.5")
| Qty | Size | Length | Use | Source / waste |
|---|---|---|---|---|
| 1 | 2x4 | 10 ft | Diagonal brace across frame interior (102"), square ends | 2x4x10ft, 18" waste |

**Lumber for brace: 1 board, 10 linear feet, ~7 bf**

**Total lumber: 25 boards** (12× 1x6x8 cedar, 5× 2x4x8 + 1× 2x4x10 PT,
5× 2x6x8 PT, 2× 4x4x8 PT)

At Phoenix prices (1x6x8 cedar ~$8–12/board, PT 2x6/2x4 ~$1.00–$1.50/bf,
4x4 ~$2.50–$3.00/bf): **~$220–$290 in lumber**, FSC premium ~+15%.
The cedar skin costs more per board than PT 2x12 but the wall is 2×
taller for roughly the same money — the accessibility height is nearly
free in lumber terms.

---

## Metal hardware (all off the shelf)

### Hinges + continuous hinge pin
| Qty | Item | Source | Cost |
|---|---|---|---|
| 4 | Galvanized butt hinge, 4"×4" leaf, ½" pin | Home Depot / McMaster | ~$5 ea = **$20** |
| 1 | ½" × 72" steel rod (continuous hinge pin) | Home Depot | **$10** |

The 72" rod threads through all 4 hinges for a single, continuous hinge axis.
Length 72" is a standard Home Depot cut.

### Panel mounting (6 × aluminum mid-clamps)
| Qty | Item | Source | Cost |
|---|---|---|---|
| 6 | Aluminum mid-clamp, 35mm channel, M8 bolt | IronRidge / Unirac | ~$3 ea = **$18** |
| 6 | M8 stainless bolt + EPDM washer | (with clamp) | (included) |

### Actuator + clevis pin
| Qty | Item | Source | Cost |
|---|---|---|---|
| 1 | ECO-WORTHY 12V 4" stroke 330 lbf linear actuator | Amazon | **$35** |
| 1 | ½" × 3" steel clevis pin | McMaster / hardware store | **$5** |

---

## Electronics (controller PCB + harness)

The full-size build uses the schematic rev B controller PCB. Components are
grouped by **subsystem** so you know which part of the system each part
serves. Schematic reference designators (U5a, U5b, etc.) are included for
cross-reference to `docs/schematic.html`.

### Power tree (battery → 5 V → 3.3 V)
| Qty | Item | Subsystem | Source | Cost |
|---|---|---|---|---|
| 1 | XT60 panel-mount connector | Power tree | Amazon / Amass | ~$2 |
| 1 | 10 A ATO fuse + inline holder | Power tree | Amazon / auto | ~$3 |
| 1 | SS34 schottky diode (reverse polarity) | Power tree | Digi-Key | <$1 |
| 1 | SMBJ16A TVS diode (16 V clamp) | Power tree | Digi-Key | <$1 |
| 1 | MP1584EN buck module, 4.5–28 V → 5 V, 3 A | Power tree | Amazon | ~$3 |
| 1 | AMS1117-3.3 LDO regulator (SOT-223) | Power tree | Digi-Key | <$1 |
| 2 | 100 µF / 35 V electrolytic (input + output bulk) | Power tree | Amazon | <$1 |
| 1 | 10 µF / 10 V ceramic (LDO output) | Power tree | Amazon | <$1 |

### MCU / Controller (ESP32-S3)
| Qty | Item | Subsystem | Source | Cost |
|---|---|---|---|---|
| 1 | ESP32-S3-DevKitC-1-N16R8 (16 MB flash, 8 MB PSRAM) | MCU | Mouser / Digi-Key / Amazon | ~$14 |
| 1 | USB-C receptacle, 16-pin, mid-mount | MCU | Digi-Key | ~$1 |
| 1 | USBLC6-2SC6 ESD protection array | MCU | Digi-Key | ~$1 |
| 2 | 5.1 kΩ 1% resistor (USB-C CC pull-down) | MCU | Amazon | <$1 |
| 1 | 10 kΩ + 1 µC R/C pair (ESP32 reset) | MCU | Amazon | <$1 |
| 2 | Tactile switch (BOOT, RST) | MCU | Amazon | ~$1 |

### Actuator (panel tilt — DRV8871 U5a)
| Qty | Item | Subsystem | Source | Cost |
|---|---|---|---|---|
| 1 | DRV8871 H-bridge motor driver (U5a) | Actuator | TI / Digi-Key | ~$3 |
| 1 | 0.1 Ω current-sense shunt (1%, 1 W) | Actuator | Digi-Key | <$1 |
| 1 | 100 nF + 10 µF cap pair (U5a supply decoupling) | Actuator | Amazon | <$1 |
| 1 | 10 kΩ pull-up (U5a nFAULT) | Actuator | Amazon | <$1 |
| 1 | 100 kΩ pull-up (U5a nSLEEP, tie to 3V3) | Actuator | Amazon | <$1 |
| 3 | JST-XH 2-pin (U5a OUT1, OUT2, motor pigtail) | Actuator | Amazon | ~$1 |

### Solenoid (water / latch — DRV8871 U5b)
| Qty | Item | Subsystem | Source | Cost |
|---|---|---|---|---|
| 1 | DRV8871 H-bridge motor driver (U5b) | Solenoid | TI / Digi-Key | ~$3 |
| 1 | 0.1 Ω current-sense shunt (1%, 1 W) | Solenoid | Digi-Key | <$1 |
| 1 | 100 nF + 10 µF cap pair (U5b supply decoupling) | Solenoid | Amazon | <$1 |
| 1 | 10 kΩ pull-up (U5b nFAULT) | Solenoid | Amazon | <$1 |
| 1 | 100 kΩ pull-up (U5b nSLEEP, tie to 3V3) | Solenoid | Amazon | <$1 |
| 1 | 12 V irrigation solenoid valve, ½" NPT, NC | Solenoid | Amazon | ~$10 |
| 1 | ½" NPT brass fitting + Teflon tape | Solenoid | Home Depot | ~$5 |
| 2 | JST-XH 2-pin (U5b OUT1, solenoid pigtail) | Solenoid | Amazon | ~$1 |

### Sensors (DS18B20, soil moisture, INA219)
| Qty | Item | Subsystem | Source | Cost |
|---|---|---|---|---|
| 3 | DS18B20 waterproof temp probe (1-Wire) | Sensors | Amazon | ~$10 |
| 1 | 4.7 kΩ pull-up (1-Wire bus) | Sensors | Amazon | <$1 |
| 1 | Capacitive soil moisture sensor (v1.2 or v2) | Sensors | Amazon | ~$4 |
| 1 | 100 nF + 10 kΩ low-pass filter (soil AOUT) | Sensors | Amazon | <$1 |
| 2 | INA219 I²C current/voltage sensor module | Sensors | Amazon | ~$6 |
| 2 | 100k/10k resistor divider (battery V sense) | Sensors | Amazon | <$1 |
| 4 | JST-XH 3-pin (sensor pigtails) | Sensors | Amazon | ~$2 |

### HMI / Status
| Qty | Item | Subsystem | Source | Cost |
|---|---|---|---|---|
| 1 | 3 mm LED, monochrome (status) | HMI / Status | Amazon | <$1 |
| 1 | 330 Ω resistor (LED current limit) | HMI / Status | Amazon | <$1 |

### Power components external to the PCB
| Qty | Item | Subsystem | Source | Cost |
|---|---|---|---|---|
| 1 | Sunapex 10 A MPPT (mini) / Victron SmartSolar 75/15 (full-size) | Solar charging | Amazon / vendor | $40-$90 |
| 1 | 12 V LiFePO4 battery, 50-100 Ah (mini: 10-20 Ah) | Solar charging | Amazon / LiTime | $90-$400 |
| 1 | Solar panel, 100 W (mini) / 620 W bifacial (full-size) | Solar charging | Longi / ECO-WORTHY | $80-$200 |

**Electronics total: ~$260-$330 (full-size, including solar charging components)**
or **~$120-$170 (mini)** — see `bom_mini.md` for the mini-specific list.

---

## Fasteners (all standard sizes)

| Qty | Item | Use |
|---|---|---|
| 8 | 3/8" × 4" carriage bolts, HDG, with washers + nuts | Bed corner joints (half-lap) |
| 8 | 5/16" × 3" lag bolts, HDG | Hinge leaves to bed wall (2 per hinge) |
| 24 | ¼" × 3" deck screws, HDG, Torx T-25 | Frame joints, panel clamp fasteners |
| 1 lb | 3" exterior deck screws (general) | Misc assembly |

**Total fasteners: ~$30**

---

## Cost summary

| Category | Cost |
|---|---|
| Lumber (13 boards, 120 bf) | $170–$230 |
| Hinges (4) | $20 |
| Hinge pin (½" × 72" rod) | $10 |
| Panel clamps (6) | $18 |
| Linear actuator | $35 |
| Clevis pin | $5 |
| Fasteners | $30 |
| **Total structural parts** | **~$290–$350** |
| Electronics (PCB, drivers, sensors, MCU) | $80–$130 |
| Solar charging (MPPT, battery, panel) | $210–$690 |
| **Total with electronics** | **~$580–$1,170** |

No welding required. No concrete. No 120V power tools beyond a drill + impact driver
+ circular saw (or a lumber yard can cut to length for you).

---

## What you DON'T need

- ❌ Welder (it's all bolted/screwed)
- ❌ Concrete / rebar / post anchors
- ❌ Steel angle iron / Unistrut
- ❌ Miter saw (all cuts are 90° square cuts)
- ❌ Custom-fabricated metal parts
- ❌ Permit (verify with your city — at this size, most residential zones
  don't require a permit for an unoccupied accessory structure, but the
  Maricopa County wind amendments and IRC triggers are real if the structure
  is larger. See `analysis/wind_load_report.md` for the engineering.)

---

## Tools needed

- Circular saw (or have the lumber yard pre-cut)
- Drill / impact driver
- ½" drill bit (for the ½" hinge rod clearance through the bed wall)
- ⅜" drill bit (for carriage bolts)
- ¼" pilot bit (for deck screws)
- Tape measure, square, level
- 9/16" wrench (for 3/8" carriage bolts)
- Socket wrench for lag bolts

